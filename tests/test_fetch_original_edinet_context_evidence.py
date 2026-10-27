import io
import sys
import unittest
import zipfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from fetch_original_edinet_context_evidence import extract_instances

XBRL = b'''<xbrl xmlns="http://www.xbrl.org/2003/instance">
<context id="CurrentYearDuration"><entity><identifier scheme="x">44060</identifier></entity>
<period><startDate>2025-04-01</startDate><endDate>2026-03-31</endDate></period>
</context></xbrl>'''

def archive(files):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        for name, value in files.items():
            zf.writestr(name, value)
    return buffer.getvalue()

class OriginalEvidenceTests(unittest.TestCase):
    def test_extract_original_instance(self):
        result = extract_instances(archive({"XBRL/PublicDoc/sample.xbrl": XBRL}))
        self.assertEqual(result["XBRL/PublicDoc/sample.xbrl"]["CurrentYearDuration"]["end_date"], "2026-03-31")

    def test_skip_unrelated_xml(self):
        self.assertEqual(extract_instances(archive({"metadata.xml": b"<metadata/>"})), {})

    def test_reject_non_zip(self):
        with self.assertRaises(ValueError):
            extract_instances(b"not a zip")

if __name__ == "__main__":
    unittest.main()
