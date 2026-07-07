"""LRULastTurnCachePolicy: LRU + session-end reclaim, NO admission (cold-gate ablation).

Isolates how much of Tenure's win is explained by the last_turn signal alone:
plain LRU insert/touch/evict order, but blocks of sessions whose client sent
last_turn=True become eviction class 0 (reclaimed first). No capacity gate,
no expected-gap usage. If this baseline matched Tenure, the win would be
"session-end reclaim", not admission; measured against the full ladder it
answers the equal-hints fairness question for the LRU family.
"""
from __future__ import annotations

from collections import OrderedDict
from collections.abc import Iterable

from vllm.v1.kv_offload.base import OffloadKey
from vllm.v1.kv_offload.cpu.policies.base import BlockStatus, CachePolicy


class LRULastTurnCachePolicy(CachePolicy):
    """Plain LRU eviction; finished sessions' blocks evicted first."""

    def __init__(self, cache_capacity: int):
        self.capacity = cache_capacity
        self.blocks: OrderedDict[OffloadKey, BlockStatus] = OrderedDict()
        self._key_job: dict[OffloadKey, str] = {}
        self._finished: set[str] = set()
        self._current_job: str | None = None
        self.stats = {
            "evicted_finished": 0,
            "evicted_lru": 0,
            "admission_refusals": 0,  # always 0 (no gate)
        }

    # ---- context hook (manager forwards kv_transfer_params) ----
    def note_request(self, params: dict | None) -> None:
        p = params or {}
        job_id = p.get("job_id")
        self._current_job = str(job_id) if job_id is not None else None
        if self._current_job is not None and p.get("last_turn"):
            self._finished.add(self._current_job)

    # ---- CachePolicy interface ----
    def get(self, key: OffloadKey) -> BlockStatus | None:
        return self.blocks.get(key)

    def insert(self, key: OffloadKey, block: BlockStatus) -> None:
        self.blocks[key] = block
        if self._current_job is not None:
            self._key_job[key] = self._current_job

    def remove(self, key: OffloadKey) -> None:
        del self.blocks[key]
        self._key_job.pop(key, None)

    def touch(self, keys: Iterable[OffloadKey]) -> None:
        for key in reversed(list(keys)):
            if key in self.blocks:
                self.blocks.move_to_end(key)
                if self._current_job is not None:
                    self._key_job[key] = self._current_job

    def clear(self) -> None:
        self.blocks.clear()
        self._key_job.clear()
        self._finished.clear()

    # ---- eviction: finished-session blocks first, then plain LRU ----
    def evict(
        self, n: int, protected: set[OffloadKey]
    ) -> list[tuple[OffloadKey, BlockStatus]] | None:
        if n == 0:
            return []
        cand: list[tuple[int, int, OffloadKey, BlockStatus]] = []
        for order, (key, block) in enumerate(self.blocks.items()):
            if block.ref_cnt != 0 or key in protected:
                continue
            job = self._key_job.get(key)
            cls = 0 if (job is not None and job in self._finished) else 1
            cand.append((cls, order, key, block))
        if len(cand) < n:
            return None
        cand.sort(key=lambda t: (t[0], t[1]))
        out = []
        for cls, _, key, block in cand[:n]:
            self.stats["evicted_finished" if cls == 0 else "evicted_lru"] += 1
            out.append((key, block))
        for key, _ in out:
            self.remove(key)
        return out
