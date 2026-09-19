"""Safe append-only creation of canonical Review JSON cycles.

A Review cycle is prepared before semantic review to freeze the target
commit/blob tuple and the next shared Review Seq. The three artifact-specific
Review bodies are then written together. Managed envelope fields are generated
by this module and cannot be supplied by the reviewer.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any, Mapping

from src.status_management.git_state import load_entry_git_state
from src.status_management.review_state import load_entry_review_state
from src.validation.schema_validator import validate_data
from src.validation.validate_entry import validate_entry

ARTICLE_ROOT = Path(__file__).resolve().parents[2]
REVIEW_ROOT = ARTICLE_ROOT / "reviews/10_each_lore"
SCHEMA_ROOT = ARTICLE_ROOT / "docs/10_each_lore/0000_tutorial/schemas"
ARTIFACTS = ("00", "10", "20")
SCHEMAS = {
    "00": "review_00_sources.schema.json",
    "10": "review_10_contents.schema.json",
    "20": "review_20_analysis.schema.json",
}
RESERVED_FIELDS = frozenset(
    {"schema_version", "entry_id", "artifact", "review_seq", "target", "verdict"}
)
SEVERITY_RANK = {"Minor": 1, "Moderate": 2, "Major": 3}
RANK_VERDICT = {0: "Pass", 1: "Minor", 2: "Moderate", 3: "Major"}


@dataclass(frozen=True)
class TargetSnapshot:
    artifact_path: str
    commit_sha: str
    blob_sha: str


@dataclass(frozen=True)
class ReviewCycleSnapshot:
    entry_id: str
    review_seq: int
    prepared_at: str
    targets: dict[str, TargetSnapshot]

    def to_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "review_seq": self.review_seq,
            "prepared_at": self.prepared_at,
            "targets": {artifact: asdict(target) for artifact, target in self.targets.items()},
        }


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _validate_entry_id(entry_id: str) -> None:
    if len(entry_id) != 4 or not entry_id.isdigit():
        raise ValueError("entry_id must be four digits")


def _require_entry_validation_pass(entry_id: str) -> None:
    result = validate_entry(entry_id)
    if result.get("result") != "PASS":
        raise RuntimeError(
            "entry deterministic validation must PASS before Review: "
            + json.dumps(result, ensure_ascii=False, sort_keys=True)
        )


def _working_tree_blob_sha(repo: Path, path: Path) -> str:
    rel = path.resolve().relative_to(repo).as_posix()
    proc = subprocess.run(
        ["git", "-C", str(repo), "hash-object", f"--path={rel}", rel],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"cannot hash working-tree artifact {rel}: {proc.stderr.strip()}")
    sha = proc.stdout.strip()
    if not sha:
        raise RuntimeError(f"empty working-tree blob SHA for {rel}")
    return sha


def _load_targets(entry_id: str) -> dict[str, TargetSnapshot]:
    snapshot = load_entry_git_state(entry_id)
    targets: dict[str, TargetSnapshot] = {}

    for artifact in ARTIFACTS:
        state = snapshot.artifacts[artifact]
        if not state.exists or not state.commit_sha or not state.blob_sha:
            raise RuntimeError(f"review target is not committed: {entry_id}/{artifact}")

        working_blob = _working_tree_blob_sha(snapshot.repository_root, state.path)
        if working_blob != state.blob_sha:
            raise RuntimeError(
                f"working tree differs from committed review target: {entry_id}/{artifact} "
                f"committed={state.blob_sha} working={working_blob}"
            )

        rel = state.path.resolve().relative_to(snapshot.repository_root).as_posix()
        targets[artifact] = TargetSnapshot(
            artifact_path=rel,
            commit_sha=state.commit_sha,
            blob_sha=state.blob_sha,
        )

    return targets


def _next_review_seq(entry_id: str) -> int:
    snapshot = load_entry_review_state(entry_id)
    if snapshot.issues:
        raise RuntimeError(
            "existing Review history is not safe for allocation: " + ", ".join(snapshot.issues)
        )

    by_seq: dict[int, set[str]] = {}
    for fact in snapshot.all_reviews:
        by_seq.setdefault(fact.review_seq, set()).add(fact.artifact)

    expected = set(ARTIFACTS)
    incomplete = {
        seq: sorted(expected - artifacts)
        for seq, artifacts in by_seq.items()
        if artifacts != expected
    }
    if incomplete:
        raise RuntimeError(
            "incomplete existing Review cycle prevents safe Seq allocation: "
            + json.dumps(incomplete, ensure_ascii=False, sort_keys=True)
        )

    return max(by_seq, default=0) + 1


def aggregate_verdict(findings: Any) -> str:
    """Return the deterministic Verdict implied by Finding severities."""
    if not isinstance(findings, list):
        raise ValueError("findings must be an array")

    max_rank = 0
    seen_ids: set[str] = set()
    for index, finding in enumerate(findings):
        if not isinstance(finding, Mapping):
            raise ValueError(f"finding[{index}] must be an object")

        finding_id = finding.get("finding_id")
        if isinstance(finding_id, str):
            if finding_id in seen_ids:
                raise ValueError(f"duplicate finding_id: {finding_id}")
            seen_ids.add(finding_id)

        severity = finding.get("severity")
        if severity not in SEVERITY_RANK:
            raise ValueError(f"invalid finding severity at index {index}: {severity}")
        max_rank = max(max_rank, SEVERITY_RANK[severity])

    return RANK_VERDICT[max_rank]


def prepare_review_cycle(entry_id: str) -> ReviewCycleSnapshot:
    """Freeze current Review targets and allocate the next shared Review Seq."""
    _validate_entry_id(entry_id)
    _require_entry_validation_pass(entry_id)
    review_seq = _next_review_seq(entry_id)
    targets = _load_targets(entry_id)
    return ReviewCycleSnapshot(
        entry_id=entry_id,
        review_seq=review_seq,
        prepared_at=_utc_now(),
        targets=targets,
    )


def _parse_cycle(data: Mapping[str, Any]) -> ReviewCycleSnapshot:
    entry_id = data.get("entry_id")
    review_seq = data.get("review_seq")
    prepared_at = data.get("prepared_at")
    raw_targets = data.get("targets")

    if not isinstance(entry_id, str):
        raise ValueError("cycle.entry_id must be a string")
    _validate_entry_id(entry_id)
    if not isinstance(review_seq, int) or isinstance(review_seq, bool) or review_seq < 1:
        raise ValueError("cycle.review_seq must be a positive integer")
    if not isinstance(prepared_at, str) or not prepared_at:
        raise ValueError("cycle.prepared_at must be a non-empty string")
    if not isinstance(raw_targets, Mapping) or set(raw_targets) != set(ARTIFACTS):
        raise ValueError("cycle.targets must contain exactly 00, 10, 20")

    targets: dict[str, TargetSnapshot] = {}
    for artifact in ARTIFACTS:
        raw = raw_targets[artifact]
        if not isinstance(raw, Mapping):
            raise ValueError(f"cycle.targets.{artifact} must be an object")
        target = TargetSnapshot(
            artifact_path=str(raw.get("artifact_path", "")),
            commit_sha=str(raw.get("commit_sha", "")),
            blob_sha=str(raw.get("blob_sha", "")),
        )
        if not target.artifact_path:
            raise ValueError(f"cycle.targets.{artifact}.artifact_path is required")
        if len(target.commit_sha) != 40 or len(target.blob_sha) != 40:
            raise ValueError(f"cycle.targets.{artifact} must contain 40-char commit/blob SHA")
        targets[artifact] = target

    return ReviewCycleSnapshot(entry_id, review_seq, prepared_at, targets)


def _validate_cycle_is_current(cycle: ReviewCycleSnapshot) -> None:
    _require_entry_validation_pass(cycle.entry_id)

    expected_seq = _next_review_seq(cycle.entry_id)
    if cycle.review_seq != expected_seq:
        raise RuntimeError(
            f"Review Seq reservation is stale: prepared={cycle.review_seq} current_next={expected_seq}"
        )

    current_targets = _load_targets(cycle.entry_id)
    if current_targets != cycle.targets:
        expected = {k: asdict(v) for k, v in cycle.targets.items()}
        actual = {k: asdict(v) for k, v in current_targets.items()}
        raise RuntimeError(
            "Review target changed after prepare: "
            + json.dumps({"prepared": expected, "current": actual}, ensure_ascii=False, sort_keys=True)
        )


def _validate_review10_coverage_contract(entry_id: str, body: Mapping[str, Any]) -> None:
    """Require complete salient-unit audit for the current 10 Contents contract."""
    snapshot = load_entry_git_state(entry_id)
    path = snapshot.artifacts["10"].path
    data = json.loads(path.read_text(encoding="utf-8"))
    summary = data.get("summary", {})
    coverage_refs = summary.get("coverage_refs") if isinstance(summary, Mapping) else None
    if not isinstance(coverage_refs, list) or not coverage_refs:
        return

    checks = body.get("checks")
    if not isinstance(checks, Mapping) or "narrative_reconstruction" not in checks:
        raise ValueError(
            "Review 10 for summary.coverage_refs contract requires checks.narrative_reconstruction"
        )

    reconstruction = body.get("reconstruction")
    if not isinstance(reconstruction, Mapping):
        raise ValueError("Review 10 reconstruction must be an object")
    audit = reconstruction.get("coverage_audit")
    if not isinstance(audit, list) or not audit:
        raise ValueError(
            "Review 10 for summary.coverage_refs contract requires reconstruction.coverage_audit"
        )

    refs = []
    differences = []
    for index, item in enumerate(audit):
        if not isinstance(item, Mapping):
            raise ValueError(f"coverage_audit[{index}] must be an object")
        ref = item.get("content_ref")
        if not isinstance(ref, str):
            raise ValueError(f"coverage_audit[{index}].content_ref must be a string")
        refs.append(ref)
        differences.append(item.get("difference"))

    if len(refs) != len(set(refs)):
        raise ValueError("coverage_audit contains duplicate content_ref")
    if set(refs) != set(coverage_refs) or len(refs) != len(coverage_refs):
        raise ValueError(
            "coverage_audit content_ref set must exactly match summary.coverage_refs: "
            + json.dumps(
                {"expected": coverage_refs, "actual": refs},
                ensure_ascii=False,
                sort_keys=True,
            )
        )

    has_loss = any(value in {"LOSS", "CONFLICT"} for value in differences)
    if has_loss:
        if reconstruction.get("verdict") != "FINDING":
            raise ValueError(
                "coverage_audit LOSS/CONFLICT requires reconstruction.verdict=FINDING"
            )
        findings = body.get("findings")
        if not isinstance(findings, list) or not any(
            isinstance(item, Mapping)
            and item.get("category") in {"narrative_reconstruction", "summary_reconstruction"}
            for item in findings
        ):
            raise ValueError(
                "coverage_audit LOSS/CONFLICT requires a narrative/summary reconstruction Finding"
            )


def _build_payloads(
    cycle: ReviewCycleSnapshot,
    reviews: Mapping[str, Any],
) -> dict[str, dict[str, Any]]:
    if set(reviews) != set(ARTIFACTS):
        raise ValueError("reviews must contain exactly 00, 10, 20")

    reviewed_at = _utc_now()
    payloads: dict[str, dict[str, Any]] = {}

    for artifact in ARTIFACTS:
        body = reviews[artifact]
        if not isinstance(body, Mapping):
            raise ValueError(f"reviews.{artifact} must be an object")
        if artifact == "10":
            _validate_review10_coverage_contract(cycle.entry_id, body)

        conflicts = sorted(RESERVED_FIELDS.intersection(body))
        if conflicts:
            raise ValueError(
                f"reviews.{artifact} contains writer-managed fields: {', '.join(conflicts)}"
            )

        findings = body.get("findings")
        verdict = aggregate_verdict(findings)

        target = asdict(cycle.targets[artifact])
        target["reviewed_at"] = reviewed_at

        payload = {
            "schema_version": "1.0",
            "entry_id": cycle.entry_id,
            "artifact": artifact,
            "review_seq": cycle.review_seq,
            "target": target,
            **dict(body),
            "verdict": verdict,
        }

        result = validate_data(
            payload,
            SCHEMA_ROOT / SCHEMAS[artifact],
            artifact=f"review_{artifact}",
        )
        if not result.ok:
            details = [
                {
                    "rule_id": issue.rule_id,
                    "path": issue.json_path,
                    "message": issue.message,
                }
                for issue in result.errors
            ]
            raise ValueError(
                f"Review {artifact} fails save-time Schema validation: "
                + json.dumps(details, ensure_ascii=False, sort_keys=True)
            )

        payloads[artifact] = payload

    return payloads


def _write_append_only(
    cycle: ReviewCycleSnapshot,
    payloads: Mapping[str, Mapping[str, Any]],
) -> dict[str, Path]:
    directory = REVIEW_ROOT / cycle.entry_id
    destinations = {
        artifact: directory
        / f"Review_{cycle.entry_id}_{artifact}_{cycle.review_seq:03d}.json"
        for artifact in ARTIFACTS
    }

    existing = [path for path in destinations.values() if path.exists()]
    if existing:
        raise FileExistsError(
            "Review JSON overwrite is forbidden: " + ", ".join(str(path) for path in existing)
        )

    directory.mkdir(parents=True, exist_ok=True)
    temp_paths: dict[str, Path] = {}
    created: list[Path] = []

    try:
        for artifact in ARTIFACTS:
            rendered = json.dumps(
                payloads[artifact],
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            ) + "\n"
            handle = tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=directory,
                prefix=f".{destinations[artifact].name}.",
                suffix=".tmp",
                delete=False,
            )
            try:
                handle.write(rendered)
                handle.flush()
                os.fsync(handle.fileno())
            finally:
                handle.close()
            temp_paths[artifact] = Path(handle.name)

        for artifact in ARTIFACTS:
            source = temp_paths[artifact]
            destination = destinations[artifact]
            os.link(source, destination)
            created.append(destination)
            source.unlink()
            del temp_paths[artifact]

    except Exception:
        for path in created:
            try:
                path.unlink()
            except FileNotFoundError:
                pass
        for path in temp_paths.values():
            try:
                path.unlink()
            except FileNotFoundError:
                pass
        raise

    return destinations


def write_review_cycle(
    entry_id: str,
    *,
    cycle: Mapping[str, Any] | ReviewCycleSnapshot,
    reviews: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate and append all three Review JSON files for one Review cycle."""
    _validate_entry_id(entry_id)
    snapshot = cycle if isinstance(cycle, ReviewCycleSnapshot) else _parse_cycle(cycle)
    if snapshot.entry_id != entry_id:
        raise ValueError(
            f"entry_id does not match prepared cycle: argument={entry_id} cycle={snapshot.entry_id}"
        )

    _validate_cycle_is_current(snapshot)
    payloads = _build_payloads(snapshot, reviews)
    paths = _write_append_only(snapshot, payloads)

    return {
        "result": "WRITTEN",
        "entry_id": entry_id,
        "review_seq": snapshot.review_seq,
        "paths": {
            artifact: path.relative_to(ARTICLE_ROOT).as_posix()
            for artifact, path in paths.items()
        },
        "verdicts": {artifact: payloads[artifact]["verdict"] for artifact in ARTIFACTS},
        "targets": {
            artifact: asdict(snapshot.targets[artifact])
            for artifact in ARTIFACTS
        },
    }


def _read_stdin_bundle() -> Mapping[str, Any]:
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        raise ValueError(f"stdin must contain one JSON object: {exc}") from exc
    if not isinstance(data, Mapping):
        raise ValueError("stdin must contain one JSON object")
    return data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare_parser = subparsers.add_parser("prepare", help="freeze target SHA/blob and allocate Review Seq")
    prepare_parser.add_argument("entry_id", help="four-digit Entry_ID")

    write_parser = subparsers.add_parser("write", help="write one complete 00/10/20 Review cycle from stdin")
    write_parser.add_argument("entry_id", help="four-digit Entry_ID")

    args = parser.parse_args(argv)

    try:
        if args.command == "prepare":
            cycle = prepare_review_cycle(args.entry_id)
            output = {"result": "READY", "cycle": cycle.to_dict()}
        else:
            bundle = _read_stdin_bundle()
            cycle = bundle.get("cycle")
            reviews = bundle.get("reviews")
            if not isinstance(cycle, Mapping):
                raise ValueError("stdin object must contain object 'cycle'")
            if not isinstance(reviews, Mapping):
                raise ValueError("stdin object must contain object 'reviews'")
            output = write_review_cycle(args.entry_id, cycle=cycle, reviews=reviews)

        print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    except Exception as exc:
        print(
            json.dumps(
                {"result": "ERROR", "error": str(exc)},
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    sys.exit(main())
