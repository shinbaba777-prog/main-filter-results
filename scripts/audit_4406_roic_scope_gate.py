#!/usr/bin/env python3
"""Fail-closed audit of ROIC XBRL candidate inventory (no financial scoring)."""
import argparse
import json
from pathlib import Path

REQUIRED = ("OperatingIncome", "IncomeBeforeIncomeTaxes", "IncomeTaxes",
            "NetAssets", "NonControllingInterests", "CashAndDeposits",
            "ShortTermLoansPayable", "CurrentPortionOfLongTermLoansPayable",
            "LongTermLoansPayable")
UNCERTAIN = ("LeaseObligationsCL", "LeaseObligationsNCL", "BondsPayable",
             "SubscriptionRightsToShares")

def audit(data):
    results = []
    for doc in data["documents"]:
        rows = doc["candidates"]
        current = {}
        individual_lease = []
        for row in rows:
            context = row.get("context", {})
            dims = context.get("dimensions", [])
            is_individual = any("NonConsolidatedMember" in d.get("member", "") for d in dims)
            period = context.get("period", {})
            if row["concept"] in UNCERTAIN and is_individual and row["context_id"].startswith("CurrentYearInstant"):
                individual_lease.append(row["concept"])
            if is_individual or dims:
                continue  # No inference of consolidated scope from other explicit dimensions.
            if row["concept"] not in REQUIRED:
                continue
            expected = "CurrentYearDuration" if row["concept"] in REQUIRED[:3] else "CurrentYearInstant"
            if row["context_id"] != expected:
                continue
            current[row["concept"]] = row
        missing = sorted(set(REQUIRED) - set(current))
        results.append({"document_id": doc["document_id"], "matched_required": sorted(current),
                        "missing_required": missing,
                        "individual_lease_not_usable_for_consolidated_roic": sorted(set(individual_lease)),
                        "unresolved_balances": list(UNCERTAIN),
                        "roic_verified": False})
    return {"status": "BLOCKED_PENDING_FULL_BS_AND_NOTES",
            "scoring_eligible": False, "publish_to_index": False,
            "approved_rows": 0, "documents": results}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("inventory", type=Path)
    parser.add_argument("--output", type=Path, default=Path("artifacts/4406_roic_scope_gate.json"))
    args = parser.parse_args()
    result = audit(json.loads(args.inventory.read_text(encoding="utf-8")))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    for row in result["documents"]:
        print(row["document_id"], "required", len(row["matched_required"]), "/", len(REQUIRED),
              "unresolved", len(row["unresolved_balances"]))
    print("BLOCKED: original XBRL balance-sheet and note completeness not yet proven")

if __name__ == "__main__":
    main()
