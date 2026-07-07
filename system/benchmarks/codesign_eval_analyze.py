# SPDX-License-Identifier: Apache-2.0
"""Analyze the co-design load-bearing eval: sessions-per-HBM-GB @ iso-task-success.

Reads the per-run dirs produced by run_codesign_eval.sh (each holds BFCL score +
result files, physical_stats.json, precision_stats.json, meta.json) and computes
the ≥7 make-or-break number:

  primary (H-frontier dual, EVAL_PLAN §2): fix the accuracy FLOOR (fp16 − 1% abs),
  drive HBM (phi = gpu-mem-util) down, and record the MINIMUM resident-HBM phi at
  which each system still holds the floor. H = phi_min. Then
      ratio = H_decoupled / H_joint          (>1 => joint sustains tighter HBM => wins)
  with a paired EPISODE-LEVEL bootstrap CI. GO iff ratio ≥ 1.2 and the bootstrap CI
  lower bound > 1.1 (non-overlapping), NO-GO iff ratio < 1.1 / CI straddles 1.0.

  Also reports: per-(system,phi) task-success + Wilson CI; the physical DRAM peak-vs-
  fp16 ratio + reload-PCIe ratio (CD_PHYSICAL_STATS) and the accounting capacity gain
  (CD_PRECISION_STATS); the homogeneous-role control (must -> ~1.0); best-static-map
  note; and a per-turn / latency best-effort. Tolerant of partial results.
"""
import argparse
import glob
import json
import math
import os
import random
from collections import defaultdict


# ---------------------------------------------------------------- I/O helpers

def _read_jsonl(path):
    out = []
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    out.append(json.loads(line))
                except ValueError:
                    pass
    except OSError:
        pass
    return out


def _score_files(run):
    return sorted(glob.glob(os.path.join(
        run, "bfcl", "score", "**", "BFCL_v*_multi_turn_*_score.json"),
        recursive=True))


def _result_files(run):
    return sorted(glob.glob(os.path.join(
        run, "bfcl", "result", "**", "BFCL_v*_multi_turn_*_result.json"),
        recursive=True))


def load_episodes(run):
    """Return {episode_id: passed_bool} pooled over categories for one run.

    Score files list a header {accuracy,correct_count,total_count} then the FAILING
    entries (valid==false). The attempted id set comes from the result files; a
    result id not in the failure set passed. Falls back to header counts if result
    files are absent (point estimate only)."""
    failures = set()
    header_correct = header_total = 0
    for sf in _score_files(run):
        rows = _read_jsonl(sf)
        if not rows:
            continue
        head = rows[0]
        if "total_count" in head:
            header_correct += int(head.get("correct_count", 0))
            header_total += int(head.get("total_count", 0))
            entries = rows[1:]
        else:
            entries = rows
        for e in entries:
            if isinstance(e, dict) and e.get("id") is not None and not e.get("valid", False):
                failures.add(e["id"])
    attempted = set()
    for rf in _result_files(run):
        for r in _read_jsonl(rf):
            if isinstance(r, dict) and r.get("id") is not None:
                attempted.add(r["id"])
    episodes = {}
    if attempted:
        for i in attempted:
            episodes[i] = i not in failures
    return {"episodes": episodes,
            "header_correct": header_correct, "header_total": header_total}


def load_meta(run):
    try:
        return json.load(open(os.path.join(run, "meta.json")))
    except (OSError, ValueError):
        return {}


def load_json(run, name):
    try:
        return json.load(open(os.path.join(run, name)))
    except (OSError, ValueError):
        return None


# ---------------------------------------------------------------- statistics

def wilson_ci(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    hw = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - hw) / d, (c + hw) / d)


def h_frontier(succ_by_phi, floor, interp=True):
    """Minimum resident-HBM phi at which success still holds the floor.

    The H-frontier is where the success(phi) curve crosses `floor`. On a coarse phi
    grid the discrete min-holding-phi is a step function (unstable under bootstrap),
    so by default we linearly INTERPOLATE the crossing phi between the lowest phi
    that holds the floor and the next-lower phi that does not -> a continuous H that
    makes the bootstrap CI meaningful. Returns None if no phi holds the floor.
    """
    if not succ_by_phi:
        return None
    phis = sorted(succ_by_phi)                       # ascending (tight -> loose HBM)
    holding = [p for p in phis if succ_by_phi[p] >= floor]
    if not holding:
        return None
    lo_hold = min(holding)
    if not interp:
        return lo_hold
    below = [p for p in phis if p < lo_hold]          # a tighter phi that FAILS
    if not below:
        return lo_hold                                # holds even at the tightest grid point
    p_fail = max(below)
    s_hold, s_fail = succ_by_phi[lo_hold], succ_by_phi[p_fail]
    if s_hold == s_fail:                              # flat -> no crossing to interpolate
        return lo_hold
    # linear interp on success between (p_fail, s_fail) and (lo_hold, s_hold)
    frac = (floor - s_fail) / (s_hold - s_fail)
    frac = max(0.0, min(1.0, frac))
    return round(p_fail + frac * (lo_hold - p_fail), 5)


# ---------------------------------------------------------------- core

def collect(root):
    runs = defaultdict(dict)   # (system, homog) -> {phi -> {seed -> episodes-dict}}
    meta_any = {}
    phys = {}
    prec = {}
    for d in sorted(glob.glob(os.path.join(root, "*"))):
        if not os.path.isdir(d) or not os.path.exists(os.path.join(d, "meta.json")):
            continue
        m = load_meta(d)
        sysname = m.get("system")
        if not sysname:
            continue
        homog = m.get("homogeneous_role") or ""
        phi = m.get("gpu_mem_util")
        seed = m.get("seed", 0)
        ep = load_episodes(d)
        runs[(sysname, homog)].setdefault(phi, {})[seed] = ep
        meta_any[(sysname, homog, phi, seed)] = m
        p = load_json(d, "physical_stats.json")
        if p:
            phys[(sysname, homog, phi, seed)] = p
        pr = load_json(d, "precision_stats.json")
        if pr:
            prec[(sysname, homog, phi, seed)] = pr
    return runs, meta_any, phys, prec


def pooled_success(seed_map):
    """Pool all seeds' episodes for a (system,phi) cell -> (correct, total, episodes-list)."""
    eps = {}
    hc = ht = 0
    for seed, ep in seed_map.items():
        for i, ok in ep["episodes"].items():
            eps[(seed, i)] = ok
        hc += ep["header_correct"]
        ht += ep["header_total"]
    if eps:
        correct = sum(1 for v in eps.values() if v)
        total = len(eps)
    else:
        correct, total = hc, ht
    return correct, total, eps


def success_curve(runs, key):
    """{phi -> success_fraction} and {phi -> episodes-dict} for a (system,homog) key."""
    curve, epsmap = {}, {}
    for phi, seed_map in runs.get(key, {}).items():
        c, t, eps = pooled_success(seed_map)
        if t > 0:
            curve[phi] = c / t
            epsmap[phi] = eps
    return curve, epsmap


def bootstrap_ratio(joint_eps, dec_eps, floor, B=2000, seed=0):
    """Paired episode-level bootstrap of ratio = H_dec / H_joint over the phi grid."""
    rng = random.Random(seed)
    phis = sorted(set(joint_eps) | set(dec_eps))
    # per-phi episode-id lists (resample within each cell)
    j_items = {phi: list(joint_eps.get(phi, {}).items()) for phi in phis}
    d_items = {phi: list(dec_eps.get(phi, {}).items()) for phi in phis}
    ratios = []
    for _ in range(B):
        js, ds = {}, {}
        for phi in phis:
            ji = j_items[phi]
            if ji:
                samp = [ji[rng.randrange(len(ji))][1] for _ in range(len(ji))]
                js[phi] = sum(samp) / len(samp)
            di = d_items[phi]
            if di:
                samp = [di[rng.randrange(len(di))][1] for _ in range(len(di))]
                ds[phi] = sum(samp) / len(samp)
        hj, hd = h_frontier(js, floor), h_frontier(ds, floor)
        if hj and hd:
            ratios.append(hd / hj)
    if not ratios:
        return None
    ratios.sort()
    lo = ratios[int(0.025 * len(ratios))]
    hi = ratios[min(len(ratios) - 1, int(0.975 * len(ratios)))]
    med = ratios[len(ratios) // 2]
    return {"ratio_median": round(med, 4), "ci95": [round(lo, 4), round(hi, 4)],
            "n_boot": len(ratios)}


def phys_summary(phys, prec, sysname):
    """Physical DRAM peak-vs-fp16 + reload PCIe (measured) and accounting gain."""
    peaks, reloads, gains = [], [], []
    for (s, homog, phi, seed), p in phys.items():
        if s == sysname and not homog:
            peaks.append(p.get("peak_vs_fp16_equiv_ratio"))
            reloads.append(p.get("reload_pcie_ratio"))
    for (s, homog, phi, seed), pr in prec.items():
        if s == sysname and not homog:
            gains.append(pr.get("capacity_gain_vs_fp16"))
    def _avg(x):
        x = [v for v in x if isinstance(v, (int, float))]
        return round(sum(x) / len(x), 4) if x else None
    return {"physical_peak_vs_fp16": _avg(peaks),
            "physical_reload_pcie_ratio": _avg(reloads),
            "accounting_capacity_gain_vs_fp16": _avg(gains)}


def collect_probes(root):
    """Per-ROLE int4-sensitivity probe: runs whose meta.probe_role is set store KV
    with ONLY that role at int4 (rest fp16). Return {role -> success_fraction}.

    A GRADIENT across roles (some roles' int4 hurts task-success much more than
    others) is what makes the co-design pay: joint can keep the sensitive roles
    lossless and int4 the tolerant ones per-block, which no static-per-role map
    matches. If int4 hurts ~uniformly (no gradient), the co-design does NOT pay.
    """
    per_role = {}
    for d in sorted(glob.glob(os.path.join(root, "*"))):
        if not os.path.isdir(d):
            continue
        m = load_meta(d)
        role = m.get("probe_role")
        if not role:
            continue
        ep = load_episodes(d)
        c = sum(1 for v in ep["episodes"].values() if v) or ep["header_correct"]
        t = len(ep["episodes"]) or ep["header_total"]
        if t:
            per_role.setdefault(role, [0, 0])
            per_role[role][0] += c
            per_role[role][1] += t
    return {r: (c, t) for r, (c, t) in per_role.items()}


def _pct(xs, q):
    if not xs:
        return None
    s = sorted(xs)
    i = min(len(s) - 1, int(q * len(s)))
    return round(s[i], 3)


def collect_latency(root):
    """{system: {episode_id: {resume:[...], all:[...], out_tok:int, lat_sum:float}}}.

    From BFCL result files (latency + output_token_count are nested per-turn per-step).
    'resume' = the FIRST step of each turn -- the prefill AFTER the idle gap, where an
    evicted prefix must be RELOADED (joint, PCIe) or RECOMPUTED (decoupled/fp16 drop,
    prefill FLOPs). That first-step cost is where precision-as-admission pays or not.
    Main joint/decoupled/fp16 arms only; pooled over phi/seed.
    """
    per = defaultdict(lambda: defaultdict(lambda: {"resume": [], "all": [],
                                                   "out_tok": 0, "lat_sum": 0.0}))
    for d in sorted(glob.glob(os.path.join(root, "*"))):
        if not os.path.isdir(d) or not os.path.exists(os.path.join(d, "meta.json")):
            continue
        m = load_meta(d)
        s = m.get("system")
        if not s or m.get("homogeneous_role") or m.get("probe_role"):
            continue
        for rf in _result_files(d):
            for e in _read_jsonl(rf):
                if not isinstance(e, dict) or e.get("id") is None:
                    continue
                lat = e.get("latency") or []
                tok = e.get("output_token_count") or []
                rec = per[s][e["id"]]
                for turn in lat:
                    if isinstance(turn, list) and turn:
                        rec["resume"].append(turn[0])
                        rec["all"].extend(turn)
                        rec["lat_sum"] += sum(turn)
                for turn in tok:
                    if isinstance(turn, list):
                        rec["out_tok"] += sum(turn)
    return per


def latency_paired(per, a, b, B=3000, boot_seed=0):
    """Paired per-episode mean-resume-latency diff (a-b) + bootstrap CI (seconds)."""
    units = []
    ea, eb = per.get(a, {}), per.get(b, {})
    for i in set(ea) & set(eb):
        ra, rb = ea[i]["resume"], eb[i]["resume"]
        if ra and rb:
            units.append(sum(ra) / len(ra) - sum(rb) / len(rb))
    if not units:
        return None
    n = len(units)
    mean = sum(units) / n
    rng = random.Random(boot_seed)
    boot = sorted(sum(units[rng.randrange(n)] for _ in range(n)) / n for _ in range(B))
    lo = boot[int(0.025 * len(boot))]
    hi = boot[min(len(boot) - 1, int(0.975 * len(boot)))]
    return {"mean_resume_lat_diff_s": round(mean, 3), "n_paired": n,
            "ci95_s": [round(lo, 3), round(hi, 3)], "excludes_0": bool(lo > 0 or hi < 0)}


def collect_paired(root):
    """{(phi,seed): {system: {episode_id: passed}}} for the paired per-episode diff.

    Only the main joint/decoupled/fp16 arms (skips homog + probe cells). Because the
    three arms run the SAME episode ids at the SAME (phi,seed), we can difference them
    PER EPISODE, cancelling the dominant episode-difficulty variance -- so a real
    ~4-8pt compression effect is visible where the +/-7pt per-arm CIs cannot resolve it.
    """
    cells = defaultdict(lambda: defaultdict(dict))
    for d in sorted(glob.glob(os.path.join(root, "*"))):
        if not os.path.isdir(d) or not os.path.exists(os.path.join(d, "meta.json")):
            continue
        m = load_meta(d)
        sysname = m.get("system")
        if not sysname or m.get("homogeneous_role") or m.get("probe_role"):
            continue
        phi = m.get("gpu_mem_util")
        seed = m.get("seed", 0)
        for i, ok in load_episodes(d)["episodes"].items():
            cells[(phi, seed)][sysname][i] = ok
    return cells


def paired_diff(cells, a, b, B=3000, boot_seed=0):
    """Mean per-episode (pass_a - pass_b) over episodes where BOTH ran + bootstrap CI.

    Pairing removes episode-difficulty variance; the residual is the compression
    effect plus per-run batching noise. Reports McNemar discordant counts (a_saves =
    a passes where b fails) and whether the 95% CI excludes 0.
    """
    units = []
    for (phi, seed), sysmap in cells.items():
        ea, eb = sysmap.get(a, {}), sysmap.get(b, {})
        for i in set(ea) & set(eb):
            units.append((1 if ea[i] else 0, 1 if eb[i] else 0))
    if not units:
        return None
    n = len(units)
    diffs = [x - y for x, y in units]
    mean = sum(diffs) / n
    a_saves = sum(1 for x, y in units if x == 1 and y == 0)
    b_saves = sum(1 for x, y in units if x == 0 and y == 1)
    rng = random.Random(boot_seed)
    boot = []
    for _ in range(B):
        boot.append(sum(diffs[rng.randrange(n)] for _ in range(n)) / n)
    boot.sort()
    lo = boot[int(0.025 * len(boot))]
    hi = boot[min(len(boot) - 1, int(0.975 * len(boot)))]
    return {"mean_diff_pts": round(mean * 100, 2), "n_paired": n,
            "a_saves": a_saves, "b_saves": b_saves,
            "ci95_pts": [round(lo * 100, 2), round(hi * 100, 2)],
            "excludes_0": bool(lo > 0 or hi < 0)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--out", default=None)
    ap.add_argument("--hbm-total-gb", type=float, default=80.0,
                    help="physical HBM the phi fraction is of (for sessions-per-GB)")
    ap.add_argument("--iso-drop", type=float, default=0.01,
                    help="iso-task-success tolerance (abs task-success drop vs fp16)")
    ap.add_argument("--bfcl-data-dir", default=None)
    args = ap.parse_args()

    runs, meta_any, phys, prec = collect(args.root)

    # fp16 control success (lossless -> ~flat over phi): the accuracy reference.
    fp16_curve, _ = success_curve(runs, ("codesign_fp16", ""))
    fp16_success = (sum(fp16_curve.values()) / len(fp16_curve)) if fp16_curve else None
    floor = (fp16_success - args.iso_drop) if fp16_success is not None else None

    joint_curve, joint_eps = success_curve(runs, ("codesign_joint", ""))
    dec_curve, dec_eps = success_curve(runs, ("codesign_decoupled", ""))

    verdict = {
        "fp16_success": round(fp16_success, 4) if fp16_success is not None else None,
        "iso_floor": round(floor, 4) if floor is not None else None,
        "success_curves": {
            "codesign_joint": {str(k): round(v, 4) for k, v in sorted(joint_curve.items())},
            "codesign_decoupled": {str(k): round(v, 4) for k, v in sorted(dec_curve.items())},
            "codesign_fp16": {str(k): round(v, 4) for k, v in sorted(fp16_curve.items())},
        },
        "physical": {
            "codesign_joint": phys_summary(phys, prec, "codesign_joint"),
            "codesign_decoupled": phys_summary(phys, prec, "codesign_decoupled"),
        },
    }

    # ---- H-frontier ratio + bootstrap CI (the load-bearing number) ----
    if floor is not None and joint_curve and dec_curve:
        Hj = h_frontier(joint_curve, floor)
        Hd = h_frontier(dec_curve, floor)
        verdict["H_frontier"] = {
            "H_joint_phi": Hj, "H_decoupled_phi": Hd,
            "H_joint_hbm_gb": round(Hj * args.hbm_total_gb, 3) if Hj else None,
            "H_decoupled_hbm_gb": round(Hd * args.hbm_total_gb, 3) if Hd else None,
            "point_ratio": round(Hd / Hj, 4) if (Hj and Hd) else None,
        }
        boot = bootstrap_ratio(joint_eps, dec_eps, floor)
        verdict["H_frontier"]["bootstrap"] = boot

        # ---- mechanical GO / NO-GO ----
        gate = {"note": "GO iff ratio>=1.2 and bootstrap CI lower>1.1"}
        if boot:
            r, lo = boot["ratio_median"], boot["ci95"][0]
            gate["ratio_median"] = r
            gate["ci95_lower"] = lo
            if r >= 1.2 and lo > 1.1:
                gate["DECISION"] = "GO"
            elif r < 1.1:
                gate["DECISION"] = "NO-GO (demote to Bet2)"
            else:
                gate["DECISION"] = "INCONCLUSIVE (need more phi cells / seeds)"
        else:
            gate["DECISION"] = "INCONCLUSIVE (frontier not yet crossed at both ends)"
        verdict["GO_NO_GO"] = gate

    # ---- homogeneous-role control (must -> ~1.0) ----
    hj_curve, hj_eps = success_curve(runs, ("codesign_joint", "user"))
    hd_curve, hd_eps = success_curve(runs, ("codesign_decoupled", "user"))
    if floor is not None and hj_curve and hd_curve:
        Hhj, Hhd = h_frontier(hj_curve, floor), h_frontier(hd_curve, floor)
        verdict["homogeneous_control"] = {
            "H_joint_phi": Hhj, "H_decoupled_phi": Hhd,
            "ratio": round(Hhd / Hhj, 4) if (Hhj and Hhd) else None,
            "expect": "~1.0 (heterogeneity removed => joint cannot beat decoupled)",
        }

    # ---- LATENCY / THROUGHPUT at iso-accuracy (the co-design's latency-reframe test) ----
    lper = collect_latency(args.root)
    if lper:
        def _sys_lat(s):
            resume = [x for ep in lper.get(s, {}).values() for x in ep["resume"]]
            allst = [x for ep in lper.get(s, {}).values() for x in ep["all"]]
            tot_tok = sum(ep["out_tok"] for ep in lper.get(s, {}).values())
            tot_lat = sum(ep["lat_sum"] for ep in lper.get(s, {}).values())
            # physical drivers: recompute proxy = dropped blocks; PCIe = reload bytes
            drops = sum(pr.get("assigned_drop", 0) for (ss, h, p, se), pr in prec.items()
                        if ss == s and not h)
            reload_b = sum(pp.get("reload_bytes", 0) for (ss, h, p, se), pp in phys.items()
                           if ss == s and not h)
            return {
                "resume_p50_s": _pct(resume, 0.50), "resume_p95_s": _pct(resume, 0.95),
                "resume_mean_s": round(sum(resume) / len(resume), 3) if resume else None,
                "step_p95_s": _pct(allst, 0.95), "n_turns": len(resume),
                "throughput_tok_per_s": round(tot_tok / tot_lat, 2) if tot_lat else None,
                "dropped_blocks_recompute": drops, "reload_bytes_pcie": reload_b,
            }
        verdict["latency_throughput"] = {
            "per_system": {s: _sys_lat(s) for s in
                           ("codesign_joint", "codesign_decoupled", "codesign_fp16")
                           if s in lper},
            "paired_resume_latency": {
                "joint_minus_decoupled": latency_paired(lper, "codesign_joint", "codesign_decoupled"),
                "joint_minus_fp16": latency_paired(lper, "codesign_joint", "codesign_fp16"),
            },
            "note": "resume = first-step-per-turn latency (reload vs recompute after the "
                    "idle gap). GO-reframe iff joint p95-turn >=20% lower OR throughput "
                    ">=1.3x vs decoupled at iso-accuracy, CIs non-overlapping.",
        }

    # ---- per-ROLE int4-sensitivity probe (the gradient the co-design needs) ----
    probes = collect_probes(args.root)
    if probes and fp16_success is not None:
        rows = {}
        for role, (c, t) in probes.items():
            s = c / t if t else None
            rows[role] = {"success": round(s, 4) if s is not None else None, "n": t,
                          "int4_drop_vs_fp16_pts": round((fp16_success - s) * 100, 2)
                          if s is not None else None}
        drops = [r["int4_drop_vs_fp16_pts"] for r in rows.values()
                 if r["int4_drop_vs_fp16_pts"] is not None]
        gradient = (round(max(drops) - min(drops), 2) if len(drops) >= 2 else None)
        verdict["int4_role_sensitivity_probe"] = {
            "per_role": rows,
            "gradient_pts": gradient,
            "verdict": (
                "GRADIENT PRESENT (co-design can pay)" if gradient and gradient >= 2.0
                else "WEAK/NO GRADIENT (co-design unlikely to pay -> NO-GO risk)"
                if gradient is not None else "insufficient probe data"),
            "note": "gradient = max-min per-role int4 task-success drop; >=2pt spread "
                    "=> roles differ enough that per-block joint beats a static map",
        }

    # ---- PAIRED per-episode diff (the decisive, noise-cancelling number) ----
    pcells = collect_paired(args.root)
    pj = paired_diff(pcells, "codesign_joint", "codesign_decoupled")
    jf = paired_diff(pcells, "codesign_joint", "codesign_fp16")
    fd = paired_diff(pcells, "codesign_fp16", "codesign_decoupled")
    if pj or jf or fd:
        decision = "INSUFFICIENT paired data"
        if pj and jf:
            # GO signal: joint > decoupled (mean>0, CI excludes 0) AND joint ~= fp16
            # (paired diff CI includes 0 -> joint is as good as lossless).
            if pj["mean_diff_pts"] > 0 and pj["excludes_0"] and not jf["excludes_0"]:
                decision = "GO-track (joint>decoupled real above noise; joint~=fp16)"
            elif not pj["excludes_0"]:
                decision = "NO-GO (joint~=decoupled within paired CI -> non-separability not demonstrable)"
            else:
                decision = "MIXED (inspect paired diffs — joint!=fp16 or sign unexpected)"
        verdict["paired_analysis"] = {
            "joint_minus_decoupled": pj,   # decisive: want mean>0, CI excludes 0
            "joint_minus_fp16": jf,        # want mean~0, CI includes 0 (joint~=lossless)
            "fp16_minus_decoupled": fd,    # sanity: decoupled's loss vs lossless
            "DECISION": decision,
            "note": "paired diff cancels episode-difficulty variance; decisive co-design "
                    "signal = joint>decoupled (CI excludes 0) AND joint~=fp16 (CI incl 0)",
        }

    # ---- per-(system,phi) task-success table with Wilson CI ----
    table = []
    for (sysname, homog), phimap in runs.items():
        for phi, seed_map in phimap.items():
            c, t, _ = pooled_success(seed_map)
            lo, hi = wilson_ci(c, t)
            table.append({"system": sysname, "homog": homog or None, "phi": phi,
                          "success": round(c / t, 4) if t else None,
                          "n": t, "wilson_ci": [round(lo, 4), round(hi, 4)]})
    verdict["success_table"] = sorted(
        table, key=lambda r: (r["system"], r["homog"] or "", r["phi"] or 0))

    txt = json.dumps(verdict, indent=2)
    print(txt)
    if args.out:
        with open(args.out, "w") as f:
            f.write(txt)


if __name__ == "__main__":
    main()
