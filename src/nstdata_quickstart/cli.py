"""Run without installation using PYTHONPATH=src python -m nstdata_quickstart."""

import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from .client import CrawlError, MockClient, SdkClient
from .config import RunConfig
from .workflow import run


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export webpage content with Nstdata Crawl.")
    parser.add_argument("--mode", choices=["mock", "live"], default="mock")
    parser.add_argument("--url", action="append", help="Repeat for up to 10 URLs.")
    parser.add_argument(
        "--format", dest="formats", choices=["markdown", "html", "rawData"], action="append"
    )
    parser.add_argument("--timeout-ms", type=int, default=30000)
    parser.add_argument(
        "--authorized", action="store_true", help="Confirm permission for live targets."
    )
    parser.add_argument(
        "--output", type=Path, help="New directory; existing directories are refused."
    )
    args = parser.parse_args(argv)
    urls = args.url
    if not urls and args.mode == "live":
        parser.error("live mode requires at least one --url")
    config = RunConfig(
        urls=tuple(urls or ["https://demo.nstdata.test/article"]),
        formats=tuple(args.formats or ["markdown", "html"]),
        timeout_ms=args.timeout_ms,
        mode=args.mode,
        authorized=args.authorized,
        token=os.environ.get("NSTDATA_API_TOKEN", "") if args.mode == "live" else "",
    )
    label = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:8]
    output = args.output or Path("output") / label
    client = None
    try:
        config.validate()
        client = MockClient() if config.mode == "mock" else SdkClient(config.token)
        manifest = run(config, client, output)
    except (ValueError, CrawlError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    except OSError:
        print("Error: cannot write output; choose a new writable directory.", file=sys.stderr)
        return 2
    finally:
        if client is not None:
            client.close()
    print(f"Mode: {config.mode}")
    print(f"Completed: {manifest['completed']}/{manifest['total']}")
    print(f"Failed: {manifest['failed']}")
    for entry in manifest["entries"]:
        if entry["status"] == "failed":
            print(f"Page {entry['index']}: {entry['error']}")
    print(f"Output: {output}")
    return 1 if manifest["failed"] else 0
