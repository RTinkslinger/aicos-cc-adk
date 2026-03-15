"""Unit tests for Web Agent hooks.

Tests rate limiting, input validation, audit logging, and metrics emission.
Uses pytest + unittest.mock for isolation.
"""

import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from web.hooks import (
    emit_metrics,
    input_validation,
    log_audit,
    rate_limit_check,
    record_strategy_outcome,
)


# -----------------------------------------------------------------------
# Tests for rate_limit_check hook
# -----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_rate_limit_allows_normal_traffic():
    """rate_limit_check() should allow normal traffic (< 10 req/min)."""
    input_data = {
        "tool_input": {
            "url": "https://example.com/page1",
        }
    }

    result = await rate_limit_check(input_data, tool_use_id="test", context=None)

    # Empty dict means allow
    assert result == {}


@pytest.mark.asyncio
async def test_rate_limit_blocks_excessive():
    """rate_limit_check() should block when 10+ requests in 60s."""
    # Make 11 rapid requests to same domain
    input_data_template = {
        "tool_input": {
            "url": "https://example.com/page{}",
        }
    }

    # Reset the module-level counter before test
    import web.hooks

    web.hooks._domain_counts.clear()

    # Allow first 10
    for i in range(10):
        input_data = {
            "tool_input": {
                "url": f"https://example.com/page{i}",
            }
        }
        result = await rate_limit_check(input_data, tool_use_id="test", context=None)
        assert result == {}, f"Request {i} should have been allowed"

    # 11th should be denied
    input_data = {
        "tool_input": {
            "url": "https://example.com/page11",
        }
    }
    result = await rate_limit_check(input_data, tool_use_id="test", context=None)

    assert "hookSpecificOutput" in result
    assert result["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert "Rate limit exceeded" in result["hookSpecificOutput"]["permissionDecisionReason"]


@pytest.mark.asyncio
async def test_rate_limit_no_url():
    """rate_limit_check() should allow when no URL provided."""
    input_data = {"tool_input": {}}

    result = await rate_limit_check(input_data, tool_use_id="test", context=None)

    assert result == {}


@pytest.mark.asyncio
async def test_rate_limit_pruning():
    """rate_limit_check() should prune old timestamps beyond 60s window."""
    import web.hooks

    web.hooks._domain_counts.clear()

    # Inject old timestamp (70 seconds ago)
    old_time = time.time() - 70
    web.hooks._domain_counts["old.example.com"] = [old_time]

    input_data = {
        "tool_input": {
            "url": "https://old.example.com/page",
        }
    }

    result = await rate_limit_check(input_data, tool_use_id="test", context=None)

    # Should allow because old entry was pruned
    assert result == {}
    # Verify pruning happened
    assert len(web.hooks._domain_counts.get("old.example.com", [])) == 1


# -----------------------------------------------------------------------
# Tests for input_validation hook
# -----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_input_validation_allows_valid_url():
    """input_validation() should allow http/https URLs."""
    input_data = {
        "tool_input": {
            "url": "https://example.com",
        }
    }

    result = await input_validation(input_data, tool_use_id="test", context=None)

    assert result == {}


@pytest.mark.asyncio
async def test_input_validation_blocks_invalid_scheme():
    """input_validation() should block non-http schemes."""
    input_data = {
        "tool_input": {
            "url": "ftp://example.com",
        }
    }

    result = await input_validation(input_data, tool_use_id="test", context=None)

    assert "hookSpecificOutput" in result
    assert result["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert "Invalid URL scheme" in result["hookSpecificOutput"]["permissionDecisionReason"]


@pytest.mark.asyncio
async def test_input_validation_blocks_oversized_content():
    """input_validation() should block content > 5MB."""
    large_content = "x" * (5_000_001)  # 5MB + 1 byte
    input_data = {
        "tool_input": {
            "content": large_content,
        }
    }

    result = await input_validation(input_data, tool_use_id="test", context=None)

    assert "hookSpecificOutput" in result
    assert result["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert "Content payload too large" in result["hookSpecificOutput"]["permissionDecisionReason"]


@pytest.mark.asyncio
async def test_input_validation_allows_undersized_content():
    """input_validation() should allow content < 5MB."""
    content = "x" * 1_000  # 1KB
    input_data = {
        "tool_input": {
            "content": content,
        }
    }

    result = await input_validation(input_data, tool_use_id="test", context=None)

    assert result == {}


# -----------------------------------------------------------------------
# Tests for log_audit hook
# -----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_log_audit_returns_empty():
    """log_audit() should return empty dict (logging only)."""
    result_data = {
        "tool_name": "scrape",
        "tool_output": {
            "content": "result",
            "status": 200,
        },
    }

    with patch("web.hooks.logger.info") as mock_log:
        result = await log_audit(result_data, tool_use_id="test-123", context=None)

        assert result == {}
        mock_log.assert_called_once()
        # Verify logging happened with correct extra data
        call_args = mock_log.call_args
        assert call_args[0][0] == "tool_complete"
        assert call_args[1]["extra"]["tool_name"] == "scrape"
        assert call_args[1]["extra"]["tool_use_id"] == "test-123"


@pytest.mark.asyncio
async def test_log_audit_detects_error():
    """log_audit() should detect errors in tool output."""
    result_data = {
        "tool_name": "scrape",
        "tool_output": {
            "error": "Connection timeout",
        },
    }

    with patch("web.hooks.logger.info") as mock_log:
        result = await log_audit(result_data, tool_use_id="test-456", context=None)

        assert result == {}
        call_args = mock_log.call_args
        assert call_args[1]["extra"]["has_error"] is True


@pytest.mark.asyncio
async def test_log_audit_handles_non_dict_output():
    """log_audit() should handle non-dict tool outputs gracefully."""
    result_data = {
        "tool_name": "scrape",
        "tool_output": "string output",
    }

    with patch("web.hooks.logger.info") as mock_log:
        result = await log_audit(result_data, tool_use_id="test-789", context=None)

        assert result == {}
        mock_log.assert_called_once()


# -----------------------------------------------------------------------
# Tests for record_strategy_outcome hook
# -----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_record_strategy_outcome_for_browse():
    """record_strategy_outcome() should record outcomes for browse tool."""
    result_data = {
        "tool_name": "browse",
        "tool_input": {
            "url": "https://example.com",
            "readiness_mode": "auto",
        },
        "tool_output": {
            "content": "page content",
            "status": 200,
        },
    }

    with patch("web.hooks.record_outcome") as mock_record:
        result = await record_strategy_outcome(result_data, tool_use_id="test", context=None)

        assert result == {}
        mock_record.assert_called_once()
        call_args = mock_record.call_args
        assert call_args[1]["origin"] == "example.com"
        assert "browser" in call_args[1]["strategy_name"]
        assert call_args[1]["success"] is True


@pytest.mark.asyncio
async def test_record_strategy_outcome_for_scrape():
    """record_strategy_outcome() should record jina vs firecrawl strategy."""
    result_data = {
        "tool_name": "scrape",
        "tool_input": {
            "url": "https://example.com",
            "use_firecrawl": False,
        },
        "tool_output": {
            "content": "content",
            "status": 200,
        },
    }

    with patch("web.hooks.record_outcome") as mock_record:
        result = await record_strategy_outcome(result_data, tool_use_id="test", context=None)

        assert result == {}
        call_args = mock_record.call_args
        assert call_args[1]["strategy_name"] == "jina_reader"


@pytest.mark.asyncio
async def test_record_strategy_outcome_detects_failure():
    """record_strategy_outcome() should mark failures correctly."""
    result_data = {
        "tool_name": "scrape",
        "tool_input": {
            "url": "https://example.com",
        },
        "tool_output": {
            "error": "timeout",
        },
    }

    with patch("web.hooks.record_outcome") as mock_record:
        result = await record_strategy_outcome(result_data, tool_use_id="test", context=None)

        assert result == {}
        call_args = mock_record.call_args
        assert call_args[1]["success"] is False


@pytest.mark.asyncio
async def test_record_strategy_outcome_ignores_other_tools():
    """record_strategy_outcome() should ignore tools outside browse/scrape/search."""
    result_data = {
        "tool_name": "health_check",
        "tool_input": {},
        "tool_output": {"status": "ok"},
    }

    with patch("web.hooks.record_outcome") as mock_record:
        result = await record_strategy_outcome(result_data, tool_use_id="test", context=None)

        assert result == {}
        mock_record.assert_not_called()


@pytest.mark.asyncio
async def test_record_strategy_outcome_handles_exception():
    """record_strategy_outcome() should gracefully handle import/execution errors."""
    result_data = {
        "tool_name": "browse",
        "tool_input": {
            "url": "https://example.com",
        },
        "tool_output": {"content": "ok", "status": 200},
    }

    with patch("web.hooks.record_outcome", side_effect=Exception("DB error")):
        with patch("web.hooks.logger.warning") as mock_warn:
            result = await record_strategy_outcome(result_data, tool_use_id="test", context=None)

            assert result == {}
            mock_warn.assert_called_once()


# -----------------------------------------------------------------------
# Tests for emit_metrics hook
# -----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_emit_metrics_returns_empty():
    """emit_metrics() should return empty dict (logging only)."""
    result_data = {}

    with patch("web.hooks.logger.info") as mock_log:
        result = await emit_metrics(result_data, tool_use_id="test", context=None)

        assert result == {}
        mock_log.assert_called_once()
        call_args = mock_log.call_args
        assert call_args[0][0] == "session_complete"
        assert call_args[1]["extra"]["event_type"] == "session_end"
