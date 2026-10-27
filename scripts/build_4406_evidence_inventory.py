#!/usr/bin/env python3
"""Build a non-scoring evidence inventory for 4406 from verified EDINET CSV."""
import csv
import json
from pathlib import Path

try:
    from scripts.verify_4406_primary_sources import verify, AUDIT
except ModuleNotFoundError as exc:
    if exc.name != 'scripts':
        raise
    from verify_4406_primary_sources import verify, AUDIT

SOURCE = Path("data/edinet/verified/4406_five_year_financials.csv")
OUT = Path("artifacts/4406_evidence_inventory.json")
METRICS = ("sales_million_yen", "operating_profit_million_yen",
           "ordinary_profit_million_yen", "parent_net_income_million_yen",
           "eps_yen", "ocf_million_yen", "icf_million_yen",
           "fcf_ocf_plus_icf_million_yen", "roe_reported_pct")
UNVERIFIED = ("roic_pct", "wacc_pct", "ebitda_verified_million_yen",
              "net_debt_verified_million_yen", "short_interest_direction",
              "industry_per_jpx", "ir_event_alpha")

def build(rows, audit):
    gate = verify(rows, audit)
    if gate['issues'] or gate['matched_metrics'] != 45 or len(rows) != 5:
        raise ValueError('Primary-source gate failed: ' + '; '.join(gate['issues']))
    entries = []
    for row in rows:
        for key in METRICS:
            entries.append({
                "fiscal_year_end": row["fiscal_year_end"],
                "metric": key,
                "value": row.get(key) or None,
                "source": "EDINET:" + row["document_id"],
                "verification": "RECONCILED_TO_OFFICIAL_PDF",
                "scoring_eligible": False,
            })
    return {
        "security_code": "4406",
        "status": "REVIEW_REQUIRED",
        "scoring_eligible": False,
        "reconciled_entries": entries,
        "unverified_metrics": [{"metric": x, "status": "UNVERIFIED", "value": None} for x in UNVERIFIED],
        "reason": "The 45-value source reconciliation does not approve the 680 extracted candidate rows or a complete Main Filter 2.3.1 score.",
    }

def main():
    with SOURCE.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    audit = json.loads(AUDIT.read_text(encoding="utf-8"))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(build(rows, audit), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Saved {OUT}; entries={len(rows) * len(METRICS)}; scoring_eligible=false")

if __name__ == "__main__":
    main()
