"""Tests for State MCP server — DB modules and server tools.

Uses unittest.mock to mock the asyncpg pool. All tests are async
and rely on pytest-asyncio (asyncio_mode = "auto" in pyproject.toml).
"""

from __future__ import annotations

import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers — fake asyncpg Record objects
# ---------------------------------------------------------------------------

def _make_record(data: dict) -> MagicMock:
    """Create a mock that behaves like an asyncpg.Record (dict-like)."""
    record = MagicMock()
    record.__getitem__ = lambda self, key: data[key]
    record.keys = lambda: data.keys()
    record.values = lambda: data.values()
    record.items = lambda: data.items()
    # dict(record) needs __iter__ + __getitem__
    record.__iter__ = lambda self: iter(data)
    record.__len__ = lambda self: len(data)
    return record


def _thesis_row(**overrides) -> dict:
    """Default thesis thread row for testing."""
    base = {
        "id": 1,
        "name": "AI Agents in SaaS",
        "core_thesis": "AI agents will replace SaaS dashboards",
        "conviction": "New",
        "status": "Active",
        "evidence_for": "",
        "evidence_against": "",
        "key_questions": "",
        "notion_page_id": None,
        "notion_synced": False,
        "created_at": datetime(2026, 3, 15, 10, 0, 0),
        "updated_at": datetime(2026, 3, 15, 10, 0, 0),
    }
    base.update(overrides)
    return base


def _inbox_row(**overrides) -> dict:
    """Default inbox row for testing."""
    base = {
        "id": 1,
        "type": "track_source",
        "content": "Track @pmarca on X",
        "metadata": {},
        "processed": False,
        "processed_at": None,
        "created_at": datetime(2026, 3, 15, 10, 0, 0),
    }
    base.update(overrides)
    return base


def _notif_row(**overrides) -> dict:
    """Default notification row for testing."""
    base = {
        "id": 1,
        "source": "content_agent",
        "type": "digest_ready",
        "content": "New digest published: AI Agents Weekly #12",
        "metadata": {},
        "read": False,
        "created_at": datetime(2026, 3, 15, 10, 0, 0),
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_pool():
    """Create a mock asyncpg pool with async methods."""
    pool = AsyncMock()
    pool.fetch = AsyncMock(return_value=[])
    pool.fetchrow = AsyncMock(return_value=None)
    pool.fetchval = AsyncMock(return_value=1)
    pool.execute = AsyncMock(return_value="UPDATE 0")
    pool.close = AsyncMock()
    return pool


@pytest.fixture(autouse=True)
def patch_get_pool(mock_pool):
    """Patch get_pool in all DB modules to return the mock pool."""
    with (
        patch("state.db.thesis.get_pool", return_value=mock_pool),
        patch("state.db.inbox.get_pool", return_value=mock_pool),
        patch("state.db.notifications.get_pool", return_value=mock_pool),
        patch("state.db.connection.get_pool", return_value=mock_pool),
    ):
        yield


# ---------------------------------------------------------------------------
# Test: thesis.get_threads
# ---------------------------------------------------------------------------

class TestThesisGetThreads:
    async def test_returns_list_of_dicts(self, mock_pool):
        row_data = _thesis_row()
        mock_pool.fetch.return_value = [_make_record(row_data)]

        from state.db.thesis import get_threads

        result = await get_threads()
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["name"] == "AI Agents in SaaS"

    async def test_returns_empty_list_when_no_threads(self, mock_pool):
        mock_pool.fetch.return_value = []

        from state.db.thesis import get_threads

        result = await get_threads()
        assert result == []


# ---------------------------------------------------------------------------
# Test: thesis.create_thread
# ---------------------------------------------------------------------------

class TestThesisCreateThread:
    async def test_creates_with_notion_synced_false(self, mock_pool):
        row_data = _thesis_row(notion_synced=False)
        mock_pool.fetchrow.return_value = _make_record(row_data)

        from state.db.thesis import create_thread

        result = await create_thread("AI Agents in SaaS", "AI agents will replace SaaS dashboards")

        assert result["notion_synced"] is False
        assert result["name"] == "AI Agents in SaaS"

        # Verify the SQL was called with notion_synced=FALSE
        call_args = mock_pool.fetchrow.call_args
        sql = call_args[0][0]
        assert "FALSE" in sql
        assert call_args[0][1] == "AI Agents in SaaS"
        assert call_args[0][2] == "AI agents will replace SaaS dashboards"


# ---------------------------------------------------------------------------
# Test: thesis.update_thread
# ---------------------------------------------------------------------------

class TestThesisUpdateThread:
    async def test_appends_evidence_for(self, mock_pool):
        row_data = _thesis_row(evidence_for="New signal: Copilot adoption up 40%")
        mock_pool.fetchrow.return_value = _make_record(row_data)

        from state.db.thesis import update_thread

        result = await update_thread("AI Agents in SaaS", "New signal: Copilot adoption up 40%", "for")

        assert result["evidence_for"] == "New signal: Copilot adoption up 40%"
        call_sql = mock_pool.fetchrow.call_args[0][0]
        assert "evidence_for" in call_sql
        assert "notion_synced = FALSE" in call_sql

    async def test_appends_evidence_against(self, mock_pool):
        row_data = _thesis_row(evidence_against="Counter: enterprise adoption slow")
        mock_pool.fetchrow.return_value = _make_record(row_data)

        from state.db.thesis import update_thread

        result = await update_thread("AI Agents in SaaS", "Counter: enterprise adoption slow", "against")

        assert result["evidence_against"] == "Counter: enterprise adoption slow"

    async def test_mixed_appends_to_both(self, mock_pool):
        row_data = _thesis_row(
            evidence_for="Mixed signal data",
            evidence_against="Mixed signal data",
        )
        mock_pool.fetchrow.return_value = _make_record(row_data)

        from state.db.thesis import update_thread

        result = await update_thread("AI Agents in SaaS", "Mixed signal data", "mixed")

        call_sql = mock_pool.fetchrow.call_args[0][0]
        assert "evidence_for" in call_sql
        assert "evidence_against" in call_sql

    async def test_raises_on_invalid_direction(self, mock_pool):
        from state.db.thesis import update_thread

        with pytest.raises(ValueError, match="Invalid direction"):
            await update_thread("AI Agents in SaaS", "evidence", "invalid")

    async def test_raises_when_thread_not_found(self, mock_pool):
        mock_pool.fetchrow.return_value = None

        from state.db.thesis import update_thread

        with pytest.raises(ValueError, match="not found"):
            await update_thread("Nonexistent Thread", "evidence", "for")


# ---------------------------------------------------------------------------
# Test: inbox.post_message
# ---------------------------------------------------------------------------

class TestInboxPostMessage:
    async def test_posts_message(self, mock_pool):
        row_data = _inbox_row()
        mock_pool.fetchrow.return_value = _make_record(row_data)

        from state.db.inbox import post_message

        result = await post_message("track_source", "Track @pmarca on X")

        assert result["type"] == "track_source"
        assert result["content"] == "Track @pmarca on X"
        assert result["processed"] is False

    async def test_posts_message_with_metadata(self, mock_pool):
        meta = {"platform": "x", "handle": "@pmarca"}
        row_data = _inbox_row(metadata=meta)
        mock_pool.fetchrow.return_value = _make_record(row_data)

        from state.db.inbox import post_message

        result = await post_message("track_source", "Track @pmarca on X", metadata=meta)

        # Verify metadata was JSON-serialized in the SQL call
        call_args = mock_pool.fetchrow.call_args[0]
        assert json.loads(call_args[3]) == meta

    async def test_posts_message_without_metadata_defaults_empty(self, mock_pool):
        row_data = _inbox_row()
        mock_pool.fetchrow.return_value = _make_record(row_data)

        from state.db.inbox import post_message

        await post_message("general", "Hello")

        call_args = mock_pool.fetchrow.call_args[0]
        assert call_args[3] == "{}"


# ---------------------------------------------------------------------------
# Test: inbox.get_pending
# ---------------------------------------------------------------------------

class TestInboxGetPending:
    async def test_returns_unprocessed_messages(self, mock_pool):
        row_data = _inbox_row()
        mock_pool.fetch.return_value = [_make_record(row_data)]

        from state.db.inbox import get_pending

        result = await get_pending()
        assert len(result) == 1
        assert result[0]["processed"] is False


# ---------------------------------------------------------------------------
# Test: inbox.mark_processed
# ---------------------------------------------------------------------------

class TestInboxMarkProcessed:
    async def test_marks_message_processed(self, mock_pool):
        row_data = _inbox_row(processed=True, processed_at=datetime(2026, 3, 15, 10, 5, 0))
        mock_pool.fetchrow.return_value = _make_record(row_data)

        from state.db.inbox import mark_processed

        result = await mark_processed(1)
        assert result is not None
        assert result["processed"] is True

    async def test_returns_none_for_missing_id(self, mock_pool):
        mock_pool.fetchrow.return_value = None

        from state.db.inbox import mark_processed

        result = await mark_processed(999)
        assert result is None


# ---------------------------------------------------------------------------
# Test: notifications.get_unread
# ---------------------------------------------------------------------------

class TestNotificationsGetUnread:
    async def test_returns_unread_notifications(self, mock_pool):
        row_data = _notif_row()
        mock_pool.fetch.return_value = [_make_record(row_data)]

        from state.db.notifications import get_unread

        result = await get_unread()
        assert len(result) == 1
        assert result[0]["read"] is False
        assert result[0]["source"] == "content_agent"


# ---------------------------------------------------------------------------
# Test: notifications.post_notification
# ---------------------------------------------------------------------------

class TestNotificationsPostNotification:
    async def test_creates_notification(self, mock_pool):
        row_data = _notif_row()
        mock_pool.fetchrow.return_value = _make_record(row_data)

        from state.db.notifications import post_notification

        result = await post_notification("content_agent", "digest_ready", "New digest published")
        assert result["source"] == "content_agent"
        assert result["type"] == "digest_ready"


# ---------------------------------------------------------------------------
# Test: notifications.mark_read
# ---------------------------------------------------------------------------

class TestNotificationsMarkRead:
    async def test_marks_notifications_read(self, mock_pool):
        mock_pool.execute.return_value = "UPDATE 3"

        from state.db.notifications import mark_read

        count = await mark_read([1, 2, 3])
        assert count == 3

    async def test_empty_list_returns_zero(self, mock_pool):
        from state.db.notifications import mark_read

        count = await mark_read([])
        assert count == 0
        mock_pool.execute.assert_not_called()


# ---------------------------------------------------------------------------
# Test: server health_check tool
# ---------------------------------------------------------------------------

class TestHealthCheck:
    async def test_health_check_ok(self, mock_pool):
        mock_pool.fetchval.return_value = 1

        # Patch get_pool at the server module level too
        with patch("state.server.get_pool", return_value=mock_pool):
            from state.server import health_check

            result = await health_check()
            assert result["status"] == "ok"
            assert result["db_connected"] is True
            assert result["service"] == "state-mcp"

    async def test_health_check_db_failure(self, mock_pool):
        mock_pool.fetchval.side_effect = Exception("Connection refused")

        with patch("state.server.get_pool", return_value=mock_pool):
            from state.server import health_check

            result = await health_check()
            assert result["status"] == "degraded"
            assert result["db_connected"] is False
            assert "Connection refused" in result["db_error"]


# ---------------------------------------------------------------------------
# Test: server.get_state tool
# ---------------------------------------------------------------------------

class TestGetState:
    async def test_returns_both_sections_by_default(self, mock_pool):
        thesis_data = _thesis_row()
        notif_data = _notif_row()
        mock_pool.fetch.side_effect = [
            [_make_record(thesis_data)],  # get_threads call
            [_make_record(notif_data)],   # get_unread call
        ]

        with (
            patch("state.server.get_threads") as mock_get_threads,
            patch("state.server.get_unread") as mock_get_unread,
        ):
            mock_get_threads.return_value = [thesis_data]
            mock_get_unread.return_value = [notif_data]

            from state.server import get_state

            result = await get_state()
            assert "thesis_threads" in result
            assert "notifications" in result
            assert len(result["thesis_threads"]) == 1
            assert result["thesis_threads"][0]["name"] == "AI Agents in SaaS"

    async def test_filters_to_thesis_only(self, mock_pool):
        thesis_data = _thesis_row()

        with (
            patch("state.server.get_threads") as mock_get_threads,
            patch("state.server.get_unread") as mock_get_unread,
        ):
            mock_get_threads.return_value = [thesis_data]

            from state.server import get_state

            result = await get_state(include=["thesis"])
            assert "thesis_threads" in result
            assert "notifications" not in result
            mock_get_unread.assert_not_called()

    async def test_filters_to_notifications_only(self, mock_pool):
        notif_data = _notif_row()

        with (
            patch("state.server.get_threads") as mock_get_threads,
            patch("state.server.get_unread") as mock_get_unread,
        ):
            mock_get_unread.return_value = [notif_data]

            from state.server import get_state

            result = await get_state(include=["notifications"])
            assert "notifications" in result
            assert "thesis_threads" not in result
            mock_get_threads.assert_not_called()
