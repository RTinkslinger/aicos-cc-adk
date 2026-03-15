"""Content Agent tools — dual layer:
  4 FastMCP tools (external callers via server.py)
  3 SDK @tool functions (agent reasoning via ClaudeSDKClient)

FastMCP tools: analyze_content, trigger_pipeline, pipeline_status, health_check.
SDK @tool functions: score_action, publish_digest, load_context_sections.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from claude_agent_sdk import create_sdk_mcp_server, tool

# -----------------------------------------------------------------------
# Module-level pipeline state (shared with server.py and FastMCP tools)
# -----------------------------------------------------------------------

pipeline_state: dict[str, Any] = {
    "last_run": None,
    "videos_processed": 0,
    "errors": [],
    "status": "idle",
}


# -----------------------------------------------------------------------
# Category 1: FastMCP tool functions (4 tools — NOT decorated here)
# server.py registers these with @mcp.tool()
# -----------------------------------------------------------------------


async def analyze_content(extraction_data: dict, content_type: str = "youtube") -> dict:
    """Run full content analysis using Agent SDK autonomous reasoning.

    Invokes a ClaudeSDKClient session that looks up thesis threads,
    checks preferences, scores actions, publishes the digest, and
    submits all data to Sync Agent.

    Args:
        extraction_data: Video/content data from Web Agent (title, channel,
                         duration, transcript, url, etc.)
        content_type: Source type — "youtube" (default), "rss", "url", "meeting"
    """
    from content.agent import run_analysis

    return await run_analysis(extraction_data)


async def trigger_pipeline() -> dict:
    """Trigger a manual content pipeline run.

    Calls Web Agent for extraction, then analyzes each video
    with Agent SDK reasoning. Same flow as the automatic 5-min cron.
    """
    # Deferred import to avoid circular at module load time
    from content.server import run_content_pipeline

    await run_content_pipeline()
    return {"status": "triggered"}


async def pipeline_status() -> dict:
    """Return current pipeline state.

    Includes last run timestamp, total videos processed, and
    any recent errors.
    """
    return {
        "status": pipeline_state.get("status", "idle"),
        "last_run": pipeline_state.get("last_run"),
        "videos_processed": pipeline_state.get("videos_processed", 0),
        "errors": pipeline_state.get("errors", []),
    }


async def health_check() -> dict:
    """Health check for the Content Agent."""
    return {"status": "ok", "agent": "content-agent"}


# -----------------------------------------------------------------------
# Category 2: Internal SDK @tool functions (for ClaudeSDKClient reasoning)
# Registered via create_sdk_mcp_server() — used only during analysis sessions.
# -----------------------------------------------------------------------


@tool(
    "score_action",
    "Score a proposed action using the 5-factor model (bucket_impact, conviction_change, time_sensitivity, action_novelty, effort_vs_impact). Returns a 0-10 score and surface/low_confidence/context_only classification.",
    {
        "bucket_impact": float,
        "conviction_change": float,
        "time_sensitivity": float,
        "action_novelty": float,
        "effort_vs_impact": float,
    },
)
async def score_action_tool(args: dict[str, Any]) -> dict[str, Any]:
    """Score a proposed action using the 5-factor weighted scoring model."""
    from content.lib.scoring import ActionInput, classify_action, score_action

    ai = ActionInput(
        bucket_impact=args["bucket_impact"],
        conviction_change=args["conviction_change"],
        time_sensitivity=args["time_sensitivity"],
        action_novelty=args["action_novelty"],
        effort_vs_impact=args["effort_vs_impact"],
    )
    score = score_action(ai)
    classification = classify_action(score)
    return {
        "content": [
            {
                "type": "text",
                "text": f"Score: {score:.2f}, Classification: {classification}",
            }
        ]
    }


@tool(
    "publish_digest",
    "Publish the completed DigestData JSON to digest.wiki via git commit + push. Triggers Vercel deploy automatically. Call this AFTER the agent has finished reasoning and produced the final DigestData.",
    {"digest_data": dict},
)
async def publish_digest_tool(args: dict[str, Any]) -> dict[str, Any]:
    """Publish digest JSON to the aicos-digests repo and trigger Vercel deploy."""
    from content.lib.publishing import publish_digest

    result = publish_digest(args["digest_data"])
    url = result.get("url", "unknown")
    pushed = result.get("pushed", False)
    deployed = result.get("deployed", False)
    return {
        "content": [
            {
                "type": "text",
                "text": (
                    f"Published: {url}. "
                    f"Pushed: {pushed}. "
                    f"Deployed: {deployed}."
                ),
            }
        ]
    }


@tool(
    "load_context_sections",
    "Load key sections from CONTEXT.md — IDS methodology, priority buckets, active thesis context, portfolio companies, and key people. Call this FIRST before analyzing any content.",
    {},
)
async def load_context_tool(args: dict[str, Any]) -> dict[str, Any]:  # noqa: ARG001
    """Load CONTEXT.md domain knowledge sections for analysis grounding."""
    context_path = os.getenv("CONTEXT_MD_PATH", "/opt/agents/CONTEXT.md")
    path = Path(context_path)
    if not path.exists():
        return {
            "content": [
                {
                    "type": "text",
                    "text": (
                        "CONTEXT.md not available at expected path. "
                        "Proceed using embedded domain knowledge from system prompt."
                    ),
                }
            ]
        }
    text = path.read_text(encoding="utf-8")
    # Return first 8000 chars — covers IDS methodology, buckets, thesis threads, people
    return {"content": [{"type": "text", "text": text[:8000]}]}


# -----------------------------------------------------------------------
# Bundle SDK tools into an in-process MCP server for ClaudeSDKClient
# -----------------------------------------------------------------------

content_sdk_server = create_sdk_mcp_server(
    name="tools",
    version="1.0.0",
    tools=[score_action_tool, publish_digest_tool, load_context_tool],
)
