#!/usr/bin/env python3
"""
YouTube Queue Processor — Cowork Pipeline Helper
=================================================
Reads extraction JSON files from the queue/ directory,
parses them into a structured format for Claude to analyze.

This script is a HELPER — the actual AI analysis, Notion cross-referencing,
and action proposal generation happens in the Cowork session via the
"process my YouTube queue" skill/scheduled task.

This script:
1. Finds unprocessed JSON files in queue/
2. Loads and validates them
3. Outputs a consolidated processing manifest
4. Marks files as processed (moves to queue/processed/)

The Cowork Claude session reads the manifest and does the intelligence work.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path


def find_queue_files(queue_dir: Path) -> list:
    """Find all unprocessed extraction JSON files."""
    files = []
    for f in sorted(queue_dir.glob("youtube_extract_*.json")):
        files.append(f)
    return files


def load_extraction(filepath: Path) -> dict:
    """Load and validate an extraction JSON file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Validate structure
        required_keys = ['extraction_timestamp', 'videos']
        for key in required_keys:
            if key not in data:
                return {'error': f'Missing key: {key}', 'file': str(filepath)}

        return data
    except json.JSONDecodeError as e:
        return {'error': f'Invalid JSON: {e}', 'file': str(filepath)}
    except Exception as e:
        return {'error': str(e), 'file': str(filepath)}


def build_processing_manifest(queue_dir: Path) -> dict:
    """Build a consolidated manifest of all videos to process."""
    files = find_queue_files(queue_dir)

    if not files:
        return {
            'status': 'empty',
            'message': 'No extraction files found in queue/',
            'queue_dir': str(queue_dir),
        }

    all_videos = []
    batch_info = []

    for filepath in files:
        data = load_extraction(filepath)
        if 'error' in data:
            batch_info.append({
                'file': filepath.name,
                'status': 'error',
                'error': data['error'],
            })
            continue

        # Extract relevant videos with transcripts
        relevant_with_transcripts = []
        relevant_no_transcripts = []
        skipped = []

        for video in data.get('videos', []):
            relevance = video.get('relevance', {})
            transcript = video.get('transcript', {})

            if not relevance.get('relevant', True):
                skipped.append(video['title'])
                continue

            video_entry = {
                'video_id': video.get('video_id'),
                'title': video.get('title', 'Unknown'),
                'channel': video.get('channel', 'Unknown'),
                'url': video.get('url', ''),
                'upload_date': video.get('upload_date', 'NA'),
                'duration_seconds': video.get('duration_seconds', 'NA'),
                'relevance_confidence': relevance.get('confidence', 'unknown'),
                'batch_file': filepath.name,
                'batch_timestamp': data.get('extraction_timestamp', ''),
            }

            if transcript and transcript.get('success'):
                video_entry['transcript_text'] = transcript['full_text']
                video_entry['transcript_language'] = transcript.get('language', 'unknown')
                video_entry['has_transcript'] = True
                relevant_with_transcripts.append(video_entry)
            else:
                video_entry['has_transcript'] = False
                video_entry['transcript_error'] = transcript.get('error', 'No transcript data') if transcript else 'Not fetched'
                relevant_no_transcripts.append(video_entry)

        all_videos.extend(relevant_with_transcripts)
        all_videos.extend(relevant_no_transcripts)

        batch_info.append({
            'file': filepath.name,
            'status': 'loaded',
            'total': len(data.get('videos', [])),
            'relevant_with_transcript': len(relevant_with_transcripts),
            'relevant_no_transcript': len(relevant_no_transcripts),
            'skipped': len(skipped),
            'skipped_titles': skipped[:5],  # Show first 5
        })

    return {
        'status': 'ready',
        'processing_timestamp': datetime.now().isoformat(),
        'total_videos': len(all_videos),
        'videos_with_transcripts': sum(1 for v in all_videos if v.get('has_transcript')),
        'videos_without_transcripts': sum(1 for v in all_videos if not v.get('has_transcript')),
        'batches': batch_info,
        'videos': all_videos,
    }


def mark_processed(queue_dir: Path):
    """Move processed files to queue/processed/ subdirectory."""
    processed_dir = queue_dir / 'processed'
    processed_dir.mkdir(exist_ok=True)

    files = find_queue_files(queue_dir)
    moved = []
    for f in files:
        dest = processed_dir / f.name
        f.rename(dest)
        moved.append(f.name)

    return moved


def main():
    """CLI entry point for testing."""
    script_dir = Path(__file__).parent
    queue_dir = script_dir.parent / 'queue'

    if not queue_dir.exists():
        print(f"Queue directory not found: {queue_dir}")
        sys.exit(1)

    manifest = build_processing_manifest(queue_dir)

    if manifest['status'] == 'empty':
        print("No files to process.")
        sys.exit(0)

    # Pretty print summary
    print(f"\n{'='*60}")
    print(f"YouTube Queue Processing Manifest")
    print(f"{'='*60}")
    print(f"Total videos: {manifest['total_videos']}")
    print(f"With transcripts: {manifest['videos_with_transcripts']}")
    print(f"Without transcripts: {manifest['videos_without_transcripts']}")
    print(f"\nBatches:")
    for batch in manifest['batches']:
        print(f"  {batch['file']}: {batch['status']} ({batch.get('total', 0)} videos)")

    print(f"\nVideos to analyze:")
    for v in manifest['videos']:
        transcript_status = "✓" if v.get('has_transcript') else "✗"
        print(f"  [{transcript_status}] {v['title'][:60]}  ({v['channel']})")

    # Save manifest
    manifest_file = queue_dir / 'processing_manifest.json'
    with open(manifest_file, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    print(f"\nManifest saved to: {manifest_file}")


if __name__ == '__main__':
    main()
