"""Run the user's Playground settings with task polling and local file export."""

import getpass
import os
import sys

from nstdata_quickstart.cli import main


if __name__ == "__main__":
    if not os.environ.get("NSTDATA_API_TOKEN", "").strip():
        os.environ["NSTDATA_API_TOKEN"] = getpass.getpass("Nstdata API key (hidden): ").strip()
    selected_formats = sys.argv[1:]
    if not selected_formats:
        selected_formats = ["--format", "markdown", "--format", "html"]
    raise SystemExit(main([
        "--mode", "live",
        "--authorized",
        "--url", "https://www.nstdata.io/scraping",
        "--timeout-ms", "30000",
        *selected_formats,
    ]))
