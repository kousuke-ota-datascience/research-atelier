"""Git commit/blob binding regression tests for 10_evidence v2.1."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from research_atelier.validation.source_revision_validator import validate_source_revisions


@unittest.skipUnless(shutil.which("git"), "git executable is required")
class SourceRevisionValidatorTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo = Path(self.tempdir.name)
        subprocess.run(["git", "init"], cwd=self.repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=self.repo, check=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=self.repo, check=True)

        source_dir = self.repo / "information_sources"
        source_dir.mkdir()
        source = {
            "schema_version": "2.0.0",
            "artifact_type": "information_source",
            "source_id": "SRC-000120",
            "notion_url": "https://www.notion.so/11111111111111111111111111111111",
            "title": "Example"
        }
        self.source_path = source_dir / "SRC-000120.json"
        self.source_path.write_text(json.dumps(source, indent=2) + "\n", encoding="utf-8")
        subprocess.run(["git", "add", "information_sources/SRC-000120.json"], cwd=self.repo, check=True)
        subprocess.run(["git", "commit", "-m", "source"], cwd=self.repo, check=True, capture_output=True)
        self.commit_sha = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=self.repo,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        self.blob_sha = subprocess.run(
            ["git", "rev-parse", "HEAD:information_sources/SRC-000120.json"],
            cwd=self.repo,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _evidence(self) -> dict:
        return {
            "schema_version": "2.1.0",
            "sources": [
                {
                    "source_id": "SRC-000120",
                    "source_revision": {
                        "commit_sha": self.commit_sha,
                        "blob_sha": self.blob_sha,
                    },
                    "accessed_at": "2026-09-24T09:00:00Z",
                    "notion_url": "https://www.notion.so/11111111111111111111111111111111",
                }
            ],
            "evidence_items": [
                {
                    "evidence_id": "E0001",
                    "provenance": {
                        "source_id": "SRC-000120",
                        "evidence_note": None,
                    },
                }
            ],
        }

    def test_matching_commit_and_blob_pass(self) -> None:
        issues = validate_source_revisions(self._evidence(), repository_root=self.repo)
        self.assertEqual(issues, ())

    def test_blob_mismatch_fails(self) -> None:
        data = self._evidence()
        data["sources"][0]["source_revision"]["blob_sha"] = "0" * 40
        issues = validate_source_revisions(data, repository_root=self.repo)
        self.assertTrue(any(issue.rule_id == "V-SRC-REV-003" for issue in issues), issues)

    def test_dangling_source_reference_fails(self) -> None:
        data = self._evidence()
        data["evidence_items"][0]["provenance"]["source_id"] = "SRC-000121"
        issues = validate_source_revisions(data, repository_root=self.repo)
        self.assertTrue(any(issue.rule_id == "V-SRC-REF-001" for issue in issues), issues)


if __name__ == "__main__":
    unittest.main()
