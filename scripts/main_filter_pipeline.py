#!/usr/bin/env python3
"""Orchestrate the safe Main Filter 2.3.1 data-to-judgment pipeline.

This stage creates a deterministic readiness report. It never approves EDINET
facts, invents market inputs, scores an unverified company, or writes index.csv.
"""
from __future__ import annotations
import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EDINET = ROOT / "data" / "edinet"
EXTRACTED = EDINET / "extracted"


def read_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def csv_count(path: Path) -> int:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            return max(0, sum(1 for _ in csv.DictReader(f)))
    except OSError:
        return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--code", required=True, help="Japanese security code")
    ap.add_argument("--company", default="", help="Company name if known")
    ap.add_argument("--out", default="data/edinet/pipeline_readiness.json")
    args = ap.parse_args()

    manifest = read_json(EDINET / "download_manifest.json")
    extraction = read_json(EXTRACTED / "extraction_summary.json")
    audit = read_json(EXTRACTED / "financial_metric_audit_summary.json")
    core = read_json(EXTRACTED / "core_metric_review_queue_summary.json")
    annual = read_json(EXTRACTED / "annual_metrics_review_summary.json")

    manifest_code = str(manifest.get("requested_code") or manifest.get("security_code") or "")
    periods = manifest.get("periods", [])
    periods = periods if isinstance(periods, list) else []
    relevant = [p for p in periods if str(p.get("security_code") or p.get("code") or args.code) in ("", args.code)]
    downloaded = [p for p in relevant if p.get("status") == "downloaded" and p.get("file")]
    gaps = manifest.get("gaps", []) or []
    failed_dates = manifest.get("failed_scan_dates", []) or []\n    missing_periods = manifest.get("missing_expected_periods", []) or []
    expected = manifest.get("expected_periods", manifest.get("fiscal_periods", [])) or []\n    requested_periods = int(manifest.get("requested_periods") or 0)\n    if not expected and periods:\n        expected = periods
    candidate_rows = csv_count(EXTRACTED / "financial_metric_candidates.csv")
    audit_rows = csv_count(EXTRACTED / "financial_metric_audit.csv")
    queue_rows = csv_count(EXTRACTED / "core_metric_review_queue.csv")
    approved_rows = 0
    queue = EXTRACTED / "core_metric_review_queue.csv"
    try:
        with queue.open("r", encoding="utf-8-sig", newline="") as f:
            approved_rows = sum(1 for row in csv.DictReader(f)
                                if str(row.get("review_status", "")).strip().upper() == "APPROVED"
                                and str(row.get("review_reason", "")).strip() == "APPROVED_SOURCE_VERIFIED")
    except OSError:
        pass

    blockers = []
    if manifest.get("status") not in ("complete", "complete_short_history", "complete_with_amendments"):
        blockers.append("EDINET manifest is not complete")
    if gaps:
        blockers.append("Expected fiscal periods have gaps")
    if failed_dates:
        blockers.append("EDINET scan dates failed; zero-result is not proof of no filing")
    if requested_periods and len(downloaded) < requested_periods and manifest.get("status") != "complete_short_history":
        blockers.append("Expected annual filing count is not satisfied")
    if not downloaded:
        blockers.append("No downloaded annual filing is recorded in the manifest")
    if not (EXTRACTED / "financial_metric_candidates.csv").exists():
        blockers.append("Financial candidate extraction is missing")
    if not (EXTRACTED / "financial_metric_audit.csv").exists():
        blockers.append("Candidate audit is missing")
    if approved_rows == 0:
        blockers.append("No facts have been explicitly source-verified and approved")
    blockers.extend([
        "Market price/PER and same-market/industry benchmark are not independently verified by this pipeline",
        "JPX institutional short history and five-business-day IR excess return are not verified by this pipeline",
        "ROIC/WACC, net debt/EBITDA, dilution, forecast/scenario and BUY-block inputs require verified calculations",
    ])

    status = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "security_code": args.code,
        "company": args.company,
        "pipeline_stage": "DATA_COLLECTION_AND_JUDGMENT_READINESS",
        "source_manifest_status": manifest.get("status", "MISSING"),
        "manifest_code": manifest_code,
        "downloaded_period_count": len(downloaded),
        "expected_period_count": len(expected) if isinstance(expected, list) else 0,
        "gap_count": len(gaps),
        "failed_scan_date_count": len(failed_dates),\n        "missing_expected_periods": missing_periods,
        "extraction_summary_present": bool(extraction),
        "candidate_rows": candidate_rows,
        "audit_rows": audit_rows,
        "review_queue_rows": queue_rows,
        "explicitly_source_verified_approved_rows": approved_rows,
        "readiness": "READY_FOR_MANUAL_SOURCE_RECONCILIATION" if approved_rows else "BLOCKED_DATA_REVIEW_REQUIRED",
        "formal_scoring_allowed": False,
        "index_csv_write_allowed": False,
        "blockers": blockers,
        "required_next_steps": [
            "Resolve all manifest gaps and failed scan dates; confirm all expected fiscal periods and amendments.",
            "Verify each metric against the original filing: fiscal year, consolidated scope, accounting standard, duration/instant, unit and scale, sign, concept definition, and corrections.",
            "Only then mark the exact queue row APPROVED with review_reason=APPROVED_SOURCE_VERIFIED.",
            "Independently collect and verify price/PER, sector benchmarks, JPX short positions, IR/index reaction, ROIC/WACC, net debt, dilution, forecast and scenario inputs.",
            "Run prepare_analysis.py and record_verified_analysis.py --dry-run; inspect scoring and BUY blocks before any formal record.",
            "Only after review, record the approved analysis and verify index.csv plus Pages deployment."
        ],
    }
    out = ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md = out.with_suffix(".md")
    md.write_text(
        "# Main Filter 2.3.1 pipeline readiness\n\n"
        f"- Code: {args.code} {args.company}\n"
        f"- Generated (UTC): {status['generated_at_utc']}\n"
        f"- EDINET manifest: {status['source_manifest_status']}\n"
        f"- Downloaded annual periods: {len(downloaded)}; expected periods listed: {len(expected) if isinstance(expected, list) else 0}\n"
        f"- Candidate/audit/review rows: {candidate_rows}/{audit_rows}/{queue_rows}\n"
        f"- Explicitly source-verified approved facts: {approved_rows}\n"
        f"- Readiness: **{status['readiness']}**\n"
        "- Formal scoring allowed: **NO**\n"
        "- index.csv write allowed: **NO**\n\n"
        "## Blockers\n" + "".join(f"- {x}\n" for x in blockers) + "\n"
        "## Required next steps\n" + "".join(f"{i}. {x}\n" for i, x in enumerate(status["required_next_steps"], 1)),
        encoding="utf-8"
    )
    print(json.dumps({"readiness": status["readiness"], "candidate_rows": candidate_rows,
                      "approved_rows": approved_rows, "blockers": len(blockers),
                      "json": str(out), "markdown": str(md)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
