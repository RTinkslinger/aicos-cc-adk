"""Sync Agent runner — asyncio timer triggers query() sessions.

v2.2 architecture: Postgres <-> Notion bidirectional sync.
Single scheduled loop:
  - Sync cycle (10 min) — find unsynced rows, push to Notion, pull human changes

Uses query() for one-off scheduled sessions (NOT ClaudeSDKClient).
Uses permission_mode="dontAsk" + allowed_tools for autonomous headless operation.
No MCP connections — Sync Agent uses Bash + psql + python3 scripts only.
No subagent spawning — Sync Agent works sequentially.
"""
from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path

SYNC_INTERVAL = 600  # 10 minutes

logger = logging.getLogger("sync-agent")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)


def load_system_prompt() -> str:
    """Load the Sync Agent system prompt from system_prompt.md."""
    return Path(__file__).parent.joinpath("system_prompt.md").read_text(encoding="utf-8")


def get_options():
    """Build ClaudeAgentOptions for Sync Agent sessions.

    Uses dontAsk permission mode: only tools in allowed_tools run,
    everything else is auto-denied with no prompts.

    No MCP servers. No Agent tool. Simpler config than Content Agent.
    """
    from claude_agent_sdk import ClaudeAgentOptions, ThinkingConfig

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
            # Skill loading
            "Skill",
        ],
        # No MCP servers — Sync Agent uses Bash + psql + python3 scripts
        # No agents — Sync Agent does not spawn subagents
        setting_sources=["project"],
        thinking=ThinkingConfig(type="enabled", budget_tokens=5000),
        effort="medium",
        max_turns=20,
        max_budget_usd=1.0,
        cwd="/opt/agents",
        env={
            "ANTHROPIC_API_KEY": os.environ.get("ANTHROPIC_API_KEY", ""),
            "DATABASE_URL": os.environ.get("DATABASE_URL", ""),
            "NOTION_TOKEN": os.environ.get("NOTION_TOKEN", ""),
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


SYNC_PROMPT = """\
Run your sync cycle. Execute the following steps in order:

## Step 1: Push unsynced rows to Notion

Find all rows with notion_synced=FALSE across the three synced tables:

```sql
SELECT id, name, conviction, status, core_thesis, evidence_for, evidence_against, key_questions, notion_page_id
FROM thesis_threads WHERE notion_synced = FALSE;

SELECT id, action_text, action_type, priority, status, assigned_to, relevance_score, reasoning, thesis_connection, notion_page_id
FROM actions WHERE notion_synced = FALSE;

SELECT id, title, channel, url, content_type, relevance_score, net_newness, summary, digest_url, notion_page_id
FROM content_digests WHERE notion_synced = FALSE;
```

For each unsynced row:
1. Load skill: skills/sync/notion-patterns.md (for Notion API property formatting)
2. If notion_page_id is NULL: CREATE a new Notion page in the appropriate database
3. If notion_page_id exists: UPDATE the existing Notion page
4. Use python3 scripts or Bash + curl with $NOTION_TOKEN for Notion API calls
5. On success: UPDATE the row SET notion_synced = TRUE, notion_page_id = '<page_id>', last_synced_at = NOW()
6. On failure: Log the error, increment sync_attempts. If sync_attempts >= 5, write an error notification.

## Step 2: Pull human-owned field changes from Notion

Query Notion for recent changes to human-owned fields:
- thesis_threads.status (Active/Exploring/Parked/Archived) — set by Aakash in Notion
- actions.outcome (Unknown/Helpful/Gold) — set by Aakash in Notion

Load skill: skills/sync/conflict-resolution.md for conflict resolution rules.

For each detected change:
1. Update the Postgres row with the Notion value (human-owned fields always win)
2. Log the change to change_events table

## Step 3: Update sync_metadata

```sql
UPDATE sync_metadata
SET last_sync_at = NOW(),
    rows_pushed = <count>,
    rows_pulled = <count>,
    errors = <count>
WHERE agent = 'sync-agent';
```

If no sync_metadata row exists, INSERT one.

## Step 4: Process change events

Load skill: skills/sync/change-interpretation.md

Query unprocessed change events:
```sql
SELECT * FROM change_events WHERE processed = FALSE ORDER BY detected_at;
```

For each change event, determine if it should generate an action or notification:
- thesis.status Active -> Parked: generate deprioritization action
- thesis.status Parked -> Active: generate resurfacing action
- thesis.conviction reaching High: generate portfolio review action
- action.outcome = Gold: generate pattern analysis action

Mark change events as processed after handling.

## Step 5: Report

Summarise what was synced: rows pushed, rows pulled, changes detected, errors encountered.
If there were errors, include details for debugging.
"""


async def sync_loop():
    """Run sync cycle every 10 minutes."""
    while True:
        try:
            logger.info("Starting sync cycle...")
            result = await run_session(SYNC_PROMPT)
            logger.info(
                "Sync cycle complete, cost=$%.4f",
                result.get("cost_usd", 0),
            )
        except Exception as e:
            logger.error("Sync cycle error: %s", e, exc_info=True)
        await asyncio.sleep(SYNC_INTERVAL)


async def main():
    """Entry point: run the sync loop."""
    logger.info("Sync Agent v2.2 starting...")
    # Small delay to let other services start first
    await asyncio.sleep(10)
    await sync_loop()


if __name__ == "__main__":
    asyncio.run(main())
