#!/usr/bin/env python3
"""
Generate INSERT statements for the enrichment staging table.
Outputs SQL files with INSERT statements in batches of 5.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from enrich_embeddings import extract_meaningful_content

COMPANIES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "companies-pages")
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "enrichment-sql", "staging")
MAPPING_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "enrichment-sql", "company_mapping.json")
BATCH_SIZE = 5  # Small batches for MCP tool


def escape_sql(s: str) -> str:
    """Escape string for SQL."""
    return s.replace("'", "''")


def main():
    with open(MAPPING_FILE) as f:
        mapping = json.load(f)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    enriched: list[tuple[int, str]] = []

    for entry in mapping:
        company_id = entry["id"]
        page_path = entry["page_content_path"]
        filepath = os.path.join(os.path.dirname(COMPANIES_DIR), page_path)

        if not os.path.exists(filepath):
            continue

        content = extract_meaningful_content(filepath)
        if not content:
            continue

        enriched.append((company_id, content))

    print(f"Total enrichable companies: {len(enriched)}")

    batch_count = 0
    for i in range(0, len(enriched), BATCH_SIZE):
        batch = enriched[i:i + BATCH_SIZE]

        values = []
        for cid, content in batch:
            escaped = escape_sql(content)
            values.append(f"({cid}, '{escaped}')")

        sql = f"INSERT INTO util.enrichment_staging (company_id, content) VALUES\n" + ",\n".join(values) + "\nON CONFLICT (company_id) DO UPDATE SET content = EXCLUDED.content;"

        filepath = os.path.join(OUTPUT_DIR, f"insert_{batch_count:03d}.sql")
        with open(filepath, "w") as f:
            f.write(sql)

        batch_count += 1

    print(f"Generated {batch_count} insert batch files in {OUTPUT_DIR}")
    print(f"After loading all, run: UPDATE companies SET agent_ids_notes = s.content FROM util.enrichment_staging s WHERE companies.id = s.company_id AND (companies.agent_ids_notes IS NULL OR companies.agent_ids_notes = '');")


if __name__ == "__main__":
    main()
