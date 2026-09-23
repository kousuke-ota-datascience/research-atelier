"""Deterministic persistence for append-only semantic Review cycles."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
import os
from pathlib import Path
import re
import tempfile
from typing import Any, Mapping

from research_atelier.validation.schema_validator import validate_data

REVIEW_SCHEMA_VERSION = "1.0.0"
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
EXPECTED_ARTIFACTS = ("00_context", "10_evidence", "20_synthesis", "30_analysis")
LAYER_FILE_PREFIX = {
    "00_context": "review_00",
    "10_evidence": "review_10",
    "20_synthesis": "review_20",
    "30_analysis": "review_30",
}
LAYER_REVIEW_KIND = {
    "00_context": "context_semantic_validity",
    "10_evidence": "source_evidence_note_to_10_evidence",
    "20_synthesis": "10_evidence_to_20_synthesis",
    "30_analysis": "20_synthesis_plus_00_context_to_30_analysis",
}
LAYER_SCHEMA = {
    "00_context": "review_00_context.schema.json",
    "10_evidence": "review_10_evidence.schema.json",
    "20_synthesis": "review_20_synthesis.schema.json",
    "30_analysis": "review_30_analysis.schema.json",
}
MANIFEST_SCHEMA = "review_manifest.schema.json"


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


def _schema_dir(schema_path: str | Path) -> Path:
    path = Path(schema_path)
    return path if path.is_dir() else path.parent


def _layer_filename(layer: str, review_seq: int) -> str:
    return f"{LAYER_FILE_PREFIX[layer]}_{review_seq:06d}.json"


def _manifest_filename(review_seq: int) -> str:
    return f"review-{review_seq:06d}.json"


def prepare_review_cycle(
    investigation_id: str,
    *,
    review_dir: str | Path,
    schema_path: str | Path,
    target_commit_sha: str,
    artifact_blob_shas: Mapping[str, Any],
) -> PreparedReviewCycle:
    """Freeze a target snapshot and allocate the next per-Investigation Review Seq.

    Existing history may contain legacy single-file cycles and new split cycles,
    but it must already be a valid contiguous append-only sequence.
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


def _normalize_layer_body(
    layer: str,
    body: Mapping[str, Any],
    *,
    finding_start: int,
    target_blob_sha: str,
    investigation_id: str,
    review_seq: int,
) -> tuple[dict[str, Any], int]:
    if not isinstance(body, Mapping):
        raise ReviewPersistenceError(f"{layer} body must be an object")
    assessment = body.get("assessment")
    if not isinstance(assessment, str) or not assessment.strip():
        raise ReviewPersistenceError(f"{layer}.assessment must be non-empty")
    findings = body.get("findings", [])
    if not isinstance(findings, list):
        raise ReviewPersistenceError(f"{layer}.findings must be an array")

    normalized_findings: list[dict[str, Any]] = []
    next_index = finding_start
    for finding in findings:
        if not isinstance(finding, Mapping):
            raise ReviewPersistenceError(f"{layer}.findings entries must be objects")
        item = dict(finding)
        item.pop("finding_id", None)
        item["finding_id"] = f"F{next_index:03d}"

        repair_direction = item.get("repair_direction")
        if not isinstance(repair_direction, Mapping):
            raise ReviewPersistenceError(f"{layer}.finding.repair_direction must be an object")
        if (
            repair_direction.get("affected_layer") == "00_context"
            and repair_direction.get("mode") == "same_investigation"
        ):
            raise ReviewPersistenceError(
                "same_investigation repair of frozen 00_context is unsafe; use new_investigation"
            )

        normalized_findings.append(item)
        next_index += 1

    verdict = "FINDINGS" if normalized_findings else "PASS"
    return (
        {
            "schema_version": REVIEW_SCHEMA_VERSION,
            "report_type": "semantic_review_layer",
            "investigation_id": investigation_id,
            "review_seq": review_seq,
            "layer": layer,
            "review_kind": LAYER_REVIEW_KIND[layer],
            "target_blob_sha": target_blob_sha,
            "assessment": assessment.strip(),
            "findings": normalized_findings,
            "verdict": verdict,
        },
        next_index,
    )


def build_review_cycle(
    prepared: PreparedReviewCycle,
    *,
    reviewed_at: str,
    layer_bodies: Mapping[str, Mapping[str, Any]],
) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    """Build one split Review cycle; all verdicts and Finding IDs are deterministic."""
    try:
        parsed = datetime.fromisoformat(reviewed_at.replace("Z", "+00:00"))
    except (AttributeError, ValueError) as exc:
        raise ReviewPersistenceError("reviewed_at must be ISO-8601 date-time") from exc
    if parsed.tzinfo is None:
        raise ReviewPersistenceError("reviewed_at must include a timezone")

    if set(layer_bodies) != set(EXPECTED_ARTIFACTS):
        raise ReviewPersistenceError(
            f"layer_bodies must contain exactly {EXPECTED_ARTIFACTS}"
        )

    layer_records: dict[str, dict[str, Any]] = {}
    next_finding = 1
    for layer in EXPECTED_ARTIFACTS:
        record, next_finding = _normalize_layer_body(
            layer,
            layer_bodies[layer],
            finding_start=next_finding,
            target_blob_sha=prepared.artifact_blob_shas[layer],
            investigation_id=prepared.investigation_id,
            review_seq=prepared.review_seq,
        )
        layer_records[layer] = record

    cycle_verdict = (
        "FINDINGS"
        if any(record["findings"] for record in layer_records.values())
        else "PASS"
    )
    manifest = {
        "schema_version": REVIEW_SCHEMA_VERSION,
        "report_type": "semantic_review_manifest",
        "investigation_id": prepared.investigation_id,
        "review_seq": prepared.review_seq,
        "target": {
            "commit_sha": prepared.target_commit_sha,
            "artifact_blob_shas": dict(prepared.artifact_blob_shas),
        },
        "reviewed_at": reviewed_at,
        "layer_files": {
            layer: _layer_filename(layer, prepared.review_seq)
            for layer in EXPECTED_ARTIFACTS
        },
        "verdict": cycle_verdict,
    }
    return manifest, layer_records


def build_review_record(
    prepared: PreparedReviewCycle,
    *,
    reviewed_at: str,
    layer_bodies: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    """Compatibility wrapper returning the split-cycle manifest."""
    manifest, _ = build_review_cycle(
        prepared,
        reviewed_at=reviewed_at,
        layer_bodies=layer_bodies,
    )
    return manifest


def _validate_payload(
    payload: Mapping[str, Any],
    schema_path: Path,
    *,
    artifact: str,
) -> None:
    validation = validate_data(payload, schema_path, artifact=artifact)
    if not validation.ok:
        detail = "; ".join(f"{e.json_path}: {e.message}" for e in validation.errors)
        raise ReviewPersistenceError(f"Review schema validation failed: {detail}")


def _write_temp_json(review_dir: Path, filename: str, payload: Mapping[str, Any]) -> Path:
    handle = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=review_dir,
        prefix=f".{filename}.",
        suffix=".tmp",
        delete=False,
    )
    try:
        with handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        return Path(handle.name)
    except Exception:
        try:
            Path(handle.name).unlink(missing_ok=True)
        finally:
            raise


def save_review_cycle(
    prepared: PreparedReviewCycle,
    *,
    reviewed_at: str,
    layer_bodies: Mapping[str, Mapping[str, Any]],
    current_target_commit_sha: str,
    current_artifact_blob_shas: Mapping[str, Any],
    review_dir: str | Path,
    schema_path: str | Path,
) -> Path:
    """Validate and append one split Review cycle.

    Layer files are finalized first and the manifest last. If process failure
    leaves orphan final layer files, the history loader treats the directory as
    invalid and fail-stops rather than silently recovering or overwriting.
    """
    current_commit = _require_sha(
        current_target_commit_sha,
        field="current_target_commit_sha",
    )
    current_blobs = _normalize_blob_shas(current_artifact_blob_shas)
    if (
        current_commit != prepared.target_commit_sha
        or current_blobs != dict(prepared.artifact_blob_shas)
    ):
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

    manifest, layer_records = build_review_cycle(
        prepared,
        reviewed_at=reviewed_at,
        layer_bodies=layer_bodies,
    )

    schema_dir = _schema_dir(schema_path)
    for layer, record in layer_records.items():
        _validate_payload(
            record,
            schema_dir / LAYER_SCHEMA[layer],
            artifact=_layer_filename(layer, prepared.review_seq),
        )
    _validate_payload(
        manifest,
        schema_dir / MANIFEST_SCHEMA,
        artifact=_manifest_filename(prepared.review_seq),
    )

    review_dir.mkdir(parents=True, exist_ok=True)
    final_paths = {
        layer: review_dir / _layer_filename(layer, prepared.review_seq)
        for layer in EXPECTED_ARTIFACTS
    }
    manifest_path = review_dir / _manifest_filename(prepared.review_seq)
    if manifest_path.exists() or any(path.exists() for path in final_paths.values()):
        existing = [
            path.name
            for path in [manifest_path, *final_paths.values()]
            if path.exists()
        ]
        raise ReviewPersistenceError(
            "append-only Review target already exists: " + ", ".join(existing)
        )

    temp_paths: list[Path] = []
    try:
        for layer in EXPECTED_ARTIFACTS:
            temp_paths.append(
                _write_temp_json(
                    review_dir,
                    final_paths[layer].name,
                    layer_records[layer],
                )
            )
        manifest_temp = _write_temp_json(review_dir, manifest_path.name, manifest)
        temp_paths.append(manifest_temp)

        for index, layer in enumerate(EXPECTED_ARTIFACTS):
            os.replace(temp_paths[index], final_paths[layer])
        os.replace(manifest_temp, manifest_path)
    except Exception:
        for temp_path in temp_paths:
            temp_path.unlink(missing_ok=True)
        raise

    return manifest_path
