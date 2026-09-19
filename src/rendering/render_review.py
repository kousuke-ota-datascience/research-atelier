"""Manually render one canonical Review JSON to deterministic Markdown."""
from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys

from src.validation.schema_validator import validate_artifact

ARTICLE_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_ROOT = ARTICLE_ROOT / "docs/10_each_lore/0000_tutorial/schemas"
SCHEMAS = {"00": "review_00_sources.schema.json", "10": "review_10_contents.schema.json", "20": "review_20_analysis.schema.json"}
NAME_RE = re.compile(r"^Review_(?P<entry>[0-9]{4})_(?P<artifact>00|10|20)_(?P<seq>[0-9]+)\.json$")


def _resolve(path_arg: str) -> Path:
    path = Path(path_arg)
    if path.is_file():
        return path.resolve()
    candidate = ARTICLE_ROOT / path
    if candidate.is_file():
        return candidate.resolve()
    raise FileNotFoundError(path_arg)


def _format_checks(checks: dict) -> list[str]:
    lines: list[str] = []
    for name in sorted(checks):
        value = checks[name]
        status = value.get("status") if isinstance(value, dict) else value
        notes = value.get("notes") if isinstance(value, dict) else None
        lines.append(f"- **{name}**: {status}" + (f" — {notes}" if notes else ""))
    return lines


def render(review_path: str) -> Path:
    source = _resolve(review_path)
    match = NAME_RE.match(source.name)
    if not match:
        raise ValueError("review filename must be Review_<Entry_ID>_<Artifact>_<Review_Seq>.json")
    artifact = match.group("artifact")
    result = validate_artifact(source, SCHEMA_ROOT / SCHEMAS[artifact], artifact=f"review_{artifact}")
    if not result.ok or not isinstance(result.data, dict):
        raise ValueError(f"review JSON does not conform to {SCHEMAS[artifact]}")
    data = result.data
    target = data["target"]
    lines = [
        "<!-- GENERATED VIEW. DO NOT EDIT AS CANONICAL REVIEW DATA. -->",
        f"<!-- Source JSON: {source.as_posix()} -->",
        "",
        f"# Review {data['entry_id']} / {data['artifact']} / {data['review_seq']}", "",
        f"- Verdict: **{data['verdict']}**",
        f"- Target artifact: {target['artifact_path']}",
        f"- Target commit: `{target['commit_sha']}`",
        f"- Target blob: `{target['blob_sha']}`",
        f"- Reviewed at: {target['reviewed_at']}",
        "", "## Checks", "",
        *_format_checks(data.get("checks", {})),
    ]
    if artifact == "10":
        r = data["reconstruction"]
        lines += ["", "## Summary Reconstruction", "", "### Blind Decode", "", r["blind_decode"], "", "### Reference Story", "", r["reference_story"], "", "### Structural Probe Matrix", "", "| Probe | Blind | Reference | Difference | Notes |", "|---|---|---|---|---|"]
        for p in sorted(r["probes"], key=lambda x: x["probe_id"]):
            vals = [p.get(k, "") for k in ("probe_id", "blind", "reference", "difference", "notes")]
            lines.append("| " + " | ".join(str(v).replace("|", "\\|").replace("\n", "<br>") for v in vals) + " |")
        ai = r["analysis_invariance"]
        lines += ["", f"Analysis invariance: **{ai['status']}** — {ai['notes']}", "", f"Reconstruction verdict: **{r['verdict']}**"]
    elif artifact == "20":
        s = data["sensemaking_reconstruction"]
        lines += ["", "## Sense-making Reconstruction", "", s["model"], "", f"- Status: {s['status']}", f"- Content refs: {', '.join(s.get('content_refs', []))}", f"- Dimension refs: {', '.join(s.get('dimension_refs', []))}", f"- Evidence refs: {', '.join(s.get('evidence_refs', [])) or '-'}"]
    lines += ["", "## Findings", ""]
    for finding in data.get("findings", []):
        lines += [
            f"### {finding['finding_id']} — {finding['severity']} / {finding['category']}", "",
            f"**Summary:** {finding['summary']}", "",
            f"**Rationale:** {finding['rationale']}", "",
            f"**Impact:** {finding['impact']}", "",
            f"**Fix direction:** {finding['fix_direction']}", "",
        ]
    if data.get("review_notes"):
        lines += ["## Review Notes", "", data["review_notes"], ""]
    entry_id = data["entry_id"]
    output = ARTICLE_ROOT / f"docs/99_work/rendered_10_each_lore/{entry_id}/review/{source.stem}.md"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return output


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("review_json_path")
    args = parser.parse_args(argv)
    print(render(args.review_json_path))
    return 0


if __name__ == "__main__":
    sys.exit(main())
