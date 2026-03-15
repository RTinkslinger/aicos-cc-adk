"""Sync Agent hooks.

PostToolUse: audit log — every tool completion is recorded for traceability.
Stop: sync metrics — session end summary with trace correlation.
"""

from __future__ import annotations

from typing import Any

from shared.logging import get_trace_id, setup_logger

logger = setup_logger("sync-agent")


async def sync_audit_log(
    result_data: dict[str, Any],
    tool_use_id: str,
    context: Any,
) -> dict[str, Any]:
    """PostToolUse hook: log every tool completion for audit trail.

    Captures tool name, tool_use_id, and trace_id for cross-agent correlation.
    Returns empty dict (no mutation of result).
    """
    logger.info(
        "tool_complete",
        extra={
            "event_type": "tool_call",
            "tool_name": result_data.get("tool_name", "unknown"),
            "tool_use_id": tool_use_id,
            "trace_id": get_trace_id(),
        },
    )
    return {}


async def emit_sync_metrics(
    result_data: dict[str, Any],
    tool_use_id: str,
    context: Any,
) -> dict[str, Any]:
    """Stop hook: log session end metrics.

    Captures session completion event with trace_id. Any cost/turns data
    available in result_data is forwarded to the structured log.
    """
    logger.info(
        "session_complete",
        extra={
            "event_type": "session_end",
            "trace_id": get_trace_id(),
            "cost_usd": result_data.get("cost_usd"),
            "turns_used": result_data.get("turns_used"),
            "tools_called": result_data.get("tools_called"),
        },
    )
    return {}
