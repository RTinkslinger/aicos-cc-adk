#!/usr/bin/env python3
"""
Execute enrichment SQL batches against Supabase via the Management API.
Uses the Supabase MCP's execute_sql endpoint pattern.

Usage: python3 run_enrichment_batches.py [start_batch] [end_batch]
"""

import glob
import json
import os
import subprocess
import sys
import time

SQL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "enrichment-sql")
PROJECT_ID = "llfkxnsfczludgigknbs"

# We'll use supabase CLI if available, otherwise fall back to REST API
# For now, just output the SQL files to be executed manually


def get_batch_files() -> list[str]:
    """Get sorted list of batch SQL files."""
    files = sorted(glob.glob(os.path.join(SQL_DIR, "batch_*.sql")))
    return files


def main():
    batch_files = get_batch_files()

    start = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    end = int(sys.argv[2]) if len(sys.argv) > 2 else len(batch_files)

    print(f"Found {len(batch_files)} batch files")
    print(f"Processing batches {start} to {end - 1}")

    for i, filepath in enumerate(batch_files[start:end], start=start):
        with open(filepath, "r") as f:
            sql = f.read()

        print(f"\n--- Batch {i:03d} ---")
        print(f"File: {os.path.basename(filepath)}")
        print(f"SQL length: {len(sql)} chars")

        # Extract company IDs from the WHERE clause
        import re
        id_match = re.search(r"WHERE id IN \(([^)]+)\)", sql)
        if id_match:
            ids = id_match.group(1)
            print(f"Company IDs: {ids}")

        print(f"Ready to execute. SQL preview: {sql[:100]}...")
        print()

    print(f"\nTotal: {end - start} batches ready")
    print("Execute each via: Supabase MCP execute_sql")


if __name__ == "__main__":
    main()
