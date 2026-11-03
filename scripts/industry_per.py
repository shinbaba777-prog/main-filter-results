#!/usr/bin/env python3
"""JPX industry simple-PER selection for Main Filter 2.3.1 (canonical rev93).

Implements the approved fallback order (2026-10-29 addendum, "業種平均PERの代替順位"
and 仕様確定事項①②⑨):

  ① same market, same 33-industry simple PER (>=10 companies, valid value)
  ② all three markets, same 33-industry, recombined exactly:
       price_total  = simple PER x simple EPS x companies   (per market)
       profit_total = simple EPS x companies                (per market)
       PER = sum(price_total) / sum(profit_total), rounded to 1 decimal
     usable only if combined companies >= 10, profit_total > 0, the file has the
     simple-EPS column, and every market with companies > 0 has a numeric PER/EPS
     (otherwise the sum cannot be reconstructed exactly). No simple or
     company-weighted averaging of market PERs.
  ③ same market, overall simple PER
  ④ 4-9 scenarios only: conservative reference PER 15x, capped by the company's
     own 5-period median actual PER when supplied (2026-10-05 addendum)

Special values: "－" and 1-9 companies fall back normally; 0 companies falls back
when no valid PER is shown. "＊" (>=1000x) is handled independently: 5-6 scoring
-> missing, 4-9 -> min(15, own median), buy range C -> not computable.
Freshness: STALE / INVALID files are treated as not obtained. CURRENT_BY_CALENDAR
and UNKNOWN are usable but flagged provisional.

The Nikkei average PER is never an input here (reference display only).
This module selects and records; it never fetches files or estimates values.
"""
from __future__ import annotations

import math
from datetime import date
from typing import Any, Optional

MARKETS = ("prime", "standard", "growth")
MARKET_LABELS = {"prime": "プライム", "standard": "スタンダード", "growth": "グロース"}
PURPOSES = ("scoring", "scenario", "buy_range_c")
FRESHNESS = ("CONFIRMED_CURRENT", "CURRENT_BY_CALENDAR", "UNKNOWN", "STALE", "INVALID")
USABLE_FRESHNESS = ("CONFIRMED_CURRENT", "CURRENT_BY_CALENDAR", "UNKNOWN")
DASH = ("－", "-", "—", "ー")
ASTERISK = ("＊", "*")
MIN_COMPANIES = 10
CONSERVATIVE_PER = 15.0
TIER_LABELS = {
    1: "①同一市場・同一業種の単純PER",
    2: "②全市場・同一業種の合算単純PER",
    3: "③同一市場の総合単純PER",
    4: "④保守参考PER（4-9のみ）",
}
# Tier-② companies show the old method (③) as a reference for 3 months after adoption.
TIER2_REFERENCE_UNTIL = date(2027, 1, 29)


def _numeric(value: Any) -> Optional[float]:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, str):
        stripped = value.strip().replace(",", "")
        if stripped in DASH or stripped in ASTERISK or stripped == "":
            return None
        try:
            value = float(stripped)
        except ValueError:
            return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _is_asterisk(value: Any) -> bool:
    return isinstance(value, str) and value.strip() in ASTERISK


def _companies(row: Optional[dict]) -> Optional[int]:
    if not row:
        return None
    n = row.get("companies")
    if isinstance(n, bool) or n is None:
        return None
    try:
        return int(n)
    except (TypeError, ValueError):
        return None


def _scenario_conservative(own_median: Optional[float]) -> tuple[float, str]:
    median = _numeric(own_median)
    if median is not None and median > 0 and median < CONSERVATIVE_PER:
        return median, f"保守参考PER15倍を自社過去5期実績PER中央値{median:g}倍で上限"
    return CONSERVATIVE_PER, "保守参考PER15倍（成長係数なし）"


def _tier2(rows: dict, eps_column_available: bool) -> tuple[Optional[float], int, str]:
    if not eps_column_available:
        return None, 0, "JPXファイルに1株当たり当期純利益（単純）の列が無い"
    price_total = 0.0
    profit_total = 0.0
    companies_total = 0
    for market in MARKETS:
        row = rows.get(market)
        n = _companies(row)
        if n is None:
            return None, 0, f"{MARKET_LABELS[market]}の社数が未取得"
        if n == 0:
            continue
        per = _numeric(row.get("simple_per"))
        eps = _numeric(row.get("eps_simple"))
        if per is None or eps is None:
            return None, 0, f"{MARKET_LABELS[market]}のPERまたはEPSが数値でなく正確に合算できない"
        price_total += per * eps * n
        profit_total += eps * n
        companies_total += n
    if companies_total < MIN_COMPANIES:
        return None, companies_total, f"合算社数{companies_total}社（10社未満）"
    if profit_total <= 0:
        return None, companies_total, "利益合計がプラスでない"
    return round(price_total / profit_total, 1), companies_total, ""


def select_industry_per(*, market: str, industry: str, rows: dict, market_total_simple_per: Any,
                        purpose: str, publication_month: str, freshness: str,
                        eps_column_available: bool, source: str,
                        own_past_per_median: Optional[float] = None,
                        analysis_date: Optional[str] = None) -> dict:
    """Return a selection record (value, tier, companies, method, fallback trail).

    rows: {market: {"simple_per": number|"－"|"＊"|None, "eps_simple": number|None,
                    "companies": int|None}} for the target 33-industry.
    purpose: "scoring" (5-6, 4-4), "scenario" (4-9), "buy_range_c".
    """
    if market not in MARKETS:
        raise ValueError(f"market must be one of {MARKETS}")
    if purpose not in PURPOSES:
        raise ValueError(f"purpose must be one of {PURPOSES}")
    if freshness not in FRESHNESS:
        raise ValueError(f"freshness must be one of {FRESHNESS}")
    if not source:
        raise ValueError("source (JPX file name/URL) is required")
    record: dict[str, Any] = {
        "market": market, "industry": industry, "purpose": purpose,
        "publication_month": publication_month, "freshness": freshness,
        "provisional": freshness in ("CURRENT_BY_CALENDAR", "UNKNOWN"),
        "source": source, "status": "UNAVAILABLE", "tier": None, "tier_label": "",
        "value": None, "companies": None, "method": "", "fallback_trail": [],
        "old_method_reference": None, "notes": [],
    }
    trail = record["fallback_trail"]

    def finish(status: str, tier: Optional[int], value: Optional[float],
               companies: Optional[int], method: str) -> dict:
        record.update(status=status, tier=tier, tier_label=TIER_LABELS.get(tier, ""),
                      value=value, companies=companies, method=method)
        return record

    def conservative_or_unavailable(reason: str) -> dict:
        trail.append(reason)
        if purpose == "scenario":
            value, method = _scenario_conservative(own_past_per_median)
            return finish("SELECTED", 4, value, None, method)
        return finish("UNAVAILABLE", None, None, None,
                      "業種PERなし：5-6は欠損、買いレンジCは算定不能")

    if freshness not in USABLE_FRESHNESS:
        return conservative_or_unavailable(f"JPXファイルが{freshness}のため未取得扱い")
    if record["provisional"]:
        record["notes"].append(f"最新性{freshness}：暫定扱い")

    own = rows.get(market) or {}
    n_own = _companies(own)
    raw_per = own.get("simple_per")
    per_own = _numeric(raw_per)
    if n_own is not None and n_own >= MIN_COMPANIES and _is_asterisk(raw_per):
        record["notes"].append("「＊」（1000倍以上）：独立管理")
        if purpose == "scenario":
            value, method = _scenario_conservative(own_past_per_median)
            return finish("SPECIAL_ASTERISK", 4, value, n_own, "「＊」のため" + method)
        return finish("SPECIAL_ASTERISK", None, None, n_own,
                      "「＊」のため5-6業種相対PERは欠損、買いレンジCは算定不能")
    if n_own is not None and n_own >= MIN_COMPANIES and per_own is not None and per_own > 0:
        return finish("SELECTED", 1, per_own, n_own, "JPX公表値をそのまま使用")
    if n_own is None:
        trail.append("①社数が未取得")
    elif n_own < MIN_COMPANIES:
        trail.append(f"①社数{n_own}社（10社未満）")
    else:
        trail.append(f"①PERが有効値でない（{raw_per!r}）")

    value2, n2, why2 = _tier2(rows, eps_column_available)
    if value2 is not None:
        record["notes"].append("②は株価合計ベースのため値がさ株の多い市場（通常プライム）の影響が大きい")
        old = _numeric(market_total_simple_per)
        within = True
        if analysis_date:
            within = date.fromisoformat(analysis_date) <= TIER2_REFERENCE_UNTIL
        if within:
            record["old_method_reference"] = old
            if old is None:
                record["notes"].append("旧方式（同一市場の総合単純PER）は未取得")
        return finish("SELECTED", 2, value2, n2,
                      "3市場の株価合計÷利益合計で再計算（単純平均・社数加重平均は不使用）")
    trail.append("②" + why2)

    total = _numeric(market_total_simple_per)
    if total is not None and total > 0:
        return finish("SELECTED", 3, total, None, "同一市場の総合単純PER")
    trail.append(f"③同一市場の総合単純PERが有効値でない（{market_total_simple_per!r}）")
    return conservative_or_unavailable("④へ")


def describe_selection(record: dict) -> str:
    """One-line record text for index.csv notes / report body."""
    month = record.get("publication_month", "")
    fresh = record.get("freshness", "")
    if record.get("status") == "SPECIAL_ASTERISK" and record.get("value") is None:
        return f"業種PER:「＊」（{month}公表、{fresh}）→5-6欠損"
    if record.get("value") is None:
        return f"業種PER: 取得不能（{month}公表、{fresh}）"
    count = f"、社数{record['companies']}" if record.get("companies") is not None else ""
    text = f"業種PER:{record.get('tier_label')} {record['value']:g}倍（{month}公表{count}、{fresh}）"
    if record.get("old_method_reference") is not None:
        text += f"; 旧方式参考{record['old_method_reference']:g}倍"
    return text


def validate_selection_record(record: Any) -> list[str]:
    """Check that a record handed to scoring has the fields needed for audit."""
    if not isinstance(record, dict):
        return ["industry_per_selection must be an object"]
    errors = []
    for key in ("status", "tier", "value", "market", "industry", "purpose",
                "publication_month", "freshness", "source", "method", "fallback_trail"):
        if key not in record:
            errors.append(f"industry_per_selection.{key} is absent")
    if errors:
        return errors
    if record["freshness"] in ("STALE", "INVALID") and record["tier"] in (1, 2, 3):
        errors.append("industry_per_selection: STALE/INVALID data cannot back tiers ①〜③")
    if record["tier"] == 4 and record["purpose"] != "scenario":
        errors.append("industry_per_selection: tier ④ (15x) is allowed only for 4-9 scenarios")
    if record["status"] == "SELECTED" and _numeric(record["value"]) is None:
        errors.append("industry_per_selection: SELECTED requires a numeric value")
    return errors
