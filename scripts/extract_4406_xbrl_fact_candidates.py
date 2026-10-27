#!/usr/bin/env python3
"""4406 EDINET original XBRL fact evidence. Review-only; never approves scoring."""
import csv
import io
import json
import os
import sys
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

DOCS = ["S100OK43", "S100R83V", "S100TUAP", "S100W17N", "S100YGXD"]
CONCEPTS = {
    "NetSales", "Revenue", "OperatingRevenue", "OperatingIncome",
    "OrdinaryIncome", "ProfitLoss", "ProfitLossAttributableToOwnersOfParent",
    "NetIncome", "EarningsPerShare", "BasicEarningsLossPerShare",
    "NetCashProvidedByUsedInOperatingActivities",
    "NetCashProvidedByUsedInInvestingActivities",
    "CashFlowsFromUsedInOperatingActivities",
    "CashFlowsFromUsedInInvestingActivities",
    "ReturnOnEquity", "EquityAttributableToOwnersOfParent",
}
NS = "{http://www.xbrl.org/2003/instance}"
FIELDS = ["doc_id", "instance", "concept", "namespace", "context_id",
          "start_date", "end_date", "instant", "dimensions", "unit_ref",
          "decimals", "value", "review_status"]

def download(doc_id, key):
    url = ("https://api.edinet-fsa.go.jp/api/v2/documents/" + doc_id + "?"
           + urllib.parse.urlencode({"type": "1", "Subscription-Key": key}))
    try:
        with urllib.request.urlopen(urllib.request.Request(
                url, headers={"Accept": "application/zip"}), timeout=35) as response:
            payload = response.read(80 * 1024 * 1024 + 1)
    except Exception:
        raise RuntimeError("download_failed") from None
    if len(payload) > 80 * 1024 * 1024 or not zipfile.is_zipfile(io.BytesIO(payload)):
        raise RuntimeError("invalid_zip")
    return payload

def extract(payload, doc_id):
    rows = []
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        for entry in archive.infolist():
            if not entry.filename.lower().endswith((".xbrl", ".xml")):
                continue
            if entry.file_size > 15 * 1024 * 1024:
                continue
            try:
                root = ET.fromstring(archive.read(entry))
            except ET.ParseError:
                continue
            if root.tag != NS + "xbrl":
                continue
            contexts = {}
            for ctx in root.findall(NS + "context"):
                period = ctx.find(NS + "period")
                if period is None:
                    continue
                contexts[ctx.get("id")] = (
                    period.findtext(NS + "startDate") or "",
                    period.findtext(NS + "endDate") or "",
                    period.findtext(NS + "instant") or "",
                    ";".join((node.get("dimension") or "") + "=" + "".join(node.itertext()).strip()
                             for node in ctx.iter() if node.tag.endswith(("explicitMember", "typedMember")))
                )
            for fact in root:
                if "}" not in fact.tag:
                    continue
                namespace, concept = fact.tag[1:].split("}", 1)
                if concept not in CONCEPTS or not fact.get("contextRef"):
                    continue
                ctx_id = fact.get("contextRef")
                if ctx_id not in contexts:
                    continue
                value = (fact.text or "").strip()
                if not value:
                    continue
                start, end, instant, dims = contexts[ctx_id]
                rows.append([doc_id, entry.filename, concept, namespace, ctx_id,
                             start, end, instant, dims, fact.get("unitRef") or "",
                             fact.get("decimals") or "", value, "REVIEW_REQUIRED"])
    return rows

def main():
    key = os.environ.get("EDINET_API_KEY", "").strip()
    if not key:
        print("BLOCKED: missing EDINET_API_KEY")
        return 2
    out = Path(os.environ.get("OUTPUT_DIR", "artifacts/4406-facts"))
    out.mkdir(parents=True, exist_ok=True)
    report = {"scoring_ready": False, "filings": []}
    all_rows = []
    for doc_id in DOCS:
        try:
            rows = extract(download(doc_id, key), doc_id)
            status = "FACT_CANDIDATES_FOUND" if rows else "NO_MATCHING_FACTS"
            all_rows.extend(rows)
            report["filings"].append({"doc_id": doc_id, "status": status, "rows": len(rows)})
        except Exception as exc:
            report["filings"].append({"doc_id": doc_id, "status": "BLOCKED",
                                      "error_type": type(exc).__name__})
        print(json.dumps(report["filings"][-1]), flush=True)
    with (out / "fact_candidates.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(FIELDS)
        writer.writerows(all_rows)
    (out / "fetch_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return 0 if all(x["status"] == "FACT_CANDIDATES_FOUND" for x in report["filings"]) else 2

if __name__ == "__main__":
    sys.exit(main())
