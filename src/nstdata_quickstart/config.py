"""Validate input before opening a client or creating output files."""

from dataclasses import dataclass
from urllib.parse import urlsplit


@dataclass(frozen=True)
class RunConfig:
    urls: tuple[str, ...]
    formats: tuple[str, ...] = ("markdown", "html")
    timeout_ms: int = 30000
    mode: str = "mock"
    authorized: bool = False
    token: str = ""

    def validate(self) -> None:
        if self.mode not in {"mock", "live"}:
            raise ValueError("Mode must be mock or live.")
        if not 1 <= len(self.urls) <= 10:
            raise ValueError("Provide between 1 and 10 URLs per run.")
        if len(set(self.urls)) != len(self.urls):
            raise ValueError("Duplicate URLs are not allowed in one run.")
        if not self.formats or not set(self.formats) <= {"markdown", "html", "rawData"}:
            raise ValueError("Formats must be markdown, html and/or rawData.")
        if len(set(self.formats)) != len(self.formats):
            raise ValueError("Duplicate formats are not allowed.")
        if not 1000 <= self.timeout_ms <= 60000:
            raise ValueError("Task timeout must be between 1000 and 60000 milliseconds.")
        for url in self.urls:
            try:
                parts = urlsplit(url)
                valid = (
                    parts.scheme == "https"
                    and bool(parts.hostname)
                    and parts.username is None
                    and parts.password is None
                    and not parts.fragment
                    and parts.port in {None, 443}
                )
            except ValueError:
                valid = False
            if not valid:
                raise ValueError(
                    "Use HTTPS URLs without credentials, fragments or custom ports."
                )
        if self.mode == "live":
            if not self.authorized:
                raise ValueError("Live mode requires --authorized for an owned or permitted target.")
            if not self.token.strip() or self.token.strip() == "YOUR_API_KEY":
                raise ValueError("Set NSTDATA_API_TOKEN locally before using live mode.")
