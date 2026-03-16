"""Content Agent runner — asyncio timers trigger query() sessions.

v2.2 architecture: agent reasons via instructions + tools + skills.
Two scheduled loops:
  - Inbox check (1 min) — reads cai_inbox via psql
  - Content cycle (5 min) — watch list sources, fetch, analyse, score, publish

Uses query() for one-off scheduled sessions (NOT ClaudeSDKClient).
Uses permission_mode="dontAsk" + allowed_tools for autonomous headless operation.
"""
from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path

INBOX_INTERVAL = 60  # 1 minute
CONTENT_INTERVAL = 300  # 5 minutes

logger = logging.getLogger("content-agent")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)


def load_system_prompt() -> str:
    """Load the Content Agent system prompt from system_prompt.md."""
    return Path(__file__).parent.joinpath("system_prompt.md").read_text(encoding="utf-8")


def get_options():
    """Build ClaudeAgentOptions for Content Agent sessions.

    Uses dontAsk permission mode: only tools in allowed_tools run,
    everything else is auto-denied with no prompts.
    """
    from claude_agent_sdk import AgentDefinition, ClaudeAgentOptions, ThinkingConfigEnabled

    return ClaudeAgentOptions(
        model=os.environ.get("AGENT_MODEL", "claude-sonnet-4-6"),
        system_prompt=load_system_prompt(),
        permission_mode="dontAsk",
        allowed_tools=[
            # CC built-in tools
            "Bash",
            "Read",
            "Write",
            "Grep",
            "Glob",
            # Subagent spawning
            "Agent",
            # Skill loading
            "Skill",
            # Web Tools MCP — direct tools
            "mcp__web__web_browse",
            "mcp__web__web_scrape",
            "mcp__web__web_search",
            "mcp__web__extract_youtube",
            "mcp__web__extract_transcript",
            "mcp__web__fingerprint",
            "mcp__web__check_strategy",
            "mcp__web__manage_session",
            "mcp__web__validate",
            "mcp__web__cookie_status",
            "mcp__web__watch_url",
        ],
        mcp_servers={
            "web": {"type": "http", "url": "http://localhost:8001/mcp"},
        },
        agents={
            "web-researcher": AgentDefinition(
                description=(
                    "Full-capability web research specialist for complex, multi-step "
                    "web tasks requiring strategy, authentication, and deep browsing"
                ),
                prompt=(
                    "You are a web research specialist with the full web toolkit.\n\n"
                    "Load web skills (skills/web/) for strategy, anti-detection, auth "
                    "escalation, and content validation. Use Bash + curl/Jina for quick "
                    "fetches. Use web_browse for SPAs. Use check_strategy before approaching "
                    "unfamiliar domains. Always validate content quality before returning.\n\n"
                    "Complete the research task thoroughly and return a comprehensive result."
                ),
                tools=[
                    "Bash",
                    "Read",
                    "Write",
                    "Skill",
                    "mcp__web__web_browse",
                    "mcp__web__web_scrape",
                    "mcp__web__web_search",
                    "mcp__web__extract_youtube",
                    "mcp__web__extract_transcript",
                    "mcp__web__fingerprint",
                    "mcp__web__check_strategy",
                    "mcp__web__manage_session",
                    "mcp__web__validate",
                    "mcp__web__cookie_status",
                    "mcp__web__watch_url",
                ],
            ),
            "content-worker": AgentDefinition(
                description="Lightweight content analysis worker for parallel batch processing",
                prompt=(
                    "You are a content analysis worker. Analyse the given content using skills "
                    "and Bash + psql for DB access. Score relevance, identify thesis connections, "
                    "generate action proposals. Load content skills for methodology. Load "
                    "data/postgres-schema skill for DB conventions.\n\n"
                    "Return structured analysis result."
                ),
                tools=["Bash", "Read", "Write", "Skill"],
            ),
        },
        setting_sources=["project"],
        thinking=ThinkingConfigEnabled(type="enabled", budget_tokens=10000),
        effort="high",
        max_turns=30,
        max_budget_usd=3.0,
        cwd="/opt/agents",
        env={
            "ANTHROPIC_API_KEY": os.environ.get("ANTHROPIC_API_KEY", ""),
            "DATABASE_URL": os.environ.get("DATABASE_URL", ""),
            "FIRECRAWL_API_KEY": os.environ.get("FIRECRAWL_API_KEY", ""),
        },
    )


async def run_session(prompt: str) -> dict:
    """Run a single agent session with the given prompt.

    Returns dict with result text and cost.
    """
    from claude_agent_sdk import AssistantMessage, ResultMessage, TextBlock, query

    options = get_options()
    result_text = ""
    cost = 0.0

    async for message in query(prompt=prompt, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    result_text += block.text
        elif isinstance(message, ResultMessage):
            cost = getattr(message, "cost_usd", 0) or 0
            logger.info("Session complete: %s, cost=$%.4f", message.subtype, cost)

    return {"result": result_text, "cost_usd": cost}


INBOX_PROMPT = """\
Check the cai_inbox table for unprocessed messages.

Run:
```
psql $DATABASE_URL -c "SELECT id, type, content, metadata, created_at FROM cai_inbox WHERE processed = FALSE ORDER BY created_at"
```

If there are unprocessed messages:
1. Load the skill: skills/content/inbox-handling.md
2. Process each message according to its type (track_source, research_request, question, etc.)
3. For track_source messages: update /opt/agents/data/watch_list.json
4. For research requests: spawn a web-researcher subagent via the Agent tool
5. For questions: look up the answer from Postgres or via web research, write response to notifications table
6. Mark each message processed after handling:
   ```
   psql $DATABASE_URL -c "UPDATE cai_inbox SET processed = TRUE, processed_at = NOW() WHERE id = <id>"
   ```

If no unprocessed messages, report: "No pending inbox messages."
"""

CONTENT_PROMPT = """\
Run your content pipeline cycle.

1. Load your watch list: Read /opt/agents/data/watch_list.json
2. Load skill: skills/data/postgres-schema.md (for DB conventions)
3. For each active source in the watch list:
   a. Check for new content since the last check timestamp
   b. Use extract_youtube for YouTube playlists/channels
   c. Use web_scrape or web_browse for RSS/web sources
   d. Use Bash + curl for simple API endpoints
4. For each new content item found:
   a. Load skill: skills/content/analysis.md
   b. Load skill: skills/content/thesis-reasoning.md
   c. Fetch thesis threads from Postgres:
      psql $DATABASE_URL -c "SELECT name, conviction, status, core_thesis, key_questions, evidence_for, evidence_against FROM thesis_threads WHERE status IN ('Active', 'Exploring')"
   d. Analyse the content against thesis threads, portfolio, and priority buckets
   e. Load skill: skills/content/scoring.md
   f. Score every proposed action using the 5-factor model
   g. Load skill: skills/content/publishing.md
   h. Publish the digest (git push to aicos-digests repo)
5. Write ALL results to Postgres with notion_synced=FALSE:
   - Content digests: INSERT INTO content_digests (...)
   - Actions: INSERT INTO actions (...)
   - Thesis evidence: UPDATE thesis_threads SET evidence_for = ..., notion_synced = FALSE WHERE name = ...
6. Write notifications for significant findings (score >= 7):
   psql $DATABASE_URL -c "INSERT INTO notifications (type, content, metadata, created_at) VALUES ('content_alert', '...', '...', NOW())"
7. Update the watch list's last_checked timestamps

If the watch list is empty or doesn't exist, report: "No active sources in watch list."
For batch processing (3+ items), use Class 3 delegation: spawn content-worker subagents via the Agent tool.
For complex web research needs, use Class 2 delegation: spawn web-researcher subagent via the Agent tool.
"""


async def inbox_loop():
    """Check CAI inbox every 1 minute."""
    while True:
        try:
            logger.info("Starting inbox check...")
            result = await run_session(INBOX_PROMPT)
            logger.info(
                "Inbox check complete, cost=$%.4f",
                result.get("cost_usd", 0),
            )
        except Exception as e:
            logger.error("Inbox check error: %s", e, exc_info=True)
        await asyncio.sleep(INBOX_INTERVAL)


async def content_loop():
    """Run content pipeline every 5 minutes."""
    while True:
        try:
            logger.info("Starting content cycle...")
            result = await run_session(CONTENT_PROMPT)
            logger.info(
                "Content cycle complete, cost=$%.4f",
                result.get("cost_usd", 0),
            )
        except Exception as e:
            logger.error("Content cycle error: %s", e, exc_info=True)
        await asyncio.sleep(CONTENT_INTERVAL)


async def main():
    """Entry point: run inbox + content loops concurrently."""
    logger.info("Content Agent v2.2 starting...")
    # Small delay to let MCP servers start first
    await asyncio.sleep(5)
    await asyncio.gather(inbox_loop(), content_loop())


if __name__ == "__main__":
    asyncio.run(main())
