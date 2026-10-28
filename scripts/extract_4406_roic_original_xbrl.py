#!/usr/bin/env python3
"""Review-only ROIC candidate extraction from original EDINET ZIP; never approves facts."""
import io
import json
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

INSTANCE = "{http://www.xbrl.org/2003/instance}"
EXPLICIT = "{http://xbrl.org/2006/xbrldi}explicitMember"
TYPED = "{http://xbrl.org/2006/xbrldi}typedMember"
# Discovery terms are intentionally broad. Never equate a keyword hit with an approved mapping.
TERMS = ("OperatingIncome", "OperatingProfit", "IncomeTaxes", "IncomeBeforeIncomeTaxes",
         "ProfitBeforeTax", "TotalEquity", "NetAssets", "NonControllingInterests",
         "MinorityInterests", "SubscriptionRights", "ShortTermLoans",
         "LongTermLoans", "BondsPayable", "LeaseObligations", "LeaseLiabilities",
         "CashAndDeposits", "CashAndCashEquivalents", "InterestBearingDebt",
         "ShareholdersEquity", "EquityAttributableToOwnersOfParent")

def extract_candidates(payload, doc_id):
    if not zipfile.is_zipfile(io.BytesIO(payload)):
        raise ValueError("EDINET original response is not ZIP")
    rows = []
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        for entry in archive.infolist():
            name = entry.filename
            if not (name.lower().endswith(".xbrl") and "publicdoc" in name.lower()):
                continue
            if entry.file_size > 20_000_000:
                continue
            root = ET.fromstring(archive.read(entry))
            if root.tag != INSTANCE + "xbrl":
                continue
            contexts = {}
            for context in root.iter(INSTANCE + "context"):
                period = context.find(INSTANCE + "period")
                details = {}
                if period is not None:
                    for child in period:
                        details[child.tag.rsplit("}", 1)[-1]] = (child.text or "").strip()
                dimensions = [{"dimension": node.get("dimension", ""),
                               "member": "".join(node.itertext()).strip()}
                              for node in context.iter() if node.tag in (EXPLICIT, TYPED)]
                contexts[context.get("id", "")] = {"period": details, "dimensions": dimensions}
            for node in root:
                concept = node.tag.rsplit("}", 1)[-1]
                if not any(term.lower() in concept.lower() for term in TERMS):
                    continue
                context_ref = node.get("contextRef")
                if not context_ref or context_ref not in contexts:
                    continue
                raw = (node.text or "").strip()
                if not raw or node.get("{http://www.w3.org/2001/XMLSchema-instance}nil") == "true":
                    continue
                rows.append({"document_id": doc_id, "concept": concept,
                             "namespace": node.tag.split("}")[0].lstrip("{") if "}" in node.tag else "",
                             "context_id": context_ref, "context": contexts[context_ref],
                             "unit_ref": node.get("unitRef"), "decimals": node.get("decimals"),
                             "value": raw, "source_instance": name,
                             "mapping_status": "CANDIDATE_REVIEW_REQUIRED"})
    return {"document_id": doc_id, "status": "REVIEW_REQUIRED",
            "scoring_eligible": False, "publish_to_index": False,
            "approved_rows": 0, "candidate_count": len(rows), "candidates": rows}

def save_review(documents, path):
    output = {"status": "REVIEW_REQUIRED", "scoring_eligible": False,
              "publish_to_index": False, "approved_rows": 0, "documents": documents}
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return output
