"""Integration tests for WebAgent.

Test tiers:
- Tier 1 (unit): quality.py, strategy.py, cookies.py — no network
- Tier 2 (integration): scrape, browse, fingerprint, search — stable URLs
- Tier 3 (agent): full web_task agent loop — costs tokens

Usage:
    python tests/test_agent.py                 # Run all tiers
    python tests/test_agent.py tier1           # Unit tests only
    python tests/test_agent.py tier2           # Integration tests
    python tests/test_agent.py tier3           # Agent mode (costs tokens)
"""

import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

PASS = 0
FAIL = 0


def report(name: str, passed: bool, detail: str = ""):
    global PASS, FAIL
    status = "PASS" if passed else "FAIL"
    if passed:
        PASS += 1
    else:
        FAIL += 1
    print(f"  [{status}] {name}" + (f" — {detail}" if detail else ""))


# -------------------------------------------------------
# TIER 1: Unit tests (no network)
# -------------------------------------------------------


def test_quality():
    print("\n=== Tier 1: quality.py ===")
    from lib.quality import validate_content

    # Good content
    r = validate_content("This is a long article about technology. " * 20)
    report("good content", r["score"] >= 70, f"score={r['score']}")

    # Empty content
    r = validate_content("")
    report("empty content", r["score"] == 0, f"verdict={r['verdict']}")

    # Login wall
    r = validate_content(
        "Sign in to continue. Log in. Create account. Forgot password."
    )
    report("login wall", r["score"] < 40, f"score={r['score']}")

    # Error page
    r = validate_content("404 Page not found. Sorry.")
    report("error page", r["score"] < 70, f"score={r['score']}")


def test_strategy():
    print("\n=== Tier 1: strategy.py ===")
    # Use temp DB
    import lib.strategy as strat

    old_path = strat.DB_PATH
    strat.DB_PATH = "/tmp/test_strategy.db"
    strat._db = None  # Force reinit

    try:
        os.remove("/tmp/test_strategy.db")
    except FileNotFoundError:
        pass

    from lib.strategy import (
        get_all_strategies,
        get_strategy,
        record_outcome,
        seed_strategies,
    )

    # Seed
    seed_strategies("test.com", {"is_spa": True, "auth_required": False})
    s = get_strategy("test.com")
    report("seed strategies", s is not None, f"name={s['strategy_name']}")

    # Record outcomes
    record_outcome("test.com", "jina_reader", success=False, latency_ms=100)
    record_outcome(
        "test.com", "browser_mutation_observer", success=True, latency_ms=3000
    )
    record_outcome(
        "test.com", "browser_mutation_observer", success=True, latency_ms=2500
    )

    # Upsert for unknown strategy
    record_outcome("new.com", "browse", success=True, latency_ms=1000)
    s = get_strategy("new.com")
    report("upsert unknown strategy", s is not None, f"name={s['strategy_name']}")

    # All strategies
    all_strats = get_all_strategies()
    report("get_all_strategies", len(all_strats) > 0, f"count={len(all_strats)}")

    # Restore
    strat.DB_PATH = old_path
    strat._db = None


def test_cookies_unit():
    print("\n=== Tier 1: cookies.py ===")
    from lib.cookies import cookie_status

    r = cookie_status("/opt/ai-cos/cookies")
    report(
        "cookie_status",
        len(r.get("cookies", [])) > 0,
        f"domains={len(r.get('cookies', []))}",
    )


# -------------------------------------------------------
# TIER 2: Integration tests (network, stable URLs)
# -------------------------------------------------------


async def test_scrape():
    print("\n=== Tier 2: scrape ===")
    from lib.scrape import scrape

    # Jina
    r = await scrape("https://example.com")
    report(
        "jina example.com",
        r.get("content_length", 0) > 50,
        f"len={r.get('content_length', 0)}",
    )

    r = await scrape("https://example.com/nonexistent-page-404")
    report("jina 404", r.get("is_404", False) or r.get("status") == 404, f"status={r.get('status')}")

    # Firecrawl (if key available)
    if os.getenv("FIRECRAWL_API_KEY"):
        r = await scrape("https://example.com", use_firecrawl=True)
        report(
            "firecrawl example.com",
            r.get("content_length", 0) > 30,
            f"len={r.get('content_length', 0)}",
        )


async def test_search():
    print("\n=== Tier 2: search ===")
    from lib.search import search

    if not os.getenv("FIRECRAWL_API_KEY"):
        print("  [SKIP] No FIRECRAWL_API_KEY")
        return

    r = await search("anthropic claude api", limit=3)
    report("search", r.get("count", 0) > 0, f"count={r.get('count', 0)}")


async def test_browse():
    print("\n=== Tier 2: browse ===")
    from lib.browser import browse, shutdown_browser

    # Static page
    r = await browse("https://example.com", readiness="none")
    report(
        "browse example.com",
        r.get("status") == "ok" and r.get("content_length", 0) > 50,
        f"len={r.get('content_length', 0)}",
    )

    # SPA (anthropic docs)
    r = await browse(
        "https://docs.anthropic.com/en/docs/about-claude/models", readiness="auto"
    )
    report(
        "browse anthropic docs (SPA)",
        r.get("status") == "ok" and r.get("content_length", 0) > 500,
        f"len={r.get('content_length', 0)}",
    )

    # Auth (x.com with cookies)
    r = await browse("https://x.com/home", cookies_domain="x.com", readiness="auto")
    report(
        "browse x.com (cookies)",
        r.get("cookies_loaded", {}).get("count", 0) > 0,
        f"cookies={r.get('cookies_loaded', {}).get('count', 0)} | len={r.get('content_length', 0)}",
    )

    await shutdown_browser()


async def test_fingerprint():
    print("\n=== Tier 2: fingerprint ===")
    from lib.fingerprint import fingerprint

    tests = [
        ("https://example.com", False, "unknown"),
        ("https://linear.app/features", True, "nextjs"),
        ("https://docs.anthropic.com/en/docs/about-claude/models", True, "nextjs"),
    ]
    for url, expected_spa, expected_fw in tests:
        r = await fingerprint(url)
        label = url.split("/")[2]
        report(
            f"fingerprint {label}",
            r.get("is_spa") == expected_spa,
            f"spa={r['is_spa']} fw={r['framework']}",
        )


# -------------------------------------------------------
# TIER 3: Agent mode (costs tokens)
# -------------------------------------------------------


async def test_agent_mode():
    print("\n=== Tier 3: agent mode ===")
    from agent import run_agent_task

    r = await run_agent_task(
        "Scrape https://example.com and validate the content quality. Be brief.",
        max_turns=10,
        timeout_s=60,
    )
    report(
        "agent web_task",
        r.get("status") == "complete" and len(r.get("output", "")) > 20,
        f"status={r['status']} turns={r.get('turns', '?')} tokens={r.get('usage', {}).get('input_tokens', '?')}+{r.get('usage', {}).get('output_tokens', '?')}",
    )


# -------------------------------------------------------
# Runner
# -------------------------------------------------------


async def main():
    tiers = sys.argv[1:] if len(sys.argv) > 1 else ["tier1", "tier2", "tier3"]

    if "tier1" in tiers:
        test_quality()
        test_strategy()
        test_cookies_unit()

    if "tier2" in tiers:
        await test_scrape()
        await test_search()
        await test_browse()
        await test_fingerprint()

    if "tier3" in tiers:
        await test_agent_mode()

    print(f"\n{'='*40}")
    print(f"RESULTS: {PASS} passed, {FAIL} failed")
    if FAIL > 0:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
