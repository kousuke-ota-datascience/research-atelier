"""Validate one canonical Information Source artifact."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import re
import sys
from typing import Any

from .schema_validator import ValidationIssue, validate_artifact


REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_SOURCE_ROOT = REPO_ROOT / "information_sources"
DEFAULT_SCHEMA_PATH = REPO_ROOT / "schemas" / "v2" / "information_source.schema.json"
SOURCE_ID_RE = re.compile(r"^SRC-(?:[0-9]{4}|[0-9]{6})$")


def validate_information_source(
    source_id: str,
    *,
    source_root: str | Path = DEFAULT_SOURCE_ROOT,
    schema_path: str | Path = DEFAULT_SCHEMA_PATH,
) -> dict[str, Any]:
    issues: list[ValidationIssue] = []
    internal_errors: list[str] = []

    if SOURCE_ID_RE.fullmatch(source_id) is None:
        issues.append(
            ValidationIssue(
                "V-SRC-000",
                "information_source",
                "$.source_id",
                "invalid Source ID format",
                "validate_information_source",
                "SRC-NNNN or SRC-NNNNNN",
                source_id,
            )
        )
        return {
            "source_id": source_id,
            "result": "FAIL",
            "errors": [asdict(issue) for issue in issues],
            "internal_errors": [],
        }

    source_path = Path(source_root) / f"{source_id}.json"
    result = validate_artifact(
        source_path,
        schema_path,
        artifact="information_source",
    )
    for issue in result.errors:
        if issue.rule_id == "V-SCHEMA-000":
            internal_errors.append(issue.message)
        else:
            issues.append(issue)

    if result.ok and isinstance(result.data, dict):
        actual_id = result.data.get("source_id")
        if actual_id != source_id:
            issues.append(
                ValidationIssue(
                    "V-SRC-001",
                    "information_source",
                    "$.source_id",
                    "source_id does not match filename",
                    "validate_information_source",
                    source_id,
                    actual_id,
                )
            )

    issues = sorted(issues, key=ValidationIssue.sort_key)
    internal_errors = sorted(set(internal_errors))
    result_name = "ERROR" if internal_errors else ("FAIL" if issues else "PASS")

    return {
        "source_id": source_id,
        "result": result_name,
        "errors": [asdict(issue) for issue in issues],
        "internal_errors": internal_errors,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_id", help="SRC-NNNN (historical) or SRC-NNNNNN (post-cutover)")
    parser.add_argument(
        "--root",
        type=Path,
        default=DEFAULT_SOURCE_ROOT,
        help="root directory containing canonical Information Source JSON",
    )
    parser.add_argument(
        "--schema",
        type=Path,
        default=DEFAULT_SCHEMA_PATH,
        help="Information Source JSON Schema",
    )
    args = parser.parse_args(argv)

    result = validate_information_source(
        args.source_id,
        source_root=args.root,
        schema_path=args.schema,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return {"PASS": 0, "FAIL": 1, "ERROR": 2}[result["result"]]


if __name__ == "__main__":
    sys.exit(main())
