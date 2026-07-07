# The Cache Contract — Artifact
Analyzers, snapshot result trees, probe harness, and system code for the paper
"The Cache Contract: Measuring, Enforcing, and Re-Pricing State Residency for LLM Agents".

- `results-mainline/` — per-turn JSON snapshot trees (ladder/sweeps/ablations/hybrid/TraceLab/
  realwindow/superposed) + `analyze_mainline.py` (one command regenerates every systems table/CI)
  + `MANIFEST.md` (number → analyzer-section → snapshot-tree map, pinned sha256s).
- `analysis/` — billing-telemetry + incentive analyzers (measurement_v2, friction_rent,
  theorem_maps, skirental_robust, breakpoints) with their published outputs; each regenerates
  from the TraceLab trace (public CC-BY; sha256 in DATA_README.md — 53MB, fetched separately).
- `probe/` — five-provider probe harness (dry-run fixtures + tests) and the live probe runners
  with their raw CSV logs (v1 single-shot + v2 statistical campaign).
- `system/` — Tenure policy code (continuum_d/) + replay bench (benchmarks/) as evaluated.
Large server logs are stripped; every quoted number's raw per-turn JSON is included.
