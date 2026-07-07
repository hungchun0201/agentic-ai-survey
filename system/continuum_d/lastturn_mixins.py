"""Signal-matched baselines: {Marconi, MORI-proxy, Continuum-TTL} + last_turn reclaim.

Cold-gate fairness grid: every baseline family gets the same one-bit session-end
signal Tenure uses (blocks of client-declared-finished sessions evict first),
keeping each policy's own ordering otherwise. No admission gate anywhere here.
"""
from __future__ import annotations

from vllm.v1.kv_offload.base import OffloadKey
from vllm.v1.kv_offload.cpu.policies.base import BlockStatus

from continuum_d.marconi_policy import MarconiUtilCachePolicy
from continuum_d.mori_policy import MoriProxyCachePolicy
from continuum_d.continuum_ttl_policy import ContinuumTTLCachePolicy


class _LastTurnMixin:
    """Track job ids + finished set from kv_transfer_params; class-0 evict."""

    def _lt_init(self):
        self._lt_key_job: dict[OffloadKey, str] = {}
        self._lt_finished: set[str] = set()
        self._lt_current: str | None = None
        self.stats.setdefault("evicted_finished", 0)

    def _lt_note(self, params: dict | None) -> None:
        p = params or {}
        job = p.get("job_id")
        self._lt_current = str(job) if job is not None else None
        if self._lt_current is not None and p.get("last_turn"):
            self._lt_finished.add(self._lt_current)

    def _lt_tag(self, key: OffloadKey) -> None:
        if self._lt_current is not None:
            self._lt_key_job[key] = self._lt_current

    def _lt_finished_key(self, key: OffloadKey) -> bool:
        job = self._lt_key_job.get(key)
        return job is not None and job in self._lt_finished

    def evict(self, n: int, protected: set[OffloadKey]):
        if n == 0:
            return []
        # take finished-session blocks first, then defer to the base ordering
        fin = [(k, b) for k, b in self.blocks.items()
               if b.ref_cnt == 0 and k not in protected and self._lt_finished_key(k)]
        if len(fin) >= n:
            out = fin[:n]
            for k, _ in out:
                self.stats["evicted_finished"] += 1
                self.remove(k)
            return out
        rest = super().evict(n - len(fin), protected | {k for k, _ in fin})
        if rest is None:
            return None
        for k, _ in fin:
            self.stats["evicted_finished"] += 1
            self.remove(k)
        return fin + rest


class MarconiLTCachePolicy(_LastTurnMixin, MarconiUtilCachePolicy):
    def __init__(self, cache_capacity: int):
        super().__init__(cache_capacity)
        self._lt_init()

    def note_request(self, params):
        base_nr = getattr(super(), "note_request", None)
        r = base_nr(params) if callable(base_nr) else None
        self._lt_note(params)
        return r

    def insert(self, key, block):
        super().insert(key, block)
        self._lt_tag(key)


class MoriLTCachePolicy(_LastTurnMixin, MoriProxyCachePolicy):
    def __init__(self, cache_capacity: int):
        super().__init__(cache_capacity)
        self._lt_init()

    def note_request(self, params):
        base_nr = getattr(super(), "note_request", None)
        r = base_nr(params) if callable(base_nr) else None
        self._lt_note(params)
        return r

    def insert(self, key, block):
        super().insert(key, block)
        self._lt_tag(key)


class TTLLTCachePolicy(_LastTurnMixin, ContinuumTTLCachePolicy):
    def __init__(self, cache_capacity: int):
        super().__init__(cache_capacity)
        self._lt_init()

    def note_request(self, params):
        r = super().note_request(params)
        self._lt_note(params)
        return r

    def insert(self, key, block):
        super().insert(key, block)
        self._lt_tag(key)
