# Continuum Experiments — Lab Record

## Environment

| Item | Value |
|---|---|
| Machine | `ssh hclin@100.107.101.84` (alias `ssh lab`) |
| GPU | 1× NVIDIA RTX 5090 (32 GB VRAM) |
| CPU / RAM | Intel desktop, 62 GB DDR |
| Conda env | `contextserve` |
| vLLM source | `/home/hclin/vllm-continuum/vllm/` (editable install, fork of v0.7.x) |
| Model | `/home/hclin/shared_models/Meta-Llama-3.1-8B-Instruct` (bf16, 15 GB) |
| KV cache | 5,402 blocks × 16 tokens/block × 2 MiB/block = 10.55 GiB |
| vLLM flags | `--max-model-len 4096 --gpu-memory-utilization 0.85 --port 8199` |
| Benchmark script | `/home/hclin/vllm-continuum/ab_benchmark.py` |
| Results dir | `/home/hclin/vllm-continuum/ab_results/` |

---

## Completed Experiments

### Exp 1: Functional Verification — Pin Mechanism (2026-04-02)

**Goal**: Confirm Continuum's KV cache pin works at the system level.

**Method**: 
- 1 sequential job, 5 turns, accumulated context + simulated tool outputs
- Poll `vllm:kv_cache_usage_perc` via `/metrics` endpoint between turns
- Server: `--scheduling-policy continuum`

**Key results**:
- KV cache usage grows monotonically: 0.000876 → 0.001577 → 0.003330 → 0.004557 (5 → 9 → 18 → 25 blocks)
- Usage stays constant during tool execution gap (pin confirmed)
- Turn 5 (`is_last_step=True`) drops to 0.000000 (release confirmed)
- Tool detection: 10/10 bash blocks parsed correctly (Llama 3.1 8B)

**Scripts**: `test_continuum.py`, `test_pin_verify.py`

**Status**: ✅ Completed. Documented in execution-note.html Section 4.

---

### Exp 2: A/B Benchmark — FCFS vs Continuum, Low Load (2026-04-02)

**Goal**: Compare scheduling policies under moderate KV cache pressure.

**Config**:
| Parameter | Value |
|---|---|
| Arrival | Poisson, JPS=2.0 |
| Duration | 120 seconds |
| Turns/job | 8 |
| Context/job | ~2,915 tokens (accumulated, realistic tool outputs) |
| Tool time | Variable: 50-300ms (fast) + 2-5s (pytest) |
| Concurrent peak | ~15-22 jobs |
| KV cache pressure | ~75% |

**Results**:
| Metric | FCFS | Continuum | Diff |
|---|---|---|---|
| Jobs completed | 206 | 231 | |
| Avg duration | 6.65s | 6.97s | +4.8% |
| Median | 6.63s | 6.96s | +5.0% |

**Conclusion**: No improvement. At 75% utilization, vLLM's prefix caching (hash-based block reuse from free queue) provides the same benefit as pin. Continuum's overhead (ToolCallEstimator, O(n) queue scan) adds cost without benefit.

**Status**: ✅ Completed. Documented in execution-note.html Section 9.2.

---

### Exp 3: A/B Benchmark — FCFS vs Continuum, High Load (2026-04-02)

**Goal**: Compare under high KV cache pressure where freed blocks get stolen.

**Config**:
| Parameter | Value |
|---|---|
| Arrival | Poisson, JPS=8.0 |
| Duration | 90 seconds |
| Turns/job | 8 |
| Context/job | ~2,915 tokens |
| Tool time | Variable (same as Exp 2) |
| Concurrent peak | FCFS: ~156, Continuum: ~111 |
| KV cache pressure | ~95%+ |

**Results**:
| Metric | FCFS | Continuum | Diff |
|---|---|---|---|
| Jobs completed | 756 | 704 | |
| Avg duration | 14.10s | **12.47s** | **-11.6%** |
| Median | 14.33s | 12.61s | -12.0% |
| P90 | 17.02s | 14.37s | -15.6% |
| P95 | 17.54s | **14.63s** | **-16.6%** |
| Jobs > 16s | 191 (25.3%) | **0 (0.0%)** | eliminated |
| Std deviation | 2.43s | 1.57s | -35% |

**Per-turn latency**:
| Turn | Prompt Tokens | FCFS | Continuum | Diff |
|---|---|---|---|---|
| 1 | 92 | 1,263ms | 1,051ms | -16.8% |
| 2 | 469 | 735ms | 519ms | **-29.4%** |
| 3 | 811 | 574ms | 479ms | -16.6% |
| 4 | 1,343 | 1,005ms | 841ms | -16.3% |
| 5 | 1,655 | 749ms | 652ms | -12.9% |
| 6 | 2,241 | 641ms | 539ms | -15.9% |
| 7 | 2,665 | 3,732ms | 3,212ms | -13.9% |
| 8 | 2,915 | 1,236ms | 1,034ms | -16.3% |

**Key findings**:
1. Turn 2 shows largest improvement (-29.4%) — first turn benefiting from pin
2. Zero jobs exceed 16s under Continuum vs 25.3% under FCFS (tail latency eliminated)
3. Lower variance (std 1.57s vs 2.43s) — more predictable performance
4. Consistent improvement across all turns (12-29%)

**Conclusion**: Continuum significantly outperforms FCFS when KV cache is under high pressure (~95%+ utilization). Pin prevents blocks from being stolen by competing jobs, avoiding costly re-prefill.

**Status**: ✅ Completed. Documented in execution-note.html Section 9.3.

---

## Planned Experiments

### Exp 4: FCFS + LMCache DRAM Offload vs Continuum

**Goal**: Compare three KV cache strategies:
1. FCFS (recompute) — baseline, already have data
2. FCFS + LMCache (DRAM offload) — copy KV to CPU, reload on next turn
3. Continuum (VRAM pin) — keep KV in GPU

**Expected trade-off**:
| Strategy | GPU VRAM usage | Next-turn cost | Bottleneck |
|---|---|---|---|
| Recompute (FCFS) | Lowest (free immediately) | Full prefill (~200-300ms) | GPU compute |
| DRAM offload | Lowest (copy then free) | memcpy H2D (~5-10ms for 3K tokens) | PCIe bandwidth |
| VRAM pin | Highest (don't free) | Zero | VRAM capacity |

**Config**: Same as Exp 3 (JPS=8.0, 90s, 8 turns)

**Server command**:
```bash
LMCACHE_MAX_LOCAL_CPU_SIZE=8 \
vllm serve MODEL \
  --scheduling-policy fcfs \
  --kv-transfer-config '{"kv_connector":"LMCacheConnectorV1","kv_role":"kv_both"}' \
  --port 8199 --max-model-len 4096 --gpu-memory-utilization 0.85
```

**Blockers**:
- `cudaHostAlloc` fails — need `ulimit -l unlimited` (requires root after reboot)
- lmcache 0.4.2 ABI mismatch with torch 2.8.0 — use lmcache 0.3.7

**Status**: ⏳ Blocked on machine reboot + memlock fix.

---

### Exp 5: Mixed Workload — Agent Jobs + Chatbot Requests

**Goal**: Test whether Continuum's pin hurts non-agent (chatbot) requests.

**Design**:
- Background: continuous stream of short chatbot requests (1 turn, no job_id)
- Foreground: agent jobs (8 turns, with job_id, same as Exp 3)
- Measure: chatbot latency under FCFS vs Continuum

**Hypothesis**: Continuum's pin occupies blocks that chatbot requests could use → chatbot latency increases under Continuum. This tests the cost side of the paper's cost-benefit model.

**Status**: 📋 Planned.

---

### Exp 6: Variable JPS Sweep

**Goal**: Reproduce paper's Figure 8 — plot avg job duration vs JPS for both policies.

**Design**:
- JPS values: 1.0, 2.0, 4.0, 6.0, 8.0, 10.0
- Duration: 90s each
- Same job config as Exp 3
- Plot: X=JPS, Y=avg job duration, two lines (FCFS, Continuum)

**Expected**: Lines diverge as JPS increases (matching paper's trend).

**Status**: 📋 Planned.

---

### Exp 7: Tool Time Sensitivity

**Goal**: Test how tool execution time affects Continuum's benefit.

**Design**:
- Fix JPS=8.0 (high load)
- Vary tool gap: 0.2s, 0.5s, 1.0s, 2.0s, 5.0s, 10.0s
- All other params same as Exp 3

**Hypothesis**:
- Very short gap (< pin TTL 2s): pin always hits, max benefit
- Gap ≈ TTL (2s): borderline, pin may expire before next turn
- Long gap (> TTL): pin expires, no benefit over FCFS

**Status**: 📋 Planned.

---

## Bugs Found

### Bug 1: KeyError 'func_call' in ToolCallEstimator

- **File**: `vllm/v1/core/estimate_with_func.py:169`
- **Trigger**: Concurrent requests with same `job_id`, or `job_id=None`
- **Cause**: `request_arrives()` assumes `history[-1]` is a departure entry, but concurrent arrivals create back-to-back arrival entries
- **Impact**: Server crash (EngineCore dies)
- **GitHub**: Not reported. Issue #15 is a different bug.
- **Status**: Not fixed. Workaround: always provide unique `job_id` per job.

### Bug 2: Qwen3 Thinking Mode Breaks ToolCallParser

- **Model**: Qwen3 8B AWQ
- **Cause**: `<think>...</think>` tokens consume the output budget before producing the bash code block
- **Impact**: ToolCallParser regex fails → `this_func_call=None` → no pin
- **Parse rate**: 2/10 (Qwen3) vs 10/10 (Llama 3.1 8B)
- **Status**: By design. ToolCallParser regex is coupled to non-thinking model output format.

---

## Server Operation Notes

⚠️ **NEVER use `kill -9` on GPU processes.** Corrupts CUDA driver, requires full machine reboot.

**Graceful shutdown**: `kill -2 $(pgrep -f "vllm serve" | head -1)` then wait up to 30s.

**Verify GPU clear**: `nvidia-smi --query-gpu=memory.used --format=csv,noheader` → should show ~1500 MiB.

See `CLAUDE.md` for complete server switch SOP.
