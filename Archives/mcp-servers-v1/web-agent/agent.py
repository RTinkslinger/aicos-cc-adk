"""WebAgent runner — Claude-powered web intelligence.

Uses anthropic SDK with manual tool-use loop (works without claude-agent-sdk).
Async throughout — compatible with FastMCP's async event loop.

Features: try/except on tools, wall-clock timeout, max_tokens=8192,
cumulative usage tracking, auto-record strategy outcomes.
"""

import asyncio
import json
import logging
import os
import sys
import time as _time
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (Path(__file__).parent / "system_prompt.md").read_text()

# Module-level client — reused across calls (avoids connection pool churn)
_anthropic_client = None


def _get_client():
    """Get or create the shared AsyncAnthropic client."""
    global _anthropic_client
    if _anthropic_client is None:
        import anthropic

        _anthropic_client = anthropic.AsyncAnthropic()
    return _anthropic_client


def _build_tools() -> list[dict]:
    """Build tool definitions for the agent."""
    return [
        {
            "name": "web_browse",
            "description": (
                "Navigate to URL and extract content with intelligent readiness "
                "detection. Returns page title, text content, console errors."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to navigate to"},
                    "action": {
                        "type": "string",
                        "enum": [
                            "snapshot",
                            "click",
                            "fill",
                            "screenshot",
                            "evaluate",
                        ],
                        "default": "snapshot",
                    },
                    "selector": {
                        "type": "string",
                        "description": "CSS selector for click/fill actions",
                        "default": "",
                    },
                    "text": {
                        "type": "string",
                        "description": "Text for fill action or JS for evaluate",
                        "default": "",
                    },
                    "cookies_domain": {
                        "type": "string",
                        "description": "Load cookies for this domain (e.g. 'youtube.com')",
                        "default": "",
                    },
                    "readiness": {
                        "type": "string",
                        "description": "Readiness mode: auto, selector:<css>, time:<ms>, none",
                        "default": "auto",
                    },
                },
                "required": ["url"],
            },
        },
        {
            "name": "web_scrape",
            "description": (
                "Extract text content from URL as markdown. Uses Jina Reader "
                "(free) by default, Firecrawl as fallback."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "url": {"type": "string"},
                    "use_firecrawl": {"type": "boolean", "default": False},
                },
                "required": ["url"],
            },
        },
        {
            "name": "web_search",
            "description": "Search the web. Returns titles, URLs, snippets.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "limit": {"type": "integer", "default": 5},
                },
                "required": ["query"],
            },
        },
        {
            "name": "fingerprint_site",
            "description": (
                "Detect site framework, CMS, page type. Returns is_spa, "
                "auth_required, framework name."
            ),
            "input_schema": {
                "type": "object",
                "properties": {"url": {"type": "string"}},
                "required": ["url"],
            },
        },
        {
            "name": "check_strategy",
            "description": (
                "Look up cached extraction strategy for a domain. "
                "Returns best strategy if known."
            ),
            "input_schema": {
                "type": "object",
                "properties": {"origin": {"type": "string"}},
                "required": ["origin"],
            },
        },
        {
            "name": "validate_content",
            "description": (
                "Score extracted content quality (0-100). Detects login walls, "
                "error pages, empty content."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "content": {"type": "string"},
                    "url": {"type": "string", "default": ""},
                },
                "required": ["content"],
            },
        },
        {
            "name": "cookie_status",
            "description": "Check available cookies and freshness.",
            "input_schema": {"type": "object", "properties": {}},
        },
    ]


async def _execute_tool(name: str, args: dict) -> str:
    """Execute a tool call and return JSON result.

    Wrapped in try/except — errors returned to Claude for reasoning,
    not propagated as crashes. Auto-records outcomes to strategy cache.
    """
    start = _time.monotonic()
    try:
        if name == "web_browse":
            from lib.browser import browse

            result = await browse(**args)
            _auto_record_outcome(
                url=args.get("url", ""),
                strategy="browse",
                success=result.get("status") == "ok",
                latency_ms=(_time.monotonic() - start) * 1000,
            )
        elif name == "web_scrape":
            from lib.scrape import scrape

            result = await scrape(**args)
            _auto_record_outcome(
                url=args.get("url", ""),
                strategy="jina_reader"
                if result.get("source") == "jina"
                else "firecrawl",
                success=result.get("content_length", 0) > 100,
                latency_ms=(_time.monotonic() - start) * 1000,
            )
        elif name == "web_search":
            from lib.search import search

            result = await search(**args)
        elif name == "fingerprint_site":
            from lib.fingerprint import fingerprint
            from lib.strategy import seed_strategies

            result = await fingerprint(args["url"])
            origin = urlparse(args["url"]).netloc
            seed_strategies(origin, result)
        elif name == "check_strategy":
            from lib.strategy import get_strategy

            result = get_strategy(args["origin"])
            if result is None:
                result = {"message": "No cached strategy. Use fingerprint_site first."}
        elif name == "validate_content":
            from lib.quality import validate_content

            result = validate_content(args["content"], args.get("url", ""))
        elif name == "cookie_status":
            from lib.cookies import cookie_status

            result = cookie_status()
        else:
            result = {"error": f"Unknown tool: {name}"}

    except Exception as e:
        logger.warning("Tool %s failed: %s", name, e)
        result = {"error": f"Tool execution failed: {e}", "tool": name}

    return json.dumps(result, default=str)


def _auto_record_outcome(
    url: str, strategy: str, success: bool, latency_ms: float
) -> None:
    """Auto-record extraction outcome to strategy cache (best-effort)."""
    try:
        from lib.strategy import record_outcome

        origin = urlparse(url).netloc
        if origin:
            record_outcome(origin, strategy, success, latency_ms)
    except Exception:
        pass  # Strategy recording never blocks


async def run_agent_task(
    task: str, max_turns: int = 20, timeout_s: int = 120
) -> dict:
    """Run the WebAgent on a task using anthropic SDK tool-use loop.

    Features:
    - Wall-clock timeout (120s default) — returns error_type: "timeout"
    - try/except on tool execution — errors go to Claude, not crash
    - max_tokens bumped to 8192
    - Handles stop_reason="max_tokens" (response truncation)
    - Cumulative usage tracking across all turns
    """
    client = _get_client()
    tools = _build_tools()
    messages: list[dict] = [{"role": "user", "content": task}]
    cumulative_usage = {"input_tokens": 0, "output_tokens": 0}

    try:
        result = await asyncio.wait_for(
            _agent_loop(client, tools, messages, max_turns, cumulative_usage),
            timeout=timeout_s,
        )
        result["usage"] = cumulative_usage
        return result
    except asyncio.TimeoutError:
        logger.warning("Agent task timed out after %ds: %s", timeout_s, task[:100])
        return {
            "status": "error",
            "error_type": "timeout",
            "error": f"Agent task exceeded {timeout_s}s wall-clock limit",
            "turns_completed": len(
                [m for m in messages if m["role"] == "assistant"]
            ),
            "usage": cumulative_usage,
        }


async def _agent_loop(
    client,
    tools: list[dict],
    messages: list[dict],
    max_turns: int,
    cumulative_usage: dict,
) -> dict:
    """Inner agent loop — separated for timeout wrapping."""
    for turn in range(max_turns):
        response = await client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=8192,
            system=SYSTEM_PROMPT,
            tools=tools,
            messages=messages,
        )

        # Track cumulative usage
        cumulative_usage["input_tokens"] += response.usage.input_tokens
        cumulative_usage["output_tokens"] += response.usage.output_tokens

        assistant_content = response.content
        messages.append({"role": "assistant", "content": assistant_content})

        # Handle completion
        if response.stop_reason == "end_turn":
            text_parts = [b.text for b in assistant_content if b.type == "text"]
            return {
                "status": "complete",
                "output": "\n".join(text_parts),
                "turns": turn + 1,
                "model": response.model,
            }

        # Handle truncation (response hit max_tokens mid-sentence)
        if response.stop_reason == "max_tokens":
            text_parts = [b.text for b in assistant_content if b.type == "text"]
            logger.warning(
                "Agent response truncated at max_tokens on turn %d", turn + 1
            )
            return {
                "status": "error",
                "error_type": "truncated",
                "error": "Response hit max_tokens limit — output may be incomplete",
                "output": "\n".join(text_parts),
                "turns": turn + 1,
            }

        # Execute tool calls
        if response.stop_reason == "tool_use":
            tool_results = []
            for block in assistant_content:
                if block.type == "tool_use":
                    try:
                        result_str = await asyncio.wait_for(
                            _execute_tool(block.name, block.input),
                            timeout=30,
                        )
                    except asyncio.TimeoutError:
                        result_str = json.dumps(
                            {"error": f"Tool {block.name} timed out after 30s"}
                        )
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result_str,
                        }
                    )
            if tool_results:
                messages.append({"role": "user", "content": tool_results})
            else:
                # Unexpected: tool_use stop_reason but no tool_use blocks
                logger.warning(
                    "tool_use stop_reason but no tool_use blocks on turn %d",
                    turn + 1,
                )
                text_parts = [
                    b.text for b in assistant_content if b.type == "text"
                ]
                return {
                    "status": "complete",
                    "output": "\n".join(text_parts),
                    "turns": turn + 1,
                }
        else:
            # Unhandled stop_reason — don't loop silently
            logger.error(
                "Unexpected stop_reason %r on turn %d",
                response.stop_reason,
                turn + 1,
            )
            return {
                "status": "error",
                "error_type": "unexpected_stop_reason",
                "error": f"Unhandled stop_reason: {response.stop_reason}",
                "turns": turn + 1,
            }

    return {
        "status": "error",
        "error_type": "max_turns",
        "error": f"Exceeded {max_turns} turns",
        "turns": max_turns,
    }


if __name__ == "__main__":
    task = sys.argv[1] if len(sys.argv) > 1 else "What tools do you have available?"
    result = asyncio.run(run_agent_task(task))
    print(json.dumps(result, indent=2))
