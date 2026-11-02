#!/usr/bin/env python3
"""Validate mandatory BUY-block inputs without silently treating unknowns as false.

Use this before scoring/recording. Booleans must be explicitly source-checked;
base_upside_pct must be a finite numeric value so the +20% BUY-block condition
cannot silently pass while the Base scenario remains unassessed.
"""
from __future__ import annotations

STRICT_BOOLEAN_KEYS = (
    "shorts_direction_zero",
    "shorts_applicable",
    "ocf_ni_zero",
    "dilution_zero",
    "roic_below_h",
    "roic_unavailable",
    "short_type_a",
)
TRISTATE_BOOLEAN_KEYS = ("peg_over_2", "industry_per_over_130")

def validate_buy_block_inputs(inputs: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(inputs, dict):
        return ["buy_block_inputs must be a JSON object"]
    for key in STRICT_BOOLEAN_KEYS:
        if key not in inputs:
            errors.append(f"buy_block_inputs.{key} is absent; verify explicitly")
        elif not isinstance(inputs[key], bool):
            errors.append(f"buy_block_inputs.{key} must be true/false after verification")
    # Explicit null is permitted for these conditions only; absent keys are not.
    for key in TRISTATE_BOOLEAN_KEYS:
        if key not in inputs:
            errors.append(f"buy_block_inputs.{key} is absent; verify explicitly")
        elif inputs[key] is not None and not isinstance(inputs[key], bool):
            errors.append(f"buy_block_inputs.{key} must be true/false/null")

    if "base_upside_pct" not in inputs:
        errors.append("buy_block_inputs.base_upside_pct is absent; provide a finite numeric value")
    else:
        try:
            import math
            if isinstance(inputs["base_upside_pct"], bool):
                raise ValueError("boolean is not a numeric upside")
            value = float(inputs["base_upside_pct"])
            if not math.isfinite(value):
                raise ValueError("not finite")
        except (TypeError, ValueError):
            errors.append("buy_block_inputs.base_upside_pct must be a finite number; assess the Base scenario before scoring")
    if inputs.get("roic_unavailable") is True and inputs.get("roic_below_h") is True:
        errors.append("ROIC unavailable and ROIC below capital cost cannot both be true")
    return errors
