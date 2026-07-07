# SPDX-License-Identifier: Apache-2.0
"""Continuum-D KEYSTONE analysis: p95/p99 turn-latency + JCT with bootstrap CIs.

Pools per-request turn latency (`total_s`, warm/error excluded) and per-job JCT
across seeds for each (gpu, condition, jps, dram) cell, computes p95/p99/mean
with 10k-resample bootstrap 95% CIs, then applies the E1 go/no-go:

  GO iff job_aware (and/or job_aware_warm) beats lru on end-to-end p95-turn by
  >=15% with NON-OVERLAPPING bootstrap CIs, at jps>=6.

Data-driven: globs <root>/**/*_dram*_jps*_seed*.json (also tolerates the older
no-seed names). Never hardcodes the condition/gpu list, so partial results
analyze cleanly.

Usage:
  python3 benchmarks/continuum_d_keystone_analyze.py --root results-pace/continuum-d-keystone
"""

import argparse
import json
import random
from collections import defaultdict
from pathlib import Path

B = 10_000            # bootstrap resamples
GO_THRESHOLD = 0.15   # E1: >=15% p95-turn improvement (job_aware vs lru)
E2_GO_A = 0.10        # E2: job_aware must beat mori_proxy p95-turn by >=10%


def pctl(xs, q):
    if not xs:
        return None
    ys = sorted(xs)
    if len(ys) == 1:
        return ys[0]
    pos = q * (len(ys) - 1)
    lo = int(pos)
    hi = min(lo + 1, len(ys) - 1)
    return ys[lo] + (ys[hi] - ys[lo]) * (pos - lo)


def boot_ci(xs, statfn, b=B, alpha=0.05, seed=12345):
    """95% bootstrap CI for statfn over sample xs (b resamples)."""
    if len(xs) < 2:
        v = statfn(xs) if xs else None
        return (v, v, v)
    rng = random.Random(seed)
    n = len(xs)
    point = statfn(xs)
    reps = []
    for _ in range(b):
        sample = [xs[rng.randrange(n)] for _ in range(n)]
        reps.append(statfn(sample))
    reps.sort()
    lo = reps[int((alpha / 2) * b)]
    hi = reps[int((1 - alpha / 2) * b) - 1]
    return (point, lo, hi)


def _gpu_from_dir(name):
    for tag in ("h100", "h200", "a100_80gb", "a100-80", "a100", "l40s", "5090"):
        if f"_{tag}_" in name or name.endswith(tag):
            return tag
    return "?"


def load_cells(root: Path):
    """cell key -> {'turn': [...], 'jct': [...], 'seeds': set, 'meta': {...},
                    'policy_stats': [...], 'ext_hit': [...]}"""
    cells = defaultdict(lambda: {"turn": [], "jct": [], "seeds": set(),
                                 "policy_stats": [], "ext_hit": [], "n_err": 0,
                                 "files": 0})
    for f in sorted(root.rglob("*_dram*_jps*.json")):
        try:
            d = json.loads(f.read_text())
        except (json.JSONDecodeError, OSError):
            continue
        s = d.get("summary", {})
        if not s:
            continue
        cfg = s.get("config", {})
        cond = s.get("condition")
        jps = cfg.get("jps")
        dram = cfg.get("dram_gb")
        seed = cfg.get("seed", "na")
        gpu = _gpu_from_dir(f.parent.name)
        key = (gpu, cond, jps, dram)
        c = cells[key]
        c["files"] += 1
        c["seeds"].add(seed)
        c["n_err"] += s.get("n_err", 0)
        # per-request turn latency: total_s of real (non-warm, non-error) turns
        for r in d.get("requests", []):
            if "error" in r or "warm" in r.get("tag", ""):
                continue
            t = r.get("total_s")
            if t is not None:
                c["turn"].append(t)
        for j in d.get("jobs", []):
            if j.get("jct_s") is not None:
                c["jct"].append(j["jct_s"])
        ps = s.get("policy_stats") or {}
        if ps:
            c["policy_stats"].append(ps)
        m = s.get("metrics", {})
        q = next((v for k, v in m.items()
                  if "external_prefix_cache_queries" in k and "created" not in k), None)
        h = next((v for k, v in m.items()
                  if "external_prefix_cache_hits" in k and "created" not in k), None)
        if q:
            c["ext_hit"].append(100.0 * (h or 0) / q)
    return cells


def summarize(cells):
    rows = {}
    for key, c in cells.items():
        turn, jct = c["turn"], c["jct"]
        rows[key] = {
            "n_seeds": len(c["seeds"]),
            "n_turn": len(turn),
            "n_jct": len(jct),
            "n_err": c["n_err"],
            "p95_turn": boot_ci(turn, lambda x: pctl(x, 0.95)),
            "p99_turn": boot_ci(turn, lambda x: pctl(x, 0.99)),
            "mean_jct": boot_ci(jct, lambda x: sum(x) / len(x)),
            "p95_jct": boot_ci(jct, lambda x: pctl(x, 0.95)),
            "ext_hit_pct": (sum(c["ext_hit"]) / len(c["ext_hit"])
                            if c["ext_hit"] else None),
            "policy_stats": c["policy_stats"],
        }
    return rows


def _fmt(ci, nd=3):
    if ci is None or ci[0] is None:
        return "-"
    return f"{ci[0]:.{nd}f} [{ci[1]:.{nd}f},{ci[2]:.{nd}f}]"


def verdict(rows, min_jps=6):
    """Apply go/no-go per (gpu, jps>=min_jps) using p95_turn CIs."""
    lines = ["", "=== E1 GO/NO-GO (p95 turn-latency, job_aware/+warm vs lru) ==="]
    by_gj = defaultdict(dict)
    for (gpu, cond, jps, dram), r in rows.items():
        by_gj[(gpu, jps, dram)][cond] = r
    any_go = False
    for (gpu, jps, dram), conds in sorted(by_gj.items(), key=lambda x: str(x[0])):
        if jps is None or jps < min_jps:
            continue
        lru = conds.get("lru")
        if not lru or lru["p95_turn"][0] is None:
            continue
        lru_p, lru_lo, lru_hi = lru["p95_turn"]
        for cand in ("job_aware", "job_aware_warm"):
            r = conds.get(cand)
            if not r or r["p95_turn"][0] is None:
                continue
            cp, clo, chi = r["p95_turn"]
            impr = (lru_p - cp) / lru_p if lru_p else 0.0
            non_overlap = chi < lru_lo           # candidate CI entirely below lru CI
            go = (impr >= GO_THRESHOLD) and non_overlap
            any_go = any_go or go
            lines.append(
                f"[{gpu} jps{jps} dram{dram}] {cand}: p95={cp:.3f}"
                f"[{clo:.3f},{chi:.3f}]s  vs lru {lru_p:.3f}"
                f"[{lru_lo:.3f},{lru_hi:.3f}]s  "
                f"impr={impr*100:+.1f}%  non_overlap={non_overlap}  "
                f"=> {'GO' if go else 'no-go'}")
    lines.append("")
    lines.append(f"OVERALL: {'GO (>=1 cell passes)' if any_go else 'NO-GO (flat / overlapping / <15%)'}")
    return "\n".join(lines)


def e2_verdict(rows, min_jps=6):
    """E2 NOVELTY GATE (apply at jps>=6, per gpu/dram cell) on p95_turn CIs.

    GO iff BOTH, in the SAME cell:
      (a) job_aware beats mori_proxy by >=E2_GO_A with NON-OVERLAPPING CIs
          (job_aware p95 CI-high < mori_proxy p95 CI-low), AND
      (b) job_aware_metadata_off is significantly WORSE than full job_aware
          (job_aware p95 CI-high < metadata_off p95 CI-low).
    NO-GO reasons:
      * no cell passes (a): novelty collapses to "MORI + tags" -> pivot to Backup.
      * no cell passes (b): the exact tags don't matter -> the story is wrong.
    """
    lines = ["", "=== E2 NOVELTY GATE (job_aware vs mori_proxy + metadata-off "
             "ablation; p95 turn-latency) ==="]
    by_gj = defaultdict(dict)
    for (gpu, cond, jps, dram), r in rows.items():
        by_gj[(gpu, jps, dram)][cond] = r
    any_a = any_b = any_cell_go = False
    for (gpu, jps, dram), conds in sorted(by_gj.items(), key=lambda x: str(x[0])):
        if jps is None or jps < min_jps:
            continue
        ja = conds.get("job_aware")
        if not ja or ja["p95_turn"][0] is None:
            continue
        jp, jlo, jhi = ja["p95_turn"]
        a_go = b_go = False
        # (a) job_aware vs mori_proxy
        mori = conds.get("mori_proxy")
        if mori and mori["p95_turn"][0] is not None:
            mp, mlo, mhi = mori["p95_turn"]
            impr_a = (mp - jp) / mp if mp else 0.0
            nonov_a = jhi < mlo
            a_go = (impr_a >= E2_GO_A) and nonov_a
            lines.append(
                f"[{gpu} jps{jps} dram{dram}] (a) job_aware p95={jp:.3f}"
                f"[{jlo:.3f},{jhi:.3f}]s  vs mori_proxy {mp:.3f}"
                f"[{mlo:.3f},{mhi:.3f}]s  impr={impr_a*100:+.1f}%  "
                f"non_overlap={nonov_a}  => {'PASS' if a_go else 'fail'}")
        else:
            lines.append(f"[{gpu} jps{jps} dram{dram}] (a) mori_proxy missing")
        # (b) metadata-off ablation vs full job_aware
        moff = conds.get("job_aware_metadata_off")
        if moff and moff["p95_turn"][0] is not None:
            fp, flo, fhi = moff["p95_turn"]
            degr_b = (fp - jp) / fp if fp else 0.0  # how much worse the ablation is
            worse_b = jhi < flo                     # job_aware CI entirely below
            b_go = worse_b
            lines.append(
                f"[{gpu} jps{jps} dram{dram}] (b) metadata_off p95={fp:.3f}"
                f"[{flo:.3f},{fhi:.3f}]s  vs job_aware {jp:.3f}"
                f"[{jlo:.3f},{jhi:.3f}]s  ablation_worse_by={degr_b*100:+.1f}%  "
                f"non_overlap={worse_b}  => {'PASS' if b_go else 'fail'}")
        else:
            lines.append(f"[{gpu} jps{jps} dram{dram}] (b) metadata_off missing")
        cell_go = a_go and b_go
        lines.append(f"[{gpu} jps{jps} dram{dram}] CELL: "
                     f"{'GO (a AND b)' if cell_go else 'no-go'}")
        any_a = any_a or a_go
        any_b = any_b or b_go
        any_cell_go = any_cell_go or cell_go
    lines.append("")
    if any_cell_go:
        overall = "GO (>=1 cell: job_aware beats mori_proxy AND requires exact tags)"
    elif not any_a:
        overall = ("NO-GO: job_aware ~= mori_proxy (novelty collapses to "
                   "'MORI + tags' -> pivot to Backup)")
    elif not any_b:
        overall = ("NO-GO: metadata_off ~= full job_aware (exact tags don't "
                   "matter -> the story is wrong)")
    else:
        overall = ("NO-GO: (a) and (b) never co-occur in a single cell "
                   "(inspect per-cell breakdown)")
    lines.append(f"OVERALL E2: {overall}")
    return "\n".join(lines)


def table(rows):
    hdr = ("| gpu | cond | jps | dram | seeds | ok-err | p95 turn s [CI] | "
           "p99 turn s [CI] | mean JCT s [CI] | ext hit% |")
    sep = "|" + "---|" * 10
    out = [hdr, sep]
    for (gpu, cond, jps, dram), r in sorted(rows.items(), key=lambda x: str(x[0])):
        eh = "-" if r["ext_hit_pct"] is None else f"{r['ext_hit_pct']:.1f}"
        out.append(
            f"| {gpu} | {cond} | {jps} | {dram} | {r['n_seeds']} | "
            f"{r['n_turn']}-{r['n_err']} | {_fmt(r['p95_turn'])} | "
            f"{_fmt(r['p99_turn'])} | {_fmt(r['mean_jct'], 2)} | {eh} |")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-jps", type=float, default=6.0)
    ap.add_argument("--root", required=True)
    ap.add_argument("--md", default=None)
    args = ap.parse_args()
    cells = load_cells(Path(args.root))
    if not cells:
        print("no keystone result files under", args.root)
        return
    rows = summarize(cells)
    tbl = table(rows)
    vd = verdict(rows, min_jps=args.min_jps)
    e2 = e2_verdict(rows, min_jps=args.min_jps)
    print(tbl)
    print(vd)
    print(e2)
    # policy stats digest (job-aware family + mori proxy)
    stat_conds = ("job_aware", "job_aware_warm", "job_aware_metadata_off",
                  "mori_proxy")
    ps_lines = ["\n=== policy.stats (last cumulative per cell) ==="]
    for (gpu, cond, jps, dram), r in sorted(rows.items(), key=lambda x: str(x[0])):
        if cond in stat_conds and r["policy_stats"]:
            ps_lines.append(f"[{gpu} {cond} jps{jps} dram{dram}] "
                            f"{r['policy_stats'][-1]}")
    print("\n".join(ps_lines))
    if args.md:
        Path(args.md).write_text(
            "# Continuum-D results — bootstrap CIs (auto-generated)\n\n"
            + tbl + "\n\n```\n" + vd + "\n\n" + e2 + "\n\n"
            + "\n".join(ps_lines) + "\n```\n")
        print(f"\nwrote {args.md}")


if __name__ == "__main__":
    main()
