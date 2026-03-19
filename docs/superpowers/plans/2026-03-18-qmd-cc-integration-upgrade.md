# QMD CC Integration Upgrade — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make QMD usage in Claude Code automatic and unavoidable via hooks, replacing the unreliable CLAUDE.md soft-triggers that depend on LLM discipline.

**Architecture:** Three hooks (SessionStart, UserPromptSubmit, PostToolUseFailure) that run QMD queries as shell scripts and inject results as `additionalContext`. The LLM never needs to "remember" to use QMD — it receives relevant context automatically before it even sees the prompt.

**Tech Stack:** Shell scripts (bash), `qmd` CLI, Claude Code hooks API (settings.json)

---

## Problem Statement

QMD has 5 automatic triggers defined in `~/.claude/CLAUDE.md`:

1. On encountering an error → search past resolutions
2. Before planning multi-step work → search prior attempts
3. Before creating memories → check for duplicates
4. On 2+ tool failures → search for workarounds
5. First visit to a project in a session → pull cross-project context

**None of these fire reliably.** They are LLM instructions competing with dozens of other CLAUDE.md rules. In practice, QMD is used ~0% of sessions unless the user explicitly asks. This has been confirmed across multiple sessions.

## Current QMD Infrastructure (What Exists)

| Component | Where | What It Does | Reliability |
|-----------|-------|-------------|-------------|
| QMD plugin | `~/.claude/plugins/cache/qmd/qmd/0.1.0/` | Provides MCP tools (query, get, multi_get, status) | Works |
| QMD MCP server | Plugin-registered, stdio transport | Exposes tools to CC | Works |
| SessionStart `qmd update` | `~/.claude/settings.json` (global hook) | Re-indexes all 11 collections on session start | Works |
| Daily reindex | `~/Library/LaunchAgents/com.qmd.reindex.plist` at 6:03 AM | preprocess-jsonl → qmd update → qmd embed | Works |
| CLAUDE.md triggers | `~/.claude/CLAUDE.md` "QMD — Proactive Knowledge Search" section | LLM instructions for when to search | **Does not work** |
| Embedding backlog | 334 docs currently unembedded | Degrades vec/hyde search | Needs manual `qmd embed` |

## What This Plan Builds

| Hook | Event | What It Does |
|------|-------|-------------|
| **qmd-context-enrichment.sh** | SessionStart (startup) | Queries QMD for project-specific context + recent patterns, injects results |
| **qmd-prompt-enrichment.sh** | UserPromptSubmit | Analyzes prompt for error/planning/tool keywords, queries QMD, injects relevant history |
| **qmd-failure-search.sh** | PostToolUseFailure | Counts consecutive failures, on 2+ searches QMD for workarounds |

## File Structure

```
~/.claude/hooks/qmd/
├── qmd-context-enrichment.sh    # SessionStart hook
├── qmd-prompt-enrichment.sh     # UserPromptSubmit hook
├── qmd-failure-search.sh        # PostToolUseFailure hook
└── state/                       # Runtime state (gitignored)
    ├── last-project.txt         # Track project for first-visit detection
    └── failure-counter.json     # Track consecutive failures per tool
```

Changes to:
- `~/.claude/settings.json` — add 3 hook entries
- `~/.claude/CLAUDE.md` — slim down QMD section (hooks handle proactive triggers, keep "how to search" guidance)

---

### Task 1: SessionStart — Project Context Enrichment

**Files:**
- Create: `~/.claude/hooks/qmd/qmd-context-enrichment.sh`
- Create: `~/.claude/hooks/qmd/state/` (directory)
- Modify: `~/.claude/settings.json` (add SessionStart hook)

**What it does:** On session startup, query QMD for project-relevant context from `cc-memories` and `project-claude-mds`. If this is the first visit to this project (different `$CLAUDE_PROJECT_DIR` than last session), also search `conversations` for recent work in this project.

- [ ] **Step 1: Create hook directory**

```bash
mkdir -p ~/.claude/hooks/qmd/state
```

- [ ] **Step 2: Write the SessionStart hook script**

```bash
# ~/.claude/hooks/qmd/qmd-context-enrichment.sh
#!/bin/bash
# QMD SessionStart hook: inject project context from past sessions
# Outputs to stdout (additionalContext for CC)

set -e

QMD="$HOME/.nvm/versions/node/v24.12.0/bin/qmd"
STATE_DIR="$HOME/.claude/hooks/qmd/state"
LAST_PROJECT_FILE="$STATE_DIR/last-project.txt"
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
PROJECT_NAME=$(basename "$PROJECT_DIR")

# Ensure state dir
mkdir -p "$STATE_DIR"

# Detect first visit
FIRST_VISIT=false
if [ -f "$LAST_PROJECT_FILE" ]; then
  LAST_PROJECT=$(cat "$LAST_PROJECT_FILE")
  if [ "$LAST_PROJECT" != "$PROJECT_DIR" ]; then
    FIRST_VISIT=true
  fi
else
  FIRST_VISIT=true
fi
echo "$PROJECT_DIR" > "$LAST_PROJECT_FILE"

# Query 1: Project-specific memories and patterns
MEMORY_RESULTS=$("$QMD" query "$PROJECT_NAME" \
  -c cc-memories \
  -n 3 \
  --min-score 0.3 \
  --files 2>/dev/null || echo "")

# Query 2: First-visit — recent conversations about this project
CONV_RESULTS=""
if [ "$FIRST_VISIT" = true ]; then
  CONV_RESULTS=$("$QMD" query "$PROJECT_NAME" \
    -c conversations \
    -n 3 \
    --min-score 0.3 \
    --files 2>/dev/null || echo "")
fi

# Build output
OUTPUT=""
if [ -n "$MEMORY_RESULTS" ] || [ -n "$CONV_RESULTS" ]; then
  OUTPUT="QMD context for $PROJECT_NAME:"
  if [ -n "$MEMORY_RESULTS" ]; then
    OUTPUT="$OUTPUT\n\nRelevant memories:\n$MEMORY_RESULTS"
  fi
  if [ -n "$CONV_RESULTS" ]; then
    OUTPUT="$OUTPUT\n\nRecent conversations:\n$CONV_RESULTS"
  fi
fi

# Output (stdout = additionalContext in CC hooks)
if [ -n "$OUTPUT" ]; then
  echo -e "$OUTPUT"
fi

exit 0
```

- [ ] **Step 3: Make executable and test standalone**

```bash
chmod +x ~/.claude/hooks/qmd/qmd-context-enrichment.sh
CLAUDE_PROJECT_DIR="$HOME/Claude Projects/Aakash AI CoS CC ADK" ~/.claude/hooks/qmd/qmd-context-enrichment.sh
```

Expected: Some output with memory/conversation file paths, or empty if no matches.

- [ ] **Step 4: Register in global settings.json**

Add to `~/.claude/settings.json` under `hooks.SessionStart` array:

```json
{
  "matcher": "startup",
  "hooks": [
    {
      "type": "command",
      "command": "$HOME/.claude/hooks/qmd/qmd-context-enrichment.sh"
    }
  ]
}
```

- [ ] **Step 5: Commit**

```bash
cd ~/.claude && git add hooks/qmd/qmd-context-enrichment.sh settings.json
git commit -m "feat: QMD SessionStart hook for project context enrichment"
```

---

### Task 2: UserPromptSubmit — Every-Prompt QMD Enrichment

**Files:**
- Create: `~/.claude/hooks/qmd/qmd-prompt-enrichment.sh`
- Modify: `~/.claude/settings.json` (add UserPromptSubmit hook)

**What it does:** Fires on EVERY user prompt. Takes the raw prompt text, uses it as a QMD search query against all relevant collections, and injects any matching results as additionalContext. No pattern matching, no keyword detection, no filtering by intent. Every prompt gets searched. QMD's own `--min-score` handles noise — low-relevance prompts simply return no results.

**Design rationale:** Pattern matching was the original plan but has the same fragility as CLAUDE.md soft-triggers — it trades "LLM forgetting" for "regex missing." The only foolproof approach is to search on every prompt and let QMD's scoring decide relevance.

- [ ] **Step 1: Write the UserPromptSubmit hook script**

```bash
#!/bin/bash
# ~/.claude/hooks/qmd/qmd-prompt-enrichment.sh
# QMD UserPromptSubmit hook: search every prompt against past context
# Reads JSON from stdin: {"user_prompt": "...", "session_id": "...", ...}
# Outputs to stdout (additionalContext)
# No pattern matching — fires on every prompt, QMD scoring handles relevance

QMD="$HOME/.nvm/versions/node/v24.12.0/bin/qmd"

# Bail if qmd not installed
[ -x "$QMD" ] || exit 0

# Read stdin (UserPromptSubmit provides JSON)
INPUT=$(cat)
PROMPT=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('user_prompt',''))" 2>/dev/null || echo "")

# Skip very short prompts (greetings, "yes", "no", "ok", etc.)
if [ ${#PROMPT} -lt 15 ]; then
  exit 0
fi

# Truncate to first 200 chars for query (longer prompts = slower search, diminishing returns)
QUERY=$(echo "$PROMPT" | head -c 200)

# Search across all relevant collections
# lex-only for speed — searches conversations, memories, traces, and project docs
RESULTS=$("$QMD" search "$QUERY" \
  -c conversations \
  -c cc-memories \
  -c traces-learnings \
  -c project-claude-mds \
  -n 5 \
  --min-score 0.4 \
  --files \
  2>/dev/null | head -c 2000 || echo "")

# Output results if any (QMD scoring filters irrelevant matches)
if [ -n "$RESULTS" ] && [ "$RESULTS" != "No results found" ]; then
  echo "QMD context (auto-searched from your prompt):"
  echo "$RESULTS"
  echo ""
  echo "Use qmd get <path> or mcp__plugin_qmd_qmd__get to read any of these if relevant."
fi

exit 0
```

- [ ] **Step 2: Make executable and test with various prompts**

```bash
chmod +x ~/.claude/hooks/qmd/qmd-prompt-enrichment.sh
```

- [ ] **Step 3: Test — error-like prompt**

```bash
echo '{"user_prompt": "fix the broken deployment pipeline on the droplet"}' | ~/.claude/hooks/qmd/qmd-prompt-enrichment.sh
```

Expected: File paths from conversations/traces about deployment issues.

- [ ] **Step 4: Test — planning prompt**

```bash
echo '{"user_prompt": "build a new sync agent for Notion bidirectional updates"}' | ~/.claude/hooks/qmd/qmd-prompt-enrichment.sh
```

Expected: File paths from conversations/memories about sync agent work.

- [ ] **Step 5: Test — casual/short prompt (should be silent)**

```bash
echo '{"user_prompt": "yes do it"}' | ~/.claude/hooks/qmd/qmd-prompt-enrichment.sh
```

Expected: Empty output (prompt < 15 chars).

- [ ] **Step 6: Test — unrelated prompt (should return empty or low-score filtered)**

```bash
echo '{"user_prompt": "what is the capital of France"}' | ~/.claude/hooks/qmd/qmd-prompt-enrichment.sh
```

Expected: Empty or no output (min-score 0.4 filters irrelevant matches).

- [ ] **Step 7: Register in global settings.json**

Add to `~/.claude/settings.json` under `hooks.UserPromptSubmit` (create array if not exists):

```json
{
  "hooks": [
    {
      "type": "command",
      "command": "$HOME/.claude/hooks/qmd/qmd-prompt-enrichment.sh"
    }
  ]
}
```

- [ ] **Step 6: Commit**

```bash
cd ~/.claude && git add hooks/qmd/qmd-prompt-enrichment.sh settings.json
git commit -m "feat: QMD UserPromptSubmit hook for prompt-aware context injection"
```

---

### Task 3: PostToolUseFailure — Failure Counter + QMD Search

**Files:**
- Create: `~/.claude/hooks/qmd/qmd-failure-search.sh`
- Modify: `~/.claude/settings.json` (add/modify PostToolUseFailure hook)

**What it does:** Tracks consecutive tool failures per session. On the 2nd+ failure, queries QMD for past workarounds for that tool/error pattern.

**Note:** This project already has a PostToolUseFailure hook (LEARNINGS.md prompt). This hook should coexist — it adds QMD context, the existing one reminds about LEARNINGS.md logging.

- [ ] **Step 1: Write the PostToolUseFailure hook script**

```bash
# ~/.claude/hooks/qmd/qmd-failure-search.sh
#!/bin/bash
# QMD PostToolUseFailure hook: on 2+ failures, search for past workarounds
# Reads JSON from stdin: {"tool_name": "...", "tool_input": {...}, "error": "..."}

set -e

QMD="$HOME/.nvm/versions/node/v24.12.0/bin/qmd"
STATE_DIR="$HOME/.claude/hooks/qmd/state"
COUNTER_FILE="$STATE_DIR/failure-counter.txt"

mkdir -p "$STATE_DIR"

# Read stdin
INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_name','unknown'))" 2>/dev/null || echo "unknown")
ERROR=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('error',d.get('tool_response',''))[:200])" 2>/dev/null || echo "")

# Increment failure counter
COUNT=0
if [ -f "$COUNTER_FILE" ]; then
  COUNT=$(cat "$COUNTER_FILE" 2>/dev/null || echo "0")
fi
COUNT=$((COUNT + 1))
echo "$COUNT" > "$COUNTER_FILE"

# Only search on 2+ failures
if [ "$COUNT" -lt 2 ]; then
  exit 0
fi

# Build search query from tool name + error snippet
QUERY="$TOOL_NAME $ERROR"
QUERY=$(echo "$QUERY" | head -c 200)

RESULTS=$("$QMD" search "$QUERY" \
  -c conversations,traces-learnings \
  -n 2 \
  --min-score 0.3 \
  2>/dev/null | head -c 1500 || echo "")

if [ -n "$RESULTS" ] && [ "$RESULTS" != "No results found" ]; then
  echo "QMD (tool failure #$COUNT): Past workarounds for $TOOL_NAME failures:"
  echo "$RESULTS"
fi

exit 0
```

- [ ] **Step 2: Make executable**

```bash
chmod +x ~/.claude/hooks/qmd/qmd-failure-search.sh
```

- [ ] **Step 3: Add counter reset to SessionStart**

The failure counter should reset at session start. Add to `qmd-context-enrichment.sh`:

```bash
# Reset failure counter at session start
echo "0" > "$STATE_DIR/failure-counter.txt"
```

- [ ] **Step 4: Register in global settings.json**

Add to `~/.claude/settings.json` under `hooks.PostToolUseFailure` (the existing LEARNINGS prompt hook stays):

```json
{
  "matcher": "Bash|Edit|Write",
  "hooks": [
    {
      "type": "command",
      "command": "$HOME/.claude/hooks/qmd/qmd-failure-search.sh"
    }
  ]
}
```

- [ ] **Step 5: Commit**

```bash
cd ~/.claude && git add hooks/qmd/ settings.json
git commit -m "feat: QMD PostToolUseFailure hook for automatic workaround search"
```

---

### Task 4: Slim Down CLAUDE.md QMD Section

**Files:**
- Modify: `~/.claude/CLAUDE.md`

**What it does:** The existing "QMD — Proactive Knowledge Search" section in global CLAUDE.md has 5 automatic triggers that are now handled by hooks. Replace the trigger section with a note that hooks handle it. Keep the "how to search effectively" and "what NOT to do" subsections — those are still useful for on-demand QMD usage.

- [ ] **Step 1: Replace the automatic triggers section**

Replace the "When to search (automatic triggers)" subsection with:

```markdown
### Automatic triggers (handled by hooks — no action needed)

These are enforced by shell hooks in `~/.claude/hooks/qmd/`, not by LLM discipline:
- **SessionStart:** Project context enrichment (memories + recent conversations)
- **UserPromptSubmit:** Error/planning/memory keyword detection → relevant history injection
- **PostToolUseFailure:** 2+ consecutive failures → workaround search

You receive QMD results as additionalContext automatically. Use them to inform your response.
```

- [ ] **Step 2: Verify remaining sections are intact**

Keep these subsections unchanged:
- "How to search effectively" (combine lex+vec, use intent, use minScore)
- "What NOT to do"

- [ ] **Step 3: Commit**

```bash
cd ~/.claude && git add CLAUDE.md
git commit -m "docs: slim QMD section — hooks now handle automatic triggers"
```

---

### Task 5: Run `qmd embed` to Clear Backlog

**Files:** None (runtime operation)

- [ ] **Step 1: Run embedding**

```bash
qmd embed
```

Expected: Processes 334 documents. Takes ~5-15 minutes depending on model loading.

- [ ] **Step 2: Verify**

```bash
qmd status
```

Expected: `needsEmbedding: 0`

---

### Task 6: Integration Test

- [ ] **Step 1: Start a new CC session in this project**

```bash
cd ~/Claude\ Projects/Aakash\ AI\ CoS\ CC\ ADK && claude
```

- [ ] **Step 2: Verify SessionStart hook output**

Expected: See `QMD context for Aakash AI CoS CC ADK:` in session startup output with memory/conversation file paths.

- [ ] **Step 3: Test error prompt**

Type: "the deployment pipeline is broken and timing out"

Expected: See `QMD (error resolution):` in additionalContext with past conversations about deployment issues.

- [ ] **Step 4: Test planning prompt**

Type: "let's build a new notification system"

Expected: See `QMD (prior work and lessons):` with past conversations about similar work.

- [ ] **Step 5: Test no-match prompt**

Type: "what's the weather"

Expected: No QMD injection (fast, silent).

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| QMD binary not found | Hook fails silently | Path check at top of each script. Graceful `exit 0` on missing binary. |
| Noisy/irrelevant results on vague prompts | Clutters context window | `--min-score 0.4` filter + 2KB output cap + `--files` mode (paths only, not full content). LLM can ignore if not relevant. |
| Hook JSON parsing fails | Silent failure | Python3 fallback + `|| echo ""` safety |
| Counter file grows stale across sessions | False positives on failure search | Reset counter in SessionStart hook |
| Short prompts ("yes", "ok", "do it") searched uselessly | Wasted cycles | Skip prompts < 15 chars |

## What This Does NOT Cover

- **Memory dedup check before creating memories** — This is hard to do in a hook because memory creation happens mid-conversation via Write tool, not via a specific prompt pattern. Would need a PreToolUse hook on Write matching `memory/*.md` paths. Can be added later.
- **Vec/hyde search in hooks** — Deliberately excluded for speed. On-demand `/ask` queries still use full hybrid search.
- **QMD embed automation** — The daily LaunchAgent handles this. The 334-doc backlog is a one-time cleanup (Task 5).
