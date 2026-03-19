# WebFront Phase 1 Execution Plan
*Date: 2026-03-19*
*Status: APPROVED — ready to execute*
*Prerequisite: Supabase migration DONE (Mumbai, ap-south-1, 31ms latency)*

---

## Overview

Build the first interactive WebFront features on digest.wiki: action triage UI + semantic search foundation. Leverages Supabase PostgREST (auto-API), Realtime (live updates), and pgvector (semantic search via Voyage AI embeddings).

**Architectural constraint:** Agents remain the orchestration layer. Supabase extensions (pgmq, pg_cron) are used ONLY as invisible infrastructure for Auto Embeddings — agents never interact with them directly. Agents are pure consumers of embeddings.

---

## Phase 0: Foundation (prerequisites)

### 0.1 RLS Policies
Grant `service_role` full access to all 11 tables (for server-side Next.js). No `anon`/`authenticated` access yet (single user, server-side only).

```sql
-- For each table: grant service_role full CRUD
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO service_role;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO service_role;
```

### 0.2 Vercel Environment Variables
Add to `aicos-digests` Vercel project:
- `NEXT_PUBLIC_SUPABASE_URL` = `https://llfkxnsfczludgigknbs.supabase.co`
- `SUPABASE_SERVICE_ROLE_KEY` = (from Supabase dashboard → API keys)
- `NEXT_PUBLIC_SUPABASE_ANON_KEY` = (from Supabase dashboard → API keys)

### 0.3 Supabase Client in Next.js
Install `@supabase/ssr` + `@supabase/supabase-js` in aicos-digests.
Create server-side Supabase client utility using `service_role` key.

### 0.4 Delete Oregon Supabase Project
Delete `bkxjvymaiknokybtupfm` (us-west-2) from Supabase dashboard. No longer needed.

---

## Phase 1A: Action Triage UI

### Pages
- `/actions` — Actions list page (Server Component, reads `actions_queue` via Supabase SDK)
  - Filter by: status (Proposed/Accepted/Dismissed), priority (P0-P3), thesis connection
  - Sort by: created_at, relevance_score, priority
  - Realtime subscription: new actions appear live without refresh

### Server Actions
- `triageAction(id, decision)` — Update action status (Proposed → Accepted/Dismissed)
- `rateOutcome(id, outcome)` — Set outcome (Unknown/Helpful/Gold)
- `deferAction(id)` — Move to lower priority

### On Digest Pages
- Add "Related Actions" section to `/d/[slug]` — shows actions where `source_digest_notion_id` matches

### Data Flow
```
Content Agent (droplet)
  → Writes action to actions_queue (psql, as today)
  → Supabase Realtime streams INSERT to WebFront
  → WebFront shows new action in real-time
  → Aakash taps Accept/Dismiss (Server Action → Supabase SDK → UPDATE)
  → Outcome data flows to action_outcomes (preference store)
```

---

## Phase 1B: Semantic Search Foundation (IRGI Phase A)

Piggybacked onto Phase 1 setup. Agents are consumers, not producers.

### 1B.1 Vector Columns
```sql
ALTER TABLE content_digests ADD COLUMN IF NOT EXISTS embedding vector(1024);
ALTER TABLE thesis_threads ADD COLUMN IF NOT EXISTS embedding vector(1024);
```
1024 dimensions = Voyage AI `voyage-3.5` default output.

### 1B.2 Auto Embeddings Pipeline (invisible infrastructure)

Enable extensions:
```sql
CREATE EXTENSION IF NOT EXISTS pgmq;    -- queue for embedding jobs
CREATE EXTENSION IF NOT EXISTS pg_cron;  -- schedules batch processing
CREATE EXTENSION IF NOT EXISTS pg_net;   -- HTTP calls to Edge Function
```

Components:
1. **DB trigger** on content_digests/thesis_threads INSERT/UPDATE → enqueues embedding job in pgmq
2. **pg_cron job** (every 30s) → batches queued jobs → calls Edge Function via pg_net
3. **Edge Function** → calls Voyage AI API (`voyage-3.5`) → writes vector back to row

Agents never see pgmq/pg_cron/pg_net. They write content as usual. Embeddings appear automatically.

### 1B.3 FTS Indexes
```sql
ALTER TABLE content_digests ADD COLUMN IF NOT EXISTS fts tsvector
  GENERATED ALWAYS AS (to_tsvector('english', coalesce(title, '') || ' ' || coalesce(channel, ''))) STORED;
CREATE INDEX IF NOT EXISTS idx_content_digests_fts ON content_digests USING gin(fts);

ALTER TABLE thesis_threads ADD COLUMN IF NOT EXISTS fts tsvector
  GENERATED ALWAYS AS (to_tsvector('english', coalesce(thread_name, '') || ' ' || coalesce(core_thesis, ''))) STORED;
CREATE INDEX IF NOT EXISTS idx_thesis_threads_fts ON thesis_threads USING gin(fts);
```

### 1B.4 Hybrid Search Function
```sql
CREATE OR REPLACE FUNCTION hybrid_search(
  query_text text,
  query_embedding vector(1024),
  match_count int DEFAULT 10,
  keyword_weight float DEFAULT 0.3,
  semantic_weight float DEFAULT 0.7
) RETURNS TABLE (id int, title text, score float) AS $$
  -- Combines FTS rank + vector cosine similarity
  -- Exposed as RPC via PostgREST: /rpc/hybrid_search
$$ LANGUAGE sql;
```

### 1B.5 Embedding Provider
- **Voyage AI** `voyage-3.5` (1024 dims, 32K context)
- API key stored as Supabase environment variable (`VOYAGE_API_KEY`)
- Edge Function calls `https://api.voyageai.com/v1/embeddings`

---

## Phase 1C: Rendering Updates

### Hybrid Rendering Strategy
| Page | Current | Target |
|------|---------|--------|
| Digest list `/` | SSG | ISR (revalidate on new content) |
| Digest detail `/d/[slug]` | SSG | SSG (no change — content is static) |
| Actions `/actions` | N/A (new) | Server Components (dynamic) |
| Search | N/A (new) | Server Components (dynamic) |

### Keep Existing SSG Flow
The git-push → Vercel SSG flow for digest pages stays. Adding Supabase access doesn't replace it — it supplements it with dynamic features.

---

## Sequencing

```
Week 1: Foundation
  ├── 0.1 RLS policies (SQL, 30 min)
  ├── 0.2 Vercel env vars (dashboard, 10 min)
  ├── 0.3 @supabase/ssr setup in aicos-digests
  ├── 0.4 Delete Oregon project
  └── Verify: Server Component can read actions_queue from Supabase

Week 2: Action Triage
  ├── /actions page (list + filters + sort)
  ├── Server Actions (triage, rate, defer)
  ├── Realtime subscription (live new actions)
  └── Related Actions on digest pages

Week 3: Semantic Search Foundation
  ├── 1B.1 Vector columns (SQL)
  ├── 1B.2 Auto Embeddings pipeline (extensions + trigger + Edge Function)
  ├── 1B.3 FTS indexes (SQL)
  ├── 1B.4 Hybrid search function (SQL)
  └── 1B.5 Backfill: embed existing 22 digests + 8 thesis threads

Week 4: Polish + Ship
  ├── Search UI on WebFront (if Phase 2 is next)
  ├── Mobile-responsive action triage
  ├── Verify agent pipeline still works (zero agent changes needed)
  └── Ship to production
```

---

## Success Criteria

- [ ] Actions visible on digest.wiki/actions with live updates
- [ ] Accept/Dismiss works, outcome data flows to action_outcomes
- [ ] All content_digests and thesis_threads have embeddings
- [ ] `SELECT * FROM hybrid_search('agentic AI infrastructure', $embedding, 5)` returns relevant results
- [ ] Zero agent code changes — agents write to Postgres as usual, everything else is infrastructure
