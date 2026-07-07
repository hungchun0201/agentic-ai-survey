#!/usr/bin/env python3
"""Analyzer for the superposed real-arrival-window runs (see README.md).

Reuses analyze_mainline.py's estimators (per-turn p95 of total_s, per-turn +
session-clustered bootstrap CIs, DRAM-tier hit rate) over the spk{4,8}_h100_*
snapshot dirs pulled back into this directory.

Usage: python3 analyze_superposed.py [--root .] [--boot 10000]
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from analyze_mainline import (  # noqa: E402
    boot_cluster, boot_turn, cell_line, hit_rate, load_cells, p95,
)

CONDS = ["job_aware", "lru", "continuum_ttl", "no_offload"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.path.dirname(os.path.abspath(__file__)))
    ap.add_argument("--boot", type=int, default=10000)
    a = ap.parse_args()

    for k in (4, 8):
        print(f"\n== Superposed real window k={k} (H100, dram=8GB, "
              f"recorded arrivals+gaps, 2 seeds) ==")
        for cond in CONDS:
            pat = f"spk{k}_h100_{cond}_jps0_dram8_seed*"
            print(" ", cell_line(a.root, pat, cond, a.boot, jct=True))

        print(f"  -- per-seed p95 / hit% (k={k}) --")
        for cond in CONDS:
            for seed in (0, 1):
                cells = load_cells(
                    a.root, f"spk{k}_h100_{cond}_jps0_dram8_seed{seed}")
                if not cells:
                    print(f"  {cond} seed{seed}: NO DATA")
                    continue
                vals = [v for c in cells for _, v in c["turns"]]
                h = hit_rate(cells)
                nerr = sum(c["summary"].get("n_err", 0) for c in cells)
                hs = f"{h:6.2f}%" if h is not None else "   n/a"
                print(f"  {cond:14s} seed{seed}: p95={p95(vals):7.3f}s "
                      f"hit={hs} turns={len(vals)} err={nerr}")

        # Tenure's latency win under superposed-real pressure: paired delta
        # vs each baseline (turn-pooled point estimate + both CI treatments).
        ja = load_cells(a.root, f"spk{k}_h100_job_aware_jps0_dram8_seed*")
        if ja:
            pooled_ja = [v for c in ja for _, v in c["turns"]]
            for base in ("lru", "continuum_ttl", "no_offload"):
                bc = load_cells(a.root, f"spk{k}_h100_{base}_jps0_dram8_seed*")
                if not bc:
                    continue
                pooled_b = [v for c in bc for _, v in c["turns"]]
                d = p95(pooled_ja) - p95(pooled_b)
                print(f"  delta p95 (job_aware - {base}): {d:+.3f}s")


if __name__ == "__main__":
    main()
