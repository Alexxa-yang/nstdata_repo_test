"""Exercise the actual SDK when available, with all HTTP traffic replaced."""

import importlib.util
import json
import unittest
from unittest.mock import patch

from nstdata_quickstart.client import CrawlError, SdkClient


@unittest.skipUnless(importlib.util.find_spec("nstdata_ai_crawl"), "Optional SDK not available")
class SdkContractTests(unittest.TestCase):
    def response(self, data, status=200):
        import requests

        response = requests.Response()
        response.status_code = status
        response._content = json.dumps(data).encode()
        return response

    def envelope(self, data):
        return {"err": False, "code": 200, "msg": "SUCCESS", "data": data}

    def test_official_client_serializes_request_and_unwraps_inline_content(self):
        response = self.response(self.envelope({
            "success": True, "status": "completed", "data": {
                "markdown": "# Owned page", "html": "<h1>Owned page</h1>",
                "metadata": {"title": "Owned page", "statusCode": 200},
            },
        }))
        submission = self.response(self.envelope({"id": "mock-task", "status": "processing"}))
        with patch("requests.sessions.Session.send", side_effect=[submission, response]) as send:
            client = SdkClient("test-value")
            try:
                page = client.scrape("https://owned.test", ("markdown", "html"), 12000)
            finally:
                client.close()
            self.assertEqual(page.markdown, "# Owned page")
            self.assertEqual(page.html, "<h1>Owned page</h1>")
            request = send.call_args_list[0].args[0]
            self.assertEqual(request.url, "https://api.nstproxy.com/api/v1/crawl/scrape?async=true")
            self.assertEqual(request.headers["x-api-key"], "test-value")
            self.assertEqual(json.loads(request.body)["timeout"], 12000)
            self.assertEqual(send.call_args.kwargs["timeout"], (10, 75))

    def test_lazy_storage_references_are_downloaded(self):
        from requests import Response

        storage = Response()
        storage.status_code = 200
        storage._content = b"# Stored markdown"
        task = self.response(self.envelope({
            "success": True, "status": "completed", "data": {"markdownRef": "mock-ref"},
        }))
        submission = self.response(self.envelope({"id": "mock-task", "status": "processing"}))
        with patch("requests.sessions.Session.send", side_effect=[submission, task, storage]) as send:
            client = SdkClient("test-value")
            try:
                page = client.scrape("https://owned.test", ("markdown",), 60000)
            finally:
                client.close()
            self.assertEqual(page.markdown, "# Stored markdown")
            self.assertIn("/storage/read?st=mock-ref", send.call_args.args[0].url)
            self.assertEqual(send.call_count, 3)

    def test_malformed_envelope_is_a_safe_failure(self):
        response = self.response({"message": "unexpected"})
        with patch("requests.sessions.Session.send", return_value=response):
            client = SdkClient("test-value")
            try:
                with self.assertRaises(CrawlError):
                    client.scrape("https://owned.test", ("markdown",), 60000)
            finally:
                client.close()


if __name__ == "__main__":
    unittest.main()
