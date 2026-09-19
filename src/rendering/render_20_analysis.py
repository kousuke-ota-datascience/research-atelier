"""Manually render <Entry_ID>_20_analysis.json to deterministic Markdown."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

from src.status_management.git_state import resolve_artifact_path
from src.validation.schema_validator import validate_artifact

ARTICLE_ROOT = Path(__file__).resolve().parents[2]
SCHEMA = ARTICLE_ROOT / "docs/10_each_lore/0000_tutorial/schemas/20_analysis.schema.json"


def _code(value) -> str:
    if value is None:
        return "-"
    parent = value.get("parent_id")
    return value.get("code_id", "-") + (f" (parent: {parent})" if parent else "")


def render(entry_id: str) -> Path:
    source = resolve_artifact_path(entry_id, "20")
    result = validate_artifact(source, SCHEMA, artifact="20")
    if not result.ok or not isinstance(result.data, dict):
        raise ValueError("analysis JSON does not conform to 20_analysis.schema.json")
    data = result.data
    scope = data["version_scope"]
    lines = [
        "<!-- GENERATED VIEW. DO NOT EDIT AS CANONICAL DATA. -->",
        f"<!-- Source JSON: {source.relative_to(ARTICLE_ROOT).as_posix()} -->",
        "",
        f"# {entry_id} Analysis",
        "",
        f"- Macro category: {data['macro_category']}",
        f"- Entry type: {data['entry_type']}",
        "",
        "## Version Scope", "", scope["description"], "",
        f"- Included variants: {', '.join(scope.get('included_variants', [])) or '-'}",
        f"- Excluded variants: {', '.join(scope.get('excluded_variants', [])) or '-'}",
        f"- Content refs: {', '.join(scope.get('content_refs', [])) or '-'}",
        "",
        "## Dimensions", "",
    ]
    for dim in sorted(data.get("dimensions", []), key=lambda x: x["dimension_id"]):
        lines += [
            f"### {dim['dimension_id']} — {dim['status']}", "",
            f"- Primary: {_code(dim.get('primary'))}",
            f"- Secondary: {', '.join(_code(x) for x in dim.get('secondary', [])) or '-'}",
            f"- Content refs: {', '.join(dim.get('content_refs', [])) or '-'}",
            f"- Evidence refs: {', '.join(dim.get('evidence_refs', [])) or '-'}",
            "", f"**Rationale:** {dim['rationale']}", "", f"**Manifestation:** {dim['manifestation']}", "",
        ]
        gap = dim.get("taxonomy_gap")
        if gap:
            lines += [f"Taxonomy gap: {gap.get('present')}" + (f" — {gap.get('description')}" if gap.get("description") else ""), ""]
    if data.get("analysis_notes"):
        lines += ["## Analysis Notes", "", data["analysis_notes"], ""]
    output = ARTICLE_ROOT / f"docs/99_work/rendered_10_each_lore/{entry_id}/{entry_id}_20_analysis.md"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return output


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("entry_id")
    args = parser.parse_args(argv)
    print(render(args.entry_id))
    return 0


if __name__ == "__main__":
    sys.exit(main())
