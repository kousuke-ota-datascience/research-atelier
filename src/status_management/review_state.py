"""Read-only normalization of canonical Review JSON facts."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from src.validation.schema_validator import validate_artifact

ARTICLE_ROOT = Path(__file__).resolve().parents[2]
REVIEW_ROOT = ARTICLE_ROOT / "reviews/10_each_lore"
SCHEMA_ROOT = ARTICLE_ROOT / "docs/10_each_lore/0000_tutorial/schemas"
SCHEMAS = {
    "00": "review_00_sources.schema.json",
    "10": "review_10_contents.schema.json",
    "20": "review_20_analysis.schema.json",
}
REVIEW_RE = re.compile(r"^Review_(?P<entry>[0-9]{4})_(?P<artifact>00|10|20)_(?P<seq>[0-9]+)\.json$")


@dataclass(frozen=True)
class ReviewFact:
    artifact: str
    review_seq: int
    target_commit_sha: str
    target_blob_sha: str
    verdict: str
    review_path: Path


@dataclass(frozen=True)
class ReviewSnapshot:
    entry_id: str
    latest: dict[str, ReviewFact]
    all_reviews: tuple[ReviewFact, ...]
    issues: tuple[str, ...]


def load_entry_review_state(entry_id: str) -> ReviewSnapshot:
    directory = REVIEW_ROOT / entry_id
    if not directory.is_dir():
        return ReviewSnapshot(entry_id, {}, (), ())

    facts: list[ReviewFact] = []
    issues: list[str] = []
    seen_keys: set[tuple[str, int]] = set()

    for path in sorted(directory.glob("*.json")):
        match = REVIEW_RE.match(path.name)
        if not match:
            issues.append(f"malformed_review_filename:{path.name}")
            continue
        if match.group("entry") != entry_id:
            issues.append(f"review_entry_mismatch:{path.name}")
            continue
        artifact = match.group("artifact")
        seq = int(match.group("seq"))
        key = (artifact, seq)
        if key in seen_keys:
            issues.append(f"duplicate_review_key:{artifact}:{seq}")
            continue
        seen_keys.add(key)

        result = validate_artifact(path, SCHEMA_ROOT / SCHEMAS[artifact], artifact=f"review_{artifact}")
        if not result.ok or not isinstance(result.data, dict):
            issues.append(f"review_schema_invalid:{path.name}")
            continue
        data = result.data
        if data.get("entry_id") != entry_id or data.get("artifact") != artifact or data.get("review_seq") != seq:
            issues.append(f"review_filename_payload_mismatch:{path.name}")
            continue
        target = data.get("target", {})
        commit = target.get("commit_sha")
        blob = target.get("blob_sha")
        if not commit or not blob:
            issues.append(f"review_missing_target_sha:{path.name}")
            continue
        facts.append(ReviewFact(artifact, seq, commit, blob, str(data.get("verdict")), path))

    latest: dict[str, ReviewFact] = {}
    for fact in sorted(facts, key=lambda x: (x.artifact, x.review_seq)):
        latest[fact.artifact] = fact
    return ReviewSnapshot(entry_id, latest, tuple(facts), tuple(sorted(set(issues))))
