#!/usr/bin/env python3
"""M1: statistical-audit hardening of TraceLab billing telemetry (EXPERIMENT_PLAN M1).
1a read-share w/ dev-cluster bootstrap CI + longitudinal; 1b retention curve (miss|gap) Wilson CI;
1c dead-holding vs TTL grid; 1d robustness splits. Zero-API, CPU-only."""
import gzip, json, math, random, argparse, datetime, collections

def ts_of(r):
    for e in (r.get("timing_events") or []):
        if e.get("timestamp"):
            return datetime.datetime.fromisoformat(e["timestamp"].replace("Z", "+00:00"))
    return None

def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0, 1.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (p, max(0.0, c - h), min(1.0, c + h))

def load(trace):
    rounds, sessions = [], collections.defaultdict(list)
    with gzip.open(trace, "rt") as f:
        for line in f:
            r = json.loads(line)
            if r.get("provider") != "claude":
                continue
            rec = {
                "sid": r["session_id"], "dev": r.get("user", "?"), "idx": r["round_index"],
                "read": r.get("claude_cache_read_input_tokens") or 0,
                "creation": r.get("claude_cache_creation_input_tokens") or 0,
                "uncached": r.get("claude_uncached_input_tokens") or 0,
                "prefix": r.get("prefix_tokens") or 0,
                "total": r.get("input_tokens_total") or 0, "ts": ts_of(r),
            }
            rounds.append(rec)
            sessions[rec["sid"]].append(rec)
    for rows in sessions.values():
        rows.sort(key=lambda x: x["idx"])
    return rounds, sessions

def read_share(rounds):
    num = sum(r["read"] for r in rounds)
    den = sum(r["read"] + r["creation"] + r["uncached"] for r in rounds)
    return num / den if den else 0.0

def dev_bootstrap(rounds, b=10000, seed=7):
    by_dev = collections.defaultdict(lambda: [0, 0])
    for r in rounds:
        by_dev[r["dev"]][0] += r["read"]
        by_dev[r["dev"]][1] += r["read"] + r["creation"] + r["uncached"]
    devs = list(by_dev.values())
    rng = random.Random(seed)
    draws = []
    for _ in range(b):
        s = [devs[rng.randrange(len(devs))] for _ in devs]
        n = sum(x[0] for x in s); d = sum(x[1] for x in s)
        draws.append(n / d if d else 0.0)
    draws.sort()
    return draws[int(0.025 * b)], draws[int(0.975 * b)], by_dev

def gaps_with_miss(sessions):
    """Per gap: ratios of round-t billing fields to E = input_tokens_total of round t-1 — an
    INDEPENDENT expectation (prefix_tokens == cache_read identically in this trace, so ratios
    against prefix would be tautological; verified 137,401/137,401 equal). If the provider
    retained the prefix, round t re-reads at least E (append-only rounds); if it evicted, those
    E tokens bill as creation/uncached instead. Compaction rounds (total_t < total_{t-1}) are
    excluded from the retention test and counted separately."""
    out, n_compact = [], 0
    for rows in sessions.values():
        for i in range(1, len(rows)):
            a, b = rows[i - 1], rows[i]
            if a["ts"] is None or b["ts"] is None or a["total"] <= 0:
                continue
            g = (b["ts"] - a["ts"]).total_seconds()
            if g < 0:
                continue
            if b["total"] < a["total"]:
                n_compact += 1
                continue
            E = a["total"]
            out.append((g, b["read"] / E, b["creation"] / E, E, b["dev"]))
    return out, n_compact

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trace", required=True)
    ap.add_argument("--csv-dir", default=None)
    a = ap.parse_args()
    rounds, sessions = load(a.trace)
    devs = sorted({r["dev"] for r in rounds})
    print(f"rounds={len(rounds)} sessions={len(sessions)} devs={len(devs)}")

    # 1a read share + CI
    s = read_share(rounds)
    lo, hi, by_dev = dev_bootstrap(rounds)
    per_round = [r["read"] / t for r in rounds if (t := r["read"] + r["creation"] + r["uncached"]) > 0]
    per_round.sort()
    n = len(per_round)
    print(f"[1a] token-weighted read share = {100*s:.1f}%  (dev-cluster bootstrap 95% CI "
          f"{100*lo:.1f}–{100*hi:.1f}%)")
    print(f"[1a] per-round: mean {100*sum(per_round)/n:.1f}% median {100*per_round[n//2]:.1f}%")
    dev_shares = sorted((v[0] / v[1] if v[1] else 0.0) for v in by_dev.values())
    m = len(dev_shares)
    print(f"[1a] per-dev share: min {100*dev_shares[0]:.1f}% p25 {100*dev_shares[m//4]:.1f}% "
          f"median {100*dev_shares[m//2]:.1f}% p75 {100*dev_shares[3*m//4]:.1f}% max {100*dev_shares[-1]:.1f}%")
    weekly = collections.defaultdict(lambda: [0, 0])
    for r in rounds:
        if r["ts"]:
            wk = r["ts"].isocalendar()[:2]
            weekly[wk][0] += r["read"]
            weekly[wk][1] += r["read"] + r["creation"] + r["uncached"]
    print("[1a] weekly token-weighted share:")
    for wk in sorted(weekly):
        n0, d0 = weekly[wk]
        if d0 > 1e6:
            print(f"      {wk[0]}-W{wk[1]:02d}: {100*n0/d0:.1f}%  (tokens {d0/1e6:.0f}M)")

    # 1b billing-visible re-creation curve (multi-threshold; NOT direct physical retention)
    gm, n_compact = gaps_with_miss(sessions)
    bins = [(0, 60), (60, 120), (120, 300), (300, 600), (600, 1200), (1200, 1800),
            (1800, 3600), (3600, 7200), (7200, 1e18)]
    print(f"[1b] billing-visible re-creation after gaps, n_gaps={len(gm)} "
          f"(+{n_compact} compaction rounds excluded)")
    print("      E = input_total of previous round (independent of round-t billing);")
    print("      miss(t) = cache_read < t*E; creation share = mean(cache_creation/E)")
    rows_csv = []
    for lo_b, hi_b in bins:
        sel = [x for x in gm if lo_b <= x[0] < hi_b]
        lab = f"{int(lo_b)}–{'inf' if hi_b > 1e17 else int(hi_b)}s"
        n = len(sel)
        cols = []
        for t in (0.5, 0.9, 0.99):
            k = sum(1 for x in sel if x[1] < t)
            p, wl, wh = wilson(k, n)
            cols.append(f"t={t}: {100*p:5.2f}% [{100*wl:.2f},{100*wh:.2f}]")
        cshare = 100 * sum(x[2] for x in sel) / n if n else 0.0
        print(f"      gap {lab:>12}: {'  '.join(cols)}  creation {cshare:5.2f}%  n={n}")
        k5 = sum(1 for x in sel if x[1] < 0.5)
        p, wl, wh = wilson(k5, n)
        rows_csv.append((lab, p, wl, wh, n))
    below = [x for x in gm if x[0] <= 300]; above = [x for x in gm if x[0] > 300]
    for t in (0.5, 0.9, 0.99):
        pb = sum(1 for x in below if x[1] < t) / len(below)
        ab = sum(1 for x in above if x[1] < t) / len(above)
        se = math.sqrt(pb * (1 - pb) / len(below) + ab * (1 - ab) / len(above))
        print(f"[1b] miss(t={t}) ≤5min {100*pb:.2f}% vs >5min {100*ab:.2f}% "
              f"(diff {100*(ab-pb):.2f}pp, z={((ab-pb)/se if se else 0):.1f})")

    # 1c dead holding vs TTL. Two labeled definitions:
    #  A (policy-consistent): live capped at TTL per gap — a strict-TTL provider.
    #  B (hold-through-gaps counterfactual): live = holding uncapped through all gaps,
    #    dead = TTL tail after the final turn — an upper-bound-holding counterfactual.
    BYTES_PER_TOKEN = 131072
    print("[1c] dead-holding share of cache token-seconds vs TTL:")
    live_obs = 0.0
    for rows in sessions.values():
        for i in range(1, len(rows)):
            aa, bb = rows[i - 1], rows[i]
            if aa["ts"] and bb["ts"] and bb["prefix"] > 0:
                live_obs += bb["prefix"] * max(0.0, (bb["ts"] - aa["ts"]).total_seconds())
    for ttl in [60, 300, 900, 1800, 3600, 7200]:
        live_cap = dead = 0.0
        for rows in sessions.values():
            for i in range(1, len(rows)):
                aa, bb = rows[i - 1], rows[i]
                if aa["ts"] and bb["ts"] and bb["prefix"] > 0:
                    g = max(0.0, (bb["ts"] - aa["ts"]).total_seconds())
                    live_cap += bb["prefix"] * min(g, ttl)
            last = rows[-1]
            if last["ts"] and last["prefix"] > 0:
                dead += last["prefix"] * ttl
        gbh = dead * BYTES_PER_TOKEN / 1e9 / 3600
        print(f"      TTL {ttl:>5}s: A(strict) {100*dead/(dead+live_cap):5.2f}%  "
              f"B(hold-thru) {100*dead/(dead+live_obs):5.2f}%  dead={gbh:,.0f} KV GB·h")

    # 1d robustness
    vol = collections.Counter()
    for r in rounds:
        vol[r["dev"]] += r["read"] + r["creation"] + r["uncached"]
    top3 = {d for d, _ in vol.most_common(3)}
    sub = [r for r in rounds if r["dev"] not in top3]
    print(f"[1d] excl top-3 devs ({100*sum(vol[d] for d in top3)/sum(vol.values()):.0f}% of tokens): "
          f"read share {100*read_share(sub):.1f}%")
    slen = {sid: len(rows) for sid, rows in sessions.items()}
    qs = sorted(slen.values())
    cuts = [qs[len(qs) // 4], qs[len(qs) // 2], qs[3 * len(qs) // 4]]
    for lab, f in [("Q1", lambda L: L <= cuts[0]), ("Q2", lambda L: cuts[0] < L <= cuts[1]),
                   ("Q3", lambda L: cuts[1] < L <= cuts[2]), ("Q4", lambda L: L > cuts[2])]:
        sel = [r for r in rounds if f(slen[r["sid"]])]
        print(f"[1d] session-length {lab} (rounds {len(sel)}): read share {100*read_share(sel):.1f}%")

    # 1e observed friction actually paid (not simulated): on over-TTL append-only gap rounds,
    # the un-read part of the previous context (E - read) was re-billed as creation at w=1.25
    # instead of read at r=0.1. Extra vs a residency bit = (w - r) * (E - read), floor 0.
    w, r_ = 1.25, 0.10
    obs = sum((w - r_) * max(0.0, E - rf * E) for g, rf, cf, E, dev in gm if g > 300)
    tot_billed = sum(0.1 * r["read"] + 1.25 * r["creation"] + r["uncached"] for r in rounds)
    print(f"[1e] observed friction paid (gap>300s, vs one-bit counterfactual): "
          f"{obs/1e6:.1f}M token-units = {100*obs/tot_billed:.1f}% of the 4.21B input bill "
          f"(bill recomputed: {tot_billed/1e9:.2f}B)")

    if a.csv_dir:
        import os
        os.makedirs(a.csv_dir, exist_ok=True)
        with open(f"{a.csv_dir}/retention_curve.csv", "w") as f:
            f.write("gap_bin,miss_rate,wilson_lo,wilson_hi,n\n")
            for lab, p, wl, wh, nn in rows_csv:
                f.write(f"{lab},{p:.4f},{wl:.4f},{wh:.4f},{nn}\n")
        print(f"csv → {a.csv_dir}/retention_curve.csv")

if __name__ == "__main__":
    main()
