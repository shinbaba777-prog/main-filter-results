#!/usr/bin/env python3
"""Regression tests for the provisional ROIC gate: review-only, no publishing."""
import unittest
from decimal import Decimal as D
from scripts.audit_4406_roic_arithmetic_review import calculate,ROWS

class ROICGateTests(unittest.TestCase):
    def test_never_approves_or_publishes(self):
        result=calculate()
        self.assertFalse(result["scoring_eligible"])
        self.assertFalse(result["publish_to_index"])
        self.assertEqual(result["approved_rows"],0)
    def test_all_years_and_year_end_capital(self):
        result=calculate()
        self.assertEqual([r["fiscal_year"] for r in result["rows"]],list(range(2021,2027)))
        self.assertAlmostEqual(result["rows"][-1]["invested_capital_million_jpy"],24135.4166667,places=4)
    def test_negative_pretax_uses_fallback(self):
        self.assertEqual(ROWS[2][-1],D("0.306"))
    def test_tax_uses_total_not_current_tax(self):
        self.assertEqual(ROWS[5][-1],D(32)/D(679))
    def test_2026_is_provisional(self):
        result=calculate()
        self.assertGreater(result["rows"][-1]["roic_percent"],2.2)
        self.assertLess(result["rows"][-1]["roic_percent"],2.3)

if __name__=="__main__":
    unittest.main()
