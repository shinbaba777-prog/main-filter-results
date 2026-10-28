import unittest
from scripts.reconcile_4406_xbrl_current_year import reconcile

def inputs():
    years=[]
    for year in range(2022,2027):
        years.append({"document_id":"DOC"+str(year),"fiscal_year_end":f"{year}-03-31",
                      "sales_million_yen":"100","ordinary_profit_million_yen":"10",
                      "parent_net_income_million_yen":"5","eps_yen":"2","roe_reported_pct":"3"})
    row={"source_zip":"44060_DOC2022_xbrl_csv.zip","source_csv":"x.csv","row_number":"1",
         "candidate_metric":"sales","context_id":"CurrentYearDuration","unit_id":"JPY",
         "value":"100000000","element_id":"jpcrp_cor:NetSalesSummaryOfBusinessResults","consolidation_scope":"その他",
         "validation_status":"REVIEW_REQUIRED"}
    audit=[dict(row,row_number=str(i),context_id="PriorYearDuration") for i in range(680)]
    audit[0]=row
    return audit,years

class ReconcileTests(unittest.TestCase):
    def test_match_still_not_approved(self):
        a,v=inputs();r=reconcile(a,v)
        self.assertEqual(r["numeric_matches"],1)
        self.assertEqual(r["approved_rows"],0)
        self.assertFalse(r["scoring_eligible"])
    def test_mismatch_detected(self):
        a,v=inputs();a[0]["value"]="99000000"
        self.assertEqual(reconcile(a,v)["numeric_mismatches"],1)
    def test_prior_context_not_used(self):
        a,v=inputs();a[0]["context_id"]="Prior1YearDuration"
        self.assertEqual(reconcile(a,v)["current_year_comparable_candidates"],0)
    def test_different_profit_concept_is_not_comparable(self):
        a,v=inputs()
        a[0]["candidate_metric"]="profit"
        a[0]["element_id"]="jppfs_cor:IncomeBeforeIncomeTaxes"
        r=reconcile(a,v)
        self.assertEqual(r["different_profit_concepts_not_comparable"],1)
        self.assertEqual(r["numeric_mismatches"],0)
        self.assertEqual(r["current_year_comparable_candidates"],0)

    def test_parent_profit_concept_matches(self):
        a,v=inputs()
        a[0]["candidate_metric"]="profit"
        a[0]["element_id"]="jppfs_cor:ProfitLossAttributableToOwnersOfParent"
        a[0]["value"]="5000000"
        r=reconcile(a,v)
        self.assertEqual(r["numeric_matches"],1)
        self.assertFalse(r["scoring_eligible"])

    def test_reject_unexpected_approval(self):
        a,v=inputs();a[0]["validation_status"]="APPROVED"
        with self.assertRaises(ValueError):reconcile(a,v)

if __name__=="__main__":unittest.main()
