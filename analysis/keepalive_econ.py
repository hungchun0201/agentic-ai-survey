#!/usr/bin/env python3
"""V6-ECON: keepalive-vs-expire economics on real TraceLab gaps (see DIRECTION.md C2).
Anthropic 5-min-TTL contract: write 1.25x, read 0.1x, hit refreshes TTL free.
Per gap g with resident prefix L (tokens): expire-cost = (1.25-0.1)L; keepalive-cost =
0.1L * floor(g/TTL). Emits corpus totals + per-session savings distribution."""
import gzip, json, datetime, argparse, statistics as st

def ts_of(r):
    for e in (r.get("timing_events") or []):
        if e.get("timestamp"):
            return datetime.datetime.fromisoformat(e["timestamp"].replace("Z","+00:00"))
    return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trace", required=True)
    ap.add_argument("--ttl", type=float, default=300.0)
    ap.add_argument("--write-mult", type=float, default=1.25)
    ap.add_argument("--read-mult", type=float, default=0.1)
    a = ap.parse_args()
    by = {}
    with gzip.open(a.trace, "rt") as f:
        for line in f:
            r = json.loads(line)
            if r.get("provider") != "claude":
                continue
            by.setdefault(r["session_id"], []).append(r)
    naive = keep = opt = 0.0
    per_sess = []
    for sid, rows in by.items():
        rows.sort(key=lambda r: r["round_index"])
        times = [ts_of(r) for r in rows]
        sn = sk = so = 0.0
        for i in range(1, len(rows)):
            if times[i] is None or times[i-1] is None:
                continue
            g = (times[i] - times[i-1]).total_seconds()
            L = rows[i].get("prefix_tokens") or 0
            if g <= a.ttl or L <= 0:
                continue
            c_exp = (a.write_mult - a.read_mult) * L
            c_keep = a.read_mult * L * int(g // a.ttl)
            sn += c_exp; sk += c_keep; so += min(c_exp, c_keep)
        naive += sn; keep += sk; opt += so
        if sn > 0:
            per_sess.append(1 - so / sn)
    print(f"corpus token-cost units: naive={naive/1e6:.1f}M keepalive={keep/1e6:.1f}M optimal={opt/1e6:.1f}M")
    print(f"savings: keepalive {100*(1-keep/naive):.1f}% | optimal {100*(1-opt/naive):.1f}%")
    per_sess.sort()
    n = len(per_sess)
    print(f"per-session optimal savings: n={n} p10={per_sess[int(.1*n)]:.2f} p50={per_sess[n//2]:.2f} p90={per_sess[int(.9*n)]:.2f}")

if __name__ == "__main__":
    main()
