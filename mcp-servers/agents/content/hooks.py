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

# Track which tools were called per session, keyed by trace_id.
# Each concurrent session gets its own list. Cleaned up at Stop.
_tools_by_session: dict[str, list[str]] = {}

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
    trace_id = get_trace_id() or "_default"
    _tools_by_session.setdefault(trace_id, []).append(tool_name)

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
    trace_id = get_trace_id() or "_default"
    session_tools = _tools_by_session.pop(trace_id, [])
    called_set = set(session_tools)
    missing = _EXPECTED_PIPELINE_TOOLS - called_set

    if missing:
        logger.warning(
            "pipeline_incomplete",
            extra={
                "event_type": "pipeline_warning",
                "missing_tools": sorted(missing),
                "called_tools": sorted(called_set),
                "trace_id": trace_id,
            },
        )
    else:
        logger.info(
            "pipeline_complete",
            extra={
                "event_type": "pipeline_ok",
                "called_tools": sorted(called_set),
                "trace_id": trace_id,
            },
        )

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
