#!/usr/bin/env python3
"""M2: friction-rent decomposition of provider prompt-cache menus on real TraceLab gaps.
Per over-TTL gap the client picks its cheapest legal action under the menu (heartbeat / let-expire
-and-rewrite / explicit storage). Decompose client spend into provider real cost (deadweight) vs
transfer (rent). Units: P = list input price per token = 1.0. Zero-API, CPU-only."""
import gzip, json, argparse, datetime, collections

C_S = 2.4e-8      # provider holding cost, P/token-second (DRAM floor; cf. p2_numeric.txt)
C_Q = 100.0       # per-ping service overhead, token-units (request handling, ~100 tok equiv)
C_P = 0.5         # provider recompute cost per token on rewrite, in P (sens: 0.3/0.7)

MENUS = {
    # name: dict(kind, write premium w-r on rewrite, read mult r, ttl seconds)
    "anthropic-5m": dict(kind="ttl", w=1.25, r=0.10, ttl=300),
    "anthropic-1h": dict(kind="ttl", w=2.00, r=0.10, ttl=3600),
    "openai-legacy": dict(kind="ttl", w=1.00, r=0.10, ttl=600),   # pre-2026-05: 5-10min best-effort
    "openai-24h":    dict(kind="ttl", w=1.00, r=0.10, ttl=86400), # 2026-05-29+: 24h default retention
    "deepseek":     dict(kind="ttl", w=1.00, r=0.02, ttl=86400), # disk cache, ~98% off, day-scale
    # Gemini explicit caching: literal storage price. $1.00/MTok-hr at ~$1.25/MTok input => 0.8 P/Mtok-hr
    "gemini-storage": dict(kind="storage", p_s=0.8e-6 / 3600.0, w=1.00, r=0.25),  # P per token-second
}

def ts_of(r):
    for e in (r.get("timing_events") or []):
        if e.get("timestamp"):
            return datetime.datetime.fromisoformat(e["timestamp"].replace("Z", "+00:00"))
    return None

def load_gaps(trace):
    by = collections.defaultdict(list)
    with gzip.open(trace, "rt") as f:
        for line in f:
            r = json.loads(line)
            if r.get("provider") != "claude":
                continue
            by[r["session_id"]].append(r)
    gaps = []  # (g_seconds, L_tokens, dev, sid)
    for sid, rows in by.items():
        rows.sort(key=lambda x: x["round_index"])
        times = [ts_of(r) for r in rows]
        for i in range(1, len(rows)):
            if times[i] is None or times[i - 1] is None:
                continue
            g = (times[i] - times[i - 1]).total_seconds()
            L = rows[i].get("prefix_tokens") or 0
            if g > 0 and L > 0:
                gaps.append((g, L, rows[i].get("user", "?"), sid))
    return gaps

def decompose(gaps, menu, c_s=C_S, c_q=C_Q, c_p=C_P):
    """Returns dict of totals; only gaps where the menu forces a choice (g>ttl for ttl menus)."""
    spend = cost = 0.0
    n_choice = 0
    per_dev = collections.Counter()
    per_sess = collections.Counter()
    for g, L, dev, sid in gaps:
        if menu["kind"] == "ttl":
            ttl = menu["ttl"]
            if g <= ttl:
                continue  # free refresh-on-hit; no friction event
            n_pings = int(g // ttl)
            c_ping = menu["r"] * L * n_pings                # client heartbeat spend
            c_rewrite = (menu["w"] - menu["r"]) * L         # extra over the read it does anyway
            if c_ping <= c_rewrite:
                s = c_ping
                k = c_q * n_pings + c_s * L * g             # provider: serve pings + hold through gap
            else:
                s = c_rewrite
                k = c_p * L                                  # provider recomputes prefill
        else:  # explicit storage
            s = min(menu["p_s"] * L * g, (menu["w"] - menu["r"]) * L)
            k = c_s * L * g if s == menu["p_s"] * L * g else c_p * L
            if g <= 300:  # short gaps: implicit hit either way, no friction event
                continue
        spend += s
        cost += k
        n_choice += 1
        per_dev[dev] += s
        per_sess[sid] += s
    rent = spend - cost
    return dict(spend=spend, cost=cost, rent=rent,
                rent_share=(rent / spend if spend else 0.0),
                n=n_choice, per_dev=per_dev, per_sess=per_sess)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trace", required=True)
    a = ap.parse_args()
    gaps = load_gaps(a.trace)
    print(f"gap events (g>0, L>0): {len(gaps)}")
    print(f"{'menu':>16} {'friction spend':>15} {'provider cost':>14} {'rent':>10} "
          f"{'rent%':>6} {'events':>7}")
    for name, menu in MENUS.items():
        d = decompose(gaps, menu)
        print(f"{name:>16} {d['spend']/1e6:>13.1f}M {d['cost']/1e6:>12.1f}M "
              f"{d['rent']/1e6:>8.1f}M {100*d['rent_share']:>5.1f}% {d['n']:>7}")
    # sensitivity on the flagship menu
    print("\nsensitivity (anthropic-5m): rent share under c_s x{0.5,1,2} X c_p {0.3,0.5,0.7}")
    for cs_m in (0.5, 1.0, 2.0):
        row = []
        for cp in (0.3, 0.5, 0.7):
            d = decompose(gaps, MENUS["anthropic-5m"], c_s=C_S * cs_m, c_p=cp)
            row.append(f"{100*d['rent_share']:5.1f}%")
        print(f"  c_s x{cs_m:<4} : {'  '.join(row)}")
    # per-dev / per-session friction spend distribution (Theorem B input)
    d = decompose(gaps, MENUS["anthropic-5m"])
    for label, ctr in (("dev", d["per_dev"]), ("session", d["per_sess"])):
        v = sorted(ctr.values())
        if not v:
            continue
        n = len(v)
        print(f"per-{label} friction spend (M tok-units): n={n} p50={v[n//2]/1e6:.3f} "
              f"p90={v[int(.9*n)]/1e6:.3f} max={v[-1]/1e6:.1f}")

if __name__ == "__main__":
    main()
