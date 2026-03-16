# Agent Lifecycle Management & Logging — Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace ephemeral `query()` runners with persistent `ClaudeSDKClient`-based agents, managed by a thin Python lifecycle manager, with filesystem hooks for iteration logging and context-aware compaction.

**Architecture:** A thin Python daemon (`lifecycle.py`) manages `ClaudeSDKClient` instances for each agent. It sends heartbeat prompts on a 60s timer, tracks token usage from `ResultMessage.usage`, writes a manifest file, and handles session restarts on compaction signals. All logging, manifest checking, and compaction triggering is done by filesystem hooks (shell scripts in `.claude/hooks/`) — not Python. Agents write their own checkpoint files before compaction; new sessions bootstrap from checkpoint files.

**Tech Stack:** Python 3.12, `claude_agent_sdk` (ClaudeSDKClient, ClaudeAgentOptions, ResultMessage, HookMatcher), `asyncio`, filesystem hooks (bash/jq), systemd.

**Scope:** This plan covers ONLY the lifecycle manager, traces/iteration system, hooks, and compaction logic. It does NOT cover agent system prompts, skills, HEARTBEAT.md content, or the @tool bridge between orchestrator and content agent — those are separate plans.

---

## File Structure

```
mcp-servers/agents/
  orchestrator/
    lifecycle.py              # Thin Python daemon — heartbeats, token tracking, session restart
    .claude/
      hooks/
        stop-iteration-log.sh     # Stop hook: log iteration to traces after every query
        prompt-manifest-check.sh  # UserPromptSubmit hook: check manifest, inject compaction warning
        pre-compact-flush.sh      # PreCompact hook: emergency checkpoint before SDK auto-compaction
      settings.json               # Registers filesystem hooks
    state/
      orc_session.txt             # Current session number (integer)
      orc_iteration.txt           # Current iteration number (integer)
      orc_last_log.txt            # Agent's self-reported summary (written by agent each turn)
      orc_checkpoint.md           # Checkpoint file (written by agent before compaction)
    CLAUDE.md                     # (Next plan — not this plan)
    HEARTBEAT.md                  # (Next plan — not this plan)
  traces/
    manifest.json                 # Token usage per agent, written by Python lifecycle
    active.txt                    # Path to current active traces file (single line)
    20260316-1400.md              # Example traces file (timestamped on creation)
    archive/                      # Closed traces files with summaries prepended
  infra/
    orchestrator.service          # systemd unit for lifecycle.py
```

**Key design decisions:**
- `orchestrator/` is the agent's workspace root (`cwd` for ClaudeSDKClient)
- `.claude/hooks/` inside the workspace — loaded via `setting_sources=["project"]`
- `traces/` is shared across all agents (lives one level up from any agent workspace)
- `state/` is per-agent, inside the agent's workspace
- `manifest.json` is the ONLY file Python writes (besides active.txt)
- All other state files are written by agents (via tools) or hooks (via shell scripts)

---

## Chunk 1: Traces Infrastructure

### Task 1: Traces directory and manifest schema

**Files:**
- Create: `mcp-servers/agents/traces/.gitkeep`
- Create: `mcp-servers/agents/traces/manifest.json`
- Create: `mcp-servers/agents/traces/active.txt`

- [ ] **Step 1: Create traces directory with initial files**

```bash
mkdir -p mcp-servers/agents/traces/archive
```

- [ ] **Step 2: Create initial manifest.json**

```json
{
  "orc": {
    "session": 1,
    "input_tokens": 0,
    "output_tokens": 0,
    "last_updated": null
  }
}
```

- [ ] **Step 3: Create active.txt pointing to first traces file**

Create `traces/active.txt` containing:
```
traces/20260316-0000.md
```

- [ ] **Step 4: Create the first traces file**

```markdown
# Traces — Started 2026-03-16 00:00 UTC

## Summary
(written on compaction)

## Iteration Logs
```

- [ ] **Step 5: Commit**

```bash
git add mcp-servers/agents/traces/
git commit -m "feat: traces infrastructure — manifest, active pointer, initial file"
```

### Task 2: State directory for orchestrator

**Files:**
- Create: `mcp-servers/agents/orchestrator/state/orc_session.txt`
- Create: `mcp-servers/agents/orchestrator/state/orc_iteration.txt`

- [ ] **Step 1: Create state directory with initial counters**

```bash
mkdir -p mcp-servers/agents/orchestrator/state
echo "1" > mcp-servers/agents/orchestrator/state/orc_session.txt
echo "0" > mcp-servers/agents/orchestrator/state/orc_iteration.txt
```

- [ ] **Step 2: Commit**

```bash
git add mcp-servers/agents/orchestrator/
git commit -m "feat: orchestrator state directory with session/iteration counters"
```

---

## Chunk 2: Filesystem Hooks

### Task 3: Stop hook — iteration logging

**Files:**
- Create: `mcp-servers/agents/orchestrator/.claude/hooks/stop-iteration-log.sh`

**Behavior:** Fires after every completed query. Reads the agent's self-reported summary from `state/{agent}_last_log.txt`, increments the iteration counter, and appends a formatted log line to the active traces file.

**Log format:** `$orc | sess #1 | it 3 | 19:24 UTC :: 'did nothing'`

- [ ] **Step 1: Write the Stop hook**

```bash
#!/bin/bash
# Stop hook: log iteration to active traces file
# Fires after every completed query (heartbeat or task).
# Reads agent's self-reported summary from state/{AGENT}_last_log.txt.
# If no summary file, logs "did nothing".
#
# Exit 0 = agent stops normally (no interference).

set -euo pipefail
command -v jq >/dev/null 2>&1 || exit 0

INPUT=$(cat)

# Prevent infinite loop if stop hook is re-firing
STOP_ACTIVE=$(echo "$INPUT" | jq -r '.stop_hook_active // false')
if [ "$STOP_ACTIVE" = "true" ]; then
  exit 0
fi

CWD=$(echo "$INPUT" | jq -r '.cwd // empty')
if [ -z "$CWD" ]; then
  exit 0
fi

AGENT="orc"
STATE_DIR="${CWD}/state"
ITER_FILE="${STATE_DIR}/${AGENT}_iteration.txt"
SESS_FILE="${STATE_DIR}/${AGENT}_session.txt"
LOG_FILE="${STATE_DIR}/${AGENT}_last_log.txt"

# Traces file path — read from shared active pointer
# active.txt is relative to the agents/ root (one level up from CWD)
AGENTS_ROOT="$(dirname "$CWD")"
ACTIVE_TRACES_PTR="${AGENTS_ROOT}/traces/active.txt"
if [ ! -f "$ACTIVE_TRACES_PTR" ]; then
  exit 0
fi
ACTIVE_TRACES="${AGENTS_ROOT}/$(cat "$ACTIVE_TRACES_PTR")"

# Read and increment iteration counter
SESS=$(cat "$SESS_FILE" 2>/dev/null || echo "1")
ITER=$(cat "$ITER_FILE" 2>/dev/null || echo "0")
ITER=$((ITER + 1))
echo "$ITER" > "$ITER_FILE"

# Read agent's self-reported summary (written by agent via Write tool)
SUMMARY=""
if [ -f "$LOG_FILE" ]; then
  SUMMARY=$(head -1 "$LOG_FILE" | cut -c1-200)
  # Clear the log file for next iteration
  : > "$LOG_FILE"
fi
[ -z "$SUMMARY" ] && SUMMARY="did nothing"

# Timestamp
TIMESTAMP=$(date -u +"%H:%M UTC")

# Append to active traces file
echo "\$${AGENT} | sess #${SESS} | it ${ITER} | ${TIMESTAMP} :: '${SUMMARY}'" >> "$ACTIVE_TRACES"

exit 0
```

- [ ] **Step 2: Make executable**

```bash
chmod +x mcp-servers/agents/orchestrator/.claude/hooks/stop-iteration-log.sh
```

- [ ] **Step 3: Test hook manually**

```bash
cd mcp-servers/agents
mkdir -p orchestrator/state traces
echo "1" > orchestrator/state/orc_session.txt
echo "0" > orchestrator/state/orc_iteration.txt
echo "checked inbox, 2 messages found" > orchestrator/state/orc_last_log.txt
echo "traces/test.md" > traces/active.txt
echo "# Test Traces" > traces/test.md

echo '{"cwd": "'$(pwd)'/orchestrator", "stop_hook_active": false}' | bash orchestrator/.claude/hooks/stop-iteration-log.sh

cat traces/test.md
# Expected: $orc | sess #1 | it 1 | HH:MM UTC :: 'checked inbox, 2 messages found'

cat orchestrator/state/orc_iteration.txt
# Expected: 1
```

- [ ] **Step 4: Commit**

```bash
git add mcp-servers/agents/orchestrator/.claude/hooks/stop-iteration-log.sh
git commit -m "feat: Stop hook for iteration logging to traces"
```

### Task 4: UserPromptSubmit hook — manifest checking

**Files:**
- Create: `mcp-servers/agents/orchestrator/.claude/hooks/prompt-manifest-check.sh`

**Behavior:** Fires before every query is processed. Reads `traces/manifest.json` for this agent's token count. If >100K tokens, injects compaction instructions via stderr + exit 2. Otherwise exit 0 (proceed normally).

- [ ] **Step 1: Write the UserPromptSubmit hook**

```bash
#!/bin/bash
# UserPromptSubmit hook: check manifest for context limits.
# If agent's token count exceeds threshold, inject compaction instructions.
#
# Exit 0 = proceed normally.
# Exit 2 = continue with stderr injected as context (compaction warning).

set -euo pipefail
command -v jq >/dev/null 2>&1 || exit 0

INPUT=$(cat)
CWD=$(echo "$INPUT" | jq -r '.cwd // empty')
if [ -z "$CWD" ]; then
  exit 0
fi

AGENT="orc"
THRESHOLD=100000
AGENTS_ROOT="$(dirname "$CWD")"
MANIFEST="${AGENTS_ROOT}/traces/manifest.json"

if [ ! -f "$MANIFEST" ]; then
  exit 0
fi

INPUT_TOKENS=$(jq -r ".${AGENT}.input_tokens // 0" "$MANIFEST" 2>/dev/null || echo "0")
OUTPUT_TOKENS=$(jq -r ".${AGENT}.output_tokens // 0" "$MANIFEST" 2>/dev/null || echo "0")
TOTAL=$((INPUT_TOKENS + OUTPUT_TOKENS))

if [ "$TOTAL" -gt "$THRESHOLD" ]; then
  cat >&2 <<EOF
COMPACTION REQUIRED: Session at ${TOTAL} tokens (threshold: ${THRESHOLD}).
Before doing anything else:
1. Write your full state to state/${AGENT}_checkpoint.md
   Include: current state, pending work, recent context (last 5 iterations), key facts.
2. End your response with the exact word: COMPACT_NOW
EOF
  exit 2
fi

exit 0
```

- [ ] **Step 2: Make executable**

```bash
chmod +x mcp-servers/agents/orchestrator/.claude/hooks/prompt-manifest-check.sh
```

- [ ] **Step 3: Test hook manually — under threshold**

```bash
# Set manifest to low token count
cat > mcp-servers/agents/traces/manifest.json <<'EOF'
{"orc": {"session": 1, "input_tokens": 5000, "output_tokens": 2000, "last_updated": null}}
EOF

echo '{"cwd": "'$(pwd)'/mcp-servers/agents/orchestrator"}' | bash mcp-servers/agents/orchestrator/.claude/hooks/prompt-manifest-check.sh
echo "Exit code: $?"
# Expected: Exit code: 0 (no output, proceed normally)
```

- [ ] **Step 4: Test hook manually — over threshold**

```bash
# Set manifest to high token count
cat > mcp-servers/agents/traces/manifest.json <<'EOF'
{"orc": {"session": 1, "input_tokens": 80000, "output_tokens": 25000, "last_updated": null}}
EOF

echo '{"cwd": "'$(pwd)'/mcp-servers/agents/orchestrator"}' | bash mcp-servers/agents/orchestrator/.claude/hooks/prompt-manifest-check.sh 2>&1
echo "Exit code: $?"
# Expected: COMPACTION REQUIRED message, Exit code: 2
```

- [ ] **Step 5: Commit**

```bash
git add mcp-servers/agents/orchestrator/.claude/hooks/prompt-manifest-check.sh
git commit -m "feat: UserPromptSubmit hook for manifest-based compaction detection"
```

### Task 5: PreCompact hook — emergency checkpoint

**Files:**
- Create: `mcp-servers/agents/orchestrator/.claude/hooks/pre-compact-flush.sh`

**Behavior:** Fires before the SDK's automatic context compaction (~180K tokens). Writes a minimal emergency checkpoint from the last 30 trace lines. This is the safety net — the primary path is the agent writing its own rich checkpoint at 100K via the UserPromptSubmit hook.

- [ ] **Step 1: Write the PreCompact hook**

```bash
#!/bin/bash
# PreCompact hook: emergency state dump before SDK auto-compaction.
# This is the SAFETY NET. The primary compaction path is agent-written
# checkpoints triggered by the UserPromptSubmit manifest check at 100K tokens.
# This hook fires if the agent somehow reaches ~180K without compacting.
#
# Writes a minimal checkpoint from recent traces. Better than nothing.
# Exit 0 = allow compaction to proceed.

set -euo pipefail
command -v jq >/dev/null 2>&1 || exit 0

INPUT=$(cat)
CWD=$(echo "$INPUT" | jq -r '.cwd // empty')
if [ -z "$CWD" ]; then
  exit 0
fi

AGENT="orc"
STATE_DIR="${CWD}/state"
AGENTS_ROOT="$(dirname "$CWD")"
ACTIVE_TRACES_PTR="${AGENTS_ROOT}/traces/active.txt"
CHECKPOINT="${STATE_DIR}/${AGENT}_checkpoint.md"
TIMESTAMP=$(date -u +"%Y-%m-%d %H:%M UTC")

# Only write if no checkpoint already exists (agent may have written one)
if [ -f "$CHECKPOINT" ]; then
  exit 0
fi

# Get recent traces
RECENT_TRACES=""
if [ -f "$ACTIVE_TRACES_PTR" ]; then
  ACTIVE_TRACES="${AGENTS_ROOT}/$(cat "$ACTIVE_TRACES_PTR")"
  if [ -f "$ACTIVE_TRACES" ]; then
    RECENT_TRACES=$(tail -30 "$ACTIVE_TRACES" 2>/dev/null || echo "no traces available")
  fi
fi

cat > "$CHECKPOINT" <<EOF
# Emergency Checkpoint — SDK Auto-Compaction
*Written: ${TIMESTAMP} by PreCompact hook (NOT by agent)*

## Warning
This checkpoint was written by the PreCompact safety net, not by the agent.
It contains minimal state. Read recent traces and state files for fuller context.

## Recent Traces (last 30 lines)
\`\`\`
${RECENT_TRACES}
\`\`\`

## Recovery Instructions
1. Read HEARTBEAT.md for your task checklist
2. Read traces/ for recent history
3. Check state/ for any pending work
4. Resume normal heartbeat operation
EOF

exit 0
```

- [ ] **Step 2: Make executable**

```bash
chmod +x mcp-servers/agents/orchestrator/.claude/hooks/pre-compact-flush.sh
```

- [ ] **Step 3: Commit**

```bash
git add mcp-servers/agents/orchestrator/.claude/hooks/pre-compact-flush.sh
git commit -m "feat: PreCompact hook for emergency checkpoint before SDK auto-compaction"
```

### Task 6: Hook registration — settings.json

**Files:**
- Create: `mcp-servers/agents/orchestrator/.claude/settings.json`

**Behavior:** Registers all three filesystem hooks so the Agent SDK loads them via `setting_sources=["project"]`.

- [ ] **Step 1: Write settings.json**

```json
{
  "hooks": {
    "Stop": [
      {
        "type": "command",
        "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/stop-iteration-log.sh"
      }
    ],
    "UserPromptSubmit": [
      {
        "type": "command",
        "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/prompt-manifest-check.sh"
      }
    ],
    "PreCompact": [
      {
        "type": "command",
        "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/pre-compact-flush.sh"
      }
    ]
  }
}
```

- [ ] **Step 2: Commit**

```bash
git add mcp-servers/agents/orchestrator/.claude/settings.json
git commit -m "feat: register filesystem hooks in settings.json"
```

---

## Chunk 3: Python Lifecycle Manager

### Task 7: lifecycle.py — core daemon

**Files:**
- Create: `mcp-servers/agents/orchestrator/lifecycle.py`

**Behavior:** The thinnest possible Python daemon. Creates a `ClaudeSDKClient` for the orchestrator, sends "heartbeat" every 60 seconds, tracks token usage from `ResultMessage.usage`, writes to `traces/manifest.json`, and detects `COMPACT_NOW` to restart the session.

- [ ] **Step 1: Write lifecycle.py**

```python
"""Orchestrator lifecycle manager — heartbeat, token tracking, session restart.

This is intentionally thin. ALL intelligence lives in the agent (system prompt,
HEARTBEAT.md, skills). ALL logging lives in filesystem hooks. This file does
exactly 4 things:
  1. Creates and maintains a ClaudeSDKClient for the orchestrator
  2. Sends "heartbeat" every 60 seconds
  3. Tracks token usage from ResultMessage → traces/manifest.json
  4. Detects COMPACT_NOW → restarts session fresh
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import signal
import sys
from datetime import datetime, timezone
from pathlib import Path

HEARTBEAT_INTERVAL = 60  # seconds
AGENTS_ROOT = Path(__file__).parent.parent  # mcp-servers/agents/
MANIFEST_PATH = AGENTS_ROOT / "traces" / "manifest.json"
AGENT_CODE = "orc"

logger = logging.getLogger("lifecycle")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)


def read_manifest() -> dict:
    """Read the token manifest. Create if missing."""
    if MANIFEST_PATH.exists():
        return json.loads(MANIFEST_PATH.read_text())
    return {}


def write_manifest(manifest: dict) -> None:
    """Write the token manifest atomically."""
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = MANIFEST_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(manifest, indent=2))
    tmp.rename(MANIFEST_PATH)


def read_session_num() -> int:
    """Read current session number from state file."""
    path = Path(__file__).parent / "state" / f"{AGENT_CODE}_session.txt"
    if path.exists():
        return int(path.read_text().strip())
    return 1


def write_session_num(n: int) -> None:
    """Write session number to state file."""
    path = Path(__file__).parent / "state" / f"{AGENT_CODE}_session.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(str(n))


def reset_iteration() -> None:
    """Reset iteration counter to 0 for a new session."""
    path = Path(__file__).parent / "state" / f"{AGENT_CODE}_iteration.txt"
    path.write_text("0")


def update_manifest_tokens(usage: dict | None) -> None:
    """Accumulate token counts from ResultMessage.usage into manifest."""
    if not usage:
        return
    manifest = read_manifest()
    if AGENT_CODE not in manifest:
        manifest[AGENT_CODE] = {
            "session": read_session_num(),
            "input_tokens": 0,
            "output_tokens": 0,
            "last_updated": None,
        }
    manifest[AGENT_CODE]["input_tokens"] += usage.get("input_tokens", 0)
    manifest[AGENT_CODE]["output_tokens"] += usage.get("output_tokens", 0)
    manifest[AGENT_CODE]["last_updated"] = datetime.now(timezone.utc).isoformat()
    write_manifest(manifest)


async def run_agent() -> None:
    """Main loop: create client, send heartbeats, handle compaction."""
    # Late import so module loads fast even if SDK isn't installed
    from claude_agent_sdk import (
        AssistantMessage,
        ClaudeAgentOptions,
        ClaudeSDKClient,
        ResultMessage,
        TextBlock,
    )

    workspace = Path(__file__).parent

    while True:
        session_num = read_session_num()
        logger.info("Starting session #%d", session_num)

        # Reset manifest token counts for new session
        manifest = read_manifest()
        manifest[AGENT_CODE] = {
            "session": session_num,
            "input_tokens": 0,
            "output_tokens": 0,
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }
        write_manifest(manifest)

        options = ClaudeAgentOptions(
            # No system_prompt= param. SDK reads CLAUDE.md from cwd via setting_sources.
            model=os.environ.get("AGENT_MODEL", "claude-sonnet-4-6"),
            permission_mode="dontAsk",
            allowed_tools=[
                "Bash", "Read", "Write", "Edit", "Glob", "Grep", "Skill",
            ],
            setting_sources=["project"],
            effort="medium",
            max_turns=30,
            max_budget_usd=2.0,
            cwd=str(workspace),
            env={
                "ANTHROPIC_API_KEY": os.environ.get("ANTHROPIC_API_KEY", ""),
                "DATABASE_URL": os.environ.get("DATABASE_URL", ""),
            },
        )

        needs_restart = False

        try:
            async with ClaudeSDKClient(options=options) as client:
                logger.info("Client connected, starting heartbeat loop")

                while not needs_restart:
                    # Send heartbeat
                    await client.query("heartbeat")

                    # Consume response, track tokens
                    async for msg in client.receive_response():
                        if isinstance(msg, ResultMessage):
                            update_manifest_tokens(msg.usage)
                            logger.info(
                                "Heartbeat complete: turns=%d, cost=$%.4f",
                                msg.num_turns,
                                msg.total_cost_usd or 0,
                            )

                            # Check for compaction signal
                            if msg.result and "COMPACT_NOW" in msg.result:
                                logger.info("COMPACT_NOW detected — restarting session")
                                needs_restart = True

                    if needs_restart:
                        break

                    # Wait for next heartbeat
                    await asyncio.sleep(HEARTBEAT_INTERVAL)

        except Exception as e:
            logger.error("Session error: %s", e, exc_info=True)
            # Brief pause before retry to avoid tight error loops
            await asyncio.sleep(5)

        # Prepare for new session
        if needs_restart:
            new_session = session_num + 1
            write_session_num(new_session)
            reset_iteration()
            logger.info("Session #%d ended. Starting session #%d", session_num, new_session)
        else:
            # Unexpected disconnection — retry same session
            logger.warning("Unexpected disconnection. Retrying session #%d in 5s", session_num)
            await asyncio.sleep(5)


async def main() -> None:
    """Entry point with graceful shutdown."""
    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    def handle_signal() -> None:
        logger.info("Shutdown signal received")
        stop_event.set()

    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, handle_signal)

    agent_task = asyncio.create_task(run_agent())

    # Wait for shutdown signal
    await stop_event.wait()
    agent_task.cancel()
    try:
        await agent_task
    except asyncio.CancelledError:
        pass
    logger.info("Lifecycle manager stopped")


if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 2: Verify syntax**

```bash
cd mcp-servers/agents && python3 -c "import ast; ast.parse(open('orchestrator/lifecycle.py').read()); print('OK')"
```

- [ ] **Step 3: Commit**

```bash
git add mcp-servers/agents/orchestrator/lifecycle.py
git commit -m "feat: orchestrator lifecycle manager — heartbeat, token tracking, compaction restart"
```

### Task 8: systemd unit

**Files:**
- Create: `mcp-servers/agents/infra/orchestrator.service`

- [ ] **Step 1: Write systemd unit**

```ini
[Unit]
Description=AI CoS Orchestrator Agent
After=network.target state-mcp.service
Wants=state-mcp.service

[Service]
Type=simple
WorkingDirectory=/opt/agents/orchestrator
ExecStart=/opt/agents/.venv/bin/python3 -m orchestrator.lifecycle
EnvironmentFile=-/opt/agents/.env
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
SyslogIdentifier=orchestrator

# Resource limits
MemoryHigh=512M
MemoryMax=768M

[Install]
WantedBy=multi-user.target
```

- [ ] **Step 2: Commit**

```bash
git add mcp-servers/agents/infra/orchestrator.service
git commit -m "feat: systemd unit for orchestrator lifecycle manager"
```

---

## Chunk 4: Traces Compaction

### Task 9: Traces compaction logic in orchestrator system prompt

**Note:** The actual system prompt content is in the next plan. However, the compaction BEHAVIOR needs to be specified here because it's part of the traces system.

**Files:**
- Create: `mcp-servers/agents/orchestrator/state/COMPACTION_PROTOCOL.md`

This file is read by the orchestrator's system prompt. It defines how the orchestrator manages traces file rotation.

- [ ] **Step 1: Write the compaction protocol**

```markdown
# Traces Compaction Protocol

You (the orchestrator) are responsible for traces file management.

## When to Check
Every 30 heartbeats (iteration % 30 == 0), check the active traces file size:
```
wc -c < "$(cat /opt/agents/traces/active.txt)"
```

## When to Compact
If the active traces file exceeds 20,000 characters:

1. **Summarize:** Read the entire active traces file. Write a 10-20 line summary
   at the TOP of the file under the `## Summary` heading. Include:
   - Date range covered
   - Key events per agent (what happened, what was dispatched)
   - Any errors or notable decisions
   - Leave the raw iteration logs below the summary as-is.

2. **Archive:** Move the current traces file:
   ```
   mv "$(cat /opt/agents/traces/active.txt)" /opt/agents/traces/archive/
   ```

3. **New file:** Create a new traces file and update the pointer:
   ```
   NEW_FILE="traces/$(date -u +%Y%m%d-%H%M).md"
   echo "# Traces — Started $(date -u +%Y-%m-%d\ %H:%M\ UTC)" > "/opt/agents/$NEW_FILE"
   echo "" >> "/opt/agents/$NEW_FILE"
   echo "## Summary" >> "/opt/agents/$NEW_FILE"
   echo "(written on compaction)" >> "/opt/agents/$NEW_FILE"
   echo "" >> "/opt/agents/$NEW_FILE"
   echo "## Iteration Logs" >> "/opt/agents/$NEW_FILE"
   echo "$NEW_FILE" > /opt/agents/traces/active.txt
   ```

4. **Log:** Write your iteration log for this cycle: `'traces compaction: archived old file, started new traces'`

## Manifest Update
You do NOT update the manifest — Python lifecycle.py handles that automatically.
The manifest tracks token usage per agent, which hooks read to trigger session compaction.
These are two different compaction systems:
- **Traces compaction** (this protocol): rotating the shared log file when it gets large
- **Session compaction** (hooks + lifecycle.py): restarting an agent session when its context window fills
```

- [ ] **Step 2: Commit**

```bash
git add mcp-servers/agents/orchestrator/state/COMPACTION_PROTOCOL.md
git commit -m "feat: traces compaction protocol for orchestrator"
```

### Task 10: Checkpoint format specification

**Files:**
- Create: `mcp-servers/agents/orchestrator/state/CHECKPOINT_FORMAT.md`

This file is read by the orchestrator's system prompt. It defines how to write checkpoints before session compaction.

- [ ] **Step 1: Write the checkpoint format spec**

```markdown
# Checkpoint Format

When you receive a COMPACTION REQUIRED message from the UserPromptSubmit hook,
write your checkpoint to `state/orc_checkpoint.md` following this format.

After writing, end your response with the exact word: COMPACT_NOW

## Template

```
# Checkpoint — $orc | Session #{N} | Iteration {M}
*Written: YYYY-MM-DD HH:MM UTC*

## Current State
- Heartbeat interval: 60s
- Active traces file: {path}
- Content Agent status: {session #, last known state}

## Pending Work
- {anything in progress or queued}
- {unprocessed inbox messages}
- {scheduled but not yet triggered tasks}

## Recent Context (last 5 iterations)
- it {N}: {summary}
- it {N-1}: {summary}
- it {N-2}: {summary}
- it {N-3}: {summary}
- it {N-4}: {summary}

## Key Facts to Remember
- {critical state that would be lost without this checkpoint}
- {agent statuses, error states, blocked items}
- {anything from HEARTBEAT.md that's in-flight}
```

## On Session Restart

When you start a new session and `state/orc_checkpoint.md` exists:
1. Read it fully — this was written by your previous self
2. Absorb the state into your working memory
3. Delete the checkpoint file (it's now in your context)
4. Continue from where you left off
5. Log: 'resumed from checkpoint, session #{N}'
```

- [ ] **Step 2: Commit**

```bash
git add mcp-servers/agents/orchestrator/state/CHECKPOINT_FORMAT.md
git commit -m "feat: checkpoint format spec for session compaction"
```

---

## Chunk 5: Deploy Integration

### Task 11: Update deploy.sh for orchestrator

**Files:**
- Modify: `mcp-servers/agents/deploy.sh`

- [ ] **Step 1: Add orchestrator to deploy.sh**

Add orchestrator service installation, enable, restart, and health check alongside the existing state-mcp, web-tools-mcp, and content-agent entries.

Specifically:
- Step 7 (systemd units): add `cp ${REMOTE_DIR}/infra/orchestrator.service /etc/systemd/system/`
- Step 7 (enable): add `orchestrator` to the `systemctl enable` list
- Step 8 (restart): add `systemctl restart orchestrator` after content-agent
- Step 9 (health check): add `orchestrator` to the systemctl agent check loop

- [ ] **Step 2: Test deploy.sh syntax**

```bash
bash -n mcp-servers/agents/deploy.sh
```

- [ ] **Step 3: Commit**

```bash
git add mcp-servers/agents/deploy.sh
git commit -m "feat: add orchestrator to deploy.sh"
```

### Task 12: Ensure traces/ and state/ survive deploy

**Files:**
- Modify: `mcp-servers/agents/deploy.sh` (step 6 — runtime directories)

- [ ] **Step 1: Add traces/ and orchestrator/state/ to runtime directory creation**

In deploy.sh step 6, add:
```bash
ssh root@${DROPLET} "mkdir -p ${REMOTE_DIR}/traces/archive ${REMOTE_DIR}/orchestrator/state"
```

- [ ] **Step 2: Ensure rsync doesn't delete traces/ or state/ on deploy**

Add `--exclude='traces/' --exclude='*/state/'` to the rsync command in step 1, so deploys don't wipe runtime state.

- [ ] **Step 3: Commit**

```bash
git add mcp-servers/agents/deploy.sh
git commit -m "fix: protect traces/ and state/ from rsync deletion during deploy"
```

---

## Dependency Map

```
Task 1 (traces dir)  ──► Task 3 (Stop hook)     ──► Task 6 (settings.json)
Task 2 (state dir)   ──► Task 4 (UserPrompt hook)──► Task 6
                     ──► Task 5 (PreCompact hook) ──► Task 6
                                                      │
Task 7 (lifecycle.py) ◄──────────────────────────────┘
Task 8 (systemd unit) ◄── Task 7
Task 9 (compaction protocol) — standalone (read by system prompt)
Task 10 (checkpoint format) — standalone (read by system prompt)
Task 11 (deploy.sh) ◄── Task 8
Task 12 (deploy protection) ◄── Task 1, Task 2
```

Tasks 1-2 are prerequisites. Tasks 3-6 are the hooks (can be parallelized: 3, 4, 5 in parallel; 6 after all three). Task 7 depends on 6. Tasks 9-10 are standalone documents. Tasks 11-12 are deploy integration.

---

## Verification Checklist

After all tasks complete:

- [ ] `orchestrator/lifecycle.py` passes syntax check
- [ ] All three hooks are executable and produce expected output when tested manually
- [ ] `settings.json` registers all three hooks
- [ ] `traces/manifest.json` exists with initial schema
- [ ] `traces/active.txt` points to a valid traces file
- [ ] `orchestrator/state/` has session and iteration counter files
- [ ] `deploy.sh` includes orchestrator in install/enable/restart/health
- [ ] `deploy.sh` protects `traces/` and `*/state/` from rsync deletion
- [ ] `COMPACTION_PROTOCOL.md` and `CHECKPOINT_FORMAT.md` exist for system prompt reference

**NOT verified in this plan (deferred to next plan):**
- Orchestrator system prompt (references COMPACTION_PROTOCOL.md and CHECKPOINT_FORMAT.md)
- HEARTBEAT.md content
- @tool bridge to content agent
- Content agent hooks (same pattern, different AGENT code)
- E2E test on droplet
