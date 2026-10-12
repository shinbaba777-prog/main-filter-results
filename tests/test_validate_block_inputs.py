import unittest
from scripts.validate_block_inputs import validate_buy_block_inputs

class BuyBlockInputValidationTests(unittest.TestCase):
    def complete(self):
        return {
            "shorts_direction_zero": False,
            "shorts_applicable": True,
            "ocf_ni_zero": False,
            "dilution_zero": False,
            "roic_below_h": False,
            "roic_unavailable": False,
            "short_type_a": False,
            "peg_over_2": False,
            "industry_per_over_130": False,
            "base_upside_pct": 25,
        }

    def test_complete_verified_inputs_pass(self):
        self.assertEqual(validate_buy_block_inputs(self.complete()), [])

    def test_missing_boolean_is_not_silently_false(self):
        values = self.complete()
        del values["short_type_a"]
        self.assertTrue(any("short_type_a is absent" in e for e in validate_buy_block_inputs(values)))

    def test_null_boolean_is_rejected(self):
        values = self.complete()
        values["roic_below_h"] = None
        self.assertTrue(any("roic_below_h must be true/false" in e for e in validate_buy_block_inputs(values)))

    def test_roic_unknown_does_not_become_roic_below_h(self):
        values = self.complete()
        values["roic_unavailable"] = True
        values["roic_below_h"] = False
        self.assertEqual(validate_buy_block_inputs(values), [])

    def test_contradictory_roic_flags_rejected(self):
        values = self.complete()
        values["roic_unavailable"] = True
        values["roic_below_h"] = True
        self.assertTrue(any("cannot both be true" in e for e in validate_buy_block_inputs(values)))

    def test_unassessed_scenario_is_rejected(self):
        values = self.complete()
        values["base_upside_pct"] = None
        self.assertTrue(any("must be a finite number" in e for e in validate_buy_block_inputs(values)))

    def test_non_finite_scenario_is_rejected(self):
        values = self.complete()
        values["base_upside_pct"] = "nan"
        self.assertTrue(any("must be a finite number" in e for e in validate_buy_block_inputs(values)))

if __name__ == "__main__":
    unittest.main()
