# Database Access Inventory — 2026-03-18

Complete catalog of all database access points in the AI CoS codebase.

---

## Summary

| Database | Type | Access Method | Env Var | Live Status |
|----------|------|----------------|---------|-------------|
| **Postgres** | Relational | asyncpg (Python) + psql (Bash) | `DATABASE_URL` | Production (Live) |
| **SQLite** | Local | sqlite3 module (Python) | Hardcoded path | Development (Strategy Cache) |

---

## Part 1: Postgres Access Points

### A. State MCP (asyncpg + Pool)

#### 1. Connection Pool Initialization

**File:** `/Users/Aakash/Claude Projects/Aakash AI CoS CC ADK/mcp-servers/agents/state/db/connection.py`

| File | Lines | Access Method | Env Var | SQL Operations | Migration Risk |
|------|-------|---------------|---------|----------------|----------------|
| `state/db/connection.py` | 1-34 | `asyncpg.create_pool()` | `DATABASE_URL` | Pool creation only (SELECT 1 test) | **Medium** — requires env var, hardcoded min_size=2 max_size=5 |

**Details:**
- Creates global asyncpg connection pool on first call to `get_pool()`
- Pool uses `DATABASE_URL` from environment
- Raises RuntimeError if `DATABASE_URL` not set
- Pool parameters: `min_size=2, max_size=5` (hardcoded — may need tuning for production load)
- Safe: uses parameterized queries, no raw SQL in this module

**Migration Risks:**
- Pool must be closed on shutdown via `close_pool()`
- Connection string must include `?sslmode=require` or similar if SSL required
- Max 5 connections — monitor connection saturation in production

---

#### 2. Thesis Threads — Read/Create/Update

**File:** `/Users/Aakash/Claude Projects/Aakash AI CoS CC ADK/mcp-servers/agents/state/db/thesis.py`

| File | Lines | Access Method | Env Var | SQL Operations | Migration Risk |
|------|-------|---------------|---------|----------------|----------------|
| `state/db/thesis.py` | 8-20 | `pool.fetch()` | Via `get_pool()` | SELECT (all thesis threads) | **Low** — read-only |
| `state/db/thesis.py` | 23-40 | `pool.fetchrow()` | Via `get_pool()` | INSERT (new thesis thread) | **Medium** — creates with `notion_synced=FALSE` |
| `state/db/thesis.py` | 43-122 | `pool.fetchrow()` | Via `get_pool()` | UPDATE (3 variants: for/against/mixed) | **Medium** — appends evidence, sets `notion_synced=FALSE` |

**Operations:**
- `get_threads()` — SELECT all with ORDER BY updated_at DESC
- `create_thread(name, core_thesis)` — INSERT with notion_synced=FALSE (for Sync Agent pickup)
- `update_thread(name, evidence, direction)` — UPDATE evidence_for/evidence_against, appends with newline separator

**Table:** `thesis_threads`
- Columns accessed: id, thread_name, core_thesis, conviction, status, evidence_for, evidence_against, key_question_summary, notion_page_id, notion_synced, created_at, updated_at
- Filter: `WHERE thread_name = $1` (parameterized)

**Migration Risks:**
- String concatenation with `E'\n'` for evidence — will work with SSL
- Uses parameterized queries ($1, $2, etc.) — injection-safe
- Creates 3 separate UPDATE statements for each direction — could be consolidated
- No DDL (CREATE TABLE) — safe

---

#### 3. CAI Inbox — Post/Read/Mark Processed

**File:** `/Users/Aakash/Claude Projects/Aakash AI CoS CC ADK/mcp-servers/agents/state/db/inbox.py`

| File | Lines | Access Method | Env Var | SQL Operations | Migration Risk |
|------|-------|---------------|---------|----------------|----------------|
| `state/db/inbox.py` | 10-34 | `pool.fetchrow()` | Via `get_pool()` | INSERT into cai_inbox | **Low** — structured inserts |
| `state/db/inbox.py` | 37-48 | `pool.fetch()` | Via `get_pool()` | SELECT WHERE processed=FALSE | **Low** — read-only |
| `state/db/inbox.py` | 51-68 | `pool.fetchrow()` | Via `get_pool()` | UPDATE processed=TRUE | **Low** — status updates only |

**Operations:**
- `post_message(type, content, metadata)` — INSERT with JSONB metadata
- `get_pending()` — SELECT unprocessed, oldest first
- `mark_processed(message_id)` — UPDATE status + timestamp

**Table:** `cai_inbox`
- Columns: id, type, content, metadata (JSONB), processed, processed_at, created_at
- Filter: `WHERE processed = FALSE`

**Migration Risks:**
- JSONB column for metadata — ensure Postgres supports JSONB
- Uses parameterized queries — injection-safe
- No DDL

---

#### 4. Notifications — Post and Mark Read

**File:** `/Users/Aakash/Claude Projects/Aakash AI CoS CC ADK/mcp-servers/agents/state/db/notifications.py`

| File | Lines | Access Method | Env Var | SQL Operations | Migration Risk |
|------|-------|---------------|---------|----------------|----------------|
| `state/db/notifications.py` | 10-22 | `pool.fetch()` | Via `get_pool()` | SELECT LIMIT 50 | **Low** — read-only, with limit |
| `state/db/notifications.py` | 25-52 | `pool.fetchrow()` | Via `get_pool()` | INSERT into notifications | **Low** — structured inserts |
| `state/db/notifications.py` | 55-79 | `pool.execute()` | Via `get_pool()` | UPDATE WHERE id = ANY($1) | **Medium** — array-based bulk update |

**Operations:**
- `get_unread()` — SELECT with LIMIT 50, ORDER BY created_at DESC
- `post_notification(source, type, content, metadata)` — INSERT with JSONB
- `mark_read(notification_ids)` — UPDATE with array parameter `$1::int[]`

**Table:** `notifications`
- Columns: id, source, type, content, metadata (JSONB), read, created_at
- Filter: `WHERE read = FALSE`

**Migration Risks:**
- Array parameter `id = ANY($1::int[])` — ensure Postgres version supports arrays (all versions do)
- Uses `pool.execute()` — returns string result "UPDATE N", needs parsing
- No DDL

---

#### 5. State MCP Server Integration

**File:** `/Users/Aakash/Claude Projects/Aakash AI CoS CC ADK/mcp-servers/agents/state/server.py`

| File | Lines | Access Method | Env Var | SQL Operations | Migration Risk |
|------|-------|---------------|---------|----------------|----------------|
| `state/server.py` | 25-36 | `get_pool()` / `close_pool()` | Via connection.py | Pool lifecycle | **Low** — called by FastMCP lifespan |
| `state/server.py` | 202-204 | `pool.fetchval()` | Via `get_pool()` | SELECT 1 (health check) | **Low** — test query |
| `state/server.py` | 227 | `pool.fetchval()` | Via `get_pool()` | SELECT 1 (HTTP health endpoint) | **Low** — test query |

**Operations:**
- Tool `health_check()` — executes SELECT 1, returns db_connected status
- HTTP GET `/health` — same SELECT 1 test for ops monitoring

**Migration Risks:**
- Health checks use `pool.fetchval("SELECT 1")` — safe universally
- Lifespan context manager ensures proper pool cleanup
- No DDL

---

### B. Orchestrator Agent (Bash + psql)

#### 6. Inbox Query — Orchestrator Heartbeat

**File:** `/Users/Aakash/Claude Projects/Aakash AI CoS CC ADK/mcp-servers/agents/orchestrator/CLAUDE.md` (instructions)

**File:** `/Users/Aakash/Claude Projects/Aakash AI CoS CC ADK/mcp-servers/agents/orchestrator/HEARTBEAT.md`

| File | Line | Access Method | Env Var | SQL Operations | Migration Risk |
|------|------|----------------|---------|----------------|----------------|
| `orchestrator/HEARTBEAT.md` | 20 | `psql $DATABASE_URL -c` | `DATABASE_URL` | SELECT id, type, content, metadata FROM cai_inbox | **Medium** — raw SQL via Bash |
| `orchestrator/HEARTBEAT.md` | 29 | `psql $DATABASE_URL -c` | `DATABASE_URL` | UPDATE cai_inbox SET processed=TRUE | **Medium** — raw SQL via Bash |

**Operations:**
- Step 2: Read unprocessed inbox messages
  ```bash
  psql $DATABASE_URL -t -A -c "SELECT id, type, content, metadata FROM cai_inbox WHERE processed = FALSE ORDER BY created_at"
  ```
- Step 2: Mark relayed messages as processed
  ```bash
  psql $DATABASE_URL -c "UPDATE cai_inbox SET processed = TRUE, processed_at = NOW() WHERE id IN (42, 43)"
  ```

**Actual Implementation:** Currently documented as instructions in CLAUDE.md/HEARTBEAT.md, executed by Orchestrator Agent during heartbeat processing.

**Migration Risks:**
- Uses raw SQL with `$DATABASE_URL` environment variable
- No parameterization in Bash — IDs come from trusted parsed input only (acceptable, but note)
- Does NOT use `psql` flags like `-h localhost` — uses full connection string from env var
- Must have `psql` binary available in container
- Connection string format: must be valid for both v13 and v14+

---

### C. Content Agent (Bash + psql)

#### 7. Content Digests — Queue/Status/Publish

**File:** `/Users/Aakash/Claude Projects/Aakash AI CoS CC ADK/mcp-servers/agents/content/CLAUDE.md` (instructions)

| Operation | Line | SQL Pattern | Env Var | Migration Risk |
|-----------|------|-------------|---------|----------------|
| INSERT queued | 72 | `INSERT INTO content_digests (...) VALUES (...) ON CONFLICT (url) DO NOTHING` | `DATABASE_URL` | **Medium** — ON CONFLICT dedup |
| SELECT queued | 75 | `SELECT id, slug, url, title FROM content_digests WHERE status = 'queued'` | `DATABASE_URL` | **Low** — read-only |
| UPDATE to processing | 78 | `UPDATE content_digests SET status = 'processing' WHERE id = {id}` | `DATABASE_URL` | **Medium** — per-item status |
| UPDATE to published | 79 | `UPDATE content_digests SET status = 'published', digest_data='{...}'::jsonb, ...` | `DATABASE_URL` | **High** — full row update with JSONB |
| UPDATE to failed | 139 | `UPDATE content_digests SET status = 'failed' WHERE id = {id}` | `DATABASE_URL` | **Low** — status only |

**Table:** `content_digests`
- Columns: id, slug, url (UNIQUE), title, channel, status, digest_data (JSONB), digest_url, relevance_score, net_newness, created_at, updated_at
- Unique constraint: url

**Schema Example:**
```sql
-- Inferred from Content Agent instructions
CREATE TABLE IF NOT EXISTS content_digests (
  id SERIAL PRIMARY KEY,
  slug VARCHAR(60),
  url TEXT UNIQUE NOT NULL,
  title TEXT,
  channel TEXT,
  content_type TEXT,
  duration TEXT,
  status VARCHAR(20),  -- queued|processing|published|failed
  digest_data JSONB,
  digest_url TEXT,
  relevance_score VARCHAR(20),  -- High|Medium|Low (not numeric in usage examples)
  net_newness VARCHAR(20),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

**Migration Risks:**
- ON CONFLICT clause — requires Postgres 9.5+
- JSONB column with embedded digest schema — ensure schema matches DigestData JSON spec (lines 520-612)
- String representation of relevance_score ('High'/'Medium'/'Low') — consider migrating to ENUM
- All operations via Bash + psql — must have psql binary in container

---

#### 8. Thesis Threads — Update Evidence

**File:** `/Users/Aakash/Claude Projects/Aakash AI CoS CC ADK/mcp-servers/agents/content/CLAUDE.md`

| Operation | Line | SQL Pattern | Env Var | Migration Risk |
|-----------|------|-------------|---------|----------------|
| SELECT active threads | 82 | `SELECT name, conviction, status, ... FROM thesis_threads WHERE status IN ('Active', 'Exploring')` | `DATABASE_URL` | **Low** — read-only filtered |
| APPEND evidence | 85 | `UPDATE thesis_threads SET evidence_for = evidence_for \|\| E'\n[date] ++ Signal: ...' WHERE name = '...'` | `DATABASE_URL` | **Medium** — string concatenation |

**Operations:**
- Phase 2.c (Analysis): Read active/exploring thesis threads
- Phase 2.e (After analysis): Append evidence with timestamp prefix + IDS notation

**Example:**
```bash
psql $DATABASE_URL -c "UPDATE thesis_threads SET evidence_for = evidence_for || E'\n[2026-03-16 ContentAgent] ++ Strong signal: Composio MCP marketplace gaining traction' WHERE name = 'Agentic AI Infrastructure'"
```

**Migration Risks:**
- String concatenation with `E'\n'` — works in all Postgres versions
- Relies on column allowing NULL (will initialize with evidence text if NULL)
- No parameterization in Bash template — thesis name and evidence from trusted agent logic (acceptable)
- No DDL

---

#### 9. Actions Queue — Write Scored Actions

**File:** `/Users/Aakash/Claude Projects/Aakash AI CoS CC ADK/mcp-servers/agents/content/CLAUDE.md`

| Operation | Line | SQL Pattern | Env Var | Migration Risk |
|-----------|------|-------------|---------|----------------|
| INSERT action | 326 | `INSERT INTO actions_queue (action_text, action_type, priority, assigned_to, relevance_score, reasoning, thesis_connection, source, created_at) VALUES (...)` | `DATABASE_URL` | **Medium** — structured insert |

**Inferred Schema:**
```sql
CREATE TABLE IF NOT EXISTS actions_queue (
  id SERIAL PRIMARY KEY,
  action_text TEXT,
  action_type VARCHAR(50),  -- Research|Meeting/Outreach|Thesis Update|...
  priority VARCHAR(10),      -- P0|P1|P2|P3
  assigned_to VARCHAR(50),   -- Aakash|Agent
  relevance_score NUMERIC,
  reasoning TEXT,
  thesis_connection TEXT,
  status VARCHAR(20),        -- not explicitly set by Content Agent
  source TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);
```

**Migration Risks:**
- Inferred schema based on scoring model (section 9) — actual schema may differ
- No examples of INSERT syntax in CLAUDE.md — assumed via psql
- Must implement before Content Agent can write actions (currently documented as "Score >= 7 surface as action")

---

#### 10. Notifications — Write Alerts

**File:** `/Users/Aakash/Claude Projects/Aakash AI CoS CC ADK/mcp-servers/agents/content/CLAUDE.md`

| Operation | Line | SQL Pattern | Env Var | Migration Risk |
|-----------|------|-------------|---------|----------------|
| INSERT notification | 494 | `INSERT INTO notifications (type, content, metadata, created_at) VALUES (...)` | `DATABASE_URL` | **Low** — same as State MCP |

**Example:**
```bash
psql $DATABASE_URL -c "INSERT INTO notifications (type, content, metadata, created_at) VALUES ('content_alert', 'High-score action: Research Composio MPC marketplace', '{\"score\": 8.2, \"thesis\": \"Agentic AI Infrastructure\"}', NOW())"
```

**Notification Types:**
- content_alert (score >= 7)
- thesis_update (conviction change)
- thesis_new (new thread created)
- contra_signal (strong counter-evidence)
- research_complete (subagent result)
- inbox_error (processing failure)

**Migration Risks:**
- JSONB metadata — ensure Postgres supports JSONB
- Same table/tool as State MCP (state/db/notifications.py) — consistent schema

---

#### 11. CAI Inbox — Mark Processed

**File:** `/Users/Aakash/Claude Projects/Aakash AI CoS CC ADK/mcp-servers/agents/content/CLAUDE.md`

| Operation | Line | SQL Pattern | Env Var | Migration Risk |
|-----------|------|-------------|---------|----------------|
| UPDATE processed | 88 | `UPDATE cai_inbox SET processed = TRUE, processed_at = NOW() WHERE id = <id>` | `DATABASE_URL` | **Low** — status update |

**Used in:**
- Inbox Message Relay (section 4) — mark each processed message
- Error handling (section 18) — mark failed messages processed to avoid infinite retry

**Migration Risks:**
- Same table as State MCP (state/db/inbox.py) — consistent
- No DDL

---

### D. Deploy & Testing

#### 12. Testing — Mock DATABASE_URL

**File:** `/Users/Aakash/Claude Projects/Aakash AI CoS CC ADK/mcp-servers/agents/tests/test_integration.py`

| File | Line | Context | Env Var | Migration Risk |
|------|------|---------|---------|----------------|
| `tests/test_integration.py` | 365-366 | Mock connection setup | `DATABASE_URL` (patched) | **Low** — test only |

**Context:**
```python
with patch.dict("os.environ", {"DATABASE_URL": "postgresql://test/test"}):
    # Mock test of connection
```

**Migration Risks:**
- Test uses fake credentials (postgresql://test/test) — not production-grade
- Mocks the environment, doesn't require real Postgres
- Skip if services unavailable (documented in test header)

---

#### 13. Deployment — No Direct DB Access

**File:** `/Users/Aakash/Claude Projects/Aakash AI CoS CC ADK/mcp-servers/agents/deploy.sh`

**File:** `/Users/Aakash/Claude Projects/Aakash AI CoS CC ADK/mcp-servers/agents/deploy/bootstrap.sh`

| File | DB Access? | Env Var | Migration Risk |
|------|-----------|---------|----------------|
| `deploy.sh` | No | — | N/A |
| `deploy/bootstrap.sh` | No | — | N/A |

**Note:** Deploy scripts do NOT access Postgres. They:
- Sync code via rsync
- Install dependencies (uv sync)
- Create runtime directories
- Seed trace files
- Install systemd units
- Restart services

**Database initialization** happens at runtime when State MCP and agents start.

---

## Part 2: SQLite Access Points

### E. Web Tools — Strategy Cache

#### 14. Strategy Cache — UCB Bandit Persistence

**File:** `/Users/Aakash/Claude Projects/Aakash AI CoS CC ADK/mcp-servers/agents/web/lib/strategy.py`

| File | Lines | Access Method | Path | SQL Operations | Migration Risk |
|------|-------|---------------|------|----------------|----------------|
| `web/lib/strategy.py` | 1-195 | `sqlite3.connect()` with WAL | `/opt/web-agent/strategy.db` | CREATE/SELECT/INSERT/UPDATE | **Low** — isolated local DB |

**Details:**
- Module-level singleton connection (reused, not per-call)
- Uses WAL mode for safe concurrent reads/writes
- Threading.Lock() wraps all writes to prevent contention

**Schema:**
```sql
CREATE TABLE IF NOT EXISTS strategies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    origin TEXT NOT NULL,
    strategy_name TEXT NOT NULL,
    config TEXT NOT NULL DEFAULT '{}',
    successes INTEGER DEFAULT 0,
    failures INTEGER DEFAULT 0,
    total_attempts INTEGER DEFAULT 0,
    avg_latency_ms REAL DEFAULT 0,
    last_used TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(origin, strategy_name)
);
```

**Operations:**
- `_init_schema()` — CREATE TABLE IF NOT EXISTS (idempotent)
- `get_strategy()` — SELECT with UCB score calculation (in-memory)
- `record_outcome()` — INSERT OR UPDATE ON CONFLICT (upsert)
- `seed_strategies()` — INSERT OR IGNORE
- `get_all_strategies()` — SELECT all for diagnostics

**Migration Risks:**
- **Hardcoded path:** `/opt/web-agent/strategy.db` — change requires code edit
- SQLite only — not Postgres, not migrating to Postgres (intentional, local optimization)
- WAL mode requires filesystem support (works on standard Linux/macOS)
- Threading.Lock() serializes all writes — may become bottleneck at high concurrency (unlikely in practice)
- No network — safe if `/opt/web-agent/` directory is writable by the agent process

**Connection String Issues:**
- No connection string — hardcoded file path
- No SSL/TLS — N/A for local SQLite
- Not part of Postgres migration plan

---

## Part 3: Summary & Migration Checklist

### Environment Variables

| Env Var | Used By | Required | Default | Migration Notes |
|---------|---------|----------|---------|-----------------|
| `DATABASE_URL` | State MCP (asyncpg) | **YES** | None — raises RuntimeError if missing | Must be set in .env or systemd unit. Format: `postgresql://user:pass@host:port/dbname?sslmode=require` |

### SSL/TLS Compatibility

All Postgres access points (asyncpg + psql) use `DATABASE_URL` connection string. To enforce SSL:

1. **For asyncpg:** Add `?sslmode=require` to connection string (State MCP handles automatically)
2. **For psql:** Must be in connection string (Orchestrator/Content Agent — automatic via env var)

**No hardcoded hosts/ports** — everything flows through `DATABASE_URL`.

### DDL (Schema Changes)

**Only SQLite creates tables:**
- `web/lib/strategy.py` line 51 — `CREATE TABLE IF NOT EXISTS strategies`

**Postgres tables are assumed to exist:**
- All tables (thesis_threads, cai_inbox, notifications, content_digests, actions_queue) must be created before agents start
- State MCP will raise RuntimeError on first call to `get_pool()` if DATABASE_URL not set
- Content Agent and Orchestrator assume all tables exist and will fail with psql errors if not

**Migration action needed:** Run schema migrations (DDL) before deploying agents.

### Connection Pool Management

**State MCP (asyncpg):**
- Pool created lazily on first call (line 24: `await asyncpg.create_pool()`)
- Min size: 2, Max size: 5 (hardcoded)
- Global singleton `_pool` variable
- Closed on shutdown via `close_pool()` in FastMCP lifespan context

**Recommendation:** Pool size (2-5) adequate for ~3 concurrent agents. Monitor in production.

### Per-File Risk Matrix

| File | Risk Level | Reason |
|------|-----------|--------|
| `state/db/connection.py` | **Medium** | Pool lifecycle, env var dependency, hardcoded pool size |
| `state/db/thesis.py` | **Low** | Parameterized queries, safe operations, no DDL |
| `state/db/inbox.py` | **Low** | Parameterized queries, JSONB support required, no DDL |
| `state/db/notifications.py` | **Medium** | Array-based bulk update, parsing of pool.execute() result |
| `state/server.py` | **Low** | Health checks, safe pool lifecycle |
| `orchestrator/HEARTBEAT.md` | **Medium** | Raw SQL via psql, env var dependency, requires psql binary |
| `content/CLAUDE.md` | **High** | Raw SQL via psql, many operations, JSONB digests, no parameterization, requires psql binary |
| `web/lib/strategy.py` | **Low** | SQLite only, isolated from Postgres, WAL safe, threading-protected writes |
| `tests/test_integration.py` | **Low** | Mock only, not production |

### Database Access Timeline

1. **Startup (deploy.sh)**
   - No DB access
   - Just code sync + service restart

2. **Service startup (systemd units)**
   - `state-mcp`: Connects to DB via `get_pool()` at first tool call
   - `orchestrator`: Reads DATABASE_URL only if executing heartbeat
   - `web-tools-mcp`: No DB access (except strategy.db for UCB learning)

3. **Runtime**
   - **State MCP:** Continuous asyncpg pool usage for thesis/notifications/inbox
   - **Orchestrator:** Periodic psql calls during heartbeat (~1 call per 60s)
   - **Content Agent:** Periodic psql calls during content pipeline (~10-30 calls per cycle)
   - **Web Tools:** Periodic SQLite writes to strategy.db (per web tool call)

### Potential Failure Points

| Scenario | Impact | Recovery |
|----------|--------|----------|
| `DATABASE_URL` not set | State MCP startup fails (RuntimeError on first call) | Set env var, restart service |
| Postgres unavailable | Asyncpg connection fails, all tools unavailable | Restore Postgres, systemctl restart state-mcp |
| psql binary missing | Orchestrator/Content Agent heartbeat fails | Install postgresql-client in container |
| Connection string has wrong sslmode | TLS handshake fails (depends on Postgres server config) | Update DATABASE_URL to match server |
| Pool exhaustion (max 5 connections) | New connection requests queue/timeout | Monitor via metrics, increase max_size if needed |
| strategy.db filesystem full | Write to strategy.db fails silently | Truncate strategy table or expand filesystem |

---

## Appendix A: Complete Table Catalog

| Table | Owner | Accessed By | Operations | Status |
|-------|-------|-----------|-----------|--------|
| `thesis_threads` | AI CoS domain | State MCP, Content Agent | SELECT, INSERT, UPDATE | ✅ Live |
| `cai_inbox` | CAI integration | Orchestrator, State MCP, Content Agent | SELECT, INSERT, UPDATE | ✅ Live |
| `notifications` | CAI integration | State MCP (write), Content Agent (read) | SELECT, INSERT, UPDATE | ✅ Live |
| `content_digests` | Content pipeline | Content Agent | SELECT, INSERT, UPDATE | ✅ Live |
| `actions_queue` | Action optimizer | Content Agent (write) | INSERT, UPDATE | ⚠️ Partially used (scoring logic documented, insert not yet shown in code) |
| `strategies` | Web tools (SQLite) | Web Tools MCP | SELECT, INSERT, UPDATE | ✅ Live (local) |

---

## Appendix B: Connection String Examples

### Production (SSL Required)
```
postgresql://aakash:password@db.example.com:5432/aicos?sslmode=require&application_name=state-mcp
```

### Local Development (No SSL)
```
postgresql://postgres:postgres@localhost:5432/aicos
```

### With Credentials in Path
```
postgresql://user:pass@host:5432/dbname?sslmode=require&connect_timeout=10
```

### Critical Parameters
- `sslmode=require` — enforces TLS (recommended for remote databases)
- `connect_timeout=10` — connection timeout in seconds
- `application_name` — helps with logging/monitoring

---

## Appendix C: Recommended Audit Schedule

| Frequency | Task | Owner |
|-----------|------|-------|
| **Per deploy** | Verify `DATABASE_URL` env var set | DevOps |
| **Weekly** | Monitor asyncpg pool saturation (pool.get_size()) | Ops |
| **Monthly** | Review psql command success rate in Orchestrator/Content Agent logs | DevOps |
| **Quarterly** | Review connection string SSL/TLS config vs. server requirements | Security |
| **Annually** | Plan schema migrations, test on staging | DevOps |

---

Generated: 2026-03-18 | Agent: Claude Code Research Explorer
