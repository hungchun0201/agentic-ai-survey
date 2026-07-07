# SPDX-License-Identifier: Apache-2.0
"""CPU-only unit tests for the JOINT precision+residency policy (no GPU needed).

The load-bearing intellectual claim is NON-SEPARABILITY: the optimal precision
for a block is not separable from its residency decision, so no static per-role
bitwidth map (the decoupled baseline) can match the joint scheduler. These tests
pin the mechanism-level signatures of that claim.

Run: PYTHONPATH=<agent-kvcache>/.pylib python -m pytest continuum_d/tests/ -q
"""
import random

from vllm.v1.kv_offload.base import make_offload_key

from continuum_d.precision_policy import (
    DEFAULT_ROLE_BITMAP,
    PrecisionAwareCachePolicy,
)

ROLES = ["system", "tool_call", "tool_result", "reasoning", "user", "filler"]


def _key(i):
    return make_offload_key(f"h{i}".encode(), 0)


def test_profile_loads_and_ordering_sane():
    P = PrecisionAwareCachePolicy(100, precision_mode="joint")
    # sensitive roles lose more than tolerant roles at int4 (TriAxialKV ordering)
    from continuum_d.codec import Precision
    assert P._acc_loss(Precision.INT4, "tool_call") > P._acc_loss(Precision.INT4, "filler")
    assert P._acc_loss(Precision.INT4, "system") > P._acc_loss(Precision.INT4, "user")


def test_joint_uses_multiple_offload_precisions():
    P = PrecisionAwareCachePolicy(100, precision_mode="joint")
    precs = set()
    for role in ROLES:
        for rp in [i / 20 for i in range(21)]:
            for phi in (0.2, 0.3, 0.4):
                d = P.choose(role, rp, phi)
                if d.action == "offload":
                    precs.add(d.precision.value)
    assert {"fp8", "int4"}.issubset(precs), precs  # both compressed tiers fire


def test_within_role_precision_varies_joint_but_not_decoupled():
    """The non-separability signature: for a role where the static map is
    conservative (system->fp16), the JOINT policy assigns >1 distinct storage
    precision across reuse (compress the rarely-reused, keep the hot ones), while
    the DECOUPLED policy -- bound to one bitwidth per role -- cannot."""
    Pj = PrecisionAwareCachePolicy(100, precision_mode="joint")
    Pd = PrecisionAwareCachePolicy(100, precision_mode="decoupled")

    def offload_precs(P, role, phi=0.3):
        return {
            P.choose(role, rp, phi).precision.value
            for rp in [i / 40 for i in range(41)]
            if P.choose(role, rp, phi).action == "offload"
        }

    joint_system = offload_precs(Pj, "system")
    dec_system = offload_precs(Pd, "system")
    assert len(joint_system) >= 2, joint_system      # joint compresses at 2+ widths
    assert len(dec_system) <= 1, dec_system          # decoupled is single-width


def test_joint_diverges_from_decoupled_across_band():
    """Joint and decoupled disagree on a non-trivial fraction of blocks across
    the whole target pressure band phi in [0.2,0.4] -- if they agreed everywhere
    the co-design would collapse to 'TriAxialKV + MORI stapled'."""
    for phi in (0.2, 0.3, 0.4):
        Pj = PrecisionAwareCachePolicy(100, precision_mode="joint")
        Pd = PrecisionAwareCachePolicy(100, precision_mode="decoupled")
        rng = random.Random(7)
        diff = n = 0
        for _ in range(3000):
            role = rng.choice(ROLES)
            rp = rng.random()
            dj = Pj.choose(role, rp, phi)
            dd = Pd.choose(role, rp, phi)
            n += 1
            if (dj.action, dj.precision.value) != (dd.action, dd.precision.value):
                diff += 1
        assert diff / n > 0.10, (phi, diff / n)


def test_decoupled_offload_precision_follows_static_map():
    P = PrecisionAwareCachePolicy(100, precision_mode="decoupled")
    for role in ROLES:
        for rp in [i / 20 for i in range(21)]:
            d = P.choose(role, rp, 0.3)
            if d.action == "offload":
                assert d.precision.value == DEFAULT_ROLE_BITMAP[role], (role, d.precision)


def test_capacity_gain_above_one_and_accounting_consistent():
    from vllm.v1.kv_offload.cpu.policies.base import BlockStatus

    P = PrecisionAwareCachePolicy(5000, precision_mode="joint")
    rng = random.Random(1)
    for i in range(800):
        role = rng.choice(ROLES)
        rp = rng.random()
        b = BlockStatus(i)
        b.ref_cnt = 0
        P.insert(_key(i), b)
        P.assign(_key(i), block_nelem=16 * 8 * 128, role=role, reuse_prob=rp,
                 pressure=0.3)
    rep = P.precision_report()
    assert rep["capacity_gain_vs_fp16"] > 1.0, rep
    assert rep["dram_bytes_used"] <= rep["dram_bytes_fp16_equiv"]
    # removing every block returns the DRAM accounting to zero (no leak)
    for i in range(800):
        if P.get(_key(i)) is not None:
            P.remove(_key(i))
    assert P.prec_stats["dram_bytes_used"] == 0, P.prec_stats
    assert P.prec_stats["dram_bytes_fp16_equiv"] == 0, P.prec_stats


def test_fp16_control_never_compresses():
    P = PrecisionAwareCachePolicy(100, precision_mode="fp16")
    for role in ROLES:
        for rp in [i / 20 for i in range(21)]:
            d = P.choose(role, rp, 0.3)
            assert d.precision.value == "fp16"
            assert d.action in ("keep", "offload")
