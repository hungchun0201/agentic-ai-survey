# SPDX-License-Identifier: Apache-2.0
"""MoriProxyCachePolicy: the honest observed-idleness baseline for Continuum-D E2.

Faithful proxy of MORI ("Idleness is Relative", arXiv 2606.00866) implemented
through the SAME v0.23 #37874 CachePolicy seam as JobAwareCachePolicy, so the
head-to-head isolates the *signal* (observed idleness vs exact client tags), not
the plumbing.

What it uses (exactly what an idleness ranker can see):
  * per-block LAST-ACCESS timestamps (set on insert, refreshed on touch), and
  * per-block OBSERVED reuse cadence (EWMA of inter-touch gaps).
Eviction ranks by RELATIVE idleness  rel = idle / cadence  (the "idleness is
relative" insight): a block idle far beyond its own rhythm is evicted before a
slow-rhythm block idle within its rhythm — strictly stronger than plain LRU.
A per-tier admission gate refuses new stores when OBSERVED-ACTIVE residency
(blocks accessed within ACTIVE_WINDOW_FACTOR x cadence) would exceed capacity,
mirroring MORI's tiered admission with observation instead of tags.

What it CANNOT use (the exact client lifecycle metadata Continuum-D adds):
  * last_turn  -> it never learns a job is dead at the instant its last turn
    completes; it must WAIT to observe ~one missed cadence of idleness before a
    dead job's blocks rank evictable / leave the active window. That reclaim lag
    is the honest gap the E2 novelty gate measures.
  * expected_gap -> it can only ESTIMATE the next wakeup from observed history,
    never read the exact gap the client already knows.

The manager forwards NO kv_transfer_params into this policy (see spec.py):
every decision here is a pure function of observed access timestamps.
"""

import time
from collections import OrderedDict
from collections.abc import Iterable

from vllm.v1.kv_offload.base import OffloadKey
from vllm.v1.kv_offload.cpu.policies.base import BlockStatus, CachePolicy


class MoriProxyCachePolicy(CachePolicy):
    """Observed-relative-idleness eviction + observed-active admission."""

    EWMA_ALPHA = 0.5          # inter-touch gap EWMA responsiveness
    GAP_FLOOR_MS = 50.0       # cadence floor (avoids div-by-zero / sub-step noise)
    DEFAULT_PRIOR_MS = 1000.0 # generic cold-start cadence; converges to observed
    ACTIVE_WINDOW_FACTOR = 3.0  # observed-active = idle < FACTOR x global cadence

    def __init__(self, cache_capacity: int):
        self.blocks: OrderedDict[OffloadKey, BlockStatus] = OrderedDict()
        self.capacity = cache_capacity
        self._last_access_ms: dict[OffloadKey, float] = {}
        self._ewma_gap_ms: dict[OffloadKey, float] = {}  # only for touched blocks
        self._global_gap_ms: float = self.DEFAULT_PRIOR_MS
        self.stats = {
            "evicted_total": 0,
            "evicted_stale": 0,   # rel >= 1 : idle beyond own cadence (observed-dead)
            "evicted_fresh": 0,   # rel <  1 : forced eviction of still-live-rhythm KV
            "admission_refusals": 0,
        }

    # ---- CachePolicy interface ----

    def get(self, key: OffloadKey) -> BlockStatus | None:
        return self.blocks.get(key)

    def insert(self, key: OffloadKey, block: BlockStatus) -> None:
        self.blocks[key] = block
        self._last_access_ms[key] = time.monotonic() * 1000.0
        # no observed interval yet -> falls back to the global cadence prior

    def remove(self, key: OffloadKey) -> None:
        del self.blocks[key]
        self._last_access_ms.pop(key, None)
        self._ewma_gap_ms.pop(key, None)

    def touch(self, keys: Iterable[OffloadKey]) -> None:
        now = time.monotonic() * 1000.0
        for key in reversed(list(keys)):
            if key not in self.blocks:
                continue
            prev = self._last_access_ms.get(key)
            if prev is not None:
                gap = now - prev
                if gap > 0:
                    ew = self._ewma_gap_ms.get(key)
                    self._ewma_gap_ms[key] = (
                        gap if ew is None
                        else self.EWMA_ALPHA * gap + (1 - self.EWMA_ALPHA) * ew
                    )
                    self._global_gap_ms = (
                        self.EWMA_ALPHA * gap
                        + (1 - self.EWMA_ALPHA) * self._global_gap_ms
                    )
            self._last_access_ms[key] = now
            self.blocks.move_to_end(key)  # keep base order = recency (LRU tiebreak)

    def clear(self) -> None:
        self.blocks.clear()
        self._last_access_ms.clear()
        self._ewma_gap_ms.clear()
        self._global_gap_ms = self.DEFAULT_PRIOR_MS

    # ---- observed signals ----

    def _cadence_ms(self, key: OffloadKey) -> float:
        """Observed reuse cadence for a block: own EWMA, else global prior."""
        typ = self._ewma_gap_ms.get(key)
        if typ is None:
            typ = self._global_gap_ms
        return max(typ, self.GAP_FLOOR_MS)

    def _rel_idle(self, key: OffloadKey, now_ms: float) -> float:
        idle = now_ms - self._last_access_ms.get(key, now_ms)
        return idle / self._cadence_ms(key)

    def observed_active_resident(self) -> int:
        """Blocks accessed within FACTOR x global cadence (observed 'live')."""
        now = time.monotonic() * 1000.0
        window = self.ACTIVE_WINDOW_FACTOR * max(self._global_gap_ms,
                                                 self.GAP_FLOOR_MS)
        n = 0
        for key in self.blocks:
            if now - self._last_access_ms.get(key, now) <= window:
                n += 1
        return n

    def admit_observed(self, n_new: int) -> bool:
        """Anti-thrash gate using OBSERVED-active residency (no client tags)."""
        if self.observed_active_resident() + n_new > self.capacity:
            self.stats["admission_refusals"] += 1
            return False
        return True

    # ---- eviction: rank by relative idleness (most-evictable = highest rel) ----

    def evict(
        self, n: int, protected: set[OffloadKey]
    ) -> list[tuple[OffloadKey, BlockStatus]] | None:
        if n == 0:
            return []
        now_ms = time.monotonic() * 1000.0
        candidates: list[tuple[float, float, int, OffloadKey, BlockStatus]] = []
        for order_idx, (key, block) in enumerate(self.blocks.items()):
            if block.ref_cnt != 0 or key in protected:
                continue
            rel = self._rel_idle(key, now_ms)
            idle = now_ms - self._last_access_ms.get(key, now_ms)
            # sort key: highest rel first, then most-idle, then oldest base order.
            candidates.append((-rel, -idle, order_idx, key, block))
        if len(candidates) < n:
            return None
        candidates.sort()
        chosen = candidates[:n]
        result = []
        for neg_rel, _, _, key, block in chosen:
            self.stats["evicted_total"] += 1
            if -neg_rel >= 1.0:
                self.stats["evicted_stale"] += 1
            else:
                self.stats["evicted_fresh"] += 1
            del self.blocks[key]
            self._last_access_ms.pop(key, None)
            self._ewma_gap_ms.pop(key, None)
            result.append((key, block))
        return result
