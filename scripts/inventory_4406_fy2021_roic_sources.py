#!/usr/bin/env python3
"""Inventory existing EDINET data for FY2021 and ROIC inputs; never estimate values."""
import csv
import json
from pathlib import Path

ROOT=Path("data/edinet")
OUTPUT=Path("artifacts/4406_fy2021_roic_source_inventory.json")
KEYS=("roic","investedcapital","invested_capital","nopat","wacc",
      "interestbearingdebt","interest_bearing_debt","totalassets",
      "totalequity","cashandcashequivalents","cash_and_cash_equivalents",
      "operatingprofit","taxexpense","corporatetax","2021-03-31")

def inventory(root=ROOT):
    files=[]
    hits=[]
    for path in sorted(root.rglob("*")):
        if not path.is_file():continue
        relative=str(path.relative_to(root))
        if len(files)<20000:files.append(relative)
        lower=relative.lower()
        if any(k in lower for k in KEYS):
            hits.append({"path":relative,"reason":"filename keyword"})
        if path.suffix.lower() not in (".csv",".json",".jsonl",".md",".txt"):continue
        if path.stat().st_size>3_000_000:continue
        try:
            data=path.read_text(encoding="utf-8-sig")
        except (UnicodeError,OSError):continue
        matching=[k for k in KEYS if k in data.lower()]
        if matching:
            hits.append({"path":relative,"reason":"content keyword",
                         "keywords":matching[:15]})
    fy2021=[h for h in hits if "2021-03-31" in h.get("keywords",[]) or
            "2021" in h["path"]]
    roic=[h for h in hits if any(k in h.get("keywords",[]) for k in KEYS[:-1])]
    return {"security_code":"4406","status":"REVIEW_REQUIRED","scoring_eligible":False,
        "publish_to_index":False,"approved_rows":0,
        "file_count":len(files),"files_truncated":len(files)>=20000,
        "fy2021_candidates":fy2021,"roic_input_candidates":roic,
        "hits":hits[:1000],
        "note":"Keyword candidates are not validated financial values or fiscal-year sources."}

def main():
    result=inventory()
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    OUTPUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("EDINET source inventory:",result["file_count"],"files;",
          len(result["fy2021_candidates"]),"FY2021 candidates;",
          len(result["roic_input_candidates"]),"ROIC input candidates; approved=0")

if __name__=="__main__":main()
