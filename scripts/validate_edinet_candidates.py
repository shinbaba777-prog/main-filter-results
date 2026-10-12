#!/usr/bin/env python3
"""Create a conservative audit view of EDINET metric candidates.

This does not approve values for investment scoring. It separates candidate
rows by context, unit, period, consolidation scope, and concept identifier.
"""
from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "edinet" / "extracted"
SOURCE = OUT / "financial_metric_candidates.csv"
AUDIT = OUT / "financial_metric_audit.csv"
SUMMARY = OUT / "financial_metric_audit_summary.json"

def metric_is_eps(row):
    return row.get("candidate_metric", "") == "eps"


def is_current_year_context(context):
    """Accept annual current-year contexts with taxonomy member suffixes.

    This only removes a false context warning; it does not approve the metric.
    """
    return context in ("CurrentYearDuration", "CurrentYearInstant") or context.startswith(
        ("CurrentYearDuration_", "CurrentYearInstant_")
    )

def main():
    if not SOURCE.exists():
        raise SystemExit(f"Missing input: {SOURCE}")
    audited = []
    counts = Counter()
    with SOURCE.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            try:
                raw = json.loads(row.get("raw_row_json") or "{}")
            except json.JSONDecodeError:
                raw = {}
            concept = raw.get("要素ID", "")
            context = raw.get("コンテキストID", "")
            period = raw.get("期間・時点", "")
            scope = raw.get("連結・個別", "")
            unit_id = raw.get("ユニットID", "")
            unit_label = raw.get("単位", "")
            relative_year = raw.get("相対年度", "")
            flags = []
            # Accept current-year contexts with taxonomy member suffixes, but keep
            # consolidation-scope checks separate and require manual review.
            if not is_current_year_context(context):
                flags.append("NOT_CURRENT_YEAR_CONTEXT")
            if not concept or ":" not in concept:
                flags.append("CONCEPT_ID_UNVERIFIED")
            if scope not in ("連結", "個別"):
                flags.append("CONSOLIDATION_SCOPE_UNCLEAR")
            if period not in ("期間", "時点"):
                flags.append("PERIOD_TYPE_UNCLEAR")
            # EDINET EPS uses JPYPerShares as the unit ID with an intentionally blank unit label.
            unit_ok = (unit_id == "JPYPerShares") if metric_is_eps(row) else bool(unit_id and unit_label)
            if not unit_ok:
                flags.append("UNIT_UNCLEAR")
            metric = row.get("candidate_metric", "")
            if metric in ("sales", "operating_profit", "ordinary_profit", "profit", "ocf", "icf", "fcf") and period != "期間":
                flags.append("EXPECTED_DURATION_METRIC")
            if metric in ("equity", "total_assets") and period != "時点":
                flags.append("EXPECTED_INSTANT_METRIC")
            if metric == "eps" and unit_id not in ("JPYPerShares", "JPYPerShare", "JPY/shares", "JPY"):
                flags.append("EPS_UNIT_REVIEW")
            status = "REVIEW_REQUIRED"
            if not flags:
                status = "STRUCTURALLY_PLAUSIBLE_REVIEW_REQUIRED"
            audited.append({
                "security_code": row.get("security_code", ""),
                "candidate_metric": metric,
                "value": row.get("value", ""),
                "source_zip": row.get("source_zip", ""),
                "source_csv": row.get("source_csv", ""),
                "row_number": row.get("row_number", ""),
                "element_id": concept,
                "context_id": context,
                "relative_year": relative_year,
                "period_type": period,
                "consolidation_scope": scope,
                "unit_id": unit_id,
                "unit_label": unit_label,
                "validation_status": status,
                "validation_flags": ";".join(flags),
                "mapping_status": row.get("mapping_status", "REVIEW_REQUIRED"),
                "raw_row_json": row.get("raw_row_json", ""),
            })
            counts[status] += 1
            for flag in flags:
                counts["flag:" + flag] += 1
    fields = ["security_code","candidate_metric","value","source_zip","source_csv","row_number",
              "element_id","context_id","relative_year","period_type","consolidation_scope",
              "unit_id","unit_label","validation_status","validation_flags","mapping_status","raw_row_json"]
    with AUDIT.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(audited)
    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "input": str(SOURCE.relative_to(ROOT)),
        "output": str(AUDIT.relative_to(ROOT)),
        "candidate_rows_audited": len(audited),
        "status_counts": dict(counts),
        "important_warning": "No row is approved for investment scoring. STRUCTURALLY_PLAUSIBLE_REVIEW_REQUIRED means only basic fields look consistent; concept definitions, filing context, period dates, consolidated statements, signs, and duplicates still require verification."
    }
    SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))
if __name__ == "__main__":
    main()
