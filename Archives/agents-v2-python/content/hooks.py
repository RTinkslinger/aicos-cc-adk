"""Content Agent hook callbacks — stateless audit logging and session metrics.

Hook types used:
  PostToolUse:  log_analysis_audit  (stateless — log every tool call)
  Stop:         emit_metrics        (stateless — log session end)

No stateful tracking. The agent tracks its own completeness via conversation
context and system prompt instructions. See: docs/archives/old-specs/2026-03-15-agentic-pipeline-reference.md (ARCHIVED — v2 era, resolved by v3 architecture).

Registration (in agent.py):
    from claude_agent_sdk import ClaudeAgentOptions, HookMatcher
    options = ClaudeAgentOptions(
        hooks={
            "PostToolUse": [HookMatcher(hooks=[log_analysis_audit])],
            "Stop":         [HookMatcher(hooks=[emit_metrics])],
        }
    )
"""
from __future__ import annotations

from shared.logging import get_trace_id, setup_logger

logger = setup_logger("content-agent")


# -----------------------------------------------------------------------
# PostToolUse hook — stateless audit logging
# -----------------------------------------------------------------------


async def log_analysis_audit(
    result_data: dict,
    tool_use_id: str | None,
    context: object,
) -> dict:
    """PostToolUse: Structured audit log for every tool call.

    Stateless — just logs and returns {}. No state accumulation.
    Tool completion tracking is the agent's job (conversation context).
    """
    tool_name = result_data.get("tool_name", "unknown")

    tool_output = result_data.get("tool_output", {})
    has_error = False
    if isinstance(tool_output, dict):
        has_error = bool(tool_output.get("error")) or tool_output.get("status") == "error"

    logger.info(
        "tool_complete",
        extra={
            "event_type": "tool_call",
            "tool_name": tool_name,
            "tool_use_id": tool_use_id,
            "has_error": has_error,
            "trace_id": get_trace_id(),
        },
    )
    return {}


# -----------------------------------------------------------------------
# Stop hook — stateless session metrics
# -----------------------------------------------------------------------


async def emit_metrics(
    result_data: dict,
    tool_use_id: str | None,
    context: object,
) -> dict:
    """Stop: Log session completion metrics."""
    logger.info(
        "session_complete",
        extra={
            "event_type": "session_end",
            "trace_id": get_trace_id(),
        },
    )
    return {}
