# NUMBERS_DELTA — corrections owed to §3 text (from measurement_v2.py, 2026-07-06)
Single source of truth: `analysis/measurement_v2.{py,txt}` (trace sha: syfi_coding_trace.jsonl.gz
53,601,226 B, 2026-07-05). Old ad-hoc numbers in contract.tex are NOT reproducible → replace.

| Claim site | Old text | Corrected | Note |
|---|---|---|---|
| corpus attribution | "140,338 rounds (43 developers)" | 140,338 Claude rounds, **37 developers** (full corpus 357,161 rounds / 43 devs incl. Codex) | 43 pairs only with 357K |
| read share | 95.8% token-weighted | keep; add **dev-cluster bootstrap 95% CI 94.1–97.1%** | per-round mean 94.1 / median 99.4 unchanged |
| retention **[SUPERSEDED by reversal row below]** | "re-creation ≈0 beyond 30min" | miss rate 0.00% in every gap bin; Wilson 95% upper ≤0.35% (10–20min, n=1086), ≤0.87% (>2h, n=437); ≤5min vs >5min diff 0.00pp | much stronger, CI-backed |
| dead holding @5min | "0.5% of holding cost" | **1.85% (as-deployed) / 4.62% (strict-TTL)** — define which in text | dual definition now explicit |
| dead holding @1h | "5.6% of all cache token-seconds" | **18.48% (as-deployed) / 25.40% (strict-TTL)** | strengthens one-bit case |
| dead absolute @1h | "~28,700 KV GB-hours" | **26,831 KV GB·h** (131,072 B/token) | same order, now reproducible |
| sessions | "546 sessions" (econ subset) | 2,676 Claude sessions total; 546 = sessions with >TTL gaps in econ analysis | label subset when cited |
| NEW robustness | — | excl. top-3 devs (59% tokens): 94.4%; session-length Q1→Q4: 74.1/84.8/91.7/96.0% | 1d |
| NEW longitudinal | — | weekly token-weighted share 81.7–97.5%, volume-weighted stable ≥94% from W10 | 1a weekly |
| ski-rental OOS | "1.07x out-of-sample" | **1.17±0.12 out-of-sample** (5-fold by developer); in-sample basin k=11–13 at 1.077–1.081x; k* scales ~(w−r)/r per menu (6 openai / 12 anthropic-5m / 25 anthropic-1h) | skirental_robust.txt |
| friction share of bill | — (new) | 344.9M = **8.2% of 4.21B input bill** | friction_rent.txt |
| rent share | 96% (345M vs 13M) | **95.9%** (344.9M spend vs 14.0M cost); sens. 94.5–97.4% | friction_rent.txt |
| OpenAI menu (2026-05-29+) | "90% discount, best-effort 5–10min" | default `prompt_cache_retention=24h` free (GPT-5.5: only mode; KV → GPU-local storage); friction 142.3M→0.7M (−99.5%) on our gaps | web-verified 2026-07-06; in-flight Thm B evidence |
| **RETENTION CLAIM REVERSED (R1 catch)** | "retention >> nominal TTL; re-creation 0.00% all bins" | TAUTOLOGY: prefix_tokens ≡ cache_read (137,401/137,401). Honest test vs E=input_total_{t-1}: ≤5min miss 0.4–2.7%; 5–10min 31.5%; >1h ~90% (z=74). **TTL cliff is real & enforced** | measurement_v2.txt [1b] |
| observed friction (new) | — | **891.8M = 21.2% of input bill** actually paid re-buying evicted state; rational-client replay 344.9M/8.2% = conservative floor | measurement_v2.txt [1e] |
| Thm A upgrade | grid check 9 points | identity ΔΠ=D_W−G_W (exact); exhaustive 8,358 prices; max ΔΠ=+0.02M at G≈0 frontier; G≥1%S → ≤−1.2M | theorem_maps.txt |
| Thm B $ bug | "$10–100/mo → 21–47% defect" | 21–47% was σ≈$0.30–3/mo. Honest: individual devs don't defect; team-level $334/mo observed ($129 optimal); platform amortization is the mechanism | theorem_maps.txt + text |
| dead-holding "as-deployed" label | as-deployed | relabeled "hold-through-gaps counterfactual" (provider does NOT hold through gaps per [1b]) | measurement_v2.txt [1c] |
