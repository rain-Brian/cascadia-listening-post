#!/usr/bin/env python3
"""Check every schema is valid, and validate it against real data where we have some.

A schema nothing validates against is a guess. Point PUBLISHED_SITE at a site
repository to check report.schema.json and site-data.schema.json against pages
that actually shipped.

    python3 tools/validate_schemas.py
    PUBLISHED_SITE=../wildlife-detections python3 tools/validate_schemas.py

Requires jsonschema. Without it, this reports that it could not check rather
than passing silently.
"""
from __future__ import annotations

import glob
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
CONTRACTS = ROOT / "contracts"


def main() -> int:
    try:
        import jsonschema
    except ImportError:
        print("   jsonschema not installed; cannot verify.")
        print("   pip install jsonschema, then re-run. Not treating this as a pass.")
        return 1

    failures = 0

    for path in sorted(CONTRACTS.glob("*.schema.json")):
        try:
            jsonschema.Draft202012Validator.check_schema(json.loads(path.read_text()))
            print(f"   {path.name}: valid")
        except Exception as exc:
            print(f"   {path.name}: INVALID: {exc}")
            failures += 1

    # The registry example must satisfy the registry schema, or the worked
    # example teaches a shape the schema refuses.
    failures += _check(
        jsonschema,
        CONTRACTS / "feeds.schema.json",
        [CONTRACTS / "feeds.example.json"],
    )

    site = os.environ.get("PUBLISHED_SITE")
    if not site:
        print("   PUBLISHED_SITE not set; skipping checks against published data.")
        return failures

    site_root = Path(site)
    failures += _check(
        jsonschema,
        CONTRACTS / "report.schema.json",
        [Path(p) for p in sorted(glob.glob(str(site_root / "reports/*/report.json")))],
    )
    failures += _check(
        jsonschema,
        CONTRACTS / "site-data.schema.json",
        [site_root / "site-data.json"],
    )
    return failures


def _check(jsonschema, schema_path: Path, docs: list[Path]) -> int:
    docs = [d for d in docs if d.exists()]
    if not docs:
        print(f"   {schema_path.name}: no documents to check against")
        return 0
    validator = jsonschema.Draft202012Validator(json.loads(schema_path.read_text()))
    bad = 0
    for doc in docs:
        errors = list(validator.iter_errors(json.loads(doc.read_text())))
        if errors:
            bad += 1
            print(f"   {schema_path.name} vs {doc}: {len(errors)} error(s)")
            for e in errors[:3]:
                print(f"       {list(e.path)}: {e.message[:110]}")
    print(f"   {schema_path.name}: {len(docs)} document(s), {bad} failing")
    return bad


if __name__ == "__main__":
    raise SystemExit(main())
