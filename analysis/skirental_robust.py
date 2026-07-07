#!/usr/bin/env python3
"""M4: ski-rental client-policy robustness on TraceLab over-TTL gaps.

Per over-TTL gap (g > TTL, resident prefix L > 0), the client faces a ski-rental
instance: each TTL renewal costs one ping r*L; abandoning costs a rewrite (w-r)*L.
OPT (offline) pays min(r*L*floor(g/TTL), (w-r)*L). The deterministic threshold-k
policy pings up to k times then abandons: cost r*L*n if n = floor(g/TTL) <= k,
else k*r*L + (w-r)*L.

Classical bound context: deterministic ski-rental with the break-even threshold is
2-competitive in the WORST CASE (and no deterministic policy beats 2). The ratios
reported here are distributional (trace-aggregate) performance of threshold-k on
real gap data — an average-case measurement, NOT a worst-case competitive claim.
"""
import gzip, json, datetime, argparse, hashlib, statistics as st

MENUS = {  # name -> (write mult w, read mult r, TTL seconds)
    "anthropic-5m": (1.25, 0.1, 300.0),
    "anthropic-1h": (2.00, 0.1, 3600.0),
    "openai-auto":  (1.00, 0.1, 600.0),
}
K_RANGE = range(1, 41)
N_FOLDS = 5

def ts_of(r):
    for e in (r.get("timing_events") or []):
        if e.get("timestamp"):
            return datetime.datetime.fromisoformat(e["timestamp"].replace("Z", "+00:00"))
    return None

def load_gaps(path):
    """Return list of (gap_seconds, prefix_tokens, developer_id); L>0, valid timestamps."""
    by = {}
    with gzip.open(path, "rt") as f:
        for line in f:
            r = json.loads(line)
            if r.get("provider") != "claude":
                continue
            by.setdefault(r["session_id"], []).append(r)
    gaps = []
    for sid, rows in by.items():
        rows.sort(key=lambda r: r["round_index"])
        times = [ts_of(r) for r in rows]
        dev = next((r.get("user") for r in rows if r.get("user")), "unknown")
        for i in range(1, len(rows)):
            if times[i] is None or times[i - 1] is None:
                continue  # missing timestamps: skip pair
            g = (times[i] - times[i - 1]).total_seconds()
            L = rows[i].get("prefix_tokens") or 0
            if L <= 0 or g <= 0:
                continue  # L=0: nothing resident to keep alive
            gaps.append((g, L, dev))
    return gaps

def menu_events(gaps, ttl):
    """Over-TTL events for a menu: (n_pings, L, dev). g == m*TTL exactly -> n = m."""
    return [(int(g // ttl), L, dev) for g, L, dev in gaps if g > ttl]

def cost_sums(events, w, r):
    """Per-dev OPT sum and per-dev policy(k) sums; pure aggregation, no globals."""
    opt, pol = {}, {}
    for n, L, dev in events:
        c_ping, c_rw = r * L * n, (w - r) * L
        o = opt.get(dev, 0.0) + min(c_ping, c_rw)
        p = pol.get(dev) or [0.0] * (len(K_RANGE) + 1)
        pol[dev] = [p[0]] + [p[k] + (c_ping if n <= k else (k * r + (w - r)) * L)
                             for k in K_RANGE]
        opt[dev] = o
    return opt, pol

def ratio(devs, opt, pol, k):
    o = sum(opt[d] for d in devs)
    p = sum(pol[d][k] for d in devs)
    return p / o if o > 0 else float("nan")

def fold_of(dev, seed):
    return int(hashlib.md5(f"{seed}:{dev}".encode()).hexdigest(), 16) % N_FOLDS

def analyze(name, gaps, w, r, ttl, seed, emit):
    events = menu_events(gaps, ttl)
    opt, pol = cost_sums(events, w, r)
    devs = sorted(opt)
    emit(f"\n== menu {name}: w={w} r={r} TTL={ttl:.0f}s | over-TTL gaps={len(events)} devs={len(devs)} ==")
    full = [(k, ratio(devs, opt, pol, k)) for k in K_RANGE]
    for row in range(0, len(full), 10):
        emit("  " + "  ".join(f"k={k:>2}:{v:.4f}" for k, v in full[row:row + 10]))
    k_star, r_star = min(full, key=lambda t: (t[1], t[0]))
    emit(f"  in-sample best: k*={k_star} ratio={r_star:.4f} | k=11 ratio={dict(full)[11]:.4f}")
    test_ratios, picked = [], []
    for f in range(N_FOLDS):
        train = [d for d in devs if fold_of(d, seed) != f]
        test = [d for d in devs if fold_of(d, seed) == f]
        if not train or not test:
            continue
        k_tr = min(K_RANGE, key=lambda k: (ratio(train, opt, pol, k), k))
        picked.append(k_tr)
        test_ratios.append(ratio(test, opt, pol, k_tr))
    mu = st.mean(test_ratios)
    sd = st.stdev(test_ratios) if len(test_ratios) > 1 else 0.0
    emit(f"  5-fold by developer (seed={seed}): k* per fold={picked}"
         f" | out-of-sample ratio={mu:.4f} +/- {sd:.4f}")
    return name, k_star, r_star, dict(full)[11], picked, mu, sd

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trace", required=True)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", default="skirental_robust.txt")
    a = ap.parse_args()
    lines = []
    def emit(s):
        print(s)
        lines.append(s)
    gaps = load_gaps(a.trace)
    emit(f"gap events (L>0, valid ts): {len(gaps)} | devs: {len(set(d for _, _, d in gaps))}")
    rows = [analyze(n, gaps, w, r, ttl, a.seed, emit) for n, (w, r, ttl) in MENUS.items()]
    emit("\n== summary: threshold-k ski-rental vs OPT (competitive ratio on trace) ==")
    hdr = f"{'menu':<14}{'k*':>4}{'in-sample':>11}{'k=11':>9}  {'fold k*':<18}{'out-of-sample':>16}"
    emit(hdr)
    emit("-" * len(hdr))
    for name, k_star, r_star, r11, picked, mu, sd in rows:
        emit(f"{name:<14}{k_star:>4}{r_star:>11.4f}{r11:>9.4f}  "
             f"{','.join(map(str, picked)):<18}{f'{mu:.4f} +/- {sd:.4f}':>16}")
    emit("\nnote: deterministic ski-rental is 2-competitive worst-case; ratios above are")
    emit("distributional performance on this trace, not a worst-case guarantee.")
    with open(a.out, "w") as f:
        f.write("\n".join(lines) + "\n")

if __name__ == "__main__":
    main()
