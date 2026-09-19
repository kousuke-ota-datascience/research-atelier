"""CLI entrypoint for deterministic validation of one lore entry."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys

from .reference_validator import ParsedArtifact, validate_references
from .schema_validator import ValidationIssue, validate_artifact
from .taxonomy_validator import load_taxonomy_catalog, validate_taxonomy

ARTICLE_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_ROOT = ARTICLE_ROOT / "docs/10_each_lore/0000_tutorial/schemas"
CANONICAL_ROOT = ARTICLE_ROOT / "docs/10_each_lore"
ARTIFACTS = {
    "00": ("00_sources", "00_sources.schema.json"),
    "10": ("10_contents", "10_contents.schema.json"),
    "20": ("20_analysis", "20_analysis.schema.json"),
}
ARTIFACT_ORDER = ("00", "10", "20")


def _resolve_artifact(entry_id: str, suffix: str) -> Path:
    matches = sorted(CANONICAL_ROOT.glob(f"*/{entry_id}_{suffix}.json"))
    matches = [p for p in matches if "0000_tutorial" not in p.parts]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        raise RuntimeError(f"ambiguous artifact path for {entry_id}_{suffix}.json: {matches}")
    dirs = sorted(p for p in CANONICAL_ROOT.glob(f"{entry_id}*") if p.is_dir() and p.name != "0000_tutorial")
    if len(dirs) == 1:
        return dirs[0] / f"{entry_id}_{suffix}.json"
    return CANONICAL_ROOT / entry_id / f"{entry_id}_{suffix}.json"


def validate_entry(entry_id: str, through: str = "20") -> dict:
    if through not in ARTIFACT_ORDER:
        raise ValueError(f"through must be one of {ARTIFACT_ORDER}: {through!r}")

    through_index = ARTIFACT_ORDER.index(through)
    required_artifacts = ARTIFACT_ORDER[: through_index + 1]

    issues: list[ValidationIssue] = []
    parsed: dict[str, ParsedArtifact] = {}
    internal_errors: list[str] = []

    for artifact in required_artifacts:
        suffix, schema_name = ARTIFACTS[artifact]
        try:
            path = _resolve_artifact(entry_id, suffix)
        except RuntimeError as exc:
            internal_errors.append(str(exc))
            continue
        result = validate_artifact(path, SCHEMA_ROOT / schema_name, artifact=artifact)
        issues.extend(result.errors)
        if result.ok and isinstance(result.data, dict):
            parsed[artifact] = ParsedArtifact(artifact, path, result.data)

    issues.extend(validate_references(entry_id, parsed))

    if "20" in parsed:
        try:
            catalog = load_taxonomy_catalog(ARTICLE_ROOT)
            issues.extend(validate_taxonomy(parsed["20"].data, catalog))
        except Exception as exc:
            internal_errors.append(f"taxonomy validation unavailable: {exc}")

    issues = sorted(issues, key=ValidationIssue.sort_key)
    if internal_errors:
        result = "ERROR"
    elif issues:
        result = "FAIL"
    else:
        result = "PASS"
    return {
        "entry_id": entry_id,
        "through": through,
        "result": result,
        "errors": [asdict(x) for x in issues],
        "internal_errors": sorted(internal_errors),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("entry_id", help="four-digit Entry_ID")
    parser.add_argument(
        "--through",
        choices=ARTIFACT_ORDER,
        default="20",
        help="validate the canonical chain through this artifact (default: 20)",
    )
    args = parser.parse_args(argv)
    if not (len(args.entry_id) == 4 and args.entry_id.isdigit()):
        parser.error("entry_id must be four digits")
    result = validate_entry(args.entry_id, through=args.through)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return {"PASS": 0, "FAIL": 1, "ERROR": 2}[result["result"]]


if __name__ == "__main__":
    sys.exit(main())
