import unittest
from scripts.scoring_engine import evaluate

GROUPS = [
    ("growth", 15), ("profitability", 15), ("roic_capital", 15),
    ("finance_cf", 10), ("eps_growth", 10), ("valuation", 15),
    ("competitive_advantage", 5), ("subsidiaries_ma", 3),
    ("shorts_supply", 7), ("ir_reaction", 5),
]

def payload(points=0, missing_group=None, missing_points=None, na_group=None, blocks=None):
    items = []
    for group, maximum in GROUPS:
        status = "scored"
        p = points * maximum / 100
        if group == missing_group:
            status, p = "missing", None
        if group == na_group:
            status, p = "not_applicable", None
        if missing_points and group in missing_points:
            status, p = "missing", None
        items.append({"key": group, "group": group, "points": p,
                      "max_points": maximum, "status": status,
                      "evidence": "test", "source": "test"})
    b = {"shorts_direction_zero": False, "shorts_applicable": False,
         "ocf_ni_zero": False, "dilution_zero": False,
         "roic_below_h": False, "roic_unavailable": False,
         "short_type_a": False, "peg_over_2": False,
         "industry_per_over_130": False, "base_upside_pct": 35}
    if blocks:
        b.update(blocks)
    return {"items": items, "buy_block_inputs": b}

class ScoringEngineTests(unittest.TestCase):
    def test_perfect_score(self):
        r = evaluate(payload(points=100))
        self.assertEqual(r["total"]["adjusted_score"], 100)
        self.assertEqual(r["judgment"], "強いBUY")

    def test_stage1_missing_over_16_stops(self):
        r = evaluate(payload(points=80, missing_points={"growth", "profitability"}))
        self.assertEqual(r["judgment"], "STAGE1 DATA-INSUFFICIENT")
        self.assertTrue(r["stage1"]["insufficient"])

    def test_total_missing_over_20_stops(self):
        r = evaluate(payload(points=100, missing_points={"growth", "profitability"}))
        self.assertEqual(r["judgment"], "STAGE1 DATA-INSUFFICIENT")

    def test_non_applicable_removed_from_denominator(self):
        r = evaluate(payload(points=80, na_group="shorts_supply"))
        self.assertEqual(r["total"]["not_applicable_points"], 7)
        self.assertAlmostEqual(r["total"]["adjusted_score"], 80)

    def test_buy_block_caps_judgment_at_hold(self):
        r = evaluate(payload(points=100, blocks={"dilution_zero": True}))
        self.assertEqual(r["judgment"], "最大HOLD")
        self.assertTrue(next(x for x in r["buy_blocks"] if x["condition"].startswith("③"))["active"])

    def test_roic_unavailable_is_notice_not_block(self):
        r = evaluate(payload(points=100, blocks={"roic_unavailable": True}))
        self.assertEqual(r["judgment"], "強いBUY")
        self.assertTrue(r["notices"])

if __name__ == "__main__":
    unittest.main()
