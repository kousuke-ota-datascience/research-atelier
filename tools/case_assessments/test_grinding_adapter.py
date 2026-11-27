"""v3 adapterの正本fixtureに対する抽出・異常入力拒否。"""
import json
from pathlib import Path
import unittest
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from build import require,lineage,unique_index
from grinding_adapter import build_grinding_contract

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/"investigations/INV-000048"

class GrindingAdapterTests(unittest.TestCase):
    def setUp(self):
        self.c,self.e,self.s,self.a=[json.loads((BASE/(x+".json")).read_text()) for x in ("00_context","10_evidence","20_synthesis","30_analysis")]
    def generate(self):
        return build_grinding_contract(self.c,self.a,{},unique_index(self.s["knowledge_units"],"knowledge_unit_id"),unique_index(self.e["evidence_items"],"evidence_id"),unique_index(self.e["sources"],"source_id"),require=require,lineage=lineage)
    def test_baseline(self):
        out=self.generate()
        self.assertEqual(out["summary"]["factor_assessment_count"],60)
        self.assertEqual(out["summary"]["criterion_assessment_count"],42)
        self.assertEqual(out["summary"]["eligibility_counts"],{"quality_estimation":4,"near_match":2})
        self.assertTrue(all(x["epistemic_status"] is None for c in out["cases"] for x in c["factor_assessments"]))
    def test_missing_category(self):
        self.a["working_answer"]["text"]=self.a["working_answer"]["text"].replace("- D10 評価・経済性：","- D11 評価・経済性：",1)
        with self.assertRaises(ValueError): self.generate()
    def test_bad_summary(self):
        self.a["working_answer"]["text"]=self.a["working_answer"]["text"].replace("| C01 | 確認済 |","| C01 | 未確認 |",1)
        with self.assertRaises(ValueError): self.generate()
    def test_out_of_scope(self):
        self.a["working_answer"]["text"]=self.a["working_answer"]["text"].replace("（K0001, K0002）\n- D02","（K0008）\n- D02",1)
        with self.assertRaises(ValueError): self.generate()
