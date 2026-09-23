"""BKL-0027 semantic Review persistence / reconciliation regression tests."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from research_atelier.reviewing.reconcile import reconcile_payload, reconcile_review_state
from research_atelier.reviewing.review_state import load_review_history
from research_atelier.reviewing.review_writer import (
    ReviewPersistenceError,
    prepare_review_cycle,
    save_review_cycle,
)

SCHEMA = REPO_ROOT / "schemas" / "v2" / "review_cycle.schema.json"
INVESTIGATION_ID = "INV-000001"
SHA_A = "a" * 40
SHA_B = "b" * 40
SHA_C = "c" * 40
SHA_D = "d" * 40
SHA_E = "e" * 40

BLOBS = {
    "00_context": SHA_A,
    "10_evidence": SHA_B,
    "20_synthesis": SHA_C,
    "30_analysis": SHA_D,
}

PASS_BODIES = {
    "source_evidence_note_to_10_evidence": {
        "assessment": "Evidence provenance is semantically sound.",
        "findings": [],
    },
    "10_evidence_to_20_synthesis": {
        "assessment": "Synthesis preserves support and uncertainty.",
        "findings": [],
    },
    "20_synthesis_plus_00_context_to_30_analysis": {
        "assessment": "Analysis is supported within the frozen context.",
        "findings": [],
    },
}

FINDING = {
    "severity": "Moderate",
    "target": "30_analysis.working_answer",
    "evidence": ["20_synthesis:K0001"],
    "impact": "The working answer overstates support.",
    "repair_direction": {
        "mode": "same_investigation",
        "affected_layer": "30_analysis",
        "instruction": "Narrow the claim to the supported boundary.",
    },
}


class ReviewContractTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.review_dir = Path(self.tempdir.name) / "reviews"

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _save(self, *, findings: bool = False) -> dict:
        prepared = prepare_review_cycle(
            INVESTIGATION_ID,
            review_dir=self.review_dir,
            schema_path=SCHEMA,
            target_commit_sha=SHA_E,
            artifact_blob_shas=BLOBS,
        )
        bodies = json.loads(json.dumps(PASS_BODIES))
        if findings:
            bodies["20_synthesis_plus_00_context_to_30_analysis"]["findings"] = [FINDING]
        path = save_review_cycle(
            prepared,
            reviewed_at="2026-09-23T00:00:00Z",
            transition_bodies=bodies,
            current_target_commit_sha=SHA_E,
            current_artifact_blob_shas=BLOBS,
            review_dir=self.review_dir,
            schema_path=SCHEMA,
        )
        return json.loads(path.read_text(encoding="utf-8"))

    def test_pass_cycle_is_saved_append_only_and_seq_increments(self) -> None:
        first = self._save()
        self.assertEqual(first["review_seq"], 1)
        self.assertEqual(first["verdict"], "PASS")
        second = self._save()
        self.assertEqual(second["review_seq"], 2)
        self.assertEqual(
            sorted(p.name for p in self.review_dir.glob("*.json")),
            ["review-000001.json", "review-000002.json"],
        )

    def test_verdict_and_finding_id_are_deterministic(self) -> None:
        record = self._save(findings=True)
        self.assertEqual(record["verdict"], "FINDINGS")
        findings = record["transitions"][2]["findings"]
        self.assertEqual(findings[0]["finding_id"], "F001")

    def test_target_change_after_prepare_fails(self) -> None:
        prepared = prepare_review_cycle(
            INVESTIGATION_ID,
            review_dir=self.review_dir,
            schema_path=SCHEMA,
            target_commit_sha=SHA_E,
            artifact_blob_shas=BLOBS,
        )
        changed = dict(BLOBS)
        changed["30_analysis"] = "f" * 40
        with self.assertRaises(ReviewPersistenceError):
            save_review_cycle(
                prepared,
                reviewed_at="2026-09-23T00:00:00Z",
                transition_bodies=PASS_BODIES,
                current_target_commit_sha=SHA_E,
                current_artifact_blob_shas=changed,
                review_dir=self.review_dir,
                schema_path=SCHEMA,
            )

    def test_history_loader_detects_gap_and_malformed(self) -> None:
        self.review_dir.mkdir(parents=True)
        (self.review_dir / "review-000002.json").write_text("{}", encoding="utf-8")
        history = load_review_history(
            INVESTIGATION_ID,
            review_dir=self.review_dir,
            schema_path=SCHEMA,
        )
        self.assertTrue(history.issues)

    def test_initial_request_becomes_review_waiting(self) -> None:
        result = reconcile_review_state(
            current_status="未",
            current_latest_review_seq=None,
            latest_review=None,
            target_relation="exact",
            review_requested=True,
            review_eligible=True,
        )
        self.assertEqual(result.outcome, "UPDATE")
        self.assertEqual(result.changes["Review Status"], "レビュー待")

    def test_ineligible_review_request_becomes_not_applicable(self) -> None:
        result = reconcile_review_state(
            current_status="レビュー待",
            current_latest_review_seq=None,
            latest_review=None,
            target_relation="missing",
            review_requested=True,
            review_eligible=False,
        )
        self.assertEqual(result.outcome, "UPDATE")
        self.assertEqual(result.changes, {"Review Status": "－（対象外）"})

    def test_payload_derives_historical_null_as_ineligible(self) -> None:
        result = reconcile_payload(
            {
                "current": {
                    "review_status": "レビュー待",
                    "latest_review_seq": None,
                },
                "review": {"latest": None, "target_relation": "missing"},
                "events": {"review_requested": True},
                "context": {
                    "context_state": "frozen",
                    "question_type": None,
                },
            }
        )
        self.assertEqual(result["outcome"], "UPDATE")
        self.assertEqual(result["changes"], {"Review Status": "－（対象外）"})

    def test_payload_derives_concrete_question_type_as_eligible(self) -> None:
        result = reconcile_payload(
            {
                "current": {
                    "review_status": "未",
                    "latest_review_seq": None,
                },
                "review": {"latest": None, "target_relation": "exact"},
                "events": {"review_requested": True},
                "context": {
                    "context_state": "frozen",
                    "question_type": "Descriptive",
                },
            }
        )
        self.assertEqual(result["outcome"], "UPDATE")
        self.assertEqual(result["changes"], {"Review Status": "レビュー待"})

    def test_payload_missing_context_blocks_instead_of_defaulting_eligible(self) -> None:
        result = reconcile_payload(
            {
                "current": {
                    "review_status": "未",
                    "latest_review_seq": None,
                },
                "review": {"latest": None, "target_relation": "exact"},
                "events": {"review_requested": True},
            }
        )
        self.assertEqual(result["outcome"], "BLOCKED")
        self.assertIn("review_eligibility_context_missing", result["issues"])

    def test_pass_becomes_complete(self) -> None:
        record = self._save()
        result = reconcile_review_state(
            current_status="レビュー待",
            current_latest_review_seq=None,
            latest_review=record,
            target_relation="exact",
            review_eligible=True,
        )
        self.assertEqual(result.changes, {"Review Status": "完了", "Latest Review Seq": 1})

    def test_findings_require_explicit_repair_start(self) -> None:
        record = self._save(findings=True)
        finding = reconcile_review_state(
            current_status="レビュー待",
            current_latest_review_seq=None,
            latest_review=record,
            target_relation="exact",
            review_eligible=True,
        )
        self.assertEqual(finding.changes["Review Status"], "要修正")
        repairing = reconcile_review_state(
            current_status="要修正",
            current_latest_review_seq=1,
            latest_review=record,
            target_relation="exact",
            review_eligible=True,
            repair_started=True,
        )
        self.assertEqual(repairing.changes["Review Status"], "再作業中")

    def test_stale_review_becomes_rereview_waiting(self) -> None:
        record = self._save(findings=True)
        result = reconcile_review_state(
            current_status="再作業中",
            current_latest_review_seq=1,
            latest_review=record,
            target_relation="stale",
            review_eligible=True,
        )
        self.assertEqual(result.changes["Review Status"], "再レビュー待")

    def test_malformed_or_duplicate_history_blocks(self) -> None:
        result = reconcile_review_state(
            current_status="レビュー待",
            current_latest_review_seq=None,
            latest_review=None,
            history_issues=("duplicate_review_seq:1",),
            target_relation="exact",
            review_eligible=True,
        )
        self.assertEqual(result.outcome, "BLOCKED")
        self.assertEqual(result.changes, {})

    def test_reconciliation_is_idempotent(self) -> None:
        record = self._save()
        result = reconcile_review_state(
            current_status="完了",
            current_latest_review_seq=1,
            latest_review=record,
            target_relation="exact",
            review_eligible=True,
        )
        self.assertEqual(result.outcome, "NOOP")
        self.assertEqual(result.changes, {})


if __name__ == "__main__":
    unittest.main()
