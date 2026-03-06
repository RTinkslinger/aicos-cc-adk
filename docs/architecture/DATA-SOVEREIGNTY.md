# Data Sovereignty — Source of Truth Map

> Defines where authoritative data lives for each AI CoS database, how sync flows between Notion and the droplet, and the architectural patterns for each.

## Source of Truth Map

| Database | Source of Truth | Droplet Role | Notion Role | Sync Pattern |
|----------|----------------|-------------|-------------|-------------|
| **Content Digest** | **Droplet** | Creates analysis, stores full record | View layer (Action Status editable) | Push: droplet → Notion |
| **Actions Queue** | **Both** | Creates proposals; some triages arrive here first | Some triages happen here first | Bidirectional, conflict-aware |
| **Thesis Tracker** | **Notion** (AI-managed) | Creates threads, updates conviction/evidence/key questions via API | AI writes all fields; Aakash edits Status only | Pull: Notion → droplet cache; Push: droplet → Notion (conviction, evidence, new threads) |
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
- **SoT:** Notion — but AI-managed. All fields are written by AI except Status (human-only).
- **Droplet reads:** Thread Name, Status, Conviction, Core Thesis, Key Question (property + page blocks for [OPEN]/[ANSWERED] questions), Key Companies, Connected Buckets, Evidence For, Evidence Against, Investment Implications
- **Droplet writes (via Notion API):**
  - Creates new thesis threads autonomously (Conviction = "New", Discovery Source = "Content Pipeline")
  - Appends evidence blocks to page body with `[date] [source] (direction) evidence` format
  - Updates Conviction level (New → Evolving → Evolving Fast → Low → Medium → High)
  - Appends to Evidence For / Evidence Against property text (IDS notation: + for, ? against)
  - Adds key questions as `[OPEN]` page blocks, marks `[ANSWERED]` when evidence resolves them
  - Updates Investment Implications, Key Companies
- **Human writes:** Status only (Active / Exploring / Parked / Archived) — this weights action scoring
- **Multiple write surfaces:** Claude.ai, Claude Code, Content Pipeline — all write to Notion directly
- **Conviction spectrum:** New / Evolving / Evolving Fast (maturity axis) → Low / Medium / High (strength axis for well-formed thesis)
- **Sync:** Pull to local cache on pipeline start (includes page blocks for key questions). Cache refresh: every pipeline run (5 min). If Notion unreachable, use last cached state (or CONTEXT.md fallback).

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
Layer 1: Postgres schema
  - Mirror key Notion tables (Notion-owned fields)
  - Add enrichment columns (droplet-only fields)
  - Add sync metadata (last_synced, sync_status, notion_page_id, version)

Layer 2: Sync engine
  - Pull: Notion → Postgres (for Thesis Tracker, Companies, Network, Portfolio)
  - Push: Postgres → Notion (for Content Digest, proposed Actions)
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

1. **Write-ahead + Thesis cache** — Prevent data loss on Notion writes. Cache thesis threads locally. (Immediate)
2. **Companies/Network/Portfolio initial pull** — Postgres schema, first Notion → local sync. Enables richer portfolio connections in digests. (Next)
3. **Bidirectional Actions Queue** — Multi-surface triaging without conflicts. (After #2)
4. **Change detection → action generation** — Notion edits become signals. (After #3)
5. **Full SyncAgent orchestration** — Ties it all together. Scheduled runs, monitoring, alerting. (Final)
