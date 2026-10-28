#!/usr/bin/env python3
"""Safely bridge a review-only evidence inventory into the existing scoring engine.

Never promote review evidence to scored rubric items. Output is an explicitly
insufficient dry run, not a formal investment score.
"""
import argparse
import json
from pathlib import Path
from scripts.scoring_engine import STAGE1_GROUPS, STAGE2_GROUPS, evaluate

def dry_run(inventory):
    if inventory.get("security_code") != "4406":
        raise ValueError("Unsupported security code")
    if inventory.get("scoring_eligible") is not False or inventory.get("status") != "REVIEW_REQUIRED":
        raise ValueError("Unexpected evidence approval state: manual review required")
    entries = inventory.get("reconciled_entries", [])
    if len(entries) != 45 or any(e.get("scoring_eligible") is not False for e in entries):
        raise ValueError("Expected exactly 45 review-only entries")
    groups = {**STAGE1_GROUPS, **STAGE2_GROUPS}
    items = [{"key": "pending_" + group, "group": group, "points": None,
              "max_points": maximum, "status": "missing",
              "evidence": "Source evidence has not been mapped to a verified rubric subitem",
              "source": "artifacts/4406_evidence_inventory.json"}
             for group, maximum in groups.items()]
    outcome = evaluate({"items": items, "buy_block_inputs": {"roic_unavailable": True}})
    if outcome["data_status"] != "DATA-INSUFFICIENT" or outcome["total"]["adjusted_score"] is not None:
        raise ValueError("Fail-closed scoring invariant violated")
    return {"security_code": "4406", "mode": "NON_SCORING_DRY_RUN",
            "source_entries": len(entries), "source_approved": False,
            "rubric_status": "ALL_PENDING_MANUAL_MAPPING",
            "engine_result": outcome, "publish_to_index": False}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", default="artifacts/4406_evidence_inventory.json")
    p.add_argument("--output", default="artifacts/4406_scoring_bridge_dry_run.json")
    args = p.parse_args()
    inventory = json.loads(Path(args.input).read_text(encoding="utf-8"))
    result = dry_run(inventory)
    dest = Path(args.output)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Dry run:", result["engine_result"]["judgment"], "score=None; publish_to_index=false")

if __name__ == "__main__":
    main()
