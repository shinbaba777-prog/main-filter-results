#!/usr/bin/env python3
"""Validate index.csv consistency before publishing the dashboard."""
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "index.csv"
EXPECTED = ["code","company","analysis_date","filter_version","score","stage1","judgment","notes","earnings_date","earnings_text","holding"]
errors = []
with PATH.open("r", encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f)
    if reader.fieldnames != EXPECTED:
        errors.append(f"Header mismatch: expected {EXPECTED}, got {reader.fieldnames}")
    rows = list(reader)
seen = set()
for n, row in enumerate(rows, start=2):
    if None in row:
        errors.append(f"Line {n}: extra columns or malformed CSV")
    code = (row.get("code") or "").strip()
    date = (row.get("analysis_date") or "").strip()
    if not code or not date:
        errors.append(f"Line {n}: code and analysis_date are required")
    key = (code, date, (row.get("filter_version") or "").strip())
    if key in seen:
        errors.append(f"Line {n}: duplicate code/date/filter_version {key}")
    seen.add(key)
    score = (row.get("score") or "").strip()
    judgment = (row.get("judgment") or "").strip()
    if score:
        try:
            value = float(score)
            if not 0 <= value <= 100:
                errors.append(f"Line {n}: score outside 0..100: {score}")
        except ValueError:
            errors.append(f"Line {n}: score is not numeric: {score}")
    if "DATA-INSUFFICIENT" in judgment and score:
        errors.append(f"Line {n}: DATA-INSUFFICIENT must not carry a final numeric score")
    holding = (row.get("holding") or "").strip().lower()
    if holding not in ("true", "false"):
        errors.append(f"Line {n}: holding must be true or false")
if errors:
    print("\n".join(errors), file=sys.stderr)
    sys.exit(1)
print(f"index.csv validation passed: {len(rows)} records")
