import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from diagnose_edinet_context_conflicts import diagnose

MANIFEST = {"periods": [{"file": "a.zip", "periodEnd": "2025-03-31"},
                        {"file": "b.zip", "periodEnd": "2026-03-31"}]}

def row(file, context, value):
    return {"security_code": "44060", "candidate_metric": "sales",
            "element_id": "jpcrp_cor:NetSalesSummaryOfBusinessResults",
            "consolidation_scope": "その他", "unit_id": "JPY",
            "source_zip": file, "context_id": context, "value": value}

class ContextConflictTests(unittest.TestCase):
    def test_different_member_suffix_not_compared(self):
        result = diagnose([row("a.zip", "CurrentYearDuration", "100"),
                           row("b.zip", "Prior1YearDuration_NonConsolidatedMember", "200")], MANIFEST)
        self.assertEqual(result["conflicts_after_suffix_partition"], 0)

    def test_same_suffix_difference_flagged(self):
        result = diagnose([row("a.zip", "CurrentYearDuration", "100"),
                           row("b.zip", "Prior1YearDuration", "200")], MANIFEST)
        self.assertEqual(result["conflicts_after_suffix_partition"], 1)
        self.assertFalse(result["scoring_ready"])

    def test_same_filing_ambiguous_values_flagged(self):
        result = diagnose([row("a.zip", "CurrentYearDuration", "100"),
                           row("a.zip", "CurrentYearDuration", "110"),
                           row("b.zip", "Prior1YearDuration", "100")], MANIFEST)
        self.assertEqual(result["reason_counts"]["WITHIN_FILING_AMBIGUITY"], 1)

if __name__ == "__main__":
    unittest.main()
