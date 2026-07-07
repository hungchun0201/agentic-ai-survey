"""Cache Contract cross-provider probe harness — M6, DRY-RUN ONLY.

Runs the black-box probe campaign against pluggable provider adapters
(anthropic, openai, gemini, deepseek, groq). In M6 every adapter replays
documented-behavior fixtures via DryRunTransport: ZERO live API calls.
The moment budget is approved, the same command with --live (plus env keys
and the M7 LiveTransport) launches the real campaign unchanged.

Probe types
  ttl_curve    write a unique ~2K-token random prefix, re-read after delay d in
               {30s, 1, 2, 4, 8, 16, 32, 64, 128 min}; verdict from billing
               (cache_read > 0) AND latency delta.
  granularity  prefix-match ladder: vary the suffix at token offsets and read
               the hit-prefix-length steps off the billing fields.
  claims_check replay each provider's documented-claims checklist
               (TTL value, refresh-on-hit, write premium, min cacheable length).

Usage
  python3 harness.py                      # dry-run, all providers, all probes
  python3 harness.py --providers anthropic,gemini --probes ttl_curve
  python3 harness.py --live               # refuses in M6 (NotImplementedError)
"""
from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

from adapters import PROVIDERS, make_adapter

TTL_GRID_S = (30, 60, 120, 240, 480, 960, 1920, 3840, 7680)  # 30s..128min, doubling
GRANULARITY_OFFSETS = (0, 256, 512, 768, 1024, 1152, 1280, 1536, 1792, 2048)
PREFIX_TOKENS = 2048      # "~2K token" unique random prefix per probe
SUFFIX_TOKENS = 256       # divergent tail appended in granularity probes
VOCAB = 50_000
LATENCY_HIT_RATIO = 0.75  # read latency <= 0.75x same-size miss baseline => latency says hit
PROBE_TYPES = ("ttl_curve", "granularity", "claims_check")
CSV_COLUMNS = ("provider", "probe_type", "t_write", "delay_s", "cache_read_tokens",
               "cache_creation_tokens", "latency_ms", "verdict", "cost_usd", "note")
CLAIM_NAMES = ("ttl_value", "refresh_on_hit", "write_premium", "min_cacheable")
DEFAULT_OUT = Path(__file__).resolve().parent / "results" / "dryrun.csv"


def make_tokens(rng: random.Random, n: int) -> list:
    return [rng.randrange(1, VOCAB) for _ in range(n)]


def iso(t: float) -> str:
    return datetime.fromtimestamp(t, tz=timezone.utc).isoformat()


def classify(read, baseline_latency_ms: float, billing_only: bool = False) -> str:
    """Verdict from billing fields AND latency delta (per M6 spec)."""
    billing_hit = read.cache_read_tokens > 0
    if billing_only:  # granularity partial hits give graded, not binary, latency
        return "hit" if billing_hit else "miss"
    latency_hit = read.latency_ms <= baseline_latency_ms * LATENCY_HIT_RATIO
    if billing_hit and latency_hit:
        return "hit"
    if not billing_hit and not latency_hit:
        return "miss"
    return "ambiguous"


def _row(probe_type: str, write, read, delay_s, verdict: str, note: str = "") -> dict:
    return {"provider": read.provider, "probe_type": probe_type,
            "t_write": iso(write.t_request), "delay_s": round(float(delay_s), 1),
            "cache_read_tokens": read.cache_read_tokens,
            "cache_creation_tokens": read.cache_creation_tokens,
            "latency_ms": round(read.latency_ms, 1), "verdict": verdict,
            "cost_usd": round(write.cost_usd + read.cost_usd, 8), "note": note}


def _probe_pair(adapter, rng, n_tokens: int, delay_s: float, probe_type: str,
                note: str = "", billing_only: bool = False):
    """One (write, delayed re-read) probe on a fresh unique random prefix."""
    prompt = make_tokens(rng, n_tokens)
    write = adapter.send(prompt)
    adapter.sleep(delay_s)
    read = adapter.send(prompt)
    verdict = classify(read, write.latency_ms, billing_only=billing_only)
    return _row(probe_type, write, read, delay_s, verdict, note), verdict


def run_ttl_curve(adapter, rng, grid=TTL_GRID_S) -> list:
    return [_probe_pair(adapter, rng, PREFIX_TOKENS, d, "ttl_curve")[0] for d in grid]


def run_granularity(adapter, rng, offsets=GRANULARITY_OFFSETS) -> list:
    """Prefix-match ladder: cache_read_tokens vs shared-prefix offset."""
    base_prompt = make_tokens(rng, PREFIX_TOKENS)
    write = adapter.send(base_prompt)
    rows = []
    for offset in offsets:
        variant = base_prompt[:offset] + make_tokens(
            rng, PREFIX_TOKENS - offset + SUFFIX_TOKENS)
        adapter.sleep(1)
        read = adapter.send(variant)
        verdict = classify(read, write.latency_ms, billing_only=True)
        rows.append(_row("granularity", write, read,
                         read.t_request - write.t_request, verdict,
                         note=f"offset={offset}"))
    return rows


def _claim_status(fixture: dict, claim: str, ok: bool) -> str:
    unverified = any(claim in item for item in fixture["_meta"].get("unverified", []))
    status = "pass" if ok else "FAIL"
    return f"{status} (doc UNVERIFIED)" if unverified else status


def run_claims_check(adapter, rng):
    """Replay the documented-claims checklist; returns (rows, summary)."""
    fx, cache, pricing = adapter.fixture, adapter.fixture["cache"], adapter.fixture["pricing"]
    ttl = cache["default_ttl_s"]
    bump = max(cache["granularity_tokens"], 64)
    rows, claims = [], {}

    r1, v1 = _probe_pair(adapter, rng, PREFIX_TOKENS, 0.5 * ttl, "claims_check",
                         f"claim=ttl_value:inside ttl={ttl}s")
    r2, v2 = _probe_pair(adapter, rng, PREFIX_TOKENS, 1.5 * ttl, "claims_check",
                         f"claim=ttl_value:past ttl={ttl}s")
    rows += [r1, r2]
    claims["ttl_value"] = _claim_status(fx, "ttl_value", v1 == "hit" and v2 == "miss")

    prompt = make_tokens(rng, PREFIX_TOKENS)  # refresh: hit at .6*TTL, re-read at 1.2*TTL total
    write = adapter.send(prompt)
    adapter.sleep(0.6 * ttl)
    mid = adapter.send(prompt)
    vm = classify(mid, write.latency_ms)
    rows.append(_row("claims_check", write, mid, 0.6 * ttl, vm, "claim=refresh_on_hit:first"))
    adapter.sleep(0.6 * ttl)
    late = adapter.send(prompt)
    vl = classify(late, write.latency_ms)
    rows.append(_row("claims_check", write, late, 1.2 * ttl, vl, "claim=refresh_on_hit:second"))
    ok = vm == "hit" and (vl == "hit") == bool(cache["refresh_on_hit"])
    claims["refresh_on_hit"] = _claim_status(fx, "refresh_on_hit", ok)

    fresh = make_tokens(rng, PREFIX_TOKENS)  # write premium implied by billing algebra
    w = adapter.send(fresh)
    out_cost = w.output_tokens * pricing["output_per_mtok"] / 1e6
    storage_cost = (w.cache_creation_tokens / 1e6
                    * pricing.get("storage_per_mtok_hr", 0.0) * (ttl / 3600.0))
    implied = ((w.cost_usd - out_cost - storage_cost)
               / (len(fresh) * pricing["input_per_mtok"] / 1e6))
    expected = (pricing.get("cache_write_per_mtok", {}).get(str(int(ttl)),
                pricing["input_per_mtok"]) / pricing["input_per_mtok"])
    premium_row = _row("claims_check", w, w, 0, "write",
                       f"claim=write_premium implied={implied:.3f}x expected={expected:.3f}x")
    rows.append({**premium_row, "cost_usd": round(w.cost_usd, 8)})  # single call, not a pair
    claims["write_premium"] = _claim_status(fx, "write_premium", abs(implied - expected) < 0.02)

    # billing-only verdicts here: at min+/-1-granularity prompt sizes the fixed
    # network latency swamps the token-proportional delta (e.g. DeepSeek disk
    # tier at 128 tokens), so billing fields are the discriminating signal.
    below_n = max(cache["min_cacheable_tokens"] - bump, 32)
    above_n = cache["min_cacheable_tokens"] + bump
    rb, vb = _probe_pair(adapter, rng, below_n, 5, "claims_check",
                         f"claim=min_cacheable:below n={below_n}", billing_only=True)
    ra, va = _probe_pair(adapter, rng, above_n, 5, "claims_check",
                         f"claim=min_cacheable:above n={above_n}", billing_only=True)
    rows += [rb, ra]
    claims["min_cacheable"] = _claim_status(fx, "min_cacheable", vb == "miss" and va == "hit")

    return rows, {"provider": adapter.name, "claims": claims,
                  "consistent": all(c.startswith("pass") for c in claims.values())}


def write_csv(path: Path, rows: list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def run_campaign(providers=PROVIDERS, probes=PROBE_TYPES, out_path: Path = DEFAULT_OUT,
                 seed: int = 20260706, live: bool = False):
    """Full campaign; returns (rows, claims_summaries). live=True raises in M6."""
    all_rows, summaries = [], []
    for provider in providers:
        adapter = make_adapter(provider, live=live)
        rng = random.Random(f"{seed}:{provider}")
        if "ttl_curve" in probes:
            all_rows += run_ttl_curve(adapter, rng)
        if "granularity" in probes:
            all_rows += run_granularity(adapter, rng)
        if "claims_check" in probes:
            rows, summary = run_claims_check(adapter, rng)
            all_rows += rows
            summaries.append(summary)
    write_csv(Path(out_path), all_rows)
    return all_rows, summaries


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--providers", default="all",
                    help="comma list or 'all' (%s)" % ",".join(PROVIDERS))
    ap.add_argument("--probes", default=",".join(PROBE_TYPES),
                    help="comma list of probe types")
    ap.add_argument("--out", default=str(DEFAULT_OUT), help="output CSV path")
    ap.add_argument("--seed", type=int, default=20260706)
    ap.add_argument("--live", action="store_true",
                    help="live API mode; refused in M6 (needs env keys + M7 transport)")
    args = ap.parse_args(argv)

    providers = PROVIDERS if args.providers == "all" else tuple(
        p.strip() for p in args.providers.split(",") if p.strip())
    probes = tuple(p.strip() for p in args.probes.split(",") if p.strip())
    for p in probes:
        if p not in PROBE_TYPES:
            ap.error(f"unknown probe type '{p}' (choose from {PROBE_TYPES})")

    mode = "LIVE" if args.live else "DRY-RUN (fixtures replay; zero API calls)"
    print(f"[cache-contract probe] mode={mode} providers={providers} probes={probes}")
    try:
        rows, summaries = run_campaign(providers, probes, Path(args.out),
                                       seed=args.seed, live=args.live)
    except NotImplementedError as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2
    print(f"wrote {len(rows)} rows -> {args.out}")
    for s in summaries:
        print("claims_check:", json.dumps(s))
    return 0


if __name__ == "__main__":
    sys.exit(main())
