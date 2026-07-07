"""ContinuumTTLCachePolicy: Continuum-style TTL keep-resident baseline (M2).

Continuum / CacheTTL (arXiv:2511.02230) pins a session's KV for a TTL derived
from the expected idle gap: blocks are protected while their TTL is live and
become ordinary eviction candidates once it expires. Same client signal our
job_aware policy sees (expected_gap_ms) but a PIN mechanism instead of an
ADMISSION gate — the head-to-head isolates mechanism, not signal.

Eviction order: (1) TTL-expired, most-expired first; (2) untagged blocks LRU;
(3) live-TTL (pinned) blocks only under duress, nearest-expiry first.
No capacity admission gate (Continuum scope).
"""
from __future__ import annotations

import os
import time
from collections import OrderedDict
from collections.abc import Iterable

from vllm.v1.kv_offload.base import OffloadKey
from vllm.v1.kv_offload.cpu.policies.base import BlockStatus, CachePolicy


class ContinuumTTLCachePolicy(CachePolicy):
    """TTL-pin keep-resident eviction (Continuum/CacheTTL transplant)."""

    # pin for slack x expected gap (arrival jitter headroom); CD_TTL_SLACK env
    # enables the sensitivity sweep without code changes.
    TTL_SLACK = float(os.environ.get("CD_TTL_SLACK", "1.5"))

    def __init__(self, cache_capacity: int):
        self.capacity = cache_capacity
        self.blocks: OrderedDict[OffloadKey, BlockStatus] = OrderedDict()
        self._last_access_ms: dict[OffloadKey, float] = {}
        self._pin_until_ms: dict[OffloadKey, float] = {}
        self._current_gap_ms: float = 0.0  # from the latest note_request
        self.stats = {
            "evicted_expired": 0,
            "evicted_untagged": 0,
            "evicted_pinned": 0,      # duress evictions of live-TTL blocks
            "admission_refusals": 0,  # always 0 (no gate in Continuum scope)
        }

    # ---- context hook (manager forwards kv_transfer_params) ----
    def note_request(self, params: dict | None) -> None:
        # per-request semantics: a request without an expected gap must NOT
        # inherit the previous request's TTL (reset to 0 = untagged).
        gap = (params or {}).get("expected_gap_ms")
        try:
            self._current_gap_ms = float(gap) if gap is not None else 0.0
        except (TypeError, ValueError):
            self._current_gap_ms = 0.0

    # ---- CachePolicy interface ----
    def get(self, key: OffloadKey) -> BlockStatus | None:
        return self.blocks.get(key)

    def insert(self, key: OffloadKey, block: BlockStatus) -> None:
        self.blocks[key] = block
        now = time.monotonic() * 1000.0
        self._last_access_ms[key] = now
        if self._current_gap_ms > 0:
            self._pin_until_ms[key] = now + self.TTL_SLACK * self._current_gap_ms

    def remove(self, key: OffloadKey) -> None:
        del self.blocks[key]
        self._last_access_ms.pop(key, None)
        self._pin_until_ms.pop(key, None)

    def touch(self, keys: Iterable[OffloadKey]) -> None:
        now = time.monotonic() * 1000.0
        for key in reversed(list(keys)):
            if key in self.blocks:
                self.blocks.move_to_end(key)
                self._last_access_ms[key] = now
                if self._current_gap_ms > 0:
                    self._pin_until_ms[key] = (
                        now + self.TTL_SLACK * self._current_gap_ms)

    def clear(self) -> None:
        self.blocks.clear()
        self._last_access_ms.clear()
        self._pin_until_ms.clear()

    # ---- eviction: expired -> untagged-LRU -> pinned (nearest expiry) ----
    def evict(
        self, n: int, protected: set[OffloadKey]
    ) -> list[tuple[OffloadKey, BlockStatus]] | None:
        if n == 0:
            return []
        now = time.monotonic() * 1000.0
        cand: list[tuple[int, float, OffloadKey, BlockStatus]] = []
        for key, block in self.blocks.items():
            if block.ref_cnt != 0 or key in protected:
                continue
            pin = self._pin_until_ms.get(key)
            if pin is None:
                # untagged: class 1, LRU (older = evict first)
                cand.append((1, self._last_access_ms.get(key, 0.0), key, block))
            elif now > pin:
                # expired: class 0, most-expired first
                cand.append((0, pin, key, block))
            else:
                # live pin: class 2, nearest expiry first (duress only)
                cand.append((2, pin, key, block))
        if len(cand) < n:
            return None
        cand.sort(key=lambda t: (t[0], t[1]))
        out = []
        for cls, _, key, block in cand[:n]:
            if cls == 0:
                self.stats["evicted_expired"] += 1
            elif cls == 1:
                self.stats["evicted_untagged"] += 1
            else:
                self.stats["evicted_pinned"] += 1
            out.append((key, block))
        for key, _ in out:
            self.remove(key)
        return out
