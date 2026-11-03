"""Repair tests for PR #6 final decision (2026-11-03, ChatGPT × Claude, user-approved).

Covers: ⑥/⑧ UNKNOWN boundaries, JPX industry-PER fallback order, 9554 AViC
regression (連結切替・CAGR保留・株式分割・自己株式控除), ir_reaction_score
single definition. Canonical reference: メインフィルター2.3.1 Doc rev93.
"""
import inspect
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import rubric_scoring  # noqa: E402
from financial_metrics import (basis_consistent_cagr, cagr, net_shares,  # noqa: E402
                               share_count_increase, split_adjusted_net_shares,
                               split_adjusted_per_share)
from industry_per import (describe_selection, select_industry_per,  # noqa: E402
                          validate_selection_record)
from rubric_scoring import eps_score, finance_cf_score, growth_score  # noqa: E402
from scoring_engine import STAGE1_GROUPS, STAGE2_GROUPS, evaluate  # noqa: E402
from series_metrics import build_series_metrics  # noqa: E402

FIXTURE_9554 = ROOT / "tests" / "fixtures" / "9554_avic_edinetdb_20261103.json"


def blocks(**overrides):
    b = dict(shorts_direction_zero=False, shorts_applicable=True, ocf_ni_zero=False,
             dilution_zero=False, roic_below_h=False, roic_unavailable=False,
             short_type_a=False, peg_over_2=False, industry_per_over_130=False,
             base_upside_pct=25)
    b.update(overrides)
    return b


def payload(growth=(15, 0), finance=(10, 0), **block_overrides):
    """growth/finance = (earned, missing). Other groups full marks."""
    items = []
    for group, maximum in {**STAGE1_GROUPS, **STAGE2_GROUPS}.items():
        spec = {"growth": growth, "finance_cf": finance}.get(group, (maximum, 0))
        earned, missing = spec
        if missing:
            items.append(dict(key=group + "_m", group=group, points=None,
                              max_points=missing, status="missing"))
        rest = maximum - missing
        if rest:
            items.append(dict(key=group, group=group, points=earned, max_points=rest))
    return dict(items=items, buy_block_inputs=blocks(**block_overrides))


def block_state(result, number):
    return result["buy_blocks"][number - 1]["state"]


class Block6UnknownTests(unittest.TestCase):
    def test_growth_boundary_true_unknown_false(self):
        cases = [((7, 0), "TRUE"), ((6, 1), "TRUE"), ((7, 1), "UNKNOWN"),
                 ((3, 12), "UNKNOWN"), ((8, 0), "FALSE"), ((8, 5), "FALSE")]
        for growth, expected in cases:
            with self.subTest(growth=growth):
                r = evaluate(payload(growth=growth, finance=(10, 0), short_type_a=True))
                self.assertEqual(block_state(r, 6), expected)

    def test_finance_boundary_true_unknown_false(self):
        cases = [((4, 0), "TRUE"), ((4, 1), "UNKNOWN"), ((5, 0), "FALSE"), ((0, 5), "UNKNOWN")]
        for finance, expected in cases:
            with self.subTest(finance=finance):
                r = evaluate(payload(growth=(15, 0), finance=finance, short_type_a=True))
                self.assertEqual(block_state(r, 6), expected)

    def test_or_true_dominates_unknown(self):
        r = evaluate(payload(growth=(3, 12), finance=(2, 0), short_type_a=True))
        self.assertEqual(block_state(r, 6), "TRUE")

    def test_short_type_a_false_is_false_even_with_missing(self):
        r = evaluate(payload(growth=(3, 12), short_type_a=False))
        self.assertEqual(block_state(r, 6), "FALSE")

    def test_unknown_does_not_downgrade_and_is_noticed(self):
        r = evaluate(payload(growth=(7, 1), short_type_a=True))
        self.assertNotEqual(r["judgment"], "最大HOLD")
        self.assertIn("⑥ 空売り型Aかつ成長性7点以下または財務・CF4点以下", r["buy_blocks_unknown"])
        self.assertTrue(any("BUYブロック⑥は判定不能" in n for n in r["notices"]))

    def test_true_still_downgrades(self):
        r = evaluate(payload(growth=(7, 0), short_type_a=True))
        self.assertEqual(r["judgment"], "最大HOLD")

    def test_short_type_a_null_still_rejected(self):
        with self.assertRaises(ValueError):
            evaluate(payload(short_type_a=None))


class Block8UnknownTests(unittest.TestCase):
    def test_boundaries(self):
        for upside, expected in [(19.99, "TRUE"), (20, "FALSE"), (-5, "TRUE")]:
            with self.subTest(upside=upside):
                self.assertEqual(block_state(evaluate(payload(base_upside_pct=upside)), 8), expected)

    def test_explicit_null_with_reason_is_unknown_notice_only(self):
        r = evaluate(payload(base_upside_pct=None,
                             fair_value_unavailable_reason="Base EPSが0以下で適正株価算定不能"))
        self.assertEqual(block_state(r, 8), "UNKNOWN")
        self.assertNotEqual(r["judgment"], "最大HOLD")
        self.assertTrue(any("BUYブロック⑧は判定不能" in n and "Base EPS" in n for n in r["notices"]))

    def test_null_without_reason_rejected(self):
        for reason in (None, "", "   "):
            with self.subTest(reason=reason):
                p = payload(base_upside_pct=None)
                if reason is not None:
                    p["buy_block_inputs"]["fair_value_unavailable_reason"] = reason
                with self.assertRaises(ValueError):
                    evaluate(p)

    def test_absent_key_still_rejected(self):
        p = payload()
        del p["buy_block_inputs"]["base_upside_pct"]
        with self.assertRaises(ValueError):
            evaluate(p)

    def test_recording_accepts_null_with_reason(self):
        p = payload(base_upside_pct=None, fair_value_unavailable_reason="適正株価算定不能")
        p.update(code="0000", company="テスト", analysis_date="2026-11-03")
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "a.json"
            src.write_text(json.dumps(p, ensure_ascii=False), encoding="utf-8")
            res = subprocess.run([sys.executable, str(ROOT / "scripts" / "record_verified_analysis.py"),
                                  str(src), "--dry-run", "--index", str(Path(td) / "i.csv")],
                                 capture_output=True, text=True, cwd=ROOT / "scripts")
            self.assertEqual(res.returncode, 0, res.stderr)
            self.assertIn("BUYブロック⑧は判定不能", res.stdout)
            self.assertFalse((Path(td) / "i.csv").exists())


def jpx(rows, total=20.0, **kw):
    args = dict(market="growth", industry="サービス業", rows=rows, market_total_simple_per=total,
                purpose="scoring", publication_month="2026-09", freshness="CONFIRMED_CURRENT",
                eps_column_available=True, source="perpbr202609.xlsx")
    args.update(kw)
    return select_industry_per(**args)


FULL = {"prime": dict(simple_per=18.0, eps_simple=100.0, companies=20),
        "standard": dict(simple_per=12.0, eps_simple=50.0, companies=8),
        "growth": dict(simple_per=30.0, eps_simple=10.0, companies=12)}


class JpxFallbackOrderTests(unittest.TestCase):
    def test_tier1(self):
        r = jpx(FULL)
        self.assertEqual((r["tier"], r["value"], r["companies"]), (1, 30.0, 12))

    def test_tier2_exact_recombination_not_average(self):
        rows = dict(FULL, growth=dict(simple_per=30.0, eps_simple=10.0, companies=9))
        r = jpx(rows, analysis_date="2026-11-03")
        price = 18 * 100 * 20 + 12 * 50 * 8 + 30 * 10 * 9
        profit = 100 * 20 + 50 * 8 + 10 * 9
        self.assertEqual(r["tier"], 2)
        self.assertEqual(r["value"], round(price / profit, 1))
        self.assertEqual(r["companies"], 37)
        self.assertNotEqual(r["value"], round((18 + 12 + 30) / 3, 1))
        self.assertEqual(r["old_method_reference"], 20.0)
        self.assertIn("①社数9社", r["fallback_trail"][0])

    def test_tier2_old_reference_only_for_three_months(self):
        rows = dict(FULL, growth=dict(simple_per="－", eps_simple=None, companies=0))
        self.assertIsNone(jpx(rows, analysis_date="2027-02-01")["old_method_reference"])

    def test_dash_in_own_market_falls_back(self):
        rows = dict(FULL, growth=dict(simple_per="－", eps_simple=None, companies=0))
        r = jpx(rows)
        self.assertEqual(r["tier"], 2)

    def test_tier2_not_exact_goes_to_tier3(self):
        rows = dict(FULL, growth=dict(simple_per=30.0, eps_simple=10.0, companies=5),
                    standard=dict(simple_per="－", eps_simple=-3.0, companies=8))
        r = jpx(rows)
        self.assertEqual((r["tier"], r["value"]), (3, 20.0))
        self.assertTrue(any("正確に合算できない" in t for t in r["fallback_trail"]))

    def test_missing_eps_column_goes_to_tier3(self):
        rows = dict(FULL, growth=dict(simple_per=30.0, eps_simple=10.0, companies=5))
        r = jpx(rows, eps_column_available=False)
        self.assertEqual(r["tier"], 3)

    def test_tier2_requires_positive_profit_and_ten_companies(self):
        small = {"prime": dict(simple_per=10.0, eps_simple=1.0, companies=3),
                 "standard": dict(simple_per=10.0, eps_simple=1.0, companies=3),
                 "growth": dict(simple_per=10.0, eps_simple=1.0, companies=3)}
        self.assertEqual(jpx(small)["tier"], 3)

    def test_tier4_only_for_scenario(self):
        rows = dict(FULL, growth=dict(simple_per="－", eps_simple=None, companies=3),
                    standard=dict(simple_per="－", eps_simple=None, companies=8))
        self.assertEqual(jpx(rows, total="－")["status"], "UNAVAILABLE")
        self.assertEqual(jpx(rows, total="－", purpose="buy_range_c")["value"], None)
        r = jpx(rows, total="－", purpose="scenario")
        self.assertEqual((r["tier"], r["value"]), (4, 15.0))
        r = jpx(rows, total="－", purpose="scenario", own_past_per_median=11.2)
        self.assertEqual(r["value"], 11.2)

    def test_asterisk_is_independent(self):
        rows = dict(FULL, growth=dict(simple_per="＊", eps_simple=0.01, companies=12))
        r = jpx(rows)
        self.assertEqual((r["status"], r["value"], r["tier"]), ("SPECIAL_ASTERISK", None, None))
        r = jpx(rows, purpose="scenario", own_past_per_median=40)
        self.assertEqual((r["status"], r["value"]), ("SPECIAL_ASTERISK", 15.0))
        r = jpx(rows, purpose="scenario", own_past_per_median=9)
        self.assertEqual(r["value"], 9)

    def test_freshness(self):
        self.assertEqual(jpx(FULL, freshness="STALE")["status"], "UNAVAILABLE")
        self.assertEqual(jpx(FULL, freshness="INVALID", purpose="scenario")["tier"], 4)
        r = jpx(FULL, freshness="CURRENT_BY_CALENDAR")
        self.assertEqual(r["tier"], 1)
        self.assertTrue(r["provisional"])

    def test_record_is_validated_and_echoed(self):
        r = jpx(dict(FULL, growth=dict(simple_per=30.0, eps_simple=10.0, companies=9)),
                analysis_date="2026-11-03")
        self.assertEqual(validate_selection_record(r), [])
        p = payload()
        p["industry_per_selection"] = r
        out = evaluate(p)
        self.assertEqual(out["industry_per_basis"]["tier"], 2)
        text = describe_selection(r)
        self.assertIn("②", text)
        self.assertIn("旧方式参考20", text)

    def test_tier4_rejected_for_scoring_record(self):
        bad = jpx(FULL)
        bad.update(tier=4, purpose="scoring")
        self.assertTrue(validate_selection_record(bad))
        p = payload()
        p["industry_per_selection"] = bad
        with self.assertRaises(ValueError):
            evaluate(p)


class AViC9554RegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fx = json.loads(FIXTURE_9554.read_text(encoding="utf-8"))
        cls.m = build_series_metrics(cls.fx["rows"])

    def test_consolidation_switch_holds_cagr(self):
        g = self.m["growth"]
        for key in ("sales_long_cagr", "sales_3y_cagr", "operating_profit_long_cagr"):
            with self.subTest(key=key):
                self.assertIsNone(g[key])
                self.assertEqual(g[key + "_hold_reason"], "basis_change")
        self.assertIsNone(self.m["eps_growth"]["eps_long_cagr"])
        self.assertEqual(self.m["eps_growth"]["eps_long_cagr_hold_reason"], "basis_change")

    def test_held_cagr_is_missing_not_fallback_point(self):
        items = {i["key"]: i for i in growth_score(dict(self.m["growth"], operating_profit_cagr_uncomputable=True,
                                                        latest_operating_profit_positive=True))}
        for key in ("sales_long_cagr", "sales_3y_cagr", "operating_profit_long_cagr"):
            self.assertEqual(items[key]["status"], "missing")
            self.assertIsNone(items[key]["points"])
            self.assertIn("連結切替", items[key]["evidence"])
        self.assertEqual(items["sales_yoy"]["points"], 3)  # FY25/FY24 both consolidated: +38.6%
        eps_items = {i["key"]: i for i in eps_score(dict(self.m["eps_growth"], eps_long_cagr_uncomputable=True,
                                                         latest_eps_positive=True))}
        self.assertEqual(eps_items["eps_long_cagr"]["status"], "missing")
        self.assertEqual(eps_items["eps_yoy"]["points"], 2)  # +72.4%

    def test_same_basis_yoy_values(self):
        self.assertAlmostEqual(self.m["growth"]["sales_yoy"], 2680875000 / 1934785000 - 1)
        self.assertAlmostEqual(self.m["eps_growth"]["eps_yoy"], 87.18 / 50.56 - 1)

    def test_treasury_deducted_and_dilution(self):
        d = self.m["dilution"]
        self.assertEqual(d["window"], (2022, 2025))
        self.assertEqual(d["net_shares_start"], 5693100 - 41)
        self.assertEqual(d["net_shares_end"], 6327800 - 85)
        self.assertAlmostEqual(d["share_count_increase_3y"], (6327800 - 85) / (5693100 - 41) - 1)
        item = [i for i in finance_cf_score({"share_count_increase_3y": d["share_count_increase_3y"],
                                             "share_count_increased_three_years": True})
                if i["key"] == "dilution_3y"][0]
        self.assertEqual(item["points"], 0)

    def test_missing_treasury_is_not_zero(self):
        rows = [dict(r) for r in self.fx["rows"]]
        rows[1]["treasury_shares_fye"] = None
        d = build_series_metrics(rows)["dilution"]
        self.assertIsNone(d["share_count_increase_3y"])
        self.assertIn("自己株式", d["hold_reason"])

    def test_split_factor_one_leaves_values(self):
        self.assertEqual(self.m["eps_growth"]["adjusted_eps_series"], [r["eps"] for r in self.fx["rows"]])

    def test_block6_unknown_for_9554_shape(self):
        growth_items = growth_score(self.m["growth"])
        earned = sum(i["points"] or 0 for i in growth_items)
        missing = sum(i["max_points"] for i in growth_items if i["status"] == "missing")
        self.assertEqual((earned, missing), (3, 12))
        r = evaluate(payload(growth=(earned, missing), short_type_a=True))
        self.assertEqual(block_state(r, 6), "UNKNOWN")
        self.assertNotEqual(r["judgment"], "最大HOLD")


class SplitAndCagrHelperTests(unittest.TestCase):
    def test_split_restates_eps_and_shares(self):
        # 1:2 split after FY1: FY1 values restated with factor 2.
        self.assertEqual(split_adjusted_per_share(100.0, 2.0), 50.0)
        start = split_adjusted_net_shares(1_000_000, 0, 2.0)
        end = split_adjusted_net_shares(2_000_000, 0, 1.0)
        self.assertEqual(share_count_increase(start, end), 0.0)
        self.assertIsNone(split_adjusted_per_share(100.0, None))

    def test_net_shares_rejects_inconsistent(self):
        self.assertIsNone(net_shares(100, None))
        self.assertIsNone(net_shares(100, 150))
        self.assertEqual(net_shares(100, 0), 100)

    def test_cagr_requires_positive_end(self):
        self.assertIsNone(cagr(100, 0, 3))
        self.assertEqual(basis_consistent_cagr([1, 2, 0], ["standalone"] * 3, 2), (None, "nonpositive"))
        self.assertEqual(basis_consistent_cagr([1, 2, 4], ["standalone", None, "standalone"], 2),
                         (None, "basis_unknown"))
        value, reason = basis_consistent_cagr([1, 2, 4], ["consolidated"] * 3, 2)
        self.assertAlmostEqual(value, 1.0)
        self.assertEqual(reason, "")

    def test_held_metric_with_value_is_rejected(self):
        with self.assertRaises(ValueError):
            growth_score({"sales_long_cagr": 0.1, "sales_long_cagr_hold_reason": "basis_change"})


class IrReactionSingleDefinitionTests(unittest.TestCase):
    def test_single_definition(self):
        source = inspect.getsource(rubric_scoring)
        self.assertEqual(source.count("def ir_reaction_score("), 1)

    def test_absent_count_is_missing(self):
        self.assertEqual(rubric_scoring.ir_reaction_score({})[0]["status"], "missing")
        self.assertEqual(rubric_scoring.ir_reaction_score({"target_ir_count_12m": 0})[0]["status"],
                         "not_applicable")


if __name__ == "__main__":
    unittest.main()
