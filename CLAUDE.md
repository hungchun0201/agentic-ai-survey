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

### Starting vLLM server (important!)
When switching between scheduling policies (fcfs/continuum), the server must be killed and restarted.

**Known issue**: `nohup vllm serve ... &` via SSH often fails silently because the background process gets SIGHUP when SSH session closes. Use this pattern instead:

```bash
ssh lab 'source ~/anaconda3/etc/profile.d/conda.sh && conda activate contextserve && cd ~/vllm-continuum && vllm serve /home/hclin/shared_models/Meta-Llama-3.1-8B-Instruct --scheduling-policy <POLICY> --port 8199 --max-model-len 4096 --gpu-memory-utilization 0.85 > server.log 2>&1 &'
```

Then in a **separate** SSH call, poll for health:
```bash
ssh lab 'for i in $(seq 1 30); do sleep 5; curl -s http://localhost:8199/health && echo " READY" && exit 0; done; echo TIMEOUT'
```

**Kill cleanly before switching policies**:
```bash
ssh lab 'kill $(pgrep -f "vllm serve") 2>/dev/null; sleep 5'
# Verify GPU is clear:
ssh lab 'nvidia-smi --query-gpu=memory.used --format=csv,noheader'
# Should show ~1500-2000 MiB (desktop only), then start new server
```

### A/B Benchmark
Script: `ab_benchmark.py` on remote at `/home/hclin/vllm-continuum/ab_benchmark.py`
Results: `/home/hclin/vllm-continuum/ab_results/`

To see meaningful Continuum vs FCFS difference, KV cache must be under high pressure:
- JPS=2.0, 120s → ~75% load → NO significant difference (prefix caching handles it)
- JPS=8.0, 90s → ~95% load → 12-17% improvement for Continuum
- Paper uses JPS=0.02-0.12 but with 70K tokens/job on 4×H100 (much larger context-to-cache ratio)
