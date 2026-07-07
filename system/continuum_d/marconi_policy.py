"""MarconiUtilCachePolicy: faithful-at-block-granularity Marconi baseline (M2).

Marconi (MLSys'25, arXiv:2411.19379) evicts radix nodes by
    S(n) = recency(n) + alpha * flop_efficiency(n),
flop_efficiency = FLOPs-saved-on-hit / bytes-of-state, both min-max normalized;
alpha is grid-searched on a bootstrap window then frozen. Admission is
speculative-insertion at radix branch points (effectively admit-everything for
append-only agent flows — no capacity gate), GPU-cache-only, no session
lifecycle signals. Those scope limits are exactly what the M2 head-to-head
isolates against our lifecycle/admission gate.

Block-granularity transplant (documented approximation, stated in the paper):
- recency(n): normalized last-access recency of the block (as Marconi).
- flop_efficiency(n): a hit on a block at token-depth d saves recomputing that
  block's prefill AT depth d; attention FLOPs grow ~linearly in d while the
  block's bytes are constant -> flop_eff ∝ depth. We use depth_norm.
  (For pure-transformer KV all blocks are same-size, so this is the honest
  degenerate form of Marconi's ratio; for the M4 hybrid column the SSM-state
  blocks get their true fixed-size ratio and the term differentiates exactly
  as in the paper.)
- alpha: CD_MARCONI_ALPHA env (default 1.0); M2 protocol fits it on seed-0's
  bootstrap eviction window, then freezes for seeds 1-2 (mirrors Marconi).
"""
from __future__ import annotations

import os
import time
from collections import OrderedDict
from collections.abc import Iterable

from vllm.v1.kv_offload.base import OffloadKey
from vllm.v1.kv_offload.cpu.policies.base import BlockStatus, CachePolicy


class MarconiUtilCachePolicy(CachePolicy):
    """Recency + alpha*flop-efficiency eviction; admit-everything (Marconi scope)."""

    def __init__(self, cache_capacity: int):
        self.capacity = cache_capacity
        self.blocks: OrderedDict[OffloadKey, BlockStatus] = OrderedDict()
        self._last_access_ms: dict[OffloadKey, float] = {}
        self._depth: dict[OffloadKey, int] = {}   # insertion order ~ token depth
        self._ins_counter = 0
        self.alpha = float(os.environ.get("CD_MARCONI_ALPHA", "1.0"))
        self.stats = {
            "evicted_total": 0,
            "evicted_low_util": 0,   # score below median at eviction time
            "evicted_high_util": 0,  # forced eviction of high-utility blocks
            "admission_refusals": 0,  # always 0: Marconi has no capacity gate
        }

    # ---- CachePolicy interface ----
    def get(self, key: OffloadKey) -> BlockStatus | None:
        return self.blocks.get(key)

    def insert(self, key: OffloadKey, block: BlockStatus) -> None:
        self.blocks[key] = block
        now = time.monotonic() * 1000.0
        self._last_access_ms[key] = now
        self._ins_counter += 1
        # depth proxy: per-request monotone insertion order (prefix property:
        # deeper blocks of a sequence are inserted after shallower ones).
        self._depth[key] = self._ins_counter

    def remove(self, key: OffloadKey) -> None:
        del self.blocks[key]
        self._last_access_ms.pop(key, None)
        self._depth.pop(key, None)

    def touch(self, keys: Iterable[OffloadKey]) -> None:
        now = time.monotonic() * 1000.0
        for key in reversed(list(keys)):
            if key in self.blocks:
                self.blocks.move_to_end(key)
                self._last_access_ms[key] = now

    def clear(self) -> None:
        self.blocks.clear()
        self._last_access_ms.clear()
        self._depth.clear()

    # ---- eviction: lowest S(n) = recency_norm + alpha * depth_norm first ----
    def evict(
        self, n: int, protected: set[OffloadKey]
    ) -> list[tuple[OffloadKey, BlockStatus]] | None:
        if n == 0:
            return []
        now = time.monotonic() * 1000.0
        cand: list[tuple[float, OffloadKey, BlockStatus]] = []
        acc = [now - self._last_access_ms.get(k, now) for k in self.blocks]
        max_idle = max(acc) if acc else 1.0
        max_depth = max(self._depth.values()) if self._depth else 1
        scores = []
        for key, block in self.blocks.items():
            if block.ref_cnt != 0 or key in protected:
                continue
            idle = now - self._last_access_ms.get(key, now)
            recency_norm = 1.0 - (idle / max_idle if max_idle > 0 else 0.0)
            depth_norm = self._depth.get(key, 0) / max_depth
            s = recency_norm + self.alpha * depth_norm
            scores.append(s)
            cand.append((s, key, block))
        if len(cand) < n:
            return None
        cand.sort(key=lambda t: t[0])  # lowest utility evicted first
        med = sorted(scores)[len(scores) // 2] if scores else 0.0
        out = []
        for s, key, block in cand[:n]:
            self.stats["evicted_total"] += 1
            if s <= med:
                self.stats["evicted_low_util"] += 1
            else:
                self.stats["evicted_high_util"] += 1
            out.append((key, block))
        for key, _ in out:
            self.remove(key)
        return out
