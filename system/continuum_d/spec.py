# SPDX-License-Identifier: Apache-2.0
"""Out-of-tree OffloadingSpec wiring JobAwareCachePolicy into vLLM v0.23.x.

Usage (no vLLM source changes):
  --kv-transfer-config '{"kv_connector":"OffloadingConnector","kv_role":"kv_both",
    "kv_connector_extra_config":{
        "spec_name":"JobAwareOffloadingSpec",
        "spec_module_path":"continuum_d.spec",
        "cpu_bytes_to_use": <bytes>,
        "admission_control": true}}'

Requests opt in by sending kv_transfer_params:
  {"job_id": "...", "turn_idx": N, "expected_gap_ms": 8000, "last_turn": false}
"""

import json
import os
import logging
from typing import Any

from vllm.v1.kv_offload.base import (
    LoadStoreSpec,
    OffloadKey,
    PrepareStoreOutput,
    ReqContext,
)
from vllm.v1.kv_offload.cpu.manager import CPUOffloadingManager
from vllm.v1.kv_offload.cpu.spec import CPUOffloadingSpec

from continuum_d.policy import JobAwareCachePolicy
from continuum_d.mori_policy import MoriProxyCachePolicy
from continuum_d.marconi_policy import MarconiUtilCachePolicy
from continuum_d.continuum_ttl_policy import ContinuumTTLCachePolicy
from continuum_d.lru_lastturn_policy import LRULastTurnCachePolicy
from continuum_d.gated_ttl_policy import GatedTTLCachePolicy
from continuum_d.lastturn_mixins import (MarconiLTCachePolicy, MoriLTCachePolicy,
                                         TTLLTCachePolicy)
from continuum_d.tinylfu_policy import TinyLFUAdmCachePolicy

logger = logging.getLogger("continuum_d")


def _params(req_context: ReqContext) -> dict[str, Any] | None:
    p = getattr(req_context, "kv_transfer_params", None)
    return p if isinstance(p, dict) else None


class JobAwareOffloadingManager(CPUOffloadingManager):
    """CPUOffloadingManager that forwards request context to the policy.

    This is the out-of-tree equivalent of the RFC #45405 plumbing
    (touch/prepare_store carrying ReqContext down into the CachePolicy).
    """

    def __init__(self, *args, admission_control: bool = True,
                 exact_tags: bool = True, **kwargs):
        super().__init__(*args, **kwargs)
        # replace whatever policy the base chose with the job-aware one.
        # exact_tags=False => E2 metadata-off ablation (last_turn/expected_gap
        # blinded at the policy boundary; see policy.py).
        self.exact_tags = exact_tags
        self._policy = JobAwareCachePolicy(
            cache_capacity=self._num_blocks, exact_tags=exact_tags)
        self._num_evictable_cache_blocks = 0
        self.admission_control = admission_control
        # CD_GATE_BYPASS_FREE=1: unpressured fast path — while the tier has
        # never been within 5% of capacity, skip ALL policy forwarding (pure
        # base-manager behavior). The gate re-engages permanently the first
        # time occupancy crosses the threshold. Evaluated at DRAM >= WS.
        self._bypass_free = os.environ.get("CD_GATE_BYPASS_FREE", "0") == "1"
        self._pressured = False

    def _unpressured(self) -> bool:
        if not self._bypass_free or self._pressured:
            return False
        if len(self._policy.blocks) >= 0.95 * self._policy.capacity:
            self._pressured = True
            return False
        return True

    # -- context forwarding --

    def lookup(self, key: OffloadKey, req_context: ReqContext):
        if not self._unpressured():
            self._policy.note_request(_params(req_context))
        return super().lookup(key, req_context)

    def touch(self, keys, req_context: ReqContext) -> None:
        if not self._unpressured():
            self._policy.note_request(_params(req_context))
        super().touch(keys, req_context)

    def prepare_store(
        self, keys, req_context: ReqContext
    ) -> PrepareStoreOutput | None:
        if self._unpressured():
            return super().prepare_store(list(keys), req_context)
        params = _params(req_context)
        job_id = self._policy.note_request(params)
        keys = list(keys)
        if self.admission_control:
            new_keys = [k for k in keys if self._policy.get(k) is None]
            if new_keys and not self._policy.admit(job_id, len(new_keys)):
                # refuse: degrade to no-DRAM for this batch (anti-thrash)
                return None
        out = super().prepare_store(keys, req_context)
        if out is not None and out.keys_to_store:
            self._policy.tag_keys(out.keys_to_store, job_id)
        return out

    def on_request_finished(self, req_context: ReqContext) -> None:
        # last_turn dead-KV reclaim is an EXACT-tag path: only the full policy
        # reads it. The ablation (exact_tags=False) never touches last_turn.
        if self.exact_tags:
            params = _params(req_context)
            if params and params.get("last_turn"):
                job_id = params.get("job_id")
                self._policy.mark_job_finished(
                    str(job_id) if job_id is not None else None
                )
        # emit cumulative stats every finished turn; the benchmark scrapes the
        # LAST line (admission_refusals + evicted_per_class are in-memory only,
        # not yet on /metrics). Decoupled from last_turn so the ablation emits.
        logger.warning("CD_POLICY_STATS %s", json.dumps(self._policy.stats))
        super().on_request_finished(req_context)

    # expose stats for the benchmark scrape
    def job_aware_stats(self) -> dict:
        return dict(self._policy.stats)


class JobAwareOffloadingSpec(CPUOffloadingSpec):
    def get_manager(self):
        base = super().get_manager()
        # rebuild with the same block budget but our manager class.
        # exact_tags is driven from extra_config so the SAME spec serves both
        # `job_aware` (exact_tags=True) and `job_aware_metadata_off`
        # (exact_tags=False, the E2 ablation) with no code divergence.
        mgr = JobAwareOffloadingManager(
            num_blocks=base._num_blocks,
            enable_events=base.events is not None,
            admission_control=bool(
                self.extra_config.get("admission_control", True)
            ),
            exact_tags=bool(self.extra_config.get("exact_tags", True)),
        )
        return mgr


class MoriProxyOffloadingManager(CPUOffloadingManager):
    """CPUOffloadingManager driving the observed-idleness MoriProxyCachePolicy.

    Deliberately forwards NO kv_transfer_params into the policy: every cache
    decision is a pure function of observed access timestamps. The only override
    beyond swapping the policy is an OBSERVED admission gate (no client tags).
    """

    def __init__(self, *args, admission_control: bool = True, **kwargs):
        super().__init__(*args, **kwargs)
        self._policy = MoriProxyCachePolicy(cache_capacity=self._num_blocks)
        self.admission_control = admission_control

    def prepare_store(
        self, keys, req_context: ReqContext
    ) -> PrepareStoreOutput | None:
        keys = list(keys)
        if self.admission_control:
            new_keys = [k for k in keys if self._policy.get(k) is None]
            if new_keys and not self._policy.admit_observed(len(new_keys)):
                # refuse: degrade to no-DRAM for this batch (anti-thrash)
                return None
        return super().prepare_store(keys, req_context)

    def on_request_finished(self, req_context: ReqContext) -> None:
        # emit cumulative stats every finished turn; scrape takes the last line.
        logger.warning("CD_POLICY_STATS %s", json.dumps(self._policy.stats))
        super().on_request_finished(req_context)

    def job_aware_stats(self) -> dict:
        return dict(self._policy.stats)


class MoriProxyOffloadingSpec(CPUOffloadingSpec):
    def get_manager(self):
        base = super().get_manager()
        return MoriProxyOffloadingManager(
            num_blocks=base._num_blocks,
            enable_events=base.events is not None,
            admission_control=bool(
                self.extra_config.get("admission_control", True)
            ),
        )


class MarconiUtilOffloadingManager(CPUOffloadingManager):
    """CPUOffloadingManager driving MarconiUtilCachePolicy (M2 baseline).

    Faithful to Marconi's scope: NO kv_transfer_params forwarded (no lifecycle
    signals), NO capacity admission gate (admit-everything, radix semantics) —
    eviction quality alone (recency + alpha*flop_efficiency) carries the policy.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._policy = MarconiUtilCachePolicy(cache_capacity=self._num_blocks)

    def on_request_finished(self, req_context: ReqContext) -> None:
        logger.warning("CD_POLICY_STATS %s", json.dumps(self._policy.stats))
        super().on_request_finished(req_context)

    def job_aware_stats(self) -> dict:
        return dict(self._policy.stats)


class MarconiUtilOffloadingSpec(CPUOffloadingSpec):
    def get_manager(self):
        base = super().get_manager()
        return MarconiUtilOffloadingManager(
            num_blocks=base._num_blocks,
            enable_events=base.events is not None,
        )


class ContinuumTTLOffloadingManager(CPUOffloadingManager):
    """Continuum/CacheTTL keep-resident baseline: TTL pin from expected_gap_ms.

    Forwards kv_transfer_params ONLY for the gap-TTL (same signal as job_aware,
    different mechanism: pin-until-TTL vs admission gate). No capacity gate.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._policy = ContinuumTTLCachePolicy(cache_capacity=self._num_blocks)

    def lookup(self, key: OffloadKey, req_context: ReqContext):
        self._policy.note_request(_params(req_context))
        return super().lookup(key, req_context)

    def touch(self, keys, req_context: ReqContext) -> None:
        self._policy.note_request(_params(req_context))
        super().touch(keys, req_context)

    def prepare_store(self, keys, req_context: ReqContext):
        self._policy.note_request(_params(req_context))
        return super().prepare_store(keys, req_context)

    def on_request_finished(self, req_context: ReqContext) -> None:
        logger.warning("CD_POLICY_STATS %s", json.dumps(self._policy.stats))
        super().on_request_finished(req_context)

    def job_aware_stats(self) -> dict:
        return dict(self._policy.stats)


class ContinuumTTLOffloadingSpec(CPUOffloadingSpec):
    def get_manager(self):
        base = super().get_manager()
        return ContinuumTTLOffloadingManager(
            num_blocks=base._num_blocks,
            enable_events=base.events is not None,
        )


class LRULastTurnOffloadingManager(CPUOffloadingManager):
    """Cold-gate ablation: plain LRU + last_turn instant reclaim, NO admission.

    Gives the LRU family the same session-end signal Tenure uses; isolates
    whether reclaim-on-finish alone (without the capacity gate) explains the win.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._policy = LRULastTurnCachePolicy(cache_capacity=self._num_blocks)

    def lookup(self, key: OffloadKey, req_context: ReqContext):
        self._policy.note_request(_params(req_context))
        return super().lookup(key, req_context)

    def touch(self, keys, req_context: ReqContext) -> None:
        self._policy.note_request(_params(req_context))
        super().touch(keys, req_context)

    def prepare_store(self, keys, req_context: ReqContext):
        self._policy.note_request(_params(req_context))
        return super().prepare_store(keys, req_context)

    def on_request_finished(self, req_context: ReqContext) -> None:
        logger.warning("CD_POLICY_STATS %s", json.dumps(self._policy.stats))
        super().on_request_finished(req_context)

    def job_aware_stats(self) -> dict:
        return dict(self._policy.stats)


class LRULastTurnOffloadingSpec(CPUOffloadingSpec):
    def get_manager(self):
        base = super().get_manager()
        return LRULastTurnOffloadingManager(
            num_blocks=base._num_blocks,
            enable_events=base.events is not None,
        )


class GatedTTLOffloadingManager(CPUOffloadingManager):
    """Fairness baseline: Tenure's admission gate + Continuum's TTL eviction."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._policy = GatedTTLCachePolicy(cache_capacity=self._num_blocks)

    def lookup(self, key: OffloadKey, req_context: ReqContext):
        self._policy.note_request(_params(req_context))
        return super().lookup(key, req_context)

    def touch(self, keys, req_context: ReqContext) -> None:
        self._policy.note_request(_params(req_context))
        super().touch(keys, req_context)

    def prepare_store(self, keys, req_context: ReqContext):
        job_id = self._policy.note_request(_params(req_context))
        keys = list(keys)
        new_keys = [k for k in keys if self._policy.get(k) is None]
        if new_keys and not self._policy.admit(job_id, len(new_keys)):
            return None
        out = super().prepare_store(keys, req_context)
        if out is not None and out.keys_to_store:
            self._policy.tag_keys(out.keys_to_store, job_id)
        return out

    def on_request_finished(self, req_context: ReqContext) -> None:
        logger.warning("CD_POLICY_STATS %s", json.dumps(self._policy.stats))
        super().on_request_finished(req_context)

    def job_aware_stats(self) -> dict:
        return dict(self._policy.stats)


class GatedTTLOffloadingSpec(CPUOffloadingSpec):
    def get_manager(self):
        base = super().get_manager()
        return GatedTTLOffloadingManager(
            num_blocks=base._num_blocks,
            enable_events=base.events is not None,
        )


class MarconiLTOffloadingManager(CPUOffloadingManager):
    """Signal-matched baseline: Marconi utility ordering + last_turn reclaim, no gate."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._policy = MarconiLTCachePolicy(cache_capacity=self._num_blocks)

    def lookup(self, key: OffloadKey, req_context: ReqContext):
        self._policy.note_request(_params(req_context))
        return super().lookup(key, req_context)

    def touch(self, keys, req_context: ReqContext) -> None:
        self._policy.note_request(_params(req_context))
        super().touch(keys, req_context)

    def prepare_store(self, keys, req_context: ReqContext):
        self._policy.note_request(_params(req_context))
        return super().prepare_store(keys, req_context)

    def on_request_finished(self, req_context: ReqContext) -> None:
        logger.warning("CD_POLICY_STATS %s", json.dumps(self._policy.stats))
        super().on_request_finished(req_context)

    def job_aware_stats(self) -> dict:
        return dict(self._policy.stats)


class MarconiLTOffloadingSpec(CPUOffloadingSpec):
    def get_manager(self):
        base = super().get_manager()
        return MarconiLTOffloadingManager(
            num_blocks=base._num_blocks,
            enable_events=base.events is not None,
        )


class MoriLTOffloadingManager(CPUOffloadingManager):
    """Signal-matched baseline: MORI-style idleness ordering + last_turn reclaim, no gate."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._policy = MoriLTCachePolicy(cache_capacity=self._num_blocks)

    def lookup(self, key: OffloadKey, req_context: ReqContext):
        self._policy.note_request(_params(req_context))
        return super().lookup(key, req_context)

    def touch(self, keys, req_context: ReqContext) -> None:
        self._policy.note_request(_params(req_context))
        super().touch(keys, req_context)

    def prepare_store(self, keys, req_context: ReqContext):
        self._policy.note_request(_params(req_context))
        return super().prepare_store(keys, req_context)

    def on_request_finished(self, req_context: ReqContext) -> None:
        logger.warning("CD_POLICY_STATS %s", json.dumps(self._policy.stats))
        super().on_request_finished(req_context)

    def job_aware_stats(self) -> dict:
        return dict(self._policy.stats)


class MoriLTOffloadingSpec(CPUOffloadingSpec):
    def get_manager(self):
        base = super().get_manager()
        return MoriLTOffloadingManager(
            num_blocks=base._num_blocks,
            enable_events=base.events is not None,
        )


class TTLLTOffloadingManager(CPUOffloadingManager):
    """Signal-matched baseline: Continuum-TTL pin ordering + last_turn reclaim, no gate."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._policy = TTLLTCachePolicy(cache_capacity=self._num_blocks)

    def lookup(self, key: OffloadKey, req_context: ReqContext):
        self._policy.note_request(_params(req_context))
        return super().lookup(key, req_context)

    def touch(self, keys, req_context: ReqContext) -> None:
        self._policy.note_request(_params(req_context))
        super().touch(keys, req_context)

    def prepare_store(self, keys, req_context: ReqContext):
        self._policy.note_request(_params(req_context))
        return super().prepare_store(keys, req_context)

    def on_request_finished(self, req_context: ReqContext) -> None:
        logger.warning("CD_POLICY_STATS %s", json.dumps(self._policy.stats))
        super().on_request_finished(req_context)

    def job_aware_stats(self) -> dict:
        return dict(self._policy.stats)


class TTLLTOffloadingSpec(CPUOffloadingSpec):
    def get_manager(self):
        base = super().get_manager()
        return TTLLTOffloadingManager(
            num_blocks=base._num_blocks,
            enable_events=base.events is not None,
        )


class TinyLFUOffloadingManager(CPUOffloadingManager):
    """Standard cache-admission baseline: TinyLFU frequency filter + LRU."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._policy = TinyLFUAdmCachePolicy(cache_capacity=self._num_blocks)

    def prepare_store(self, keys, req_context: ReqContext):
        keys = list(keys)
        new_keys = [k for k in keys if self._policy.get(k) is None]
        admitted = set(self._policy.freq_admit(new_keys)) if new_keys else set()
        keep = [k for k in keys if k in admitted or self._policy.get(k) is not None]
        if new_keys and not keep:
            return None
        return super().prepare_store(keep, req_context)

    def on_request_finished(self, req_context: ReqContext) -> None:
        logger.warning("CD_POLICY_STATS %s", json.dumps(self._policy.stats))
        super().on_request_finished(req_context)

    def job_aware_stats(self) -> dict:
        return dict(self._policy.stats)


class TinyLFUOffloadingSpec(CPUOffloadingSpec):
    def get_manager(self):
        base = super().get_manager()
        return TinyLFUOffloadingManager(
            num_blocks=base._num_blocks,
            enable_events=base.events is not None,
        )
