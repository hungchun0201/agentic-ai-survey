#!/usr/bin/env python3
"""Transitional migration: lit-survey CSV → content/extracted/<slug>.json (one paper per file).

Source CSV is at ../literature_survey/literature_survey.csv (overridable).
For each row, derives a slug (reusing the editorial slug when arxiv id matches an
existing content/papers/<slug>.json), then writes a self-contained JSON.

After Zotero is retired, the future extract skill writes one file per prompt at the
same path with the same schema. No CSV, no pandas, no Zotero in that flow.

Run:
    python3 tools/migrate-zotero-extracted.py [--dry-run]
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CSV = REPO_ROOT.parent / "literature_survey" / "literature_survey.csv"
EDITORIAL_DIR = REPO_ROOT / "content" / "papers"
EXTRACTED_DIR = REPO_ROOT / "content" / "extracted"

NOT_SPEC = "Not Specified"

# Field groups mirror lit-survey/config.yaml extraction_fields, so the table view
# can render them as collapsible sections.
GROUPS: dict[str, list[str]] = {
    "core_insights": ["problem_statement", "key_innovation"],
    "evaluation_and_results": ["baselines_compared", "key_improvements", "open_source"],
    "experimental_setup": ["evaluation_method", "software_simulator", "network_topology"],
    "workload_and_traffic": ["ai_task", "traffic_pattern"],
    "hardware_infrastructure": ["compute_memory_hw", "network_hw", "platform"],
    "networking_stack": ["transport_and_interconnect", "routing_and_congestion_control", "comm_libraries"],
    "scale": ["gpu_count", "node_count"],
}

# Long-form prose fields that need bilingual support. These get written as
# {"en": "...", "zh": "..."} dicts in the output JSON. Other fields stay as
# plain strings. Short technical fields (hardware names, baselines, tags) stay
# in EN — they're proper nouns.
BILINGUAL_FIELDS: set[str] = {
    "problem_statement",
    "key_innovation",
    "key_improvements",
}


def norm_arxiv(s: str | None) -> str | None:
    if not s:
        return None
    s = str(s).strip()
    if s in ("", NOT_SPEC, "None"):
        return None
    m = re.search(r"(\d{4}\.\d{4,5})", s)
    return m.group(1) if m else None


def derive_slug(title: str) -> str:
    """Slug from title: take portion before colon/em-dash subtitle, kebab-case.

    Only splits on `:` and em/en-dash separators — hyphens are kept because they
    appear inside compound terms (End-to-End, On-Orbit, Lumen-1).
    """
    head = re.split(r"[:—–]", title, maxsplit=1)[0].strip()
    if len(head) < 4 and len(title) > 4:
        head = title
    slug = re.sub(r"[^a-z0-9]+", "-", head.lower()).strip("-")
    return slug[:50] or "untitled"


def load_editorial_slugs() -> tuple[dict[str, str], set[str]]:
    """Return (arxiv → slug map, set of all editorial slugs)."""
    arxiv_to_slug: dict[str, str] = {}
    all_slugs: set[str] = set()
    for f in sorted(EDITORIAL_DIR.glob("*.json")):
        if f.name == "_index.json":
            continue
        try:
            p = json.loads(f.read_text())
        except json.JSONDecodeError:
            continue
        slug = p.get("slug") or f.stem
        all_slugs.add(slug)
        ax = norm_arxiv(p.get("arxiv"))
        if ax:
            arxiv_to_slug[ax] = slug
    return arxiv_to_slug, all_slugs


def assign_slug(row: dict, arxiv_to_editorial: dict[str, str], used: set[str]) -> tuple[str, str]:
    """Return (slug, source) where source ∈ {'editorial-arxiv-match', 'derived'}."""
    arxiv = norm_arxiv(row.get("arxiv_id") or row.get("url_or_arxiv"))
    if arxiv and arxiv in arxiv_to_editorial:
        slug = arxiv_to_editorial[arxiv]
        return slug, "editorial-arxiv-match"
    base = derive_slug(row.get("title", "")) or "paper"
    slug = base
    n = 2
    while slug in used:
        slug = f"{base}-{n}"
        n += 1
    return slug, "derived"


def build_record(row: dict, slug: str, slug_source: str, generated_at: str) -> dict:
    """Construct content/extracted/<slug>.json payload."""
    def clean(v: str | None) -> str:
        if v is None:
            return NOT_SPEC
        v = str(v).strip()
        return v or NOT_SPEC

    arxiv = norm_arxiv(row.get("arxiv_id") or row.get("url_or_arxiv"))
    # Zotero collection field has a typo in CSV header (colleㄏction). Try both.
    coll = row.get("collection") or row.get("colleㄏction") or ""

    record: dict = {
        "slug": slug,
        "title": clean(row.get("title")),
        "authors": clean(row.get("authors")),
        "year": clean(row.get("year")),
        "venue": clean(row.get("publication_venue")),
        "venue_full": clean(row.get("publication_venue_full")),
        "arxiv": arxiv or "",
        "url": clean(row.get("url_or_arxiv")) if row.get("url_or_arxiv") else "",
        "affiliations": clean(row.get("affiliations")),
        "zotero_collections": [c.strip() for c in coll.split(",") if c.strip()] if coll else [],
    }

    for group, fields in GROUPS.items():
        block: dict = {}
        for f in fields:
            v = clean(row.get(f))
            if f in BILINGUAL_FIELDS:
                # English populated from CSV; Chinese left empty for future
                # skill/translator to fill in (page falls back to EN when zh empty).
                block[f] = {"en": v if v != NOT_SPEC else "", "zh": ""}
            else:
                block[f] = v
        record[group] = block

    record["source"] = {
        "zotero_key": row.get("zotero_key", "") or "",
        "extracted_by": "lit-survey-csv-migration",
        "migrated_at": generated_at,
        "slug_assignment": slug_source,
    }
    return record


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", type=Path, default=DEFAULT_CSV, help="Source CSV path")
    ap.add_argument("--dry-run", action="store_true", help="Don't write files; print plan")
    args = ap.parse_args()

    if not args.csv.exists():
        print(f"ERROR: CSV not found at {args.csv}", file=sys.stderr)
        return 1

    arxiv_to_editorial, editorial_slugs = load_editorial_slugs()
    print(f"Loaded {len(editorial_slugs)} editorial slugs ({len(arxiv_to_editorial)} with arxiv id).")

    with args.csv.open() as fh:
        rows = list(csv.DictReader(fh))
    print(f"Read {len(rows)} rows from {args.csv}.")

    used_slugs: set[str] = set()
    seen_arxivs: set[str] = set()
    plan: list[tuple[dict, str, str]] = []
    by_source: dict[str, int] = {"editorial-arxiv-match": 0, "derived": 0}
    collisions_with_editorial: list[tuple[str, str]] = []
    duplicates: list[tuple[str, str, str]] = []  # (reason, zotero_key, title)

    for row in rows:
        arxiv = norm_arxiv(row.get("arxiv_id") or row.get("url_or_arxiv"))
        if arxiv and arxiv in seen_arxivs:
            duplicates.append((f"arxiv={arxiv}", row.get("zotero_key", ""), row.get("title", "")[:60]))
            continue
        slug, src = assign_slug(row, arxiv_to_editorial, used_slugs)
        if slug in used_slugs:
            duplicates.append((f"slug={slug}", row.get("zotero_key", ""), row.get("title", "")[:60]))
            continue
        if arxiv:
            seen_arxivs.add(arxiv)
        used_slugs.add(slug)
        by_source[src] += 1
        if src == "derived" and slug in editorial_slugs:
            collisions_with_editorial.append((slug, row.get("title", "")[:60]))
        plan.append((row, slug, src))

    if duplicates:
        print(f"\nSkipped {len(duplicates)} duplicate row(s):")
        for reason, k, t in duplicates:
            print(f"  {reason:30} zotero_key={k}  {t}")

    print()
    print(f"Slug assignment: {by_source}")
    if collisions_with_editorial:
        print(f"WARNING: {len(collisions_with_editorial)} derived slug(s) collide with editorial:")
        for s, t in collisions_with_editorial:
            print(f"  {s}: {t}")

    if args.dry_run:
        print("\n=== Dry run plan (first 20) ===")
        for row, slug, src in plan[:20]:
            tag = "🔗" if src == "editorial-arxiv-match" else "🆕"
            print(f"  {tag} {slug:35} ← {row.get('title','')[:55]}")
        if len(plan) > 20:
            print(f"  ... +{len(plan) - 20} more")
        return 0

    EXTRACTED_DIR.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    written = 0
    for row, slug, src in plan:
        record = build_record(row, slug, src, generated_at)
        out = EXTRACTED_DIR / f"{slug}.json"
        out.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
        written += 1

    print(f"\nWrote {written} files to {EXTRACTED_DIR.relative_to(REPO_ROOT)}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
