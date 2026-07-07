#!/usr/bin/env python3
"""A/B Benchmark: FCFS vs Continuum under realistic load.

Simulates Poisson-arrival agentic jobs with long accumulated context,
variable tool execution times, and high KV cache pressure.

Designed to match Continuum paper's methodology:
- Poisson arrival (JPS control)
- Multi-turn jobs with growing context (~3000+ tokens)
- Variable tool times (mostly fast, some slow)
- Measures average job duration (paper's primary metric)

Usage:
  vllm serve MODEL --scheduling-policy continuum --port 8199 --max-model-len 4096
  python3 ab_benchmark.py --policy continuum --port 8199 --jps 2.0 --duration 120
"""

import argparse
import hashlib
import json
import math
import os
import random
import string
import threading
import time
from dataclasses import dataclass, field
from openai import OpenAI

# ──────────────── Realistic Agent Simulation ────────────────

SYSTEM_PROMPT = """You are a senior software engineer debugging a complex Python project.
You have access to a bash terminal. For each step, respond with ONLY a ```bash``` code block.
Do not explain your reasoning. Just output the command."""

# ──────────────── Per-Job Randomized Tool Outputs ────────────────
# Target token counts per turn (measured from original static outputs).
# Each job generates UNIQUE content at these sizes to defeat prefix caching.
# 5x original targets for higher KV pressure
TOOL_OUTPUT_TOKEN_TARGETS = [1640, 1510, 2455, 1335, 2730, 1930, 775]

# Word pool for generating realistic-looking random tool output.
_WORD_POOL = (
    "def class import return self args kwargs None True False if else elif "
    "for while try except finally raise with as from async await yield "
    "int str list dict set tuple float bool bytes type len range print "
    "open read write close flush seek tell readline readlines append extend "
    "insert remove pop clear copy update items keys values get setdefault "
    "join split strip lstrip rstrip replace find index count startswith "
    "endswith upper lower title format encode decode isdigit isalpha "
    "isinstance issubclass hasattr getattr setattr delattr callable "
    "staticmethod classmethod property super object type id hash repr "
    "logger debug info warning error critical exception traceback "
    "request response status_code headers body json params query path "
    "database connection pool cursor execute fetch commit rollback close "
    "table column index primary foreign unique constraint migration "
    "config settings env secret_key debug_mode port host bind address "
    "router endpoint middleware handler filter serializer validator "
    "test assert mock patch fixture setup teardown parametrize mark "
    "PASSED FAILED ERROR SKIP WARNING TODO BUG FIXME HACK NOTE XXX "
    "src tests docs build dist node_modules venv .git .env Makefile "
    "README LICENSE CHANGELOG requirements setup.py pyproject.toml "
    "0 1 2 3 4 5 6 7 8 9 0x00 0xff 127.0.0.1 localhost 8080 443 "
    "GET POST PUT DELETE PATCH HEAD OPTIONS HTTP/1.1 200 201 400 404 500 "
    "utf-8 ascii json yaml toml xml html css js py rs go java rb "
    "== != >= <= += -= *= /= //= %= **= &= |= ^= <<= >>= "
).split()


def _generate_random_tool_output(job_id: str, turn_idx: int,
                                  target_tokens: int) -> str:
    """Generate random tool output with approximately target_tokens tokens.

    Uses a seeded RNG per (job_id, turn_idx) for reproducibility.
    The output looks like a mix of file listings, code, and command output
    but is unique per job, defeating prefix caching.
    """
    seed = hashlib.md5(f"{job_id}:{turn_idx}".encode()).hexdigest()
    rng = random.Random(seed)

    # Header with unique job context (ensures first tokens differ across jobs)
    header = f"[{job_id}:turn{turn_idx}:{seed[:8]}] "

    lines = [header]
    # Measured: ~2.0 tokens per word with this word pool
    words_needed = int(target_tokens / 2.0)
    words_generated = len(header.split())

    while words_generated < words_needed:
        line_len = rng.randint(5, 20)
        line_words = [rng.choice(_WORD_POOL) for _ in range(line_len)]

        r = rng.random()
        if r < 0.2:
            # File path line
            depth = rng.randint(1, 4)
            path = "/".join(rng.choice(["src", "lib", "tests", "api", "core",
                                         "utils", "models", "views", "db"])
                           for _ in range(depth))
            ext = rng.choice([".py", ".js", ".ts", ".go", ".rs", ".java"])
            size = rng.choice(["1.2K", "3.5K", "7.8K", "12.4K", "256B"])
            name = ''.join(rng.choices(string.ascii_lowercase, k=rng.randint(4, 12)))
            line = f"-rw-r--r-- 1 user user {size} ./{path}/{name}{ext}"
        elif r < 0.35:
            # Grep-like result
            lineno = rng.randint(1, 500)
            fname = '_'.join(rng.choices(_WORD_POOL[:30], k=2))
            line = f"src/{fname}.py:{lineno}: {' '.join(line_words[:8])}"
        elif r < 0.5:
            # Test result line
            status = rng.choice(["PASSED", "PASSED", "PASSED", "FAILED", "ERROR"])
            pct = rng.randint(1, 100)
            tname = '_'.join(rng.choices(_WORD_POOL[:20], k=2))
            tname2 = '_'.join(rng.choices(_WORD_POOL[:20], k=2))
            line = f"tests/test_{tname}.py::test_{tname2} {status} [{pct:>3d}%]"
        else:
            indent = "    " * rng.randint(0, 3)
            line = indent + " ".join(line_words)

        lines.append(line)
        words_generated += len(line.split())

    return "\n".join(lines)


def get_tool_output(job_id: str, turn_idx: int) -> str:
    """Get randomized tool output for a specific job and turn."""
    if turn_idx < len(TOOL_OUTPUT_TOKEN_TARGETS):
        target = TOOL_OUTPUT_TOKEN_TARGETS[turn_idx]
    else:
        target = 300
    return _generate_random_tool_output(job_id, turn_idx, target)


TASKS = [
    "List all Python files with sizes to understand the project structure.",
    "Read the main application file to understand the architecture.",
    "Read the database module - there seem to be connection pool issues.",
    "Search for all TODO, BUG, and FIXME comments across the codebase.",
    "Run the test suite to see what's currently failing.",
    "Read the API routes to understand the endpoint structure.",
    "Fix the race condition bug in the database connection pool.",
    "Run the tests again to verify the fix works.",
]

# Fixed tool execution time for controlled experiment
FIXED_TOOL_TIME = 0.5  # seconds — uniform across all tools


def sample_tool_time(turn_idx):
    """Return fixed tool execution time (0.5s for all tools)."""
    return FIXED_TOOL_TIME


@dataclass
class JobResult:
    job_id: str
    start_time: float = 0
    end_time: float = 0
    turns: list = field(default_factory=list)

    @property
    def duration(self):
        return self.end_time - self.start_time


def run_job(base_url, model_id, job_id, n_turns, max_tokens=150):
    """Run a single multi-turn agent job with accumulated context."""
    client = OpenAI(base_url=f"{base_url}/v1", api_key="EMPTY")
    result = JobResult(job_id=job_id)
    result.start_time = time.time()

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    for i in range(n_turns):
        is_last = (i == n_turns - 1)
        task = TASKS[i % len(TASKS)]
        messages.append({"role": "user", "content": task})

        try:
            t0 = time.time()
            resp = client.chat.completions.create(
                model=model_id,
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.1,
                extra_body={
                    "job_id": job_id,
                    "is_last_step": is_last,
                    "min_tokens": max_tokens,  # force exact token count
                },
            )
            latency = time.time() - t0
            usage = resp.usage
            output = resp.choices[0].message.content

            result.turns.append({
                "turn": i + 1,
                "request_id": resp.id,
                "prompt_tokens": usage.prompt_tokens,
                "completion_tokens": usage.completion_tokens,
                "latency_ms": round(latency * 1000),
            })

            messages.append({"role": "assistant", "content": output})

            if not is_last and i < len(TOOL_OUTPUT_TOKEN_TARGETS):
                # Add per-job randomized tool output (unique per job)
                tool_out = get_tool_output(job_id, i)
                messages.append({"role": "user", "content": f"Command output:\n{tool_out}"})
                # Simulate variable tool execution time
                tool_time = sample_tool_time(i)
                time.sleep(tool_time)

        except Exception as e:
            result.turns.append({
                "turn": i + 1,
                "error": str(e),
                "latency_ms": 0,
            })

    result.end_time = time.time()
    return result


def poisson_arrival(jps, duration_s, base_url, model_id, n_turns, max_tokens=150, seed=42):
    """Generate jobs with Poisson arrival process."""
    results = []
    results_lock = threading.Lock()
    threads = []
    job_count = 0
    start_time = time.time()

    def _run_and_store(jid, n_turns):
        r = run_job(base_url, model_id, jid, n_turns, max_tokens=max_tokens)
        with results_lock:
            results.append(r)

    # Fixed seed for reproducible arrival pattern
    random.seed(seed)
    print(f"Starting Poisson arrival: JPS={jps}, duration={duration_s}s")
    print(f"Expected total jobs: ~{int(jps * duration_s)}")
    print()

    while time.time() - start_time < duration_s:
        # Poisson inter-arrival time
        wait = random.expovariate(jps)
        time.sleep(wait)

        if time.time() - start_time >= duration_s:
            break

        job_id = f"job_{job_count:04d}"
        job_count += 1
        t = threading.Thread(target=_run_and_store, args=(job_id, n_turns))
        t.start()
        threads.append(t)

        if job_count % 10 == 0:
            active = sum(1 for t in threads if t.is_alive())
            elapsed = time.time() - start_time
            print(f"  t={elapsed:.0f}s: launched {job_count} jobs, {active} active")

    # Wait for all jobs to finish
    print(f"\nAll {job_count} jobs launched. Waiting for completion...")
    for t in threads:
        t.join(timeout=120)

    return results


def get_server_stats(base_url):
    """Get cache stats from /metrics."""
    import requests
    try:
        r = requests.get(f"{base_url}/metrics", timeout=5)
        stats = {}
        for line in r.text.split("\n"):
            if line.startswith("vllm:kv_cache_usage_perc{"):
                stats["kv_cache_usage"] = float(line.split()[-1])
        return stats
    except Exception:
        return {}


def main():
    parser = argparse.ArgumentParser(description="A/B Benchmark: FCFS vs Continuum")
    parser.add_argument("--policy", required=True, )
    parser.add_argument("--port", type=int, default=8199)
    parser.add_argument("--jps", type=float, default=2.0,
                        help="Jobs Per Second (Poisson arrival rate)")
    parser.add_argument("--duration", type=int, default=120,
                        help="Duration of Poisson arrival in seconds")
    parser.add_argument("--turns", type=int, default=8,
                        help="Number of turns per job")
    parser.add_argument("--max-tokens", type=int, default=150,
                        help="Max tokens per completion")
    parser.add_argument("--output-dir", default="./ab_results")
    args = parser.parse_args()

    base_url = f"http://localhost:{args.port}"

    # Health check
    import requests as req
    try:
        r = req.get(f"{base_url}/health", timeout=5)
        assert r.status_code == 200
    except Exception as e:
        print(f"Server not ready: {e}")
        return

    # Get model
    client = OpenAI(base_url=f"{base_url}/v1", api_key="EMPTY")
    model_id = client.models.list().data[0].id

    print(f"{'='*70}")
    print(f"A/B Benchmark: policy={args.policy}")
    print(f"{'='*70}")
    print(f"Model: {model_id}")
    print(f"JPS: {args.jps} (Poisson arrival)")
    print(f"Duration: {args.duration}s")
    print(f"Turns/job: {args.turns}")
    print(f"Expected jobs: ~{int(args.jps * args.duration)}")
    print(f"{'='*70}\n")

    # Write JPS marker to scheduler trace + signal file for server-side tagging
    trace_path = os.environ.get("SCHED_TRACE_PATH")
    if trace_path:
        import json as _json
        # 1. Write run_marker event to trace file
        with open(trace_path, "a") as _f:
            _f.write(_json.dumps({
                "event": "run_marker",
                "jps": args.jps,
                "policy": args.policy,
                "duration": args.duration,
                "ts": time.time(),
            }) + "\n")
        # 2. Write JPS signal file (server reads this to tag its own events)
        signal_path = os.path.join(os.path.dirname(trace_path), ".jps_signal")
        with open(signal_path, "w") as _f:
            _f.write(str(args.jps))

    # Run benchmark
    results = poisson_arrival(
        jps=args.jps,
        duration_s=args.duration,
        base_url=base_url,
        model_id=model_id,
        n_turns=args.turns,
        max_tokens=args.max_tokens,
    )

    # Collect server stats
    server_stats = get_server_stats(base_url)

    # Analyze
    print(f"\n{'='*70}")
    print(f"RESULTS: {args.policy}")
    print(f"{'='*70}")

    completed = [r for r in results if r.duration > 0]
    durations = [r.duration for r in completed]
    n_errors = sum(1 for r in results for t in r.turns if "error" in t)

    if durations:
        durations.sort()
        avg_duration = sum(durations) / len(durations)
        median_duration = durations[len(durations) // 2]
        p90 = durations[int(len(durations) * 0.9)]
        p95 = durations[int(len(durations) * 0.95)]

        print(f"Completed jobs:   {len(completed)}")
        print(f"Errors:           {n_errors}")
        print(f"Avg job duration: {avg_duration:.2f}s")
        print(f"Median duration:  {median_duration:.2f}s")
        print(f"P90 duration:     {p90:.2f}s")
        print(f"P95 duration:     {p95:.2f}s")
        print(f"Min/Max:          {min(durations):.2f}s / {max(durations):.2f}s")

        # Per-turn latency
        latencies_by_turn = {}
        tokens_by_turn = {}
        for r in completed:
            for t in r.turns:
                if "error" not in t:
                    turn = t["turn"]
                    latencies_by_turn.setdefault(turn, []).append(t["latency_ms"])
                    tokens_by_turn.setdefault(turn, []).append(t["prompt_tokens"])

        print(f"\nPer-turn averages:")
        print(f"{'Turn':<6} {'Avg Latency':>12} {'Avg Prompt':>12}")
        print("-" * 32)
        for t in sorted(latencies_by_turn):
            avg_lat = sum(latencies_by_turn[t]) / len(latencies_by_turn[t])
            avg_tok = sum(tokens_by_turn[t]) / len(tokens_by_turn[t])
            print(f"  {t:<4} {avg_lat:>10.0f} ms {avg_tok:>10.0f}")
    else:
        print("No completed jobs!")

    # Save
    os.makedirs(args.output_dir, exist_ok=True)
    output = {
        "policy": args.policy,
        "jps": args.jps,
        "duration_s": args.duration,
        "turns_per_job": args.turns,
        "total_jobs": len(results),
        "completed_jobs": len(completed),
        "errors": n_errors,
        "avg_duration_s": round(avg_duration, 3) if durations else None,
        "median_duration_s": round(median_duration, 3) if durations else None,
        "p90_duration_s": round(p90, 3) if durations else None,
        "p95_duration_s": round(p95, 3) if durations else None,
        "server_stats": server_stats,
        "per_turn_avg_latency_ms": {
            str(t): round(sum(lats)/len(lats))
            for t, lats in latencies_by_turn.items()
        } if durations else {},
        "per_turn_avg_prompt_tokens": {
            str(t): round(sum(toks)/len(toks))
            for t, toks in tokens_by_turn.items()
        } if durations else {},
        "job_durations": [round(d, 3) for d in durations],
        "jobs": [
            {
                "job_id": r.job_id,
                "start_time": round(r.start_time, 3),
                "duration_s": round(r.duration, 3),
                "turns": r.turns,
            }
            for r in completed
        ],
    }
    outfile = os.path.join(args.output_dir, f"{args.policy}_jps{args.jps}.json")
    with open(outfile, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nSaved to {outfile}")


if __name__ == "__main__":
    main()
