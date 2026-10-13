import unittest
from scripts.build_edinet_core_metric_review import infer_fiscal_year


class EdinetCoreMetricReviewTests(unittest.TestCase):
    def test_current_year_context_uses_filing_year(self):
        self.assertEqual(infer_fiscal_year("2026-03-31", 0), "2026")

    def test_prior_context_subtracts_offset(self):
        self.assertEqual(infer_fiscal_year("2026-03-31", 4), "2022")

    def test_invalid_filing_period_stays_missing(self):
        self.assertEqual(infer_fiscal_year("unknown", 1), "")


if __name__ == "__main__":
    unittest.main()
