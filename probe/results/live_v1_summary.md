# live_probe v1 (single-shot TTL curve) — 2026-07-06, cost $0.157
CSV: live_ttl_20260706_1152.csv (44 rows: 2 providers × 10 delays × write+read + 2 controls + smoke)
| delay s | anthropic haiku-4.5 (5m TTL) | openai gpt-4o-mini (default) |
|---|---|---|
| 30/60/120/240 | HIT ×4 | HIT ×4 |
| 360/480 | MISS ×2 | HIT ×2 |
| 720/960/1800/3600 | MISS ×4 | MISS ×4 |
Verdicts from billing fields (cache_read>0 / cached_tokens>0); miss rows show full re-creation.
→ Anthropic 5-min TTL enforced (cliff between 240–360s). OpenAI default retention minutes-scale
(cliff between 480–720s; "24h" applies to GPT-5-series default / opt-in param — param accepted
on 4o-mini in smoke). Single-shot (n=1/point): statistical campaign v2 (n=6, 285/315s straddle,
4 arms) launched 2026-07-06 ~12:53, ~2.16h.
