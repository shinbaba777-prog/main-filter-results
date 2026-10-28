#!/usr/bin/env python3
"""Review FY2021 comparative sales in the FY2022 EDINET original ZIP."""
import io
import json
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

XBRL = "{http://www.xbrl.org/2003/instance}"
DIMENSIONS = ("explicitMember", "typedMember")
CONTEXT_IDS = {"Prior1YearDuration", "Prior1YearInstant"}
KEYWORDS = ("sales", "revenue", "lease", "loanspayable", "netassets", "cashanddeposits", "noncontrolling")

def extract(payload):
    if not zipfile.is_zipfile(io.BytesIO(payload)):
        raise ValueError("Expected original filing ZIP")
    facts = []
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        for entry in archive.infolist():
            if not entry.filename.lower().endswith(".xbrl") or "publicdoc" not in entry.filename.lower():
                continue
            if entry.file_size > 20000000:
                raise ValueError("Oversized XBRL")
            root = ET.fromstring(archive.read(entry))
            if root.tag != XBRL + "xbrl":
                continue
            contexts = {}
            for node in root.iter(XBRL + "context"):
                cid = node.get("id")
                if cid not in CONTEXT_IDS:
                    continue
                if any(child.tag.rsplit("}", 1)[-1] in DIMENSIONS for child in node.iter()):
                    continue
                period = [(x.tag.rsplit("}", 1)[-1], x.text) for x in node.iter()
                          if x.tag.rsplit("}", 1)[-1] in ("instant", "startDate", "endDate")]
                contexts[cid] = period
            for node in root:
                cid = node.get("contextRef")
                if cid not in contexts or not node.get("unitRef"):
                    continue
                concept = node.tag.rsplit("}", 1)[-1]
                if not any(k in concept.lower() for k in KEYWORDS):
                    continue
                facts.append({"concept": concept, "context_id": cid,
                              "period": contexts[cid], "unit": node.get("unitRef"),
                              "value": (node.text or "").strip(), "instance": entry.filename})
    return {"document_id": "S100OK43", "facts": facts,
            "status": "REVIEW_REQUIRED", "scoring_eligible": False,
            "publish_to_index": False, "approved_rows": 0}

def save(data, path):
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data, ensure_ascii=False, indent=2) + chr(10), encoding="utf-8")
