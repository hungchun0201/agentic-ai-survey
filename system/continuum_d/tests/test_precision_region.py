# SPDX-License-Identifier: Apache-2.0
"""CPU-only unit tests for the PHYSICAL compressed side-region + worker handler.

Simulates the worker's KV tensors as CPU int8 tensors (device-agnostic handler),
proving: store -> corrupt-GPU -> reload genuinely reconstructs the KV from the
compact host payload, the resident host bytes are physically smaller than an
fp16 pool, and the joint|decoupled|fp16 precision code routes correctly.

Run: PYTHONPATH=<agent-kvcache>/.pylib python -m pytest continuum_d/tests/ -q
"""
import numpy as np
import torch

from vllm.v1.kv_offload.base import CanonicalKVCacheTensor, CanonicalKVCaches, GPULoadStoreSpec

from continuum_d.codec import Precision
from continuum_d.precision_region import (
    PrecisionCompressedHandlers,
    PrecisionCPULoadStoreSpec,
    precision_code,
)

NUM_BLOCKS = 16
PAGE_BYTES = 4096  # 2048 fp16 elems/block/tensor
N_TENSORS = 2      # e.g. K and V canonical tensors


def _fake_kv(seed=0):
    g = torch.Generator().manual_seed(seed)
    tensors = []
    for _ in range(N_TENSORS):
        # realistic small KV values as fp16, viewed as the int8 page tensor
        fp16 = (torch.randn(NUM_BLOCKS, PAGE_BYTES // 2, generator=g) * 2).to(torch.float16)
        t = fp16.view(torch.int8).contiguous()
        tensors.append(CanonicalKVCacheTensor(tensor=t, page_size_bytes=PAGE_BYTES))
    return CanonicalKVCaches(tensors=tensors, group_data_refs=[[]])


def _gpu_spec(block_ids):
    return GPULoadStoreSpec(list(block_ids), group_sizes=[len(block_ids)],
                            block_indices=[0])


def _roundtrip(precision: Precision):
    kv = _fake_kv()
    orig = [t.tensor.clone() for t in kv.tensors]
    handlers = PrecisionCompressedHandlers(kv, kv_dtype=torch.float16)

    gpu_ids = [1, 3, 5, 7]
    cpu_ids = [1, 3, 5, 7]  # 1:1 slot mapping
    codes = [precision_code(precision)] * len(gpu_ids)
    store_spec = (_gpu_spec(gpu_ids), PrecisionCPULoadStoreSpec(cpu_ids, codes))
    assert handlers.gpu_to_cpu_handler.transfer_async(0, store_spec)
    assert len(handlers.gpu_to_cpu_handler.get_finished()) == 1

    # CORRUPT the GPU pages so a successful reload must come from the host store
    for t in kv.tensors:
        for b in gpu_ids:
            t.tensor[b].zero_()

    load_spec = (PrecisionCPULoadStoreSpec(cpu_ids, codes), _gpu_spec(gpu_ids))
    assert handlers.cpu_to_gpu_handler.transfer_async(1, load_spec)
    assert len(handlers.cpu_to_gpu_handler.get_finished()) == 1

    # reconstructed pages match the originals within the codec's error bound
    errs = []
    for t, o in zip(kv.tensors, orig):
        for b in gpu_ids:
            rec = t.tensor[b].view(torch.float16).float()
            ref = o[b].view(torch.float16).float()
            errs.append(((rec - ref).norm() / ref.norm().clamp(min=1e-6)).item())
    return handlers.gpu_to_cpu_handler.region, max(errs)


def test_fp16_roundtrip_is_lossless_and_full_size():
    region, max_err = _roundtrip(Precision.FP16)
    assert max_err < 1e-3, max_err  # raw store is lossless
    # fp16 stores full bytes: peak ~ fp16-equivalent (ratio ~1)
    assert 0.95 <= region.report()["peak_vs_fp16_equiv_ratio"] <= 1.05


def test_fp8_physically_smaller_and_reload_correct():
    region, max_err = _roundtrip(Precision.FP8)
    rep = region.report()
    assert rep["peak_vs_fp16_equiv_ratio"] < 0.65, rep   # physically ~half
    assert rep["reload_pcie_ratio"] < 0.65, rep          # less PCIe on reload
    assert max_err < 0.10, max_err                        # reload reconstructs KV


def test_int4_physically_smallest_and_reload_correct():
    region, max_err = _roundtrip(Precision.INT4)
    rep = region.report()
    assert rep["peak_vs_fp16_equiv_ratio"] < 0.40, rep   # physically ~quarter
    assert rep["reload_pcie_ratio"] < 0.40, rep
    assert max_err < 0.25, max_err


def test_missing_slot_on_load_is_a_noop():
    kv = _fake_kv()
    handlers = PrecisionCompressedHandlers(kv, kv_dtype=torch.float16)
    # load a slot that was never stored (e.g. dropped block) -> must not crash
    load_spec = (PrecisionCPULoadStoreSpec([2], [precision_code(Precision.INT4)]),
                 _gpu_spec([2]))
    assert handlers.cpu_to_gpu_handler.transfer_async(9, load_spec)


def test_precision_code_roundtrip():
    for p in (Precision.FP16, Precision.FP8, Precision.INT4):
        arr = np.asarray([precision_code(p)], dtype=np.int8)
        assert PrecisionCPULoadStoreSpec([0], arr).precisions[0] == precision_code(p)
