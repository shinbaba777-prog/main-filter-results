#!/usr/bin/env python3
"""Fail-closed arithmetic audit for 4406 ROIC candidates; NEVER approves scoring."""
from decimal import Decimal as D
import json
from pathlib import Path

# Rounded JPY-million candidates; verify provenance before approval.
ROWS=[
(2021,15208,8925,3148,24437,None,None),
(2022,15937,9962,3495,32358,1202,D(49)/D(930)),
(2023,15866,10166,2956,33105,-439,D("0.306")),
(2024,17285,7589,3816,32863,361,D(182)/D(520)),
(2025,17786,7295,2942,32703,829,D(155)/D(723)),
(2026,19743,7402,5685,32105,576,D(32)/D(679)),
]
def calculate():
    rows=[]
    previous=None
    for year,equity,debt,cash,sales,op,tax in ROWS:
        excess=max(D(cash)-D(sales)/12,D(0))
        capital=D(equity)+D(debt)-excess
        if capital<=0: raise ValueError("nonpositive invested capital; ROE fallback must be separately audited")
        row={"fiscal_year":year,"invested_capital_million_jpy":float(capital),
             "excess_cash_million_jpy":float(excess)}
        if previous is not None:
            avg=(capital+previous)/2
            row["effective_tax_rate"]=float(tax)
            row["roic_percent"]=float(D(op)*(1-tax)/avg*100)
        rows.append(row)
        previous=capital
    return {"status":"REVIEW_ONLY_SOURCE_VERIFICATION_PENDING","scoring_eligible":False,
            "publish_to_index":False,"approved_rows":0,"rows":rows}
def main():
    result=calculate()
    assert len(result["rows"])==6 and result["approved_rows"]==0
    assert D(str(result["rows"][-1]["roic_percent"]))<D("2.3")
    dest=Path("artifacts/4406_roic_arithmetic_audit.json")
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,ensure_ascii=False,indent=2)+chr(10),encoding="utf-8")
    print("ROIC arithmetic checked for FY2022-FY2026; source approval BLOCKED")
if __name__=="__main__":
    main()
