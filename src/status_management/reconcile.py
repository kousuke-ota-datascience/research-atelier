"""Pure reconciliation of Notion, Git, and Review snapshots."""
from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any, Iterable, Mapping


ARTIFACTS = ("00", "10", "20")
ALLOWED_STATUSES = frozenset(
    {"未", "レビュー待", "要修正", "再作業中", "再レビュー待", "完了", "－（対象外）"}
)


@dataclass(frozen=True)
class Mutation:
    artifact: str
    changes: dict[str, Any]


@dataclass(frozen=True)
class ReconcileResult:
    outcome: str
    mutations: tuple[Mutation, ...]
    issues: tuple[str, ...]
    summary: str


def _status_from_review(verdict: str) -> str:
    return "完了" if verdict == "Pass" else "要修正"


def _normalize_changes(cp, changes: dict[str, Any]) -> dict[str, Any]:
    current_by_name = {
        "Status": cp.status,
        "最新レビュー版": cp.latest_review_seq,
        "pre-SHA": cp.pre_sha,
        "post-SHA": cp.post_sha,
        "remarks": cp.remarks,
    }
    return {name: value for name, value in changes.items() if current_by_name.get(name) != value}


def _validate_correction_start(
    artifact: str,
    cp,
    git,
    review,
    *,
    cp_relation: str,
    review_relation: str,
) -> str | None:
    """Return an issue code when a correction-start event is not applicable."""
    if cp.status not in {"要修正", "再作業中"}:
        return f"correction_start_invalid_status:{artifact}:{cp.status}"
    if git is None or not git.exists or not git.commit_sha or not git.blob_sha:
        return f"correction_start_missing_artifact:{artifact}"
    if cp_relation != "exact":
        return f"correction_start_requires_exact_controlplane:{artifact}:{cp_relation}"
    if review is None:
        return f"correction_start_requires_review:{artifact}"
    if review_relation != "exact":
        return f"correction_start_requires_exact_review:{artifact}:{review_relation}"
    if review.target_blob_sha != git.blob_sha:
        return f"review_target_blob_mismatch:{artifact}"
    if review.verdict == "Pass":
        return f"correction_start_on_passed_review:{artifact}"
    return None


def reconcile(
    controlplane_snapshot,
    git_snapshot,
    review_snapshot,
    relations: Mapping[tuple[str, str], str],
    *,
    correction_started: Iterable[str] = (),
) -> ReconcileResult:
    """Derive a mutation plan from already-read facts.

    correction_started is an explicit operational event emitted only after
    Workflow 00 actually enters the correction phase. It is never inferred
    from Entry_ID, Git, or Review facts.
    """
    issues: list[str] = []
    mutations: list[Mutation] = []
    correction_started = frozenset(correction_started)

    unknown_events = sorted(correction_started - set(ARTIFACTS))
    if unknown_events:
        return ReconcileResult(
            "BLOCKED",
            (),
            tuple(f"invalid_correction_start_artifact:{x}" for x in unknown_events),
            "correction-start event contains an unknown artifact",
        )

    if getattr(controlplane_snapshot, "issues", ()):
        return ReconcileResult(
            "BLOCKED",
            (),
            tuple(controlplane_snapshot.issues),
            "control plane snapshot is not uniquely usable",
        )
    if getattr(review_snapshot, "issues", ()):
        return ReconcileResult(
            "BLOCKED",
            (),
            tuple(review_snapshot.issues),
            "review snapshot contains malformed or duplicate facts",
        )

    for artifact in ARTIFACTS:
        cp = controlplane_snapshot.artifacts.get(artifact)
        git = git_snapshot.artifacts.get(artifact)
        review = review_snapshot.latest.get(artifact)

        if cp is None:
            issues.append(f"missing_controlplane:{artifact}")
            continue
        if cp.status not in ALLOWED_STATUSES:
            issues.append(f"invalid_status_value:{artifact}:{cp.status!r}")
            continue

        if artifact in correction_started and cp.status not in {"要修正", "再作業中"}:
            issues.append(f"correction_start_invalid_status:{artifact}:{cp.status}")
            continue

        # Target-outside is explicit operational state; never infer or clear it
        # from Git/Review facts alone.
        if cp.status == "－（対象外）":
            continue

        if git is None or not git.exists:
            if cp.status != "未" or cp.post_sha or review:
                issues.append(f"artifact_missing_but_state_present:{artifact}")
            continue
        if not git.commit_sha or not git.blob_sha:
            issues.append(f"artifact_not_committed:{artifact}")
            continue

        changes: dict[str, Any] = {}
        cp_relation = relations.get(("cp_post", artifact), "missing") if cp.post_sha else "missing"
        review_relation = relations.get(("review_target", artifact), "missing") if review else "missing"

        if artifact in correction_started:
            event_issue = _validate_correction_start(
                artifact,
                cp,
                git,
                review,
                cp_relation=cp_relation,
                review_relation=review_relation,
            )
            if event_issue:
                issues.append(event_issue)
                continue

        if cp.post_sha is None:
            if review is not None:
                issues.append(f"review_exists_before_controlplane_post:{artifact}")
                continue
            if cp.status != "未":
                issues.append(f"missing_post_sha_for_status:{artifact}:{cp.status}")
                continue
            changes["post-SHA"] = git.commit_sha
            changes["Status"] = "レビュー待"

        elif cp_relation == "exact":
            if review is None:
                if cp.latest_review_seq is not None:
                    issues.append(f"review_seq_without_review_file:{artifact}:{cp.latest_review_seq}")
                    continue
                if cp.status == "未":
                    changes["Status"] = "レビュー待"
                elif cp.status not in {"レビュー待"}:
                    issues.append(f"status_requires_review_fact:{artifact}:{cp.status}")
                    continue

            elif review_relation == "exact":
                if review.target_blob_sha != git.blob_sha:
                    issues.append(f"review_target_blob_mismatch:{artifact}")
                    continue
                changes["最新レビュー版"] = review.review_seq
                changes["post-SHA"] = git.commit_sha
                if review.verdict == "Pass":
                    changes["Status"] = "完了"
                elif artifact in correction_started:
                    changes["Status"] = "再作業中"
                elif cp.status == "再作業中":
                    # A sync during active correction must not roll operational
                    # state back to 要修正 merely because the triggering Review
                    # remains the latest Review fact.
                    pass
                else:
                    changes["Status"] = "要修正"

            elif review_relation == "left_ancestor":
                # The latest Review targets an older artifact version. This is
                # normal after a correction commit and before re-review.
                if cp.status in {"要修正", "再作業中", "再レビュー待", "完了"}:
                    changes["最新レビュー版"] = review.review_seq
                    changes["Status"] = "再レビュー待"
                else:
                    issues.append(f"unexpected_stale_review:{artifact}:{cp.status}")
                    continue

            elif review_relation == "right_ancestor":
                issues.append(f"review_target_ahead_of_artifact:{artifact}")
                continue
            else:
                issues.append(f"unsafe_review_sha_relation:{artifact}:{review_relation}")
                continue

        elif cp_relation == "left_ancestor":
            # Git contains a newer canonical artifact than the control-plane
            # checkpoint. Advance pre/post and derive the waiting state.
            changes["pre-SHA"] = cp.post_sha
            changes["post-SHA"] = git.commit_sha

            if review is None:
                changes["Status"] = "再レビュー待" if cp.latest_review_seq else "レビュー待"

            elif review_relation == "exact":
                if review.target_blob_sha != git.blob_sha:
                    issues.append(f"review_target_blob_mismatch:{artifact}")
                    continue
                changes["最新レビュー版"] = review.review_seq
                changes["Status"] = _status_from_review(review.verdict)

            elif review_relation == "left_ancestor":
                changes["最新レビュー版"] = review.review_seq
                changes["Status"] = "再レビュー待"

            elif review_relation == "right_ancestor":
                issues.append(f"review_target_ahead_of_artifact:{artifact}")
                continue
            else:
                issues.append(f"unsafe_review_sha_relation:{artifact}:{review_relation}")
                continue

        else:
            issues.append(f"unsafe_controlplane_sha_relation:{artifact}:{cp_relation}")
            continue

        normalized = _normalize_changes(cp, changes)
        if normalized:
            mutations.append(Mutation(artifact, normalized))

    if issues:
        return ReconcileResult(
            "BLOCKED",
            (),
            tuple(sorted(set(issues))),
            "unsafe or ambiguous state; no mutation generated",
        )
    if mutations:
        return ReconcileResult(
            "UPDATE",
            tuple(mutations),
            (),
            f"{len(mutations)} artifact state(s) require synchronization",
        )
    return ReconcileResult("NOOP", (), (), "control plane already matches Git and Review facts")

def _namespace_map(items: Mapping[str, Mapping[str, Any]]) -> dict[str, SimpleNamespace]:
    return {key: SimpleNamespace(**dict(value)) for key, value in items.items()}


def reconcile_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    """JSON-friendly, I/O-free adapter for connector-driven production sync."""
    cp_data = dict(payload.get("controlplane") or {})
    git_data = dict(payload.get("git") or {})
    review_data = dict(payload.get("review") or {})

    cp = SimpleNamespace(
        artifacts=_namespace_map(cp_data.get("artifacts") or {}),
        issues=tuple(cp_data.get("issues") or ()),
    )
    git = SimpleNamespace(
        artifacts=_namespace_map(git_data.get("artifacts") or {}),
    )
    reviews = SimpleNamespace(
        latest=_namespace_map(review_data.get("latest") or {}),
        issues=tuple(review_data.get("issues") or ()),
    )

    relations: dict[tuple[str, str], str] = {}
    for key, value in dict(payload.get("relations") or {}).items():
        if isinstance(key, str) and ":" in key:
            relation_kind, artifact = key.split(":", 1)
            relations[(relation_kind, artifact)] = str(value)

    events = dict(payload.get("events") or {})
    result = reconcile(
        cp,
        git,
        reviews,
        relations,
        correction_started=events.get("correction_started") or (),
    )
    return {
        "outcome": result.outcome,
        "summary": result.summary,
        "issues": list(result.issues),
        "mutations": [
            {"artifact": mutation.artifact, "changes": dict(mutation.changes)}
            for mutation in result.mutations
        ],
    }

