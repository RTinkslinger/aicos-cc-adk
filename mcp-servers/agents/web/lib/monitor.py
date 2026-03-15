"""URL monitoring — watch URLs for changes, notify on diff.

Stub for v1. Will be implemented in Phase 2 (proactive monitoring).
"""
from __future__ import annotations

import asyncio
from typing import Any


_watched_urls: dict[str, dict[str, Any]] = {}


async def register_watch(url: str, interval_minutes: int = 60, notify_method: str = "log") -> dict:
    """Register a URL for periodic monitoring."""
    _watched_urls[url] = {
        "interval_minutes": interval_minutes,
        "notify_method": notify_method,
        "last_hash": None,
        "last_checked": None,
    }
    return {"registered": True, "url": url, "interval": interval_minutes}


async def get_watched_urls() -> list[dict]:
    """Get all registered watched URLs."""
    return [{"url": url, **info} for url, info in _watched_urls.items()]
