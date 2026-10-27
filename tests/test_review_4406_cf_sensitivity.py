import unittest
from scripts.review_4406_cf_sensitivity import calculate

def rows():
    values = [
        ("2022-03-31",1078,-1602,811),
        ("2023-03-31",104,-659,-444),
        ("2024-03-31",3578,-60,220),
        ("2025-03-31",-224,-174,522),
        ("2026-03-31",1643,501,597),
    ]
    return [{"fiscal_year_end":y,"consolidation_scope":"連結","document_id":f"D{i}",
             "ocf_million_yen":str(o),"icf_million_yen":str(inv),
             "fcf_ocf_plus_icf_million_yen":str(o+inv),
             "parent_net_income_million_yen":str(ni)}
            for i,(y,o,inv,ni) in enumerate(values)]

class SensitivityTests(unittest.TestCase):
    def test_sensitivity_and_no_scoring(self):
        r=calculate(rows())
        self.assertEqual(r["reported_fcf_3y_million_yen"],5264)
        self.assertEqual(r["fcf_3y_excluding_2026_security_sale_proceeds_million_yen"],4322)
        self.assertEqual(r["fcf_2026_excluding_security_sale_proceeds_million_yen"],1202)
        self.assertEqual(r["ocf_3y_million_yen"],4997)
        self.assertFalse(r["scoring_eligible"])
        self.assertFalse(r["publish_to_index"])

    def test_rejects_mismatched_fcf(self):
        a=rows();a[-1]["fcf_ocf_plus_icf_million_yen"]="999"
        with self.assertRaises(ValueError):calculate(a)

    def test_rejects_missing_year(self):
        with self.assertRaises(ValueError):calculate(rows()[:-1])

    def test_rejects_unprovenanced_scope(self):
        a=rows();a[-1]["consolidation_scope"]="個別"
        with self.assertRaises(ValueError):calculate(a)

if __name__=="__main__":
    unittest.main()
