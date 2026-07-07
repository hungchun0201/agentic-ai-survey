# SPDX-License-Identifier: Apache-2.0
"""Continuum-D benchmark: multi-turn agent jobs vs VRAM<->DRAM policies.

Drives a `vllm serve` subprocess per condition over HTTP, measuring per-turn
TTFT and job completion time (JCT) under a Poisson job-arrival, multi-turn,
tool-gap workload. Scrapes /metrics for KV-transfer counters.

Conditions (--condition):
  no_offload              baseline, no KV offloading
  lru                     native OffloadingConnector, default LRU policy
  job_aware               continuum_d JobAwareOffloadingSpec (+admission control)
  job_aware_warm          job_aware + client-side predictive warm request per gap
  job_aware_metadata_off  E2 ablation: job_aware with exact_tags=False -- last_turn
                          + expected_gap blinded (idle-order fallback within classes)
  mori_proxy              E2 baseline: MoriProxyOffloadingSpec observed-idleness
                          ranking (relative idleness + observed admission, no tags)

Usage:
  .venv-cd/bin/python benchmarks/continuum_d_bench.py \
      --model meta-llama/Llama-3.1-8B-Instruct --condition lru \
      --jobs 24 --turns 6 --jps 2 --dram-gb 24 --out results-local/continuum-d
"""

import argparse
import asyncio
import json
import os
import random
import signal
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
VLLM_BIN = os.environ.get("CD_VLLM_BIN", str(REPO / ".venv-cd/bin/vllm"))
PORT = int(os.environ.get("CD_PORT", "18321"))
BASE = f"http://127.0.0.1:{PORT}"


def build_server_cmd(args) -> tuple[list[str], dict]:
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{REPO}/.pylib:{env.get('PYTHONPATH','')}"
    cmd = [
        VLLM_BIN, "serve", args.model,
        "--port", str(PORT),
        "--seed", str(args.seed),
        "--gpu-memory-utilization", str(args.gpu_mem_util),
        "--max-model-len", str(args.max_model_len),
        "--enable-prefix-caching",
    ]
    if getattr(args, "max_num_seqs", 0):
        cmd += ["--max-num-seqs", str(args.max_num_seqs)]
    if args.condition != "no_offload":
        extra = {"offload_prompt_only": False}
        if args.condition in ("job_aware", "job_aware_warm"):
            extra.update({
                "spec_name": "JobAwareOffloadingSpec",
                "spec_module_path": "continuum_d.spec",
                "admission_control": True,
            })
        elif args.condition == "job_aware_metadata_off":
            # E2 ablation: SAME job-aware spec, but exact_tags=False blinds the
            # policy to last_turn + expected_gap (falls back to idle-order within
            # the eviction classes; job_id grouping + admission kept).
            extra.update({
                "spec_name": "JobAwareOffloadingSpec",
                "spec_module_path": "continuum_d.spec",
                "admission_control": True,
                "exact_tags": False,
            })
        elif args.condition == "mori_proxy":
            # E2 honest baseline: observed-idleness ranking (no client tags).
            extra.update({
                "spec_name": "MoriProxyOffloadingSpec",
                "spec_module_path": "continuum_d.spec",
                "admission_control": True,
            })
        elif args.condition == "continuum_ttl":
            # M2 baseline: Continuum/CacheTTL keep-resident TTL pin from
            # expected_gap_ms (same signal as job_aware, PIN mechanism).
            extra.update({
                "spec_name": "ContinuumTTLOffloadingSpec",
                "spec_module_path": "continuum_d.spec",
            })
        elif args.condition == "lru_lastturn":
            # Cold-gate ablation: LRU + last_turn reclaim, no admission gate.
            extra.update({
                "spec_name": "LRULastTurnOffloadingSpec",
                "spec_module_path": "continuum_d.spec",
            })
        elif args.condition == "gated_ttl":
            # Fairness baseline: Tenure's admission gate + TTL pin ordering.
            extra.update({
                "spec_name": "GatedTTLOffloadingSpec",
                "spec_module_path": "continuum_d.spec",
            })
        elif args.condition in ("marconi_lt", "mori_lt", "ttl_lt"):
            # Signal-matched baselines: base ordering + last_turn reclaim, no gate.
            spec = {"marconi_lt": "MarconiLTOffloadingSpec",
                    "mori_lt": "MoriLTOffloadingSpec",
                    "ttl_lt": "TTLLTOffloadingSpec"}[args.condition]
            extra.update({
                "spec_name": spec,
                "spec_module_path": "continuum_d.spec",
            })
        elif args.condition == "tinylfu_adm":
            # Standard cache-admission baseline (TinyLFU frequency filter + LRU).
            extra.update({
                "spec_name": "TinyLFUOffloadingSpec",
                "spec_module_path": "continuum_d.spec",
            })
        elif args.condition == "marconi_util":
            # M2 baseline: Marconi-style recency + alpha*flop-efficiency
            # eviction, admit-everything, no lifecycle signals (MLSys'25 scope).
            extra.update({
                "spec_name": "MarconiUtilOffloadingSpec",
                "spec_module_path": "continuum_d.spec",
            })
        elif args.condition in ("codesign_joint", "codesign_decoupled",
                                "codesign_fp16"):
            # Precision-as-admission-currency: the JOINT precision+residency
            # scheduler (codesign_joint) vs the DECOUPLED baseline
            # (codesign_decoupled = TriAxialKV-offline-precision (+) MORI-admission)
            # vs the fp16 control -- all one spec, one flag.
            extra.update({
                "spec_name": "PrecisionOffloadingSpec",
                "spec_module_path": "continuum_d.precision_spec",
                "admission_control": True,
                "precision_mode": args.condition.split("_", 1)[1],
                "accuracy_profile": args.accuracy_profile,
            })
        kvt = {
            "kv_connector": "OffloadingConnector",
            "kv_role": "kv_both",
            "kv_connector_extra_config": {
                **extra,
                "cpu_bytes_to_use": int(args.dram_gb * (1 << 30)),
            },
        }
        cmd += ["--kv-transfer-config", json.dumps(kvt)]
    return cmd, env


def wait_health(proc, timeout=600):
    t0 = time.time()
    while time.time() - t0 < timeout:
        if proc.poll() is not None:
            raise RuntimeError(f"server died rc={proc.returncode}")
        try:
            urllib.request.urlopen(f"{BASE}/health", timeout=2)
            return
        except Exception:
            time.sleep(2)
    raise TimeoutError("server health timeout")


def scrape_metrics() -> dict:
    try:
        text = urllib.request.urlopen(f"{BASE}/metrics", timeout=5).read().decode()
    except Exception:
        return {}
    out = {}
    for line in text.splitlines():
        if line.startswith("#"):
            continue
        for pat in ("kv_offload", "kv_transfer", "prefix_cache",
                    "external"):
            if pat in line:
                try:
                    name, val = line.rsplit(" ", 1)
                    out[name] = float(val)
                except ValueError:
                    pass
    return out


TOK = None  # lazy tokenizer for prompt sizing
MODEL_NAME = "unset"
CAPTURE_OUTPUT = False  # when True, record each request's generated text ("out")
JOBS_DATA = None   # real-trace replay mode: list of jobs w/ per-turn token ids
REPLAY_CTX_CAP = 0  # max prompt tokens allowed in replay mode (skip longer turns)


def make_prompt(job_id: int, turn: int, seg_tokens: int) -> str:
    """Deterministic per-job growing prompt (shared prefix across turns)."""
    rng = random.Random(job_id * 1000)
    base = f"[JOB {job_id}] system: you are agent {job_id}. "
    words = []
    for t in range(turn + 1):
        trng = random.Random(job_id * 1000 + t + 1)
        words += [f"tok{trng.randint(0, 99999)}" for _ in range(seg_tokens)]
    return base + " ".join(words) + f"\nTurn {turn}: continue."


async def one_request(session_sem, prompt, max_tokens, kv_params, tag, results):
    import aiohttp
    body = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "max_tokens": max_tokens,
        "temperature": 0,
        "stream": True,
    }
    if JOBS_DATA is not None:
        body["ignore_eos"] = True  # forced-decode replay: reproduce trace output lengths
    if kv_params:
        body["kv_transfer_params"] = kv_params
    t0 = time.perf_counter()
    ttft = None
    # generous per-request timeout: under tight-VRAM contention a turn can
    # queue for a while; record a timeout/conn error as a result instead of
    # letting the exception crash the whole workload (which would lose the JSON).
    timeout = aiohttp.ClientTimeout(total=900, sock_read=900, sock_connect=60)
    try:
        async with session_sem() as session:
            async with session.post(f"{BASE}/v1/completions", json=body,
                                    timeout=timeout) as resp:
                if resp.status != 200:
                    results.append({"tag": tag, "error": resp.status,
                                    "text": (await resp.text())[:200]})
                    return
                text_parts = []
                async for _line in resp.content:
                    if _line.strip() and ttft is None:
                        ttft = time.perf_counter() - t0
                    if CAPTURE_OUTPUT and _line.startswith(b"data:"):
                        payload = _line[5:].strip()
                        if payload and payload != b"[DONE]":
                            try:
                                ch = json.loads(payload)["choices"][0]
                                text_parts.append(ch.get("text", ""))
                            except (ValueError, KeyError, IndexError):
                                pass
    except Exception as e:  # noqa: BLE001 - keep the workload alive on any net error
        results.append({"tag": tag, "error": "exc",
                        "text": f"{type(e).__name__}: {e}"[:200]})
        return
    rec = {
        "tag": tag, "ttft_s": ttft,
        "total_s": time.perf_counter() - t0,
        "prompt_chars": len(prompt),
    }
    if CAPTURE_OUTPUT:
        rec["out"] = "".join(text_parts)
    results.append(rec)


async def run_job(job_id, args, http, results, jstats):
    seg = args.seg_tokens
    t_start = time.perf_counter()
    replay = JOBS_DATA is not None
    if replay:
        jd = JOBS_DATA[job_id % len(JOBS_DATA)]
        turns_iter = jd["turns"]
        n_turns = len(turns_iter)
    else:
        n_turns = args.turns
    n_skipped = 0
    for turn in range(n_turns):
        if replay:
            td = turns_iter[turn]
            prompt = td["input_token_ids"]
            if REPLAY_CTX_CAP and len(prompt) > REPLAY_CTX_CAP:
                n_skipped += 1
                continue  # turn exceeds model context budget; record via jstats
            gen_this = max(1, min(len(td.get("output_token_ids", []) or [1]),
                                  args.gen_tokens))
        else:
            prompt = make_prompt(job_id, turn, seg)
            gen_this = args.gen_tokens
        last = turn == n_turns - 1
        gap_ms = 0.0
        if not last:
            if replay and td.get("gap_s") is not None:
                # trace-recorded tool gap (TraceLab column); same cap applies
                gap_ms = float(td["gap_s"]) * 1000.0
            else:
                gap_ms = random.Random(
                    args.seed * 1_000_003 + job_id * 77 + turn).lognormvariate(
                    args.gap_mu, args.gap_sigma) * 1000.0
            gap_ms = min(gap_ms, args.gap_cap_s * 1000.0)
        # chat-template role of this turn + reuse-probability drive the precision
        # policy (ignored by the non-codesign specs). Roles cycle through the
        # sensitive/tolerant mix; reuse_prob decays with turn age so recent turns
        # are "hot" -- giving the joint policy real (role, reuse) heterogeneity.
        role_cycle = ["system", "tool_call", "reasoning", "tool_result",
                      "user", "filler"]
        if replay:
            role = ("system" if turn == 0
                    else ("tool_result" if td.get("tool_name") else "reasoning"))
        else:
            role = "system" if turn == 0 else role_cycle[turn % len(role_cycle)]
        reuse_prob = round(max(0.05, 0.95 - 0.12 * turn), 3)
        # CD_HINT_NOISE perturbs the *hint* only (the actual gap slept is unchanged):
        #   exact (default) | pm25 | pm50 | random | missing50 | none
        # CD_NO_LASTTURN=1 strips the last_turn signal (no instant reclaim).
        hint_ms = gap_ms
        noise = os.environ.get("CD_HINT_NOISE", "exact")
        hr = random.Random(args.seed * 7_919 + job_id * 131 + turn)
        if noise == "pm25":
            hint_ms = gap_ms * hr.uniform(0.75, 1.25)
        elif noise == "pm50":
            hint_ms = gap_ms * hr.uniform(0.5, 1.5)
        elif noise == "random":
            hint_ms = hr.uniform(0.0, args.gap_cap_s * 1000.0)
        elif noise == "missing50":
            hint_ms = gap_ms if hr.random() < 0.5 else 0.0
        elif noise == "none":
            hint_ms = 0.0
        last_signal = last and os.environ.get("CD_NO_LASTTURN", "0") != "1"
        # CD_LT_MODE perturbs the last_turn signal itself:
        #   exact (default) | missing50 (half of sessions never signal) |
        #   falsepos (a random mid-session turn also signals end)
        lt_mode = os.environ.get("CD_LT_MODE", "exact")
        ltr = random.Random(args.seed * 104_729 + job_id * 17)
        if lt_mode == "missing50" and ltr.random() < 0.5:
            last_signal = False
        elif lt_mode == "falsepos" and not last:
            # ~1 false end-signal per session on average
            if random.Random(args.seed * 104_729 + job_id * 17 + turn).random() < 1.0 / max(n_turns, 1):
                last_signal = True
        kvp = {
            "job_id": f"job-{job_id}",
            "turn_idx": turn,
            "expected_gap_ms": hint_ms,
            "last_turn": last_signal,
            "role": role,
            "reuse_prob": reuse_prob,
        }
        await one_request(http, prompt, gen_this, kvp,
                          f"job{job_id}/t{turn}", results)
        if not last:
            gap_s = gap_ms / 1000.0
            if args.condition == "job_aware_warm" and gap_s > args.warm_lead_s:
                await asyncio.sleep(gap_s - args.warm_lead_s)
                # predictive warm: touch the full prefix so DRAM->VRAM
                # promotion happens before the real turn arrives
                warm_kvp = dict(kvp, turn_idx=turn + 0.5)
                await one_request(http, prompt, 1, warm_kvp,
                                  f"job{job_id}/warm{turn}", results)
                await asyncio.sleep(args.warm_lead_s)
            else:
                await asyncio.sleep(gap_s)
    jrec = {"job": job_id, "jct_s": time.perf_counter() - t_start}
    if replay:
        jrec["instance_id"] = jd.get("instance_id", "")
        jrec["n_turns"] = n_turns
        jrec["n_skipped_ctx"] = n_skipped
    jstats.append(jrec)


async def run_workload(args):
    import aiohttp
    results, jstats = [], []
    conn = aiohttp.TCPConnector(limit=256)
    async with aiohttp.ClientSession(connector=conn) as session:
        def http():
            class _S:
                async def __aenter__(self):
                    return session
                async def __aexit__(self, *a):
                    return False
            return _S()
        tasks = []
        rng = random.Random(1000 + args.seed)
        t0 = time.perf_counter()
        # If the jobs file carries recorded arrival offsets (fully-real window
        # replay), honor them; otherwise draw Poisson inter-arrivals.
        real_offsets = (JOBS_DATA is not None and len(JOBS_DATA) > 0
                        and JOBS_DATA[0].get("arrival_offset_s") is not None)
        for j in range(args.jobs):
            if real_offsets and j < len(JOBS_DATA):
                target = float(JOBS_DATA[j]["arrival_offset_s"])
                now = time.perf_counter() - t0
                if target > now:
                    await asyncio.sleep(target - now)
            else:
                delay = rng.expovariate(args.jps) if args.jps > 0 else 0
                await asyncio.sleep(delay)
            tasks.append(asyncio.create_task(
                run_job(j, args, http, results, jstats)))
        await asyncio.gather(*tasks)
        wall = time.perf_counter() - t0
    return results, jstats, wall


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model", default="facebook/opt-125m")
    p.add_argument("--condition", required=True,
                   choices=["no_offload", "lru", "job_aware", "job_aware_warm",
                            "job_aware_metadata_off", "mori_proxy",
                            "marconi_util", "continuum_ttl", "lru_lastturn", "gated_ttl",
                            "marconi_lt", "mori_lt", "ttl_lt", "tinylfu_adm",
                            "codesign_joint", "codesign_decoupled",
                            "codesign_fp16"])
    p.add_argument("--accuracy-profile", default="literature_pessimistic",
                   help="per-role accuracy-loss profile the precision policy "
                        "reads (swap for Bet4's measured BFCL curve when it lands)")
    p.add_argument("--capture-output", action="store_true",
                   help="record each request's generated text (for the "
                        "output-preservation comparison across conditions)")
    p.add_argument("--jobs", type=int, default=24)
    p.add_argument("--turns", type=int, default=6)
    p.add_argument("--jps", type=float, default=2.0)
    p.add_argument("--seg-tokens", type=int, default=256)
    p.add_argument("--gen-tokens", type=int, default=64)
    p.add_argument("--gap-mu", type=float, default=1.6)   # lognormal ~5s
    p.add_argument("--gap-sigma", type=float, default=0.5)
    p.add_argument("--gap-cap-s", type=float, default=20.0)
    p.add_argument("--warm-lead-s", type=float, default=1.5)
    p.add_argument("--dram-gb", type=float, default=24.0)
    p.add_argument("--gpu-mem-util", type=float, default=0.85)
    p.add_argument("--max-model-len", type=int, default=16384)
    p.add_argument("--max-num-seqs", type=int, default=0,
                   help="cap engine max_num_seqs (hybrid models: Mamba cache blocks bound)")
    p.add_argument("--seed", type=int, default=0,
                   help="drives arrival + tool-gap RNG and engine seed; "
                        "vary across replicates for bootstrap CIs")
    p.add_argument("--jobs-file", default=None,
                   help="real-trace replay: JSON list of jobs with per-turn "
                        "input_token_ids/output_token_ids (e.g. SWE-smith "
                        "jobs_100_pinjab.json). Overrides --jobs/--turns/"
                        "--seg-tokens; --gen-tokens becomes the output cap.")
    p.add_argument("--max-jobs", type=int, default=0,
                   help="replay mode: use only the first N jobs (0 = all)")
    p.add_argument("--out", default="results-local/continuum-d")
    args = p.parse_args()

    global MODEL_NAME, CAPTURE_OUTPUT, JOBS_DATA, REPLAY_CTX_CAP
    MODEL_NAME = args.model
    CAPTURE_OUTPUT = args.capture_output
    if args.jobs_file:
        with open(args.jobs_file) as jf:
            JOBS_DATA = json.load(jf)
        if args.max_jobs:
            JOBS_DATA = JOBS_DATA[: args.max_jobs]
        args.jobs = len(JOBS_DATA)
        # leave headroom for the largest per-turn generation
        REPLAY_CTX_CAP = max(1024, args.max_model_len - args.gen_tokens - 64)
        n_t = sum(len(j["turns"]) for j in JOBS_DATA)
        print(f"REPLAY MODE: {len(JOBS_DATA)} jobs / {n_t} turns from "
              f"{args.jobs_file} (ctx cap {REPLAY_CTX_CAP})", flush=True)
    outdir = Path(args.out); outdir.mkdir(parents=True, exist_ok=True)
    # NVIDIA driver on this box fails sysmem allocs under fragmentation
    # (NVRM "Cannot allocate sysmem through fb heap") -> compact first.
    subprocess.run(
        ["sudo", "-n", "sh", "-c",
         "sync; echo 3 > /proc/sys/vm/drop_caches; "
         "echo 1 > /proc/sys/vm/compact_memory"],
        check=False, capture_output=True)
    cmd, env = build_server_cmd(args)
    print("SERVER:", " ".join(cmd), flush=True)
    logf = open(outdir / f"server_{args.condition}.log", "w")
    proc = subprocess.Popen(cmd, env=env, cwd=str(REPO / ".pylib"), stdout=logf, stderr=subprocess.STDOUT)
    try:
        wait_health(proc)
        print("server healthy; running workload", flush=True)
        results, jstats, wall = asyncio.run(run_workload(args))
        metrics = scrape_metrics()
    finally:
        proc.send_signal(signal.SIGTERM)  # never kill -9 CUDA procs
        try:
            proc.wait(timeout=60)
        except subprocess.TimeoutExpired:
            proc.terminate(); proc.wait(timeout=60)
        logf.close()

    # JobAwareOffloadingManager logs its policy.stats as "CD_POLICY_STATS {json}"
    # (admission_refusals + evicted_per_class are in-memory only, not on
    # /metrics yet); take the last line = final cumulative counters.
    policy_stats = {}
    try:
        logtext = (outdir / f"server_{args.condition}.log").read_text(
            errors="ignore")
        for ln in reversed(logtext.splitlines()):
            i = ln.find("CD_POLICY_STATS ")
            if i != -1:
                policy_stats = json.loads(ln[i + len("CD_POLICY_STATS "):])
                break
    except (OSError, ValueError):
        pass

    real = [r for r in results if "warm" not in r.get("tag", "") and "error" not in r]
    errs = [r for r in results if "error" in r]
    per_turn = {}
    for r in real:
        t = int(r["tag"].split("/t")[1])
        per_turn.setdefault(t, []).append(r["ttft_s"])
    summary = {
        "condition": args.condition,
        "config": vars(args),
        "wall_s": wall,
        "n_ok": len(real), "n_err": len(errs),
        "avg_jct_s": sum(j["jct_s"] for j in jstats) / max(len(jstats), 1),
        "avg_ttft_s": sum(r["ttft_s"] for r in real) / max(len(real), 1),
        "per_turn_avg_ttft": {t: sum(v) / len(v) for t, v in sorted(per_turn.items())},
        "metrics": metrics,
        "policy_stats": policy_stats,
    }
    tag = (f"{args.condition}_dram{int(args.dram_gb)}"
           f"_jps{args.jps}_seed{args.seed}")
    (outdir / f"{tag}.json").write_text(json.dumps(
        {"summary": summary, "jobs": jstats, "requests": results}, indent=1))
    print(json.dumps(summary, indent=1), flush=True)
    if summary["n_ok"] == 0 or summary["n_err"] > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
