"""Regression checks for the 2026-11-03 safety patch."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from scoring_engine import evaluate, STAGE1_GROUPS, STAGE2_GROUPS


def payload(missing_growth=0, score_growth=15):
    items = []
    for group, maximum in {**STAGE1_GROUPS, **STAGE2_GROUPS}.items():
        if group == "growth" and missing_growth:
            items.append(dict(key="growth_missing",group=group,points=None,max_points=missing_growth,status="missing"))
            maximum -= missing_growth
        items.append(dict(key=group,group=group,points=min(maximum,score_growth) if group=="growth" else maximum,max_points=maximum))
    return dict(items=items,buy_block_inputs=dict(shorts_direction_zero=False,shorts_applicable=True,ocf_ni_zero=False,dilution_zero=False,roic_below_h=False,roic_unavailable=False,short_type_a=False,peg_over_2=False,industry_per_over_130=False,base_upside_pct=25))

class SafetyPatchTests(unittest.TestCase):
    def test_direct_evaluate_rejects_missing_buy_inputs(self):
        p=payload();p["buy_block_inputs"]["ocf_ni_zero"]=None
        with self.assertRaises(ValueError):evaluate(p)
    def test_stage1_missing_adjusted_threshold(self):
        p=payload(missing_growth=10,score_growth=5)
        # Stage 1: 70/70; missing points do not force raw score >= 52.
        result=evaluate(p)
        self.assertTrue(result["stage1"]["passed"])
    def test_stage1_missing_over_limit(self):
        p=payload(missing_growth=15,score_growth=0)
        p["items"].append(dict(key="extra_missing",group="profitability",points=None,max_points=2,status="missing"))
        p["items"]=[x if x["key"]!="profitability" else {**x,"max_points":13,"points":13} for x in p["items"]]
        self.assertTrue(evaluate(p)["stage1"]["insufficient"])

if __name__=="__main__":unittest.main()
