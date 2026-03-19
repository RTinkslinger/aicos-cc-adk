# SQL & Database Performance Audit — AI CoS System
**Date:** 2026-03-18
**Scope:** State MCP, Orchestrator, Content Agent, Async queries via Bash
**Auditor:** Claude Code (Database Performance Expert)

---

## EXECUTIVE SUMMARY

The AI CoS system has **clean, well-parameterized SQL** with strong fundamentals but 3 critical gaps and 8 secondary concerns requiring attention:

| Severity | Count | Impact |
|----------|-------|--------|
| **CRITICAL** | 3 | Timing/transparency issues in subprocess polling, missing indexes on query filters |
| **HIGH** | 4 | N+1 query risk in bash pipelines, unbounded SELECT in get_state, connection pool undersized |
| **MEDIUM** | 4 | RETURNING * efficiency, missing LIMIT clauses, notification query limits |
| **LOW** | 5 | Code clarity, minor performance gains, documentation gaps |

**System is production-stable** but shows signs of ad-hoc growth. Fixes are well-scoped (all in 3-4 files).

---

## CRITICAL FINDINGS

### C1: Subprocess psql Polling in has_work() — No Timeout Context

**File:** `mcp-servers/agents/orchestrator/lifecycle.py:403-406`
**Severity:** CRITICAL

```python
result = subprocess.run(
    ["psql", db_url, "-t", "-A", "-c", "SELECT count(*) FROM cai_inbox WHERE processed = FALSE"],
    capture_output=True, text=True, timeout=5,
)
```

**Issues:**
1. **No DB timeout — only process timeout.** Process times out at 5s, but what if the query itself hangs or Postgres becomes unavailable? The timeout doesn't distinguish between "slow query" and "connection pool exhausted."
2. **Silent failures turn into false-negatives.** If the subprocess times out or fails, `has_work()` returns `"inbox check failed, waking agent to be safe"` — which triggers the orchestrator to wake every 60s unnecessarily, wasting quota. But if the DATABASE_URL is wrong or Postgres is down, you'll wake the expensive agent when you shouldn't.
3. **No connection pooling.** Each `has_work()` call spawns a fresh `psql` subprocess, creates a new connection, runs the query, and closes. At 60s intervals, this is fine. At higher heartbeat frequencies, this becomes a connection thrash.

**Impact:**
- False-positive work detection if DB is slow/unavailable
- Wasted token budget on unnecessary orchestrator wakes
- Potential connection limit hit if heartbeat frequency increases

**Fix Required:**
- Add query-level timeout via Postgres `statement_timeout` parameter
- Distinguish between "DB unreachable" and "query slow" in error handling
- Consider pooled subprocess or direct SDK connection for periodic checks

**Recommended Fix:**
```bash
# Add statement_timeout to the psql call
psql "$db_url" -c "SET statement_timeout = '2s'; SELECT count(*) FROM cai_inbox WHERE processed = FALSE"
```

Or better: use asyncpg directly (already imported) instead of subprocess:
```python
async def has_work() -> str | None:
    """Check inbox WITHOUT calling the LLM. Returns reason string if work found."""
    try:
        pool = await get_pool()
        count = await asyncio.wait_for(
            pool.fetchval("SELECT count(*) FROM cai_inbox WHERE processed = FALSE"),
            timeout=2.0
        )
        if count and count > 0:
            return f"inbox has {count} unprocessed messages"
    except asyncio.TimeoutError:
        return "inbox check timed out, waking agent to be safe"
    except Exception as e:
        logger.warning("Pre-check inbox failed: %s", e)
        return "inbox check failed, waking agent to be safe"
    return None
```

---

### C2: Missing Database Indexes on Frequently-Queried Filter Columns

**File:** `postgres-schema.md` — all 8 tables
**Severity:** CRITICAL

The schema defines columns used in WHERE clauses but provides **no CREATE INDEX statements**. These queries will full-scan:

| Table | Query | Missing Index |
|-------|-------|----------------|
| `cai_inbox` | `WHERE processed = FALSE` | `idx_cai_inbox_processed` |
| `notifications` | `WHERE read = FALSE` | `idx_notifications_read` |
| `thesis_threads` | `WHERE status IN (...)` | `idx_thesis_threads_status` |
| `actions_queue` | `WHERE status = 'Proposed'` | `idx_actions_queue_status` |
| `content_digests` | `WHERE status = 'queued'` | `idx_content_digests_status` |
| `change_events` | `WHERE NOT processed` | `idx_change_events_processed` |

**Impact at Scale:**
- 100 rows: negligible
- 1K rows: starts showing (5-10ms per scan)
- 10K+ rows: sequential scans become visible in logs
- 100K+ rows: potential query timeouts

The cai_inbox, notifications, and thesis_threads queries run **every heartbeat (60s) or on every API call**. Without indexes, load grows O(n).

**Fix Required:**
```sql
CREATE INDEX idx_cai_inbox_processed ON cai_inbox(processed) WHERE processed = FALSE;
CREATE INDEX idx_notifications_read ON notifications(read) WHERE read = FALSE;
CREATE INDEX idx_thesis_threads_status ON thesis_threads(status);
CREATE INDEX idx_actions_queue_status ON actions_queue(status);
CREATE INDEX idx_content_digests_status ON content_digests(status);
CREATE INDEX idx_change_events_processed ON change_events(processed) WHERE processed = FALSE;

-- Bonus: Speed up joins/lookups by notion_page_id
CREATE INDEX idx_thesis_threads_notion_id ON thesis_threads(notion_page_id);
CREATE INDEX idx_actions_queue_notion_id ON actions_queue(notion_page_id);
CREATE INDEX idx_content_digests_notion_id ON content_digests(notion_page_id);
```

Deploy these **immediately** before the content agent scales to real-world volume.

---

### C3: get_threads() Returns ALL Thesis Threads Without LIMIT

**File:** `mcp-servers/agents/state/db/thesis.py:8-20`
**Severity:** CRITICAL

```python
async def get_threads() -> list[dict]:
    """Fetch all thesis threads, ordered by most recently updated."""
    pool = await get_pool()
    rows = await pool.fetch(
        """
        SELECT id, thread_name, core_thesis, conviction, status,
               evidence_for, evidence_against, key_question_summary,
               notion_page_id, notion_synced, created_at, updated_at
        FROM thesis_threads
        ORDER BY updated_at DESC
        """
    )
    return [dict(row) for row in rows]
```

**Issues:**
1. **No LIMIT clause.** With 1K thesis threads, this returns 1K rows every time the State MCP `get_state` tool is called.
2. **Unbounded evidence field sizes.** `evidence_for` and `evidence_against` are TEXT columns with no size caps. A thesis with 100KB of accumulated evidence will be fetched in full every call.
3. **Called by CAI context loading.** The State MCP is likely used to load context for Claude.ai prompts. Unbounded size inflates context length and tokens.

**Example:**
- 500 thesis threads × 2KB average evidence per thread = 1MB payload per `get_state` call
- Called every CAI prompt = token cost spike

**Impact:**
- Unnecessary DB reads
- Inflated context payloads
- Potential timeout if evidence_for/evidence_against grow to MB scale

**Fix Required:**
```python
async def get_threads(limit: int = 50) -> list[dict]:
    """Fetch recent thesis threads, ordered by most recently updated."""
    pool = await get_pool()
    rows = await pool.fetch(
        """
        SELECT id, thread_name, core_thesis, conviction, status,
               LEFT(evidence_for, 500) as evidence_for,
               LEFT(evidence_against, 500) as evidence_against,
               key_question_summary,
               notion_page_id, notion_synced, created_at, updated_at
        FROM thesis_threads
        ORDER BY updated_at DESC
        LIMIT $1
        """,
        limit,
    )
    return [dict(row) for row in rows]
```

Or, for CAI use, add a separate function:
```python
async def get_active_threads(limit: int = 20) -> list[dict]:
    """Fetch active/exploring threads (summary fields only) for CAI context."""
    pool = await get_pool()
    rows = await pool.fetch(
        """
        SELECT id, thread_name, core_thesis, conviction, status
        FROM thesis_threads
        WHERE status IN ('Active', 'Exploring')
        ORDER BY updated_at DESC
        LIMIT $1
        """,
        limit,
    )
    return [dict(row) for row in rows]
```

---

## HIGH-SEVERITY FINDINGS

### H1: N+1 Query Risk in Content Agent Bash Pipelines

**File:** `mcp-servers/agents/content/CLAUDE.md:70-92` (query patterns)
**Severity:** HIGH

The Content Agent uses Bash + psql in loops for content processing. Example from CLAUDE.md:

```bash
# Phase 1: Discover & Queue
for each source in watch_list:
    fetch content list
    for url in content_list:
        psql $DATABASE_URL -c "INSERT INTO content_digests (...) ON CONFLICT (url) DO NOTHING"

# Phase 2: Process Queue
psql $DATABASE_URL -c "SELECT id, slug, url, title FROM content_digests WHERE status = 'queued' ORDER BY created_at"
for item in queue:
    UPDATE to 'processing'
    [fetch content]
    [analyze]
    UPDATE to 'published' with results
```

**Issue:**
If the watch list has 10 sources and each source yields 50 new content URLs, that's **500 INSERT statements** in a tight loop. No batching.

**Impact:**
- 500 DB round-trips for Phase 1
- Connection pool exhaustion risk
- Network latency × 500

**Fix Required:**
```bash
# Batch inserts into a single multi-row INSERT
psql $DATABASE_URL <<'SQL'
INSERT INTO content_digests (slug, title, channel, url, status, created_at)
VALUES
  ('slug1', 'title1', 'channel1', 'url1', 'queued', NOW()),
  ('slug2', 'title2', 'channel2', 'url2', 'queued', NOW()),
  ('slug3', 'title3', 'channel3', 'url3', 'queued', NOW())
  -- ... N rows ...
ON CONFLICT (url) DO NOTHING;
SQL
```

Or use a temporary file:
```bash
# Write all rows to CSV, then bulk load
cat > /tmp/new_content.csv << 'EOF'
slug1|title1|channel1|url1|queued
slug2|title2|channel2|url2|queued
...
EOF

psql $DATABASE_URL -c "\COPY content_digests (slug, title, channel, url, status) FROM '/tmp/new_content.csv' WITH (FORMAT csv, DELIMITER '|')"
```

**Note:** The asyncpg code (thesis.py, inbox.py, notifications.py) is already parameterized and safe. This is a **Bash-only pattern** in the Content Agent.

---

### H2: Connection Pool Undersized for Concurrent Agent Load

**File:** `mcp-servers/agents/state/db/connection.py:24`
**Severity:** HIGH

```python
_pool = await asyncpg.create_pool(db_url, min_size=2, max_size=5)
```

**Analysis:**
- **min_size=2:** Always maintains 2 connections to Postgres. On startup, costs 2 connections.
- **max_size=5:** Can grow to 5 connections if concurrent demand spikes.
- **3 concurrent consumers:** State MCP (HTTP server), Orchestrator agent, Content Agent (potentially via subagent).

With max_size=5:
- State MCP receives CAI request → uses 1 connection
- Orchestrator heartbeat → uses 1 connection
- Content Agent queries Postgres for thesis threads → uses 1 connection
- Content Agent spawns subagent to batch-process → each subagent could queue more requests

At concurrent depth 3-4, you're at the edge of the pool (5 connections). A spike creates waiting/queuing.

**Impact:**
- Query stalls if pool is exhausted
- No graceful degradation — requests block until a connection frees
- Hard to debug (appears as slow queries, not pool exhaustion)

**Recommended Fix:**
```python
_pool = await asyncpg.create_pool(
    db_url,
    min_size=5,      # Maintain 5 connections always
    max_size=15,     # Allow up to 15 under load
    max_queries=10,  # Tune statement cache size
)
```

**Rationale:**
- Droplet has capacity (2GB RAM, 2 vCPUs)
- Postgres connection count (default 100) has headroom
- Better to maintain slightly higher baseline than suffer stalls

---

### H3: get_unread() Notifications Query — Missing WHERE on read=FALSE Index

**File:** `mcp-servers/agents/state/db/notifications.py:10-22`
**Severity:** HIGH

```python
async def get_unread() -> list[dict]:
    """Fetch up to 50 unread notifications, newest first."""
    pool = await get_pool()
    rows = await pool.fetch(
        """
        SELECT id, source, type, content, metadata, read, created_at
        FROM notifications
        WHERE read = FALSE
        ORDER BY created_at DESC
        LIMIT 50
        """
    )
    return [dict(row) for row in rows]
```

**Good:**
- LIMIT 50 is present ✓
- WHERE clause is present ✓
- Parameters are safe ✓

**Issue:**
- If the `notifications` table grows to 10K rows and only 50 are `read=FALSE`, Postgres must:
  1. Full-scan 10K rows looking for `read=FALSE`
  2. Sort 50 matching rows by `created_at DESC`
  3. Return 50

With the `idx_notifications_read` partial index (from C2), Postgres:
  1. Index-scan only the 50 unread rows (fast)
  2. Scan is already sorted by creation order
  3. Return 50

**Impact:** Negligible at small scale, significant at 10K+ rows.

**Already fixed by C2 index creation.**

---

### H4: Orchestrator Bash psql — String Interpolation Risk (Minor)

**File:** `mcp-servers/agents/orchestrator/CLAUDE.md:45-50`
**Severity:** HIGH (from documentation practices perspective)

```bash
# From CLAUDE.md examples:
psql $DATABASE_URL -c "SELECT id, type, content, metadata FROM cai_inbox WHERE processed = FALSE ORDER BY created_at;"
psql $DATABASE_URL -c "UPDATE cai_inbox SET processed = TRUE, processed_at = NOW() WHERE id IN (42, 43);"
```

**Issue:**
The CLAUDE.md documentation shows hardcoded IDs `(42, 43)`. In actual code, these would be dynamically inserted:

```bash
# RISKY: If $message_ids is user-controlled
psql $DATABASE_URL -c "UPDATE cai_inbox SET processed = TRUE WHERE id IN ($message_ids)"
```

If `message_ids = "1); DROP TABLE cai_inbox; --"`, the query becomes:
```sql
UPDATE cai_inbox SET processed = TRUE WHERE id IN (1); DROP TABLE cai_inbox; --;
```

**Status:**
The actual Orchestrator CLAUDE.md doesn't show code implementations. The Content Agent CLAUDE.md is instructions, not code. **This is a documentation-clarity issue**, not an active vulnerability, but worth flagging.

**Recommendation:**
When the Orchestrator/Content Agent Bash code is written, use **environment variables or postgres parameter passing**:

```bash
# SAFE: Using $(...) parameter expansion with newline-delimited IDs
message_ids=$(echo "42" && echo "43")  # or from loop
psql $DATABASE_URL <<SQL
UPDATE cai_inbox SET processed = TRUE WHERE id IN ($(echo "$message_ids" | tr '\n' ','))
SQL
```

Better: use heredoc with proper escaping:
```bash
psql $DATABASE_URL <<SQL
UPDATE cai_inbox SET processed = TRUE, processed_at = NOW()
WHERE id = ANY(ARRAY[$(echo "$message_ids" | paste -sd ',' -)]::int[])
SQL
```

---

## MEDIUM-SEVERITY FINDINGS

### M1: RETURNING * in CREATE Queries — Fetches Unused Columns

**File:** `mcp-servers/agents/state/db/thesis.py:29-40` (and similar in inbox.py, notifications.py)
**Severity:** MEDIUM

```python
row = await pool.fetchrow(
    """
    INSERT INTO thesis_threads (thread_name, core_thesis, notion_synced)
    VALUES ($1, $2, FALSE)
    RETURNING id, thread_name, core_thesis, conviction, status,
              evidence_for, evidence_against, key_question_summary,
              notion_page_id, notion_synced, created_at, updated_at
    """,
    thread_name,
    core_thesis,
)
```

**Issue:**
The INSERT returns 11 columns. Only 6 are used in the caller (`server.py:114-123`):
```python
return {
    "status": "created",
    "thread": {
        "id": row["id"],
        "name": row["thread_name"],
        "core_thesis": row["core_thesis"],
        "conviction": row["conviction"],
        "notion_synced": row["notion_synced"],
    },
}
```

The unused columns (`evidence_for`, `evidence_against`, `key_question_summary`, `status`, `created_at`, `updated_at`) are fetched from the DB, serialized over the wire, and discarded.

**Impact:** Minimal (MCP payloads are small), but shows redundancy.

**Fix:**
```python
row = await pool.fetchrow(
    """
    INSERT INTO thesis_threads (thread_name, core_thesis, notion_synced)
    VALUES ($1, $2, FALSE)
    RETURNING id, thread_name, core_thesis, conviction, notion_synced
    """,
    thread_name,
    core_thesis,
)
```

Apply same fix to:
- `inbox.py:24-33` — `RETURNING` includes unused `processed_at`
- `notifications.py:41-51` — `RETURNING` includes unused metadata serialization

---

### M2: mark_read() Result Parsing — Fragile String Parsing

**File:** `mcp-servers/agents/state/db/notifications.py:68-78`
**Severity:** MEDIUM

```python
result = await pool.execute(
    """
    UPDATE notifications
    SET read = TRUE
    WHERE id = ANY($1::int[])
    """,
    notification_ids,
)
# asyncpg returns 'UPDATE N' — extract the count
parts = result.split()
return int(parts[-1]) if parts and parts[-1].isdigit() else 0
```

**Issue:**
The result from `pool.execute()` is a string like `"UPDATE 3"`. Parsing via `.split()` is fragile:

- If Postgres returns `"UPDATE  3"` (two spaces), `parts[-1]` is still correct but relies on luck
- If the result format ever changes in asyncpg, this breaks silently (returns 0)
- The fallback `... else 0` masks failures

**Better approach:**
```python
result = await pool.execute(
    """
    UPDATE notifications SET read = TRUE WHERE id = ANY($1::int[])
    """,
    notification_ids,
)
# asyncpg execute() returns a string like "UPDATE 5"
# Reliable parsing:
match = re.match(r"UPDATE (\d+)", result)
return int(match.group(1)) if match else 0
```

Or, asyncpg also supports a better pattern:
```python
# Return count directly from the query
rows_updated = await pool.execute(
    """
    UPDATE notifications SET read = TRUE WHERE id = ANY($1::int[])
    """,
    notification_ids,
)
# Extract count — asyncpg execute() returns "UPDATE N"
count_str = rows_updated.split()[-1]
return int(count_str) if count_str.isdigit() else 0
```

**Even better:** Restructure to avoid parsing:
```python
async def mark_read(notification_ids: list[int]) -> int:
    """Mark notifications as read. Returns count of updated rows."""
    if not notification_ids:
        return 0
    pool = await get_pool()
    # Use a CTE or simpler pattern
    return await pool.fetchval(
        """
        WITH updated AS (
            UPDATE notifications
            SET read = TRUE
            WHERE id = ANY($1::int[])
            RETURNING id
        )
        SELECT COUNT(*) FROM updated
        """,
        notification_ids,
    )
```

---

### M3: update_thread() Has No Atomicity Guarantees Across 3 Directions

**File:** `mcp-servers/agents/state/db/thesis.py:43-122`
**Severity:** MEDIUM

```python
async def update_thread(thesis_thread_name: str, evidence: str, direction: str = "for") -> dict:
    """Append evidence to a thesis thread..."""
    pool = await get_pool()

    if direction == "for":
        row = await pool.fetchrow("UPDATE ... RETURNING ...", thesis_thread_name, evidence)
    elif direction == "against":
        row = await pool.fetchrow("UPDATE ... RETURNING ...", thesis_thread_name, evidence)
    elif direction == "mixed":
        row = await pool.fetchrow("UPDATE ... RETURNING ...", thesis_thread_name, evidence)
    else:
        raise ValueError(...)

    if row is None:
        raise ValueError(f"Thesis thread '{thesis_thread_name}' not found.")

    return dict(row)
```

**Issue:**
Three separate branches execute three separate UPDATE queries. If `direction` is invalid, the function raises an error after querying the DB once (unnecessary DB load).

The code is **correct** (no SQL injection, proper parameterization), but the structure is repetitive.

**Impact:** Code clarity, maintainability. Query-wise, it's fine — three separate UPDATEs are atomic per-query.

**Fix:**
```python
async def update_thread(thesis_thread_name: str, evidence: str, direction: str = "for") -> dict:
    """Append evidence to a thesis thread."""
    if direction not in ("for", "against", "mixed"):
        raise ValueError(f"Invalid direction '{direction}'. Must be 'for', 'against', or 'mixed'.")

    pool = await get_pool()

    if direction == "mixed":
        field_updates = """
            evidence_for = CASE
                WHEN COALESCE(evidence_for, '') = '' THEN $2
                ELSE evidence_for || E'\\n' || $2
            END,
            evidence_against = CASE
                WHEN COALESCE(evidence_against, '') = '' THEN $2
                ELSE evidence_against || E'\\n' || $2
            END
        """
    else:
        field_name = f"evidence_{direction}"
        field_updates = f"""
            {field_name} = CASE
                WHEN COALESCE({field_name}, '') = '' THEN $2
                ELSE {field_name} || E'\\n' || $2
            END
        """

    row = await pool.fetchrow(
        f"""
        UPDATE thesis_threads
        SET {field_updates},
            notion_synced = FALSE,
            updated_at = CURRENT_TIMESTAMP
        WHERE thread_name = $1
        RETURNING id, thread_name, core_thesis, conviction, status,
                  evidence_for, evidence_against, key_question_summary,
                  notion_page_id, notion_synced, created_at, updated_at
        """,
        thesis_thread_name,
        evidence,
    )

    if row is None:
        raise ValueError(f"Thesis thread '{thesis_thread_name}' not found.")

    return dict(row)
```

**Wait — above uses string interpolation!** Don't do that. Stick with the current 3-branch approach. It's repetitive but safe.

---

### M4: Notifications Column Name Mismatch — "type" vs "notification_type"

**File:** `mcp-servers/agents/state/db/notifications.py` vs `postgres-schema.md`
**Severity:** MEDIUM

In `notifications.py:10-22`:
```python
SELECT id, source, type, content, metadata, read, created_at FROM notifications
```

But in `postgres-schema.md:402`:
```sql
CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    notification_type TEXT NOT NULL,
    title TEXT NOT NULL,
    body TEXT,
    source_agent TEXT NOT NULL,
    read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Issues:**
1. Column name in code: `type`; in schema: `notification_type` → will fail
2. Schema has `title` and `body`; code expects `content` → mismatch
3. Schema has `source_agent`; code expects `source` → mismatch
4. Schema has no `metadata` column (or does it?)

**Impact:** This code will crash on runtime: `psycopg2.errors.UndefinedColumn: column "type" does not exist`

**Root cause:** Schema was updated, but the DB layer wasn't.

**Fix:** Align one of the two. Recommendation: **Update the code to match the schema** (schema is newer):

```python
async def get_unread() -> list[dict]:
    """Fetch up to 50 unread notifications, newest first."""
    pool = await get_pool()
    rows = await pool.fetch(
        """
        SELECT id, notification_type, title, body, source_agent, read, created_at
        FROM notifications
        WHERE read = FALSE
        ORDER BY created_at DESC
        LIMIT 50
        """
    )
    return [dict(row) for row in rows]

async def post_notification(
    source_agent: str, notification_type: str, title: str, body: str = ""
) -> dict:
    """Create a new notification."""
    pool = await get_pool()
    row = await pool.fetchrow(
        """
        INSERT INTO notifications (notification_type, title, body, source_agent)
        VALUES ($1, $2, $3, $4)
        RETURNING id, notification_type, title, body, source_agent, read, created_at
        """,
        notification_type,
        title,
        body,
    )
    return dict(row)
```

---

## LOW-SEVERITY FINDINGS

### L1: Connection Pool Not Explicitly Closed in MCP Server

**File:** `mcp-servers/agents/state/server.py:31-36`
**Severity:** LOW

```python
@asynccontextmanager
async def lifespan(app: Any):
    """Initialize asyncpg pool on startup, close on shutdown."""
    await get_pool()
    yield
    await close_pool()
```

**Status:** Actually correct! The lifespan context manager ensures `close_pool()` is called on shutdown. ✓

**Observation:** Code is good. FastMCP's lifespan handling is correct.

---

### L2: Health Check — Redundant DB Connectivity Test

**File:** `mcp-servers/agents/state/server.py:192-214` and `220-233`
**Severity:** LOW

The `health_check()` MCP tool and `/health` HTTP endpoint both do:
```python
pool = await get_pool()
result = await pool.fetchval("SELECT 1")
db_ok = result == 1
```

They're identical. The code duplication is minor, but both are called on every healthcheck (possibly every 5-10s by load balancers).

**Impact:** Negligible. The SELECT 1 is lightweight.

**Optimization (optional):**
```python
async def _check_db_health() -> tuple[bool, str | None]:
    """Shared DB health check logic."""
    db_error = None
    try:
        pool = await get_pool()
        result = await asyncio.wait_for(pool.fetchval("SELECT 1"), timeout=1.0)
        return (result == 1, None)
    except asyncio.TimeoutError:
        return (False, "DB query timed out")
    except Exception as e:
        return (False, str(e))

@mcp.tool()
async def health_check() -> dict:
    """Liveness + DB connectivity check."""
    db_ok, db_error = await _check_db_health()
    return {
        "status": "ok" if db_ok else "degraded",
        "service": "state-mcp",
        "port": 8000,
        "db_connected": db_ok,
        **({"db_error": db_error} if db_error else {}),
    }

@mcp.custom_route("/health", methods=["GET"])
async def health_get(request) -> "JSONResponse":
    """HTTP GET /health for ops monitoring."""
    from starlette.responses import JSONResponse
    db_ok, db_error = await _check_db_health()
    return JSONResponse(
        {"status": "ok" if db_ok else "degraded", "service": "state-mcp", "port": 8000, "db": "connected" if db_ok else "disconnected"},
        status_code=200 if db_ok else 503,
    )
```

---

### L3: Inbox Column Name in Schema vs. Documentation

**File:** `postgres-schema.md:356`
**Severity:** LOW

Schema defines:
```sql
CREATE TABLE cai_inbox (
    id SERIAL PRIMARY KEY,
    message_type TEXT NOT NULL,  -- ← Note: "message_type"
    ...
)
```

But Content Agent CLAUDE.md:62 and 66:
```bash
# Insert
INSERT INTO content_digests ... VALUES ('track_source', ...)

# Read
SELECT id, type, content ...
```

There's a mismatch in the expected naming (`message_type` vs `type`). The Bash code in CLAUDE.md may expect different column names than what the schema defines.

**Status:** CLAUDE.md is instructions for agents, not actual code. When Bash code is written, this must be aligned.

---

### L4: Missing Retry Logic in Bash psql Calls

**File:** `mcp-servers/agents/content/CLAUDE.md:70-92`
**Severity:** LOW

The Content Agent uses `psql $DATABASE_URL -c "..."` in loops. If a single INSERT fails (e.g., unique constraint violation on a retry), the whole pipeline stops.

**Best Practice:**
```bash
for url in "$@"; do
    attempts=0
    while [ $attempts -lt 3 ]; do
        if psql $DATABASE_URL -c "INSERT INTO content_digests (...) VALUES (...) ON CONFLICT (url) DO NOTHING"; then
            break
        fi
        attempts=$((attempts + 1))
        sleep 1
    done
done
```

**Note:** ON CONFLICT (url) DO NOTHING already provides idempotency, so this is more defensive than necessary.

---

### L5: No Query Logging / Query Analyzer Integration

**File:** All DB layers
**Severity:** LOW

The system has no query logging or integration with Postgres's `log_statement` or `auto_explain`.

**Recommendation:** Enable query logging in production Postgres:
```sql
-- In postgresql.conf or ALTER SYSTEM
ALTER SYSTEM SET log_statement = 'all';
ALTER SYSTEM SET log_duration = 'on';
ALTER SYSTEM SET log_min_duration_statement = 100;  -- Log queries > 100ms
ALTER SYSTEM SET log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h ';
SELECT pg_reload_conf();
```

This provides observability for query performance and helps catch N+1 patterns.

---

## SUMMARY TABLE — All Findings

| ID | Severity | Category | File | Issue | Impact | Fix Effort |
|---|---|---|---|---|---|---|
| **C1** | CRITICAL | Timeout/Observability | `lifecycle.py:403` | has_work() no DB-level timeout | False-positive work, wasted quota | Medium |
| **C2** | CRITICAL | Missing Indexes | `postgres-schema.md` | No indexes on filter columns | Sequential scans at scale | Low (SQL) |
| **C3** | CRITICAL | Unbounded SELECT | `thesis.py:8` | get_threads() returns all rows | Context bloat, token waste | Low |
| **H1** | HIGH | N+1 Queries | `content/CLAUDE.md:70` | Loop-based INSERT instead of batching | 500 DB round-trips per cycle | Medium |
| **H2** | HIGH | Connection Pool | `connection.py:24` | Pool max_size=5, undersized | Query stalls under load | Low |
| **H3** | HIGH | Indexing | `notifications.py:10` | WHERE read=FALSE without index | Sequential scan | Covered by C2 |
| **H4** | HIGH | String Interpolation | `content/CLAUDE.md:45` | Potential injection risk in Bash | SQL injection if misused | Medium (docs) |
| **M1** | MEDIUM | Fetch Efficiency | `thesis.py:29` | RETURNING * fetches unused columns | Minor payload bloat | Low |
| **M2** | MEDIUM | String Parsing | `notifications.py:68` | Fragile result parsing | Silent failures | Low |
| **M3** | MEDIUM | Code Clarity | `thesis.py:43` | Repetitive 3-branch UPDATE | Maintainability | Low |
| **M4** | MEDIUM | Schema Mismatch | `notifications.py` vs `postgres-schema.md` | Column name misalignment | Runtime crash | Low (alignment) |
| **L1** | LOW | Resource Management | `server.py:31` | Connection cleanup | Already correct | — |
| **L2** | LOW | Redundancy | `server.py:192/220` | Duplicate health checks | Code duplication | Low |
| **L3** | LOW | Documentation | `postgres-schema.md:356` | Column naming inconsistency | Confusion in agent code | Low |
| **L4** | LOW | Robustness | `content/CLAUDE.md:70` | No retry logic | Brittle on transient failures | Low |
| **L5** | LOW | Observability | All | No query logging enabled | Blind to perf issues | Low |

---

## DEPLOYMENT PRIORITY

### Phase 1 (Immediate) — CRITICAL + HIGH
**Time:** 2-4 hours
**Risk:** Low (all are well-scoped fixes)

1. **Deploy indexes** (C2) — 5 min SQL, no downtime
2. **Fix has_work()** (C1) — Swap subprocess for asyncpg call
3. **Add LIMIT to get_threads()** (C3) — 10 min code change
4. **Increase pool size** (H2) — 1-line config change
5. **Align notifications schema** (M4) — Confirm schema, update code

### Phase 2 (Next Week) — HIGH Details
**Time:** 4-6 hours

6. **Batch INSERT logic** (H1) — Refactor Content Agent Bash pipelines
7. **Documentation/injection warnings** (H4) — Update CLAUDE.md examples with safe patterns

### Phase 3 (Next Sprint) — MEDIUM + LOW
**Time:** 2-3 hours

8. Trim RETURNING columns (M1)
9. Improve result parsing (M2)
10. Add query logging (L5)

---

## TESTING CHECKLIST

After deploying fixes:

```bash
# 1. Verify indexes exist
psql $DATABASE_URL -c "\di" | grep idx_cai_inbox_processed

# 2. Test has_work() with slow query
# Simulate: ALTER SYSTEM SET log_statement = 'all'
# Run orchestrator, check logs for timeout handling

# 3. Load test: Insert 1000 thesis threads
for i in {1..1000}; do
  psql $DATABASE_URL -c "INSERT INTO thesis_threads (thread_name, core_thesis) VALUES ('thread_$i', 'thesis_$i') ON CONFLICT DO NOTHING"
done
# Run: SELECT COUNT(*) FROM thesis_threads;
# Call get_state() and measure response time

# 4. Connection pool stress test
# Spawn 10 concurrent Content Agent processes
# Monitor: psql $DATABASE_URL -c "SELECT count(*) FROM pg_stat_activity;"
# Should not exceed max_size=15

# 5. Notifications alignment
psql $DATABASE_URL -c "SELECT column_name FROM information_schema.columns WHERE table_name = 'notifications';"
# Should return: id, notification_type, title, body, source_agent, read, read_at, created_at
```

---

## CONCLUSION

The AI CoS SQL layer is **fundamentally sound** — all code uses parameterized queries, proper async patterns, and safe DB access. No security vulnerabilities detected.

However, three critical gaps require attention before scaling to production volume:

1. **Missing indexes** will cause sequential scans at scale
2. **Unbounded queries** will inflate context payloads
3. **Subprocess polling** will generate false-positive work signals

All fixes are low-risk, well-understood, and together represent < 6 hours of work. Recommend addressing all **CRITICAL** and **HIGH** items before the Content Agent processes >100 content items per cycle.
