"""Deterministic guard for Investigation reuse versus new allocation.

BKL-0035 separates workflow retry/repair from a semantically independent
Research execution. The guard does not infer human intent from phrases such as
rerun or try again; callers classify intent and provide material cutoff/snapshot
change explicitly.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

INTENTS = (
    "retry_completion",
    "repair",
    "explicit_new_execution",
    "semantic_reinvestigation",
)

_AUTO_MATERIAL_FIELDS = (
    "rq_id",
    "question_type",
    "scope",
    "include",
    "exclude",
    "assumptions",
    "time_horizon",
    "dataset_boundary",
    "source_boundary",
)


@dataclass(frozen=True)
class AllocationDecision:
    decision: str
    selected_existing_investigation: str | None
    new_investigation_allocated: bool
    semantic_differences: tuple[Mapping[str, Any], ...]
    explicit_new_execution_intent: bool
    intent: str
    reason_codes: tuple[str, ...]
    issues: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "decision": self.decision,
            "selected_existing_investigation": self.selected_existing_investigation,
            "new_investigation_allocated": self.new_investigation_allocated,
            "semantic_differences": [
                {
                    "field": item["field"],
                    "existing": _json_value(item.get("existing")),
                    "requested": _json_value(item.get("requested")),
                    "material": bool(item["material"]),
                    "reason": item["reason"],
                }
                for item in self.semantic_differences
            ],
            "explicit_new_execution_intent": self.explicit_new_execution_intent,
            "intent": self.intent,
            "reason_codes": list(self.reason_codes),
            "issues": list(self.issues),
        }


def _json_value(value: Any) -> Any:
    if isinstance(value, tuple):
        return [_json_value(item) for item in value]
    if isinstance(value, Mapping):
        return {str(key): _json_value(item) for key, item in value.items()}
    return value


def _normalize_sequence(value: Any) -> tuple[Any, ...] | None:
    if value is None:
        return None
    if not isinstance(value, (list, tuple, set, frozenset)):
        return (value,)
    normalized = [_normalize_value(item) for item in value]
    return tuple(sorted(normalized, key=repr))


def _normalize_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return tuple(
            sorted(
                (str(key), _normalize_value(item))
                for key, item in value.items()
            )
        )
    if isinstance(value, (list, tuple, set, frozenset)):
        return _normalize_sequence(value)
    return value


def _semantic_context(context: Mapping[str, Any] | None) -> dict[str, Any]:
    """Extract fields that define Research execution semantics.

    Accepts canonical 00_context objects and partial requested context overlays.
    Missing requested fields mean no requested change, not erase the value.
    """
    if context is None:
        return {}

    boundary_value = context.get("investigation_boundary")
    boundary = dict(boundary_value) if isinstance(boundary_value, Mapping) else {}

    def pick(name: str, *aliases: str) -> Any:
        for key in (name, *aliases):
            if key in context:
                return context.get(key)
            if key in boundary:
                return boundary.get(key)
        return None

    extracted: dict[str, Any] = {}
    fields = {
        "rq_id": pick("rq_id"),
        "question_type": pick("question_type"),
        "scope": pick("scope"),
        "include": pick("include"),
        "exclude": pick("exclude"),
        "assumptions": pick("assumptions"),
        "evidence_cutoff": pick("evidence_cutoff"),
        "time_horizon": pick("time_horizon"),
        "dataset_boundary": pick("dataset_boundary", "dataset"),
        "source_boundary": pick("source_boundary", "sources_boundary"),
    }
    for field, value in fields.items():
        if value is not None:
            if field in {"include", "exclude", "assumptions"}:
                extracted[field] = _normalize_sequence(value)
            else:
                extracted[field] = _normalize_value(value)
    return extracted


def decide_investigation_allocation(
    *,
    intent: str,
    existing_investigation_id: str | None,
    existing_context: Mapping[str, Any] | None,
    requested_context: Mapping[str, Any] | None = None,
    evidence_population_changed: bool | None = None,
) -> AllocationDecision:
    """Decide whether Workflow 00 should reuse or allocate an Investigation.

    requested_context may be partial. Omitted fields inherit existing semantics
    for comparison.

    Evidence-cutoff value changes are special: a timestamp difference alone is
    not proof of a new semantic execution. The caller states whether Evidence
    population/snapshot meaning changed. If unresolved, the guard blocks.
    """
    if intent not in INTENTS:
        return AllocationDecision(
            decision="blocked",
            selected_existing_investigation=existing_investigation_id,
            new_investigation_allocated=False,
            semantic_differences=(),
            explicit_new_execution_intent=False,
            intent=intent,
            reason_codes=("invalid_intent",),
            issues=(f"unknown_intent:{intent}",),
        )

    explicit_new = intent == "explicit_new_execution"

    if existing_investigation_id is None or existing_context is None:
        return AllocationDecision(
            decision="allocate_new",
            selected_existing_investigation=None,
            new_investigation_allocated=True,
            semantic_differences=(),
            explicit_new_execution_intent=explicit_new,
            intent=intent,
            reason_codes=("no_existing_investigation",),
            issues=(),
        )

    existing = _semantic_context(existing_context)
    requested = _semantic_context(requested_context)
    differences: list[dict[str, Any]] = []
    issues: list[str] = []

    for field in (*_AUTO_MATERIAL_FIELDS, "evidence_cutoff"):
        if field not in requested:
            continue
        existing_value = existing.get(field)
        requested_value = requested[field]
        if existing_value == requested_value:
            continue

        if field == "evidence_cutoff":
            if evidence_population_changed is None:
                material = False
                reason = "cutoff_materiality_unresolved"
                issues.append("evidence_cutoff_materiality_unresolved")
            elif evidence_population_changed:
                material = True
                reason = "evidence_population_or_snapshot_changed"
            else:
                material = False
                reason = "timestamp_difference_without_semantic_snapshot_change"
        else:
            material = True
            reason = "context_defining_field_changed"

        differences.append(
            {
                "field": field,
                "existing": existing_value,
                "requested": requested_value,
                "material": material,
                "reason": reason,
            }
        )

    if issues:
        return AllocationDecision(
            decision="blocked",
            selected_existing_investigation=existing_investigation_id,
            new_investigation_allocated=False,
            semantic_differences=tuple(differences),
            explicit_new_execution_intent=explicit_new,
            intent=intent,
            reason_codes=("semantic_difference_unresolved",),
            issues=tuple(sorted(set(issues))),
        )

    material_differences = [item for item in differences if item["material"]]

    if explicit_new:
        return AllocationDecision(
            decision="allocate_new",
            selected_existing_investigation=existing_investigation_id,
            new_investigation_allocated=True,
            semantic_differences=tuple(differences),
            explicit_new_execution_intent=True,
            intent=intent,
            reason_codes=("explicit_independent_execution",),
            issues=(),
        )

    if material_differences:
        return AllocationDecision(
            decision="allocate_new",
            selected_existing_investigation=existing_investigation_id,
            new_investigation_allocated=True,
            semantic_differences=tuple(differences),
            explicit_new_execution_intent=False,
            intent=intent,
            reason_codes=("material_semantic_difference",),
            issues=(),
        )

    if intent == "semantic_reinvestigation":
        return AllocationDecision(
            decision="blocked",
            selected_existing_investigation=existing_investigation_id,
            new_investigation_allocated=False,
            semantic_differences=tuple(differences),
            explicit_new_execution_intent=False,
            intent=intent,
            reason_codes=("semantic_reinvestigation_without_material_difference",),
            issues=("material_semantic_difference_not_identified",),
        )

    reason = (
        "same_semantics_repair"
        if intent == "repair"
        else "same_semantics_retry_or_completion"
    )
    return AllocationDecision(
        decision="reuse_existing",
        selected_existing_investigation=existing_investigation_id,
        new_investigation_allocated=False,
        semantic_differences=tuple(differences),
        explicit_new_execution_intent=False,
        intent=intent,
        reason_codes=(reason,),
        issues=(),
    )


def decide_investigation_allocation_payload(
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    """JSON-friendly adapter for connector-driven Workflow 00 orchestration."""
    existing_value = payload.get("existing")
    existing = dict(existing_value) if isinstance(existing_value, Mapping) else {}
    requested_value = payload.get("requested_context")
    requested = (
        dict(requested_value) if isinstance(requested_value, Mapping) else None
    )
    evidence_change = payload.get("evidence_population_changed")
    if evidence_change not in {None, True, False}:
        return AllocationDecision(
            decision="blocked",
            selected_existing_investigation=existing.get("investigation_id"),
            new_investigation_allocated=False,
            semantic_differences=(),
            explicit_new_execution_intent=False,
            intent=str(payload.get("intent") or ""),
            reason_codes=("invalid_evidence_population_change_flag",),
            issues=("evidence_population_changed_must_be_boolean_or_null",),
        ).as_dict()

    context_value = existing.get("context")
    existing_context = (
        dict(context_value) if isinstance(context_value, Mapping) else None
    )
    return decide_investigation_allocation(
        intent=str(payload.get("intent") or ""),
        existing_investigation_id=existing.get("investigation_id"),
        existing_context=existing_context,
        requested_context=requested,
        evidence_population_changed=evidence_change,
    ).as_dict()
