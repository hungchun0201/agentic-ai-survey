# SPDX-License-Identifier: Apache-2.0
"""CPU-only unit tests for the E2 novelty-gate policies (no GPU needed).

Covers:
  * MoriProxyCachePolicy: relative-idleness ranking (differs from LRU) +
    observed-active admission.
  * JobAwareCachePolicy(exact_tags=False): the metadata-off ablation blinds
    last_turn + expected_gap so eviction degrades to base (idle) order.

Run: PYTHONPATH=<agent-kvcache> python -m pytest continuum_d/tests/ -q
"""
import time

from vllm.v1.kv_offload.base import make_offload_key
from vllm.v1.kv_offload.cpu.policies.base import BlockStatus

from continuum_d.mori_policy import MoriProxyCachePolicy
from continuum_d.policy import JobAwareCachePolicy


def _key(i):
    return make_offload_key(f"h{i}".encode(), 0)


def _blk(P, i):
    b = BlockStatus(i)
    b.ref_cnt = 0
    P.insert(_key(i), b)


# ------------------------- MORI-proxy baseline -------------------------

def test_mori_relative_idleness_beats_lru_recency():
    """A fast-rhythm block idle >> its cadence is evicted before never-reused
    blocks that are absolutely older -- the opposite of LRU, and MORI's point."""
    P = MoriProxyCachePolicy(cache_capacity=10)
    _blk(P, 0)          # dead pair: inserted, never re-touched (cadence=prior)
    _blk(P, 1)
    _blk(P, 2)          # live-rhythm block: touched on a ~20ms cadence
    time.sleep(0.02); P.touch([_key(2)])
    time.sleep(0.02); P.touch([_key(2)])   # block 2 is the MOST-recently used
    time.sleep(0.20)                       # everyone idles ~0.2s

    ev = P.evict(1, protected=set())
    got = [k for k, _ in ev]
    # LRU would keep block 2 (touched last). Relative idleness evicts it first:
    # it broke its own ~20ms rhythm by ~10x (rel>=1 -> counted "stale").
    assert got == [_key(2)]
    assert P.stats["evicted_stale"] == 1
    assert P.stats["evicted_total"] == 1


def test_mori_observed_admission_gate():
    P = MoriProxyCachePolicy(cache_capacity=2)
    _blk(P, 0); _blk(P, 1)          # both just inserted -> observed-active = 2
    # capacity 2 already full of observed-active blocks -> refuse the new store
    assert P.admit_observed(1) is False
    assert P.stats["admission_refusals"] == 1
    # a policy with headroom admits
    Q = MoriProxyCachePolicy(cache_capacity=10)
    _blk(Q, 0)
    assert Q.admit_observed(1) is True


def test_mori_remove_and_evict_cleanup():
    P = MoriProxyCachePolicy(cache_capacity=10)
    _blk(P, 0); _blk(P, 1)
    P.remove(_key(0))
    assert _key(0) not in P._last_access_ms and _key(0) not in P.blocks
    time.sleep(0.01)
    P.evict(1, protected=set())
    assert len(P.blocks) == 0
    assert not P._last_access_ms and not P._ewma_gap_ms


def test_mori_never_reads_client_tags():
    """The policy has no note_request / tag hooks: it is observation-only."""
    P = MoriProxyCachePolicy(cache_capacity=10)
    assert not hasattr(P, "note_request")
    assert not hasattr(P, "tag_keys")
    assert not hasattr(P, "mark_job_finished")


# --------------------- metadata-off ablation of job_aware ---------------------

def test_metadata_off_blinds_last_turn_and_gap():
    P = JobAwareCachePolicy(cache_capacity=10, exact_tags=False)
    jid = P.note_request(
        {"job_id": "A", "expected_gap_ms": 60000, "last_turn": True})
    assert jid == "A"                       # job_id grouping still tracked
    _blk(P, 0); _blk(P, 1)
    P.tag_keys([_key(0), _key(1)], jid)
    P.mark_job_finished("A")                # no-op under exact_tags=False
    info = P._jobs["A"]
    assert info.finished is False           # last_turn blinded (no dead reclaim)
    assert info.wakeup_ms is None           # expected_gap blinded (no ordering)
    now = time.monotonic() * 1000.0
    # every tagged block falls to the base-order (LRU) class 3, not finished(0)
    assert P._job_class(_key(0), now) == (3, 0.0)


def test_metadata_off_evicts_in_base_order():
    """With tags blinded, a 'finished' job's blocks do NOT jump the queue;
    eviction follows insertion/idle (base) order like LRU."""
    P = JobAwareCachePolicy(cache_capacity=10, exact_tags=False)
    a = P.note_request({"job_id": "A", "last_turn": True})   # would be dead if seen
    _blk(P, 0); _blk(P, 1); P.tag_keys([_key(0), _key(1)], a)
    b = P.note_request({"job_id": "B", "expected_gap_ms": 100})
    _blk(P, 2); _blk(P, 3); P.tag_keys([_key(2), _key(3)], b)
    P.mark_job_finished("A")
    ev = P.evict(2, protected=set())
    got = [k for k, _ in ev]
    # base order: A's blocks were inserted first -> evicted first, but ONLY
    # because they are oldest, not because last_turn marked them dead.
    assert set(got) == {_key(0), _key(1)}
    assert P.stats["evicted_finished"] == 0     # finished class never triggered
    assert P.stats["evicted_lru"] == 2          # all via base-order class


def test_metadata_off_keeps_admission():
    P = JobAwareCachePolicy(cache_capacity=10, exact_tags=False)
    a = P.note_request({"job_id": "A"})
    _blk(P, 0); _blk(P, 1); P.tag_keys([_key(0), _key(1)], a)
    # grouping/admission survive: 2 active-resident + 9 new > cap 10 -> refuse
    assert P.admit("B", 9) is False
    assert P.stats["admission_refusals"] == 1
    assert P.admit("B", 2) is True


def test_full_policy_unchanged_by_default():
    """exact_tags defaults True -> E1 behavior preserved (finished + wakeup set)."""
    P = JobAwareCachePolicy(cache_capacity=10)          # default exact_tags=True
    P.note_request({"job_id": "A", "expected_gap_ms": 5000, "last_turn": True})
    info = P._jobs["A"]
    assert info.finished is True
    assert info.wakeup_ms is not None
