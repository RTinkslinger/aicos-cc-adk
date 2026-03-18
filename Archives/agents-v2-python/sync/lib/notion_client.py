from __future__ import annotations

"""Notion REST API wrapper for AI CoS databases.

Direct API access for Content Digest DB, Actions Queue, and Thesis Tracker.
Used by Agent SDK runners to create entries without going through MCP.

Uses notion-client v3 (data_source_id parent, data_sources.query).
Requires NOTION_TOKEN env var (internal integration token).
"""

import os
from datetime import datetime, timezone
from typing import Any, Optional

from notion_client import Client

from shared.logging import get_trace_id

NOTION_TOKEN = os.getenv("NOTION_TOKEN", "")

# Database IDs
CONTENT_DIGEST_DB = "df2d73d6-e020-46e8-9a8a-7b9da48b6ee2"
ACTIONS_QUEUE_DB = "1df4858c-6629-4283-b31d-50c5e7ef885d"
THESIS_TRACKER_DB = "3c8d1a34-e723-4fb1-be28-727777c22ec6"
NETWORK_DB = "6462102f-112b-40e9-8984-7cb1e8fe5e8b"
COMPANIES_DB = "1edda9cc-df8b-41e1-9c08-22971495aa43"


def _get_client() -> Client:
    if not NOTION_TOKEN:
        raise ValueError("NOTION_TOKEN not set. Create at notion.so/profile/integrations")
    return Client(auth=NOTION_TOKEN)


def _truncate_rich_text(text: str, limit: int = 2000) -> str:
    """Truncate text to Notion's 2000-char rich_text limit."""
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def create_digest_entry(
    title: str,
    slug: str,
    url: str,
    channel: str,
    relevance_score: str,
    net_newness: str,
    connected_buckets: list[str],
    digest_url: str,
    content_type: str = "",
    duration: str = "",
    summary: str = "",
    key_insights: str = "",
    thesis_connections: str = "",
    portfolio_relevance: str = "",
    essence_notes: str = "",
    watch_sections: str = "",
    contra_signals: str = "",
    rabbit_holes: str = "",
    proposed_actions_summary: str = "",
    processing_date: str | None = None,
    upload_date: str | None = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Create a Content Digest DB entry with all available fields."""
    # TODO: Add request_id column to notion_digest_entries (or actions_queue) if idempotency needed at DB level
    client = _get_client()

    properties: dict[str, Any] = {
        "Video Title": {"title": [{"text": {"content": title}}]},
        "Video URL": {"url": url},
        "Channel": {"rich_text": [{"text": {"content": channel}}]},
        "Relevance Score": {"select": {"name": relevance_score}},
        "Net Newness": {"select": {"name": net_newness}},
        "Digest URL": {"url": digest_url},
        "Discovery Source": {"select": {"name": "YouTube"}},
        "Action Status": {"select": {"name": "Pending"}},
    }

    if connected_buckets:
        properties["Connected Buckets"] = {
            "multi_select": [{"name": b} for b in connected_buckets]
        }

    if content_type:
        properties["Content Type"] = {"select": {"name": content_type}}

    if duration:
        properties["Duration"] = {"rich_text": [{"text": {"content": duration}}]}

    if summary:
        properties["Summary"] = {"rich_text": [{"text": {"content": _truncate_rich_text(summary)}}]}

    if key_insights:
        properties["Key Insights"] = {"rich_text": [{"text": {"content": _truncate_rich_text(key_insights)}}]}

    if thesis_connections:
        properties["Thesis Connections"] = {"rich_text": [{"text": {"content": _truncate_rich_text(thesis_connections)}}]}

    if portfolio_relevance:
        properties["Portfolio Relevance"] = {"rich_text": [{"text": {"content": _truncate_rich_text(portfolio_relevance)}}]}

    if essence_notes:
        properties["Essence Notes"] = {"rich_text": [{"text": {"content": _truncate_rich_text(essence_notes)}}]}

    if watch_sections:
        properties["Watch These Sections"] = {"rich_text": [{"text": {"content": _truncate_rich_text(watch_sections)}}]}

    if contra_signals:
        properties["Contra Signals"] = {"rich_text": [{"text": {"content": _truncate_rich_text(contra_signals)}}]}

    if rabbit_holes:
        properties["Rabbit Holes"] = {"rich_text": [{"text": {"content": _truncate_rich_text(rabbit_holes)}}]}

    if proposed_actions_summary:
        properties["Proposed Actions"] = {"rich_text": [{"text": {"content": _truncate_rich_text(proposed_actions_summary)}}]}

    if processing_date:
        properties["date:Processing Date:start"] = processing_date
        properties["date:Processing Date:is_datetime"] = 0

    if upload_date:
        properties["date:Upload Date:start"] = upload_date
        properties["date:Upload Date:is_datetime"] = 0

    page = client.pages.create(
        parent={"data_source_id": CONTENT_DIGEST_DB},
        properties=properties,
    )
    print(f"Created Content Digest entry: {title}")
    return page


# Action Type mapping: Claude's output → Notion select option
ACTION_TYPE_MAP = {
    "research": "Research",
    "meeting": "Meeting/Outreach",
    "meeting/outreach": "Meeting/Outreach",
    "thesis-update": "Thesis Update",
    "thesis update": "Thesis Update",
    "follow-up": "Content Follow-up",
    "content": "Content Follow-up",
    "content follow-up": "Content Follow-up",
    "portfolio-checkin": "Portfolio Check-in",
    "portfolio check-in": "Portfolio Check-in",
    "follow-on": "Follow-on Eval",
    "follow-on eval": "Follow-on Eval",
    "pipeline": "Pipeline Action",
    "pipeline action": "Pipeline Action",
}

# Priority mapping: Claude's short form → Notion select option
PRIORITY_MAP = {
    "P0": "P0 - Act Now",
    "P1": "P1 - This Week",
    "P2": "P2 - This Month",
    "P3": "P3 - Backlog",
}

# Assignment logic: action types that the AI agent can handle autonomously
AGENT_ASSIGNABLE_TYPES = {"Research", "Thesis Update", "Content Follow-up"}


def create_action_entry(
    action_text: str,
    priority: str,
    action_type: str,
    assigned_to: str = "Aakash",
    company_name: str | None = None,
    thesis_connection: str | None = None,
    source_digest_page_id: str | None = None,
    relevance_score: float | None = None,
    reasoning: str = "",
    source_content: str = "",
    request_id: str | None = None,
) -> dict[str, Any]:
    """Create an Actions Queue entry with full field coverage."""
    # TODO: Add request_id column to actions_queue table for idempotency check
    client = _get_client()

    # Normalize action type and priority to match Notion select options
    notion_action_type = ACTION_TYPE_MAP.get(action_type.lower(), action_type)
    notion_priority = PRIORITY_MAP.get(priority, priority)

    # Assignment logic: Agent gets research/thesis/content tasks, Aakash gets human-required ones
    if assigned_to == "Agent" or (assigned_to == "Aakash" and notion_action_type in AGENT_ASSIGNABLE_TYPES):
        notion_assigned_to = "Agent"
    else:
        notion_assigned_to = assigned_to

    properties: dict[str, Any] = {
        "Action": {"title": [{"text": {"content": action_text}}]},
        "Priority": {"select": {"name": notion_priority}},
        "Action Type": {"select": {"name": notion_action_type}},
        "Assigned To": {"select": {"name": notion_assigned_to}},
        "Status": {"select": {"name": "Proposed"}},
        "Source": {"select": {"name": "Content Processing"}},
        "Created By": {"select": {"name": "AI CoS"}},
    }

    if thesis_connection:
        properties["Thesis Connection"] = {
            "rich_text": [{"text": {"content": _truncate_rich_text(thesis_connection)}}]
        }

    if source_digest_page_id:
        properties["Source Digest"] = {
            "relation": [{"id": source_digest_page_id}]
        }

    if relevance_score is not None:
        # Score is 0-10 from scoring model, Notion field is 0-100
        properties["Relevance Score"] = {"number": min(100, round(relevance_score * 10))}

    if reasoning:
        properties["Reasoning"] = {
            "rich_text": [{"text": {"content": _truncate_rich_text(reasoning)}}]
        }

    if source_content:
        properties["Source Content"] = {
            "rich_text": [{"text": {"content": _truncate_rich_text(source_content)}}]
        }

    # Company relation lookup — search by name, set relation if found
    if company_name:
        try:
            matches = search_companies(company_name, limit=1)
            if matches:
                properties["Company"] = {
                    "relation": [{"id": matches[0]["id"]}]
                }
        except Exception:
            pass  # Non-blocking — company lookup is best-effort

    page = client.pages.create(
        parent={"data_source_id": ACTIONS_QUEUE_DB},
        properties=properties,
    )
    print(f"Created Action: [{notion_priority}] [{notion_assigned_to}] {action_text[:50]}")
    return page


CONVICTION_OPTIONS = {"New", "Evolving", "Evolving Fast", "Low", "Medium", "High"}


def create_thesis_thread(
    thread_name: str,
    core_thesis: str,
    key_questions: list[str] | None = None,
    connected_buckets: list[str] | None = None,
    discovery_source: str = "Content Pipeline",
    conviction: str = "New",
    request_id: str | None = None,
) -> dict[str, Any]:
    """Create a new thesis thread autonomously.

    AI creates freely at Conviction='New'. Key questions are added as page
    content blocks in [OPEN] format. The Key Question property holds a summary count.
    """
    # TODO: Add request_id column to thesis_threads table for idempotency check
    client = _get_client()

    if conviction not in CONVICTION_OPTIONS:
        conviction = "New"

    properties: dict[str, Any] = {
        "Thread Name": {"title": [{"text": {"content": thread_name}}]},
        "Core Thesis": {"rich_text": [{"text": {"content": _truncate_rich_text(core_thesis)}}]},
        "Conviction": {"select": {"name": conviction}},
        "Status": {"select": {"name": "Exploring"}},
        "Discovery Source": {"select": {"name": discovery_source}},
        "Date Discovered": {"date": {"start": datetime.now(timezone.utc).strftime("%Y-%m-%d")}},
    }

    if connected_buckets:
        properties["Connected Buckets"] = {
            "multi_select": [{"name": b} for b in connected_buckets]
        }

    page = client.pages.create(
        parent={"data_source_id": THESIS_TRACKER_DB},
        properties=properties,
    )
    page_id = page["id"]
    print(f"Created thesis thread: {thread_name} [Conviction={conviction}]")

    # Add key questions as page content blocks
    if key_questions:
        blocks = []
        for q in key_questions:
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"text": {"content": f"[OPEN] {q}"}}]
                },
            })
        client.blocks.children.append(block_id=page_id, children=blocks)

        # Update Key Question property with summary count
        client.pages.update(
            page_id=page_id,
            properties={
                "Key Question": {
                    "rich_text": [{"text": {"content": f"{len(key_questions)} open questions — see page body"}}]
                }
            },
        )

    return page


def update_thesis_tracker(
    thesis_name: str,
    new_evidence: str,
    evidence_direction: str = "for",
    source: str = "ContentAgent",
    conviction: str | None = None,
    new_key_questions: list[str] | None = None,
    answered_questions: list[str] | None = None,
    investment_implications: str | None = None,
    key_companies: str | None = None,
    request_id: str | None = None,
) -> Optional[dict[str, Any]]:
    """Update an existing thesis thread with new evidence and optionally update conviction.

    Enhanced for AI-managed conviction engine:
    - Appends evidence block to page body
    - Optionally updates Conviction select
    - Adds new key questions as [OPEN] blocks
    - Marks answered questions (updates block text to [ANSWERED])
    - Updates Investment Implications, Key Companies if provided
    - Appends to Evidence For/Against property text
    """
    # TODO: Add request_id column to thesis_threads table for idempotency check
    client = _get_client()

    results = client.data_sources.query(
        data_source_id=THESIS_TRACKER_DB,
        filter={
            "property": "Thread Name",
            "title": {"contains": thesis_name},
        },
    )

    if not results.get("results"):
        print(f"Thesis '{thesis_name}' not found in tracker")
        return None

    page = results["results"][0]
    page_id = page["id"]

    # 1. Append evidence block to page body
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    evidence_block = {
        "object": "block",
        "type": "paragraph",
        "paragraph": {
            "rich_text": [
                {"text": {"content": _truncate_rich_text(
                    f"[{timestamp}] [{source}] ({evidence_direction}) {new_evidence}"
                )}}
            ]
        },
    }
    blocks_to_append = [evidence_block]

    # 2. Add new key questions as [OPEN] blocks
    if new_key_questions:
        for q in new_key_questions:
            blocks_to_append.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"text": {"content": f"[OPEN] {q}"}}]
                },
            })

    client.blocks.children.append(block_id=page_id, children=blocks_to_append)

    # 3. Mark answered questions — scan existing blocks for matching [OPEN] text
    if answered_questions:
        _mark_questions_answered(client, page_id, answered_questions)

    # 4. Update page properties
    props_update: dict[str, Any] = {}

    if conviction and conviction in CONVICTION_OPTIONS:
        props_update["Conviction"] = {"select": {"name": conviction}}

    # Append to Evidence For/Against
    props = page.get("properties", {})
    if evidence_direction in ("for", "mixed"):
        existing = _extract_plain_text(props.get("Evidence For", {}), "rich_text")
        new_text = f"{existing}\n+ {new_evidence}" if existing else f"+ {new_evidence}"
        props_update["Evidence For"] = {
            "rich_text": [{"text": {"content": _truncate_rich_text(new_text)}}]
        }
    if evidence_direction in ("against", "mixed"):
        existing = _extract_plain_text(props.get("Evidence Against", {}), "rich_text")
        new_text = f"{existing}\n? {new_evidence}" if existing else f"? {new_evidence}"
        props_update["Evidence Against"] = {
            "rich_text": [{"text": {"content": _truncate_rich_text(new_text)}}]
        }

    if investment_implications:
        existing = _extract_plain_text(props.get("Investment Implications", {}), "rich_text")
        new_text = f"{existing}\n{investment_implications}" if existing else investment_implications
        props_update["Investment Implications"] = {
            "rich_text": [{"text": {"content": _truncate_rich_text(new_text)}}]
        }

    if key_companies:
        existing = _extract_plain_text(props.get("Key Companies", {}), "rich_text")
        if key_companies not in existing:
            new_text = f"{existing}, {key_companies}" if existing else key_companies
            props_update["Key Companies"] = {
                "rich_text": [{"text": {"content": _truncate_rich_text(new_text)}}]
            }

    if props_update:
        client.pages.update(page_id=page_id, properties=props_update)

    conviction_str = f", conviction→{conviction}" if conviction else ""
    print(f"Updated thesis '{thesis_name}' ({evidence_direction}{conviction_str})")
    return page


def _mark_questions_answered(
    client: Client, page_id: str, answered_questions: list[str]
) -> None:
    """Scan page blocks for [OPEN] questions matching answered list, update to [ANSWERED]."""
    try:
        blocks = client.blocks.children.list(block_id=page_id)
        for block in blocks.get("results", []):
            if block.get("type") != "paragraph":
                continue
            rich_text = block.get("paragraph", {}).get("rich_text", [])
            if not rich_text:
                continue
            text = rich_text[0].get("plain_text", "")
            if not text.startswith("[OPEN]"):
                continue
            question_text = text[7:].strip()  # Remove "[OPEN] " prefix
            for aq in answered_questions:
                if aq.lower() in question_text.lower() or question_text.lower() in aq.lower():
                    client.blocks.update(
                        block_id=block["id"],
                        paragraph={
                            "rich_text": [{"text": {"content": f"[ANSWERED] {question_text}"}}]
                        },
                    )
                    print(f"  Marked question answered: {question_text[:50]}")
                    break
    except Exception as e:
        print(f"  Warning: failed to mark questions answered: {e}")


def _extract_plain_text(prop: dict[str, Any], prop_type: str) -> str:
    """Extract plain text from a Notion property value."""
    if prop_type == "title":
        return prop.get("title", [{}])[0].get("plain_text", "") if prop.get("title") else ""
    if prop_type == "rich_text":
        parts = prop.get("rich_text", [])
        return " ".join(p.get("plain_text", "") for p in parts) if parts else ""
    if prop_type == "select":
        sel = prop.get("select")
        return sel.get("name", "") if sel else ""
    if prop_type == "multi_select":
        return ", ".join(s.get("name", "") for s in prop.get("multi_select", []))
    return ""


def fetch_thesis_threads(include_key_questions: bool = False) -> list[dict[str, Any]]:
    """Fetch all active thesis threads from Notion Thesis Tracker.

    Returns list of dicts with: name, status, conviction, core_thesis,
    key_question, key_companies, connected_buckets, evidence_for,
    evidence_against, investment_implications.

    If include_key_questions=True, also reads page blocks to get
    individual [OPEN] and [ANSWERED] key questions (slower — one API call per thread).
    """
    client = _get_client()

    # Query all threads (no filter — we want Active + Exploring)
    results = client.data_sources.query(
        data_source_id=THESIS_TRACKER_DB,
        page_size=50,
    )

    threads: list[dict[str, Any]] = []
    for page in results.get("results", []):
        props = page.get("properties", {})
        thread: dict[str, Any] = {
            "id": page.get("id", ""),
            "name": _extract_plain_text(props.get("Thread Name", {}), "title"),
            "status": _extract_plain_text(props.get("Status", {}), "select"),
            "conviction": _extract_plain_text(props.get("Conviction", {}), "select"),
            "core_thesis": _extract_plain_text(props.get("Core Thesis", {}), "rich_text"),
            "key_question": _extract_plain_text(props.get("Key Question", {}), "rich_text"),
            "key_companies": _extract_plain_text(props.get("Key Companies", {}), "rich_text"),
            "connected_buckets": _extract_plain_text(props.get("Connected Buckets", {}), "multi_select"),
            "evidence_for": _extract_plain_text(props.get("Evidence For", {}), "rich_text"),
            "evidence_against": _extract_plain_text(props.get("Evidence Against", {}), "rich_text"),
            "investment_implications": _extract_plain_text(props.get("Investment Implications", {}), "rich_text"),
        }
        # Skip archived/empty
        if thread["name"] and thread["status"] != "Archived":
            # Optionally fetch key questions from page blocks
            if include_key_questions:
                thread["open_questions"] = []
                thread["answered_questions"] = []
                try:
                    blocks = client.blocks.children.list(block_id=page["id"])
                    for block in blocks.get("results", []):
                        if block.get("type") != "paragraph":
                            continue
                        rt = block.get("paragraph", {}).get("rich_text", [])
                        if not rt:
                            continue
                        text = rt[0].get("plain_text", "")
                        if text.startswith("[OPEN]"):
                            thread["open_questions"].append(text[7:].strip())
                        elif text.startswith("[ANSWERED]"):
                            thread["answered_questions"].append(text[11:].strip())
                except Exception:
                    pass
            threads.append(thread)

    print(f"Fetched {len(threads)} thesis threads from Notion")
    return threads


def seed_thesis_threads_to_postgres() -> int:
    """One-time seed: pull all thesis threads from Notion into Postgres.

    Skips threads that already exist in Postgres (by notion_page_id).
    Returns count of newly inserted threads.
    """
    from sync.lib.thesis_db import create_thread, set_notion_page_id

    client = _get_client()
    results = client.data_sources.query(
        data_source_id=THESIS_TRACKER_DB,
        page_size=50,
    )

    inserted = 0
    for page in results.get("results", []):
        page_id = page.get("id", "")
        props = page.get("properties", {})
        name = _extract_plain_text(props.get("Thread Name", {}), "title")
        if not name:
            continue

        # Check if already in Postgres
        from sync.lib.thesis_db import find_thread_by_name
        existing = find_thread_by_name(name)
        if existing and existing.get("notion_page_id"):
            continue

        status = _extract_plain_text(props.get("Status", {}), "select")
        conviction = _extract_plain_text(props.get("Conviction", {}), "select")
        core_thesis = _extract_plain_text(props.get("Core Thesis", {}), "rich_text")
        discovery_source = _extract_plain_text(props.get("Discovery Source", {}), "select") or "Content Pipeline"
        buckets_str = _extract_plain_text(props.get("Connected Buckets", {}), "multi_select")
        connected_buckets = [b.strip() for b in buckets_str.split(",") if b.strip()] if buckets_str else []

        # Read key questions from page blocks
        open_qs = []
        answered_qs = []
        try:
            blocks = client.blocks.children.list(block_id=page_id)
            for block in blocks.get("results", []):
                if block.get("type") != "paragraph":
                    continue
                rt = block.get("paragraph", {}).get("rich_text", [])
                if not rt:
                    continue
                text = rt[0].get("plain_text", "")
                if text.startswith("[OPEN]"):
                    open_qs.append(text[7:].strip())
                elif text.startswith("[ANSWERED]"):
                    answered_qs.append(text[11:].strip())
        except Exception:
            pass

        try:
            row = create_thread(
                thread_name=name,
                core_thesis=core_thesis,
                conviction=conviction or "New",
                status=status or "Exploring",
                discovery_source=discovery_source,
                connected_buckets=connected_buckets,
                key_questions=open_qs,
                notion_page_id=page_id,
            )
            # Also copy over existing evidence/companies/implications
            import psycopg2
            import psycopg2.extras
            conn = psycopg2.connect(os.getenv("DATABASE_URL", ""))
            with conn.cursor() as cur:
                cur.execute(
                    """UPDATE thesis_threads SET
                        evidence_for = %s,
                        evidence_against = %s,
                        key_companies = %s,
                        investment_implications = %s,
                        key_questions_json = %s::jsonb,
                        last_synced_at = NOW()
                    WHERE id = %s""",
                    (
                        _extract_plain_text(props.get("Evidence For", {}), "rich_text"),
                        _extract_plain_text(props.get("Evidence Against", {}), "rich_text"),
                        _extract_plain_text(props.get("Key Companies", {}), "rich_text"),
                        _extract_plain_text(props.get("Investment Implications", {}), "rich_text"),
                        __import__("json").dumps({"open": open_qs, "answered": answered_qs}),
                        row["id"],
                    ),
                )
            conn.commit()
            conn.close()
            inserted += 1
            print(f"Seeded thesis: {name} [page_id={page_id}]")
        except Exception as e:
            print(f"Failed to seed thesis '{name}': {e}")

    print(f"Seed complete: {inserted} new threads inserted")
    return inserted


def sync_thesis_status_from_notion() -> list[dict[str, str]]:
    """Pull Status field from Notion for all thesis threads and update Postgres.

    Status is the only human-owned field. This syncs Notion → Postgres.
    Returns list of changes detected.
    """
    from sync.lib.thesis_db import update_status_from_notion

    client = _get_client()
    results = client.data_sources.query(
        data_source_id=THESIS_TRACKER_DB,
        page_size=50,
    )

    changes = []
    for page in results.get("results", []):
        page_id = page.get("id", "")
        props = page.get("properties", {})
        name = _extract_plain_text(props.get("Thread Name", {}), "title")
        status = _extract_plain_text(props.get("Status", {}), "select")
        if page_id and status:
            try:
                update_status_from_notion(page_id, status)
                changes.append({"page_id": page_id, "name": name, "status": status})
            except Exception as e:
                print(f"Failed to sync status for {name}: {e}")

    print(f"Synced status for {len(changes)} thesis threads from Notion")
    return changes


def sync_actions_from_notion() -> dict[str, int]:
    """Pull all actions from Notion into Postgres (upsert).

    Used for bidirectional sync: picks up status changes made in Notion.
    Returns counts of inserted and updated records.
    """
    from sync.lib.actions_db import upsert_from_notion

    client = _get_client()
    results = client.data_sources.query(
        data_source_id=ACTIONS_QUEUE_DB,
        page_size=100,
    )

    inserted = 0
    updated = 0
    for page in results.get("results", []):
        page_id = page.get("id", "")
        props = page.get("properties", {})
        action_text = _extract_plain_text(props.get("Action", {}), "title")
        if not action_text:
            continue

        # Check if this is a new insert or update
        from sync.lib.actions_db import find_action_by_notion_id
        existing = find_action_by_notion_id(page_id)

        try:
            upsert_from_notion(
                notion_page_id=page_id,
                action=action_text,
                action_type=_extract_plain_text(props.get("Action Type", {}), "select"),
                status=_extract_plain_text(props.get("Status", {}), "select"),
                priority=_extract_plain_text(props.get("Priority", {}), "select"),
                source=_extract_plain_text(props.get("Source", {}), "select"),
                assigned_to=_extract_plain_text(props.get("Assigned To", {}), "select"),
                created_by=_extract_plain_text(props.get("Created By", {}), "select"),
                reasoning=_extract_plain_text(props.get("Reasoning", {}), "rich_text"),
                source_content=_extract_plain_text(props.get("Source Content", {}), "rich_text"),
                thesis_connection=_extract_plain_text(props.get("Thesis Connection", {}), "rich_text"),
                relevance_score=props.get("Relevance Score", {}).get("number"),
                outcome=_extract_plain_text(props.get("Outcome", {}), "select"),
            )
            if existing:
                updated += 1
            else:
                inserted += 1
        except Exception as e:
            print(f"Failed to sync action '{action_text[:50]}': {e}")

    print(f"Actions sync: {inserted} inserted, {updated} updated")
    return {"inserted": inserted, "updated": updated}


def push_action_to_notion(pg_action: dict[str, Any], request_id: str | None = None) -> Optional[str]:
    """Push a Postgres-created action to Notion. Returns Notion page ID."""
    # TODO: Add request_id column to actions_queue table for idempotency check
    client = _get_client()

    properties: dict[str, Any] = {
        "Action": {"title": [{"text": {"content": pg_action["action"]}}]},
    }

    if pg_action.get("action_type"):
        properties["Action Type"] = {"select": {"name": pg_action["action_type"]}}
    if pg_action.get("status"):
        properties["Status"] = {"select": {"name": pg_action["status"]}}
    if pg_action.get("priority"):
        properties["Priority"] = {"select": {"name": pg_action["priority"]}}
    if pg_action.get("source"):
        properties["Source"] = {"select": {"name": pg_action["source"]}}
    if pg_action.get("assigned_to"):
        properties["Assigned To"] = {"select": {"name": pg_action["assigned_to"]}}
    if pg_action.get("created_by"):
        properties["Created By"] = {"select": {"name": pg_action["created_by"]}}
    if pg_action.get("reasoning"):
        properties["Reasoning"] = {"rich_text": [{"text": {"content": _truncate_rich_text(pg_action["reasoning"])}}]}
    if pg_action.get("source_content"):
        properties["Source Content"] = {"rich_text": [{"text": {"content": _truncate_rich_text(pg_action["source_content"])}}]}
    if pg_action.get("thesis_connection"):
        properties["Thesis Connection"] = {"rich_text": [{"text": {"content": _truncate_rich_text(pg_action["thesis_connection"])}}]}
    if pg_action.get("relevance_score") is not None:
        properties["Relevance Score"] = {"number": pg_action["relevance_score"]}

    # Relations
    if pg_action.get("company_notion_id"):
        properties["Company"] = {"relation": [{"id": pg_action["company_notion_id"]}]}
    if pg_action.get("source_digest_notion_id"):
        properties["Source Digest"] = {"relation": [{"id": pg_action["source_digest_notion_id"]}]}

    page = client.pages.create(
        parent={"data_source_id": ACTIONS_QUEUE_DB},
        properties=properties,
    )
    print(f"Pushed action to Notion: {pg_action['action'][:50]}")
    return page.get("id", "")


def search_companies(query: str, limit: int = 5) -> list[dict[str, Any]]:
    """Search Companies DB for portfolio matches."""
    client = _get_client()
    results = client.data_sources.query(
        data_source_id=COMPANIES_DB,
        filter={
            "property": "Name",
            "title": {"contains": query},
        },
        page_size=limit,
    )
    return [
        {
            "id": r["id"],
            "name": r["properties"].get("Name", {}).get("title", [{}])[0].get("plain_text", ""),
        }
        for r in results.get("results", [])
    ]


def fetch_recent_digests(limit: int = 10) -> list[dict[str, Any]]:
    """Fetch recent Content Digest entries from Notion.

    Returns list of dicts with key fields, sorted by Processing Date descending.
    """
    client = _get_client()

    results = client.data_sources.query(
        data_source_id=CONTENT_DIGEST_DB,
        page_size=limit,
        sorts=[{"property": "Processing Date", "direction": "descending"}],
    )

    digests: list[dict[str, Any]] = []
    for page in results.get("results", []):
        props = page.get("properties", {})
        digests.append({
            "id": page.get("id", ""),
            "title": _extract_plain_text(props.get("Video Title", {}), "title"),
            "channel": _extract_plain_text(props.get("Channel", {}), "rich_text"),
            "relevance_score": _extract_plain_text(props.get("Relevance Score", {}), "select"),
            "net_newness": _extract_plain_text(props.get("Net Newness", {}), "select"),
            "content_type": _extract_plain_text(props.get("Content Type", {}), "select"),
            "action_status": _extract_plain_text(props.get("Action Status", {}), "select"),
            "connected_buckets": _extract_plain_text(props.get("Connected Buckets", {}), "multi_select"),
            "summary": _extract_plain_text(props.get("Summary", {}), "rich_text")[:300],
            "digest_url": props.get("Digest URL", {}).get("url", ""),
            "video_url": props.get("Video URL", {}).get("url", ""),
        })

    print(f"Fetched {len(digests)} recent digests from Notion")
    return digests


def fetch_actions(status_filter: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
    """Fetch Actions Queue entries from Notion.

    Args:
        status_filter: Optional status to filter by (Proposed, Accepted, In Progress, Done, Dismissed)
        limit: Max number of actions to return
    """
    client = _get_client()

    query_kwargs: dict[str, Any] = {
        "data_source_id": ACTIONS_QUEUE_DB,
        "page_size": limit,
    }

    if status_filter:
        query_kwargs["filter"] = {
            "property": "Status",
            "select": {"equals": status_filter},
        }

    results = client.data_sources.query(**query_kwargs)

    actions: list[dict[str, Any]] = []
    for page in results.get("results", []):
        props = page.get("properties", {})
        actions.append({
            "id": page.get("id", ""),
            "action": _extract_plain_text(props.get("Action", {}), "title"),
            "priority": _extract_plain_text(props.get("Priority", {}), "select"),
            "status": _extract_plain_text(props.get("Status", {}), "select"),
            "action_type": _extract_plain_text(props.get("Action Type", {}), "select"),
            "assigned_to": _extract_plain_text(props.get("Assigned To", {}), "select"),
            "reasoning": _extract_plain_text(props.get("Reasoning", {}), "rich_text")[:300],
            "thesis_connection": _extract_plain_text(props.get("Thesis Connection", {}), "rich_text"),
            "source": _extract_plain_text(props.get("Source", {}), "select"),
            "outcome": _extract_plain_text(props.get("Outcome", {}), "select"),
        })

    print(f"Fetched {len(actions)} actions from Notion")
    return actions
