# MCP Tools Inventory
*Last Updated: 2026-03-07*

All 17 tools exposed by the `ai-cos-mcp` server. Server runs on the DO droplet as a systemd service (FastMCP Python, streamable HTTP transport).

---

## Access Surfaces

| Surface | Connection | URL |
|---------|-----------|-----|
| **Claude.ai** | Remote MCP connector | `https://mcp.3niac.com/mcp` (Cloudflare Tunnel) |
| **Claude Code** | `.mcp.json` (Tailscale) | `http://aicos-droplet:8000/mcp` |
| **Content Pipeline** | Direct Python import (`lib/` modules) | No MCP hop — imports `lib/` directly |
| **SyncAgent** | Direct Python import | No MCP hop — imports `lib/` + `runners/` directly |

---

## Tool Routing Rules

| Database | Read Tool | Write Tool |
|----------|-----------|------------|
| **Thesis Tracker** | `cos_get_thesis_threads` | `cos_create_thesis_thread`, `cos_update_thesis` |
| **Content Digest** | `cos_get_recent_digests` | Pipeline only (no manual writes) |
| **Actions Queue** | `cos_get_actions` | Notion MCP for status changes (accept/dismiss) |

Use Notion MCP directly for: Companies DB, Network DB, Portfolio DB, Build Roadmap, Tasks Tracker.

**Conviction guardrail:** Never set the `conviction` parameter on thesis tools from Claude Code. Provide evidence and ask Aakash if conviction should change.

---

## Tool Reference

### 1. health_check

**Purpose:** Server and database connectivity check.
**Params:** None
**Returns:** Server status, database status, action_outcomes count, thesis_threads count, sync_queue pending count.
**Use when:** Verifying the system is up, debugging connectivity.

---

### 2. cos_load_context

**Purpose:** Load AI CoS domain context (CONTEXT.md) for any Claude session.
**Params:** None
**Returns:** First 8000 chars of CONTEXT.md, file path, total length.
**Use when:** Starting a Claude.ai session that needs domain context.

---

### 3. cos_score_action

**Purpose:** Score an action using the Action Scoring Model (5 of 7 factors implemented; `key_question_relevance` and `stakeholder_priority` planned).
**Params:**
- `bucket_impact` (float, 0-10) — Which priority bucket does this serve?
- `conviction_change` (float, 0-10) — Could this move investment conviction?
- `time_sensitivity` (float, 0-10) — Reason to act NOW?
- `action_novelty` (float, 0-10) — New information vs redundant?
- `effort_vs_impact` (float, 0-10) — Time cost vs expected value?

**Returns:** Score (0-10), classification (surface/low_confidence/context_only).
**Use when:** Evaluating whether an action is worth surfacing to Aakash.

---

### 4. cos_get_preferences

**Purpose:** Load recent action outcome preferences for calibration.
**Params:**
- `limit` (int, default 20) — Max outcomes to return

**Returns:** Recent outcomes from `action_outcomes` table, summary statistics.
**Use when:** Before reasoning about action proposals — calibrate to Aakash's actual behavior.

---

### 5. cos_create_thesis_thread

**Purpose:** Create a new thesis thread (write-ahead: Postgres first, then Notion).
**Params:**
- `thread_name` (str, required) — Short, distinctive thesis name
- `core_thesis` (str, required) — One-liner: the durable value insight
- `key_questions` (list[str], optional) — 2-3 critical questions
- `connected_buckets` (list[str], optional) — Priority buckets served
- `discovery_source` (str, default "Claude") — Origin: Claude, Content Pipeline, Meeting, Research
- `conviction` (str, default "New") — Initial conviction level

**Returns:** IDs (pg_id, notion page id), thread_name, conviction, notion_synced status.
**Write-ahead:** If Notion push fails, data is safe in Postgres and queued for retry.

---

### 6. cos_update_thesis

**Purpose:** Update an existing thesis thread with new evidence (write-ahead).
**Params:**
- `thesis_name` (str, required) — Name of existing thread (partial match supported)
- `new_evidence` (str, required) — Evidence text to append
- `evidence_direction` (str, default "for") — "for", "against", or "mixed"
- `source` (str, default "Claude") — Evidence origin
- `conviction` (str, optional) — New conviction level if it should change
- `new_key_questions` (list[str], optional) — New questions raised
- `answered_questions` (list[str], optional) — Open questions this evidence answers
- `investment_implications` (str, optional) — What Aakash should DO about this
- `key_companies` (str, optional) — Companies relevant to this thesis

**Returns:** IDs, thesis_name, updated status, notion_synced, pg_backed.
**Fallback:** If thread exists in Notion but not Postgres (transition period), falls back to Notion-only update.

---

### 7. cos_get_thesis_threads

**Purpose:** Get all active thesis threads from the Thesis Tracker.
**Params:**
- `include_key_questions` (bool, default False) — Fetch [OPEN]/[ANSWERED] from page blocks (slower, one API call per thread)

**Returns:** Thread list with names, conviction, core thesis, evidence, key questions. Thread count.
**Use when:** Understanding current thesis state before creating or updating threads.

---

### 8. cos_get_recent_digests

**Purpose:** Get recent content digests from Content Digest DB.
**Params:**
- `limit` (int, default 10) — Max digests to return

**Returns:** Digests with titles, channels, relevance scores, net newness, summaries, digest URLs.
**Use when:** Reviewing recent content analysis, checking what the pipeline has processed.

---

### 9. cos_get_actions

**Purpose:** Get actions from the Actions Queue.
**Params:**
- `status` (str, optional) — Filter: Proposed, Accepted, In Progress, Done, Dismissed. None = all.
- `limit` (int, default 20) — Max actions to return

**Returns:** Actions with priorities, types, assignments, thesis connections, reasoning.
**Use when:** Reviewing pending actions, checking action queue state.

---

### 10. cos_sync_thesis_status

**Purpose:** Sync thesis Status field from Notion to Postgres.
**Params:** None
**Returns:** Count of synced threads, list of status changes detected.
**Use when:** Before scoring (ensures Postgres has latest human Status decisions). Called automatically by SyncAgent.

---

### 11. cos_seed_thesis_db

**Purpose:** One-time seed — pull all thesis threads from Notion into Postgres.
**Params:** None
**Returns:** Count of inserted threads.
**Use when:** Initial setup or re-seeding after database reset. Safe to run multiple times (skips existing).

---

### 12. cos_retry_sync_queue

**Purpose:** Process pending items in the sync retry queue.
**Params:** None
**Returns:** Count processed, per-item results (done/failed with error details).
**Use when:** Manually draining failed Notion pushes. Called automatically by SyncAgent.

---

### 13. cos_sync_actions

**Purpose:** Bidirectional sync for Actions Queue.
**Params:** None
**Returns:** Sync results: actions pulled from Notion, status changes detected.
**Use when:** Syncing action state between Notion and Postgres. Called automatically by SyncAgent.

---

### 14. cos_full_sync

**Purpose:** Run all sync operations in one call.
**Params:** None
**Returns:** Combined results for: thesis status sync, actions bidirectional sync, retry queue drain, change processing.
**Use when:** Manual full sync trigger. SyncAgent calls this on its 10-min cron.

---

### 15. cos_get_changes

**Purpose:** Get recent change events detected during sync.
**Params:**
- `limit` (int, default 20) — Max changes to return

**Returns:** Unprocessed changes with table, field, old/new values, detection timestamps.
**Use when:** Auditing sync behavior, debugging change detection.

---

### 16. cos_sync_status

**Purpose:** Get unified sync status dashboard.
**Params:** None
**Returns:** Thesis sync state (total threads, last sync), actions sync state (total, last sync, unsynced count), sync queue depth (pending/failed), recent change events.
**Use when:** Monitoring sync health, checking if sync is running properly.

---

### 17. cos_process_changes

**Purpose:** Process unprocessed change events and generate actions from them.
**Params:** None
**Returns:** Generated actions with triggers (e.g., "conviction moved to High").
**Action generation rules:**
- Thesis conviction → High: propose portfolio review for investment opportunities
- Thesis status Active → Parked/Archived: propose deprioritizing connected actions
- Thesis status Parked → Active: propose resurfacing actions for reactivated thesis
- Action outcome → Gold: propose pattern analysis of high-value actions
**Use when:** Closing the feedback loop after sync. Called automatically by SyncAgent.

---

## Tool Categories

| Category | Tools | Purpose |
|----------|-------|---------|
| **Health** | health_check | System monitoring |
| **Context** | cos_load_context | Domain knowledge injection |
| **Scoring** | cos_score_action, cos_get_preferences | Action evaluation + calibration |
| **Thesis CRUD** | cos_create_thesis_thread, cos_update_thesis, cos_get_thesis_threads | AI-managed conviction engine |
| **Data Access** | cos_get_recent_digests, cos_get_actions | Read content + action state |
| **Sync Ops** | cos_sync_thesis_status, cos_seed_thesis_db, cos_retry_sync_queue, cos_sync_actions, cos_full_sync | Notion-Postgres synchronization |
| **Observability** | cos_get_changes, cos_sync_status, cos_process_changes | Sync health + change detection |

---

## Detailed Reference

- **Full tool implementations:** `mcp-servers/ai-cos-mcp/server.py`
- **Notion client library:** `mcp-servers/ai-cos-mcp/lib/notion_client.py`
- **Thesis DB operations:** `mcp-servers/ai-cos-mcp/lib/thesis_db.py`
- **Actions DB operations:** `mcp-servers/ai-cos-mcp/lib/actions_db.py`
- **Change detection engine:** `mcp-servers/ai-cos-mcp/lib/change_detection.py`
- **SyncAgent runner:** `mcp-servers/ai-cos-mcp/runners/sync_agent.py`
