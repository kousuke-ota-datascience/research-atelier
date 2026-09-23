"""Canonical Review -> successor Investigation handoff contract.

A valid handoff is a separate append-only artifact from the Review Cycle itself.
This keeps the source Review verdict immutable while recording that repair
responsibility moved to a successor Investigation after Workflow 00 validated
the allocation and RQ binding.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from research_atelier.reviewing.review_state import ensure_normalized_review
from research_atelier.validation.schema_validator import validate_data


HANDOFF_MODE = "new_investigation"
HANDOFF_REPORT_TYPE = "review_repair_handoff"


class ReviewHandoffError(ValueError):
    """Raised when a Review handoff artifact is malformed or unsafe."""


@dataclass(frozen=True)
class ReviewHandoffPlan:
    outcome: str  # CREATE | NOOP | BLOCKED
    record: Mapping[str, Any] | None
    canonical_path: str
    issues: tuple[str, ...]


@dataclass(frozen=True)
class ReviewHandoffPreflight:
    outcome: str  # PROCEED | REUSE | BLOCKED
    successor_investigation_id: str | None
    canonical_path: str
    issues: tuple[str, ...]


def review_handoff_filename(review_seq: int) -> str:
    if not isinstance(review_seq, int) or review_seq < 1:
        raise ReviewHandoffError("review_seq must be an integer >= 1")
    return f"handoff-{review_seq:06d}.json"


def review_handoff_path(investigation_id: str, review_seq: int) -> str:
    if not isinstance(investigation_id, str) or not investigation_id:
        raise ReviewHandoffError("investigation_id must be a non-empty string")
    return (
        f"investigations/{investigation_id}/reviews/"
        f"{review_handoff_filename(review_seq)}"
    )


def _all_findings(review: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    normalized = ensure_normalized_review(review)
    layers = normalized.get("layers")
    if not isinstance(layers, Mapping):
        raise ReviewHandoffError("normalized Review layers missing")
    findings: list[Mapping[str, Any]] = []
    for layer in ("00_context", "10_evidence", "20_synthesis", "30_analysis"):
        record = layers.get(layer)
        if not isinstance(record, Mapping):
            raise ReviewHandoffError(f"normalized Review layer missing: {layer}")
        values = record.get("findings", [])
        if not isinstance(values, list):
            raise ReviewHandoffError(f"{layer}.findings must be an array")
        for finding in values:
            if not isinstance(finding, Mapping):
                raise ReviewHandoffError(f"{layer}.findings entries must be objects")
            findings.append(finding)
    return findings


def _review_identity(review: Mapping[str, Any]) -> tuple[str, int]:
    normalized = ensure_normalized_review(review)
    investigation_id = normalized.get("investigation_id")
    review_seq = normalized.get("review_seq")
    if not isinstance(investigation_id, str) or not investigation_id:
        raise ReviewHandoffError("source Review investigation_id missing")
    if not isinstance(review_seq, int) or review_seq < 1:
        raise ReviewHandoffError("source Review review_seq invalid")
    return investigation_id, review_seq


def _validate_datetime(value: Any, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ReviewHandoffError(f"{field} must be a non-empty ISO-8601 date-time")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ReviewHandoffError(f"{field} must be ISO-8601 date-time") from exc
    if parsed.tzinfo is None:
        raise ReviewHandoffError(f"{field} must include a timezone")
    return value


def _candidate_record(
    *,
    source_review: Mapping[str, Any],
    source_rq_id: str,
    allocation_decision: Mapping[str, Any],
    successor: Mapping[str, Any],
    handoff_at: str,
) -> tuple[dict[str, Any] | None, tuple[str, ...]]:
    issues: list[str] = []
    normalized = ensure_normalized_review(source_review)
    source_investigation_id, source_review_seq = _review_identity(normalized)

    if normalized.get("verdict") != "FINDINGS":
        issues.append("handoff_requires_findings_review")

    try:
        findings = _all_findings(normalized)
    except ReviewHandoffError as exc:
        issues.append(f"invalid_source_review:{exc}")
        findings = []

    finding_ids: list[str] = []
    new_investigation_findings = 0
    for finding in findings:
        finding_id = finding.get("finding_id")
        if not isinstance(finding_id, str) or not finding_id:
            issues.append("source_finding_id_missing")
            continue
        finding_ids.append(finding_id)
        repair = finding.get("repair_direction")
        if not isinstance(repair, Mapping):
            issues.append(f"source_finding_repair_direction_missing:{finding_id}")
            continue
        if repair.get("mode") == HANDOFF_MODE:
            new_investigation_findings += 1
    if not findings:
        issues.append("handoff_requires_findings")
    if new_investigation_findings == 0:
        issues.append("handoff_requires_new_investigation_finding")

    if not isinstance(source_rq_id, str) or not source_rq_id:
        issues.append("source_rq_id_missing")

    decision = allocation_decision.get("decision")
    if decision != "allocate_new":
        issues.append("versioning_decision_not_allocate_new")
    if allocation_decision.get("new_investigation_allocated") is not True:
        issues.append("new_investigation_not_allocated")
    if allocation_decision.get("selected_existing_investigation") != source_investigation_id:
        issues.append("allocation_source_investigation_mismatch")
    allocation_issues = allocation_decision.get("issues", [])
    if not isinstance(allocation_issues, Sequence) or isinstance(
        allocation_issues, (str, bytes)
    ):
        issues.append("allocation_issues_invalid")
        allocation_issues = []
    if list(allocation_issues):
        issues.append("allocation_decision_has_issues")

    successor_exists = successor.get("exists")
    successor_investigation_id = successor.get("investigation_id")
    rq_ids = successor.get("rq_ids")
    if successor_exists is not True:
        issues.append("successor_investigation_not_persisted")
    if not isinstance(successor_investigation_id, str) or not successor_investigation_id:
        issues.append("successor_investigation_id_missing")
    elif successor_investigation_id == source_investigation_id:
        issues.append("successor_matches_source_investigation")
    if not isinstance(rq_ids, Sequence) or isinstance(rq_ids, (str, bytes)):
        issues.append("successor_rq_binding_invalid")
        actual_rq_ids: list[str] = []
    else:
        actual_rq_ids = [str(item) for item in rq_ids]
        if len(actual_rq_ids) != 1 or actual_rq_ids[0] != source_rq_id:
            issues.append("successor_rq_binding_not_exact")

    try:
        handoff_at = _validate_datetime(handoff_at, field="handoff_at")
    except ReviewHandoffError as exc:
        issues.append(str(exc))

    reason_codes = allocation_decision.get("reason_codes", [])
    if not isinstance(reason_codes, Sequence) or isinstance(reason_codes, (str, bytes)):
        issues.append("allocation_reason_codes_invalid")
        reason_codes = []
    elif not list(reason_codes):
        issues.append("allocation_reason_codes_missing")
    semantic_differences = allocation_decision.get("semantic_differences", [])
    if not isinstance(semantic_differences, Sequence) or isinstance(
        semantic_differences, (str, bytes)
    ):
        issues.append("allocation_semantic_differences_invalid")
        semantic_differences = []

    if issues:
        return None, tuple(sorted(set(issues)))

    record = {
        "schema_version": "1.0.0",
        "report_type": HANDOFF_REPORT_TYPE,
        "source_investigation_id": source_investigation_id,
        "source_review_seq": source_review_seq,
        "source_rq_id": source_rq_id,
        "finding_ids": finding_ids,
        "handoff_mode": HANDOFF_MODE,
        "successor_investigation_id": successor_investigation_id,
        "successor_exists": True,
        "successor_rq_binding": {
            "expected_rq_id": source_rq_id,
            "actual_rq_ids": actual_rq_ids,
            "exact": True,
        },
        "versioning_decision": {
            "decision": "allocate_new",
            "selected_existing_investigation": source_investigation_id,
            "new_investigation_allocated": True,
            "semantic_differences": list(semantic_differences),
            "explicit_new_execution_intent": bool(
                allocation_decision.get("explicit_new_execution_intent", False)
            ),
            "reason_codes": [str(item) for item in reason_codes],
        },
        "handoff_at": handoff_at,
    }
    return record, ()


def validate_review_handoff_record(
    record: Mapping[str, Any],
    *,
    source_review: Mapping[str, Any],
    source_rq_id: str | None = None,
) -> tuple[str, ...]:
    """Validate handoff semantics needed by the Review reconciler.

    JSON Schema validation remains a persistence concern; this function verifies
    that the record actually closes the supplied source Review without changing
    its semantic verdict.
    """

    issues: list[str] = []
    normalized = ensure_normalized_review(source_review)
    source_investigation_id, source_review_seq = _review_identity(normalized)
    findings = _all_findings(normalized)
    expected_finding_ids = [str(item.get("finding_id")) for item in findings]

    if normalized.get("verdict") != "FINDINGS":
        issues.append("handoff_requires_findings_review")
    if record.get("report_type") != HANDOFF_REPORT_TYPE:
        issues.append("invalid_handoff_report_type")
    if record.get("source_investigation_id") != source_investigation_id:
        issues.append("handoff_source_investigation_mismatch")
    if record.get("source_review_seq") != source_review_seq:
        issues.append("handoff_source_review_seq_mismatch")
    record_source_rq_id = record.get("source_rq_id")
    if not isinstance(record_source_rq_id, str) or not record_source_rq_id:
        issues.append("handoff_source_rq_id_missing")
    if source_rq_id is not None and record_source_rq_id != source_rq_id:
        issues.append("handoff_source_rq_id_mismatch")
    if record.get("handoff_mode") != HANDOFF_MODE:
        issues.append("invalid_handoff_mode")
    if record.get("successor_exists") is not True:
        issues.append("successor_investigation_not_persisted")

    successor_id = record.get("successor_investigation_id")
    if not isinstance(successor_id, str) or not successor_id:
        issues.append("successor_investigation_id_missing")
    elif successor_id == source_investigation_id:
        issues.append("successor_matches_source_investigation")

    finding_ids = record.get("finding_ids")
    if not isinstance(finding_ids, list) or finding_ids != expected_finding_ids:
        issues.append("handoff_finding_coverage_mismatch")
    if not any(
        isinstance(finding.get("repair_direction"), Mapping)
        and finding["repair_direction"].get("mode") == HANDOFF_MODE
        for finding in findings
    ):
        issues.append("handoff_requires_new_investigation_finding")

    binding = record.get("successor_rq_binding")
    if not isinstance(binding, Mapping):
        issues.append("successor_rq_binding_missing")
    else:
        expected_rq_id = binding.get("expected_rq_id")
        actual_rq_ids = binding.get("actual_rq_ids")
        if expected_rq_id != record_source_rq_id:
            issues.append("handoff_expected_rq_mismatch")
        if binding.get("exact") is not True:
            issues.append("successor_rq_binding_not_exact")
        if (
            not isinstance(expected_rq_id, str)
            or not isinstance(actual_rq_ids, list)
            or actual_rq_ids != [expected_rq_id]
        ):
            issues.append("successor_rq_binding_not_exact")

    versioning = record.get("versioning_decision")
    if not isinstance(versioning, Mapping):
        issues.append("versioning_decision_missing")
    else:
        if versioning.get("decision") != "allocate_new":
            issues.append("versioning_decision_not_allocate_new")
        if versioning.get("new_investigation_allocated") is not True:
            issues.append("new_investigation_not_allocated")
        if versioning.get("selected_existing_investigation") != source_investigation_id:
            issues.append("allocation_source_investigation_mismatch")

    try:
        _validate_datetime(record.get("handoff_at"), field="handoff_at")
    except ReviewHandoffError as exc:
        issues.append(str(exc))

    return tuple(sorted(set(issues)))


def preflight_review_handoff(
    *,
    source_review: Mapping[str, Any],
    source_rq_id: str,
    existing_handoff: Mapping[str, Any] | None,
) -> ReviewHandoffPreflight:
    """Resolve an already-completed handoff before any successor allocation.

    Workflow 00 must call this before running a new allocation/numbering step.
    A valid existing record is an idempotency barrier: reuse its successor and
    do not create another Investigation or handoff record for the same Review.
    """

    source_investigation_id, source_review_seq = _review_identity(source_review)
    canonical_path = review_handoff_path(source_investigation_id, source_review_seq)
    if existing_handoff is None:
        return ReviewHandoffPreflight("PROCEED", None, canonical_path, ())

    issues = validate_review_handoff_record(
        existing_handoff,
        source_review=source_review,
        source_rq_id=source_rq_id,
    )
    if issues:
        return ReviewHandoffPreflight("BLOCKED", None, canonical_path, issues)

    successor_id = existing_handoff.get("successor_investigation_id")
    if not isinstance(successor_id, str) or not successor_id:
        return ReviewHandoffPreflight(
            "BLOCKED",
            None,
            canonical_path,
            ("successor_investigation_id_missing",),
        )
    return ReviewHandoffPreflight("REUSE", successor_id, canonical_path, ())


def plan_review_handoff(
    *,
    source_review: Mapping[str, Any],
    source_rq_id: str,
    allocation_decision: Mapping[str, Any],
    successor: Mapping[str, Any],
    handoff_at: str,
    existing_handoff: Mapping[str, Any] | None = None,
) -> ReviewHandoffPlan:
    """Plan one append-only handoff artifact with idempotent rerun semantics."""

    source_investigation_id, source_review_seq = _review_identity(source_review)
    canonical_path = review_handoff_path(source_investigation_id, source_review_seq)
    candidate, issues = _candidate_record(
        source_review=source_review,
        source_rq_id=source_rq_id,
        allocation_decision=allocation_decision,
        successor=successor,
        handoff_at=handoff_at,
    )
    if issues or candidate is None:
        return ReviewHandoffPlan("BLOCKED", None, canonical_path, issues)

    if existing_handoff is None:
        return ReviewHandoffPlan("CREATE", candidate, canonical_path, ())

    existing_issues = validate_review_handoff_record(
        existing_handoff,
        source_review=source_review,
    )
    if existing_issues:
        return ReviewHandoffPlan(
            "BLOCKED",
            None,
            canonical_path,
            existing_issues,
        )

    candidate_compare = dict(candidate)
    existing_compare = dict(existing_handoff)
    candidate_compare.pop("handoff_at", None)
    existing_compare.pop("handoff_at", None)
    if existing_compare == candidate_compare:
        return ReviewHandoffPlan(
            "NOOP",
            dict(existing_handoff),
            canonical_path,
            (),
        )
    return ReviewHandoffPlan(
        "BLOCKED",
        None,
        canonical_path,
        ("conflicting_existing_review_handoff",),
    )


def load_review_handoff(
    path: str | Path,
    *,
    schema_path: str | Path,
    source_review: Mapping[str, Any],
) -> Mapping[str, Any]:
    """Load and validate one canonical handoff artifact."""

    path = Path(path)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ReviewHandoffError(f"malformed handoff JSON: {path}: {exc}") from exc
    if not isinstance(data, Mapping):
        raise ReviewHandoffError("handoff JSON must be an object")

    validation = validate_data(data, Path(schema_path), artifact=path.name)
    if not validation.ok:
        detail = "; ".join(
            f"{issue.json_path}:{issue.message}" for issue in validation.errors
        )
        raise ReviewHandoffError(f"handoff schema validation failed: {detail}")

    issues = validate_review_handoff_record(data, source_review=source_review)
    if issues:
        raise ReviewHandoffError("; ".join(issues))
    return dict(data)
