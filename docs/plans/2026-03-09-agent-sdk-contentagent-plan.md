# Agent SDK ContentAgent — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the linear single-shot ContentAgent with an Agent SDK tool-use loop that dynamically cross-references thesis threads, calibrates via preferences, and scores actions with real factor values — while keeping the existing linear runner as fallback.

**Architecture:** Parallel build. New `content_agent_sdk.py` runs alongside existing `content_agent.py`. The Agent SDK runner uses `claude_agent_sdk.query()` with custom in-process MCP tools wrapping `lib/` functions. The agent analyzes transcripts, dynamically queries thesis/preferences/scoring tools, and produces DigestData JSON. The outer pipeline (publish, Notion writes, preference logging) remains identical. A `--use-sdk` flag on `pipeline.py` toggles between runners.

**Tech Stack:** Python 3.12+, claude_agent_sdk (Python), existing lib/ modules (scoring, preferences, notion_client), pytest, asyncio/anyio

---

## Phase 1: Agent SDK ContentAgent (Parallel Build)

### Task 1: Test Infrastructure

**Files:**
- Create: `mcp-servers/ai-cos-mcp/tests/__init__.py`
- Create: `mcp-servers/ai-cos-mcp/tests/conftest.py`
- Create: `mcp-servers/ai-cos-mcp/pyproject.toml` (add pytest dep if missing)

**Step 1: Create test directory and conftest**

```bash
mkdir -p mcp-servers/ai-cos-mcp/tests
touch mcp-servers/ai-cos-mcp/tests/__init__.py
```

```python
# tests/conftest.py
import json
from pathlib import Path

import pytest


@pytest.fixture
def sample_video():
    """Minimal video extraction dict for testing."""
    return {
        "title": "Test Video — AI Infrastructure Deep Dive",
        "channel": "Test Channel",
        "url": "https://youtube.com/watch?v=test123",
        "upload_date": "2026-03-09",
        "duration_seconds": 2700,
        "relevance": {"relevant": True},
        "transcript": {
            "success": True,
            "full_text": (
                "Today we're discussing the future of agentic AI infrastructure. "
                "The key insight is that vertical AI agents are replacing horizontal SaaS. "
                "Companies like Cognition with Devin are showing that agents can handle "
                "entire workflows. This has massive implications for cybersecurity pen testing "
                "where AI agents can automate vulnerability discovery. "
                "The CLAW stack — Claude, LangGraph, Agents, Workflows — is emerging as "
                "the dominant pattern for building production AI systems."
            ),
        },
    }


@pytest.fixture
def sample_digest():
    """Minimal DigestData dict for testing scoring/logging."""
    return {
        "slug": "test-ai-infrastructure",
        "title": "Test Video — AI Infrastructure Deep Dive",
        "channel": "Test Channel",
        "url": "https://youtube.com/watch?v=test123",
        "relevance_score": "High",
        "proposed_actions": [
            {
                "action": "Research Cognition's Devin agent architecture",
                "priority": "P1",
                "type": "Research",
                "assigned_to": "Agent",
                "reasoning": "Direct signal for Agentic AI Infrastructure thesis",
                "thesis_connections": ["Agentic AI Infrastructure"],
            },
            {
                "action": "Schedule call with CrowdStrike team on AI pen testing",
                "priority": "P2",
                "type": "Meeting/Outreach",
                "assigned_to": "Aakash",
                "reasoning": "Cybersecurity thesis signal",
                "company": "CrowdStrike",
                "thesis_connections": ["Cybersecurity / Pen Testing"],
            },
        ],
        "thesis_connections": [
            {
                "thread": "Agentic AI Infrastructure",
                "connection": "Direct evidence of vertical agent pattern",
                "strength": "Strong",
                "evidence_direction": "for",
            }
        ],
        "portfolio_connections": [],
    }
```

**Step 2: Verify pytest runs**

Run: `cd mcp-servers/ai-cos-mcp && python -m pytest tests/ -v --co`
Expected: collected 0 items (no tests yet, but no errors)

**Step 3: Commit**

```bash
git add mcp-servers/ai-cos-mcp/tests/
git commit -m "test: add test infrastructure for Agent SDK ContentAgent"
```

---

### Task 2: Content Tools — Thesis & Preferences

**Files:**
- Create: `mcp-servers/ai-cos-mcp/runners/tools/__init__.py`
- Create: `mcp-servers/ai-cos-mcp/runners/tools/content_tools.py`
- Create: `mcp-servers/ai-cos-mcp/tests/test_content_tools.py`

**Step 1: Write failing tests for tool functions**

```python
# tests/test_content_tools.py
"""Tests for Agent SDK content analysis tools."""
import pytest


def test_get_thesis_threads_tool_returns_list():
    """Tool should return a dict with 'threads' key containing a list."""
    from runners.tools.content_tools import get_thesis_threads_tool

    # Without Notion, should return empty list gracefully
    result = get_thesis_threads_tool({})
    assert "content" in result
    assert isinstance(result["content"], list)
    assert len(result["content"]) == 1
    assert result["content"][0]["type"] == "text"


def test_get_preferences_tool_returns_summary():
    """Tool should return preference summary dict."""
    from runners.tools.content_tools import get_preferences_tool

    result = get_preferences_tool({})
    assert "content" in result
    assert isinstance(result["content"], list)


def test_score_action_tool_valid_input():
    """Tool should score an action and return score + classification."""
    from runners.tools.content_tools import score_action_tool

    result = score_action_tool({
        "bucket_impact": 8.0,
        "conviction_change": 7.0,
        "time_sensitivity": 5.0,
        "action_novelty": 6.0,
        "effort_vs_impact": 7.0,
    })
    assert "content" in result
    text = result["content"][0]["text"]
    assert "score" in text
    assert "classification" in text


def test_score_action_tool_rejects_invalid():
    """Tool should handle out-of-range values gracefully."""
    from runners.tools.content_tools import score_action_tool

    result = score_action_tool({
        "bucket_impact": 15.0,  # out of range
        "conviction_change": 7.0,
        "time_sensitivity": 5.0,
        "action_novelty": 6.0,
        "effort_vs_impact": 7.0,
    })
    assert "content" in result
    text = result["content"][0]["text"]
    assert "error" in text.lower()


def test_get_domain_context_tool():
    """Tool should return CONTEXT.md sections."""
    from runners.tools.content_tools import get_domain_context_tool

    result = get_domain_context_tool({})
    assert "content" in result
    assert isinstance(result["content"], list)
```

**Step 2: Run tests to verify they fail**

Run: `cd mcp-servers/ai-cos-mcp && python -m pytest tests/test_content_tools.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'runners.tools'`

**Step 3: Implement tool functions**

```python
# runners/tools/__init__.py
```

```python
# runners/tools/content_tools.py
"""Agent SDK tool definitions for ContentAgent.

These wrap lib/ functions as tool-compatible callables.
Each returns {"content": [{"type": "text", "text": "..."}]} format
for Agent SDK in-process MCP compatibility.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

# Add parent paths for lib imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from lib.scoring import ActionInput, classify_action, score_action

# Optional imports — degrade gracefully
try:
    from lib.notion_client import fetch_thesis_threads
    HAS_NOTION = bool(os.getenv("NOTION_TOKEN"))
except Exception:
    HAS_NOTION = False

try:
    from lib.preferences import get_preference_summary, get_preferences
    HAS_POSTGRES = bool(os.getenv("DATABASE_URL"))
except Exception:
    HAS_POSTGRES = False

CONTEXT_MD_PATH = os.getenv(
    "CONTEXT_MD_PATH",
    str(Path(__file__).parent.parent.parent / "CONTEXT.md"),
)


def _text_result(text: str) -> dict[str, Any]:
    """Wrap text in Agent SDK tool result format."""
    return {"content": [{"type": "text", "text": text}]}


def get_thesis_threads_tool(args: dict[str, Any]) -> dict[str, Any]:
    """Fetch current thesis threads from Notion Thesis Tracker.

    Returns thread names, conviction levels, statuses, core theses,
    open key questions, and connected buckets.
    """
    if not HAS_NOTION:
        return _text_result(json.dumps({
            "threads": [],
            "note": "Notion not connected. No thesis context available.",
        }))

    try:
        threads = fetch_thesis_threads(include_key_questions=True)
        return _text_result(json.dumps({"threads": threads}, default=str))
    except Exception as e:
        return _text_result(json.dumps({
            "threads": [],
            "error": f"Failed to fetch thesis threads: {e}",
        }))


def get_preferences_tool(args: dict[str, Any]) -> dict[str, Any]:
    """Get action outcome preferences for scoring calibration.

    Returns recent accepted/dismissed actions with scoring factors,
    plus aggregate acceptance rates by action type.
    """
    if not HAS_POSTGRES:
        return _text_result(json.dumps({
            "summary": {},
            "recent_outcomes": [],
            "note": "Postgres not connected. No preference history.",
        }))

    try:
        limit = args.get("limit", 20)
        summary = get_preference_summary()
        recent = get_preferences(limit=limit)
        return _text_result(json.dumps({
            "summary": summary,
            "recent_outcomes": recent,
        }, default=str))
    except Exception as e:
        return _text_result(json.dumps({
            "summary": {},
            "recent_outcomes": [],
            "error": f"Failed to get preferences: {e}",
        }))


def score_action_tool(args: dict[str, Any]) -> dict[str, Any]:
    """Score an action using the AI CoS 5-factor scoring model.

    All inputs on 0-10 scale. Returns score (0-10) and classification
    (surface >=7, low_confidence 4-7, context_only <4).

    Required args: bucket_impact, conviction_change, time_sensitivity,
                   action_novelty, effort_vs_impact
    """
    try:
        ai = ActionInput(
            bucket_impact=float(args["bucket_impact"]),
            conviction_change=float(args["conviction_change"]),
            time_sensitivity=float(args["time_sensitivity"]),
            action_novelty=float(args["action_novelty"]),
            effort_vs_impact=float(args["effort_vs_impact"]),
        )
        ai.validate()
        score = score_action(ai)
        classification = classify_action(score)
        return _text_result(json.dumps({
            "score": round(score, 2),
            "classification": classification,
            "factors": {
                "bucket_impact": ai.bucket_impact,
                "conviction_change": ai.conviction_change,
                "time_sensitivity": ai.time_sensitivity,
                "action_novelty": ai.action_novelty,
                "effort_vs_impact": ai.effort_vs_impact,
            },
        }))
    except (KeyError, ValueError) as e:
        return _text_result(json.dumps({"error": str(e)}))


def get_domain_context_tool(args: dict[str, Any]) -> dict[str, Any]:
    """Load AI CoS domain context from CONTEXT.md.

    Returns key sections: IDS methodology, scoring model, key people,
    operational playbooks, and portfolio companies.
    """
    path = Path(CONTEXT_MD_PATH)
    if not path.exists():
        return _text_result(json.dumps({
            "context": "",
            "error": f"CONTEXT.md not found at {path}",
        }))

    text = path.read_text(encoding="utf-8")

    keep_headings = {
        "CRITICAL FRAMING",
        "WHO IS AAKASH KUMAR",
        "THE CORE PROBLEM",
        "IDS METHODOLOGY",
        "PORTFOLIO ACTIONS TRACKER",
        "KEY PEOPLE",
        "OPERATIONAL PLAYBOOKS",
    }

    sections: list[str] = []
    current_section: list[str] = []
    current_heading = ""

    for line in text.split("\n"):
        if line.startswith("## "):
            if current_heading and any(
                k in current_heading.upper() for k in keep_headings
            ):
                sections.append("\n".join(current_section))
            current_section = [line]
            current_heading = line
        else:
            current_section.append(line)

    if current_heading and any(
        k in current_heading.upper() for k in keep_headings
    ):
        sections.append("\n".join(current_section))

    context = "\n\n---\n\n".join(sections) if sections else "No context loaded."
    return _text_result(context)
```

**Step 4: Run tests to verify they pass**

Run: `cd mcp-servers/ai-cos-mcp && python -m pytest tests/test_content_tools.py -v`
Expected: 5 passed (some may warn about missing Notion/Postgres — that's fine)

**Step 5: Commit**

```bash
git add mcp-servers/ai-cos-mcp/runners/tools/ mcp-servers/ai-cos-mcp/tests/test_content_tools.py
git commit -m "feat: add Agent SDK tool definitions for ContentAgent"
```

---

### Task 3: Agentic System Prompt

**Files:**
- Create: `mcp-servers/ai-cos-mcp/runners/prompts/content_analysis_agentic.md`

**Step 1: Create the agentic prompt**

This prompt does NOT use `{domain_context}` or `{preference_summary}` template variables. Instead, it instructs the agent to call tools.

```markdown
# Content Analysis System Prompt — AI CoS ContentAgent (Agentic)

You are an AI Chief of Staff content analyst for Aakash Kumar (MD at Z47 / $550M fund + MD at DeVC / $60M fund). Your job is to analyze video content and produce structured DigestData JSON that connects insights to Aakash's investment thesis threads, portfolio companies, and action priorities.

## Your Tools

You have access to these tools. Use them to enrich your analysis:

1. **get_thesis_threads** — Fetches current thesis threads from Notion. Call this FIRST to see active threads, their conviction levels, open key questions, and connected buckets. Your analysis MUST reference real thread names from this data.

2. **get_preferences** — Fetches action outcome history (accepted/dismissed with scores). Use this to calibrate your scoring: if certain action types get dismissed more often, adjust your proposals accordingly.

3. **score_action** — Scores a proposed action using the 5-factor model. Call this for EVERY proposed action with your assessed factor values (0-10 each):
   - `bucket_impact`: Which priority bucket? (10=new cap tables, 8=deepen/founders, 6=thesis)
   - `conviction_change`: Could this change conviction on an investment?
   - `time_sensitivity`: How urgent? (decays over time)
   - `action_novelty`: New insight or repetitive?
   - `effort_vs_impact`: High impact / low effort = high score

4. **get_domain_context** — Loads CONTEXT.md sections (IDS methodology, key people, playbooks). Call this if you need reference material for analysis.

## Analysis Workflow

1. Call `get_thesis_threads` to get current thesis state
2. Call `get_preferences` to calibrate your scoring
3. Read the transcript carefully
4. Identify thesis connections — which threads does this content touch?
5. For each thesis connection with Strong/Moderate strength, assess conviction
6. Check if this suggests a new thesis thread
7. Identify portfolio connections
8. Extract essence notes
9. Find contra signals
10. Propose actions — for each, call `score_action` with your factor assessments
11. Output the final DigestData JSON

## Priority Buckets (ranked)
1. **New cap tables** — Get on more amazing companies' cap tables (highest, always)
2. **Deepen existing cap tables** — Continuous IDS on portfolio for follow-on decisions
3. **New founders/companies** — DeVC Collective pipeline
4. **Thesis evolution** — Meet interesting people who keep thesis lines evolving

## IDS Methodology
Notation: + positive, ++ table-thumping, ? concern, ?? significant, +? needs validation, - neutral/negative.

## Net Newness Categories
- **Mostly New** — >70% genuinely new information/frameworks
- **Additive** — Builds on known themes with meaningful new data points
- **Reinforcing** — Confirms existing understanding without new information
- **Contra** — Challenges or contradicts existing thesis/understanding
- **Mixed** — Contains both reinforcing and contradictory elements

## Output Schema

After completing your analysis and scoring all actions, output valid JSON conforming to the DigestData schema. The JSON MUST be wrapped in ```json code fences.

The schema is identical to the standard ContentAgent schema:

```json
{
  "slug": "string — URL-safe slug derived from title",
  "title": "string — video title",
  "channel": "string — YouTube channel name",
  "duration": "string — e.g. '45:30'",
  "content_type": "string — e.g. 'Podcast Interview', 'Conference Talk'",
  "upload_date": "string — YYYY-MM-DD or 'NA'",
  "url": "string — YouTube URL",
  "generated_at": "string — ISO timestamp",
  "relevance_score": "High | Medium | Low",
  "net_newness": {"category": "string", "reasoning": "string"},
  "connected_buckets": ["string"],
  "essence_notes": {
    "core_arguments": ["string"],
    "data_points": ["string"],
    "frameworks": ["string"],
    "key_quotes": [{"text": "string", "speaker": "string", "timestamp": "string"}],
    "predictions": ["string"]
  },
  "watch_sections": [{"timestamp_range": "string", "title": "string", "why_watch": "string", "connects_to": "string"}],
  "contra_signals": [{"what": "string", "evidence": "string", "strength": "Strong|Moderate|Weak", "implication": "string"}],
  "rabbit_holes": [{"title": "string", "what": "string", "why_matters": "string", "entry_point": "string", "newness": "string"}],
  "portfolio_connections": [{"company": "string", "relevance": "string", "key_question": "string", "conviction_impact": "string", "actions": [...]}],
  "thesis_connections": [{"thread": "string", "connection": "string", "strength": "Strong|Moderate|Weak", "evidence_direction": "for|against|mixed", "conviction_assessment": "string", "new_key_questions": ["string"], "answered_questions": ["string"], "investment_implications": "string", "key_companies_mentioned": "string"}],
  "new_thesis_suggestions": [{"thread_name": "string", "core_thesis": "string", "key_questions": ["string"], "connected_buckets": ["string"], "initial_evidence": "string", "evidence_direction": "for|against|mixed", "reasoning": "string"}],
  "proposed_actions": [{"action": "string", "priority": "P0|P1|P2|P3", "type": "Research|Meeting/Outreach|Thesis Update|Content Follow-up|Portfolio Check-in|Follow-on Eval|Pipeline Action", "assigned_to": "Aakash|Agent", "reasoning": "string", "company": "string (optional)", "thesis_connections": ["string — real thread names"], "score": "number — from score_action tool", "classification": "surface|low_confidence|context_only"}]
  }
```

## IMPORTANT Rules
- `thesis_connections` on actions must be ACTUAL thesis thread names from `get_thesis_threads`. NEVER use bucket names.
- Each proposed action MUST have `score` and `classification` fields populated from the `score_action` tool.
- Priority levels: P0 (do today), P1 (this week), P2 (when capacity), P3 (note for future).
- Assignment: Aakash = human judgment/relationships. Agent = research/analysis/updates.
- Output valid JSON only — no commentary outside the JSON block.

## Thesis Tracker Protocol
The Thesis Tracker is an AI-managed conviction engine. Conviction spectrum:
- Maturity: New → Evolving → Evolving Fast
- Strength: Low → Medium → High

Flag conviction assessments for Strong/Moderate thesis connections. Suggest new threads only for genuinely novel investment theses.
```

**Step 2: Commit**

```bash
git add mcp-servers/ai-cos-mcp/runners/prompts/content_analysis_agentic.md
git commit -m "feat: add agentic system prompt for Agent SDK ContentAgent"
```

---

### Task 4: Agent SDK Runner — Core

**Files:**
- Create: `mcp-servers/ai-cos-mcp/runners/content_agent_sdk.py`
- Create: `mcp-servers/ai-cos-mcp/tests/test_content_agent_sdk.py`

**Step 1: Write failing test for the analyze function**

```python
# tests/test_content_agent_sdk.py
"""Tests for Agent SDK ContentAgent runner."""
import json
from unittest.mock import AsyncMock, patch

import pytest


def test_load_agentic_prompt():
    """Agentic prompt loads without template variables."""
    from runners.content_agent_sdk import load_agentic_prompt

    prompt = load_agentic_prompt()
    assert "{domain_context}" not in prompt
    assert "{preference_summary}" not in prompt
    assert "get_thesis_threads" in prompt
    assert "score_action" in prompt


def test_parse_digest_from_messages():
    """Should extract DigestData JSON from agent message stream."""
    from runners.content_agent_sdk import parse_digest_from_messages

    messages_text = '''I'll analyze this video. Let me first check thesis threads.

Here's the analysis:

```json
{"slug": "test", "title": "Test", "proposed_actions": []}
```'''

    result = parse_digest_from_messages(messages_text)
    assert result is not None
    assert result["slug"] == "test"


def test_parse_digest_handles_no_json():
    """Should return None when no valid JSON found."""
    from runners.content_agent_sdk import parse_digest_from_messages

    result = parse_digest_from_messages("No JSON here at all.")
    assert result is None


def test_build_user_message():
    """Should format video metadata and transcript into user message."""
    from runners.content_agent_sdk import build_user_message

    video = {
        "title": "Test Video",
        "channel": "TestChan",
        "url": "https://youtube.com/watch?v=abc",
        "upload_date": "2026-03-09",
        "duration_seconds": 1800,
        "transcript": {"success": True, "full_text": "Hello world test transcript."},
    }
    msg = build_user_message(video)
    assert "Test Video" in msg
    assert "30:00" in msg
    assert "Hello world test transcript." in msg
```

**Step 2: Run tests to verify they fail**

Run: `cd mcp-servers/ai-cos-mcp && python -m pytest tests/test_content_agent_sdk.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'runners.content_agent_sdk'`

**Step 3: Implement the Agent SDK runner**

```python
# runners/content_agent_sdk.py
from __future__ import annotations

"""ContentAgent (Agent SDK) — Agentic content analysis with tool-use loop.

Parallel build alongside content_agent.py. Uses claude_agent_sdk with
custom in-process MCP tools for dynamic thesis/preference/scoring queries.

Usage:
    python -m runners.content_agent_sdk
    python runners/content_agent_sdk.py --queue-dir /path/to/queue
    python runners/content_agent_sdk.py --dry-run
"""

import argparse
import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.publishing import publish_digest
from lib.scoring import ActionInput, classify_action, score_action

try:
    from lib.notion_client import (
        create_action_entry,
        create_digest_entry,
        create_thesis_thread,
        fetch_thesis_threads,
        update_thesis_tracker,
    )
    HAS_NOTION = bool(os.getenv("NOTION_TOKEN"))
except Exception:
    HAS_NOTION = False

try:
    from lib.preferences import get_preference_summary, log_outcome
    HAS_POSTGRES = bool(os.getenv("DATABASE_URL"))
except Exception:
    HAS_POSTGRES = False

try:
    from claude_agent_sdk import (
        ClaudeAgentOptions,
        AssistantMessage,
        ResultMessage,
        TextBlock,
        ToolUseBlock,
        query,
        tool,
        create_sdk_mcp_server,
    )
    HAS_AGENT_SDK = True
except ImportError:
    HAS_AGENT_SDK = False
    print("WARNING: claude_agent_sdk not available. Install with: pip install claude-agent-sdk")

DEFAULT_QUEUE_DIR = os.getenv("QUEUE_DIR", str(Path(__file__).parent.parent / "queue"))
AGENTIC_PROMPT_PATH = Path(__file__).parent / "prompts" / "content_analysis_agentic.md"


def load_agentic_prompt() -> str:
    """Load the agentic system prompt (no template variables to hydrate)."""
    return AGENTIC_PROMPT_PATH.read_text(encoding="utf-8")


def build_user_message(video: dict[str, Any]) -> str:
    """Format video metadata + transcript into the user message."""
    transcript = video.get("transcript", {})
    if not transcript or not transcript.get("success") or not transcript.get("full_text"):
        return ""

    duration_secs = video.get("duration_seconds", "NA")
    if duration_secs != "NA":
        try:
            mins = int(duration_secs) // 60
            secs = int(duration_secs) % 60
            duration_str = f"{mins}:{secs:02d}"
        except (ValueError, TypeError):
            duration_str = str(duration_secs)
    else:
        duration_str = "Unknown"

    return f"""Analyze this video and produce DigestData JSON.

**Title:** {video.get('title', 'Unknown')}
**Channel:** {video.get('channel', 'Unknown')}
**Duration:** {duration_str}
**URL:** {video.get('url', '')}
**Upload Date:** {video.get('upload_date', 'NA')}

**Transcript:**
{transcript['full_text'][:100000]}"""


def parse_digest_from_messages(text: str) -> dict[str, Any] | None:
    """Extract DigestData JSON from agent output text.

    Looks for JSON in ```json code fences first, then tries raw JSON.
    """
    # Try ```json ... ``` blocks
    pattern = r"```json\s*\n(.*?)\n\s*```"
    matches = re.findall(pattern, text, re.DOTALL)
    for match in reversed(matches):  # last JSON block is most likely the final output
        try:
            return json.loads(match.strip())
        except json.JSONDecodeError:
            continue

    # Fallback: try the whole text as JSON
    text = text.strip()
    if text.startswith("{"):
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

    return None


async def analyze_video_agentic(
    video: dict[str, Any],
    system_prompt: str,
) -> dict[str, Any] | None:
    """Analyze a video using Agent SDK tool-use loop.

    The agent dynamically queries thesis threads, preferences, and scoring
    tools to produce enriched DigestData JSON.
    """
    user_message = build_user_message(video)
    if not user_message:
        print(f"  Skipping {video.get('title', 'unknown')} — no transcript")
        return None

    # Import tool functions
    from runners.tools.content_tools import (
        get_thesis_threads_tool,
        get_preferences_tool,
        score_action_tool,
        get_domain_context_tool,
    )

    # Define tools for Agent SDK
    thesis_tool = tool(
        "get_thesis_threads",
        "Fetch current thesis threads from Notion Thesis Tracker with conviction levels, open key questions, and connected buckets.",
        {},
    )(get_thesis_threads_tool)

    prefs_tool = tool(
        "get_preferences",
        "Get action outcome preferences for scoring calibration. Returns recent accepted/dismissed actions with scores.",
        {"limit": int},
    )(get_preferences_tool)

    scoring_tool = tool(
        "score_action",
        "Score a proposed action using the 5-factor model. All inputs 0-10. Returns score and classification.",
        {
            "bucket_impact": float,
            "conviction_change": float,
            "time_sensitivity": float,
            "action_novelty": float,
            "effort_vs_impact": float,
        },
    )(score_action_tool)

    context_tool = tool(
        "get_domain_context",
        "Load AI CoS domain context from CONTEXT.md — IDS methodology, key people, playbooks.",
        {},
    )(get_domain_context_tool)

    # Create in-process MCP server with tools
    tools_server = create_sdk_mcp_server(
        name="content-tools",
        version="1.0.0",
        tools=[thesis_tool, prefs_tool, scoring_tool, context_tool],
    )

    options = ClaudeAgentOptions(
        system_prompt=system_prompt,
        model="claude-sonnet-4-5",
        max_turns=15,
        max_budget_usd=0.50,
        mcp_servers={"content_tools": tools_server},
        allowed_tools=[
            "mcp__content_tools__get_thesis_threads",
            "mcp__content_tools__get_preferences",
            "mcp__content_tools__score_action",
            "mcp__content_tools__get_domain_context",
        ],
        permission_mode="bypassPermissions",
    )

    # Collect agent output
    full_text = ""
    tool_calls = 0

    async for message in query(prompt=user_message, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    full_text += block.text
                elif isinstance(block, ToolUseBlock):
                    tool_calls += 1
                    print(f"    Tool call: {block.name}")
        elif isinstance(message, ResultMessage):
            cost = message.total_cost_usd or 0
            print(f"    Agent done: {message.num_turns} turns, {tool_calls} tool calls, ${cost:.4f}")

    return parse_digest_from_messages(full_text)


def process_extraction_sdk(
    extraction_path: Path,
    system_prompt: str,
    dry_run: bool = False,
) -> list[dict[str, Any]]:
    """Process a single extraction JSON file using Agent SDK runner.

    Post-processing (publish, Notion, preferences) is identical to linear runner.
    """
    import anyio

    with open(extraction_path, encoding="utf-8") as f:
        extraction = json.load(f)

    videos = extraction.get("videos", [])
    print(f"\nProcessing {extraction_path.name}: {len(videos)} videos (Agent SDK)")

    results = []
    for video in videos:
        relevance = video.get("relevance", {})
        if not relevance.get("relevant", True):
            continue
        transcript = video.get("transcript", {})
        if not transcript or not transcript.get("success"):
            continue

        title = video.get("title", "Unknown")
        print(f"\n  Analyzing (agentic): {title[:70]}...")

        # Run agentic analysis
        digest = anyio.run(analyze_video_agentic, video, system_prompt)
        if not digest:
            print(f"  Failed to analyze {title}")
            continue

        # Ensure metadata populated
        digest.setdefault("generated_at", datetime.now(timezone.utc).isoformat())
        digest.setdefault("url", video.get("url", ""))
        digest.setdefault("channel", video.get("channel", ""))
        digest.setdefault("title", title)

        # Actions should already have score/classification from tool calls
        # Verify and fill any gaps
        for action in digest.get("proposed_actions", []):
            if "score" not in action:
                # Fallback: use simple scoring if agent didn't call tool
                from lib.scoring import ActionInput as AI
                priority_map = {"P0": 9.0, "P1": 7.0, "P2": 5.0, "P3": 3.0}
                base = priority_map.get(action.get("priority", "P2"), 5.0)
                ai = AI(
                    bucket_impact=base,
                    conviction_change=base * 0.8,
                    time_sensitivity=base * 0.9 if action.get("priority") in ("P0", "P1") else 3.0,
                    action_novelty=7.0,
                    effort_vs_impact=6.0,
                )
                action["score"] = round(score_action(ai), 2)
                action["classification"] = classify_action(action["score"])

        action_count = len(digest.get("proposed_actions", []))
        surface_count = sum(
            1 for a in digest.get("proposed_actions", [])
            if a.get("classification") == "surface"
        )
        print(f"  {action_count} actions proposed, {surface_count} surface-level (score >=7)")

        if dry_run:
            print(f"  [DRY RUN] Skipping publish/Notion/Postgres")
            results.append(digest)
            continue

        # --- Post-processing (identical to linear runner) ---

        # Publish to digest.wiki
        try:
            pub_result = publish_digest(digest)
            print(f"  Published: {pub_result['url']}")
        except Exception as e:
            print(f"  Publish failed: {e}")
            pub_result = {"url": "", "slug": digest.get("slug", ""), "pushed": False}

        # Notion entries
        if HAS_NOTION:
            _write_notion_entries(digest, pub_result, title)

        # Preference store — log with FULL scoring factors
        if HAS_POSTGRES:
            _log_preferences(digest)

        results.append(digest)

    return results


def _write_notion_entries(
    digest: dict[str, Any],
    pub_result: dict[str, Any],
    title: str,
) -> None:
    """Write digest, action, and thesis entries to Notion."""
    # Import formatters from linear runner (reuse, don't duplicate)
    from runners.content_agent import (
        _format_summary,
        _format_key_insights,
        _format_thesis_connections_text,
        _format_portfolio_relevance,
        _format_essence_notes,
        _format_watch_sections,
        _format_contra_signals,
        _format_rabbit_holes,
        _format_proposed_actions_summary,
    )

    digest_page_id = None
    try:
        notion_page = create_digest_entry(
            title=digest["title"],
            slug=digest.get("slug", ""),
            url=digest.get("url", ""),
            channel=digest.get("channel", ""),
            relevance_score=digest.get("relevance_score", "Medium"),
            net_newness=digest.get("net_newness", {}).get("category", "Mixed"),
            connected_buckets=digest.get("connected_buckets", []),
            digest_url=pub_result.get("url", ""),
            content_type=digest.get("content_type", ""),
            duration=digest.get("duration", ""),
            summary=_format_summary(digest),
            key_insights=_format_key_insights(digest),
            thesis_connections=_format_thesis_connections_text(digest),
            portfolio_relevance=_format_portfolio_relevance(digest),
            essence_notes=_format_essence_notes(digest),
            watch_sections=_format_watch_sections(digest),
            contra_signals=_format_contra_signals(digest),
            rabbit_holes=_format_rabbit_holes(digest),
            proposed_actions_summary=_format_proposed_actions_summary(digest),
            processing_date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            upload_date=digest.get("upload_date") or None,
        )
        digest_page_id = notion_page.get("id")
    except Exception as e:
        print(f"  Notion digest entry failed: {e}")

    # Action entries
    all_actions = list(digest.get("proposed_actions", []))
    for pc in digest.get("portfolio_connections", []):
        all_actions.extend(pc.get("actions", []))

    source_content_str = f"{digest.get('title', '')} — {digest.get('url', '')}"

    for action in all_actions:
        try:
            create_action_entry(
                action_text=action["action"],
                priority=action.get("priority", "P2"),
                action_type=action.get("type", "content"),
                assigned_to=action.get("assigned_to", "Aakash"),
                company_name=action.get("company"),
                thesis_connection=(
                    " | ".join(action.get("thesis_connections", []))
                    or action.get("thesis_connection")
                ),
                source_digest_page_id=digest_page_id,
                relevance_score=action.get("score"),
                reasoning=action.get("reasoning", ""),
                source_content=source_content_str,
            )
        except Exception as e:
            print(f"  Action entry failed: {e}")

    # Thesis updates
    for tc in digest.get("thesis_connections", []):
        if tc.get("strength") in ("Strong", "Moderate"):
            try:
                update_thesis_tracker(
                    thesis_name=tc["thread"],
                    new_evidence=f"From '{title}': {tc['connection']}",
                    evidence_direction=tc.get("evidence_direction", "for"),
                    conviction=tc.get("conviction_assessment"),
                    new_key_questions=tc.get("new_key_questions"),
                    answered_questions=tc.get("answered_questions"),
                    investment_implications=tc.get("investment_implications"),
                    key_companies=tc.get("key_companies_mentioned"),
                )
            except Exception as e:
                print(f"  Thesis update failed: {e}")

    # New thesis threads
    for nts in digest.get("new_thesis_suggestions", []):
        try:
            create_thesis_thread(
                thread_name=nts["thread_name"],
                core_thesis=nts.get("core_thesis", ""),
                key_questions=nts.get("key_questions"),
                connected_buckets=nts.get("connected_buckets"),
                discovery_source="Content Pipeline (Agent SDK)",
                conviction="New",
            )
            if nts.get("initial_evidence"):
                update_thesis_tracker(
                    thesis_name=nts["thread_name"],
                    new_evidence=f"Initial signal from '{title}': {nts['initial_evidence']}",
                    evidence_direction=nts.get("evidence_direction", "for"),
                )
        except Exception as e:
            print(f"  New thesis creation failed: {e}")


def _log_preferences(digest: dict[str, Any]) -> None:
    """Log action outcomes with FULL scoring factor snapshots."""
    for action in digest.get("proposed_actions", []):
        try:
            # Use real scoring factors from agent's tool calls (not approximations)
            scoring_factors = {}
            if isinstance(action.get("scoring_factors"), dict):
                scoring_factors = action["scoring_factors"]
            else:
                # Reconstruct from score if factors not embedded
                scoring_factors = {
                    "bucket_impact": action.get("score", 0.0),
                    "conviction_change": 0.0,
                    "time_sensitivity": 0.0,
                    "action_novelty": 0.0,
                    "effort_vs_impact": 0.0,
                    "source": "content_agent_sdk",
                }

            log_outcome(
                action_text=action["action"],
                action_type=action.get("type", "content"),
                outcome="proposed",
                score=action.get("score", 0.0),
                scoring_factors=scoring_factors,
                source_digest_slug=digest.get("slug"),
                company=action.get("company"),
                thesis_thread=(
                    " | ".join(action.get("thesis_connections", []))
                    or action.get("thesis_connection")
                ),
            )
        except Exception as e:
            print(f"  Preference log failed: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="ContentAgent (Agent SDK) — agentic content analysis"
    )
    parser.add_argument("--queue-dir", default=DEFAULT_QUEUE_DIR, help="Queue directory")
    parser.add_argument("--dry-run", action="store_true", help="Analyze only, don't publish")
    parser.add_argument("--file", help="Process a specific extraction JSON file")
    args = parser.parse_args()

    if not HAS_AGENT_SDK:
        print("ERROR: claude_agent_sdk is required. Install with: pip install claude-agent-sdk")
        sys.exit(1)

    queue_dir = Path(args.queue_dir)
    processed_dir = queue_dir / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)

    print("Loading agentic system prompt...")
    system_prompt = load_agentic_prompt()
    print(f"  Prompt length: {len(system_prompt):,} chars")

    if args.file:
        files = [Path(args.file)]
    else:
        files = sorted(queue_dir.glob("youtube_extract_*.json"))

    if not files:
        print(f"No extraction files in {queue_dir}")
        return

    print(f"Found {len(files)} extraction file(s) to process")

    total_digests = 0
    for extraction_file in files:
        results = process_extraction_sdk(extraction_file, system_prompt, dry_run=args.dry_run)
        total_digests += len(results)

        if not args.dry_run and results:
            dest = processed_dir / extraction_file.name
            shutil.move(str(extraction_file), str(dest))
            print(f"  Moved to {dest}")

    print(f"\nDone! Processed {total_digests} digest(s) from {len(files)} extraction file(s)")


if __name__ == "__main__":
    main()
```

**Step 4: Run tests to verify they pass**

Run: `cd mcp-servers/ai-cos-mcp && python -m pytest tests/test_content_agent_sdk.py -v`
Expected: 4 passed

**Step 5: Commit**

```bash
git add mcp-servers/ai-cos-mcp/runners/content_agent_sdk.py mcp-servers/ai-cos-mcp/tests/test_content_agent_sdk.py
git commit -m "feat: add Agent SDK ContentAgent runner with tool-use loop"
```

---

### Task 5: Pipeline Toggle — --use-sdk Flag

**Files:**
- Modify: `mcp-servers/ai-cos-mcp/runners/pipeline.py`
- Create: `mcp-servers/ai-cos-mcp/tests/test_pipeline_toggle.py`

**Step 1: Read current pipeline.py**

Read: `mcp-servers/ai-cos-mcp/runners/pipeline.py`
Understand how the pipeline currently invokes ContentAgent.

**Step 2: Write failing test**

```python
# tests/test_pipeline_toggle.py
"""Tests for pipeline SDK toggle."""


def test_pipeline_has_use_sdk_arg():
    """Pipeline should accept --use-sdk flag."""
    import argparse
    # This test verifies the arg is registered — actual integration tested E2E
    from runners.pipeline import build_parser
    parser = build_parser()
    args = parser.parse_args(["--use-sdk"])
    assert args.use_sdk is True


def test_pipeline_default_is_linear():
    """Without --use-sdk, should use linear runner."""
    from runners.pipeline import build_parser
    parser = build_parser()
    args = parser.parse_args([])
    assert args.use_sdk is False
```

**Step 3: Run tests to verify they fail**

Run: `cd mcp-servers/ai-cos-mcp && python -m pytest tests/test_pipeline_toggle.py -v`
Expected: FAIL

**Step 4: Add --use-sdk flag to pipeline.py**

Add `build_parser()` function and `--use-sdk` argument. When `--use-sdk` is passed, import and use `process_extraction_sdk` from `content_agent_sdk` instead of `process_extraction` from `content_agent`.

**Step 5: Run tests to verify they pass**

Run: `cd mcp-servers/ai-cos-mcp && python -m pytest tests/test_pipeline_toggle.py -v`
Expected: 2 passed

**Step 6: Commit**

```bash
git add mcp-servers/ai-cos-mcp/runners/pipeline.py mcp-servers/ai-cos-mcp/tests/test_pipeline_toggle.py
git commit -m "feat: add --use-sdk flag to pipeline for Agent SDK toggle"
```

---

### Task 6: Benchmark Script

**Files:**
- Create: `mcp-servers/ai-cos-mcp/scripts/benchmark_sdk.py`

**Step 1: Create benchmark script**

```python
# scripts/benchmark_sdk.py
"""Benchmark: Linear ContentAgent vs Agent SDK ContentAgent.

Runs both runners on the same extraction file (dry-run mode),
compares output quality metrics:
- Number of thesis connections
- Number of scored actions
- Score distribution
- Tool calls made (SDK only)
- Processing time
- Cost (SDK only)
"""

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def run_benchmark(extraction_file: str):
    from runners.content_agent import load_system_prompt, process_extraction
    from runners.content_agent_sdk import load_agentic_prompt, process_extraction_sdk

    path = Path(extraction_file)
    if not path.exists():
        print(f"File not found: {path}")
        return

    print("=" * 60)
    print("BENCHMARK: Linear vs Agent SDK ContentAgent")
    print("=" * 60)

    # Linear runner
    print("\n--- LINEAR RUNNER ---")
    linear_prompt = load_system_prompt()
    t0 = time.time()
    linear_results = process_extraction(path, linear_prompt, dry_run=True)
    linear_time = time.time() - t0

    # SDK runner
    print("\n--- AGENT SDK RUNNER ---")
    sdk_prompt = load_agentic_prompt()
    t0 = time.time()
    sdk_results = process_extraction_sdk(path, sdk_prompt, dry_run=True)
    sdk_time = time.time() - t0

    # Compare
    print("\n" + "=" * 60)
    print("COMPARISON")
    print("=" * 60)

    for label, results, elapsed in [
        ("Linear", linear_results, linear_time),
        ("Agent SDK", sdk_results, sdk_time),
    ]:
        if not results:
            print(f"\n{label}: No results")
            continue
        for d in results:
            actions = d.get("proposed_actions", [])
            scores = [a.get("score", 0) for a in actions]
            surface = sum(1 for s in scores if s >= 7)
            thesis = d.get("thesis_connections", [])
            print(f"\n{label} — {d.get('title', 'Unknown')[:50]}:")
            print(f"  Time: {elapsed:.1f}s")
            print(f"  Thesis connections: {len(thesis)}")
            print(f"  Actions: {len(actions)} ({surface} surface)")
            if scores:
                print(f"  Score range: {min(scores):.1f} - {max(scores):.1f}")
                print(f"  Avg score: {sum(scores)/len(scores):.1f}")

    # Save comparison JSON
    out = Path("benchmark_results.json")
    out.write_text(json.dumps({
        "linear": {"time": linear_time, "results": linear_results},
        "sdk": {"time": sdk_time, "results": sdk_results},
    }, default=str, indent=2))
    print(f"\nFull results saved to {out}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/benchmark_sdk.py <extraction_file.json>")
        sys.exit(1)
    run_benchmark(sys.argv[1])
```

**Step 2: Commit**

```bash
git add mcp-servers/ai-cos-mcp/scripts/benchmark_sdk.py
git commit -m "feat: add benchmark script for linear vs Agent SDK comparison"
```

---

### Task 7: Install Agent SDK on Droplet

**Step 1: SSH to droplet and install**

```bash
ssh root@aicos-droplet
cd /opt/ai-cos-mcp
uv pip install claude-agent-sdk
```

**Step 2: Verify Claude Code CLI is available**

The Agent SDK requires Claude Code CLI. Check if it's installed:

```bash
which claude || echo "Claude Code CLI not installed"
```

If not installed, install it:

```bash
npm install -g @anthropic-ai/claude-code
# OR if no npm:
curl -fsSL https://claude.ai/install.sh | sh
```

Verify: `claude --version`

**Step 3: Verify ANTHROPIC_API_KEY is set**

```bash
grep ANTHROPIC_API_KEY /opt/ai-cos-mcp/.env
```

**Step 4: Deploy updated code**

```bash
# From Mac:
cd mcp-servers/ai-cos-mcp && bash deploy.sh
```

**Step 5: Test dry-run on droplet**

```bash
ssh root@aicos-droplet
cd /opt/ai-cos-mcp
# Use a previously processed file for testing:
ls queue/processed/ | head -1
# Copy one back for testing:
cp queue/processed/<file>.json queue/test_benchmark.json
python -m runners.content_agent_sdk --file queue/test_benchmark.json --dry-run
```

**Step 6: Commit any deploy script changes**

```bash
git add -A && git commit -m "infra: install Agent SDK on droplet, verify deployment"
```

---

### Task 8: End-to-End Integration Test

**Files:**
- Create: `mcp-servers/ai-cos-mcp/tests/test_e2e_sdk.py`

**Step 1: Create E2E test with fixture data**

```python
# tests/test_e2e_sdk.py
"""End-to-end test for Agent SDK ContentAgent.

Uses a real extraction JSON fixture to verify the full pipeline
(dry-run mode — no publishing or Notion writes).
"""

import json
from pathlib import Path

import pytest

FIXTURE_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def extraction_fixture(tmp_path):
    """Create a minimal extraction JSON for E2E testing."""
    fixture = {
        "playlist_url": "test",
        "extraction_date": "2026-03-09",
        "videos": [
            {
                "title": "AI Agents Are Replacing SaaS — Here's How",
                "channel": "Test AI Channel",
                "url": "https://youtube.com/watch?v=test_e2e",
                "upload_date": "2026-03-08",
                "duration_seconds": 1200,
                "relevance": {"relevant": True, "reason": "Directly relevant to thesis"},
                "transcript": {
                    "success": True,
                    "method": "youtube-transcript-api",
                    "full_text": (
                        "The era of horizontal SaaS is coming to an end. "
                        "What we're seeing is that AI agents are now capable of handling "
                        "entire vertical workflows that previously required multiple SaaS tools. "
                        "Take the example of sales — instead of Salesforce plus Outreach plus "
                        "ZoomInfo, a single AI agent can prospect, qualify, and manage the pipeline. "
                        "This is the SaaS Death thesis in action. Companies like 11x.ai and "
                        "Artisan are building these vertical agents. The infrastructure layer — "
                        "companies like Anthropic, LangChain, and Modal — are the picks and shovels. "
                        "For investors, the question is: do you bet on the infrastructure or "
                        "the vertical applications? History suggests infrastructure wins, "
                        "but vertical agents have defensible data moats."
                    ),
                },
            }
        ],
    }
    fixture_path = tmp_path / "youtube_extract_test.json"
    fixture_path.write_text(json.dumps(fixture))
    return fixture_path


@pytest.mark.skipif(
    not Path(__file__).parent.parent.joinpath("runners/content_agent_sdk.py").exists(),
    reason="Agent SDK runner not yet created",
)
def test_e2e_dry_run_produces_digest(extraction_fixture):
    """Full pipeline produces valid DigestData with scored actions."""
    from runners.content_agent_sdk import load_agentic_prompt, process_extraction_sdk

    prompt = load_agentic_prompt()
    results = process_extraction_sdk(extraction_fixture, prompt, dry_run=True)

    assert len(results) >= 1
    digest = results[0]

    # Structural checks
    assert "slug" in digest
    assert "proposed_actions" in digest
    assert "thesis_connections" in digest

    # Actions should have scores from tool calls
    for action in digest.get("proposed_actions", []):
        assert "score" in action, f"Action missing score: {action.get('action', '')}"
        assert "classification" in action
        assert isinstance(action["score"], (int, float))
```

**Step 2: Run (skip if Agent SDK not installed locally)**

Run: `cd mcp-servers/ai-cos-mcp && python -m pytest tests/test_e2e_sdk.py -v -s`
Expected: 1 passed (or skipped if SDK not available)

Note: This test makes real Claude API calls. Skip in CI. Run manually for validation.

**Step 3: Commit**

```bash
git add mcp-servers/ai-cos-mcp/tests/test_e2e_sdk.py
git commit -m "test: add E2E integration test for Agent SDK ContentAgent"
```

---

## Phase 2: Action Frontend MVP (digest.wiki)

> **Note:** Detailed atomic steps will be written when Phase 1 ships. Below is task-level outline.

### Task 9: API Route — GET /api/actions

**Files:**
- Create: `aicos-digests/app/api/actions/route.ts`

Fetch actions from Notion Actions Queue (via Notion API or cos_get_actions MCP).
Return JSON: `{ actions: [...], counts: { proposed, accepted, dismissed } }`.
Filter by status (default: Proposed). Sort by relevance_score desc.

---

### Task 10: Actions Page Component

**Files:**
- Create: `aicos-digests/app/actions/page.tsx`
- Create: `aicos-digests/components/action-card.tsx`

Card for each action showing: action text, priority badge, score, type, reasoning, thesis connections.
Accept (green) and Dismiss (red) buttons on each card.
Group by priority: P0 → P1 → P2 → P3.

---

### Task 11: API Route — POST /api/actions/[id]/respond

**Files:**
- Create: `aicos-digests/app/api/actions/[id]/respond/route.ts`

Accept or dismiss an action. Two writes:
1. Notion: Update Actions Queue item status (Proposed → Accepted or Dismissed)
2. Postgres: `log_outcome()` with full scoring factors (call cos_get_preferences or direct API)

---

### Task 12: Preference Signal Capture

**Files:**
- Modify: `mcp-servers/ai-cos-mcp/lib/preferences.py` (add `update_outcome()`)

When user accepts/dismisses via frontend, update the existing `proposed` row to `accepted`/`dismissed`.
This is the RL signal that closes the preference loop.

---

### Task 13: Wire Preferences into Agent SDK ContentAgent

**Files:**
- Modify: `mcp-servers/ai-cos-mcp/runners/tools/content_tools.py`

Enhance `get_preferences_tool` to format calibration data in a way the agent can use:
- "You proposed 12 Research actions last week. 8 were accepted (67%). Average accepted score: 7.2. Average dismissed score: 4.8."
- "Meeting/Outreach actions have 90% acceptance — lean into these."

---

### Task 14: Deploy & Validate

- `cd aicos-digests && npm run build` — verify no build errors
- `git push origin main` — auto-deploy to Vercel
- Test at `https://digest.wiki/actions`
- Accept/dismiss 5 actions, verify Notion + Postgres updates

---

## Phase 3: PostMeetingAgent (outline)

> **Note:** Detailed plan written when Phase 2 ships.

### Task 15: Meeting Tools

**Files:**
- Create: `mcp-servers/ai-cos-mcp/runners/tools/meeting_tools.py`

Tools wrapping Granola MCP: `get_recent_meetings`, `get_meeting_transcript`.
Tools wrapping Network DB: `lookup_person`, `create_network_entry`.
Reuse: `get_thesis_threads_tool`, `score_action_tool`, `get_preferences_tool`.

---

### Task 16: PostMeetingAgent Runner

**Files:**
- Create: `mcp-servers/ai-cos-mcp/runners/post_meeting_agent.py`
- Create: `mcp-servers/ai-cos-mcp/runners/prompts/post_meeting_analysis.md`

Copy Agent SDK pattern from `content_agent_sdk.py`. Replace video analysis with meeting analysis:
- Extract IDS signals (+, ++, ?, ??, +?)
- Detect commitments and follow-ups
- Identify new people for Network DB
- Score follow-up actions
- Update thesis threads with meeting evidence

---

### Task 17: Meeting Trigger

**Files:**
- Modify: `mcp-servers/ai-cos-mcp/runners/pipeline.py`

Add Granola polling: check for new meetings since last run.
When found, invoke PostMeetingAgent.
Cron: every 30 min (meetings less frequent than content).

---

### Task 18: Integration & Deploy

- Test with real Granola transcript (dry-run)
- Deploy to droplet
- Add cron job
- Verify thesis updates and action creation from meeting signals
