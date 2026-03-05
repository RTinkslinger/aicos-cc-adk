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


def create_digest_entry(
    title: str,
    slug: str,
    url: str,
    channel: str,
    relevance_score: str,
    net_newness: str,
    connected_buckets: list[str],
    digest_url: str,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Create a Content Digest DB entry.

    Schema: Video Title (title), Video URL, Channel, Relevance Score (select),
    Net Newness (select), Digest URL, Discovery Source (select),
    Action Status (select), Connected Buckets (multi_select).
    """
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

    page = client.pages.create(
        parent={"data_source_id": CONTENT_DIGEST_DB},
        properties=properties,
    )
    print(f"Created Content Digest entry: {title}")
    return page


def create_action_entry(
    action_text: str,
    priority: str,
    action_type: str,
    assigned_to: str = "Aakash",
    company: str | None = None,
    thesis_connection: str | None = None,
    source_digest_page_id: str | None = None,
) -> dict[str, Any]:
    """Create an Actions Queue entry.

    Schema: Action (title), Priority (select), Action Type (select),
    Assigned To (select), Status (select), Source (select),
    Thesis Connection (rich_text), Source Digest (relation).
    Company is a relation — skipped here (would need page ID lookup).
    """
    client = _get_client()

    properties: dict[str, Any] = {
        "Action": {"title": [{"text": {"content": action_text}}]},
        "Priority": {"select": {"name": priority}},
        "Action Type": {"select": {"name": action_type}},
        "Assigned To": {"select": {"name": assigned_to}},
        "Status": {"select": {"name": "Proposed"}},
        "Source": {"select": {"name": "ContentAgent"}},
    }

    if thesis_connection:
        properties["Thesis Connection"] = {"rich_text": [{"text": {"content": thesis_connection}}]}

    if source_digest_page_id:
        properties["Source Digest"] = {
            "relation": [{"id": source_digest_page_id}]
        }

    page = client.pages.create(
        parent={"data_source_id": ACTIONS_QUEUE_DB},
        properties=properties,
    )
    print(f"Created Action: [{priority}] {action_text[:60]}")
    return page


def update_thesis_tracker(
    thesis_name: str,
    new_evidence: str,
    evidence_direction: str = "for",
    source: str = "ContentAgent",
) -> Optional[dict[str, Any]]:
    """Update an existing thesis thread with new evidence.

    Schema: Thread Name (title). Searches by Thread Name, appends evidence block.
    """
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

    page_id = results["results"][0]["id"]

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    evidence_block = {
        "object": "block",
        "type": "paragraph",
        "paragraph": {
            "rich_text": [
                {"text": {"content": f"[{timestamp}] [{source}] ({evidence_direction}) {new_evidence}"}}
            ]
        },
    }

    client.blocks.children.append(block_id=page_id, children=[evidence_block])
    print(f"Updated thesis '{thesis_name}' with new evidence ({evidence_direction})")
    return results["results"][0]


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


def fetch_thesis_threads() -> list[dict[str, str]]:
    """Fetch all active thesis threads from Notion Thesis Tracker.

    Returns list of dicts with: name, status, conviction, core_thesis,
    key_question, key_companies, connected_buckets.
    """
    client = _get_client()

    # Query all threads (no filter — we want Active + Exploring)
    results = client.data_sources.query(
        data_source_id=THESIS_TRACKER_DB,
        page_size=50,
    )

    threads: list[dict[str, str]] = []
    for page in results.get("results", []):
        props = page.get("properties", {})
        thread = {
            "name": _extract_plain_text(props.get("Thread Name", {}), "title"),
            "status": _extract_plain_text(props.get("Status", {}), "select"),
            "conviction": _extract_plain_text(props.get("Conviction", {}), "select"),
            "core_thesis": _extract_plain_text(props.get("Core Thesis", {}), "rich_text"),
            "key_question": _extract_plain_text(props.get("Key Question", {}), "rich_text"),
            "key_companies": _extract_plain_text(props.get("Key Companies", {}), "rich_text"),
            "connected_buckets": _extract_plain_text(props.get("Connected Buckets", {}), "multi_select"),
        }
        # Skip archived/empty
        if thread["name"] and thread["status"] != "Archived":
            threads.append(thread)

    print(f"Fetched {len(threads)} thesis threads from Notion")
    return threads


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
