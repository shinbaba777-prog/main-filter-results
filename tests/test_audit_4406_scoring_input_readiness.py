import csv
import unittest
from pathlib import Path
from scripts.audit_4406_scoring_input_readiness import audit

class ScoringReadinessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with Path("data/edinet/verified/4406_five_year_financials.csv").open(encoding="utf-8-sig",newline="") as f:
            cls.rows=list(csv.DictReader(f))
    def test_current_rows_block_scoring(self):
        r=audit(self.rows)
        self.assertIsNone(r["formal_score"])
        self.assertFalse(r["scoring_eligible"])
        self.assertEqual(r["fcf_arithmetic_matches"],5)
        self.assertEqual(len(r["metric_missing_years"]["roic_pct"]),5)
    def test_reject_fcf_mismatch(self):
        rows=[dict(x) for x in self.rows]
        rows[0]["fcf_ocf_plus_icf_million_yen"]="0"
        with self.assertRaises(ValueError):audit(rows)
    def test_reject_nonconsecutive_periods(self):
        rows=[dict(x) for x in self.rows]
        rows[1]["fiscal_year_end"]="2024-03-31"
        with self.assertRaises(ValueError):audit(rows)
    def test_reject_nonconsolidated_scope(self):
        rows=[dict(x) for x in self.rows]
        rows[0]["consolidation_scope"]="個別"
        with self.assertRaises(ValueError):audit(rows)

if __name__=="__main__":unittest.main()
