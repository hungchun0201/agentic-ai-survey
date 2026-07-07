#!/usr/bin/env python3
"""Cache Contract live-probe campaign v2 (statistical). Stdlib only.

One interleaved timeline with four arms:
  A. TTL survival curves with repeats (Wilson-CI-ready):
     4 arms x 12 delays x n=6 independent (write,read) pairs.
     - anthropic-5m      cache_control {"type":"ephemeral"}          (haiku-4.5)
     - anthropic-1h      cache_control {"type":"ephemeral","ttl":"1h"} (verify;
                         falls back to beta header, else arm dropped)
     - openai-24h        prompt_cache_retention="24h"                (gpt-4o-mini)
     - openai-inmem      prompt_cache_retention="in_memory" (falls back to
                         omitting the param, relabelled openai-default)
  B. Model-tier spot check: sonnet-4.5 (5m TTL) and gpt-4o (default),
     delays [240,360,720] x n=3.
  C. Min-cacheable bisect: haiku 1024..4832, gpt-4o-mini 512..2048
     (6 adaptive pairs each, write then read 15 s later).
  D. Granularity ladder: one cached 4832-token prefix per provider, reads
     diverging at ~{25,50,75,95}% (n=2) plus a 100% control read.

Usage:
    python3 live_probe_v2.py --selftest              # no HTTP, fake transport
    python3 live_probe_v2.py --run                   # live campaign (~2.2 h)
    python3 live_probe_v2.py --run --resume results/live_v2_<ts>.csv

Detached launch (after v1 curve finishes):
    cd /home/hclin/PhD_Research/inference_improvement/paper-cachecontract/probe && \
      source ~/.keys/cachecontract_probe.env && \
      nohup python3 live_probe_v2.py --run > results/live_v2.log 2>&1 &

API keys are read from os.environ (ANTHROPIC_API_KEY / OPENAI_API_KEY) and are
never printed, logged, or written anywhere.
"""

import csv
import hashlib
import json
import os
import random
import sys
import threading
import time
import urllib.error
import urllib.request
from collections import Counter
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(HERE, "results")

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
OPENAI_URL = "https://api.openai.com/v1/chat/completions"
ANTHROPIC_1H_BETA = "extended-cache-ttl-2025-04-11"

MODEL_CANDIDATES = {
    "haiku": ["claude-haiku-4-5-20251001"],
    "sonnet": ["claude-sonnet-4-5", "claude-sonnet-4-5-20250929"],
    "4o-mini": ["gpt-4o-mini"],
    "4o": ["gpt-4o"],
}
MODEL_PROVIDER = {"haiku": "anthropic", "sonnet": "anthropic",
                  "4o-mini": "openai", "4o": "openai"}
PRICE_IN = {"haiku": 1.00, "sonnet": 3.00, "4o-mini": 0.60, "4o": 2.50}  # $/MTok

DELAYS_A = [30, 120, 240, 285, 315, 360, 480, 720, 1200, 2400, 3600, 7200]
REPS_A = 6
DELAYS_B = [240, 360, 720]
REPS_B = 3
PREFIX_TOKENS = 4832        # >= anthropic haiku-4.5 min-cacheable (4096)
TAG_TOKENS = 10             # est tokens of the "probe-<hex12>" tag line
BISECT = {"anthropic": {"model_key": "haiku", "lo": 1024, "hi": 4832},
          "openai": {"model_key": "4o-mini", "lo": 512, "hi": 2048}}
BISECT_PAIRS = 6
BISECT_READ_DELAY = 15.0
GRAN_OFFSETS_PCT = [25, 50, 75, 95]
GRAN_REPS = 2
WRITE_STAGGER_S = 2.0       # requirement: >= 1.3 s
SOFT_BUDGET_USD = 20.0
HARD_BUDGET_USD = 40.0
TIMEOUT_S = 60
GATE_TIMEOUT_S = 90

ARMS_A = [  # (arm_key, provider, model_key) -- provider-alternating order
    ("anthropic-5m", "anthropic", "haiku"),
    ("openai-24h", "openai", "4o-mini"),
    ("anthropic-1h", "anthropic", "haiku"),
    ("openai-inmem", "openai", "4o-mini"),
]
ARMS_B = [
    ("anthropic-sonnet-5m", "anthropic", "sonnet"),
    ("openai-4o-default", "openai", "4o"),
]

COLUMNS = ["provider", "arm", "probe_type", "event", "probe_id", "rep",
           "delay_s", "prefix_tokens_target", "t_iso", "cache_creation",
           "cache_read", "input_tokens", "latency_ms", "est_cost_usd", "note"]

EXPECTED_ARM_EVENTS = {
    "anthropic-5m": 144, "anthropic-1h": 144,
    "openai-24h": 144, "openai-inmem": 144,
    "anthropic-sonnet-5m": 18, "openai-4o-default": 18,
    "anthropic-bisect": 12, "openai-bisect": 12,
    "anthropic-gran": 10, "openai-gran": 10,
}

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
    """Thread-safe cumulative estimated spend with soft warn / hard abort."""

    def __init__(self, soft_usd, hard_usd, preload=0.0):
        self.soft_usd, self.hard_usd = soft_usd, hard_usd
        self.total_usd = preload
        self.soft_warned = False
        self._lock = threading.Lock()

    def add(self, cost_usd):
        with self._lock:
            self.total_usd += cost_usd
            if self.total_usd > self.soft_usd and not self.soft_warned:
                self.soft_warned = True
                print(f"[budget] SOFT WARN: est spend ${self.total_usd:.4f} "
                      f"> ${self.soft_usd:.2f}", flush=True)
            if self.total_usd > self.hard_usd:
                raise BudgetExceeded(
                    f"est spend ${self.total_usd:.4f} exceeds hard limit "
                    f"${self.hard_usd:.2f}")


class RealClock:
    def now(self):
        return time.time()

    def sleep_until(self, t, stop):
        while not stop.is_set():
            d = t - time.time()
            if d <= 0:
                return
            time.sleep(min(d, 5.0))


class FakeClock:
    """Selftest clock: jumps instantly to each scheduled instant."""

    def __init__(self, t0=1_800_000_000.0):
        self.t = t0

    def now(self):
        return self.t

    def sleep_until(self, t, stop):
        self.t = max(self.t, t)


def iso(epoch):
    return datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat(
        timespec="seconds")


# ---------------------------------------------------------------- prefixes --

def det_words(seed_str, n):
    return random.Random(seed_str).choices(VOCAB, k=n)


def det_prefix(salt, probe_id, tokens_target):
    """Deterministic unique prefix of ~tokens_target tokens (resume-safe)."""
    tag = hashlib.sha256(
        f"{salt}|{probe_id}|{tokens_target}".encode()).hexdigest()[:12]
    n_words = max(8, tokens_target - TAG_TOKENS)
    words = det_words(f"{salt}|{probe_id}|{tokens_target}|words", n_words)
    return f"probe-{tag}\n" + " ".join(words)


def gran_divergent_prefix(salt, base_pid, read_pid, pct):
    """Copy of the base prefix whose first divergence is at ~pct% of tokens."""
    base = det_prefix(salt, base_pid, PREFIX_TOKENS)
    if pct >= 100:
        return base
    tag_line, body = base.split("\n", 1)
    words = body.split()
    keep = int(len(words) * pct / 100)
    suffix = det_words(f"{salt}|{read_pid}|suffix", len(words) - keep)
    return tag_line + "\n" + " ".join(words[:keep] + suffix)


# --------------------------------------------------------------- transport --

def cost_usd(provider, model_key, opts, creation, read, inp):
    base = PRICE_IN[model_key]
    if provider == "anthropic":
        cmult = 2.0 if opts.get("cc_ttl") == "1h" else 1.25
        return (inp * base + creation * cmult * base + read * 0.10 * base) / 1e6
    return ((inp - read) * base + read * 0.50 * base) / 1e6


class RealTransport:
    """Live HTTP with 3x backoff retry on 429/5xx/network. 60 s timeouts."""

    def __init__(self):
        self.openai_token_param = "max_tokens"  # swapped on 400 if needed

    def _post(self, url, headers, body):
        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers,
                                     method="POST")
        t0 = time.monotonic()
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
                return (resp.status, json.loads(resp.read().decode("utf-8")),
                        (time.monotonic() - t0) * 1000.0)
        except urllib.error.HTTPError as err:
            try:
                payload = json.loads(err.read().decode("utf-8"))
            except Exception:
                payload = {"error": {"message": "unparseable error body"}}
            return err.code, payload, (time.monotonic() - t0) * 1000.0

    def _post_retry(self, url, headers, body):
        last = (0, {"error": {"message": "no attempt made"}}, 0.0)
        for attempt in range(4):  # 1 try + 3 retries, 2/4/8 s backoff
            if attempt:
                time.sleep(2 ** attempt)
            try:
                status, payload, latency = self._post(url, headers, body)
            except Exception as exc:
                last = (0, {"error": {"message":
                                      f"network:{type(exc).__name__}"}}, 0.0)
                continue
            if status == 429 or status >= 500:
                last = (status, payload, latency)
                continue
            return status, payload, latency
        return last

    def request(self, provider, model_key, model, prefix, opts):
        if provider == "anthropic":
            headers = {"x-api-key": os.environ["ANTHROPIC_API_KEY"],
                       "anthropic-version": "2023-06-01",
                       "content-type": "application/json"}
            if opts.get("beta"):
                headers["anthropic-beta"] = ANTHROPIC_1H_BETA
            cc = {"type": "ephemeral"}
            if opts.get("cc_ttl"):
                cc = {"type": "ephemeral", "ttl": opts["cc_ttl"]}
            body = {"model": model, "max_tokens": 1,
                    "system": [{"type": "text", "text": prefix,
                                "cache_control": cc}],
                    "messages": [{"role": "user", "content": "hi"}]}
            status, payload, latency = self._post_retry(
                ANTHROPIC_URL, headers, body)
            if status != 200:
                return self._err(status, payload, latency)
            usage = payload.get("usage") or {}
            creation = usage.get("cache_creation_input_tokens") or 0
            read = usage.get("cache_read_input_tokens") or 0
            inp = usage.get("input_tokens") or 0
        else:
            headers = {"Authorization": "Bearer " + os.environ["OPENAI_API_KEY"],
                       "content-type": "application/json"}
            body = {"model": model, self.openai_token_param: 1,
                    "messages": [{"role": "system", "content": prefix},
                                 {"role": "user", "content": "hi"}]}
            if opts.get("retention"):
                body["prompt_cache_retention"] = opts["retention"]
            status, payload, latency = self._post_retry(
                OPENAI_URL, headers, body)
            if status == 400 and "max_completion_tokens" in json.dumps(payload):
                self.openai_token_param = "max_completion_tokens"
                body.pop("max_tokens", None)
                body["max_completion_tokens"] = 1
                status, payload, latency = self._post_retry(
                    OPENAI_URL, headers, body)
            if status != 200:
                return self._err(status, payload, latency)
            usage = payload.get("usage") or {}
            creation = 0
            read = (usage.get("prompt_tokens_details") or {}).get(
                "cached_tokens") or 0
            inp = usage.get("prompt_tokens") or 0
        return {"ok": True, "status": status, "creation": creation,
                "read": read, "input": inp,
                "latency_ms": round(latency, 1),
                "cost": cost_usd(provider, model_key, opts, creation, read,
                                 inp), "note": ""}

    @staticmethod
    def _err(status, payload, latency):
        msg = str((payload.get("error") or {}).get("message", payload))[:300]
        return {"ok": False, "status": status, "creation": 0, "read": 0,
                "input": 0, "latency_ms": round(latency, 1), "cost": 0.0,
                "note": f"error:{status}:{msg}"}


class FakeTransport:
    """Selftest transport: simulates provider cache semantics, no HTTP.

    Anthropic: all-or-nothing exact-prefix cache, min 4096 tokens,
    TTL 300 s (5m) / 3600 s (1h). OpenAI: longest-common-prefix cache in
    128-token blocks, min 1024 tokens, TTL 300 s (default/in_memory) or
    86400 s (24h)."""

    def __init__(self, clock):
        self.clock = clock
        self.anthro = {}   # sha(text) -> expiry
        self.oa = []       # (words_tuple, expiry)

    @staticmethod
    def _tokens(text):
        return len(text.split()) + TAG_TOKENS - 1

    def request(self, provider, model_key, model, prefix, opts):
        now = self.clock.now()
        tokens = self._tokens(prefix)
        creation = read = 0
        if provider == "anthropic":
            ttl = 3600 if opts.get("cc_ttl") == "1h" else 300
            key = hashlib.sha256(prefix.encode()).hexdigest()
            if key in self.anthro and now < self.anthro[key]:
                read = tokens
            elif tokens >= 4096:
                creation = tokens
                self.anthro[key] = now + ttl
            inp = 7
        else:
            ttl = 86400 if opts.get("retention") == "24h" else 300
            words = tuple(prefix.split())
            best = 0
            for cached_words, expiry in self.oa:
                if now >= expiry:
                    continue
                n = 0
                for a, b in zip(cached_words, words):
                    if a != b:
                        break
                    n += 1
                best = max(best, n)
            matched = (min(best + TAG_TOKENS - 1, tokens) // 128) * 128
            read = matched if matched >= 1024 else 0
            self.oa.append((words, now + ttl))
            inp = tokens + 8
        return {"ok": True, "status": 200, "creation": creation, "read": read,
                "input": inp, "latency_ms": 0.0,
                "cost": cost_usd(provider, model_key, opts, creation, read,
                                 inp), "note": ""}


# ---------------------------------------------------------------- timeline --

def _ev(seq, offset, provider, arm_key, model_key, ptype, event, pid,
        rep="", delay="", tokens=PREFIX_TOKENS, gran_pct=None,
        gran_base=None, bisect_k=None):
    return {"seq": seq, "offset": offset, "provider": provider,
            "arm_key": arm_key, "model_key": model_key, "ptype": ptype,
            "event": event, "pid": pid, "rep": rep, "delay": delay,
            "tokens": tokens, "gran_pct": gran_pct, "gran_base": gran_base,
            "bisect_k": bisect_k}


def build_timeline():
    """All 656 events of arms A-D on one offset axis, sorted by time."""
    events, seq, widx = [], 0, 0

    def add(**kw):
        nonlocal seq
        events.append(_ev(seq, **kw))
        seq += 1

    for rep in range(REPS_A):                      # arm A: 288 pairs
        for delay in DELAYS_A:
            for arm_key, provider, model_key in ARMS_A:
                off = widx * WRITE_STAGGER_S
                widx += 1
                pid = f"{arm_key}-d{delay}-r{rep}"
                for event, o in (("write", off), ("read", off + delay)):
                    add(offset=o, provider=provider, arm_key=arm_key,
                        model_key=model_key, ptype="ttl", event=event,
                        pid=pid, rep=rep, delay=delay)
    for rep in range(REPS_B):                      # arm B: 18 pairs
        for delay in DELAYS_B:
            for arm_key, provider, model_key in ARMS_B:
                off = widx * WRITE_STAGGER_S
                widx += 1
                pid = f"{arm_key}-d{delay}-r{rep}"
                for event, o in (("write", off), ("read", off + delay)):
                    add(offset=o, provider=provider, arm_key=arm_key,
                        model_key=model_key, ptype="tier", event=event,
                        pid=pid, rep=rep, delay=delay)

    g0 = widx * WRITE_STAGGER_S + 8.0              # arm D: granularity ladder
    gran_cfg = [("anthropic", "haiku"), ("openai", "4o-mini")]
    for j, (provider, model_key) in enumerate(gran_cfg):
        arm_key = f"{provider}-gran"
        wpid = f"{arm_key}-w"
        wt = g0 + j * WRITE_STAGGER_S
        add(offset=wt, provider=provider, arm_key=arm_key,
            model_key=model_key, ptype="gran", event="write", pid=wpid)
        slot = 0
        for pct in GRAN_OFFSETS_PCT:
            for rep in range(GRAN_REPS):
                add(offset=wt + 30 + slot * 6, provider=provider,
                    arm_key=arm_key, model_key=model_key, ptype="gran",
                    event="read", pid=f"{arm_key}-{pct}pct-r{rep}", rep=rep,
                    delay=round(30 + slot * 6), gran_pct=pct, gran_base=wpid)
                slot += 1
        add(offset=wt + 30 + slot * 6, provider=provider, arm_key=arm_key,
            model_key=model_key, ptype="gran", event="read",
            pid=f"{arm_key}-100pct-r0", rep=0, delay=round(30 + slot * 6),
            gran_pct=100, gran_base=wpid)

    b0 = g0 + 30 + (len(GRAN_OFFSETS_PCT) * GRAN_REPS + 1) * 6 + 20
    for k in range(BISECT_PAIRS):                  # arm C: adaptive bisect
        for j, provider in enumerate(("anthropic", "openai")):
            arm_key = f"{provider}-bisect"
            model_key = BISECT[provider]["model_key"]
            wt = b0 + k * 30 + j * 7
            pid = f"{arm_key}-{k}"
            add(offset=wt, provider=provider, arm_key=arm_key,
                model_key=model_key, ptype="bisect", event="write", pid=pid,
                rep=k, tokens=None, bisect_k=k)
            add(offset=wt + BISECT_READ_DELAY, provider=provider,
                arm_key=arm_key, model_key=model_key, ptype="bisect",
                event="read", pid=pid, rep=k, delay=BISECT_READ_DELAY,
                tokens=None, bisect_k=k)

    return sorted(events, key=lambda e: (e["offset"], e["seq"]))


def worst_case_cost(events):
    total = 0.0
    for ev in events:
        tokens = ev["tokens"] or BISECT[ev["provider"]]["hi"]
        base = PRICE_IN[ev["model_key"]]
        if ev["provider"] == "anthropic":
            mult = 2.0 if ev["arm_key"] == "anthropic-1h" else 1.25
        else:
            mult = 1.0
        total += tokens * base * mult / 1e6
    return total


def print_summary(events, csv_path, n_skipped=0):
    counts = Counter(ev["arm_key"] for ev in events)
    est = worst_case_cost(events)
    wall = max(ev["offset"] for ev in events) if events else 0.0
    eta = datetime.now() + timedelta(seconds=wall)
    print("=== SCHEDULE SUMMARY (live_probe_v2) ===", flush=True)
    print(f"csv: {csv_path}")
    print("events per arm:")
    for arm in sorted(counts):
        print(f"  {arm:22s} {counts[arm]:4d} events "
              f"({counts[arm] // 2} write/read pairs)")
    print(f"total events: {sum(counts.values())}"
          + (f"  (resume: {n_skipped} already complete, skipped)"
             if n_skipped else ""))
    print(f"est worst-case cost: ${est:.2f} "
          f"(soft ${SOFT_BUDGET_USD:.0f} / hard abort ${HARD_BUDGET_USD:.0f})")
    print(f"est wall time: {wall:.0f} s (~{wall / 3600:.2f} h); "
          f"est completion: {eta.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 41, flush=True)
    return est


# ------------------------------------------------------------------ resume --

def load_resume(path):
    """Parse a partial CSV: completed events, write walls, spend, arm modes,
    and bisect bracket replay. Rows whose note contains 'error:' are retried."""
    completed, write_wall, spent = set(), {}, 0.0
    inmem_mode, ttl1h_mode = "param", "plain"
    bisect_rows = []
    with open(path, newline="") as fh:
        for row in csv.DictReader(fh):
            if row.get("event") not in ("write", "read"):
                continue
            note = row.get("note") or ""
            try:
                spent += float(row.get("est_cost_usd") or 0.0)
            except ValueError:
                pass
            if "error:" in note:
                continue
            key = (row["probe_id"], row["event"])
            completed.add(key)
            if row["event"] == "write":
                try:
                    write_wall[row["probe_id"]] = datetime.fromisoformat(
                        row["t_iso"]).timestamp()
                except ValueError:
                    pass
            if row.get("arm") == "openai-default":
                inmem_mode = "omit"
            if "1h_beta_header" in note:
                ttl1h_mode = "beta"
            if row.get("probe_type") == "bisect":
                bisect_rows.append(row)
    return {"completed": completed, "write_wall": write_wall, "spent": spent,
            "inmem_mode": inmem_mode, "ttl1h_mode": ttl1h_mode,
            "bisect_rows": bisect_rows}


# ---------------------------------------------------------------- campaign --

class Campaign:
    def __init__(self, events, csv_path, transport, clock, threaded,
                 resume=None):
        self.events, self.csv_path = events, csv_path
        self.transport, self.clock, self.threaded = transport, clock, threaded
        self.salt = os.path.splitext(os.path.basename(csv_path))[0]
        self.resume = resume or {"completed": set(), "write_wall": {},
                                 "spent": 0.0, "inmem_mode": "param",
                                 "ttl1h_mode": "plain", "bisect_rows": []}
        self.budget = Budget(SOFT_BUDGET_USD, HARD_BUDGET_USD,
                             preload=self.resume["spent"])
        self.stop = threading.Event()
        self.exit_code = 0
        self.executed = 0
        self.models = {}
        self.dead_arms = {}
        self.skipped = Counter()
        self.write_wall = dict(self.resume["write_wall"])
        self.inmem_mode = self.resume["inmem_mode"]
        self.ttl1h_mode = self.resume["ttl1h_mode"]
        self._lock = threading.Lock()
        self._csv_lock = threading.Lock()
        self._fh = None
        self._writer = None
        self.bisect = {
            p: {"lo": cfg["lo"], "hi": cfg["hi"], "sizes": {},
                "gates": [threading.Event() for _ in range(BISECT_PAIRS + 1)],
                "wdone": [threading.Event() for _ in range(BISECT_PAIRS)]}
            for p, cfg in BISECT.items()}
        for st in self.bisect.values():
            st["gates"][0].set()
        self._replay_bisect()

    def _replay_bisect(self):
        rows = sorted(self.resume["bisect_rows"],
                      key=lambda r: (r["probe_id"], r["event"] == "write"))
        for row in rows:
            provider = row["provider"]
            st = self.bisect.get(provider)
            if st is None:
                continue
            try:
                k = int(row["probe_id"].rsplit("-", 1)[1])
                size = int(row["prefix_tokens_target"])
            except (ValueError, IndexError):
                continue
            st["sizes"][k] = size
            if row["event"] == "write":
                st["wdone"][k].set()
                st["gates"][k].set()
            else:
                hit = int(row["cache_read"] or 0) > 0
                if hit:
                    st["hi"] = min(st["hi"], size)
                else:
                    st["lo"] = max(st["lo"], size)
                st["gates"][k + 1].set()
                st["gates"][k].set()

    # -- CSV ------------------------------------------------------------
    def _open_csv(self):
        os.makedirs(RESULTS_DIR, exist_ok=True)
        new = not os.path.exists(self.csv_path)
        self._fh = open(self.csv_path, "a", newline="")
        self._writer = csv.writer(self._fh)
        if new:
            self._writer.writerow(COLUMNS)
            self._fh.flush()

    def _row(self, provider, arm, ptype, event, pid, rep, delay, tokens, res,
             note):
        with self._csv_lock:
            self._writer.writerow([
                provider, arm, ptype, event, pid, rep, delay,
                tokens if tokens is not None else "",
                iso(self.clock.now()), res["creation"], res["read"],
                res["input"], res["latency_ms"], f"{res['cost']:.6f}", note])
            self._fh.flush()

    def _meta_row(self, provider, note, cost=0.0):
        with self._csv_lock:
            self._writer.writerow([provider, "", "meta", "meta", "", "", "",
                                   "", iso(self.clock.now()), "", "", "", "",
                                   f"{cost:.6f}", note])
            self._fh.flush()

    # -- models ----------------------------------------------------------
    def _resolve_models(self):
        needed = sorted({ev["model_key"] for ev in self.events})
        for key in needed:
            provider = MODEL_PROVIDER[key]
            resolved = None
            for model in MODEL_CANDIDATES[key]:
                res = self.transport.request(provider, key, model,
                                             "model resolution ping",
                                             {"cc_ttl": None})
                try:
                    self.budget.add(res["cost"])
                except BudgetExceeded:
                    pass
                if res["ok"]:
                    resolved = model
                    break
                print(f"[resolve] {key}: {model} rejected -> {res['note']}",
                      flush=True)
            if resolved:
                self.models[key] = resolved
                self._meta_row(provider, f"model_resolved:{key}={resolved}")
                print(f"[resolve] {key} -> {resolved}", flush=True)
            else:
                for arm, mk in _arm_model_keys().items():
                    if mk == key:
                        self.dead_arms[arm] = f"model_unresolved:{key}"
                self._meta_row(provider, f"model_unresolved:{key}")
                print(f"[resolve] {key}: NO candidate accepted; dependent "
                      f"arms dropped", flush=True)

    # -- per-event helpers -------------------------------------------------
    def _arm_label(self, arm_key):
        if arm_key == "openai-inmem" and self.inmem_mode == "omit":
            return "openai-default"
        return arm_key

    def _opts_for(self, ev):
        arm = ev["arm_key"]
        if ev["provider"] == "anthropic":
            return {"cc_ttl": "1h" if arm == "anthropic-1h" else None,
                    "beta": self.ttl1h_mode == "beta"}
        if arm == "openai-24h":
            return {"retention": "24h"}
        if arm == "openai-inmem" and self.inmem_mode == "param":
            return {"retention": "in_memory"}
        return {"retention": None}

    def _prefix_for(self, ev):
        """Returns (prefix, tokens_target, note_extra)."""
        p, pid = ev["ptype"], ev["pid"]
        if p in ("ttl", "tier"):
            return det_prefix(self.salt, pid, PREFIX_TOKENS), PREFIX_TOKENS, ""
        if p == "gran":
            if ev["event"] == "write":
                return (det_prefix(self.salt, pid, PREFIX_TOKENS),
                        PREFIX_TOKENS, "")
            return (gran_divergent_prefix(self.salt, ev["gran_base"], pid,
                                          ev["gran_pct"]), PREFIX_TOKENS,
                    f"div={ev['gran_pct']}pct")
        st = self.bisect[ev["provider"]]                    # bisect
        k, note = ev["bisect_k"], ""
        if ev["event"] == "write":
            if not st["gates"][k].wait(GATE_TIMEOUT_S):
                note = "gate_timeout"
            with self._lock:
                size = (st["lo"] + st["hi"]) // 2
                st["sizes"][k] = size
        else:
            if not st["wdone"][k].wait(GATE_TIMEOUT_S):
                note = "gate_timeout"
            size = st["sizes"].get(k, (st["lo"] + st["hi"]) // 2)
        return det_prefix(self.salt, pid, size), size, note

    def _arm_fallbacks(self, ev, res, prefix, size):
        """First-rejection handling for anthropic-1h and openai-inmem."""
        arm = ev["arm_key"]
        if res["ok"] or res["status"] != 400:
            return res, ""
        if arm == "anthropic-1h":
            if self.ttl1h_mode == "plain":
                with self._lock:
                    self.ttl1h_mode = "beta"
                res2 = self.transport.request(
                    ev["provider"], ev["model_key"],
                    self.models[ev["model_key"]], prefix,
                    {"cc_ttl": "1h", "beta": True})
                if res2["ok"]:
                    return res2, "1h_beta_header"
                res = res2
            self.dead_arms[arm] = "1h_ttl_rejected"
            self._meta_row("anthropic", f"arm_rejected:anthropic-1h:"
                                        f"{res['note'][:160]}")
            print("[arm] anthropic-1h REJECTED; arm dropped", flush=True)
            return res, "arm_rejected_dropped"
        if arm == "openai-inmem" and self.inmem_mode == "param":
            with self._lock:
                self.inmem_mode = "omit"
            self._meta_row("openai", f"inmem_rejected_fallback_default:"
                                     f"{res['note'][:160]}")
            print("[arm] openai in_memory param rejected; falling back to "
                  "openai-default (param omitted)", flush=True)
            res2 = self.transport.request(
                ev["provider"], ev["model_key"],
                self.models[ev["model_key"]], prefix, {"retention": None})
            return res2, "inmem_rejected_fallback_default"
        return res, ""

    # -- task --------------------------------------------------------------
    def _task(self, ev):
        if self.stop.is_set():
            return
        arm = ev["arm_key"]
        if arm in self.dead_arms:
            with self._lock:
                self.skipped[arm] += 1
            return
        prefix, size, pre_note = self._prefix_for(ev)
        opts = self._opts_for(ev)
        model = self.models.get(ev["model_key"], "")
        res = self.transport.request(ev["provider"], ev["model_key"], model,
                                     prefix, opts)
        res, fb_note = self._arm_fallbacks(ev, res, prefix, size)
        with self._lock:
            self.executed += 1
        aborted = False
        try:
            self.budget.add(res["cost"])
        except BudgetExceeded as exc:
            aborted = True
            fb_note = (fb_note + ";" if fb_note else "") + f"abort_budget:{exc}"
        notes = []
        if ev["event"] == "write":
            self.write_wall[ev["pid"]] = self.clock.now()
            notes.append(f"model={model}")
            if (ev["provider"] == "anthropic" and res["ok"]
                    and ev["ptype"] in ("ttl", "tier")
                    and res["creation"] <= 0 and res["read"] <= 0):
                notes.append("warn_no_creation")
        else:
            ww = self.write_wall.get(ev["pid"])
            notes.append(f"d_act={self.clock.now() - ww:.1f}"
                         if ww is not None else "d_act=na")
        for n in (pre_note, fb_note, res["note"]):
            if n:
                notes.append(n)
        self._row(ev["provider"], self._arm_label(arm), ev["ptype"],
                  ev["event"], ev["pid"], ev["rep"], ev["delay"], size, res,
                  ";".join(notes))
        if ev["ptype"] == "bisect":
            st = self.bisect[ev["provider"]]
            k = ev["bisect_k"]
            if ev["event"] == "write":
                st["wdone"][k].set()
            else:
                with self._lock:
                    if res["ok"]:
                        if res["read"] > 0:
                            st["hi"] = min(st["hi"], size)
                        else:
                            st["lo"] = max(st["lo"], size)
                if k + 1 <= BISECT_PAIRS:
                    st["gates"][min(k + 1, BISECT_PAIRS)].set()
        print(f"[v2] {ev['event']:5s} {ev['pid']:34s} status={res['status']} "
              f"creation={res['creation']} read={res['read']} "
              f"cum=${self.budget.total_usd:.4f}", flush=True)
        if aborted:
            print(f"[v2] HARD ABORT at ${self.budget.total_usd:.4f}",
                  flush=True)
            self.exit_code = 2
            self.stop.set()

    # -- run -----------------------------------------------------------------
    def run(self):
        self._open_csv()
        try:
            self._resolve_models()
            pending = [ev for ev in self.events
                       if (ev["pid"], ev["event"])
                       not in self.resume["completed"]]
            t0 = self.clock.now()
            for ev in pending:
                if (ev["event"] == "read" and ev["delay"] != ""
                        and (ev["pid"], "write") in self.resume["completed"]
                        and ev["pid"] in self.write_wall):
                    ev["target"] = self.write_wall[ev["pid"]] + ev["delay"]
                else:
                    ev["target"] = t0 + ev["offset"]
            pending.sort(key=lambda e: (e["target"], e["seq"]))
            print(f"[v2] scheduling {len(pending)} events "
                  f"({len(self.events) - len(pending)} skipped via resume)",
                  flush=True)
            threads = []
            for ev in pending:
                if self.stop.is_set():
                    break
                self.clock.sleep_until(ev["target"], self.stop)
                if self.stop.is_set():
                    break
                if self.threaded:
                    th = threading.Thread(target=self._task, args=(ev,))
                    th.start()
                    threads.append(th)
                else:
                    self._task(ev)
            for th in threads:
                th.join(timeout=TIMEOUT_S * 4 + 120)
        except KeyboardInterrupt:
            self.stop.set()
            self.exit_code = 130
            self._meta_row("meta", "interrupted")
            print("[v2] interrupted; partial CSV is resume-able", flush=True)
        for arm, why in self.dead_arms.items():
            if self.skipped[arm]:
                self._meta_row("meta",
                               f"arm_dropped:{arm}:{why}:"
                               f"{self.skipped[arm]}_events_skipped")
        for provider, st in self.bisect.items():
            self._meta_row(provider,
                           f"bisect_bracket:{provider}:lo={st['lo']}:"
                           f"hi={st['hi']}")
        self._meta_row("meta", "campaign_total_est_cost",
                       cost=self.budget.total_usd)
        self._fh.close()
        print(f"[v2] done; est total ${self.budget.total_usd:.4f}; "
              f"exit={self.exit_code}", flush=True)
        return self.exit_code


def _arm_model_keys():
    keys = {arm: mk for arm, _, mk in ARMS_A}
    keys.update({arm: mk for arm, _, mk in ARMS_B})
    keys.update({"anthropic-bisect": "haiku", "openai-bisect": "4o-mini",
                 "anthropic-gran": "haiku", "openai-gran": "4o-mini"})
    return keys


# ---------------------------------------------------------------- selftest --

def _check(name, cond):
    if not cond:
        print(f"[selftest] FAIL {name}", flush=True)
        raise AssertionError(name)
    print(f"[selftest] PASS {name}", flush=True)


def cmd_selftest():
    csv_path = os.path.join(RESULTS_DIR, "selftest_v2.csv")
    if os.path.exists(csv_path):
        os.remove(csv_path)
    events = build_timeline()

    offsets = [ev["offset"] for ev in events]
    _check("timeline sorted by time", offsets == sorted(offsets))
    counts = Counter(ev["arm_key"] for ev in events)
    _check(f"per-arm event counts == expected ({dict(counts)})",
           dict(counts) == EXPECTED_ARM_EVENTS)
    writes = sorted(ev["offset"] for ev in events if ev["event"] == "write")
    min_gap = min(b - a for a, b in zip(writes, writes[1:]))
    _check(f"write stagger >= 1.3 s (min gap {min_gap:.1f} s)", min_gap >= 1.3)

    est = print_summary(events, csv_path)
    _check(f"budget estimate printed and under hard cap (${est:.2f})",
           0 < est < HARD_BUDGET_USD)

    clock = FakeClock()
    camp = Campaign(events, csv_path, FakeTransport(clock), clock,
                    threaded=False)
    rc = camp.run()
    _check("fake campaign exit code 0", rc == 0)
    _check(f"all 656 events executed ({camp.executed})", camp.executed == 656)

    with open(csv_path, newline="") as fh:
        rows = list(csv.reader(fh))
    _check("CSV header matches schema", rows[0] == COLUMNS)
    data = [dict(zip(COLUMNS, r)) for r in rows[1:]]
    probe_rows = [r for r in data if r["event"] in ("write", "read")]
    _check(f"CSV probe rows == 656 ({len(probe_rows)})",
           len(probe_rows) == 656)

    def hits(arm, delay):
        return [int(r["cache_read"]) > 0 for r in probe_rows
                if r["arm"] == arm and r["event"] == "read"
                and r["probe_type"] in ("ttl", "tier")
                and r["delay_s"] == str(delay)]

    for arm, ttl in [("anthropic-5m", 300), ("openai-inmem", 300),
                     ("anthropic-1h", 3600), ("openai-24h", 86400)]:
        for delay in DELAYS_A:
            h = hits(arm, delay)
            expect = delay < ttl
            _check(f"{arm} d={delay}s -> {'hit' if expect else 'miss'} x6",
                   len(h) == REPS_A and all(x == expect for x in h))
    for arm in ("anthropic-sonnet-5m", "openai-4o-default"):
        for delay in DELAYS_B:
            h = hits(arm, delay)
            expect = delay < 300
            _check(f"{arm} d={delay}s -> {'hit' if expect else 'miss'} x3",
                   len(h) == REPS_B and all(x == expect for x in h))

    ab, ob = camp.bisect["anthropic"], camp.bisect["openai"]
    _check(f"anthropic bisect bracket ({ab['lo']},{ab['hi']}] contains 4096, "
           f"width<=60", ab["lo"] < 4096 <= ab["hi"]
           and ab["hi"] - ab["lo"] <= 60)
    _check(f"openai bisect bracket ({ob['lo']},{ob['hi']}] contains 1024, "
           f"width<=24", ob["lo"] < 1024 <= ob["hi"]
           and ob["hi"] - ob["lo"] <= 24)

    gran = [r for r in probe_rows if r["probe_type"] == "gran"
            and r["event"] == "read"]
    a_div = [int(r["cache_read"]) for r in gran
             if r["arm"] == "anthropic-gran" and "100pct" not in r["probe_id"]]
    a_full = [int(r["cache_read"]) for r in gran
              if r["arm"] == "anthropic-gran" and "100pct" in r["probe_id"]]
    _check("anthropic granularity all-or-nothing (divergent=0, exact=full)",
           all(v == 0 for v in a_div) and all(v >= 4096 for v in a_full))
    o_by_pct = {}
    for r in gran:
        if r["arm"] == "openai-gran":
            pct = int(r["probe_id"].split("-")[2].replace("pct", ""))
            o_by_pct.setdefault(pct, []).append(int(r["cache_read"]))
    o_means = [sum(o_by_pct[p]) / len(o_by_pct[p]) for p in sorted(o_by_pct)]
    _check(f"openai granularity monotone in divergence offset ({o_means})",
           all(a <= b for a, b in zip(o_means, o_means[1:]))
           and o_means[-1] >= 4096)
    _check(f"fake-run est cost under hard cap "
           f"(${camp.budget.total_usd:.4f})",
           0 < camp.budget.total_usd < HARD_BUDGET_USD)

    resume = load_resume(csv_path)
    clock2 = FakeClock()
    camp2 = Campaign(build_timeline(), csv_path, FakeTransport(clock2),
                     clock2, threaded=False, resume=resume)
    rc2 = camp2.run()
    _check("resume run exit code 0", rc2 == 0)
    _check(f"resume skips all completed events (executed={camp2.executed})",
           camp2.executed == 0)

    print("[selftest] SELFTEST PASS (no HTTP performed)", flush=True)
    return 0


# --------------------------------------------------------------------- run --

def cmd_run(resume_path=None):
    for var in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY"):
        if not os.environ.get(var):
            print(f"[v2] {var} not set; source ~/.keys/cachecontract_probe.env"
                  f" first", flush=True)
            return 1
    events = build_timeline()
    resume = None
    n_skipped = 0
    if resume_path:
        resume = load_resume(resume_path)
        csv_path = resume_path
        n_skipped = sum(1 for ev in events
                        if (ev["pid"], ev["event"]) in resume["completed"])
    else:
        csv_path = os.path.join(
            RESULTS_DIR, f"live_v2_{time.strftime('%Y%m%d_%H%M')}.csv")
    print_summary(events, csv_path, n_skipped=n_skipped)
    camp = Campaign(events, csv_path, RealTransport(), RealClock(),
                    threaded=True, resume=resume)
    return camp.run()


def main(argv):
    if "--selftest" in argv:
        return cmd_selftest()
    if "--run" in argv:
        resume_path = None
        if "--resume" in argv:
            resume_path = argv[argv.index("--resume") + 1]
            if not os.path.exists(resume_path):
                print(f"[v2] resume csv not found: {resume_path}")
                return 1
        return cmd_run(resume_path)
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
