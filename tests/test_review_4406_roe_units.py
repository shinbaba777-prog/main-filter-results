import unittest
from scripts.review_4406_roe_units import review,TAG

def fixtures():
    verified=[];rows=[]
    for year in range(2022,2027):
        doc="DOC"+str(year)
        verified.append({"document_id":doc,"fiscal_year_end":f"{year}-03-31","roe_reported_pct":"5.2"})
        rows.append({"source_zip":f"44060_{doc}_xbrl_csv.zip","source_csv":"a.csv",
            "row_number":str(year),"candidate_metric":"roe","context_id":"CurrentYearDuration",
            "element_id":TAG,"unit_id":"pure","value":"0.052","consolidation_scope":"その他",
            "validation_status":"REVIEW_REQUIRED"})
    filler=dict(rows[0],candidate_metric="sales",context_id="Prior1YearDuration")
    rows += [dict(filler,row_number=str(i)) for i in range(675)]
    return rows,verified

class RoeUnitTests(unittest.TestCase):
    def test_pure_ratio_matches_percent_without_approval(self):
        a,v=fixtures();r=review(a,v)
        self.assertEqual(r["numeric_matches"],5)
        self.assertEqual(r["approved_rows"],0)
        self.assertFalse(r["scoring_eligible"])
    def test_mismatch_detected(self):
        a,v=fixtures();a[0]["value"]="0.051"
        self.assertEqual(review(a,v)["numeric_mismatches"],1)
    def test_rejects_approval_flip(self):
        a,v=fixtures();a[0]["validation_status"]="APPROVED"
        with self.assertRaises(ValueError):review(a,v)
    def test_rejects_duplicate_filing_roe(self):
        a,v=fixtures();a[5]=dict(a[0])
        with self.assertRaises(ValueError):review(a,v)

if __name__=="__main__":unittest.main()
