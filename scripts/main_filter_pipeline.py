#!/usr/bin/env python3
"""Conservative readiness gate for Main Filter 2.3.1."""
import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "edinet"
EXTRACTED = DATA / "extracted"


def load_json(path):
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def load_csv(path):
    try:
        with path.open(encoding="utf-8-sig", newline="") as stream:
            return list(csv.DictReader(stream))
    except OSError:
        return []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--code", required=True)
    ap.add_argument("--company", default="")
    ap.add_argument("--out", default="data/edinet/pipeline_readiness.json")
    args = ap.parse_args()
    manifest = load_json(DATA / "download_manifest.json")
    periods = manifest.get("periods", [])
    periods = periods if isinstance(periods, list) else []
    downloaded = [p for p in periods if p.get("status") == "downloaded" and p.get("file")]
    expected = manifest.get("expected_periods", manifest.get("fiscal_periods", [])) or periods
    gaps = manifest.get("gaps", []) or []
    failed = manifest.get("failed_scan_dates", []) or []
    missing = manifest.get("missing_expected_periods", []) or []
    amendments = manifest.get("amendments", []) or []
    candidates = load_csv(EXTRACTED / "financial_metric_candidates.csv")
    audits = load_csv(EXTRACTED / "financial_metric_audit.csv")
    queue = load_csv(EXTRACTED / "core_metric_review_queue.csv")
    approved = [r for r in queue if r.get("review_status", "").strip().upper() == "APPROVED"
                and r.get("review_reason", "").strip() == "APPROVED_SOURCE_VERIFIED"]
    blockers = []
    manifest_status = manifest.get("status", "MISSING")
    if manifest_status not in ("complete", "complete_short_history", "complete_with_amendments"):
        blockers.append("EDINET manifest is not complete")
    if gaps or missing:
        blockers.append("Expected fiscal periods have gaps")
    if failed:
        blockers.append("Some EDINET scan dates failed")
    requested = manifest.get("requested_periods")
    if requested is not None and manifest_status != "complete_short_history":
        try:
            if len(downloaded) < int(requested):
                blockers.append("Expected annual filing count is not satisfied")
        except (ValueError, TypeError):
            blockers.append("Requested annual filing count is invalid")
    if not downloaded:
        blockers.append("No downloaded annual filings")
    if not candidates or not audits or not queue:
        blockers.append("Candidate extraction, audit, or review queue is missing/empty")
    if amendments:
        blockers.append("Amendments require reconciliation against original filings")
    if not approved:
        blockers.append("No source-verified facts have been approved")
    blockers.extend([
        "Price/PER and market/industry benchmarks still need verified inputs",
        "JPX short positions and five-business-day IR excess returns still need verified inputs",
        "ROIC/WACC, net debt/EBITDA, dilution, forecast and scenario checks still need verified inputs",
    ])
    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "security_code": args.code, "company": args.company,
        "manifest_status": manifest_status,
        "downloaded_period_count": len(downloaded),
        "expected_period_count": len(expected) if isinstance(expected, list) else 0,
        "gap_count": len(gaps), "failed_scan_date_count": len(failed),
        "missing_expected_periods": missing, "amendment_count": len(amendments),
        "candidate_rows": len(candidates), "audit_rows": len(audits),
        "review_queue_rows": len(queue), "approved_rows": len(approved),
        "readiness": "BLOCKED_DATA_REVIEW_REQUIRED",
        "formal_scoring_allowed": False, "index_csv_write_allowed": False,
        "blockers": blockers,
    }
    out = ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md = ["# Main Filter 2.3.1 pipeline readiness", "",
          f"- Code: {args.code} {args.company}",
          f"- EDINET manifest: {manifest_status}",
          f"- Periods downloaded: {len(downloaded)}",
          f"- Candidate/audit/queue rows: {len(candidates)}/{len(audits)}/{len(queue)}",
          f"- Approved source-verified facts: {len(approved)}",
          "- Formal scoring allowed: NO", "- index.csv write allowed: NO", "",
          "## Blockers", *[f"- {x}" for x in blockers], ""]
    out.with_suffix(".md").write_text("\n".join(md), encoding="utf-8")
    print(json.dumps({"readiness": report["readiness"], "blockers": len(blockers),
                      "downloaded_periods": len(downloaded)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
