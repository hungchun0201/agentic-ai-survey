#!/usr/bin/env python3
"""Offline-optimal (OPT) tier value for the agent reference class, computed
exactly from the replay inputs.

Model (matches the replay): session i's turn t re-reads its full prefix
L_i(t); after the turn its (grown) prefix may be stored to the DRAM tier;
between turns the resident amount can only shrink (evicted KV is gone until
the next materialization). Holding x tokens of session i across the gap
before turn t+1 yields exactly x re-read tokens served from the tier.

OPT therefore solves:  max Σ_I x_I   s.t.  x_I ≤ L_I,  and for every time
instant τ: Σ_{I∋τ} x_I ≤ C   — a fractional interval-packing LP (exact via
HiGHS). We also report a shortest-interval-first greedy (lower bound) as a
cross-check. The nominal schedule (Poisson arrivals + recorded/lognormal
gaps, service time 0) is reconstructed with the bench's own RNG streams.

Capacity: C_tokens = dram_gb * 2^30 / bytes_per_token;
Llama-3.1-8B fp16 KV: 32 layers * 8 kv-heads * 128 head-dim * 2 (K,V) * 2 B
= 131,072 B/token -> 65,536 tokens at 8 GB.
"""
import argparse
import json
import random

import numpy as np
from scipy.optimize import linprog
from scipy.sparse import lil_matrix

BYTES_PER_TOKEN = 32 * 8 * 128 * 2 * 2  # Llama-3.1-8B fp16


def build_intervals(jobs, seed, jps, gap_mu, gap_sigma, gap_cap, ctx_cap):
    rng = random.Random(1000 + seed)
    arrivals = []
    t = 0.0
    for _ in range(len(jobs)):
        t += rng.expovariate(jps) if jps > 0 else 0.0
        arrivals.append(t)
    intervals = []  # (start, end, size_tokens)
    for j, job in enumerate(jobs):
        turns = job["turns"]
        tau = arrivals[j]
        for t_idx in range(len(turns) - 1):
            nxt = turns[t_idx + 1]
            L_next = len(nxt["input_token_ids"])
            if L_next > ctx_cap:
                continue
            if nxt.get("gap_s") is not None:
                gap = min(float(turns[t_idx]["gap_s"]), gap_cap) \
                    if turns[t_idx].get("gap_s") is not None else 0.0
            else:
                gap = min(random.Random(seed * 1_000_003 + j * 77 + t_idx)
                          .lognormvariate(gap_mu, gap_sigma), gap_cap)
            intervals.append((tau, tau + gap, L_next))
            tau += gap
    return intervals


def opt_lp(intervals, C):
    """Exact fractional interval-packing optimum (HiGHS)."""
    pts = sorted({p for s, e, _ in intervals for p in (s, e)})
    seg_of = {p: k for k, p in enumerate(pts)}
    n, m = len(intervals), len(pts) - 1
    A = lil_matrix((m, n))
    for i, (s, e, _) in enumerate(intervals):
        for k in range(seg_of[s], seg_of[e]):
            A[k, i] = 1.0
    ub = [float(L) for _, _, L in intervals]
    res = linprog(c=[-1.0] * n, A_ub=A.tocsr(), b_ub=[float(C)] * m,
                  bounds=list(zip([0.0] * n, ub)), method="highs")
    assert res.status == 0, res.message
    return -res.fun


def greedy_short_first(intervals, C):
    pts = sorted({p for s, e, _ in intervals for p in (s, e)})
    seg_of = {p: k for k, p in enumerate(pts)}
    used = np.zeros(len(pts) - 1)
    order = sorted(range(len(intervals)),
                   key=lambda i: intervals[i][1] - intervals[i][0])
    tot = 0.0
    for i in order:
        s, e, L = intervals[i]
        a, b = seg_of[s], seg_of[e]
        if a == b:
            tot += L
            continue
        room = C - used[a:b].max()
        alloc = max(0.0, min(float(L), room))
        used[a:b] += alloc
        tot += alloc
    return tot


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs-file", required=True)
    ap.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2])
    ap.add_argument("--jps", type=float, default=0.5)
    ap.add_argument("--dram-gb", type=float, default=8.0)
    ap.add_argument("--gap-mu", type=float, default=1.6)
    ap.add_argument("--gap-sigma", type=float, default=0.5)
    ap.add_argument("--gap-cap", type=float, default=20.0)
    ap.add_argument("--ctx-cap", type=int, default=16384)
    a = ap.parse_args()

    jobs = json.load(open(a.jobs_file))
    C = a.dram_gb * (2 ** 30) / BYTES_PER_TOKEN
    print(f"capacity C = {C:.0f} tokens ({a.dram_gb} GB)")
    for seed in a.seeds:
        iv = build_intervals(jobs, seed, a.jps, a.gap_mu, a.gap_sigma,
                             a.gap_cap, a.ctx_cap)
        demand = sum(L for _, _, L in iv)
        opt = opt_lp(iv, C)
        grd = greedy_short_first(iv, C)
        print(f"seed {seed}: reread demand {demand/1e6:.2f}M tok | "
              f"OPT {opt/1e6:.3f}M ({100*opt/demand:.2f}%) | "
              f"greedy {100*grd/demand:.2f}%")


if __name__ == "__main__":
    main()
