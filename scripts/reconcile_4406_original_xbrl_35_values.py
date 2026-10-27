#!/usr/bin/env python3
"""Fail-closed exact numeric comparison: original XBRL facts vs 35 CSV audit rows."""
import csv
import json
from collections import Counter
from decimal import Decimal
from pathlib import Path

AUDIT=Path("data/edinet/extracted/financial_metric_audit.csv")
REVIEW=Path("artifacts/4406_consolidation_scope_review.json")
ORIGINAL=Path("artifacts/4406_original_xbrl_facts_linkbases.json")
OUTPUT=Path("artifacts/4406_original_xbrl_35_numeric_reconciliation.json")

def reconcile(audit,review,original):
    unresolved=review.get("unresolved_rows",[])
    if len(unresolved)!=35 or review.get("approved_rows")!=0:raise ValueError("Unexpected review inventory")
    docs={d["document_id"]:d for d in original.get("documents",[])}
    if len(docs)!=5:raise ValueError("Expected five original filings")
    audit_index={}
    for row in audit:
        doc_candidates=[d for d in docs if "_"+d+"_" in row.get("source_zip","")]
        if len(doc_candidates)!=1:continue
        key=(doc_candidates[0],row.get("source_csv"),str(row.get("row_number")),
             row.get("element_id"),row.get("context_id"))
        if key in audit_index:raise ValueError("Duplicate audit provenance")
        audit_index[key]=row
    findings=[]
    for row in unresolved:
        doc=row["document_id"]
        key=(doc,row["source_csv"],str(row["row_number"]),row["element_id"],row["context_id"])
        if key not in audit_index:raise ValueError("Missing audit row")
        audit_row=audit_index[key]
        local_name=row["element_id"].split(":")[-1]
        facts=[f for f in docs[doc]["facts"] if f["concept"]==local_name and
               f["context_id"]==row["context_id"]]
        if len(facts)!=1:raise ValueError("Ambiguous original XBRL fact")
        fact=facts[0]
        same_unit=fact["unit_ref"]==audit_row.get("unit_id")
        same_value=Decimal(fact["value"])==Decimal(audit_row["value"])
        if not same_unit or not same_value:raise ValueError("Original XBRL / CSV numeric mismatch")
        findings.append({"document_id":doc,"source_csv":row["source_csv"],
            "row_number":row["row_number"],"concept":local_name,
            "context_id":row["context_id"],"unit":fact["unit_ref"],
            "value":fact["value"],"numeric_match":True,"unit_match":True,
            "status":"NUMERIC_MATCH_REVIEW_REQUIRED","scoring_eligible":False})
    if len(findings)!=35 or len({(x["document_id"],x["concept"]) for x in findings})!=35:
        raise ValueError("Unexpected numeric evidence cardinality")
    return {"security_code":"4406","status":"REVIEW_REQUIRED","scoring_eligible":False,
        "publish_to_index":False,"approved_rows":0,"numeric_matches":len(findings),
        "numeric_mismatches":0,"unit_counts":dict(Counter(x["unit"] for x in findings)),
        "rows":findings}

def main():
    with AUDIT.open(encoding="utf-8-sig",newline="") as f:audit=list(csv.DictReader(f))
    review=json.loads(REVIEW.read_text(encoding="utf-8"))
    original=json.loads(ORIGINAL.read_text(encoding="utf-8"))
    result=reconcile(audit,review,original)
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    OUTPUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("Original XBRL exact numeric and unit matches: 35/35; approved=0")

if __name__=="__main__":main()
