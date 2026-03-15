"""Sync Agent — ClaudeSDKClient for autonomous sync reasoning.
Used for complex operations: conflict resolution, intelligent action generation.

NOT used for regular tool handling — the FastMCP server in server.py handles
those directly. This module is invoked only when changes require reasoning:
  - Conviction transitions (e.g. Medium → High)
  - Status transitions with downstream implications
  - Conflict resolution between Notion and Postgres state
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Any

_session_semaphore = asyncio.Semaphore(2)  # H1: max 2 concurrent sessions


def _load_system_prompt() -> str:
    path = Path(__file__).parent / "system_prompt.md"
    return path.read_text(encoding="utf-8")


async def reason_about_changes(
    changes: list[dict[str, Any]],
    context: str = "",
) -> dict[str, Any]:
    """Invoke Agent SDK to reason about sync changes and generate actions.

    Used when changes are complex (conviction moves, status transitions)
    and simple rules aren't sufficient.

    Args:
        changes: List of change event dicts from change_events table
        context: Optional additional context string

    Returns:
        Dict with keys: status ('complete' | 'timeout' | 'error'), reasoning (str)
    """
    async with _session_semaphore:
        prompt = (
            "Analyze these sync changes and determine appropriate actions:\n\n"
            f"{changes}\n\n"
            f"Context: {context}"
        )

        try:
            from claude_agent_sdk import (
                AssistantMessage,
                ClaudeAgentOptions,
                HookMatcher,
                ResultMessage,
                TextBlock,
                ThinkingConfig,
                query,
            )
        except ImportError as exc:
            return {
                "status": "error",
                "reasoning": f"claude_agent_sdk not available: {exc}",
            }

        options = ClaudeAgentOptions(
            model="claude-sonnet-4-6",
            permission_mode="dontAsk",
            system_prompt=_load_system_prompt(),
            disallowed_tools=["Bash", "Write", "Edit", "Read"],
            thinking=ThinkingConfig(type="enabled", budget_tokens=5000),
            effort="medium",
            max_turns=10,
            max_budget_usd=0.50,
            env={"ANTHROPIC_API_KEY": os.environ.get("ANTHROPIC_API_KEY", "")},
            cwd="/opt/agents",
        )

        try:
            result_text = await asyncio.wait_for(
                _collect_query(prompt, options),
                timeout=120,
            )
            return {"status": "complete", "reasoning": result_text}
        except asyncio.TimeoutError:
            return {
                "status": "timeout",
                "reasoning": "Agent SDK session timed out after 120s",
            }
        except Exception as exc:
            return {"status": "error", "reasoning": str(exc)}


async def _collect_query(prompt: str, options: Any) -> str:
    """Async generator wrapper for query(): collect all text blocks into a string."""
    from claude_agent_sdk import AssistantMessage, ResultMessage, TextBlock, query

    result_text = ""
    async for message in query(prompt=prompt, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    result_text += block.text
        elif isinstance(message, ResultMessage):
            break
    return result_text
