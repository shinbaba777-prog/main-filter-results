#!/usr/bin/env python3
"""Calculate transparent, non-scoring 4406 CF sensitivities from reconciled CSV.

The script never imports the scoring engine or writes to index.csv.
"""
import csv
import json
from pathlib import Path

SOURCE = Path("data/edinet/verified/4406_five_year_financials.csv")
OUT = Path("artifacts/4406_cf_sensitivity_review.json")
SECURITIES_SALE_PROCEEDS_2026_MJPY = 942  # issuer FY2026 CF statement; review only

def calculate(rows):
    years = {r["fiscal_year_end"]: r for r in rows}
    wanted = ("2024-03-31", "2025-03-31", "2026-03-31")
    if len(rows) != 5 or len(years) != 5 or not all(y in years for y in wanted):
        raise ValueError("Expected unique five-year verified source rows")
    for y in wanted:
        if years[y].get("consolidation_scope") != "連結" or not years[y].get("document_id"):
            raise ValueError("Missing consolidated source provenance")
    fcf = {y: int(years[y]["fcf_ocf_plus_icf_million_yen"]) for y in wanted}
    ocf = {y: int(years[y]["ocf_million_yen"]) for y in wanted}
    icf = {y: int(years[y]["icf_million_yen"]) for y in wanted}
    for y in wanted:
        if fcf[y] != ocf[y] + icf[y]:
            raise ValueError("FCF arithmetic inconsistent with source")
    ni = {y: int(years[y]["parent_net_income_million_yen"]) for y in wanted}
    fcf3 = sum(fcf.values())
    fcf2026_adj = fcf["2026-03-31"] - SECURITIES_SALE_PROCEEDS_2026_MJPY
    return {
        "security_code": "4406", "status": "REVIEW_REQUIRED", "scoring_eligible": False,
        "publish_to_index": False,
        "source_file": str(SOURCE),
        "source_documents": {y: years[y]["document_id"] for y in wanted},
        "periods": list(wanted),
        "ocf_3y_million_yen": sum(ocf.values()),
        "parent_ni_3y_million_yen": sum(ni.values()),
        "ocf_parent_ni_ratio_3y": sum(ocf.values()) / sum(ni.values()) if sum(ni.values()) else None,
        "reported_fcf_3y_million_yen": fcf3,
        "reported_fcf_2026_million_yen": fcf["2026-03-31"],
        "2026_investing_security_sale_proceeds_million_yen": SECURITIES_SALE_PROCEEDS_2026_MJPY,
        "fcf_2026_excluding_security_sale_proceeds_million_yen": fcf2026_adj,
        "fcf_3y_excluding_2026_security_sale_proceeds_million_yen": fcf3 - SECURITIES_SALE_PROCEEDS_2026_MJPY,
        "methodology": "Sensitivity subtracts gross security-sale cash inflow only; not normalized FCF and not approved rubric input.",
        "primary_source_2026": "https://www.nj-chem.co.jp/app/upload/ir/pdf/36433ee666c2c24d3f13cbb481af6901.pdf",
    }

def main():
    with SOURCE.open(newline="", encoding="utf-8-sig") as f:
        result = calculate(list(csv.DictReader(f)))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"REVIEW_REQUIRED; reported 3y FCF={result['reported_fcf_3y_million_yen']}m; adjusted sensitivity={result['fcf_3y_excluding_2026_security_sale_proceeds_million_yen']}m; no scoring")

if __name__ == "__main__":
    main()
