#!/usr/bin/env python3
"""M3: numeric maps behind Theorem A (monopoly IC of the friction contract) and
Theorem B (competition flips it). Reuses friction_rent loaders/constants. Zero-API."""
import argparse, collections
from friction_rent import load_gaps, MENUS, C_S, C_Q, C_P

def gap_actions(gaps, menu):
    """Per over-TTL gap: (client spend s_old, provider cost k_old, L, g, dev)."""
    out = []
    ttl, w, r = menu["ttl"], menu["w"], menu["r"]
    for g, L, dev, sid in gaps:
        if g <= ttl:
            continue
        n_pings = int(g // ttl)
        c_ping = r * L * n_pings
        c_rewrite = (w - r) * L
        if c_ping <= c_rewrite:
            out.append((c_ping, C_Q * n_pings + C_S * L * g, L, g, dev))
        else:
            out.append((c_rewrite, C_P * L, L, g, dev))
    return out

def theorem_a(acts):
    """Scan storage price p_s: clients switch to (storage+bit) iff cheaper; report provider
    profit delta. Monopoly IC region = where every offered p_s lowers profit."""
    print("[A] provider profit delta from offering storage+lifecycle-bit at price p_s")
    print(f"{'p_s (xc_s)':>12} {'switched':>9} {'client gain':>12} {'provider dPi':>13}")
    grid = [1.5, 3, 10, 30, 100, 300, 1000, 3000, 10000]
    rows = []
    for m in grid:
        p_s = C_S * m
        dpi = cg = 0.0
        n_sw = 0
        for s_old, k_old, L, g, dev in acts:
            s_new = p_s * L * g
            if s_new < s_old:
                n_sw += 1
                cg += s_old - s_new
                dpi += (s_new - C_S * L * g) - (s_old - k_old)
        rows.append((m, n_sw, cg, dpi))
        print(f"{m:>10}x {n_sw:>9} {cg/1e6:>10.1f}M {dpi/1e6:>11.1f}M")
    all_neg = all(r[3] < 0 for r in rows if r[1] > 0)
    print(f"[A] grid check (dPi<0 wherever clients would switch): {all_neg}")
    # Exhaustive verification: dPi(p_s) is piecewise-linear in p_s with breakpoints exactly at
    # the switching thresholds p_s = s_old/(L*g) per gap; its extrema over any interval occur at
    # breakpoints (or interval ends). Evaluate at ALL thresholds + midpoints between consecutive
    # ones -> complete sign coverage for every client-acceptable price (W nonempty).
    thr = sorted(s_old / (L * g) for s_old, k_old, L, g, dev in acts)
    cands = set(thr)
    for i in range(len(thr) - 1):
        cands.add((thr[i] + thr[i + 1]) / 2.0)
    cands.add(thr[0] * 0.5)
    # Identity: dPi(W) = D_W - G_W, where D_W = sum_W (k_old - c_s L g) is recoverable
    # deadweight and G_W = sum_W (s_old - p_s L g) is client gain. Exact, price-free proof of
    # the theorem; the sweep below reports (G, D, dPi) and verifies the identity numerically.
    worst = -float("inf"); worst_p = worst_G = worst_D = None
    best_at_gain = {0.01: -float("inf"), 0.05: -float("inf")}
    S_tot = sum(s for s, k, L, g, d in acts)
    for p_s in cands:
        dpi = G = D = 0.0; n_sw = 0
        for s_old, k_old, L, g, dev in acts:
            s_new = p_s * L * g
            if s_new < s_old:
                n_sw += 1
                dpi += (s_new - C_S * L * g) - (s_old - k_old)
                G += s_old - s_new
                D += k_old - C_S * L * g
        assert abs(dpi - (D - G)) < 1e-6 * max(1.0, abs(dpi)), "identity violated"
        if n_sw and dpi > worst:
            worst, worst_p, worst_G, worst_D = dpi, p_s, G, D
        for f in best_at_gain:
            if G >= f * S_tot:
                best_at_gain[f] = max(best_at_gain[f], dpi)
    print(f"[A] EXHAUSTIVE over {len(cands)} candidate prices (all switching thresholds + "
          f"midpoints); identity dPi = D_W - G_W verified at every point.")
    print(f"[A] max dPi = {worst/1e6:.2f}M at p_s={worst_p:.3e} ({worst_p/C_S:.0f}x c_s), where "
          f"client gain G = {worst_G/1e6:.2f}M, deadweight D = {worst_D/1e6:.2f}M "
          f"(indifference frontier: dPi>0 only by skimming deadweight while G~0)")
    for f, v in sorted(best_at_gain.items()):
        print(f"[A] max dPi subject to client gain >= {int(100*f)}% of friction spend: "
              f"{v/1e6:.1f}M  -> {'LOSES' if v < 0 else 'profits'}")
    return rows

def theorem_b(acts, months=8.0):
    """Defection share vs switching cost sigma: fraction of devs whose friction spend under the
    incumbent menu exceeds sigma (they defect to a challenger offering residency at ~cost)."""
    per_dev = collections.Counter()
    for s_old, k_old, L, g, dev in acts:
        per_dev[dev] += s_old
    monthly = sorted(v / months for v in per_dev.values())
    n = len(monthly)
    print(f"\n[B] per-dev MONTHLY friction spend (token-units): n={n} "
          f"p25={monthly[n//4]/1e6:.3f}M p50={monthly[n//2]/1e6:.3f}M "
          f"p75={monthly[3*n//4]/1e6:.3f}M p90={monthly[int(.9*n)]/1e6:.2f}M max={monthly[-1]/1e6:.1f}M")
    print(f"{'sigma (Mtok-units/mo)':>22} {'defecting share':>16}")
    for sig in [0.01e6, 0.03e6, 0.1e6, 0.3e6, 1e6, 3e6, 10e6]:
        share = sum(1 for v in monthly if v > sig) / n
        print(f"{sig/1e6:>20.2f}M {100*share:>14.1f}%")
    # dollar anchor: 1M token-units at Claude Sonnet input $3/MTok = $3
    print("[B] anchor: 1M token-units ~= $3 at $3/MTok list input price")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trace", required=True)
    ap.add_argument("--menu", default="anthropic-5m")
    a = ap.parse_args()
    gaps = load_gaps(a.trace)
    acts = gap_actions(gaps, MENUS[a.menu])
    print(f"menu={a.menu} over-TTL events={len(acts)}")
    theorem_a(acts)
    theorem_b(acts)

if __name__ == "__main__":
    main()
