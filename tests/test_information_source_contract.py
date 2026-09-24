"""Information Source and 10_evidence v2.1 schema regression tests."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import unittest

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from research_atelier.validation.schema_validator import validate_data


SCHEMA_ROOT = REPO_ROOT / "schemas" / "v2"


class InformationSourceContractTest(unittest.TestCase):
    def _source(self, source_id: str) -> dict:
        return {
            "schema_version": "2.0.0",
            "artifact_type": "information_source",
            "source_id": source_id,
            "notion_url": "https://www.notion.so/11111111111111111111111111111111",
            "title": "Example source",
            "source_type": "Journal Article",
            "journal_or_publisher": "Example Journal",
            "authors": "A. Researcher",
            "year": 2026,
            "url": "https://example.com/source",
            "doi": "10.0000/example",
            "version_or_edition": None,
            "reliability_note": None
        }

    def test_historical_four_digit_source_id_passes(self) -> None:
        result = validate_data(
            self._source("SRC-0119"),
            SCHEMA_ROOT / "information_source.schema.json",
            artifact="information_source",
        )
        self.assertTrue(result.ok, result.errors)

    def test_post_cutover_six_digit_source_id_passes(self) -> None:
        result = validate_data(
            self._source("SRC-000120"),
            SCHEMA_ROOT / "information_source.schema.json",
            artifact="information_source",
        )
        self.assertTrue(result.ok, result.errors)

    def test_five_digit_source_id_fails(self) -> None:
        result = validate_data(
            self._source("SRC-00120"),
            SCHEMA_ROOT / "information_source.schema.json",
            artifact="information_source",
        )
        self.assertFalse(result.ok)

    def test_historical_10_evidence_20_remains_schema_valid(self) -> None:
        data = json.loads(
            (REPO_ROOT / "tests" / "fixtures" / "v2" / "10_evidence.valid.min.json").read_text(
                encoding="utf-8"
            )
        )
        result = validate_data(
            data,
            SCHEMA_ROOT / "10_evidence.schema.json",
            artifact="10",
        )
        self.assertTrue(result.ok, result.errors)

    def test_new_10_evidence_21_requires_source_snapshot(self) -> None:
        data = {
            "schema_version": "2.1.0",
            "artifact_type": "10_evidence",
            "investigation_id": "INV-000001",
            "rq_id": "RQ-0007",
            "snapshot_at": "2026-09-24T09:00:00Z",
            "sources": [
                {
                    "source_id": "SRC-0119",
                    "source_revision": {
                        "commit_sha": "a" * 40,
                        "blob_sha": "b" * 40
                    },
                    "accessed_at": "2026-09-24T08:50:00Z",
                    "notion_url": "https://www.notion.so/11111111111111111111111111111111"
                }
            ],
            "evidence_items": [
                {
                    "evidence_id": "E0001",
                    "content": "Source-faithful observation.",
                    "source_locator": "p. 1",
                    "selection_reason": None,
                    "note_type": "Result",
                    "direct_quote": None,
                    "provenance": {
                        "source_id": "SRC-0119",
                        "evidence_note": None
                    }
                }
            ]
        }
        result = validate_data(
            data,
            SCHEMA_ROOT / "10_evidence.schema.json",
            artifact="10",
        )
        self.assertTrue(result.ok, result.errors)

        missing = copy.deepcopy(data)
        missing.pop("sources")
        result = validate_data(
            missing,
            SCHEMA_ROOT / "10_evidence.schema.json",
            artifact="10",
        )
        self.assertFalse(result.ok)


if __name__ == "__main__":
    unittest.main()
