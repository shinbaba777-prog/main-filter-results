import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/check_original_xbrl_contexts.py"

class EvidenceIntegrationTests(unittest.TestCase):
    def make_fixture(self, root, evidence, provided=True):
        base = root / "data/edinet"
        (base / "extracted").mkdir(parents=True)
        manifest = {"periods": [{"file": "44060_S100OK43_xbrl_csv.zip", "docID": "S100OK43"}]}
        (base / "download_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        with (base / "extracted/financial_metric_audit.csv").open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["source_zip", "context_id"])
            writer.writeheader()
            writer.writerow({"source_zip": "44060_S100OK43_xbrl_csv.zip",
                             "context_id": "CurrentYearDuration"})
        evidence.mkdir()
        if provided:
            (evidence / "S100OK43.contexts.json").write_text(json.dumps({
                "XBRL/PublicDoc/one.xbrl": {
                    "CurrentYearDuration": {
                        "start_date": "2021-04-01", "end_date": "2022-03-31",
                        "instant": None, "dimensions": []
                    }
                }
            }), encoding="utf-8")

    def run_gate(self, root, evidence):
        return subprocess.run([sys.executable, str(SCRIPT), "--root", str(root),
                               "--evidence-dir", str(evidence)],
                              capture_output=True, text=True)

    def test_original_json_connects_to_audit(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evidence = root / "evidence"
            self.make_fixture(root, evidence)
            result = self.run_gate(root, evidence)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["contexts_found"], 1)
            self.assertFalse(payload["scoring_ready"])

    def test_missing_original_evidence_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evidence = root / "evidence"
            self.make_fixture(root, evidence, provided=False)
            result = self.run_gate(root, evidence)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(json.loads(result.stdout)["missing_evidence_rows"], 1)

if __name__ == "__main__":
    unittest.main()
