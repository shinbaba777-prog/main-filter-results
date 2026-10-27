#!/usr/bin/env python3
"""Extract fact-level 4406 scope evidence from original EDINET XBRL ZIPs (no approval)."""
import io
import json
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

CONCEPTS=(
    "NetSalesSummaryOfBusinessResults",
    "OrdinaryIncomeLossSummaryOfBusinessResults",
    "ProfitLossAttributableToOwnersOfParentSummaryOfBusinessResults",
    "BasicEarningsLossPerShareSummaryOfBusinessResults",
    "NetCashProvidedByUsedInOperatingActivitiesSummaryOfBusinessResults",
    "NetCashProvidedByUsedInInvestingActivitiesSummaryOfBusinessResults",
    "RateOfReturnOnEquitySummaryOfBusinessResults",
)
INSTANCE="{http://www.xbrl.org/2003/instance}"
EXPLICIT="{http://xbrl.org/2006/xbrldi}explicitMember"
TYPED="{http://xbrl.org/2006/xbrldi}typedMember"

def inspect_original_zip(payload,doc_id):
    if not zipfile.is_zipfile(io.BytesIO(payload)):
        raise ValueError("Original filing response is not ZIP")
    facts=[]
    linkbases=[]
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        for entry in archive.infolist():
            name=entry.filename
            if entry.file_size>15_000_000: continue
            if name.lower().endswith((".xml",".xsd")) and "publicdoc" in name.lower():
                if any(part in name.lower() for part in ("_pre","_def","presentation","definition")):
                    linkbases.append(name)
            if not (name.lower().endswith(".xbrl") and "publicdoc" in name.lower()):
                continue
            root=ET.fromstring(archive.read(entry))
            if root.tag!=INSTANCE+"xbrl":continue
            contexts={x.get("id"):x for x in root.iter(INSTANCE+"context")}
            for el in root.iter():
                if el.tag.rsplit("}",1)[-1] not in CONCEPTS: continue
                context_id=el.get("contextRef","")
                ctx=contexts.get(context_id)
                dims=[]
                if ctx is not None:
                    dims=[{"dimension":x.get("dimension",""),"member":"".join(x.itertext()).strip()}
                          for x in ctx.iter() if x.tag in (EXPLICIT,TYPED)]
                facts.append({"concept":el.tag.rsplit("}",1)[-1],"context_id":context_id,
                    "unit_ref":el.get("unitRef",""),"value":(el.text or "").strip(),
                    "source_instance":name,"context_found":ctx is not None,
                    "dimensions":dims,"scope_status":"REVIEW_REQUIRED"})
    if not facts:raise ValueError("No relevant original XBRL facts")
    return {"document_id":doc_id,"facts":facts,"linkbase_candidates":linkbases,
        "current_year_facts":sum(x["context_id"]=="CurrentYearDuration" for x in facts),
        "status":"REVIEW_REQUIRED","scoring_eligible":False,"approved_rows":0}

def save_inventory(documents,path):
    result={"status":"REVIEW_REQUIRED","scoring_eligible":False,
            "publish_to_index":False,"approved_rows":0,
            "documents":documents}
    output=Path(path)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return result
