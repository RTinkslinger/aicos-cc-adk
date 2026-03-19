# Supabase Migration Audit — Post-Cutover
*Date: 2026-03-19*
*Auditors: 4 parallel agents (schema, security, performance, code)*

---

## Executive Summary

Migration from self-hosted PostgreSQL 16 (droplet, BLR1) to Supabase PostgreSQL 17 (us-west-2) is **functionally complete and data-intact**. However, the audit surfaced **1 CRITICAL, 3 HIGH, and 5 MEDIUM** findings.

**CRITICAL:** Droplet is in Bangalore, Supabase is in Oregon — ~490ms per query (490x regression from local PG). This is the dominant issue.

---

## Findings Summary

| # | Severity | Finding | Category |
|---|----------|---------|----------|
| 1 | **CRITICAL** | Geographic mismatch: BLR1→us-west-2 = ~490ms/query | Performance |
| 2 | **HIGH** | 3 skill files have wrong column names (will cause agent SQL failures) | Code |
| 3 | **HIGH** | Old PostgreSQL still running on droplet (Phase 6 decommission pending) | Security |
| 4 | **HIGH** | `connection.py` missing `statement_cache_size=0` for pooler safety | Code |
| 5 | **MEDIUM** | No `command_timeout` or reconnection logic in connection.py | Code |
| 6 | **MEDIUM** | Sequences `companies_id_seq`/`network_id_seq` have NULL last_value | Schema |
| 7 | **MEDIUM** | No RLS policies — needed before WebFront accesses Supabase | Security |
| 8 | **MEDIUM** | pgvector in `extensions` schema — search_path consideration | Schema |
| 9 | **MEDIUM** | Stuck pipeline loop burning $0.25-0.51/min in API costs | Operations |

---

## CRITICAL: Geographic Latency

| Metric | Value |
|--------|-------|
| TCP RTT (BLR1 → us-west-2) | ~270ms |
| asyncpg query avg (warm pool) | **511ms** |
| asyncpg query p50 | **488ms** |
| asyncpg query p99 | **731ms** |
| Previous (local PG) | <1ms |
| Regression factor | **~490x** |

**Root cause:** Droplet is in DigitalOcean BLR1 (Bangalore, India). Supabase is in AWS us-west-2 (Oregon, USA). ~13,000km distance.

**Options:**
- **A (recommended): Migrate Supabase to ap-south-1 (Mumbai)** — new project, pg_dump/restore, ~10-20ms RTT
- **B: Migrate droplet to US-West** — DigitalOcean SFO3/SJC1, ~5-15ms RTT
- **C: Accept the latency** — 490ms is tolerable for the current 60s heartbeat cycle, but compounds with multiple queries per heartbeat

---

## Schema Audit: 10/10 PASS

| Check | Result |
|-------|--------|
| Constraints (10 PK, 8 UNIQUE) | PASS — matches source |
| Sequences (11) | PASS — no collision risk |
| Indexes (37 including 4 partial) | PASS — all migrated |
| Defaults (87 columns) | PASS — all correct |
| TIMESTAMPTZ (28 columns) | PASS — all timezone-aware |
| PG17 compatibility | PASS — no deprecated features |
| Triggers/functions | PASS — none custom (only Supabase built-in) |
| NULL audit (critical columns) | PASS — zero NULLs |
| Timestamp sanity | PASS — all dates in expected range |
| Orphaned objects | PASS — clean schema |

**Advisory:** `companies_id_seq` and `network_id_seq` have NULL last_value. Fix with:
```sql
SELECT setval('companies_id_seq', COALESCE((SELECT MAX(id) FROM companies), 0));
SELECT setval('network_id_seq', COALESCE((SELECT MAX(id) FROM network), 0));
```

---

## Security Audit: Secure by Default

| Check | Status |
|-------|--------|
| RLS enabled on all 11 tables | YES (deny-all default) |
| anon/authenticated data access | NONE (no SELECT/INSERT/UPDATE/DELETE grants) |
| REST API exposure | NOT EXPOSED (double-protected) |
| SSL enforcement | TLSv1.2 minimum, server cipher preference |
| Connection count | 8/60 (13% utilization) |
| Realtime publication | Empty (no tables published) |
| Old DB accessibility | Localhost-only (127.0.0.1) |

**Key insight:** pg_restore as `postgres` role means Supabase API roles (anon, authenticated, service_role) have NO data access grants. This is a security win over creating tables via the dashboard.

**Action needed for WebFront:** Before connecting from Next.js, must create RLS policies and grant `service_role` access.

---

## Code Audit: 3 FAIL, 3 WARN

### FAIL — Skill doc schema drift (3 files)

| File | Wrong Column | Correct Column |
|------|-------------|----------------|
| `skills/data/postgres-schema.md` (Table 7) | `message_type` | `type` |
| `skills/data/postgres-schema.md` (Table 8) | `notification_type, title, body, source_agent` | `type, content, source` |
| `skills/content/inbox-handling.md` | `message_type`, wrong INSERT | `type`, correct INSERT |
| `skills/sync/change-interpretation.md` | wrong notification INSERT | correct columns |

**Impact:** Content Agent and Sync Agent will get SQL errors when using these skills. Pre-existing issue, not caused by migration.

### WARN — connection.py hardening

1. **Missing `statement_cache_size=0`** — Prepared statement cache can break through session pooler under connection recycling. Safest to disable.
2. **No `command_timeout`** — Queries can hang indefinitely on network issues. Add `command_timeout=30`.
3. **No reconnection logic** — Full Supabase restart leaves pool broken with no recovery. asyncpg handles some recycling internally but a catastrophic disconnect has no recovery path.

### PASS — All other code

- `lifecycle.py` psql subprocess: Uses list form (safe from shell injection), 5s timeout, defensive fallback on failure
- All CLAUDE.md files: Use `$DATABASE_URL`, no localhost references
- `deploy.sh`: No local Postgres assumptions
- `web/server.py`: No Postgres access (unaffected by migration)
- All SQL files: PG17 compatible

---

## Performance Audit

| Metric | Value | Status |
|--------|-------|--------|
| Query latency (avg) | 511ms | CRITICAL (geographic) |
| Connection utilization | 8/60 (13%) | GREEN |
| Buffer cache hit ratio | 99.82% | GREEN |
| Total DB size | 1.3 MB | GREEN |
| Pool config (min=1, max=3) | Appropriate | GREEN |
| Session pooler (port 5432) | Correct for asyncpg | GREEN |
| Index hit ratio | 0-54% | OK (tables too small for index benefit) |
| Heartbeat cost | $0.25-0.51/cycle | HIGH (stuck pipeline loop) |

---

## Action Items

### Immediate (before next session)

1. **Fix skill doc schema drift** — Update 3 skill files with correct column names
2. **Add `statement_cache_size=0`** to `asyncpg.create_pool()` in connection.py
3. **Add `command_timeout=30`** to asyncpg pool for network safety

### Short-term (this week)

4. **Fix stuck pipeline loop** — Content agent not clearing "overdue" condition, burning ~$360-734/day
5. **Reset NULL sequences** — `companies_id_seq` and `network_id_seq`
6. **Evaluate geographic latency** — Decide: migrate Supabase to ap-south-1, migrate droplet to US-West, or accept 490ms

### Phase 6 (1-2 weeks)

7. **Decommission old PostgreSQL** — Stop, disable, final backup
8. **Create RLS policies** — Before WebFront Phase 1 connects to Supabase
