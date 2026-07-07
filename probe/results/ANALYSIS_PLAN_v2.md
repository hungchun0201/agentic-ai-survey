# Analysis plan — live probe campaign v2 (`live_v2_<ts>.csv`)

How the v2 CSV becomes paper figures/tables, and exactly which claim each arm
supports or refutes. Companion to `live_probe_v2.py` (see its docstring for
arm definitions). All analysis uses **API-reported** token counts and the
**actual** achieved delay, never the nominal schedule.

## 0. Hygiene rules (apply before any figure)

- Drop rows whose `note` contains `error:` (persistent HTTP failure) and
  their pair partner; report the count in the paper's appendix.
- For every `read` row, parse `d_act=<seconds>` from `note` and use it as the
  delay coordinate (scheduler jitter under load makes nominal `delay_s`
  approximate; `d_act` is ground truth measured write→read).
- Hit definition, uniform across providers: `cache_read > 0`.
  (Anthropic miss re-creates the entry: `cache_creation > 0, cache_read = 0`.
  OpenAI miss: `cached_tokens = 0`.)
- Arm relabels: if `openai-inmem` was rejected, its rows carry
  `arm=openai-default` (param omitted) — analyze under that label and say so.
  If `anthropic-1h` rows carry `1h_beta_header`, note the header requirement;
  if a `meta` row says `arm_rejected:anthropic-1h`, the arm is absent and the
  paper reports "1h TTL not purchasable on this account" as a finding.
- Independence: every (write, read) pair uses a unique deterministic prefix,
  so pairs are independent Bernoulli trials — Wilson CIs are valid.

## 1. Per-arm TTL survival curves with Wilson CIs (arm A — headline figure)

- Group `probe_type=ttl` read rows by (`arm`, nominal `delay_s`); n=6 each.
- For each cell compute hit count k, p̂=k/n, and the 95% Wilson interval:
  center=(p̂+z²/2n)/(1+z²/n), half-width=z·sqrt(p̂(1−p̂)/n+z²/4n²)/(1+z²/n),
  z=1.96. With n=6: 6/6 hits → [0.61, 1.0]; 0/6 → [0.0, 0.39].
- Figure: survival P(hit) vs delay (log-x), one curve per arm, CI whiskers,
  scatter of individual d_act values at y∈{0,1} underneath. Vertical dashed
  lines at 300 s / 3600 s / 86400 s (the *advertised* contracts).
- The 285/315 pair localizes the 5m cliff to a ±30 s window; 2400→3600→7200
  brackets the 1h arm; the 24h arm should be flat at 1.0 over the whole grid.
- Claims:
  - SUPPORTS "Anthropic 5m TTL is a sharp contract cliff at ~300 s" if
    285 s ≈ 1.0 and 315 s ≈ 0.0 with non-overlapping CIs.
  - REFUTES it (→ "TTL is soft/probabilistic") if intermediate hit rates
    appear (CIs spanning both) — equally publishable, changes the paper's
    eviction model from deterministic to stochastic.
  - SUPPORTS "paid retention (1h / 24h) actually extends survival" if those
    arms stay ≈1.0 past their cheaper sibling's cliff; refutes ("retention
    parameter is cosmetic") if their curves collapse onto the 5m/default one.
  - openai-inmem vs openai-24h separation measures what the free in-memory
    tier really holds vs the paid 24h tier.

## 2. Trace-vs-probe cliff overlay (links to the paper's passive evidence)

- Overlay figure 1's active survival curves with the passive trace-derived
  reuse-interval CDF (from the paper's existing trace analysis of agent
  workloads): x-axis shared (interval between successive uses of a prefix).
- Message: the mass of real agent reuse intervals that falls *beyond* each
  provider's measured cliff = the fraction of reuses the contract silently
  drops. This is the paper's "contract vs workload mismatch" figure; arm A
  supplies the vertical cliff positions with CIs, the trace supplies the CDF.

## 3. Tier-dependence table (arm B)

- Rows `probe_type=tier`: `anthropic-sonnet-5m` and `openai-4o-default`,
  delays {240, 360, 720}, n=3.
- Table: provider × model × delay → k/n hits (with Wilson CIs), side by side
  with the same three delays sliced out of arm A (haiku n=6, 4o-mini n=6).
- Test: Fisher's exact on 2×2 (haiku vs sonnet hits at each delay; 4o-mini
  vs 4o). With n=3 vs n=6 only gross differences are detectable — this is a
  spot check, phrased in the paper as "we found no evidence the contract
  differs by tier" (supports) or "the contract is tier-dependent" (refutes
  the implicit provider claim that caching behavior is model-uniform).

## 4. Min-cacheable claims table (arm C)

- `probe_type=bisect` rows + the `bisect_bracket:<provider>:lo=..:hi=..`
  meta row give the final bracket: threshold ∈ (lo, hi] in prefix-token
  target space; convert to measured tokens via the write rows'
  `input_tokens`/`cache_creation` (Anthropic) and `input_tokens` (OpenAI).
- Table: provider | documented minimum | measured bracket | verdict.
  - Anthropic haiku-4.5: docs say 4096; bracket should contain 4096.
  - OpenAI gpt-4o-mini: docs say 1024 (whole prompt incl. chat scaffolding);
    bracket should contain 1024 − (scaffold ≈ 8–20 tok) in prefix space.
- SUPPORTS "the min-cacheable clause is enforced as documented" if brackets
  contain the documented value; REFUTES (undocumented drift) otherwise —
  either way it is a measured row in the paper's "contract audit" table.

## 5. Granularity ladder (arm D)

- `probe_type=gran` read rows: divergence at ~{25,50,75,95}% (n=2) plus a
  100% control, per provider.
- Figure/table: x = divergence offset (fraction of the 4832-token prefix),
  y = `cache_read` tokens.
  - Expected Anthropic: all-or-nothing — 0 at every divergent offset, full
    (~4832) at 100% (cache keyed on the exact block up to the breakpoint).
  - Expected OpenAI: staircase ≈ floor(matched/128)·128, i.e., incremental
    longest-prefix matching (v1 already saw 4736 = 37×128 on a full match).
- Claims: quantifies the *unit of reuse* each contract sells — Anthropic
  sells exact-prefix blocks, OpenAI sells 128-token increments. SUPPORTS the
  paper's "granularity clause" section; refuted if Anthropic shows partial
  hits (would indicate undocumented sub-block matching) or OpenAI shows
  all-or-nothing.

## 6. Cost/robustness reporting

- Sum `est_cost_usd` (the final `campaign_total_est_cost` meta row) →
  reported experiment cost (worst-case pre-estimate: $3.82; soft cap $20,
  hard abort $40).
- Report retry/error counts from `note` as a data-quality footnote.
- Reproducibility: prefixes are deterministic in (csv basename, probe_id),
  so the exact byte-level stimuli can be regenerated from the CSV alone.
