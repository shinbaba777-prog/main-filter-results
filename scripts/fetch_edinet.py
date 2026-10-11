#!/usr/bin/env python3
"""Fetch EDINET API v2 filing metadata; optionally download XBRL CSV ZIP for one security code.

The API key is read only from EDINET_API_KEY. Never print request URLs or the key.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import os
import sys
import time
import zipfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import requests

BASE = "https://api.edinet-fsa.go.jp/api/v2"
OUT = Path("data/edinet")
FIELDS = [
    "docID", "submitDateTime", "edinetCode", "secCode", "filerName",
    "docDescription", "docTypeCode", "periodStart", "periodEnd", "csvFlag",
    "legalStatus", "parentDocID", "withdrawalStatus",
]
ANNUAL_REPORT_CODES = {"120", "130"}  # 有価証券報告書 / 訂正有価証券報告書


def normalize_code(value: object) -> str:
    return "".join(ch for ch in str(value or "") if ch.isdigit())


def api_get(path: str, params: dict, api_key: str) -> requests.Response:
    response = requests.get(
        f"{BASE}/{path}",
        params={**params, "Subscription-Key": api_key},
        timeout=60,
    )
    response.raise_for_status()
    return response


def fetch_listing(day: date, api_key: str) -> list[dict]:
    response = api_get("documents.json", {"date": day.isoformat(), "type": "2"}, api_key)
    payload = response.json()
    if payload.get("metadata", {}).get("status") not in (None, "200"):
        raise RuntimeError(f"EDINET API returned status {payload.get('metadata', {}).get('status')}")
    return payload.get("results", [])


def write_metadata(rows: list[dict]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rows.sort(key=lambda r: (str(r.get("submitDateTime") or ""), str(r.get("docID") or "")), reverse=True)
    with (OUT / "documents.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    (OUT / "documents.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def download_csv_zip(row: dict, api_key: str) -> Path:
    doc_id = row.get("docID")
    if not doc_id:
        raise ValueError("Selected document has no docID")
    response = api_get(f"documents/{doc_id}", {"type": "5"}, api_key)
    content_type = response.headers.get("Content-Type", "").lower()
    if "json" in content_type:
        try:
            message = response.json().get("message", "unknown API error")
        except Exception:
            message = "unknown API error"
        raise RuntimeError(f"CSV download failed for {doc_id}: {message}")
    if not zipfile.is_zipfile(io.BytesIO(response.content)):
        raise RuntimeError(f"EDINET response for {doc_id} was not a ZIP archive")
    OUT.mkdir(parents=True, exist_ok=True)
    safe_name = f"{normalize_code(row.get('secCode')) or 'unknown'}_{doc_id}_xbrl_csv.zip"
    path = OUT / safe_name
    path.write_bytes(response.content)
    return path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=14, help="Days of listing metadata to refresh")
    parser.add_argument("--code", default="", help="Optional Japanese securities code, e.g. 44060 or 4406")
    parser.add_argument("--download-csv", action="store_true", help="Download the latest matching annual report CSV")
    parser.add_argument("--history-years", type=int, default=0, help="Scan up to 5 years of annual filings for --code")
    args = parser.parse_args()

    api_key = os.environ.get("EDINET_API_KEY", "").strip()
    if not api_key:
        print("ERROR: EDINET_API_KEY is not set. Add it as a GitHub Actions repository secret.", file=sys.stderr)
        return 2
    if not 1 <= args.days <= 365:
        print("ERROR: --days must be between 1 and 365.", file=sys.stderr)
        return 2
    if not 0 <= args.history_years <= 5:
        print("ERROR: --history-years must be between 0 and 5.", file=sys.stderr)
        return 2
    code = normalize_code(args.code)
    if args.history_years and (not args.download_csv or not code):
        print("ERROR: --history-years requires --download-csv and --code.", file=sys.stderr)
        return 2

    today = datetime.now(timezone.utc).date()
    rows: list[dict] = []
    for offset in range(args.days):
        day = today - timedelta(days=offset)
        try:
            rows.extend(fetch_listing(day, api_key))
        except requests.HTTPError as exc:
            print(f"Warning: listing request failed for {day}: HTTP {exc.response.status_code if exc.response else 'unknown'}")
        except (requests.RequestException, ValueError, RuntimeError) as exc:
            print(f"Warning: listing request failed for {day}: {type(exc).__name__}")
        time.sleep(0.25)

    unique = {str(row.get("docID")): row for row in rows if row.get("docID")}
    rows = list(unique.values())
    annual = [r for r in rows if str(r.get("docTypeCode", "")) in ANNUAL_REPORT_CODES]
    accepted_codes = {code, code + "0"} if len(code) == 4 else ({code} if code else set())
    matches = [r for r in annual if normalize_code(r.get("secCode")) in accepted_codes and str(r.get("csvFlag", "")) == "1" and str(r.get("legalStatus", "1")) in {"1", "2"}]
    print(f"Recent EDINET filing records: {len(rows)}; annual-report candidates: {len(annual)}")

    if args.history_years:
        # EDINET listing is date-scoped. Query weekdays concurrently with a small
        # worker pool: sequential requests can take many minutes due to per-request
        # network latency. Keep concurrency modest to avoid stressing the public API.
        from concurrent.futures import ThreadPoolExecutor, as_completed

        start_day = today - timedelta(days=365 * args.history_years)
        end_day = today - timedelta(days=args.days)
        scan_days = []
        day = start_day
        while day <= end_day:
            if day.weekday() < 5:
                scan_days.append(day)
            day += timedelta(days=1)

        historical_matches = []
        failed_days = []
        def fetch_historical_day(scan_day):
            return scan_day, fetch_listing(scan_day, api_key)

        with ThreadPoolExecutor(max_workers=12) as pool:
            futures = {pool.submit(fetch_historical_day, scan_day): scan_day for scan_day in scan_days}
            completed = 0
            for future in as_completed(futures):
                scan_day = futures[future]
                try:
                    _, listing = future.result()
                    historical_matches.extend(
                        r for r in listing
                        if str(r.get("docTypeCode", "")) in ANNUAL_REPORT_CODES
                        and normalize_code(r.get("secCode")) in accepted_codes
                        and str(r.get("csvFlag", "")) == "1"
                        and str(r.get("legalStatus", "1")) in {"1", "2"}
                    )
                except (requests.RequestException, ValueError, RuntimeError) as exc:
                    failed_days.append(scan_day)
                    print(f"Warning: historical listing request failed for {scan_day}: {type(exc).__name__}")
                completed += 1
                if completed % 100 == 0 or completed == len(scan_days):
                    print(f"Historical scan progress: {completed}/{len(scan_days)} weekdays processed; {len(historical_matches)} matching filings found so far.", flush=True)

        print(f"Historical scan: {len(scan_days) - len(failed_days)}/{len(scan_days)} weekday queries succeeded; {len(failed_days)} failed.")
        if failed_days:
            print("WARNING: Historical scan was incomplete; review failed dates before relying on year coverage.")
        by_period = {}
        for row in matches + historical_matches:
            period_end = str(row.get("periodEnd") or "")
            if not row.get("docID") or not period_end:
                continue
            old = by_period.get(period_end)
            if old is None or str(row.get("submitDateTime") or "") > str(old.get("submitDateTime") or ""):
                by_period[period_end] = row
        selected = sorted(by_period.values(), key=lambda r: str(r.get("periodEnd") or ""), reverse=True)[:args.history_years]
        if not selected:
            print(f"ERROR: no annual-report CSV filings found for securities code {code}.", file=sys.stderr)
            return 2
        print(f"Historical scan: {scanned} weekdays queried; {len(historical_matches)} matching records; {len(selected)} fiscal periods selected.")
        for row in reversed(selected):
            path = download_csv_zip(row, api_key)
            print(f"Downloaded annual-report CSV ZIP: {path} (periodEnd={row.get('periodEnd')})")
            time.sleep(0.25)
        if len(selected) < args.history_years:
            print("WARNING: Fewer fiscal periods were available than requested; missing years must not be treated as zero.")
    elif args.download_csv:
        if not code:
            print("ERROR: --download-csv requires --code.", file=sys.stderr)
            return 2
        if not matches:
            print(f"No downloadable annual-report CSV found for securities code {code} in the last {args.days} days.")
            print("Try --history-years 5 to scan older annual filings.")
            return 0
        matches.sort(key=lambda r: r.get("submitDateTime", ""), reverse=True)
        path = download_csv_zip(matches[0], api_key)
        print(f"Downloaded latest matching XBRL CSV ZIP: {path}")

    write_metadata(rows)
    print(f"Saved {len(rows)} recent EDINET filing records to data/edinet/documents.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
