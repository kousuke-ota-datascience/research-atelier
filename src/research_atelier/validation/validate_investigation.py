"""Validate one Research Atelier Investigation deterministically."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import re
import sys
from typing import Any, Mapping

from .reference_validator import ParsedArtifact, validate_references
from .schema_validator import ValidationIssue, validate_artifact


REPO_ROOT = Path(__file__).resolve().parents[3]
LEGACY_SCHEMA_ROOT = REPO_ROOT / "schemas" / "v1"
CANONICAL_SCHEMA_ROOT = REPO_ROOT / "schemas" / "v2"
DEFAULT_SCHEMA_ROOT = CANONICAL_SCHEMA_ROOT
DEFAULT_INVESTIGATION_ROOT = REPO_ROOT / "investigations"

ARTIFACTS = {
    "00": ("00_context.json", "00_context.schema.json"),
    "10": ("10_evidence.json", "10_evidence.schema.json"),
    "20": ("20_synthesis.json", "20_synthesis.schema.json"),
    "30": ("30_analysis.json", "30_analysis.schema.json"),
}
ARTIFACT_ORDER = ("00", "10", "20", "30")
LEGACY_INVESTIGATION_RE = re.compile(r"^RQ-[0-9]{4}-v(?!000)[0-9]{3}$")
CANONICAL_INVESTIGATION_RE = re.compile(r"^INV-(?!000000)[0-9]{6}$")


def validate_new_freeze_context(data: Mapping[str, Any]) -> tuple[ValidationIssue, ...]:
    """Validate operation-time invariants for creating a new frozen v2 Context.

    This is intentionally separate from schema validation. The v2 schema keeps
    question_type=null valid so historical artifacts remain readable/validatable.
    New freeze operations must call this gate before 00_context is committed.
    """
    issues: list[ValidationIssue] = []

    if data.get("context_state") != "frozen":
        issues.append(
            ValidationIssue(
                "V-FREEZE-001",
                "00",
                "$.context_state",
                "new freeze candidate must have context_state=frozen",
                "validate_new_freeze_context",
                "frozen",
                data.get("context_state"),
            )
        )

    if data.get("question_type") is None:
        issues.append(
            ValidationIssue(
                "V-FREEZE-002",
                "00",
                "$.question_type",
                "Question Type must be committed before a new Investigation Context can be frozen",
                "validate_new_freeze_context",
                "non-null Question Type",
                None,
            )
        )

    return tuple(sorted(issues, key=ValidationIssue.sort_key))


def validate_investigation(
    investigation_id: str,
    *,
    through: str = "30",
    investigation_root: str | Path = DEFAULT_INVESTIGATION_ROOT,
    schema_root: str | Path | None = None,
    new_freeze: bool = False,
) -> dict[str, Any]:
    if through not in ARTIFACT_ORDER:
        raise ValueError(f"through must be one of {ARTIFACT_ORDER}: {through!r}")

    legacy_id = LEGACY_INVESTIGATION_RE.fullmatch(investigation_id) is not None
    canonical_id = CANONICAL_INVESTIGATION_RE.fullmatch(investigation_id) is not None
    if not legacy_id and not canonical_id:
        issue = ValidationIssue(
            "V-INV-000",
            "investigation",
            "$",
            "invalid investigation_id format",
            "validate_investigation",
            "INV-NNNNNN or RQ-NNNN-vVVV (legacy)",
            investigation_id,
        )
        return {
            "investigation_id": investigation_id,
            "through": through,
            "result": "FAIL",
            "errors": [asdict(issue)],
            "internal_errors": [],
        }

    investigation_root = Path(investigation_root)
    if schema_root is None:
        schema_root = LEGACY_SCHEMA_ROOT if legacy_id else CANONICAL_SCHEMA_ROOT
    schema_root = Path(schema_root)
    investigation_dir = investigation_root / investigation_id
    required = ARTIFACT_ORDER[: ARTIFACT_ORDER.index(through) + 1]

    issues: list[ValidationIssue] = []
    parsed: dict[str, ParsedArtifact] = {}
    internal_errors: list[str] = []

    for artifact in required:
        filename, schema_name = ARTIFACTS[artifact]
        path = investigation_dir / filename
        schema_path = schema_root / schema_name
        result = validate_artifact(path, schema_path, artifact=artifact)

        for issue in result.errors:
            if issue.rule_id == "V-SCHEMA-000":
                internal_errors.append(
                    f"{artifact}: {issue.message}"
                )
            else:
                issues.append(issue)

        if result.ok and isinstance(result.data, dict):
            parsed[artifact] = ParsedArtifact(artifact, path, result.data)

    if new_freeze:
        context = parsed.get("00")
        if context is not None:
            issues.extend(validate_new_freeze_context(context.data))

    issues.extend(validate_references(investigation_id, parsed))
    issues = sorted(issues, key=ValidationIssue.sort_key)
    internal_errors = sorted(set(internal_errors))

    if internal_errors:
        result_name = "ERROR"
    elif issues:
        result_name = "FAIL"
    else:
        result_name = "PASS"

    return {
        "investigation_id": investigation_id,
        "through": through,
        "new_freeze": new_freeze,
        "result": result_name,
        "errors": [asdict(issue) for issue in issues],
        "internal_errors": internal_errors,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("investigation_id", help="INV-NNNNNN (canonical) or RQ-NNNN-vVVV (legacy)")
    parser.add_argument(
        "--through",
        choices=ARTIFACT_ORDER,
        default="30",
        help="validate the canonical chain through this artifact (default: 30)",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=DEFAULT_INVESTIGATION_ROOT,
        help="root directory containing Investigation directories",
    )
    parser.add_argument(
        "--schema-root",
        type=Path,
        default=None,
        help="schema directory override; default auto-selects v2 for INV IDs and v1 for legacy IDs",
    )
    parser.add_argument(
        "--new-freeze",
        action="store_true",
        help=(
            "apply operation-time freeze invariants; use only when creating a new "
            "frozen v2 00_context, not when validating historical artifacts"
        ),
    )
    args = parser.parse_args(argv)

    result = validate_investigation(
        args.investigation_id,
        through=args.through,
        investigation_root=args.root,
        schema_root=args.schema_root,
        new_freeze=args.new_freeze,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return {"PASS": 0, "FAIL": 1, "ERROR": 2}[result["result"]]


if __name__ == "__main__":
    sys.exit(main())
