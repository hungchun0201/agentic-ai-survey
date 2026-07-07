"""TinyLFUAdmCachePolicy: standard frequency-based cache ADMISSION baseline.

W-TinyLFU-style admission (Einziger et al., TinyLFU: A Highly Efficient Cache
Admission Policy, ACM ToS 2017), transplanted to the KV offload tier: a
count-min sketch estimates each block key's access frequency; when the tier
is full, an incoming block is admitted only if its estimated frequency
exceeds the LRU victim's. This is THE standard admission baseline from the
caching literature; on the agent reference class it is predicted to fail
because first-touch blocks (every newly grown prefix block) have no
frequency history and cross-session frequency carries no signal about
within-session re-reads.
"""
from __future__ import annotations

import hashlib
from collections import OrderedDict
from collections.abc import Iterable

from vllm.v1.kv_offload.base import OffloadKey
from vllm.v1.kv_offload.cpu.policies.base import BlockStatus, CachePolicy


class _CountMinSketch:
    W = 4096
    D = 4

    def __init__(self):
        self.t = [[0] * self.W for _ in range(self.D)]
        self.total = 0

    def _idx(self, key, d):
        h = hashlib.blake2b(repr(key).encode(), digest_size=8,
                            salt=bytes([d])).digest()
        return int.from_bytes(h, "little") % self.W

    def add(self, key):
        for d in range(self.D):
            self.t[d][self._idx(key, d)] += 1
        self.total += 1
        if self.total >= 16 * self.W:  # periodic aging (halving), per TinyLFU
            for d in range(self.D):
                row = self.t[d]
                for i in range(self.W):
                    row[i] >>= 1
            self.total >>= 1

    def est(self, key):
        return min(self.t[d][self._idx(key, d)] for d in range(self.D))


class TinyLFUAdmCachePolicy(CachePolicy):
    """LRU eviction + TinyLFU frequency admission filter."""

    def __init__(self, cache_capacity: int):
        self.capacity = cache_capacity
        self.blocks: OrderedDict[OffloadKey, BlockStatus] = OrderedDict()
        self.sketch = _CountMinSketch()
        self.stats = {
            "admission_refusals": 0,
            "evicted_lru": 0,
        }

    def freq_admit(self, keys) -> list:
        """Return the subset of keys the TinyLFU filter admits."""
        if len(self.blocks) < self.capacity:
            for k in keys:
                self.sketch.add(k)
            return list(keys)
        victim = next(iter(self.blocks), None)
        vf = self.sketch.est(victim) if victim is not None else 0
        out = []
        for k in keys:
            self.sketch.add(k)
            if self.sketch.est(k) >= max(vf, 1):
                out.append(k)
            else:
                self.stats["admission_refusals"] += 1
        return out

    # ---- CachePolicy interface ----
    def get(self, key: OffloadKey) -> BlockStatus | None:
        if key in self.blocks:
            self.sketch.add(key)
        return self.blocks.get(key)

    def insert(self, key: OffloadKey, block: BlockStatus) -> None:
        self.blocks[key] = block

    def remove(self, key: OffloadKey) -> None:
        del self.blocks[key]

    def touch(self, keys: Iterable[OffloadKey]) -> None:
        for key in reversed(list(keys)):
            if key in self.blocks:
                self.blocks.move_to_end(key)
                self.sketch.add(key)

    def clear(self) -> None:
        self.blocks.clear()

    def evict(
        self, n: int, protected: set[OffloadKey]
    ) -> list[tuple[OffloadKey, BlockStatus]] | None:
        if n == 0:
            return []
        cand = [(k, b) for k, b in self.blocks.items()
                if b.ref_cnt == 0 and k not in protected]
        if len(cand) < n:
            return None
        out = cand[:n]
        for k, _ in out:
            self.stats["evicted_lru"] += 1
            self.remove(k)
        return out
