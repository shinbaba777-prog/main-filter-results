#!/usr/bin/env python3
"""Read-only verification gate for 4406; never authorizes scoring."""
import csv
import json
from pathlib import Path

EXPECTED = {
    "2022-03-31": (32358,1202,1589,811,21.76,1078,-1602,-524,5.2),
    "2023-03-31": (33105,-439,105,-444,-11.92,104,-659,-555,-2.8),
    "2024-03-31": (32863,361,780,220,5.92,3578,-60,3518,1.3),
    "2025-03-31": (32703,829,1195,522,14.00,-224,-174,-398,3.0),
    "2026-03-31": (32105,576,547,597,16.03,1643,501,2144,3.2),
}
FIELDS = (
    "sales_million_yen", "operating_profit_million_yen",
    "ordinary_profit_million_yen", "parent_net_income_million_yen",
    "eps_yen", "ocf_million_yen", "icf_million_yen",
    "fcf_ocf_plus_icf_million_yen", "roe_reported_pct"
)
SOURCE = Path("data/edinet/verified/4406_five_year_financials.csv")
AUDIT = Path("data/edinet/extracted/financial_metric_audit_summary.json")
OUT = Path("artifacts/4406_primary_source_gate.json")

def verify(rows, audit):
    issues = []
    matched = 0
    seen = set()
    for row in rows:
        fy = row.get("fiscal_year_end")
        if fy not in EXPECTED or fy in seen:
            issues.append(f"Unexpected or duplicate fiscal year: {fy}")
            continue
        seen.add(fy)
        if row.get("security_code") != "4406" or row.get("consolidation_scope") != "連結":
            issues.append(f"{fy}: incorrect security code or consolidation scope")
            continue
        for field, expected in zip(FIELDS, EXPECTED[fy]):
            try:
                actual = float(row[field])
            except (ValueError, KeyError, TypeError):
                issues.append(f"{fy}: missing or invalid {field}")
                continue
            if abs(actual - expected) > 0.000001:
                issues.append(f"{fy}: {field} mismatch {actual} != {expected}")
            else:
                matched += 1
        if abs(float(row["ocf_million_yen"]) + float(row["icf_million_yen"]) - float(row["fcf_ocf_plus_icf_million_yen"])) > 0.000001:
            issues.append(f"{fy}: FCF arithmetic mismatch")
    for fy in EXPECTED:
        if fy not in seen:
            issues.append(f"Missing year: {fy}")
    if audit.get("candidate_rows_audited") != 680 or "No row is approved for investment scoring" not in audit.get("important_warning", ""):
        issues.append("Candidate audit approval status changed: manual review required")
    return {"status": "REVIEW_REQUIRED" if not issues else "MISMATCH",
            "matched_metrics": matched, "expected_metrics": 45, "issues": issues,
            "scoring_eligible": False, "note": "Comparison with manually transcribed official earnings PDF values; not XBRL row approval."}

def main():
    with SOURCE.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    audit = json.loads(AUDIT.read_text(encoding="utf-8"))
    result = verify(rows, audit)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    if result["issues"]:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
