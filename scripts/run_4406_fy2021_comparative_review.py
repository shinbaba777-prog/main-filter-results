#!/usr/bin/env python3
"""Fetch FY2022 original filing to audit FY2021 comparative facts."""
import os
import urllib.parse
import urllib.request
from scripts.extract_4406_fy2021_comparative_facts import extract, save

def main():
    key = os.environ.get("EDINET_API_KEY", "").strip()
    if not key:
        raise SystemExit("BLOCKED: missing EDINET_API_KEY")
    url = ("https://api.edinet-fsa.go.jp/api/v2/documents/S100OK43?"
           + urllib.parse.urlencode({"type": "1", "Subscription-Key": key}))
    try:
        with urllib.request.urlopen(urllib.request.Request(url), timeout=35) as response:
            payload = response.read(80000001)
        if len(payload) > 80000000:
            raise ValueError("Oversized ZIP")
        result = extract(payload)
    except Exception as exc:
        print("BLOCKED: " + type(exc).__name__)
        raise SystemExit(2) from None
    save(result, "artifacts/4406_fy2021_comparative_review.json")
    print("FY2021 original comparative candidate facts:", len(result["facts"]))
    print("REVIEW ONLY; no scoring or publishing")

if __name__ == "__main__":
    main()
