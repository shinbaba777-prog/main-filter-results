import unittest
from scripts.prioritize_4406_xbrl_review import prioritize

def row(metric="sales",context="CurrentYearDuration"):
    return {"candidate_metric":metric,"source_zip":"filing.zip","source_csv":"file.csv","row_number":"7",
            "element_id":"tag","context_id":context,"validation_status":"REVIEW_REQUIRED",
            "validation_flags":"CONSOLIDATION_SCOPE_UNCLEAR","unit_id":"JPY","consolidation_scope":"その他"}

class PriorityTests(unittest.TestCase):
    def test_groups_and_no_approval(self):
        r=prioritize([row(),row("ordinary_profit")])
        self.assertEqual(r["candidate_rows"],2)
        self.assertEqual(r["review_groups"],2)
        self.assertEqual(r["approved_rows"],0)
        self.assertFalse(r["scoring_eligible"])
    def test_focus_metric_first(self):
        r=prioritize([row("unknown"),row("sales")])
        self.assertEqual(r["groups"][0]["candidate_metric"],"sales")
    def test_reject_approved_status(self):
        x=row();x["validation_status"]="APPROVED"
        with self.assertRaises(ValueError):prioritize([x])
    def test_reject_missing_provenance(self):
        x=row();x["element_id"]=""
        with self.assertRaises(ValueError):prioritize([x])

if __name__=="__main__":unittest.main()
