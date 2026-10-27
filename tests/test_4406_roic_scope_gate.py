#!/usr/bin/env python3
"""Unit tests: ROIC scope audit must never approve or conflate individual facts."""
import unittest
from scripts.audit_4406_roic_scope_gate import audit, REQUIRED

def fact(concept, context, member=None):
    dims = [] if member is None else [{"dimension":"ConsolidatedOrNonConsolidatedAxis","member":member}]
    return {"concept":concept,"context_id":context,
            "context":{"dimensions":dims,"period":{"instant":"2026-03-31"}},
            "value":"123","unit_ref":"JPY"}

class ScopeGateTests(unittest.TestCase):
    def test_complete_candidates_remain_blocked(self):
        rows=[fact(c,"CurrentYearDuration" if c in REQUIRED[:3] else "CurrentYearInstant") for c in REQUIRED]
        result=audit({"documents":[{"document_id":"S100YGXD","candidates":rows}]})
        self.assertEqual(result["documents"][0]["missing_required"],[])
        self.assertFalse(result["scoring_eligible"])
        self.assertFalse(result["publish_to_index"])
        self.assertEqual(result["approved_rows"],0)
        self.assertFalse(result["documents"][0]["roic_verified"])

    def test_nonconsolidated_lease_is_not_consolidated(self):
        rows=[fact("LeaseObligationsCL","CurrentYearInstant","jppfs_cor:NonConsolidatedMember")]
        result=audit({"documents":[{"document_id":"S100YGXD","candidates":rows}]})
        doc=result["documents"][0]
        self.assertIn("LeaseObligationsCL",doc["individual_lease_not_usable_for_consolidated_roic"])
        self.assertIn("LeaseObligationsCL",doc["unresolved_balances"])

    def test_explicit_nonconsolidated_required_fact_is_rejected(self):
        rows=[fact("NetAssets","CurrentYearInstant","jppfs_cor:NonConsolidatedMember")]
        result=audit({"documents":[{"document_id":"S100YGXD","candidates":rows}]})
        self.assertIn("NetAssets",result["documents"][0]["missing_required"])

    def test_conflicting_duplicate_is_flagged(self):\n        a=fact("NetAssets","CurrentYearInstant")\n        b=fact("NetAssets","CurrentYearInstant")\n        b["value"]="456"\n        result=audit({"documents":[{"document_id":"S100YGXD","candidates":[a,b]}]})\n        self.assertIn("NetAssets",result["documents"][0]["conflicting_duplicate_concepts"])\n        self.assertEqual(result["approved_rows"],0)\n\n    def test_nonstandard_context_not_accepted(self):
        rows=[fact("NetAssets","Prior1YearInstant")]
        result=audit({"documents":[{"document_id":"S100YGXD","candidates":rows}]})
        self.assertIn("NetAssets",result["documents"][0]["missing_required"])

if __name__ == "__main__":
    unittest.main()
