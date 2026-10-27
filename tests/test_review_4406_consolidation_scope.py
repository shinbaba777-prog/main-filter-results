import unittest
from scripts.review_4406_consolidation_scope import build

def fixtures():
    x={"numeric_matches":65,"numeric_mismatches":0,"comparisons":[
        {"scoring_eligible":False,"consolidation_scope":"その他","document_id":"D",
         "source_csv":"x.csv","row_number":str(i),"element_id":"tag","context_id":"CurrentYearDuration"}
        for i in range(65)]}
    r={"numeric_matches":5,"rows":[{"scoring_eligible":False,"consolidation_scope":"その他",
         "document_id":"D","source_csv":"x.csv","row_number":str(i),"element_id":"roe",
         "context_id":"CurrentYearDuration"} for i in range(5)]}
    return x,r

class ScopeTests(unittest.TestCase):
    def test_unresolved_is_not_approved(self):
        x,r=fixtures();out=build(x,r)
        self.assertEqual(out["unresolved_scope_count"],70)
        self.assertFalse(out["consolidated_scope_confirmed"])
        self.assertFalse(out["scoring_eligible"])
    def test_rejects_unexpected_numeric_match_count(self):
        x,r=fixtures();x["numeric_matches"]=64
        with self.assertRaises(ValueError):build(x,r)
    def test_rejects_scoring_approval(self):
        x,r=fixtures();x["comparisons"][0]["scoring_eligible"]=True
        with self.assertRaises(ValueError):build(x,r)
    def test_explicit_scope_not_automatic_approval(self):
        x,r=fixtures()
        for row in x["comparisons"]+r["rows"]:row["consolidation_scope"]="連結"
        out=build(x,r)
        self.assertTrue(out["consolidated_scope_confirmed"])
        self.assertEqual(out["approved_rows"],0)

if __name__=="__main__":unittest.main()
