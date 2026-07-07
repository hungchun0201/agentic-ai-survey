#!/usr/bin/env python3
"""ONE analyzer for every number in paper-mainline. Runs entirely from the
snapshot trees committed under results/mainline/ — no cluster access needed.

Usage:
    python3 analyze_mainline.py [--root results/mainline] [--boot N]

Emits every paper table (ladder H100/A100, mechanism counters, codesign,
hybrid, synthetic-control, loose-budget control, BFCL floor) and, for each
headline p95, BOTH CI treatments:
  - per-turn bootstrap (turns resampled i.i.d.) — the paper's original CIs
  - session-clustered bootstrap (resample (seed, session) clusters with
    replacement, keeping each session's turns together) — the conservative
    treatment for correlated turns (cf. Field & Welsh 2007).

Every emitted line is the source of truth for the corresponding paper number.
"""
import argparse
import glob
import json
import os
import random
import statistics as st

random.seed(0)


def p95(xs):
    xs = sorted(xs)
    return xs[max(0, int(0.95 * len(xs)) - 1)]


def load_cells(root, pattern):
    """-> list of per-seed dicts {seed_dir, turns:[(session, total_s)], summary}"""
    cells = []
    for d in sorted(glob.glob(os.path.join(root, pattern))):
        js = [j for j in glob.glob(d + "/*.json")]
        if not js:
            continue
        data = json.load(open(js[0]))
        turns = [(r["tag"].split("/")[0], r["total_s"])
                 for r in data.get("requests", []) if r.get("total_s") is not None]
        cells.append({"dir": d, "turns": turns, "summary": data.get("summary", {}),
                      "jobs": data.get("jobs", [])})
    return cells


def boot_turn(vals, n):
    out = []
    for _ in range(n):
        s = [random.choice(vals) for _ in range(len(vals))]
        out.append(p95(s))
    out.sort()
    return out[int(0.025 * n)], out[int(0.975 * n)]


def boot_cluster(cells, n):
    """Resample (seed, session) clusters with replacement."""
    clusters = []
    for i, c in enumerate(cells):
        by = {}
        for sess, v in c["turns"]:
            by.setdefault((i, sess), []).append(v)
        clusters.extend(by.values())
    out = []
    for _ in range(n):
        pool = []
        for _ in range(len(clusters)):
            pool.extend(random.choice(clusters))
        out.append(p95(pool))
    out.sort()
    return out[int(0.025 * n)], out[int(0.975 * n)]


def hit_rate(cells):
    h = q = 0.0
    for c in cells:
        for k, v in c["summary"].get("metrics", {}).items():
            if k.startswith("vllm:external_prefix_cache_hits_total"):
                h += v
            elif k.startswith("vllm:external_prefix_cache_queries_total"):
                q += v
    return 100.0 * h / q if q else None


def counters(cells, key):
    vs = [c["summary"].get("policy_stats", {}).get(key)
          for c in cells if c["summary"].get("policy_stats")]
    vs = [v for v in vs if v is not None]
    return (min(vs), max(vs)) if vs else None


def cell_line(root, pattern, label, nboot, jct=False):
    cells = load_cells(root, pattern)
    if not cells:
        return f"{label:34s} NO DATA ({pattern})"
    pooled = [v for c in cells for _, v in c["turns"]]
    nerr = sum(c["summary"].get("n_err", 0) for c in cells)
    lo, hi = boot_turn(pooled, nboot)
    clo, chi = boot_cluster(cells, nboot)
    h = hit_rate(cells)
    hs = f"hit={h:.2f}%" if h is not None else "hit=n/a"
    out = (f"{label:34s} seeds={len(cells)} turns={len(pooled)} err={nerr} "
           f"p95={p95(pooled):7.3f} turnCI=[{lo:.3f},{hi:.3f}] "
           f"clustCI=[{clo:.3f},{chi:.3f}] {hs}")
    if jct:
        jcts = [j["jct_s"] for c in cells for j in c["jobs"] if j.get("jct_s") is not None]
        mu = st.mean(jcts)
        bs = sorted(st.mean([random.choice(jcts) for _ in jcts]) for _ in range(nboot))
        out += f" JCT={mu:.1f} [{bs[int(0.025*nboot)]:.1f},{bs[int(0.975*nboot)]:.1f}]"
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.path.dirname(os.path.abspath(__file__)))
    ap.add_argument("--boot", type=int, default=2000)
    a = ap.parse_args()
    R, N = a.root, a.boot

    print("== Ladder (H100, real SWE replay, jps0.5 dram8) ==")
    for cond, label in [("job_aware", "Tenure (ours)"),
                        ("job_aware_metadata_off", "ours w/o lifecycle tags"),
                        ("continuum_ttl", "Continuum-TTL"),
                        ("marconi_util", "Marconi-utility"),
                        ("lru", "LRU offload"),
                        ("mori_proxy", "MORI-idleness"),
                        ("no_offload", "no DRAM tier")]:
        print(cell_line(R, f"m1swe_snapshots/m1swe_h100_{cond}_jps0.5_dram8_seed*", label, N))

    print("\n== Ladder (A100-80 replication) ==")
    for cond in ["job_aware", "job_aware_metadata_off", "continuum_ttl",
                 "marconi_util", "lru", "mori_proxy", "no_offload"]:
        print(cell_line(R, f"m1swe_snapshots/m1swe_a100-80_{cond}_jps0.5_dram8_seed*", cond, N, jct=True))

    print("\n== Mechanism counters (Tenure, H100, per-seed min-max) ==")
    cells = load_cells(R, "m1swe_snapshots/m1swe_h100_job_aware_jps0.5_dram8_seed*")
    for key in ["evicted_finished", "evicted_overdue", "evicted_far_wakeup",
                "evicted_lru", "admission_refusals"]:
        print(f"  {key}: {counters(cells, key)}")

    print("\n== Precision tier (codesign, measured negative) ==")
    for sku in ["h100", "a100-80"]:
        for cond in ["codesign_fp16", "codesign_joint"]:
            for dram in ["dram4", "dram8"]:
                print(cell_line(R, f"m1swe_snapshots/m1swe_{sku}_{cond}_jps0.5_{dram}_seed*",
                                f"{sku} {cond} {dram}", N))

    print("\n== Hybrid column (Falcon-H1-7B, H100) ==")
    for cond in ["job_aware", "lru"]:
        print(cell_line(R, f"m4hyb_snapshots/m4hyb_h100_{cond}_jps0.5_dram8_seed*",
                        f"hybrid {cond}", N, jct=True))

    print("\n== Synthetic-gap control (E2: tags null + MORI flattered) ==")
    for cond in ["job_aware", "job_aware_metadata_off", "lru", "mori_proxy"]:
        for jps in ["jps6", "jps10"]:
            print(cell_line(R, f"e2_synth_snapshots/e2_a100_80gb_{cond}_{jps}_dram8_seed*",
                            f"E2 {cond} {jps}", N))

    print("\n== Loose-budget control (E1 keystone H200, dram8 vs dram40) ==")
    for cond in ["job_aware", "lru", "no_offload"]:
        for dram in ["dram8", "dram40", "dram0"]:
            line = cell_line(R, f"e1_keystone_snapshots/cd_h200_{cond}_jps2_{dram}",
                             f"H200 {cond} {dram}", N)
            if "NO DATA" not in line:
                print(line)

    print("\n== Sweeps (H100 real SWE replay; ours rows use the O(1)-accounting")
    print("   implementation at dram16/32 [see coldfix2]; all others unaffected) ==")
    for jps in ["0.25", "0.5", "0.75", "1.0"]:
        for cond in ["job_aware", "lru"]:
            root_pat = ("m1swe_snapshots/m1swe_h100_{c}_jps0.5_dram8_seed*" if jps == "0.5"
                        else "sweep_snapshots/swp_h100_{c}_jps" + jps + "_dram8_seed*")
            print(cell_line(R, root_pat.format(c=cond), f"jps{jps} {cond}", N))
    OURS_D = {"4": "sweep_snapshots/swp_h100_job_aware_jps0.5_dram4_seed*",
              "8": "m1swe_snapshots/m1swe_h100_job_aware_jps0.5_dram8_seed*",
              "16": "coldfix2_snapshots/fix16_h100_job_aware_jps0.5_dram16_seed*",
              "32": "coldfix2_snapshots/fix32_h100_job_aware_jps0.5_dram32_seed*"}
    LRU_D = {"4": "sweep_snapshots/swp_h100_lru_jps0.5_dram4_seed*",
             "8": "m1swe_snapshots/m1swe_h100_lru_jps0.5_dram8_seed*",
             "16": "sweep_snapshots/swp_h100_lru_jps0.5_dram16_seed*",
             "32": "sweep_snapshots/swp_h100_lru_jps0.5_dram32_seed*"}
    for dram in ["4", "8", "16", "32"]:
        tag = " (O1 impl)" if dram in ("16", "32") else ""
        print(cell_line(R, OURS_D[dram], f"dram{dram} ours{tag}", N))
        print(cell_line(R, LRU_D[dram], f"dram{dram} lru", N))
    print("  -- baseline sensitivity --")
    for lbl, pat in [("marconi a=0.25", "sweep_snapshots/swpA025_h100_marconi_util_jps0.5_dram8_seed*"),
                     ("marconi a=4.0", "sweep_snapshots/swpA4_h100_marconi_util_jps0.5_dram8_seed*"),
                     ("ttl slack 1.0", "sweep_snapshots/swpS1_h100_continuum_ttl_jps0.5_dram8_seed*"),
                     ("ttl slack 3.0", "sweep_snapshots/swpS3_h100_continuum_ttl_jps0.5_dram8_seed*")]:
        print(cell_line(R, pat, lbl, N))

    print("\n== TraceLab second family (real Claude Code, real gaps, H100) ==")
    for cond in ["job_aware", "lru", "continuum_ttl", "no_offload"]:
        print(cell_line(R, f"tracelab_snapshots/tl_h100_{cond}_jps0.5_dram8_seed*",
                        f"TL {cond}", N))
    for jps in ["0.125", "0.25"]:
        for cond in ["job_aware", "lru"]:
            print(cell_line(R, f"tracelab_snapshots/tl_h100_{cond}_jps{jps}_dram8_seed*",
                            f"TL jps{jps} {cond}", N))
    for cond in ["job_aware", "lru"]:
        print(cell_line(R, f"tracelab_snapshots/tl_h100_{cond}_jps0.25_dram32_seed*",
                        f"TL dram32 {cond}", N))

    print("\n== Throughput / PCIe traffic (headline cells) ==")
    def sysmetrics(pat, lbl):
        cells = load_cells(R, pat)
        if not cells: return
        wall = sum(c["summary"].get("wall_s", 0) for c in cells)
        turns = sum(len(c["turns"]) for c in cells)
        g2c = c2g = 0.0
        for c in cells:
            for k, v in c["summary"].get("metrics", {}).items():
                if k.startswith("vllm:kv_offload_total_bytes_total") and "GPU_to_CPU" in k:
                    g2c += v
                elif k.startswith("vllm:kv_offload_total_bytes_total") and "CPU_to_GPU" in k:
                    c2g += v
        print(f"  {lbl}: {turns/wall:.2f} turns/s  store={g2c/1e9:.1f}GB reload={c2g/1e9:.1f}GB")
    for cond in ["job_aware", "job_aware_metadata_off", "lru", "continuum_ttl", "no_offload"]:
        sysmetrics(f"m1swe_snapshots/m1swe_h100_{cond}_jps0.5_dram8_seed*", f"H100 {cond}")

    print("\n== Signal-matched last_turn baselines (no gate) ==")
    for cond in ["marconi_lt", "mori_lt", "ttl_lt"]:
        print(cell_line(R, f"coldfix3_snapshots/sm_h100_{cond}_jps0.5_dram8_seed*",
                        f"coldfix3 {cond}", N))
    for cond in ["job_aware", "lru"]:
        print(cell_line(R, f"coldfix3_snapshots/seeds3_h100_{cond}_jps0.5_dram8_seed*",
                        f"coldfix3 seeds6-8 {cond}", N))
    print(cell_line(R, "coldfix3_snapshots/tlfu_h100_tinylfu_adm_jps0.5_dram8_seed*",
                    "coldfix3 TinyLFU-admission", N))
    print("\n== L40S third SKU (landing) ==")
    for cond in ["job_aware", "lru"]:
        print(cell_line(R, f"m1swe_snapshots/m1swe_l40s_{cond}_jps0.5_dram8_seed*",
                        f"L40S {cond}", N))

    print("\n== Latency decomposition (ttft vs decode, H100 headline) ==")
    for cond in ["job_aware", "lru"]:
        cells = load_cells(R, f"m1swe_snapshots/m1swe_h100_{cond}_jps0.5_dram8_seed*")
        import glob as _g, json as _j
        tt, dec = [], []
        for c in cells:
            d = _j.load(open(_g.glob(c["dir"] + "/*.json")[0]))
            for r in d["requests"]:
                if r.get("total_s") is not None and r.get("ttft_s") is not None:
                    tt.append(r["ttft_s"]); dec.append(r["total_s"] - r["ttft_s"])
        tt.sort(); dec.sort(); n = len(tt)
        print(f"  {cond}: ttft p50={tt[n//2]:.3f} p95={tt[int(.95*n)]:.3f} | "
              f"decode p50={dec[n//2]:.3f} p95={dec[int(.95*n)]:.3f}")

    print("\n== Signal decomposition / hint robustness (coldfix grid) ==")
    for tag in ["hn_pm25", "hn_pm50", "hn_random", "hn_missing50", "hn_none", "nolt"]:
        print(cell_line(R, f"coldfix_snapshots/{tag}_h100_job_aware_jps0.5_dram8_seed*",
                        f"coldfix {tag}", N))
    print(cell_line(R, "coldfix_snapshots/lrult_h100_lru_lastturn_jps0.5_dram8_seed*",
                    "coldfix lru+last_turn (no gate)", N))
    print("  -- coldfix2: O(1)-accounting sweep + fairness baselines + bound --")
    for tag, d in [("fix8", "dram8"), ("fix16", "dram16"), ("fix32", "dram32"), ("fix64", "dram64")]:
        print(cell_line(R, f"coldfix2_snapshots/{tag}_h100_job_aware_jps0.5_{d}_seed*",
                        f"coldfix2 ours {d} (O1)", N))
    print(cell_line(R, "coldfix2_snapshots/cap64_h100_lru_jps0.5_dram64_seed*",
                    "coldfix2 LRU dram64 (residency bound)", N))
    print(cell_line(R, "coldfix2_snapshots/gttl_h100_gated_ttl_jps0.5_dram8_seed*",
                    "coldfix2 gate+TTL", N))
    for tag in ["lt_missing50", "lt_falsepos"]:
        print(cell_line(R, f"coldfix2_snapshots/{tag}_h100_job_aware_jps0.5_dram8_seed*",
                        f"coldfix2 {tag}", N))
    for cond in ["job_aware", "lru", "no_offload"]:
        print(cell_line(R, f"coldfix2_snapshots/seeds2_h100_{cond}_jps0.5_dram8_seed*",
                        f"coldfix2 seeds3-5 {cond}", N))

    print("\n== Paired-delta bootstrap (conditions share per-seed arrival schedules) ==")
    def paired_delta(pat_a, pat_b, label):
        A = load_cells(R, pat_a); B = load_cells(R, pat_b)
        if not A or not B or len(A) != len(B):
            print(f"  {label}: incomplete"); return
        # sessions paired by (seed idx, session id); bootstrap session pairs
        pairs = []
        for i, (a, b) in enumerate(zip(A, B)):
            sa, sb = {}, {}
            for sess, v in a["turns"]: sa.setdefault(sess, []).append(v)
            for sess, v in b["turns"]: sb.setdefault(sess, []).append(v)
            for sess in set(sa) & set(sb):
                pairs.append((sa[sess], sb[sess]))
        ds = []
        for _ in range(2000):
            pa, pb = [], []
            for _ in range(len(pairs)):
                x, y = random.choice(pairs); pa.extend(x); pb.extend(y)
            ds.append(p95(pa) - p95(pb))
        ds.sort()
        point = p95([v for c in A for _, v in c["turns"]]) - p95([v for c in B for _, v in c["turns"]])
        print(f"  {label}: delta_p95={point:+.3f}s pairedCI=[{ds[int(0.025*len(ds))]:+.3f},{ds[int(0.975*len(ds))]:+.3f}] (n_pairs={len(pairs)})")

    paired_delta("m1swe_snapshots/m1swe_h100_job_aware_jps0.5_dram8_seed*",
                 "m1swe_snapshots/m1swe_h100_lru_jps0.5_dram8_seed*", "H100 ours-vs-LRU")
    paired_delta("m1swe_snapshots/m1swe_h100_job_aware_metadata_off_jps0.5_dram8_seed*",
                 "m1swe_snapshots/m1swe_h100_lru_jps0.5_dram8_seed*", "H100 tagsoff-vs-LRU")
    paired_delta("m1swe_snapshots/m1swe_h100_job_aware_jps0.5_dram8_seed*",
                 "m1swe_snapshots/m1swe_h100_job_aware_metadata_off_jps0.5_dram8_seed*", "H100 ours-vs-tagsoff")
    paired_delta("m1swe_snapshots/m1swe_a100-80_job_aware_jps0.5_dram8_seed*",
                 "m1swe_snapshots/m1swe_a100-80_lru_jps0.5_dram8_seed*", "A100 ours-vs-LRU")
    paired_delta("m4hyb_snapshots/m4hyb_h100_job_aware_jps0.5_dram8_seed*",
                 "m4hyb_snapshots/m4hyb_h100_lru_jps0.5_dram8_seed*", "hybrid ours-vs-LRU")
    paired_delta("tracelab_snapshots/tl_h100_job_aware_jps0.5_dram8_seed*",
                 "tracelab_snapshots/tl_h100_lru_jps0.5_dram8_seed*", "TraceLab ours-vs-LRU")

    print("\n== Paired deltas: each baseline vs the no-tier control ==")
    for cond, lbl in [("lru", "LRU-vs-notier"), ("continuum_ttl", "TTL-vs-notier"),
                      ("marconi_util", "Marconi-vs-notier"), ("mori_proxy", "MORI-vs-notier")]:
        paired_delta(f"m1swe_snapshots/m1swe_h100_{cond}_jps0.5_dram8_seed*",
                     "m1swe_snapshots/m1swe_h100_no_offload_jps0.5_dram8_seed*",
                     f"H100 {lbl}")
    for cond, lbl in [("lru", "TL LRU-vs-notier"), ("continuum_ttl", "TL TTL-vs-notier")]:
        paired_delta(f"tracelab_snapshots/tl_h100_{cond}_jps0.5_dram8_seed*",
                     "tracelab_snapshots/tl_h100_no_offload_jps0.5_dram8_seed*",
                     lbl)

    print("\n== Error-inclusive p95 (errored turns counted as +inf) ==")
    for pat, lbl in [("m1swe_snapshots/m1swe_h100_marconi_util_jps0.5_dram8_seed*", "H100 Marconi"),
                     ("m1swe_snapshots/m1swe_h100_mori_proxy_jps0.5_dram8_seed*", "H100 MORI"),
                     ("m4hyb_snapshots/m4hyb_h100_job_aware_jps0.5_dram8_seed*", "hybrid ours"),
                     ("tracelab_snapshots/tl_h100_lru_jps0.5_dram8_seed*", "TL lru")]:
        cells = load_cells(R, pat)
        if not cells: continue
        vals = [v for c in cells for _, v in c["turns"]]
        nerr = sum(c["summary"].get("n_err", 0) for c in cells)
        vals_inf = sorted(vals) + [float("inf")] * nerr
        p95_inf = vals_inf[max(0, int(0.95 * len(vals_inf)) - 1)]
        print(f"  {lbl}: p95_retained={p95(vals):.3f} p95_err_as_inf={p95_inf:.3f} (n_err={nerr})")

    print("\n== Per-seed p95 table (headline conditions, H100) ==")
    for cond in ["job_aware", "job_aware_metadata_off", "lru", "no_offload"]:
        cells = load_cells(R, f"m1swe_snapshots/m1swe_h100_{cond}_jps0.5_dram8_seed*")
        per = [f"{p95([v for _, v in c['turns']]):.2f}" for c in cells]
        print(f"  {cond}: " + " / ".join(per))

    # raw paired job-level deltas exported for the artifact
    import csv
    exp = os.path.join(R, "paired_job_deltas.csv")
    with open(exp, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["column", "seed_idx", "job", "jct_ours_s", "jct_lru_s", "delta_pct"])
        for col, pa, pb in [
            ("h100_swe", "m1swe_snapshots/m1swe_h100_job_aware_jps0.5_dram8_seed*",
             "m1swe_snapshots/m1swe_h100_lru_jps0.5_dram8_seed*"),
            ("a100_swe", "m1swe_snapshots/m1swe_a100-80_job_aware_jps0.5_dram8_seed*",
             "m1swe_snapshots/m1swe_a100-80_lru_jps0.5_dram8_seed*"),
            ("tracelab", "tracelab_snapshots/tl_h100_job_aware_jps0.5_dram8_seed*",
             "tracelab_snapshots/tl_h100_lru_jps0.5_dram8_seed*")]:
            A, B = load_cells(R, pa), load_cells(R, pb)
            for i, (a, b) in enumerate(zip(A, B)):
                ja = {j["job"]: j["jct_s"] for j in a["jobs"] if j.get("jct_s")}
                jb = {j["job"]: j["jct_s"] for j in b["jobs"] if j.get("jct_s")}
                for k in sorted(set(ja) & set(jb)):
                    w.writerow([col, i, k, round(ja[k], 2), round(jb[k], 2),
                                round((jb[k] - ja[k]) / jb[k] * 100, 2)])
    print("\n(raw paired job deltas -> results/mainline/paired_job_deltas.csv)")

    print("\n== Per-session fairness (paired per-job JCT deltas, ours vs LRU) ==")
    def fairness(pat_a, pat_b, label):
        A = load_cells(R, pat_a); B = load_cells(R, pat_b)
        if not A or not B or len(A) != len(B):
            print(f"  {label}: incomplete"); return
        deltas = []
        for a, b in zip(A, B):
            ja = {j["job"]: j["jct_s"] for j in a["jobs"] if j.get("jct_s") is not None}
            jb = {j["job"]: j["jct_s"] for j in b["jobs"] if j.get("jct_s") is not None}
            deltas.extend((jb[k] - ja[k]) / jb[k] * 100 for k in set(ja) & set(jb) if jb[k] > 0)
        deltas.sort()
        n = len(deltas)
        imp = 100 * sum(1 for d in deltas if d > 0) / n
        print(f"  {label}: n_jobs={n} improved={imp:.1f}% "
              f"JCT-delta p10={deltas[int(0.1*n)]:+.1f}% p50={deltas[n//2]:+.1f}% p90={deltas[int(0.9*n)]:+.1f}%")

    fairness("m1swe_snapshots/m1swe_h100_job_aware_jps0.5_dram8_seed*",
             "m1swe_snapshots/m1swe_h100_lru_jps0.5_dram8_seed*", "H100 SWE")
    fairness("m1swe_snapshots/m1swe_a100-80_job_aware_jps0.5_dram8_seed*",
             "m1swe_snapshots/m1swe_a100-80_lru_jps0.5_dram8_seed*", "A100 SWE")
    fairness("tracelab_snapshots/tl_h100_job_aware_jps0.5_dram8_seed*",
             "tracelab_snapshots/tl_h100_lru_jps0.5_dram8_seed*", "TraceLab")

    print("\n== Fully-real window (recorded arrivals+gaps+sizes; 133 sessions, 05-29 burst) ==")
    for cond in ["job_aware", "continuum_ttl", "lru", "no_offload"]:
        print(cell_line(R, f"realwindow_snapshots/rw_h100_{cond}_jps0_dram8_seed*",
                        f"RW {cond}", N))

    print("\n== BFCL task-success floor (Qwen3-8B-FC, n=400) ==")
    qm = os.path.join(os.path.dirname(R), "quality_moat",
                      "quality_moat_stepA_qwen3fc-a100-80_10712534", "summary.json")
    if os.path.exists(qm):
        s = json.load(open(qm))
        for k, v in s["configs"].items():
            print(f"  {k}: {v.get('status')} rate={v.get('success_rate')} "
                  f"wilson={v.get('wilson_ci')} gap_pts={v.get('gap_vs_baseline_pts')}")
    else:
        print("  summary not found:", qm)


if __name__ == "__main__":
    main()
