import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from scoring_engine import evaluate,STAGE1_GROUPS,STAGE2_GROUPS

class BoundaryTests(unittest.TestCase):
 def test_43_of_65_passes(self):
  scores={'growth':0,'profitability':15,'roic_capital':0,'finance_cf':10,'eps_growth':10,'valuation':8}
  items=[]
  for g,m in {**STAGE1_GROUPS,**STAGE2_GROUPS}.items():
   if g=='growth':items.append(dict(key='missing',group=g,points=None,max_points=15,status='missing'))
   else:items.append(dict(key=g,group=g,points=scores.get(g,m),max_points=m))
  b=dict(shorts_direction_zero=False,shorts_applicable=True,ocf_ni_zero=False,dilution_zero=False,roic_below_h=False,roic_unavailable=False,short_type_a=False,peg_over_2=False,industry_per_over_130=False,base_upside_pct=25)
  result=evaluate(dict(items=items,buy_block_inputs=b))
  self.assertEqual(result['stage1']['raw_score'],43)
  self.assertTrue(result['stage1']['passed'])

if __name__=='__main__':unittest.main()
