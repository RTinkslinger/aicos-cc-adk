"""Content Agent — Content pipeline orchestrator.

Calls Web Agent for extraction, uses Agent SDK for analysis,
calls Sync Agent for all DB writes. Publishes to digest.wiki directly.

Port 8002. 5-minute pipeline loop via asyncio.create_task at startup.
"""
from __future__ import annotations

import asyncio
import datetime
import os

from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastmcp import FastMCP

from content.tools import (
    analyze_content,
    health_check,
    pipeline_state,
    pipeline_status,
    trigger_pipeline,
)
from shared.logging import set_trace_id, setup_logger

load_dotenv()

logger = setup_logger("content-agent", "/opt/agents/logs/content.log")

# -----------------------------------------------------------------------
# FastMCP server
# -----------------------------------------------------------------------

@asynccontextmanager
async def _lifespan(app):
    """Start pipeline loop on server startup."""
    task = asyncio.create_task(_pipeline_loop())
    logger.info("content_agent_started", extra={"event_type": "startup", "port": 8002})
    yield
    task.cancel()
    logger.info("content_agent_stopped")


mcp = FastMCP(
    "content-agent",
    instructions=(
        "Content pipeline orchestrator and analyst. "
        "Processes content from YouTube (v1) and future sources. "
        "Use analyze_content to run analysis on extracted video data. "
        "Use trigger_pipeline for a manual pipeline run. "
        "Use pipeline_status to check pipeline health. "
        "Content Agent calls Web Agent for extraction and Sync Agent for all DB writes."
    ),
    lifespan=_lifespan,
)

# GET /health — ops liveness check (C2 audit fix)
from starlette.requests import Request
from starlette.responses import JSONResponse


@mcp.custom_route("/health", methods=["GET"])
async def health_get(request: Request) -> JSONResponse:
    """Simple GET health check for ops tooling."""
    return JSONResponse({"status": "ok", "agent": "content-agent", "port": 8002})


# Register the 4 FastMCP tools
mcp.tool()(analyze_content)
mcp.tool()(trigger_pipeline)
mcp.tool()(pipeline_status)
mcp.tool()(health_check)


# -----------------------------------------------------------------------
# Pipeline loop
# -----------------------------------------------------------------------

_PIPELINE_INTERVAL_SECONDS = int(os.getenv("PIPELINE_INTERVAL_SECONDS", "300"))  # 5 min default
_WEB_AGENT_URL = os.getenv("WEB_AGENT_URL", "http://localhost:8001/mcp")
_PLAYLIST_URL = os.getenv("YOUTUBE_PLAYLIST_URL", "")


async def run_content_pipeline() -> None:
    """Execute one full pipeline cycle.

    1. Call Web Agent: extract_youtube for recent videos
    2. Filter: skip no-transcript, skip non-relevant
    3. For each video: invoke ClaudeSDKClient analysis session
    """
    from shared.mcp_client import AgentCallError, call_agent_tool

    pipeline_state["status"] = "running"
    pipeline_state["last_run"] = datetime.datetime.utcnow().isoformat() + "Z"

    logger.info(
        "pipeline_start",
        extra={"event_type": "pipeline_start", "trace_id": set_trace_id()},
    )

    videos_processed = 0
    errors: list[str] = []

    # Step 1 — Extract from Web Agent
    try:
        extract_args: dict = {"since_days": 3}
        if _PLAYLIST_URL:
            extract_args["playlist_url"] = _PLAYLIST_URL

        extraction_result = await call_agent_tool(
            agent_url=_WEB_AGENT_URL,
            tool_name="extract_youtube",
            arguments=extract_args,
            timeout_s=90,
            agent_name="web",
        )
    except AgentCallError as exc:
        msg = f"Web Agent extraction failed: {exc}"
        logger.error("extraction_failed", extra={"event_type": "error", "error": msg})
        errors.append(msg)
        pipeline_state.update({"status": "error", "errors": errors})
        return
    except Exception as exc:  # noqa: BLE001
        msg = f"Unexpected extraction error: {exc}"
        logger.error("extraction_error", extra={"event_type": "error", "error": msg})
        errors.append(msg)
        pipeline_state.update({"status": "error", "errors": errors})
        return

    # Step 2 — Filter
    raw_videos = extraction_result.get("videos", [])
    relevant_videos = [
        v for v in raw_videos
        if v.get("transcript") and v.get("transcript") != ""
    ]

    logger.info(
        "extraction_complete",
        extra={
            "event_type": "extraction_ok",
            "total": len(raw_videos),
            "relevant": len(relevant_videos),
        },
    )

    # Step 3 — Analyse each video
    for video in relevant_videos:
        try:
            await analyze_content(extraction_data=video, content_type="youtube")
            videos_processed += 1
        except Exception as exc:  # noqa: BLE001
            err = f"Analysis failed for '{video.get('title', 'unknown')}': {exc}"
            logger.error("analysis_error", extra={"event_type": "error", "error": err})
            errors.append(err)

    pipeline_state.update(
        {
            "status": "idle",
            "videos_processed": pipeline_state.get("videos_processed", 0) + videos_processed,
            "errors": errors[-20:],  # Keep last 20 errors only
        }
    )

    logger.info(
        "pipeline_complete",
        extra={
            "event_type": "pipeline_ok",
            "videos_processed": videos_processed,
            "errors": len(errors),
        },
    )


async def _pipeline_loop() -> None:
    """5-minute pipeline scheduling loop. Runs indefinitely."""
    logger.info("pipeline_loop_start", extra={"event_type": "loop_start", "interval_s": _PIPELINE_INTERVAL_SECONDS})
    while True:
        try:
            await run_content_pipeline()
        except Exception as exc:  # noqa: BLE001
            logger.error(
                "pipeline_loop_error",
                extra={"event_type": "loop_error", "error": str(exc)},
            )
        await asyncio.sleep(_PIPELINE_INTERVAL_SECONDS)


# -----------------------------------------------------------------------
# Startup — kick off the pipeline loop
# -----------------------------------------------------------------------


### NOTE: Startup handled via lifespan context manager (FastMCP 3.x pattern)


# -----------------------------------------------------------------------
# Entrypoint
# -----------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8002)
