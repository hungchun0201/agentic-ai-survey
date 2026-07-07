# P3: Online placement of K = 4 cache breakpoints (M5)

Companion code: `breakpoints.py` (stdlib-only; `--selftest` pins hand-enumerated toys).
Results: `breakpoints.txt`. Trace: SyFi coding trace, `provider == "claude"` rounds.

## 1. Formal statement

**Session.** A session is a sequence of rounds `t = 1..T`. At round `t` the client
submits its full context of length `n_t` tokens. Within an *append-only segment*,
`n_1 <= n_2 <= ... <= n_T` and every earlier context is a prefix of every later one.
The real trace has occasional compaction where `n_t < n_{t-1}`; we handle a drop by
starting a **fresh segment**: all cache entries die and no earlier position matches
again. Rounds are separated by wall-clock gaps `g_t = time(t) - time(t-1) >= 0`.

**Decisions.** At round `t` the client chooses a set `P_t` of at most `K = 4`
breakpoint positions. Positions are restricted to *round-boundary values*
`{n_1, ..., n_t}` (with 0 = no breakpoint), must satisfy `p <= n_t`, and may reuse
previous positions. Write `b_t = max(P_t)` (0 if `P_t` is empty).

**Aliveness (simplified TTL).** The provider's cache has TTL = 300 s, refreshed on
use. We adopt the one-step simplification: *an entry at position `p` is alive at
round `t` iff it was read or written at round `t-1` and `g_t <= 300 s`; otherwise it
is expired.* Read at round `t-1` means: `p` was the hit position `m_{t-1}`, or `p` was
a chosen position `<= m_{t-1}` (re-placing a breakpoint on cached content is a free
refresh). Written means `p` was chosen with `m_{t-1} < p <= b_{t-1}`. Hence the alive
set entering round `t` is `A_t = P_{t-1} ∪ {m_{t-1}}` if `g_t <= 300` (and the segment
did not break), else `A_t = ∅`.

**Billing.** Menu in units of the list input price per token: write `w = 1.25`,
read `r = 0.1`, uncached `1.0`. Let `m_t = max(A_t)` (0 if `A_t = ∅`) be the longest
previously-written, alive, matching breakpoint prefix. WLOG `b_t >= m_t` whenever
`A_t ≠ ∅` (raising `b_t` to `m_t` converts tokens billed at 1.0 into reads at `r`,
strictly cheaper and weakly better for the future; opting out entirely is likewise
dominated). Per-round cost:

    Cost_t = r * m_t + w * (b_t - m_t) + 1.0 * (n_t - b_t),

i.e., read the alive prefix, pay the write premium up to the top breakpoint, pay list
price for the uncached suffix. Objective: `min Σ_t Cost_t`.

**Information structure (online).** At round `t` the client knows `n_1..n_t`,
`g_1..g_t`, and its own past choices; it does not know `n_{t+1}..n_T`, future gaps,
or `T`. The clairvoyant offline optimum (DP below) knows everything.

## 2. Slot-collapse lemma: K = 1 is WLOG in-model

**Lemma 1.** In the model of Section 1, the optimal value from any state depends on
the alive set `A_t` only through `max(A_t)`; consequently there is an optimal policy
with `|P_t| <= 1` for every `t`, and the K = 4 slot budget is never binding.

*Proof sketch (backward induction).* `Cost_t` depends on `A_t` only through
`m_t = max(A_t)` (within a segment every alive position matches, so the longest match
is the maximum). The transition `A_{t+1} = P_t ∪ {m_t}` (or `∅`) gives
`max(A_{t+1}) = max(b_t, m_t) = b_t`, again a function of `(m_t, b_t)` alone, and the
survival condition `g_{t+1} <= TTL` is *uniform* across the alive set because every
alive entry shares the same last-touch round `t`. So the value function
`V_t(A) = V_t(max A)`, and choosing the singleton `P_t = {b_t}` achieves it. ∎

Numerical check: the faithful alive-set DP with `K' = 2` equals the reduced
single-slot DP to 0 tokens on 400 real sessions and on both toys (`breakpoints.txt`).

**What breaks the lemma in reality.** The collapse is an artifact of three
simplifications, which is exactly why Anthropic ships 4 slots:
(a) *partial-prefix survival under compaction* — real compaction keeps system prompt
+ tools + a summary, so a low breakpoint at the system-prompt boundary survives a
drop that kills the top one (we instead declare the whole segment dead);
(b) *cross-request sharing* — subagents/branches fork from a shared prefix, giving
non-nested read patterns over one entry set;
(c) *non-uniform refresh* — mixed TTLs (5 min vs 1 h beta) and refreshes by sibling
requests de-synchronize last-touch times, so a lower entry can outlive the top.
Under (a)–(c) lower slots are hedges and K binds. Grounding: the trace's actual bill
is 0.82x our model-OPT (`breakpoints.txt`), i.e., real entries survive events our
model kills — an upper bound (~18%) on what the fresh-segment abstraction forfeits.

## 3. Reduced offline DP (exact) and complexity

Per segment, state = (round `t`, top alive position `a`); actions
`b ∈ {a} ∪ {n_j : n_j ∈ (a, n_t], j <= t}`; transition `a' = b` if `g_{t+1} <= TTL`
else 0; stage cost as above. Exact by Lemma 1; `O(T)` states per round after
dominance pruning (`(a', c')` dominates `(a, c)` if `a' >= a`, `c' <= c`; `V_t` is
nonincreasing in `a` by a mimicking argument), `O(T)` actions: `O(T^3)` worst case,
seconds in practice for the whole corpus. A *bang-bang* restriction
`b ∈ {a, n_t}` (move fully or stay) is empirically lossless — max deviation 0 tokens
over all 1,675 sessions with `T <= 18` — and is used for the corpus-wide OPT; we do
not claim a proof that bang-bang is always exact (the value function would need to
be concave-free in the right way; plausible, unproven).

## 4. Relation to ski-rental and rental caching

This is **not ski-rental**, for structural reasons worth stating precisely:

1. **The purchase expires.** Writing a prefix is not a durable "buy": it must be
   re-touched within TTL or it evaporates. The per-token problem "pay 1.0/round rent,
   or pay a premium `w` once to rent at `r` while a validity window is maintained" is
   the **Bahncard problem** (Fleischer 2001: `(2 - β)`-competitive deterministic,
   `e/(e-1+β)` randomized, here `β = r = 0.1`), not classic ski-rental — with the
   twist that the validity window renews for free on every use and dies with a gap.
2. **Growth.** The item set grows: tokens arrive appended, and a write covers a
   *prefix interval*, coupling all tokens below the breakpoint. It is closer to
   rental/file-migration problems on a line than to independent ski instances.
3. **Multiple nested slots.** K slots with nested-prefix semantics form a chain
   (a rank-K constraint on which prefixes may stay warm). In-model this collapses
   (Lemma 1); under divergence (Sec. 2 a–c) it does not, and no clean reduction to a
   known rental problem is apparent to us.
4. **Degenerate price gap.** The write premium `w - 1 = 0.25` is *smaller than one
   round's read saving* `1 - r = 0.9`. So in the always-alive regime "buy
   immediately" is optimal and the online problem is trivial; all adversarial power
   sits in gap/termination uncertainty (will the next round come within TTL? is this
   the last round?). This is why always-top is near-optimal on real traces and why
   any interesting lower bound must be driven by gap adversaries, not length
   adversaries.

## 5. Open problem (honest framing)

**P3-K (open).** In the divergence-enabled model — the adversary may, at any round,
truncate the context to an arbitrary previously-written position (compaction that
retains a prefix), with the Section-1 menu and TTL — what is the optimal competitive
ratio of online breakpoint placement as a function of K, w, r, TTL?

What we can and cannot say:
- *Offline is easy*: the DP extends (state = alive chain restricted to surviving
  positions), polynomial for constant K.
- *K = 1, no divergence*: the problem is a Bahncard variant with reset (expiry on
  gap > TTL, free renewal on use). A gap adversary that straddles the TTL forces any
  deterministic policy to either waste writes or forfeit reads; we conjecture a
  constant deterministic lower bound `> 1` and a constant upper bound for a
  cadence/ski hybrid, both open here. We do **not** claim the `(2 - β)` Bahncard
  bound transfers: free renewal-on-use breaks the standard adversary.
- *K >= 2 with divergence*: the slots hedge across truncation depths; even the right
  lower-bound instance shape is unclear (adversary controls both gaps and truncation
  points). We leave this as the paper's stated open problem, with the empirical gap
  below as the only evidence that the achievable online loss is small on real
  workloads (which bounds the *empirical* price of online-ness, not the competitive
  ratio).

## 6. Empirical protocol and headline results

Trace reconstruction: per session, `n_t` = `input_tokens_total` sorted by
`round_index` (timestamp tiebreak), gaps from first `timing_events` timestamps
(negatives clamped to 0, missing = alive), drops start fresh segments.
Corpus: 2,676 sessions / 140,338 rounds / 3,218 segments; 4.6% of gaps > TTL.

Policies (all online, top-breakpoint only, per Lemma 1): **always-top** (`b_t = n_t`
every round — the SDK default shape); **cadence-c** (move only when `n_t - m_t >= c`,
`c ∈ {2k, 8k, 32k}`); **ski-informed** (rent until accumulated uncached spend since
the last move `>= w * (n_t - m_t)`, then move — the classic rent-to-buy trigger).

From `breakpoints.txt` (token-units, millions; ratio = policy / clairvoyant DP):

| policy | T<=18 subset (1,675 sess.) | full corpus (2,676 sess.) |
|---|---|---|
| dp-opt | 151.8 (1.000) | 5,143.5 (1.000) |
| always-top | 161.0 (1.061) | 5,215.9 (**1.014**) |
| cadence-2k | 164.3 (1.082) | 5,285.6 (1.028) |
| cadence-8k | 179.3 (1.181) | 5,573.5 (1.084) |
| cadence-32k | 274.7 (1.809) | 6,735.1 (1.309) |
| ski-informed | 197.0 (1.298) | 6,665.3 (1.296) |
| no-cache | 461.4 (3.040) | 28,466.2 (5.534) |

**Winner: always-top**, at 1.4% above clairvoyant OPT corpus-wide (6.1% on the
short-session subset, where the one wasted final-round write premium and pre-gap
writes weigh more; per-session p95 ratio 1.25 = the pure "last write wasted" case).
The ski trigger *underperforms* the naive default because with `w - 1 << 1 - r`
renting is almost never worth a single round of forfeited read discount — consistent
with Section 4, point 4. OPT's only edge over always-top is clairvoyance about
session end and > TTL gaps.
