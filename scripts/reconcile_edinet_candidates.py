#!/usr/bin/env python3
"""Reconcile extracted EDINET candidates against the existing audit CSV.

A matching row is NOT a verified financial fact. This is a read-only
provenance/consistency check; consolidated scope and XBRL semantics require
separate review.
"""
from __future__ import annotations
import argparse
import csv
import json
from collections import Counter
from pathlib import Path

KEYS = ("security_code", "candidate_metric", "value", "source_zip",
        "source_csv", "row_number")
def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))

def reconcile(candidates, audits, manifest):
    issues = []
    if not isinstance(manifest, dict):
        return {"status": "BLOCKED", "issues": ["manifest unavailable"]}
    expected_files = {p.get("file") for p in manifest.get("periods", [])
                      if isinstance(p, dict) and p.get("file")}
    def key(row):
        return tuple(row.get(k, "") for k in KEYS)
    candidate_counts = Counter(key(r) for r in candidates)
    audit_counts = Counter(key(r) for r in audits)
    missing = sum((candidate_counts - audit_counts).values())
    extra = sum((audit_counts - candidate_counts).values())
    if missing or extra:
        issues.append("candidate/audit row mismatch: missing=%d extra=%d" % (missing, extra))
    if not expected_files:
        issues.append("manifest has no source ZIP references")
    unexpected = sorted({r.get("source_zip", "") for r in candidates
                         if r.get("source_zip") not in expected_files})
    if unexpected:
        issues.append("candidate source ZIP not listed in manifest: " + ", ".join(unexpected[:10]))
    unknown_scope = sum(r.get("consolidation_scope") not in ("連結", "個別") for r in audits)
    unapproved = sum(r.get("validation_status") != "APPROVED" for r in audits)
    if unknown_scope:
        issues.append("consolidation scope unresolved: %d rows" % unknown_scope)
    if unapproved:
        issues.append("audit rows not approved: %d" % unapproved)
    # Even APPROVED is insufficient without independent filing-level checks.
    issues.append("filing context, units, sign and document provenance need independent verification")
    return {"status": "REVIEW_REQUIRED" if not missing and not extra and not unexpected else "BLOCKED",
            "scoring_ready": False, "candidate_rows": len(candidates),
            "audit_rows": len(audits), "scope_unresolved": unknown_scope,
            "not_approved": unapproved, "issues": issues}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    base = args.root / "data" / "edinet"
    try:
        manifest = json.loads((base / "download_manifest.json").read_text(encoding="utf-8"))
        candidates = read_csv(base / "extracted/financial_metric_candidates.csv")
        audits = read_csv(base / "extracted/financial_metric_audit.csv")
        result = reconcile(candidates, audits, manifest)
    except (OSError, ValueError, csv.Error) as exc:
        result = {"status": "BLOCKED", "scoring_ready": False,
                  "issues": ["unable to inspect inputs: " + type(exc).__name__]}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 2 if result["status"] == "BLOCKED" else 0

if __name__ == "__main__":
    raise SystemExit(main())
