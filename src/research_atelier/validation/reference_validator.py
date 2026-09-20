"""Deterministic cross-artifact identity and lineage validation."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any, Mapping

from .schema_validator import ValidationIssue


LEGACY_INVESTIGATION_RE = re.compile(r"^(RQ-[0-9]{4})-v(?!000)[0-9]{3}$")
CANONICAL_INVESTIGATION_RE = re.compile(r"^INV-(?!000000)[0-9]{6}$")


@dataclass(frozen=True)
class ParsedArtifact:
    artifact: str
    path: Path
    data: Mapping[str, Any]


def _issue(
    rule_id: str,
    artifact: str,
    json_path: str,
    message: str,
    *,
    expected: Any | None = None,
    actual: Any | None = None,
) -> ValidationIssue:
    return ValidationIssue(
        rule_id,
        artifact,
        json_path,
        message,
        "reference_validator",
        expected,
        actual,
    )


def _duplicates(values: list[str]) -> set[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return duplicates


def _string_ids(items: Any, key: str) -> list[str]:
    if not isinstance(items, list):
        return []
    return [
        item[key]
        for item in items
        if isinstance(item, dict) and isinstance(item.get(key), str)
    ]


def validate_references(
    investigation_id: str,
    artifacts: Mapping[str, ParsedArtifact],
) -> tuple[ValidationIssue, ...]:
    """Validate deterministic identities and references among parsed artifacts.

    This validator intentionally does not contact Notion or judge semantic truth.
    External Source / Evidence Note existence is an operational concern; the
    schema validates that provenance references are structurally present.
    """
    errors: list[ValidationIssue] = []

    legacy_match = LEGACY_INVESTIGATION_RE.fullmatch(investigation_id)
    canonical_match = CANONICAL_INVESTIGATION_RE.fullmatch(investigation_id)
    if legacy_match is None and canonical_match is None:
        return (
            _issue(
                "V-INV-000",
                "investigation",
                "$",
                "invalid investigation_id format",
                expected="INV-NNNNNN or RQ-NNNN-vVVV (legacy)",
                actual=investigation_id,
            ),
        )

    expected_rq_id = legacy_match.group(1) if legacy_match is not None else None
    canonical_rq_id: str | None = None

    for artifact, parsed in artifacts.items():
        actual_investigation = parsed.data.get("investigation_id")
        if actual_investigation != investigation_id:
            errors.append(
                _issue(
                    "V-INV-001",
                    artifact,
                    "$.investigation_id",
                    "investigation_id mismatch",
                    expected=investigation_id,
                    actual=actual_investigation,
                )
            )
        actual_rq = parsed.data.get("rq_id")
        if expected_rq_id is not None:
            if actual_rq != expected_rq_id:
                errors.append(
                    _issue(
                        "V-RQ-001",
                        artifact,
                        "$.rq_id",
                        "rq_id does not match legacy investigation_id prefix",
                        expected=expected_rq_id,
                        actual=actual_rq,
                    )
                )
        elif isinstance(actual_rq, str):
            if canonical_rq_id is None:
                canonical_rq_id = actual_rq
            elif actual_rq != canonical_rq_id:
                errors.append(
                    _issue(
                        "V-RQ-001",
                        artifact,
                        "$.rq_id",
                        "rq_id mismatch across Investigation artifact chain",
                        expected=canonical_rq_id,
                        actual=actual_rq,
                    )
                )

    evidence_ids: set[str] = set()
    knowledge_ids: set[str] = set()

    evidence = artifacts.get("10")
    if evidence is not None:
        items = evidence.data.get("evidence_items", [])
        ids = _string_ids(items, "evidence_id")
        evidence_ids.update(ids)
        for duplicate in sorted(_duplicates(ids)):
            errors.append(
                _issue(
                    "V-ID-001",
                    "10",
                    "$.evidence_items",
                    f"duplicate evidence_id: {duplicate}",
                )
            )

    synthesis = artifacts.get("20")
    if synthesis is not None:
        knowledge_units = synthesis.data.get("knowledge_units", [])
        relations = synthesis.data.get("relations", [])
        uncertainties = synthesis.data.get("uncertainties", [])

        knowledge_values = _string_ids(knowledge_units, "knowledge_unit_id")
        relation_values = _string_ids(relations, "relation_id")
        uncertainty_values = _string_ids(uncertainties, "uncertainty_id")
        knowledge_ids.update(knowledge_values)

        for path, label, values in (
            ("$.knowledge_units", "knowledge_unit_id", knowledge_values),
            ("$.relations", "relation_id", relation_values),
            ("$.uncertainties", "uncertainty_id", uncertainty_values),
        ):
            for duplicate in sorted(_duplicates(values)):
                errors.append(
                    _issue(
                        "V-ID-001",
                        "20",
                        path,
                        f"duplicate {label}: {duplicate}",
                    )
                )

        if evidence is not None:
            for idx, unit in enumerate(knowledge_units):
                if not isinstance(unit, dict):
                    continue
                for ref in unit.get("evidence_refs", []):
                    if isinstance(ref, str) and ref not in evidence_ids:
                        errors.append(
                            _issue(
                                "V-REF-001",
                                "20",
                                f"$.knowledge_units[{idx}].evidence_refs",
                                f"dangling evidence reference: {ref}",
                            )
                        )

            for collection_name, values in (
                ("relations", relations),
                ("uncertainties", uncertainties),
            ):
                for idx, item in enumerate(values):
                    if not isinstance(item, dict):
                        continue
                    for ref in item.get("evidence_refs", []):
                        if isinstance(ref, str) and ref not in evidence_ids:
                            errors.append(
                                _issue(
                                    "V-REF-001",
                                    "20",
                                    f"$.{collection_name}[{idx}].evidence_refs",
                                    f"dangling evidence reference: {ref}",
                                )
                            )

        for collection_name, values in (
            ("relations", relations),
            ("uncertainties", uncertainties),
        ):
            for idx, item in enumerate(values):
                if not isinstance(item, dict):
                    continue
                for ref in item.get("knowledge_unit_refs", []):
                    if isinstance(ref, str) and ref not in knowledge_ids:
                        errors.append(
                            _issue(
                                "V-REF-002",
                                "20",
                                f"$.{collection_name}[{idx}].knowledge_unit_refs",
                                f"dangling knowledge unit reference: {ref}",
                            )
                        )

    analysis = artifacts.get("30")
    if analysis is not None:
        judgments = analysis.data.get("judgments", [])
        judgment_values = _string_ids(judgments, "judgment_id")
        for duplicate in sorted(_duplicates(judgment_values)):
            errors.append(
                _issue(
                    "V-ID-001",
                    "30",
                    "$.judgments",
                    f"duplicate judgment_id: {duplicate}",
                )
            )

        if synthesis is not None:
            ref_groups: list[tuple[str, Any]] = [
                ("$.working_answer.knowledge_unit_refs", analysis.data.get("working_answer", {})),
            ]
            for name in ("judgments", "limitations", "alternative_interpretations"):
                for idx, item in enumerate(analysis.data.get(name, [])):
                    ref_groups.append((f"$.{name}[{idx}].knowledge_unit_refs", item))

            for path, item in ref_groups:
                if not isinstance(item, dict):
                    continue
                for ref in item.get("knowledge_unit_refs", []):
                    if isinstance(ref, str) and ref not in knowledge_ids:
                        errors.append(
                            _issue(
                                "V-REF-002",
                                "30",
                                path,
                                f"dangling knowledge unit reference: {ref}",
                            )
                        )

    context = artifacts.get("00")
    if context is not None and analysis is not None:
        context_type = context.data.get("question_type")
        analysis_type = analysis.data.get("question_type")
        if context_type is not None and context_type != analysis_type:
            errors.append(
                _issue(
                    "V-CONTEXT-001",
                    "30",
                    "$.question_type",
                    "question_type differs from frozen context",
                    expected=context_type,
                    actual=analysis_type,
                )
            )

    return tuple(sorted(errors, key=ValidationIssue.sort_key))
