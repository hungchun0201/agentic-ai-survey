"""Provider adapters + transports for the Cache Contract probe harness (M6).

DRY-RUN ONLY. No network code exists in this module or anywhere under probe/.
Every provider adapter shares one interface::

    adapter.send(prompt_tokens, cache_controls) -> UsageRecord

and delegates wire behavior to a Transport. The only transport implemented in
M6 is DryRunTransport, which replays the documented-behavior fixtures in
fixtures/ (each fixture is marked "documented-behavior ... until budget
approved"). Live mode raises NotImplementedError by design: it requires BOTH
the --live flag and the provider env key, and even then the live wire is
deferred to M7 (see PROBE_PLAN.md).
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, replace
from pathlib import Path

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
PROVIDERS = ("anthropic", "openai", "gemini", "deepseek", "groq")
ENV_KEYS = {
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
    "groq": "GROQ_API_KEY",
}
# Fixed virtual epoch (2026-01-01T00:00:00Z): the dry-run clock never touches
# wall time, so campaigns are byte-for-byte reproducible.
VIRTUAL_EPOCH = 1_767_225_600.0
DEFAULT_OUTPUT_TOKENS = 8


def load_fixture(provider: str) -> dict:
    path = FIXTURES_DIR / f"{provider}.json"
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"cannot load fixture for '{provider}' at {path}: {exc}") from exc


@dataclass(frozen=True)
class UsageRecord:
    """Normalized per-request billing/latency record (the adapter contract)."""
    provider: str
    t_request: float            # virtual epoch seconds
    input_tokens: int           # uncached input billed at base rate
    cache_read_tokens: int      # as reported by provider billing fields
    cache_creation_tokens: int  # 0 for providers that do not report it
    output_tokens: int
    latency_ms: float
    cost_usd: float
    raw: dict = field(default_factory=dict)


@dataclass(frozen=True)
class CacheEntry:
    tokens: tuple
    created: float
    last_used: float
    ttl_s: float


def _lcp(a: tuple, b: tuple) -> int:
    n = min(len(a), len(b))
    for i in range(n):
        if a[i] != b[i]:
            return i
    return n


def _cost_usd(pricing: dict, base_billed: int, creation: int, cached: int,
              output_tokens: int, ttl_s: float) -> float:
    write_price = pricing.get("cache_write_per_mtok", {}).get(
        str(int(ttl_s)), pricing["input_per_mtok"])
    cost = (base_billed * pricing["input_per_mtok"]
            + creation * write_price
            + cached * pricing["cache_read_per_mtok"]
            + output_tokens * pricing["output_per_mtok"]) / 1e6
    storage = pricing.get("storage_per_mtok_hr", 0.0)
    if storage and creation:
        cost += (creation / 1e6) * storage * (ttl_s / 3600.0)
    return cost


def _latency_ms(model: dict, uncached_tokens: int, cached_tokens: int) -> float:
    return (model["base_ms"]
            + uncached_tokens / 1000.0 * model["per_1k_uncached_ms"]
            + cached_tokens / 1000.0 * model["per_1k_cached_ms"])


class DryRunTransport:
    """Replays documented provider cache behavior from a fixture. Zero network.

    Keeps a virtual clock (sleep() advances it instantly) and a tuple of
    immutable CacheEntry records simulating the provider-side prefix cache.
    """
    live = False

    def __init__(self, fixture: dict, t0: float = VIRTUAL_EPOCH):
        self.fixture = fixture
        self.now = float(t0)
        self.entries: tuple = ()

    def sleep(self, seconds: float) -> None:
        self.now += float(seconds)

    def _match(self, prompt: tuple):
        cache = self.fixture["cache"]
        best_len, best_entry = 0, None
        for entry in self.entries:
            if self.now - entry.last_used > entry.ttl_s:
                continue  # expired
            if cache["match_mode"] == "breakpoint":
                n = len(entry.tokens)
                matched = n if (len(prompt) >= n and prompt[:n] == entry.tokens) else 0
            else:  # incremental: longest common prefix, quantized down
                g = cache["granularity_tokens"]
                matched = (_lcp(prompt, entry.tokens) // g) * g
            if matched >= cache["min_cacheable_tokens"] and matched > best_len:
                best_len, best_entry = matched, entry
        return best_len, best_entry

    def complete(self, prompt_tokens, cache_controls: dict) -> dict:
        cache = self.fixture["cache"]
        prompt = tuple(prompt_tokens)
        cached, hit_entry = self._match(prompt)
        if hit_entry is not None and cache["refresh_on_hit"]:
            self.entries = tuple(
                replace(e, last_used=self.now) if e is hit_entry else e
                for e in self.entries)
        wants_write = cache_controls.get("cache_write", cache["auto_cache"])
        ttl_s = float(cache_controls.get("ttl_s", cache["default_ttl_s"]))
        creation = 0
        if wants_write and len(prompt) >= cache["min_cacheable_tokens"] and cached < len(prompt):
            creation = len(prompt) - cached
            self.entries = self.entries + (
                CacheEntry(tokens=prompt, created=self.now, last_used=self.now, ttl_s=ttl_s),)
        base_billed = len(prompt) - cached - creation
        output_tokens = int(cache_controls.get("max_output_tokens", DEFAULT_OUTPUT_TOKENS))
        cost = _cost_usd(self.fixture["pricing"], base_billed, creation, cached,
                         output_tokens, ttl_s)
        latency_ms = _latency_ms(self.fixture["latency_model"],
                                 base_billed + creation, cached)
        t_request = self.now
        self.sleep(latency_ms / 1000.0)  # request itself takes (virtual) time
        return {"t_request": t_request, "cached": cached, "creation": creation,
                "base_billed": base_billed, "output_tokens": output_tokens,
                "latency_ms": latency_ms, "cost_usd": cost, "ttl_s": ttl_s}


def build_transport(provider: str, fixture: dict, live: bool = False):
    """M6 policy gate: dry-run always works; live is double-locked."""
    if not live:
        return DryRunTransport(fixture)
    env_key = ENV_KEYS[provider]
    if not os.environ.get(env_key):
        raise NotImplementedError(
            f"live mode for '{provider}' requires BOTH the explicit --live flag AND "
            f"{env_key} in the environment; refusing (M6 is dry-run only, zero API calls)")
    raise NotImplementedError(
        f"LiveTransport for '{provider}' is intentionally unimplemented in M6 "
        "(zero live API calls until budget approval); wire it in M7 per PROBE_PLAN.md")


class ProviderAdapter:
    """Common interface: send(prompt_tokens, cache_controls) -> UsageRecord."""
    name = "base"

    def __init__(self, fixture: dict | None = None, transport=None, live: bool = False):
        self.fixture = fixture if fixture is not None else load_fixture(self.name)
        self.transport = (transport if transport is not None
                          else build_transport(self.name, self.fixture, live=live))

    @property
    def now(self) -> float:
        return self.transport.now

    def sleep(self, seconds: float) -> None:
        self.transport.sleep(seconds)

    def default_controls(self) -> dict:
        return {}

    def send(self, prompt_tokens, cache_controls: dict | None = None) -> UsageRecord:
        controls = {**self.default_controls(), **(cache_controls or {})}
        sim = self.transport.complete(prompt_tokens, controls)
        raw = self._shape_raw(sim)
        read_tok, creation_tok = self._billing_fields(raw)
        return UsageRecord(
            provider=self.name, t_request=sim["t_request"],
            input_tokens=sim["base_billed"], cache_read_tokens=read_tok,
            cache_creation_tokens=creation_tok, output_tokens=sim["output_tokens"],
            latency_ms=sim["latency_ms"], cost_usd=sim["cost_usd"], raw=raw)

    def _shape_raw(self, sim: dict) -> dict:
        raise NotImplementedError

    def _billing_fields(self, raw: dict) -> tuple:
        raise NotImplementedError


class AnthropicAdapter(ProviderAdapter):
    name = "anthropic"

    def default_controls(self) -> dict:  # explicit cache_control breakpoint on full prefix
        return {"cache_write": True, "ttl_s": self.fixture["cache"]["default_ttl_s"]}

    def _shape_raw(self, sim: dict) -> dict:
        return {"usage": {"input_tokens": sim["base_billed"],
                          "cache_read_input_tokens": sim["cached"],
                          "cache_creation_input_tokens": sim["creation"],
                          "output_tokens": sim["output_tokens"]}}

    def _billing_fields(self, raw: dict) -> tuple:
        u = raw["usage"]
        return u["cache_read_input_tokens"], u["cache_creation_input_tokens"]


class OpenAIAdapter(ProviderAdapter):
    name = "openai"  # automatic caching; no creation field in usage

    def _shape_raw(self, sim: dict) -> dict:
        total = sim["base_billed"] + sim["creation"] + sim["cached"]
        return {"usage": {"prompt_tokens": total,
                          "completion_tokens": sim["output_tokens"],
                          "prompt_tokens_details": {"cached_tokens": sim["cached"]}}}

    def _billing_fields(self, raw: dict) -> tuple:
        return raw["usage"]["prompt_tokens_details"]["cached_tokens"], 0


class GeminiAdapter(ProviderAdapter):
    name = "gemini"  # explicit cachedContents object with settable TTL

    def default_controls(self) -> dict:
        return {"cache_write": True, "ttl_s": self.fixture["cache"]["default_ttl_s"]}

    def _shape_raw(self, sim: dict) -> dict:
        total = sim["base_billed"] + sim["creation"] + sim["cached"]
        return {"usageMetadata": {"promptTokenCount": total,
                                  "cachedContentTokenCount": sim["cached"],
                                  "candidatesTokenCount": sim["output_tokens"]},
                "cachedContents_create": {"usageMetadata": {"totalTokenCount": sim["creation"]}}}

    def _billing_fields(self, raw: dict) -> tuple:
        return (raw["usageMetadata"]["cachedContentTokenCount"],
                raw["cachedContents_create"]["usageMetadata"]["totalTokenCount"])


class DeepSeekAdapter(ProviderAdapter):
    name = "deepseek"  # automatic disk cache; hit/miss token split in usage

    def _shape_raw(self, sim: dict) -> dict:
        return {"usage": {"prompt_cache_hit_tokens": sim["cached"],
                          "prompt_cache_miss_tokens": sim["base_billed"] + sim["creation"],
                          "completion_tokens": sim["output_tokens"]}}

    def _billing_fields(self, raw: dict) -> tuple:
        return raw["usage"]["prompt_cache_hit_tokens"], 0


class GroqAdapter(ProviderAdapter):
    name = "groq"  # OpenAI-compatible; cached-token field name UNVERIFIED (see fixture)

    def _shape_raw(self, sim: dict) -> dict:
        total = sim["base_billed"] + sim["creation"] + sim["cached"]
        return {"usage": {"prompt_tokens": total,
                          "completion_tokens": sim["output_tokens"],
                          "prompt_tokens_details": {"cached_tokens": sim["cached"]}}}

    def _billing_fields(self, raw: dict) -> tuple:
        return raw["usage"]["prompt_tokens_details"]["cached_tokens"], 0


ADAPTER_CLASSES = {cls.name: cls for cls in
                   (AnthropicAdapter, OpenAIAdapter, GeminiAdapter,
                    DeepSeekAdapter, GroqAdapter)}


def make_adapter(provider: str, live: bool = False) -> ProviderAdapter:
    if provider not in ADAPTER_CLASSES:
        raise ValueError(f"unknown provider '{provider}'; choose from {PROVIDERS}")
    return ADAPTER_CLASSES[provider](live=live)
