import unittest
from scripts.build_4406_evidence_inventory import build
from scripts.verify_4406_primary_sources import EXPECTED, FIELDS

def fixtures():
    rows=[]
    for year, values in EXPECTED.items():
        r={"fiscal_year_end":year,"security_code":"4406","consolidation_scope":"連結","document_id":"DOC"+year[:4],"source_file":"DOC"+year[:4]+".zip"}
        r.update({field:str(value) for field,value in zip(FIELDS,values)})
        rows.append(r)
    return rows

def audit():
    return {"candidate_rows_audited":680,"important_warning":"No row is approved for investment scoring."}

class InventoryGateTests(unittest.TestCase):
    def test_valid_source_still_review_only(self):
        x=build(fixtures(),audit())
        self.assertEqual(len(x["reconciled_entries"]),45)
        self.assertFalse(x["scoring_eligible"])
        self.assertTrue(all(e["scoring_eligible"] is False for e in x["reconciled_entries"]))

    def test_rejects_tampered_metric(self):
        x=fixtures();x[0]["sales_million_yen"]="1"
        with self.assertRaises(ValueError):build(x,audit())

    def test_rejects_audit_status_change(self):
        x=audit();x["candidate_rows_audited"]=679
        with self.assertRaises(ValueError):build(fixtures(),x)

    def test_rejects_missing_year(self):
        with self.assertRaises(ValueError):build(fixtures()[:-1],audit())

    def test_rejects_missing_document_id(self):
        x=fixtures();x[0]["document_id"]=""
        with self.assertRaises(ValueError):build(x,audit())

    def test_rejects_duplicate_document_id(self):
        x=fixtures();x[0]["document_id"]=x[1]["document_id"]
        with self.assertRaises(ValueError):build(x,audit())

    def test_rejects_missing_source_file(self):
        x=fixtures();x[0]["source_file"]=""
        with self.assertRaises(ValueError):build(x,audit())

if __name__=="__main__":
    unittest.main()
