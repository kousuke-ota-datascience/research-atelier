"""Validate Information Source revision bindings in 10_evidence v2.1."""
from __future__ import annotations

from pathlib import Path
import re
import subprocess
from typing import Any, Mapping

from .schema_validator import ValidationIssue


REPO_ROOT = Path(__file__).resolve().parents[3]
SOURCE_ID_RE = re.compile(r"^SRC-(?:[0-9]{4}|[0-9]{6})$")


def _issue(
    rule_id: str,
    json_path: str,
    message: str,
    *,
    expected: Any | None = None,
    actual: Any | None = None,
) -> ValidationIssue:
    return ValidationIssue(
        rule_id,
        "10",
        json_path,
        message,
        "source_revision_validator",
        expected,
        actual,
    )


def _git(repository_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repository_root), *args],
        check=False,
        capture_output=True,
        text=True,
    )


def validate_source_revisions(
    evidence_data: Mapping[str, Any],
    *,
    repository_root: str | Path = REPO_ROOT,
) -> tuple[ValidationIssue, ...]:
    """Validate Source references and commit/blob bindings for 10_evidence 2.1.

    Historical 2.0.0 evidence artifacts are intentionally excluded. BKL-0038
    owns migration of those artifacts to the new provenance contract.
    """
    if evidence_data.get("schema_version") != "2.1.0":
        return ()

    repository_root = Path(repository_root)
    errors: list[ValidationIssue] = []
    sources = evidence_data.get("sources", [])
    evidence_items = evidence_data.get("evidence_items", [])

    source_ids: list[str] = []
    source_by_id: dict[str, Mapping[str, Any]] = {}
    if isinstance(sources, list):
        for idx, source in enumerate(sources):
            if not isinstance(source, Mapping):
                continue
            source_id = source.get("source_id")
            if not isinstance(source_id, str):
                continue
            source_ids.append(source_id)
            if source_id in source_by_id:
                errors.append(
                    _issue(
                        "V-SRC-002",
                        "$.sources",
                        f"duplicate source_id: {source_id}",
                    )
                )
            else:
                source_by_id[source_id] = source

            if SOURCE_ID_RE.fullmatch(source_id) is None:
                continue

            revision = source.get("source_revision")
            if not isinstance(revision, Mapping):
                continue
            commit_sha = revision.get("commit_sha")
            blob_sha = revision.get("blob_sha")
            if not isinstance(commit_sha, str) or not isinstance(blob_sha, str):
                continue

            commit_check = _git(repository_root, "cat-file", "-e", f"{commit_sha}^{{commit}}")
            if commit_check.returncode != 0:
                errors.append(
                    _issue(
                        "V-SRC-REV-001",
                        f"$.sources[{idx}].source_revision.commit_sha",
                        "Source revision commit does not exist in repository",
                        actual=commit_sha,
                    )
                )
                continue

            source_path = f"information_sources/{source_id}.json"
            tree = _git(repository_root, "ls-tree", commit_sha, "--", source_path)
            if tree.returncode != 0 or not tree.stdout.strip():
                errors.append(
                    _issue(
                        "V-SRC-REV-002",
                        f"$.sources[{idx}].source_revision",
                        "Source JSON does not exist at recorded commit",
                        expected=source_path,
                        actual=commit_sha,
                    )
                )
                continue

            parts = tree.stdout.strip().split(None, 3)
            actual_blob = parts[2] if len(parts) >= 3 else None
            if actual_blob != blob_sha:
                errors.append(
                    _issue(
                        "V-SRC-REV-003",
                        f"$.sources[{idx}].source_revision.blob_sha",
                        "recorded blob_sha does not match Source JSON blob at commit_sha",
                        expected=actual_blob,
                        actual=blob_sha,
                    )
                )

    referenced_ids: list[str] = []
    if isinstance(evidence_items, list):
        for idx, item in enumerate(evidence_items):
            if not isinstance(item, Mapping):
                continue
            provenance = item.get("provenance")
            if not isinstance(provenance, Mapping):
                continue
            source_id = provenance.get("source_id")
            if not isinstance(source_id, str):
                continue
            referenced_ids.append(source_id)
            if source_id not in source_by_id:
                errors.append(
                    _issue(
                        "V-SRC-REF-001",
                        f"$.evidence_items[{idx}].provenance.source_id",
                        "Evidence references a Source not present in $.sources",
                        expected=sorted(source_by_id),
                        actual=source_id,
                    )
                )

    referenced_set = set(referenced_ids)
    for idx, source_id in enumerate(source_ids):
        if source_id not in referenced_set:
            errors.append(
                _issue(
                    "V-SRC-REF-002",
                    f"$.sources[{idx}].source_id",
                    "10_evidence Source snapshot contains an unreferenced Source",
                    expected="Source referenced by at least one evidence item",
                    actual=source_id,
                )
            )

    return tuple(sorted(errors, key=ValidationIssue.sort_key))
