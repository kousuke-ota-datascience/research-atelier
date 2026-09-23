"""Deterministic reconciliation of Git Review facts to Investigation Review pointers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from research_atelier.reviewing.handoff import validate_review_handoff_record

REVIEW_STATUSES = (
    "未",
    "レビュー待",
    "要修正",
    "再作業中",
    "再レビュー待",
    "完了",
    "引継済",
    "－（対象外）",
)
SAFE_RELATIONS = ("exact", "stale", "ahead", "diverged", "missing")


@dataclass(frozen=True)
class ReviewReconcileResult:
    outcome: str  # NOOP | UPDATE | BLOCKED
    changes: Mapping[str, Any]
    issues: tuple[str, ...]
    summary: str


def derive_review_eligibility(
    context: Mapping[str, Any] | None,
) -> tuple[bool | None, tuple[str, ...]]:
    """Derive Review eligibility from the frozen canonical Context.

    The adapter owns this derivation. Missing Context is unresolved rather than
    implicitly eligible, preventing caller omission from reopening historical
    null-Question-Type Investigations to Review.
    """
    if context is None:
        return None, ("review_eligibility_context_missing",)
    if context.get("context_state") != "frozen":
        return None, ("review_eligibility_context_not_frozen",)
    return context.get("question_type") is not None, ()


def reconcile_review_state(
    *,
    current_status: str | None,
    current_latest_review_seq: int | None,
    latest_review: Mapping[str, Any] | None,
    history_issues: tuple[str, ...] = (),
    target_relation: str = "missing",
    review_requested: bool = False,
    review_not_applicable: bool = False,
    review_eligible: bool | None = None,
    repair_started: bool = False,
    new_investigation_handoff_completed: bool = False,
    review_handoff: Mapping[str, Any] | None = None,
    source_rq_id: str | None = None,
) -> ReviewReconcileResult:
    """Derive only Review Status / Latest Review Seq; never mutate semantic content."""
    issues: list[str] = list(history_issues)
    status = current_status or "未"
    if status not in REVIEW_STATUSES:
        issues.append(f"unknown_review_status:{status}")
    if target_relation not in SAFE_RELATIONS:
        issues.append(f"unknown_target_relation:{target_relation}")

    # Historical compatibility: eligibility must be deterministically resolved
    # from the frozen 00_context by the adapter. Omission is unsafe and blocks.
    if review_eligible is None:
        issues.append("review_eligibility_unresolved")
    elif not review_eligible:
        review_requested = False
        review_not_applicable = True

    if review_requested and review_not_applicable:
        issues.append("conflicting_review_events")
    if new_investigation_handoff_completed and review_not_applicable:
        issues.append("handoff_conflicts_with_not_applicable")
    if new_investigation_handoff_completed and repair_started:
        issues.append("conflicting_repair_and_handoff_events")
    if new_investigation_handoff_completed and latest_review is None:
        issues.append("handoff_without_review")
    if new_investigation_handoff_completed and review_handoff is None:
        issues.append("handoff_event_without_record")
    if review_handoff is not None and not new_investigation_handoff_completed:
        issues.append("handoff_record_without_completion_event")
    if issues:
        return ReviewReconcileResult("BLOCKED", {}, tuple(sorted(set(issues))), "unsafe Review state")

    desired_status = status
    desired_seq = current_latest_review_seq

    if review_not_applicable:
        if latest_review is not None or repair_started:
            return ReviewReconcileResult(
                "BLOCKED", {}, ("not_applicable_conflicts_with_review_history",), "unsafe Review state"
            )
        desired_status = "－（対象外）"
        desired_seq = None

    elif latest_review is None:
        if repair_started:
            return ReviewReconcileResult(
                "BLOCKED", {}, ("repair_start_without_review",), "unsafe Review state"
            )
        if review_requested:
            if target_relation not in {"exact", "missing"}:
                return ReviewReconcileResult(
                    "BLOCKED", {}, ("review_request_target_not_ready",), "unsafe Review state"
                )
            desired_status = "レビュー待"
            desired_seq = None
        elif status not in {"未", "－（対象外）", "レビュー待"}:
            return ReviewReconcileResult(
                "BLOCKED", {}, ("status_requires_review_history",), "unsafe Review state"
            )

    else:
        seq = latest_review.get("review_seq")
        verdict = latest_review.get("verdict")
        if not isinstance(seq, int) or seq < 1:
            return ReviewReconcileResult(
                "BLOCKED", {}, ("invalid_latest_review_seq",), "unsafe Review state"
            )
        if verdict not in {"PASS", "FINDINGS"}:
            return ReviewReconcileResult(
                "BLOCKED", {}, ("invalid_latest_review_verdict",), "unsafe Review state"
            )
        desired_seq = seq

        if new_investigation_handoff_completed:
            if target_relation != "exact":
                return ReviewReconcileResult(
                    "BLOCKED",
                    {},
                    ("handoff_requires_exact_review_target",),
                    "unsafe Review handoff",
                )
            assert review_handoff is not None
            if source_rq_id is None:
                return ReviewReconcileResult(
                    "BLOCKED",
                    {},
                    ("handoff_source_rq_unresolved",),
                    "unsafe Review handoff",
                )
            handoff_issues = validate_review_handoff_record(
                review_handoff,
                source_review=latest_review,
                source_rq_id=source_rq_id,
            )
            if handoff_issues:
                return ReviewReconcileResult(
                    "BLOCKED",
                    {},
                    handoff_issues,
                    "unsafe Review handoff",
                )
            desired_status = "引継済"

        elif target_relation == "exact":
            if verdict == "PASS":
                if repair_started:
                    return ReviewReconcileResult(
                        "BLOCKED", {}, ("repair_start_after_pass",), "unsafe Review state"
                    )
                desired_status = "完了"
            else:
                if repair_started or status == "再作業中":
                    desired_status = "再作業中"
                else:
                    desired_status = "要修正"

        elif target_relation == "stale":
            if repair_started:
                return ReviewReconcileResult(
                    "BLOCKED", {}, ("repair_start_on_stale_review",), "unsafe Review state"
                )
            desired_status = "再レビュー待"

        else:
            return ReviewReconcileResult(
                "BLOCKED",
                {},
                (f"unsafe_review_target_relation:{target_relation}",),
                "unsafe Review target relation",
            )

    changes: dict[str, Any] = {}
    if desired_status != status:
        changes["Review Status"] = desired_status
    if desired_seq != current_latest_review_seq:
        changes["Latest Review Seq"] = desired_seq

    if changes:
        return ReviewReconcileResult("UPDATE", changes, (), "Review current state requires synchronization")
    return ReviewReconcileResult("NOOP", {}, (), "Review current state already matches canonical facts")


def reconcile_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    """JSON-friendly adapter used by connector-driven Workflow 00/20 orchestration."""
    current = dict(payload.get("current") or {})
    review = dict(payload.get("review") or {})
    events = dict(payload.get("events") or {})
    context_value = payload.get("context")
    context = dict(context_value) if isinstance(context_value, Mapping) else None
    handoff_value = payload.get("handoff")
    handoff = dict(handoff_value) if isinstance(handoff_value, Mapping) else None
    review_eligible, eligibility_issues = derive_review_eligibility(context)
    result = reconcile_review_state(
        current_status=current.get("review_status"),
        current_latest_review_seq=current.get("latest_review_seq"),
        latest_review=review.get("latest"),
        history_issues=tuple(review.get("issues") or ()) + eligibility_issues,
        target_relation=str(review.get("target_relation") or "missing"),
        review_requested=bool(events.get("review_requested", False)),
        review_not_applicable=bool(events.get("review_not_applicable", False)),
        review_eligible=review_eligible,
        repair_started=bool(events.get("repair_started", False)),
        new_investigation_handoff_completed=bool(
            events.get("new_investigation_handoff_completed", False)
        ),
        review_handoff=handoff,
        source_rq_id=(
            str(context.get("rq_id"))
            if context is not None and context.get("rq_id") is not None
            else None
        ),
    )
    return {
        "outcome": result.outcome,
        "changes": dict(result.changes),
        "issues": list(result.issues),
        "summary": result.summary,
    }
