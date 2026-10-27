import unittest

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from verify_scoring_inputs import validate

class ScoringInputGateTests(unittest.TestCase):
    def test_missing_payload_is_blocked(self):
        self.assertTrue(validate(None, None, None, None))

    def test_empty_metrics_and_blocks_are_blocked(self):
        manifest = {"requested_code": "4406", "requested_periods": 1, "status": "complete",
                    "periods": [{"periodEnd": "2026-03-31", "docID": "S100YGXD",
                                 "status": "downloaded", "file": "a.zip"}],
                    "gaps": [], "failed_scan_dates": [], "amendments": []}
        payload = {"code": "4406", "company": "新日本理化",
                   "analysis_date": "2026-10-28", "metrics": {},
                   "verified_sources": {}, "buy_block_inputs": {}}
        problems = validate(payload, manifest, {}, {})
        self.assertTrue(any("metric group missing" in x for x in problems))
        self.assertTrue(any("BUY-block" in x for x in problems))

    def test_uncited_metric_is_blocked(self):
        manifest = {"requested_code": "4406", "requested_periods": 1, "status": "complete",
                    "periods": [{"periodEnd": "2026-03-31", "docID": "S100YGXD",
                                 "status": "downloaded", "file": "a.zip"}],
                    "gaps": [], "failed_scan_dates": [], "amendments": []}
        groups = {name: {} for name in (
            "growth", "profitability", "roic_capital", "finance_cf",
            "eps_growth", "valuation", "competitive_advantage",
            "subsidiaries_ma", "shorts_supply", "ir_reaction")}
        groups["growth"]["sales_yoy"] = 0.1
        payload = {"code": "4406", "company": "新日本理化",
                   "analysis_date": "2026-10-28", "metrics": groups,
                   "verified_sources": {}, "buy_block_inputs": {}}
        problems = validate(payload, manifest, {}, {})
        self.assertIn("unverified metric: growth.sales_yoy", problems)

if __name__ == "__main__":
    unittest.main()
