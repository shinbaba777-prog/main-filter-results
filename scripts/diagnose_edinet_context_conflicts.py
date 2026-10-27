#!/usr/bin/env python3
"""Diagnose whether apparent cross-filing conflicts mix different XBRL contexts.

Read-only triage. Never treats a matching context suffix as proof of identical
XBRL dimensions or dates; original XBRL must be inspected before approval.
"""
import argparse
import csv
import json
import re
from collections import defaultdict, Counter
from pathlib import Path

PATTERN = re.compile(r"^(CurrentYear|Prior([1-4])Year)(Duration|Instant)(.*)$")

def diagnose(rows, manifest):
    periods = {p.get("file"): p.get("periodEnd") for p in manifest.get("periods", [])
               if isinstance(p, dict) and p.get("file") and p.get("periodEnd")}
    groups = defaultdict(list)
    excluded = 0
    for row in rows:
        match = PATTERN.match(row.get("context_id", ""))
        end = periods.get(row.get("source_zip"))
        if not match or not end:
            excluded += 1
            continue
        year = int(end[:4]) - int(match.group(2) or 0)
        # Preserve suffix to avoid comparing explicit non-consolidated members
        # with a base context or with a different member.
        key = (row.get("security_code"), row.get("candidate_metric"),
               row.get("element_id"), row.get("consolidation_scope"),
               row.get("unit_id"), match.group(3), match.group(4), year)
        groups[key].append(row)
    conflicts = []
    for key, facts in groups.items():
        if len({r.get("source_zip") for r in facts}) < 2:
            continue
        by_filing = defaultdict(set)
        for row in facts:
            by_filing[row["source_zip"]].add(str(row.get("value", "")).strip())
        distinct = set().union(*by_filing.values())
        if len(distinct) > 1:
            conflicts.append({"metric": key[1], "year_inferred": key[-1],
                              "context_suffix": key[-2], "scope_label": key[3],
                              "source_files": sorted(by_filing),
                              "values": sorted(distinct),
                              "within_filing_ambiguity": any(len(v) > 1 for v in by_filing.values())})
    reasons = Counter("WITHIN_FILING_AMBIGUITY" if c["within_filing_ambiguity"]
                      else "CROSS_FILING_DIFFERENCE" for c in conflicts)
    return {"status": "REVIEW_REQUIRED", "scoring_ready": False,
            "conflicts_after_suffix_partition": len(conflicts),
            "reason_counts": dict(reasons), "excluded_rows": excluded,
            "conflicts": conflicts[:100],
            "limitation": "Context suffix is not actual XBRL period or dimensions. All differences require source review."}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    base = args.root / "data/edinet"
    try:
        manifest = json.loads((base / "download_manifest.json").read_text(encoding="utf-8"))
        with (base / "extracted/financial_metric_audit.csv").open(encoding="utf-8-sig", newline="") as f:
            result = diagnose(list(csv.DictReader(f)), manifest)
    except (OSError, ValueError, csv.Error, KeyError) as exc:
        result = {"status": "BLOCKED", "scoring_ready": False, "error": type(exc).__name__}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 2 if result["status"] == "BLOCKED" else 0

if __name__ == "__main__":
    raise SystemExit(main())
