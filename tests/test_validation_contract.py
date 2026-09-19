"""Research Atelier v1 deterministic validation contractのregression test。"""
from __future__ import annotations

from copy import deepcopy
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


INVESTIGATION_ID = "RQ-0007-v001"
SCHEMA_ROOT = REPO_ROOT / "schemas" / "v1"
FIXTURE_ROOT = REPO_ROOT / "tests" / "fixtures" / "v1"

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


class ValidationContractTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.investigation_root = Path(self.tempdir.name)
        self.investigation_dir = self.investigation_root / INVESTIGATION_ID
        self.investigation_dir.mkdir(parents=True)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _valid_docs(self) -> dict[str, dict]:
        return {
            stage: _load_json(FIXTURE_ROOT / filename)
            for stage, filename in VALID_FIXTURES.items()
        }

    def _write_docs(self, docs: dict[str, dict], through: str = "30") -> None:
        through_index = ARTIFACT_ORDER.index(through)
        for stage in ARTIFACT_ORDER[: through_index + 1]:
            path = self.investigation_dir / ARTIFACT_FILES[stage]
            path.write_text(
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

    def _assert_fail_rule(self, result: dict, rule_id: str) -> None:
        self.assertEqual(result["result"], "FAIL", result)
        self.assertTrue(
            any(error["rule_id"] == rule_id for error in result["errors"]),
            result,
        )

    def test_valid_chain_passes(self) -> None:
        docs = self._valid_docs()
        self._write_docs(docs)

        result = self._validate("30")

        self.assertEqual(result["result"], "PASS", result)
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["internal_errors"], [])

    def test_missing_required_field_fails_schema(self) -> None:
        docs = self._valid_docs()
        del docs["00"]["question"]
        self._write_docs(docs, "00")

        self._assert_fail_rule(self._validate("00"), "V-SCHEMA-001")

    def test_wrong_enum_fails_schema(self) -> None:
        docs = self._valid_docs()
        docs["30"]["question_type"] = "NotAQuestionType"
        self._write_docs(docs)

        self._assert_fail_rule(self._validate("30"), "V-SCHEMA-001")

    def test_malformed_id_fails_schema(self) -> None:
        docs = self._valid_docs()
        docs["00"]["investigation_id"] = "RQ-7-v1"
        self._write_docs(docs, "00")

        self._assert_fail_rule(self._validate("00"), "V-SCHEMA-001")

    def test_dangling_evidence_reference_fails(self) -> None:
        docs = self._valid_docs()
        docs["20"]["knowledge_units"][0]["evidence_refs"] = ["E9999"]
        self._write_docs(docs, "20")

        self._assert_fail_rule(self._validate("20"), "V-REF-001")

    def test_duplicate_id_fails(self) -> None:
        docs = self._valid_docs()
        duplicate = deepcopy(docs["10"]["evidence_items"][0])
        docs["10"]["evidence_items"].append(duplicate)
        self._write_docs(docs, "10")

        self._assert_fail_rule(self._validate("10"), "V-ID-001")

    def test_investigation_mismatch_fails(self) -> None:
        docs = self._valid_docs()
        docs["20"]["investigation_id"] = "RQ-0007-v002"
        self._write_docs(docs, "20")

        self._assert_fail_rule(self._validate("20"), "V-INV-001")

    def test_partial_validation_passes_each_stage(self) -> None:
        for through in ARTIFACT_ORDER:
            with self.subTest(through=through):
                for path in self.investigation_dir.glob("*.json"):
                    path.unlink()

                docs = self._valid_docs()
                self._write_docs(docs, through)

                result = self._validate(through)
                self.assertEqual(result["result"], "PASS", result)


if __name__ == "__main__":
    unittest.main()
