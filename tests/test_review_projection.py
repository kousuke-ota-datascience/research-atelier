import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from research_atelier.projection import (  # noqa: E402
    AmbiguousInvestigationProjectionRowError,
    DuplicateReviewProjectionRowError,
    ReviewProjectionError,
    build_review_projection,
    derive_artifact_outcomes,
    derive_next_action,
    plan_review_row,
    reconcile_latest_review_relation,
    resolve_unique_investigation_row,
    resolve_unique_review_row,
)


REVIEW_PATH = ROOT / "investigations" / "INV-000015" / "reviews" / "review-000001.json"


class ReviewProjectionRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.review = json.loads(REVIEW_PATH.read_text(encoding="utf-8"))

    def test_inv_000015_projection_matches_operational_contract(self) -> None:
        projection = build_review_projection(self.review)
        self.assertEqual(projection.title, "INV-000015 / Review 000001")
        self.assertEqual(projection.properties["Verdict"], "FINDINGS")
        self.assertEqual(projection.properties["00 Context"], "OK")
        self.assertEqual(projection.properties["10 Evidence"], "OK")
        self.assertEqual(projection.properties["20 Synthesis"], "OK")
        self.assertEqual(projection.properties["30 Analysis"], "NG")
        self.assertEqual(projection.properties["Highest Severity"], "Minor")
        self.assertEqual(projection.properties["date:Reviewed At:start"], "2026-09-23T04:26:00Z")
        self.assertEqual(projection.next_action.workflow, "Workflow 10")
        self.assertEqual(projection.next_action.investigation, "INV-000015")
        self.assertEqual(projection.next_action.resume_from, "30_analysis")
        self.assertIn("Do not allocate a new Investigation", projection.next_action.do_not)
        self.assertIn("# Summary", projection.body_markdown)
        self.assertIn("# Next Action — Quick Reference", projection.body_markdown)
        self.assertIn("# Review Details", projection.body_markdown)
        self.assertIn("# Provenance", projection.body_markdown)
        self.assertIn("F001", projection.body_markdown)

    def test_artifact_outcomes_follow_transition_and_affected_layer_findings(self) -> None:
        outcomes = derive_artifact_outcomes(self.review)
        self.assertEqual(
            outcomes,
            {
                "00_context": "OK",
                "10_evidence": "OK",
                "20_synthesis": "OK",
                "30_analysis": "NG",
            },
        )

        context_finding = copy.deepcopy(self.review)
        finding = context_finding["transitions"][2]["findings"][0]
        finding["repair_direction"]["mode"] = "new_investigation"
        finding["repair_direction"]["affected_layer"] = "00_context"
        outcomes = derive_artifact_outcomes(context_finding)
        self.assertEqual(outcomes["00_context"], "NG")
        self.assertEqual(outcomes["30_analysis"], "NG")

    def test_new_investigation_finding_hands_off_to_workflow_00(self) -> None:
        review = copy.deepcopy(self.review)
        finding = review["transitions"][2]["findings"][0]
        finding["repair_direction"]["mode"] = "new_investigation"
        finding["repair_direction"]["affected_layer"] = "00_context"
        action = derive_next_action(review)
        self.assertEqual(action.workflow, "Workflow 00")
        self.assertEqual(action.resume_from, "new Investigation allocation")
        self.assertIn("Do not repair", action.do_not)

    def test_pass_review_requires_no_repair(self) -> None:
        review = copy.deepcopy(self.review)
        for transition in review["transitions"]:
            transition["findings"] = []
        review["verdict"] = "PASS"
        projection = build_review_projection(review)
        self.assertEqual(projection.properties["Verdict"], "PASS")
        self.assertIsNone(projection.properties["Highest Severity"])
        self.assertEqual(projection.properties["30 Analysis"], "OK")
        self.assertEqual(projection.next_action.workflow, "Workflow 20")
        self.assertEqual(projection.next_action.resume_from, "none")

    def test_same_investigation_context_repair_fails_safe(self) -> None:
        review = copy.deepcopy(self.review)
        finding = review["transitions"][2]["findings"][0]
        finding["repair_direction"]["mode"] = "same_investigation"
        finding["repair_direction"]["affected_layer"] = "00_context"
        with self.assertRaises(ReviewProjectionError):
            derive_next_action(review)

    def test_duplicate_review_row_fails_stop(self) -> None:
        rows = [
            {"investigation_id": "INV-000015", "review_seq": 1, "url": "a"},
            {"investigation_id": "INV-000015", "review_seq": 1, "url": "b"},
        ]
        with self.assertRaises(DuplicateReviewProjectionRowError):
            resolve_unique_review_row(
                rows, investigation_id="INV-000015", review_seq=1
            )

    def test_review_row_resolution_is_idempotent(self) -> None:
        row = {"investigation_id": "INV-000015", "review_seq": 1, "url": "review-url"}
        self.assertEqual(
            resolve_unique_review_row(
                [row], investigation_id="INV-000015", review_seq=1
            ),
            row,
        )
        self.assertIsNone(
            resolve_unique_review_row(
                [row], investigation_id="INV-000015", review_seq=2
            )
        )

    def test_investigation_binding_requires_exactly_one_row(self) -> None:
        row = {"investigation_id": "INV-000015", "url": "inv-url"}
        self.assertEqual(
            resolve_unique_investigation_row([row], investigation_id="INV-000015"),
            row,
        )
        with self.assertRaises(AmbiguousInvestigationProjectionRowError):
            resolve_unique_investigation_row([], investigation_id="INV-000015")
        with self.assertRaises(AmbiguousInvestigationProjectionRowError):
            resolve_unique_investigation_row(
                [row, dict(row)], investigation_id="INV-000015"
            )

    def test_review_row_plan_create_update_noop(self) -> None:
        projection = build_review_projection(self.review)
        create = plan_review_row(self.review, existing_rows=[])
        self.assertEqual(create.outcome, "CREATE")
        self.assertIsNone(create.review_url)

        current = {
            "investigation_id": "INV-000015",
            "review_seq": 1,
            "url": "review-url",
            "properties": dict(projection.properties),
            "body_markdown": projection.body_markdown,
        }
        noop = plan_review_row(self.review, existing_rows=[current])
        self.assertEqual(noop.outcome, "NOOP")
        self.assertEqual(noop.review_url, "review-url")

        stale = copy.deepcopy(current)
        stale["properties"]["30 Analysis"] = "OK"
        update = plan_review_row(self.review, existing_rows=[stale])
        self.assertEqual(update.outcome, "UPDATE")
        self.assertEqual(update.properties["30 Analysis"], "NG")

    def test_latest_review_relation_reconciliation_is_idempotent(self) -> None:
        self.assertEqual(
            reconcile_latest_review_relation(
                current_latest_review_url="review-url",
                latest_review_url="review-url",
                latest_review_exists=True,
            ),
            {},
        )
        self.assertEqual(
            reconcile_latest_review_relation(
                current_latest_review_url=None,
                latest_review_url="review-url",
                latest_review_exists=True,
            ),
            {"Latest Review": ["review-url"]},
        )
        with self.assertRaises(ReviewProjectionError):
            reconcile_latest_review_relation(
                current_latest_review_url=None,
                latest_review_url=None,
                latest_review_exists=True,
            )


if __name__ == "__main__":
    unittest.main()
