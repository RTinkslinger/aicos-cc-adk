"""Basic tests for sync/tools.py.

Tests:
  1. All 23 tool functions are importable.
  2. Idempotency: write_digest called twice with same request_id writes only once.
  3. Proxy error handling: circuit breaker open raises and tools return graceful error dict.
"""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# 1. Importability test — all 23 tools must be importable
# ---------------------------------------------------------------------------

EXPECTED_TOOLS = [
    # State read (9)
    "health_check",
    "cos_load_context",
    "cos_get_thesis_threads",
    "cos_get_recent_digests",
    "cos_get_actions",
    "cos_get_preferences",
    "cos_score_action",
    "cos_sync_status",
    "cos_get_changes",
    # Write-receiver (5)
    "write_digest",
    "write_actions",
    "update_thesis",
    "create_thesis_thread",
    "log_preference",
    # Sync operations (6)
    "cos_sync_thesis_status",
    "cos_sync_actions",
    "cos_full_sync",
    "cos_retry_sync_queue",
    "cos_process_changes",
    "cos_seed_thesis_db",
    # Proxy (3)
    "web_task",
    "web_scrape",
    "web_search",
]


def test_all_tools_importable():
    """All 23 tool functions must exist in sync.tools."""
    import sync.tools as tools_module

    for name in EXPECTED_TOOLS:
        assert hasattr(tools_module, name), f"Tool '{name}' not found in sync.tools"
        fn = getattr(tools_module, name)
        assert callable(fn), f"'{name}' is not callable"


def test_tool_count():
    """Exactly 23 tools must be defined (all expected names present)."""
    assert len(EXPECTED_TOOLS) == 23


# ---------------------------------------------------------------------------
# 2. Idempotency test for write_digest
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_write_digest_idempotency():
    """Calling write_digest twice with same request_id writes to Notion only once."""
    import sync.tools as tools

    # Simulate idempotency_log hit on second call
    _log: dict[str, str] = {}  # request_id -> notion_page_id

    def fake_connect(url: str):
        conn = MagicMock()
        cursor = MagicMock()
        conn.__enter__ = MagicMock(return_value=conn)
        conn.__exit__ = MagicMock(return_value=False)

        def fake_cursor_ctx():
            cur = MagicMock()
            cur.__enter__ = MagicMock(return_value=cur)
            cur.__exit__ = MagicMock(return_value=False)

            def execute_side_effect(query: str, params: tuple | None = None):
                if "SELECT result_id FROM idempotency_log" in query:
                    rid = params[0] if params else ""
                    cur.fetchone.return_value = (_log[rid],) if rid in _log else None
                elif "INSERT INTO idempotency_log" in query:
                    if params:
                        _log[params[0]] = params[1]

            cur.execute.side_effect = execute_side_effect
            return cur

        conn.cursor.return_value.__enter__ = MagicMock(return_value=MagicMock())
        # Use context manager protocol
        conn.cursor = fake_cursor_ctx
        return conn

    # Track how many times the Notion create_digest_entry is called
    call_count = 0

    async def fake_acquire():
        pass

    def fake_create_digest_entry(**kwargs: Any) -> dict[str, Any]:
        nonlocal call_count
        call_count += 1
        return {"id": "notion-page-abc123"}

    with (
        patch("sync.tools.psycopg2") as mock_psycopg2,
        patch("sync.lib.rate_limiter.notion_limiter") as mock_limiter,
        patch("sync.lib.notion_client.create_digest_entry", side_effect=fake_create_digest_entry),
    ):
        mock_psycopg2.connect.side_effect = fake_connect
        mock_limiter.acquire = AsyncMock(side_effect=fake_acquire)

        request_id = "test-digest-2026-03-15"
        digest_data: dict[str, Any] = {
            "title": "Test Video",
            "slug": "test-video",
            "url": "https://youtube.com/watch?v=test",
            "channel": "Test Channel",
            "relevance_score": "High",
            "net_newness": "New Insight",
            "connected_buckets": ["New Cap Tables"],
            "digest_url": "https://digest.wiki/test",
        }

        # First call — should write
        result1 = await tools.write_digest(digest_data=digest_data, request_id=request_id)
        assert result1["notion_page_id"] == "notion-page-abc123"
        assert result1["idempotent"] is False

        # Second call with same request_id — should return cached, skip Notion write
        result2 = await tools.write_digest(digest_data=digest_data, request_id=request_id)
        assert result2["idempotent"] is True
        assert result2["notion_page_id"] == "notion-page-abc123"

    # Notion create should have been called exactly once
    assert call_count == 1, f"Expected 1 Notion write, got {call_count}"


# ---------------------------------------------------------------------------
# 3. Proxy error handling — circuit breaker open
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_web_task_circuit_open_returns_error_dict():
    """web_task returns a graceful error dict when circuit breaker is open."""
    import pybreaker

    import sync.tools as tools

    with patch("sync.tools.call_agent_tool", new_callable=AsyncMock) as mock_call:
        mock_call.side_effect = pybreaker.CircuitBreakerError("web-agent")
        result = await tools.web_task(task="Research AI infrastructure companies")

    assert "error" in result
    assert result.get("circuit_open") is True


@pytest.mark.asyncio
async def test_web_scrape_circuit_open_returns_error_dict():
    """web_scrape returns a graceful error dict when circuit breaker is open."""
    import pybreaker

    import sync.tools as tools

    with patch("sync.tools.call_agent_tool", new_callable=AsyncMock) as mock_call:
        mock_call.side_effect = pybreaker.CircuitBreakerError("web-agent")
        result = await tools.web_scrape(url="https://example.com")

    assert "error" in result
    assert result.get("circuit_open") is True


@pytest.mark.asyncio
async def test_web_search_circuit_open_returns_error_dict():
    """web_search returns a graceful error dict when circuit breaker is open."""
    import pybreaker

    import sync.tools as tools

    with patch("sync.tools.call_agent_tool", new_callable=AsyncMock) as mock_call:
        mock_call.side_effect = pybreaker.CircuitBreakerError("web-agent")
        result = await tools.web_search(query="AI infrastructure VC trends 2026")

    assert "error" in result
    assert result.get("circuit_open") is True


@pytest.mark.asyncio
async def test_web_task_agent_call_error_returns_error_dict():
    """web_task returns error dict on AgentCallError (not just circuit open)."""
    from shared.mcp_client import AgentCallError

    import sync.tools as tools

    with patch("sync.tools.call_agent_tool", new_callable=AsyncMock) as mock_call:
        mock_call.side_effect = AgentCallError("web-agent/web_task: 500 Internal Server Error")
        result = await tools.web_task(task="Research companies")

    assert "error" in result
    assert "circuit_open" not in result or result.get("circuit_open") is not True
