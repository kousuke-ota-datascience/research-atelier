"""Read-only normalization of canonical semantic Review history."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any, Mapping

from research_atelier.validation.schema_validator import validate_data

REVIEW_FILENAME_RE = re.compile(r"^review-([0-9]{6})\.json$")


@dataclass(frozen=True)
class ReviewHistory:
    records: tuple[Mapping[str, Any], ...]
    issues: tuple[str, ...]

    @property
    def latest(self) -> Mapping[str, Any] | None:
        return self.records[-1] if self.records else None


def load_review_history(
    investigation_id: str,
    *,
    review_dir: str | Path,
    schema_path: str | Path,
) -> ReviewHistory:
    """Load append-only Review cycles and surface malformed/duplicate/gap issues."""
    review_dir = Path(review_dir)
    if not review_dir.exists():
        return ReviewHistory((), ())

    issues: list[str] = []
    by_seq: dict[int, Mapping[str, Any]] = {}
    json_files = sorted(review_dir.glob("*.json"), key=lambda p: p.name)

    for path in json_files:
        match = REVIEW_FILENAME_RE.fullmatch(path.name)
        if match is None:
            issues.append(f"unexpected_review_filename:{path.name}")
            continue
        filename_seq = int(match.group(1))
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            issues.append(f"malformed_review_json:{path.name}:{exc}")
            continue

        validation = validate_data(data, schema_path, artifact=path.name)
        if not validation.ok:
            issues.extend(
                f"invalid_review_schema:{path.name}:{issue.json_path}:{issue.message}"
                for issue in validation.errors
            )
            continue

        if data.get("investigation_id") != investigation_id:
            issues.append(f"review_investigation_mismatch:{path.name}")
            continue
        payload_seq = data.get("review_seq")
        if payload_seq != filename_seq:
            issues.append(f"review_seq_filename_mismatch:{path.name}:{payload_seq}")
            continue
        if filename_seq in by_seq:
            issues.append(f"duplicate_review_seq:{filename_seq}")
            continue
        by_seq[filename_seq] = data

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
