# System State
*Last Updated: 2026-03-07*

Current infrastructure, services, endpoints, and operational state of the AI CoS system.

---

## Infrastructure Overview

| Component | Details |
|-----------|---------|
| **Compute** | DigitalOcean droplet, $12/mo, 1 vCPU, 1GB RAM, 25GB disk, Ubuntu 24.04 |
| **Access** | Tailscale mesh only, hostname `aicos-droplet`, `ssh root@aicos-droplet` |
| **Database** | PostgreSQL on droplet (local), 7 tables |
| **Public Endpoint** | `https://mcp.3niac.com/mcp` via Cloudflare Tunnel (zero-trust, auto-TLS) |
| **Domain** | `3niac.com` (Cloudflare DNS), used for MCP tunnel endpoint |
| **Digest Site** | `https://digest.wiki` (Vercel, Next.js 16, auto-deploy on git push) |
| **Networking** | Tailscale for all internal access, Cloudflare Tunnel for public MCP |

---

## Services

### 1. ai-cos-mcp (MCP Server)

| Item | Value |
|------|-------|
| Type | systemd service (always-on) |
| Unit file | `/etc/systemd/system/ai-cos-mcp.service` |
| Code | `/opt/ai-cos-mcp/server.py` |
| Runtime | `uv run server.py` (FastMCP Python) |
| Transport | Streamable HTTP (MCP spec 2025-06-18) |
| Port | 8000 (localhost) |
| Public URL | `https://mcp.3niac.com/mcp` (Cloudflare Tunnel) |
| Tools | 17 MCP tools (see MCP-TOOLS-INVENTORY.md) |

Commands: `systemctl status ai-cos-mcp`, `systemctl restart ai-cos-mcp`, `journalctl -u ai-cos-mcp -f`

### 2. Content Pipeline (Cron)

| Item | Value |
|------|-------|
| Schedule | Every 5 minutes |
| Wrapper | `/opt/ai-cos-mcp/cron/pipeline.sh` |
| Orchestrator | `/opt/ai-cos-mcp/runners/pipeline.py` |
| Log | `/opt/ai-cos-mcp/logs/pipeline.log` |
| Lock | `/tmp/aicos-pipeline-cron.lock` (bash flock) |
| Idle run | ~10 seconds |
| Active run | ~45-60 seconds per new video |

Pipeline flow: YouTube playlist poll, yt-dlp extraction, dedup check, transcript fetch, Claude analysis (ContentAgent), Notion writes (Content Digest + Actions Queue + Thesis Tracker), digest.wiki publish (JSON + git push + Vercel deploy)

### 3. SyncAgent (Cron)

| Item | Value |
|------|-------|
| Schedule | Every 10 minutes |
| Command | `cd /opt/ai-cos-mcp && uv run python -m runners.sync_agent full` |
| Log | `/opt/ai-cos-mcp/logs/sync_agent.log` |

Sync flow: Thesis status sync (Notion to Postgres), Actions bidirectional sync, Retry queue drain, Change detection, Action generation from changes

### 4. Cloudflare Tunnel

| Item | Value |
|------|-------|
| Tunnel name | `aicos-mcp` |
| DNS route | `mcp.3niac.com` routes to `localhost:8000` on droplet |
| Service | `cloudflared` (installed via apt) |
| TLS | Automatic via Cloudflare, valid certs, zero config |
| Auth | Currently authless (public endpoint) |

### 5. Digest Site (aicos-digests)

| Item | Value |
|------|-------|
| Tech | Next.js 16 + React 19 + Tailwind CSS 4 (SSG) |
| Domain | `https://digest.wiki` (Vercel) |
| GitHub | `github.com/RTinkslinger/aicos-digests` |
| Droplet clone | `/opt/aicos-digests` |
| Deploy | Git push triggers Vercel Git Integration auto-deploy (~15s) |
| Backup deploy | POST to VERCEL_DEPLOY_HOOK env var |
| Git author | `Aakash Kumar <hi@aacash.me>` (required by Vercel) |

---

## Endpoints

| Endpoint | Access | Purpose |
|----------|--------|---------|
| `https://mcp.3niac.com/mcp` | Public (Cloudflare Tunnel) | MCP server for Claude.ai remote connector |
| `localhost:8000` | Droplet only | MCP server local |
| `https://digest.wiki` | Public (Vercel) | Content digest site |

---

## Connected Surfaces

| Surface | Connection Method | Status |
|---------|------------------|--------|
| Claude.ai | Remote MCP connector via mcp.3niac.com/mcp | Connected |
| Claude Code | .mcp.json via Tailscale (aicos-droplet:8000) | Connected |
| Notion | Internal integration token (NOTION_TOKEN in .env) | Connected |
| Vercel | Git Integration + deploy hook | Connected |
| GitHub | PAT embedded in git remote URL (aicos-digests) | Connected |
| YouTube | yt-dlp with browser cookies | Connected (cookies expire every 1-2 weeks) |
| Granola | MCP (query/transcript) from Claude surfaces | Connected (not automated) |
| Google Calendar | MCP from Claude surfaces | Connected (not automated) |
| Gmail | MCP from Claude surfaces | Connected (not automated) |

---

## Directory Layout (Droplet)

```
/opt/ai-cos-mcp/
  .env                    # Credentials (not synced by deploy.sh)
  cookies.txt             # YouTube auth cookies
  CONTEXT.md              # Domain context (synced from Mac)
  server.py               # MCP server entry point
  lib/                    # Core: notion_client, thesis_db, actions_db,
                          #   change_detection, scoring, preferences
  runners/                # Pipeline, content_agent, sync_agent, publishing, extraction
  cron/                   # Cron wrapper scripts
  queue/                  # Extraction JSONs (transient)
    processed/            # Analyzed extractions (archived)
    processed_videos.json # Dedup tracker
  logs/
    pipeline.log          # Content pipeline output
    sync_agent.log        # SyncAgent output

/opt/aicos-digests/       # digest.wiki Next.js repo (separate git repo)
  src/data/               # Digest JSONs published here
```

---

## Credentials (in /opt/ai-cos-mcp/.env)

| Variable | Purpose |
|----------|---------|
| ANTHROPIC_API_KEY | Claude API for content analysis |
| NOTION_TOKEN | Notion internal integration |
| DATABASE_URL | Postgres connection string |
| YOUTUBE_PLAYLIST_URL | Default playlist to poll |
| YOUTUBE_COOKIES_PATH | Path to cookies.txt |
| AICOS_DIGESTS_REPO | Path to digest site repo |
| VERCEL_DEPLOY_HOOK | Vercel deploy hook URL |
| QUEUE_DIR | Queue directory |
| CONTEXT_MD_PATH | CONTEXT.md path |

GitHub PAT is embedded in the aicos-digests git remote URL (not in .env).

---

## Deployment

From Mac, inside mcp-servers/ai-cos-mcp/:

Run `./deploy.sh` which rsyncs code, runs uv sync, restarts MCP server, syncs CONTEXT.md, pulls latest aicos-digests, installs/updates both cron jobs, cleans stale lockfiles.

Key detail: deploy.sh manages BOTH cron jobs (pipeline every 5 min and SyncAgent every 10 min). It strips all ai-cos-mcp cron entries and re-adds them fresh on each deploy, so any cron changes must be made in deploy.sh.

---

## Monitoring

Pipeline log: `ssh root@aicos-droplet "tail -f /opt/ai-cos-mcp/logs/pipeline.log"`

MCP server log: `ssh root@aicos-droplet "journalctl -u ai-cos-mcp -f"`

SyncAgent log: `ssh root@aicos-droplet "tail -f /opt/ai-cos-mcp/logs/sync_agent.log"`

Cron status: `ssh root@aicos-droplet "crontab -l | grep ai-cos-mcp"`

---

## Cookie Refresh (YouTube)

YouTube blocks datacenter IPs. Pipeline uses browser cookies that expire every 1-2 weeks.

Export from Safari on Mac: `yt-dlp --cookies-from-browser safari --cookies /tmp/cookies.txt --skip-download "https://youtube.com/watch?v=dQw4w9WgXcQ"`

Upload to droplet: `rsync /tmp/cookies.txt root@aicos-droplet:/opt/ai-cos-mcp/cookies.txt`

Signs of expired cookies: WARNING YouTube cookie check failed in pipeline log, all transcripts failing.

---

## Detailed Reference

- Full operational runbook: `docs/architecture/DROPLET-RUNBOOK.md`
- Deploy script: `mcp-servers/ai-cos-mcp/deploy.sh`
- MCP config (Claude Code): `.mcp.json`
