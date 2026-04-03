# CLAUDE.md — agentic-ai-survey-deploy

## Project Overview
GitHub Pages site for agentic AI survey. Deployed at `https://hungchun0201.github.io/agentic-ai-survey/`.

## Key Directories
- `papers/continuum/index.html` — Continuum implementation analysis (i18n EN/ZH)
- `papers/continuum/execution-note.html` — Execution note: hands-on experiments & verification
- `papers/ai-infra-basics/vllm/scheduler.html` — vLLM v1 scheduler deep dive

## Style & Conventions
- Dark theme, all CSS embedded in `<style>` tag per page (no external CSS)
- Bilingual: use `<span class="i18n" data-en="..." data-zh="...">default text</span>`
- File paths and code values (e.g., `None`, `find`, `pytest`) should NOT be translated
- Use `<code style="background:rgba(233,69,96,.12);border:1px solid rgba(233,69,96,.3);color:#e94560;padding:2px 8px;border-radius:4px">` for Continuum-modified file paths (red)
- Use `<code style="background:rgba(166,227,161,.1);border:1px solid rgba(166,227,161,.3);color:#a6e3a1;padding:2px 8px;border-radius:4px">` for non-vLLM file paths (green)
- Avoid ASCII art — use HTML elements (`.blk`, `.gpu-bar`, `.vflow`, `.tbar`)
- File path references: always use full paths (e.g., `vllm/v1/core/sched/scheduler.py` not `scheduler.py`)

## Remote Lab (vllm-continuum experiments)
- SSH: `ssh lab` (alias for `ssh hclin@100.107.101.84`)
- Conda env: `contextserve`
- vLLM source: `/home/hclin/vllm-continuum/vllm/` (editable install)
- Models: `/home/hclin/shared_models/Meta-Llama-3.1-8B-Instruct`

### ⚠️ CRITICAL: vLLM Server Lifecycle (DO NOT USE kill -9)

**NEVER use `kill -9` on vLLM or any GPU process.** It corrupts the CUDA driver state, making the GPU unusable until full machine reboot. There is no recovery short of rebooting.

#### Graceful shutdown (MANDATORY)

Always use `kill -2` (SIGINT, same as Ctrl+C). vLLM handles SIGINT to:
1. Stop accepting new requests
2. Let in-flight requests finish
3. Clean up CUDA resources and free GPU memory

```bash
# Step 1: Find PID and send SIGINT
ssh lab 'kill -2 $(pgrep -f "vllm serve" | head -1)'

# Step 2: Wait for process to exit (up to 30 seconds)
ssh lab 'for i in $(seq 1 30); do sleep 1; pgrep -f "vllm serve" > /dev/null || break; done'

# Step 3: VERIFY GPU memory is released before doing anything else
ssh lab 'nvidia-smi --query-gpu=memory.used --format=csv,noheader'
# Must show ~1500 MiB (desktop only). If higher, WAIT — do not proceed.
```

**If the process doesn't exit after 30 seconds**, use `kill -15` (SIGTERM) as escalation. Only as absolute last resort, and understanding it may require a reboot, use `kill -9`.

#### Starting a server

`nohup` via SSH fails silently (SIGHUP on disconnect). Use direct background instead:

```bash
ssh lab 'source ~/anaconda3/etc/profile.d/conda.sh && conda activate contextserve && \
  cd ~/vllm-continuum && \
  vllm serve /home/hclin/shared_models/Meta-Llama-3.1-8B-Instruct \
    --scheduling-policy <POLICY> --port 8199 \
    --max-model-len 4096 --gpu-memory-utilization 0.85 \
    > server.log 2>&1 &'
```

Then poll health in a **separate** SSH call:
```bash
ssh lab 'for i in $(seq 1 30); do sleep 5; \
  curl -s http://localhost:8199/health && echo " READY" && exit 0; done; echo TIMEOUT'
```

#### Complete server switch SOP

```bash
# 1. Graceful shutdown
ssh lab 'kill -2 $(pgrep -f "vllm serve" | head -1)'
ssh lab 'for i in $(seq 1 30); do sleep 1; pgrep -f "vllm serve" > /dev/null || break; done'

# 2. Verify GPU clear (~1500 MiB)
ssh lab 'nvidia-smi --query-gpu=memory.used --format=csv,noheader'

# 3. Start new server with different policy
ssh lab 'source ~/anaconda3/etc/profile.d/conda.sh && conda activate contextserve && \
  cd ~/vllm-continuum && vllm serve MODEL --scheduling-policy NEW_POLICY ... > server.log 2>&1 &'

# 4. Wait for health
ssh lab 'for i in $(seq 1 30); do sleep 5; \
  curl -s http://localhost:8199/health && echo " READY" && exit 0; done; echo TIMEOUT'
```

### LMCache (CPU DRAM offload)

**Status**: lmcache 0.3.7 imports OK with torch 2.8.0, but `cudaHostAlloc` fails at runtime.

**Root cause**: Pinned (page-locked) CPU memory allocation is limited by `ulimit -l` (memlock). After vLLM loads the model and allocates CUDA resources, the remaining memlock budget is insufficient for LMCache.

**Fix (requires root, do after reboot)**:
```bash
# Temporary
ulimit -l unlimited

# Permanent
echo "hclin soft memlock unlimited" | sudo tee -a /etc/security/limits.conf
echo "hclin hard memlock unlimited" | sudo tee -a /etc/security/limits.conf
```

**Version compatibility**:
- lmcache 0.4.2: C extension ABI mismatch with torch 2.8.0 (undefined symbol)
- lmcache 0.3.7: imports OK, needs memlock fix above

### A/B Benchmark
Script: `ab_benchmark.py` on remote at `/home/hclin/vllm-continuum/ab_benchmark.py`
Results: `/home/hclin/vllm-continuum/ab_results/`

To see meaningful Continuum vs FCFS difference, KV cache must be under high pressure:
- JPS=2.0, 120s → ~75% load → NO significant difference (prefix caching handles it)
- JPS=8.0, 90s → ~95% load → 12-17% improvement for Continuum
- Paper uses JPS=0.02-0.12 but with 70K tokens/job on 4×H100 (much larger context-to-cache ratio)
