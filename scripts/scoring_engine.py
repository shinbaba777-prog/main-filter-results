#!/usr/bin/env python3
"""Deterministic Main Filter 2.3.1 scoring/gating core.

This module deliberately scores supplied, source-verified rubric items; it does not
scrape filings or invent values. Each item must have points, max_points, and one
status: scored, missing, not_applicable, or fixed_zero. Fixed-zero items remain
in the denominator. The upstream data collector must supply evidence/source fields.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any

STAGE1_GROUPS = {
    "growth": 15, "profitability": 15, "roic_capital": 15,
    "finance_cf": 10, "eps_growth": 10, "valuation": 15,
}
STAGE2_GROUPS = {
    "competitive_advantage": 5, "subsidiaries_ma": 3,
    "shorts_supply": 7, "ir_reaction": 5,
}
VALID_STATUSES = {"scored", "missing", "not_applicable", "fixed_zero"}

@dataclass
class Item:
    key: str
    group: str
    points: float | None
    max_points: float
    status: str = "scored"
    evidence: str = ""
    source: str = ""

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Item":
        item = cls(**d)
        if item.status not in VALID_STATUSES:
            raise ValueError(f"{item.key}: invalid status {item.status}")
        if item.max_points < 0:
            raise ValueError(f"{item.key}: max_points must be >= 0")
        if item.status == "missing" or item.status == "not_applicable":
            item.points = None
        elif item.points is None or item.points < 0 or item.points > item.max_points:
            raise ValueError(f"{item.key}: points must be between 0 and max_points")
        if item.status == "fixed_zero" and item.points != 0:
            raise ValueError(f"{item.key}: fixed_zero must have 0 points")
        return item

def _sum_group(items: list[Item], group: str) -> dict[str, float]:
    chosen = [i for i in items if i.group == group]
    earned = sum(float(i.points or 0) for i in chosen if i.status in {"scored", "fixed_zero"})
    missing = sum(i.max_points for i in chosen if i.status == "missing")
    na = sum(i.max_points for i in chosen if i.status == "not_applicable")
    available = sum(i.max_points for i in chosen if i.status not in {"missing", "not_applicable"})
    configured = sum(i.max_points for i in chosen)
    return {"earned": earned, "missing": missing, "not_applicable": na,
            "available": available, "configured": configured}

def tri_and(left: bool | None, right: bool | None) -> bool | None:
    """Three-valued AND: False dominates; True requires two True values."""
    if left is False or right is False:
        return False
    if left is True and right is True:
        return True
    return None


def evaluate(payload: dict[str, Any]) -> dict[str, Any]:
    """Evaluate score, Stage 1, final band and mandatory BUY blocks.

    Required payload keys:
      items: list of item dicts
      buy_block_inputs: keys shorts_direction_zero, ocf_ni_zero, dilution_zero,
        roic_below_h, roic_unavailable, short_type_a, peg_over_2,
        industry_per_over_130, base_upside_pct
    The 10 rubric group names must add up to their specification maximum.
    """
    items = [Item.from_dict(x) for x in payload.get("items", [])]
    errors = []
    expected = {**STAGE1_GROUPS, **STAGE2_GROUPS}
    actual = {}
    for group, maximum in expected.items():
        actual[group] = _sum_group(items, group)
        if abs(actual[group]["configured"] - maximum) > 1e-6:
            errors.append(f"{group}: rubric maximum must be {maximum}, got {actual[group]['configured']}")
    if errors:
        raise ValueError("; ".join(errors))

    stage1_names = list(STAGE1_GROUPS)
    stage1_earned = sum(actual[g]["earned"] for g in stage1_names)
    stage1_missing = sum(actual[g]["missing"] for g in stage1_names)
    stage1_na = sum(actual[g]["not_applicable"] for g in stage1_names)
    stage1_denominator = 80 - stage1_missing - stage1_na
    stage1_rate = (stage1_earned / stage1_denominator * 100) if stage1_denominator > 0 else None
    stage1_insufficient = stage1_missing > 16
    stage1_pass = (not stage1_insufficient and stage1_rate is not None and stage1_rate >= 65 and stage1_earned >= 52)

    earned = sum(v["earned"] for v in actual.values())
    missing = sum(v["missing"] for v in actual.values())
    na = sum(v["not_applicable"] for v in actual.values())
    denominator = 100 - missing - na
    total_insufficient = missing > 20
    adjusted = (earned / denominator * 100) if denominator > 0 and not total_insufficient else None

    b = payload.get("buy_block_inputs", {})
    checks = [
        ("① 空売り方向性0点", bool(b.get("shorts_direction_zero")) and bool(b.get("shorts_applicable", True))),
        ("② 営業CF÷純利益0点", bool(b.get("ocf_ni_zero"))),
        ("③ 希薄化0点", bool(b.get("dilution_zero"))),
        ("④ ROIC＜基準資本コストH", bool(b.get("roic_below_h"))),
        ("⑤ 欠損配点20点超", total_insufficient),
        ("⑥ 空売り型Aかつ成長性7点以下または財務・CF4点以下",
         bool(b.get("short_type_a")) and
         (actual["growth"]["earned"] <= 7 or actual["finance_cf"]["earned"] <= 4)),
        ("⑦ PEG＞2.0かつ業種相対PER＞130%", tri_and(b.get("peg_over_2"), b.get("industry_per_over_130"))),
        ("⑧ Base想定上昇余地＋20%未満",
         b.get("base_upside_pct") is not None and float(b["base_upside_pct"]) < 20),
    ]
    # ROIC unavailable is a notice, not a block. No other metric is inferred.
    blocks = [label for label, active in checks if active is True]
    notices = []
    if checks[6][1] is None:
        notices.append("🚨 BUYブロック⑦は判定不能（PEG・業種相対PERのUNKNOWN。格下げには使わない）")
    if b.get("roic_unavailable"):
        notices.append("ROIC算出不能：BUYブロック④は判定不能（格下げに使用しない）")
    if stage1_insufficient:
        judgment = "STAGE1 DATA-INSUFFICIENT"
    elif not stage1_pass:
        judgment = "一次不通過"
    elif total_insufficient:
        judgment = "DATA-INSUFFICIENT"
    elif adjusted is None:
        judgment = "DATA-INSUFFICIENT"
    elif blocks:
        judgment = "最大HOLD"
    elif adjusted >= 90:
        judgment = "強いBUY"
    elif adjusted >= 85:
        judgment = "BUY"
    elif adjusted >= 75:
        judgment = "条件付きBUY"
    elif adjusted >= 65:
        judgment = "HOLD"
    elif adjusted >= 55:
        judgment = "様子見"
    else:
        judgment = "未保有なら原則見送り／保有中ならSELL"

    return {
        "filter_version": "2.3.1",
        "group_scores": actual,
        "stage1": {"raw_score": stage1_earned, "max_score": 80,
                   "missing_points": stage1_missing, "not_applicable_points": stage1_na,
                   "denominator": stage1_denominator, "achievement_pct": stage1_rate,
                   "insufficient": stage1_insufficient, "passed": stage1_pass},
        "total": {"raw_score": earned, "max_score": 100, "missing_points": missing,
                  "not_applicable_points": na, "denominator": denominator,
                  "adjusted_score": adjusted, "insufficient": total_insufficient},
        "buy_blocks": [{"condition": label, "active": active} for label, active in checks],
        "notices": notices,
        "judgment": judgment,
        "data_status": "DATA-INSUFFICIENT" if total_insufficient or stage1_insufficient else "CALCULATED",
    }

if __name__ == "__main__":
    import json, sys
    try:
        data = json.load(sys.stdin)
        print(json.dumps(evaluate(data), ensure_ascii=False, indent=2))
    except Exception as exc:
        print(f"scoring_engine error: {exc}", file=sys.stderr)
        raise SystemExit(2)
