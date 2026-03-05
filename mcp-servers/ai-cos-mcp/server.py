"""AI CoS MCP Server — exposes tools for remote Claude clients.

Deployed on DO droplet, accessible via Tailscale.
Remote clients (Claude.ai mobile, digest.wiki) call these tools.
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


if __name__ == "__main__":
    mcp.run(transport="sse", host="0.0.0.0", port=8000)
