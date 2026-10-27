#!/usr/bin/env python3
"""Fetch original EDINET XBRL instance context evidence for manifest filings.

Only writes to an explicitly supplied local output directory. Never commits
source archives or keys; does not approve financial facts.
"""
import argparse
import io
import json
import os
import re
import subprocess
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from fetch_edinet import api_get, DOC_RE
from check_original_xbrl_contexts import context_details

XBRLI = "{http://www.xbrl.org/2003/instance}"
MAX_ARCHIVE_BYTES = 80 * 1024 * 1024
MAX_MEMBER_BYTES = 15 * 1024 * 1024

def extract_instances(payload):
    if len(payload) > MAX_ARCHIVE_BYTES or not zipfile.is_zipfile(io.BytesIO(payload)):
        raise ValueError("invalid or oversized original XBRL archive")
    results = {}
    with zipfile.ZipFile(io.BytesIO(payload)) as zf:
        for item in zf.infolist():
            if not item.filename.lower().endswith((".xbrl", ".xml")):
                continue
            if item.file_size > MAX_MEMBER_BYTES:
                continue
            try:
                raw = zf.read(item)
                root = ET.fromstring(raw)
                if root.tag != XBRLI + "xbrl":
                    continue
                contexts = context_details(raw)
                if contexts:
                    results[item.filename] = contexts
            except (ET.ParseError, ValueError, RuntimeError, zipfile.BadZipFile):
                continue
    return results

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--check-audit", action="store_true", help="Run the read-only 680-row context evidence gate after retrieval")
    args = parser.parse_args()
    key = os.environ.get("EDINET_API_KEY", "").strip()
    if not key:
        print("BLOCKED: EDINET_API_KEY missing")
        return 2
    manifest = json.loads((args.root / "data/edinet/download_manifest.json").read_text(encoding="utf-8"))
    reports = []
    for period in manifest.get("periods", []):
        doc_id = period.get("docID", "")
        if not DOC_RE.fullmatch(doc_id):
            reports.append({"docID": "INVALID", "status": "BLOCKED"})
            continue
        try:
            response = api_get(f"documents/{doc_id}", {"type": "1"}, key, f"Original XBRL {doc_id}")
            instances = extract_instances(response.content)
            status = "CONTEXTS_FOUND" if instances else "NO_XBRL_INSTANCES"
            # Store context metadata, not raw archives or sensitive API responses.
            if instances:
                args.output_dir.mkdir(parents=True, exist_ok=True)
                output = args.output_dir / (doc_id + ".contexts.json")
                output.write_text(json.dumps(instances, ensure_ascii=False, indent=2), encoding="utf-8")
            reports.append({"docID": doc_id, "status": status,
                            "instance_files": len(instances),
                            "context_count": sum(len(v) for v in instances.values())})
        except Exception as exc:
            # No request URL or exception text (may include key).
            reports.append({"docID": doc_id, "status": "BLOCKED", "error_type": type(exc).__name__})
    print(json.dumps({"status": "REVIEW_REQUIRED", "scoring_ready": False,
                      "filings": reports}, ensure_ascii=False, indent=2))
    fetch_complete = bool(reports and all(x["status"] == "CONTEXTS_FOUND" for x in reports))
    if args.check_audit:
        command = [sys.executable, str(Path(__file__).with_name("check_original_xbrl_contexts.py")),
                   "--root", str(args.root), "--evidence-dir", str(args.output_dir)]
        check = subprocess.run(command, check=False)
        return 0 if fetch_complete and check.returncode == 0 else 2
    return 0 if fetch_complete else 2

if __name__ == "__main__":
    raise SystemExit(main())
