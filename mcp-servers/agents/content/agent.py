"""Content Agent — ClaudeSDKClient for autonomous content analysis.

The agent reasons about content, looks up thesis threads, checks preferences,
scores actions, publishes digests, and submits all data to Sync Agent.

One session per video analysis. Max 2 concurrent sessions via semaphore.
"""
from __future__ import annotations

import asyncio
import os
from pathlib import Path

from claude_agent_sdk import ClaudeAgentOptions, HookMatcher, ThinkingConfig

from content.hooks import emit_metrics, log_analysis_audit
from content.tools import content_sdk_server
from shared.logging import set_trace_id, setup_logger

logger = setup_logger("content-agent")

_SYNC_AGENT_URL = os.getenv("SYNC_AGENT_URL", "http://localhost:8000/mcp")

# H1: max 2 concurrent analysis sessions
_session_semaphore = asyncio.Semaphore(2)


def _load_system_prompt() -> str:
    path = Path(__file__).parent / "system_prompt.md"
    return path.read_text(encoding="utf-8")


def _build_analysis_prompt(video_data: dict) -> str:
    """Construct the analysis prompt from extracted video data."""
    title = video_data.get("title", "Untitled")
    channel = video_data.get("channel", "Unknown Channel")
    duration = video_data.get("duration", "Unknown")
    url = video_data.get("url", "")
    upload_date = video_data.get("upload_date", "Unknown")
    transcript = video_data.get("transcript", "")
    description = video_data.get("description", "")

    prompt_parts = [
        f"Analyze the following YouTube video for Aakash Kumar's AI CoS system.",
        f"",
        f"**Title:** {title}",
        f"**Channel:** {channel}",
        f"**Duration:** {duration}",
        f"**Upload Date:** {upload_date}",
        f"**URL:** {url}",
    ]

    if description:
        prompt_parts += [f"", f"**Description:**", description[:500]]

    if transcript:
        prompt_parts += [f"", f"**Transcript:**", transcript]
    else:
        prompt_parts += [f"", f"*(No transcript available — analyse from title, channel, and description.)*"]

    prompt_parts += [
        f"",
        f"Follow your mandatory tool sequence:",
        f"1. Call load_context_sections to get domain context",
        f"2. Call cos_get_thesis_threads to load active thesis threads",
        f"3. Call cos_get_preferences to calibrate scoring",
        f"4. Analyse the content and produce DigestData",
        f"5. Call score_action for each proposed action",
        f"6. Call publish_digest to publish to digest.wiki",
        f"7. Call write_digest (via Sync Agent) for Notion entry",
        f"8. Call write_actions (via Sync Agent) for each proposed action",
        f"9. Call update_thesis (via Sync Agent) for each thesis connection",
        f"10. Call create_thesis_thread (via Sync Agent) only if a genuinely new thesis is identified",
        f"11. Call log_preference (via Sync Agent) for each proposed action",
    ]

    return "\n".join(prompt_parts)


async def run_analysis(video_data: dict) -> dict:
    """Run an autonomous content analysis session using ClaudeSDKClient.

    The agent autonomously:
    - Loads thesis threads and preference history via Sync Agent
    - Analyses content against thesis context
    - Scores every proposed action
    - Publishes digest to digest.wiki
    - Submits digest, actions, and thesis evidence to Sync Agent

    Args:
        video_data: Extracted video data from Web Agent (title, channel,
                    duration, transcript, url, upload_date, description)

    Returns:
        dict with status, result text, and video title.
    """
    async with _session_semaphore:
        trace_id = set_trace_id()
        title = video_data.get("title", "unknown")

        logger.info(
            "analysis_start",
            extra={"event_type": "analysis_start", "title": title, "trace_id": trace_id},
        )

        prompt = _build_analysis_prompt(video_data)

        options = ClaudeAgentOptions(
            model=os.environ.get("AGENT_MODEL", "claude-sonnet-4-6"),
            permission_mode="dontAsk",
            system_prompt=_load_system_prompt(),
            mcp_servers={
                # In-process tools: score_action, publish_digest, load_context_sections
                "tools": content_sdk_server,
                # External: Sync Agent — all DB reads + writes
                "sync": {
                    "type": "http",
                    "url": _SYNC_AGENT_URL,
                },
            },
            allowed_tools=[
                # In-process tools
                "mcp__tools__score_action",
                "mcp__tools__publish_digest",
                "mcp__tools__load_context_sections",
                # Sync Agent — state reads
                "mcp__sync__cos_get_thesis_threads",
                "mcp__sync__cos_get_preferences",
                # Sync Agent — write-receiver tools
                "mcp__sync__write_digest",
                "mcp__sync__write_actions",
                "mcp__sync__update_thesis",
                "mcp__sync__create_thesis_thread",
                "mcp__sync__log_preference",
            ],
            disallowed_tools=["Bash", "Write", "Edit", "Read"],
            thinking=ThinkingConfig(type="enabled", budget_tokens=10000),
            effort="high",
            max_turns=15,
            max_budget_usd=1.50,
            env={"ANTHROPIC_API_KEY": os.environ.get("ANTHROPIC_API_KEY", "")},
            cwd="/opt/agents",
            hooks={
                "PostToolUse": [
                    HookMatcher(hooks=[log_analysis_audit]),
                ],
                "Stop": [
                    HookMatcher(hooks=[emit_metrics]),
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
                "title": title,
            }

        try:
            result = await asyncio.wait_for(_run(), timeout=120)
            logger.info(
                "analysis_complete",
                extra={"event_type": "analysis_ok", "title": title, "trace_id": trace_id},
            )
            return result
        except asyncio.TimeoutError:
            logger.error(
                "analysis_timeout",
                extra={"event_type": "timeout", "title": title, "trace_id": trace_id},
            )
            return {"status": "timeout", "error": "Analysis session timed out after 120s", "title": title}
        except Exception as exc:  # noqa: BLE001
            logger.error(
                "analysis_error",
                extra={"event_type": "error", "title": title, "error": str(exc), "trace_id": trace_id},
            )
            return {"status": "error", "error": str(exc), "title": title}
