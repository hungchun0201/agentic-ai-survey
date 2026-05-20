#!/usr/bin/env python3
"""Validate schemas/ and content/extracted/ for the paper comparison table.

Two passes:

1. SCHEMAS — every schemas/*.yaml must parse, have a `name`, declare its
   `fields` map, and reference only existing parents in `inherits:`. Each
   field with kind: tags should ideally have canonical_values (warning if
   not — sometimes intentional).

2. RECORDS — every content/extracted/*.json must:
   - have a non-empty `domains` array,
   - reference only existing domains (matching a schemas/*.yaml),
   - have every key declared by the union of its domains' resolved schemas,
   - have correct value shapes per kind (bilingual → {en,zh}, tags → str, etc.).

Usage:
    python3 tools/validate.py             # validate both
    python3 tools/validate.py --schemas   # schemas only
    python3 tools/validate.py --records   # records only
    python3 tools/validate.py --strict    # warnings count as errors

Designed to run in CI: exit 0 only when no errors. Warnings don't fail
unless --strict.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is required. `pip install pyyaml` or `pip3 install pyyaml`.", file=sys.stderr)
    sys.exit(2)

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_DIR = REPO_ROOT / "schemas"
EXTRACTED_DIR = REPO_ROOT / "content" / "extracted"

VALID_KINDS = {
    "title", "text", "tags", "list", "venue", "arxiv",
    "affiliations", "link", "domains",
}


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def err(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    def ok(self) -> bool:
        return not self.errors


def load_schemas() -> dict[str, dict]:
    """Load all schemas/*.yaml into a name → raw_schema map (no inheritance resolution)."""
    schemas = {}
    for f in sorted(SCHEMA_DIR.glob("*.yaml")):
        try:
            raw = yaml.safe_load(f.read_text())
        except yaml.YAMLError as e:
            print(f"FATAL: {f.name} is not valid YAML: {e}", file=sys.stderr)
            sys.exit(2)
        name = raw.get("name")
        if not name:
            print(f"FATAL: {f.name} missing top-level `name`", file=sys.stderr)
            sys.exit(2)
        if name != f.stem:
            print(f"WARNING: {f.name} declares name={name!r} which differs from filename")
        schemas[name] = raw
    return schemas


def resolve_schema(name: str, all_schemas: dict[str, dict], visiting: set[str] | None = None) -> dict:
    """Return a schema with inherited fields merged in, in order."""
    visiting = visiting or set()
    if name in visiting:
        raise ValueError(f"cycle in inherits chain at {name!r}")
    if name not in all_schemas:
        raise ValueError(f"unknown schema {name!r}")
    raw = all_schemas[name]
    merged_fields = {}
    for parent in raw.get("inherits", []) or []:
        parent_resolved = resolve_schema(parent, all_schemas, visiting | {name})
        merged_fields.update(parent_resolved["fields"])
    merged_fields.update(raw.get("fields", {}) or {})
    out = dict(raw)
    out["fields"] = merged_fields
    return out


def validate_schemas(schemas: dict[str, dict], rep: Report) -> dict[str, dict]:
    """Check schema structural correctness. Returns resolved schemas."""
    resolved: dict[str, dict] = {}
    for name in schemas:
        try:
            resolved[name] = resolve_schema(name, schemas)
        except ValueError as e:
            rep.err(f"schema {name}: {e}")
            continue
        raw = schemas[name]
        for parent in raw.get("inherits", []) or []:
            if parent not in schemas:
                rep.err(f"schema {name}: inherits unknown {parent!r}")
        for field_key, field in (raw.get("fields") or {}).items():
            if not isinstance(field, dict):
                rep.err(f"schema {name}: field {field_key!r} must be a mapping")
                continue
            kind = field.get("kind")
            if kind not in VALID_KINDS:
                rep.err(f"schema {name}: field {field_key!r} has invalid kind={kind!r}")
            if kind == "tags" and "canonical_values" not in field:
                rep.warn(f"schema {name}: field {field_key!r} (kind=tags) has no canonical_values; tag normalization will rely on existing-record grep")
            if field.get("bilingual") and kind != "text":
                rep.err(f"schema {name}: field {field_key!r} marked bilingual but kind={kind!r} (only kind=text supports bilingual)")
            if "label" in field:
                lbl = field["label"]
                if not isinstance(lbl, dict) or "en" not in lbl:
                    rep.warn(f"schema {name}: field {field_key!r} label should be a {{en, zh}} mapping")
    return resolved


def validate_record(record_path: Path, resolved: dict[str, dict], rep: Report) -> None:
    try:
        record = json.loads(record_path.read_text())
    except json.JSONDecodeError as e:
        rep.err(f"{record_path.name}: invalid JSON: {e}")
        return
    slug = record.get("slug") or record_path.stem
    domains = record.get("domains") or []
    if not isinstance(domains, list) or not domains:
        rep.err(f"{slug}: missing or empty `domains` array")
        return
    union_fields: dict[str, dict] = {}
    for d in domains:
        if d not in resolved:
            rep.err(f"{slug}: declares unknown domain {d!r} (no schemas/{d}.yaml)")
            continue
        union_fields.update(resolved[d]["fields"])

    for field_key, field in union_fields.items():
        if field.get("kind") in ("idx", "domains"):
            continue
        if field_key not in record:
            if field.get("required"):
                rep.err(f"{slug}: missing required field {field_key!r}")
            else:
                rep.warn(f"{slug}: missing field {field_key!r}")
            continue
        value = record[field_key]
        kind = field["kind"]
        bilingual = field.get("bilingual", False)
        if bilingual:
            if not isinstance(value, dict) or "en" not in value or "zh" not in value:
                rep.err(f"{slug}: field {field_key!r} bilingual but value is not {{en, zh}}: {value!r}")
        elif kind == "list":
            if not isinstance(value, list):
                rep.err(f"{slug}: field {field_key!r} (kind=list) expected array, got {type(value).__name__}")
        else:
            if not isinstance(value, str):
                rep.err(f"{slug}: field {field_key!r} expected string, got {type(value).__name__}")

        # canonical_values: warn on non-canonical tags (not an error — corpus may have legit variants)
        if kind == "tags" and isinstance(value, str) and field.get("canonical_values"):
            canon = set(field["canonical_values"])
            present = [t.strip() for t in value.split(",") if t.strip()]
            unknown = [t for t in present if t not in canon and t != "Not Specified"]
            if unknown:
                rep.warn(f"{slug}: field {field_key!r} has non-canonical tags: {unknown!r}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--schemas", action="store_true", help="validate schemas only")
    ap.add_argument("--records", action="store_true", help="validate records only")
    ap.add_argument("--strict", action="store_true", help="warnings fail too")
    args = ap.parse_args()
    do_schemas = args.schemas or not args.records
    do_records = args.records or not args.schemas

    rep = Report()
    schemas = load_schemas() if SCHEMA_DIR.is_dir() else {}

    if do_schemas:
        if not schemas:
            rep.err("no schemas in schemas/ — refusing to validate records against nothing")
        resolved = validate_schemas(schemas, rep)
    else:
        resolved = {n: resolve_schema(n, schemas) for n in schemas}

    if do_records and rep.ok():
        if not EXTRACTED_DIR.is_dir():
            rep.warn("no content/extracted/ directory — skipping record validation")
        else:
            for f in sorted(EXTRACTED_DIR.glob("*.json")):
                validate_record(f, resolved, rep)

    if rep.errors:
        print("ERRORS:")
        for e in rep.errors:
            print(f"  ✗ {e}")
    if rep.warnings:
        print(f"\nWARNINGS ({len(rep.warnings)}):")
        for w in rep.warnings[:30]:
            print(f"  ! {w}")
        if len(rep.warnings) > 30:
            print(f"  ... +{len(rep.warnings) - 30} more")

    n_err = len(rep.errors)
    n_warn = len(rep.warnings)
    print(f"\n{'✓' if n_err == 0 else '✗'} {n_err} errors, {n_warn} warnings")
    if n_err > 0:
        return 1
    if args.strict and n_warn > 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
