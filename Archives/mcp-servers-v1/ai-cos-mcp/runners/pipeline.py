from __future__ import annotations

"""Unified Content Pipeline — extract + analyze + publish in one pass.

Replaces the two-step cron (extract.sh + analyze.sh) with a single script
that runs every 5 minutes. If no new videos are found, exits in ~5 seconds.
If new videos exist, processes them end-to-end (~3-4 min per video).

Locking is handled by the bash wrapper (cron/pipeline.sh) via flock.
For manual runs via `yt`, no locking is needed (user controls timing).

Usage:
    python -m runners.pipeline                    # default playlist, last 3 days
    python -m runners.pipeline --since-days 7     # last 7 days
    python -m runners.pipeline --urls URL1 URL2   # specific videos
    python -m runners.pipeline --dry-run           # extract + analyze, skip publish
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Add parent to path for lib imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.extraction import check_cookie_health, extract_and_save
from runners.content_agent import load_system_prompt, process_extraction


def run_pipeline(
    since_days: int = 3,
    video_urls: list[str] | None = None,
    dry_run: bool = False,
) -> int:
    """Run the full pipeline: extract → analyze → publish.

    Returns the number of digests produced.
    """
    start = datetime.now(timezone.utc)
    print(f"\n{'='*60}")
    print(f"AI CoS Pipeline — {start.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"{'='*60}")

    # Step 0: Cookie health check
    health = check_cookie_health()
    if health["cookie_age_days"] is not None and health["cookie_age_days"] > 10:
        print(f"WARNING: cookies.txt is {health['cookie_age_days']} days old — may expire soon")
    if not health["healthy"]:
        print(f"WARNING: YouTube cookie check failed: {health['error']}")
        print(f"  To refresh cookies:")
        print(f"  1. Mac: yt-dlp --cookies-from-browser safari --cookies /tmp/cookies.txt --skip-download 'https://youtube.com/watch?v=dQw4w9WgXcQ'")
        print(f"  2. rsync /tmp/cookies.txt root@aicos-droplet:/opt/ai-cos-mcp/cookies.txt")
        # Continue anyway — per-video transcript fetch will fail gracefully,
        # and the dedup fix ensures failed videos are retried next run.

    # Step 1: Extract
    print("\n[1/3] Extracting from YouTube...")
    extraction_path = extract_and_save(
        video_urls=video_urls,
        since_days=since_days,
    )

    if extraction_path is None:
        print("No videos found. Pipeline idle.")
        return 0

    # Check if extraction has any relevant videos with transcripts
    with open(extraction_path, encoding="utf-8") as f:
        extraction = json.load(f)

    relevant_with_transcript = [
        v for v in extraction.get("videos", [])
        if v.get("relevance", {}).get("relevant", True)
        and v.get("transcript", {}).get("success")
    ]

    if not relevant_with_transcript:
        print(f"Extraction produced {extraction_path.name} but no new relevant videos with transcripts.")
        # Clean up empty extraction
        extraction_path.unlink(missing_ok=True)
        return 0

    print(f"  {len(relevant_with_transcript)} video(s) ready for analysis")

    # Step 2: Analyze + Score + Publish + Notion + Postgres
    print("\n[2/3] Analyzing and publishing...")
    system_prompt = load_system_prompt()
    print(f"  System prompt loaded ({len(system_prompt):,} chars)")

    results = process_extraction(extraction_path, system_prompt, dry_run=dry_run)

    # Step 3: Summary
    elapsed = (datetime.now(timezone.utc) - start).total_seconds()
    print(f"\n[3/3] Pipeline complete")
    print(f"  Digests produced: {len(results)}")
    print(f"  Elapsed: {elapsed:.0f}s")
    print(f"{'='*60}\n")

    return len(results)


def main():
    parser = argparse.ArgumentParser(description="AI CoS Unified Content Pipeline")
    parser.add_argument("--since-days", type=int, default=3, help="Look back N days (default: 3)")
    parser.add_argument("--urls", nargs="+", help="Specific video URLs to process")
    parser.add_argument("--dry-run", action="store_true", help="Extract + analyze only, skip publish/Notion")
    args = parser.parse_args()

    count = run_pipeline(
        since_days=args.since_days,
        video_urls=args.urls,
        dry_run=args.dry_run,
    )
    sys.exit(0 if count >= 0 else 1)


if __name__ == "__main__":
    main()
