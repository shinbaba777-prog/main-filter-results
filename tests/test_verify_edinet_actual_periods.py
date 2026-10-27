import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from verify_edinet_actual_periods import inspect

MANIFEST = {"periods": [{"file": "a.zip", "docID": "S100OK43",
                        "periodEnd": "2022-03-31"}]}

def row(context):
    return {"source_zip": "a.zip", "context_id": context}

def evidence(directory, context="CurrentYearDuration", end="2022-03-31",
             start="2021-04-01"):
    payload = {"XBRL/PublicDoc/report.xbrl": {context: {
        "start_date": start, "end_date": end,
        "instant": None, "dimensions": []}}}
    (directory / "S100OK43.contexts.json").write_text(
        json.dumps(payload), encoding="utf-8")

class ActualPeriodTests(unittest.TestCase):
    def test_matching_real_dates_still_require_review(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            evidence(root)
            result = inspect([row("CurrentYearDuration")], MANIFEST, root)
            self.assertEqual(result["period_evidence_matched"], 1)
            self.assertEqual(result["period_evidence_unresolved"], 0)
            self.assertFalse(result["scoring_ready"])

    def test_mismatched_actual_period_is_blocked(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            evidence(root, end="2021-03-31")
            result = inspect([row("CurrentYearDuration")], MANIFEST, root)
            self.assertEqual(result["reasons"]["ACTUAL_PERIOD_END_MISMATCH"], 1)

    def test_missing_evidence_is_blocked(self):
        with tempfile.TemporaryDirectory() as temp:
            result = inspect([row("CurrentYearDuration")], MANIFEST, Path(temp))
            self.assertEqual(result["reasons"]["ORIGINAL_CONTEXT_EVIDENCE_MISSING"], 1)

    def test_same_id_different_instances_is_ambiguous(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            evidence(root)
            path = root / "S100OK43.contexts.json"
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["XBRL/PublicDoc/other.xbrl"] = {
                "CurrentYearDuration": {
                    "start_date": "2020-04-01", "end_date": "2021-03-31",
                    "instant": None, "dimensions": []}}
            path.write_text(json.dumps(payload), encoding="utf-8")
            result = inspect([row("CurrentYearDuration")], MANIFEST, root)
            self.assertEqual(result["reasons"]["AMBIGUOUS_CONTEXT_DEFINITION"], 1)

if __name__ == "__main__":
    unittest.main()
