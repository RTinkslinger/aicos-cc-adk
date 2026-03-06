# Data Sovereignty — Source of Truth Map

> Defines where authoritative data lives for each AI CoS database, how sync flows between Notion and the droplet, and the architectural patterns for each.

## Source of Truth Map

| Database | Source of Truth | Droplet Role | Notion Role | Sync Pattern |
|----------|----------------|-------------|-------------|-------------|
| **Content Digest** | **Droplet** | Creates analysis, stores full record | View layer (Action Status editable) | Push: droplet → Notion |
| **Actions Queue** | **Both** | Creates proposals; some triages arrive here first | Some triages happen here first | Bidirectional, conflict-aware |
| **Thesis Tracker** | **Droplet → Notion** (AI-managed, transitioning) | Creates threads, updates conviction/evidence/key questions. Becoming single write authority via public MCP endpoint. | View layer + Status field (human-only). All other fields AI-written via ai-cos-mcp tools. | Push: droplet → Notion. All surfaces (Claude.ai, Claude Code, Content Pipeline) write through ai-cos-mcp. |
| **Companies DB** | **Droplet (enriched)** + Notion (human fields) | Full enriched version — agent-curated IDS, computed data | Limited view: human-managed fields (name, deal status, sector) | Pull Notion fields periodically. Change detection → actions. |
| **Network DB** | **Droplet (enriched)** + Notion (human fields) | Same as Companies — enriched, evolving | Human-managed core fields | Same as Companies |
| **Portfolio DB** | **Droplet (enriched)** + Notion (human fields) | Same as Companies/Network — enriched, evolving | Financial data, follow-ons, human-managed fields. Each entry has a hidden `Company Name` relation property linking to Companies DB. | Same as Companies/Network |

## Key Principles

### 1. Notion is the Human Interface, Droplet is the Brain

Aakash interacts with data in Notion. The AI CoS agent reasons over data on the droplet. The droplet's version is always **equal or richer** — it has everything Notion has (synced periodically) plus agent-generated analysis, computed fields, and historical enrichments that don't map to Notion's schema.

### 2. Field-Level Ownership

For Companies, Network, and Portfolio: Notion owns the human-managed fields (company name, deal status, sector, contact info, etc.). The droplet owns enriched fields (agent IDS notes, computed scores, historical signals). On sync, Notion field values overwrite the corresponding droplet columns — but enriched columns are never touched by the sync.

### 3. Change Detection as Signal

When Notion fields change between sync cycles (Aakash moves a company from Pipeline to Portfolio, adds a new person to Network DB, updates deal status), the sync engine detects the diff and generates events. These changes are themselves **signals** — "Company X deal status changed from Active Pipeline to IC Ready" is actionable intelligence for the AI CoS.

### 4. Write-Ahead for Droplet-Originated Data

Content Digest entries and proposed Actions are created in Postgres first, then pushed to Notion. If the Notion API call fails, the data is safe locally and retried on the next sync cycle. No data loss.

### 5. Bidirectional Sync for Actions Queue

Actions can be triaged from multiple surfaces — some triage events arrive at the droplet first (agent-driven), some at Notion first (manual). The sync engine must handle both directions. Conflict resolution: last-writer-wins at field level, using timestamps.

## Database Detail

### Content Digest DB
- **SoT:** Droplet (Postgres)
- **Droplet creates:** Full analysis JSON, digest URL, relevance score, net newness, connected buckets, proposed actions, portfolio connections, thesis connections
- **Notion receives:** Summary view — Video Title, Video URL, Channel, Relevance Score, Net Newness, Digest URL, Discovery Source, Action Status, Connected Buckets
- **Notion → Droplet:** Action Status changes (Pending → Reviewed → Actions Taken → Skipped)
- **Sync:** Push after pipeline creates entry. Pull Action Status periodically.

### Actions Queue
- **SoT:** Both (bidirectional)
- **Droplet creates:** Proposed actions from Content Pipeline (Source = ContentAgent), agent-generated actions
- **Notion creates/edits:** Manual actions, status changes (Proposed → Accepted → In Progress → Done / Dismissed)
- **Other surfaces:** Future triage UX on digest.wiki, WhatsApp responses — these hit the droplet first
- **Conflict:** Field-level last-writer-wins. Status field is most conflict-prone.
- **Sync:** Push proposals droplet → Notion. Pull status changes Notion → droplet. Bidirectional on triage events.

### Thesis Tracker (AI-Managed Conviction Engine)
- **SoT:** Droplet (transitioning from Notion). All fields are AI-written except Status (human-only).
- **Architecture:** All write surfaces (Claude.ai, Claude Code, Content Pipeline) route through ai-cos-mcp tools on the droplet. The droplet is the single write authority; Notion is the view layer.
- **Public MCP endpoint:** Droplet exposes ai-cos-mcp via Cloudflare Tunnel (TLS, authless). Claude.ai connects as a remote MCP connector. Claude Code connects via MCP config (Tailscale or tunnel).
- **MCP tools:**
  - `cos_create_thesis_thread` — creates new threads (Conviction = "New", Status = "Exploring")
  - `cos_update_thesis` — appends evidence, updates conviction, manages key questions
  - `cos_get_thesis_threads` — reads current thesis state for any surface
- **Droplet writes (to Notion via API):**
  - Creates new thesis threads autonomously (Discovery Source = "Content Pipeline" or surface name)
  - Appends evidence blocks to page body with `[date] [source] (direction) evidence` format
  - Updates Conviction level (New → Evolving → Evolving Fast → Low → Medium → High)
  - Appends to Evidence For / Evidence Against property text (IDS notation: + for, ? against)
  - Adds key questions as `[OPEN]` page blocks, marks `[ANSWERED]` when evidence resolves them
  - Updates Investment Implications, Key Companies
- **Human writes:** Status only (Active / Exploring / Parked / Archived) — this weights action scoring
- **Conviction spectrum:** New / Evolving / Evolving Fast (maturity axis) → Low / Medium / High (strength axis for well-formed thesis)
- **Sync:** Pull Status from Notion periodically (human-owned field). Cache refresh: every pipeline run (5 min). If Notion unreachable, use last cached state (or CONTEXT.md fallback).
- **Future:** Add `thesis_threads` Postgres table as primary store with write-ahead pattern (same as Content Digest). Notion becomes eventually-consistent view.

### Companies DB
- **SoT:** Droplet (enriched) + Notion (human fields)
- **Notion-owned fields:** Company Name, Deal Status, Stage, Sector, Thesis, Spiky Score, EO/FMF/Thesis/Price scores, Founders (relation to Network DB), Team Notes, JTBD
- **Droplet-enriched fields:** Agent IDS notes, content pipeline connections, thesis thread links, signal history, computed conviction scores, enrichment metadata
- **Change detection:** Diff Notion fields on each sync. Changes generate events: "Deal Status changed", "New founder added", etc.
- **Sync period:** TBD — likely every few hours or daily. Companies data changes slowly.

### Network DB
- **SoT:** Droplet (enriched) + Notion (human fields)
- **Notion-owned fields:** Person Name, Archetype, Company, Role, LinkedIn, Email, Phone, City, IDS Notes, Relationship Status, Last Interaction, Source, Collective Status
- **Droplet-enriched fields:** Agent-generated interaction summaries, meeting context, content connections, signal history
- **Change detection:** Same as Companies — diff and generate events.
- **Sync period:** TBD — similar to Companies.

### Portfolio DB
- **SoT:** Droplet (enriched) + Notion (human fields)
- **Notion-owned fields:** Financial data, follow-on tracking, EF/EO scores, rollup to Finance DB. Each entry has a **hidden `Company Name` relation** linking to the corresponding Companies DB entry in Notion.
- **Droplet-enriched fields:** Agent-generated portfolio health signals, content pipeline cross-references, thesis conviction tracking
- **Key relation:** Portfolio → Companies DB via `Company Name` property. This links portfolio financial data to the company IDS trail. The droplet schema should mirror this relation.
- **Sync period:** TBD — similar to Companies.

## Implementation Layers

```
Layer 0: Public MCP endpoint (NEW — enables unified write path)
  - Cloudflare Tunnel: droplet → public URL with TLS
  - FastMCP Streamable HTTP transport (MCP spec 2025-06-18)
  - Claude.ai connects as remote MCP connector
  - Claude Code connects via MCP config (Tailscale or tunnel)
  - All surfaces write through ai-cos-mcp tools, not Notion directly

Layer 1: Postgres schema
  - Mirror key Notion tables (Notion-owned fields)
  - Add enrichment columns (droplet-only fields)
  - Add sync metadata (last_synced, sync_status, notion_page_id, version)

Layer 2: Sync engine
  - Pull: Notion → Postgres (for Status field on Thesis Tracker, Companies, Network, Portfolio)
  - Push: Postgres → Notion (for Content Digest, proposed Actions, Thesis Tracker writes)
  - Change detection: diff Notion fields between sync cycles → generate events

Layer 3: Write-ahead log
  - Queue failed Notion writes in `sync_queue` table
  - Retry on next sync cycle
  - Track attempts, last error, created_at

Layer 4: SyncAgent runner
  - Orchestrates sync on schedule (different periods per table)
  - Handles conflicts based on field ownership rules
  - Generates change events as actions/signals
  - Logs all sync operations
```

## Build Phases

### Phase 1: Public MCP Endpoint + Thesis Write Tools (Sprint 2)

Centralizes thesis writes through the droplet. All surfaces use ai-cos-mcp instead of Notion MCP directly.

| Step | Work | Effort |
|------|------|--------|
| 1a. Install `cloudflared` on droplet | `apt install cloudflared`, create tunnel, point at localhost:PORT | 10 min |
| 1b. TLS | Automatic via Cloudflare Tunnel — valid certs, no config | Free |
| 1c. Streamable HTTP transport | Change `server.py` to run with `transport="streamable-http"`. FastMCP 3.1.0 supports this. | 15 min |
| 1d. Spec compliance | Verify HEAD endpoint + `MCP-Protocol-Version` header. FastMCP 3.x likely handles this. | Verify |
| 1e. Add thesis write tools | Wrap existing `notion_client.py` functions as MCP tools: `cos_create_thesis_thread`, `cos_update_thesis`, `cos_get_thesis_threads` | 30 min |
| 1f. Add as Claude.ai connector | Settings → Integrations, paste tunnel URL | 2 min |
| 1g. Claude Code MCP config | Add ai-cos-mcp to `.mcp.json` (Tailscale endpoint) | 5 min |
| 1h. Update prompts | Claude.ai memory + CLAUDE.md: "use cos_* tools for thesis, not Notion MCP directly" | 10 min |

**Deliverable:** All thesis writes flow through droplet. Single write authority established.

### Phase 2: Thesis Postgres Backing (Sprint 3)

Add `thesis_threads` table as primary store. Write-ahead pattern for Notion resilience.

| Step | Work | Effort |
|------|------|--------|
| 2a. Postgres schema | `thesis_threads` table mirroring Notion fields + enrichment columns | 30 min |
| 2b. Write-ahead | MCP tools write to Postgres first, then push to Notion. Failed pushes queued for retry. | 1 hr |
| 2c. Status sync | Pull Status field from Notion periodically (only human-owned field) | 30 min |

**Deliverable:** Thesis data survives Notion outages. Droplet is true SoT.

### Phase 3: Companies/Network/Portfolio Initial Pull (Sprint 3-4)

Postgres schema for remaining DBs, first Notion → local sync.

### Phase 4: Bidirectional Actions Queue (After Phase 3)

Multi-surface triaging without conflicts. Field-level last-writer-wins.

### Phase 5: Change Detection → Action Generation (After Phase 4)

Notion edits become signals. Deal status changes, new founders added → auto-generated actions.

### Phase 6: Full SyncAgent Orchestration (Final)

Ties it all together. Scheduled runs per table, monitoring, alerting.
