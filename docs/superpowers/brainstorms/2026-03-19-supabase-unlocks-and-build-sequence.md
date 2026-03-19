# Supabase Unlocks: Analysis & Revised Build Sequence
*2026-03-19 — Post-migration capability assessment*

---

## Architectural Constraint

**Agents are the orchestration layer.** Supabase extensions (pgmq, pg_cron, pg_net) are used ONLY as invisible infrastructure for Auto Embeddings. Agents never interact with queue functions, cron jobs, or HTTP triggers directly. They write content to Postgres as usual; embeddings appear automatically. The database is storage + search, not orchestration.

---

## 1. Auto Embeddings: Complementary to IRGI, Not Conflicting

### IRGI Phases (unchanged)
- **Phase A:** Hybrid Search (pgvector + FTS + reranking) — **accelerated by Auto Embeddings**
- **Phase B:** QMD Cloud — already deployed, independent
- **Phase C:** Temporal Graph (Neo4j/Graphiti) — separate service, unaffected
- **Phase D:** Query Router — orchestration logic, unaffected
- **Phase E:** RL Infrastructure — action_outcomes table, unaffected

### What Auto Embeddings Does
DB trigger on content_digests/thesis_threads INSERT/UPDATE → pgmq queue → pg_cron batches → Edge Function calls Voyage AI → vector column populated. All invisible to agents.

### Why It Fits
- Agents write content normally (psql INSERT/UPDATE) — zero changes
- Embeddings appear automatically — no agent context wasted on mechanical embedding work
- Agents search with simple SQL: `ORDER BY embedding <=> query_vector LIMIT 10`
- Doesn't touch FTS, reranking, or graph — those remain as IRGI planned
- pgmq retry semantics handle transient Voyage AI API failures

### Embedding Provider: Voyage AI
- Anthropic does NOT have a native embedding model
- Voyage AI `voyage-3.5` — 1024 dims, 32K context, Anthropic-recommended
- API key stored as Supabase environment variable
- Edge Function calls `https://api.voyageai.com/v1/embeddings`

### IRGI Phase A Glide Path
1. Vector columns on content_digests + thesis_threads (1024 dims)
2. Auto Embeddings pipeline (trigger + pgmq + cron + Edge Function + Voyage AI)
3. FTS tsvector columns + GIN indexes
4. Hybrid search SQL function (vector similarity + BM25)
5. Backfill existing 22 digests + 8 thesis threads
6. Phase C (Neo4j) proceeds independently whenever ready

---

## 2. PostgREST + Realtime: Already the Implementation Pattern

Not a separate unlock — it's HOW WebFront gets built. `@supabase/ssr` uses PostgREST under the hood. Realtime streams DB changes to the browser.

**PostgREST:** Every table instantly accessible via REST. Server Components read data. Server Actions write data. Zero custom API routes.

**Realtime:** New actions, thesis updates, pipeline status stream live to WebFront. Agents write to Postgres as usual — Realtime broadcasts the changes automatically.

**Prerequisite:** RLS policies (grant `service_role` access). One-time SQL.

**Build sequence impact:** None — this is how Phase 1 works, not a separate task.

---

## 3. Supabase Storage: Deferred to Phase 2.5

Current filesystem → git push → Vercel SSG works reliably. Moving to Storage requires rewriting the publishing pipeline. Not urgent.

Becomes relevant when WebFront Phase 2 is already reading from Supabase for thesis/actions — at that point, migrating digest data too is natural.

---

## 4. Revised Near-Term Build Sequence

### Completed
- [x] Supabase migration (Mumbai, ap-south-1, 31ms)
- [x] Post-migration audit (9 findings, 3 fixed)
- [x] Audit fixes (connection.py hardening, skill doc schema drift, NULL sequences)

### Next: WebFront Phase 1 (Action Triage + IRGI Phase A Foundation)
Full plan: `docs/superpowers/plans/2026-03-19-webfront-phase1-execution.md`

**Week 1 — Foundation:**
- RLS policies (SQL, 30 min)
- Vercel env vars (Supabase URL + keys)
- `@supabase/ssr` setup in aicos-digests
- Delete Oregon Supabase project

**Week 2 — Action Triage:**
- `/actions` page (list + filters + sort)
- Server Actions (triage, rate, defer)
- Realtime subscription (live new actions)
- Related Actions on digest pages

**Week 3 — Semantic Search Foundation:**
- Vector columns (SQL)
- Auto Embeddings pipeline (extensions + trigger + Edge Function + Voyage AI)
- FTS indexes (SQL)
- Hybrid search function (SQL)
- Backfill existing data

**Week 4 — Polish + Ship**

### Then: WebFront Phase 2 (Thesis Interaction)
- Thesis dashboard, evidence timeline, conviction viz
- Semantic search in action: "find digests related to this thesis"

### Then: Phase 2.5 (Storage, if needed)
### Then: Phase 3-4 (Pipeline Status, Agent Messaging)

### Separate Track:
- IRGI Phase C: Neo4j/Graphiti (when ready)
- Phase 6: Decommission droplet Postgres (1-2 weeks monitoring)
