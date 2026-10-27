#!/usr/bin/env python3
"""Read-only source-backed market snapshot. No scoring or changes to index.csv."""
import argparse
import datetime as dt
import html
from html.parser import HTMLParser
import json
import re
import urllib.request
from pathlib import Path

URLS = {
    "yahoo": "https://finance.yahoo.co.jp/quote/{code}.T",
    "irbank": "https://irbank.net/{code}",
    "company_ir": "https://www.nj-chem.co.jp/app/ir",
    "company_highlights": "https://www.nj-chem.co.jp/ir/highlight.php",
}

class TextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
    def handle_data(self, data):
        s = html.unescape(data).strip()
        if s:
            self.parts.append(s)

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; ResearchSnapshot/1.0)"})
    with urllib.request.urlopen(req, timeout=18) as response:
        raw = response.read(2_000_000)
        charset = response.headers.get_content_charset() or "utf-8"
    parser = TextParser()
    parser.feed(raw.decode(charset, errors="replace"))
    return " ".join(parser.parts)

def parse_value(text, label):
    # Only label-bound values are eligible. Fail closed on layout changes.
    pattern = re.escape(label) + r"\s*(?:用語\s*)?[:：]?\s*([0-9,]+(?:\.[0-9]+)?)"
    match = re.search(pattern, text)
    return match.group(1) if match else None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--code", default="4406", choices=["4406"], help="Only verified company-specific links supported")
    ap.add_argument("--output", default="artifacts/source_snapshots/4406.json")
    args = ap.parse_args()
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    results = {}
    for name, template in URLS.items():
        url = template.format(code=args.code)
        try:
            content = fetch(url)
            results[name] = {
                "url": url, "retrieved_at_utc": now, "status": "FETCHED",
                "metrics": ({
                    "per_forecast": parse_value(content, "PER（会社予想）"),
                    "pbr_actual": parse_value(content, "PBR（実績）"),
                    "market_cap_million_jpy": parse_value(content, "時価総額"),
                    "forecast_eps_jpy": parse_value(content, "EPS（会社予想）"),
                } if name == "yahoo" else {}),
                "content_length_chars": len(content),
            }
        except Exception as exc:
            results[name] = {"url": url, "retrieved_at_utc": now, "status": "FETCH_FAILED", "error_type": type(exc).__name__, "metrics": {}}
    payload = {"security_code": args.code, "generated_at_utc": now,
               "status": "REVIEW_REQUIRED", "scoring_eligible": False,
               "note": "Website layout and financial period must be manually verified. No zero filling.",
               "sources": results}
    dest = Path(args.output)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Saved review-only snapshot: {dest}")
    print("Fetched:", sum(x["status"] == "FETCHED" for x in results.values()), "/", len(results))

if __name__ == "__main__":
    main()
