#!/usr/bin/env python3
"""
Paginate through Notion databases using the REST API.
Handles cursor-based pagination to extract ALL pages.
"""
import json
import sys
import time
import urllib.request
import urllib.error

import os
# Load from .env.local or environment
NOTION_TOKEN = os.environ.get("NOTION_TOKEN", "")
if not NOTION_TOKEN:
    env_path = os.path.join(os.path.dirname(__file__), "../../.env.local")
    if os.path.exists(env_path):
        for line in open(env_path):
            if line.startswith("NOTION_TOKEN="):
                NOTION_TOKEN = line.strip().split("=", 1)[1]
if not NOTION_TOKEN:
    print("ERROR: Set NOTION_TOKEN in .env.local or environment"); sys.exit(1)
NOTION_VERSION = "2022-06-28"

DATABASES = {
    "companies": {
        "id": "45a7e3ff56f54363b72cf44456786c60",
        "output": "/Users/Aakash/Claude Projects/Aakash AI CoS CC ADK/sql/data/companies-full-export.json"
    },
    "network": {
        "id": "d5f52503f23447b09701d9b354af9d1a",
        "output": "/Users/Aakash/Claude Projects/Aakash AI CoS CC ADK/sql/data/network-full-export.json"
    }
}


def query_database(db_id, start_cursor=None, page_size=100):
    """Query a Notion database with pagination support."""
    url = f"https://api.notion.com/v1/databases/{db_id}/query"

    body = {"page_size": page_size}
    if start_cursor:
        body["start_cursor"] = start_cursor

    data = json.dumps(body).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {NOTION_TOKEN}",
            "Notion-Version": NOTION_VERSION,
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        print(f"  HTTP {e.code}: {error_body[:200]}")
        raise


def extract_all_pages(db_name, db_config):
    """Extract all pages from a database using pagination."""
    db_id = db_config["id"]
    output_path = db_config["output"]

    print(f"\n{'='*60}")
    print(f"Extracting: {db_name} (DB ID: {db_id})")
    print(f"{'='*60}")

    all_pages = []
    cursor = None
    page_num = 0

    while True:
        page_num += 1
        print(f"  Page {page_num}: fetching (cursor={str(cursor)[:20] if cursor else 'None'})...", end=" ", flush=True)

        try:
            response = query_database(db_id, start_cursor=cursor)
        except Exception as e:
            print(f"ERROR: {e}")
            if page_num > 1:
                print(f"  Saving {len(all_pages)} pages collected so far...")
                break
            else:
                raise

        results = response.get("results", [])
        has_more = response.get("has_more", False)
        next_cursor = response.get("next_cursor")

        # Process results
        for page in results:
            page_id = page.get("id", "")
            page_url = page.get("url", "")
            properties = page.get("properties", {})

            all_pages.append({
                "notion_page_id": page_id,
                "notion_url": page_url,
                "properties": properties,
            })

        print(f"{len(results)} results (total: {len(all_pages)}, has_more: {has_more})")

        if not has_more or not next_cursor:
            break

        cursor = next_cursor
        # Small delay to be nice to the API
        time.sleep(0.3)

    # Save output
    print(f"\nSaving {len(all_pages)} pages to {output_path}")
    with open(output_path, "w") as f:
        json.dump(all_pages, f, indent=2, ensure_ascii=False)

    print(f"Done! {len(all_pages)} total pages extracted for {db_name}")
    return len(all_pages)


def main():
    # Allow selecting specific DB or all
    targets = sys.argv[1:] if len(sys.argv) > 1 else list(DATABASES.keys())

    totals = {}
    for db_name in targets:
        if db_name not in DATABASES:
            print(f"Unknown database: {db_name}. Available: {list(DATABASES.keys())}")
            continue
        count = extract_all_pages(db_name, DATABASES[db_name])
        totals[db_name] = count

    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    for name, count in totals.items():
        print(f"  {name}: {count} pages")


if __name__ == "__main__":
    main()
