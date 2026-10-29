#!/usr/bin/env python3
"""Score a source-verified analysis payload and append it to index.csv.

Usage:
  python3 scripts/record_analysis.py path/to/analysis.json
  python3 scripts/record_analysis.py path/to/analysis.json --dry-run

The JSON must include code, company, analysis_date, items, buy_block_inputs.
This tool does not fetch financial data or invent missing values. Missing items
must be represented explicitly in the payload and their evidence/source recorded.
"""
from __future__ import annotations
import argparse
import csv
import json
import sys
from pathlib import Path
from scoring_engine import evaluate
from validate_block_inputs import validate_buy_block_inputs

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "index.csv"
FIELDS = ["code", "company", "analysis_date", "filter_version", "score",
          "stage1", "judgment", "notes", "earnings_date", "earnings_text", "holding"]

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("payload", help="JSON input file with source-verified rubric items")
    parser.add_argument("--dry-run", action="store_true", help="print result without changing index.csv")
    parser.add_argument("--index", default=str(CSV_PATH), help="CSV destination (defaults to repository index.csv)")
    args = parser.parse_args()
    index_path = Path(args.index)
    path = Path(args.payload)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Cannot read input JSON: {exc}", file=sys.stderr)
        return 2

    for key in ("code", "company", "analysis_date", "items", "buy_block_inputs"):
        if key not in payload:
            print(f"Missing required input field: {key}", file=sys.stderr)
            return 2

    errors = validate_buy_block_inputs(payload["buy_block_inputs"])
    if errors:
        print("BUY-block input validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 2

    result = evaluate(payload)
    stage1 = result["stage1"]
    stage1_text = (f'{stage1["raw_score"]:g}/80' if not stage1["insufficient"]
                   else "DATA-INSUFFICIENT")
    total = result["total"]
    score_text = "" if result["data_status"] == "DATA-INSUFFICIENT" else f'{total["adjusted_score"]:.1f}'
    notes = payload.get("notes", "")
    if result["buy_blocks"]:
        active = [x["condition"] for x in result["buy_blocks"] if x["active"]]
        if active:
            notes = (notes + "; " if notes else "") + "BUYブロック: " + "、".join(active)
    if result["notices"]:
        notes = (notes + "; " if notes else "") + "／".join(result["notices"])
    if result["data_status"] == "DATA-INSUFFICIENT":
        notes = (notes + "; " if notes else "") + f'欠損配点{total["missing_points"]}点; STAGE1欠損{stage1["missing_points"]}点'
    row = {
        "code": str(payload["code"]).strip(),
        "company": str(payload["company"]).strip(),
        "analysis_date": str(payload["analysis_date"]).strip(),
        "filter_version": "2.3.1",
        "score": score_text,
        "stage1": stage1_text,
        "judgment": result["judgment"],
        "notes": notes,
        "earnings_date": str(payload.get("earnings_date", "") or ""),
        "earnings_text": str(payload.get("earnings_text", "") or ""),
        "holding": "true" if payload.get("holding", False) else "false",
    }
    if not row["code"] or not row["company"] or not row["analysis_date"]:
        print("code/company/analysis_date must not be blank", file=sys.stderr)
        return 2

    existing = []
    if index_path.exists():
        with index_path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames != FIELDS:
                print(f"index.csv header mismatch: {reader.fieldnames}", file=sys.stderr)
                return 2
            existing = list(reader)
    duplicate = next((r for r in existing if
                      r.get("code") == row["code"] and
                      r.get("analysis_date") == row["analysis_date"] and
                      r.get("filter_version") == row["filter_version"]), None)
    if duplicate:
        print("Duplicate code/date/filter_version exists; refusing to overwrite.", file=sys.stderr)
        return 3

    output = {"record": row, "scoring": result}
    print(json.dumps(output, ensure_ascii=False, indent=2))
    if not args.dry_run:
        index_path.parent.mkdir(parents=True, exist_ok=True)
        with index_path.open("a", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS, lineterminator="\n")
            if not existing and index_path.stat().st_size == 0:
                writer.writeheader()
            writer.writerow(row)
        print(f"Appended to {index_path}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
