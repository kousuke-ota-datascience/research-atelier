"""Deterministic persistence for append-only semantic Review cycles."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
import re
from typing import Any, Mapping

from research_atelier.validation.schema_validator import validate_data

REVIEW_SCHEMA_VERSION = "1.0.0"
REVIEW_FILENAME_RE = re.compile(r"^review-([0-9]{6})\.json$")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
EXPECTED_ARTIFACTS = ("00_context", "10_evidence", "20_synthesis", "30_analysis")
EXPECTED_TRANSITIONS = (
    ("source_evidence_note_to_10_evidence", "10_evidence"),
    ("10_evidence_to_20_synthesis", "20_synthesis"),
    ("20_synthesis_plus_00_context_to_30_analysis", "30_analysis"),
)


class ReviewPersistenceError(ValueError):
    """Raised when Review persistence would violate the canonical contract."""


@dataclass(frozen=True)
class PreparedReviewCycle:
    investigation_id: str
    review_seq: int
    target_commit_sha: str
    artifact_blob_shas: Mapping[str, str]


def _require_sha(value: Any, *, field: str) -> str:
    if not isinstance(value, str) or SHA_RE.fullmatch(value) is None:
        raise ReviewPersistenceError(f"{field} must be a lowercase 40-hex Git SHA")
    return value


def _normalize_blob_shas(values: Mapping[str, Any]) -> dict[str, str]:
    if not isinstance(values, Mapping):
        raise ReviewPersistenceError("artifact_blob_shas must be an object")
    if set(values) != set(EXPECTED_ARTIFACTS):
        raise ReviewPersistenceError(
            f"artifact_blob_shas must contain exactly {EXPECTED_ARTIFACTS}"
        )
    return {
        artifact: _require_sha(values[artifact], field=f"artifact_blob_shas.{artifact}")
        for artifact in EXPECTED_ARTIFACTS
    }


def prepare_review_cycle(
    investigation_id: str,
    *,
    review_dir: str | Path,
    schema_path: str | Path,
    target_commit_sha: str,
    artifact_blob_shas: Mapping[str, Any],
) -> PreparedReviewCycle:
    """Freeze a target snapshot and allocate the next per-Investigation Review Seq.

    Existing history must already be a valid contiguous append-only sequence.
    """
    from .review_state import load_review_history

    review_dir = Path(review_dir)
    history = load_review_history(
        investigation_id,
        review_dir=review_dir,
        schema_path=schema_path,
    )
    if history.issues:
        raise ReviewPersistenceError(
            "cannot allocate Review Seq from invalid history: " + "; ".join(history.issues)
        )
    seqs = [int(record["review_seq"]) for record in history.records]
    return PreparedReviewCycle(
        investigation_id=investigation_id,
        review_seq=(seqs[-1] + 1 if seqs else 1),
        target_commit_sha=_require_sha(target_commit_sha, field="target_commit_sha"),
        artifact_blob_shas=_normalize_blob_shas(artifact_blob_shas),
    )


def _normalize_transition(
    transition_name: str,
    artifact: str,
    body: Mapping[str, Any],
    *,
    finding_start: int,
    target_blob_sha: str,
) -> tuple[dict[str, Any], int]:
    if not isinstance(body, Mapping):
        raise ReviewPersistenceError(f"{transition_name} body must be an object")
    assessment = body.get("assessment")
    if not isinstance(assessment, str) or not assessment.strip():
        raise ReviewPersistenceError(f"{transition_name}.assessment must be non-empty")
    findings = body.get("findings", [])
    if not isinstance(findings, list):
        raise ReviewPersistenceError(f"{transition_name}.findings must be an array")

    normalized_findings: list[dict[str, Any]] = []
    next_index = finding_start
    for finding in findings:
        if not isinstance(finding, Mapping):
            raise ReviewPersistenceError(f"{transition_name}.findings entries must be objects")
        item = dict(finding)
        item.pop("finding_id", None)
        item["finding_id"] = f"F{next_index:03d}"
        normalized_findings.append(item)
        next_index += 1

    return (
        {
            "transition": transition_name,
            "target_artifact": artifact,
            "target_blob_sha": target_blob_sha,
            "assessment": assessment.strip(),
            "findings": normalized_findings,
        },
        next_index,
    )


def build_review_record(
    prepared: PreparedReviewCycle,
    *,
    reviewed_at: str,
    transition_bodies: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    """Build one complete cycle; verdict and local Finding IDs are deterministic."""
    try:
        datetime.fromisoformat(reviewed_at.replace("Z", "+00:00"))
    except (AttributeError, ValueError) as exc:
        raise ReviewPersistenceError("reviewed_at must be ISO-8601 date-time") from exc

    expected_names = {name for name, _ in EXPECTED_TRANSITIONS}
    if set(transition_bodies) != expected_names:
        raise ReviewPersistenceError(
            "transition_bodies must contain exactly "
            + str(tuple(name for name, _ in EXPECTED_TRANSITIONS))
        )

    transitions: list[dict[str, Any]] = []
    next_finding = 1
    for transition_name, artifact in EXPECTED_TRANSITIONS:
        normalized, next_finding = _normalize_transition(
            transition_name,
            artifact,
            transition_bodies[transition_name],
            finding_start=next_finding,
            target_blob_sha=prepared.artifact_blob_shas[artifact],
        )
        transitions.append(normalized)

    verdict = "FINDINGS" if any(t["findings"] for t in transitions) else "PASS"
    return {
        "schema_version": REVIEW_SCHEMA_VERSION,
        "report_type": "semantic_review",
        "investigation_id": prepared.investigation_id,
        "review_seq": prepared.review_seq,
        "target": {
            "commit_sha": prepared.target_commit_sha,
            "artifact_blob_shas": dict(prepared.artifact_blob_shas),
        },
        "reviewed_at": reviewed_at,
        "transitions": transitions,
        "verdict": verdict,
    }


def save_review_cycle(
    prepared: PreparedReviewCycle,
    *,
    reviewed_at: str,
    transition_bodies: Mapping[str, Mapping[str, Any]],
    current_target_commit_sha: str,
    current_artifact_blob_shas: Mapping[str, Any],
    review_dir: str | Path,
    schema_path: str | Path,
) -> Path:
    """Validate and append one Review cycle, failing if target changed after prepare."""
    current_commit = _require_sha(current_target_commit_sha, field="current_target_commit_sha")
    current_blobs = _normalize_blob_shas(current_artifact_blob_shas)
    if current_commit != prepared.target_commit_sha or current_blobs != dict(prepared.artifact_blob_shas):
        raise ReviewPersistenceError("review target changed after prepare; re-prepare required")

    from .review_state import load_review_history

    review_dir = Path(review_dir)
    history = load_review_history(
        prepared.investigation_id,
        review_dir=review_dir,
        schema_path=schema_path,
    )
    if history.issues:
        raise ReviewPersistenceError(
            "cannot save into invalid Review history: " + "; ".join(history.issues)
        )
    seqs = [int(record["review_seq"]) for record in history.records]
    expected_next = seqs[-1] + 1 if seqs else 1
    if prepared.review_seq != expected_next:
        raise ReviewPersistenceError(
            f"prepared Review Seq is stale: prepared={prepared.review_seq}, next={expected_next}"
        )

    record = build_review_record(
        prepared,
        reviewed_at=reviewed_at,
        transition_bodies=transition_bodies,
    )
    validation = validate_data(record, schema_path, artifact="review_cycle")
    if not validation.ok:
        detail = "; ".join(f"{e.json_path}: {e.message}" for e in validation.errors)
        raise ReviewPersistenceError(f"Review schema validation failed: {detail}")

    review_dir.mkdir(parents=True, exist_ok=True)
    path = review_dir / f"review-{prepared.review_seq:06d}.json"
    try:
        with path.open("x", encoding="utf-8") as f:
            json.dump(record, f, ensure_ascii=False, indent=2)
            f.write("\n")
    except FileExistsError as exc:
        raise ReviewPersistenceError(f"append-only Review target already exists: {path.name}") from exc
    return path
