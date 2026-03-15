"""Web search — Firecrawl search (primary, requires API key).

Async to avoid blocking the event loop.
"""

import logging
import os

import httpx

logger = logging.getLogger("web-agent")


async def search(query: str, limit: int = 5) -> dict:
    """Search the web. Returns titles, URLs, snippets."""
    api_key = os.getenv("FIRECRAWL_API_KEY", "")
    if not api_key:
        return {
            "source": "none",
            "query": query,
            "error": "No search API configured",
            "results": [],
        }

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.firecrawl.dev/v1/search",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={"query": query, "limit": limit},
                timeout=15.0,
            )
        if resp.status_code != 200:
            return {
                "source": "firecrawl",
                "query": query,
                "error": f"HTTP {resp.status_code}",
                "results": [],
            }
        data = resp.json()
        results = data.get("data", [])[:limit]
        return {
            "source": "firecrawl",
            "query": query,
            "results": [
                {
                    "title": r.get("title", r.get("metadata", {}).get("title", "")),
                    "url": r.get("url", ""),
                    "snippet": r.get("markdown", r.get("description", ""))[:500],
                }
                for r in results
            ],
            "count": len(results),
        }
    except Exception as e:
        return {"source": "firecrawl", "query": query, "error": str(e), "results": []}
