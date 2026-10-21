import io
import json
import os
import socket
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock, patch

from nstdata_quickstart.cli import main
from nstdata_quickstart.client import CrawlError, MockClient, PageContent, SdkClient
from nstdata_quickstart.config import RunConfig
from nstdata_quickstart.workflow import run


class ConfigTests(unittest.TestCase):
    def test_live_requires_key_and_permission(self):
        for overrides in [{}, {"authorized": True}, {"token": "test-value"}]:
            with self.subTest(overrides=overrides), self.assertRaises(ValueError):
                RunConfig(urls=("https://owned.test/page",), mode="live", **overrides).validate()

    def test_invalid_urls_and_bounds(self):
        cases = [
            {"urls": ()},
            {"urls": ("https://owned.test",) * 11},
            {"urls": ("https://owned.test",) * 2},
            {"urls": ("file:///etc/passwd",)},
            {"urls": ("https://user:pass@owned.test",)},
            {"urls": ("https://owned.test:bad",)},
            {"urls": ("https://owned.test",), "timeout_ms": 0},
            {"urls": ("https://owned.test",), "formats": ("pdf",)},
        ]
        for kwargs in cases:
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                RunConfig(**kwargs).validate()


class WorkflowTests(unittest.TestCase):
    def test_mock_export_is_offline_and_labels_fixture(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(
            socket, "create_connection", side_effect=AssertionError("Unexpected network call")
        ):
            output = Path(temp) / "run"
            manifest = run(
                RunConfig(urls=("https://owned.test/a?private=do-not-record",)), MockClient(), output
            )
            self.assertEqual(manifest["source"], "offline-fixture")
            self.assertEqual(manifest["completed"], 1)
            self.assertEqual(
                manifest["entries"][0]["url_without_query"], "https://owned.test/a"
            )
            self.assertIn("# Demo article", (output / "page-001.md").read_text())
            self.assertIn("<article>", (output / "page-001.html").read_text())
            self.assertEqual(json.loads((output / "manifest.json").read_text()), manifest)

    def test_partial_batch_failure_does_not_look_successful(self):
        client = MagicMock()
        client.scrape.side_effect = [
            CrawlError("Task failed."),
            PageContent("# Good", "<h1>Good</h1>", "Good", 200),
        ]
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "run"
            manifest = run(
                RunConfig(urls=("https://owned.test/a", "https://owned.test/b")), client, output
            )
            self.assertEqual((manifest["completed"], manifest["failed"]), (1, 1))
            self.assertFalse((output / "page-001.md").exists())
            self.assertTrue((output / "page-002.md").exists())

    def test_missing_format_creates_no_content_files(self):
        client = MagicMock()
        client.scrape.return_value = PageContent("# Good", None, "Good", 200)
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "run"
            manifest = run(RunConfig(urls=("https://owned.test",)), client, output)
            self.assertEqual(manifest["failed"], 1)
            self.assertEqual(manifest["entries"][0]["error"],
                             "Missing or empty requested formats: html")
            self.assertEqual(manifest["entries"][0]["format_status"],
                             {"markdown": "available", "html": "missing-or-empty"})
            self.assertEqual(sorted(p.name for p in output.iterdir()), ["manifest.json"])

    def test_existing_output_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as temp:
            client = MagicMock()
            with self.assertRaises(FileExistsError):
                run(RunConfig(urls=("https://owned.test",)), client, Path(temp))
            client.scrape.assert_not_called()


class AdapterTests(unittest.TestCase):
    def setUp(self):
        self.module = ModuleType("nstdata_ai_crawl")
        self.sdk = MagicMock()
        self.module.NstDataClient = MagicMock(return_value=self.sdk)
        self.module.ScrapeRequestDto = lambda **kwargs: SimpleNamespace(**kwargs)
        self.module.ProxyDto = lambda **kwargs: SimpleNamespace(**kwargs)
        self.sdk.submit_scrape_task.return_value = SimpleNamespace(id="mock-task")
        self.patcher = patch.dict(sys.modules, {"nstdata_ai_crawl": self.module})
        self.patcher.start()
        self.addCleanup(self.patcher.stop)

    def test_adapter_request_and_lazy_content_accessors(self):
        data = SimpleNamespace(
            metadata=SimpleNamespace(title="Owned page", statusCode=200),
            get_markdown=MagicMock(return_value="# Owned page"),
            get_html=MagicMock(return_value="<h1>Owned page</h1>"),
        )
        self.sdk.get_scrape_task_result.return_value = SimpleNamespace(
            success=True, status="completed", data=data
        )
        client = SdkClient("test-value")
        page = client.scrape("https://owned.test", ("markdown",), 12000)
        req = self.sdk.submit_scrape_task.call_args.args[0]
        self.assertEqual((req.url, req.formats, req.timeout, req.proxy.country),
                         ("https://owned.test", ["markdown"], 12000, "ANY"))
        self.sdk.submit_scrape_task.assert_called_once()
        self.assertEqual(page.markdown, "# Owned page")
        data.get_html.assert_not_called()
        self.assertEqual(self.sdk.session.request.keywords["timeout"], (10, 75))
        client.close()
        self.sdk.close.assert_called_once()

    def test_business_failure_with_successful_transport_is_rejected(self):
        self.sdk.get_scrape_task_result.return_value = SimpleNamespace(
            success=False, status="failed", data=None
        )
        with self.assertRaises(CrawlError):
            SdkClient("test-value").scrape("https://owned.test", ("markdown",), 60000)

    def test_http_error_page_is_rejected(self):
        self.sdk.get_scrape_task_result.return_value = SimpleNamespace(
            success=True, status="completed",
            data=SimpleNamespace(metadata=SimpleNamespace(statusCode=403)),
        )
        with self.assertRaises(CrawlError):
            SdkClient("test-value").scrape("https://owned.test", ("markdown",), 60000)

    def test_sdk_exception_body_cannot_leak_into_cli_error(self):
        self.sdk.get_scrape_task_result.side_effect = RuntimeError("secret-value-in-body")
        with self.assertRaises(CrawlError) as error:
            SdkClient("test-value").scrape("https://owned.test", ("markdown",), 60000)
        self.assertNotIn("secret-value-in-body", str(error.exception))

    def test_processing_task_is_polled_without_resubmission(self):
        data = SimpleNamespace(
            metadata=None, get_markdown=lambda: "# Done", get_raw_data=lambda: b"raw bytes"
        )
        self.sdk.get_scrape_task_result.side_effect = [
            SimpleNamespace(status="processing"),
            SimpleNamespace(status="completed", success=True, data=data),
        ]
        page = SdkClient("test-value", poll_interval=0).scrape(
            "https://owned.test", ("markdown", "rawData"), 30000
        )
        self.assertEqual(page.raw_data, b"raw bytes")
        self.sdk.submit_scrape_task.assert_called_once()
        self.assertEqual(self.sdk.get_scrape_task_result.call_count, 2)

    def test_polling_limit_stops_without_duplicate_submission(self):
        self.sdk.get_scrape_task_result.return_value = SimpleNamespace(status="processing")
        with self.assertRaisesRegex(CrawlError, "Polling limit reached"):
            SdkClient("test-value", max_polls=2, poll_interval=0).scrape(
                "https://owned.test", ("markdown",), 30000
            )
        self.sdk.submit_scrape_task.assert_called_once()
        self.assertEqual(self.sdk.get_scrape_task_result.call_count, 2)

    def test_missing_task_id_stops_before_polling(self):
        self.sdk.submit_scrape_task.return_value = SimpleNamespace(id=None)
        with self.assertRaisesRegex(CrawlError, "task ID"):
            SdkClient("test-value").scrape("https://owned.test", ("markdown",), 30000)
        self.sdk.get_scrape_task_result.assert_not_called()


class CliTests(unittest.TestCase):
    def test_missing_permission_fails_before_creating_client(self):
        with patch.dict(os.environ, {"NSTDATA_API_TOKEN": "test-value"}), patch(
            "nstdata_quickstart.cli.SdkClient"
        ) as factory, redirect_stderr(io.StringIO()):
            self.assertEqual(main(["--mode", "live", "--url", "https://owned.test"]), 2)
            factory.assert_not_called()

    def test_mock_smoke_in_fresh_process(self):
        with tempfile.TemporaryDirectory() as temp:
            result = subprocess.run(
                [sys.executable, "-m", "nstdata_quickstart", "--mode", "mock",
                 "--output", str(Path(temp) / "run")],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Completed: 1/1", result.stdout)

    def test_failed_batch_returns_nonzero(self):
        mock = MagicMock()
        mock.scrape.side_effect = CrawlError("Task failed.")
        with tempfile.TemporaryDirectory() as temp, patch(
            "nstdata_quickstart.cli.MockClient", return_value=mock
        ), redirect_stdout(io.StringIO()):
            self.assertEqual(main(["--output", str(Path(temp) / "run")]), 1)
            mock.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
