# Superposed real-arrival window (cold-review answer to "synthetic Poisson arrivals")

Pressure-tests the fully-real recorded window (TraceLab 2026-05-29 burst,
`jobs_realwindow.json`, 133 sessions, recorded `arrival_offset_s` + per-turn
`gap_s`) by superposing k independent copies of the window on one H100 —
models k teams sharing one GPU with a fully-real arrival structure. The k=1
window is lightly loaded; k=4/k=8 push the same real arrival process into the
contention regime (k=1 already moved 348 GB GPU→CPU on the 8 GB DRAM tier).

## Workload derivation

`make_superposed_jobs.py` (this dir) over the canonical
`jobs_realwindow.json`
(sha256 `065c83ad6b806554257d52290b9e1be463519f2c0f4d42e78f569e200448c0c5`,
same file as results-realwindow; verified byte-identical local vs PACE):

- each session duplicated k times, `job_id`/`instance_id` suffixed `_c0.._c{k-1}`
- `arrival_offset_s` UNCHANGED (copies arrive together, as k parallel teams)
- per-turn `gap_s` UNCHANGED (recorded think/tool gaps)
- token content identical EXCEPT one per-copy salt token (ids 100100..100107,
  ordinary Llama-3.1 vocab ids outside the trace's id range [2000, 99999])
  prepended to every turn's `input_token_ids`.

**Why the salt token (documented deviation):** vLLM prefix caching and the
OffloadingConnector DRAM tier are content-addressed (block-hash keyed;
`keys_to_store` dedup). Byte-identical copies would dedupe into ONE set of KV
blocks, so the superposed working set would NOT scale with k and the pressure
test would be vacuous. One distinct leading token per copy shifts every
downstream block hash → the k copies are cache-independent ("k teams, k
distinct codebases"), while the workload stays 99.99+% byte-identical and all
within-copy prefix structure (turns are ~97% cumulative) is preserved exactly.

Generated files (on PACE, `/storage/scratch1/1/hlin464/inference_improvement/`):

| file | sessions | turns | sha256 |
|---|---|---|---|
| jobs_realwindow_k4.json | 532 | 1852 | `2a407564ffa93cc35a0c452dcc343662440bfd999b6cbc3cf5bf48ef9fe41483` |
| jobs_realwindow_k8.json | 1064 | 3704 | `d8da029a84dc0c409339b031d8a468faf4faa038859371c6f1e271f53f4b1379` |

## Runs (submitted 2026-07-06, PACE H100, account gts-rs275-paid qos inferno)

Same harness + engine as results-realwindow: `m6_realwindow.sbatch` →
`benchmarks/continuum_d_bench.py` (vllm 0.23.0 venv-cu13), model
`meta-llama/Llama-3.1-8B-Instruct`, replay mode (`jps=0`, recorded arrivals +
gaps), `--gen-tokens 512 --gap-cap-s 60 --dram-gb 8 --gpu-mem-util 0.30
--max-model-len 36864`, one H100 (`--gres=gpu:h100:1`) per run, one seed per
job. DRAM tier budget 8 GB — identical to the k=1 realwindow runs.

| k | condition | seed | Slurm job | result dir (PACE results-superposed/) |
|---|---|---|---|---|
| 4 | job_aware | 0 | 10827300 | spk4_h100_job_aware_jps0_dram8_seed0 |
| 4 | job_aware | 1 | 10827301 | spk4_h100_job_aware_jps0_dram8_seed1 |
| 4 | lru | 0 | 10827302 | spk4_h100_lru_jps0_dram8_seed0 |
| 4 | lru | 1 | 10827303 | spk4_h100_lru_jps0_dram8_seed1 |
| 4 | continuum_ttl | 0 | 10827304 | spk4_h100_continuum_ttl_jps0_dram8_seed0 |
| 4 | continuum_ttl | 1 | 10827305 | spk4_h100_continuum_ttl_jps0_dram8_seed1 |
| 4 | no_offload | 0 | 10827306 | spk4_h100_no_offload_jps0_dram8_seed0 |
| 4 | no_offload | 1 | 10827307 | spk4_h100_no_offload_jps0_dram8_seed1 |
| 8 | job_aware | 0 | 10827308 | spk8_h100_job_aware_jps0_dram8_seed0 |
| 8 | job_aware | 1 | 10827309 | spk8_h100_job_aware_jps0_dram8_seed1 |
| 8 | lru | 0 | 10827310 | spk8_h100_lru_jps0_dram8_seed0 |
| 8 | lru | 1 | 10827311 | spk8_h100_lru_jps0_dram8_seed1 |
| 8 | continuum_ttl | 0 | 10827312 | spk8_h100_continuum_ttl_jps0_dram8_seed0 |
| 8 | continuum_ttl | 1 | 10827313 | spk8_h100_continuum_ttl_jps0_dram8_seed1 |
| 8 | no_offload | 0 | 10827314 | spk8_h100_no_offload_jps0_dram8_seed0 |
| 8 | no_offload | 1 | 10827317 | spk8_h100_no_offload_jps0_dram8_seed1 |

Monitoring: `ssh pace 'squeue -u hlin464 -n cdspw4,cdspw8 -o "%i %j %T %M %R"'`
Per-run sidecar: `<result dir>/job_meta.txt` (node, env, BENCH_EXIT).

## Analysis

`analyze_superposed.py` (this dir) — same estimators as `analyze_mainline.py`
(per-turn p95 of `total_s`, per-turn + session-clustered bootstrap CIs,
tier hit rate = `vllm:external_prefix_cache_hits_total / queries_total`),
over the snapshot dirs pulled back into this directory.
