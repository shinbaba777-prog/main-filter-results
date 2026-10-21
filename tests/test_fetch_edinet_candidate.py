"""Focused regression tests for scripts/fetch_edinet_candidate.py (no EDINET API calls)."""
import importlib.util
import tempfile
import unittest
import zipfile
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location(
    "fetch_edinet_candidate", Path(__file__).parents[1] / "scripts" / "fetch_edinet_candidate.py"
)
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


class CandidateRegressionTests(unittest.TestCase):
    def test_valid_existing_zip_is_reused_without_api_call(self):
        with tempfile.TemporaryDirectory() as tmp:
            old_out = mod.OUT
            mod.OUT = Path(tmp)
            try:
                mod.OUT.mkdir(parents=True, exist_ok=True)
                target = mod.OUT / "44060_S100ABC_xbrl_csv.zip"
                with zipfile.ZipFile(target, "w") as zf:
                    zf.writestr("sample.csv", "value\n1\n")
                row = {"docID": "S100ABC", "secCode": "44060"}
                with patch.object(mod, "api_get", side_effect=AssertionError("network must not be called")):
                    self.assertEqual(mod.download_csv_zip(row, "dummy-secret"), target)
            finally:
                mod.OUT = old_out

    def test_old_successful_listing_is_cached_and_reused(self):
        with tempfile.TemporaryDirectory() as tmp:
            old_out = mod.OUT
            mod.OUT = Path(tmp)
            try:
                day = date.today() - timedelta(days=240)
                expected = [{"docID": "S100ABC", "docTypeCode": "130"}]
                with patch.object(mod, "fetch_listing", return_value=expected) as fetch:
                    self.assertEqual(mod.cached_fetch_listing(day, "dummy-secret"), expected)
                    self.assertEqual(mod.cached_fetch_listing(day, "dummy-secret"), expected)
                    self.assertEqual(fetch.call_count, 1)
            finally:
                mod.OUT = old_out


if __name__ == "__main__":
    unittest.main()
