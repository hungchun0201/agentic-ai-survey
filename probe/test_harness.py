"""Tests for the M6 dry-run probe harness. Run: python3 -m pytest test_harness.py -q"""
from __future__ import annotations

import csv
import random
import re
from pathlib import Path

import pytest

import cost_estimator
import harness
from adapters import ENV_KEYS, PROVIDERS, load_fixture, make_adapter

PROBE_DIR = Path(__file__).resolve().parent
SPEC_COLUMNS = ["provider", "probe_type", "t_write", "delay_s", "cache_read_tokens",
                "cache_creation_tokens", "latency_ms", "verdict", "cost_usd"]


@pytest.fixture(scope="module")
def campaign(tmp_path_factory):
    out = tmp_path_factory.mktemp("results") / "dryrun.csv"
    rows, summaries = harness.run_campaign(out_path=out)
    with open(out, newline="", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        header = next(reader)
        csv_rows = [dict(zip(header, r)) for r in reader]
    return {"out": out, "rows": rows, "summaries": summaries,
            "header": header, "csv_rows": csv_rows}


# ---------------- CSV schema ----------------

def test_csv_header_matches_spec(campaign):
    assert campaign["header"][:len(SPEC_COLUMNS)] == SPEC_COLUMNS
    assert campaign["header"][len(SPEC_COLUMNS):] == ["note"]  # single extra detail column


def test_csv_rows_schema_correct(campaign):
    assert len(campaign["csv_rows"]) > 0
    for row in campaign["csv_rows"]:
        assert row["provider"] in PROVIDERS
        assert row["probe_type"] in harness.PROBE_TYPES
        assert re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", row["t_write"])
        assert float(row["delay_s"]) >= 0
        assert int(row["cache_read_tokens"]) >= 0
        assert int(row["cache_creation_tokens"]) >= 0
        assert float(row["latency_ms"]) > 0
        assert row["verdict"] in ("hit", "miss", "ambiguous", "write")
        assert float(row["cost_usd"]) > 0


def test_dry_run_is_deterministic(tmp_path):
    out1, out2 = tmp_path / "a.csv", tmp_path / "b.csv"
    harness.run_campaign(out_path=out1)
    harness.run_campaign(out_path=out2)
    assert out1.read_bytes() == out2.read_bytes()


# ---------------- ttl_curve ----------------

def test_ttl_curve_grid_complete(campaign):
    for provider in PROVIDERS:
        delays = sorted(float(r["delay_s"]) for r in campaign["csv_rows"]
                        if r["provider"] == provider and r["probe_type"] == "ttl_curve")
        assert delays == sorted(float(d) for d in harness.TTL_GRID_S), provider


def test_ttl_verdicts_track_fixture_ttl(campaign):
    for provider in PROVIDERS:
        ttl = load_fixture(provider)["cache"]["default_ttl_s"]
        for row in campaign["csv_rows"]:
            if row["provider"] != provider or row["probe_type"] != "ttl_curve":
                continue
            expected = "hit" if float(row["delay_s"]) <= ttl else "miss"
            assert row["verdict"] == expected, (provider, row["delay_s"])


def test_ttl_verdict_consistent_with_billing(campaign):
    for row in campaign["csv_rows"]:
        if row["probe_type"] != "ttl_curve":
            continue
        billing_hit = int(row["cache_read_tokens"]) > 0
        assert (row["verdict"] == "hit") == billing_hit  # billing AND latency agree in dry-run


# ---------------- granularity ----------------

def _ladder(campaign, provider):
    steps = {}
    for row in campaign["csv_rows"]:
        if row["provider"] == provider and row["probe_type"] == "granularity":
            offset = int(row["note"].split("=")[1])
            steps[offset] = int(row["cache_read_tokens"])
    return steps


def test_granularity_openai_128_token_steps(campaign):
    steps = _ladder(campaign, "openai")
    assert set(steps) == set(harness.GRANULARITY_OFFSETS)
    for offset, hit_len in steps.items():
        assert hit_len == (offset if offset >= 1024 else 0)  # 128-tok grid, 1024 min


def test_granularity_anthropic_breakpoint_all_or_nothing(campaign):
    steps = _ladder(campaign, "anthropic")
    for offset, hit_len in steps.items():
        assert hit_len == (harness.PREFIX_TOKENS if offset == harness.PREFIX_TOKENS else 0)


def test_granularity_deepseek_64_token_chunks(campaign):
    steps = _ladder(campaign, "deepseek")
    for offset, hit_len in steps.items():
        assert hit_len == (offset // 64) * 64


# ---------------- claims_check ----------------

def test_claims_check_all_consistent_with_docs(campaign):
    assert len(campaign["summaries"]) == len(PROVIDERS)
    for summary in campaign["summaries"]:
        assert set(summary["claims"]) == set(harness.CLAIM_NAMES)
        assert summary["consistent"], summary  # fixtures replay their own documented claims


def test_anthropic_refresh_on_hit_semantics():
    adapter = make_adapter("anthropic")
    prompt = harness.make_tokens(random.Random(1), 2048)
    write = adapter.send(prompt)
    adapter.sleep(240)                      # inside 300 s TTL -> hit refreshes TTL
    mid = adapter.send(prompt)
    adapter.sleep(240)                      # 480 s after write, 240 s after refresh
    late = adapter.send(prompt)
    assert mid.cache_read_tokens == 2048 and late.cache_read_tokens == 2048
    assert write.cache_creation_tokens == 2048 and late.cache_creation_tokens == 0


# ---------------- cost estimator ----------------

def test_estimator_under_budget(capsys):
    est = cost_estimator.main()
    assert est["campaign_with_safety_usd"] <= cost_estimator.BUDGET_USD
    assert est["longitudinal_usd"] <= cost_estimator.BUDGET_USD
    for entry in est["per_provider"]:
        assert entry["total"] > 0
    out = capsys.readouterr().out
    assert "BUDGET CHECK: OK" in out


def test_estimator_grid_math_matches_harness():
    calls = cost_estimator.campaign_calls()
    assert calls["ttl_curve"] == len(harness.TTL_GRID_S) * cost_estimator.REPEATS * 2
    assert calls["granularity"] == (1 + len(harness.GRANULARITY_OFFSETS)) * cost_estimator.REPEATS
    assert calls["claims_check"] == cost_estimator.CLAIMS_CALLS * cost_estimator.REPEATS


# ---------------- live-mode double lock ----------------

@pytest.mark.parametrize("provider", PROVIDERS)
def test_live_mode_without_env_key_raises(provider, monkeypatch):
    monkeypatch.delenv(ENV_KEYS[provider], raising=False)
    with pytest.raises(NotImplementedError, match="--live flag AND"):
        make_adapter(provider, live=True)


@pytest.mark.parametrize("provider", PROVIDERS)
def test_live_mode_even_with_env_key_unimplemented_in_m6(provider, monkeypatch):
    monkeypatch.setenv(ENV_KEYS[provider], "sk-test-not-a-real-key")
    with pytest.raises(NotImplementedError, match="M7"):
        make_adapter(provider, live=True)


def test_cli_refuses_live_mode(monkeypatch, capsys):
    for key in ENV_KEYS.values():
        monkeypatch.delenv(key, raising=False)
    assert harness.main(["--live", "--providers", "anthropic"]) == 2
    assert "REFUSED" in capsys.readouterr().err


def test_dry_run_needs_no_env_keys(monkeypatch):
    for key in ENV_KEYS.values():
        monkeypatch.delenv(key, raising=False)
    usage = make_adapter("groq").send(harness.make_tokens(random.Random(2), 64))
    assert usage.cost_usd > 0


# ---------------- zero-live-HTTP guarantee ----------------

def test_no_http_client_imports_anywhere():
    forbidden = re.compile(
        r"^\s*(?:import|from)\s+(requests|httpx|aiohttp|urllib3|urllib\b|"
        r"http\b|socket|ssl)", re.MULTILINE)
    DRY_RUN_MODULES = {"harness.py", "adapters.py", "cost_estimator.py", "test_harness.py"}
    for py in sorted(p for p in PROBE_DIR.glob("*.py") if p.name in DRY_RUN_MODULES):  # M7 live_probe*.py intentionally uses urllib
        hits = forbidden.findall(py.read_text(encoding="utf-8"))
        assert not hits, f"{py.name} imports HTTP/network module(s): {hits}"
