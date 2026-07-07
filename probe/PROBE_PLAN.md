# Cache Contract — Cross-Provider Probe Campaign Plan (M6)

**Status: LIVE on Anthropic+OpenAI since 2026-07-06 (see §7 LIVE STATUS below); other providers remain dry-run fixtures until keys are granted.
Every adapter replays `fixtures/*.json` ("documented-behavior fixture; replaces
live wire until budget approved"). The moment API budget lands, the campaign
launches with the single command in §6 — nothing else needs to change except
the M7 `LiveTransport` wiring (§7).

Feeds paper claims C1 (contract constants table) and the measure half of the
V6 evidence object (docs-vs-wire gap). See `../DIRECTION.md`.

## 1. Probe types

| Probe | Question | Method | Verdict signal |
|---|---|---|---|
| `ttl_curve` | Does the entry actually live as long as the docs say? | Write a unique random ~2K-token prefix, re-read after delay d in {30 s, 1, 2, 4, 8, 16, 32, 64, 128 min} | billing (`cache_read > 0`) AND latency delta (read ≤ 0.75× same-size miss baseline) |
| `granularity` | At what token boundary do hits snap? | Prefix-match ladder: share the first k tokens (k ∈ {0, 256, 512, 768, 1024, 1152, 1280, 1536, 1792, 2048}), diverge after; read hit-prefix length off billing fields | billing-primary (partial hits give graded, not binary, latency) |
| `claims_check` | Do the four documented contract terms hold on the wire? | TTL value (probe at 0.5× and 1.5× documented TTL), refresh-on-hit (hit at 0.6×TTL, re-read at 1.2×TTL), write premium (implied multiplier from billing algebra), min cacheable length (min ± 1 granularity) | pass / FAIL per claim; `(doc UNVERIFIED)` tag where docs give no number |

## 2. Per-provider probe matrix

| Provider | Reference model | Cache type | Doc TTL | Refresh on hit | Write premium | Min tokens | Granularity | UNVERIFIED before live |
|---|---|---|---|---|---|---|---|---|
| anthropic | claude-sonnet-4 | explicit breakpoints | 5 min / 1 h | yes (free) | 1.25× / 2× | 1024 | exact prefix to breakpoint | — |
| openai | gpt-4o | automatic | 5–10 min best-effort | yes ("since last use") | none | 1024 | 128 tok | `prompt_cache_retention` param existence; TTL is a range not a value |
| gemini | gemini-2.5-flash | explicit `cachedContents` | settable, 1 h default | no | none (+$1.00/MTok·hr storage) | 1024 | all-or-nothing object | implicit-vs-explicit interaction |
| deepseek | deepseek-chat | automatic (disk) | undocumented (~hours–days) | undocumented | none (hit $0.07 vs miss $0.27/MTok) | 64 | 64 tok | TTL, refresh — the live curve IS the result |
| groq | llama-3.3-70b | automatic | undocumented | undocumented | none (50% cached discount) | 1024? | 128? | TTL, min, granularity, usage field name, rate-limit-exemption scope |

Groq extra (live-only): the rate-limit exemption cannot be seen in billing
fields — log `x-ratelimit-remaining-tokens` headers around cached vs uncached
requests during the live run (M7 note; not modeled in dry-run).

## 3. Expected token & $ spend (re-derive any time: `python3 cost_estimator.py`)

Per provider per campaign: 9×3×2 + 11×3 + 12×3 = **123 calls ≈ 283K input tokens**
(~2.3K tokens/call, 8 output tokens/call — minimal-consumption by design).
Worst-case (all input at write-premium rate, zero cache discounts, Gemini
storage a full TTL-hour every call):

anthropic $1.72 · openai $0.72 · gemini $0.37 · deepseek $0.08 · groq $0.17
= **$3.05 per full 5-provider campaign**; ×1.5 safety = **$4.57**;
×12 weekly re-runs = **$54.90 ≪ $200 budget** (asserted in `cost_estimator.py`
and `test_harness.py`). Real spend will be lower — re-reads that hit are billed
at read rates.

## 4. Longitudinal cadence

- **Weekly re-run** of the full campaign for 12 weeks (contracts are
  changeable-without-notice; the longitudinal series is the evidence that the
  measured constants are stable — or a dated record of when they moved).
- One CSV per run: `results/campaign_YYYY-MM-DD.csv`; never overwrite.
- Off-peak AND on-peak pair for openai (docs say retention stretches to ~1 h
  off-peak): run the weekly campaign at a fixed hour, plus one monthly
  off-peak (03:00 US-Pacific) replicate.
- Drift alarm: diff each week's `claims_check` summary against the fixture;
  any `FAIL` = provider changed the contract → snapshot docs page same day.

## 5. ToS / ethics notes

- **Documented-behavior probing only**: every probe verifies a claim the
  provider itself publishes (TTL, price multiplier, min length, granularity).
  No exploitation, no attempt to infer other tenants' data — all prefixes are
  our own fresh cryptographically-random token strings, so a cache hit can
  only ever be against our own prior request.
- **Minimal consumption**: ~2–8K tokens per probe pair, 8-token max outputs,
  123 calls/provider/week — orders of magnitude below normal application
  traffic; no load testing, no concurrency.
- **Rate-limit compliance**: ≥1 s spacing between calls; on any 429/`Retry-After`,
  back off exponentially and never retry more than 3× (M7 transport
  requirement); Groq header logging is passive observation only.
- **Account hygiene**: paid accounts in our own name, no free-tier arbitrage,
  spend caps set provider-side at $50/account.
- **Responsible disclosure**: if a probe reveals a discrepancy that looks like
  a billing bug (e.g., charged write premium without retention) rather than a
  documented-behavior gap, report to the provider before publication;
  published tables report measured values with timestamps, not provider-blame
  framing.

## 6. Launch command (the moment budget lands)

```bash
cd /home/hclin/PhD_Research/inference_improvement/paper-cachecontract/probe
ANTHROPIC_API_KEY=... OPENAI_API_KEY=... GEMINI_API_KEY=... \
DEEPSEEK_API_KEY=... GROQ_API_KEY=... \
python3 harness.py --live --providers all \
  --probes ttl_curve,granularity,claims_check \
  --out results/campaign_$(date +%F).csv
```

Today this command **refuses with `NotImplementedError` by design** (double
lock: `--live` flag AND env key AND M7 transport). Weekly cron: same command,
Monday 09:00.

## 7. M7 wiring checklist (small diff, adapters already shaped)

1. Implement `LiveTransport` in `adapters.py` (stdlib `urllib` or add
   `httpx` — the no-HTTP-import test then moves to guarding `DryRunTransport`
   only): real `sleep()`, per-provider POST, return the same sim-dict keys.
2. The per-provider usage-field parsing is already written and tested —
   `_shape_raw` mirrors each provider's real response shape
   (`cache_read_input_tokens`, `prompt_tokens_details.cached_tokens`,
   `cachedContentTokenCount`, `prompt_cache_hit_tokens`, ...); point
   `_billing_fields` at live responses.
3. Re-verify every fixture line tagged UNVERIFIED against current docs;
   snapshot the docs pages (archive.org) the same day.
4. Latency baseline: replace the fixture latency model with 5 warm-up miss
   calls per provider; keep the 0.75 ratio, report ambiguous verdicts as-is.
5. Add Groq rate-limit header logging (§2).

## §7 LIVE STATUS (updated 2026-07-06)
M7 live campaign STARTED (Anthropic + OpenAI keys granted; Gemini/DeepSeek/Groq pending).
- `live_probe.py` (v1): smoke PASS both providers; single-shot TTL curve ran 2026-07-06
  (results/live_ttl_20260706_1152.csv). Findings: anthropic haiku-4.5 min-cacheable 4096 tok;
  `prompt_cache_retention:"24h"` accepted on gpt-4o-mini; anthropic 5-min cliff live-confirmed
  (hits ≤240s, misses ≥360s); openai gpt-4o-mini DEFAULT retention minutes-scale (hit 480s,
  miss ≥720s) — "24h default" applies to GPT-5-series only.
- `live_probe_v2.py`: statistical campaign (n=6 reps × 12 delays × 4 contract arms + tier
  spot-checks + min-cacheable bisect + granularity ladder; 656 events, ~$3.82 worst-case,
  ~2.16h; selftest 100 assertions PASS). Analysis mapping: results/ANALYSIS_PLAN_v2.md.
- The M6 dry-run harness (harness.py/adapters.py) remains fixture-only (no HTTP imports,
  enforced by test_harness.py scoped scan); live HTTP lives exclusively in live_probe*.py.
