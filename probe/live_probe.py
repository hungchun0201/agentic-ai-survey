#!/usr/bin/env python3
"""M7 live prompt-cache TTL probe: Anthropic + OpenAI (stdlib only).

Usage:
    python3 live_probe.py --smoke    # synchronous smoke test (~70 s)
    python3 live_probe.py --curve    # full interleaved TTL curve (~61 min)

API keys are read from os.environ (ANTHROPIC_API_KEY / OPENAI_API_KEY) and
are never printed, logged, or written anywhere.
"""

import csv
import json
import os
import random
import sys
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(HERE, "results")
STATE_PATH = os.path.join(RESULTS_DIR, "smoke_status.json")

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
OPENAI_URL = "https://api.openai.com/v1/chat/completions"
ANTHROPIC_MODELS = ["claude-3-5-haiku-20241022", "claude-haiku-4-5-20251001"]
OPENAI_MODELS = ["gpt-4o-mini", "gpt-4.1-mini", "gpt-5-mini"]

# Haiku 4.5 requires >=4096 tokens in the cacheable prefix (shorter prefixes
# silently do not cache), so we use ~4800 words (~5k tokens) rather than the
# originally planned 2100. Still comfortably inside the $2 budget.
PREFIX_WORDS = 4800
DELAYS = [30, 60, 120, 240, 360, 480, 720, 960, 1800, 3600]
BUDGET_USD = 2.00
TIMEOUT_S = 60
WRITE_STAGGER_S = 1.3

VOCAB = (
    "time year people way day man thing woman life child world school state "
    "family student group country problem hand part place case week company "
    "system program question work government number night point home water "
    "room mother area money story fact month lot right study book eye job "
    "word business issue side kind head house service friend father power "
    "hour game line end member law car city community name president team "
    "minute idea body information back parent face others level office door "
    "health person art war history party result change morning reason "
    "research girl guy moment air teacher force education foot boy age "
    "policy process music market sense nation plan college interest death "
    "experience effect use class control care field development role effort "
    "rate heart drug show leader light voice wife whole police mind price "
    "report decision son view relationship town road arm difference value "
    "building action model season society tax director position player "
    "record paper space ground form event official matter center couple "
    "site project activity star table need court oil situation cost industry "
    "figure street image phone data picture practice piece land product "
    "doctor wall patient worker news test movie north love support technology"
).split()


class BudgetExceeded(RuntimeError):
    pass


class Budget:
    """Tracks cumulative estimated spend; hard-aborts past the limit."""

    def __init__(self, limit_usd):
        self.limit_usd = limit_usd
        self.total_usd = 0.0

    def add(self, cost_usd):
        self.total_usd += cost_usd
        if self.total_usd > self.limit_usd:
            raise BudgetExceeded(
                f"estimated spend ${self.total_usd:.4f} exceeds hard limit "
                f"${self.limit_usd:.2f}"
            )


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def make_prefix(n_words=PREFIX_WORDS):
    words = " ".join(random.choices(VOCAB, k=n_words))
    return f"probe-{uuid.uuid4()}\n{words}"


def http_post(url, headers, body):
    """Single POST. Returns (status, payload_dict, latency_ms)."""
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    t0 = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
            return resp.status, payload, (time.monotonic() - t0) * 1000.0
    except urllib.error.HTTPError as err:
        try:
            payload = json.loads(err.read().decode("utf-8"))
        except Exception:
            payload = {"error": {"message": "unparseable error body"}}
        return err.code, payload, (time.monotonic() - t0) * 1000.0


def post_with_retry(url, headers, body):
    """Retry 429/5xx/network up to 3x with 2/4/8 s backoff."""
    last = (0, {"error": {"message": "no attempt made"}}, 0.0)
    for attempt in range(4):  # 1 initial try + 3 retries
        if attempt:
            time.sleep(2 ** attempt)  # 2, 4, 8 seconds
        try:
            status, payload, latency = http_post(url, headers, body)
        except Exception as exc:  # URLError, socket timeout, etc.
            last = (0, {"error": {"message": f"network:{type(exc).__name__}"}}, 0.0)
            continue
        if status == 429 or status >= 500:
            last = (status, payload, latency)
            continue
        return status, payload, latency
    return last


def anthropic_headers():
    return {
        "x-api-key": os.environ["ANTHROPIC_API_KEY"],
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }


def openai_headers():
    return {
        "Authorization": "Bearer " + os.environ["OPENAI_API_KEY"],
        "content-type": "application/json",
    }


def anthropic_body(model, prefix):
    return {
        "model": model,
        "max_tokens": 1,
        "system": [
            {"type": "text", "text": prefix, "cache_control": {"type": "ephemeral"}}
        ],
        "messages": [{"role": "user", "content": "hi"}],
    }


_OPENAI_TOKEN_PARAM = {"name": "max_tokens"}  # swapped if a model rejects it


def openai_body(model, prefix, extra=None):
    body = {
        "model": model,
        _OPENAI_TOKEN_PARAM["name"]: 1,
        "messages": [
            {"role": "system", "content": prefix},
            {"role": "user", "content": "hi"},
        ],
    }
    return {**body, **(extra or {})}


def parse_anthropic(payload):
    usage = payload.get("usage") or {}
    creation = usage.get("cache_creation_input_tokens") or 0
    read = usage.get("cache_read_input_tokens") or 0
    inp = usage.get("input_tokens") or 0
    cost = (inp * 1.00 + creation * 1.25 + read * 0.10) / 1e6
    return creation, read, inp, cost, usage


def parse_openai(payload):
    usage = payload.get("usage") or {}
    prompt = usage.get("prompt_tokens") or 0
    details = usage.get("prompt_tokens_details") or {}
    cached = details.get("cached_tokens") or 0
    cost = ((prompt - cached) * 0.60 + cached * 0.30) / 1e6
    return 0, cached, prompt, cost, usage


def run_probe(provider, model, prefix, extra=None):
    """One live request. Returns a result dict; caller accounts the budget."""
    if provider == "anthropic":
        status, payload, latency = post_with_retry(
            ANTHROPIC_URL, anthropic_headers(), anthropic_body(model, prefix)
        )
        parse = parse_anthropic
    else:
        status, payload, latency = post_with_retry(
            OPENAI_URL, openai_headers(), openai_body(model, prefix, extra)
        )
        if status == 400 and "max_completion_tokens" in json.dumps(payload):
            _OPENAI_TOKEN_PARAM["name"] = "max_completion_tokens"
            status, payload, latency = post_with_retry(
                OPENAI_URL, openai_headers(), openai_body(model, prefix, extra)
            )
        parse = parse_openai
    if status != 200:
        msg = str((payload.get("error") or {}).get("message", payload))[:300]
        return {
            "ok": False, "status": status, "creation": 0, "read": 0, "input": 0,
            "latency_ms": round(latency, 1), "cost": 0.0, "usage": {},
            "note": f"error:{status}:{msg}",
        }
    creation, read, inp, cost, usage = parse(payload)
    return {
        "ok": True, "status": status, "creation": creation, "read": read,
        "input": inp, "latency_ms": round(latency, 1), "cost": cost,
        "usage": usage, "note": "",
    }


def resolve_model(provider, budget):
    """Try candidates with a tiny prompt until one is accepted."""
    candidates = ANTHROPIC_MODELS if provider == "anthropic" else OPENAI_MODELS
    for model in candidates:
        res = run_probe(provider, model, "model resolution ping")
        budget.add(res["cost"])
        if res["ok"]:
            return model
        print(f"[{provider}] model {model} rejected -> {res['note']}")
    return None


def smoke_provider(provider, model, budget):
    prefix = make_prefix()
    write = run_probe(provider, model, prefix)
    budget.add(write["cost"])
    print(f"[smoke {provider}] write usage: {json.dumps(write['usage'])}")
    if not write["ok"]:
        return False, f"write failed: {write['note']}"
    time.sleep(20)
    read = run_probe(provider, model, prefix)
    budget.add(read["cost"])
    print(f"[smoke {provider}] read  usage: {json.dumps(read['usage'])}")
    if not read["ok"]:
        return False, f"read failed: {read['note']}"
    if provider == "anthropic":
        if write["creation"] <= 0:
            return False, f"cache_creation=0 on write (usage={write['usage']})"
        if read["read"] <= 0:
            return False, f"cache_read=0 on re-read (usage={read['usage']})"
    elif read["read"] <= 0:
        return False, f"cached_tokens=0 on re-read (usage={read['usage']})"
    return True, "pass"


def retention_probe(model, budget):
    """One extra OpenAI pair testing prompt_cache_retention='24h'."""
    extra = {"prompt_cache_retention": "24h"}
    prefix = make_prefix()
    write = run_probe("openai", model, prefix, extra=extra)
    budget.add(write["cost"])
    if not write["ok"]:
        return {"accepted": False, "error": write["note"]}
    time.sleep(20)
    read = run_probe("openai", model, prefix, extra=extra)
    budget.add(read["cost"])
    return {
        "accepted": True, "error": "",
        "read_cached_tokens": read["read"], "read_note": read["note"],
    }


def cmd_smoke():
    budget = Budget(BUDGET_USD)
    os.makedirs(RESULTS_DIR, exist_ok=True)
    state = {"passed": {}, "models": {}, "retention_24h": None}
    for provider in ("anthropic", "openai"):
        key_var = "ANTHROPIC_API_KEY" if provider == "anthropic" else "OPENAI_API_KEY"
        if not os.environ.get(key_var):
            print(f"[smoke {provider}] {key_var} not set - excluded")
            state["passed"][provider] = False
            continue
        model = resolve_model(provider, budget)
        if model is None:
            print(f"[smoke {provider}] no accepted model - excluded")
            state["passed"][provider] = False
            continue
        print(f"[smoke {provider}] using model {model}")
        state["models"][provider] = model
        ok, detail = smoke_provider(provider, model, budget)
        state["passed"][provider] = ok
        print(f"[smoke {provider}] {'PASS' if ok else 'FAIL'}: {detail}")
    if state["passed"].get("openai"):
        state["retention_24h"] = retention_probe(state["models"]["openai"], budget)
        print(f"[smoke openai] prompt_cache_retention=24h -> "
              f"{json.dumps(state['retention_24h'])}")
    state["est_cost_usd_smoke"] = round(budget.total_usd, 6)
    with open(STATE_PATH, "w") as fh:
        json.dump(state, fh, indent=2)
    print(f"[smoke] est cost ${budget.total_usd:.4f}; state -> {STATE_PATH}")
    return 0 if any(state["passed"].values()) else 1


def build_timeline(providers):
    """One sorted timeline of (offset_s, provider, probe_type, event, id, delay)."""
    events = []
    idx = 0
    for delay in DELAYS:
        for provider in providers:
            w_off = idx * WRITE_STAGGER_S
            probe_id = f"{provider[:4]}-{delay}s"
            events.append((w_off, provider, "ttl", "write", probe_id, delay))
            events.append((w_off + delay, provider, "ttl", "read", probe_id, delay))
            idx += 1
    base = idx * WRITE_STAGGER_S + 5.0
    for j, provider in enumerate(providers):
        events.append((base + j * WRITE_STAGGER_S, provider, "control", "read",
                       f"{provider[:4]}-control", ""))
    return sorted(events, key=lambda e: e[0])


def cmd_curve():
    budget = Budget(BUDGET_USD)
    os.makedirs(RESULTS_DIR, exist_ok=True)
    try:
        with open(STATE_PATH) as fh:
            state = json.load(fh)
    except FileNotFoundError:
        print("[curve] no smoke state found; run --smoke first")
        return 1
    providers = [p for p in ("anthropic", "openai") if state["passed"].get(p)]
    if not providers:
        print("[curve] no provider passed smoke; nothing to do")
        return 1
    models = state["models"]
    csv_path = os.path.join(
        RESULTS_DIR, f"live_ttl_{time.strftime('%Y%m%d_%H%M')}.csv")
    events = build_timeline(providers)
    prefixes = {}
    print(f"[curve] providers={providers} models={models} "
          f"events={len(events)} csv={csv_path}")
    t0 = time.monotonic()
    with open(csv_path, "a", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["provider", "probe_type", "event", "probe_id", "delay_s",
                         "t_iso", "cache_creation", "cache_read", "input_tokens",
                         "latency_ms", "est_cost_usd", "note"])
        fh.flush()
        for offset, provider, ptype, ev, probe_id, delay in events:
            wait = t0 + offset - time.monotonic()
            if wait > 0:
                time.sleep(wait)
            if probe_id not in prefixes:
                prefixes[probe_id] = make_prefix()
            res = run_probe(provider, models[provider], prefixes[probe_id])
            note, aborted = res["note"], False
            try:
                budget.add(res["cost"])
            except BudgetExceeded as exc:
                note = (note + ";" if note else "") + f"abort_budget:{exc}"
                aborted = True
            writer.writerow([provider, ptype, ev, probe_id, delay, now_iso(),
                             res["creation"], res["read"], res["input"],
                             res["latency_ms"], f"{res['cost']:.6f}", note])
            fh.flush()
            print(f"[curve] {ev:5s} {probe_id:14s} status={res['status']} "
                  f"creation={res['creation']} read={res['read']} "
                  f"cum=${budget.total_usd:.4f}")
            if aborted:
                print(f"[curve] HARD ABORT at ${budget.total_usd:.4f}")
                return 2
        writer.writerow(["meta", "summary", "", "", "", now_iso(), "", "", "",
                         "", f"{budget.total_usd:.6f}", "campaign_total_est_cost"])
        fh.flush()
    print(f"[curve] done; est total ${budget.total_usd:.4f}; csv={csv_path}")
    return 0


def main(argv):
    if "--smoke" in argv:
        return cmd_smoke()
    if "--curve" in argv:
        return cmd_curve()
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
