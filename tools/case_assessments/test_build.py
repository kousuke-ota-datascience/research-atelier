import unittest
from build import parse_cases, parse_criterion_definitions, lineage

class ParserTests(unittest.TestCase):
    def setUp(self):
        self.framework={"factor_definitions":[{"factor_id":"D01.1"}]}
        self.k={"K0001":{"evidence_refs":["E0001"]}}
        self.e={"E0001":{"provenance":{"source_id":"SRC-000001"}}}
        self.s={"SRC-000001":{}}
        self.text=(
            "### C01 Example（SRC-000001）\n"
            "近接事例。根拠範囲：K0001。\n"
            "R1［未確認］未知（K0001）\n"
            "R2［確認済］確認（K0001）\n"
            "R3［未確認］未知（K0001）\n"
            "R4［不適合］なし（K0001）\n"
            "D01.1 対象［未知］部分既知・他は不明（確認範囲：K0001）"
        )

    def parse(self, text):
        return parse_cases(text,self.framework,self.k,self.e,self.s)

    def test_unknown_and_trace(self):
        a=self.parse(self.text)[0]["factor_assessments"][0]
        self.assertIsNone(a["value"])
        self.assertEqual(a["assessment_text"],"部分既知・他は不明")
        self.assertEqual(a["reference_role"],"confirmation_scope")
        self.assertEqual(a["source_refs"],["SRC-000001"])

    def test_reject_missing_factor(self):
        with self.assertRaises(ValueError):
            self.parse(self.text.rsplit("\n",1)[0])

    def test_reject_duplicate_factor(self):
        with self.assertRaises(ValueError):
            self.parse(self.text+"\n"+self.text.splitlines()[-1])

    def test_reject_unknown_reference(self):
        with self.assertRaises(ValueError):
            self.parse(self.text.replace("確認範囲：K0001","確認範囲：K9999"))

    def test_reject_semantic_role_drift(self):
        with self.assertRaises(ValueError):
            self.parse(self.text.replace("確認範囲：K0001","根拠：K0001"))

    def test_reject_eligibility_contradiction(self):
        with self.assertRaises(ValueError):
            self.parse(self.text.replace("近接事例。","完全適合事例。"))

    def test_preserves_mixed_status(self):
        a=self.parse(self.text.replace("［未知］部分既知・他は不明（確認範囲：","［サブタスク別：非該当／未知］現在非該当・将来不明（根拠："))[0]["factor_assessments"][0]
        self.assertEqual(a["applicability"],"mixed")
        self.assertIsNone(a["value"])

if __name__=="__main__":
    unittest.main()
