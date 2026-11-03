#!/usr/bin/env python3
"""Build 5-1 / 5-5 / 5-4(dilution) metric inputs from verified annual rows.

Input rows are oldest-to-newest dicts holding source-verified values:
  fiscal_year, basis ("consolidated"|"standalone"), revenue, operating_income,
  eps (as reported), split_factor (cumulative ratio to the latest share basis,
  1.0 when none), shares_issued_fye, treasury_shares_fye, source.

Rules (canonical rev93):
  * CAGR is computed only inside one reporting basis; a window that contains a
    consolidated/standalone switch (連結切替) is held as missing with the reason
    recorded, never spliced and never sent to the nonpositive-CAGR fallback.
  * Long CAGR (5 periods = 4 intervals) falls back to the 3-year CAGR when the
    long window is unavailable, as the spec allows; the substitution is noted.
  * EPS is split-adjusted to the latest share basis before any comparison.
  * Dilution uses (issued - treasury) at fiscal year end, split-adjusted,
    t vs t-3. A missing treasury count is not assumed to be zero.
  * YoY is computed only when both years share a basis.
No value is estimated; anything not computable stays None with a reason.
"""
from __future__ import annotations

from typing import Any, Optional

from financial_metrics import (basis_consistent_cagr, share_count_increase,
                               split_adjusted_net_shares, split_adjusted_per_share, yoy)


def _series(rows: list[dict], key: str) -> list[Optional[float]]:
    return [r.get(key) for r in rows]


def _yoy_same_basis(rows: list[dict], key: str, values: list[Optional[float]]) -> tuple[Optional[float], str]:
    if len(rows) < 2:
        return None, "insufficient_periods"
    if rows[-1].get("basis") != rows[-2].get("basis"):
        return None, "basis_change"
    value = yoy(values[-1], values[-2])
    return value, "" if value is not None else "missing_value"


def _cagr_with_fallback(values, bases, out: dict, long_key: str, short_key: Optional[str]) -> None:
    long_value, long_reason = basis_consistent_cagr(values, bases, 4)
    short_value, short_reason = basis_consistent_cagr(values, bases, 3)
    note = ""
    if long_value is None and long_reason != "nonpositive" and short_value is not None:
        # Spec: 長期CAGRは3年CAGRで代替し明記
        long_value, long_reason, note = short_value, "", "長期CAGRは3年CAGRで代替"
    out[long_key] = long_value
    if long_reason:
        out[long_key + "_hold_reason"] = long_reason
    if note:
        out[long_key + "_note"] = note
    if short_key:
        out[short_key] = short_value
        if short_reason:
            out[short_key + "_hold_reason"] = short_reason


def build_series_metrics(rows: list[dict]) -> dict[str, Any]:
    if len(rows) < 2:
        raise ValueError("at least two annual rows are required")
    bases = [r.get("basis") for r in rows]
    growth: dict[str, Any] = {}
    eps: dict[str, Any] = {}

    revenue = _series(rows, "revenue")
    _cagr_with_fallback(revenue, bases, growth, "sales_long_cagr", "sales_3y_cagr")
    growth["sales_yoy"], reason = _yoy_same_basis(rows, "revenue", revenue)
    if reason:
        growth["sales_yoy_hold_reason"] = reason

    op = _series(rows, "operating_income")
    _cagr_with_fallback(op, bases, growth, "operating_profit_long_cagr", None)
    if growth.get("operating_profit_long_cagr_hold_reason") == "nonpositive":
        growth["operating_profit_cagr_uncomputable"] = True
        growth["latest_operating_profit_positive"] = (op[-1] or 0) > 0

    adjusted_eps = [split_adjusted_per_share(r.get("eps"), r.get("split_factor")) for r in rows]
    eps["adjusted_eps_series"] = adjusted_eps
    _cagr_with_fallback(adjusted_eps, bases, eps, "eps_long_cagr", None)
    if eps.get("eps_long_cagr_hold_reason") == "nonpositive":
        eps["eps_long_cagr_uncomputable"] = True
        eps["latest_eps_positive"] = (adjusted_eps[-1] or 0) > 0
    eps["eps_yoy"], reason = _yoy_same_basis(rows, "eps", adjusted_eps)
    if reason:
        eps["eps_yoy_hold_reason"] = reason

    dilution: dict[str, Any] = {"share_count_increase_3y": None}
    if len(rows) >= 4:
        start, end = rows[-4], rows[-1]
        s = split_adjusted_net_shares(start.get("shares_issued_fye"), start.get("treasury_shares_fye"),
                                      start.get("split_factor"))
        e = split_adjusted_net_shares(end.get("shares_issued_fye"), end.get("treasury_shares_fye"),
                                      end.get("split_factor"))
        dilution.update(share_count_increase_3y=share_count_increase(s, e),
                        net_shares_start=s, net_shares_end=e,
                        window=(start.get("fiscal_year"), end.get("fiscal_year")))
        if s is None or e is None:
            dilution["hold_reason"] = "発行済株式数または自己株式数（期末）が未確認"
    return {"growth": growth, "eps_growth": eps, "dilution": dilution}
