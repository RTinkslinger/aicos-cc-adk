"""Content Agent hook callbacks — audit logging and pipeline completion verification.

Hook types used:
  PostToolUse:  log_analysis_audit
  Stop:         verify_pipeline_completion, emit_metrics

Registration (in agent.py):
    from claude_agent_sdk import ClaudeAgentOptions, HookMatcher
    options = ClaudeAgentOptions(
        hooks={
            "PostToolUse": [HookMatcher(hooks=[log_analysis_audit])],
            "Stop":         [HookMatcher(hooks=[verify_pipeline_completion, emit_metrics])],
        }
    )
"""
from __future__ import annotations

from shared.logging import get_trace_id, setup_logger

logger = setup_logger("content-agent")

# Track which tools were called during an analysis session.
# Reset by verify_pipeline_completion at Stop.
_tools_called: list[str] = []

# Tools we expect to see in a complete pipeline run.
_EXPECTED_PIPELINE_TOOLS: frozenset[str] = frozenset(
    {"score_action", "publish_digest"}
)


# -----------------------------------------------------------------------
# PostToolUse hook
# -----------------------------------------------------------------------


async def log_analysis_audit(
    result_data: dict,
    tool_use_id: str | None,
    context: object,
) -> dict:
    """PostToolUse: Structured audit log for every tool call in an analysis session.

    Appends tool name to the session tracking list so Stop hooks can
    verify all expected pipeline steps were completed.
    """
    tool_name = result_data.get("tool_name", "unknown")
    _tools_called.append(tool_name)

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
# Stop hooks
# -----------------------------------------------------------------------


async def verify_pipeline_completion(
    result_data: dict,
    tool_use_id: str | None,
    context: object,
) -> dict:
    """Stop: Verify that all expected pipeline steps were completed.

    Checks that score_action and publish_digest were both called
    during the session. Logs a warning for any missing tools so
    incomplete runs are visible in logs without crashing.
    """
    global _tools_called  # noqa: PLW0603

    called_set = set(_tools_called)
    missing = _EXPECTED_PIPELINE_TOOLS - called_set

    if missing:
        logger.warning(
            "pipeline_incomplete",
            extra={
                "event_type": "pipeline_warning",
                "missing_tools": sorted(missing),
                "called_tools": sorted(called_set),
                "trace_id": get_trace_id(),
            },
        )
    else:
        logger.info(
            "pipeline_complete",
            extra={
                "event_type": "pipeline_ok",
                "called_tools": sorted(called_set),
                "trace_id": get_trace_id(),
            },
        )

    # Reset for the next analysis session
    _tools_called = []
    return {}


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
