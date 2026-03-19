"""URL validation — blocks internal/private IPs and unsafe schemes.

Applied at the lib layer so ALL callers (FastMCP direct + SDK agent) are protected.
"""
from __future__ import annotations

import re
from urllib.parse import urlparse


_BLOCKED_PATTERNS = [
    r"^https?://169\.254\.",          # Link-local / cloud metadata (AWS, DO, GCP)
    r"^https?://10\.",                # RFC-1918 Class A
    r"^https?://192\.168\.",          # RFC-1918 Class C
    r"^https?://172\.(1[6-9]|2\d|3[01])\.",  # RFC-1918 Class B
    r"^https?://127\.",              # Loopback
    r"^https?://localhost",          # Loopback name
    r"^https?://\[::1\]",           # IPv6 loopback
    r"^https?://0\.0\.0\.0",        # Unspecified
]

_ALLOWED_SCHEMES = {"http", "https"}


def validate_url(url: str) -> str | None:
    """Returns error string if URL is unsafe, else None."""
    if not url:
        return "Empty URL"

    parsed = urlparse(url)
    if parsed.scheme not in _ALLOWED_SCHEMES:
        return f"Blocked scheme: {parsed.scheme}. Only http/https allowed."

    for pattern in _BLOCKED_PATTERNS:
        if re.match(pattern, url, re.IGNORECASE):
            return f"Blocked internal/private URL: {url}"

    return None
