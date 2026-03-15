"""Unit tests for Content Agent hook callbacks."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from content import hooks


class TestLogAnalysisAudit:
    """Test the PostToolUse log_analysis_audit hook."""

    @pytest.mark.asyncio
    async def test_log_analysis_audit_returns_empty(self) -> None:
        """Test that log_analysis_audit returns an empty dict."""
        result_data = {
            "tool_name": "score_action",
            "tool_output": {"status": "ok"},
        }
        result = await hooks.log_analysis_audit(
            result_data=result_data,
            tool_use_id="test-id",
            context=None,
        )
        assert result == {}

    @pytest.mark.asyncio
    async def test_log_analysis_audit_tracks_tool_name(self) -> None:
        """Test that log_analysis_audit appends tool name to tracking list."""
        # Clear the tracking list first
        hooks._tools_called.clear()

        result_data = {
            "tool_name": "score_action",
            "tool_output": {"status": "ok"},
        }
        await hooks.log_analysis_audit(
            result_data=result_data,
            tool_use_id="test-id",
            context=None,
        )

        assert "score_action" in hooks._tools_called

    @pytest.mark.asyncio
    async def test_log_analysis_audit_detects_error(self) -> None:
        """Test that log_analysis_audit correctly identifies errors in tool_output."""
        hooks._tools_called.clear()

        result_data = {
            "tool_name": "publish_digest",
            "tool_output": {"error": "Something went wrong"},
        }
        result = await hooks.log_analysis_audit(
            result_data=result_data,
            tool_use_id="test-id",
            context=None,
        )

        # Should still return empty dict
        assert result == {}
        assert "publish_digest" in hooks._tools_called

    @pytest.mark.asyncio
    async def test_log_analysis_audit_detects_status_error(self) -> None:
        """Test that log_analysis_audit detects status=error in tool_output."""
        hooks._tools_called.clear()

        result_data = {
            "tool_name": "load_context",
            "tool_output": {"status": "error", "message": "CONTEXT.md not found"},
        }
        result = await hooks.log_analysis_audit(
            result_data=result_data,
            tool_use_id="test-id",
            context=None,
        )

        assert result == {}
        assert "load_context" in hooks._tools_called

    @pytest.mark.asyncio
    async def test_log_analysis_audit_missing_tool_name(self) -> None:
        """Test that log_analysis_audit handles missing tool_name gracefully."""
        hooks._tools_called.clear()

        result_data = {
            "tool_output": {"status": "ok"},
            # Missing tool_name
        }
        result = await hooks.log_analysis_audit(
            result_data=result_data,
            tool_use_id="test-id",
            context=None,
        )

        assert result == {}
        assert "unknown" in hooks._tools_called


class TestVerifyPipelineCompletion:
    """Test the Stop hook verify_pipeline_completion."""

    @pytest.mark.asyncio
    async def test_verify_pipeline_completion_warns_on_missing(self) -> None:
        """Test that verify_pipeline_completion logs warning when score_action is missing."""
        hooks._tools_called.clear()
        hooks._tools_called.append("publish_digest")

        with patch("content.hooks.logger") as mock_logger:
            result = await hooks.verify_pipeline_completion(
                result_data={},
                tool_use_id=None,
                context=None,
            )

            assert result == {}
            # Should have logged a warning about missing tools
            mock_logger.warning.assert_called_once()
            call_kwargs = mock_logger.warning.call_args[1]
            assert "missing_tools" in call_kwargs["extra"]
            assert "score_action" in call_kwargs["extra"]["missing_tools"]

    @pytest.mark.asyncio
    async def test_verify_pipeline_completion_success(self) -> None:
        """Test that verify_pipeline_completion logs success when all expected tools are called."""
        hooks._tools_called.clear()
        hooks._tools_called.append("score_action")
        hooks._tools_called.append("publish_digest")

        with patch("content.hooks.logger") as mock_logger:
            result = await hooks.verify_pipeline_completion(
                result_data={},
                tool_use_id=None,
                context=None,
            )

            assert result == {}
            # Should have logged info about pipeline completion
            mock_logger.info.assert_called()
            call_kwargs = mock_logger.info.call_args[1]
            assert call_kwargs["extra"]["event_type"] == "pipeline_ok"

    @pytest.mark.asyncio
    async def test_verify_pipeline_completion_resets_tools_called(self) -> None:
        """Test that verify_pipeline_completion resets _tools_called for next session."""
        hooks._tools_called.clear()
        hooks._tools_called.append("score_action")
        hooks._tools_called.append("publish_digest")

        with patch("content.hooks.logger"):
            await hooks.verify_pipeline_completion(
                result_data={},
                tool_use_id=None,
                context=None,
            )

        # After the call, _tools_called should be empty
        assert hooks._tools_called == []

    @pytest.mark.asyncio
    async def test_verify_pipeline_completion_missing_publish_digest(self) -> None:
        """Test that verify_pipeline_completion warns when publish_digest is missing."""
        hooks._tools_called.clear()
        hooks._tools_called.append("score_action")

        with patch("content.hooks.logger") as mock_logger:
            result = await hooks.verify_pipeline_completion(
                result_data={},
                tool_use_id=None,
                context=None,
            )

            assert result == {}
            mock_logger.warning.assert_called_once()
            call_kwargs = mock_logger.warning.call_args[1]
            assert "publish_digest" in call_kwargs["extra"]["missing_tools"]

    @pytest.mark.asyncio
    async def test_verify_pipeline_completion_missing_both(self) -> None:
        """Test that verify_pipeline_completion warns when both tools are missing."""
        hooks._tools_called.clear()

        with patch("content.hooks.logger") as mock_logger:
            result = await hooks.verify_pipeline_completion(
                result_data={},
                tool_use_id=None,
                context=None,
            )

            assert result == {}
            mock_logger.warning.assert_called_once()
            call_kwargs = mock_logger.warning.call_args[1]
            missing = call_kwargs["extra"]["missing_tools"]
            assert "score_action" in missing
            assert "publish_digest" in missing


class TestEmitMetrics:
    """Test the Stop hook emit_metrics."""

    @pytest.mark.asyncio
    async def test_emit_metrics_returns_empty(self) -> None:
        """Test that emit_metrics returns an empty dict."""
        result = await hooks.emit_metrics(
            result_data={},
            tool_use_id=None,
            context=None,
        )
        assert result == {}

    @pytest.mark.asyncio
    async def test_emit_metrics_logs_session_complete(self) -> None:
        """Test that emit_metrics logs session_complete event."""
        with patch("content.hooks.logger") as mock_logger:
            result = await hooks.emit_metrics(
                result_data={},
                tool_use_id=None,
                context=None,
            )

            assert result == {}
            mock_logger.info.assert_called_once()
            call_kwargs = mock_logger.info.call_args[1]
            assert call_kwargs["extra"]["event_type"] == "session_end"


class TestHookState:
    """Test module-level state in hooks."""

    def test_expected_pipeline_tools_constant(self) -> None:
        """Verify _EXPECTED_PIPELINE_TOOLS contains expected values."""
        assert "score_action" in hooks._EXPECTED_PIPELINE_TOOLS
        assert "publish_digest" in hooks._EXPECTED_PIPELINE_TOOLS
        assert isinstance(hooks._EXPECTED_PIPELINE_TOOLS, frozenset)

    def test_tools_called_list_mutable(self) -> None:
        """Verify _tools_called can be modified."""
        original_len = len(hooks._tools_called)
        hooks._tools_called.append("test_tool")
        assert len(hooks._tools_called) == original_len + 1
        hooks._tools_called.remove("test_tool")

    def test_tools_called_starts_empty_or_manageable(self) -> None:
        """Verify _tools_called list is manageable between tests."""
        # This verifies the state doesn't blow up
        hooks._tools_called.clear()
        assert isinstance(hooks._tools_called, list)


class TestHookIntegration:
    """Test hook interactions."""

    @pytest.mark.asyncio
    async def test_full_pipeline_flow(self) -> None:
        """Test a full pipeline: log audit, then verify completion."""
        hooks._tools_called.clear()

        # Simulate first tool call
        await hooks.log_analysis_audit(
            result_data={
                "tool_name": "score_action",
                "tool_output": {"status": "ok"},
            },
            tool_use_id="id1",
            context=None,
        )

        # Simulate second tool call
        await hooks.log_analysis_audit(
            result_data={
                "tool_name": "publish_digest",
                "tool_output": {"status": "ok"},
            },
            tool_use_id="id2",
            context=None,
        )

        # Verify completion (should not warn)
        with patch("content.hooks.logger") as mock_logger:
            await hooks.verify_pipeline_completion(
                result_data={},
                tool_use_id=None,
                context=None,
            )

            # Should have logged info (success), not warning
            mock_logger.info.assert_called()
            assert mock_logger.warning.call_count == 0

        # Tools called list should be reset
        assert hooks._tools_called == []

    @pytest.mark.asyncio
    async def test_incomplete_pipeline_flow(self) -> None:
        """Test an incomplete pipeline: missing one tool."""
        hooks._tools_called.clear()

        # Simulate only one tool call
        await hooks.log_analysis_audit(
            result_data={
                "tool_name": "score_action",
                "tool_output": {"status": "ok"},
            },
            tool_use_id="id1",
            context=None,
        )

        # Verify completion (should warn)
        with patch("content.hooks.logger") as mock_logger:
            await hooks.verify_pipeline_completion(
                result_data={},
                tool_use_id=None,
                context=None,
            )

            # Should have logged warning
            mock_logger.warning.assert_called_once()

        # Tools called list should be reset even on warning
        assert hooks._tools_called == []
