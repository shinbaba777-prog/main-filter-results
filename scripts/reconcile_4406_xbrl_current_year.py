#!/usr/bin/env python3
"""Match current-year XBRL audit candidates to five-year PDF-reconciled values.
A numerical match is NOT approval of consolidated scope or XBRL concept.
"""
import csv
import json
from collections import Counter
from pathlib import Path

AUDIT=Path("data/edinet/extracted/financial_metric_audit.csv")
VERIFIED=Path("data/edinet/verified/4406_five_year_financials.csv")
OUT=Path("artifacts/4406_xbrl_current_year_matches.json")
METRIC_MAP={"sales":"sales_million_yen","ordinary_profit":"ordinary_profit_million_yen",
            "profit":"parent_net_income_million_yen","eps":"eps_yen","roe":"roe_reported_pct",
            "operating_profit":"operating_profit_million_yen","ocf":"ocf_million_yen",
            "icf":"icf_million_yen"}
CONTEXT={"CurrentYearDuration","CurrentYearInstant"}
PARENT_PROFIT_TAGS={"jpcrp_cor:ProfitLossAttributableToOwnersOfParentSummaryOfBusinessResults",
                    "jppfs_cor:ProfitLossAttributableToOwnersOfParent"}
def reconcile(audit,verified):
    if len(verified)!=5 or len(audit)!=680:
        raise ValueError("Expected 5 verified fiscal years and 680 audit candidates")
    ids={}
    for v in verified:
        doc=v.get("document_id","")
        if not doc or doc in ids:raise ValueError("Missing or duplicate document ID")
        ids[doc]=v
    rows=[]
    skipped_different_profit_concepts=0
    for a in audit:
        if a.get("validation_status") not in ("REVIEW_REQUIRED","STRUCTURALLY_PLAUSIBLE_REVIEW_REQUIRED"):
            raise ValueError("Unexpected approval state")
        metric=a.get("candidate_metric")
        if metric not in METRIC_MAP or a.get("context_id") not in CONTEXT:continue
        if metric=="profit" and a.get("element_id") not in PARENT_PROFIT_TAGS:
            skipped_different_profit_concepts+=1
            continue
        matched_docs=[doc for doc in ids if "_"+doc+"_" in a.get("source_zip","")]
        if len(matched_docs)!=1:raise ValueError("Cannot resolve source document uniquely")
        v=ids[matched_docs[0]]
        value=a.get("value","")
        try:
            actual=float(value)
            expected=float(v[METRIC_MAP[metric]])
        except (ValueError,TypeError,KeyError):
            continue
        # Unit labels may be absent or misleading; only compare known JPY and JPY/share.
        unit=a.get("unit_id","")
        if metric=="eps":
            if unit not in ("JPYPerShares","JPYPerShare"):continue
            normalized=actual
        elif metric=="roe":
            # ROE unit may be pure ratio or percent; do not infer normalization.
            continue
        else:
            if unit!="JPY":continue
            normalized=actual/1_000_000
        matches=abs(normalized-expected)<0.000001
        rows.append({"fiscal_year_end":v["fiscal_year_end"],"document_id":matched_docs[0],
            "candidate_metric":metric,"reference_metric":METRIC_MAP[metric],
            "source_zip":a["source_zip"],"source_csv":a["source_csv"],
            "row_number":a["row_number"],"element_id":a["element_id"],
            "context_id":a["context_id"],"consolidation_scope":a["consolidation_scope"],
            "unit_id":unit,"raw_value":value,"normalized_value":normalized,
            "official_pdf_reference_value":expected,"numeric_match":matches,
            "validation_flags":a.get("validation_flags",""),
            "status":"REVIEW_REQUIRED","scoring_eligible":False})
    counts=Counter(str(x["numeric_match"]) for x in rows)
    return {"security_code":"4406","status":"REVIEW_REQUIRED","scoring_eligible":False,
        "publish_to_index":False,"audit_candidates":len(audit),
        "current_year_comparable_candidates":len(rows),"numeric_matches":counts.get("True",0),
        "numeric_mismatches":counts.get("False",0),"different_profit_concepts_not_comparable":skipped_different_profit_concepts,"approved_rows":0,
        "note":"Profit comparisons use only explicit parent-attributable XBRL concepts; other profit concepts are not comparable. Numeric matches do not establish consolidated scope or approval. ROE skipped pending unit interpretation.",
        "comparisons":rows}
def main():
    with AUDIT.open(encoding="utf-8-sig",newline="") as f:a=list(csv.DictReader(f))
    with VERIFIED.open(encoding="utf-8-sig",newline="") as f:v=list(csv.DictReader(f))
    result=reconcile(a,v)
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"Current-year comparisons={result['current_year_comparable_candidates']}, matches={result['numeric_matches']}, mismatches={result['numeric_mismatches']}; different-profit-concepts={result['different_profit_concepts_not_comparable']}; approved=0")
if __name__=="__main__":main()
