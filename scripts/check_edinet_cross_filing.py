#!/usr/bin/env python3
"""Detect conflicting annual EDINET values across different filings.

Read-only diagnostics. A matching fact is not approval: context, accounting
standard, scope, restatements and amendment precedence still require review.
"""
import argparse
import csv
import json
import re
from collections import defaultdict
from pathlib import Path

CONTEXT = re.compile(r"^(CurrentYear|Prior([1-4])Year)(Duration|Instant)(?:_|$)")
def inspect(rows, manifest):
    periods = {p["file"]: p["periodEnd"] for p in manifest.get("periods", [])
               if isinstance(p, dict) and p.get("file") and p.get("periodEnd")}
    groups = defaultdict(list)
    skipped = 0
    for row in rows:
        match = CONTEXT.match(row.get("context_id", ""))
        filing_end = periods.get(row.get("source_zip"))
        if not match or not filing_end:
            skipped += 1
            continue
        offset = int(match.group(2) or 0)
        fiscal_year = int(filing_end[:4]) - offset
        # Compare only like-for-like taxonomy, scope, unit and duration.
        key = (row.get("security_code"), row.get("candidate_metric"),
               row.get("element_id"), row.get("consolidation_scope"),
               row.get("unit_id"), match.group(3), fiscal_year)
        groups[key].append(row)
    conflicts = []
    overlapping = 0
    for key, facts in groups.items():
        filings = {r.get("source_zip") for r in facts}
        if len(filings) < 2:
            continue
        overlapping += 1
        values = {str(r.get("value", "")).strip() for r in facts}
        if len(values) > 1:
            conflicts.append({"metric": key[1], "fiscal_year_inferred": key[-1],
                              "scope": key[3], "unit": key[4],
                              "filings": sorted(filings), "values": sorted(values)})
    return {"status": "REVIEW_REQUIRED", "scoring_ready": False,
            "overlapping_groups": overlapping, "conflict_groups": len(conflicts),
            "skipped_rows": skipped, "conflicts": conflicts[:100],
            "note": "Fiscal years inferred from filing year; compare actual context dates and restatements before approval."}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    base = args.root / "data/edinet"
    try:
        manifest = json.loads((base / "download_manifest.json").read_text(encoding="utf-8"))
        with (base / "extracted/financial_metric_audit.csv").open(encoding="utf-8-sig", newline="") as f:
            result = inspect(list(csv.DictReader(f)), manifest)
    except (OSError, ValueError, csv.Error, KeyError) as exc:
        result = {"status": "BLOCKED", "scoring_ready": False, "error": type(exc).__name__}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 2 if result["status"] == "BLOCKED" else 0

if __name__ == "__main__":
    raise SystemExit(main())
