"""Lifecycle manager — orchestrator + content agent.

Manages two persistent ClaudeSDKClient sessions connected via @tool bridge.
Thin wrapper — ALL intelligence in CLAUDE.md files, ALL logging in hooks.

Does 5 things:
  1. Creates persistent ClaudeSDKClient for content agent
  2. Creates persistent ClaudeSDKClient for orchestrator (with @tool bridge)
  3. Sends "heartbeat" to orchestrator every 60s
  4. Tracks token usage for both agents -> traces/manifest.json
  5. Detects COMPACT_NOW -> restarts the appropriate agent session
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import signal
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HEARTBEAT_INTERVAL = 60
MAX_RESPONSE_CHARS = 2000
AGENTS_ROOT = Path(__file__).parent.parent
MANIFEST_PATH = AGENTS_ROOT / "traces" / "manifest.json"
ORC_WORKSPACE = Path(__file__).parent
CONTENT_WORKSPACE = AGENTS_ROOT / "content"

logger = logging.getLogger("lifecycle")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)


class ClientState:
    content_client: Any = None
    content_needs_restart: bool = False


clients = ClientState()


# --- Manifest helpers ---


def read_manifest() -> dict:
    if MANIFEST_PATH.exists():
        return json.loads(MANIFEST_PATH.read_text())
    return {}


def write_manifest(manifest: dict) -> None:
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = MANIFEST_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(manifest, indent=2))
    tmp.rename(MANIFEST_PATH)


def update_manifest_tokens(agent: str, usage: dict | None) -> None:
    if not usage:
        return
    manifest = read_manifest()
    if agent not in manifest:
        manifest[agent] = {
            "session": read_session_num(agent),
            "input_tokens": 0,
            "output_tokens": 0,
            "last_updated": None,
        }
    manifest[agent]["input_tokens"] += usage.get("input_tokens", 0)
    manifest[agent]["output_tokens"] += usage.get("output_tokens", 0)
    manifest[agent]["last_updated"] = datetime.now(timezone.utc).isoformat()
    write_manifest(manifest)


def reset_manifest_tokens(agent: str, session_num: int) -> None:
    manifest = read_manifest()
    manifest[agent] = {
        "session": session_num,
        "input_tokens": 0,
        "output_tokens": 0,
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }
    write_manifest(manifest)


# --- Session state helpers ---


def _state_dir(agent: str) -> Path:
    return (ORC_WORKSPACE if agent == "orc" else CONTENT_WORKSPACE) / "state"


def read_session_num(agent: str) -> int:
    path = _state_dir(agent) / f"{agent}_session.txt"
    return int(path.read_text().strip()) if path.exists() else 1


def write_session_num(agent: str, n: int) -> None:
    path = _state_dir(agent) / f"{agent}_session.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(str(n))


def reset_iteration(agent: str) -> None:
    (_state_dir(agent) / f"{agent}_iteration.txt").write_text("0")


def bump_session(agent: str) -> None:
    new = read_session_num(agent) + 1
    write_session_num(agent, new)
    reset_iteration(agent)
    logger.info("%s: bumped to session #%d", agent, new)


# --- @tool bridge ---


def create_bridge_server():
    from claude_agent_sdk import (
        AssistantMessage,
        ResultMessage,
        TextBlock,
        create_sdk_mcp_server,
        tool,
    )

    @tool(
        "send_to_content_agent",
        "Send prompt to the persistent Content Agent and return its response. "
        "Use for: content pipeline triggers, inbox message relay, any work for the content agent.",
        {"prompt": str},
    )
    async def send_to_content_agent(args: dict[str, Any]) -> dict[str, Any]:
        if clients.content_client is None:
            return {
                "content": [{"type": "text", "text": "Error: Content agent not connected"}],
                "is_error": True,
            }

        prompt = args["prompt"]
        logger.info("Bridge: forwarding to content agent (%d chars)", len(prompt))
        await clients.content_client.query(prompt)

        result_text = ""
        async for msg in clients.content_client.receive_response():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        result_text += block.text
            elif isinstance(msg, ResultMessage):
                update_manifest_tokens("content", msg.usage)
                logger.info(
                    "Bridge: content done — turns=%d, cost=$%.4f",
                    msg.num_turns,
                    msg.total_cost_usd or 0,
                )

        if "COMPACT_NOW" in result_text:
            clients.content_needs_restart = True
            logger.info("Bridge: content agent signaled COMPACT_NOW")

        if len(result_text) > MAX_RESPONSE_CHARS:
            result_text = result_text[:MAX_RESPONSE_CHARS] + "\n[Response truncated]"

        return {"content": [{"type": "text", "text": result_text}]}

    return create_sdk_mcp_server(name="bridge", version="1.0.0", tools=[send_to_content_agent])


# --- Agent option builders ---


def build_orc_options(bridge_server):
    from claude_agent_sdk import ClaudeAgentOptions

    # No system_prompt — SDK reads CLAUDE.md from cwd via setting_sources.
    # bypassPermissions — full tool access, no restrictions.
    return ClaudeAgentOptions(
        model=os.environ.get("AGENT_MODEL", "claude-sonnet-4-6"),
        permission_mode="acceptEdits",
        mcp_servers={"bridge": bridge_server},
        setting_sources=["project"],
        effort="medium",
        max_turns=30,
        max_budget_usd=2.0,
        cwd=str(ORC_WORKSPACE),
        env={
            "ANTHROPIC_API_KEY": os.environ.get("ANTHROPIC_API_KEY", ""),
            "DATABASE_URL": os.environ.get("DATABASE_URL", ""),
        },
    )


def build_content_options():
    from claude_agent_sdk import AgentDefinition, ClaudeAgentOptions, ThinkingConfigEnabled

    # No system_prompt — SDK reads CLAUDE.md from cwd via setting_sources.
    # bypassPermissions — full tool access, no restrictions.
    return ClaudeAgentOptions(
        model=os.environ.get("AGENT_MODEL", "claude-sonnet-4-6"),
        permission_mode="acceptEdits",
        mcp_servers={"web": {"type": "http", "url": "http://localhost:8001/mcp"}},
        agents={
            "web-researcher": AgentDefinition(
                description="Web research specialist for complex multi-step web tasks",
                prompt=(
                    "You are a web research specialist. Load skills from /opt/agents/skills/web/ "
                    "for strategy. Use Bash + curl for quick fetches, web_browse for SPAs. "
                    "Complete the research task and return a comprehensive result."
                ),
                tools=[
                    "Bash", "Read", "Write", "Skill",
                    "mcp__web__web_browse", "mcp__web__web_scrape", "mcp__web__web_search",
                    "mcp__web__extract_youtube", "mcp__web__extract_transcript",
                    "mcp__web__fingerprint", "mcp__web__check_strategy",
                    "mcp__web__manage_session", "mcp__web__validate",
                    "mcp__web__cookie_status", "mcp__web__watch_url",
                ],
            ),
            "content-worker": AgentDefinition(
                description="Lightweight content analysis worker for parallel batch processing",
                prompt=(
                    "You are a content analysis worker. Use Bash + psql for DB access. "
                    "Load skills from /opt/agents/skills/content/ and /opt/agents/skills/data/. "
                    "Return structured analysis result."
                ),
                tools=["Bash", "Read", "Write", "Skill"],
            ),
        },
        setting_sources=["project"],
        thinking=ThinkingConfigEnabled(type="enabled", budget_tokens=10000),
        effort="high",
        max_turns=50,
        max_budget_usd=5.0,
        cwd=str(CONTENT_WORKSPACE),
        env={
            "ANTHROPIC_API_KEY": os.environ.get("ANTHROPIC_API_KEY", ""),
            "DATABASE_URL": os.environ.get("DATABASE_URL", ""),
            "FIRECRAWL_API_KEY": os.environ.get("FIRECRAWL_API_KEY", ""),
        },
    )


# --- Content client lifecycle ---


async def start_content_client():
    from claude_agent_sdk import ClaudeSDKClient

    client = ClaudeSDKClient(options=build_content_options())
    await client.__aenter__()
    return client


async def stop_content_client():
    if clients.content_client:
        try:
            await clients.content_client.__aexit__(None, None, None)
        except Exception as e:
            logger.warning("Error stopping content client: %s", e)
        clients.content_client = None


async def restart_content_client():
    logger.info("Restarting content agent session")
    await stop_content_client()
    bump_session("content")
    reset_manifest_tokens("content", read_session_num("content"))
    clients.content_client = await start_content_client()
    clients.content_needs_restart = False


# --- Main loop ---


async def run_agent() -> None:
    from claude_agent_sdk import ClaudeSDKClient, ResultMessage

    bridge_server = create_bridge_server()

    while True:
        # Start content agent
        reset_manifest_tokens("content", read_session_num("content"))
        clients.content_client = await start_content_client()
        clients.content_needs_restart = False
        logger.info("Content agent started — session #%d", read_session_num("content"))

        # Start orchestrator
        orc_session = read_session_num("orc")
        reset_manifest_tokens("orc", orc_session)
        orc_needs_restart = False

        try:
            async with ClaudeSDKClient(options=build_orc_options(bridge_server)) as orc_client:
                logger.info("Orchestrator started — session #%d", orc_session)

                while not orc_needs_restart:
                    if clients.content_needs_restart:
                        await restart_content_client()

                    await orc_client.query("heartbeat")
                    async for msg in orc_client.receive_response():
                        if isinstance(msg, ResultMessage):
                            update_manifest_tokens("orc", msg.usage)
                            logger.info(
                                "Heartbeat done — turns=%d, cost=$%.4f",
                                msg.num_turns,
                                msg.total_cost_usd or 0,
                            )
                            if msg.result and "COMPACT_NOW" in msg.result:
                                orc_needs_restart = True

                    if not orc_needs_restart:
                        await asyncio.sleep(HEARTBEAT_INTERVAL)

        except Exception as e:
            logger.error("Session error: %s", e, exc_info=True)
            await asyncio.sleep(5)
        finally:
            await stop_content_client()

        if orc_needs_restart:
            bump_session("orc")
        else:
            await asyncio.sleep(5)


async def main() -> None:
    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    def handle_signal() -> None:
        logger.info("Shutdown signal received")
        stop_event.set()

    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, handle_signal)

    agent_task = asyncio.create_task(run_agent())
    await stop_event.wait()
    agent_task.cancel()
    try:
        await agent_task
    except asyncio.CancelledError:
        pass
    await stop_content_client()
    logger.info("Lifecycle manager stopped")


if __name__ == "__main__":
    asyncio.run(main())
