"""Debug Jina search response format."""
import httpx
from urllib.parse import quote

query = "Claude API pricing 2025"
url = f"https://s.jina.ai/{quote(query)}"
print(f"URL: {url}")

resp = httpx.get(
    url,
    headers={"Accept": "application/json", "X-Retain-Images": "none"},
    timeout=15.0,
    follow_redirects=True,
)
print(f"Status: {resp.status_code}")
print(f"Content-Type: {resp.headers.get('content-type', 'unknown')}")
print(f"Body (first 1000):\n{resp.text[:1000]}")
