# IRGI Phase A: Edge Functions for Auto-Embeddings + Hybrid Search

**Date:** 2026-03-20
**Status:** Ready for deployment review
**Project:** AI CoS (llfkxnsfczludgigknbs, ap-south-1 Mumbai, PG17)

---

## Architecture

```
                    EMBEDDING PIPELINE (automatic, invisible)
                    =========================================

  Agent writes content        Postgres triggers          pgmq queue
  ┌──────────────┐          ┌──────────────┐         ┌──────────────┐
  │ INSERT/UPDATE ├─────────►│ queue_embed  ├─────────►│ embedding_   │
  │ on any table  │          │ trigger      │         │ jobs queue   │
  └──────────────┘          └──────────────┘         └──────┬───────┘
                                                            │
                                                            │ pg_cron (every 10s)
                                                            │ calls process_embeddings()
                                                            ▼
                                                     ┌──────────────┐
                                                     │ pg_net HTTP  │
                                                     │ POST to Edge │
                                                     │ Function     │
                                                     └──────┬───────┘
                                                            │
                                                            ▼
  ┌──────────────┐          ┌──────────────┐         ┌──────────────┐
  │ Embedding    │◄─────────│ Voyage AI    │◄────────│ embed Edge   │
  │ written back │          │ voyage-3.5   │         │ Function     │
  │ to row       │          │ 1024 dims    │         │ (Deno)       │
  └──────────────┘          └──────────────┘         └──────────────┘


                    SEARCH PIPELINE (on-demand, WebFront)
                    =====================================

  WebFront / Client          Edge Function             Postgres
  ┌──────────────┐          ┌──────────────┐         ┌──────────────┐
  │ POST /search ├──────────►│ search Edge  ├─────┐   │              │
  │ {query: ...} │          │ Function     │     │   │ hybrid_      │
  └──────────────┘          └──────┬───────┘     │   │ search()     │
                                   │             │   │ SQL function │
                            Voyage AI embeds     └──►│              │
                            query text                │ RRF ranking │
                                                     │ across 4    │
                            ◄─────────────────────────│ tables      │
                            ranked results            └──────────────┘
```

---

## Edge Functions

### 1. `embed` -- Auto-Embedding Worker

**Path:** `supabase/functions/embed/index.ts`
**Runtime:** Deno (Supabase Edge Functions)
**Trigger:** pg_cron -> pg_net -> HTTP POST (internal, no JWT)

#### Request

```http
POST /functions/v1/embed
Content-Type: application/json
Authorization: Bearer <service_role_key>  (provided by pg_net from Vault)

[
  {
    "jobId": 42,
    "id": 7,
    "schema": "public",
    "table": "content_digests",
    "contentFunction": "embedding_input_content_digests",
    "embeddingColumn": "embedding"
  }
]
```

#### Response

```json
{
  "completedJobs": [
    { "jobId": 42, "id": 7, "schema": "public", "table": "content_digests", ... }
  ],
  "failedJobs": [
    { "jobId": 43, "id": 8, ..., "error": "Row not found: public.content_digests/8" }
  ]
}
```

**Headers:**
- `x-completed-jobs: 1`
- `x-failed-jobs: 1`

#### Behavior

| Scenario | Behavior |
|----------|----------|
| Empty content | Skips embedding, deletes job from queue |
| Row not found | Fails job with error message |
| Content not string | Fails job with type error |
| Text > 120K chars | Truncates to 120K before sending to Voyage AI |
| Voyage AI 429 | Stops batch early, marks remaining as rate-limited |
| Worker terminating | Marks all remaining pending jobs as failed |
| Missing API key | Fails with descriptive error |
| Invalid identifiers | Rejects with SQL injection protection |

#### Health Check

```http
GET /functions/v1/embed
```
Returns: `{ "status": "ok", "function": "embed", "model": "voyage-3.5", "hasApiKey": true }`

---

### 2. `search` -- Hybrid Search API

**Path:** `supabase/functions/search/index.ts`
**Runtime:** Deno (Supabase Edge Functions)
**Trigger:** HTTP POST from WebFront or any client (JWT required)

#### Request

```http
POST /functions/v1/search
Content-Type: application/json
Authorization: Bearer <anon_key>

{
  "query": "agentic AI infrastructure for fintech",
  "tables": ["content_digests", "thesis_threads"],
  "status": "published",
  "date_from": "2026-03-01T00:00:00Z",
  "date_to": "2026-03-20T23:59:59Z",
  "thesis_id": 3,
  "limit": 10,
  "semantic_weight": 0.7,
  "keyword_weight": 0.3
}
```

**All fields except `query` are optional.**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | string | (required) | Search text (1-10,000 chars) |
| `tables` | string[] | all 4 tables | Restrict to specific tables |
| `status` | string | null | Filter by status column |
| `date_from` | ISO datetime | null | Created at >= this |
| `date_to` | ISO datetime | null | Created at <= this |
| `thesis_id` | int | null | Filter for thesis-related results |
| `limit` | int | 20 | Max results (1-50) |
| `semantic_weight` | float | 0.7 | Weight for vector similarity (0-1) |
| `keyword_weight` | float | 0.3 | Weight for FTS/BM25 (0-1) |

#### Response

```json
{
  "query": "agentic AI infrastructure for fintech",
  "results": [
    {
      "source_table": "content_digests",
      "record_id": 12,
      "title": "Building AI Agent Infrastructure",
      "snippet": "YouTube channel analysis...",
      "semantic_rank": 1,
      "keyword_rank": 3,
      "semantic_score": 0.87,
      "keyword_score": 0.42,
      "combined_score": 0.0147
    }
  ],
  "total": 8,
  "timing_ms": 340,
  "filters": {
    "tables": ["content_digests", "thesis_threads"],
    "status": "published",
    "date_from": "2026-03-01T00:00:00Z",
    "date_to": null
  }
}
```

**Headers:**
- `x-timing-ms: 340`
- `x-result-count: 8`

#### Error Responses

| Status | When |
|--------|------|
| 400 | Invalid JSON, missing query, bad parameter types |
| 405 | Non-POST method (except OPTIONS for CORS and GET for health) |
| 429 | Voyage AI rate limited |
| 500 | DB error, Voyage AI error, unexpected failure |

#### CORS

The search function includes CORS headers (`Access-Control-Allow-Origin: *`) for browser access from WebFront. Tighten to `https://digest.wiki` in production if needed.

---

## Deployment

### Prerequisites

1. **Supabase CLI**: `brew install supabase/tap/supabase`
2. **Login**: `supabase login`
3. **Voyage AI API key**: From [dash.voyageai.com](https://dash.voyageai.com/api-keys)

### Deploy Commands

```bash
# Deploy both functions + set secrets (interactive)
./supabase/deploy-functions.sh --set-secrets

# Deploy functions only (secrets already set)
./supabase/deploy-functions.sh

# Check deployed function status
./supabase/deploy-functions.sh --status

# Set/update secrets only
./supabase/deploy-functions.sh --secrets-only
```

### Post-Deployment Steps

1. **Add project URL to Vault** (run in SQL Editor, once):
   ```sql
   SELECT vault.create_secret(
     'https://llfkxnsfczludgigknbs.supabase.co',
     'project_url'
   );
   ```

2. **Run the SQL migration** (`sql/irgi-phase-a.sql`) to create:
   - Vector columns, indexes, triggers, pgmq queue, pg_cron job, hybrid_search function

3. **Backfill existing rows**:
   ```sql
   SELECT * FROM util.backfill_embeddings();
   ```

4. **Verify embeddings** (wait ~30s after backfill):
   ```sql
   SELECT id, title, embedding IS NOT NULL AS has_embedding
   FROM content_digests;
   ```

5. **Test search**:
   ```bash
   curl -X POST 'https://llfkxnsfczludgigknbs.supabase.co/functions/v1/search' \
     -H 'Authorization: Bearer <anon-key>' \
     -H 'Content-Type: application/json' \
     -d '{"query": "agentic AI infrastructure"}'
   ```

### JWT Configuration

| Function | JWT Required | Reason |
|----------|-------------|--------|
| `embed` | No (`--no-verify-jwt`) | Called by pg_net from Postgres internals |
| `search` | Yes | Called by external clients (WebFront) |

---

## Searchable Tables

| Table | Rows (current) | Embedding Input | FTS Columns |
|-------|----------------|-----------------|-------------|
| `content_digests` | ~22 | title + channel + type + essence_notes + thesis_connections + proposed_actions + contra_signals + rabbit_holes | title, channel, content_type |
| `thesis_threads` | ~8 | thread_name + core_thesis + evidence_for/against + key_companies + investment_implications + key_questions | thread_name, core_thesis, key_companies, investment_implications |
| `actions_queue` | ~115 | action + action_type + reasoning + thesis_connection + source_content | action, reasoning, thesis_connection, action_type |
| `companies` | ~0 | name + sector + deal_status + jtbd + agent_ids_notes | name, sector, agent_ids_notes, jtbd |

---

## Ranking: Reciprocal Rank Fusion (RRF)

The hybrid_search function uses RRF to combine vector similarity and FTS keyword scores:

```
combined_score = semantic_weight * (1 / (k + semantic_rank))
               + keyword_weight * (1 / (k + keyword_rank))
```

Where `k = 60` (standard RRF constant). This normalizes scores from different ranking systems (cosine similarity vs BM25 tf-idf) into a unified ranking by position rather than raw score value.

Default weights: 70% semantic, 30% keyword. Adjustable per query.

---

## Cost Estimates

### Voyage AI Pricing (as of March 2026)

| Item | Rate |
|------|------|
| Embedding API | $0.06 per 1M tokens |
| Rate limits | 300 RPM, 1M tokens/min |

### Estimated Costs for AI CoS

| Operation | Tokens (est.) | Cost |
|-----------|---------------|------|
| Initial backfill (145 rows) | ~100K tokens | $0.006 |
| Daily new content (~5 rows) | ~3K tokens | $0.0002 |
| Search queries (50/day) | ~5K tokens | $0.0003 |
| **Monthly total** | ~200K tokens | **~$0.02** |

Voyage AI is extremely cost-effective for this scale. Even at 10x growth (1,450 rows, 500 searches/day), monthly cost stays under $0.50.

### Supabase Edge Function Costs

Edge Functions are included in the Supabase Pro plan. The embed function runs on a 10-second cron schedule but only does work when the pgmq queue has jobs. Empty polls are essentially free (no Voyage AI calls, minimal DB query).

---

## Testing Plan

### Unit Tests (pre-deployment)

1. **Schema validation**: Send malformed JSON to both functions, verify 400 responses
2. **Empty batch**: POST `[]` to embed, verify empty success response
3. **Missing API key**: Unset VOYAGE_API_KEY, verify descriptive error

### Integration Tests (post-deployment)

1. **Embed pipeline end-to-end**:
   - Insert a row into content_digests
   - Wait 15 seconds (pg_cron interval + processing time)
   - Verify embedding column is NOT NULL
   - Verify embedding is 1024 dimensions: `SELECT array_length(embedding::float[], 1) FROM content_digests WHERE id = <new_id>`

2. **Embedding update on content change**:
   - Update the title of an existing content_digest
   - Verify embedding is immediately NULL (clear trigger fired)
   - Wait 15 seconds
   - Verify new embedding is generated

3. **Search function**:
   - POST a query to search function
   - Verify response has expected shape (results array, timing_ms, etc.)
   - Verify results are sorted by combined_score descending
   - Test with table filter: `{"query": "AI", "tables": ["thesis_threads"]}`
   - Test with date filter: verify only matching rows returned

4. **Error handling**:
   - Search with empty query: expect 400
   - Search with invalid table name: expect 400
   - Verify CORS headers present on all responses

5. **Rate limit behavior**:
   - Backfill all rows simultaneously
   - Monitor Edge Function logs for rate limit handling
   - Verify jobs are retried on next pg_cron cycle

### Smoke Test Script

```bash
# After deployment, run from Mac:
SUPABASE_URL="https://llfkxnsfczludgigknbs.supabase.co"
ANON_KEY="<your-anon-key>"

# 1. Health check - embed
curl -s "${SUPABASE_URL}/functions/v1/embed" | jq .

# 2. Health check - search
curl -s -H "Authorization: Bearer ${ANON_KEY}" \
  "${SUPABASE_URL}/functions/v1/search" | jq .

# 3. Test search
curl -s -X POST "${SUPABASE_URL}/functions/v1/search" \
  -H "Authorization: Bearer ${ANON_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"query": "AI infrastructure investment thesis", "limit": 5}' | jq .
```

---

## File Inventory

| File | Purpose |
|------|---------|
| `supabase/functions/embed/index.ts` | Embedding worker Edge Function |
| `supabase/functions/embed/.env.example` | Environment variable template |
| `supabase/functions/search/index.ts` | Hybrid search API Edge Function |
| `supabase/deploy-functions.sh` | Deployment script (both functions + secrets) |
| `sql/irgi-phase-a.sql` | SQL migration (extensions, triggers, queue, hybrid_search) |
| `sql/irgi-edge-function.ts` | Original edge function draft (superseded by supabase/functions/embed/) |
