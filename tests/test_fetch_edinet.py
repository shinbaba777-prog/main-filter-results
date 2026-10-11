import unittest
from datetime import date
from unittest.mock import patch, Mock

from scripts import fetch_edinet


class FakeResponse:
    def __init__(self, status=200, payload=None, headers=None, content=b""):
        self.status_code = status
        self._payload = payload or {}
        self.headers = headers or {"Content-Type": "application/json"}
        self.content = content

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            import requests
            raise requests.HTTPError("status failure", response=self)


class FetchEdinetTests(unittest.TestCase):
    def test_alphanumeric_security_codes_are_preserved(self):
        self.assertEqual(fetch_edinet.normalize_code("519A"), "519A")
        self.assertEqual(fetch_edinet.normalize_code("519a0"), "519A0")
        self.assertEqual(fetch_edinet.normalize_code("４４０６"), "4406")
        self.assertEqual(fetch_edinet.normalize_code("477A0"), "477A0")

    def test_invalid_security_code_is_rejected(self):
        self.assertEqual(fetch_edinet.normalize_code("ABCDE"), "")
        self.assertEqual(fetch_edinet.normalize_code("44-06"), "")

    def test_add_months_clamps_end_of_month(self):
        self.assertEqual(fetch_edinet.add_months(date(2024, 1, 31), 1), date(2024, 2, 29))
        self.assertEqual(fetch_edinet.add_months(date(2024, 11, 30), 3), date(2025, 2, 28))

    def test_weekday_dates_are_inclusive_and_skip_weekends(self):
        self.assertEqual(
            fetch_edinet.weekday_dates(date(2026, 10, 9), date(2026, 10, 12)),
            [date(2026, 10, 9), date(2026, 10, 12)],
        )

    def test_history_filter_keeps_only_matching_valid_issuer_filings(self):
        rows = [
            {"docTypeCode": "120", "secCode": "44060", "csvFlag": "1"},
            {"docTypeCode": "120", "secCode": "99990", "csvFlag": "1"},
            {"docTypeCode": "120", "secCode": "44060", "csvFlag": "0"},
            {"docTypeCode": "130", "secCode": "44060", "csvFlag": "1"},
        ]
        filtered = fetch_edinet.filter_history_rows(rows, {"4406", "44060"})
        self.assertEqual(len(filtered), 2)

    def test_listing_without_metadata_is_not_an_empty_day(self):
        with patch.object(fetch_edinet, "api_get", return_value=FakeResponse(payload={"StatusCode": 429, "message": "Too Many Requests"})):
            with self.assertRaises(fetch_edinet.EdinetError):
                fetch_edinet.fetch_listing(date(2026, 10, 1), "not-a-real-key")

    def test_listing_missing_results_is_rejected(self):
        with patch.object(fetch_edinet, "api_get", return_value=FakeResponse(payload={"metadata": {"status": "200"}})):
            with self.assertRaises(fetch_edinet.EdinetError):
                fetch_edinet.fetch_listing(date(2026, 10, 1), "not-a-real-key")

    def test_http_200_json_rate_limit_is_retried(self):
        limited = FakeResponse(payload={"StatusCode": 429, "message": "Too Many Requests"})
        success = FakeResponse(payload={"metadata": {"status": "200"}, "results": []})
        with patch.object(fetch_edinet.requests, "get", side_effect=[limited, success]) as get, \
             patch.object(fetch_edinet.THROTTLE, "wait"), \
             patch.object(fetch_edinet.THROTTLE, "pause"), \
             patch.object(fetch_edinet.time, "sleep"):
            response = fetch_edinet.api_get("documents.json", {"date": "2026-10-01", "type": "2"}, "not-a-real-key")
        self.assertIs(response, success)
        self.assertEqual(get.call_count, 2)

    def test_auth_error_is_not_retried(self):
        denied = FakeResponse(payload={"StatusCode": 401, "message": "Unauthorized"})
        with patch.object(fetch_edinet.requests, "get", return_value=denied) as get, \
             patch.object(fetch_edinet.THROTTLE, "wait"):
            with self.assertRaises(fetch_edinet.EdinetAuthError):
                fetch_edinet.api_get("documents.json", {}, "not-a-real-key")
        self.assertEqual(get.call_count, 1)

    def test_api_key_is_not_in_exception_text(self):
        secret = "TOP_SECRET_KEY_DO_NOT_LOG"
        denied = FakeResponse(payload={"StatusCode": 401, "message": "Unauthorized " + secret})
        with patch.object(fetch_edinet.requests, "get", return_value=denied), \
             patch.object(fetch_edinet.THROTTLE, "wait"):
            with self.assertRaises(fetch_edinet.EdinetAuthError) as ctx:
                fetch_edinet.api_get("documents.json", {}, secret)
        self.assertNotIn(secret, str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
