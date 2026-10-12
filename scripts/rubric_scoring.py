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
    for lower, points in thresholds:
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


def valuation_score(m: dict) -> list[dict]:
    """5-6 Valuation: ratios are decimals (130% = 1.30)."""
    out=[]
    peg=m.get("peg")
    if peg is None: peg=m.get("peg_proxy")
    if peg is None: p=None;s="missing"
    else:
        p=6 if peg<=.75 else 5 if peg<=1 else 4 if peg<=1.25 else 3 if peg<=1.5 else 2 if peg<=2 else 1 if peg<=3 else 0
        s="scored"
    out.append({"key":"peg","group":"valuation","points":p,"max_points":6,"status":s,"evidence":f"peg_or_proxy={peg!r}","source":m.get("peg_source","")})
    rel=m.get("industry_relative_per")
    if rel is None: p=None;s="missing"
    elif m.get("actual_eps_nonpositive"): p=0;s="scored"
    else:
        p=4 if rel<=.7 else 3 if rel<=.9 else 2 if rel<=1.1 else 1 if rel<=1.3 else 0
        s="scored"
    out.append({"key":"industry_relative_per","group":"valuation","points":p,"max_points":4,"status":s,"evidence":f"relative_per={rel!r}; actual_eps_nonpositive={m.get('actual_eps_nonpositive')}","source":m.get("industry_relative_per_source","")})
    y=m.get("fcf_yield")
    p,s=band(y,[(.05,3),(.03,2),(.01,1)])
    out.append({"key":"fcf_yield","group":"valuation","points":p,"max_points":3,"status":s,"evidence":f"fcf_yield={y!r}","source":m.get("fcf_yield_source","")})
    ev=m.get("ev_ebitda")
    if ev is None: p=None;s="missing"
    elif m.get("ebitda_nonpositive") or ev>15: p=0;s="scored"
    elif ev<=8: p=2;s="scored"
    else: p=1;s="scored"
    out.append({"key":"ev_ebitda","group":"valuation","points":p,"max_points":2,"status":s,"evidence":f"ev_ebitda={ev!r}","source":m.get("ev_ebitda_source","")})
    return out

def competitive_advantage_score(m: dict) -> list[dict]:
    types=m.get("evidence_backed_advantage_types")
    if types is None: p=None;s="missing";ev="一次資料＋直接裏付け定量値が未確認"
    else:
        count=len(set(types)); r=m.get("roic_or_roe_last3")
        p=0 if count==0 else 1 if count==1 else 3 if r is not None and len(r)>=3 and all(x is not None and x>=.15 for x in r[:3]) else 2
        s="scored";ev=f"types={types!r}; ROIC/ROE last3={r!r}"
    out=[{"key":"competitive_advantage","group":"competitive_advantage","points":p,"max_points":3,"status":s,"evidence":ev,"source":m.get("advantage_source","")}]
    p,s=band(m.get("management_ownership"),[(.10,2),(.05,1)])
    out.append({"key":"management_ownership","group":"competitive_advantage","points":p,"max_points":2,"status":s,"evidence":f"management_ownership={m.get('management_ownership')!r}; controlling_owner={m.get('controlling_owner')}","source":m.get("management_ownership_source","")})
    return out

def subsidiaries_ma_score(m: dict) -> list[dict]:
    if m.get("no_material_subsidiaries_and_no_ma_5y") is True:
        return [{"key":"subsidiaries_ma","group":"subsidiaries_ma","points":None,"max_points":3,"status":"not_applicable","evidence":"重要子会社なし、直近5年M&A実績なし","source":m.get("source","")}]
    keys=("material_impairment_ratio","loss_subsidiary_loss_vs_op_profit","goodwill_plus_intangibles_to_equity","goodwill_to_equity","post_ma_op_margin_change")
    if any(m.get(k) is None for k in keys):
        p=None;s="missing";e="M&A・子会社の必須指標不足"
    elif m["material_impairment_ratio"]>=.01 or m["loss_subsidiary_loss_vs_op_profit"]>=.20:
        p=0;s="scored";e="重要減損または赤字子会社等の損失が基準以上"
    elif m["goodwill_plus_intangibles_to_equity"]>=.50 or m["post_ma_op_margin_change"]<=-.005:
        p=1;s="scored";e="のれん等50%以上またはM&A後営業利益率が0.5pt以上低下"
    elif .20<=m["goodwill_to_equity"]<.50 and not m.get("material_impairment",False):
        p=2;s="scored";e="のれん20〜50%、重要減損なし"
    elif m["goodwill_to_equity"]<.20 and not m.get("material_impairment",False) and m["post_ma_op_margin_change"]>=0:
        p=3;s="scored";e="のれん20%未満、重要減損なし、営業利益率低下なし"
    else:
        p=None;s="missing";e="仕様表の条件を確定できず。一次資料確認が必要"
    return [{"key":"subsidiaries_ma","group":"subsidiaries_ma","points":p,"max_points":3,"status":s,"evidence":e,"source":m.get("source","")}]

def shorts_supply_score(m: dict) -> list[dict]:
    if m.get("no_public_short_positions_90d") is True:
        return [{"key":"shorts_supply","group":"shorts_supply","points":None,"max_points":7,"status":"not_applicable","evidence":"90日間に0.5%以上の公表残高なし（0.5%未満は確認不能）","source":m.get("source","")}]
    out=[]; start=m.get("short_ratio_start"); end=m.get("short_ratio_end"); entrants=m.get("new_institutions",0)
    if m.get("only_one_short_observation") or start is None or end is None or m.get("comparison_days",0)<20:
        d=None;s="missing";e="比較可能な2時点（20営業日以上）が不足"
    elif start==0 and end>0:
        d=1 if entrants==1 else 0 if entrants>=2 else None;s="scored" if d is not None else "missing";e=f"新規参入機関数={entrants}"
    elif end==0 or (start-end)/start>=.50: d=4;s="scored";e=f"{start}→{end}"
    elif (start-end)/start>=.20: d=3;s="scored";e=f"{start}→{end}"
    elif abs((end-start)/start)<.20: d=2;s="scored";e=f"{start}→{end}"
    elif (end-start)/start<.50: d=1;s="scored";e=f"{start}→{end}"
    else: d=0;s="scored";e=f"{start}→{end}; entrants={entrants}"
    out.append({"key":"shorts_direction","group":"shorts_supply","points":d,"max_points":4,"status":s,"evidence":e,"source":m.get("direction_source","")})
    p,s=band(end,[(.03,0),(.01,1)])
    if end is not None and end<.01: p=2;s="scored"
    out.append({"key":"shorts_concentration","group":"shorts_supply","points":p,"max_points":2,"status":s,"evidence":f"base_date_total_ratio={end!r}","source":m.get("concentration_source","")})
    post=m.get("post_earnings_30d_change")
    p=None if post is None else (1 if post<=0 else 0);s="missing" if post is None else "scored"
    out.append({"key":"shorts_post_earnings","group":"shorts_supply","points":p,"max_points":1,"status":s,"evidence":f"30-day change={post!r}","source":m.get("post_earnings_source","")})
    return out

def ir_reaction_score(m: dict) -> list[dict]:
    target=m.get("target_ir_count_12m",0); eligible=m.get("eligible_ir_count_12m",0)
    if target==0:
        p=None;s="not_applicable";e="対象IRが直近12ヶ月ゼロ"
    elif eligible==0:
        p=None;s="missing";e="対象IRあり、成熟・非重複の採点可能IRなし"
    else:
        total=0
        for ret in m.get("eligible_excess_returns",[]):
            total += 2 if ret>=.10 else 1 if ret>=.03 else 0 if ret>-.03 else -1 if ret>-.10 else -2
        p=5 if total>=4 else 4 if total>=2 else 3 if total>=0 else 2 if total>=-2 else 1 if total>=-4 else 0
        s="scored";e=f"eligible={eligible}; returns={m.get('eligible_excess_returns')!r}; adjustment_sum={total}"
    return [{"key":"ir_reaction","group":"ir_reaction","points":p,"max_points":5,"status":s,"evidence":e,"source":m.get("source","")}]


def roic_capital_score(m: dict) -> list[dict]:
    """5-3 ROIC/capital efficiency (15). Rates are decimals."""
    out=[]
    roic=m.get("roic")
    proxy=m.get("roe") if m.get("roic_uncomputable") else None
    used=roic if roic is not None else proxy
    p,s=band(used,[(.20,5),(.15,4),(.10,3),(.07,2),(0,1)])
    out.append({"key":"roic_level","group":"roic_capital","points":p,"max_points":5,"status":s,"evidence":f"ROIC={roic!r}; ROE proxy={proxy!r}","source":m.get("roic_source","")})
    inc=m.get("incremental_roic")
    if inc is None and m.get("incremental_roic_uncomputable"):
        if m.get("nopat_change") is None: p=None;s="missing"
        else: p=4 if m["nopat_change"]>0 else 0;s="scored"
    elif inc is None: p=None;s="missing"
    else:
        p=4 if inc>=.20 else 3 if inc>=.10 else 2 if inc>=.05 else 1 if inc>=0 else 0;s="scored"
    out.append({"key":"incremental_roic","group":"roic_capital","points":p,"max_points":4,"status":s,"evidence":f"incremental_roic={inc!r}; NOPAT change={m.get('nopat_change')!r}","source":m.get("incremental_roic_source","")})
    deltas=m.get("roic_deltas")
    if deltas is None or len(deltas)<3: p=None;s="missing";e="直近3回の前期差不足"
    else:
        improve=sum(x is not None and x>=.005 for x in deltas[:3]); decline=sum(x is not None and x<=-.005 for x in deltas[:3])
        p=2 if improve>=2 else 0 if decline>=2 else 1;s="scored";e=f"deltas={deltas[:3]!r}"
    out.append({"key":"roic_direction","group":"roic_capital","points":p,"max_points":2,"status":s,"evidence":e,"source":m.get("roic_deltas_source","")})
    reinvest=m.get("reinvestment_rate"); h=m.get("capital_cost_h")
    if reinvest is None or h is None or used is None: p=None;s="missing"
    elif used>h and reinvest>=.30: p=2;s="scored"
    elif used>h and reinvest>=.10: p=1;s="scored"
    else: p=0;s="scored"
    out.append({"key":"reinvestment_rate","group":"roic_capital","points":p,"max_points":2,"status":s,"evidence":f"rate={reinvest!r}; capital_cost={h!r}; ROIC/ROE={used!r}","source":m.get("reinvestment_rate_source","")})
    roe=m.get("roe")
    p,s=band(roe,[(.15,2),(.08,1)])
    out.append({"key":"roe","group":"roic_capital","points":p,"max_points":2,"status":s,"evidence":f"roe={roe!r}","source":m.get("roe_source","")})
    return out

def build_items(metrics: dict) -> list[dict]:
    """Convert source-verified metric groups into scoring-engine items.
    Missing groups are explicitly marked missing; never filled with guessed values.
    """
    funcs=[
        ("growth",growth_score),("profitability",profitability_score),
        ("roic_capital",roic_capital_score),("finance_cf",finance_cf_score),
        ("eps_growth",eps_score),("valuation",valuation_score),
        ("competitive_advantage",competitive_advantage_score),
        ("subsidiaries_ma",subsidiaries_ma_score),
        ("shorts_supply",shorts_supply_score),("ir_reaction",ir_reaction_score)
    ]
    items=[]
    for group,fn in funcs:
        data=metrics.get(group)
        if data is None:
            maximum={"growth":15,"profitability":15,"roic_capital":15,"finance_cf":10,"eps_growth":10,"valuation":15,"competitive_advantage":5,"subsidiaries_ma":3,"shorts_supply":7,"ir_reaction":5}[group]
            items.append({"key":group,"group":group,"points":None,"max_points":maximum,"status":"missing","evidence":"このグループの指標データが未提供","source":""})
        else:
            items.extend(fn(data))
    return items
