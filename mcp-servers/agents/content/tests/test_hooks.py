"""Unit tests for Content Agent hook callbacks.

Hooks are stateless (log + return {}). No state tracking.
The agent tracks its own completeness via conversation context.
See: docs/superpowers/specs/2026-03-15-agentic-pipeline-reference.md
"""
from __future__ import annotations

from unittest.mock import patch

import pytest

from content import hooks


class TestLogAnalysisAudit:
    """Test the PostToolUse log_analysis_audit hook."""

    @pytest.mark.asyncio
    async def test_returns_empty_dict(self) -> None:
        result_data = {"tool_name": "score_action", "tool_output": {"status": "ok"}}
        result = await hooks.log_analysis_audit(result_data, "test-id", None)
        assert result == {}

    @pytest.mark.asyncio
    async def test_handles_missing_tool_name(self) -> None:
        result_data = {"tool_output": {"status": "ok"}}
        result = await hooks.log_analysis_audit(result_data, "test-id", None)
        assert result == {}

    @pytest.mark.asyncio
    async def test_detects_error_in_output(self) -> None:
        result_data = {"tool_name": "publish_digest", "tool_output": {"error": "fail"}}
        with patch("content.hooks.logger") as mock_logger:
            await hooks.log_analysis_audit(result_data, "test-id", None)
            call_kwargs = mock_logger.info.call_args[1]
            assert call_kwargs["extra"]["has_error"] is True

    @pytest.mark.asyncio
    async def test_detects_status_error(self) -> None:
        result_data = {"tool_name": "x", "tool_output": {"status": "error"}}
        with patch("content.hooks.logger") as mock_logger:
            await hooks.log_analysis_audit(result_data, "test-id", None)
            call_kwargs = mock_logger.info.call_args[1]
            assert call_kwargs["extra"]["has_error"] is True

    @pytest.mark.asyncio
    async def test_no_error_on_success(self) -> None:
        result_data = {"tool_name": "score_action", "tool_output": {"status": "ok"}}
        with patch("content.hooks.logger") as mock_logger:
            await hooks.log_analysis_audit(result_data, "test-id", None)
            call_kwargs = mock_logger.info.call_args[1]
            assert call_kwargs["extra"]["has_error"] is False

    @pytest.mark.asyncio
    async def test_logs_tool_name(self) -> None:
        result_data = {"tool_name": "cos_get_thesis_threads", "tool_output": {}}
        with patch("content.hooks.logger") as mock_logger:
            await hooks.log_analysis_audit(result_data, "use-123", None)
            call_kwargs = mock_logger.info.call_args[1]
            assert call_kwargs["extra"]["tool_name"] == "cos_get_thesis_threads"
            assert call_kwargs["extra"]["tool_use_id"] == "use-123"


class TestEmitMetrics:
    """Test the Stop hook emit_metrics."""

    @pytest.mark.asyncio
    async def test_returns_empty_dict(self) -> None:
        result = await hooks.emit_metrics({}, None, None)
        assert result == {}

    @pytest.mark.asyncio
    async def test_logs_session_end(self) -> None:
        with patch("content.hooks.logger") as mock_logger:
            await hooks.emit_metrics({}, None, None)
            mock_logger.info.assert_called_once()
            call_kwargs = mock_logger.info.call_args[1]
            assert call_kwargs["extra"]["event_type"] == "session_end"
