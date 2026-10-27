#!/usr/bin/env python3
"""Read-only original-XBRL context evidence gate.

An EDINET XBRL_TO_CSV row's context ID is NOT a substitute for the actual
xbrli:context definition. This gate requires explicitly supplied original
XBRL context evidence from original instance XML, and never approves scoring automatically.
"""
import argparse
import csv
import json
import xml.etree.ElementTree as ET
from pathlib import Path

XBRLI = "{http://www.xbrl.org/2003/instance}"
XBRLDI = "{http://xbrl.org/2006/xbrldi}"

def context_details(xml_bytes):
    root = ET.fromstring(xml_bytes)
    result = {}
    for context in root.iter(XBRLI + "context"):
        context_id = context.get("id")
        if not context_id:
            continue
        period = context.find(XBRLI + "period")
        if period is None:
            continue
        start = period.findtext(XBRLI + "startDate")
        end = period.findtext(XBRLI + "endDate")
        instant = period.findtext(XBRLI + "instant")
        dims = []
        for child in context.iter():
            if child.tag in (XBRLDI + "explicitMember", XBRLDI + "typedMember"):
                dims.append({"dimension": child.get("dimension", ""),
                             "member": "".join(child.itertext()).strip()})
        result[context_id] = {"start_date": start, "end_date": end,
                              "instant": instant, "dimensions": dims}
    return result

def inspect(rows, instances):
    missing = []
    checked = 0
    for row in rows:
        source = row.get("source_zip", "")
        context_id = row.get("context_id", "")
        contexts = instances.get(source)
        if contexts is None:
            missing.append({"source_zip": source, "reason": "ORIGINAL_XBRL_NOT_PROVIDED"})
        elif context_id not in contexts:
            missing.append({"source_zip": source, "context_id": context_id,
                            "reason": "CONTEXT_NOT_IN_ORIGINAL_XBRL"})
        else:
            checked += 1
    return {"status": "REVIEW_REQUIRED", "scoring_ready": False,
            "rows": len(rows), "contexts_found": checked,
            "missing_evidence_rows": len(missing),
            "missing_evidence_examples": missing[:10],
            "note": "Matching original XBRL contexts is necessary but not sufficient for approving financial facts."}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--evidence-dir", type=Path,
                        help="Directory containing <docID>.contexts.json from original XBRL fetch")
    args = parser.parse_args()
    try:
        path = args.root / "data/edinet/extracted/financial_metric_audit.csv"
        with path.open(encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
        instances = {}
        manifest_path = args.root / "data/edinet/download_manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if args.evidence_dir:
            for period in manifest.get("periods", []):
                source, doc_id = period.get("file"), period.get("docID")
                if not source or not doc_id:
                    continue
                json_path = args.evidence_dir / (doc_id + ".contexts.json")
                if not json_path.is_file():
                    continue
                evidence = json.loads(json_path.read_text(encoding="utf-8"))
                if not isinstance(evidence, dict):
                    raise ValueError("Invalid context evidence")
                merged = {}
                ambiguous = set()
                for contexts in evidence.values():
                    if not isinstance(contexts, dict):
                        raise ValueError("Invalid instance context map")
                    for context_id, details in contexts.items():
                        if context_id in merged and merged[context_id] != details:
                            ambiguous.add(context_id)
                        else:
                            merged[context_id] = details
                for context_id in ambiguous:
                    merged.pop(context_id, None)
                instances[source] = merged
        result = inspect(rows, instances)
    except (OSError, ValueError, csv.Error, ET.ParseError, TypeError) as exc:
        result = {"status": "BLOCKED", "scoring_ready": False,
                  "error": type(exc).__name__}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 2 if result["status"] == "BLOCKED" or result["missing_evidence_rows"] else 0

if __name__ == "__main__":
    raise SystemExit(main())
