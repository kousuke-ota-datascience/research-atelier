"""Research Atelier v2 identity / compatibility regression tests."""
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

from research_atelier.validation.validate_investigation import validate_investigation

INVESTIGATION_ID = "INV-000001"
SCHEMA_ROOT = REPO_ROOT / "schemas" / "v2"
FIXTURE_ROOT = REPO_ROOT / "tests" / "fixtures" / "v2"
VALID_FIXTURES = {
    "00": "00_context.valid.min.json",
    "10": "10_evidence.valid.min.json",
    "20": "20_synthesis.valid.min.json",
    "30": "30_analysis.valid.min.json",
}
ARTIFACT_FILES = {
    "00": "00_context.json",
    "10": "10_evidence.json",
    "20": "20_synthesis.json",
    "30": "30_analysis.json",
}
ARTIFACT_ORDER = ("00", "10", "20", "30")

def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))

class ValidationContractV2Test(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.investigation_root = Path(self.tempdir.name)
        self.investigation_dir = self.investigation_root / INVESTIGATION_ID
        self.investigation_dir.mkdir(parents=True)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _valid_docs(self) -> dict[str, dict]:
        return {stage: _load_json(FIXTURE_ROOT / filename) for stage, filename in VALID_FIXTURES.items()}

    def _write_docs(self, docs: dict[str, dict], through: str = "30") -> None:
        through_index = ARTIFACT_ORDER.index(through)
        for stage in ARTIFACT_ORDER[:through_index + 1]:
            (self.investigation_dir / ARTIFACT_FILES[stage]).write_text(
                json.dumps(docs[stage], ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

    def _validate(self, through: str = "30") -> dict:
        return validate_investigation(
            INVESTIGATION_ID,
            through=through,
            investigation_root=self.investigation_root,
            schema_root=SCHEMA_ROOT,
        )

    def test_valid_v2_chain_passes(self) -> None:
        self._write_docs(self._valid_docs())
        result = self._validate("30")
        self.assertEqual(result["result"], "PASS", result)

    def test_investigation_id_is_independent_from_rq_id(self) -> None:
        docs = self._valid_docs()
        for doc in docs.values():
            doc["rq_id"] = "RQ-0427"
        self._write_docs(docs)
        result = self._validate("30")
        self.assertEqual(result["result"], "PASS", result)

    def test_cross_artifact_rq_mismatch_fails(self) -> None:
        docs = self._valid_docs()
        docs["20"]["rq_id"] = "RQ-0008"
        self._write_docs(docs, "20")
        result = self._validate("20")
        self.assertEqual(result["result"], "FAIL", result)
        self.assertTrue(any(e["rule_id"] == "V-RQ-001" for e in result["errors"]), result)

    def test_zero_investigation_id_is_rejected(self) -> None:
        result = validate_investigation(
            "INV-000000",
            through="00",
            investigation_root=self.investigation_root,
            schema_root=SCHEMA_ROOT,
        )
        self.assertEqual(result["result"], "FAIL", result)
        self.assertTrue(any(e["rule_id"] == "V-INV-000" for e in result["errors"]), result)

    def test_historical_frozen_null_question_type_remains_validatable(self) -> None:
        docs = self._valid_docs()
        docs["00"]["context_state"] = "frozen"
        docs["00"]["frozen_at"] = "2026-09-22T14:19:25.560Z"
        self._write_docs(docs, "00")

        result = self._validate("00")

        self.assertEqual(result["result"], "PASS", result)

    def test_new_freeze_rejects_null_question_type(self) -> None:
        docs = self._valid_docs()
        docs["00"]["context_state"] = "frozen"
        docs["00"]["frozen_at"] = "2026-09-23T04:00:00Z"
        self._write_docs(docs, "00")

        result = validate_investigation(
            INVESTIGATION_ID,
            through="00",
            investigation_root=self.investigation_root,
            schema_root=SCHEMA_ROOT,
            new_freeze=True,
        )

        self.assertEqual(result["result"], "FAIL", result)
        self.assertTrue(
            any(error["rule_id"] == "V-FREEZE-002" for error in result["errors"]),
            result,
        )

    def test_new_freeze_accepts_concrete_question_type(self) -> None:
        docs = self._valid_docs()
        docs["00"]["context_state"] = "frozen"
        docs["00"]["question_type"] = "Descriptive"
        docs["00"]["frozen_at"] = "2026-09-23T04:00:00Z"
        self._write_docs(docs, "00")

        result = validate_investigation(
            INVESTIGATION_ID,
            through="00",
            investigation_root=self.investigation_root,
            schema_root=SCHEMA_ROOT,
            new_freeze=True,
        )

        self.assertEqual(result["result"], "PASS", result)

    def test_partial_validation_passes_each_stage(self) -> None:
        for through in ARTIFACT_ORDER:
            with self.subTest(through=through):
                for path in self.investigation_dir.glob("*.json"):
                    path.unlink()
                self._write_docs(self._valid_docs(), through)
                result = self._validate(through)
                self.assertEqual(result["result"], "PASS", result)

if __name__ == "__main__":
    unittest.main()
