#!/usr/bin/env python3
"""EDINET original XBRL context inventory. Never approves scoring."""
import io
import json
import os
import urllib.request
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

DOCS=("S100OK43","S100R83V","S100TUAP","S100W17N","S100YGXD")
OUT=Path("artifacts/4406_original_xbrl_context_inventory.json")
NS="{http://www.xbrl.org/2003/instance}context"

def inspect_zip(raw,docid):
    if not zipfile.is_zipfile(io.BytesIO(raw)):
        raise ValueError(f"{docid}: not a ZIP")
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        instances=[n for n in archive.namelist() if n.lower().endswith(".xbrl") and "publicdoc" in n.lower()]
        if not instances: raise ValueError(f"{docid}: missing XBRL instance")
        contexts=[]
        for name in instances:
            root=ET.fromstring(archive.read(name))
            for node in root.iter(NS):
                dims=[{"dimension":e.attrib.get("dimension",""),"member":(e.text or "").strip()}
                      for e in node.iter() if e.tag.endswith(("explicitMember","typedMember"))]
                contexts.append({"id":node.attrib.get("id",""),"dimensions":dims})
        if not contexts: raise ValueError(f"{docid}: no contexts")
        return {"doc_id":docid,"instance_count":len(instances),"context_count":len(contexts),
                "contexts":contexts,"scope_status":"REVIEW_REQUIRED","scoring_eligible":False}

def main():
    key=os.environ.get("EDINET_API_KEY")
    if not key: raise SystemExit("EDINET_API_KEY missing")
    result={"status":"REVIEW_REQUIRED","scoring_eligible":False,"publish_to_index":False,
            "approved_rows":0,"documents":[]}
    for docid in DOCS:
        url=f"https://api.edinet-fsa.go.jp/api/v2/documents/{docid}?type=1"
        request=urllib.request.Request(url,headers={"Ocp-Apim-Subscription-Key":key})
        with urllib.request.urlopen(request,timeout=20) as response:
            raw=response.read(25_000_001)
        if len(raw)>25_000_000: raise ValueError("Response exceeds size limit")
        item=inspect_zip(raw,docid)
        result["documents"].append(item)
        print(f"{docid}: {item['context_count']} contexts")
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
if __name__=="__main__":main()
