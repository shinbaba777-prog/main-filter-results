import unittest
from scripts.check_edinet_readiness import assess

def sample():
    return {"requested_code": "4406", "requested_periods": 2, "status": "complete",
            "periods": [{"periodEnd": "2025-03-31", "docID": "A12345", "status": "downloaded", "file": "a.zip"},
                        {"periodEnd": "2026-03-31", "docID": "B12345", "status": "downloaded", "file": "b.zip"}],
            "gaps": [], "failed_scan_dates": [], "amendments": []}

class ReadinessGateTests(unittest.TestCase):
    def test_complete_never_means_scoring_ready(self):
        result = assess(sample(), {}, {}, "4406")
        self.assertTrue(result["download_complete"])
        self.assertFalse(result["scoring_ready"])
        self.assertEqual(result["status"], "REVIEW_REQUIRED")

    def test_missing_period_blocks(self):
        data = sample()
        data["periods"].pop()
        self.assertFalse(assess(data, {}, {})["download_complete"])

    def test_amendment_blocks(self):
        data = sample()
        data["amendments"] = [{"docID": "C12345"}]
        self.assertFalse(assess(data, {}, {})["download_complete"])

    def test_code_mismatch_blocks(self):
        self.assertFalse(assess(sample(), {}, {}, "9999")["download_complete"])

    def test_missing_manifest_blocks(self):
        self.assertEqual(assess(None, {}, {})["status"], "DATA_INSUFFICIENT")

if __name__ == "__main__":
    unittest.main()
