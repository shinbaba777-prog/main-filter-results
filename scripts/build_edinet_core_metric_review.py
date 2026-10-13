#!/usr/bin/env python3
"""Build a conservative review queue for core consolidated annual metrics.

This creates a human-review aid only. It never marks values as approved for scoring.
"""
from __future__ import annotations
import csv, json
from collections import Counter
from datetime import datetime, timezone, date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "edinet" / "extracted"
SOURCE = OUT / "financial_metric_candidates.csv"
QUEUE = OUT / "core_metric_review_queue.csv"
SUMMARY = OUT / "core_metric_review_queue_summary.json"
MANIFEST = ROOT / "data" / "edinet" / "extraction_summary.json"

# Narrow allowlist: concepts whose meaning is sufficiently explicit for triage.
# These still require filing-period, taxonomy, and duplicate checks by a human.
CONCEPTS = {
    ("sales", "jppfs_cor:NetSales"),
    ("sales", "jpcrp_cor:NetSalesSummaryOfBusinessResults"),
    ("operating_profit", "jppfs_cor:OperatingIncome"),
    ("operating_profit", "jpigp_cor:OperatingProfitLossIFRS"),
    ("operating_profit", "jpcrp_cor:OperatingIncomeLossUSGAAPSummaryOfBusinessResults"),
    ("ordinary_profit", "jppfs_cor:OrdinaryIncome"),
    ("ordinary_profit", "jpcrp_cor:OrdinaryIncomeLossSummaryOfBusinessResults"),
    ("profit", "jppfs_cor:ProfitLoss"),
    ("profit", "jpcrp_cor:NetIncomeLossSummaryOfBusinessResults"),
    ("profit", "jpcrp_cor:ProfitLossAttributableToOwnersOfParentSummaryOfBusinessResults"),
    ("eps", "jpcrp_cor:BasicEarningsLossPerShareSummaryOfBusinessResults"),
    ("ocf", "jpcrp_cor:NetCashProvidedByUsedInOperatingActivitiesSummaryOfBusinessResults"),
    ("ocf", "jppfs_cor:NetCashProvidedByUsedInOperatingActivities"),
    ("icf", "jpcrp_cor:NetCashProvidedByUsedInInvestingActivitiesSummaryOfBusinessResults"),
    ("icf", "jppfs_cor:NetCashProvidedByUsedInInvestmentActivities"),
}
CONTEXTS = {
    f"{prefix}{kind}"
    for prefix in ("CurrentYear", "Prior1Year", "Prior2Year", "Prior3Year", "Prior4Year")
    for kind in ("Duration", "Instant")
}
FIELDS = [
    "security_code", "candidate_metric", "value", "relative_year",
    "filing_period_end", "fiscal_year_inferred", "context_year_offset",
    "source_zip", "source_csv", "row_number", "element_id", "context_id",
    "period_type", "consolidation_scope", "unit_id", "unit_label",
    "review_status", "review_reason", "duplicate_count", "source_row_numbers", "raw_row_json",
]

def is_annual_context(context: str) -> bool:
    """Accept standard annual contexts and annual business-results summary member contexts.

    Member contexts remain review-only; they are never treated as consolidated facts.
    """
    for base in CONTEXTS:
        if context == base:
            return True
        if context.startswith(base + "_NonConsolidatedMember"):
            return True
    return False


def main():
    if not SOURCE.exists():
        raise SystemExit(f"Missing input: {SOURCE}")
    rows, counts = [], Counter()
    filing_periods = {}
    if MANIFEST.exists():
        try:
            manifest_data = json.loads(MANIFEST.read_text(encoding="utf-8"))
            filing_periods = {
                item.get("file", ""): item.get("periodEnd", "")
                for item in manifest_data.get("fiscal_periods", manifest_data.get("periods", []))
                if item.get("file") and item.get("periodEnd")
            }
        except (OSError, json.JSONDecodeError):
            filing_periods = {}
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
            is_summary_concept = concept.startswith("jpcrp_cor:") and concept.endswith("SummaryOfBusinessResults")
            if not is_annual_context(context):
                counts["excluded_nonannual_or_member_context"] += 1
                continue
            # Summary-table facts using a non-consolidated member are retained only
            # as explicit manual-review candidates. They must not be auto-approved.
            # Scope other than consolidated is retained only for manual review
            # for these explicitly identified cash-flow summary concepts.
            scope_unclear = scope != "連結"
            # Business-results summary concepts commonly carry the EDINET scope
            # label "その他". Keep these exact, allowlisted concepts for review,
            # but explicitly flag scope as unverified instead of assuming consolidated.
            if scope_unclear and not is_summary_concept:
                counts["excluded_nonconsolidated_or_unclear_scope"] += 1
                continue
            expected_period = "時点" if metric in ("equity", "total_assets") else "期間"
            reasons = []
            if scope_unclear:
                reasons.append("CONSOLIDATION_SCOPE_UNCLEAR")
            if period != expected_period:
                reasons.append("PERIOD_TYPE_MISMATCH")
            if metric == "eps":
                # EDINET EPS facts commonly use JPYPerShares as the unit ID while the unit label is blank.
                unit_ok = unit_id == "JPYPerShares"
            else:
                unit_ok = bool(unit_id and unit_label)
            if not unit_ok:
                reasons.append("UNIT_MISSING")
            if context.startswith("CurrentYear"):
                year, offset = "当期", 0
            elif context.startswith("Prior1Year"):
                year, offset = "前期", 1
            elif context.startswith("Prior2Year"):
                year, offset = "前々期", 2
            elif context.startswith("Prior3Year"):
                year, offset = "3期前", 3
            else:
                year, offset = "4期前", 4

            source_zip = row.get("source_zip", "")
            filing_period_end = filing_periods.get(source_zip, "")
            fiscal_year_inferred = ""
            if filing_period_end:
                try:
                    # The XBRL context provides a relative annual offset, but this
                    # source CSV may not expose the exact historical end date.
                    # Preserve the inferred year separately; never call it verified.
                    fiscal_year_inferred = str(date.fromisoformat(filing_period_end).year - offset)
                except ValueError:
                    counts["invalid_filing_period_end"] += 1
            rec = {
                "security_code": row.get("security_code", ""),
                "candidate_metric": metric,
                "value": row.get("value", ""),
                "relative_year": year,
                "filing_period_end": filing_period_end,
                "fiscal_year_inferred": fiscal_year_inferred,
                "context_year_offset": offset,
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
    # Collapse exact duplicate facts from the same filing/member/context. Keep
    # provenance for every source row so deduplication remains auditable.
    deduped = {}
    duplicate_rows_collapsed = 0
    key_fields = (
        "security_code", "candidate_metric", "value", "source_zip", "source_csv",
        "element_id", "context_id", "period_type", "consolidation_scope",
        "unit_id", "unit_label",
    )
    for rec in rows:
        key = tuple(rec.get(k, "") for k in key_fields)
        if key not in deduped:
            rec["duplicate_count"] = 1
            rec["source_row_numbers"] = rec.get("row_number", "")
            deduped[key] = rec
        else:
            existing = deduped[key]
            existing["duplicate_count"] = int(existing["duplicate_count"]) + 1
            existing["source_row_numbers"] += ";" + rec.get("row_number", "")
            duplicate_rows_collapsed += 1
    rows = list(deduped.values())
    counts["duplicate_rows_collapsed"] = duplicate_rows_collapsed

    with QUEUE.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "input": str(SOURCE.relative_to(ROOT)),
        "output": str(QUEUE.relative_to(ROOT)),
        "rows_queued": len(rows),
        "rows_before_deduplication": len(rows) + duplicate_rows_collapsed,
        "duplicate_rows_collapsed": duplicate_rows_collapsed,
        "counts": dict(counts),
        "important_warning": "Review queue only. No row is approved for investment scoring. fiscal_year_inferred is inferred from filing period end and relative context offset, not a verified period end; confirm exact XBRL dates, filing, taxonomy definition, unit/scale, signs, and duplicates before use."
    }
    SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))

if __name__ == "__main__":
    main()
