"""BKL-0035 Investigation allocation / rerun regression tests."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from research_atelier.orchestration.investigation_allocation import (
    decide_investigation_allocation,
    decide_investigation_allocation_payload,
)


def load_context(investigation_id: str) -> dict:
    return json.loads(
        (
            REPO_ROOT
            / "investigations"
            / investigation_id
            / "00_context.json"
        ).read_text(encoding="utf-8")
    )


class InvestigationAllocationTest(unittest.TestCase):
    def test_first_execution_allocates_new(self) -> None:
        result = decide_investigation_allocation(
            intent="retry_completion",
            existing_investigation_id=None,
            existing_context=None,
        )
        self.assertEqual(result.decision, "allocate_new")
        self.assertTrue(result.new_investigation_allocated)

    def test_rq_0022_retry_reuses_inv_000018(self) -> None:
        context = load_context("INV-000018")
        result = decide_investigation_allocation(
            intent="retry_completion",
            existing_investigation_id="INV-000018",
            existing_context=context,
            requested_context={"rq_id": "RQ-0022"},
        )
        self.assertEqual(result.decision, "reuse_existing")
        self.assertFalse(result.new_investigation_allocated)
        self.assertEqual(
            result.reason_codes,
            ("same_semantics_retry_or_completion",),
        )

    def test_rq_0022_cutoff_timestamp_difference_is_not_self_justifying(self) -> None:
        existing = load_context("INV-000018")
        accidental_successor = load_context("INV-000019")
        result = decide_investigation_allocation(
            intent="retry_completion",
            existing_investigation_id="INV-000018",
            existing_context=existing,
            requested_context=accidental_successor,
            evidence_population_changed=False,
        )
        self.assertEqual(result.decision, "reuse_existing")
        cutoff = next(
            item
            for item in result.semantic_differences
            if item["field"] == "evidence_cutoff"
        )
        self.assertFalse(cutoff["material"])

    def test_cutoff_difference_blocks_if_snapshot_materiality_is_unknown(self) -> None:
        existing = load_context("INV-000018")
        accidental_successor = load_context("INV-000019")
        result = decide_investigation_allocation(
            intent="retry_completion",
            existing_investigation_id="INV-000018",
            existing_context=existing,
            requested_context=accidental_successor,
        )
        self.assertEqual(result.decision, "blocked")
        self.assertIn(
            "evidence_cutoff_materiality_unresolved",
            result.issues,
        )

    def test_rq_0020_review_repair_reuses_inv_000016(self) -> None:
        context = load_context("INV-000016")
        result = decide_investigation_allocation(
            intent="repair",
            existing_investigation_id="INV-000016",
            existing_context=context,
            requested_context=context,
        )
        self.assertEqual(result.decision, "reuse_existing")
        self.assertEqual(result.reason_codes, ("same_semantics_repair",))

    def test_rq_0020_inv_000020_cutoff_difference_does_not_justify_allocation(self) -> None:
        existing = load_context("INV-000016")
        accidental_successor = load_context("INV-000020")
        result = decide_investigation_allocation(
            intent="repair",
            existing_investigation_id="INV-000016",
            existing_context=existing,
            requested_context=accidental_successor,
            evidence_population_changed=False,
        )
        self.assertEqual(result.decision, "reuse_existing")
        self.assertFalse(result.new_investigation_allocated)

    def test_scope_change_allocates_new(self) -> None:
        existing = load_context("INV-000018")
        result = decide_investigation_allocation(
            intent="semantic_reinvestigation",
            existing_investigation_id="INV-000018",
            existing_context=existing,
            requested_context={"scope": existing["scope"] + " 追加対象を含む。"},
        )
        self.assertEqual(result.decision, "allocate_new")
        self.assertIn("material_semantic_difference", result.reason_codes)

    def test_question_type_change_allocates_new(self) -> None:
        existing = load_context("INV-000018")
        result = decide_investigation_allocation(
            intent="semantic_reinvestigation",
            existing_investigation_id="INV-000018",
            existing_context=existing,
            requested_context={"question_type": "Mechanistic"},
        )
        self.assertEqual(result.decision, "allocate_new")

    def test_evidence_population_change_allocates_new(self) -> None:
        existing = load_context("INV-000018")
        result = decide_investigation_allocation(
            intent="semantic_reinvestigation",
            existing_investigation_id="INV-000018",
            existing_context=existing,
            requested_context={"evidence_cutoff": "2026-09-24T00:00:00Z"},
            evidence_population_changed=True,
        )
        self.assertEqual(result.decision, "allocate_new")
        self.assertTrue(result.semantic_differences[0]["material"])

    def test_explicit_independent_execution_allocates_without_semantic_diff(self) -> None:
        existing = load_context("INV-000018")
        result = decide_investigation_allocation(
            intent="explicit_new_execution",
            existing_investigation_id="INV-000018",
            existing_context=existing,
            requested_context={"rq_id": "RQ-0022"},
        )
        self.assertEqual(result.decision, "allocate_new")
        self.assertTrue(result.explicit_new_execution_intent)

    def test_semantic_reinvestigation_without_difference_blocks(self) -> None:
        existing = load_context("INV-000018")
        result = decide_investigation_allocation(
            intent="semantic_reinvestigation",
            existing_investigation_id="INV-000018",
            existing_context=existing,
            requested_context={"rq_id": "RQ-0022"},
        )
        self.assertEqual(result.decision, "blocked")
        self.assertIn(
            "material_semantic_difference_not_identified",
            result.issues,
        )

    def test_payload_report_contains_required_audit_fields(self) -> None:
        context = load_context("INV-000016")
        result = decide_investigation_allocation_payload(
            {
                "intent": "repair",
                "existing": {
                    "investigation_id": "INV-000016",
                    "context": context,
                },
                "requested_context": {"rq_id": "RQ-0020"},
            }
        )
        self.assertEqual(
            {
                "decision",
                "selected_existing_investigation",
                "new_investigation_allocated",
                "semantic_differences",
                "explicit_new_execution_intent",
                "intent",
                "reason_codes",
                "issues",
            },
            set(result),
        )
        self.assertEqual(result["selected_existing_investigation"], "INV-000016")


if __name__ == "__main__":
    unittest.main()
