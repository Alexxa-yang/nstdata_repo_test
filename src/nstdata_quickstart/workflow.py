"""Sequential bounded batch export with a machine-readable run manifest."""

import json
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from .client import CrawlError, PageClient
from .config import RunConfig


def run(config: RunConfig, client: PageClient, output: Path) -> dict:
    config.validate()
    # Refuse overwrites: a completed example run should remain available for review.
    output.mkdir(parents=True, exist_ok=False)
    entries = []
    for index, url in enumerate(config.urls, start=1):
        parts = urlsplit(url)
        public_url = urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))
        entry = {"index": index, "url_without_query": public_url, "files": {}}
        try:
            page = client.scrape(url, config.formats, config.timeout_ms)
            contents = {"markdown": page.markdown, "html": page.html, "rawData": page.raw_data}
            missing = [
                fmt for fmt in config.formats
                if not isinstance(contents[fmt], bytes if fmt == "rawData" else str)
                or not contents[fmt].strip()
            ]
            entry["format_status"] = {
                fmt: "missing-or-empty" if fmt in missing else "available"
                for fmt in config.formats
            }
            if missing:
                raise CrawlError("Missing or empty requested formats: " + ", ".join(missing))
            for fmt in config.formats:
                suffix = {"markdown": "md", "html": "html", "rawData": "raw.bin"}[fmt]
                filename = f"page-{index:03d}.{suffix}"
                if fmt == "rawData":
                    (output / filename).write_bytes(contents[fmt])
                else:
                    (output / filename).write_text(contents[fmt], encoding="utf-8")
                entry["files"][fmt] = filename
            entry.update(status="completed", title=page.title, status_code=page.status_code)
        except CrawlError as exc:
            entry.update(status="failed", error=str(exc))
        entries.append(entry)
    manifest = {
        "mode": config.mode,
        "source": "offline-fixture" if config.mode == "mock" else "nstdata-crawl",
        "total": len(entries),
        "completed": sum(item["status"] == "completed" for item in entries),
        "failed": sum(item["status"] == "failed" for item in entries),
        "entries": entries,
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return manifest
