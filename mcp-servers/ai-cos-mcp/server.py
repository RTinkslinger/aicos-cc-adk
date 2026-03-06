"""AI CoS MCP Server — exposes tools for remote Claude clients.

Deployed on DO droplet, accessible via Tailscale + Cloudflare Tunnel.
Remote clients (Claude.ai, Claude Code, digest.wiki) call these tools.
Agent SDK runners import lib/ directly — no MCP hop.
"""

import os

from dotenv import load_dotenv
from fastmcp import FastMCP

load_dotenv()

mcp = FastMCP(
    "ai-cos-mcp",
    instructions="AI Chief of Staff MCP server. Provides context loading, action scoring, and preference tracking.",
)

DATABASE_URL = os.getenv("DATABASE_URL", "")


@mcp.tool()
def health_check() -> dict:
    """Check server and database connectivity."""
    import psycopg2

    result = {"server": "ok", "database": "unknown"}
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM action_outcomes")
        count = cur.fetchone()[0]
        cur.close()
        conn.close()
        result["database"] = "ok"
        result["action_outcomes_count"] = count
    except Exception as e:
        result["database"] = f"error: {e}"
    return result


@mcp.tool()
def cos_load_context() -> dict:
    """Load AI CoS domain context — key sections from CONTEXT.md."""
    from pathlib import Path

    context_path = os.getenv("CONTEXT_MD_PATH", str(Path(__file__).parent / "CONTEXT.md"))
    path = Path(context_path)
    if not path.exists():
        return {"error": f"CONTEXT.md not found at {path}", "context": ""}

    text = path.read_text(encoding="utf-8")
    # Return a trimmed version for MCP clients (keep under 8K chars)
    return {"context": text[:8000], "path": str(path), "length": len(text)}


@mcp.tool()
def cos_score_action(
    bucket_impact: float,
    conviction_change: float,
    time_sensitivity: float,
    action_novelty: float,
    effort_vs_impact: float,
) -> dict:
    """Score an action using the AI CoS action scoring model.

    All inputs on 0-10 scale. Returns score (0-10) and classification.
    """
    from lib.scoring import ActionInput, classify_action, score_action

    action = ActionInput(
        bucket_impact=bucket_impact,
        conviction_change=conviction_change,
        time_sensitivity=time_sensitivity,
        action_novelty=action_novelty,
        effort_vs_impact=effort_vs_impact,
    )
    score = score_action(action)
    return {
        "score": round(score, 2),
        "classification": classify_action(score),
    }


@mcp.tool()
def cos_get_preferences(limit: int = 20) -> dict:
    """Get recent action outcome preferences for calibration."""
    from lib.preferences import get_preference_summary, get_preferences

    return {
        "recent_outcomes": get_preferences(limit=limit),
        "summary": get_preference_summary(),
    }


@mcp.tool()
def cos_create_thesis_thread(
    thread_name: str,
    core_thesis: str,
    key_questions: list[str] | None = None,
    connected_buckets: list[str] | None = None,
    discovery_source: str = "Claude",
    conviction: str = "New",
) -> dict:
    """Create a new thesis thread in the Thesis Tracker.

    Creates at Conviction='New' by default. Key questions are added as [OPEN]
    blocks on the page. All surfaces should use this instead of writing to
    Notion directly.

    Args:
        thread_name: Short, distinctive name for the thesis thread
        core_thesis: One-liner: what is the durable value insight?
        key_questions: 2-3 critical questions that would move conviction up or down
        connected_buckets: Priority buckets (New Cap Tables, Deepen Existing, New Founders, Thesis Evolution)
        discovery_source: Where this thesis originated (Claude, Content Pipeline, Meeting, Research)
        conviction: Initial conviction level (New, Evolving, Evolving Fast, Low, Medium, High)
    """
    from lib.notion_client import create_thesis_thread

    result = create_thesis_thread(
        thread_name=thread_name,
        core_thesis=core_thesis,
        key_questions=key_questions,
        connected_buckets=connected_buckets,
        discovery_source=discovery_source,
        conviction=conviction,
    )
    return {"id": result.get("id", ""), "thread_name": thread_name, "conviction": conviction}


@mcp.tool()
def cos_update_thesis(
    thesis_name: str,
    new_evidence: str,
    evidence_direction: str = "for",
    source: str = "Claude",
    conviction: str | None = None,
    new_key_questions: list[str] | None = None,
    answered_questions: list[str] | None = None,
    investment_implications: str | None = None,
    key_companies: str | None = None,
) -> dict:
    """Update an existing thesis thread with new evidence.

    Appends evidence to the page body, optionally updates conviction level,
    adds new key questions, and marks answered questions. All surfaces should
    use this instead of writing to Notion directly.

    Args:
        thesis_name: Name of the existing thesis thread (partial match supported)
        new_evidence: The evidence text to append
        evidence_direction: 'for', 'against', or 'mixed'
        source: Where this evidence came from (Claude, Content Pipeline, Meeting, Research)
        conviction: New conviction level if it should change (New, Evolving, Evolving Fast, Low, Medium, High)
        new_key_questions: New questions this evidence raises
        answered_questions: Existing open questions this evidence answers
        investment_implications: What Aakash should DO about this
        key_companies: Companies mentioned relevant to this thesis
    """
    from lib.notion_client import update_thesis_tracker

    result = update_thesis_tracker(
        thesis_name=thesis_name,
        new_evidence=new_evidence,
        evidence_direction=evidence_direction,
        source=source,
        conviction=conviction,
        new_key_questions=new_key_questions,
        answered_questions=answered_questions,
        investment_implications=investment_implications,
        key_companies=key_companies,
    )
    if result is None:
        return {"error": f"Thesis '{thesis_name}' not found in tracker"}
    return {"id": result.get("id", ""), "thesis_name": thesis_name, "updated": True}


@mcp.tool()
def cos_get_thesis_threads(include_key_questions: bool = False) -> dict:
    """Get all active thesis threads from the Thesis Tracker.

    Returns thread names, conviction levels, core theses, evidence,
    and key questions. Use this to understand current thesis state
    before creating or updating threads.

    Args:
        include_key_questions: If True, also fetches individual [OPEN]/[ANSWERED]
            questions from page blocks (slower — one API call per thread)
    """
    from lib.notion_client import fetch_thesis_threads

    threads = fetch_thesis_threads(include_key_questions=include_key_questions)
    return {"threads": threads, "count": len(threads)}


@mcp.tool()
def cos_get_recent_digests(limit: int = 10) -> dict:
    """Get recent content digests from the Content Digest DB.

    Returns analyzed content with titles, channels, relevance scores,
    net newness, summaries, and digest URLs.

    Args:
        limit: Max number of digests to return (default 10)
    """
    from lib.notion_client import fetch_recent_digests

    digests = fetch_recent_digests(limit=limit)
    return {"digests": digests, "count": len(digests)}


@mcp.tool()
def cos_get_actions(status: str | None = None, limit: int = 20) -> dict:
    """Get actions from the Actions Queue.

    Returns proposed, accepted, or in-progress actions with priorities,
    types, assignments, and thesis connections.

    Args:
        status: Filter by status (Proposed, Accepted, In Progress, Done, Dismissed).
            If None, returns all actions.
        limit: Max number of actions to return (default 20)
    """
    from lib.notion_client import fetch_actions

    actions = fetch_actions(status_filter=status, limit=limit)
    return {"actions": actions, "count": len(actions)}


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8000)
