"""Web Agent — ClaudeSDKClient configuration and session management.
Handles autonomous web task reasoning with tool selection, retry logic, strategy.
"""
from __future__ import annotations

import asyncio
import os
from pathlib import Path

from claude_agent_sdk import ClaudeAgentOptions, HookMatcher, ThinkingConfig
from web.hooks import (
    emit_metrics,
    inject_strategy_hints,
    input_validation,
    log_audit,
    rate_limit_check,
    record_strategy_outcome,
)
from web.tools import web_sdk_server

_session_semaphore = asyncio.Semaphore(2)  # H1: max 2 concurrent sessions


def _load_system_prompt() -> str:
    path = Path(__file__).parent / "system_prompt.md"
    return path.read_text(encoding="utf-8")


async def run_agent_task(
    task: str,
    url: str = "",
    output_schema: dict | None = None,
    effort: str = "high",
) -> dict:
    """Run an autonomous web task using ClaudeSDKClient.

    The agent reasons about the task, selects tools, handles retries,
    and returns structured results.
    """
    async with _session_semaphore:
        prompt = f"Task: {task}"
        if url:
            prompt += f"\nTarget URL: {url}"
        if output_schema:
            prompt += f"\nReturn results matching this schema: {output_schema}"

        options = ClaudeAgentOptions(
            model=os.environ.get("AGENT_MODEL", "claude-sonnet-4-6"),
            fallback_model=os.environ.get("AGENT_FALLBACK_MODEL", "claude-opus-4-6"),
            permission_mode="dontAsk",
            setting_sources=["project"],
            system_prompt=_load_system_prompt(),
            mcp_servers={"web": web_sdk_server},
            allowed_tools=[
                "mcp__web__browse",
                "mcp__web__scrape",
                "mcp__web__search",
                "mcp__web__screenshot",
                "mcp__web__interact",
                "mcp__web__fingerprint",
                "mcp__web__check_strategy",
                "mcp__web__manage_session",
                "mcp__web__validate",
            ],
            disallowed_tools=["Bash", "Write", "Edit", "Read"],
            thinking=ThinkingConfig(type="enabled", budget_tokens=8000),
            effort=effort,
            max_turns=20,
            max_budget_usd=2.00,
            cwd="/opt/agents",
            hooks={
                "PreToolUse": [
                    HookMatcher(hooks=[rate_limit_check, input_validation]),
                ],
                "PostToolUse": [
                    HookMatcher(hooks=[record_strategy_outcome, log_audit]),
                ],
                "Stop": [
                    HookMatcher(hooks=[emit_metrics]),
                ],
                "UserPromptSubmit": [
                    HookMatcher(hooks=[inject_strategy_hints]),
                ],
            },
        )

        async def _run() -> dict:
            from claude_agent_sdk import AssistantMessage, ResultMessage, TextBlock, query

            result_text = ""
            async for message in query(prompt=prompt, options=options):
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            result_text += block.text
                elif isinstance(message, ResultMessage):
                    break

            return {
                "status": "complete",
                "result": result_text,
                "url": url,
            }

        try:
            return await asyncio.wait_for(_run(), timeout=120)
        except asyncio.TimeoutError:
            return {"status": "timeout", "error": "Agent session timed out"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
