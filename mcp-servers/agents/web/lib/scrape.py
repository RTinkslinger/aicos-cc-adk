"""Content extraction — Jina Reader (free, primary) + Firecrawl (fallback).

All functions are async to avoid blocking the event loop.
"""

import logging
import os

import httpx

logger = logging.getLogger("web-agent")


def _get_firecrawl_key() -> str:
    """Read API key at call time (not import time) so .env changes take effect."""
    return os.getenv("FIRECRAWL_API_KEY", "")


async def scrape(url: str, use_firecrawl: bool = False) -> dict:
    """Extract content from URL as clean markdown."""
    firecrawl_key = _get_firecrawl_key()
    if use_firecrawl and firecrawl_key:
        return await _scrape_firecrawl(url, firecrawl_key)

    jina_url = f"https://r.jina.ai/{url}"
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                jina_url,
                headers={"Accept": "text/plain"},
                timeout=15.0,
                follow_redirects=True,
            )
        content = resp.text
        is_404 = "Warning: Target URL returned error 404" in content
        return {
            "source": "jina",
            "url": url,
            "status": 404 if is_404 else resp.status_code,
            "content": content[:50000],
            "content_length": len(content),
            "is_404": is_404,
        }
    except httpx.TimeoutException:
        return {"source": "jina", "url": url, "error": "timeout", "content": ""}
    except Exception as e:
        if firecrawl_key:
            return await _scrape_firecrawl(url, firecrawl_key)
        return {"source": "jina", "url": url, "error": str(e), "content": ""}


async def _scrape_firecrawl(url: str, api_key: str) -> dict:
    """Firecrawl scrape with mandatory metadata validation."""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.firecrawl.dev/v1/scrape",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={"url": url, "formats": ["markdown"], "onlyMainContent": True},
                timeout=30.0,
            )
        data = resp.json()
        if not data.get("success"):
            return {
                "source": "firecrawl",
                "url": url,
                "error": data.get("error", "unknown"),
                "content": "",
            }

        result_data = data.get("data", {})
        metadata = result_data.get("metadata", {})
        markdown = result_data.get("markdown") or ""
        return {
            "source": "firecrawl",
            "url": url,
            "actual_url": metadata.get("url", ""),
            "status": metadata.get("statusCode", 0),
            "redirected": metadata.get("url", "") != url
            and bool(metadata.get("url")),
            "content": markdown[:50000],
            "content_length": len(markdown),
            "title": metadata.get("title", ""),
        }
    except Exception as e:
        return {"source": "firecrawl", "url": url, "error": str(e), "content": ""}
