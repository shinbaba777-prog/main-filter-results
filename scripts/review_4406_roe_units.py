#!/usr/bin/env python3
"""Check current-year ROE pure-unit ratio against issuer-PDF ROE, without approval."""
import csv
import json
from pathlib import Path

AUDIT=Path("data/edinet/extracted/financial_metric_audit.csv")
VERIFIED=Path("data/edinet/verified/4406_five_year_financials.csv")
OUT=Path("artifacts/4406_roe_unit_review.json")
TAG="jpcrp_cor:RateOfReturnOnEquitySummaryOfBusinessResults"

def review(audit, verified):
    if len(audit)!=680 or len(verified)!=5:raise ValueError("Unexpected source row counts")
    docs={}
    for v in verified:
        doc=v.get("document_id","")
        if not doc or doc in docs:raise ValueError("Invalid source document identifiers")
        docs[doc]=v
    results=[]
    for a in audit:
        if a.get("candidate_metric")!="roe" or a.get("context_id")!="CurrentYearDuration":continue
        if a.get("validation_status") not in ("REVIEW_REQUIRED","STRUCTURALLY_PLAUSIBLE_REVIEW_REQUIRED"):
            raise ValueError("Unexpected ROE approval status")
        matched=[d for d in docs if "_"+d+"_" in a.get("source_zip","")]
        if len(matched)!=1:raise ValueError("Ambiguous ROE source")
        v=docs[matched[0]]
        unit=a.get("unit_id","")
        if a.get("element_id")!=TAG or unit!="pure":
            results.append({"document_id":matched[0],"status":"NOT_COMPARABLE","reason":"Unexpected ROE concept or unit","scoring_eligible":False})
            continue
        ratio=float(a["value"])
        if not -2<=ratio<=2:raise ValueError("Implausible raw ROE ratio")
        pct=ratio*100
        expected=float(v["roe_reported_pct"])
        results.append({"fiscal_year_end":v["fiscal_year_end"],"document_id":matched[0],
            "source_zip":a["source_zip"],"source_csv":a["source_csv"],"row_number":a["row_number"],
            "element_id":a["element_id"],"context_id":a["context_id"],"unit_id":unit,
            "consolidation_scope":a["consolidation_scope"],"raw_ratio":ratio,
            "converted_pct":pct,"official_pdf_pct":expected,
            "numeric_match":abs(pct-expected)<0.000001,
            "status":"REVIEW_REQUIRED","scoring_eligible":False})
    if len(results)!=5 or len({r["document_id"] for r in results})!=5:
        raise ValueError("Expected exactly one current-year ROE candidate per filing")
    return {"security_code":"4406","status":"REVIEW_REQUIRED","scoring_eligible":False,
        "publish_to_index":False,"approved_rows":0,"candidates":len(results),
        "numeric_matches":sum(r.get("numeric_match") is True for r in results),
        "numeric_mismatches":sum(r.get("numeric_match") is False for r in results),
        "note":"pure x 100 matches are numerical checks only; consolidated scope still unapproved.",
        "rows":results}

def main():
    with AUDIT.open(encoding="utf-8-sig",newline="") as f:a=list(csv.DictReader(f))
    with VERIFIED.open(encoding="utf-8-sig",newline="") as f:v=list(csv.DictReader(f))
    result=review(a,v)
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"ROE unit review: {result['numeric_matches']}/{result['candidates']} matched, mismatches={result['numeric_mismatches']}, approved=0")

if __name__=="__main__":main()
