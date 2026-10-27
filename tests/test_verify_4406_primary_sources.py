#!/usr/bin/env python3
"""Regression tests for the review-only source gate. No network or scoring."""
import copy
import unittest
from scripts.verify_4406_primary_sources import EXPECTED, FIELDS, verify

def sample_rows():
    return [
        dict(fiscal_year_end=fy, security_code="4406", consolidation_scope="連結",
             **{field: str(value) for field, value in zip(FIELDS, values)})
        for fy, values in EXPECTED.items()
    ]

def sample_audit():
    return {"candidate_rows_audited": 680,
            "important_warning": "No row is approved for investment scoring."}

class PrimarySourceGateTests(unittest.TestCase):
    def test_clean_reconciliation_still_blocks_scoring(self):
        result = verify(sample_rows(), sample_audit())
        self.assertEqual(result["matched_metrics"], 45)
        self.assertEqual(result["issues"], [])
        self.assertFalse(result["scoring_eligible"])
        self.assertEqual(result["status"], "REVIEW_REQUIRED")

    def test_single_changed_value_fails_closed(self):
        rows = sample_rows()
        rows[0]["ocf_million_yen"] = "1079"
        result = verify(rows, sample_audit())
        self.assertEqual(result["status"], "MISMATCH")
        self.assertTrue(result["issues"])
        self.assertFalse(result["scoring_eligible"])

    def test_missing_year_fails_closed(self):
        result = verify(sample_rows()[:-1], sample_audit())
        self.assertEqual(result["status"], "MISMATCH")

    def test_duplicate_year_fails_closed(self):
        rows = sample_rows()
        rows.append(copy.deepcopy(rows[0]))
        self.assertEqual(verify(rows, sample_audit())["status"], "MISMATCH")

    def test_unexpected_scope_fails_closed(self):
        rows = sample_rows()
        rows[0]["consolidation_scope"] = "個別"
        self.assertEqual(verify(rows, sample_audit())["status"], "MISMATCH")

    def test_changed_audit_warning_fails_closed(self):
        audit = sample_audit()
        audit["important_warning"] = "all approved"
        self.assertEqual(verify(sample_rows(), audit)["status"], "MISMATCH")

    def test_missing_metric_fails_closed(self):
        rows = sample_rows()
        rows[0].pop("eps_yen")
        self.assertEqual(verify(rows, sample_audit())["status"], "MISMATCH")

if __name__ == "__main__":
    unittest.main()
