import unittest
from build import lineage, require
from category_adapter import definitions, parse_cases, parse_refs, build_category_contract, PREFIX


class CategoryTests(unittest.TestCase):
    def setUp(self):
        self.context = {
            "investigation_id": "INV-000001", "rq_id": "RQ-000001",
            "assumptions": [PREFIX + "、".join(f"D{i:02d} label{i}（定義{i}）" for i in range(1, 10)) + "。各カテゴリを記述し、留保を保持する。"],
            "investigation_boundary": {"include": [f"R{i}：条件{i}。" for i in range(1, 5)]}
        }
        self.framework, self.criteria = definitions(self.context, require)
        self.k = {f"K{i:04d}": {"evidence_refs": [f"E{i:04d}"]} for i in (1, 2, 3)}
        self.e = {f"E{i:04d}": {"provenance": {"source_id": f"SRC-{i:06d}"}} for i in (1, 2, 3)}
        self.s = {f"SRC-{i:06d}": {} for i in (1, 2, 3)}
        self.text = "\n".join([
            "## 回答と採択判定",
            "| 事例 | R1 | R2 | R3 | R4 | 区分 |",
            "| --- | --- | --- | --- | --- | --- |",
            "| C01 Example | 確認済 | 確認済 | 確認済 | 未確認 | 要因分析 |",
            "## 事例別9カテゴリ", "説明", "### C01 Example",
            "- 採択区分：要因分析（K0001, K0002）",
            "- R1 確認済 / R2 確認済 / R3 確認済 / R4 未確認",
            "- 判定理由：一部未確認。",
            *[f"- D{i:02d} label{i}：報告あり。別属性は未知（K0001–K0002）。" for i in range(1,10)],
            "## ユースケース構築の示唆（分析上の推論）",
            "別章"
        ])

    def parse(self, text):
        return parse_cases(text, self.framework, self.k, self.e, self.s, require=require, lineage=lineage)

    def test_preserve_original_and_scope(self):
        c = self.parse(self.text)[0]
        self.assertEqual(c["eligibility"], "factor_analysis")
        self.assertEqual(c["criteria_assessments"][3]["status"], "unconfirmed")
        self.assertIsNone(c["criteria_assessments"][3]["assessment_text"])
        self.assertEqual(c["criteria_assessments"][3]["reference_role"], "case_scope")
        self.assertEqual(c["assessment_reason"], "一部未確認。")
        a = c["factor_assessments"][0]
        self.assertIsNone(a["canonical_status"])
        self.assertIsNone(a["value"])
        self.assertEqual(a["assessment_text"], "報告あり。別属性は未知")
        self.assertEqual(a["source_refs"], ["SRC-000001", "SRC-000002"])
        self.assertEqual(a["reference_role"], "category_scope")
        self.assertEqual(self.text.splitlines()[a["analysis_line"]-1], a["canonical_line"])
        self.assertEqual(self.text.splitlines()[c["reason_analysis_line"]-1], c["canonical_reason_line"])

    def test_refs(self):
        self.assertEqual(parse_refs("K0001–K0003", require), ["K0001", "K0002", "K0003"])
        for raw in ["K0003–K0001", "K0001,K0001", "K0001–K0002,K0002", "K0000", "K1", "K0001,"]:
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                parse_refs(raw, require)

    def test_reject_contract_and_rows(self):
        for bad in [
            self.text.replace("D09 label9", "D08 label8"),
            self.text.replace("D09 label9", "D09 altered"),
            self.text.replace("- D09 label9：報告あり。別属性は未知（K0001–K0002）。\n", ""),
            self.text.replace("K0001–K0002", "K0003"),
            self.text.replace("K0001–K0002", "K9999"),
            self.text.replace("R4 未確認", "R4 確認済"),
            self.text.replace("| 未確認 | 要因分析 |", "| 確認済 | 要因分析 |"),
            self.text.replace("採択区分：要因分析", "採択区分：近接"),
            self.text.replace("## 事例別9カテゴリ", "## other"),
            self.text + "\n### C99 hidden",
            self.text.replace("- 判定理由：一部未確認。", "- 補足：一部未確認。")
        ]:
            with self.subTest(bad=bad[:100]), self.assertRaises(ValueError):
                self.parse(bad)

    def test_definitions_from_context(self):
        self.assertEqual(self.criteria[0]["definition_text"], "条件1。")
        self.assertEqual(self.framework["factor_count"], 9)
        self.context["assumptions"][0] = self.context["assumptions"][0].replace("D09 label9", "D08 label8")
        with self.assertRaises(ValueError):
            definitions(self.context, require)

    def test_build_counts(self):
        b = build_category_contract(self.context, {"working_answer": {"text": self.text}}, {},
                                    self.k, self.e, self.s, require=require, lineage=lineage)
        self.assertEqual(b["summary"]["case_count"], 1)
        self.assertEqual(b["summary"]["factor_rows_without_explicit_status"], 9)
        self.assertEqual(b["summary"]["criterion_assessment_count"], 4)
        self.assertEqual(b["summary"]["eligibility_counts"], {"factor_analysis": 1})


if __name__ == "__main__":
    unittest.main()
