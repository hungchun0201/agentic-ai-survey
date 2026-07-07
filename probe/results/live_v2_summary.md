# live_probe v2 (statistical campaign) — 2026-07-06, 664 rows, $2.82 total
n=6 per (arm, delay); Wilson-CI-ready. CSV: live_v2_20260706_1252.csv
| arm | survival by delay |
|---|---|
| anthropic-5m | 6/6 through **285s**; 0/6 from **315s** — cliff exactly at the 300s contract |
| anthropic-1h | 6/6 through 3600s; 0/6 at 7200s — 1h tier exact |
| openai-inmem (4o-mini) | 6/6 ≤360s; 3/6 @480s; 0/6 ≥720s — soft ~6–8min window |
| openai-24h (4o-mini) | 6/6 ≤120s; 5/6 240–360s; 4/6 @480s; 0/6 ≥720s — **param ACCEPTED but INERT** (≈ in_memory) |
Tier spot-checks (n=3): anthropic sonnet ≡ haiku (miss ≥360s); **gpt-4o default HIT @720s** where
4o-mini misses — retention is model-dependent within one provider.
Granularity: anthropic ALL-OR-NOTHING (any divergence → read=0); openai PREFIX-LADDER
(read = 1024/2176/3072/4224 tokens at 25/50/75/95% divergence).
Min-cacheable bisect: anthropic (4058,4118] ∋ 4096 (docs✓); openai (1016,1040] ∋ 1024 (docs✓).
