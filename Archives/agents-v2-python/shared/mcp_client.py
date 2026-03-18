"""HTTP MCP client for inter-agent communication.

Includes circuit breaker (C3: open after 5 failures, reset 60s),
per-tool timeouts, and trace ID propagation.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx
import pybreaker

from .logging import get_trace_id

logger = logging.getLogger("mcp-client")

# Circuit breakers per target agent
_breakers: dict[str, pybreaker.CircuitBreaker] = {}


def _get_breaker(agent_name: str) -> pybreaker.CircuitBreaker:
    if agent_name not in _breakers:
        _breakers[agent_name] = pybreaker.CircuitBreaker(
            fail_max=5,
            reset_timeout=60,
            name=f"cb_{agent_name}",
        )
    return _breakers[agent_name]


class AgentCallError(Exception):
    """Raised when an inter-agent MCP call fails."""


async def call_agent_tool(
    agent_url: str,
    tool_name: str,
    arguments: dict[str, Any],
    timeout_s: float = 30.0,
    agent_name: str = "unknown",
) -> dict[str, Any]:
    """Call an MCP tool on another agent via HTTP.

    Args:
        agent_url: Full MCP endpoint URL (e.g., "http://localhost:8000/mcp")
        tool_name: Tool name (e.g., "cos_get_thesis_threads")
        arguments: Tool arguments dict
        timeout_s: Per-tool timeout in seconds (C3)
        agent_name: Target agent name for circuit breaker key

    Returns:
        Tool result dict

    Raises:
        pybreaker.CircuitBreakerError: If circuit is open (agent considered down)
        AgentCallError: If the MCP call returns an error
        httpx.TimeoutException: If call exceeds timeout
    """
    breaker = _get_breaker(agent_name)

    # Propagate trace ID (C4)
    trace_id = get_trace_id()
    if trace_id and "trace_id" not in arguments:
        arguments = {**arguments, "trace_id": trace_id}

    @breaker
    async def _call() -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=timeout_s) as client:
            response = await client.post(
                agent_url,
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {"name": tool_name, "arguments": arguments},
                    "id": 1,
                },
            )
            response.raise_for_status()
            result = response.json()
            if "error" in result:
                raise AgentCallError(f"MCP error from {agent_name}/{tool_name}: {result['error']}")
            return result.get("result", {})

    try:
        return await _call()
    except pybreaker.CircuitBreakerError:
        logger.error(
            "circuit_open",
            extra={"agent": agent_name, "tool": tool_name, "trace_id": trace_id},
        )
        raise
    except httpx.TimeoutException:
        logger.error(
            "timeout",
            extra={"agent": agent_name, "tool": tool_name, "timeout_s": timeout_s, "trace_id": trace_id},
        )
        raise
    except AgentCallError:
        raise
    except Exception as e:
        logger.error(
            "call_failed",
            extra={"agent": agent_name, "tool": tool_name, "error": str(e), "trace_id": trace_id},
        )
        raise AgentCallError(f"Failed to call {agent_name}/{tool_name}: {e}") from e


async def check_agent_health(agent_url: str, timeout_s: float = 5.0) -> bool:
    """Fast health check for another agent. Returns True if healthy."""
    try:
        async with httpx.AsyncClient(timeout=timeout_s) as client:
            response = await client.post(
                agent_url,
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {"name": "health_check", "arguments": {}},
                    "id": 1,
                },
            )
            return response.status_code == 200
    except Exception:
        return False
