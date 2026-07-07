# SPDX-License-Identifier: Apache-2.0
"""CPU-only unit tests for JobAwareCachePolicy (no GPU needed).

Run: PYTHONPATH=<agent-kvcache> python -m pytest continuum_d/tests/ -q
(any venv with vllm>=0.20 importable works, incl. the cu13 latest-main env)
"""
import time

from vllm.v1.kv_offload.base import make_offload_key
from vllm.v1.kv_offload.cpu.policies.base import BlockStatus

from continuum_d.policy import JobAwareCachePolicy


def _key(i):
    return make_offload_key(f"h{i}".encode(), 0)


def _store(P, job, ks, gap_ms=None, last=False):
    jid = P.note_request(
        {"job_id": job, "expected_gap_ms": gap_ms, "last_turn": last}
    )
    for i in ks:
        b = BlockStatus(i)
        b.ref_cnt = 0
        P.insert(_key(i), b)
    P.tag_keys([_key(i) for i in ks], jid)


def test_eviction_order_and_admission():
    P = JobAwareCachePolicy(cache_capacity=10)
    _store(P, "A", [0, 1]); P.mark_job_finished("A")
    _store(P, "B", [2, 3], gap_ms=-10000)   # overdue
    _store(P, "C", [4, 5], gap_ms=60000)    # far wakeup
    _store(P, "D", [6, 7], gap_ms=100)      # imminent (within slack)
    time.sleep(0.2)

    ev = P.evict(4, protected=set())
    got = [k for k, _ in ev]
    assert set(got[:2]) == {_key(0), _key(1)}   # finished first
    assert set(got[2:4]) == {_key(2), _key(3)}  # overdue second

    ev2 = P.evict(2, protected=set())
    assert set(k for k, _ in ev2) == {_key(4), _key(5)}  # far before imminent

    assert P.admit("E", 9) is False   # would exceed capacity vs active jobs
    assert P.stats["admission_refusals"] == 1
    assert P.admit("E", 2) is True

    before = len(P.blocks)
    assert P.evict(5, protected=set()) is None  # atomic refusal
    assert len(P.blocks) == before
