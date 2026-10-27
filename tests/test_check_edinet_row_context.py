import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from check_edinet_row_context import inspect

def row(**overrides):
    data = {"candidate_metric": "sales", "context_id": "CurrentYearDuration",
            "consolidation_scope": "連結", "period_type": "期間", "unit_id": "JPY",
            "source_zip": "a.zip", "source_csv": "b.csv", "row_number": "3",
            "validation_status": "REVIEW_REQUIRED"}
    data.update(overrides)
    return data

class ContextDiagnosticsTests(unittest.TestCase):
    def test_valid_labels_still_not_scoring_ready(self):
        result = inspect([row()])
        self.assertFalse(result["scoring_ready"])
        self.assertEqual(result["issue_counts"]["NOT_APPROVED"], 1)

    def test_scope_unclear_flagged(self):
        result = inspect([row(consolidation_scope="その他")])
        self.assertEqual(result["issue_counts"]["SCOPE_UNRESOLVED"], 1)

    def test_monetary_unit_mismatch_flagged(self):
        result = inspect([row(unit_id="USD")])
        self.assertEqual(result["issue_counts"]["MONETARY_UNIT_MISMATCH"], 1)

    def test_duration_mismatch_flagged(self):
        result = inspect([row(period_type="時点")])
        self.assertEqual(result["issue_counts"]["DURATION_PERIOD_MISMATCH"], 1)

    def test_missing_context_flagged(self):
        result = inspect([row(context_id="")])
        self.assertEqual(result["issue_counts"]["CONTEXT_ID_MISSING"], 1)

if __name__ == "__main__":
    unittest.main()
