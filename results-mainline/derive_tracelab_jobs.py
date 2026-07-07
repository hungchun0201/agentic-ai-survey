#!/usr/bin/env python3
"""TraceLab -> continuum_d replay jobs (count-faithful, real recorded gaps).

Selection: Claude-provider sessions, >=8 rounds, max input_tokens_total <= CTX_CAP.
No monotonicity filter: real Claude Code sessions include context compactions;
synthesis keeps ids prefix-consistent with the recorded prefix_tokens, so the
replayed cache behavior (hits on kept prefix, miss on compacted tail) matches
the recorded session's own cache accounting.
Token ids are synthetic (uniform in a safe Llama-3.1 vocab range) with the
recorded per-round prefix/append/output COUNTS — count-faithful replay: the
memory system sees the recorded context sizes, sharing structure, and timing.
Gaps: recorded max tool wall latency per round (capped in the bench via
--gap-cap-s); rounds with no tool events get gap 0 (agent chains immediately).
"""
import gzip, json, random, sys

SRC = "syfi_coding_trace.jsonl.gz"
CTX_CAP = 32000
N_JOBS = 100
MIN_ROUNDS, MAX_ROUNDS = 8, 40
random.seed(42)

by = {}
with gzip.open(SRC, "rt") as f:
    for line in f:
        r = json.loads(line)
        if r.get("provider") != "claude":
            continue
        by.setdefault(r["session_id"], []).append(r)

cands = []
for sid, rows in by.items():
    if not (MIN_ROUNDS <= len(rows) <= MAX_ROUNDS):
        continue
    rows.sort(key=lambda r: r["round_index"])
    if max(r["input_tokens_total"] for r in rows) > CTX_CAP:
        continue
    if any(r["input_tokens_total"] <= 0 or r["output_tokens"] < 0 for r in rows):
        continue
    cands.append((sid, rows))

print(f"eligible sessions: {len(cands)}", file=sys.stderr)
random.shuffle(cands)
cands = cands[:N_JOBS]

def ids(n):
    return [random.randrange(2000, 100000) for _ in range(n)]

jobs = []
for k, (sid, rows) in enumerate(cands):
    ctx = []
    turns = []
    for i, r in enumerate(rows):
        total = r["input_tokens_total"]
        pfx = min(max(r["prefix_tokens"], 0), len(ctx), total)
        ctx = ctx[:pfx] + ids(total - pfx)
        out_n = max(1, min(r["output_tokens"], 2048))
        tools = r.get("tools") or []
        gap_ms = max((t.get("tool_wall_latency_ms") or 0) for t in tools) if tools else 0
        turns.append({
            "turn_idx": i,
            "input_text_len": r.get("current_input_chars") or 0,
            "input_token_ids": list(ctx),
            "output_text_len": 0,
            "output_token_ids": ids(out_n),
            "tool_name": (tools[0].get("tool_name") if tools else "none"),
            "gap_s": round(gap_ms / 1000.0, 3),
        })
        ctx = ctx + turns[-1]["output_token_ids"]
    jobs.append({
        "job_id": f"tl_{k:04d}", "instance_id": sid[:40], "n_turns": len(turns),
        "turns": turns,
        "total_input_max": max(t and len(t["input_token_ids"]) for t in turns),
        "total_output_sum": sum(len(t["output_token_ids"]) for t in turns),
    })

with open("jobs_100_tracelab.json", "w") as f:
    json.dump(jobs, f)
import statistics as st
mx = [j["total_input_max"] for j in jobs]
nt = [j["n_turns"] for j in jobs]
gp = [t["gap_s"] for j in jobs for t in j["turns"] if t["gap_s"] > 0]
print(f"jobs={len(jobs)} turns={sum(nt)} ctx p50={st.median(mx):.0f} max={max(mx)} "
      f"turns/job p50={st.median(nt)} gaps>0 p50={st.median(gp):.1f}s p99={sorted(gp)[int(0.99*len(gp))]:.0f}s", file=sys.stderr)
