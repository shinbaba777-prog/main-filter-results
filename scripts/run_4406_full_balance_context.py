#!/usr/bin/env python3
"""Fetch full instant-context inventory of original EDINET filings; never publish."""
import os
import time
import urllib.parse
import urllib.request
from pathlib import Path
from scripts.inventory_4406_full_balance_context import inventory, save

DOCS=("S100OK43","S100R83V","S100TUAP","S100W17N","S100YGXD")
def main():
    key=os.environ.get("EDINET_API_KEY","").strip()
    if not key:
        raise SystemExit("BLOCKED: EDINET_API_KEY missing")
    records=[]
    for doc in DOCS:
        url="https://api.edinet-fsa.go.jp/api/v2/documents/"+doc+"?"+urllib.parse.urlencode({"type":"1","Subscription-Key":key})
        try:
            with urllib.request.urlopen(urllib.request.Request(url,headers={"Accept":"application/zip"}),timeout=35) as response:
                payload=response.read(80_000_001)
            if len(payload)>80_000_000:
                raise ValueError("ZIP too large")
            record=inventory(payload,doc)
        except Exception as exc:
            print(doc+": BLOCKED ("+type(exc).__name__+")")
            raise SystemExit(2) from None
        records.append(record)
        print(doc+": full context numeric facts="+str(record["fact_count"]))
        time.sleep(0.4)
    result=save(records,Path("artifacts/4406_full_balance_context_inventory.json"))
    assert not result["scoring_eligible"] and result["approved_rows"]==0
    print("REVIEW ONLY; no scoring or publishing")

if __name__=="__main__":
    main()
