#!/usr/bin/env python3
"""
YouTube Content Extractor for AI CoS
=====================================
Runs on your Mac (not in Cowork VM — YouTube is blocked there).

Usage:
  python3 youtube_extractor.py <PLAYLIST_URL_OR_ID>
  python3 youtube_extractor.py <PLAYLIST_URL_OR_ID> --since 2026-03-01
  python3 youtube_extractor.py <PLAYLIST_URL_OR_ID> --since-days 3
  python3 youtube_extractor.py <PLAYLIST_URL_OR_ID> --limit 10
  python3 youtube_extractor.py --urls video_url1 video_url2 ...

Requirements (install once):
  pip3 install yt-dlp youtube-transcript-api

Output:
  Saves JSON to ../queue/youtube_extract_YYYY-MM-DD_HHMMSS.json
  The Cowork AI CoS pipeline reads from this folder.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Attempt imports
try:
    from youtube_transcript_api import YouTubeTranscriptApi
    from youtube_transcript_api.formatters import TextFormatter
except ImportError:
    print("ERROR: youtube-transcript-api not installed. Run: pip3 install youtube-transcript-api")
    sys.exit(1)


def find_yt_dlp() -> str:
    """Find yt-dlp binary, checking PATH and common install locations."""
    found = shutil.which('yt-dlp')
    if found:
        return found
    # Fallback paths for launchd/cron environments with limited PATH
    fallback_paths = [
        os.path.expanduser('~/.local/bin/yt-dlp'),
        '/opt/homebrew/bin/yt-dlp',
        '/usr/local/bin/yt-dlp',
        '/usr/bin/yt-dlp',
    ]
    for path in fallback_paths:
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path
    # Last resort — hope it's on PATH at runtime
    return 'yt-dlp'


def extract_video_id(url_or_id: str) -> str:
    """Extract YouTube video ID from various URL formats."""
    patterns = [
        r'(?:v=|/v/|youtu\.be/)([a-zA-Z0-9_-]{11})',
        r'^([a-zA-Z0-9_-]{11})$',
    ]
    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)
    return url_or_id


def get_playlist_videos(playlist_url: str, limit: int = None, since_date: str = None) -> list:
    """Use yt-dlp to get video metadata from a playlist."""
    cmd = [
        find_yt_dlp(), '--flat-playlist',
        '--print', '%(id)s\t%(title)s\t%(channel)s\t%(duration)s\t%(upload_date)s\t%(webpage_url)s',
        '--no-warnings',
    ]
    if limit:
        cmd.extend(['--playlist-end', str(limit)])

    cmd.append(playlist_url)

    print(f"Fetching playlist metadata...")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

    if result.returncode != 0:
        print(f"yt-dlp error: {result.stderr[:500]}")
        return []

    videos = []
    for line in result.stdout.strip().split('\n'):
        if not line.strip():
            continue
        parts = line.split('\t')
        if len(parts) >= 4:
            video_id = parts[0]
            title = parts[1] if len(parts) > 1 else 'Unknown'
            channel = parts[2] if len(parts) > 2 else 'Unknown'
            duration = parts[3] if len(parts) > 3 else 'NA'
            upload_date = parts[4] if len(parts) > 4 else 'NA'
            url = parts[5] if len(parts) > 5 else f'https://www.youtube.com/watch?v={video_id}'

            # Filter by date if specified
            if since_date and upload_date != 'NA':
                try:
                    vid_date = datetime.strptime(upload_date, '%Y%m%d').strftime('%Y-%m-%d')
                    if vid_date < since_date:
                        continue
                except ValueError:
                    pass

            videos.append({
                'video_id': video_id,
                'title': title,
                'channel': channel,
                'duration_seconds': duration,
                'upload_date': upload_date,
                'url': url,
            })

    print(f"Found {len(videos)} videos in playlist")
    return videos


def get_transcript(video_id: str) -> dict:
    """Fetch transcript for a single video."""
    try:
        ytt_api = YouTubeTranscriptApi()
        transcript = ytt_api.fetch(video_id)
        formatter = TextFormatter()
        text = formatter.format_transcript(transcript)

        # Also build a structured version with timestamps
        segments = []
        for snippet in transcript.snippets:
            segments.append({
                'start': snippet.start,
                'text': snippet.text,
            })

        return {
            'success': True,
            'full_text': text,
            'segments': segments,
            'language': transcript.language,
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'full_text': None,
            'segments': [],
        }


def classify_relevance(title: str, channel: str) -> dict:
    """Quick heuristic classification — is this work-relevant?

    Returns relevance score and category.
    The AI analysis in Cowork will do deeper classification,
    but this pre-filter helps cut obvious noise.
    """
    title_lower = title.lower()
    channel_lower = channel.lower()

    # Work-relevant keywords (investing, tech, venture, economics, etc.)
    work_keywords = [
        'venture', 'startup', 'invest', 'vc', 'funding', 'founder',
        'saas', 'b2b', 'fintech', 'ai', 'artificial intelligence', 'machine learning',
        'deep tech', 'semiconductor', 'chip', 'gpu',
        'cybersecurity', 'security', 'hack', 'pen test',
        'economics', 'macro', 'gdp', 'inflation', 'interest rate', 'fed',
        'geopolitics', 'trade', 'tariff', 'supply chain',
        'software', 'cloud', 'infrastructure', 'devops', 'api',
        'india', 'market', 'growth', 'revenue', 'unit economics',
        'physics', 'energy', 'nuclear', 'fusion', 'quantum',
        'history', 'civilization', 'empire', 'strategy',
        'aviation', 'defense', 'ustol', 'vtol', 'drone',
        'mcp', 'agent', 'llm', 'gpt', 'claude', 'anthropic', 'openai',
        'podcast', 'interview', 'conversation with', 'fireside',
        'thesis', 'conviction', 'portfolio', 'cap table', 'board',
        'ceo', 'cto', 'cfo', 'founder', 'operator',
        'product', 'market fit', 'pmf', 'go to market', 'gtm',
        'blockchain', 'crypto', 'defi', 'web3', 'token',
        'biotech', 'health', 'genomics', 'drug discovery',
        'space', 'satellite', 'rocket', 'orbit',
        'robotics', 'automation', 'manufacturing',
        'climate', 'carbon', 'sustainability', 'clean energy', 'solar', 'wind',
        'regulation', 'policy', 'antitrust', 'compliance',
    ]

    # Personal/non-work keywords to deprioritize
    personal_keywords = [
        'recipe', 'cooking', 'food', 'mukbang',
        'travel vlog', 'vacation', 'hotel review', 'flight review',
        'shopping haul', 'unboxing', 'buy this',
        'fitness', 'workout', 'gym', 'yoga', 'meditation',
        'movie', 'trailer', 'netflix', 'tv show', 'series review',
        'music video', 'official video', 'lyrics',
        'gaming', 'gameplay', 'walkthrough', 'twitch',
        'comedy', 'prank', 'funny', 'meme',
        'beauty', 'skincare', 'makeup', 'haircut',
        'cricket', 'football', 'soccer', 'tennis', 'sports highlight',
        'daily vlog', 'day in my life', 'morning routine',
        'asmr', 'relaxing', 'sleep',
        'diy', 'craft', 'home decor',
    ]

    combined = f"{title_lower} {channel_lower}"

    work_score = sum(1 for kw in work_keywords if kw in combined)
    personal_score = sum(1 for kw in personal_keywords if kw in combined)

    if personal_score > 0 and work_score == 0:
        return {'relevant': False, 'confidence': 'high', 'work_score': work_score, 'personal_score': personal_score}
    elif work_score >= 2:
        return {'relevant': True, 'confidence': 'high', 'work_score': work_score, 'personal_score': personal_score}
    elif work_score == 1:
        return {'relevant': True, 'confidence': 'medium', 'work_score': work_score, 'personal_score': personal_score}
    else:
        # Unknown — include it, let AI decide
        return {'relevant': True, 'confidence': 'low', 'work_score': work_score, 'personal_score': personal_score}


def process_videos(videos: list, skip_transcripts: bool = False) -> list:
    """Process each video: classify relevance and fetch transcript."""
    processed = []
    for i, video in enumerate(videos):
        print(f"  [{i+1}/{len(videos)}] {video['title'][:60]}...")

        # Quick relevance check
        relevance = classify_relevance(video['title'], video['channel'])
        video['relevance'] = relevance

        if not relevance['relevant']:
            print(f"    → Skipped (personal content, confidence: {relevance['confidence']})")
            video['transcript'] = None
            processed.append(video)
            continue

        # Fetch transcript
        if not skip_transcripts:
            print(f"    → Fetching transcript...")
            transcript = get_transcript(video['video_id'])
            video['transcript'] = transcript
            if transcript['success']:
                word_count = len(transcript['full_text'].split())
                print(f"    → Got transcript ({word_count:,} words)")
            else:
                print(f"    → No transcript: {transcript['error'][:80]}")
        else:
            video['transcript'] = None

        processed.append(video)

    return processed


def main():
    parser = argparse.ArgumentParser(description='YouTube Content Extractor for AI CoS')
    parser.add_argument('playlist', nargs='?', help='YouTube playlist URL or ID')
    parser.add_argument('--urls', nargs='+', help='Individual video URLs to process')
    parser.add_argument('--since', help='Only include videos uploaded after this date (YYYY-MM-DD)')
    parser.add_argument('--since-days', type=int, help='Only include videos from the last N days (alternative to --since)')
    parser.add_argument('--limit', type=int, help='Max number of videos to process')
    parser.add_argument('--skip-transcripts', action='store_true', help='Skip transcript fetching (metadata only)')
    parser.add_argument('--output-dir', default=None, help='Output directory (default: ../queue/)')

    args = parser.parse_args()

    if not args.playlist and not args.urls:
        parser.print_help()
        print("\nExamples:")
        print("  python3 youtube_extractor.py 'https://www.youtube.com/playlist?list=PLxxxxxxx'")
        print("  python3 youtube_extractor.py --urls 'https://www.youtube.com/watch?v=xxxxx' 'https://...'")
        sys.exit(1)

    # Determine output directory
    script_dir = Path(__file__).parent
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        output_dir = script_dir.parent / 'queue'
    output_dir.mkdir(parents=True, exist_ok=True)

    # Get video list
    videos = []
    # Resolve --since-days to a --since date
    since_date = args.since
    if args.since_days and not since_date:
        since_date = (datetime.now() - timedelta(days=args.since_days)).strftime('%Y-%m-%d')
        print(f"Filtering to videos from last {args.since_days} days (since {since_date})")

    if args.playlist:
        videos = get_playlist_videos(args.playlist, limit=args.limit, since_date=since_date)
    elif args.urls:
        for url in args.urls:
            vid_id = extract_video_id(url)
            videos.append({
                'video_id': vid_id,
                'title': 'Unknown',
                'channel': 'Unknown',
                'duration_seconds': 'NA',
                'upload_date': 'NA',
                'url': url,
            })

    if not videos:
        print("No videos found. Check your playlist URL or video IDs.")
        sys.exit(1)

    # Process videos
    print(f"\nProcessing {len(videos)} videos...")
    processed = process_videos(videos, skip_transcripts=args.skip_transcripts)

    # Build output
    relevant = [v for v in processed if v.get('relevance', {}).get('relevant', True)]
    skipped = [v for v in processed if not v.get('relevance', {}).get('relevant', True)]

    output = {
        'extraction_timestamp': datetime.now().isoformat(),
        'source_playlist': args.playlist or 'individual_urls',
        'total_videos': len(processed),
        'relevant_videos': len(relevant),
        'skipped_personal': len(skipped),
        'videos': processed,
    }

    # Save
    timestamp = datetime.now().strftime('%Y-%m-%d_%H%M%S')
    output_file = output_dir / f'youtube_extract_{timestamp}.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*60}")
    print(f"Done! Processed {len(processed)} videos:")
    print(f"  - {len(relevant)} work-relevant (with transcripts)")
    print(f"  - {len(skipped)} skipped (personal content)")
    print(f"\nOutput saved to: {output_file}")
    print(f"\nNext: Say 'process my content queue' (Cowork desktop or scheduled at 9 PM)")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
