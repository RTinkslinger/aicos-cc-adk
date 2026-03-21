#!/usr/bin/env python3
"""
Execute enrichment updates by calling the batch_update_agent_notes function
via Supabase REST API.
"""

import json
import os
import sys
import time
import urllib.request
import urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from enrich_embeddings import extract_meaningful_content

COMPANIES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "companies-pages")
MAPPING_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "enrichment-sql", "company_mapping.json")

SUPABASE_URL = "https://llfkxnsfczludgigknbs.supabase.co"
ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxsZmt4bnNmY3psdWRnaWdrbmJzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzM4OTczNDksImV4cCI6MjA4OTQ3MzM0OX0.EjLP6wfUU7di-M19VijYjWQfx73A36O9Nrt9qzO5TmY"

BATCH_SIZE = 10


def call_rpc(function_name: str, params: dict) -> dict:
    """Call a Supabase RPC function."""
    url = f"{SUPABASE_URL}/rest/v1/rpc/{function_name}"
    headers = {
        "apikey": ANON_KEY,
        "Authorization": f"Bearer {ANON_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }
    data = json.dumps(params).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        return {"error": str(e), "body": error_body}


def execute_sql_via_rest(sql: str) -> dict:
    """Execute raw SQL via the Supabase REST API (requires service_role key)."""
    # The REST API doesn't support raw SQL with anon key
    # We need to use the RPC function approach
    pass


def main():
    with open(MAPPING_FILE) as f:
        mapping = json.load(f)

    # Process each company
    enriched: list[dict] = []

    for entry in mapping:
        company_id = entry["id"]
        page_path = entry["page_content_path"]
        filepath = os.path.join(os.path.dirname(COMPANIES_DIR), page_path)

        if not os.path.exists(filepath):
            continue

        content = extract_meaningful_content(filepath)
        if not content:
            continue

        enriched.append({"id": str(company_id), "content": content})

    print(f"Total enrichable companies: {len(enriched)}")

    # Process in batches
    total_updated = 0
    for i in range(0, len(enriched), BATCH_SIZE):
        batch = enriched[i:i + BATCH_SIZE]
        batch_ids = [b["id"] for b in batch]

        result = call_rpc("batch_update_agent_notes", {"updates": batch})

        if isinstance(result, dict) and "error" in result:
            print(f"  Batch {i // BATCH_SIZE}: ERROR - {result}")
            # Try to continue
        else:
            count = result if isinstance(result, int) else 0
            total_updated += count
            print(f"  Batch {i // BATCH_SIZE}: Updated {count} companies (ids: {batch_ids[0]}..{batch_ids[-1]})")

        # Small delay between batches
        time.sleep(0.5)

    print(f"\nTotal updated: {total_updated}")


if __name__ == "__main__":
    main()
