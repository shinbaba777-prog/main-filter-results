#!/usr/bin/env python3
"""Safely gate source-verified metrics before invoking existing scoring scripts.

This tool never edits index.csv or runs official scoring. Input is a JSON
document with `metrics`, `buy_block_inputs`, and `verified_sources`.
Each non-null metric requires an explicit citation in verified_sources.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from check_edinet_readiness import assess
from validate_block_inputs import validate_buy_block_inputs

REQUIRED_GROUPS = (
    "growth", "profitability", "roic_capital", "finance_cf",
    "eps_growth", "valuation", "competitive_advantage",
    "subsidiaries_ma", "shorts_supply", "ir_reaction",
)

def validate(payload, manifest, audit, queue):
    problems = []
    if not isinstance(payload, dict):
        return ["payload must be a JSON object"]
    code = payload.get("code")
    gate = assess(manifest, audit, queue, code)
    if not gate["download_complete"]:
        problems.append("EDINET download gate is incomplete")
    if not isinstance(code, str) or not code:
        problems.append("security code missing")
    for field in ("company", "analysis_date"):
        if not isinstance(payload.get(field), str) or not payload[field]:
            problems.append(field + " missing")
    metrics = payload.get("metrics")
    sources = payload.get("verified_sources")
    if not isinstance(metrics, dict):
        problems.append("metrics must be an object")
        metrics = {}
    if not isinstance(sources, dict):
        problems.append("verified_sources must be an object")
        sources = {}
    for group in REQUIRED_GROUPS:
        values = metrics.get(group)
        if not isinstance(values, dict):
            problems.append("metric group missing: " + group)
            continue
        for key, value in values.items():
            if key.endswith("_source") or value is None:
                continue
            # False and empty collections can be unverified defaults too.
            citation = sources.get(group + "." + key)
            if not isinstance(citation, str) or not citation.strip():
                problems.append("unverified metric: " + group + "." + key)
    problems.extend(validate_buy_block_inputs(payload.get("buy_block_inputs")))
    for key in ("shorts_direction_zero", "shorts_applicable", "ocf_ni_zero",
                "dilution_zero", "roic_below_h", "roic_unavailable",
                "short_type_a", "peg_over_2", "industry_per_over_130",
                "base_upside_pct"):
        if not isinstance(sources.get("buy_block_inputs." + key), str) or not sources["buy_block_inputs." + key].strip():
            problems.append("unverified BUY-block input: " + key)
    return problems

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    try:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
        base = args.root / "data" / "edinet"
        def read(path):
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                return None
        problems = validate(payload, read(base / "download_manifest.json"),
                            read(base / "extracted/financial_metric_audit_summary.json"),
                            read(base / "extracted/core_metric_review_queue_summary.json"))
    except (OSError, ValueError) as exc:
        problems = ["invalid input: " + str(exc)]
    print(json.dumps({"status": "BLOCKED" if problems else "READY_FOR_EXISTING_PREPARE_ANALYSIS",
                      "issues": problems}, ensure_ascii=False, indent=2))
    return 2 if problems else 0

if __name__ == "__main__":
    raise SystemExit(main())
