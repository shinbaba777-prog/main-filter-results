#!/usr/bin/env python3
"""Inventory all numeric XBRL facts in core balance-sheet contexts; review only."""
import io
import json
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET
from scripts.extract_4406_roic_original_xbrl import INSTANCE, EXPLICIT, TYPED

CONTEXTS = ("CurrentYearInstant", "Prior1YearInstant")
MAX_FACTS = 25000

def inventory(payload, doc_id):
    if not zipfile.is_zipfile(io.BytesIO(payload)):
        raise ValueError("Original EDINET response is not ZIP")
    rows = []
    with zipfile.ZipFile(io.BytesIO(payload)) as z:
        for entry in z.infolist():
            if not (entry.filename.lower().endswith(".xbrl") and "publicdoc" in entry.filename.lower()):
                continue
            if entry.file_size > 20_000_000:
                raise ValueError("Oversized instance; review required")
            root = ET.fromstring(z.read(entry))
            if root.tag != INSTANCE+"xbrl":
                continue
            contexts = {}
            for c in root.iter(INSTANCE+"context"):
                if c.get("id") not in CONTEXTS:
                    continue
                dims = [n for n in c.iter() if n.tag in (EXPLICIT,TYPED)]
                contexts[c.get("id")] = {"dimensions": len(dims)}
            for node in root:
                ctx = node.get("contextRef")
                if ctx not in contexts or contexts[ctx]["dimensions"]:
                    continue
                if not node.get("unitRef"):
                    continue
                raw = (node.text or "").strip()
                if not raw or node.get("{http://www.w3.org/2001/XMLSchema-instance}nil") == "true":
                    continue
                try:
                    float(raw)
                except ValueError:
                    continue
                rows.append({"concept":node.tag.rsplit("}",1)[-1],
                             "namespace":node.tag.split("}")[0].lstrip("{") if "}" in node.tag else "",
                             "context_id":ctx,"unit_ref":node.get("unitRef"),
                             "value":raw,"source_instance":entry.filename})
                if len(rows)>MAX_FACTS:
                    raise ValueError("Too many facts; manual review required")
    return {"document_id":doc_id,"fact_count":len(rows),"facts":rows,
            "status":"FULL_CONTEXT_INVENTORY_REVIEW_REQUIRED",
            "scoring_eligible":False,"publish_to_index":False,"approved_rows":0}

def save(documents, path):
    result={"status":"REVIEW_REQUIRED","scoring_eligible":False,
            "publish_to_index":False,"approved_rows":0,"documents":documents}
    dest=Path(path)
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,ensure_ascii=False,indent=2)+chr(10),encoding="utf-8")
    return result
