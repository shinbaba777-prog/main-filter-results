#!/usr/bin/env python3
"""Compare broad vs member-aware EDINET cross-filing conflicts.

Read-only regression audit. The reported difference is diagnostic only, never
proof of the correct consolidation scope or approval for investment scoring.
"""
import argparse
import csv
import json
from pathlib import Path
from check_edinet_cross_filing import inspect as broad_inspect
from diagnose_edinet_context_conflicts import diagnose as member_inspect

def summarize(rows, manifest):
    broad = broad_inspect(rows, manifest)
    member = member_inspect(rows, manifest)
    broad_count = broad["conflict_groups"]
    refined_count = member["conflicts_after_suffix_partition"]
    return {
        "status": "REVIEW_REQUIRED",
        "scoring_ready": False,
        "broad_conflicts": broad_count,
        "member_aware_conflicts": refined_count,
        "resolved_by_context_partition_only": max(0, broad_count - refined_count),
        "review_required": True,
        "warning": "A disappeared comparison is not a verified financial fact; inspect original XBRL contexts."
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    base = args.root / "data/edinet"
    try:
        manifest = json.loads((base / "download_manifest.json").read_text(encoding="utf-8"))
        with (base / "extracted/financial_metric_audit.csv").open(encoding="utf-8-sig", newline="") as f:
            result = summarize(list(csv.DictReader(f)), manifest)
    except (OSError, ValueError, csv.Error, KeyError) as exc:
        result = {"status": "BLOCKED", "scoring_ready": False, "error": type(exc).__name__}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 2 if result["status"] == "BLOCKED" else 0

if __name__ == "__main__":
    raise SystemExit(main())
