"""Site fingerprinting — detect framework, CMS, and page type.

Async to avoid blocking the event loop.
Uses partial content fetch (stream with read limit) for bandwidth efficiency.
"""

import logging
import re

import httpx

logger = logging.getLogger("web-agent")


async def fingerprint(url: str) -> dict:
    """Analyze a URL and return site fingerprint.

    Returns: framework, cms, page_type, is_spa, auth_required, signals
    """
    result: dict = {
        "url": url,
        "framework": "unknown",
        "cms": "unknown",
        "page_type": "unknown",
        "is_spa": False,
        "auth_required": False,
        "signals": [],
    }

    try:
        async with httpx.AsyncClient() as client:
            # Stream with read limit for bandwidth efficiency
            async with client.stream(
                "GET",
                url,
                timeout=10.0,
                follow_redirects=True,
                headers={"Accept": "text/html"},
            ) as resp:
                html = ""
                async for chunk in resp.aiter_text():
                    html += chunk
                    if len(html) > 51200:
                        break
                headers = {k.lower(): v for k, v in resp.headers.items()}

        html = html[:50000].lower()

        # Framework detection
        if (
            "__next_data__" in html
            or "self.__next_f.push" in html
            or "_next/" in html
        ):
            result["framework"] = "nextjs"
            result["is_spa"] = True
            result["signals"].append("__NEXT_DATA__ or _next/ assets")
        elif (
            "data-reactroot" in html
            or "_reactlistening" in html
            or "react" in headers.get("x-powered-by", "")
        ):
            result["framework"] = "react"
            result["is_spa"] = True
            result["signals"].append("React markers in DOM")
        elif "__vue__" in html or ("vue" in html and "app.__vue" in html):
            result["framework"] = "vue"
            result["is_spa"] = True
            result["signals"].append("Vue markers")
        elif "ng-version" in html or "ng-app" in html:
            result["framework"] = "angular"
            result["is_spa"] = True
            result["signals"].append("Angular markers")
        elif "svelte" in html:
            result["framework"] = "svelte"
            result["is_spa"] = True
            result["signals"].append("Svelte markers")

        # CMS detection
        if "wp-content" in html or "wordpress" in headers.get("x-powered-by", ""):
            result["cms"] = "wordpress"
            result["signals"].append("WordPress indicators")
        elif "cdn.shopify" in html or "shopify" in html:
            result["cms"] = "shopify"
            result["signals"].append("Shopify CDN")

        # Page type
        if '"@type":"product"' in html or "schema.org/product" in html:
            result["page_type"] = "product"
        elif '"@type":"article"' in html or "<article" in html:
            result["page_type"] = "article"
        elif "<form" in html and 'type="password"' in html:
            result["page_type"] = "login"
            result["auth_required"] = True

        # Auth signals
        if any(
            p in url.lower()
            for p in ["/dashboard", "/settings", "/account", "/my/", "/inbox"]
        ):
            result["auth_required"] = True
            result["signals"].append("Auth path detected")

        # SPA detection fallback (minimal HTML with large JS bundles)
        if not result["is_spa"]:
            script_count = html.count("<script")
            body_text_ratio = len(re.sub(r"<[^>]+>", "", html)) / max(len(html), 1)
            if script_count > 10 and body_text_ratio < 0.1:
                result["is_spa"] = True
                result["signals"].append(
                    f"SPA heuristic: {script_count} scripts, {body_text_ratio:.2f} text ratio"
                )

    except Exception as e:
        result["error"] = str(e)

    return result
