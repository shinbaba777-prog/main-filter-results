#!/usr/bin/env python3
"""Read-only EDINET acquisition gate; never approves investment scoring."""
import json
from pathlib import Path

def assess(manifest, audit, queue, expected_code=None):
    if not isinstance(manifest, dict):
        return {"download_complete": False, "scoring_ready": False, "status": "DATA_INSUFFICIENT"}
    periods = manifest.get("periods")
    count = manifest.get("requested_periods")
    valid = isinstance(periods, list) and isinstance(count, int) and count > 0 and len(periods) == count
    if valid:
        valid = all(isinstance(p, dict) and p.get("status") == "downloaded"
                    and p.get("periodEnd") and p.get("docID") and p.get("file") for p in periods)
    if valid:
        valid = len({p["periodEnd"] for p in periods}) == count and len({p["docID"] for p in periods}) == count
    valid = bool(valid and manifest.get("status") in ("complete", "complete_with_amendments")
                 and manifest.get("gaps") == [] and manifest.get("failed_scan_dates") == []
                 and manifest.get("amendments") == [])
    if expected_code is not None and str(manifest.get("requested_code")) != str(expected_code):
        valid = False
    return {"security_code": manifest.get("requested_code"), "download_complete": valid,
            "scoring_ready": False, "status": "REVIEW_REQUIRED" if valid else "DATA_INSUFFICIENT",
            "audit_available": isinstance(audit, dict), "review_queue_available": isinstance(queue, dict),
            "reason": "All financial facts and external BUY-block inputs require source verification"}

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--code")
    args = parser.parse_args()
    base = args.root / "data" / "edinet"
    def read(path):
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
    result = assess(read(base / "download_manifest.json"),
                    read(base / "extracted/financial_metric_audit_summary.json"),
                    read(base / "extracted/core_metric_review_queue_summary.json"), args.code)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["download_complete"] else 2

if __name__ == "__main__":
    raise SystemExit(main())
