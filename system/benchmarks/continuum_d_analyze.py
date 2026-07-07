# SPDX-License-Identifier: Apache-2.0
"""Aggregate continuum_d_bench result JSONs into a comparison table.

Data-driven: globs <root>/**/<cond>_dram<N>_jps<J>.json — never hardcodes
the GPU/condition list, so partial results analyze cleanly and backfill
is a zero-edit rerun (pace-slurm-submit T-min rule).

Usage:
  python3 benchmarks/continuum_d_analyze.py --root results-pace/continuum-d \
      [--md EXPERIMENTS_CONTINUUM_D.md]
"""

import argparse
import json
import statistics
from pathlib import Path


def load_runs(root: Path) -> list[dict]:
    runs = []
    for f in sorted(root.rglob("*_dram*_jps*.json")):
        try:
            d = json.loads(f.read_text())
        except (json.JSONDecodeError, OSError) as e:
            print(f"SKIP {f}: {e}")
            continue
        s = d.get("summary", {})
        if not s:
            continue
        parts = f.parent.name  # e.g. cd_h200_lru_jps2_dram24 or smk_...
        runs.append({
            "dir": f.parent.name,
            "file": f.name,
            "condition": s["condition"],
            "gpu": _gpu_from_dir(parts),
            "dram_gb": s["config"]["dram_gb"],
            "jps": s["config"]["jps"],
            "jobs": s["config"]["jobs"],
            "turns": s["config"]["turns"],
            "n_ok": s["n_ok"],
            "n_err": s["n_err"],
            "wall_s": s["wall_s"],
            "avg_jct_s": s["avg_jct_s"],
            "avg_ttft_s": s["avg_ttft_s"],
            "per_turn_ttft": s.get("per_turn_avg_ttft", {}),
            "ext_queries": _metric(s, "external_prefix_cache_queries_total"),
            "ext_hits": _metric(s, "external_prefix_cache_hits_total"),
            "ext_tokens": _metric(s, "external_kv_transfer"),
            "jcts": [j["jct_s"] for j in d.get("jobs", [])],
        })
    return runs


def _gpu_from_dir(name: str) -> str:
    for tag in ("h100", "h200", "a100_80gb", "a100", "l40s", "5090"):
        if f"_{tag}_" in name or name.endswith(tag):
            return tag
    return "?"


def _metric(summary: dict, needle: str) -> float | None:
    for k, v in summary.get("metrics", {}).items():
        if needle in k and "created" not in k:
            return v
    return None


def p90(xs):
    if not xs:
        return None
    return statistics.quantiles(xs, n=10)[-1] if len(xs) >= 3 else max(xs)


def fmt(v, nd=2):
    return "-" if v is None else f"{v:.{nd}f}"


def table(runs: list[dict]) -> str:
    hdr = ("| gpu | condition | dram | jps | ok/err | avg JCT s | p90 JCT s "
           "| avg TTFT s | late-turn TTFT s | ext hit% |")
    sep = "|" + "---|" * 10
    lines = [hdr, sep]
    for r in sorted(runs, key=lambda r: (r["gpu"], r["dram_gb"], r["condition"])):
        late = [v for t, v in r["per_turn_ttft"].items() if int(t) >= 2]
        late_avg = statistics.mean(late) if late else None
        hitp = (100.0 * r["ext_hits"] / r["ext_queries"]
                if r["ext_queries"] else None)
        lines.append(
            f"| {r['gpu']} | {r['condition']} | {r['dram_gb']:.0f} "
            f"| {r['jps']} | {r['n_ok']}/{r['n_err']} "
            f"| {fmt(r['avg_jct_s'])} | {fmt(p90(r['jcts']))} "
            f"| {fmt(r['avg_ttft_s'], 4)} | {fmt(late_avg, 4)} "
            f"| {fmt(hitp, 1)} |")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--md", default=None)
    args = ap.parse_args()

    runs = load_runs(Path(args.root))
    if not runs:
        print("no result files found under", args.root)
        return
    out = table(runs)
    print(out)
    if args.md:
        Path(args.md).write_text(
            "# Continuum-D experiment results (auto-generated)\n\n"
            + out + "\n\nRegenerate: `python3 benchmarks/continuum_d_analyze.py"
            f" --root {args.root} --md {args.md}`\n")
        print(f"\nwrote {args.md}")


if __name__ == "__main__":
    main()
