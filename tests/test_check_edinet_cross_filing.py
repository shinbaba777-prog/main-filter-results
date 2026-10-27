import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from check_edinet_cross_filing import inspect

MANIFEST = {"periods": [{"file": "old.zip", "periodEnd": "2025-03-31"},
                        {"file": "new.zip", "periodEnd": "2026-03-31"}]}

def fact(source, context, value, scope="連結"):
    return {"security_code": "44060", "candidate_metric": "sales",
            "element_id": "jppfs_cor:NetSales", "consolidation_scope": scope,
            "unit_id": "JPY", "source_zip": source,
            "context_id": context, "value": value}

class CrossFilingTests(unittest.TestCase):
    def test_conflicting_prior_year_is_flagged(self):
        rows = [fact("old.zip", "CurrentYearDuration", "100"),
                fact("new.zip", "Prior1YearDuration", "110")]
        result = inspect(rows, MANIFEST)
        self.assertEqual(result["conflict_groups"], 1)
        self.assertFalse(result["scoring_ready"])

    def test_matching_values_are_not_approved(self):
        rows = [fact("old.zip", "CurrentYearDuration", "100"),
                fact("new.zip", "Prior1YearDuration", "100")]
        result = inspect(rows, MANIFEST)
        self.assertEqual(result["conflict_groups"], 0)
        self.assertEqual(result["overlapping_groups"], 1)
        self.assertFalse(result["scoring_ready"])

    def test_different_scopes_not_compared(self):
        rows = [fact("old.zip", "CurrentYearDuration", "100"),
                fact("new.zip", "Prior1YearDuration", "110", "個別")]
        self.assertEqual(inspect(rows, MANIFEST)["overlapping_groups"], 0)

if __name__ == "__main__":
    unittest.main()
