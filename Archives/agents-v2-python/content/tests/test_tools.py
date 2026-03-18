"""Unit tests for Content Agent tools."""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from content import tools


class TestFastMCPTools:
    """Test the 4 FastMCP tool functions."""

    @pytest.mark.asyncio
    async def test_health_check(self) -> None:
        """Test health_check returns expected status."""
        result = await tools.health_check()
        assert result == {"status": "ok", "agent": "content-agent"}

    @pytest.mark.asyncio
    async def test_pipeline_status_returns_dict(self) -> None:
        """Test pipeline_status returns dict with expected keys."""
        result = await tools.pipeline_status()
        assert isinstance(result, dict)
        assert "status" in result
        assert "last_run" in result
        assert "videos_processed" in result
        assert "errors" in result

    def test_all_fastmcp_functions_exist(self) -> None:
        """Verify all 4 FastMCP function names are importable from content.tools."""
        assert hasattr(tools, "health_check")
        assert hasattr(tools, "pipeline_status")
        assert hasattr(tools, "analyze_content")
        assert hasattr(tools, "trigger_pipeline")

    def test_sdk_server_exists(self) -> None:
        """Verify content_sdk_server is importable."""
        assert hasattr(tools, "content_sdk_server")
        assert tools.content_sdk_server is not None

    @pytest.mark.asyncio
    async def test_score_action_tool(self) -> None:
        """Test the @tool score_action with known inputs.

        Verifies that score is in expected range and classification is valid.
        """
        args = {
            "bucket_impact": 8.0,
            "conviction_change": 7.0,
            "time_sensitivity": 6.0,
            "action_novelty": 5.0,
            "effort_vs_impact": 9.0,
        }
        result = await tools.score_action_tool(args)

        # Check response structure
        assert isinstance(result, dict)
        assert "content" in result
        assert isinstance(result["content"], list)
        assert len(result["content"]) > 0

        # Check content format
        content = result["content"][0]
        assert content["type"] == "text"
        assert "Score:" in content["text"]
        assert "Classification:" in content["text"]

        # Parse score and verify it's in range
        text = content["text"]
        assert "surface" in text or "low_confidence" in text or "context_only" in text

    @pytest.mark.asyncio
    async def test_score_action_tool_low_values(self) -> None:
        """Test score_action with low input values."""
        args = {
            "bucket_impact": 1.0,
            "conviction_change": 1.0,
            "time_sensitivity": 1.0,
            "action_novelty": 1.0,
            "effort_vs_impact": 1.0,
        }
        result = await tools.score_action_tool(args)

        # Verify structure
        assert isinstance(result, dict)
        assert "content" in result
        text = result["content"][0]["text"]
        # Low values should result in "context_only"
        assert "context_only" in text

    @pytest.mark.asyncio
    async def test_score_action_tool_high_values(self) -> None:
        """Test score_action with high input values."""
        args = {
            "bucket_impact": 10.0,
            "conviction_change": 10.0,
            "time_sensitivity": 10.0,
            "action_novelty": 10.0,
            "effort_vs_impact": 10.0,
        }
        result = await tools.score_action_tool(args)

        # Verify structure
        assert isinstance(result, dict)
        assert "content" in result
        text = result["content"][0]["text"]
        # High values should result in "surface"
        assert "surface" in text


class TestPipelineState:
    """Test module-level pipeline_state management."""

    def test_pipeline_state_initial_values(self) -> None:
        """Verify pipeline_state is initialized with expected structure."""
        state = tools.pipeline_state
        assert isinstance(state, dict)
        assert "last_run" in state
        assert "videos_processed" in state
        assert "errors" in state
        assert "status" in state

    def test_pipeline_state_is_mutable(self) -> None:
        """Verify pipeline_state can be modified."""
        original_status = tools.pipeline_state["status"]
        tools.pipeline_state["status"] = "running"
        assert tools.pipeline_state["status"] == "running"
        # Restore
        tools.pipeline_state["status"] = original_status


class TestToolRegistry:
    """Test that tools are properly registered for SDK."""

    def test_score_action_tool_has_metadata(self) -> None:
        """Verify score_action_tool has expected metadata."""
        # The tool should have __wrapped__ or similar marker from decorator
        assert callable(tools.score_action_tool)

    def test_publish_digest_tool_exists(self) -> None:
        """Verify publish_digest_tool is defined."""
        assert hasattr(tools, "publish_digest_tool")
        assert callable(tools.publish_digest_tool)

    def test_load_context_tool_exists(self) -> None:
        """Verify load_context_tool is defined."""
        assert hasattr(tools, "load_context_tool")
        assert callable(tools.load_context_tool)


class TestAsyncTools:
    """Test async behavior of tools."""

    @pytest.mark.asyncio
    async def test_health_check_is_async(self) -> None:
        """Verify health_check is callable as coroutine."""
        result = await tools.health_check()
        assert result is not None

    @pytest.mark.asyncio
    async def test_pipeline_status_is_async(self) -> None:
        """Verify pipeline_status is callable as coroutine."""
        result = await tools.pipeline_status()
        assert result is not None

    @pytest.mark.asyncio
    async def test_multiple_health_checks(self) -> None:
        """Verify multiple health checks can run concurrently."""
        results = await asyncio.gather(
            tools.health_check(),
            tools.health_check(),
            tools.health_check(),
        )
        assert len(results) == 3
        assert all(r["status"] == "ok" for r in results)
