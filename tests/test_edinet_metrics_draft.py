import csv
import tempfile
import unittest
from pathlib import Path
from scripts.build_edinet_metrics_draft import load_approved, yoy_series


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

    def test_eps_yoy_returns_missing_when_prior_eps_nonpositive(self):
        self.assertIsNone(yoy_series([-1, 10, 12, 14, 16]))

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


if __name__ == "__main__":
    unittest.main()
