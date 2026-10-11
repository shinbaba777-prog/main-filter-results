#!/usr/bin/env python3
"""Build a conservative review queue for core consolidated annual metrics.

This creates a human-review aid only. It never marks values as approved for scoring.
"""
from __future__ import annotations
import csv, json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "edinet" / "extracted"
SOURCE = OUT / "financial_metric_candidates.csv"
QUEUE = OUT / "core_metric_review_queue.csv"
SUMMARY = OUT / "core_metric_review_queue_summary.json"

# Narrow allowlist: concepts whose meaning is sufficiently explicit for triage.
# These still require filing-period, taxonomy, and duplicate checks by a human.
CONCEPTS = {
    ("sales", "jppfs_cor:NetSales"),
    ("sales", "jpcrp_cor:NetSalesSummaryOfBusinessResults"),
    ("operating_profit", "jppfs_cor:OperatingIncome"),
    ("ordinary_profit", "jppfs_cor:OrdinaryIncome"),
    ("profit", "jppfs_cor:ProfitLoss"),
}
CONTEXTS = {
    f"{prefix}{kind}"
    for prefix in ("CurrentYear", "Prior1Year", "Prior2Year", "Prior3Year", "Prior4Year")
    for kind in ("Duration", "Instant")
}
FIELDS = [
    "security_code", "candidate_metric", "value", "relative_year",
    "source_zip", "source_csv", "row_number", "element_id", "context_id",
    "period_type", "consolidation_scope", "unit_id", "unit_label",
    "review_status", "review_reason", "raw_row_json",
]

def main():
    if not SOURCE.exists():
        raise SystemExit(f"Missing input: {SOURCE}")
    rows, counts = [], Counter()
    with SOURCE.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            try:
                raw = json.loads(row.get("raw_row_json") or "{}")
            except json.JSONDecodeError:
                raw = {}
            metric = row.get("candidate_metric", "")
            concept = raw.get("要素ID", "")
            context = raw.get("コンテキストID", "")
            scope = raw.get("連結・個別", "")
            period = raw.get("期間・時点", "")
            unit_id = raw.get("ユニットID", "")
            unit_label = raw.get("単位", "")
            if (metric, concept) not in CONCEPTS:
                counts["excluded_concept_or_metric"] += 1
                continue
            if context not in CONTEXTS:
                counts["excluded_nonannual_or_member_context"] += 1
                continue
            if scope != "連結":
                counts["excluded_nonconsolidated_or_unclear_scope"] += 1
                continue
            expected_period = "時点" if metric in ("equity", "total_assets") else "期間"
            reasons = []
            if period != expected_period:
                reasons.append("PERIOD_TYPE_MISMATCH")
            if not unit_id or not unit_label:
                reasons.append("UNIT_MISSING")
            if context.startswith("CurrentYear"):
                year = "当期"
            elif context.startswith("Prior1Year"):
                year = "前期"
            elif context.startswith("Prior2Year"):
                year = "前々期"
            elif context.startswith("Prior3Year"):
                year = "3期前"
            else:
                year = "4期前"
            rec = {
                "security_code": row.get("security_code", ""),
                "candidate_metric": metric,
                "value": row.get("value", ""),
                "relative_year": year,
                "source_zip": row.get("source_zip", ""),
                "source_csv": row.get("source_csv", ""),
                "row_number": row.get("row_number", ""),
                "element_id": concept,
                "context_id": context,
                "period_type": period,
                "consolidation_scope": scope,
                "unit_id": unit_id,
                "unit_label": unit_label,
                "review_status": "MANUAL_REVIEW_REQUIRED",
                "review_reason": ";".join(reasons) if reasons else "CHECK_FILING_AND_DUPLICATES",
                "raw_row_json": row.get("raw_row_json", ""),
            }
            rows.append(rec)
            counts["queued_" + metric] += 1
    with QUEUE.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "input": str(SOURCE.relative_to(ROOT)),
        "output": str(QUEUE.relative_to(ROOT)),
        "rows_queued": len(rows),
        "counts": dict(counts),
        "important_warning": "Review queue only. No row is approved for investment scoring. Confirm official filing, fiscal period dates, taxonomy definition, unit/scale, signs, and duplicates before use."
    }
    SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))

if __name__ == "__main__":
    main()
