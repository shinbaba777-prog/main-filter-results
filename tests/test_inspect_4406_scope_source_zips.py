import tempfile
import unittest
import zipfile
from pathlib import Path
from scripts.inspect_4406_scope_source_zips import inspect

def fixture(folder):
    rows=[]
    for i in range(35):
        doc="DOC"+str(i//7)
        archive=folder/f"44060_{doc}_xbrl_csv.zip"
        if not archive.exists():
            with zipfile.ZipFile(archive,"w") as z:
                z.writestr("source.csv","element_id,context_id,value\nexample,CurrentYearDuration,1\n")
        rows.append({"document_id":doc,"source_csv":"source.csv","row_number":"2",
                     "element_id":"example","context_id":"CurrentYearDuration"})
    return {"unresolved_rows":rows,"approved_rows":0}

class ZipSourceTests(unittest.TestCase):
    def test_source_provenance_without_approval(self):
        with tempfile.TemporaryDirectory() as tmp:
            r=inspect(fixture(Path(tmp)),Path(tmp))
            self.assertEqual(r["source_csv_files_verified"],35)
            self.assertEqual(r["approved_rows"],0)
            self.assertFalse(r["scoring_eligible"])
    def test_tab_delimited_source_header(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp);f=fixture(folder)
            with zipfile.ZipFile(folder/"44060_DOC0_xbrl_csv.zip","w") as z:
                z.writestr("source.csv","要素ID\\t項目名\\tコンテキストID\\nexample\\t売上高\\tCurrentYearDuration\\n".encode("utf-16"))
            out=inspect(f,folder)
            self.assertEqual(out["rows"][0]["source_csv_columns"],["要素ID","項目名","コンテキストID"])
    def test_utf16_source_csv(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp);f=fixture(folder)
            with zipfile.ZipFile(folder/"44060_DOC0_xbrl_csv.zip","w") as z:
                z.writestr("source.csv","element_id,context_id,value\\nexample,CurrentYearDuration,1\\n".encode("utf-16"))
            self.assertEqual(inspect(f,folder)["source_csv_files_verified"],35)
    def test_missing_source_file_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            f=fixture(Path(tmp));f["unresolved_rows"][0]["source_csv"]="missing.csv"
            with self.assertRaises(ValueError):inspect(f,Path(tmp))
    def test_unexpected_approval_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            f=fixture(Path(tmp));f["approved_rows"]=1
            with self.assertRaises(ValueError):inspect(f,Path(tmp))

if __name__=="__main__":unittest.main()
