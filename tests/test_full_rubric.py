import unittest
from scripts.rubric_scoring import valuation_score, competitive_advantage_score, subsidiaries_ma_score, shorts_supply_score, ir_reaction_score, roic_capital_score, build_items

class FullRubricTests(unittest.TestCase):
    def test_valuation_thresholds(self):
        r=valuation_score({"peg":0.75,"industry_relative_per":0.70,"fcf_yield":0.05,"ev_ebitda":8})
        self.assertEqual([x["points"] for x in r],[6,4,3,2])

    def test_advantage_requires_evidence(self):
        r=competitive_advantage_score({"evidence_backed_advantage_types":["switching_cost","niche_top"],"roic_or_roe_last3":[.15,.16,.17],"management_ownership":.10})
        self.assertEqual([x["points"] for x in r],[3,2])

    def test_no_short_positions_is_not_applicable(self):
        r=shorts_supply_score({"no_public_short_positions_90d":True})
        self.assertEqual(r[0]["status"],"not_applicable")

    def test_ir_zero_target_is_not_applicable(self):
        self.assertEqual(ir_reaction_score({"target_ir_count_12m":0})[0]["status"],"not_applicable")

    def test_ir_events_are_scored_by_sum(self):
        r=ir_reaction_score({"target_ir_count_12m":2,"eligible_ir_count_12m":2,"eligible_excess_returns":[.10,.03]})
        self.assertEqual(r[0]["points"],4)

    def test_roic_capital_total(self):
        r=roic_capital_score({"roic":.20,"incremental_roic":.20,"roic_deltas":[.01,.01,0],"reinvestment_rate":.30,"capital_cost_h":.08,"roe":.15})
        self.assertEqual([x["points"] for x in r],[5,4,2,2,2])
        self.assertEqual(sum(x["max_points"] for x in r),15)

    def test_build_items_marks_unprovided_groups_missing(self):
        r=build_items({})
        self.assertEqual(len(r),10)
        self.assertTrue(all(x["status"]=="missing" for x in r))

if __name__=="__main__":
    unittest.main()
