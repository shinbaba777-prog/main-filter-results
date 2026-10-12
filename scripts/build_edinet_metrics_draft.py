#!/usr/bin/env python3
"""Build a conservative Main Filter 2.3.1 metrics draft from manually approved EDINET facts.

This is an integration bridge, not an auto-approval engine. Only rows explicitly
marked APPROVED in core_metric_review_queue.csv are used. Unapproved, ambiguous,
duplicate-unresolved, or missing facts remain null. The output still requires
review of non-EDINET inputs and BUY-block conditions before scoring.
"""
from __future__ import annotations
import argparse
import csv
import json
import math
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUEUE_DEFAULT = ROOT / "data/edinet/extracted/core_metric_review_queue.csv"
YEAR_ORDER = {"4期前": 0, "3期前": 1, "前々期": 2, "前期": 3, "当期": 4}
VALUE_METRICS = {"sales", "operating_profit", "ordinary_profit", "profit", "eps", "ocf", "icf"}


def num(value):
    try:
        x = float(str(value).replace(",", "").replace("△", "-").replace("▲", "-"))
        return x if math.isfinite(x) else None
    except (TypeError, ValueError):
        return None


def yoy_series(values):
    """Return up to four year-over-year rates; invalid year-pairs stay missing."""
    if len(values) < 5:
        return None
    out = [None if a is None or b is None or a <= 0 else (b / a) - 1
           for a, b in zip(values, values[1:])]
    return out[-4:]


def load_approved(path: Path, code: str):
    if not path.exists():
        raise ValueError(f"Missing review queue: {path}")
    facts = {}
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        required = {"security_code", "candidate_metric", "value", "relative_year", "review_status",
                    "review_reason", "source_zip", "source_csv", "element_id", "context_id", "unit_id"}
        if not required.issubset(set(reader.fieldnames or [])):
            raise ValueError("Review queue is missing required columns")
        for row in reader:
            if str(row.get("security_code", "")).strip().upper() not in {code, code + "0"}:
                continue
            if row.get("review_status") != "APPROVED":
                continue
            if row.get("review_reason") != "APPROVED_SOURCE_VERIFIED":
                raise ValueError("Approved row has an unresolved review_reason; resolve it explicitly first")
            metric, year = row.get("candidate_metric", ""), row.get("relative_year", "")
            if metric not in VALUE_METRICS or year not in YEAR_ORDER:
                continue
            value = num(row.get("value"))
            if value is None:
                raise ValueError(f"Approved row has invalid numeric value: {row.get('source_csv')} row {row.get('row_number')}")
            key = (metric, year)
            fact = {"value": value, "source": f"EDINET {row.get('source_zip')} / {row.get('source_csv')} row {row.get('row_number')}",
                    "element_id": row.get("element_id", ""), "context_id": row.get("context_id", ""),
                    "unit_id": row.get("unit_id", ""), "review_reason": row.get("review_reason", "")}
            if key in facts and facts[key]["value"] != value:
                raise ValueError(f"Conflicting approved facts for {metric}/{year}; resolve duplicates before drafting")
            facts[key] = fact
    return facts


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--code", required=True, help="EDINET securities code as used in the queue")
    ap.add_argument("--company", required=True)
    ap.add_argument("--analysis-date", default=date.today().isoformat())
    ap.add_argument("--queue", default=str(QUEUE_DEFAULT))
    ap.add_argument("--out", required=True, help="Output draft JSON path")
    args = ap.parse_args()
    code = args.code.strip().upper()
    if not code or not args.company.strip():
        raise SystemExit("--code and --company must not be blank")
    try:
        facts = load_approved(Path(args.queue), code)
    except (OSError, ValueError) as exc:
        raise SystemExit(f"Cannot build metrics draft: {exc}") from None

    def v(metric, year):
        item = facts.get((metric, year))
        return item["value"] if item else None
    def src(metric, year):
        item = facts.get((metric, year))
        return item["source"] if item else ""
    def growth(metric, start, end, years):
        a, b = v(metric, start), v(metric, end)
        if a is None or b is None or a <= 0 or b < 0:
            return None
        return (b / a) ** (1 / years) - 1

    sales = [v("sales", y) for y in ("4期前", "3期前", "前々期", "前期", "当期")]
    op = [v("operating_profit", y) for y in ("4期前", "3期前", "前々期", "前期", "当期")]
    profit = [v("profit", y) for y in ("4期前", "3期前", "前々期", "前期", "当期")]
    eps = [v("eps", y) for y in ("4期前", "3期前", "前々期", "前期", "当期")]
    ocf = [v("ocf", y) for y in ("4期前", "3期前", "前々期", "前期", "当期")]
    icf = [v("icf", y) for y in ("4期前", "3期前", "前々期", "前期", "当期")]
    sales_margins = [None if s in (None, 0) or p is None else p/s for s,p in zip(sales,op)]
    def deltas(values):
        return [None if a is None or b is None else b-a for a,b in zip(values, values[1:])]
    def latest_yoy(values):
        a,b=values[-2],values[-1]
        return None if a is None or b is None or a <= 0 else b/a-1
    metrics = {
      "growth": {"sales_long_cagr": growth("sales","4期前","当期",4), "sales_3y_cagr": growth("sales","3期前","当期",3),
                 "sales_yoy": latest_yoy(sales), "sales_forecast_growth": None,
                 "operating_profit_long_cagr": growth("operating_profit","4期前","当期",4),
                 "sales_long_cagr_source": src("sales","4期前")+"; "+src("sales","当期"),
                 "sales_yoy_source": src("sales","前期")+"; "+src("sales","当期")},
      "profitability": {"operating_margin": None if not sales or sales[-1] in (None,0) or op[-1] is None else op[-1]/sales[-1],
                        "operating_margin_deltas": deltas(sales_margins[-4:]), "gross_margin_deltas": None, "roa": None,
                        "operating_margin_source": src("operating_profit","当期")+"; "+src("sales","当期")},
      "roic_capital": {"roic": None, "roic_uncomputable": True, "roe": None, "incremental_roic": None,
                       "incremental_roic_uncomputable": True, "nopat_change": None, "roic_deltas": None,
                       "reinvestment_rate": None, "capital_cost_h": None},
      "finance_cf": {"ocf_ni_3y": None, "ocf_negative_two_consecutive": False, "net_income_3y": None,
                     "ocf_3y": None, "net_debt_ebitda": None, "net_cash": False, "share_count_increase_3y": None,
                     "share_count_increased_three_years": False, "equity_ratio": None, "fcf_3y_sum": None, "fcf_latest": None},
      "eps_growth": {"eps_long_cagr": growth("eps","4期前","当期",4), "eps_yoy": latest_yoy(eps),
                     "eps_forecast_growth": None, "eps_yoy_last4": yoy_series(eps)},
      "valuation": {"peg": None, "peg_proxy": None, "industry_relative_per": None, "actual_eps_nonpositive": eps[-1] is not None and eps[-1] <= 0,
                    "fcf_yield": None, "ev_ebitda": None, "ebitda_nonpositive": False},
      "competitive_advantage": {"evidence_backed_advantage_types": None, "roic_or_roe_last3": None, "management_ownership": None, "controlling_owner": None},
      "subsidiaries_ma": {"no_material_subsidiaries_and_no_ma_5y": False, "material_impairment_ratio": None,
                          "loss_subsidiary_loss_vs_op_profit": None, "goodwill_plus_intangibles_to_equity": None,
                          "goodwill_to_equity": None, "post_ma_op_margin_change": None, "material_impairment": False},
      "shorts_supply": {"no_public_short_positions_90d": False, "only_one_short_observation": False,
                        "short_ratio_start": None, "short_ratio_end": None, "comparison_days": None,
                        "new_institutions": None, "post_earnings_30d_change": None},
      "ir_reaction": {"target_ir_count_12m": None, "eligible_ir_count_12m": None, "eligible_excess_returns": None}
    }
    # Do not set absent facts to zero; all non-EDINET inputs remain explicitly unknown.
    payload = {
      "code": code, "company": args.company.strip(), "analysis_date": args.analysis_date,
      "filter_version": "2.3.1", "metrics": metrics,
      "buy_block_inputs": {"shorts_direction_zero": None, "shorts_applicable": None, "ocf_ni_zero": None,
        "dilution_zero": None, "roic_below_h": None, "roic_unavailable": None, "short_type_a": None,
        "peg_over_2": None, "industry_per_over_130": None, "base_upside_pct": None},
      "edinet_fact_count_approved": len(facts),
      "edinet_fact_provenance": [{"metric": k[0], "relative_year": k[1], **val} for k,val in sorted(facts.items(), key=lambda x:(x[0][0],YEAR_ORDER[x[0][1]]))],
      "warning": "DRAFT ONLY. Not scoreable until remaining source facts and every BUY-block input are reviewed. Do not fill nulls by assumption."
    }
    out=Path(args.out)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"output":str(out),"approved_facts":len(facts),"warning":payload["warning"]},ensure_ascii=False))

if __name__ == "__main__":
    main()
