"""Read-only normalization of canonical semantic Review history."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any, Mapping

from research_atelier.validation.schema_validator import validate_data

REVIEW_FILENAME_RE = re.compile(r"^review-([0-9]{6})\.json$")
LAYER_FILENAME_RE = re.compile(r"^review_(00|10|20|30)_([0-9]{6})\.json$")
LAYER_BY_TOKEN = {
    "00": "00_context",
    "10": "10_evidence",
    "20": "20_synthesis",
    "30": "30_analysis",
}
LAYER_FILE_PREFIX = {
    "00_context": "review_00",
    "10_evidence": "review_10",
    "20_synthesis": "review_20",
    "30_analysis": "review_30",
}
LAYER_SCHEMA = {
    "00_context": "review_00_context.schema.json",
    "10_evidence": "review_10_evidence.schema.json",
    "20_synthesis": "review_20_synthesis.schema.json",
    "30_analysis": "review_30_analysis.schema.json",
}
LAYER_REVIEW_KIND = {
    "00_context": "context_semantic_validity",
    "10_evidence": "source_evidence_note_to_10_evidence",
    "20_synthesis": "10_evidence_to_20_synthesis",
    "30_analysis": "20_synthesis_plus_00_context_to_30_analysis",
}
EXPECTED_ARTIFACTS = ("00_context", "10_evidence", "20_synthesis", "30_analysis")
LEGACY_TRANSITION_TO_LAYER = {
    "source_evidence_note_to_10_evidence": "10_evidence",
    "10_evidence_to_20_synthesis": "20_synthesis",
    "20_synthesis_plus_00_context_to_30_analysis": "30_analysis",
}


@dataclass(frozen=True)
class ReviewHistory:
    records: tuple[Mapping[str, Any], ...]
    issues: tuple[str, ...]

    @property
    def latest(self) -> Mapping[str, Any] | None:
        return self.records[-1] if self.records else None


def _schema_dir(schema_path: str | Path) -> Path:
    path = Path(schema_path)
    return path if path.is_dir() else path.parent


def _canonical_paths(investigation_id: str, review_seq: int) -> dict[str, str]:
    base = f"investigations/{investigation_id}/reviews"
    paths = {"manifest": f"{base}/review-{review_seq:06d}.json"}
    for layer in EXPECTED_ARTIFACTS:
        paths[layer] = f"{base}/{LAYER_FILE_PREFIX[layer]}_{review_seq:06d}.json"
    return paths


def _verdict_from_findings(findings: list[Mapping[str, Any]]) -> str:
    return "FINDINGS" if findings else "PASS"


def normalize_legacy_review(
    review: Mapping[str, Any],
    *,
    canonical_path: str | None = None,
) -> dict[str, Any]:
    """Normalize one validated legacy single-file cycle into the storage-neutral model."""
    investigation_id = review.get("investigation_id")
    review_seq = review.get("review_seq")
    transitions = review.get("transitions")
    if not isinstance(investigation_id, str):
        raise ValueError("legacy review investigation_id missing")
    if not isinstance(review_seq, int) or review_seq < 1:
        raise ValueError("legacy review review_seq invalid")
    if not isinstance(transitions, list):
        raise ValueError("legacy review transitions missing")

    target = review.get("target")
    target_blobs = (
        target.get("artifact_blob_shas")
        if isinstance(target, Mapping)
        else None
    )
    if not isinstance(target_blobs, Mapping):
        raise ValueError("legacy review target.artifact_blob_shas missing")

    by_layer: dict[str, dict[str, Any]] = {
        "00_context": {
            "layer": "00_context",
            "review_kind": "legacy_no_standalone_context_assessment",
            "target_blob_sha": target_blobs.get("00_context"),
            "assessment": (
                "Legacy single-file Review has no standalone 00_context assessment; "
                "operational outcome is compatibility-derived from Finding affected_layer."
            ),
            "findings": [],
            "verdict": "PASS",
        }
    }
    for transition in transitions:
        if not isinstance(transition, Mapping):
            raise ValueError("legacy transition must be an object")
        name = transition.get("transition")
        layer = LEGACY_TRANSITION_TO_LAYER.get(str(name))
        if layer is None:
            raise ValueError(f"unexpected legacy transition: {name!r}")
        findings = transition.get("findings", [])
        if not isinstance(findings, list):
            raise ValueError("legacy transition findings must be an array")
        by_layer[layer] = {
            "layer": layer,
            "review_kind": str(name),
            "target_blob_sha": transition.get("target_blob_sha"),
            "assessment": transition.get("assessment"),
            "findings": list(findings),
            "verdict": _verdict_from_findings(
                [item for item in findings if isinstance(item, Mapping)]
            ),
        }

    if set(by_layer) != set(EXPECTED_ARTIFACTS):
        raise ValueError("legacy review does not contain the expected semantic transitions")

    paths = _canonical_paths(investigation_id, review_seq)
    if canonical_path is not None:
        paths["manifest"] = canonical_path

    return {
        "schema_version": review.get("schema_version"),
        "report_type": "semantic_review_normalized",
        "investigation_id": investigation_id,
        "review_seq": review_seq,
        "target": review.get("target"),
        "reviewed_at": review.get("reviewed_at"),
        "layers": by_layer,
        "verdict": review.get("verdict"),
        "storage_format": "legacy_single",
        "canonical_paths": {"manifest": paths["manifest"]},
    }


def ensure_normalized_review(review: Mapping[str, Any]) -> dict[str, Any]:
    """Return a storage-neutral Review Cycle.

    Split manifests cannot be normalized without their layer files and therefore
    must be loaded through load_review_history().
    """
    if review.get("report_type") == "semantic_review_normalized":
        return dict(review)
    if review.get("report_type") == "semantic_review":
        return normalize_legacy_review(review)
    raise ValueError(
        "Review cycle is not normalized; split manifests must be loaded with load_review_history"
    )


def _all_findings(review: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    layers = review.get("layers")
    if not isinstance(layers, Mapping):
        raise ValueError("normalized review layers missing")
    findings: list[Mapping[str, Any]] = []
    for layer in EXPECTED_ARTIFACTS:
        layer_record = layers.get(layer)
        if not isinstance(layer_record, Mapping):
            raise ValueError(f"normalized layer missing: {layer}")
        values = layer_record.get("findings", [])
        if not isinstance(values, list):
            raise ValueError(f"{layer}.findings must be an array")
        for finding in values:
            if not isinstance(finding, Mapping):
                raise ValueError(f"{layer}.findings entries must be objects")
            findings.append(finding)
    return findings


def _normalized_invariant_issues(review: Mapping[str, Any]) -> list[str]:
    issues: list[str] = []
    try:
        findings = _all_findings(review)
    except ValueError as exc:
        return [f"invalid_normalized_review:{exc}"]

    expected_cycle_verdict = "FINDINGS" if findings else "PASS"
    if review.get("verdict") != expected_cycle_verdict:
        issues.append(
            f"review_verdict_finding_mismatch:{review.get('review_seq')}:{review.get('verdict')}:{expected_cycle_verdict}"
        )

    layers = review["layers"]
    expected_ids = [f"F{index:03d}" for index in range(1, len(findings) + 1)]
    actual_ids = [finding.get("finding_id") for finding in findings]
    if actual_ids != expected_ids:
        issues.append(
            f"review_finding_id_sequence_mismatch:{review.get('review_seq')}:{actual_ids}"
        )

    for layer in EXPECTED_ARTIFACTS:
        layer_record = layers[layer]
        layer_findings = layer_record.get("findings", [])
        expected_layer_verdict = "FINDINGS" if layer_findings else "PASS"
        if layer_record.get("verdict") != expected_layer_verdict:
            issues.append(
                f"layer_verdict_finding_mismatch:{review.get('review_seq')}:{layer}"
            )
        for finding in layer_findings:
            repair = finding.get("repair_direction")
            if not isinstance(repair, Mapping):
                issues.append(
                    f"finding_repair_direction_missing:{review.get('review_seq')}:{finding.get('finding_id')}"
                )
                continue
            if (
                repair.get("affected_layer") == "00_context"
                and repair.get("mode") == "same_investigation"
            ):
                issues.append(
                    f"unsafe_context_same_investigation:{review.get('review_seq')}:{finding.get('finding_id')}"
                )
    return issues


def _load_json(path: Path, *, issues: list[str]) -> Mapping[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        issues.append(f"malformed_review_json:{path.name}:{exc}")
        return None
    if not isinstance(data, Mapping):
        issues.append(f"review_json_not_object:{path.name}")
        return None
    return data


def _validate(
    data: Mapping[str, Any],
    schema_path: Path,
    *,
    artifact: str,
    issues: list[str],
) -> bool:
    validation = validate_data(data, schema_path, artifact=artifact)
    if validation.ok:
        return True
    issues.extend(
        f"invalid_review_schema:{artifact}:{issue.json_path}:{issue.message}"
        for issue in validation.errors
    )
    return False


def _load_split_cycle(
    investigation_id: str,
    *,
    review_dir: Path,
    manifest_path: Path,
    manifest: Mapping[str, Any],
    schema_dir: Path,
    layer_files_by_seq: Mapping[int, Mapping[str, Path]],
    issues: list[str],
) -> Mapping[str, Any] | None:
    review_seq = manifest.get("review_seq")
    if not isinstance(review_seq, int) or review_seq < 1:
        issues.append(f"invalid_review_seq:{manifest_path.name}")
        return None

    if not _validate(
        manifest,
        schema_dir / "review_manifest.schema.json",
        artifact=manifest_path.name,
        issues=issues,
    ):
        return None
    if manifest.get("investigation_id") != investigation_id:
        issues.append(f"review_investigation_mismatch:{manifest_path.name}")
        return None

    cycle_issue_start = len(issues)
    files_for_seq = dict(layer_files_by_seq.get(review_seq, {}))
    expected_layer_names = {
        layer: f"{LAYER_FILE_PREFIX[layer]}_{review_seq:06d}.json"
        for layer in EXPECTED_ARTIFACTS
    }
    manifest_layer_files = manifest.get("layer_files")
    if not isinstance(manifest_layer_files, Mapping):
        issues.append(f"review_layer_files_missing:{manifest_path.name}")
        return None
    for layer, expected_name in expected_layer_names.items():
        if manifest_layer_files.get(layer) != expected_name:
            issues.append(
                f"review_layer_filename_manifest_mismatch:{manifest_path.name}:{layer}"
            )
    if len(issues) != cycle_issue_start:
        return None

    missing_layers = [layer for layer in EXPECTED_ARTIFACTS if layer not in files_for_seq]
    if missing_layers:
        issues.append(
            f"incomplete_split_review:{review_seq}:{','.join(missing_layers)}"
        )
        return None

    target = manifest.get("target")
    target_blobs = target.get("artifact_blob_shas") if isinstance(target, Mapping) else None
    if not isinstance(target_blobs, Mapping):
        issues.append(f"review_target_blobs_missing:{manifest_path.name}")
        return None

    layers: dict[str, Mapping[str, Any]] = {}
    for layer in EXPECTED_ARTIFACTS:
        path = files_for_seq[layer]
        data = _load_json(path, issues=issues)
        if data is None:
            return None
        if not _validate(
            data,
            schema_dir / LAYER_SCHEMA[layer],
            artifact=path.name,
            issues=issues,
        ):
            return None
        if data.get("investigation_id") != investigation_id:
            issues.append(f"review_layer_investigation_mismatch:{path.name}")
        if data.get("review_seq") != review_seq:
            issues.append(f"review_layer_seq_mismatch:{path.name}:{data.get('review_seq')}")
        if data.get("layer") != layer:
            issues.append(f"review_layer_identity_mismatch:{path.name}:{data.get('layer')}")
        if data.get("review_kind") != LAYER_REVIEW_KIND[layer]:
            issues.append(f"review_kind_mismatch:{path.name}:{data.get('review_kind')}")
        if data.get("target_blob_sha") != target_blobs.get(layer):
            issues.append(f"review_layer_target_sha_mismatch:{path.name}")
        layers[layer] = data

    if len(issues) != cycle_issue_start:
        return None

    normalized = {
        "schema_version": manifest.get("schema_version"),
        "report_type": "semantic_review_normalized",
        "investigation_id": investigation_id,
        "review_seq": review_seq,
        "target": manifest.get("target"),
        "reviewed_at": manifest.get("reviewed_at"),
        "layers": layers,
        "verdict": manifest.get("verdict"),
        "storage_format": "split_v2",
        "canonical_paths": _canonical_paths(investigation_id, review_seq),
    }
    invariant_issues = _normalized_invariant_issues(normalized)
    issues.extend(invariant_issues)
    if invariant_issues:
        return None
    return normalized


def load_review_history(
    investigation_id: str,
    *,
    review_dir: str | Path,
    schema_path: str | Path,
) -> ReviewHistory:
    """Load append-only Review cycles across legacy and split v2 formats."""
    review_dir = Path(review_dir)
    if not review_dir.exists():
        return ReviewHistory((), ())

    schema_path = Path(schema_path)
    schema_dir = _schema_dir(schema_path)
    issues: list[str] = []
    anchors: dict[int, tuple[Path, Mapping[str, Any]]] = {}
    layer_files_by_seq: dict[int, dict[str, Path]] = {}

    json_files = sorted(review_dir.glob("*.json"), key=lambda p: p.name)
    for path in json_files:
        anchor_match = REVIEW_FILENAME_RE.fullmatch(path.name)
        if anchor_match is not None:
            seq = int(anchor_match.group(1))
            data = _load_json(path, issues=issues)
            if data is not None:
                anchors[seq] = (path, data)
            continue

        layer_match = LAYER_FILENAME_RE.fullmatch(path.name)
        if layer_match is not None:
            layer = LAYER_BY_TOKEN[layer_match.group(1)]
            seq = int(layer_match.group(2))
            layer_files_by_seq.setdefault(seq, {})[layer] = path
            continue

        issues.append(f"unexpected_review_filename:{path.name}")

    by_seq: dict[int, Mapping[str, Any]] = {}
    split_anchor_seqs: set[int] = set()

    for seq in sorted(anchors):
        path, data = anchors[seq]
        if data.get("review_seq") != seq:
            issues.append(f"review_seq_filename_mismatch:{path.name}:{data.get('review_seq')}")
            continue

        report_type = data.get("report_type")
        if report_type == "semantic_review":
            if not _validate(data, schema_path, artifact=path.name, issues=issues):
                continue
            if data.get("investigation_id") != investigation_id:
                issues.append(f"review_investigation_mismatch:{path.name}")
                continue
            try:
                normalized = normalize_legacy_review(
                    data,
                    canonical_path=f"investigations/{investigation_id}/reviews/{path.name}",
                )
            except ValueError as exc:
                issues.append(f"invalid_legacy_review:{path.name}:{exc}")
                continue
            invariant_issues = _normalized_invariant_issues(normalized)
            issues.extend(invariant_issues)
            if invariant_issues:
                continue
            by_seq[seq] = normalized
        elif report_type == "semantic_review_manifest":
            split_anchor_seqs.add(seq)
            normalized = _load_split_cycle(
                investigation_id,
                review_dir=review_dir,
                manifest_path=path,
                manifest=data,
                schema_dir=schema_dir,
                layer_files_by_seq=layer_files_by_seq,
                issues=issues,
            )
            if normalized is not None:
                by_seq[seq] = normalized
        else:
            issues.append(f"unknown_review_report_type:{path.name}:{report_type}")

    for seq, layer_files in layer_files_by_seq.items():
        if seq not in split_anchor_seqs:
            for path in layer_files.values():
                issues.append(f"orphan_review_layer:{path.name}")

    seqs = sorted(by_seq)
    if seqs and seqs != list(range(1, seqs[-1] + 1)):
        issues.append(f"incomplete_review_history:{seqs}")

    records = tuple(by_seq[seq] for seq in seqs)
    return ReviewHistory(records, tuple(sorted(set(issues))))


def target_relation_from_blobs(
    review: Mapping[str, Any],
    current_artifact_blob_shas: Mapping[str, str],
) -> str:
    """Return exact/stale based on frozen blobs; ancestry-unsafe cases stay adapter-owned."""
    target = review.get("target")
    if not isinstance(target, Mapping):
        return "missing"
    frozen = target.get("artifact_blob_shas")
    if not isinstance(frozen, Mapping):
        return "missing"
    return "exact" if dict(frozen) == dict(current_artifact_blob_shas) else "stale"
