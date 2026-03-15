from __future__ import annotations

"""YouTube Content Extraction — extracts playlist metadata and transcripts.

Core extraction logic for droplet deployment.
Keeps ONLY: extraction, transcript fetching, cookie health, relevance classification,
and dedup tracking. All ContentAgent/content-analysis code has been removed.

Requirements: yt-dlp, youtube-transcript-api
"""

import argparse
import json
import logging
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

logger = logging.getLogger("web-agent")

try:
    from youtube_transcript_api import YouTubeTranscriptApi
    from youtube_transcript_api.formatters import TextFormatter
except ImportError:
    print("ERROR: youtube-transcript-api not installed. Run: uv add youtube-transcript-api")
    sys.exit(1)

# Default config
DEFAULT_PLAYLIST = os.getenv(
    "YOUTUBE_PLAYLIST_URL",
    "https://youtube.com/playlist?list=PLSAj-XU9ZUhPHrwSpZKxop1mDL8NgVPkD",
)
DEFAULT_QUEUE_DIR = os.getenv("QUEUE_DIR", str(Path(__file__).parent.parent / "queue"))
DEFAULT_SINCE_DAYS = 3
COOKIES_PATH = os.getenv("YOUTUBE_COOKIES_PATH", str(Path(__file__).parent.parent / "cookies.txt"))

# Work-relevant keywords for pre-filtering
WORK_KEYWORDS = [
    "venture", "startup", "invest", "vc", "funding", "founder",
    "saas", "b2b", "fintech", "ai", "artificial intelligence", "machine learning",
    "deep tech", "semiconductor", "chip", "gpu",
    "cybersecurity", "security", "hack", "pen test",
    "economics", "macro", "gdp", "inflation", "interest rate", "fed",
    "geopolitics", "trade", "tariff", "supply chain",
    "software", "cloud", "infrastructure", "devops", "api",
    "india", "market", "growth", "revenue", "unit economics",
    "physics", "energy", "nuclear", "fusion", "quantum",
    "history", "civilization", "empire", "strategy",
    "aviation", "defense", "ustol", "vtol", "drone",
    "mcp", "agent", "llm", "gpt", "claude", "anthropic", "openai",
    "podcast", "interview", "conversation with", "fireside",
    "thesis", "conviction", "portfolio", "cap table", "board",
    "ceo", "cto", "cfo", "founder", "operator",
    "product", "market fit", "pmf", "go to market", "gtm",
    "blockchain", "crypto", "defi", "web3", "token",
    "biotech", "health", "genomics", "drug discovery",
    "space", "satellite", "rocket", "orbit",
    "robotics", "automation", "manufacturing",
    "climate", "carbon", "sustainability", "clean energy", "solar", "wind",
    "regulation", "policy", "antitrust", "compliance",
]

PERSONAL_KEYWORDS = [
    "recipe", "cooking", "food", "mukbang",
    "travel vlog", "vacation", "hotel review", "flight review",
    "shopping haul", "unboxing", "buy this",
    "fitness", "workout", "gym", "yoga", "meditation",
    "movie", "trailer", "netflix", "tv show", "series review",
    "music video", "official video", "lyrics",
    "gaming", "gameplay", "walkthrough", "twitch",
    "comedy", "prank", "funny", "meme",
    "beauty", "skincare", "makeup", "haircut",
    "cricket", "football", "soccer", "tennis", "sports highlight",
    "daily vlog", "day in my life", "morning routine",
    "asmr", "relaxing", "sleep",
    "diy", "craft", "home decor",
]


# ---------------------------------------------------------------------------
# DedupTracker — inlined from ai-cos-mcp/lib/dedup.py
# ---------------------------------------------------------------------------


class DedupTracker:
    """Manages a set of processed item IDs with JSON file persistence.

    Usage:
        with DedupTracker(Path('processed_videos.json')) as tracker:
            if not tracker.is_processed('video_id_123'):
                # process it
                tracker.mark_processed('video_id_123')
    """

    def __init__(self, filepath: Path):
        self.filepath = Path(filepath)
        self._processed_ids: set[str] = self.load()

    def load(self) -> set[str]:
        if not self.filepath.exists():
            return set()
        try:
            with open(self.filepath, encoding="utf-8") as f:
                data = json.load(f)
                return set(data.get("processed_ids", []))
        except (json.JSONDecodeError, IOError):
            return set()

    def save(self, ids: set[str] | None = None) -> None:
        ids = ids if ids is not None else self._processed_ids
        data = {
            "processed_ids": sorted(ids),
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "source": "web-agent",
        }
        try:
            self.filepath.parent.mkdir(parents=True, exist_ok=True)
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"Warning: Could not save dedup file {self.filepath}: {e}")

    def is_processed(self, item_id: str) -> bool:
        return item_id in self._processed_ids

    def mark_processed(self, item_id: str) -> None:
        self._processed_ids.add(item_id)

    def commit(self) -> None:
        self.save()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.commit()
        return False


# ---------------------------------------------------------------------------
# Core extraction functions
# ---------------------------------------------------------------------------


def find_yt_dlp() -> str:
    """Find yt-dlp binary."""
    found = shutil.which("yt-dlp")
    if found:
        return found
    fallback_paths = [
        os.path.expanduser("~/.local/bin/yt-dlp"),
        "/opt/homebrew/bin/yt-dlp",
        "/usr/local/bin/yt-dlp",
        "/usr/bin/yt-dlp",
    ]
    for path in fallback_paths:
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path
    return "yt-dlp"


def extract_video_id(url_or_id: str) -> str:
    """Extract YouTube video ID from various URL formats."""
    patterns = [
        r"(?:v=|/v/|youtu\.be/)([a-zA-Z0-9_-]{11})",
        r"^([a-zA-Z0-9_-]{11})$",
    ]
    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)
    return url_or_id


def get_playlist_videos(
    playlist_url: str,
    limit: int | None = None,
    since_date: str | None = None,
) -> list[dict]:
    """Use yt-dlp to get video metadata from a playlist."""
    cmd = [
        find_yt_dlp(),
        "--flat-playlist",
        "--print",
        "%(id)s\t%(title)s\t%(channel)s\t%(duration)s\t%(upload_date)s\t%(webpage_url)s",
        "--no-warnings",
        "--remote-components", "ejs:github",
    ]
    if os.path.isfile(COOKIES_PATH):
        cmd.extend(["--cookies", COOKIES_PATH])
    if limit:
        cmd.extend(["--playlist-end", str(limit)])
    cmd.append(playlist_url)

    print(f"Fetching playlist metadata...")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        print(f"yt-dlp error: {result.stderr[:500]}")
        return []

    videos = []
    for line in result.stdout.strip().split("\n"):
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) >= 4:
            video_id = parts[0]
            title = parts[1] if len(parts) > 1 else "Unknown"
            channel = parts[2] if len(parts) > 2 else "Unknown"
            duration = parts[3] if len(parts) > 3 else "NA"
            upload_date = parts[4] if len(parts) > 4 else "NA"
            url = parts[5] if len(parts) > 5 else f"https://www.youtube.com/watch?v={video_id}"

            if since_date and upload_date != "NA":
                try:
                    vid_date = datetime.strptime(upload_date, "%Y%m%d").strftime("%Y-%m-%d")
                    if vid_date < since_date:
                        continue
                except ValueError:
                    pass

            videos.append({
                "video_id": video_id,
                "title": title,
                "channel": channel,
                "duration_seconds": duration,
                "upload_date": upload_date,
                "url": url,
            })

    print(f"Found {len(videos)} videos in playlist")
    return videos


def get_transcript(video_id: str) -> dict:
    """Fetch transcript for a single video.

    Tries youtube-transcript-api first, falls back to yt-dlp subtitles
    if blocked (common on datacenter IPs).
    """
    # Try youtube-transcript-api first (faster, more structured)
    try:
        # Pass cookies via requests.Session if available
        http_client = None
        if os.path.isfile(COOKIES_PATH):
            import http.cookiejar
            import requests
            jar = http.cookiejar.MozillaCookieJar(COOKIES_PATH)
            jar.load(ignore_discard=True, ignore_expires=True)
            session = requests.Session()
            session.cookies = jar
            http_client = session
        ytt_api = YouTubeTranscriptApi(http_client=http_client)
        transcript = ytt_api.fetch(video_id)
        formatter = TextFormatter()
        text = formatter.format_transcript(transcript)
        segments = [{"start": s.start, "text": s.text} for s in transcript.snippets]
        return {
            "success": True,
            "full_text": text,
            "segments": segments,
            "language": transcript.language,
        }
    except Exception:
        pass

    # Fallback: use yt-dlp to fetch subtitles (handles IP blocks better)
    try:
        return _get_transcript_via_ytdlp(video_id)
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "full_text": None,
            "segments": [],
        }


def _get_transcript_via_ytdlp(video_id: str) -> dict:
    """Fetch transcript using yt-dlp subtitle extraction."""
    import tempfile

    url = f"https://www.youtube.com/watch?v={video_id}"
    with tempfile.TemporaryDirectory() as tmpdir:
        cmd = [
            find_yt_dlp(),
            "--skip-download",
            "--write-auto-sub",
            "--write-sub",
            "--sub-lang", "en",
            "--sub-format", "vtt",
            "--convert-subs", "vtt",
            "-o", f"{tmpdir}/%(id)s",
            "--remote-components", "ejs:github",
            "--ignore-no-formats-error",
            *(["--cookies", COOKIES_PATH] if os.path.isfile(COOKIES_PATH) else []),
            "--no-warnings",
            url,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

        # Find the subtitle file
        sub_files = list(Path(tmpdir).glob("*.vtt"))
        if not sub_files:
            return {
                "success": False,
                "error": f"yt-dlp found no subtitles (rc={result.returncode})",
                "full_text": None,
                "segments": [],
            }

        raw = sub_files[0].read_text(encoding="utf-8")
        text = _parse_vtt_to_text(raw)
        if not text.strip():
            return {
                "success": False,
                "error": "Subtitle file was empty after parsing",
                "full_text": None,
                "segments": [],
            }
        return {
            "success": True,
            "full_text": text,
            "segments": [],
            "language": "en",
        }


def _parse_vtt_to_text(vtt_content: str) -> str:
    """Strip VTT timestamps and metadata, return plain text."""
    lines = []
    seen = set()
    for line in vtt_content.split("\n"):
        line = line.strip()
        # Skip VTT headers, timestamps, and empty lines
        if not line or line.startswith("WEBVTT") or line.startswith("Kind:") or line.startswith("Language:"):
            continue
        if "-->" in line:
            continue
        # Skip position/alignment tags
        if line.startswith("NOTE") or re.match(r"^\d+$", line):
            continue
        # Strip inline VTT tags like <c> </c> <00:00:00.000>
        cleaned = re.sub(r"<[^>]+>", "", line).strip()
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            lines.append(cleaned)
    return " ".join(lines)


def check_cookie_health() -> dict:
    """Check if YouTube cookies are valid and not expired.

    Tests by fetching metadata for a known-good video. Returns status dict.
    """
    cookie_path = Path(COOKIES_PATH)
    result: dict = {"healthy": True, "error": None, "cookie_age_days": None}

    if not cookie_path.exists():
        result["healthy"] = False
        result["error"] = f"No cookies file at {COOKIES_PATH}"
        return result

    # Check file age
    mtime = datetime.fromtimestamp(cookie_path.stat().st_mtime)
    age_days = (datetime.now() - mtime).days
    result["cookie_age_days"] = age_days

    # Test with a known-good video (Rick Astley - never gets removed)
    cmd = [
        find_yt_dlp(),
        "--skip-download",
        "--print", "%(title)s",
        "--cookies", COOKIES_PATH,
        "--remote-components", "ejs:github",
        "--no-warnings",
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        stderr = proc.stderr.lower()
        if "sign in" in stderr or "bot" in stderr or "blocked" in stderr:
            result["healthy"] = False
            result["error"] = "YouTube cookies expired — bot detection triggered"
        elif proc.returncode != 0:
            result["healthy"] = False
            result["error"] = f"yt-dlp failed (rc={proc.returncode})"
    except subprocess.TimeoutExpired:
        result["healthy"] = False
        result["error"] = "yt-dlp timed out during cookie health check"
    except Exception as e:
        result["healthy"] = False
        result["error"] = str(e)

    return result


def classify_relevance(title: str, channel: str) -> dict:
    """Quick heuristic: is this work-relevant?"""
    combined = f"{title.lower()} {channel.lower()}"
    work_score = sum(1 for kw in WORK_KEYWORDS if kw in combined)
    personal_score = sum(1 for kw in PERSONAL_KEYWORDS if kw in combined)

    if personal_score > 0 and work_score == 0:
        return {"relevant": False, "confidence": "high", "work_score": work_score, "personal_score": personal_score}
    elif work_score >= 2:
        return {"relevant": True, "confidence": "high", "work_score": work_score, "personal_score": personal_score}
    elif work_score == 1:
        return {"relevant": True, "confidence": "medium", "work_score": work_score, "personal_score": personal_score}
    return {"relevant": True, "confidence": "low", "work_score": work_score, "personal_score": personal_score}


def process_videos(
    videos: list[dict],
    skip_transcripts: bool = False,
    processed_ids: set[str] | None = None,
) -> tuple[list[dict], set[str]]:
    """Process each video: classify relevance and fetch transcript."""
    processed = []
    if processed_ids is None:
        processed_ids = set()
    newly_processed_ids: set[str] = set()

    for i, video in enumerate(videos):
        if video["video_id"] in processed_ids:
            print(f"  [{i+1}/{len(videos)}] {video['title'][:60]}... (SKIPPED - dedup)")
            processed.append(video)
            continue

        print(f"  [{i+1}/{len(videos)}] {video['title'][:60]}...")
        relevance = classify_relevance(video["title"], video["channel"])
        video["relevance"] = relevance

        if not relevance["relevant"]:
            print(f"    -> Skipped (personal content)")
            video["transcript"] = None
            processed.append(video)
            newly_processed_ids.add(video["video_id"])  # Dedup personal content
            continue

        if not skip_transcripts:
            print(f"    -> Fetching transcript...")
            transcript = get_transcript(video["video_id"])
            video["transcript"] = transcript
            if transcript["success"]:
                word_count = len(transcript["full_text"].split())
                print(f"    -> Got transcript ({word_count:,} words)")
                newly_processed_ids.add(video["video_id"])  # Only dedup on success
            else:
                print(f"    -> No transcript: {transcript['error'][:80]} (will retry next run)")
        else:
            video["transcript"] = None

        processed.append(video)

    return processed, newly_processed_ids


def extract_and_save(
    playlist_url: str | None = None,
    video_urls: list[str] | None = None,
    since_days: int = DEFAULT_SINCE_DAYS,
    output_dir: str | None = None,
    skip_transcripts: bool = False,
    force: bool = False,
    limit: int | None = None,
) -> Path | None:
    """Main extraction entry point. Returns path to output JSON or None."""
    playlist_url = playlist_url or DEFAULT_PLAYLIST
    queue_dir = Path(output_dir or DEFAULT_QUEUE_DIR)
    queue_dir.mkdir(parents=True, exist_ok=True)

    since_date = (datetime.now() - timedelta(days=since_days)).strftime("%Y-%m-%d")
    print(f"Filtering to videos from last {since_days} days (since {since_date})")

    # Get video list
    videos: list[dict] = []
    if video_urls:
        for url in video_urls:
            vid_id = extract_video_id(url)
            videos.append({
                "video_id": vid_id,
                "title": "Unknown",
                "channel": "Unknown",
                "duration_seconds": "NA",
                "upload_date": "NA",
                "url": url,
            })
    else:
        videos = get_playlist_videos(playlist_url, limit=limit, since_date=since_date)

    if not videos:
        print("No videos found.")
        return None

    # Dedup
    dedup_path = queue_dir / "processed_videos.json"
    tracker = DedupTracker(dedup_path)
    processed_ids = set() if force else tracker.load()

    print(f"\nProcessing {len(videos)} videos...")
    processed, newly_processed_ids = process_videos(
        videos, skip_transcripts=skip_transcripts, processed_ids=processed_ids,
    )

    relevant = [v for v in processed if v.get("relevance", {}).get("relevant", True)]
    skipped = [v for v in processed if not v.get("relevance", {}).get("relevant", True)]

    output = {
        "extraction_timestamp": datetime.now().isoformat(),
        "source_playlist": playlist_url or "individual_urls",
        "total_videos": len(processed),
        "relevant_videos": len(relevant),
        "skipped_personal": len(skipped),
        "skipped_dedup": len(processed_ids),
        "videos": processed,
    }

    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    output_file = queue_dir / f"youtube_extract_{timestamp}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    # Update dedup tracker
    all_processed = processed_ids | newly_processed_ids
    tracker.save(all_processed)

    print(f"\nDone! {len(relevant)} relevant, {len(skipped)} personal, {len(processed_ids)} dedup")
    print(f"Output: {output_file}")
    return output_file


def main():
    parser = argparse.ArgumentParser(description="YouTube Content Extractor for AI CoS")
    parser.add_argument("playlist", nargs="?", help="YouTube playlist URL or ID")
    parser.add_argument("--urls", nargs="+", help="Individual video URLs")
    parser.add_argument("--since-days", type=int, default=DEFAULT_SINCE_DAYS)
    parser.add_argument("--limit", type=int, help="Max videos to process")
    parser.add_argument("--skip-transcripts", action="store_true")
    parser.add_argument("--force", action="store_true", help="Skip dedup")
    parser.add_argument("--output-dir", default=None)
    args = parser.parse_args()

    extract_and_save(
        playlist_url=args.playlist,
        video_urls=args.urls,
        since_days=args.since_days,
        output_dir=args.output_dir,
        skip_transcripts=args.skip_transcripts,
        force=args.force,
        limit=args.limit,
    )


if __name__ == "__main__":
    main()
