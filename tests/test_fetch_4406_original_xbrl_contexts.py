import io
import unittest
import zipfile
from scripts.fetch_4406_original_xbrl_contexts import inspect_zip

XBRL='''<?xml version="1.0" encoding="UTF-8"?>
<xbrli:xbrl xmlns:xbrli="http://www.xbrl.org/2003/instance"
xmlns:xbrldi="http://xbrl.org/2006/xbrldi">
<xbrli:context id="CurrentYearDuration"><xbrli:entity><xbrli:identifier scheme="test">44060</xbrli:identifier></xbrli:entity><xbrli:period><xbrli:startDate>2025-04-01</xbrli:startDate><xbrli:endDate>2026-03-31</xbrli:endDate></xbrli:period></xbrli:context>
<xbrli:context id="ConsolidatedCurrentYear"><xbrli:entity><xbrli:identifier scheme="test">44060</xbrli:identifier><xbrli:segment><xbrldi:explicitMember dimension="test:ConsolidationAxis">test:ConsolidatedMember</xbrldi:explicitMember></xbrli:segment></xbrli:entity><xbrli:period><xbrli:instant>2026-03-31</xbrli:instant></xbrli:period></xbrli:context>
</xbrli:xbrl>'''

def archive(payload=XBRL,filename="XBRL/PublicDoc/sample.xbrl"):
    buf=io.BytesIO()
    with zipfile.ZipFile(buf,"w") as z:z.writestr(filename,payload)
    return buf.getvalue()

class OriginalXbrlTests(unittest.TestCase):
    def test_extract_contexts_without_approval(self):
        r=inspect_zip(archive(),"TEST")
        self.assertEqual(r["context_count"],2)
        self.assertFalse(r["scoring_eligible"])
        self.assertEqual(r["scope_status"],"REVIEW_REQUIRED")
        self.assertEqual(r["contexts"][1]["dimensions"][0]["member"],"test:ConsolidatedMember")
    def test_reject_nonzip(self):
        with self.assertRaises(ValueError):inspect_zip(b'{"message":"Too Many Requests"}',"TEST")
    def test_reject_csv_only_zip(self):
        with self.assertRaises(ValueError):inspect_zip(archive("x","XBRL_TO_CSV/sample.csv"),"TEST")
    def test_reject_xbrl_without_contexts(self):
        with self.assertRaises(ValueError):inspect_zip(archive("<xbrl/>"),"TEST")

if __name__=="__main__":unittest.main()
