#!/usr/bin/env python3
"""Regression tests: review-only 4406 evidence cannot become a published score."""
import unittest
from scripts.bridge_4406_review_to_scoring import dry_run

def inventory():
    return {"security_code": "4406", "status": "REVIEW_REQUIRED",
            "scoring_eligible": False,
            "reconciled_entries": [
                {"metric": f"metric_{i}", "scoring_eligible": False} for i in range(45)
            ]}

class ScoringBridgeSafetyTests(unittest.TestCase):
    def test_no_score_and_no_publication(self):
        result = dry_run(inventory())
        self.assertFalse(result["publish_to_index"])
        self.assertFalse(result["source_approved"])
        self.assertEqual(result["engine_result"]["judgment"], "STAGE1 DATA-INSUFFICIENT")
        self.assertIsNone(result["engine_result"]["total"]["adjusted_score"])

    def test_rejects_approval_flip(self):
        data = inventory()
        data["scoring_eligible"] = True
        with self.assertRaises(ValueError):
            dry_run(data)

    def test_rejects_single_approved_entry(self):
        data = inventory()
        data["reconciled_entries"][0]["scoring_eligible"] = True
        with self.assertRaises(ValueError):
            dry_run(data)

    def test_rejects_missing_evidence(self):
        data = inventory()
        data["reconciled_entries"].pop()
        with self.assertRaises(ValueError):
            dry_run(data)

    def test_rejects_wrong_security(self):
        data = inventory()
        data["security_code"] = "9999"
        with self.assertRaises(ValueError):
            dry_run(data)

if __name__ == "__main__":
    unittest.main()
