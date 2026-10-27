#!/usr/bin/env python3
"""Validate actual original-XBRL context dates for each EDINET audit row.

Read-only and fail-closed. Context dates and dimensions are source evidence,
not final approval of the financial value or consolidation scope.
"""
import argparse
import csv
import json
import re
from collections import Counter
from datetime import date
from pathlib import Path

CONTEXT = re.compile(r"^(CurrentYear|Prior([1-4])Year)(Duration|Instant)(.*)$")

def inspect(rows, manifest, evidence_dir):
    mapping = {p["file"]: p for p in manifest.get("periods", [])
               if isinstance(p, dict) and p.get("file") and p.get("docID") and p.get("periodEnd")}
    cached = {}
    reasons = Counter()
    examples = []
    checked = 0
    for row in rows:
        source = row.get("source_zip", "")
        period = mapping.get(source)
        reason = None
        if not period:
            reason = "SOURCE_NOT_IN_MANIFEST"
        else:
            doc_id = period["docID"]
            if doc_id not in cached:
                path = evidence_dir / (doc_id + ".contexts.json")
                if path.is_file():
                    payload = json.loads(path.read_text(encoding="utf-8"))
                    cached[doc_id] = payload if isinstance(payload, dict) else {}
                else:
                    cached[doc_id] = {}
            instances = cached[doc_id]
            match = CONTEXT.match(row.get("context_id", ""))
            if not instances:
                reason = "ORIGINAL_CONTEXT_EVIDENCE_MISSING"
            elif not match:
                reason = "CONTEXT_PATTERN_UNKNOWN"
            else:
                found = []
                for instance in instances.values():
                    if isinstance(instance, dict):
                        value = instance.get(row.get("context_id", ""))
                        if isinstance(value, dict):
                            found.append(value)
                if not found:
                    reason = "CONTEXT_NOT_FOUND"
                elif len({json.dumps(item, sort_keys=True) for item in found}) != 1:
                    reason = "AMBIGUOUS_CONTEXT_DEFINITION"
                else:
                    fact = found[0]
                    expected_year = int(period["periodEnd"][:4]) - int(match.group(2) or 0)
                    end = fact.get("end_date") or fact.get("instant")
                    try:
                        actual_end = date.fromisoformat(end)
                        expected_month_day = period["periodEnd"][4:]
                        if actual_end.year != expected_year or actual_end.isoformat()[4:] != expected_month_day:
                            reason = "ACTUAL_PERIOD_END_MISMATCH"
                        elif match.group(3) == "Duration":
                            start = date.fromisoformat(fact.get("start_date"))
                            if not start < actual_end:
                                reason = "INVALID_DURATION"
                            else:
                                checked += 1
                        elif fact.get("instant"):
                            checked += 1
                        else:
                            reason = "EXPECTED_INSTANT"
                    except (TypeError, ValueError):
                        reason = "INVALID_OR_MISSING_PERIOD"
        if reason:
            reasons[reason] += 1
            if len(examples) < 15:
                examples.append({"source_zip": source, "context_id": row.get("context_id"),
                                 "reason": reason})
    return {"status": "REVIEW_REQUIRED", "scoring_ready": False,
            "rows": len(rows), "period_evidence_matched": checked,
            "period_evidence_unresolved": sum(reasons.values()),
            "reasons": dict(sorted(reasons.items())), "examples": examples,
            "note": "Dates matched, if any, are not approved values; source CSV instance identity and dimensions still need review."}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--evidence-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        base = args.root / "data/edinet"
        manifest = json.loads((base / "download_manifest.json").read_text(encoding="utf-8"))
        with (base / "extracted/financial_metric_audit.csv").open(encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
        result = inspect(rows, manifest, args.evidence_dir)
    except (OSError, ValueError, csv.Error, TypeError) as exc:
        result = {"status": "BLOCKED", "scoring_ready": False, "error": type(exc).__name__}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 2 if result["status"] == "BLOCKED" or result["period_evidence_unresolved"] else 0

if __name__ == "__main__":
    raise SystemExit(main())
