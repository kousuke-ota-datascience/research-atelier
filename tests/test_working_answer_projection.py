import json
from pathlib import Path
import sys
import unittest

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from research_atelier.projection import (  # noqa: E402
    DuplicateWorkingAnswerSectionError,
    build_projection_log_v2,
    patch_working_answer_section,
    render_working_answer_section,
    working_answer_projection_state,
    working_answer_section_matches,
)


ANALYSIS = {
    "working_answer": {"text": "Current answer.", "knowledge_unit_refs": ["K0001"]},
    "judgments": [
        {"judgment_id": "J0001", "statement": "Judgment one.", "knowledge_unit_refs": ["K0001"]}
    ],
    "limitations": [{"text": "Limitation one.", "knowledge_unit_refs": ["K0001"]}],
    "unresolved_questions": ["What remains?"],
    "alternative_interpretations": [
        {"text": "Alternative one.", "knowledge_unit_refs": ["K0001"]}
    ],
}


class WorkingAnswerRenderingTests(unittest.TestCase):
    def test_render_structured_current_view_without_internal_ids(self):
        rendered = render_working_answer_section(ANALYSIS)
        self.assertIn("# Working Answer", rendered)
        self.assertIn("## Answer\nCurrent answer.", rendered)
        self.assertIn("## Key Judgments\n- Judgment one.", rendered)
        self.assertIn("## Limitations\n- Limitation one.", rendered)
        self.assertIn("## Unresolved Questions\n- What remains?", rendered)
        self.assertIn("## Alternative Interpretations\n- Alternative one.", rendered)
        self.assertNotIn("J0001", rendered)
        self.assertNotIn("K0001", rendered)

    def test_empty_optional_fields_omit_empty_chapters(self):
        analysis = {
            "working_answer": {"text": "Only answer.", "knowledge_unit_refs": []},
            "judgments": [],
            "limitations": [],
            "unresolved_questions": [],
            "alternative_interpretations": [],
        }
        rendered = render_working_answer_section(analysis)
        self.assertEqual(rendered, "# Working Answer\n## Answer\nOnly answer.")
        self.assertNotIn("Key Judgments", rendered)
        self.assertNotIn("Limitations", rendered)


class WorkingAnswerPatchTests(unittest.TestCase):
    def test_create_on_empty_notion_body(self):
        result = patch_working_answer_section("<empty-block/>", ANALYSIS)
        self.assertEqual(result.action, "CREATE")
        self.assertTrue(result.markdown.startswith("# Working Answer"))

    def test_create_preserves_other_chapters(self):
        body = "# Notes\nmanual notes\n\n# Related\nmanual links"
        result = patch_working_answer_section(body, ANALYSIS)
        self.assertEqual(result.action, "CREATE")
        self.assertTrue(result.markdown.startswith(body))
        self.assertIn("# Working Answer", result.markdown)

    def test_replace_preserves_content_before_and_after(self):
        body = (
            "# Notes\nkeep before\n\n"
            "# Working Answer\n\n## Answer\nstale answer\n\n"
            "# Related\nkeep after"
        )
        result = patch_working_answer_section(body, ANALYSIS)
        self.assertEqual(result.action, "REPLACE")
        self.assertIn("# Notes\nkeep before", result.markdown)
        self.assertIn("# Related\nkeep after", result.markdown)
        self.assertNotIn("stale answer", result.markdown)
        self.assertIn("Current answer.", result.markdown)

    def test_rerun_is_noop_when_current(self):
        rendered = render_working_answer_section(ANALYSIS)
        body = f"# Notes\nkeep\n\n{rendered}\n\n# Related\nkeep"
        result = patch_working_answer_section(body, ANALYSIS)
        self.assertEqual(result.action, "NOOP")
        self.assertEqual(result.markdown, body)
        self.assertTrue(working_answer_section_matches(body, ANALYSIS))

    def test_duplicate_target_heading_blocks_projection(self):
        body = "# Working Answer\nold one\n\n# Notes\nkeep\n\n# Working Answer\nold two"
        with self.assertRaises(DuplicateWorkingAnswerSectionError):
            patch_working_answer_section(body, ANALYSIS)

    def test_heading_inside_code_fence_is_not_target(self):
        body = "# Notes\n```markdown\n# Working Answer\nexample\n```"
        result = patch_working_answer_section(body, ANALYSIS)
        self.assertEqual(result.action, "CREATE")

    def test_projection_state_supports_workflow_00_completion_rule(self):
        rendered = render_working_answer_section(ANALYSIS)
        self.assertEqual(working_answer_projection_state("<empty-block/>", ANALYSIS), "MISSING")
        self.assertEqual(
            working_answer_projection_state("# Working Answer\n## Answer\nstale", ANALYSIS),
            "STALE",
        )
        self.assertEqual(working_answer_projection_state(rendered, ANALYSIS), "CURRENT")
        duplicate = f"{rendered}\n\n# Notes\nkeep\n\n{rendered}"
        self.assertEqual(working_answer_projection_state(duplicate, ANALYSIS), "BLOCKED")


class ProjectionLogTests(unittest.TestCase):
    def test_v2_log_uses_body_target_not_target_property(self):
        log = build_projection_log_v2(
            target_rq_url="https://app.notion.com/p/example",
            rq_id="RQ-0018",
            source_investigation_id="INV-000013",
            source_30_analysis_commit_sha="b7c93c1c4786a288d273bccc314d3b772a0b1f86",
            projection_timestamp="2026-09-23T01:00:00+09:00",
            result="SUCCESS",
        )
        self.assertEqual(log["projection_target"]["surface"], "page_body")
        self.assertEqual(log["projection_target"]["section_heading"], "# Working Answer")
        self.assertNotIn("target_property", log)

    def test_failure_log_is_supported(self):
        log = build_projection_log_v2(
            target_rq_url="https://app.notion.com/p/example",
            rq_id="RQ-0018",
            source_investigation_id="INV-000013",
            source_30_analysis_commit_sha="b7c93c1c4786a288d273bccc314d3b772a0b1f86",
            projection_timestamp="2026-09-23T01:00:00+09:00",
            result="FAILURE",
            note="Notion write failed",
        )
        self.assertEqual(log["result"], "FAILURE")
        self.assertEqual(log["note"], "Notion write failed")

    def test_v2_log_validates_against_schema(self):
        schema = json.loads((ROOT / "schemas/v2/projection_log.schema.json").read_text())
        log = build_projection_log_v2(
            target_rq_url="https://app.notion.com/p/3e3e5855be3981129c7fd1ff68a9098b",
            rq_id="RQ-0018",
            source_investigation_id="INV-000013",
            source_30_analysis_commit_sha="b7c93c1c4786a288d273bccc314d3b772a0b1f86",
            projection_timestamp="2026-09-23T01:00:00+09:00",
            result="SUCCESS",
        )
        Draft202012Validator(schema, format_checker=FormatChecker()).validate(log)


if __name__ == "__main__":
    unittest.main()
