#!/usr/bin/env python3
"""Create a conservative 5-year EDINET annual metrics review table; never auto-approve."""
import csv, json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"data/edinet/extracted"
SOURCE=OUT/"financial_metric_candidates.csv"
MANIFEST=ROOT/"data/edinet/download_manifest.json"
TABLE=OUT/"annual_financial_metrics_review.csv"
SUMMARY=OUT/"annual_financial_metrics_review_summary.json"
CONCEPTS={
 "sales":("sales",{"jppfs_cor:NetSales"},{"JPY"}),
 "operating_profit":("operating_profit",{"jppfs_cor:OperatingIncome"},{"JPY"}),
 "ordinary_profit":("ordinary_profit",{"jppfs_cor:OrdinaryIncome"},{"JPY"}),
 "net_income_parent":("profit",{"jppfs_cor:ProfitLossAttributableToOwnersOfParent"},{"JPY"}),
 "eps":("eps",{"jpcrp_cor:BasicEarningsLossPerShareSummaryOfBusinessResults"},{"JPYPerShares"}),
 "ocf":("ocf",{"jppfs_cor:NetCashProvidedByUsedInOperatingActivities"},{"JPY"}),
 "icf":("icf",{"jppfs_cor:NetCashProvidedByUsedInInvestmentActivities"},{"JPY"}),
 "roe":("roe",{"jpcrp_cor:RateOfReturnOnEquitySummaryOfBusinessResults"},{"pure"}),
}
METRICS=list(CONCEPTS)
FIELDS=["security_code","fiscal_period_end","fiscal_year",*METRICS,"fcf_ocf_plus_icf","status","review_notes","source_doc_id","source_zip"]
def main():
 if not SOURCE.exists() or not MANIFEST.exists(): raise SystemExit("Missing source CSV/manifest")
 manifest=json.loads(MANIFEST.read_text(encoding="utf-8"))
 if manifest.get("status")!="complete": raise SystemExit("Manifest not complete; refusing to build table")
 periods=[p for p in manifest.get("periods",[]) if p.get("status")=="downloaded" and p.get("file")]
 byfile={p["file"]:p for p in periods}
 candidates=defaultdict(list)
 with SOURCE.open(encoding="utf-8-sig",newline="") as f:
  for r in csv.DictReader(f):
   if r.get("source_zip") not in byfile: continue
   try: raw=json.loads(r.get("raw_row_json") or "{}")
   except json.JSONDecodeError: continue
   if raw.get("コンテキストID")!="CurrentYearDuration" or raw.get("連結・個別")!="連結" or raw.get("期間・時点")!="期間" and r.get("candidate_metric")!="roe": continue
   for outmetric,(candidate,concepts,units) in CONCEPTS.items():
    if r.get("candidate_metric")==candidate and raw.get("要素ID") in concepts and raw.get("ユニットID") in units:
     if outmetric=="roe" and raw.get("コンテキストID")!="CurrentYearDuration": continue
     candidates[(r["source_zip"],outmetric)].append(r)
 rows=[]; ambiguous=missing=0
 for filename,p in sorted(byfile.items(),key=lambda kv:kv[1].get("periodEnd","")):
  end=p.get("periodEnd",""); rec={"security_code":"44060","fiscal_period_end":end,"fiscal_year":end[:4],"source_doc_id":p.get("docID",""),"source_zip":filename,"status":"REVIEW_REQUIRED"}
  notes=[]
  for metric in METRICS:
   choices=candidates.get((filename,metric),[])
   if len(choices)==1:
    try: rec[metric]=format(float(choices[0]["value"]),".12g")
    except (ValueError,TypeError): rec[metric]="";notes.append(metric+":NON_NUMERIC");missing+=1
   elif len(choices)>1: rec[metric]="";notes.append(metric+":AMBIGUOUS");ambiguous+=1
   else: rec[metric]="";notes.append(metric+":NOT_FOUND_STRICT_RULES");missing+=1
  if rec.get("ocf") and rec.get("icf"): rec["fcf_ocf_plus_icf"]=format(float(rec["ocf"])+float(rec["icf"]),".12g")
  else: rec["fcf_ocf_plus_icf"]="";notes.append("FCF_NOT_CALCULATED")
  rec["review_notes"]=";".join(notes);rows.append(rec)
 with TABLE.open("w",encoding="utf-8-sig",newline="") as f:
  w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(rows)
 summary={"generated_at_utc":datetime.now(timezone.utc).isoformat(),"output":str(TABLE.relative_to(ROOT)),"filing_periods":len(rows),"metrics":METRICS,"ambiguous_metric_cells":ambiguous,"missing_or_invalid_metric_cells":missing,"approved_for_investment_scoring":0,"warning":"Review table only. Exact consolidated concepts, CurrentYearDuration contexts, and expected units are required; all selected values still require human verification of filing, fiscal dates, taxonomy, signs, and scale. ROE unit 'pure' is preserved in source scale and is not converted to percent."}
 SUMMARY.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(json.dumps(summary,ensure_ascii=False))
if __name__=="__main__": main()
