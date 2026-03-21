#!/usr/bin/env python3
"""
Generate batched individual UPDATE statements for direct execution.
Each batch contains multiple single-row UPDATEs concatenated.
Target: ~30KB per batch file (fits in MCP tool limits).
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from enrich_embeddings import extract_meaningful_content

COMPANIES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "companies-pages")
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "enrichment-sql", "updates")
MAPPING_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "enrichment-sql", "company_mapping.json")
MAX_BATCH_BYTES = 30000  # ~30KB per batch


def escape_sql(s: str) -> str:
    return s.replace("'", "''")


def main():
    with open(MAPPING_FILE) as f:
        mapping = json.load(f)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Generate individual UPDATE statements
    updates: list[tuple[int, str]] = []

    for entry in mapping:
        company_id = entry["id"]
        page_path = entry["page_content_path"]
        filepath = os.path.join(os.path.dirname(COMPANIES_DIR), page_path)

        if not os.path.exists(filepath):
            continue

        content = extract_meaningful_content(filepath)
        if not content:
            continue

        escaped = escape_sql(content)
        sql = f"UPDATE companies SET agent_ids_notes = '{escaped}' WHERE id = {company_id} AND (agent_ids_notes IS NULL OR agent_ids_notes = '');\n"
        updates.append((company_id, sql))

    print(f"Total UPDATE statements: {len(updates)}")

    # Batch by size
    batch_idx = 0
    current_batch = ""
    current_ids: list[int] = []

    for cid, sql in updates:
        if len(current_batch) + len(sql) > MAX_BATCH_BYTES and current_batch:
            filepath = os.path.join(OUTPUT_DIR, f"update_{batch_idx:03d}.sql")
            with open(filepath, "w") as f:
                f.write(current_batch)
            print(f"  update_{batch_idx:03d}.sql: {len(current_batch)} bytes, {len(current_ids)} companies (ids: {current_ids[0]}..{current_ids[-1]})")
            batch_idx += 1
            current_batch = ""
            current_ids = []

        current_batch += sql
        current_ids.append(cid)

    if current_batch:
        filepath = os.path.join(OUTPUT_DIR, f"update_{batch_idx:03d}.sql")
        with open(filepath, "w") as f:
            f.write(current_batch)
        print(f"  update_{batch_idx:03d}.sql: {len(current_batch)} bytes, {len(current_ids)} companies (ids: {current_ids[0]}..{current_ids[-1]})")
        batch_idx += 1

    print(f"\nTotal batches: {batch_idx}")


if __name__ == "__main__":
    main()
