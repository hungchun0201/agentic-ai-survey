#!/usr/bin/env python3
"""Flatten nested content/extracted/*.json records + add `domains` field.

Before:
    {
      "slug": "mooncake",
      "core_insights": {
        "problem_statement": {"en": "...", "zh": "..."},
        "key_innovation": {"en": "...", "zh": "..."}
      },
      "evaluation_and_results": { ... },
      "experimental_setup": { ... },
      "workload_and_traffic": { ... },
      "hardware_infrastructure": { ... },
      "networking_stack": { ... },
      "scale": { "gpu_count": "...", "node_count": "..." }
    }

After:
    {
      "slug": "mooncake",
      "domains": ["ai-networking"],
      "problem_statement": {"en": "...", "zh": "..."},
      "key_innovation": {"en": "...", "zh": "..."},
      "baselines_compared": "...",
      "gpu_count": "...",
      ...
    }

The nested grouping was a holdover from lit-survey's config.yaml. The new
schema files (schemas/<domain>.yaml) declare `group:` per field for visual
grouping in the viewer; records themselves are flat. Plus a `domains` array
tags each paper with which subtables it belongs in.

Idempotent: re-running on already-flat records is a no-op apart from
refreshing `source.flattened_at`.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EXTRACTED_DIR = REPO_ROOT / "content" / "extracted"

# Old nested group keys to flatten.
NESTED_GROUPS = [
    "core_insights",
    "evaluation_and_results",
    "experimental_setup",
    "workload_and_traffic",
    "hardware_infrastructure",
    "networking_stack",
    "scale",
]

# Per user: every existing record gets tagged with ai-networking.
# Lit-survey CSV came from a Zotero collection focused on AI datacenter
# networking, so this is the right default. New records that go via the
# /paper-extract skill will set their own domains based on --domain arg.
DEFAULT_DOMAINS = ["ai-networking"]


def flatten(record: dict) -> dict:
    """Return a flattened copy of the record."""
    flat = {}
    for k, v in record.items():
        if k in NESTED_GROUPS and isinstance(v, dict):
            for sub_k, sub_v in v.items():
                if sub_k in flat:
                    print(f"  WARNING: field {sub_k!r} clashed; keeping nested-group value", file=sys.stderr)
                flat[sub_k] = sub_v
        else:
            flat[k] = v
    return flat


def main() -> int:
    if not EXTRACTED_DIR.exists():
        print(f"ERROR: {EXTRACTED_DIR} does not exist", file=sys.stderr)
        return 1

    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    n_flat = 0
    n_already_flat = 0
    n_domains_added = 0

    for f in sorted(EXTRACTED_DIR.glob("*.json")):
        record = json.loads(f.read_text())

        # 1. Flatten nested groups (if any present).
        had_nested = any(k in record and isinstance(record[k], dict) for k in NESTED_GROUPS)
        if had_nested:
            flat = flatten(record)
            n_flat += 1
        else:
            flat = dict(record)
            n_already_flat += 1

        # 2. Add domains (idempotent).
        if "domains" not in flat or not flat["domains"]:
            flat["domains"] = list(DEFAULT_DOMAINS)
            n_domains_added += 1

        # 3. Stamp migration. Keep existing source.* keys.
        src = flat.get("source") or {}
        if not isinstance(src, dict):
            src = {}
        src["flattened_at"] = now
        flat["source"] = src

        # 4. Reorder so identity + domains lead, then content, then source.
        ordered = reorder(flat)

        f.write_text(json.dumps(ordered, ensure_ascii=False, indent=2) + "\n")

    print(f"flattened {n_flat} records ({n_already_flat} were already flat)")
    print(f"added domains to {n_domains_added} records")
    print(f"all records now tagged: domains={DEFAULT_DOMAINS}")
    return 0


# Display order for the flattened record — improves diff readability.
DISPLAY_ORDER = [
    "slug",
    "domains",
    "title",
    "authors",
    "year",
    "venue",
    "venue_full",
    "arxiv",
    "url",
    "affiliations",
    "zotero_collections",
    # Core insights
    "problem_statement",
    "key_innovation",
    # Evaluation & results
    "baselines_compared",
    "key_improvements",
    "open_source",
    # Experimental setup
    "evaluation_method",
    "software_simulator",
    "network_topology",
    # Workload & traffic
    "ai_task",
    "traffic_pattern",
    # Hardware
    "compute_memory_hw",
    "network_hw",
    "platform",
    # Networking stack
    "transport_and_interconnect",
    "routing_and_congestion_control",
    "comm_libraries",
    # Scale
    "gpu_count",
    "node_count",
    # Provenance always last
    "source",
]


def reorder(record: dict) -> dict:
    out = {}
    for k in DISPLAY_ORDER:
        if k in record:
            out[k] = record[k]
    # Anything else (forward-compat: new schema fields not yet known here)
    for k, v in record.items():
        if k not in out:
            out[k] = v
    return out


if __name__ == "__main__":
    raise SystemExit(main())
