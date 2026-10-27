import unittest
from scripts.build_4406_xbrl_review_queue import triage

def fixtures():
    return [{"source_zip":"a.zip","source_csv":"a.csv","row_number":"3","candidate_metric":"sales",
             "element_id":"tag","context_id":"CurrentYearDuration","consolidation_scope":"その他",
             "unit_id":"JPY","validation_status":"REVIEW_REQUIRED",
             "validation_flags":"CONSOLIDATION_SCOPE_UNCLEAR"}]

def summary():
    return {"candidate_rows_audited":1,"important_warning":"No row is approved for investment scoring."}

class QueueTests(unittest.TestCase):
    def test_review_only(self):
        r=triage(fixtures(),summary())
        self.assertEqual(r["approved_rows"],0)
        self.assertFalse(r["scoring_eligible"])
        self.assertEqual(r["by_candidate_metric"]["sales"]["scope_unclear"],1)
    def test_reject_count_mismatch(self):
        with self.assertRaises(ValueError):triage([],summary())
    def test_reject_approval_flip(self):
        r=fixtures();r[0]["validation_status"]="APPROVED"
        with self.assertRaises(ValueError):triage(r,summary())
    def test_reject_duplicate_source_row(self):
        r=fixtures()*2;s=summary();s["candidate_rows_audited"]=2
        with self.assertRaises(ValueError):triage(r,s)

if __name__=="__main__":unittest.main()
