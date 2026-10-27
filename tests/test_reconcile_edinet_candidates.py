import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from reconcile_edinet_candidates import reconcile

MANIFEST = {"periods": [{"file": "a.zip"}]}
ROW = {"security_code": "44060", "candidate_metric": "sales",
       "value": "100", "source_zip": "a.zip", "source_csv": "x.csv", "row_number": "2"}

class ReconciliationTests(unittest.TestCase):
    def test_matching_rows_still_require_review(self):
        result = reconcile([ROW], [dict(ROW, consolidation_scope="その他",
                                      validation_status="REVIEW_REQUIRED")], MANIFEST)
        self.assertEqual(result["status"], "REVIEW_REQUIRED")
        self.assertFalse(result["scoring_ready"])
        self.assertEqual(result["scope_unresolved"], 1)

    def test_missing_audit_row_blocks(self):
        self.assertEqual(reconcile([ROW], [], MANIFEST)["status"], "BLOCKED")

    def test_unexpected_source_zip_blocks(self):
        changed = dict(ROW, source_zip="unknown.zip")
        self.assertEqual(reconcile([changed], [changed], MANIFEST)["status"], "BLOCKED")

    def test_missing_manifest_blocks(self):
        self.assertEqual(reconcile([ROW], [ROW], None)["status"], "BLOCKED")

if __name__ == "__main__":
    unittest.main()
