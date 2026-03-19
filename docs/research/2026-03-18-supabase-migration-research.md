# PostgreSQL to Supabase Migration Research

**Date:** 2026-03-18
**Context:** Migrating self-hosted PostgreSQL 16 (DigitalOcean droplet) to Supabase managed Postgres
**Sources:** Supabase official documentation, verified via web fetch March 2026

---

## 1. pg_dump / pg_restore Format

**Recommended format: directory** (not plain SQL, not custom binary).

Supabase's official migration guide recommends directory format with parallel jobs:

```bash
# DUMP
pg_dump \
  --host=<source_host> \
  --port=<source_port> \
  --username=<source_username> \
  --dbname=<source_database> \
  --jobs=4 \
  --format=directory \
  --no-owner \
  --no-privileges \
  --no-subscriptions \
  --verbose \
  --file=./db_dump 2>&1 | tee -a dump.log

# RESTORE
pg_restore \
  --dbname="$SUPABASE_DB_URL" \
  --jobs=4 \
  --format=directory \
  --no-owner \
  --no-privileges \
  --verbose \
  ./db_dump 2>&1 | tee -a restore.log
```

**Critical flags:**
- `--no-owner` -- prevents `ALTER OWNER TO "aicos"` statements that would fail on Supabase
- `--no-privileges` -- prevents ACL/GRANT statements that conflict with Supabase's role system
- `--no-subscriptions` -- logical replication subscriptions won't work on managed Supabase
- `--jobs=N` -- enables parallel dump/restore (cannot combine with `--single-transaction`)

**Parallelism guidance by DB size:**

| DB Size | Testing | Production |
|---------|---------|------------|
| < 10 GB | 2 | 4 |
| 10-100 GB | 2-4 | 8 |
| 100-500 GB | 4 | 16 |

**Post-restore:** Run `VACUUM VERBOSE ANALYZE;` to update statistics.

**Source:** [Migrate from Postgres to Supabase](https://supabase.com/docs/guides/platform/migrating-to-supabase/postgres)

---

## 2. Connection String Format

Three connection types, each with a distinct format:

### Direct Connection (port 5432)
```
postgresql://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres
```
- Best for: persistent servers (VMs, droplets, long-lived containers)
- Uses IPv6 by default; IPv4 requires add-on or use pooler instead

### Pooler -- Session Mode (port 5432 via pooler host)
```
postgres://postgres.[PROJECT_REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:5432/postgres
```
- Best for: persistent backends that need IPv4

### Pooler -- Transaction Mode (port 6543)
```
postgres://postgres.[PROJECT_REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres
```
- Best for: serverless/edge functions, many short-lived connections
- Does NOT support prepared statements

### SSL

`?sslmode=require` is **NOT mandatory** by default. Supabase allows non-SSL connections out of the box for maximum client compatibility. However:
- SSL enforcement can be toggled on via Dashboard, CLI, or Management API
- When enforced, `sslmode=verify-full` is recommended (requires downloading Supabase CA cert)
- Best practice: always use `?sslmode=require` at minimum for production

**Sources:** [Connecting to Postgres](https://supabase.com/docs/guides/database/connecting-to-postgres), [SSL Enforcement](https://supabase.com/docs/guides/platform/ssl-enforcement)

---

## 3. Connection Pooling

### Supavisor (default, shared pooler)
Supabase's built-in connection pooler. Available on all plans. Supports both session mode (port 5432) and transaction mode (port 6543). Supports IPv4 and IPv6.

### PgBouncer (dedicated pooler)
Available on **Micro compute and above** (paid plans only). Co-located with database for lower latency. Always runs in transaction mode. Does NOT support prepared statements.

### Connection Limits by Compute Size

| Compute | RAM | Max DB Connections | Pooler Max Clients | Price/mo |
|---------|-----|--------------------|--------------------|----------|
| **Nano (Free)** | 0.5 GB | 60 | 200 | $0 |
| **Micro** | 1 GB | 60 | 200 | ~$10 |
| **Small** | 2 GB | 90 | 400 | ~$20 |
| **Medium** | 4 GB | 120 | 600 | ~$40 |
| **Large** | 8 GB | 160 | 800 | ~$80 |
| **XL** | 16 GB | 240 | 1,000 | ~$160 |
| **2XL** | 32 GB | 380 | 1,500 | ~$320 |
| **4XL** | 64 GB | 480 | 3,000 | ~$640 |
| **8XL** | 128 GB | 490 | 6,000 | ~$1,870 |
| **12XL** | 192 GB | 500 | 9,000 | ~$2,800 |
| **16XL** | 256 GB | 500 | 12,000 | ~$3,730 |

**Pool size recommendation:** If heavily using PostgREST API, keep pool size under 40% of max_connections. Otherwise, up to 80% is fine, reserving the rest for auth and utility services.

**Source:** [Compute and Disk](https://supabase.com/docs/guides/platform/compute-and-disk), [Connection Management](https://supabase.com/docs/guides/database/connection-management)

---

## 4. Enabling pgvector

### Dashboard Method
1. Go to Database page in Dashboard
2. Click "Extensions" in sidebar
3. Search for "vector"
4. Enable it

### SQL Method
```sql
CREATE EXTENSION vector WITH SCHEMA extensions;
```

### Usage
```sql
CREATE TABLE posts (
  id serial PRIMARY KEY,
  title text NOT NULL,
  body text NOT NULL,
  embedding extensions.vector(384)
);
```

Note the `extensions.` schema prefix -- Supabase recommends enabling extensions in the `extensions` schema.

**Source:** [pgvector Extension](https://supabase.com/docs/guides/database/extensions/pgvector)

---

## 5. Schema Ownership (`OWNER TO` Conflicts)

**What happens:** If your dump contains `ALTER TABLE ... OWNER TO "aicos"`, the restore will fail because the `aicos` role does not exist on Supabase. Supabase uses the `postgres` role as the default owner.

**Solution:** The `--no-owner` flag on both pg_dump and pg_restore strips all ownership statements. All objects are created under the role running the restore (which is `postgres` on Supabase).

**If you forget `--no-owner`:** You can manually edit the dump and comment out any `ALTER ... OWNER TO` lines, or re-run with the flag.

**Edge case:** If you created tables via custom roles on your source DB, you may hit `42501 privilege` errors. Fix by granting postgres ownership before dump: `REASSIGN OWNED BY aicos TO postgres;`

**Source:** [Migrate from Postgres to Supabase](https://supabase.com/docs/guides/platform/migrating-to-supabase/postgres)

---

## 6. SERIAL Sequences

**Yes, SERIAL sequences transfer correctly via pg_dump/pg_restore.** Sequence definitions and their current values are included in the data section of the dump. When using `--no-owner`, sequence ownership is assigned to the restoring role (`postgres`).

**Potential issue:** If you encounter `permission denied for sequence` errors (e.g., `refresh_tokens_id_seq`), run this on the source before dumping:
```sql
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO postgres;
```

**Source:** [PostgreSQL pg_dump documentation](https://www.postgresql.org/docs/current/app-pgdump.html), [Supabase GitHub Discussion #3464](https://github.com/orgs/supabase/discussions/3464)

---

## 7. Known Gotchas

### Migration-Specific
1. **`OWNER TO` failures** -- Use `--no-owner --no-privileges` on both dump AND restore
2. **`supabase_admin` role errors** -- If restoring FROM Supabase (not relevant for us, but worth knowing): comment out `ALTER ... OWNER TO "supabase_admin"` lines
3. **Logical replication subscriptions** -- Won't work; use `--no-subscriptions`
4. **Extension availability** -- Verify your extensions exist on Supabase before migrating. Check: `SELECT * FROM pg_extension;`
5. **Sequence permissions** -- May need `GRANT ALL ON ALL SEQUENCES` before dump
6. **Triggers during restore** -- Set `session_replication_role = replica` to disable triggers during data load (prevents double encryption, cascading effects)
7. **pg client version mismatch** -- Use pg_dump/pg_restore matching your source PostgreSQL version

### Operational
8. **IPv6 default** -- Direct connections use IPv6. Most droplets are IPv4-only. Use pooler session mode or get IPv4 add-on
9. **Prepared statements** -- Transaction mode pooler does NOT support prepared statements. If your app uses them, use session mode or direct connection
10. **Free plan pausing** -- Free projects pause after 1 week of inactivity. Not suitable for always-on agents
11. **Fail2ban** -- 2 wrong password attempts in a row triggers IP ban. Be careful during initial connection testing
12. **Custom roles need password reset** -- If you migrate custom roles with login, you must manually reset passwords on the new project

---

## 8. psql Access from Droplet

**Yes, you can connect from a droplet using `psql`.** The recommended connection:

```bash
psql "postgresql://postgres.[PROJECT_REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:5432/postgres?sslmode=require"
```

Use the **session mode pooler** (port 5432 via pooler host) for droplet connections since most droplets are IPv4-only and direct connections default to IPv6.

### Network Restrictions
- **Default:** No restrictions. All IPs can connect (still need valid credentials)
- Network restrictions are optional and configurable via Dashboard or CLI
- When enabled, restrictions apply to **both pooled and direct** connections
- Restrictions use CIDR notation; must include both IPv4 and IPv6 if applicable
- Restrictions do NOT apply to HTTPS APIs (PostgREST, Auth, etc.)

### Configuring Restrictions (optional)
```bash
# Check current restrictions
supabase network-restrictions --project-ref $REF get

# Allow specific IP
supabase network-restrictions --project-ref $REF update --db-allow-cidr "YOUR_DROPLET_IP/32"

# Remove all restrictions (allow all)
supabase network-restrictions --project-ref $REF update --db-allow-cidr "0.0.0.0/0" --db-allow-cidr "::/0"
```

**Source:** [Connecting with PSQL](https://supabase.com/docs/guides/database/psql), [Network Restrictions](https://supabase.com/docs/guides/platform/network-restrictions)

---

## 9. Free vs Pro Plan Comparison

| Feature | Free | Pro |
|---------|------|-----|
| **Price** | $0/mo | $25/mo per project |
| **Database size** | 500 MB | 8 GB included |
| **Database egress** | 5 GB | 250 GB |
| **File storage** | 1 GB | 100 GB |
| **Compute** | Nano (shared, 0.5 GB RAM) | Micro (shared, 1 GB RAM) |
| **Max DB connections** | 60 | 60 (same as Micro) |
| **Pooler max clients** | 200 | 200 (same as Micro) |
| **Backups** | None | 7-day daily snapshots |
| **MAUs** | 50,000 | 100,000 |
| **Pausing** | After 1 week inactive | Never |
| **Active projects** | 2 | Unlimited |
| **Support** | Community | Email |
| **Compute upgrades** | No | Yes (Small through 16XL) |
| **Dedicated pooler** | No | Yes (PgBouncer) |

**Pro overage pricing:** Database storage $0.125/GB, file storage $0.021/GB, egress $0.09/GB, MAUs $0.00325/user.

**For our use case (always-on agents):** Free plan is unsuitable due to pausing. Pro at $25/mo is the minimum. With ~7 tables and moderate data, 8 GB is likely sufficient. Connection limits of 60 direct + 200 pooler are adequate for our workload (single orchestrator + 2 agents).

**Source:** [Supabase Pricing](https://supabase.com/pricing), [UI Bakery Supabase Pricing Breakdown](https://uibakery.io/blog/supabase-pricing)

---

## 10. Rollback Strategy

### Before Migration
1. **Keep source database running** -- Do not decommission the droplet Postgres until migration is verified
2. **Take a full backup** of source:
   ```bash
   pg_dump --format=directory --jobs=4 --no-owner --no-privileges \
     --file=./pre_migration_backup \
     "postgresql://user:pass@localhost:5432/aicos"
   ```
3. **Record current state:** Note all sequence values, row counts per table, extension list

### If Migration Fails
1. **Supabase side:** Reset the Supabase database via Dashboard (Settings > General > Reset Database), or create a fresh project
2. **Source side:** Source database is untouched -- simply revert `DATABASE_URL` in your services back to the self-hosted connection string
3. **Re-attempt:** Fix whatever failed, re-run pg_dump/pg_restore

### If Migration Succeeds but Issues Found Later
1. **Supabase backups (Pro):** 7-day daily snapshots available from Dashboard
2. **Point-in-time recovery:** Only available on Enterprise plan
3. **Manual rollback:** Switch `DATABASE_URL` back to self-hosted, re-sync any data written to Supabase during the transition period

### Recommended Approach
Run both databases in parallel during a transition period:
1. Migrate data to Supabase
2. Point one non-critical service at Supabase first (e.g., read-only queries)
3. Verify data integrity and performance
4. Cut over remaining services
5. Keep source database alive for 1-2 weeks as insurance
6. Decommission source only after confidence is established

---

## Summary: Migration Checklist

```
[ ] Verify extensions exist on Supabase (pgvector, etc.)
[ ] Enable extensions via Dashboard before restore
[ ] Run pg_dump with --format=directory --no-owner --no-privileges --no-subscriptions
[ ] Use session mode pooler URL for restore (IPv4 compatible)
[ ] Run pg_restore with --no-owner --no-privileges
[ ] Run VACUUM VERBOSE ANALYZE post-restore
[ ] Verify sequence values match source
[ ] Verify row counts match source
[ ] Test psql access from droplet
[ ] Update DATABASE_URL in all services
[ ] Test all services against Supabase
[ ] Monitor for 1-2 weeks before decommissioning source
```
