"""Campaign cost estimator for the Cache Contract probe harness (M6).

Prints the expected $ per FULL live campaign per provider using the pricing in
fixtures/ (single source of truth) and asserts the total fits the $200 budget.
Deliberately WORST-CASE: every input token billed at the provider's most
expensive input rate (write premium), zero cache-read discounts, and Gemini
storage charged a full TTL-hour on every call. Real spend will be far lower
because re-reads hit the cache at the read rate.

Grid math (shown in the output):
  ttl_curve    len(TTL_GRID_S)=9 delays x REPEATS x 2 calls (write + read)
  granularity  (1 write + len(GRANULARITY_OFFSETS)=10 reads) x REPEATS
  claims_check CLAIMS_CALLS=12 calls x REPEATS
               (ttl_value 2x2 + refresh 1+2 + write_premium 1 + min_cacheable 2x2)
"""
from __future__ import annotations

from adapters import PROVIDERS, load_fixture
from harness import GRANULARITY_OFFSETS, PREFIX_TOKENS, SUFFIX_TOKENS, TTL_GRID_S

REPEATS = 3                 # live-campaign repeats per probe point (dry-run uses 1)
CLAIMS_CALLS = 12           # 4 (ttl_value) + 3 (refresh) + 1 (premium) + 4 (min_cacheable)
IN_TOKENS_PER_CALL = PREFIX_TOKENS + SUFFIX_TOKENS  # 2304: upper-bounds every probe prompt
OUT_TOKENS_PER_CALL = 8
SAFETY_FACTOR = 1.5
LONGITUDINAL_WEEKS = 12     # weekly re-run cadence (PROBE_PLAN.md)
BUDGET_USD = 200.0


def campaign_calls() -> dict:
    ttl_calls = len(TTL_GRID_S) * REPEATS * 2
    gran_calls = (1 + len(GRANULARITY_OFFSETS)) * REPEATS
    claims_calls = CLAIMS_CALLS * REPEATS
    return {"ttl_curve": ttl_calls, "granularity": gran_calls,
            "claims_check": claims_calls,
            "total": ttl_calls + gran_calls + claims_calls}


def estimate_provider(provider: str) -> dict:
    fixture = load_fixture(provider)
    pricing = fixture["pricing"]
    calls = campaign_calls()["total"]
    total_in = calls * IN_TOKENS_PER_CALL
    total_out = calls * OUT_TOKENS_PER_CALL
    worst_in_rate = max([pricing["input_per_mtok"]]
                        + list(pricing.get("cache_write_per_mtok", {}).values()))
    in_cost = total_in / 1e6 * worst_in_rate
    out_cost = total_out / 1e6 * pricing["output_per_mtok"]
    storage_rate = pricing.get("storage_per_mtok_hr", 0.0)
    ttl_hr = fixture["cache"]["default_ttl_s"] / 3600.0
    storage_cost = calls * IN_TOKENS_PER_CALL / 1e6 * storage_rate * ttl_hr
    return {"provider": provider, "calls": calls, "in_tokens": total_in,
            "out_tokens": total_out, "worst_in_rate": worst_in_rate,
            "in_cost": in_cost, "out_cost": out_cost, "storage_cost": storage_cost,
            "total": in_cost + out_cost + storage_cost}


def estimate_all() -> dict:
    per_provider = [estimate_provider(p) for p in PROVIDERS]
    campaign = sum(e["total"] for e in per_provider)
    with_safety = campaign * SAFETY_FACTOR
    longitudinal = with_safety * LONGITUDINAL_WEEKS
    return {"per_provider": per_provider, "campaign_usd": campaign,
            "campaign_with_safety_usd": with_safety,
            "longitudinal_usd": longitudinal, "budget_usd": BUDGET_USD}


def main() -> dict:
    calls = campaign_calls()
    print("CACHE CONTRACT PROBE CAMPAIGN - WORST-CASE COST ESTIMATE (prices from fixtures/)")
    print("\nGrid math, per provider, one full campaign:")
    print(f"  ttl_curve   : {len(TTL_GRID_S)} delays (30s..128min) x {REPEATS} repeats "
          f"x 2 calls (write+read) = {calls['ttl_curve']} calls")
    print(f"  granularity : (1 write + {len(GRANULARITY_OFFSETS)} offsets) x {REPEATS} "
          f"repeats = {calls['granularity']} calls")
    print(f"  claims_check: {CLAIMS_CALLS} calls x {REPEATS} repeats = "
          f"{calls['claims_check']} calls")
    print(f"  total       : {calls['total']} calls x ({IN_TOKENS_PER_CALL} in + "
          f"{OUT_TOKENS_PER_CALL} out) tokens = "
          f"{calls['total'] * IN_TOKENS_PER_CALL:,} in-tok, "
          f"{calls['total'] * OUT_TOKENS_PER_CALL:,} out-tok per provider")
    print("\nWorst-case pricing: all input at max(base, write premium); no read "
          "discounts; Gemini storage 1 full TTL-hour per call.")

    est = estimate_all()
    print(f"\n  {'provider':<10} {'calls':>6} {'in-tok':>9} {'worst-in $/MTok':>16} "
          f"{'in $':>8} {'out $':>7} {'storage $':>10} {'total $':>8}")
    for e in est["per_provider"]:
        print(f"  {e['provider']:<10} {e['calls']:>6} {e['in_tokens']:>9,} "
              f"{e['worst_in_rate']:>16.2f} {e['in_cost']:>8.3f} {e['out_cost']:>7.4f} "
              f"{e['storage_cost']:>10.3f} {e['total']:>8.3f}")

    print(f"\n  one full campaign, 5 providers ....... ${est['campaign_usd']:.2f}")
    print(f"  x{SAFETY_FACTOR} safety factor ................. "
          f"${est['campaign_with_safety_usd']:.2f}")
    print(f"  x{LONGITUDINAL_WEEKS} weekly longitudinal re-runs ..... "
          f"${est['longitudinal_usd']:.2f}")
    print(f"  budget ............................... ${est['budget_usd']:.2f}")

    assert est["campaign_with_safety_usd"] <= BUDGET_USD, (
        f"single campaign ${est['campaign_with_safety_usd']:.2f} exceeds "
        f"${BUDGET_USD} budget")
    assert est["longitudinal_usd"] <= BUDGET_USD, (
        f"{LONGITUDINAL_WEEKS}-week longitudinal program ${est['longitudinal_usd']:.2f} "
        f"exceeds ${BUDGET_USD} budget")
    print(f"\n  BUDGET CHECK: OK - full {LONGITUDINAL_WEEKS}-week longitudinal program "
          f"fits under ${BUDGET_USD:.0f}.")
    return est


if __name__ == "__main__":
    main()
