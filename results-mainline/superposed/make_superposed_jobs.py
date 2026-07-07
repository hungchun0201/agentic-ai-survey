# SPDX-License-Identifier: Apache-2.0
"""Superposed real-arrival-window jobs generator (cold-review answer).

Takes the fully-real recorded window jobs_realwindow.json (TraceLab 2026-05-29
burst; 133 sessions, recorded arrival_offset_s + per-turn gap_s) and superposes
k independent copies: every session is duplicated k times with

  * job_id / instance_id suffixed _c0.._c{k-1}          (traceability)
  * arrival_offset_s UNCHANGED                          (fully-real arrivals)
  * per-turn gap_s UNCHANGED                            (fully-real think time)
  * token content identical EXCEPT one per-copy salt
    token prepended to every turn's input_token_ids.

Why the salt token: vLLM prefix caching and the OffloadingConnector tier are
content-addressed (block-hash keyed). Byte-identical copies would dedupe into
ONE set of KV blocks, so the superposed working set would not scale with k and
the pressure test would be vacuous. One distinct leading token per copy shifts
every downstream block hash, making the k copies cache-independent (the
"k teams, k distinct codebases" model) while keeping the workload 99.99+%
byte-identical and all within-copy prefix reuse intact (LCP relations are
preserved under a common prepended token). Salt ids 100100..100107 are ordinary
Llama-3.1 vocab ids outside the trace's id range [2000, 99999].

Copies of a session are emitted consecutively, so the file stays sorted by
arrival_offset_s (the bench's replay loop expects monotone arrival targets).

Usage: python3 make_superposed_jobs.py <jobs_realwindow.json> <k> <out.json>
"""
import json
import sys

SALT_BASE = 100100


def superpose(sessions, k):
    out = []
    for sess in sessions:
        for c in range(k):
            salt = SALT_BASE + c
            turns = [
                {**t, "input_token_ids": [salt] + t["input_token_ids"]}
                for t in sess["turns"]
            ]
            out.append({
                **sess,
                "job_id": f"{sess['job_id']}_c{c}",
                "instance_id": f"{sess['instance_id']}_c{c}",
                "turns": turns,
                "total_input_max": sess["total_input_max"] + 1,
            })
    return out


def main():
    src, k, dst = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    with open(src) as f:
        sessions = json.load(f)
    sup = superpose(sessions, k)
    offs = [s["arrival_offset_s"] for s in sup]
    assert offs == sorted(offs), "arrival offsets must stay monotone"
    assert len(sup) == k * len(sessions)
    with open(dst, "w") as f:
        json.dump(sup, f)
    n_turns = sum(len(s["turns"]) for s in sup)
    print(f"{dst}: {len(sup)} sessions / {n_turns} turns (k={k}, "
          f"salt ids {SALT_BASE}..{SALT_BASE + k - 1})")


if __name__ == "__main__":
    main()
