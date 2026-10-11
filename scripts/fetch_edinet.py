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
import re
import random
import sys
import tempfile
import time
import unicodedata
import zipfile
from email.utils import parsedate_to_datetime
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
CODE_RE = re.compile(r"^[0-9][0-9A-Z][0-9][0-9A-Z][0-9A-Z]?$")
DOC_RE = re.compile(r"^[A-Za-z0-9_-]{5,32}$")
class EdinetError(RuntimeError): pass
class EdinetAuthError(EdinetError): pass
class Throttle:
    def __init__(self, interval=0.4):
        import threading
        self.interval, self.lock, self.next_at, self.pause_until = interval, threading.Lock(), 0.0, 0.0
    def wait(self):
        with self.lock:
            now = time.monotonic(); target = max(self.next_at, self.pause_until)
            if target > now: time.sleep(target-now); now = time.monotonic()
            self.next_at = now + self.interval
    def pause(self, seconds):
        with self.lock: self.pause_until = max(self.pause_until, time.monotonic()+seconds)
THROTTLE = Throttle()
RETRYABLE = {429, 500, 502, 503, 504}
AUTH_ERRORS = {401, 403}
def api_error(response):
    try: body = response.json()
    except Exception: return None, ""
    if not isinstance(body, dict): return None, ""
    status = body.get("StatusCode", body.get("statusCode"))
    if status is None and isinstance(body.get("metadata"), dict): status = body["metadata"].get("status")
    try: status = int(status) if status is not None else None
    except (ValueError, TypeError): status = None
    return status, str(body.get("message", body.get("Message", "")))[:300]
def retry_after_seconds(value):
    if not value: return None
    try: return min(120.0, max(1.0, float(value.strip())))
    except (ValueError, AttributeError):
        try:
            dt = parsedate_to_datetime(value)
            if dt.tzinfo is None: dt = dt.replace(tzinfo=timezone.utc)
            return min(120.0, max(1.0, (dt-datetime.now(timezone.utc)).total_seconds()))
        except Exception: return None


def normalize_code(value: object) -> str:
    text = unicodedata.normalize("NFKC", str(value or "")).strip().upper()
    return text if CODE_RE.fullmatch(text) else ""


def api_get(path: str, params: dict, api_key: str, label: str = "EDINET request") -> requests.Response:
    url = f"{BASE}/{path}"
    request_params = {**params, "Subscription-Key": api_key}
    for attempt in range(6):
        THROTTLE.wait()
        try:
            response = requests.get(url, params=request_params, timeout=(10, 60))
        except requests.RequestException as exc:
            if attempt == 5: raise EdinetError(f"{label}: network request failed ({type(exc).__name__})") from None
            delay = min(120.0, 3.0 * (2 ** attempt) + random.uniform(0, 1.0))
            print(f"{label}: network error {type(exc).__name__}; retry {attempt+1}/6 in {delay:.1f}s", flush=True)
            time.sleep(delay); continue
        body_status, message = api_error(response)
        status = body_status if response.status_code == 200 and body_status not in (None, 200) else response.status_code
        if status == 200: return response
        last = f"HTTP {response.status_code}, API status {body_status}, message={message!r}"
        if status in AUTH_ERRORS: raise EdinetAuthError(f"{label}: authentication/permission failure ({last})") from None
        if status not in RETRYABLE: raise EdinetError(f"{label}: request rejected ({last})") from None
        if attempt == 5: raise EdinetError(f"{label}: retries exhausted ({last})") from None
        delay = retry_after_seconds(response.headers.get("Retry-After")) or min(120.0, 3.0 * (2 ** attempt) + random.uniform(0, 1.0))
        THROTTLE.pause(delay)
        print(f"{label}: retryable response ({last}); retry {attempt+1}/6 in {delay:.1f}s", flush=True)
    raise EdinetError(f"{label}: retries exhausted") from None


def fetch_listing(day: date, api_key: str) -> list[dict]:
    response = api_get("documents.json", {"date": day.isoformat(), "type": "2"}, api_key, f"listing {day}")
    try: payload = response.json()
    except ValueError: raise EdinetError(f"listing {day}: invalid JSON response") from None
    if not isinstance(payload, dict): raise EdinetError(f"listing {day}: response is not an object")
    metadata = payload.get("metadata")
    if not isinstance(metadata, dict) or str(metadata.get("status")) != "200":
        status, message = api_error(response)
        raise EdinetError(f"listing {day}: metadata.status=200 required; API status={status}, message={message!r}")
    results = payload.get("results")
    if not isinstance(results, list): raise EdinetError(f"listing {day}: results missing or not a list")
    count = metadata.get("resultset", {}).get("count") if isinstance(metadata.get("resultset"), dict) else None
    if count is not None:
        try:
            if int(count) != len(results): raise EdinetError(f"listing {day}: result count mismatch ({count} != {len(results)})")
        except (ValueError, TypeError): raise EdinetError(f"listing {day}: invalid result count") from None
    return results


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
    doc_id = str(row.get("docID") or "")
    if not DOC_RE.fullmatch(doc_id): raise EdinetError("Selected document has invalid docID")
    response = api_get(f"documents/{doc_id}", {"type": "5"}, api_key, f"CSV download {doc_id}")
    if "json" in response.headers.get("Content-Type", "").lower():
        _, message = api_error(response)
        raise EdinetError(f"CSV download failed for {doc_id}: {message or 'JSON response instead of ZIP'}")
    payload = io.BytesIO(response.content)
    if not zipfile.is_zipfile(payload): raise EdinetError(f"EDINET response for {doc_id} was not a ZIP archive")
    payload.seek(0)
    try:
        with zipfile.ZipFile(payload) as zf:
            if zf.testzip(): raise EdinetError(f"EDINET ZIP for {doc_id} failed CRC validation")
    except zipfile.BadZipFile: raise EdinetError(f"EDINET ZIP for {doc_id} is corrupt") from None
    code = normalize_code(row.get("secCode")) or "unknown"
    path = OUT / f"{code}_{doc_id}_xbrl_csv.zip"
    OUT.mkdir(parents=True, exist_ok=True)
    if path.exists():
        try:
            with zipfile.ZipFile(path) as zf:
                if zf.testzip() is None: return path
        except (zipfile.BadZipFile, OSError): pass
    fd, temp_name = tempfile.mkstemp(prefix=".edinet-", suffix=".tmp", dir=OUT)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(response.content); f.flush(); os.fsync(f.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name): os.unlink(temp_name)
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
    if args.code and not code:
        print("ERROR: invalid securities code; use a valid 4/5-character numeric or alphanumeric code.", file=sys.stderr)
        return 2
    if args.history_years and (not args.download_csv or not code):
        print("ERROR: --history-years requires --download-csv and --code.", file=sys.stderr)
        return 2

    from zoneinfo import ZoneInfo
    today = datetime.now(ZoneInfo("Asia/Tokyo")).date()
    rows: list[dict] = []
    for offset in range(args.days):
        day = today - timedelta(days=offset)
        try:
            rows.extend(fetch_listing(day, api_key))
        except (requests.RequestException, ValueError, RuntimeError) as exc:
            print(f"ERROR: listing request failed for {day}: {type(exc).__name__}; preserving previous metadata.", file=sys.stderr, flush=True)
            return 3
        time.sleep(0.25)

    unique = {str(row.get("docID")): row for row in rows if row.get("docID")}
    rows = list(unique.values())
    annual = [r for r in rows if str(r.get("docTypeCode", "")) in ANNUAL_REPORT_CODES]
    accepted_codes = {code, code + "0"} if len(code) == 4 and code.isdigit() else ({code} if code else set())
    matches = [r for r in annual if normalize_code(r.get("secCode")) in accepted_codes and str(r.get("csvFlag", "")) == "1" and str(r.get("legalStatus", "1")) in {"1", "2"}]
    print(f"Recent EDINET filing records: {len(rows)}; annual-report candidates: {len(annual)}")

    if args.history_years:
        # EDINET listing is date-scoped. Query weekdays concurrently with a small
        # worker pool: sequential requests can take many minutes due to per-request
        # network latency. Keep concurrency modest to avoid stressing the public API.
        from concurrent.futures import ThreadPoolExecutor, as_completed

        start_day = today - timedelta(days=365 * args.history_years + 120)
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

        with ThreadPoolExecutor(max_workers=3) as pool:
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
        print(f"Historical scan: {len(scan_days)} weekdays queried; {len(historical_matches)} matching records; {len(selected)} fiscal periods selected.", flush=True)
        manifest = {"requested_code": code, "requested_periods": args.history_years, "status": "incomplete", "periods": [], "gaps": [], "failed_scan_dates": [d.isoformat() for d in failed_days], "amendments": []}
        for row in historical_matches + matches:
            if str(row.get("docTypeCode", "")) == "130":
                manifest["amendments"].append({"docID": row.get("docID"), "parentDocID": row.get("parentDocID"), "periodEnd": row.get("periodEnd") or "", "status": "needs_review"})
        downloaded = 0
        for row in reversed(selected):
            item = {"periodEnd": row.get("periodEnd") or "", "docID": row.get("docID"), "status": "missing", "reason": ""}
            try:
                path = download_csv_zip(row, api_key)
                item.update({"status": "downloaded", "file": path.name})
                downloaded += 1
                print(f"Downloaded annual-report CSV ZIP: {path} (periodEnd={row.get('periodEnd')})", flush=True)
            except (requests.RequestException, ValueError, RuntimeError, OSError) as exc:
                item["reason"] = f"{type(exc).__name__}: {str(exc)[:200]}"
                print(f"ERROR: download failed for period {item['periodEnd']}: {item['reason']}", file=sys.stderr, flush=True)
            manifest["periods"].append(item)
            time.sleep(2.0)
        manifest["periods"].sort(key=lambda p: p.get("periodEnd", ""))
        dates = [p["periodEnd"] for p in manifest["periods"] if p.get("periodEnd")]
        for left, right in zip(dates, dates[1:]):
            try:
                if (date.fromisoformat(right)-date.fromisoformat(left)).days > 400:
                    manifest["gaps"].append({"from": left, "to": right, "reason": "period_gap_over_400_days"})
            except ValueError:
                manifest["gaps"].append({"from": left, "to": right, "reason": "invalid_period_end"})
        if failed_days or downloaded < len(selected) or len(selected) < args.history_years or manifest["gaps"]:
            manifest["status"] = "incomplete"
        elif len(selected) == args.history_years:
            manifest["status"] = "complete"
        else:
            manifest["status"] = "complete_short_history"
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / "download_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"download_manifest": manifest}, ensure_ascii=False), flush=True)
        if manifest["status"] == "incomplete": return 3
    elif args.download_csv:
        if not code:
            print("ERROR: --download-csv requires --code.", file=sys.stderr)
            return 2
        if not matches:
            OUT.mkdir(parents=True, exist_ok=True)
            manifest = {"requested_code": code, "requested_periods": 1, "status": "incomplete", "periods": [], "gaps": [], "failed_scan_dates": [], "amendments": [], "reason": "no_matching_filing_in_recent_window"}
            (OUT / "download_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"No downloadable annual-report CSV found for securities code {code} in the last {args.days} days.")
            return 3
        matches.sort(key=lambda r: r.get("submitDateTime", ""), reverse=True)
        path = download_csv_zip(matches[0], api_key)
        print(f"Downloaded latest matching XBRL CSV ZIP: {path}")

    write_metadata(rows)
    print(f"Saved {len(rows)} recent EDINET filing records to data/edinet/documents.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
