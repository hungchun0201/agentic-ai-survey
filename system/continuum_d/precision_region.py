# SPDX-License-Identifier: Apache-2.0
"""Physical quantize-on-offload: a compressed CPU/DRAM side-region + worker handler.

This is the DEFERRED SEAM made real (EVAL_PLAN §6). v0.23's stock
`SingleDirectionOffloadingHandler` pre-allocates a fixed-stride pinned pool of
`(num_cpu_blocks, cpu_page_size)` int8 and moves blocks with a raw-pointer batched
DMA (`ops.swap_blocks_batch`) — there is NO seam for a variable-size compressed
payload. So instead of retrofitting that kernel, we replace the CPU-side storage
with a **compressed side-region**:

  * on OFFLOAD (GPU->CPU): read the block's KV page off the live GPU KV tensor,
    quantize it (reuse continuum_d.codec: fp8 / int4), and store ONLY the compact
    payload (+ fp16 scales) on the host. The big fixed pinned pool is never
    allocated, so the resident host bytes are PHYSICALLY smaller (peak-bytes
    measured), and less data crosses PCIe on reload.
  * on RELOAD (CPU->GPU): dequantize the compact payload back to the model dtype
    and write it into the GPU KV page before it re-enters attention
    (dequant-on-reload; no mixed-precision attention kernel).

Precision is chosen per block by the scheduler policy and rides to the worker in
a `PrecisionCPULoadStoreSpec` (a `CPULoadStoreSpec` subclass carrying a parallel
per-block precision-code array). For TP=1 (UniProcExecutor) the connector metadata
passes by reference in-process, so the subclass travels for free; for TP>1 it
serializes as a plain object with numpy arrays.

The `joint | decoupled | fp16` flag flows through unchanged: `fp16` blocks are
stored raw (lossless, full size); `fp8`/`int4` blocks are compressed.
"""

from __future__ import annotations

import json
import logging

import numpy as np
import torch

logger = logging.getLogger("continuum_d")

from vllm.v1.kv_offload.cpu.common import CPULoadStoreSpec
from vllm.v1.kv_offload.base import CanonicalKVCaches, GPULoadStoreSpec
from vllm.v1.kv_offload.worker.worker import (
    OffloadingHandler,
    TransferResult,
    TransferSpec,
)

from continuum_d.codec import CompressedBlock, Precision, compress, decompress

# compact int code per precision, carried in the spec across the worker boundary
_PREC_CODE: dict[Precision, int] = {
    Precision.FP16: 0,
    Precision.FP8: 1,
    Precision.INT4: 2,
}
_CODE_PREC: dict[int, Precision] = {v: k for k, v in _PREC_CODE.items()}


def precision_code(p: Precision) -> int:
    return _PREC_CODE[p]


class PrecisionCPULoadStoreSpec(CPULoadStoreSpec):
    """CPULoadStoreSpec + a per-block precision code (0=fp16,1=fp8,2=int4).

    `precisions[i]` is the storage precision of the block at `block_ids[i]`.
    medium() stays "CPU" so the worker routes it to the CPU<->GPU handlers.
    """

    def __init__(self, block_ids: list[int], precisions: list[int] | np.ndarray):
        super().__init__(block_ids)
        self.precisions = np.asarray(precisions, dtype=np.int8)

    def __repr__(self) -> str:
        return f"PrecisionCPULoadStoreSpec(blocks={self.block_ids!r}, prec={self.precisions!r})"


def _choose_group_size(n: int) -> int:
    """Largest group size in {128,64,32,16} dividing n, else n (single group)."""
    for gs in (128, 64, 32, 16):
        if n % gs == 0:
            return gs
    return n


class _StoredBlock:
    """One offloaded block: a list of per-canonical-tensor compact payloads."""

    __slots__ = ("payloads", "nbytes")

    def __init__(self, payloads: list, nbytes: int):
        self.payloads = payloads  # list of ("raw", cpu_bytes) | ("comp", CompressedBlock_cpu, n, gs)
        self.nbytes = nbytes


class CompressedSideRegion:
    """Host-resident store of compressed KV blocks, keyed by CPU block-slot id.

    Tracks the REAL resident byte footprint (current + peak) so the physical DRAM
    reduction is measured, not assumed. Shared by the store + load handlers.
    """

    def __init__(self):
        self._blocks: dict[int, _StoredBlock] = {}
        self.current_bytes: int = 0
        self.peak_bytes: int = 0
        # book-keeping for the smoke's measurement
        self.fp16_equiv_bytes_stored: int = 0   # what fp16-offload would have used
        self.compressed_bytes_stored: int = 0   # what we actually stored (cumulative)
        self.reload_bytes: int = 0              # compact bytes moved on reload
        self.reload_fp16_equiv_bytes: int = 0   # fp16 bytes the same reloads would move

    def put(self, block_id: int, sb: _StoredBlock, fp16_equiv: int) -> None:
        old = self._blocks.get(block_id)
        if old is not None:
            self.current_bytes -= old.nbytes
        self._blocks[block_id] = sb
        self.current_bytes += sb.nbytes
        self.peak_bytes = max(self.peak_bytes, self.current_bytes)
        self.compressed_bytes_stored += sb.nbytes
        self.fp16_equiv_bytes_stored += fp16_equiv

    def get(self, block_id: int) -> _StoredBlock | None:
        return self._blocks.get(block_id)

    def note_reload(self, compact: int, fp16_equiv: int) -> None:
        self.reload_bytes += compact
        self.reload_fp16_equiv_bytes += fp16_equiv

    def report(self) -> dict:
        ratio = (self.peak_bytes / self.fp16_equiv_bytes_stored
                 if self.fp16_equiv_bytes_stored else 1.0)
        return {
            "peak_resident_bytes": self.peak_bytes,
            "current_resident_bytes": self.current_bytes,
            "fp16_equiv_bytes_stored": self.fp16_equiv_bytes_stored,
            "compressed_bytes_stored": self.compressed_bytes_stored,
            "peak_vs_fp16_equiv_ratio": round(ratio, 4),
            "reload_bytes": self.reload_bytes,
            "reload_fp16_equiv_bytes": self.reload_fp16_equiv_bytes,
            "reload_pcie_ratio": round(
                self.reload_bytes / self.reload_fp16_equiv_bytes, 4)
            if self.reload_fp16_equiv_bytes else 1.0,
        }


class PrecisionOffloadingHandler(OffloadingHandler):
    """Synchronous compress-on-offload / dequant-on-reload transfer handler.

    Correctness-first (synchronous) rather than the stock async-stream DMA: for a
    smoke this proves the physical mechanism; async streaming is a follow-up.
    """

    def __init__(
        self,
        gpu_tensors: list[torch.Tensor],   # each (num_blocks, page_size) int8, on GPU
        region: CompressedSideRegion,
        kv_dtype: torch.dtype,
        gpu_to_cpu: bool,
    ):
        self.gpu_tensors = gpu_tensors
        self.region = region
        self.kv_dtype = kv_dtype
        self.gpu_to_cpu = gpu_to_cpu
        self._itemsize = torch.empty(0, dtype=kv_dtype).element_size()
        self._finished: list[TransferResult] = []
        self.transfer_type = ("GPU", "CPU") if gpu_to_cpu else ("CPU", "GPU")
        self._on_cuda = bool(gpu_tensors) and gpu_tensors[0].device.type == "cuda"

    def _sync(self) -> None:
        if self._on_cuda:
            torch.cuda.synchronize()

    # ---- codec on a single raw KV page ----

    def _compress_page(self, page_i8: torch.Tensor, prec: Precision) -> tuple:
        """page_i8: (page_size,) int8 on GPU -> a compact CPU payload tuple."""
        if prec is Precision.FP16:
            cpu = page_i8.to("cpu", copy=True)
            return ("raw", cpu, cpu.numel())
        kv = page_i8.view(self.kv_dtype)             # (N,) model-dtype
        n = kv.numel()
        gs = _choose_group_size(n)
        x = kv.reshape(n // gs, gs)                  # per-group scales along axis=-1
        cb = compress(x, prec, axis=-1, group_size=gs)
        data_cpu = cb.data.view(torch.uint8).to("cpu", copy=True)
        scales_cpu = (cb.scales.to("cpu", copy=True)
                      if cb.scales is not None else None)
        nbytes = data_cpu.numel() + (scales_cpu.numel() * scales_cpu.element_size()
                                     if scales_cpu is not None else 0)
        return ("comp", prec, data_cpu, scales_cpu, n, gs, cb.data.dtype, nbytes)

    def _decompress_page(self, payload: tuple, out_page_i8: torch.Tensor) -> None:
        """Reconstruct into out_page_i8 (a (page_size,) int8 GPU view)."""
        dev = out_page_i8.device
        if payload[0] == "raw":
            out_page_i8.copy_(payload[1].to(dev, non_blocking=True).view(torch.int8))
            return
        _, prec, data_cpu, scales_cpu, n, gs, data_dtype, _ = payload
        data = data_cpu.to(dev, non_blocking=True).view(data_dtype)
        scales = scales_cpu.to(dev, non_blocking=True) if scales_cpu is not None else None
        cb = CompressedBlock(
            precision=prec, data=data, scales=scales,
            shape=(n // gs, gs), dtype=self.kv_dtype, axis=-1, group_size=gs,
        )
        rec = decompress(cb).reshape(-1)             # (N,) model-dtype
        out_page_i8.view(self.kv_dtype).copy_(rec)

    # ---- OffloadingHandler interface ----

    def transfer_async(self, job_id: int, spec: TransferSpec) -> bool:
        src_spec, dst_spec = spec
        if self.gpu_to_cpu:
            gpu_spec, cpu_spec = src_spec, dst_spec
        else:
            cpu_spec, gpu_spec = src_spec, dst_spec
        assert isinstance(gpu_spec, GPULoadStoreSpec)

        gpu_ids = np.asarray(gpu_spec.block_ids).tolist()
        cpu_ids = np.asarray(cpu_spec.block_ids).tolist()
        # factor==1, full-attention: GPU and CPU blocks align 1:1 (see scheduler).
        assert len(gpu_ids) == len(cpu_ids), (
            f"precision handler needs 1:1 block alignment (factor==1); "
            f"got {len(gpu_ids)} gpu vs {len(cpu_ids)} cpu")
        precisions = getattr(cpu_spec, "precisions", None)

        # GPU->CPU reads the live KV cache; make sure compute has landed.
        if self.gpu_to_cpu and gpu_ids:
            self._sync()

        total_bytes = 0
        for i, (gbid, cbid) in enumerate(zip(gpu_ids, cpu_ids)):
            prec = (_CODE_PREC.get(int(precisions[i]), Precision.FP16)
                    if precisions is not None else Precision.FP16)
            if self.gpu_to_cpu:
                payloads = []
                nbytes = 0
                fp16_equiv = 0
                for t in self.gpu_tensors:
                    page = t[gbid]
                    p = self._compress_page(page, prec)
                    payloads.append(p)
                    nbytes += p[-1]
                    fp16_equiv += page.numel()
                self.region.put(cbid, _StoredBlock(payloads, nbytes), fp16_equiv)
                total_bytes += nbytes
            else:
                sb = self.region.get(cbid)
                if sb is None:
                    continue  # nothing stored (e.g. dropped) — leave GPU page as-is
                fp16_equiv = 0
                for t, payload in zip(self.gpu_tensors, sb.payloads):
                    self._decompress_page(payload, t[gbid])
                    fp16_equiv += t[gbid].numel()
                self.region.note_reload(sb.nbytes, fp16_equiv)
                total_bytes += sb.nbytes
        if not self.gpu_to_cpu and gpu_ids:
            self._sync()

        # emit the live physical footprint so the smoke can scrape it (worker-side;
        # the scheduler manager has a separate spec instance and cannot see it).
        if self.gpu_to_cpu and gpu_ids:
            logger.warning("CD_PHYSICAL_STATS %s", json.dumps(self.region.report()))

        self._finished.append(TransferResult(
            job_id=job_id, success=True, transfer_size=total_bytes,
            transfer_time=0.0, transfer_type=self.transfer_type,
        ))
        return True

    def get_finished(self) -> list[TransferResult]:
        out = self._finished
        self._finished = []
        return out

    def wait(self, job_ids: set[int]) -> None:
        return  # synchronous: already complete

    def shutdown(self) -> None:
        self._finished.clear()


class PrecisionCompressedHandlers:
    """Builds the GPU->CPU (store) and CPU->GPU (load) compressed handlers,
    sharing one CompressedSideRegion and the live GPU KV tensors. NO fixed pinned
    pool is allocated — that is the physical DRAM saving."""

    def __init__(self, kv_caches: CanonicalKVCaches, kv_dtype: torch.dtype):
        self.region = CompressedSideRegion()
        gpu_tensors = [t.tensor for t in kv_caches.tensors]
        for gt in gpu_tensors:
            assert gt.dtype == torch.int8 and gt.ndim == 2
        self.gpu_to_cpu_handler = PrecisionOffloadingHandler(
            gpu_tensors, self.region, kv_dtype, gpu_to_cpu=True)
        self.cpu_to_gpu_handler = PrecisionOffloadingHandler(
            gpu_tensors, self.region, kv_dtype, gpu_to_cpu=False)
