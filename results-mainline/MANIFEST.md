# Numbers Manifest — paper-mainline ("Tenure")

Every number in the paper maps to a section of `ANALYSIS.txt`, which
`analyze_mainline.py --boot 10000` regenerates from the raw snapshot trees below
(~25 min single-core; `--boot 500` is a <2-min smoke run with CIs within ±0.05s of the
10k values on every headline cell).
CIs: per-turn AND session-clustered bootstrap both emitted; the paper quotes per-turn
[95%] and asserts survival under both.

| Paper element | Analyzer section | Snapshot tree |
|---|---|---|
| Table (ladder H100) + Fig (ladder) | "Ladder (H100...)" | m1swe_snapshots/m1swe_h100_{cond}_jps0.5_dram8_seed{0,1,2} |
| A100 replication sentence | "Ladder (A100-80...)" | m1swe_snapshots/m1swe_a100-80_* |
| Mechanism panel ranges | "Mechanism counters" | m1swe_snapshots (summary.policy_stats) |
| 5.4 sensitivity bullet | "Sweeps ... baseline sensitivity" | sweep_snapshots/swp{A025,A4,S1,S3}_* |
| 5.5 precision negative | "Precision tier (codesign...)" | m1swe_snapshots/m1swe_{sku}_codesign_* |
| 5.5 BFCL floor | "BFCL task-success floor" | ../quality_moat/quality_moat_stepA_qwen3fc-a100-80_10712534/summary.json |
| 5.6 hybrid column | "Hybrid column" | m4hyb_snapshots/* |
| Second-family subsection | "TraceLab second family" | tracelab_snapshots/tl_h100_* |
| Fig (sweeps a/b) | "Sweeps (R1-fix grid...)" | sweep_snapshots + m1swe_snapshots |
| 5.7 synthetic controls | "Synthetic-gap control" / "Loose-budget control" | e2_synth_snapshots / e1_keystone_snapshots |
| §2 characterization | (direct) | characterization_v1.json |
| 5.5 codec physical (0.35-0.51x bytes) | (direct) | codec_phys_snapshots/phys_{10711673,10711835}/phys_verdict.json |
| 5.4 signal decomposition | "Signal decomposition / hint robustness" | coldfix_snapshots/* |
| residency bound + gate+TTL + seed exp. | (coldfix2 sections, landing) | coldfix2_snapshots/* |
| raw paired per-session deltas | (CSV) | paired_job_deltas.csv |

## Per-cell error counts
`grep -h '"n_err"' <tree>/*/*.json`, or read the `err=` column in ANALYSIS.txt — every cell
retains ≥99.9% of issued turns; max observed pooled-cell errors: 4 of 5,373 (ttl-slack-3.0
cell), hybrid 3 of 5,373; ladder headline cells 0-2.

## Trace derivation provenance
- SWE column: jobs_100_pinjab.json,
  sha256 3a38b2824442f8d57b81e0122cf0dcc10e6e18db8aa323798244e4cacae72398, derived from
  SWE-smith trajectories (derivation scripts in the artifact package; file ships with the
  artifact, mirrored on the experiment cluster).
- TraceLab column: derive_tracelab_jobs.py (this dir) over the public release
  syfi_coding_trace.jsonl.gz (TraceLab v0.0.1, CC-BY-4.0),
  sha256 9d265eae69a31cae203848bea936f018148eed7ca8bf56050c5abe96da0b4e6b;
  output jobs_100_tracelab.json
  sha256 a564ebb906fabd7f57e35a2262a0532cb0f9a49bd7002de83a5d275392adcd7a
  (179 MB; regenerate with the script — seed 42, deterministic).
- Gap calibration (SWE column): lognormal mu=1.6 sigma=0.5 cap 20s, fitted on 2,817 tool steps
  (Claude-Code corpus). TraceLab column uses recorded per-round gaps, cap 60s.

## Harness/plugin
Bench: agent-kvcache/benchmarks/continuum_d_bench.py; policies: agent-kvcache/continuum_d/
(spec.py, marconi_policy.py, continuum_ttl_policy.py, ...). Sbatch + submit scripts mirrored
on PACE at /storage/scratch1/1/hlin464/continuum-d/.

[2026-07-06 correction] TraceLab jsonl.gz sha256 tail was mis-recorded; corrected to the
recomputed value (9d265eae…da0b4e6b), which matches paper-cachecontract/data/README.md.
