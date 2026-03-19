# AI CoS Droplet Runbook

Operational guide for the DO droplet running the v3 persistent agent system.

## Infrastructure

| Item | Value |
|------|-------|
| Provider | DigitalOcean |
| Size | s-2vcpu-4gb ($24/mo) |
| OS | Ubuntu 24.04 |
| Access | Tailscale only — hostname `aicos-droplet` |
| SSH | `ssh root@aicos-droplet` (via Tailscale SSH) |
| IP | No public IP; Tailscale mesh network only |

## Services

### 1. Orchestrator (`orchestrator.service`)

Python lifecycle manager running two persistent ClaudeSDKClient agents (orchestrator + content agent). Sends heartbeats, relays inbox messages, triggers content pipeline.

| Item | Value |
|------|-------|
| Unit file | `/etc/systemd/system/orchestrator.service` |
| Code | `/opt/agents/orchestrator/lifecycle.py` |
| WorkingDirectory | `/opt/agents/orchestrator` |
| Manages | Orchestrator agent + Content agent (both persistent sessions) |
| Heartbeat | Every 60s (Python pre-check skips LLM if no work) |

```bash
systemctl status orchestrator
systemctl restart orchestrator
journalctl -u orchestrator -f
```

### 2. State MCP (`state-mcp.service`)

FastMCP server — CAI's window into system state. 5 tools.

| Item | Value |
|------|-------|
| Unit file | `/etc/systemd/system/state-mcp.service` |
| Code | `/opt/agents/state/server.py` |
| Port | 8000 |
| Tunnel | `https://mcp.3niac.com/mcp` |
| Tools | `get_state`, `create_thesis_thread`, `update_thesis`, `post_message`, `health_check` |

```bash
systemctl status state-mcp
curl -sf http://localhost:8000/health
```

### 3. Web Tools MCP (`web-tools-mcp.service`)

FastMCP server — browser automation, scraping, search. 11+ tools.

| Item | Value |
|------|-------|
| Unit file | `/etc/systemd/system/web-tools-mcp.service` |
| Code | `/opt/agents/web/server.py` |
| Port | 8001 |
| Tunnel | `https://web.3niac.com/mcp` |

```bash
systemctl status web-tools-mcp
curl -sf http://localhost:8001/health
```

### Postgres (migrating to Supabase)

Currently runs on the droplet. **Planned migration to Supabase** (managed Postgres with real-time, PostgREST, MCP). After migration, droplet becomes pure compute — agents connect to Supabase via `DATABASE_URL`, same as WebFront on Vercel. See `WEBFRONT.md` for migration steps.

### 4. Digest Site (`aicos-digests`)

Next.js 16 static site at https://digest.wiki. Content agent publishes JSON files and git pushes. Vercel auto-deploys.

| Item | Value |
|------|-------|
| Repo | `/opt/aicos-digests` |
| Remote | `https://github.com/RTinkslinger/aicos-digests.git` |
| Git author | `Aakash Kumar <hi@aacash.me>` (required by Vercel) |
| Deploy | git push → Vercel auto-deploy (~15s) |

## Directory Layout

```
/opt/agents/
├── .env                        # Credentials (not synced by deploy)
├── CONTEXT.md                  # Domain context (synced from parent project)
├── orchestrator/
│   ├── lifecycle.py            # Python daemon (manages both agents)
│   ├── CLAUDE.md               # Orchestrator identity + rules
│   ├── HEARTBEAT.md            # Heartbeat checklist
│   ├── COMPACTION_PROTOCOL.md  # Traces rotation protocol
│   ├── CHECKPOINT_FORMAT.md    # Session checkpoint template
│   ├── .claude/hooks/          # Filesystem hooks (Stop, UserPromptSubmit, PreCompact)
│   ├── .claude/settings.json   # Hook registration
│   ├── state/                  # Runtime: session/iteration counters, logs
│   └── live.log                # Real-time activity log (PostToolUse hooks)
├── content/
│   ├── CLAUDE.md               # Content agent identity + pipeline + scoring
│   ├── CHECKPOINT_FORMAT.md    # Session checkpoint template
│   ├── .claude/hooks/          # Filesystem hooks
│   ├── .claude/settings.json   # Hook registration
│   ├── state/                  # Runtime: session/iteration, last_pipeline_run.txt
│   └── live.log                # Real-time activity log
├── state/                      # State MCP server code
│   ├── server.py
│   └── db/                     # Postgres connection, inbox, notifications, thesis
├── web/                        # Web Tools MCP server code
│   ├── server.py
│   └── lib/                    # Browser, scrape, search, fingerprint, strategy
├── skills/                     # 14 skill markdown files
├── traces/                     # Shared iteration logs
│   ├── manifest.json           # Token usage per agent
│   ├── active.txt              # Pointer to current traces file
│   └── *.md                    # Traces files (rotated by orchestrator)
├── data/
│   ├── watch_list.json         # Curated content sources (manual only)
│   └── digests/                # Published digest JSONs
├── deploy/                     # Deploy scripts
│   ├── bootstrap.sh            # First-run state seeding
│   └── cleanup.sh              # Remove stale files
├── infra/                      # systemd unit files
├── cookies/                    # YouTube auth cookies (synced from Mac)
└── logs/                       # Service logs

/opt/aicos-digests/             # digest.wiki Next.js repo
└── src/data/                   # Digest JSONs (content agent publishes here)
```

## Credentials

All in `/opt/agents/.env`. NOT synced by deploy.sh.

| Variable | Purpose | Rotation |
|----------|---------|----------|
| `ANTHROPIC_API_KEY` | Claude API for agents | Anthropic console |
| `DATABASE_URL` | Postgres connection string (currently local, migrating to Supabase) | DO dashboard → Supabase dashboard |
| `FIRECRAWL_API_KEY` | Web search/scrape | Firecrawl dashboard |

**GitHub token** embedded in aicos-digests git remote URL. To rotate:
```bash
cd /opt/aicos-digests
NEW_TOKEN="ghp_..."
git remote set-url origin "https://x-access-token:${NEW_TOKEN}@github.com/RTinkslinger/aicos-digests.git"
```

## Cookie Refresh Procedure

YouTube blocks datacenter IPs. Cookies expire every 1-2 weeks.

### When to refresh

- Content agent's YouTube extraction fails repeatedly
- Cookie files > 14 days old: `ls -la /opt/agents/cookies/`

### How to refresh

From Mac terminal:
```bash
# 1. Export cookies from Safari
yt-dlp --cookies-from-browser safari --cookies /tmp/cookies.txt \
  --skip-download "https://youtube.com/watch?v=dQw4w9WgXcQ"

# 2. Upload to droplet
rsync /tmp/cookies.txt root@aicos-droplet:/opt/agents/cookies/youtube.txt

# 3. Verify age
ssh root@aicos-droplet 'ls -la /opt/agents/cookies/youtube.txt'
```

Or use the automated cookie-sync script (daily cron on Mac):
```bash
~/.ai-cos/scripts/cookie-sync.sh
```

## Deploying Updates

From Mac, inside `mcp-servers/agents/`:
```bash
bash deploy.sh
```

3-phase deploy:
1. **SYNC** — rsync code (excludes runtime state/traces/data), sync tools + skills + CONTEXT.md
2. **BOOTSTRAP** — create dirs and seed state files if missing (idempotent)
3. **CLEANUP + RESTART** — remove stale files, install systemd units, restart services in dependency order

See `deploy/DROPLET-MANIFEST.md` for complete file inventory.

## Monitoring

### Live dashboards (4 terminal tabs)

```bash
# Orchestrator activity (real-time tool calls, thinking, text)
ssh -t root@aicos-droplet /opt/agents/live-orc.sh

# Content agent activity
ssh -t root@aicos-droplet /opt/agents/live-content.sh

# Traces (iteration logs from Stop hook)
ssh -t root@aicos-droplet /opt/agents/live-traces.sh

# Python lifecycle logs
ssh -t root@aicos-droplet journalctl -u orchestrator -f
```

### Quick checks

```bash
# All services status
ssh root@aicos-droplet 'systemctl is-active state-mcp web-tools-mcp orchestrator'

# MCP health
ssh root@aicos-droplet 'curl -sf http://localhost:8000/health && curl -sf http://localhost:8001/health'

# Memory
ssh root@aicos-droplet 'free -h | head -2'

# Disk
ssh root@aicos-droplet 'df -h /opt'

# Inbox status
ssh root@aicos-droplet 'psql postgresql://aicos:XPa10EuFJgfyUb5mnBr6laxEJLvAYIW@localhost:5432/aicos_db -t -c "SELECT count(*) FROM cai_inbox WHERE processed = FALSE"'

# Content digests
ssh root@aicos-droplet 'psql postgresql://aicos:XPa10EuFJgfyUb5mnBr6laxEJLvAYIW@localhost:5432/aicos_db -t -c "SELECT count(*), status FROM content_digests GROUP BY status"'

# Recent digest commits
ssh root@aicos-droplet 'cd /opt/aicos-digests && git log --oneline -5'
```

## Failure Recovery

### Orchestrator not processing heartbeats
```bash
# Check if running
systemctl status orchestrator

# Check for budget exhaustion (0-turn heartbeats in log)
journalctl -u orchestrator --no-pager -n 20

# Restart (fresh session, budget resets)
systemctl restart orchestrator
```

### Content agent stuck/busy
```bash
# Check live log
tail -20 /opt/agents/content/live.log

# Restart orchestrator (restarts both agents)
systemctl restart orchestrator
```

### MCP server down
```bash
systemctl restart state-mcp      # or web-tools-mcp
journalctl -u state-mcp -f       # check for errors
```

### Digest not appearing on digest.wiki
```bash
# Check git status
cd /opt/aicos-digests && git status && git log --oneline -3

# Manual push
cd /opt/aicos-digests && git push origin main
```

### Claude API failing
```bash
# Check key
grep ANTHROPIC /opt/agents/.env

# Test API
cd /opt/agents && .venv/bin/python3 -c "
import anthropic; c = anthropic.Anthropic()
r = c.messages.create(model='claude-sonnet-4-6', max_tokens=10, messages=[{'role':'user','content':'hi'}])
print(r.content[0].text)
"
```

### Postgres connection failing
```bash
psql postgresql://aicos:XPa10EuFJgfyUb5mnBr6laxEJLvAYIW@localhost:5432/aicos_db -c "SELECT 1"
```

## Scaling Roadmap

How to scale the droplet as infrastructure grows. Budget is unconstrained; operational simplicity is the constraint.

### Tier 1: Current ($24/mo)

s-2vcpu-4gb. Running 3 services + persistent agents. Comfortable for current workload.

### Tier 2: Multi-Runner + Embeddings ($48/mo)

**Trigger:** Running 3+ autonomous agents, generating embeddings locally, or Postgres DB exceeds 20 GB.

General Purpose (2 dedicated vCPUs, 8 GB RAM, 160 GB SSD). Dedicated CPUs critical when agents do sustained work.

### Tier 3: Full Infrastructure ($96/mo)

**Trigger:** Graph store added, processing 10+ signal sources, embedding corpus exceeds 1M vectors.

General Purpose (4 dedicated vCPUs, 16 GB RAM, 320 GB SSD).

### Scaling Principles

- **Prefer vertical scaling** (bigger droplet) until a service needs isolation or zero-downtime deploys.
- **Prefer Postgres extensions** over new services: pgvector over Qdrant, TimescaleDB over separate time-series DB, CTEs over Neo4j.
- **Resize process:** Power off (1-2 min), resize via DO console, power on — ~5 min downtime. Disk can never shrink (irreversible).

---

## Installed Software

| Package | Purpose | Install |
|---------|---------|---------|
| Python 3.12 | Runtime | System |
| uv | Package manager | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Google Chrome 146 | Playwright browser | `apt install google-chrome-stable` |
| Playwright | Browser automation | Via uv (in .venv) |
| PostgreSQL 16 | Database | System |
| cloudflared | Tunnel to Cloudflare edge | `.deb` from GitHub releases |
| Tailscale | Mesh VPN | `curl -fsSL https://tailscale.com/install.sh \| sh` |
