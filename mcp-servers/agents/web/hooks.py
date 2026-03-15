"""Web Agent hook callbacks — rate limiting, input validation, strategy recording, audit logging, metrics.

Hook types used:
  PreToolUse:       rate_limit_check, input_validation
  PostToolUse:      record_strategy_outcome, log_audit
  Stop:             emit_metrics
  UserPromptSubmit: inject_strategy_hints

Registration (in agent.py):
    from claude_agent_sdk import ClaudeAgentOptions, HookMatcher
    options = ClaudeAgentOptions(
        hooks={
            "PreToolUse":        [HookMatcher(hooks=[rate_limit_check, input_validation])],
            "PostToolUse":       [HookMatcher(hooks=[record_strategy_outcome, log_audit])],
            "Stop":              [HookMatcher(hooks=[emit_metrics])],
            "UserPromptSubmit":  [HookMatcher(hooks=[inject_strategy_hints])],
        }
    )
"""

from __future__ import annotations

import asyncio
import time
from urllib.parse import urlparse

from shared.logging import get_trace_id, setup_logger

logger = setup_logger("web-agent")

# Track request timestamps per domain for rate limiting
# domain -> list of UNIX timestamps (pruned to the last 60 seconds on each check)
_domain_counts: dict[str, list[float]] = {}
_domain_lock = asyncio.Lock()  # M3: protect concurrent access

# Max requests per domain per 60-second window
_RATE_LIMIT = 10


# -----------------------------------------------------------------------
# PreToolUse hooks
# -----------------------------------------------------------------------


async def rate_limit_check(input_data: dict, tool_use_id: str | None, context: object) -> dict:
    """PreToolUse: Rate limiting per domain (max 10 req/min/domain).

    Extracts the URL from tool_input, derives the domain, and enforces a
    sliding-window rate limit. Returns a deny decision if the limit is exceeded.
    """
    tool_input = input_data.get("tool_input", {})
    url = tool_input.get("url", "")

    if not url:
        return {}

    domain = urlparse(url).netloc
    if not domain:
        return {}

    async with _domain_lock:  # M3: thread-safe access
        now = time.time()
        _domain_counts.setdefault(domain, [])
        _domain_counts[domain] = [t for t in _domain_counts[domain] if now - t < 60]

        if len(_domain_counts[domain]) >= _RATE_LIMIT:
            logger.warning(
                "rate_limit_exceeded",
                extra={
                    "event_type": "rate_limit",
                    "domain": domain,
                    "count": len(_domain_counts[domain]),
                    "trace_id": get_trace_id(),
                },
            )
            return {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": (
                        f"Rate limit exceeded for {domain} ({_RATE_LIMIT} req/min). "
                        "Wait before retrying."
                    ),
                }
            }

        _domain_counts[domain].append(now)
    return {}


async def input_validation(input_data: dict, tool_use_id: str | None, context: object) -> dict:
    """PreToolUse: Validate URL format and size limits.

    Checks that URLs are well-formed and that content args don't exceed
    reasonable size limits (prevents OOM on large payloads).
    """
    tool_input = input_data.get("tool_input", {})
    url = tool_input.get("url", "")

    if url:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https", ""):
            return {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": f"Invalid URL scheme '{parsed.scheme}'. Only http/https allowed.",
                }
            }

    # Guard against oversized content payloads (e.g. validate tool content arg)
    content = tool_input.get("content", "")
    if isinstance(content, str) and len(content) > 5_000_000:  # 5MB guard
        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": f"Content payload too large ({len(content):,} chars). Maximum is 5MB.",
            }
        }

    return {}


# -----------------------------------------------------------------------
# PostToolUse hooks
# -----------------------------------------------------------------------


async def record_strategy_outcome(result_data: dict, tool_use_id: str | None, context: object) -> dict:
    """PostToolUse: Auto-record strategy outcome to SQLite UCB cache.

    For browse/scrape/search tools, extracts origin, strategy name, success
    flag, and latency, then persists to the strategy SQLite DB so UCB bandit
    can learn over time.
    """
    tool_name = result_data.get("tool_name", "")
    if tool_name not in ("browse", "scrape", "search"):
        return {}

    tool_input = result_data.get("tool_input", {})
    tool_output = result_data.get("tool_output", {})
    url = tool_input.get("url", "")

    if not url:
        return {}

    origin = urlparse(url).netloc
    if not origin:
        return {}

    # Determine success from tool output
    if isinstance(tool_output, dict):
        success = not bool(tool_output.get("error")) and tool_output.get("status") != "error"
    else:
        success = True

    # Map tool name to strategy name
    readiness = tool_input.get("readiness_mode", tool_input.get("readiness", "auto"))
    if tool_name == "scrape":
        strategy_name = "firecrawl" if tool_input.get("use_firecrawl") else "jina_reader"
    elif tool_name == "browse":
        strategy_name = f"browser_{readiness}" if readiness != "auto" else "browser_mutation_observer"
    else:
        strategy_name = f"{tool_name}_default"

    try:
        from web.lib.strategy import record_outcome

        record_outcome(origin=origin, strategy_name=strategy_name, success=success, latency_ms=0)
        logger.info(
            "strategy_recorded",
            extra={
                "event_type": "strategy_outcome",
                "tool_name": tool_name,
                "origin": origin,
                "strategy": strategy_name,
                "success": success,
                "trace_id": get_trace_id(),
            },
        )
    except Exception as exc:
        logger.warning("strategy_record_failed", extra={"error": str(exc), "trace_id": get_trace_id()})

    return {}


async def log_audit(result_data: dict, tool_use_id: str | None, context: object) -> dict:
    """PostToolUse: Structured audit log for all tool calls.

    Logs tool name, success/error status, and trace ID for every tool
    invocation during an agent session.
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
# Stop hook
# -----------------------------------------------------------------------


async def emit_metrics(result_data: dict, tool_use_id: str | None, context: object) -> dict:
    """Stop: Log final session metrics when the agent finishes."""
    logger.info(
        "session_complete",
        extra={
            "event_type": "session_end",
            "trace_id": get_trace_id(),
        },
    )
    return {}


# -----------------------------------------------------------------------
# UserPromptSubmit hook
# -----------------------------------------------------------------------


async def inject_strategy_hints(input_data: dict, tool_use_id: str | None, context: object) -> dict:
    """UserPromptSubmit: Inject cookie health warnings into the agent's context.

    Checks YouTube cookie freshness before the agent starts reasoning.
    If cookies are stale or missing, adds a visible warning so the agent
    can adjust its strategy (e.g. fall back to yt-dlp subtitle extraction).
    """
    hints: list[str] = []

    try:
        from web.lib.sessions import cookie_status

        status = cookie_status()
        cookies = status.get("cookies", [])
        stale = [c for c in cookies if c.get("warning")]
        if stale:
            domains = ", ".join(c["domain"] for c in stale)
            hints.append(f"[WARNING] Stale cookies detected for: {domains}. Re-run cookie-sync.sh.")
        if status.get("error"):
            hints.append(f"[WARNING] Cookie directory issue: {status['error']}")
    except Exception as exc:
        logger.debug("inject_strategy_hints: cookie check failed: %s", exc)

    if hints:
        return {
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": "\n".join(hints),
            }
        }

    return {}
