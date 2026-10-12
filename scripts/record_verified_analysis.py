#!/usr/bin/env python3
"""Validated entry point for recording a 2.3.1 analysis payload.

Requires explicit BUY-block inputs and a numeric, assessed Base-scenario upside.
Usage: python3 scripts/record_verified_analysis.py payload.json [--dry-run]
"""
from __future__ import annotations
import json
import math
import sys
from pathlib import Path
from validate_block_inputs import validate_buy_block_inputs
import record_analysis


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        return 2
    try:
        payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Cannot read input JSON: {exc}", file=sys.stderr)
        return 2

    if not isinstance(payload, dict):
        print("Input payload must be a JSON object", file=sys.stderr)
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

    upside = payload["buy_block_inputs"].get("base_upside_pct")
    try:
        upside_number = float(upside)
        if not math.isfinite(upside_number):
            raise ValueError("not finite")
    except (TypeError, ValueError):
        print(
            "Recording blocked: buy_block_inputs.base_upside_pct must be a finite number. "
            "Assess the Base scenario first; null/unknown must not be treated as passing the +20% BUY block.",
            file=sys.stderr,
        )
        return 2

    # record_analysis parses the same payload path and optional --dry-run from argv.
    return record_analysis.main()


if __name__ == "__main__":
    raise SystemExit(main())
