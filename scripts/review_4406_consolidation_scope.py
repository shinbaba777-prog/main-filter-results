#!/usr/bin/env python3
"""Review-only inventory of unresolved consolidated-scope flags for current-year matches."""
import json
from collections import Counter
from pathlib import Path

MATCHES=Path("artifacts/4406_xbrl_current_year_matches.json")
ROE=Path("artifacts/4406_roe_unit_review.json")
OUT=Path("artifacts/4406_consolidation_scope_review.json")

def build(matches,roe):
    if matches.get("numeric_matches")!=65 or matches.get("numeric_mismatches")!=0 or len(matches.get("comparisons",[]))!=65:
        raise ValueError("Unexpected XBRL numeric reconciliation")
    if roe.get("numeric_matches")!=5 or len(roe.get("rows",[]))!=5:
        raise ValueError("Unexpected ROE reconciliation")
    combined=matches["comparisons"]+roe["rows"]
    if any(x.get("scoring_eligible") is not False for x in combined):
        raise ValueError("Unexpected scoring approval")
    scope_counts=Counter(x.get("consolidation_scope","") for x in combined)
    unknown=[x for x in combined if x.get("consolidation_scope") not in ("連結","Consolidated")]
    return {"security_code":"4406","status":"REVIEW_REQUIRED","scoring_eligible":False,
        "publish_to_index":False,"reviewed_numeric_candidates":len(combined),
        "scope_counts":dict(scope_counts),"unresolved_scope_count":len(unknown),
        "consolidated_scope_confirmed":len(unknown)==0,
        "approved_rows":0,
        "next_step":"Inspect source XBRL context definitions and consolidated/standalone financial statement tables; do not infer scope from numeric agreement.",
        "unresolved_rows":[{"document_id":x.get("document_id"),"source_csv":x.get("source_csv"),
            "row_number":x.get("row_number"),"element_id":x.get("element_id"),
            "context_id":x.get("context_id"),"consolidation_scope":x.get("consolidation_scope")} for x in unknown]}
def main():
    result=build(json.loads(MATCHES.read_text()),json.loads(ROE.read_text()))
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"Consolidation scope: {result['unresolved_scope_count']}/{result['reviewed_numeric_candidates']} unresolved; approved=0")
if __name__=="__main__":main()
