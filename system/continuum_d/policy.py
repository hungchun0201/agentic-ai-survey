# SPDX-License-Identifier: Apache-2.0
"""JobAwareCachePolicy: agent-job-aware DRAM-side eviction for Continuum-D.

Eviction order (most-evictable first):
  1. blocks of FINISHED jobs
  2. blocks of OVERDUE jobs (now > expected wakeup + slack)
  3. blocks of jobs with the FARTHEST predicted wakeup
  4. untagged blocks / intra-class LRU (base order)

Admission control (anti-thrash, finding experiments.md 3.6#3): refuse new
stores when the sum of ACTIVE jobs' resident blocks would exceed capacity,
so tight DRAM degrades to no-DRAM instead of below it.
"""

import time
from collections import OrderedDict
from collections.abc import Iterable

from vllm.v1.kv_offload.base import OffloadKey
from vllm.v1.kv_offload.cpu.policies.base import BlockStatus, CachePolicy


class _JobInfo:
    __slots__ = ("keys", "wakeup_ms", "finished", "last_seen_ms")

    def __init__(self):
        self.keys: OrderedDict[OffloadKey, None] = OrderedDict()
        self.wakeup_ms: float | None = None  # predicted next-turn arrival
        self.finished: bool = False
        self.last_seen_ms: float = time.monotonic() * 1000.0


class JobAwareCachePolicy(CachePolicy):
    """LRU-compatible policy with job-level grouping and wakeup ordering.

    Context flows in via the *_with_context hooks called by
    JobAwareOffloadingManager (out-of-tree #45405-style plumbing).
    """

    def __init__(self, cache_capacity: int, overdue_slack_ms: float = 4000.0,
                 exact_tags: bool = True):
        self.blocks: OrderedDict[OffloadKey, BlockStatus] = OrderedDict()
        self.capacity = cache_capacity
        self.overdue_slack_ms = overdue_slack_ms
        # exact_tags=False is the E2 metadata-off ablation: the two EXACT client
        # lifecycle signals an idleness ranker cannot infer are blinded --
        #   * last_turn   -> finished flag never set (no instant dead-KV reclaim;
        #                    dead jobs age out by idle order like any block), and
        #   * expected_gap-> wakeup_ms never set (no overdue/far-wakeup ordering).
        # job_id grouping + capacity admission are KEPT (both inferable from
        # observed co-access), so eviction degrades to idle-order within the
        # SAME framework -- isolating the exact-metadata contribution.
        self.exact_tags = exact_tags
        self._key_job: dict[OffloadKey, str] = {}
        # O(1)-amortized residency accounting (cold-gate fix: the previous
        # O(total-tracked-keys) scan per admit() dominated the critical path
        # at loose budgets, e.g. DRAM >= working set).
        self._counted: set[OffloadKey] = set()
        self._resident: dict[str, int] = {}
        self._jobs: dict[str, _JobInfo] = {}
        # stats for the experiment writeup
        self.stats = {
            "evicted_finished": 0,
            "evicted_overdue": 0,
            "evicted_far_wakeup": 0,
            "evicted_lru": 0,
            "admission_refusals": 0,
        }

    # ---- context hooks (called by JobAwareOffloadingManager) ----

    def note_request(self, ctx_params: dict | None) -> str | None:
        """Update job bookkeeping from kv_transfer_params; returns job_id."""
        if not ctx_params:
            return None
        job_id = ctx_params.get("job_id")
        if job_id is None:
            return None
        info = self._jobs.setdefault(str(job_id), _JobInfo())
        now = time.monotonic() * 1000.0
        info.last_seen_ms = now
        if self.exact_tags:
            gap = ctx_params.get("expected_gap_ms")
            if gap is not None:
                info.wakeup_ms = now + float(gap)
            if ctx_params.get("last_turn"):
                info.finished = True
        return str(job_id)

    def _count(self, key) -> None:
        job = self._key_job.get(key)
        if job is not None and key in self.blocks and key not in self._counted:
            self._counted.add(key)
            self._resident[job] = self._resident.get(job, 0) + 1

    def _uncount(self, key) -> None:
        if key in self._counted:
            self._counted.discard(key)
            job = self._key_job.get(key)
            if job is not None:
                self._resident[job] = self._resident.get(job, 1) - 1

    def tag_keys(self, keys: Iterable[OffloadKey], job_id: str | None) -> None:
        if job_id is None:
            return
        info = self._jobs.setdefault(job_id, _JobInfo())
        info.finished = False  # storing again -> job live
        for k in keys:
            prev = self._key_job.get(k)
            if prev is not None and prev != job_id:
                self._uncount(k)
            self._key_job[k] = job_id
            info.keys[k] = None
            self._count(k)

    def mark_job_finished(self, job_id: str | None) -> None:
        if not self.exact_tags:
            return  # metadata-off ablation: last_turn dead-KV reclaim disabled
        if job_id is not None and job_id in self._jobs:
            self._jobs[job_id].finished = True

    def active_resident_blocks(self, exclude_job: str | None = None) -> int:
        n = 0
        for jid, info in self._jobs.items():
            if info.finished or jid == exclude_job:
                continue
            n += self._resident.get(jid, 0)
        return n

    def admit(self, job_id: str | None, n_new: int) -> bool:
        """Anti-thrash gate: active jobs' residency must fit capacity."""
        resident_other = self.active_resident_blocks(exclude_job=job_id)
        resident_self = 0
        if job_id is not None and job_id in self._jobs:
            resident_self = self._resident.get(job_id, 0)
        if resident_other + resident_self + n_new > self.capacity:
            self.stats["admission_refusals"] += 1
            return False
        return True

    # ---- CachePolicy interface ----

    def get(self, key: OffloadKey) -> BlockStatus | None:
        return self.blocks.get(key)

    def insert(self, key: OffloadKey, block: BlockStatus) -> None:
        self.blocks[key] = block
        self._count(key)

    def remove(self, key: OffloadKey) -> None:
        self._uncount(key)
        del self.blocks[key]
        job = self._key_job.pop(key, None)
        if job is not None and job in self._jobs:
            self._jobs[job].keys.pop(key, None)

    def touch(self, keys: Iterable[OffloadKey]) -> None:
        for key in reversed(list(keys)):
            if key in self.blocks:
                self.blocks.move_to_end(key)

    def clear(self) -> None:
        self.blocks.clear()
        self._key_job.clear()
        self._jobs.clear()
        self._counted.clear()
        self._resident.clear()

    def _job_class(self, key: OffloadKey, now_ms: float) -> tuple[int, float]:
        """(class, tiebreak) — lower class evicts first."""
        job = self._key_job.get(key)
        if job is None:
            return (3, 0.0)  # untagged: with plain-LRU class
        info = self._jobs.get(job)
        if info is None:
            return (3, 0.0)
        if info.finished:
            return (0, 0.0)
        if info.wakeup_ms is not None:
            if now_ms > info.wakeup_ms + self.overdue_slack_ms:
                return (1, now_ms - info.wakeup_ms)  # most overdue first
            # active, waiting: evict farthest wakeup first (evict() sorts by
            # -tie ascending, so larger tie = evicted earlier)
            return (2, info.wakeup_ms - now_ms)
        return (3, 0.0)

    def evict(
        self, n: int, protected: set[OffloadKey]
    ) -> list[tuple[OffloadKey, BlockStatus]] | None:
        if n == 0:
            return []
        now_ms = time.monotonic() * 1000.0
        candidates: list[tuple[int, float, int, OffloadKey, BlockStatus]] = []
        for order_idx, (key, block) in enumerate(self.blocks.items()):
            if block.ref_cnt != 0 or key in protected:
                continue
            cls, tie = self._job_class(key, now_ms)
            candidates.append((cls, -tie, order_idx, key, block))
        if len(candidates) < n:
            return None
        candidates.sort()
        chosen = candidates[:n]
        stat_names = {
            0: "evicted_finished",
            1: "evicted_overdue",
            2: "evicted_far_wakeup",
            3: "evicted_lru",
        }
        for cls, _, _, key, _ in chosen:
            self.stats[stat_names[cls]] += 1
        result = []
        for _, _, _, key, block in chosen:
            self._uncount(key)
            del self.blocks[key]
            job = self._key_job.pop(key, None)
            if job is not None and job in self._jobs:
                self._jobs[job].keys.pop(key, None)
            result.append((key, block))
        return result
