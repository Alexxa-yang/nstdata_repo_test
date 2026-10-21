"""Content clients; SDK imports happen only in live mode."""

from dataclasses import dataclass
from functools import partial
from time import sleep
from typing import Protocol


class CrawlError(Exception):
    """A safe, user-facing error; never includes an SDK response body."""


@dataclass(frozen=True)
class PageContent:
    markdown: str | None
    html: str | None
    title: str
    status_code: int | None
    raw_data: bytes | None = None


class PageClient(Protocol):
    def scrape(self, url: str, formats: tuple[str, ...], timeout_ms: int) -> PageContent: ...

    def close(self) -> None: ...


class MockClient:
    """Return a fixed fixture; never access the supplied URL or the network."""

    def scrape(self, url: str, formats: tuple[str, ...], timeout_ms: int) -> PageContent:
        return PageContent(
            markdown="# Demo article\n\nOffline fixture for content export.\n",
            html=(
                "<article><h1>Demo article</h1>"
                "<p>Offline fixture for content export.</p></article>\n"
            ),
            title="Demo article (mock)",
            status_code=200,
            raw_data=b"<html><body>Offline raw-data fixture.</body></html>\n",
        )

    def close(self) -> None:
        pass


class SdkClient:
    """Adapter for the official 0.1.1 SDK; no HTTP route is reimplemented."""

    def __init__(self, token: str, max_polls: int = 20, poll_interval: float = 2):
        if max_polls < 1 or poll_interval < 0:
            raise ValueError("Polling requires a positive count and a nonnegative interval.")
        try:
            from nstdata_ai_crawl import NstDataClient, ProxyDto, ScrapeRequestDto
        except ImportError:
            raise CrawlError("Live mode needs the optional live dependencies.") from None
        self._request_type = ScrapeRequestDto
        self._proxy_type = ProxyDto
        self._max_polls = max_polls
        self._poll_interval = poll_interval
        self._client = NstDataClient(token)
        # Preserve the SDK default endpoint, matching the user's Playground snippet.
        # The reviewed source uses api.nstproxy.com; deployed compatibility is unverified.
        # Bound HTTP connect/read waits, including lazy storage fetches.
        # The SDK task timeout field alone does not set requests' socket timeouts.
        self._client.session.request = partial(self._client.session.request, timeout=(10, 75))

    def scrape(self, url: str, formats: tuple[str, ...], timeout_ms: int) -> PageContent:
        request = self._request_type(
            url=url, proxy=self._proxy_type(country="ANY"),
            formats=list(formats), timeout=timeout_ms
        )
        try:
            submitted = self._client.submit_scrape_task(request)
            if not submitted.id:
                raise CrawlError("Submission did not return a task ID; no content was exported.")
            for attempt in range(self._max_polls):
                if attempt:
                    sleep(self._poll_interval)
                result = self._client.get_scrape_task_result(submitted.id)
                if result.status in {"completed", "failed"}:
                    break
            else:
                raise CrawlError(
                    "Polling limit reached; the remote task may still be running. "
                    "Check task history before submitting another request."
                )
            if result.success is not True or result.status != "completed" or result.data is None:
                raise CrawlError(
                    "Crawl task did not complete successfully; no content was exported."
                )
            data = result.data
            status_code = getattr(data.metadata, "statusCode", None)
            if status_code is not None and status_code >= 400:
                raise CrawlError("Target returned an HTTP error; no content was exported.")
            markdown = data.get_markdown() if "markdown" in formats else None
            html = data.get_html() if "html" in formats else None
            return PageContent(
                markdown=markdown,
                html=html,
                title=getattr(data.metadata, "title", None) or "Untitled",
                status_code=status_code,
                raw_data=data.get_raw_data() if "rawData" in formats else None,
            )
        except CrawlError:
            raise
        except Exception:
            raise CrawlError(
                "SDK request or content download failed. "
                "Check the key, balance, endpoint and network."
            ) from None

    def close(self) -> None:
        self._client.close()
