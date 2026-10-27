#!/usr/bin/env python3
"""Audit five-year 4406 scoring-input readiness without authorizing a score."""
import csv
import json
from datetime import date
from decimal import Decimal
from pathlib import Path

SOURCE=Path("data/edinet/verified/4406_five_year_financials.csv")
OUTPUT=Path("artifacts/4406_scoring_input_readiness.json")
METRICS=("sales_million_yen","operating_profit_million_yen",
         "ordinary_profit_million_yen","parent_net_income_million_yen",
         "eps_yen","ocf_million_yen","icf_million_yen",
         "fcf_ocf_plus_icf_million_yen","roe_reported_pct","roic_pct")

def audit(rows):
    if len(rows)!=5:raise ValueError("Expected exactly five fiscal years")
    expected_years=list(range(2022,2027))
    years=[date.fromisoformat(r["fiscal_year_end"]).year for r in rows]
    if years!=expected_years or any(not r["fiscal_year_end"].endswith("-03-31") for r in rows):
        raise ValueError("Fiscal periods must be five consecutive March year-ends")
    if len({r["document_id"] for r in rows})!=5:raise ValueError("Duplicate filing")
    if any(r["security_code"]!="4406" or r["consolidation_scope"]!="連結" for r in rows):
        raise ValueError("Unexpected issuer or scope")
    missing={}
    for metric in METRICS:
        missing[metric]=[r["fiscal_year_end"] for r in rows if not r.get(metric,"").strip()]
    for r in rows:
        if Decimal(r["ocf_million_yen"])+Decimal(r["icf_million_yen"])!=Decimal(r["fcf_ocf_plus_icf_million_yen"]):
            raise ValueError("FCF arithmetic mismatch")
    year0=rows[0];year4=rows[-1]
    comparisons={}
    for metric in METRICS:
        if metric=="roic_pct":continue
        first=Decimal(year0[metric]);last=Decimal(year4[metric])
        comparisons[metric]={"first":str(first),"last":str(last),
            "delta":str(last-first),
            "growth_rate_applicable":first>0 and last>0}
    blockers=["ROIC missing in all five years",
              "Five rows provide FY2022-FY2026; six annual endpoints needed for FY2021-FY2026 five-year CAGR",
              "Rubric-level ROIC/WACC, valuation, shorts, technicals and Stage 2 source evidence not yet mapped",
              "Source fact review approval is independent from scoring authorization"]
    return {"security_code":"4406","status":"REVIEW_REQUIRED",
        "scoring_eligible":False,"publish_to_index":False,"approved_rows":0,
        "periods":years,"metric_missing_years":missing,
        "fcf_arithmetic_matches":5,"endpoints":comparisons,
        "blocking_issues":blockers,"formal_score":None}

def main():
    with SOURCE.open(encoding="utf-8-sig",newline="") as f:rows=list(csv.DictReader(f))
    result=audit(rows)
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    OUTPUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("4406 scoring readiness: 5 fiscal years; FCF 5/5; ROIC missing 5/5; score BLOCKED")

if __name__=="__main__":main()
