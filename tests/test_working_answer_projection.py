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

    def test_notion_roundtrip_blank_block_separators_is_current(self):
        rendered = render_working_answer_section(ANALYSIS)
        notion_readback = rendered.replace(
            "# Working Answer\n## Answer",
            "# Working Answer\n\n## Answer",
        ).replace("## Key Judgments\n", "## Key Judgments\n\n")
        self.assertTrue(working_answer_section_matches(notion_readback, ANALYSIS))
        self.assertEqual(working_answer_projection_state(notion_readback, ANALYSIS), "CURRENT")
        self.assertEqual(patch_working_answer_section(notion_readback, ANALYSIS).action, "NOOP")

    def test_notion_inline_bold_roundtrip_is_current(self):
        # Notion NFM fetch returns <b> even when canonical Git text used **.
        analysis = {
            "working_answer": {
                "text": "Domain **decision** and **time horizon**.",
                "knowledge_unit_refs": [],
            },
            "judgments": [], "limitations": [],
            "unresolved_questions": [], "alternative_interpretations": [],
        }
        notion_readback = (
            "# Working Answer\n\n## Answer\n"
            "Domain <b>decision</b> and <b>time horizon</b>."
        )
        self.assertTrue(working_answer_section_matches(notion_readback, analysis))
        self.assertEqual(working_answer_projection_state(notion_readback, analysis), "CURRENT")
        self.assertEqual(patch_working_answer_section(notion_readback, analysis).action, "NOOP")

    def test_notion_escaped_formula_punctuation_roundtrip_is_current(self):
        # Notion NFM readback escapes Markdown punctuation in prose, but the
        # accepted Git analysis uses ordinary characters in the formula.
        analysis = {
            "working_answer": {
                "text": "logit P(T∈(t,t+Δ] | T>t, H_t)=α(t)+βᵀx(t)",
                "knowledge_unit_refs": [],
            },
            "judgments": [], "limitations": [],
            "unresolved_questions": [], "alternative_interpretations": [],
        }
        notion_readback = (
            "# Working Answer\n\n## Answer\n\n"
            "logit P(T∈(t,t+Δ\\] \\| T>t, H\\_t)=α(t)+βᵀx(t)"
        )
        self.assertTrue(working_answer_section_matches(notion_readback, analysis))
        self.assertEqual(working_answer_projection_state(notion_readback, analysis), "CURRENT")
        self.assertEqual(patch_working_answer_section(notion_readback, analysis).action, "NOOP")

    def test_notion_escaped_opening_bracket_roundtrip_is_current(self):
        # Notion NFM escapes opening brackets in factor labels in prose.
        analysis = {"working_answer": {"text": "D01.1 [C] example"}}
        readback = "# Working Answer\n## Answer\nD01.1 \\[C] example"
        self.assertTrue(working_answer_section_matches(readback, analysis))
        self.assertEqual(working_answer_projection_state(readback, analysis), "CURRENT")
        self.assertEqual(patch_working_answer_section(readback, analysis).action, "NOOP")
        self.assertEqual(
            working_answer_projection_state(readback.replace("[C]", "[U]"), analysis),
            "STALE",
        )

    def test_notion_escaped_opening_bracket_inside_code_is_not_normalized(self):
        analysis = {"working_answer": {"text": "\x60\x60\x60md\n[C]\n\x60\x60\x60"}}
        rendered = render_working_answer_section(analysis)
        self.assertFalse(working_answer_section_matches(rendered.replace("[C]", "\\[C]"), analysis))

    def test_notion_escaped_opening_bracket_inside_table_is_not_normalized(self):
        analysis = {"working_answer": {"text": "| Factor |\n| --- |\n| [C] |"}}
        rendered = render_working_answer_section(analysis)
        self.assertFalse(working_answer_section_matches(rendered.replace("[C]", "\\[C]"), analysis))

    def test_notion_inline_bold_code_fence_is_not_normalized(self):
        analysis = {
            "working_answer": {
                "text": "```md\n**literal markdown**\n```",
                "knowledge_unit_refs": [],
            },
            "judgments": [], "limitations": [],
            "unresolved_questions": [], "alternative_interpretations": [],
        }
        readback = "# Working Answer\n## Answer\n```md\n<b>literal markdown</b>\n```"
        self.assertFalse(working_answer_section_matches(readback, analysis))

    def test_notion_literal_dollar_and_bare_domain_roundtrip(self):
        analysis = {"working_answer": {"text": 'Query "$230,000" and C3.ai. site:quantzig.com/case-studies/manufacturing-predictive-maintenance'}}
        readback = (
            '# Working Answer\n## Answer\nQuery "\\$230,000" and '
            '[C3.ai](http://C3.ai). site:[quantzig.com/case-studies/manufacturing-predictive-maintenance]'
            '(http://quantzig.com/case-studies/manufacturing-predictive-maintenance)'
        )
        self.assertEqual(working_answer_projection_state(readback, analysis), "CURRENT")
        self.assertEqual(patch_working_answer_section(readback, analysis).action, "NOOP")
        self.assertEqual(working_answer_projection_state(readback.replace("http://C3.ai", "http://other.ai"), analysis), "STALE")
        self.assertEqual(working_answer_projection_state(readback.replace("230,000", "240,000"), analysis), "STALE")

    def test_explicit_identity_link_remains_current(self):
        analysis = {"working_answer": {"text": "[C3.ai](http://C3.ai)"}}
        self.assertEqual(working_answer_projection_state(render_working_answer_section(analysis), analysis), "CURRENT")

    def test_notion_literal_dollar_in_table_is_not_normalized(self):
        analysis = {"working_answer": {"text": "| Cost |\n| --- |\n| $1 |"}}
        self.assertFalse(working_answer_section_matches(render_working_answer_section(analysis).replace("$1", r"\$1"), analysis))

    def test_notion_native_table_delimiter_width_is_current(self):
        analysis = {"working_answer": {"text": "| A | B |\n| --- | :---: |\n| x | y |"}}
        readback = render_working_answer_section(analysis).replace("| --- | :---: |", "| - | :-: |")
        self.assertEqual(working_answer_projection_state(readback, analysis), "CURRENT")
        self.assertEqual(patch_working_answer_section(readback, analysis).action, "NOOP")
        for altered in (readback.replace("| x | y |", "| x | z |"),
                        readback.replace("| - | :-: |", "| - | - |"),
                        readback.replace("| - | :-: |", "| - |")):
            self.assertEqual(working_answer_projection_state(altered, analysis), "STALE")

    def test_notion_numeric_less_than_is_current_only_for_exact_prose(self):
        analysis = {"working_answer": {"text": "Welch p<0.001"}}
        readback = render_working_answer_section(analysis).replace("p<", r"p\<")
        self.assertEqual(working_answer_projection_state(readback, analysis), "CURRENT")
        self.assertEqual(working_answer_projection_state(readback.replace("0.001", "0.01"), analysis), "STALE")
        for literal in ("| p<0.001 |", "```\np<0.001\n```", "`p<0.001`"):
            a = {"working_answer": {"text": literal}}
            self.assertEqual(working_answer_projection_state(
                render_working_answer_section(a).replace("p<", r"p\<"), a), "STALE")

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
