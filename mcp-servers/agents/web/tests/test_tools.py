"""Unit tests for Web Agent tools.

Tests all 11 FastMCP tool functions and SDK server existence.
Uses pytest + unittest.mock for isolation.
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from web.tools import (
    cookie_status,
    extract_transcript,
    extract_youtube,
    fingerprint,
    health_check,
    web_browse,
    web_scrape,
    web_search,
    web_screenshot,
    web_task,
    watch_url,
    web_sdk_server,
)


# -----------------------------------------------------------------------
# Tests for FastMCP tool functions
# -----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_health_check():
    """health_check() should return status OK."""
    result = await health_check()
    assert isinstance(result, dict)
    assert result["status"] == "ok"
    assert result["agent"] == "web-agent"


@pytest.mark.asyncio
async def test_web_scrape_calls_lib():
    """web_scrape() should call lib.scrape.scrape."""
    with patch("web.tools.scrape") as mock_scrape:
        mock_scrape.return_value = {
            "content": "Mock content",
            "content_length": 12,
            "source": "jina",
            "status": 200,
        }

        result = await web_scrape("https://example.com")

        mock_scrape.assert_called_once_with("https://example.com", use_firecrawl=False)
        assert result["url"] == "https://example.com"
        assert result["content"] == "Mock content"
        assert result["content_length"] == 12


@pytest.mark.asyncio
async def test_web_scrape_with_firecrawl():
    """web_scrape() should pass use_firecrawl flag."""
    with patch("web.tools.scrape") as mock_scrape:
        mock_scrape.return_value = {
            "content": "FC content",
            "content_length": 9,
            "source": "firecrawl",
            "status": 200,
        }

        result = await web_scrape("https://example.com", use_firecrawl=True)

        mock_scrape.assert_called_once_with("https://example.com", use_firecrawl=True)
        assert result["source"] == "firecrawl"


@pytest.mark.asyncio
async def test_web_browse_calls_lib():
    """web_browse() should call lib.browser.browse."""
    with patch("web.tools.browse") as mock_browse:
        mock_browse.return_value = {
            "content": "Page content",
            "status": 200,
        }

        result = await web_browse("https://example.com")

        mock_browse.assert_called_once()
        assert result["content"] == "Page content"


@pytest.mark.asyncio
async def test_web_search_calls_lib():
    """web_search() should call lib.search.search."""
    with patch("web.tools.search") as mock_search:
        mock_search.return_value = {
            "results": [{"title": "Result 1", "url": "https://example.com"}],
        }

        result = await web_search("test query", limit=5)

        mock_search.assert_called_once_with("test query", limit=5)
        assert "results" in result


@pytest.mark.asyncio
async def test_web_screenshot_calls_lib():
    """web_screenshot() should call lib.browser.browse with screenshot action."""
    with patch("web.tools.browse") as mock_browse:
        mock_browse.return_value = {
            "screenshot_base64": "iVBORw0KGgo=",
        }

        result = await web_screenshot("https://example.com")

        mock_browse.assert_called_once()
        call_args = mock_browse.call_args
        assert call_args[1]["url"] == "https://example.com"
        assert call_args[1]["action"] == "screenshot"


@pytest.mark.asyncio
async def test_extract_youtube_calls_lib():
    """extract_youtube() should call lib.extraction.extract_and_save."""
    with patch("web.tools.extract_and_save") as mock_extract:
        # Mock returns a path, function reads and returns JSON
        mock_path = MagicMock()
        mock_path.__str__ = MagicMock(return_value="/tmp/youtube_extract_test.json")
        mock_extract.return_value = mock_path

        mock_data = {
            "extraction_timestamp": "2024-01-01T00:00:00",
            "source_playlist": "https://youtube.com/playlist?list=test",
            "total_videos": 1,
            "videos": [{"video_id": "test", "title": "Test Video"}],
        }

        with patch("builtins.open", create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = json.dumps(mock_data)
            mock_open.return_value.__enter__.return_value = MagicMock()
            mock_open.return_value.__enter__.return_value.__iter__ = MagicMock(return_value=iter([]))

            with patch("json.load", return_value=mock_data):
                result = await extract_youtube()

                mock_extract.assert_called_once()
                assert result["total_videos"] == 1
                assert "output_file" in result


@pytest.mark.asyncio
async def test_extract_youtube_no_videos():
    """extract_youtube() should handle no_videos response."""
    with patch("web.tools.extract_and_save") as mock_extract:
        mock_extract.return_value = None

        result = await extract_youtube()

        assert result["status"] == "no_videos"
        assert result["total_videos"] == 0


@pytest.mark.asyncio
async def test_extract_transcript_calls_lib():
    """extract_transcript() should call lib.extraction.get_transcript."""
    with patch("web.tools.extract_video_id") as mock_extract_id:
        with patch("web.tools.get_transcript") as mock_get_transcript:
            mock_extract_id.return_value = "dQw4w9WgXcQ"
            mock_get_transcript.return_value = {
                "success": True,
                "full_text": "Mock transcript",
                "segments": [],
            }

            result = await extract_transcript("dQw4w9WgXcQ")

            mock_extract_id.assert_called_once_with("dQw4w9WgXcQ")
            mock_get_transcript.assert_called_once_with("dQw4w9WgXcQ")
            assert result["success"] is True


@pytest.mark.asyncio
async def test_cookie_status_returns_dict():
    """cookie_status() should return a dict with status info."""
    with patch("web.tools._cookie_status") as mock_status:
        mock_status.return_value = {
            "cookies": [
                {"domain": "youtube.com", "age_days": 5, "warning": None},
            ],
        }

        result = await cookie_status()

        mock_status.assert_called_once()
        assert isinstance(result, dict)
        assert "cookies" in result


@pytest.mark.asyncio
async def test_fingerprint_calls_lib():
    """fingerprint() should call lib.fingerprint.fingerprint."""
    with patch("web.tools._fingerprint") as mock_fingerprint:
        mock_fingerprint.return_value = {
            "framework": "react",
            "is_spa": True,
            "auth_required": False,
        }

        result = await fingerprint("https://example.com")

        mock_fingerprint.assert_called_once_with("https://example.com")
        assert result["framework"] == "react"
        assert result["is_spa"] is True


@pytest.mark.asyncio
async def test_watch_url_calls_lib():
    """watch_url() should call lib.monitor.register_watch."""
    with patch("web.tools.register_watch") as mock_register:
        mock_register.return_value = {
            "status": "registered",
            "url": "https://example.com",
            "interval_minutes": 60,
        }

        result = await watch_url("https://example.com")

        mock_register.assert_called_once()
        assert result["status"] == "registered"


@pytest.mark.asyncio
async def test_web_task_not_implemented():
    """web_task() should return not_implemented status (placeholder)."""
    result = await web_task("test task")

    assert result["status"] == "not_implemented"
    assert "message" in result


# -----------------------------------------------------------------------
# Tests for SDK server
# -----------------------------------------------------------------------


def test_sdk_server_exists():
    """web_sdk_server should be importable."""
    assert web_sdk_server is not None
    assert hasattr(web_sdk_server, "name")
    assert web_sdk_server.name == "web"


def test_all_fastmcp_functions_exist():
    """All 11 FastMCP tool functions should be importable."""
    functions = [
        "web_task",
        "web_scrape",
        "web_browse",
        "web_search",
        "web_screenshot",
        "extract_youtube",
        "extract_transcript",
        "cookie_status",
        "fingerprint",
        "watch_url",
        "health_check",
    ]

    for func_name in functions:
        assert hasattr(__import__("web.tools", fromlist=[func_name]), func_name), f"{func_name} not found"
