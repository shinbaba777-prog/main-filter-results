#!/usr/bin/env python3
"""Prepare the record_analysis.py input from source-verified metrics JSON.

Input JSON requires code, company, analysis_date, metrics, buy_block_inputs.
Each metric group must contain source-verified values; omitted groups remain missing.
Usage: python3 scripts/prepare_analysis.py input_metrics.json output_payload.json
"""
import json
import sys
from pathlib import Path
from rubric_scoring import build_items

def main():
    if len(sys.argv) != 3:
        print(__doc__, file=sys.stderr)
        return 2
    try:
        src=json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Input JSON error: {exc}",file=sys.stderr)
        return 2
    for key in ("code","company","analysis_date","metrics","buy_block_inputs"):
        if key not in src:
            print(f"Missing required field: {key}",file=sys.stderr)
            return 2
    result={k:src[k] for k in ("code","company","analysis_date","earnings_date","earnings_text","holding","notes","buy_block_inputs") if k in src}
    result["items"]=build_items(src["metrics"])
    result["filter_version"]="2.3.1"
    Path(sys.argv[2]).write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"Prepared {len(result['items'])} rubric items at {sys.argv[2]}")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
