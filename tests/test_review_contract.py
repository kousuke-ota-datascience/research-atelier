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

from research_atelier.reviewing.handoff import plan_review_handoff
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

PASS_LAYERS = {
    "00_context": {
        "assessment": "Frozen Investigation Context is semantically coherent.",
        "findings": [],
    },
    "10_evidence": {
        "assessment": "Evidence provenance is semantically sound.",
        "findings": [],
    },
    "20_synthesis": {
        "assessment": "Synthesis preserves support and uncertainty.",
        "findings": [],
    },
    "30_analysis": {
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

NEW_INVESTIGATION_FINDING = {
    "severity": "Major",
    "target": "00_context.investigation_boundary.scope",
    "evidence": ["00_context:investigation_boundary.scope"],
    "impact": "The finding cannot be repaired without changing frozen Context semantics.",
    "repair_direction": {
        "mode": "new_investigation",
        "affected_layer": "00_context",
        "instruction": "Create a successor Investigation with the corrected frozen Context.",
    },
}

SOURCE_RQ_ID = "RQ-0001"
SUCCESSOR_ID = "INV-000002"


class ReviewContractTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.review_dir = Path(self.tempdir.name) / "reviews"

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _save(self, *, findings: bool = False, new_investigation: bool = False) -> dict:
        prepared = prepare_review_cycle(
            INVESTIGATION_ID,
            review_dir=self.review_dir,
            schema_path=SCHEMA,
            target_commit_sha=SHA_E,
            artifact_blob_shas=BLOBS,
        )
        layers = json.loads(json.dumps(PASS_LAYERS))
        if findings:
            if new_investigation:
                layers["00_context"]["findings"] = [NEW_INVESTIGATION_FINDING]
            else:
                layers["30_analysis"]["findings"] = [FINDING]
        save_review_cycle(
            prepared,
            reviewed_at="2026-09-23T00:00:00Z",
            layer_bodies=layers,
            current_target_commit_sha=SHA_E,
            current_artifact_blob_shas=BLOBS,
            review_dir=self.review_dir,
            schema_path=SCHEMA,
        )
        history = load_review_history(
            INVESTIGATION_ID,
            review_dir=self.review_dir,
            schema_path=SCHEMA,
        )
        self.assertEqual(history.issues, ())
        assert history.latest is not None
        return dict(history.latest)

    def test_pass_cycle_is_saved_append_only_and_seq_increments(self) -> None:
        first = self._save()
        self.assertEqual(first["review_seq"], 1)
        self.assertEqual(first["verdict"], "PASS")
        second = self._save()
        self.assertEqual(second["review_seq"], 2)
        self.assertEqual(
            sorted(p.name for p in self.review_dir.glob("*.json")),
            [
                "review-000001.json",
                "review-000002.json",
                "review_00_000001.json",
                "review_00_000002.json",
                "review_10_000001.json",
                "review_10_000002.json",
                "review_20_000001.json",
                "review_20_000002.json",
                "review_30_000001.json",
                "review_30_000002.json",
            ],
        )

    def test_verdict_and_finding_id_are_deterministic(self) -> None:
        record = self._save(findings=True)
        self.assertEqual(record["verdict"], "FINDINGS")
        findings = record["layers"]["30_analysis"]["findings"]
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
                layer_bodies=PASS_LAYERS,
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

    def test_legacy_seq1_and_split_seq2_load_as_one_history(self) -> None:
        legacy_source = (
            REPO_ROOT
            / "investigations"
            / "INV-000015"
            / "reviews"
            / "review-000001.json"
        )
        legacy = json.loads(legacy_source.read_text(encoding="utf-8"))
        self.review_dir.mkdir(parents=True)
        (self.review_dir / "review-000001.json").write_text(
            json.dumps(legacy, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        prepared = prepare_review_cycle(
            "INV-000015",
            review_dir=self.review_dir,
            schema_path=SCHEMA,
            target_commit_sha=legacy["target"]["commit_sha"],
            artifact_blob_shas=legacy["target"]["artifact_blob_shas"],
        )
        self.assertEqual(prepared.review_seq, 2)
        save_review_cycle(
            prepared,
            reviewed_at="2026-09-23T06:00:00Z",
            layer_bodies=PASS_LAYERS,
            current_target_commit_sha=legacy["target"]["commit_sha"],
            current_artifact_blob_shas=legacy["target"]["artifact_blob_shas"],
            review_dir=self.review_dir,
            schema_path=SCHEMA,
        )
        history = load_review_history(
            "INV-000015",
            review_dir=self.review_dir,
            schema_path=SCHEMA,
        )
        self.assertEqual(history.issues, ())
        self.assertEqual(
            [record["storage_format"] for record in history.records],
            ["legacy_single", "split_v2"],
        )

    def test_orphan_split_layer_blocks_history(self) -> None:
        self.review_dir.mkdir(parents=True)
        (self.review_dir / "review_00_000001.json").write_text(
            "{}\n",
            encoding="utf-8",
        )
        history = load_review_history(
            INVESTIGATION_ID,
            review_dir=self.review_dir,
            schema_path=SCHEMA,
        )
        self.assertTrue(
            any(issue.startswith("orphan_review_layer:") for issue in history.issues)
        )

    def test_legacy_schema_paths_are_explicitly_deprecated(self) -> None:
        schema_dir = REPO_ROOT / "schemas" / "v2"
        for name in ("review_common.schema.json", "review_cycle.schema.json"):
            schema = json.loads((schema_dir / name).read_text(encoding="utf-8"))
            self.assertTrue(schema.get("deprecated"), name)
            self.assertIn("DEPRECATED", schema.get("title", ""))
            self.assertIn("Do not use", schema.get("description", ""))

        current_schema_names = (
            "review_manifest.schema.json",
            "review_00_context.schema.json",
            "review_10_evidence.schema.json",
            "review_20_synthesis.schema.json",
            "review_30_analysis.schema.json",
        )
        for name in current_schema_names:
            text = (schema_dir / name).read_text(encoding="utf-8")
            self.assertIn("review_layer_common.schema.json", text)
            self.assertNotIn('"$ref": "review_common.schema.json', text)

    def test_legacy_schema_compatibility_redirect_validates_historical_review(self) -> None:
        historical = json.loads(
            (
                REPO_ROOT
                / "investigations"
                / "INV-000015"
                / "reviews"
                / "review-000001.json"
            ).read_text(encoding="utf-8")
        )
        from research_atelier.validation.schema_validator import validate_data

        result = validate_data(
            historical,
            REPO_ROOT / "schemas" / "v2" / "review_cycle.schema.json",
            artifact="legacy-review-compat",
        )
        self.assertTrue(result.ok, result.errors)

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

    def test_inv_000008_explicit_review_request_remains_not_applicable(self) -> None:
        context = json.loads(
            (REPO_ROOT / "investigations" / "INV-000008" / "00_context.json").read_text(
                encoding="utf-8"
            )
        )
        result = reconcile_payload(
            {
                "current": {
                    "review_status": "未",
                    "latest_review_seq": None,
                },
                "review": {"latest": None, "target_relation": "missing"},
                "events": {"review_requested": True},
                "context": context,
            }
        )
        self.assertEqual(result["outcome"], "UPDATE")
        self.assertEqual(result["changes"], {"Review Status": "－（対象外）"})
        self.assertFalse(
            (REPO_ROOT / "investigations" / "INV-000008" / "reviews").exists()
        )

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

    def _valid_allocation_decision(self) -> dict:
        return {
            "decision": "allocate_new",
            "selected_existing_investigation": INVESTIGATION_ID,
            "new_investigation_allocated": True,
            "semantic_differences": [
                {
                    "field": "scope",
                    "existing": "old scope",
                    "requested": "corrected scope",
                    "material": True,
                    "reason": "context_defining_field_changed",
                }
            ],
            "explicit_new_execution_intent": False,
            "intent": "repair",
            "reason_codes": ["material_semantic_difference"],
            "issues": [],
        }

    def _valid_handoff(self, record: dict, *, existing: dict | None = None):
        return plan_review_handoff(
            source_review=record,
            source_rq_id=SOURCE_RQ_ID,
            allocation_decision=self._valid_allocation_decision(),
            successor={
                "exists": True,
                "investigation_id": SUCCESSOR_ID,
                "rq_ids": [SOURCE_RQ_ID],
            },
            handoff_at="2026-09-24T00:00:00Z",
            existing_handoff=existing,
        )

    def test_new_investigation_finding_alone_does_not_close_review(self) -> None:
        record = self._save(findings=True, new_investigation=True)
        result = reconcile_review_state(
            current_status="レビュー待",
            current_latest_review_seq=None,
            latest_review=record,
            target_relation="exact",
            review_eligible=True,
        )
        self.assertEqual(
            result.changes,
            {"Review Status": "要修正", "Latest Review Seq": 1},
        )

    def test_valid_successor_handoff_transitions_to_terminal_state(self) -> None:
        record = self._save(findings=True, new_investigation=True)
        plan = self._valid_handoff(record)
        self.assertEqual(plan.outcome, "CREATE")
        self.assertIsNotNone(plan.record)
        assert plan.record is not None
        result = reconcile_review_state(
            current_status="要修正",
            current_latest_review_seq=1,
            latest_review=record,
            target_relation="exact",
            review_eligible=True,
            new_investigation_handoff_completed=True,
            review_handoff=plan.record,
            source_rq_id=SOURCE_RQ_ID,
        )
        self.assertEqual(result.outcome, "UPDATE")
        self.assertEqual(result.changes, {"Review Status": "引継済"})
        self.assertEqual(record["verdict"], "FINDINGS")

    def test_handoff_plan_is_idempotent_and_preserves_original_timestamp(self) -> None:
        record = self._save(findings=True, new_investigation=True)
        first = self._valid_handoff(record)
        assert first.record is not None
        second = plan_review_handoff(
            source_review=record,
            source_rq_id=SOURCE_RQ_ID,
            allocation_decision=self._valid_allocation_decision(),
            successor={
                "exists": True,
                "investigation_id": SUCCESSOR_ID,
                "rq_ids": [SOURCE_RQ_ID],
            },
            handoff_at="2026-09-24T01:00:00Z",
            existing_handoff=first.record,
        )
        self.assertEqual(second.outcome, "NOOP")
        self.assertEqual(second.record["handoff_at"], "2026-09-24T00:00:00Z")

    def test_handoff_blocks_until_successor_persisted_and_exactly_bound(self) -> None:
        record = self._save(findings=True, new_investigation=True)
        missing = plan_review_handoff(
            source_review=record,
            source_rq_id=SOURCE_RQ_ID,
            allocation_decision=self._valid_allocation_decision(),
            successor={
                "exists": False,
                "investigation_id": SUCCESSOR_ID,
                "rq_ids": [SOURCE_RQ_ID],
            },
            handoff_at="2026-09-24T00:00:00Z",
        )
        self.assertEqual(missing.outcome, "BLOCKED")
        self.assertIn("successor_investigation_not_persisted", missing.issues)

        bad_binding = plan_review_handoff(
            source_review=record,
            source_rq_id=SOURCE_RQ_ID,
            allocation_decision=self._valid_allocation_decision(),
            successor={
                "exists": True,
                "investigation_id": SUCCESSOR_ID,
                "rq_ids": ["RQ-9999"],
            },
            handoff_at="2026-09-24T00:00:00Z",
        )
        self.assertEqual(bad_binding.outcome, "BLOCKED")
        self.assertIn("successor_rq_binding_not_exact", bad_binding.issues)

    def test_handoff_blocks_without_allocate_new_versioning_decision(self) -> None:
        record = self._save(findings=True, new_investigation=True)
        decision = self._valid_allocation_decision()
        decision["decision"] = "reuse_existing"
        decision["new_investigation_allocated"] = False
        plan = plan_review_handoff(
            source_review=record,
            source_rq_id=SOURCE_RQ_ID,
            allocation_decision=decision,
            successor={
                "exists": True,
                "investigation_id": SUCCESSOR_ID,
                "rq_ids": [SOURCE_RQ_ID],
            },
            handoff_at="2026-09-24T00:00:00Z",
        )
        self.assertEqual(plan.outcome, "BLOCKED")
        self.assertIn("versioning_decision_not_allocate_new", plan.issues)

    def test_handoff_event_without_canonical_record_blocks(self) -> None:
        record = self._save(findings=True, new_investigation=True)
        result = reconcile_review_state(
            current_status="要修正",
            current_latest_review_seq=1,
            latest_review=record,
            target_relation="exact",
            review_eligible=True,
            new_investigation_handoff_completed=True,
        )
        self.assertEqual(result.outcome, "BLOCKED")
        self.assertIn("handoff_event_without_record", result.issues)

    def test_handoff_payload_reconciliation_is_idempotent(self) -> None:
        record = self._save(findings=True, new_investigation=True)
        plan = self._valid_handoff(record)
        assert plan.record is not None
        payload = {
            "current": {
                "review_status": "引継済",
                "latest_review_seq": 1,
            },
            "review": {"latest": record, "target_relation": "exact"},
            "handoff": plan.record,
            "events": {"new_investigation_handoff_completed": True},
            "context": {
                "context_state": "frozen",
                "question_type": "Descriptive",
                "rq_id": SOURCE_RQ_ID,
            },
        }
        result = reconcile_payload(payload)
        self.assertEqual(result["outcome"], "NOOP")
        self.assertEqual(result["changes"], {})

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
