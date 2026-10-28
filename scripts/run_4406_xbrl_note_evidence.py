#!/usr/bin/env python3
"""Collect review-only note evidence for five original 4406 EDINET filings."""
import os
import time
import urllib.parse
import urllib.request
from pathlib import Path
from scripts.inspect_4406_xbrl_note_evidence import inspect,save

DOCS=("S100OK43","S100R83V","S100TUAP","S100W17N","S100YGXD")
def main():
    key=os.environ.get("EDINET_API_KEY","").strip()
    if not key: raise SystemExit("BLOCKED: EDINET_API_KEY missing")
    records=[]
    for doc in DOCS:
        url="https://api.edinet-fsa.go.jp/api/v2/documents/"+doc+"?"+urllib.parse.urlencode({"type":"1","Subscription-Key":key})
        try:
            with urllib.request.urlopen(urllib.request.Request(url,headers={"Accept":"application/zip"}),timeout=35) as response:
                payload=response.read(80_000_001)
            if len(payload)>80_000_000: raise ValueError("ZIP too large")
            row=inspect(payload,doc)
        except Exception as exc:
            print(doc+": BLOCKED ("+type(exc).__name__+")")
            raise SystemExit(2) from None
        records.append(row)
        print(doc+": evidence matches="+str(row["match_count"]))
        time.sleep(0.4)
    result=save(records,Path("artifacts/4406_original_xbrl_note_evidence.json"))
    assert not result["scoring_eligible"] and result["approved_rows"]==0
    print("REVIEW ONLY: note evidence, not verified ROIC")

if __name__=="__main__":
    main()
