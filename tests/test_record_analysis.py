import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "record_analysis.py"
GROUPS = [
    ("growth", 15), ("profitability", 15), ("roic_capital", 15),
    ("finance_cf", 10), ("eps_growth", 10), ("valuation", 15),
    ("competitive_advantage", 5), ("subsidiaries_ma", 3),
    ("shorts_supply", 7), ("ir_reaction", 5),
]
BUY_BLOCKS = {
    "shorts_direction_zero": False, "shorts_applicable": False,
    "ocf_ni_zero": False, "dilution_zero": False,
    "roic_below_h": False, "roic_unavailable": False,
    "short_type_a": False, "peg_over_2": False,
    "industry_per_over_130": False, "base_upside_pct": 35,
}

def payload(code="9999", date="2026-10-12"):
    return {
        "code": code, "company": "テスト株式会社", "analysis_date": date,
        "items": [
            {"key": group, "group": group, "points": maximum,
             "max_points": maximum, "status": "scored",
             "evidence": "test fixture", "source": "unit test"}
            for group, maximum in GROUPS
        ],
        "buy_block_inputs": BUY_BLOCKS,
    }

class RecordAnalysisTests(unittest.TestCase):
    def run_record(self, payload_path, csv_path, *extra):
        return subprocess.run(
            [sys.executable, str(SCRIPT), str(payload_path), "--index", str(csv_path), *extra],
            cwd=ROOT, text=True, capture_output=True, check=False,
        )

    def test_appends_well_formed_csv_rows_with_newlines(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source = base / "analysis.json"
            target = base / "index.csv"
            source.write_text(json.dumps(payload(), ensure_ascii=False), encoding="utf-8")
            first = self.run_record(source, target)
            self.assertEqual(first.returncode, 0, first.stderr)
            second_payload = payload(code="8888", date="2026-10-13")
            source.write_text(json.dumps(second_payload, ensure_ascii=False), encoding="utf-8")
            second = self.run_record(source, target)
            self.assertEqual(second.returncode, 0, second.stderr)
            with target.open(encoding="utf-8", newline="") as f:
                rows = list(csv.DictReader(f))
            self.assertEqual(len(rows), 2)
            self.assertEqual([r["code"] for r in rows], ["9999", "8888"])
            self.assertEqual(rows[0]["company"], "テスト株式会社")

    def test_duplicate_code_date_version_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source = base / "analysis.json"
            target = base / "index.csv"
            source.write_text(json.dumps(payload(), ensure_ascii=False), encoding="utf-8")
            first = self.run_record(source, target)
            self.assertEqual(first.returncode, 0, first.stderr)
            duplicate = self.run_record(source, target)
            self.assertEqual(duplicate.returncode, 3)
            self.assertIn("Duplicate", duplicate.stderr)
            with target.open(encoding="utf-8", newline="") as f:
                self.assertEqual(len(list(csv.DictReader(f))), 1)

    def test_dry_run_does_not_create_csv(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source = base / "analysis.json"
            target = base / "index.csv"
            source.write_text(json.dumps(payload(), ensure_ascii=False), encoding="utf-8")
            result = self.run_record(source, target, "--dry-run")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(target.exists())

if __name__ == "__main__":
    unittest.main()
