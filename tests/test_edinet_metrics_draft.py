import csv
import json
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path
from scripts.build_edinet_metrics_draft import load_approved, yoy_series, main


class EdinetMetricsDraftTests(unittest.TestCase):
    def write_queue(self, rows):
        fields = ["security_code", "candidate_metric", "value", "relative_year",
                  "review_status", "review_reason", "source_zip", "source_csv",
                  "element_id", "context_id", "unit_id", "row_number"]
        tmp = tempfile.NamedTemporaryFile("w", encoding="utf-8-sig", newline="", delete=False)
        self.addCleanup(lambda: Path(tmp.name).unlink(missing_ok=True))
        with tmp:
            writer = csv.DictWriter(tmp, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
        return Path(tmp.name)

    def row(self, **overrides):
        row = {"security_code": "12340", "candidate_metric": "sales", "value": "100",
               "relative_year": "当期", "review_status": "APPROVED",
               "review_reason": "APPROVED_SOURCE_VERIFIED", "source_zip": "12340_DOC_xbrl_csv.zip",
               "source_csv": "XBRL_TO_CSV/abc.csv", "element_id": "jppfs_cor:NetSales",
               "context_id": "CurrentYearDuration", "unit_id": "JPY", "row_number": "12"}
        row.update(overrides)
        return row

    def test_eps_persistence_uses_yoy_rates_not_absolute_deltas(self):
        rates = yoy_series([100, 110, 121, 133.1, 146.41])
        self.assertEqual(len(rates), 4)
        for rate in rates:
            self.assertAlmostEqual(rate, 0.1)

    def test_eps_yoy_marks_nonpositive_base_as_missing(self):
        rates = yoy_series([-1, 10, 12, 14, 16])
        self.assertIsNone(rates[0])
        self.assertAlmostEqual(rates[1], 0.2)

    def test_only_explicitly_approved_rows_are_used(self):
        path = self.write_queue([
            self.row(value="100"),
            self.row(value="999", review_status="MANUAL_REVIEW_REQUIRED")
        ])
        facts = load_approved(path, "1234")
        self.assertEqual(facts[("sales", "当期")]["value"], 100.0)

    def test_conflicting_approved_values_fail_closed(self):
        path = self.write_queue([self.row(value="100"), self.row(value="101")])
        with self.assertRaisesRegex(ValueError, "Conflicting approved facts"):
            load_approved(path, "1234")

    def test_invalid_approved_value_fails_closed(self):
        path = self.write_queue([self.row(value="N/A")])
        with self.assertRaisesRegex(ValueError, "invalid numeric"):
            load_approved(path, "1234")


    def test_approved_row_with_unresolved_reason_is_rejected(self):
        path = self.write_queue([self.row(review_reason="CHECK_FILING_AND_DUPLICATES")])
        with self.assertRaisesRegex(ValueError, "unresolved review_reason"):
            load_approved(path, "1234")

    def test_unreviewed_rows_are_not_used(self):
        path = self.write_queue([self.row(review_status="MANUAL_REVIEW_REQUIRED")])
        self.assertEqual(load_approved(path, "1234"), {})


    def test_unverified_risk_flags_are_unknown_in_generated_draft(self):
        queue = self.write_queue([])
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "draft.json"
            argv = ["build_edinet_metrics_draft.py", "--code", "1234", "--company", "テスト株式会社", "--queue", str(queue), "--out", str(output)]
            with patch.object(sys, "argv", argv):
                self.assertEqual(main(), None)
            payload = json.loads(output.read_text(encoding="utf-8"))
        self.assertIsNone(payload["metrics"]["finance_cf"]["ocf_negative_two_consecutive"])
        self.assertIsNone(payload["metrics"]["finance_cf"]["net_cash"])
        self.assertIsNone(payload["metrics"]["finance_cf"]["share_count_increased_three_years"])
        self.assertIsNone(payload["metrics"]["valuation"]["ebitda_nonpositive"])
        self.assertIsNone(payload["metrics"]["subsidiaries_ma"]["no_material_subsidiaries_and_no_ma_5y"])
        self.assertIsNone(payload["metrics"]["subsidiaries_ma"]["material_impairment"])
        self.assertIsNone(payload["metrics"]["shorts_supply"]["no_public_short_positions_90d"])
        self.assertTrue(all(value is None for value in payload["buy_block_inputs"].values()))

if __name__ == "__main__":
    unittest.main()
