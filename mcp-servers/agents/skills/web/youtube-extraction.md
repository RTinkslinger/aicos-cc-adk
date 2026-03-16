# YouTube Extraction Skill

Instructions for extracting YouTube playlist metadata and video transcripts.

---

## Overview

YouTube extraction uses yt-dlp for playlist metadata and a two-tier transcript system: youtube-transcript-api (primary, faster) with yt-dlp subtitle extraction as fallback.

**Key constraint:** Datacenter IPs are blocked by YouTube. Cookie files are required for both metadata and transcript extraction from the droplet.

---

## Extraction Flow

### 1. Playlist Metadata Extraction

Use `extract_youtube` tool or call yt-dlp directly:

```
extract_youtube(playlist_url="https://youtube.com/playlist?list=...", since_days=3)
```

**What it does:**
1. Calls yt-dlp with `--flat-playlist` to get metadata (no video download).
2. Extracts per-video: `video_id`, `title`, `channel`, `duration_seconds`, `upload_date`, `url`.
3. Filters by `since_date` (upload_date >= cutoff).
4. Returns list of video metadata dicts.

**Default playlist:** `PLSAj-XU9ZUhPHrwSpZKxop1mDL8NgVPkD` (Aakash's Watch Later / curated playlist).

### 2. Relevance Classification

Before fetching transcripts, each video is classified:

**Work-relevant keywords** (triggers `relevant: true`): venture, startup, invest, vc, funding, saas, b2b, fintech, ai, cybersecurity, economics, macro, geopolitics, software, cloud, thesis, conviction, portfolio, mcp, agent, llm, biotech, robotics, climate, and ~50 more.

**Personal keywords** (triggers `relevant: false`): recipe, cooking, travel vlog, shopping haul, fitness, gaming, comedy, beauty, cricket, asmr, diy, and ~25 more.

**Scoring logic:**
- `personal_score > 0` AND `work_score == 0` --> Not relevant (high confidence)
- `work_score >= 2` --> Relevant (high confidence)
- `work_score == 1` --> Relevant (medium confidence)
- `work_score == 0` AND `personal_score == 0` --> Relevant (low confidence, include by default)

### 3. Transcript Extraction

Use `extract_transcript(video_id)` for single videos.

**Two-tier approach:**

**Tier 1: youtube-transcript-api (primary)**
- Faster, returns structured segments with timestamps.
- Returns: `{full_text, segments: [{start, text}], language}`.
- If cookies file exists, passes cookies via `requests.Session` with `MozillaCookieJar`.

**Tier 2: yt-dlp subtitle extraction (fallback)**
- Better at handling IP blocks (more robust cookie/auth handling).
- Downloads `.vtt` subtitle file, parses to plain text.
- Strips VTT timestamps, metadata, position tags, duplicate lines.
- Returns: `{full_text, segments: [], language: "en"}`.

**Failure modes:**
- Both tiers fail = `{success: false, error: "...", full_text: null, segments: []}`.
- No subtitles available (live stream, music video, non-English without auto-translate).
- Cookie expired = transcript API returns auth error, yt-dlp returns "sign in" error.

---

## Dedup Logic

The DedupTracker prevents re-processing videos. Understanding what gets dedup'd is critical:

### What gets dedup'd (added to processed set):
1. **Personal content** -- Classified as not relevant. Will never be re-checked.
2. **Successful transcript extraction** -- Transcript obtained. Processing complete.

### What does NOT get dedup'd (will retry next run):
1. **Failed transcript extraction** -- Transcript fetch failed (timeout, cookie issue, no subtitles). Will be retried on next extraction run.

### Dedup file location
- Path: `{queue_dir}/processed_videos.json`
- Default queue dir: `/opt/agents/queue/`
- Format:
```json
{
  "processed_ids": ["video_id_1", "video_id_2", "..."],
  "last_updated": "2026-03-15T10:30:00+00:00",
  "source": "web-agent"
}
```

### Force re-processing
Use `force=True` parameter to skip dedup and reprocess all videos.

---

## Cookie Requirements

### Why cookies are needed
YouTube blocks datacenter IP ranges. Without cookies, you get:
- "Sign in to confirm you're not a bot" errors
- Empty metadata responses
- No transcript access

### Cookie file
- Path: `/opt/agents/cookies/youtube.com.txt` (or `YOUTUBE_COOKIES_PATH` env var)
- Format: Netscape/Mozilla cookie format
- Source: Exported from Safari on Aakash's Mac
- Lifespan: Expires every 1-2 weeks

### Checking cookie health
```
cookie_status()
```

Or use the dedicated health check:
```python
check_cookie_health()  # Tests against known-good video (Rick Astley)
```

Returns:
```json
{
  "healthy": true,
  "error": null,
  "cookie_age_days": 3
}
```

**Warning signs:**
- `cookie_age_days > 7` -- Likely expired. Pipeline will warn.
- `healthy: false` with "bot detection triggered" -- Cookies definitely expired.
- `healthy: false` with "yt-dlp timed out" -- Network issue, not cookie issue.

### Refreshing cookies
Cookies must be refreshed from Aakash's Mac:
```bash
# On Mac:
yt-dlp --cookies-from-browser safari --cookies /tmp/cookies.txt --skip-download "https://youtube.com/watch?v=dQw4w9WgXcQ"
rsync /tmp/cookies.txt root@aicos-droplet:/opt/agents/cookies/youtube.com.txt
```

---

## Output Format

The extraction saves a JSON file to the queue directory:

**Filename:** `youtube_extract_{YYYY-MM-DD_HHMMSS}.json`

**Schema:**
```json
{
  "extraction_timestamp": "2026-03-15T10:30:00",
  "source_playlist": "https://youtube.com/playlist?list=...",
  "total_videos": 15,
  "relevant_videos": 12,
  "skipped_personal": 2,
  "skipped_dedup": 5,
  "videos": [
    {
      "video_id": "abc123def45",
      "title": "Video Title",
      "channel": "Channel Name",
      "duration_seconds": "1234",
      "upload_date": "20260315",
      "url": "https://www.youtube.com/watch?v=abc123def45",
      "relevance": {
        "relevant": true,
        "confidence": "high",
        "work_score": 3,
        "personal_score": 0
      },
      "transcript": {
        "success": true,
        "full_text": "Full transcript text...",
        "segments": [{"start": 0.0, "text": "..."}],
        "language": "en"
      }
    }
  ]
}
```

**Queue directory:** `/opt/agents/queue/` (default, configurable via `QUEUE_DIR` env var).

---

## Individual Video Extraction

For extracting specific videos (not from a playlist):

```
extract_youtube(video_urls=["https://youtube.com/watch?v=abc123", "https://youtube.com/watch?v=def456"])
```

This skips playlist metadata fetching and directly processes the given URLs. Dedup still applies unless `force=True`.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| "Sign in to confirm" in stderr | Cookies expired | Refresh cookies from Mac |
| Empty playlist (0 videos) | yt-dlp error or playlist URL wrong | Check yt-dlp stderr, verify URL |
| Transcript `success: false` | No subtitles or cookie issue | Check if video has CC; retry after cookie refresh |
| "yt-dlp timed out" | Network/DNS issue | Retry; check droplet connectivity |
| Dedup skipping everything | All videos already processed | Use `force=True` or check `processed_videos.json` |
