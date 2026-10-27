#!/usr/bin/env python3
"""Fetch original EDINET filings for review-only ROIC fact candidates."""
import os
import time
import urllib.parse
import urllib.request
from pathlib import Path
from scripts.extract_4406_roic_original_xbrl import extract_candidates, save_review

DOCS = ("S100OK43", "S100R83V", "S100TUAP", "S100W17N", "S100YGXD")

def main():
    key = os.environ.get("EDINET_API_KEY", "").strip()
    if not key:
        raise SystemExit("BLOCKED: EDINET_API_KEY missing")
    documents = []
    for doc in DOCS:
        url = "https://api.edinet-fsa.go.jp/api/v2/documents/" + doc + "?" + urllib.parse.urlencode(
            {"type": "1", "Subscription-Key": key})
        try:
            with urllib.request.urlopen(
                urllib.request.Request(url, headers={"Accept": "application/zip"}), timeout=35
            ) as response:
                payload = response.read(80_000_001)
            if len(payload) > 80_000_000:
                raise ValueError("ZIP exceeds limit")
            record = extract_candidates(payload, doc)
        except Exception as exc:
            # No exception message or URL: both may leak credentials.
            print(doc + ": BLOCKED (" + type(exc).__name__ + ")")
            raise SystemExit(2) from None
        documents.append(record)
        print(doc + ": ROIC candidates=" + str(record["candidate_count"]))
        time.sleep(0.4)
    result = save_review(documents, Path("artifacts/4406_roic_original_xbrl_candidates.json"))
    assert result["approved_rows"] == 0 and not result["scoring_eligible"]
    print("PASS: ROIC candidate inventory only; approved=0")

if __name__ == "__main__":
    main()
