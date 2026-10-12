#!/usr/bin/env python3
"""Validate mandatory BUY-block inputs without silently treating unknowns as false.

Use this before scoring/recording. Booleans must be explicitly source-checked;
base_upside_pct may be null only to represent an unassessed scenario and will be
reported as an unresolved block condition by the caller.
"""
from __future__ import annotations

BOOLEAN_KEYS = (
    "shorts_direction_zero",
    "shorts_applicable",
    "ocf_ni_zero",
    "dilution_zero",
    "roic_below_h",
    "roic_unavailable",
    "short_type_a",
    "peg_over_2",
    "industry_per_over_130",
)

def validate_buy_block_inputs(inputs: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(inputs, dict):
        return ["buy_block_inputs must be a JSON object"]
    for key in BOOLEAN_KEYS:
        if key not in inputs:
            errors.append(f"buy_block_inputs.{key} is absent; verify explicitly")
        elif not isinstance(inputs[key], bool):
            errors.append(f"buy_block_inputs.{key} must be true/false after verification")
    if "base_upside_pct" not in inputs:
        errors.append("buy_block_inputs.base_upside_pct is absent; provide a value or explicit null")
    elif inputs["base_upside_pct"] is not None:
        try:
            float(inputs["base_upside_pct"])
        except (TypeError, ValueError):
            errors.append("buy_block_inputs.base_upside_pct must be numeric or null")
    if inputs.get("roic_unavailable") is True and inputs.get("roic_below_h") is True:
        errors.append("ROIC unavailable and ROIC below capital cost cannot both be true")
    return errors
