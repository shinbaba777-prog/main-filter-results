#!/usr/bin/env python3
"""Create review queue for 4406 XBRL candidate rows; NEVER approve scoring."""
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

SOURCE = Path("data/edinet/extracted/financial_metric_audit.csv")
SUMMARY = Path("data/edinet/extracted/financial_metric_audit_summary.json")
OUT = Path("artifacts/4406_xbrl_review_queue.json")
KEY_FIELDS = ("source_zip","source_csv","row_number","candidate_metric","element_id","context_id","consolidation_scope","unit_id")

def triage(rows, summary):
    if len(rows) != summary.get("candidate_rows_audited"):
        raise ValueError("Audit row count does not match summary")
    if "No row is approved for investment scoring" not in summary.get("important_warning",""):
        raise ValueError("Approval state unexpectedly changed")
    if any(r.get("validation_status") not in ("REVIEW_REQUIRED","STRUCTURALLY_PLAUSIBLE_REVIEW_REQUIRED") for r in rows):
        raise ValueError("Unexpected approval status; manual intervention required")
    if any(not all(r.get(k) for k in KEY_FIELDS) for r in rows):
        raise ValueError("Incomplete XBRL provenance")
    if len({(r["source_zip"],r["source_csv"],r["row_number"]) for r in rows}) != len(rows):
        raise ValueError("Duplicate XBRL source row identifiers")
    by_metric=defaultdict(lambda:{"count":0,"review_required":0,"structurally_plausible":0,"scope_unclear":0,"unit_unclear":0})
    for r in rows:
        g=by_metric[r["candidate_metric"]];g["count"]+=1
        if r["validation_status"]=="REVIEW_REQUIRED":g["review_required"]+=1
        else:g["structurally_plausible"]+=1
        flags=r.get("validation_flags","")
        if "CONSOLIDATION_SCOPE_UNCLEAR" in flags:g["scope_unclear"]+=1
        if "UNIT_UNCLEAR" in flags:g["unit_unclear"]+=1
    return {"security_code":"4406","status":"REVIEW_REQUIRED","scoring_eligible":False,"publish_to_index":False,
            "source_file":str(SOURCE),"candidate_rows":len(rows),"approved_rows":0,
            "source_filing_count":len({r["source_zip"] for r in rows}),
            "validation_status_counts":dict(sorted(Counter(r["validation_status"] for r in rows).items())),
            "by_candidate_metric":dict(sorted(by_metric.items())),
            "next_review":"Verify consolidated scope, XBRL concept, unit, fiscal context, amendment and official filing before any row approval."}

def main():
    with SOURCE.open(encoding="utf-8-sig",newline="") as f:rows=list(csv.DictReader(f))
    summary=json.loads(SUMMARY.read_text(encoding="utf-8"))
    result=triage(rows,summary)
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"XBRL review queue: {result['candidate_rows']} candidates, {result['approved_rows']} approved, scoring_eligible=false")

if __name__=="__main__":main()
