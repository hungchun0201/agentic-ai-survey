"""GatedTTLCachePolicy: capacity-ADMISSION gate + TTL-pin eviction ordering.

Cold-gate fairness baseline: gives the TTL mechanism our refusal-based
admission (working-set accounting identical to Tenure) while keeping its
own pin-based eviction ordering. Isolates gate-vs-class-ordering.

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


class GatedTTLCachePolicy(CachePolicy):
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
        self._current_job: str | None = None
        self._job_keys: dict[str, set[OffloadKey]] = {}
        self._finished: set[str] = set()
        self.stats = {
            "evicted_expired": 0,
            "evicted_untagged": 0,
            "evicted_pinned": 0,      # duress evictions of live-TTL blocks
            "admission_refusals": 0,  # the gate (Tenure-identical accounting)
        }

    # ---- context hook (manager forwards kv_transfer_params) ----
    def note_request(self, params: dict | None):
        p = params or {}
        gap = p.get("expected_gap_ms")
        try:
            self._current_gap_ms = float(gap) if gap is not None else 0.0
        except (TypeError, ValueError):
            self._current_gap_ms = 0.0
        job_id = p.get("job_id")
        self._current_job = str(job_id) if job_id is not None else None
        if self._current_job is not None and p.get("last_turn"):
            self._finished.add(self._current_job)
        return self._current_job

    def admit(self, job_id: str | None, n_new: int) -> bool:
        """Anti-thrash gate: active jobs' residency must fit capacity
        (accounting identical to Tenure's admit())."""
        resident_other = 0
        for jid, keys in self._job_keys.items():
            if jid == job_id or jid in self._finished:
                continue
            resident_other += sum(1 for k in keys if k in self.blocks)
        resident_self = 0
        if job_id is not None and job_id in self._job_keys:
            resident_self = sum(1 for k in self._job_keys[job_id] if k in self.blocks)
        if resident_other + resident_self + n_new > self.capacity:
            self.stats["admission_refusals"] += 1
            return False
        return True

    def tag_keys(self, keys, job_id) -> None:
        if job_id is None:
            return
        self._job_keys.setdefault(job_id, set()).update(keys)

    # ---- CachePolicy interface ----
    def get(self, key: OffloadKey) -> BlockStatus | None:
        return self.blocks.get(key)

    def insert(self, key: OffloadKey, block: BlockStatus) -> None:
        self.blocks[key] = block
        now = time.monotonic() * 1000.0
        self._last_access_ms[key] = now
        if self._current_gap_ms > 0:
            self._pin_until_ms[key] = now + self.TTL_SLACK * self._current_gap_ms
        if self._current_job is not None:
            self._job_keys.setdefault(self._current_job, set()).add(key)

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
