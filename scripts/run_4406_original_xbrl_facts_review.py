#!/usr/bin/env python3
"""Read-only original EDINET XBRL fact review, never publishes or approves."""
import json
import os
import time
import urllib.parse
import urllib.request
from pathlib import Path
from scripts.inspect_4406_original_xbrl_facts import inspect_original_zip,save_inventory

DOCS=("S100OK43","S100R83V","S100TUAP","S100W17N","S100YGXD")

def main():
    key=os.environ.get("EDINET_API_KEY","").strip()
    if not key:raise SystemExit("BLOCKED: EDINET_API_KEY missing")
    items=[]
    for doc in DOCS:
        url="https://api.edinet-fsa.go.jp/api/v2/documents/"+doc+"?"+urllib.parse.urlencode(
            {"type":"1","Subscription-Key":key})
        try:
            with urllib.request.urlopen(urllib.request.Request(url,headers={"Accept":"application/zip"}),timeout=35) as response:
                data=response.read(80_000_001)
            if len(data)>80_000_000:raise ValueError("ZIP exceeds 80 MB")
            item=inspect_original_zip(data,doc)
        except Exception as exc:
            # Never print URL or exception message; either can include the secret.
            print(doc+": BLOCKED ("+type(exc).__name__+")")
            raise SystemExit(2) from None
        items.append(item)
        print(doc+": facts="+str(len(item["facts"]))+
              ", current-year="+str(item["current_year_facts"])+
              ", linkbases="+str(len(item["linkbase_candidates"])))
        time.sleep(0.3)
    result=save_inventory(items,Path("artifacts/4406_original_xbrl_facts_linkbases.json"))
    if len(items)!=5 or any(x["current_year_facts"]<7 for x in items):
        raise SystemExit("BLOCKED: missing original XBRL fact evidence")
    assert result["approved_rows"]==0 and not result["publish_to_index"]
    print("PASS: original XBRL facts inventoried, approvals=0")

if __name__=="__main__":main()
