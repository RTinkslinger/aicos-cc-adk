"""Lifecycle manager — orchestrator + content agent + datum agent.

Manages three persistent ClaudeSDKClient sessions connected via @tool bridge.
Thin wrapper — ALL intelligence in CLAUDE.md files, ALL logging in hooks.

Does 6 things:
  1. Creates persistent ClaudeSDKClient for content agent + datum agent
  2. Creates persistent ClaudeSDKClient for orchestrator (with @tool bridge)
  3. Sends "heartbeat" to orchestrator every 60s
  4. Tracks token usage for all agents -> traces/manifest.json
  5. Detects COMPACT_NOW -> restarts the appropriate agent session
  6. Writes real-time live logs (PostToolUse hooks + AssistantMessage extraction)
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
DATUM_WORKSPACE = AGENTS_ROOT / "datum"
ORC_LIVE_LOG = ORC_WORKSPACE / "live.log"
CONTENT_LIVE_LOG = CONTENT_WORKSPACE / "live.log"
DATUM_LIVE_LOG = DATUM_WORKSPACE / "live.log"

logger = logging.getLogger("lifecycle")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)


class ClientState:
    content_client: Any = None
    content_needs_restart: bool = False
    content_busy: bool = False

    datum_client: Any = None
    datum_needs_restart: bool = False
    datum_busy: bool = False


clients = ClientState()


# --- Live log helpers ---


def _live_log(path: Path, line: str) -> None:
    """Append a timestamped line to a live log file."""
    ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
    try:
        with open(path, "a") as f:
            f.write(f"{ts} {line}\n")
            f.flush()
    except Exception as e:
        logger.warning("_live_log write failed (%s): %s", path, e)


def _log_assistant_message(path: Path, msg: Any) -> None:
    """Extract ThinkingBlock, TextBlock, ToolUseBlock from AssistantMessage."""
    from claude_agent_sdk import TextBlock

    try:
        from claude_agent_sdk import ThinkingBlock
    except ImportError:
        ThinkingBlock = None

    try:
        from claude_agent_sdk import ToolUseBlock
    except ImportError:
        ToolUseBlock = None

    for block in msg.content:
        if ThinkingBlock and isinstance(block, ThinkingBlock):
            thinking = getattr(block, "thinking", "")[:200]
            _live_log(path, f"(think) {thinking}")
        elif isinstance(block, TextBlock):
            text = block.text[:200]
            if text.strip():
                _live_log(path, f"TEXT: {text}")
        elif ToolUseBlock and isinstance(block, ToolUseBlock):
            name = getattr(block, "name", "?")
            inp = str(getattr(block, "input", ""))[:130]
            _live_log(path, f"TOOL_CALL {name}: {inp}")


def _log_result_message(path: Path, msg: Any) -> None:
    """Log ResultMessage summary."""
    turns = getattr(msg, "num_turns", 0)
    cost = getattr(msg, "total_cost_usd", 0) or 0
    _live_log(path, f"=== DONE: ${cost:.4f} | {turns} turns ===")


# --- PostToolUse hook factories ---


def _make_tool_hook(log_path: Path):
    """Create a PostToolUse hook callback that writes to the given live log."""

    async def hook(input_data: dict, tool_use_id: str | None, context: Any) -> dict:
        try:
            name = input_data.get("tool_name", "?")
            inp = str(input_data.get("tool_input", ""))[:130]
            resp = str(input_data.get("tool_response", ""))[:150]
            _live_log(log_path, f"TOOL {name}: {inp}")
            _live_log(log_path, f"  <- {resp}")
        except Exception:
            pass
        return {}

    return hook


# --- Manifest helpers ---


def read_manifest() -> dict:
    if MANIFEST_PATH.exists():
        try:
            return json.loads(MANIFEST_PATH.read_text())
        except (json.JSONDecodeError, OSError):
            logger.warning("Corrupt manifest.json — starting fresh")
            return {}
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
    if agent == "orc":
        return ORC_WORKSPACE / "state"
    elif agent == "content":
        return CONTENT_WORKSPACE / "state"
    elif agent == "datum":
        return DATUM_WORKSPACE / "state"
    else:
        raise ValueError(f"Unknown agent: {agent}")


def read_session_num(agent: str) -> int:
    path = _state_dir(agent) / f"{agent}_session.txt"
    return int(path.read_text().strip()) if path.exists() else 1


def write_session_num(agent: str, n: int) -> None:
    path = _state_dir(agent) / f"{agent}_session.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(str(n))


def reset_iteration(agent: str) -> None:
    path = _state_dir(agent) / f"{agent}_iteration.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("0")


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

    async def _read_content_response():
        """Background task: read content agent response, track tokens, detect compaction."""
        try:
            async for msg in clients.content_client.receive_response():
                if isinstance(msg, AssistantMessage):
                    _log_assistant_message(CONTENT_LIVE_LOG, msg)
                elif isinstance(msg, ResultMessage):
                    update_manifest_tokens("content", msg.usage)
                    _log_result_message(CONTENT_LIVE_LOG, msg)
                    logger.info(
                        "Bridge: content done — turns=%d, cost=$%.4f",
                        msg.num_turns,
                        msg.total_cost_usd or 0,
                    )
                    if msg.result and "COMPACT_NOW" in msg.result:
                        clients.content_needs_restart = True
                        logger.info("Bridge: content agent signaled COMPACT_NOW")
        except Exception as e:
            logger.error("Bridge: error reading content response: %s", e)
        finally:
            clients.content_busy = False
            _live_log(CONTENT_LIVE_LOG, "--- idle (ready for next prompt) ---")

    @tool(
        "send_to_content_agent",
        "Send prompt to the persistent Content Agent. Returns immediately — content agent works in background. "
        "If content agent is busy, returns a busy message. Check on next heartbeat.",
        {"prompt": str},
    )
    async def send_to_content_agent(args: dict[str, Any]) -> dict[str, Any]:
        if clients.content_client is None:
            return {
                "content": [{"type": "text", "text": "Error: Content agent not connected"}],
                "is_error": True,
            }

        if clients.content_busy:
            return {
                "content": [{"type": "text", "text": "Content agent is still processing previous work. Will check again next heartbeat."}],
            }

        prompt = args["prompt"]
        logger.info("Bridge: forwarding to content agent (%d chars)", len(prompt))
        _live_log(CONTENT_LIVE_LOG, f">>> PROMPT: {prompt[:200]}")
        clients.content_busy = True
        try:
            await clients.content_client.query(prompt)
            asyncio.create_task(_read_content_response())
        except Exception as e:
            clients.content_busy = False
            logger.error("Bridge: failed to send to content agent: %s", e)
            return {
                "content": [{"type": "text", "text": f"Error sending to content agent: {e}"}],
                "is_error": True,
            }

        return {
            "content": [{"type": "text", "text": "Prompt sent to content agent. Working in background."}],
        }

    async def _read_datum_response():
        """Background task: read datum agent response, track tokens, detect compaction."""
        try:
            async for msg in clients.datum_client.receive_response():
                if isinstance(msg, AssistantMessage):
                    _log_assistant_message(DATUM_LIVE_LOG, msg)
                elif isinstance(msg, ResultMessage):
                    update_manifest_tokens("datum", msg.usage)
                    _log_result_message(DATUM_LIVE_LOG, msg)
                    logger.info(
                        "Bridge: datum done — turns=%d, cost=$%.4f",
                        msg.num_turns,
                        msg.total_cost_usd or 0,
                    )
                    if msg.result and "COMPACT_NOW" in msg.result:
                        clients.datum_needs_restart = True
                        logger.info("Bridge: datum agent signaled COMPACT_NOW")
        except Exception as e:
            logger.error("Bridge: error reading datum response: %s", e)
        finally:
            clients.datum_busy = False
            _live_log(DATUM_LIVE_LOG, "--- idle (ready for next prompt) ---")

    @tool(
        "send_to_datum_agent",
        "Send entity data to the persistent Datum Agent for dedup, enrichment, and storage. "
        "Returns immediately — datum agent works in background. "
        "If datum agent is busy, returns a busy message.",
        {"prompt": str},
    )
    async def send_to_datum_agent(args: dict[str, Any]) -> dict[str, Any]:
        if clients.datum_client is None:
            return {
                "content": [{"type": "text", "text": "Error: Datum agent not connected"}],
                "is_error": True,
            }

        if clients.datum_busy:
            return {
                "content": [{"type": "text", "text": "Datum agent is still processing previous work. Will check again next heartbeat."}],
            }

        prompt = args["prompt"]
        logger.info("Bridge: forwarding to datum agent (%d chars)", len(prompt))
        _live_log(DATUM_LIVE_LOG, f">>> PROMPT: {prompt[:200]}")
        clients.datum_busy = True
        try:
            await clients.datum_client.query(prompt)
            asyncio.create_task(_read_datum_response())
        except Exception as e:
            clients.datum_busy = False
            logger.error("Bridge: failed to send to datum agent: %s", e)
            return {
                "content": [{"type": "text", "text": f"Error sending to datum agent: {e}"}],
                "is_error": True,
            }

        return {
            "content": [{"type": "text", "text": "Prompt sent to datum agent. Working in background."}],
        }

    return create_sdk_mcp_server(name="bridge", version="1.0.0", tools=[send_to_content_agent, send_to_datum_agent])


# --- Agent option builders ---


def build_orc_options(bridge_server):
    from claude_agent_sdk import ClaudeAgentOptions, HookMatcher

    orc_tool_hook = _make_tool_hook(ORC_LIVE_LOG)

    return ClaudeAgentOptions(
        model=os.environ.get("AGENT_MODEL", "claude-sonnet-4-6"),
        permission_mode="dontAsk",
        allowed_tools=[
            "Bash", "Read", "Write", "Edit", "Glob", "Grep",
            "mcp__bridge__send_to_content_agent",
            "mcp__bridge__send_to_datum_agent",
        ],
        mcp_servers={"bridge": bridge_server},
        hooks={"PostToolUse": [HookMatcher(hooks=[orc_tool_hook])]},
        setting_sources=["project"],
        effort="low",
        max_turns=15,
        max_budget_usd=0.50,
        cwd=str(ORC_WORKSPACE),
        env={
            "ANTHROPIC_API_KEY": os.environ.get("ANTHROPIC_API_KEY", ""),
            "DATABASE_URL": os.environ.get("DATABASE_URL", ""),
        },
    )


def build_content_options():
    from claude_agent_sdk import AgentDefinition, ClaudeAgentOptions, HookMatcher, ThinkingConfigEnabled

    content_tool_hook = _make_tool_hook(CONTENT_LIVE_LOG)

    return ClaudeAgentOptions(
        model=os.environ.get("AGENT_MODEL", "claude-sonnet-4-6"),
        permission_mode="dontAsk",
        allowed_tools=[
            "Bash", "Read", "Write", "Edit", "Grep", "Glob", "Agent", "Skill",
            "mcp__web__web_browse", "mcp__web__web_scrape", "mcp__web__web_search",
            "mcp__web__extract_youtube", "mcp__web__extract_transcript",
            "mcp__web__fingerprint", "mcp__web__check_strategy",
            "mcp__web__manage_session", "mcp__web__validate",
            "mcp__web__cookie_status", "mcp__web__watch_url",
        ],
        mcp_servers={"web": {"type": "http", "url": "http://localhost:8001/mcp"}},
        hooks={"PostToolUse": [HookMatcher(hooks=[content_tool_hook])]},
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


def build_datum_options():
    from claude_agent_sdk import ClaudeAgentOptions, HookMatcher, ThinkingConfigEnabled

    datum_tool_hook = _make_tool_hook(DATUM_LIVE_LOG)

    return ClaudeAgentOptions(
        model=os.environ.get("AGENT_MODEL", "claude-sonnet-4-6"),
        permission_mode="dontAsk",
        allowed_tools=[
            "Bash", "Read", "Write", "Edit", "Grep", "Glob", "Skill",
            "mcp__web__web_browse", "mcp__web__web_scrape", "mcp__web__web_search",
            "mcp__web__fingerprint", "mcp__web__check_strategy",
            "mcp__web__manage_session", "mcp__web__validate",
        ],
        mcp_servers={"web": {"type": "http", "url": "http://localhost:8001/mcp"}},
        hooks={"PostToolUse": [HookMatcher(hooks=[datum_tool_hook])]},
        setting_sources=["project"],
        thinking=ThinkingConfigEnabled(type="enabled", budget_tokens=5000),
        effort="high",
        max_turns=30,
        max_budget_usd=2.0,
        cwd=str(DATUM_WORKSPACE),
        env={
            "ANTHROPIC_API_KEY": os.environ.get("ANTHROPIC_API_KEY", ""),
            "DATABASE_URL": os.environ.get("DATABASE_URL", ""),
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


# --- Datum client lifecycle ---


async def start_datum_client():
    from claude_agent_sdk import ClaudeSDKClient

    client = ClaudeSDKClient(options=build_datum_options())
    await client.__aenter__()
    return client


async def stop_datum_client():
    if clients.datum_client:
        try:
            await clients.datum_client.__aexit__(None, None, None)
        except Exception as e:
            logger.warning("Error stopping datum client: %s", e)
        clients.datum_client = None


async def restart_datum_client():
    logger.info("Restarting datum agent session")
    await stop_datum_client()
    bump_session("datum")
    reset_manifest_tokens("datum", read_session_num("datum"))
    clients.datum_client = await start_datum_client()
    clients.datum_needs_restart = False


# --- Pre-check: skip LLM if no work ---

PIPELINE_INTERVAL_SECONDS = 12 * 3600  # 12 hours


async def has_work() -> str | None:
    """Check inbox + pipeline schedule WITHOUT calling the LLM. Returns reason string if work found, None if idle."""
    import subprocess

    # Check inbox
    try:
        db_url = os.environ.get("DATABASE_URL", "")
        if db_url:
            result = subprocess.run(
                ["psql", db_url, "-t", "-A", "-c", "SELECT count(*) FROM cai_inbox WHERE processed = FALSE"],
                capture_output=True, text=True, timeout=5,
            )
            count_str = result.stdout.strip()
            if not count_str or not count_str.isdigit():
                return "inbox check returned unexpected output, waking agent to be safe"
            count = int(count_str)
            if count > 0:
                return f"inbox has {count} unprocessed messages"
    except Exception as e:
        logger.warning("Pre-check inbox failed: %s", e)
        return "inbox check failed, waking agent to be safe"

    # Check pipeline schedule
    try:
        ts_file = CONTENT_WORKSPACE / "state" / "last_pipeline_run.txt"
        if not ts_file.exists() or not ts_file.read_text().strip():
            return "pipeline never ran (no timestamp)"
        from datetime import datetime, timezone
        last_run_str = ts_file.read_text().strip()
        last_run = datetime.fromisoformat(last_run_str.replace("Z", "+00:00"))
        elapsed = (datetime.now(timezone.utc) - last_run).total_seconds()
        if elapsed > PIPELINE_INTERVAL_SECONDS:
            return f"pipeline overdue ({elapsed/3600:.1f}h since last run)"
    except Exception as e:
        logger.warning("Pre-check pipeline failed: %s", e)
        return "pipeline check failed, waking agent to be safe"

    return None  # No work


# --- Main loop ---


async def run_agent() -> None:
    from claude_agent_sdk import AssistantMessage, ClaudeSDKClient, ResultMessage

    bridge_server = create_bridge_server()
    logger.info("Model: %s", os.environ.get("AGENT_MODEL", "claude-sonnet-4-6"))

    while True:
        # Start content agent
        reset_manifest_tokens("content", read_session_num("content"))
        clients.content_client = await start_content_client()
        clients.content_needs_restart = False
        _live_log(CONTENT_LIVE_LOG, f"=== Content agent started — session #{read_session_num('content')} ===")
        logger.info("Content agent started — session #%d", read_session_num("content"))

        # Start datum agent
        reset_manifest_tokens("datum", read_session_num("datum"))
        clients.datum_client = await start_datum_client()
        clients.datum_needs_restart = False
        _live_log(DATUM_LIVE_LOG, f"=== Datum agent started — session #{read_session_num('datum')} ===")
        logger.info("Datum agent started — session #%d", read_session_num("datum"))

        # Start orchestrator
        orc_session = read_session_num("orc")
        reset_manifest_tokens("orc", orc_session)
        orc_needs_restart = False
        consecutive_zero_turns = 0
        _live_log(ORC_LIVE_LOG, f"=== Orchestrator started — session #{orc_session} ===")

        try:
            async with ClaudeSDKClient(options=build_orc_options(bridge_server)) as orc_client:
                logger.info("Orchestrator started — session #%d", orc_session)

                while not orc_needs_restart:
                    if clients.content_needs_restart:
                        await restart_content_client()
                    if clients.datum_needs_restart:
                        await restart_datum_client()

                    # Pre-check: skip LLM call if no work (free)
                    work_reason = await has_work()
                    if work_reason is None:
                        _live_log(ORC_LIVE_LOG, "--- idle (no work) ---")
                        await asyncio.sleep(HEARTBEAT_INTERVAL)
                        continue

                    _live_log(ORC_LIVE_LOG, f">>> heartbeat ({work_reason})")
                    logger.info("Work detected: %s", work_reason)
                    await orc_client.query("heartbeat")
                    async for msg in orc_client.receive_response():
                        if isinstance(msg, AssistantMessage):
                            _log_assistant_message(ORC_LIVE_LOG, msg)
                        elif isinstance(msg, ResultMessage):
                            update_manifest_tokens("orc", msg.usage)
                            _log_result_message(ORC_LIVE_LOG, msg)
                            logger.info(
                                "Heartbeat done — turns=%d, cost=$%.4f",
                                msg.num_turns,
                                msg.total_cost_usd or 0,
                            )
                            if msg.result and "COMPACT_NOW" in msg.result:
                                orc_needs_restart = True
                            # Detect dead session (budget exhausted or broken)
                            if msg.num_turns == 0:
                                consecutive_zero_turns += 1
                            else:
                                consecutive_zero_turns = 0

                    # 2 consecutive zero-turn heartbeats = session is dead, restart
                    if consecutive_zero_turns >= 2:
                        logger.warning("Orchestrator dead (2 zero-turn heartbeats) — restarting session")
                        _live_log(ORC_LIVE_LOG, "!!! SESSION DEAD — restarting !!!")
                        orc_needs_restart = True

                    if not orc_needs_restart:
                        await asyncio.sleep(HEARTBEAT_INTERVAL)

        except Exception as e:
            logger.error("Session error: %s", e, exc_info=True)
            await asyncio.sleep(5)
        finally:
            await stop_content_client()
            await stop_datum_client()

        # Always bump session on re-entry (exception or compaction)
        bump_session("orc")


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
    await stop_datum_client()
    logger.info("Lifecycle manager stopped")


if __name__ == "__main__":
    asyncio.run(main())
