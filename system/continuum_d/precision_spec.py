# SPDX-License-Identifier: Apache-2.0
"""Out-of-tree OffloadingSpec wiring the JOINT precision+residency scheduler into
vLLM v0.23.x -- precision becomes an offload action inside the existing #37874
CachePolicy seam, with NO vLLM source changes and NO mixed-precision attention.

Usage (co-design / joint):
  --kv-transfer-config '{"kv_connector":"OffloadingConnector","kv_role":"kv_both",
    "kv_connector_extra_config":{
        "spec_name":"PrecisionOffloadingSpec",
        "spec_module_path":"continuum_d.precision_spec",
        "cpu_bytes_to_use": <bytes>,
        "precision_mode":"joint",              # joint | decoupled | fp16
        "accuracy_profile":"literature_pessimistic",
        "admission_control": true}}'

The DECOUPLED baseline (the load-bearing comparison) is the SAME spec with
"precision_mode":"decoupled" -- precision fixed offline by the static per-role
bitwidth map, residency scheduled independently. One flag, same harness.

Requests opt in via kv_transfer_params; the precision policy additionally reads:
  {"job_id","turn_idx","expected_gap_ms","last_turn","role","reuse_prob"}
where `role` in {system,tool_call,tool_result,reasoning,user,filler} and
`reuse_prob` in [0,1] is the client's estimate that this turn's KV is read again.

--- HONEST SCOPE (the v0.23 offload seam) --------------------------------------
The precision DECISION and the DRAM byte-budget ACCOUNTING run live in the
scheduler-side manager here (real, per-block, logged as CD_PRECISION_STATS).
The *physical* byte compression -- routing the fp8/int4 payload through the
worker's GPU<->CPU DMA so the pinned CPU pool is physically smaller -- is a
worker-handler change (SingleDirectionOffloadingHandler is a fixed-stride,
pre-allocated, raw-pointer batched-DMA path with no variable-size-payload seam).
The codec that does that compression is proven physically + measured standalone
in continuum_d/codec.py (compress->store->dequant round-trip on real KV blocks);
threading it through the worker DMA is the eval-harness integration (EVAL_PLAN).
So: the mechanism (precision as a live per-block admission action + its DRAM
accounting) runs end-to-end in the engine; the physical pinned-pool shrink is
the one deferred seam, called out honestly rather than faked.
"""

import json
import logging
from typing import Any

from vllm.v1.kv_offload.base import (
    CanonicalKVCaches,
    GPULoadStoreSpec,
    PrepareStoreOutput,
    ReqContext,
)
from vllm.v1.kv_offload.cpu.spec import CPUOffloadingSpec

from continuum_d.precision_policy import PrecisionAwareCachePolicy
from continuum_d.precision_region import (
    PrecisionCompressedHandlers,
    PrecisionCPULoadStoreSpec,
    precision_code,
)
from continuum_d.spec import JobAwareOffloadingManager

logger = logging.getLogger("continuum_d")


def _params(req_context: ReqContext) -> dict[str, Any] | None:
    p = getattr(req_context, "kv_transfer_params", None)
    return p if isinstance(p, dict) else None


class PrecisionOffloadingManager(JobAwareOffloadingManager):
    """JobAwareOffloadingManager whose policy also chooses KV PRECISION per block.

    Reuses all of the base admission/eviction plumbing; the only additions are
    (1) swapping in PrecisionAwareCachePolicy and (2) assigning a precision action
    to each finished-turn block at store time, with live DRAM byte accounting.
    """

    def __init__(self, *args, precision_mode: str = "joint",
                 accuracy_profile: str = "literature_pessimistic",
                 role_bitmap: dict[str, str] | None = None,
                 kv_bytes_per_block: int = 0,
                 admission_control: bool = True, exact_tags: bool = True,
                 **kwargs):
        # base __init__ builds a JobAwareCachePolicy; we replace it below so the
        # precision policy owns the same block budget.
        super().__init__(*args, admission_control=admission_control,
                         exact_tags=exact_tags, **kwargs)
        self.precision_mode = precision_mode
        # fp16 KV elements per offloaded block (bytes / 2) for byte accounting.
        self._block_nelem = max(int(kv_bytes_per_block) // 2, 1)
        self._policy = PrecisionAwareCachePolicy(
            cache_capacity=self._num_blocks,
            precision_mode=precision_mode,
            accuracy_profile=accuracy_profile,
            role_bitmap=role_bitmap,
            exact_tags=exact_tags,
        )
        self._num_evictable_cache_blocks = 0

    def prepare_store(self, keys, req_context: ReqContext) -> PrepareStoreOutput | None:
        params = _params(req_context)
        job_id = self._policy.note_request(params)
        keys = list(keys)
        if self.admission_control:
            new_keys = [k for k in keys if self._policy.get(k) is None]
            if new_keys and not self._policy.admit(job_id, len(new_keys)):
                return None
        # base CPUOffloadingManager machinery (allocate slots, evict, insert)
        # NOTE: the base CPUOffloadingManager.prepare_store builds the store_spec
        # via self._get_load_store_spec(...) BEFORE returning, and our override of
        # that method assigns each block's precision there (so the precision code
        # is already baked into the PrecisionCPULoadStoreSpec that flows to the
        # worker). Here we only add the job-grouping bookkeeping for eviction.
        out = super(JobAwareOffloadingManager, self).prepare_store(keys, req_context)
        if out is not None and out.keys_to_store:
            self._policy.tag_keys(out.keys_to_store, job_id)
        return out

    def _get_load_store_spec(self, keys, blocks):
        """Emit a precision-carrying CPU spec. On the STORE path a block's
        precision may be unassigned yet, so assign it here (precision-as-admission-
        action, jointly with residency, using live role/reuse/pressure); on the
        LOAD path the precision was fixed at store time and is looked up."""
        keys = list(keys)
        blocks = list(blocks)
        codes: list[int] = []
        for key, block in zip(keys, blocks):
            prec = self._policy._key_prec.get(key)
            if prec is None:
                prec = self._policy.assign(key, self._block_nelem).precision
            codes.append(precision_code(prec))
        return PrecisionCPULoadStoreSpec(
            [block.block_id for block in blocks], codes
        )

    def on_request_finished(self, req_context: ReqContext) -> None:
        # emit BOTH the base job-aware counters and the precision report so the
        # smoke/eval can scrape the live per-block precision decisions + the
        # DRAM byte accounting (capacity gain) straight from the engine log.
        if self.exact_tags:
            params = _params(req_context)
            if params and params.get("last_turn"):
                jid = params.get("job_id")
                self._policy.mark_job_finished(str(jid) if jid is not None else None)
        logger.warning("CD_POLICY_STATS %s", json.dumps(self._policy.stats))
        logger.warning("CD_PRECISION_STATS %s",
                       json.dumps(self._policy.precision_report()))
        super(JobAwareOffloadingManager, self).on_request_finished(req_context)

    def precision_stats(self) -> dict:
        return self._policy.precision_report()


class PrecisionOffloadingSpec(CPUOffloadingSpec):
    """CPUOffloadingSpec that installs the PrecisionOffloadingManager.

    `precision_mode` (joint|decoupled|fp16) is read from extra_config so the
    co-design and the decoupled baseline run through one spec, one flag.
    """

    def get_handlers(self, kv_caches: CanonicalKVCaches):
        """Return the PHYSICAL compressed handlers (compress-on-offload /
        dequant-on-reload) instead of the stock fixed-stride pinned-pool DMA.

        No `(num_cpu_blocks, cpu_page_size)` pinned pool is allocated — the host
        holds only the compact compressed payloads, so DRAM is PHYSICALLY smaller.
        Set extra_config physical_compression=false to fall back to the stock
        (accounting-only) handlers.
        """
        if not bool(self.extra_config.get("physical_compression", True)):
            yield from super().get_handlers(kv_caches)
            return
        if getattr(self, "_prec_handlers", None) is None:
            kv_dtype = self.vllm_config.model_config.dtype
            self._prec_handlers = PrecisionCompressedHandlers(kv_caches, kv_dtype)
            logger.warning(
                "PrecisionOffloadingSpec: PHYSICAL compressed side-region active "
                "(no pinned pool; kv_dtype=%s, tensors=%d)",
                kv_dtype, len(kv_caches.tensors),
            )
        h = self._prec_handlers
        yield GPULoadStoreSpec, PrecisionCPULoadStoreSpec, h.gpu_to_cpu_handler
        yield PrecisionCPULoadStoreSpec, GPULoadStoreSpec, h.cpu_to_gpu_handler

    def get_manager(self):
        base = super().get_manager()
        mgr = PrecisionOffloadingManager(
            num_blocks=base._num_blocks,
            enable_events=base.events is not None,
            precision_mode=str(self.extra_config.get("precision_mode", "joint")),
            accuracy_profile=str(
                self.extra_config.get("accuracy_profile", "literature_pessimistic")
            ),
            role_bitmap=self.extra_config.get("role_bitmap"),
            kv_bytes_per_block=int(self.kv_bytes_per_offloaded_block),
            admission_control=bool(self.extra_config.get("admission_control", True)),
            exact_tags=bool(self.extra_config.get("exact_tags", True)),
        )
        logger.warning(
            "PrecisionOffloadingSpec ready: mode=%s blocks=%d bytes/block=%d",
            mgr.precision_mode, base._num_blocks, self.kv_bytes_per_offloaded_block,
        )
        return mgr
