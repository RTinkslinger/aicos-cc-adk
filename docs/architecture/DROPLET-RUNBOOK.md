# AI CoS Droplet Runbook

Operational guide for the DO droplet that runs the AI CoS MCP server and content pipeline.

## Infrastructure

| Item | Value |
|------|-------|
| Provider | DigitalOcean |
| Size | $12/mo (1 vCPU, 1GB RAM, 25GB disk) |
| OS | Ubuntu 24.04 |
| Access | Tailscale only — hostname `aicos-droplet` |
| SSH | `ssh root@aicos-droplet` (via Tailscale SSH) |
| IP | No public IP; Tailscale mesh network only |

## Services

### 1. MCP Server (`ai-cos-mcp`)

FastMCP server exposing tools for remote Claude clients.

| Item | Value |
|------|-------|
| Type | systemd service |
| Unit file | `/etc/systemd/system/ai-cos-mcp.service` |
| Code | `/opt/ai-cos-mcp/server.py` |
| Port | 8000 (SSE transport) |
| Runtime | `uv run server.py` |

```bash
systemctl status ai-cos-mcp      # check
systemctl restart ai-cos-mcp     # restart
journalctl -u ai-cos-mcp -f      # tail logs
```

**Tools exposed:** `health_check`, `cos_load_context`, `cos_score_action`, `cos_get_preferences`

### 2. Content Pipeline (cron)

Polls YouTube playlist every 5 minutes. If new videos are found, extracts transcripts, runs Claude analysis, publishes to digest.wiki, creates Notion entries, logs to Postgres.

| Item | Value |
|------|-------|
| Cron | `*/5 * * * *` |
| Wrapper | `/opt/ai-cos-mcp/cron/pipeline.sh` |
| Python | `/opt/ai-cos-mcp/runners/pipeline.py` |
| Log | `/opt/ai-cos-mcp/logs/pipeline.log` |
| Lock | `/tmp/aicos-pipeline-cron.lock` (bash flock) |

```bash
tail -f /opt/ai-cos-mcp/logs/pipeline.log    # watch live
crontab -l | grep ai-cos-mcp                 # verify cron
```

**Idle run:** ~10 seconds (playlist fetch + dedup check, no new videos).
**Active run:** ~45-60 seconds per new video (transcript fetch + Claude analysis + git push).

### 3. Digest Site (`aicos-digests`)

Next.js 16 static site at https://digest.wiki. The pipeline publishes JSON files to this repo and triggers Vercel via deploy hook.

| Item | Value |
|------|-------|
| Repo | `/opt/aicos-digests` (cloned from GitHub) |
| Remote | `https://github.com/RTinkslinger/aicos-digests.git` |
| Auth | GitHub personal access token embedded in remote URL |
| Git author | `Aakash Kumar <hi@aacash.me>` (required by Vercel) |
| Deploy chain | git pull → commit → push → Vercel deploy hook (~30s) |
| Deploy hook | `VERCEL_DEPLOY_HOOK` env var (curl POST, no auth needed) |

**Important:** The Vercel Git Integration (auto-deploy on push) is broken. Deploys are triggered explicitly via the deploy hook in `lib/publishing.py`. Do NOT re-enable the GitHub Actions deploy workflow — it was removed to avoid conflicts.

## Directory Layout

```
/opt/ai-cos-mcp/
├── .env                    # Credentials (see below)
├── cookies.txt             # YouTube auth cookies (see Cookie Refresh)
├── CONTEXT.md              # Domain context for prompt hydration
├── server.py               # MCP server
├── lib/                    # Core library modules
├── runners/                # Pipeline + content agent
├── cron/                   # Cron wrappers
├── queue/                  # Extraction JSONs (transient)
│   ├── processed/          # Analyzed extractions (archived)
│   └── processed_videos.json  # Dedup tracker
└── logs/
    └── pipeline.log        # Pipeline output

/opt/aicos-digests/         # digest.wiki Next.js repo
└── src/data/               # Digest JSONs (published here)
```

## Credentials

All credentials live in `/opt/ai-cos-mcp/.env`. This file is **not** synced by deploy.sh.

| Variable | Purpose | Rotation |
|----------|---------|----------|
| `ANTHROPIC_API_KEY` | Claude API for video analysis | Rotate via Anthropic console |
| `NOTION_TOKEN` | Notion internal integration | Rotate via notion.so/my-integrations |
| `DATABASE_URL` | Postgres connection string | Managed via DO dashboard |
| `YOUTUBE_PLAYLIST_URL` | Default playlist to poll | Change anytime |
| `YOUTUBE_COOKIES_PATH` | Path to cookies.txt (default: `./cookies.txt`) | See Cookie Refresh below |
| `AICOS_DIGESTS_REPO` | Path to digest site repo (default: `/opt/aicos-digests`) | Rarely changes |
| `VERCEL_DEPLOY_HOOK` | Vercel deploy hook URL (triggers production build) | Rotate via Vercel dashboard → Project → Settings → Git → Deploy Hooks |
| `QUEUE_DIR` | Queue directory (default: `./queue`) | Rarely changes |
| `CONTEXT_MD_PATH` | CONTEXT.md path (default: `./CONTEXT.md`) | Rarely changes |

**GitHub token** is embedded in the aicos-digests git remote URL. To rotate:
```bash
cd /opt/aicos-digests
NEW_TOKEN="ghp_..."
git remote set-url origin "https://x-access-token:${NEW_TOKEN}@github.com/RTinkslinger/aicos-digests.git"
```

## Cookie Refresh Procedure

YouTube blocks datacenter IPs from fetching video content. The pipeline uses exported browser cookies to authenticate. **Cookies expire every 1-2 weeks.**

### When to refresh

- Pipeline log shows: `WARNING: YouTube cookie check failed`
- Pipeline log shows: `WARNING: cookies.txt is N days old`
- All videos show `No transcript` errors
- Cookie age > 14 days

### How to refresh

From your Mac terminal:

```bash
# 1. Export cookies from Safari
yt-dlp --cookies-from-browser safari --cookies /tmp/cookies.txt \
  --skip-download "https://youtube.com/watch?v=dQw4w9WgXcQ"

# 2. Upload to droplet
rsync /tmp/cookies.txt root@aicos-droplet:/opt/ai-cos-mcp/cookies.txt

# 3. Verify
ssh root@aicos-droplet 'export PATH="/root/.deno/bin:$PATH" && cd /opt/ai-cos-mcp && \
  /root/.local/bin/uv run python -c "from lib.extraction import check_cookie_health; print(check_cookie_health())"'
```

### Why cookies are needed

YouTube uses anti-bot detection on datacenter IPs. Without cookies:
- `youtube-transcript-api` gets `RequestBlocked` exceptions
- `yt-dlp` gets "Sign in to confirm you're not a bot" errors

The cookies prove you're a real YouTube user. They're exported in Netscape cookie format from your browser.

## Installed Software

| Package | Purpose | Install method |
|---------|---------|---------------|
| Python 3.12 | Runtime | System |
| uv | Python package manager | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| deno | JavaScript runtime for yt-dlp | `curl -fsSL https://deno.land/install.sh \| sh` (at `/root/.deno/bin/deno`) |
| yt-dlp | YouTube metadata + subtitle extraction | uv (in .venv) |
| git | Version control for digest publishing | System |

**PATH note:** Cron doesn't inherit shell PATH. `cron/pipeline.sh` explicitly sets:
```bash
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/root/.deno/bin"
```

## Pipeline Data Flow

```
YouTube Playlist (polled every 5 min)
    │
    ▼
yt-dlp --flat-playlist (with cookies + remote-components)
    │ Returns: video_id, title, channel, duration, upload_date
    │
    ▼
Dedup check (queue/processed_videos.json)
    │ Skip videos already successfully processed
    │ Videos with failed transcripts are NOT dedup'd (retried next run)
    │
    ▼
Relevance classification (keyword matching)
    │ Personal content → dedup'd and skipped
    │ Work-relevant → continue
    │
    ▼
Transcript fetch (two attempts):
    │ 1. youtube-transcript-api (with cookies via requests.Session)
    │ 2. yt-dlp --write-auto-sub (with cookies + remote-components)
    │
    ▼
Claude Analysis (claude-sonnet-4, 8192 max_tokens)
    │ System prompt: content_analysis.md hydrated with thesis/portfolio/preferences
    │ Returns: DigestData JSON (slug, title, essence_notes, actions, etc.)
    │
    ▼
Action Scoring (weighted model, 0-10 scale)
    │ ≥7 → "surface" (immediate action)
    │ 4-7 → "low_confidence"
    │ <4 → "context_only"
    │
    ▼ ┌─────────────────────────┐
    ├─│ digest.wiki publish     │ git push → GitHub Action → Vercel (~90s)
    │ └─────────────────────────┘
    │ ┌─────────────────────────┐
    ├─│ Notion entries          │ Content Digest DB + Actions Queue + Thesis Tracker
    │ └─────────────────────────┘
    │ ┌─────────────────────────┐
    └─│ Postgres logging        │ action_outcomes table (preference store)
      └─────────────────────────┘
```

## Failure Recovery

### Pipeline not running
```bash
# Check cron
crontab -l | grep ai-cos-mcp

# Check for stale lockfile
ls -la /tmp/aicos-pipeline-cron.lock
rm -f /tmp/aicos-pipeline-cron.lock   # safe to remove

# Manual test run
export PATH="/root/.deno/bin:$PATH"
cd /opt/ai-cos-mcp && /root/.local/bin/uv run python -m runners.pipeline --dry-run
```

### All transcripts failing
Most likely: cookies expired. See Cookie Refresh Procedure above.

### Claude analysis failing
```bash
# Check API key
grep ANTHROPIC /opt/ai-cos-mcp/.env

# Test Claude API
cd /opt/ai-cos-mcp && /root/.local/bin/uv run python -c "
import anthropic; c = anthropic.Anthropic()
r = c.messages.create(model='claude-sonnet-4-20250514', max_tokens=10, messages=[{'role':'user','content':'hi'}])
print(r.content[0].text)
"
```

### Digest not appearing on digest.wiki
```bash
# Check git push status
cd /opt/aicos-digests && git status && git log --oneline -3

# Manual push
cd /opt/aicos-digests && git push origin main

# Check GitHub Actions
# Visit: https://github.com/RTinkslinger/aicos-digests/actions
```

### Notion writes failing
```bash
# Check token
grep NOTION /opt/ai-cos-mcp/.env

# Test Notion API
cd /opt/ai-cos-mcp && /root/.local/bin/uv run python -c "
from notion_client import Client
c = Client(auth='<token>')
print(c.users.me())
"
```

### Dedup stuck (videos being skipped that shouldn't be)
```bash
# View tracked IDs
cat /opt/ai-cos-mcp/queue/processed_videos.json | python3 -m json.tool

# Remove specific ID
python3 -c "
import json
with open('/opt/ai-cos-mcp/queue/processed_videos.json') as f:
    d = json.load(f)
d['processed_ids'].remove('VIDEO_ID_HERE')
with open('/opt/ai-cos-mcp/queue/processed_videos.json', 'w') as f:
    json.dump(d, f, indent=2)
"

# Nuclear: reset all dedup
rm /opt/ai-cos-mcp/queue/processed_videos.json
```

### MCP server down
```bash
systemctl restart ai-cos-mcp
journalctl -u ai-cos-mcp -f  # check for errors
```

## Deploying Updates

From your Mac, inside `mcp-servers/ai-cos-mcp/`:

```bash
./deploy.sh
```

This:
1. rsyncs code to droplet (excludes .env, .venv, __pycache__)
2. Runs `uv sync` to install deps
3. Restarts MCP server
4. Syncs CONTEXT.md
5. Pulls latest aicos-digests
6. Installs/updates cron job
7. Cleans stale lockfiles

**Manual partial deploy** (just code, no restart):
```bash
rsync -avz --exclude='.env' --exclude='__pycache__' --exclude='.venv' \
  ./ root@aicos-droplet:/opt/ai-cos-mcp/
```

## Monitoring

```bash
# Live pipeline log
ssh root@aicos-droplet "tail -f /opt/ai-cos-mcp/logs/pipeline.log"

# MCP server log
ssh root@aicos-droplet "journalctl -u ai-cos-mcp -f"

# System resources
ssh root@aicos-droplet "htop"

# Disk usage
ssh root@aicos-droplet "df -h /opt"

# Recent digest commits
ssh root@aicos-droplet "cd /opt/aicos-digests && git log --oneline -10"

# Dedup state
ssh root@aicos-droplet "cat /opt/ai-cos-mcp/queue/processed_videos.json | python3 -c 'import json,sys; d=json.load(sys.stdin); print(len(d[\"processed_ids\"]),\"videos tracked\")'"
```
