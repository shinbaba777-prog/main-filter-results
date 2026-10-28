import io
import unittest
import zipfile
from scripts.inspect_4406_original_xbrl_facts import inspect_original_zip

XBRL='''<xbrli:xbrl xmlns:xbrli="http://www.xbrl.org/2003/instance"
xmlns:jpcrp_cor="http://example.org/jpcrp"
xmlns:xbrldi="http://xbrl.org/2006/xbrldi">
<xbrli:context id="CurrentYearDuration"><xbrli:entity><xbrli:identifier scheme="test">44060</xbrli:identifier></xbrli:entity><xbrli:period><xbrli:startDate>2025-04-01</xbrli:startDate><xbrli:endDate>2026-03-31</xbrli:endDate></xbrli:period></xbrli:context>
<xbrli:context id="CurrentYearDuration_NonConsolidatedMember"><xbrli:entity><xbrli:identifier scheme="test">44060</xbrli:identifier><xbrli:segment><xbrldi:explicitMember dimension="test:ConsolidatedOrNonConsolidatedAxis">test:NonConsolidatedMember</xbrldi:explicitMember></xbrli:segment></xbrli:entity><xbrli:period><xbrli:startDate>2025-04-01</xbrli:startDate><xbrli:endDate>2026-03-31</xbrli:endDate></xbrli:period></xbrli:context>
<jpcrp_cor:NetSalesSummaryOfBusinessResults contextRef="CurrentYearDuration" unitRef="JPY">100</jpcrp_cor:NetSalesSummaryOfBusinessResults>
<jpcrp_cor:NetSalesSummaryOfBusinessResults contextRef="CurrentYearDuration_NonConsolidatedMember" unitRef="JPY">90</jpcrp_cor:NetSalesSummaryOfBusinessResults>
</xbrli:xbrl>'''

def zipbytes(name="XBRL/PublicDoc/example.xbrl",content=XBRL):
    out=io.BytesIO()
    with zipfile.ZipFile(out,"w") as archive:archive.writestr(name,content)
    return out.getvalue()

class OriginalFactsTests(unittest.TestCase):
    def test_fact_context_pair(self):
        result=inspect_original_zip(zipbytes(),"SAMPLE")
        self.assertEqual(result["current_year_facts"],1)
        self.assertEqual(len(result["facts"]),2)
        self.assertEqual(result["facts"][0]["dimensions"],[])
        self.assertEqual(result["facts"][1]["dimensions"][0]["member"],"test:NonConsolidatedMember")
        self.assertEqual(result["approved_rows"],0)
    def test_reject_api_error(self):
        with self.assertRaises(ValueError):inspect_original_zip(b'{"message":"Too Many Requests"}',"SAMPLE")
    def test_reject_no_facts(self):
        with self.assertRaises(ValueError):inspect_original_zip(zipbytes("XBRL/PublicDoc/a.xbrl","<xbrl/>"),"SAMPLE")
    def test_linkbase_filename_inventory(self):
        buf=io.BytesIO()
        with zipfile.ZipFile(buf,"w") as z:
            z.writestr("XBRL/PublicDoc/a.xbrl",XBRL)
            z.writestr("XBRL/PublicDoc/a_pre.xml","<linkbase/>")
        result=inspect_original_zip(buf.getvalue(),"SAMPLE")
        self.assertEqual(len(result["linkbase_candidates"]),1)

if __name__=="__main__":unittest.main()
