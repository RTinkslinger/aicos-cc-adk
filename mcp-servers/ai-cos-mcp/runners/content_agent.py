from __future__ import annotations

"""ContentAgent — AI CoS Agent SDK runner for content analysis.

Reads extraction JSONs from queue/, sends each video transcript to Claude
for analysis, then publishes digests and creates Notion entries.

Usage:
    python -m runners.content_agent
    python runners/content_agent.py
    python runners/content_agent.py --queue-dir /path/to/queue
    python runners/content_agent.py --dry-run  # analyze but don't publish/notify
"""

import argparse
import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

load_dotenv()

# Add parent to path for lib imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.publishing import publish_digest
from lib.scoring import ActionInput, classify_action, score_action

# Optional imports — gracefully degrade if not available
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
    import claude_agent_sdk as sdk
    HAS_AGENT_SDK = True
except ImportError:
    # Fallback: use anthropic SDK directly
    try:
        import anthropic
        HAS_AGENT_SDK = False
    except ImportError:
        print("ERROR: Neither claude-agent-sdk nor anthropic is installed")
        sys.exit(1)


DEFAULT_QUEUE_DIR = os.getenv("QUEUE_DIR", str(Path(__file__).parent.parent / "queue"))
PROMPT_PATH = Path(__file__).parent / "prompts" / "content_analysis.md"
CONTEXT_MD_PATH = os.getenv(
    "CONTEXT_MD_PATH",
    str(Path(__file__).parent.parent / "CONTEXT.md"),
)


def _load_context_sections(include_thesis_fallback: bool = False) -> str:
    """Read CONTEXT.md and extract sections relevant to content analysis.

    Returns raw markdown sections for: IDS methodology, scoring model,
    key people, and operational playbooks. Claude reads these natively.

    Args:
        include_thesis_fallback: If True, include the THESIS THREADS section
            from CONTEXT.md (used when Notion is unreachable).
    """
    path = Path(CONTEXT_MD_PATH)
    if not path.exists():
        print(f"  WARNING: CONTEXT.md not found at {path}")
        return "CONTEXT.md not available. Proceed with general analysis."

    text = path.read_text(encoding="utf-8")

    # Static framework sections — rarely change
    keep_headings = {
        "CRITICAL FRAMING",
        "WHO IS AAKASH KUMAR",
        "THE CORE PROBLEM",
        "IDS METHODOLOGY",
        "PORTFOLIO ACTIONS TRACKER",
        "KEY PEOPLE",
        "OPERATIONAL PLAYBOOKS",
    }
    # Fallback: include thesis threads from CONTEXT.md if Notion is unreachable
    if include_thesis_fallback:
        keep_headings.add("THESIS THREADS")

    sections: list[str] = []
    current_section: list[str] = []
    current_heading = ""

    for line in text.split("\n"):
        if line.startswith("## "):
            # Save previous section if it matches
            if current_heading and any(k in current_heading.upper() for k in keep_headings):
                sections.append("\n".join(current_section))
            current_section = [line]
            current_heading = line
        else:
            current_section.append(line)

    # Don't forget the last section
    if current_heading and any(k in current_heading.upper() for k in keep_headings):
        sections.append("\n".join(current_section))

    # Also list portfolio companies from portfolio-research/ directory
    portfolio_dir = Path(__file__).parent.parent / "portfolio-research"
    if portfolio_dir.exists():
        companies = sorted(
            f.stem.replace("-", " ").title()
            for f in portfolio_dir.glob("*.md")
        )
        if companies:
            sections.append(
                "## Portfolio Companies (from deep research files)\n\n"
                + ", ".join(companies)
            )

    return "\n\n---\n\n".join(sections) if sections else "No context sections loaded."


def _format_thesis_threads_from_notion() -> str:
    """Fetch thesis threads from Notion and format as markdown for the prompt.

    Includes open key questions so the analysis model can flag when
    content answers existing questions.
    """
    if not HAS_NOTION:
        return ""

    try:
        threads = fetch_thesis_threads(include_key_questions=True)
    except Exception as e:
        print(f"  WARNING: Failed to fetch thesis threads from Notion: {e}")
        return ""

    if not threads:
        return ""

    lines = ["## Active Thesis Threads (live from Notion Thesis Tracker)\n"]
    for t in threads:
        conviction = f" [{t['conviction']}]" if t["conviction"] else ""
        status = f" ({t['status']})" if t["status"] else ""
        line = f"- **{t['name']}**{conviction}{status}"
        if t["core_thesis"]:
            line += f" — {t['core_thesis']}"
        lines.append(line)
        if t.get("open_questions"):
            lines.append(f"  - Open questions:")
            for q in t["open_questions"]:
                lines.append(f"    - [OPEN] {q}")
        elif t.get("key_question"):
            lines.append(f"  - Key question: {t['key_question']}")
        if t.get("key_companies"):
            lines.append(f"  - Key companies: {t['key_companies']}")
        if t.get("connected_buckets"):
            lines.append(f"  - Buckets: {t['connected_buckets']}")

    return "\n".join(lines)


def load_system_prompt() -> str:
    """Load and hydrate the content analysis system prompt."""
    template = PROMPT_PATH.read_text(encoding="utf-8")

    # Thesis threads: Notion is source of truth, CONTEXT.md is fallback
    thesis_section = _format_thesis_threads_from_notion()
    use_thesis_fallback = not thesis_section
    if use_thesis_fallback:
        print("  Notion thesis fetch unavailable — falling back to CONTEXT.md")

    domain_context = _load_context_sections(include_thesis_fallback=use_thesis_fallback)

    if thesis_section:
        domain_context += "\n\n---\n\n" + thesis_section

    # Format preference summary
    pref_str = "No preference history available yet."
    if HAS_POSTGRES:
        try:
            summary = get_preference_summary()
            if summary.get("by_action_type"):
                pref_lines = []
                for atype, stats in summary["by_action_type"].items():
                    pref_lines.append(
                        f"- {atype}: {stats['accepted']} accepted, {stats['dismissed']} dismissed "
                        f"(avg accepted score: {stats['avg_accepted_score']}, "
                        f"avg dismissed: {stats['avg_dismissed_score']})"
                    )
                pref_str = "\n".join(pref_lines)
        except Exception:
            pass

    return (
        template
        .replace("{domain_context}", domain_context)
        .replace("{preference_summary}", pref_str)
    )


def analyze_video(
    video: dict[str, Any],
    system_prompt: str,
) -> dict[str, Any] | None:
    """Send a video transcript to Claude for analysis, return DigestData dict."""
    transcript = video.get("transcript", {})
    if not transcript or not transcript.get("success") or not transcript.get("full_text"):
        print(f"  Skipping {video.get('title', 'unknown')} — no transcript")
        return None

    # Build user message
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

    user_message = f"""Analyze this video and produce DigestData JSON.

**Title:** {video.get('title', 'Unknown')}
**Channel:** {video.get('channel', 'Unknown')}
**Duration:** {duration_str}
**URL:** {video.get('url', '')}
**Upload Date:** {video.get('upload_date', 'NA')}

**Transcript:**
{transcript['full_text'][:100000]}"""

    # Call Claude
    if HAS_AGENT_SDK:
        return _analyze_with_agent_sdk(system_prompt, user_message)
    else:
        return _analyze_with_anthropic(system_prompt, user_message)


def _analyze_with_agent_sdk(system_prompt: str, user_message: str) -> dict[str, Any] | None:
    """Use Claude Agent SDK for analysis."""
    agent = sdk.Agent(
        model="claude-sonnet-4-20250514",
        system=system_prompt,
    )
    result = agent.run(user_message)
    return _parse_json_response(result.text)


def _analyze_with_anthropic(system_prompt: str, user_message: str) -> dict[str, Any] | None:
    """Fallback: use anthropic SDK directly."""
    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=8192,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )
    text = response.content[0].text
    return _parse_json_response(text)


def _parse_json_response(text: str) -> dict[str, Any] | None:
    """Parse JSON from Claude's response, handling markdown code blocks."""
    # Strip markdown code fences if present
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        print(f"  Failed to parse JSON response: {e}")
        print(f"  Response preview: {text[:200]}")
        return None


def score_proposed_actions(digest: dict[str, Any]) -> dict[str, Any]:
    """Score each proposed action using the action scoring model.

    Modifies digest in place, adding score and classification to each action.
    """
    for action in digest.get("proposed_actions", []):
        # Map priority to approximate scoring dimensions
        priority_map = {"P0": 9.0, "P1": 7.0, "P2": 5.0, "P3": 3.0}
        base = priority_map.get(action.get("priority", "P2"), 5.0)

        ai = ActionInput(
            bucket_impact=base,
            conviction_change=base * 0.8,
            time_sensitivity=base * 0.9 if action.get("priority") in ("P0", "P1") else 3.0,
            action_novelty=7.0,  # Content-derived actions are generally novel
            effort_vs_impact=6.0,
        )
        action["score"] = round(score_action(ai), 2)
        action["classification"] = classify_action(action["score"])

    # Also score portfolio connection actions
    for pc in digest.get("portfolio_connections", []):
        for action in pc.get("actions", []):
            priority_map = {"P0": 9.0, "P1": 7.0, "P2": 5.0, "P3": 3.0}
            base = priority_map.get(action.get("priority", "P2"), 5.0)
            ai = ActionInput(
                bucket_impact=base,
                conviction_change=base * 0.9,  # Portfolio actions have higher conviction weight
                time_sensitivity=base * 0.9 if action.get("priority") in ("P0", "P1") else 3.0,
                action_novelty=7.0,
                effort_vs_impact=6.0,
            )
            action["score"] = round(score_action(ai), 2)
            action["classification"] = classify_action(action["score"])

    return digest


def _format_summary(digest: dict[str, Any]) -> str:
    """Build Summary from essence_notes core arguments."""
    en = digest.get("essence_notes", {})
    args = en.get("core_arguments", [])
    if not args:
        return ""
    return "\n".join(f"• {a}" for a in args)


def _format_key_insights(digest: dict[str, Any]) -> str:
    """Build Key Insights from essence_notes frameworks + data points."""
    en = digest.get("essence_notes", {})
    parts: list[str] = []
    for fw in en.get("frameworks", []):
        parts.append(f"[Framework] {fw}")
    for dp in en.get("data_points", []):
        parts.append(f"[Data] {dp}")
    for pred in en.get("predictions", []):
        parts.append(f"[Prediction] {pred}")
    return "\n".join(parts) if parts else ""


def _format_thesis_connections_text(digest: dict[str, Any]) -> str:
    """Format thesis connections for Notion rich_text."""
    tcs = digest.get("thesis_connections", [])
    if not tcs:
        return ""
    lines: list[str] = []
    for tc in tcs:
        direction = tc.get("evidence_direction", "")
        strength = tc.get("strength", "")
        lines.append(f"• {tc.get('thread', '')} [{strength}, {direction}]: {tc.get('connection', '')}")
    return "\n".join(lines)


def _format_portfolio_relevance(digest: dict[str, Any]) -> str:
    """Format portfolio connections for Notion rich_text."""
    pcs = digest.get("portfolio_connections", [])
    if not pcs:
        return ""
    lines: list[str] = []
    for pc in pcs:
        lines.append(f"• {pc.get('company', '')}: {pc.get('relevance', '')}")
        if pc.get("key_question"):
            lines.append(f"  Key Q: {pc['key_question']}")
    return "\n".join(lines)


def _format_essence_notes(digest: dict[str, Any]) -> str:
    """Format essence notes for Notion rich_text."""
    en = digest.get("essence_notes", {})
    if not en:
        return ""
    parts: list[str] = []
    for arg in en.get("core_arguments", []):
        parts.append(f"• {arg}")
    for quote in en.get("key_quotes", []):
        speaker = quote.get("speaker", "")
        ts = quote.get("timestamp", "")
        parts.append(f'"{quote.get("text", "")}" —{speaker} [{ts}]')
    return "\n".join(parts) if parts else ""


def _format_watch_sections(digest: dict[str, Any]) -> str:
    """Format watch sections for Notion rich_text."""
    ws = digest.get("watch_sections", [])
    if not ws:
        return ""
    lines: list[str] = []
    for s in ws:
        lines.append(f"• [{s.get('timestamp_range', '')}] {s.get('title', '')}")
        lines.append(f"  Why: {s.get('why_watch', '')}")
    return "\n".join(lines)


def _format_contra_signals(digest: dict[str, Any]) -> str:
    """Format contra signals for Notion rich_text."""
    cs = digest.get("contra_signals", [])
    if not cs:
        return ""
    lines: list[str] = []
    for c in cs:
        strength = c.get("strength", "")
        lines.append(f"• [{strength}] {c.get('what', '')}")
        if c.get("implication"):
            lines.append(f"  → {c['implication']}")
    return "\n".join(lines)


def _format_rabbit_holes(digest: dict[str, Any]) -> str:
    """Format rabbit holes for Notion rich_text."""
    rhs = digest.get("rabbit_holes", [])
    if not rhs:
        return ""
    lines: list[str] = []
    for r in rhs:
        lines.append(f"• {r.get('title', '')}: {r.get('what', '')}")
        if r.get("entry_point"):
            lines.append(f"  Start: {r['entry_point']}")
    return "\n".join(lines)


def _format_proposed_actions_summary(digest: dict[str, Any]) -> str:
    """Format proposed actions summary for Notion rich_text."""
    actions = digest.get("proposed_actions", [])
    if not actions:
        return ""
    lines: list[str] = []
    for a in actions:
        score_str = f" (score: {a['score']})" if a.get("score") else ""
        lines.append(f"• [{a.get('priority', 'P2')}]{score_str} {a.get('action', '')}")
    return "\n".join(lines)


def process_extraction(
    extraction_path: Path,
    system_prompt: str,
    dry_run: bool = False,
) -> list[dict[str, Any]]:
    """Process a single extraction JSON file. Returns list of published digests."""
    with open(extraction_path, encoding="utf-8") as f:
        extraction = json.load(f)

    videos = extraction.get("videos", [])
    print(f"\nProcessing {extraction_path.name}: {len(videos)} videos")

    results = []
    for video in videos:
        # Skip non-relevant or no-transcript videos
        relevance = video.get("relevance", {})
        if not relevance.get("relevant", True):
            continue
        transcript = video.get("transcript", {})
        if not transcript or not transcript.get("success"):
            continue

        title = video.get("title", "Unknown")
        print(f"\n  Analyzing: {title[:70]}...")

        # 1. Claude analysis
        digest = analyze_video(video, system_prompt)
        if not digest:
            print(f"  Failed to analyze {title}")
            continue

        # Ensure metadata is populated
        digest.setdefault("generated_at", datetime.now(timezone.utc).isoformat())
        digest.setdefault("url", video.get("url", ""))
        digest.setdefault("channel", video.get("channel", ""))
        digest.setdefault("title", title)

        # 2. Score proposed actions
        digest = score_proposed_actions(digest)
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

        # 3. Publish to digest.wiki
        try:
            pub_result = publish_digest(digest)
            print(f"  Published: {pub_result['url']}")
        except Exception as e:
            print(f"  Publish failed: {e}")
            pub_result = {"url": "", "slug": digest.get("slug", ""), "pushed": False}

        # 4. Create Notion entries
        digest_page_id = None
        if HAS_NOTION:
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
                )
                digest_page_id = notion_page.get("id")
            except Exception as e:
                print(f"  Notion digest entry failed: {e}")

            # Create action entries (proposed_actions + portfolio_connection actions)
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
                        thesis_connection=" | ".join(action.get("thesis_connections", [])) or action.get("thesis_connection"),
                        source_digest_page_id=digest_page_id,
                        relevance_score=action.get("score"),
                        reasoning=action.get("reasoning", ""),
                        source_content=source_content_str,
                    )
                except Exception as e:
                    print(f"  Action entry failed: {e}")

            # Update thesis tracker with new evidence + conviction assessments
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

            # Create new thesis threads if suggested
            for nts in digest.get("new_thesis_suggestions", []):
                try:
                    create_thesis_thread(
                        thread_name=nts["thread_name"],
                        core_thesis=nts.get("core_thesis", ""),
                        key_questions=nts.get("key_questions"),
                        connected_buckets=nts.get("connected_buckets"),
                        discovery_source="Content Pipeline",
                        conviction="New",
                    )
                    # Also append the initial evidence as a block
                    if nts.get("initial_evidence"):
                        update_thesis_tracker(
                            thesis_name=nts["thread_name"],
                            new_evidence=f"Initial signal from '{title}': {nts['initial_evidence']}",
                            evidence_direction=nts.get("evidence_direction", "for"),
                        )
                except Exception as e:
                    print(f"  New thesis creation failed: {e}")

        # 5. Log to preference store
        if HAS_POSTGRES:
            for action in digest.get("proposed_actions", []):
                try:
                    log_outcome(
                        action_text=action["action"],
                        action_type=action.get("type", "content"),
                        outcome="proposed",
                        score=action.get("score", 0.0),
                        scoring_factors={
                            "bucket_impact": action.get("score", 0.0),
                            "source": "content_agent",
                        },
                        source_digest_slug=digest.get("slug"),
                        company=action.get("company"),
                        thesis_thread=" | ".join(action.get("thesis_connections", [])) or action.get("thesis_connection"),
                    )
                except Exception as e:
                    print(f"  Preference log failed: {e}")

        results.append(digest)

    return results


def main():
    parser = argparse.ArgumentParser(description="ContentAgent — AI CoS content analysis runner")
    parser.add_argument("--queue-dir", default=DEFAULT_QUEUE_DIR, help="Queue directory")
    parser.add_argument("--dry-run", action="store_true", help="Analyze only, don't publish")
    parser.add_argument("--file", help="Process a specific extraction JSON file")
    args = parser.parse_args()

    queue_dir = Path(args.queue_dir)
    processed_dir = queue_dir / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)

    # Load system prompt (reads CONTEXT.md sections directly — no regex parsing)
    print("Loading system prompt + CONTEXT.md...")
    system_prompt = load_system_prompt()
    print(f"  CONTEXT.md path: {CONTEXT_MD_PATH}")
    print(f"  Prompt length: {len(system_prompt):,} chars")

    # Find extraction files to process
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
        results = process_extraction(extraction_file, system_prompt, dry_run=args.dry_run)
        total_digests += len(results)

        # Move to processed/
        if not args.dry_run and results:
            dest = processed_dir / extraction_file.name
            shutil.move(str(extraction_file), str(dest))
            print(f"  Moved to {dest}")

    print(f"\nDone! Processed {total_digests} digest(s) from {len(files)} extraction file(s)")


if __name__ == "__main__":
    main()
