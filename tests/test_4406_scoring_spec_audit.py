"""Read-only specification audit: detect, do not change, scoring gate behavior."""
import unittest
from scripts.scoring_engine import evaluate, STAGE1_GROUPS, STAGE2_GROUPS

def payload(stage1_status="scored", roic_unavailable=False):
    items=[]
    for group,maxp in {**STAGE1_GROUPS,**STAGE2_GROUPS}.items():
        if group=="roic_capital" and stage1_status=="not_applicable":
            status="not_applicable";points=None
        else:
            status="scored";points=maxp
        items.append(dict(key=group,group=group,max_points=maxp,points=points,status=status,source="synthetic",evidence="TEST ONLY"))
    return {"items":items,"buy_block_inputs":{"roic_unavailable":roic_unavailable}}

class SpecAudit(unittest.TestCase):
    def test_stage1_raw_score_52_requirement_even_when_adjusted_achievement_passes(self):
        p=payload()
        for x in p["items"]:
            if x["group"]=="growth":x["status"]="not_applicable";x["points"]=None
            elif x["group"]=="profitability":x["points"]=0
            elif x["group"]=="finance_cf":x["points"]=0
        r=evaluate(p)
        self.assertEqual(r["stage1"]["raw_score"],40)
        self.assertAlmostEqual(r["stage1"]["achievement_pct"],40/65*100)
        self.assertFalse(r["stage1"]["passed"])
        self.assertEqual(r["judgment"],"一次不通過")

    def test_roic_unavailable_is_notice_not_buy_block(self):
        r=evaluate(payload(roic_unavailable=True))
        self.assertTrue(any("ROIC算出不能" in x for x in r["notices"]))
        self.assertFalse(any(x["active"] and "ROIC" in x["condition"] for x in r["buy_blocks"]))
        self.assertEqual(r["judgment"],"強いBUY")

    def test_roic_below_h_blocks_buy(self):
        p=payload();p["buy_block_inputs"]["roic_below_h"]=True
        r=evaluate(p)
        self.assertEqual(r["judgment"],"最大HOLD")

if __name__=="__main__":
    unittest.main()
