import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from check_original_xbrl_contexts import context_details, inspect

XML = b'''<xbrl xmlns="http://www.xbrl.org/2003/instance"
xmlns:xbrldi="http://xbrl.org/2006/xbrldi">
<context id="CurrentYearDuration"><entity><identifier scheme="s">44060</identifier>
<segment><xbrldi:explicitMember dimension="scope">Consolidated</xbrldi:explicitMember>
</segment></entity><period><startDate>2025-04-01</startDate>
<endDate>2026-03-31</endDate></period></context></xbrl>'''

class OriginalXbrlTests(unittest.TestCase):
    def test_parse_actual_period_and_dimension(self):
        c = context_details(XML)["CurrentYearDuration"]
        self.assertEqual(c["start_date"], "2025-04-01")
        self.assertEqual(c["end_date"], "2026-03-31")
        self.assertEqual(c["dimensions"][0]["member"], "Consolidated")

    def test_missing_original_blocks(self):
        result = inspect([{"source_zip": "a.zip", "context_id": "CurrentYearDuration"}], {})
        self.assertEqual(result["missing_evidence_rows"], 1)
        self.assertFalse(result["scoring_ready"])

    def test_present_context_still_not_approved(self):
        result = inspect([{"source_zip": "a.zip", "context_id": "CurrentYearDuration"}],
                         {"a.zip": context_details(XML)})
        self.assertEqual(result["contexts_found"], 1)
        self.assertFalse(result["scoring_ready"])

if __name__ == "__main__":
    unittest.main()
