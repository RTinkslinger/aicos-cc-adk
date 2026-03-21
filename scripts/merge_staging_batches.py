#!/usr/bin/env python3
"""Merge staging insert batches into larger files."""

import glob
import os

STAGING_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "enrichment-sql", "staging")
MERGED_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "enrichment-sql", "merged")
MAX_SIZE = 45000  # ~45KB per merged file


def main():
    os.makedirs(MERGED_DIR, exist_ok=True)

    files = sorted(glob.glob(os.path.join(STAGING_DIR, "insert_*.sql")))
    print(f"Found {len(files)} insert files")

    merged_idx = 0
    current_sql = ""
    current_size = 0

    for filepath in files:
        with open(filepath) as f:
            sql = f.read()

        if current_size + len(sql) > MAX_SIZE and current_sql:
            out_path = os.path.join(MERGED_DIR, f"merged_{merged_idx:03d}.sql")
            with open(out_path, "w") as f:
                f.write(current_sql)
            print(f"  {os.path.basename(out_path)}: {current_size} bytes")
            merged_idx += 1
            current_sql = ""
            current_size = 0

        current_sql += sql + "\n"
        current_size += len(sql) + 1

    if current_sql:
        out_path = os.path.join(MERGED_DIR, f"merged_{merged_idx:03d}.sql")
        with open(out_path, "w") as f:
            f.write(current_sql)
        print(f"  {os.path.basename(out_path)}: {current_size} bytes")
        merged_idx += 1

    print(f"\nMerged into {merged_idx} files")


if __name__ == "__main__":
    main()
