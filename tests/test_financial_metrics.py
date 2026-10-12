import unittest
from scripts.financial_metrics import cagr, yoy, margins, margin_deltas, roa, net_debt_ebitda, fcf, ocf_ni_ratio, share_count_increase, incremental_roic

class FinancialMetricTests(unittest.TestCase):
    def test_cagr(self):
        self.assertAlmostEqual(cagr(100, 121, 2), .1)
        self.assertIsNone(cagr(-1, 10, 3))
        self.assertIsNone(cagr(100, None, 3))

    def test_yoy_and_margin_changes(self):
        self.assertAlmostEqual(yoy(120,100),.2)
        self.assertIsNone(yoy(120,-100))
        vals=margins([100,110,120],[10,12,15])
        self.assertEqual(len(margin_deltas(vals)),2)
        self.assertAlmostEqual(vals[-1],.125)

    def test_roa_average_assets(self):
        self.assertAlmostEqual(roa(10,90,110),.1)
        self.assertIsNone(roa(10,0,0))

    def test_debt_ebitda_and_fcf(self):
        self.assertAlmostEqual(net_debt_ebitda(30,10,10),2)
        self.assertIsNone(net_debt_ebitda(30,10,0))
        self.assertEqual(fcf(12,-5),7)
        self.assertIsNone(fcf(12,None))

    def test_three_year_ocf_ni(self):
        self.assertAlmostEqual(ocf_ni_ratio([1,2,3],[2,2,2]),1)
        self.assertIsNone(ocf_ni_ratio([1,None,3],[2,2,2]))

    def test_shares_and_incremental_roic(self):
        self.assertAlmostEqual(share_count_increase(100,105),.05)
        self.assertAlmostEqual(incremental_roic(10,20,100,150),.2)
        self.assertIsNone(incremental_roic(10,20,100,100))

if __name__=="__main__":
    unittest.main()
