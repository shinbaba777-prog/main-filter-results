#!/usr/bin/env python3
"""Prioritize 4406 XBRL audit candidates for human review; never score."""
import csv
import json
from collections import defaultdict
from pathlib import Path

SOURCE=Path("data/edinet/extracted/financial_metric_audit.csv")
OUT=Path("artifacts/4406_xbrl_priority_review.json")
FOCUS={"sales","operating_profit","ordinary_profit","parent_net_income","eps","ocf","icf","fcf","roe","roic"}
FLAG_WEIGHT={"CONSOLIDATION_SCOPE_UNCLEAR":30,"UNIT_UNCLEAR":20}

def prioritize(rows):
    groups=defaultdict(lambda:{"candidate_rows":0,"scope_unclear":0,"unit_unclear":0,"current_year_rows":0,"examples":[]})
    for row in rows:
        if row.get("validation_status") not in ("REVIEW_REQUIRED","STRUCTURALLY_PLAUSIBLE_REVIEW_REQUIRED"):
            raise ValueError("Unexpected validation approval")
        metric=row.get("candidate_metric","")
        filing=row.get("source_zip","")
        if not metric or not filing or not row.get("element_id") or not row.get("context_id"):
            raise ValueError("Missing candidate provenance")
        key=(filing,metric)
        item=groups[key];item["candidate_rows"]+=1
        flags=row.get("validation_flags","")
        for flag,field in (("CONSOLIDATION_SCOPE_UNCLEAR","scope_unclear"),("UNIT_UNCLEAR","unit_unclear")):
            if flag in flags:item[field]+=1
        if row["context_id"].startswith("CurrentYear"):
            item["current_year_rows"]+=1
        if len(item["examples"])<3:
            item["examples"].append({"source_csv":row.get("source_csv"),"row_number":row.get("row_number"),"element_id":row["element_id"],"context_id":row["context_id"],"unit_id":row.get("unit_id"),"consolidation_scope":row.get("consolidation_scope")})
    out=[]
    for (filing,metric),d in groups.items():
        weight=100 if metric in FOCUS else 0
        priority=weight+min(d["scope_unclear"],10)*3+min(d["unit_unclear"],10)*2+(10 if d["current_year_rows"] else 0)
        out.append({"source_zip":filing,"candidate_metric":metric,"review_priority":priority,**d,"status":"REVIEW_REQUIRED"})
    out.sort(key=lambda x:(-x["review_priority"],x["source_zip"],x["candidate_metric"]))
    return {"security_code":"4406","status":"REVIEW_REQUIRED","scoring_eligible":False,"publish_to_index":False,
            "candidate_rows":len(rows),"review_groups":len(out),"approved_rows":0,
            "priority_method":"Heuristic review order only; not an evidence-quality or scoring measure.",
            "groups":out}

def main():
    with SOURCE.open(encoding="utf-8-sig",newline="") as f:rows=list(csv.DictReader(f))
    if len(rows)!=680:raise SystemExit("Expected exactly 680 source candidate rows")
    result=prioritize(rows)
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"Prioritized {result['candidate_rows']} XBRL rows into {result['review_groups']} review groups; approved=0")

if __name__=="__main__":main()
