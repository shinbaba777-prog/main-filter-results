import unittest
from scripts.rubric_scoring import band, growth_score, profitability_score, eps_score, finance_cf_score

class RubricScoringTests(unittest.TestCase):
    def test_band_thresholds_are_inclusive(self):
        self.assertEqual(band(0.20, [(0.20, 4), (0.10, 2)]), (4, "scored"))
        self.assertEqual(band(0.099, [(0.20, 4), (0.10, 2)]), (0, "scored"))
        self.assertEqual(band(None, [(0.20, 4)]), (None, "missing"))

    def test_growth_scores_and_missing_forecast(self):
        r = growth_score({
            "sales_long_cagr":0.20, "sales_3y_cagr":0.10, "sales_yoy":0.05,
            "sales_forecast_growth":None, "operating_profit_long_cagr":0.20
        })
        self.assertEqual([x["points"] for x in r], [4,2,1,None,2])
        self.assertEqual(sum(x["max_points"] for x in r), 15)

    def test_profitability_margin_direction_declines_override(self):
        r = profitability_score({
            "operating_margin":0.25,
            "operating_margin_deltas":[0.01,-0.01,-0.01],
            "gross_margin_deltas":[0.01,0.01,0.01],
            "roa":0.10
        })
        self.assertEqual([x["points"] for x in r], [5,0,3,3])
        self.assertEqual(sum(x["max_points"] for x in r), 15)

    def test_eps_forecast_missing_is_explicit(self):
        r = eps_score({"eps_long_cagr":0.20,"eps_yoy":0.15,"eps_forecast_growth":None,"eps_yoy_last4":[0.1,0.2,0.3,0.4]})
        self.assertEqual([x["points"] for x in r], [3,2,None,2])
        self.assertEqual(sum(x["max_points"] for x in r), 10)

    def test_finance_cf_scoring(self):
        r = finance_cf_score({
            "ocf_ni_3y":0.8,"net_income_3y":10,"ocf_3y":8,
            "net_debt_ebitda":3,"share_count_increase_3y":0.01,
            "share_count_increased_three_years":False,"equity_ratio":0.5,
            "fcf_3y_sum":1,"fcf_latest":-1
        })
        self.assertEqual([x["points"] for x in r], [2,1,1,2,1])
        self.assertEqual(sum(x["max_points"] for x in r), 10)

if __name__ == "__main__":
    unittest.main()
