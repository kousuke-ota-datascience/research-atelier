"""Deterministic Git Review -> Notion Reviews projection helpers.

Git Review files remain the canonical Review authority. This module renders a
human-facing Notion projection from the storage-neutral Review Cycle model and
provides identity/pointer helpers for the connector adapter. It never writes
canonical Review facts back from Notion.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

from research_atelier.reviewing.review_state import ensure_normalized_review


ARTIFACT_LAYERS = ("00_context", "10_evidence", "20_synthesis", "30_analysis")
LAYER_PROPERTY = {
    "00_context": "00 Context",
    "10_evidence": "10 Evidence",
    "20_synthesis": "20 Synthesis",
    "30_analysis": "30 Analysis",
}
SEVERITY_RANK = {"Minor": 1, "Moderate": 2, "Major": 3}


class ReviewProjectionError(ValueError):
    """Raised when canonical Review facts cannot be projected safely."""


class DuplicateReviewProjectionRowError(ReviewProjectionError):
    """Raised when one logical Review identity resolves to multiple Notion rows."""


class AmbiguousInvestigationProjectionRowError(ReviewProjectionError):
    """Raised when an Investigation identity does not resolve exactly once."""


@dataclass(frozen=True)
class NextAction:
    workflow: str
    investigation: str
    resume_from: str
    action: str
    do_not: str
    completion: str


@dataclass(frozen=True)
class ReviewProjection:
    investigation_id: str
    review_seq: int
    title: str
    properties: Mapping[str, Any]
    body_markdown: str
    canonical_path: str
    next_action: NextAction


@dataclass(frozen=True)
class ReviewRowPlan:
    outcome: str  # CREATE | UPDATE | NOOP
    review_url: str | None
    properties: Mapping[str, Any]
    body_markdown: str


def _normalized(review: Mapping[str, Any]) -> dict[str, Any]:
    try:
        return ensure_normalized_review(review)
    except ValueError as exc:
        raise ReviewProjectionError(str(exc)) from exc


def _nonempty_text(value: Any, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ReviewProjectionError(f"{field} must be a non-empty string")
    return value.strip()


def _line_text(value: Any, *, field: str) -> str:
    return " ".join(_nonempty_text(value, field=field).splitlines())


def _notion_datetime(value: str) -> str:
    """Normalize an exact canonical timestamp to Notion's minute-level date surface."""

    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ReviewProjectionError("reviewed_at must be ISO-8601 date-time") from exc
    if parsed.tzinfo is None:
        raise ReviewProjectionError("reviewed_at must include a timezone")
    normalized = parsed.astimezone(timezone.utc).replace(second=0, microsecond=0)
    return normalized.strftime("%Y-%m-%dT%H:%M:00.000Z")


def _identity(review: Mapping[str, Any]) -> tuple[str, int]:
    normalized = _normalized(review)
    investigation_id = _nonempty_text(
        normalized.get("investigation_id"), field="investigation_id"
    )
    review_seq = normalized.get("review_seq")
    if not isinstance(review_seq, int) or review_seq < 1:
        raise ReviewProjectionError("review_seq must be an integer >= 1")
    return investigation_id, review_seq


def _layers(review: Mapping[str, Any]) -> Mapping[str, Mapping[str, Any]]:
    normalized = _normalized(review)
    value = normalized.get("layers")
    if not isinstance(value, Mapping):
        raise ReviewProjectionError("layers must be an object")
    layers: dict[str, Mapping[str, Any]] = {}
    for layer in ARTIFACT_LAYERS:
        item = value.get(layer)
        if not isinstance(item, Mapping):
            raise ReviewProjectionError(f"layers.{layer} must be an object")
        layers[layer] = item
    return layers


def _findings(review: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    findings: list[Mapping[str, Any]] = []
    for layer, layer_record in _layers(review).items():
        layer_findings = layer_record.get("findings", [])
        if not isinstance(layer_findings, list):
            raise ReviewProjectionError(f"layers.{layer}.findings must be an array")
        for finding_index, finding in enumerate(layer_findings):
            if not isinstance(finding, Mapping):
                raise ReviewProjectionError(
                    f"layers.{layer}.findings[{finding_index}] must be an object"
                )
            findings.append(finding)
    return findings


def derive_artifact_outcomes(review: Mapping[str, Any]) -> dict[str, str]:
    """Derive Notion OK/NG from direct layer verdicts plus repair ownership."""

    outcomes: dict[str, str] = {}
    layers = _layers(review)
    for layer in ARTIFACT_LAYERS:
        verdict = layers[layer].get("verdict")
        if verdict not in {"PASS", "FINDINGS"}:
            raise ReviewProjectionError(
                f"unexpected layer verdict for {layer}: {verdict!r}"
            )
        outcomes[layer] = "NG" if verdict == "FINDINGS" else "OK"

    for finding in _findings(review):
        repair_direction = finding.get("repair_direction")
        if not isinstance(repair_direction, Mapping):
            raise ReviewProjectionError("finding.repair_direction must be an object")
        affected_layer = repair_direction.get("affected_layer")
        if affected_layer not in ARTIFACT_LAYERS:
            raise ReviewProjectionError(
                f"unexpected affected_layer: {affected_layer!r}"
            )
        outcomes[str(affected_layer)] = "NG"
    return outcomes


def highest_severity(review: Mapping[str, Any]) -> str | None:
    highest: str | None = None
    for finding in _findings(review):
        severity = finding.get("severity")
        if severity not in SEVERITY_RANK:
            raise ReviewProjectionError(f"unexpected severity: {severity!r}")
        if highest is None or SEVERITY_RANK[str(severity)] > SEVERITY_RANK[highest]:
            highest = str(severity)
    return highest


def _validate_verdict(
    review: Mapping[str, Any],
) -> tuple[str, list[Mapping[str, Any]]]:
    normalized = _normalized(review)
    verdict = normalized.get("verdict")
    if verdict not in {"PASS", "FINDINGS"}:
        raise ReviewProjectionError(f"unexpected verdict: {verdict!r}")
    findings = _findings(normalized)
    expected = "FINDINGS" if findings else "PASS"
    if verdict != expected:
        raise ReviewProjectionError(
            f"verdict/finding mismatch: verdict={verdict}, expected={expected}"
        )
    return str(verdict), findings


def _unique_instructions(findings: Sequence[Mapping[str, Any]]) -> str:
    values: list[str] = []
    for finding in findings:
        repair_direction = finding.get("repair_direction")
        if not isinstance(repair_direction, Mapping):
            raise ReviewProjectionError("finding.repair_direction must be an object")
        instruction = _line_text(
            repair_direction.get("instruction"),
            field="finding.repair_direction.instruction",
        )
        if instruction not in values:
            values.append(instruction)
    return " / ".join(values)


def derive_next_action(review: Mapping[str, Any]) -> NextAction:
    normalized = _normalized(review)
    investigation_id, _ = _identity(normalized)
    verdict, findings = _validate_verdict(normalized)

    if verdict == "PASS":
        return NextAction(
            workflow="Workflow 20",
            investigation=investigation_id,
            resume_from="none",
            action="No repair is required for this reviewed target.",
            do_not="Do not reopen canonical artifacts solely from this PASS Review.",
            completion="Reconcile Review Status = 完了 and Latest Review to this Review cycle.",
        )

    new_investigation = []
    same_investigation = []
    for finding in findings:
        repair_direction = finding.get("repair_direction")
        if not isinstance(repair_direction, Mapping):
            raise ReviewProjectionError("finding.repair_direction must be an object")
        mode = repair_direction.get("mode")
        if mode == "new_investigation":
            new_investigation.append(finding)
        elif mode == "same_investigation":
            same_investigation.append(finding)
        else:
            raise ReviewProjectionError(f"unexpected repair mode: {mode!r}")

    if new_investigation:
        return NextAction(
            workflow="Workflow 00",
            investigation=investigation_id,
            resume_from="new Investigation allocation",
            action=_unique_instructions(findings),
            do_not="Do not repair the frozen/accepted Investigation in place.",
            completion=(
                "Allocate a new Investigation, build and validate its canonical chain, commit, "
                "then run Workflow 20 again when Review is required."
            ),
        )

    affected_layers: list[str] = []
    for finding in same_investigation:
        repair_direction = finding["repair_direction"]
        layer = str(repair_direction.get("affected_layer"))
        if layer == "00_context":
            raise ReviewProjectionError(
                "same_investigation repair of frozen 00_context is unsafe; use new_investigation"
            )
        if layer not in {"10_evidence", "20_synthesis", "30_analysis"}:
            raise ReviewProjectionError(f"unexpected affected_layer: {layer!r}")
        affected_layers.append(layer)

    order = {"10_evidence": 10, "20_synthesis": 20, "30_analysis": 30}
    resume_from = min(affected_layers, key=order.__getitem__)
    do_not = {
        "10_evidence": (
            "Do not allocate a new Investigation; do not reuse stale 20_synthesis/30_analysis "
            "after the Evidence repair."
        ),
        "20_synthesis": (
            "Do not allocate a new Investigation; do not rebuild 10_evidence; "
            "do not reuse stale 30_analysis."
        ),
        "30_analysis": (
            "Do not allocate a new Investigation; do not rebuild 10_evidence; "
            "do not rebuild 20_synthesis."
        ),
    }[resume_from]
    return NextAction(
        workflow="Workflow 10",
        investigation=investigation_id,
        resume_from=resume_from,
        action=_unique_instructions(same_investigation),
        do_not=do_not,
        completion="through-30 PASS → commit → Workflow 20 re-review.",
    )


def _render_summary(
    review: Mapping[str, Any],
    outcomes: Mapping[str, str],
) -> list[str]:
    verdict, findings = _validate_verdict(review)
    severity = highest_severity(review)
    if findings:
        summary = (
            f"{len(findings)} {severity or ''} finding(s) recorded; "
            + ", ".join(f"{layer}={outcomes[layer]}" for layer in ARTIFACT_LAYERS)
            + "."
        )
    else:
        summary = "No semantic finding is recorded for the reviewed target."

    return [
        "# Summary",
        f"- Verdict: {verdict}",
        f"- Findings: {len(findings)}",
        f"- Highest Severity: {severity or 'none'}",
        f"- 00_context: {outcomes['00_context']}",
        f"- 10_evidence: {outcomes['10_evidence']}",
        f"- 20_synthesis: {outcomes['20_synthesis']}",
        f"- 30_analysis: {outcomes['30_analysis']}",
        f"- Summary: {summary}",
    ]


def _render_next_action(action: NextAction) -> list[str]:
    return [
        "# Next Action — Quick Reference",
        f"- Workflow: {action.workflow}",
        f"- Investigation: {action.investigation}",
        f"- Resume from: {action.resume_from}",
        f"- Action: {action.action}",
        f"- Do not: {action.do_not}",
        f"- Completion: {action.completion}",
    ]


def _render_review_details(review: Mapping[str, Any]) -> list[str]:
    lines = ["# Review Details"]
    for layer, layer_record in _layers(review).items():
        review_kind = _nonempty_text(
            layer_record.get("review_kind"),
            field=f"layers.{layer}.review_kind",
        )
        assessment = _line_text(
            layer_record.get("assessment"),
            field=f"layers.{layer}.assessment",
        )
        verdict = layer_record.get("verdict")
        if verdict not in {"PASS", "FINDINGS"}:
            raise ReviewProjectionError(f"unexpected layer verdict: {verdict!r}")
        lines.extend(
            [
                f"## {layer}",
                f"- Review kind: {review_kind}",
                f"- Layer verdict: {verdict}",
                f"**Assessment:** {assessment}",
            ]
        )
        findings = layer_record.get("findings", [])
        if not findings:
            lines.append("**Findings:** none.")
            continue
        for finding_index, finding in enumerate(findings):
            if not isinstance(finding, Mapping):
                raise ReviewProjectionError(
                    f"layers.{layer}.findings[{finding_index}] must be an object"
                )
            finding_id = _nonempty_text(
                finding.get("finding_id"),
                field=f"layers.{layer}.findings[{finding_index}].finding_id",
            )
            severity = finding.get("severity")
            if severity not in SEVERITY_RANK:
                raise ReviewProjectionError(f"unexpected severity: {severity!r}")
            target = _line_text(finding.get("target"), field="finding.target")
            evidence = finding.get("evidence")
            if not isinstance(evidence, list) or not evidence:
                raise ReviewProjectionError("finding.evidence must be a non-empty array")
            evidence_text = "; ".join(
                _line_text(item, field="finding.evidence[]") for item in evidence
            )
            impact = _line_text(finding.get("impact"), field="finding.impact")
            repair_direction = finding.get("repair_direction")
            if not isinstance(repair_direction, Mapping):
                raise ReviewProjectionError("finding.repair_direction must be an object")
            mode = _nonempty_text(
                repair_direction.get("mode"),
                field="repair_direction.mode",
            )
            affected_layer = _nonempty_text(
                repair_direction.get("affected_layer"),
                field="repair_direction.affected_layer",
            )
            instruction = _line_text(
                repair_direction.get("instruction"),
                field="repair_direction.instruction",
            )
            lines.extend(
                [
                    f"### {finding_id}",
                    f"- Severity: {severity}",
                    f"- Target: {target}",
                    f"- Evidence: {evidence_text}",
                    f"- Impact: {impact}",
                    f"- Repair mode: {mode}",
                    f"- Affected layer: {affected_layer}",
                    f"- Repair direction: {instruction}",
                ]
            )
    return lines


def _render_provenance(
    review: Mapping[str, Any],
    *,
    canonical_path: str | None = None,
) -> list[str]:
    normalized = _normalized(review)
    target = normalized.get("target")
    if not isinstance(target, Mapping):
        raise ReviewProjectionError("target must be an object")
    commit_sha = _nonempty_text(target.get("commit_sha"), field="target.commit_sha")
    blob_shas = target.get("artifact_blob_shas")
    if not isinstance(blob_shas, Mapping):
        raise ReviewProjectionError("target.artifact_blob_shas must be an object")
    reviewed_at = _nonempty_text(normalized.get("reviewed_at"), field="reviewed_at")
    paths = normalized.get("canonical_paths")
    if not isinstance(paths, Mapping):
        raise ReviewProjectionError("canonical_paths must be an object")
    manifest_path = canonical_path or _nonempty_text(
        paths.get("manifest"),
        field="canonical_paths.manifest",
    )

    lines = [
        "# Provenance",
        f"- Canonical Review manifest: {manifest_path}",
        f"- Storage format: {_nonempty_text(normalized.get('storage_format'), field='storage_format')}",
        f"- Review target commit SHA: {commit_sha}",
    ]
    if normalized.get("storage_format") == "split_v2":
        for layer in ARTIFACT_LAYERS:
            lines.append(
                f"- {layer} Review JSON: "
                f"{_nonempty_text(paths.get(layer), field=f'canonical_paths.{layer}')}"
            )
    for layer in ARTIFACT_LAYERS:
        lines.append(
            f"- {layer} blob SHA: "
            f"{_nonempty_text(blob_shas.get(layer), field=f'target.artifact_blob_shas.{layer}')}"
        )
    lines.append(f"- Reviewed at: {reviewed_at}")
    return lines


def build_review_projection(
    review: Mapping[str, Any],
    *,
    canonical_path: str | None = None,
) -> ReviewProjection:
    """Render one canonical Review cycle into a deterministic Notion projection."""

    if not isinstance(review, Mapping):
        raise ReviewProjectionError("review must be an object")
    normalized = _normalized(review)
    investigation_id, review_seq = _identity(normalized)
    verdict, _ = _validate_verdict(normalized)
    outcomes = derive_artifact_outcomes(normalized)
    severity = highest_severity(normalized)
    reviewed_at = _nonempty_text(normalized.get("reviewed_at"), field="reviewed_at")
    paths = normalized.get("canonical_paths")
    if not isinstance(paths, Mapping):
        raise ReviewProjectionError("canonical_paths must be an object")
    canonical_path = canonical_path or _nonempty_text(
        paths.get("manifest"),
        field="canonical_paths.manifest",
    )
    title = f"{investigation_id} / Review {review_seq:06d}"
    action = derive_next_action(normalized)

    properties: dict[str, Any] = {
        "Review": title,
        "Review Seq": review_seq,
        "Verdict": verdict,
        "Highest Severity": severity,
        "date:Reviewed At:start": _notion_datetime(reviewed_at),
        "date:Reviewed At:is_datetime": 1,
    }
    for layer in ARTIFACT_LAYERS:
        properties[LAYER_PROPERTY[layer]] = outcomes[layer]

    body_markdown = "\n".join(
        [
            *_render_summary(normalized, outcomes),
            *_render_next_action(action),
            *_render_review_details(normalized),
            *_render_provenance(normalized, canonical_path=canonical_path),
        ]
    ).rstrip()

    return ReviewProjection(
        investigation_id=investigation_id,
        review_seq=review_seq,
        title=title,
        properties=properties,
        body_markdown=body_markdown,
        canonical_path=canonical_path,
        next_action=action,
    )


def resolve_unique_investigation_row(
    rows: Sequence[Mapping[str, Any]],
    *,
    investigation_id: str,
) -> Mapping[str, Any]:
    """Resolve exactly one adapter-normalized Investigation row or fail-stop."""

    matches = [row for row in rows if row.get("investigation_id") == investigation_id]
    if len(matches) != 1:
        raise AmbiguousInvestigationProjectionRowError(
            f"expected exactly one Investigation row for {investigation_id}, found {len(matches)}"
        )
    return matches[0]


def resolve_unique_review_row(
    rows: Sequence[Mapping[str, Any]],
    *,
    investigation_id: str,
    review_seq: int,
) -> Mapping[str, Any] | None:
    """Resolve zero or one adapter-normalized Review row for the logical identity."""

    matches = [
        row
        for row in rows
        if row.get("investigation_id") == investigation_id
        and row.get("review_seq") == review_seq
    ]
    if len(matches) > 1:
        raise DuplicateReviewProjectionRowError(
            f"duplicate Review rows for ({investigation_id}, {review_seq})"
        )
    return matches[0] if matches else None


def plan_review_row(
    review: Mapping[str, Any],
    *,
    existing_rows: Sequence[Mapping[str, Any]],
    canonical_path: str | None = None,
) -> ReviewRowPlan:
    """Plan CREATE/UPDATE/NOOP for one logical Review projection row."""

    projection = build_review_projection(review, canonical_path=canonical_path)
    existing = resolve_unique_review_row(
        existing_rows,
        investigation_id=projection.investigation_id,
        review_seq=projection.review_seq,
    )
    if existing is None:
        return ReviewRowPlan(
            outcome="CREATE",
            review_url=None,
            properties=projection.properties,
            body_markdown=projection.body_markdown,
        )

    review_url = existing.get("url")
    if not isinstance(review_url, str) or not review_url:
        raise ReviewProjectionError("existing Review row must have a URL")
    current_properties = existing.get("properties")
    if not isinstance(current_properties, Mapping):
        raise ReviewProjectionError("existing Review row properties must be an object")
    current_body = existing.get("body_markdown")
    if not isinstance(current_body, str):
        raise ReviewProjectionError("existing Review row body_markdown must be a string")

    properties_match = all(
        current_properties.get(name) == value
        for name, value in projection.properties.items()
    )
    body_matches = current_body.rstrip() == projection.body_markdown
    return ReviewRowPlan(
        outcome="NOOP" if properties_match and body_matches else "UPDATE",
        review_url=review_url,
        properties=projection.properties,
        body_markdown=projection.body_markdown,
    )


def plan_review_projection(
    review: Mapping[str, Any],
    *,
    investigation_rows: Sequence[Mapping[str, Any]],
    existing_review_rows: Sequence[Mapping[str, Any]],
    canonical_path: str | None = None,
) -> ReviewRowPlan:
    """Plan one Review row with a verified exactly-one Investigation binding."""

    projection = build_review_projection(review, canonical_path=canonical_path)
    investigation_row = resolve_unique_investigation_row(
        investigation_rows,
        investigation_id=projection.investigation_id,
    )
    investigation_url = investigation_row.get("url")
    if not isinstance(investigation_url, str) or not investigation_url:
        raise ReviewProjectionError("Investigation row must have a URL")

    base_plan = plan_review_row(
        review,
        existing_rows=existing_review_rows,
        canonical_path=canonical_path,
    )
    desired_properties = dict(base_plan.properties)
    desired_properties["Investigation"] = [investigation_url]

    existing = resolve_unique_review_row(
        existing_review_rows,
        investigation_id=projection.investigation_id,
        review_seq=projection.review_seq,
    )
    if existing is None:
        return ReviewRowPlan(
            outcome="CREATE",
            review_url=None,
            properties=desired_properties,
            body_markdown=base_plan.body_markdown,
        )

    current_properties = existing.get("properties")
    if not isinstance(current_properties, Mapping):
        raise ReviewProjectionError("existing Review row properties must be an object")
    properties_match = all(
        current_properties.get(name) == value
        for name, value in desired_properties.items()
    )
    body_matches = existing.get("body_markdown", "").rstrip() == base_plan.body_markdown
    return ReviewRowPlan(
        outcome="NOOP" if properties_match and body_matches else "UPDATE",
        review_url=base_plan.review_url,
        properties=desired_properties,
        body_markdown=base_plan.body_markdown,
    )


def reconcile_latest_review_relation(
    *,
    current_latest_review_url: str | None,
    latest_review_url: str | None,
    latest_review_exists: bool,
) -> dict[str, Any]:
    """Derive the Notion Latest Review relation mutation."""

    if latest_review_exists and not latest_review_url:
        raise ReviewProjectionError(
            "latest canonical Review exists but Review row URL is missing"
        )
    desired = latest_review_url if latest_review_exists else None
    if current_latest_review_url == desired:
        return {}
    return {"Latest Review": [desired] if desired else []}
