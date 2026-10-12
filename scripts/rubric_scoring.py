#!/usr/bin/env python3
"""Deterministic metric-to-points helpers transcribed from Main Filter 2.3.1.

These functions calculate rubric points only after source-verified metrics are supplied.
They do not fetch or infer metrics. None means the source value is unavailable.
"""
from __future__ import annotations
from typing import Optional

def band(value: Optional[float], thresholds: list[tuple[float, float]], missing_points: float = 0) -> tuple[Optional[float], str]:
    """Return points for ascending lower-bound thresholds; None means missing."""
    if value is None:
        return None, "missing"
    for lower, points in reversed(thresholds):
        if value >= lower:
            return points, "scored"
    return missing_points, "scored"

def growth_score(metrics: dict) -> list[dict]:
    """5-1 Growth (15): metrics are rates as decimals (e.g. 0.2 = 20%)."""
    specs = [
        ("sales_long_cagr", "sales_long_cagr", 4, [(0.20,4),(0.15,3),(0.10,2),(0.05,1)]),
        ("sales_3y_cagr", "sales_3y_cagr", 3, [(0.20,3),(0.10,2),(0.05,1)]),
        ("sales_yoy", "sales_yoy", 3, [(0.20,3),(0.10,2),(0.05,1)]),
        ("sales_forecast_growth", "sales_forecast_growth", 3, [(0.20,3),(0.10,2),(0.05,1)]),
        ("operating_profit_long_cagr", "operating_profit_long_cagr", 2, [(0.20,2),(0.10,1)]),
    ]
    out = []
    for key, label, maximum, thresholds in specs:
        value = metrics.get(key)
        pts, status = band(value, thresholds)
        if key == "operating_profit_long_cagr" and value is None and metrics.get("operating_profit_cagr_uncomputable"):
            pts = 1 if metrics.get("latest_operating_profit_positive") else 0
            status = "scored"
        out.append({"key": label, "group": "growth", "points": pts, "max_points": maximum,
                    "status": status, "evidence": f"value={value!r}", "source": metrics.get(key+"_source","")})
    return out

def profitability_score(metrics: dict) -> list[dict]:
    """5-2 Profitability (15). margins are decimals; margin_deltas are percentage-point differences."""
    out=[]
    opm=metrics.get("operating_margin")
    pts,status=band(opm,[(0.25,5),(0.20,4),(0.15,3),(0.10,2),(0.05,1)])
    out.append({"key":"operating_margin_level","group":"profitability","points":pts,"max_points":5,"status":status,"evidence":f"operating_margin={opm!r}","source":metrics.get("operating_margin_source","")})
    out.append(_direction_item("operating_margin_direction","profitability",4,metrics.get("operating_margin_deltas"),gross=False,source=metrics.get("operating_margin_deltas_source","")))
    out.append(_direction_item("gross_margin_direction","profitability",3,metrics.get("gross_margin_deltas"),gross=True,source=metrics.get("gross_margin_deltas_source","")))
    roa=metrics.get("roa")
    pts,status=band(roa,[(0.10,3),(0.05,2),(0.02,1)])
    out.append({"key":"roa","group":"profitability","points":pts,"max_points":3,"status":status,"evidence":f"roa={roa!r}","source":metrics.get("roa_source","")})
    return out

def _direction_item(key: str, group: str, maximum: float, deltas, gross: bool, source: str="") -> dict:
    if deltas is None or len(deltas)<3:
        return {"key":key,"group":group,"points":None,"max_points":maximum,"status":"missing","evidence":"直近3回の前期差が不足","source":source}
    improvements=sum(x is not None and x>=0.005 for x in deltas[:3])
    declines=sum(x is not None and x<=-0.005 for x in deltas[:3])
    if declines>=2: pts=0
    elif gross: pts={0:0,1:1,2:2,3:3}[improvements]
    else: pts={0:1,1:2,2:3,3:4}[improvements]
    return {"key":key,"group":group,"points":pts,"max_points":maximum,"status":"scored","evidence":f"deltas={deltas[:3]!r}; improvements={improvements}; declines={declines}","source":source}

def eps_score(metrics: dict) -> list[dict]:
    """5-5 EPS growth (10). rates are decimals, adjusted EPS values are supplied by caller."""
    out=[]
    specs=[
        ("eps_long_cagr",3,[(0.20,3),(0.10,2),(0.05,1)]),
        ("eps_yoy",2,[(0.15,2),(0.05,1)]),
        ("eps_forecast_growth",3,[(0.20,3),(0.10,2),(0.05,1)]),
    ]
    for key,maximum,thresholds in specs:
        value=metrics.get(key)
        pts,status=band(value,thresholds)
        if value is None and metrics.get(key+"_uncomputable") and key=="eps_long_cagr":
            pts=1 if metrics.get("latest_eps_positive") else 0; status="scored"
        if value is None and metrics.get(key+"_uncomputable") and key in ("eps_yoy","eps_forecast_growth"):
            pts=(2 if metrics.get("latest_eps_positive") else 0) if key=="eps_yoy" else (3 if metrics.get("forecast_eps_positive") else 0)
            status="scored"
        out.append({"key":key,"group":"eps_growth","points":pts,"max_points":maximum,"status":status,"evidence":f"value={value!r}","source":metrics.get(key+"_source","")})
    yoy=metrics.get("eps_yoy_last4")
    if yoy is None or len(yoy)<4:
        pts=None; status="missing"; evidence="直近4回の前期比が不足"
    else:
        increases=sum(x is not None and x>0 for x in yoy[:4])
        pts=2 if increases==4 else 1 if increases==3 else 0; status="scored"; evidence=f"last4={yoy[:4]!r}; increases={increases}"
    out.append({"key":"eps_persistence","group":"eps_growth","points":pts,"max_points":2,"status":status,"evidence":evidence,"source":metrics.get("eps_yoy_last4_source","")})
    return out

def finance_cf_score(metrics: dict) -> list[dict]:
    """5-4 Finance/CF (10); raw values must be computed from source statements first."""
    out=[]
    ocf_ni=metrics.get("ocf_ni_3y")
    if metrics.get("ocf_negative_two_consecutive"):
        p=0; s="scored"
    elif ocf_ni is None:
        p=None; s="missing"
    elif metrics.get("net_income_3y",0)<=0:
        p=2 if metrics.get("ocf_3y",0)>0 else 1; s="scored"
    else:
        p=2 if ocf_ni>=0.8 else 1; s="scored"
    out.append({"key":"ocf_ni","group":"finance_cf","points":p,"max_points":2,"status":s,"evidence":f"ocf_ni_3y={ocf_ni!r}; consecutive_negative={metrics.get('ocf_negative_two_consecutive')}","source":metrics.get("ocf_ni_source","")})
    lev=metrics.get("net_debt_ebitda")
    if lev is None:
        p=None;s="missing"
    elif lev<=1 or metrics.get("net_cash"):
        p=2;s="scored"
    elif lev<=3:
        p=1;s="scored"
    else:
        p=0;s="scored"
    out.append({"key":"net_debt_ebitda","group":"finance_cf","points":p,"max_points":2,"status":s,"evidence":f"net_debt_ebitda={lev!r}; net_cash={metrics.get('net_cash')}","source":metrics.get("net_debt_ebitda_source","")})
    dilution=metrics.get("share_count_increase_3y")
    if dilution is None:
        p=None;s="missing"
    elif dilution<0.01 and not metrics.get("share_count_increased_three_years"):
        p=2;s="scored"
    elif dilution<0.05 and not metrics.get("share_count_increased_three_years"):
        p=1;s="scored"
    else:
        p=0;s="scored"
    out.append({"key":"dilution_3y","group":"finance_cf","points":p,"max_points":2,"status":s,"evidence":f"increase={dilution!r}; three_consecutive={metrics.get('share_count_increased_three_years')}","source":metrics.get("share_count_increase_3y_source","")})
    equity=metrics.get("equity_ratio")
    p,s=band(equity,[(0.50,2),(0.30,1)])
    out.append({"key":"equity_ratio","group":"finance_cf","points":p,"max_points":2,"status":s,"evidence":f"equity_ratio={equity!r}","source":metrics.get("equity_ratio_source","")})
    fcf=metrics.get("fcf_3y_sum")
    latest_fcf=metrics.get("fcf_latest")
    if fcf is None or latest_fcf is None:
        p=None;s="missing"
    else:
        positive=(fcf>0,latest_fcf>0)
        p=2 if all(positive) else 1 if any(positive) else 0;s="scored"
    out.append({"key":"fcf_stability","group":"finance_cf","points":p,"max_points":2,"status":s,"evidence":f"fcf_3y_sum={fcf!r}; latest={latest_fcf!r}","source":metrics.get("fcf_source","")})
    return out
