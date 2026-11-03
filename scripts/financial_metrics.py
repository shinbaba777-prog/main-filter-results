#!/usr/bin/env python3
"""Pure calculations for Main Filter 2.3.1 from source-verified statement values.

Amounts must use one currency/unit consistently. Series are oldest-to-newest.
This module does not fetch filings, guess missing figures, or assign rubric points.
"""
from __future__ import annotations
from typing import Optional, Sequence

def safe_ratio(numerator: Optional[float], denominator: Optional[float]) -> Optional[float]:
    if numerator is None or denominator is None or denominator == 0:
        return None
    return numerator / denominator

def cagr(start: Optional[float], end: Optional[float], years: int) -> Optional[float]:
    """CAGR only when both start and end are positive (spec 2.3.1: 始点・終点ともプラス).

    A nonpositive start or end returns None; it is never adjusted or replaced.
    """
    if start is None or end is None or years <= 0 or start <= 0 or end <= 0:
        return None
    return (end / start) ** (1 / years) - 1


# Reporting basis of an annual value. A CAGR window must not mix bases.
BASES = ("consolidated", "standalone")


def basis_consistent_cagr(values: Sequence[Optional[float]], bases: Sequence[Optional[str]],
                          years: int) -> tuple[Optional[float], str]:
    """CAGR over the last `years` intervals of an oldest-to-newest series.

    Returns (value, reason). reason is "" when computed, otherwise one of:
      "insufficient_periods"  fewer than years+1 values
      "missing_value"         start or end value is None
      "basis_unknown"         a basis inside the window is None/invalid
      "basis_change"          the window mixes consolidated and standalone
                              (連結切替: the CAGR is held, never spliced)
      "nonpositive"           start or end is not positive
    Only "nonpositive" may feed the spec's uncomputable-CAGR fallback; the other
    reasons are a data hold and must be scored as missing.
    """
    if years <= 0 or len(values) < years + 1 or len(bases) != len(values):
        return None, "insufficient_periods"
    window_values = list(values[-(years + 1):])
    window_bases = list(bases[-(years + 1):])
    if any(b not in BASES for b in window_bases):
        return None, "basis_unknown"
    if len(set(window_bases)) > 1:
        return None, "basis_change"
    start, end = window_values[0], window_values[-1]
    if start is None or end is None:
        return None, "missing_value"
    if start <= 0 or end <= 0:
        return None, "nonpositive"
    return cagr(start, end, years), ""

def yoy(current: Optional[float], previous: Optional[float]) -> Optional[float]:
    if current is None or previous is None or previous <= 0:
        return None
    return current / previous - 1

def margins(revenue: Sequence[Optional[float]], profit: Sequence[Optional[float]]) -> list[Optional[float]]:
    return [safe_ratio(p, r) for r, p in zip(revenue, profit)]

def margin_deltas(values: Sequence[Optional[float]]) -> list[Optional[float]]:
    return [None if a is None or b is None else b-a for a,b in zip(values, values[1:])]

def roa(net_income: Optional[float], assets_start: Optional[float], assets_end: Optional[float]) -> Optional[float]:
    if net_income is None or assets_start is None or assets_end is None:
        return None
    avg=(assets_start+assets_end)/2
    return safe_ratio(net_income,avg)

def equity_ratio(equity: Optional[float], assets: Optional[float]) -> Optional[float]:
    return safe_ratio(equity,assets)

def net_debt_ebitda(interest_bearing_debt: Optional[float], cash_and_equivalents: Optional[float], ebitda: Optional[float]) -> Optional[float]:
    if interest_bearing_debt is None or cash_and_equivalents is None or ebitda is None or ebitda <= 0:
        return None
    return (interest_bearing_debt-cash_and_equivalents)/ebitda

def fcf(operating_cash_flow: Optional[float], investing_cash_flow: Optional[float]) -> Optional[float]:
    if operating_cash_flow is None or investing_cash_flow is None:
        return None
    return operating_cash_flow+investing_cash_flow

def ocf_ni_ratio(ocf_series: Sequence[Optional[float]], ni_series: Sequence[Optional[float]]) -> Optional[float]:
    if len(ocf_series)<3 or len(ni_series)<3 or any(x is None for x in ocf_series[-3:]) or any(x is None for x in ni_series[-3:]):
        return None
    return safe_ratio(sum(ocf_series[-3:]),sum(ni_series[-3:]))

def net_shares(issued: Optional[float], treasury: Optional[float]) -> Optional[float]:
    """Issued shares minus treasury shares (both at the same date).

    A missing treasury count is not treated as zero: the caller must supply an
    explicitly verified 0 when the filing confirms there are no treasury shares.
    """
    if issued is None or treasury is None or issued <= 0 or treasury < 0 or treasury > issued:
        return None
    return issued - treasury


def split_adjusted_net_shares(issued: Optional[float], treasury: Optional[float],
                              split_factor: Optional[float]) -> Optional[float]:
    """Net shares restated to the latest share basis.

    split_factor = cumulative split ratio between this date and the latest date
    (e.g. a later 1:2 split -> 2.0; a later 2:1 consolidation -> 0.5; none -> 1.0).
    """
    shares = net_shares(issued, treasury)
    if shares is None or split_factor is None or split_factor <= 0:
        return None
    return shares * split_factor


def split_adjusted_per_share(value: Optional[float], split_factor: Optional[float]) -> Optional[float]:
    """Restate a per-share value (EPS, BPS) to the latest share basis."""
    if value is None or split_factor is None or split_factor <= 0:
        return None
    return value / split_factor


def share_count_increase(adjusted_net_shares_start: Optional[float], adjusted_net_shares_end: Optional[float]) -> Optional[float]:
    if adjusted_net_shares_start is None or adjusted_net_shares_end is None or adjusted_net_shares_start <= 0:
        return None
    return adjusted_net_shares_end/adjusted_net_shares_start-1

def fcf_yield(fcf_value: Optional[float], market_cap: Optional[float]) -> Optional[float]:
    return safe_ratio(fcf_value,market_cap)

def incremental_roic(nopat_old: Optional[float], nopat_new: Optional[float], invested_capital_old: Optional[float], invested_capital_new: Optional[float]) -> Optional[float]:
    """Specified 3-year incremental ROIC; a nonpositive denominator is handled separately."""
    if None in (nopat_old,nopat_new,invested_capital_old,invested_capital_new):
        return None
    delta_capital=invested_capital_new-invested_capital_old
    if delta_capital <= 0:
        return None
    return (nopat_new-nopat_old)/delta_capital
