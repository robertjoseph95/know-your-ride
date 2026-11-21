"""Offline contract tests for the model-year recall endpoint."""
import importlib.util
import io
import json
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

_SOURCE = Path(__file__).resolve().parents[1] / "wrench_deploy" / "api" / "recalls.py"
_SPEC = importlib.util.spec_from_file_location("kyr_recalls", _SOURCE)
endpoint = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(endpoint)


class RecallLookupTest(unittest.TestCase):
    def request(self, payload, *, cache=None, timeout=False,
                path="/api/recalls?make=ACURA&model=RDX&year=2012"):
        handler = endpoint.handler.__new__(endpoint.handler)
        handler.path = path
        handler._send = Mock()
        body = json.dumps(payload).encode()
        with patch.object(endpoint, "_redis", return_value=cache), patch.object(
            endpoint.urllib.request, "urlopen",
            side_effect=TimeoutError("mock") if timeout else None,
            return_value=io.BytesIO(body),
        ) as upstream, patch.object(endpoint.sys, "stderr", new=io.StringIO()):
            handler.do_GET()
        self.assertEqual(handler._send.call_count, 1)
        return (*handler._send.call_args.args, upstream)

    def test_valid_empty_list_is_success(self):
        self.assertEqual(self.request({"Count": 0, "results": []})[:2],
                         (200, {"count": 0, "recalls": []}))

    def test_campaigns_are_returned_unchanged(self):
        campaigns = [{"NHTSACampaignNumber": "TEST", "parkIt": True}]
        self.assertEqual(self.request({"Count": 1, "results": campaigns})[:2],
                         (200, {"count": 1, "recalls": campaigns}))

    def test_malformed_or_error_response_is_not_empty_success(self):
        for payload in ({}, None, {"results": None}, {"results": {}},
                        {"results": [None]}, {"Count": 1, "results": []},
                        {"error": "unavailable", "results": []}):
            with self.subTest(payload=payload):
                status, body, _ = self.request(payload)
                self.assertEqual(status, 502)
                self.assertIn("error", body)

    def test_invalid_response_is_not_cached(self):
        cache = Mock()
        cache.get.return_value = None
        self.assertEqual(self.request({}, cache=cache)[0], 502)
        cache.set.assert_not_called()

    def test_cache_hit_and_cache_shape(self):
        cache = Mock()
        cache.get.return_value = '{"recalls":[]}'
        status, body, upstream = self.request(None, cache=cache)
        self.assertEqual((status, body), (200, {"count": 0, "recalls": [], "cached": True}))
        upstream.assert_not_called()
        self.assertTrue(cache.get.call_args.args[0].startswith("recalls:v2:"))
        cache.get.return_value = '{"recalls":null}'
        status, body, upstream = self.request({"results": []}, cache=cache)
        self.assertEqual((status, body), (200, {"count": 0, "recalls": []}))
        upstream.assert_called_once()

    def test_missing_fields_and_upstream_timeout_are_errors(self):
        status, body, upstream = self.request(None, path="/api/recalls?year=2012")
        self.assertEqual(status, 400)
        self.assertIn("error", body)
        upstream.assert_not_called()
        status, body, _ = self.request(None, timeout=True)
        self.assertEqual(status, 502)
        self.assertIn("error", body)


if __name__ == "__main__":
    unittest.main()
