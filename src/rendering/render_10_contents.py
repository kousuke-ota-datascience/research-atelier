"""Manually render <Entry_ID>_10_contents.json to deterministic Markdown."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

from src.status_management.git_state import resolve_artifact_path
from src.validation.schema_validator import validate_artifact

ARTICLE_ROOT = Path(__file__).resolve().parents[2]
SCHEMA = ARTICLE_ROOT / "docs/10_each_lore/0000_tutorial/schemas/10_contents.schema.json"


def _display_structured(value: dict) -> str:
    status = value.get("status")
    actual = value.get("value")
    if actual is None:
        return str(status)
    if isinstance(actual, list):
        actual = "; ".join(str(x) for x in actual)
    return f"{status}: {actual}"


def render(entry_id: str) -> Path:
    source = resolve_artifact_path(entry_id, "10")
    result = validate_artifact(source, SCHEMA, artifact="10")
    if not result.ok or not isinstance(result.data, dict):
        raise ValueError("content JSON does not conform to 10_contents.schema.json")
    data = result.data
    lines = [
        "<!-- GENERATED VIEW. DO NOT EDIT AS CANONICAL DATA. -->",
        f"<!-- Source JSON: {source.relative_to(ARTICLE_ROOT).as_posix()} -->",
        "",
        f"# {entry_id} {data['lore_name']}",
        "",
        "## Summary",
        "",
        data["summary"]["narrative"],
        "",
        "Coverage refs: " + ", ".join(data["summary"].get("coverage_refs", [])),
        "",
        "### Structure",
        "",
    ]
    for key, value in data["summary"]["structure"].items():
        lines.append(f"- **{key}**: {_display_structured(value)}")
    lines += ["", "## Content Units", ""]
    for item in data.get("content_units", []):
        lines += [f"### {item['content_id']} — {item['type']}", "", item["text"], "", f"Evidence: {', '.join(item.get('evidence_refs', [])) or '-'}", ""]
        if item.get("notes"):
            lines += [f"Notes: {item['notes']}", ""]
    lines += ["## Variants", ""]
    for item in data.get("variants", []):
        lines += [
            f"### {item['variant_id']} — {item['kind']}", "", item["description"], "",
            f"Content refs: {', '.join(item.get('content_refs', [])) or '-'}", "",
            f"Evidence refs: {', '.join(item.get('evidence_refs', [])) or '-'}", "",
        ]
        if item.get("attestation"):
            lines += [f"Attestation: {item['attestation']}", ""]
        if item.get("notes"):
            lines += [f"Notes: {item['notes']}", ""]
    lines += ["## Uncertainties", ""]
    for item in data.get("uncertainties", []):
        refs = [*(item.get("content_refs", [])), *(item.get("evidence_refs", []))]
        lines.append(f"- {item['text']}" + (f" ({', '.join(refs)})" if refs else ""))
    output = ARTICLE_ROOT / f"docs/99_work/rendered_10_each_lore/{entry_id}/{entry_id}_10_contents.md"
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
