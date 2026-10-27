#!/usr/bin/env python3
"""Strict EDINET row context checks; fail closed without asserting approval.

Uses the extracted financial_metric_audit.csv columns. Does not change source
data, grant scoring approval, or infer a consolidated scope.
"""
from __future__ import annotations
import argparse
import csv
import json
from collections import Counter
from pathlib import Path

DURATION = {"sales", "operating_profit", "ordinary_profit", "profit", "ocf", "icf", "fcf"}
MONETARY = {"sales", "operating_profit", "ordinary_profit", "profit", "ocf", "icf", "fcf"}
ALLOWED_PERIOD = {"期間", "時点"}
ALLOWED_SCOPE = {"連結", "個別"}

def inspect(rows):
    reasons = Counter()
    for row in rows:
        metric = row.get("candidate_metric", "")
        context = row.get("context_id", "")
        scope = row.get("consolidation_scope", "")
        period = row.get("period_type", "")
        unit = row.get("unit_id", "")
        if not context:
            reasons["CONTEXT_ID_MISSING"] += 1
        if scope not in ALLOWED_SCOPE:
            reasons["SCOPE_UNRESOLVED"] += 1
        if period not in ALLOWED_PERIOD:
            reasons["PERIOD_TYPE_UNKNOWN"] += 1
        if metric in DURATION and period != "期間":
            reasons["DURATION_PERIOD_MISMATCH"] += 1
        if metric in MONETARY and unit != "JPY":
            reasons["MONETARY_UNIT_MISMATCH"] += 1
        if not row.get("source_zip") or not row.get("source_csv") or not row.get("row_number"):
            reasons["SOURCE_LOCATION_MISSING"] += 1
        if row.get("validation_status") != "APPROVED":
            reasons["NOT_APPROVED"] += 1
    return {"status": "REVIEW_REQUIRED", "scoring_ready": False,
            "rows_checked": len(rows), "issue_counts": dict(sorted(reasons.items())),
            "note": "Context labels and source references require filing-level verification."}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    path = args.root / "data/edinet/extracted/financial_metric_audit.csv"
    try:
        with path.open(encoding="utf-8-sig", newline="") as handle:
            result = inspect(list(csv.DictReader(handle)))
    except (OSError, ValueError, csv.Error) as exc:
        result = {"status": "BLOCKED", "scoring_ready": False,
                  "error": type(exc).__name__}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 2 if result["status"] == "BLOCKED" else 0

if __name__ == "__main__":
    raise SystemExit(main())
