> **SUBSUMED — Canonical version now in `docs/source-of-truth/SYSTEM-STATE.md` (Scaling Roadmap section).** This file is preserved as the original research artifact.

# Droplet Scaling Roadmap

How to scale the DigitalOcean droplet as AI CoS infrastructure grows. Budget is unconstrained; operational simplicity is the constraint.

---

## Current State

| Spec | Value |
|------|-------|
| Provider | DigitalOcean |
| Plan | $12/mo (Basic) |
| vCPUs | 1 |
| RAM | 2 GB |
| Disk | 50 GB SSD |
| Transfer | 2 TB |

**Running services:** Postgres, ai-cos-mcp (FastMCP), Content Pipeline (cron), Cloudflare Tunnel, systemd services.

**Current resource profile:** Low. Content Pipeline runs every 5 min but each run is short (LLM calls are external, local work is JSON parsing + DB writes). MCP server handles low-volume tool calls. Postgres stores ~7 tables with low row counts.

---

## Scaling Triggers & Recommended Specs

### Tier 1: Current → Near-Term Growth
**Trigger:** Any of these become true:
- Postgres DB exceeds 5 GB (row growth from content pipeline + action outcomes)
- Adding pgvector extension (embedding storage + similarity search)
- Adding TimescaleDB extension (timeline queries on action_outcomes)
- Running 2+ pipeline crons concurrently (content + sync agent)

**Recommended spec:**
| Spec | Value |
|------|-------|
| Plan | $24/mo (Basic) |
| vCPUs | 2 |
| RAM | 4 GB |
| Disk | 80 GB SSD |

**Why:** pgvector similarity search is RAM-hungry. 4 GB gives comfortable headroom for Postgres with 2 extensions loaded. Second vCPU prevents pipeline runs from starving MCP server responses.

---

### Tier 2: Multi-Runner + Embedding Generation
**Trigger:** Any of these become true:
- Running 3+ autonomous runners (ContentAgent + SyncAgent + PostMeetingAgent)
- Generating embeddings locally (rather than calling external API)
- ER pipeline running as async worker
- Postgres DB exceeds 20 GB
- Action Frontend (Next.js) served from droplet (if not on Vercel)

**Recommended spec:**
| Spec | Value |
|------|-------|
| Plan | $48/mo (General Purpose) |
| vCPUs | 2 (dedicated) |
| RAM | 8 GB |
| Disk | 160 GB SSD |

**Why:** General Purpose droplets have dedicated (not shared) vCPUs — critical when runners are doing sustained work. 8 GB RAM handles Postgres with pgvector + multiple concurrent Python processes. 160 GB gives room for embedding storage growth.

**Key difference:** "Basic" plans share CPU with other tenants. Once you have always-on runners doing real work, dedicated CPU matters for latency predictability.

---

### Tier 3: Full Infrastructure
**Trigger:** Any of these become true:
- Graph store added (Neo4j or similar — memory hungry)
- Processing 10+ signal sources (YouTube, LinkedIn, X, WhatsApp, email, calendar, etc.)
- Embedding corpus exceeds 1M vectors
- Running ML model inference locally (classification, scoring beyond LLM API)
- Multiple developers hitting the MCP server concurrently

**Recommended spec:**
| Spec | Value |
|------|-------|
| Plan | $96/mo (General Purpose) |
| vCPUs | 4 (dedicated) |
| RAM | 16 GB |
| Disk | 320 GB SSD |

**Why:** Neo4j alone wants 4+ GB RAM. Combined with Postgres (pgvector + TimescaleDB), multiple runners, and embedding generation, 16 GB is the comfortable floor. 4 dedicated vCPUs handle concurrent pipeline runs without contention.

---

### Tier 4: Production Scale (if reached)
**Trigger:** System serves multiple users or external API traffic, or vector corpus exceeds 10M embeddings.

**At this point:** Consider splitting into multiple droplets or moving to managed services rather than scaling vertically. Managed Postgres (DO Managed Database, $15/mo starting) offloads backup/scaling. Separate compute droplet for runners. This is the "ops simplicity" ceiling for a single box.

---

## Scaling Decision Framework

**Prefer vertical scaling (bigger droplet) until:**
- A single service needs isolation (different OS deps, security boundary)
- You need zero-downtime deploys (can't restart everything at once)
- Backup/recovery for Postgres becomes critical enough to justify managed DB

**Prefer Postgres extensions over new services:**
- pgvector over self-hosted Qdrant/Pinecone (until 1M+ vectors)
- TimescaleDB extension over separate time-series DB
- Postgres JSONB + recursive CTEs over Neo4j (until graph queries become the bottleneck — evaluate per migration cost framework)

**When to split off managed Postgres:**
- DB exceeds 50 GB
- Need point-in-time recovery
- Multiple services writing concurrently with transaction isolation needs
- DO Managed Database starts at $15/mo — worth it when data is critical

---

## Resize Process

DigitalOcean droplet resize is straightforward:

1. **Power off** the droplet (1-2 min downtime)
2. **Resize** via DO console (select new plan)
3. **Power on** — all services restart via systemd
4. Total downtime: ~5 minutes

For disk-only expansion (no CPU/RAM change), DO supports live resize with no downtime.

**Important:** You can always scale UP a droplet. Scaling DOWN CPU/RAM requires creating a new droplet and migrating. Disk can never shrink. So don't over-provision disk — it's the one irreversible dimension.

---

## Cost Summary

| Tier | Monthly | When |
|------|---------|------|
| Current | $12 | Now |
| Tier 1 | $24 | pgvector + multi-cron |
| Tier 2 | $48 | Multi-runner + embeddings |
| Tier 3 | $96 | Graph store + full infra |
| Tier 4 | $100-200 | Split architecture |

All well within "budget unconstrained" territory. The real cost driver will be LLM API calls from runners, not infrastructure.
