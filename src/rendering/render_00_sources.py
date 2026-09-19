"""Manually render <Entry_ID>_00_sources.json to deterministic Markdown."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

from src.status_management.git_state import resolve_artifact_path
from src.validation.schema_validator import validate_artifact

ARTICLE_ROOT = Path(__file__).resolve().parents[2]
SCHEMA = ARTICLE_ROOT / "docs/10_each_lore/0000_tutorial/schemas/00_sources.schema.json"


def _cell(value) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        value = ", ".join(str(x) for x in value)
    return str(value).replace("|", "\\|").replace("\n", "<br>")


def render(entry_id: str) -> Path:
    source = resolve_artifact_path(entry_id, "00")
    result = validate_artifact(source, SCHEMA, artifact="00")
    if not result.ok or not isinstance(result.data, dict):
        raise ValueError("source JSON does not conform to 00_sources.schema.json")
    data = result.data
    lines = [
        "<!-- GENERATED VIEW. DO NOT EDIT AS CANONICAL DATA. -->",
        f"<!-- Source JSON: {source.relative_to(ARTICLE_ROOT).as_posix()} -->",
        "",
        f"# {entry_id} Sources / Evidence",
        "",
        "## Sources",
        "",
        "| Source ID | Type | Title | Locator | Accessed | Relation to primary | Evidence role | URL | Bibliographic info | Archive info | Notes |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for item in data.get("sources", []):
        lines.append("| " + " | ".join(_cell(item.get(k)) for k in ("source_id", "source_type", "title", "locator", "accessed_at", "relation_to_primary", "evidence_role", "url", "bibliographic_info", "archive_info", "notes")) + " |")
    lines += ["", "## Evidence", "", "| Evidence ID | Source ID | Locator | Representation | Content | Uncertainty | Notes |", "|---|---|---|---|---|---|---|"]
    for item in data.get("evidence", []):
        lines.append("| " + " | ".join(_cell(item.get(k)) for k in ("evidence_id", "source_id", "locator", "representation", "content", "uncertainty", "notes")) + " |")
    if data.get("notes"):
        lines += ["", "## Notes", "", str(data["notes"])]
    output = ARTICLE_ROOT / f"docs/99_work/rendered_10_each_lore/{entry_id}/{entry_id}_00_sources.md"
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
