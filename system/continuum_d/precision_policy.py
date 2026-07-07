# SPDX-License-Identifier: Apache-2.0
"""PrecisionAwareCachePolicy: the JOINT precision+residency scheduler.

This extends Continuum-D's JobAwareCachePolicy so that KV *precision* is a
first-class, capacity-gated admission action. Per finished-turn KV block, under
HBM budget pressure phi, the policy chooses one of:

    keep_resident   -> stays in HBM at fp16 (attention reads it directly)
    offload_fp16    -> full-precision copy to DRAM  (1.00x DRAM, 1.00x reload PCIe)
    offload_fp8     -> fp8 codec, then DRAM         (0.50x DRAM, 0.50x reload PCIe)
    offload_int4    -> int4 KIVI codec, then DRAM   (~0.28x DRAM, ~0.28x reload PCIe)
    drop_recompute  -> dropped; recomputed on resume (0 DRAM, prefill cost on reuse)

greedily by  value(a) = HBM_freed(a) / (alpha*acc_loss + beta*reload_PCIe +
gamma*recompute), using the block's ROLE (system/tool_call/reasoning sensitive ->
keep hi-precision; user/filler tolerant -> compress) and its REUSE-PROBABILITY.

Two modes, selected by `precision_mode`, run through the SAME harness so the
load-bearing co-design-vs-decoupled comparison is a one-flag change:

  * "joint"      -- precision chosen PER BLOCK, jointly with residency, from live
                    (role, reuse_prob, pressure). The non-separable choice the sim
                    validated: two blocks of the SAME role but different reuse_prob
                    get DIFFERENT precision -- something no static map can express.
  * "decoupled"  -- precision fixed OFFLINE by a static per-role bitwidth map
                    (TriAxialKV-style), decided BEFORE the scheduler runs; the
                    residency scheduler then decides keep/offload/drop by idleness,
                    blind to precision. This is the best DECOUPLED baseline
                    (TriAxialKV-offline-precision (+) MORI-admission, stapled).
  * "fp16"       -- control: every offloaded block stays fp16 (no precision knob).

The accuracy-loss table is read from `accuracy_profile.json` (same schema the
non-separability sim + Bet4 BFCL curve use), so measured per-role/per-turn numbers
drop in with zero code change.
"""

from __future__ import annotations

import json
import os
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from vllm.v1.kv_offload.base import OffloadKey

from continuum_d.codec import NOMINAL_RATIO, Precision
from continuum_d.policy import JobAwareCachePolicy

ROLES = ("system", "tool_call", "tool_result", "reasoning", "user", "filler")

# TriAxialKV-style static per-role bitwidth map used by the DECOUPLED baseline.
# Sensitive roles get fidelity; tolerant roles get compressed. Fixed offline.
DEFAULT_ROLE_BITMAP: dict[str, str] = {
    "system": "fp16",
    "tool_call": "fp8",
    "tool_result": "fp8",
    "reasoning": "fp8",
    "user": "int4",
    "filler": "int4",
}

# Offload precisions the joint policy may pick among (keep/drop handled separately).
_OFFLOAD_PRECISIONS = (Precision.FP16, Precision.FP8, Precision.INT4)

_DEFAULT_PROFILE_PATH = (
    Path(__file__).resolve().parent.parent
    / "experiments" / "codesign" / "accuracy_profile.json"
)


def _load_accuracy_profile(profile: str = "literature_pessimistic",
                           path: str | os.PathLike | None = None) -> dict:
    """Load the per-role x per-precision accuracy-loss table (+ drop severity)."""
    p = Path(path) if path else _DEFAULT_PROFILE_PATH
    with open(p) as f:
        doc = json.load(f)
    prof = doc["profiles"][profile]
    return {
        "acc": {  # acc[precision][role] = task-success points lost
            "fp16": prof["fp16"],
            "fp8": prof["fp8"],
            "int4": prof["int4"],
        },
        "drop_severity": prof["drop_severity"],
        "compounding_rate": prof.get("compounding_rate", 0.0),
    }


@dataclass
class PrecisionDecision:
    action: str            # keep | offload | drop
    precision: Precision   # storage precision (fp16 for keep/drop)
    value: float           # greedy value that won
    dram_ratio: float      # resident-DRAM footprint vs fp16 (0 for keep/drop)


class PrecisionAwareCachePolicy(JobAwareCachePolicy):
    """JobAwareCachePolicy + precision-as-admission-currency.

    Adds, on top of the base residency/eviction machinery, a per-block precision
    decision and a DRAM byte-budget accounting so the capacity gain (more logical
    KV per DRAM-GB) is measured, not assumed.
    """

    def __init__(
        self,
        cache_capacity: int,
        *,
        precision_mode: str = "joint",
        role_bitmap: dict[str, str] | None = None,
        accuracy_profile: str = "literature_pessimistic",
        accuracy_profile_path: str | None = None,
        dram_price: float = 6.0,   # DRAM shadow-price scale (x pressure -> lam_dram)
        acc_price: float = 0.5,    # shadow price on accuracy-loss points
        pcie_price: float = 2.5,   # shadow price on reload PCIe bytes
        recompute_price: float = 1.0,  # shadow price on recompute FLOPs
        recompute_cost: float = 2.0,   # prefill cost of a dropped block, relative
        hbm_price: float = 2.2,    # cost of keeping one block resident (the H objective)
        acc_reuse_floor: float = 0.2,  # accuracy penalty COMPOUNDS with reuse: a
                                       # block read every turn pays its compression
                                       # loss repeatedly, so high-reuse blocks keep
                                       # higher precision and low-reuse compress hard
                                       # (this is what makes precision vary WITHIN a
                                       # role by reuse -> the non-separable choice)
        group_size: int = 64,
        overdue_slack_ms: float = 4000.0,
        exact_tags: bool = True,
    ):
        super().__init__(cache_capacity, overdue_slack_ms=overdue_slack_ms,
                         exact_tags=exact_tags)
        assert precision_mode in ("joint", "decoupled", "fp16"), precision_mode
        self.precision_mode = precision_mode
        self.role_bitmap = dict(role_bitmap or DEFAULT_ROLE_BITMAP)
        self._prof = _load_accuracy_profile(accuracy_profile, accuracy_profile_path)
        self.dram_price = dram_price
        self.acc_price = acc_price
        self.pcie_price = pcie_price
        self.recompute_price = recompute_price
        self.recompute_cost = recompute_cost
        self.hbm_price = hbm_price
        self.acc_reuse_floor = acc_reuse_floor
        self.group_size = group_size

        # per-key decision state
        self._key_role: dict[OffloadKey, str] = {}
        self._key_reuse: dict[OffloadKey, float] = {}
        self._key_prec: dict[OffloadKey, Precision] = {}
        self._key_action: dict[OffloadKey, str] = {}
        self._key_nelem: dict[OffloadKey, int] = {}
        # exact DRAM bytes charged per key at assign time: (used, fp16_equiv).
        # keep/drop charge (0, 0); only offloaded blocks occupy DRAM.
        self._key_dram: dict[OffloadKey, tuple[int, int]] = {}

        # request-scoped context captured from kv_transfer_params
        self._cur_role = "filler"
        self._cur_reuse = 0.5

        self.prec_stats = {
            "assigned_keep": 0,
            "assigned_offload_fp16": 0,
            "assigned_offload_fp8": 0,
            "assigned_offload_int4": 0,
            "assigned_drop": 0,
            # DRAM byte accounting: what we actually store vs the fp16-equivalent.
            "dram_bytes_used": 0,
            "dram_bytes_fp16_equiv": 0,
        }

    # ---- context capture (role + reuse-prob ride on kv_transfer_params) ----

    def note_request(self, ctx_params: dict | None) -> str | None:
        jid = super().note_request(ctx_params)
        if ctx_params:
            role = ctx_params.get("role")
            if role in ROLES:
                self._cur_role = role
            rp = ctx_params.get("reuse_prob")
            if rp is not None:
                self._cur_reuse = float(rp)
        return jid

    # ---- the joint (or decoupled) precision decision ----

    def _acc_loss(self, precision: Precision, role: str) -> float:
        return float(self._prof["acc"][precision.value].get(role, 0.0))

    def _drop_severity(self, role: str) -> float:
        return float(self._prof["drop_severity"].get(role, 1.0))

    def _action_cost(self, action: str, precision: Precision, role: str,
                     reuse_prob: float, lam_dram: float) -> float:
        """Lagrangian cost of one action (LOWER is better); matches the sim dual.

        We MINIMISE per-session HBM footprint H (hbm term) subject to DRAM,
        accuracy, PCIe and recompute budgets carried as shadow-priced terms:

            cost = hbm_price*hbm + lam_dram*dram + acc_price*acc
                   + pcie_price*reload_pcie + recompute_price*recompute

        keep consumes HBM (=1) but no DRAM; each offload frees HBM and consumes
        DRAM = ratio(precision); compressing trades accuracy for cheaper DRAM +
        PCIe. Under high pressure lam_dram rises, so fp16-offload becomes costlier
        than KEEPING -> the only way to still free HBM is to COMPRESS: that is the
        precision-as-admission-currency coupling.
        """
        if action == "keep":
            return self.hbm_price  # one unit of the H objective, zero DRAM/acc
        if action == "drop":
            recomp = self.recompute_price * self.recompute_cost * reuse_prob
            risk = self.acc_price * self._drop_severity(role) * reuse_prob
            return recomp + risk
        # offload at `precision`. The accuracy term COMPOUNDS with reuse: a block
        # read every turn realises its compression loss repeatedly, so heavily
        # reused blocks pay more to be compressed (favouring higher precision /
        # keeping), while rarely-reused blocks compress cheaply. This reuse
        # dependence is precisely what makes the optimal precision non-separable
        # from the residency decision.
        ratio = NOMINAL_RATIO[precision]
        acc_compounded = self._acc_loss(precision, role) * (
            self.acc_reuse_floor + reuse_prob
        )
        return (
            lam_dram * ratio
            + self.acc_price * acc_compounded
            + self.pcie_price * reuse_prob * ratio
        )

    def choose(self, role: str, reuse_prob: float, pressure: float) -> PrecisionDecision:
        """Pick the capacity-freeing action for one finished-turn block.

        Args:
            role: chat-template role of the turn that produced the block.
            reuse_prob: probability the block is read again (drives PCIe/recompute).
            pressure: capacity pressure phi in [0,1]; higher => DRAM scarcer =>
                compression favoured over fp16-offload/keep.
        """
        lam_dram = self.dram_price * pressure

        if self.precision_mode == "fp16":
            # control: no compression. Choose keep vs fp16-offload only.
            keep_c = self._action_cost("keep", Precision.FP16, role, reuse_prob, lam_dram)
            off_c = self._action_cost("offload", Precision.FP16, role, reuse_prob, lam_dram)
            if keep_c <= off_c:
                return PrecisionDecision("keep", Precision.FP16, -keep_c, 0.0)
            return PrecisionDecision("offload", Precision.FP16, -off_c, 1.0)

        if self.precision_mode == "decoupled":
            # Precision fixed OFFLINE by the static per-role map. The residency
            # scheduler independently decides keep vs offload vs drop by cost, but
            # is BLIND to precision: the offload precision is whatever the map says,
            # not what the live (reuse, pressure) would choose.
            fixed = Precision(self.role_bitmap.get(role, "int4"))
            candidates = [
                ("keep", Precision.FP16),
                ("offload", fixed),          # precision pre-decided, not chosen here
                ("drop", Precision.FP16),
            ]
        else:  # joint: precision is chosen jointly with residency, per block
            candidates = [("keep", Precision.FP16)]
            candidates += [("offload", p) for p in _OFFLOAD_PRECISIONS]
            candidates.append(("drop", Precision.FP16))

        best: tuple[float, str, Precision] | None = None
        for action, prec in candidates:
            c = self._action_cost(action, prec, role, reuse_prob, lam_dram)
            if best is None or c < best[0]:
                best = (c, action, prec)
        cost, action, prec = best
        ratio = NOMINAL_RATIO[prec] if action == "offload" else 0.0
        return PrecisionDecision(action, prec, -cost, ratio)

    def pressure(self) -> float:
        """Current HBM pressure phi ~= active resident fraction of capacity."""
        if self.capacity <= 0:
            return 1.0
        return min(1.0, self.active_resident_blocks() / self.capacity)

    def assign(self, key: OffloadKey, block_nelem: int,
               role: str | None = None, reuse_prob: float | None = None,
               pressure: float | None = None) -> PrecisionDecision:
        """Decide + record the precision action for one finished-turn block."""
        role = role if role is not None else self._cur_role
        reuse_prob = reuse_prob if reuse_prob is not None else self._cur_reuse
        phi = pressure if pressure is not None else self.pressure()
        dec = self.choose(role, reuse_prob, phi)

        self._key_role[key] = role
        self._key_reuse[key] = reuse_prob
        self._key_prec[key] = dec.precision
        self._key_action[key] = dec.action
        self._key_nelem[key] = block_nelem

        used = equiv = 0
        if dec.action == "keep":
            self.prec_stats["assigned_keep"] += 1
        elif dec.action == "drop":
            self.prec_stats["assigned_drop"] += 1
        else:
            self.prec_stats[f"assigned_offload_{dec.precision.value}"] += 1
            equiv = block_nelem * 2
            used = int(equiv * dec.dram_ratio)
            self.prec_stats["dram_bytes_fp16_equiv"] += equiv
            self.prec_stats["dram_bytes_used"] += used
        self._key_dram[key] = (used, equiv)
        return dec

    def tag_keys_with_precision(self, keys: Iterable[OffloadKey], job_id: str | None,
                                block_nelem: int) -> None:
        """Tag stored keys with the base job bookkeeping AND a precision action."""
        keys = list(keys)
        self.tag_keys(keys, job_id)
        for k in keys:
            self.assign(k, block_nelem)

    def remove(self, key: OffloadKey) -> None:
        # refund exactly what this key was charged at assign time (0 for keep/drop)
        used, equiv = self._key_dram.pop(key, (0, 0))
        self.prec_stats["dram_bytes_used"] -= used
        self.prec_stats["dram_bytes_fp16_equiv"] -= equiv
        self._key_prec.pop(key, None)
        self._key_nelem.pop(key, None)
        self._key_role.pop(key, None)
        self._key_reuse.pop(key, None)
        self._key_action.pop(key, None)
        super().remove(key)

    def capacity_gain(self) -> float:
        """Effective DRAM capacity multiplier vs an all-fp16 store (>=1).

        sessions-per-DRAM-GB scales with this: storing the same logical KV in
        fewer bytes lets the same DRAM budget hold proportionally more.
        """
        used = self.prec_stats["dram_bytes_used"]
        equiv = self.prec_stats["dram_bytes_fp16_equiv"]
        if used <= 0:
            return 1.0
        return equiv / used

    def precision_report(self) -> dict:
        rep = dict(self.prec_stats)
        rep["precision_mode"] = self.precision_mode
        rep["capacity_gain_vs_fp16"] = round(self.capacity_gain(), 4)
        return rep
