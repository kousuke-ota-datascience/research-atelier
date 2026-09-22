"""Deterministic rendering and section-level patching for RQ Working Answer bodies.

The canonical analysis remains the accepted Git ``30_analysis`` artifact. This
module only renders and patches the derived Notion current view.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Mapping, Sequence

WORKING_ANSWER_HEADING = "# Working Answer"
_EMPTY_NOTION_BODY = "<empty-block/>"
_H1_RE = re.compile(r"^#\\s+.+")
_TARGET_H1_RE = re.compile(r"^#\\s+Working Answer(?:\\s+\\{[^}]*\\})?\\s*$")


class DuplicateWorkingAnswerSectionError(ValueError):
    """Raised when more than one top-level Working Answer section exists."""


@dataclass(frozen=True)
class PatchResult:
    """Result of applying the deterministic Working Answer section patch."""

    markdown: str
    action: str  # CREATE | REPLACE | NOOP


def _nonempty_text(value: Any, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value.strip()


def _render_bullets(items: Sequence[str]) -> list[str]:
    return [f"- {_nonempty_text(item, field='list item')}" for item in items]


def _object_texts(items: Any, *, text_key: str, field: str) -> list[str]:
    if items is None:
        return []
    if not isinstance(items, list):
        raise ValueError(f"{field} must be an array")
    rendered: list[str] = []
    for index, item in enumerate(items):
        if not isinstance(item, Mapping):
            raise ValueError(f"{field}[{index}] must be an object")
        rendered.append(_nonempty_text(item.get(text_key), field=f"{field}[{index}].{text_key}"))
    return rendered


def _string_items(items: Any, *, field: str) -> list[str]:
    if items is None:
        return []
    if not isinstance(items, list):
        raise ValueError(f"{field} must be an array")
    return [_nonempty_text(item, field=f"{field}[{index}]") for index, item in enumerate(items)]


def render_working_answer_section(analysis: Mapping[str, Any]) -> str:
    """Render accepted ``30_analysis`` into the canonical Notion body section.

    ``Answer`` is always emitted. Optional list sections are omitted when the
    corresponding accepted analysis field is absent or empty. Internal
    lineage identifiers (J#### / K####) are intentionally not rendered.
    """

    if not isinstance(analysis, Mapping):
        raise ValueError("analysis must be an object")

    working_answer = analysis.get("working_answer")
    if not isinstance(working_answer, Mapping):
        raise ValueError("working_answer must be an object")
    answer_text = _nonempty_text(working_answer.get("text"), field="working_answer.text")

    judgments = _object_texts(analysis.get("judgments", []), text_key="statement", field="judgments")
    limitations = _object_texts(analysis.get("limitations", []), text_key="text", field="limitations")
    unresolved = _string_items(analysis.get("unresolved_questions", []), field="unresolved_questions")
    alternatives = _object_texts(
        analysis.get("alternative_interpretations", []),
        text_key="text",
        field="alternative_interpretations",
    )

    blocks: list[str] = [WORKING_ANSWER_HEADING, "", "## Answer", answer_text]

    for title, items in (
        ("Key Judgments", judgments),
        ("Limitations", limitations),
        ("Unresolved Questions", unresolved),
        ("Alternative Interpretations", alternatives),
    ):
        if items:
            blocks.extend(["", f"## {title}", *_render_bullets(items)])

    return "\n".join(blocks).rstrip()


def _top_level_heading_positions(markdown: str) -> tuple[list[int], list[int]]:
    """Return (all H1 line indices, target H1 line indices), ignoring code fences."""

    h1_positions: list[int] = []
    target_positions: list[int] = []
    in_fence = False

    for index, line in enumerate(markdown.splitlines()):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if _H1_RE.match(line) and not line.startswith("##"):
            h1_positions.append(index)
            if _TARGET_H1_RE.match(line):
                target_positions.append(index)

    return h1_positions, target_positions


def _section_bounds(markdown: str) -> tuple[int, int] | None:
    lines = markdown.splitlines()
    h1_positions, targets = _top_level_heading_positions(markdown)
    if len(targets) > 1:
        raise DuplicateWorkingAnswerSectionError(
            "multiple top-level '# Working Answer' headings found; projection is BLOCKED"
        )
    if not targets:
        return None

    start = targets[0]
    next_h1 = next((position for position in h1_positions if position > start), len(lines))
    return start, next_h1


def patch_working_answer_section(page_markdown: str, analysis: Mapping[str, Any]) -> PatchResult:
    """Create/replace only the top-level ``# Working Answer`` section.

    The rest of the RQ page body is preserved byte-for-byte at line granularity.
    A duplicate target heading is treated as an unsafe ambiguity and raises
    ``DuplicateWorkingAnswerSectionError``.
    """

    if not isinstance(page_markdown, str):
        raise ValueError("page_markdown must be a string")

    rendered = render_working_answer_section(analysis)
    body = page_markdown
    if body.strip() in {"", _EMPTY_NOTION_BODY}:
        return PatchResult(markdown=rendered, action="CREATE")

    bounds = _section_bounds(body)
    if bounds is None:
        separator = "" if body.endswith("\n\n") else ("\n" if body.endswith("\n") else "\n\n")
        return PatchResult(markdown=f"{body}{separator}{rendered}", action="CREATE")

    lines = body.splitlines()
    start, end = bounds
    current = "\n".join(lines[start:end]).rstrip()
    if current == rendered:
        return PatchResult(markdown=body, action="NOOP")

    replacement_lines = rendered.splitlines()
    patched_lines = [*lines[:start], *replacement_lines, *lines[end:]]
    return PatchResult(markdown="\n".join(patched_lines), action="REPLACE")


def working_answer_section_matches(page_markdown: str, analysis: Mapping[str, Any]) -> bool:
    """Return whether the unique body section equals the current deterministic rendering."""

    if not isinstance(page_markdown, str):
        raise ValueError("page_markdown must be a string")
    bounds = _section_bounds(page_markdown)
    if bounds is None:
        return False
    lines = page_markdown.splitlines()
    start, end = bounds
    current = "\n".join(lines[start:end]).rstrip()
    return current == render_working_answer_section(analysis)


def working_answer_projection_state(page_markdown: str, analysis: Mapping[str, Any]) -> str:
    """Derive body projection state for Workflow 00 completion logic.

    Returns one of ``MISSING``, ``STALE``, ``CURRENT``, or ``BLOCKED``.
    ``BLOCKED`` is reserved for ambiguous duplicate target headings.
    """

    try:
        bounds = _section_bounds(page_markdown)
    except DuplicateWorkingAnswerSectionError:
        return "BLOCKED"
    if bounds is None:
        return "MISSING"
    return "CURRENT" if working_answer_section_matches(page_markdown, analysis) else "STALE"


def build_projection_log_v2(
    *,
    target_rq_url: str,
    rq_id: str,
    source_investigation_id: str,
    source_30_analysis_commit_sha: str,
    projection_timestamp: str,
    result: str,
    note: str | None = None,
) -> dict[str, Any]:
    """Build the v2 body-section projection provenance record.

    Historical v1 ``projection_log.json`` records use ``target_property`` and
    are intentionally left untouched. New body projections use the structured
    ``projection_target`` field and are written separately as
    ``projection_log_v2.json``.
    """

    normalized_result = result.upper()
    if normalized_result not in {"SUCCESS", "FAILURE"}:
        raise ValueError("result must be SUCCESS or FAILURE")

    record: dict[str, Any] = {
        "schema_version": "2.0.0",
        "report_type": "projection_log",
        "target_rq_url": _nonempty_text(target_rq_url, field="target_rq_url"),
        "rq_id": _nonempty_text(rq_id, field="rq_id"),
        "source_investigation_id": _nonempty_text(
            source_investigation_id, field="source_investigation_id"
        ),
        "source_30_analysis_commit_sha": _nonempty_text(
            source_30_analysis_commit_sha, field="source_30_analysis_commit_sha"
        ),
        "projection_timestamp": _nonempty_text(projection_timestamp, field="projection_timestamp"),
        "projection_target": {
            "surface": "page_body",
            "section_heading": WORKING_ANSWER_HEADING,
        },
        "result": normalized_result,
    }
    if note is not None and note.strip():
        record["note"] = note.strip()
    return record
