import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from audit_edinet_false_conflicts import summarize

MANIFEST = {"periods": [{"file": "a.zip", "periodEnd": "2025-03-31"},
                        {"file": "b.zip", "periodEnd": "2026-03-31"}]}

def fact(source, context, value):
    return {"security_code": "44060", "candidate_metric": "sales",
            "element_id": "jpcrp_cor:NetSalesSummaryOfBusinessResults",
            "consolidation_scope": "その他", "unit_id": "JPY",
            "source_zip": source, "context_id": context, "value": value}

class FalseConflictAuditTests(unittest.TestCase):
    def test_member_difference_removes_false_comparison(self):
        result = summarize([fact("a.zip", "CurrentYearDuration", "100"),
                            fact("b.zip", "Prior1YearDuration_NonConsolidatedMember", "200")], MANIFEST)
        self.assertEqual(result["broad_conflicts"], 1)
        self.assertEqual(result["member_aware_conflicts"], 0)
        self.assertFalse(result["scoring_ready"])

    def test_real_same_member_difference_stays_flagged(self):
        result = summarize([fact("a.zip", "CurrentYearDuration", "100"),
                            fact("b.zip", "Prior1YearDuration", "200")], MANIFEST)
        self.assertEqual(result["member_aware_conflicts"], 1)
        self.assertFalse(result["scoring_ready"])

if __name__ == "__main__":
    unittest.main()
