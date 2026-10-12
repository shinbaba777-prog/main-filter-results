#!/usr/bin/env python3
"""Validated entry point: check BUY-block inputs, then delegate to record_analysis."""
from __future__ import annotations
import json
import sys
from pathlib import Path
from validate_block_inputs import validate_buy_block_inputs
import record_analysis

def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/record_verified_analysis.py payload.json [--dry-run]", file=sys.stderr)
        return 2
    try:
        payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Cannot read input JSON: {exc}", file=sys.stderr)
        return 2
    if "buy_block_inputs" not in payload:
        print("Missing required input field: buy_block_inputs", file=sys.stderr)
        return 2
    errors = validate_buy_block_inputs(payload["buy_block_inputs"])
    if errors:
        print("BUY-block input validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 2
    return record_analysis.main()

if __name__ == "__main__":
    raise SystemExit(main())
