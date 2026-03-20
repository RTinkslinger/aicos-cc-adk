-- =============================================================================
-- IRGI Phase A: Hybrid Search Infrastructure
-- =============================================================================
-- Project: AI CoS (llfkxnsfczludgigknbs, ap-south-1 Mumbai, PG17)
-- Embedding model: Voyage AI voyage-3.5 (1024 dimensions)
-- Date prepared: 2026-03-20
-- Status: EXECUTED 2026-03-20 via Supabase MCP (7 batches, all verified)
--
-- This migration adds:
--   1. Required extensions (pgmq, pg_net, pg_cron, hstore)
--   2. Utility schema + functions (project URL, Edge Function invoker, column clearer)
--   3. Vault secret for project URL
--   4. Vector columns on 4 tables (content_digests, thesis_threads, actions_queue, companies)
--   5. HNSW indexes on vector columns
--   6. Full-text search tsvector columns + GIN indexes on 4 tables
--   7. Embedding queue + triggers (pgmq-based auto embedding pipeline)
--   8. pg_cron scheduled job for embedding processing
--   9. Hybrid search SQL function (vector + FTS + metadata filters)
--  10. Backfill helper to queue existing rows for embedding
--
-- Architectural constraint: Agents are pure consumers. They write content normally
-- via psql INSERT/UPDATE. Embeddings appear automatically via the invisible
-- trigger -> pgmq -> pg_cron -> Edge Function -> Voyage AI pipeline.
-- =============================================================================


-- =============================================================================
-- SECTION 1: Enable Required Extensions
-- =============================================================================
-- pgvector 0.8.0 already enabled in `extensions` schema. No action needed.
-- The following 4 extensions are new.

-- pgmq: Message queue for embedding job processing
CREATE EXTENSION IF NOT EXISTS pgmq;

-- pg_net: Async HTTP calls from Postgres to Edge Functions
CREATE EXTENSION IF NOT EXISTS pg_net
  WITH SCHEMA extensions;

-- pg_cron: Scheduled job processing for embedding queue
CREATE EXTENSION IF NOT EXISTS pg_cron;

-- hstore: Used by util.clear_column() to NULL out embedding on content update
CREATE EXTENSION IF NOT EXISTS hstore
  WITH SCHEMA extensions;


-- =============================================================================
-- SECTION 2: Utility Schema + Functions
-- =============================================================================
-- Following the official Supabase Auto Embeddings pattern.
-- These are generic helpers reusable across any table.

CREATE SCHEMA IF NOT EXISTS util;

-- Retrieve the Supabase project URL from Vault (needed for Edge Function invocation)
CREATE OR REPLACE FUNCTION util.project_url()
RETURNS text
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  secret_value text;
BEGIN
  SELECT decrypted_secret INTO secret_value
  FROM vault.decrypted_secrets
  WHERE name = 'project_url';
  RETURN secret_value;
END;
$$;

-- Generic Edge Function invoker via pg_net async HTTP POST
CREATE OR REPLACE FUNCTION util.invoke_edge_function(
  name text,
  body jsonb,
  timeout_milliseconds int DEFAULT 5 * 60 * 1000  -- 5 minute default
)
RETURNS void
LANGUAGE plpgsql
AS $$
DECLARE
  headers_raw text;
  auth_header text;
BEGIN
  -- If in a PostgREST session, reuse request headers for authorization
  headers_raw := current_setting('request.headers', true);

  auth_header := CASE
    WHEN headers_raw IS NOT NULL THEN
      (headers_raw::json->>'authorization')
    ELSE
      NULL
  END;

  -- Async HTTP POST to the Edge Function
  PERFORM net.http_post(
    url => util.project_url() || '/functions/v1/' || name,
    headers => jsonb_build_object(
      'Content-Type', 'application/json',
      'Authorization', auth_header
    ),
    body => body,
    timeout_milliseconds => timeout_milliseconds
  );
END;
$$;

-- Generic trigger function to clear a column on UPDATE (used to invalidate
-- stale embeddings when content changes, before the new embedding is generated)
CREATE OR REPLACE FUNCTION util.clear_column()
RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE
  clear_column text := TG_ARGV[0];
BEGIN
  NEW := NEW #= extensions.hstore(clear_column, NULL);
  RETURN NEW;
END;
$$;


-- =============================================================================
-- SECTION 3: Vault Secret for Project URL
-- =============================================================================
-- IMPORTANT: Run this separately in the SQL Editor (not in a migration file).
-- Replace with the actual project URL from Supabase Dashboard > Settings > API.
--
-- SELECT vault.create_secret(
--   'https://llfkxnsfczludgigknbs.supabase.co',
--   'project_url'
-- );
--
-- This is commented out because vault.create_secret is not idempotent and
-- will error if the secret already exists. Execute manually once.


-- =============================================================================
-- SECTION 4: Vector Columns (1024 dims for Voyage AI voyage-3.5)
-- =============================================================================
-- Using vector(1024) not halfvec because Voyage AI outputs float32 and
-- 1024 dims at full precision is only ~4KB per row. With 22 digests +
-- 8 theses + 115 actions + 0 companies = ~145 rows, space is not a concern.
-- Can switch to halfvec(1024) later if row counts grow to 100K+.

-- 4a. content_digests: Primary search target (22 rows)
-- Rich content: title + channel + essence notes + thesis connections
ALTER TABLE content_digests
  ADD COLUMN IF NOT EXISTS embedding vector(1024);

-- 4b. thesis_threads: Second search target (8 rows)
-- Rich content: thread_name + core_thesis + evidence_for + evidence_against
ALTER TABLE thesis_threads
  ADD COLUMN IF NOT EXISTS embedding vector(1024);

-- 4c. actions_queue: Third search target (115 rows)
-- Content: action text + reasoning + thesis_connection
ALTER TABLE actions_queue
  ADD COLUMN IF NOT EXISTS embedding vector(1024);

-- 4d. companies: Future search target (0 rows currently, but schema ready)
-- Content: name + sector + agent_ids_notes + jtbd
ALTER TABLE companies
  ADD COLUMN IF NOT EXISTS embedding vector(1024);

-- NOTE: network table is excluded for now (0 rows, less text content for
-- meaningful embeddings). Can be added later with minimal effort.


-- =============================================================================
-- SECTION 5: HNSW Indexes on Vector Columns
-- =============================================================================
-- Using HNSW (not IVFFlat) because:
--   - Better recall at low row counts (<10K)
--   - No training step needed (IVFFlat needs representative data first)
--   - Cosine distance (<=>) matches Voyage AI's default similarity metric
--
-- HNSW index parameters left at defaults (m=16, ef_construction=64) which
-- are suitable for <10K rows. Tune if row count exceeds 100K.

CREATE INDEX IF NOT EXISTS idx_content_digests_embedding
  ON content_digests
  USING hnsw (embedding vector_cosine_ops);

CREATE INDEX IF NOT EXISTS idx_thesis_threads_embedding
  ON thesis_threads
  USING hnsw (embedding vector_cosine_ops);

CREATE INDEX IF NOT EXISTS idx_actions_queue_embedding
  ON actions_queue
  USING hnsw (embedding vector_cosine_ops);

CREATE INDEX IF NOT EXISTS idx_companies_embedding
  ON companies
  USING hnsw (embedding vector_cosine_ops);


-- =============================================================================
-- SECTION 6: Full-Text Search (tsvector + GIN indexes)
-- =============================================================================
-- Generated columns auto-maintain the tsvector when source columns change.
-- GIN indexes enable fast BM25-style keyword search.
-- Combined with vector search in the hybrid_search function (Section 9).

-- 6a. content_digests: title + channel + content_type
-- Note: digest_data (JSONB) contains rich text but GENERATED columns cannot
-- reference JSONB path expressions dynamically. We index the top-level columns
-- and handle digest_data search via the embedding (semantic) path instead.
ALTER TABLE content_digests
  ADD COLUMN IF NOT EXISTS fts tsvector
  GENERATED ALWAYS AS (
    to_tsvector('english',
      coalesce(title, '') || ' ' ||
      coalesce(channel, '') || ' ' ||
      coalesce(content_type, '')
    )
  ) STORED;

CREATE INDEX IF NOT EXISTS idx_content_digests_fts
  ON content_digests USING gin(fts);

-- 6b. thesis_threads: thread_name + core_thesis + key_companies + investment_implications
ALTER TABLE thesis_threads
  ADD COLUMN IF NOT EXISTS fts tsvector
  GENERATED ALWAYS AS (
    to_tsvector('english',
      coalesce(thread_name, '') || ' ' ||
      coalesce(core_thesis, '') || ' ' ||
      coalesce(key_companies, '') || ' ' ||
      coalesce(investment_implications, '')
    )
  ) STORED;

CREATE INDEX IF NOT EXISTS idx_thesis_threads_fts
  ON thesis_threads USING gin(fts);

-- 6c. actions_queue: action + reasoning + thesis_connection + action_type
ALTER TABLE actions_queue
  ADD COLUMN IF NOT EXISTS fts tsvector
  GENERATED ALWAYS AS (
    to_tsvector('english',
      coalesce(action, '') || ' ' ||
      coalesce(reasoning, '') || ' ' ||
      coalesce(thesis_connection, '') || ' ' ||
      coalesce(action_type, '')
    )
  ) STORED;

CREATE INDEX IF NOT EXISTS idx_actions_queue_fts
  ON actions_queue USING gin(fts);

-- 6d. companies: name + sector + agent_ids_notes
-- Note: jtbd is TEXT[] and array_to_string() is not IMMUTABLE in PG17, so it
-- cannot be used in a GENERATED ALWAYS column. jtbd is covered by the embedding
-- (semantic) path via embedding_input_companies() instead.
ALTER TABLE companies
  ADD COLUMN IF NOT EXISTS fts tsvector
  GENERATED ALWAYS AS (
    to_tsvector('english',
      coalesce(name, '') || ' ' ||
      coalesce(sector, '') || ' ' ||
      coalesce(agent_ids_notes, '')
    )
  ) STORED;

CREATE INDEX IF NOT EXISTS idx_companies_fts
  ON companies USING gin(fts);


-- =============================================================================
-- SECTION 7: Embedding Queue + Trigger Infrastructure
-- =============================================================================
-- Following the official Supabase Auto Embeddings pattern:
-- INSERT/UPDATE -> trigger -> pgmq queue -> pg_cron batch -> Edge Function -> Voyage AI

-- 7a. Create the pgmq queue for embedding jobs
SELECT pgmq.create('embedding_jobs');

-- 7b. Generic trigger function to enqueue embedding jobs
-- Accepts: content_function name (SQL function returning text for embedding input)
--          embedding_column name (destination column for the vector)
CREATE OR REPLACE FUNCTION util.queue_embeddings()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
DECLARE
  content_function text = TG_ARGV[0];
  embedding_column text = TG_ARGV[1];
BEGIN
  PERFORM pgmq.send(
    queue_name => 'embedding_jobs',
    msg => jsonb_build_object(
      'id', NEW.id,
      'schema', TG_TABLE_SCHEMA,
      'table', TG_TABLE_NAME,
      'contentFunction', content_function,
      'embeddingColumn', embedding_column
    )
  );
  RETURN NEW;
END;
$$;

-- 7c. Process embedding jobs from queue in batches via Edge Function
CREATE OR REPLACE FUNCTION util.process_embeddings(
  batch_size int DEFAULT 10,
  max_requests int DEFAULT 10,
  timeout_milliseconds int DEFAULT 5 * 60 * 1000  -- 5 min
)
RETURNS void
LANGUAGE plpgsql
AS $$
DECLARE
  job_batches jsonb[];
  batch jsonb;
BEGIN
  WITH
    numbered_jobs AS (
      SELECT
        message || jsonb_build_object('jobId', msg_id) AS job_info,
        (row_number() OVER (ORDER BY 1) - 1) / batch_size AS batch_num
      FROM pgmq.read(
        queue_name => 'embedding_jobs',
        vt => timeout_milliseconds / 1000,
        qty => max_requests * batch_size
      )
    ),
    batched_jobs AS (
      SELECT
        jsonb_agg(job_info) AS batch_array,
        batch_num
      FROM numbered_jobs
      GROUP BY batch_num
    )
  SELECT array_agg(batch_array)
  FROM batched_jobs
  INTO job_batches;

  -- Nothing to process
  IF job_batches IS NULL THEN
    RETURN;
  END IF;

  -- Invoke the embed Edge Function for each batch
  FOREACH batch IN ARRAY job_batches LOOP
    PERFORM util.invoke_edge_function(
      name => 'embed',
      body => batch,
      timeout_milliseconds => timeout_milliseconds
    );
  END LOOP;
END;
$$;

-- 7d. Schedule embedding processing every 10 seconds
SELECT cron.schedule(
  'process-embeddings',
  '10 seconds',
  $$SELECT util.process_embeddings();$$
);


-- =============================================================================
-- SECTION 7e: Content Input Functions (per-table)
-- =============================================================================
-- Each function defines WHAT text gets embedded for a given table row.
-- These are called by the Edge Function to extract content before sending
-- to Voyage AI. Design principle: include enough text for semantic meaning
-- but stay within Voyage AI's 32K token context window.

-- content_digests: Title + channel + rich analysis from digest_data JSONB
-- This concatenates the most semantically meaningful fields.
-- NOTE: Parameter name 'rec' used instead of 'row' because 'row' is a reserved
-- keyword in PG17. Original SQL had 'row' which causes syntax error 42601.
CREATE OR REPLACE FUNCTION embedding_input_content_digests(rec content_digests)
RETURNS text
LANGUAGE plpgsql
IMMUTABLE
AS $$
BEGIN
  RETURN
    '# ' || coalesce(rec.title, '') || E'\n' ||
    'Channel: ' || coalesce(rec.channel, '') || E'\n' ||
    'Type: ' || coalesce(rec.content_type, '') || E'\n\n' ||
    coalesce(rec.digest_data->>'essence_notes', '') || E'\n\n' ||
    'Thesis connections: ' || coalesce(rec.digest_data->>'thesis_connections', '') || E'\n' ||
    'Proposed actions: ' || coalesce(rec.digest_data->>'proposed_actions', '') || E'\n' ||
    'Contra signals: ' || coalesce(rec.digest_data->>'contra_signals', '') || E'\n' ||
    'Rabbit holes: ' || coalesce(rec.digest_data->>'rabbit_holes', '');
END;
$$;

-- thesis_threads: Name + core thesis + evidence + questions + implications
CREATE OR REPLACE FUNCTION embedding_input_thesis_threads(rec thesis_threads)
RETURNS text
LANGUAGE plpgsql
IMMUTABLE
AS $$
BEGIN
  RETURN
    '# ' || coalesce(rec.thread_name, '') || E'\n\n' ||
    coalesce(rec.core_thesis, '') || E'\n\n' ||
    'Evidence for: ' || coalesce(rec.evidence_for, '') || E'\n' ||
    'Evidence against: ' || coalesce(rec.evidence_against, '') || E'\n' ||
    'Key companies: ' || coalesce(rec.key_companies, '') || E'\n' ||
    'Investment implications: ' || coalesce(rec.investment_implications, '') || E'\n' ||
    'Key questions: ' || coalesce(rec.key_questions_json::text, '');
END;
$$;

-- actions_queue: Action text + reasoning + thesis connection + type
CREATE OR REPLACE FUNCTION embedding_input_actions_queue(rec actions_queue)
RETURNS text
LANGUAGE plpgsql
IMMUTABLE
AS $$
BEGIN
  RETURN
    coalesce(rec.action, '') || E'\n\n' ||
    'Type: ' || coalesce(rec.action_type, '') || E'\n' ||
    'Reasoning: ' || coalesce(rec.reasoning, '') || E'\n' ||
    'Thesis connection: ' || coalesce(rec.thesis_connection, '') || E'\n' ||
    'Source: ' || coalesce(rec.source_content, '');
END;
$$;

-- companies: Name + sector + JTBD + agent IDS notes
CREATE OR REPLACE FUNCTION embedding_input_companies(rec companies)
RETURNS text
LANGUAGE plpgsql
IMMUTABLE
AS $$
BEGIN
  RETURN
    '# ' || coalesce(rec.name, '') || E'\n' ||
    'Sector: ' || coalesce(rec.sector, '') || E'\n' ||
    'Deal status: ' || coalesce(rec.deal_status, '') || E'\n' ||
    'JTBD: ' || coalesce(array_to_string(rec.jtbd, ', '), '') || E'\n' ||
    'IDS Notes: ' || coalesce(rec.agent_ids_notes, '');
END;
$$;


-- =============================================================================
-- SECTION 7f: Table-Specific Triggers
-- =============================================================================
-- Each table gets 3 triggers:
--   1. AFTER INSERT -> queue embedding job
--   2. AFTER UPDATE of content columns -> queue embedding job
--   3. BEFORE UPDATE of content columns -> clear stale embedding (optional safety)
--
-- The "clear on update" triggers ensure stale embeddings don't pollute search
-- results while the new embedding is being generated (10-30s lag).

-- ---- content_digests triggers ----

CREATE OR REPLACE TRIGGER embed_content_digests_on_insert
  AFTER INSERT ON content_digests
  FOR EACH ROW
  EXECUTE FUNCTION util.queue_embeddings('embedding_input_content_digests', 'embedding');

CREATE OR REPLACE TRIGGER embed_content_digests_on_update
  AFTER UPDATE OF title, channel, content_type, digest_data ON content_digests
  FOR EACH ROW
  EXECUTE FUNCTION util.queue_embeddings('embedding_input_content_digests', 'embedding');

CREATE OR REPLACE TRIGGER clear_content_digests_embedding_on_update
  BEFORE UPDATE OF title, channel, content_type, digest_data ON content_digests
  FOR EACH ROW
  EXECUTE FUNCTION util.clear_column('embedding');

-- ---- thesis_threads triggers ----

CREATE OR REPLACE TRIGGER embed_thesis_threads_on_insert
  AFTER INSERT ON thesis_threads
  FOR EACH ROW
  EXECUTE FUNCTION util.queue_embeddings('embedding_input_thesis_threads', 'embedding');

CREATE OR REPLACE TRIGGER embed_thesis_threads_on_update
  AFTER UPDATE OF thread_name, core_thesis, evidence_for, evidence_against, key_companies, investment_implications, key_questions_json ON thesis_threads
  FOR EACH ROW
  EXECUTE FUNCTION util.queue_embeddings('embedding_input_thesis_threads', 'embedding');

CREATE OR REPLACE TRIGGER clear_thesis_threads_embedding_on_update
  BEFORE UPDATE OF thread_name, core_thesis, evidence_for, evidence_against, key_companies, investment_implications, key_questions_json ON thesis_threads
  FOR EACH ROW
  EXECUTE FUNCTION util.clear_column('embedding');

-- ---- actions_queue triggers ----

CREATE OR REPLACE TRIGGER embed_actions_queue_on_insert
  AFTER INSERT ON actions_queue
  FOR EACH ROW
  EXECUTE FUNCTION util.queue_embeddings('embedding_input_actions_queue', 'embedding');

CREATE OR REPLACE TRIGGER embed_actions_queue_on_update
  AFTER UPDATE OF action, action_type, reasoning, thesis_connection, source_content ON actions_queue
  FOR EACH ROW
  EXECUTE FUNCTION util.queue_embeddings('embedding_input_actions_queue', 'embedding');

CREATE OR REPLACE TRIGGER clear_actions_queue_embedding_on_update
  BEFORE UPDATE OF action, action_type, reasoning, thesis_connection, source_content ON actions_queue
  FOR EACH ROW
  EXECUTE FUNCTION util.clear_column('embedding');

-- ---- companies triggers ----

CREATE OR REPLACE TRIGGER embed_companies_on_insert
  AFTER INSERT ON companies
  FOR EACH ROW
  EXECUTE FUNCTION util.queue_embeddings('embedding_input_companies', 'embedding');

CREATE OR REPLACE TRIGGER embed_companies_on_update
  AFTER UPDATE OF name, sector, deal_status, jtbd, agent_ids_notes ON companies
  FOR EACH ROW
  EXECUTE FUNCTION util.queue_embeddings('embedding_input_companies', 'embedding');

CREATE OR REPLACE TRIGGER clear_companies_embedding_on_update
  BEFORE UPDATE OF name, sector, deal_status, jtbd, agent_ids_notes ON companies
  FOR EACH ROW
  EXECUTE FUNCTION util.clear_column('embedding');


-- =============================================================================
-- SECTION 8: Hybrid Search Function
-- =============================================================================
-- Combines vector similarity (cosine) + FTS BM25 relevance with configurable
-- weights. Returns unified results across all 4 searchable tables.
--
-- Called from WebFront via PostgREST RPC: POST /rest/v1/rpc/hybrid_search
-- The query_embedding parameter must be generated client-side by calling
-- Voyage AI before invoking the search (or via a server action).
--
-- Design decisions:
--   - Separate CTEs per table for clarity and maintainability
--   - UNION ALL to combine results (no dedup -- results are typed by source)
--   - Reciprocal Rank Fusion (RRF) blending of vector + FTS scores
--     RRF is more robust than raw score mixing because vector distances and
--     FTS ranks are on different scales. RRF normalizes via rank position.
--   - Optional filters: date range, status, source table, action_type

CREATE OR REPLACE FUNCTION hybrid_search(
  query_text text,                               -- User's search query (for FTS)
  query_embedding vector(1024),                  -- Pre-computed embedding of query
  match_count int DEFAULT 20,                    -- Max results to return
  keyword_weight float DEFAULT 0.3,              -- Weight for FTS component (0-1)
  semantic_weight float DEFAULT 0.7,             -- Weight for vector component (0-1)
  filter_tables text[] DEFAULT NULL,             -- Restrict to specific tables: 'content_digests', 'thesis_threads', 'actions_queue', 'companies'
  filter_status text DEFAULT NULL,               -- Filter by status (applies to tables that have status column)
  filter_date_from timestamptz DEFAULT NULL,     -- Filter: created_at >= this
  filter_date_to timestamptz DEFAULT NULL        -- Filter: created_at <= this
)
RETURNS TABLE (
  source_table text,
  record_id int,
  title text,
  snippet text,
  semantic_rank int,
  keyword_rank int,
  semantic_score float,
  keyword_score float,
  combined_score float
)
LANGUAGE plpgsql
AS $$
DECLARE
  ts_query tsquery;
  rrf_k int := 60;  -- RRF constant (standard value from literature)
BEGIN
  -- Parse the query text into a tsquery for FTS
  -- Using plainto_tsquery for robustness (handles natural language input)
  ts_query := plainto_tsquery('english', query_text);

  RETURN QUERY

  WITH
  -- =========================================
  -- Content Digests: semantic + keyword search
  -- =========================================
  cd_semantic AS (
    SELECT
      cd.id,
      cd.title AS cd_title,
      coalesce(cd.channel, '') AS cd_snippet,
      1 - (cd.embedding <=> query_embedding) AS score,
      row_number() OVER (ORDER BY cd.embedding <=> query_embedding) AS rank
    FROM content_digests cd
    WHERE cd.embedding IS NOT NULL
      AND (filter_tables IS NULL OR 'content_digests' = ANY(filter_tables))
      AND (filter_status IS NULL OR cd.status = filter_status)
      AND (filter_date_from IS NULL OR cd.created_at >= filter_date_from)
      AND (filter_date_to IS NULL OR cd.created_at <= filter_date_to)
    ORDER BY cd.embedding <=> query_embedding
    LIMIT match_count * 2  -- Overfetch for RRF blending
  ),
  cd_keyword AS (
    SELECT
      cd.id,
      cd.title AS cd_title,
      coalesce(cd.channel, '') AS cd_snippet,
      ts_rank_cd(cd.fts, ts_query) AS score,
      row_number() OVER (ORDER BY ts_rank_cd(cd.fts, ts_query) DESC) AS rank
    FROM content_digests cd
    WHERE cd.fts @@ ts_query
      AND (filter_tables IS NULL OR 'content_digests' = ANY(filter_tables))
      AND (filter_status IS NULL OR cd.status = filter_status)
      AND (filter_date_from IS NULL OR cd.created_at >= filter_date_from)
      AND (filter_date_to IS NULL OR cd.created_at <= filter_date_to)
    ORDER BY ts_rank_cd(cd.fts, ts_query) DESC
    LIMIT match_count * 2
  ),
  cd_combined AS (
    SELECT
      'content_digests'::text AS source_table,
      coalesce(s.id, k.id) AS record_id,
      coalesce(s.cd_title, k.cd_title) AS title,
      coalesce(s.cd_snippet, k.cd_snippet) AS snippet,
      s.rank::int AS semantic_rank,
      k.rank::int AS keyword_rank,
      coalesce(s.score, 0.0)::float AS semantic_score,
      coalesce(k.score, 0.0)::float AS keyword_score,
      (
        semantic_weight * coalesce(1.0 / (rrf_k + s.rank), 0.0) +
        keyword_weight * coalesce(1.0 / (rrf_k + k.rank), 0.0)
      )::float AS combined_score
    FROM cd_semantic s
    FULL OUTER JOIN cd_keyword k ON s.id = k.id
  ),

  -- =========================================
  -- Thesis Threads: semantic + keyword search
  -- =========================================
  tt_semantic AS (
    SELECT
      tt.id,
      tt.thread_name AS tt_title,
      left(coalesce(tt.core_thesis, ''), 200) AS tt_snippet,
      1 - (tt.embedding <=> query_embedding) AS score,
      row_number() OVER (ORDER BY tt.embedding <=> query_embedding) AS rank
    FROM thesis_threads tt
    WHERE tt.embedding IS NOT NULL
      AND (filter_tables IS NULL OR 'thesis_threads' = ANY(filter_tables))
      AND (filter_status IS NULL OR tt.status = filter_status)
      AND (filter_date_from IS NULL OR tt.created_at >= filter_date_from)
      AND (filter_date_to IS NULL OR tt.created_at <= filter_date_to)
    ORDER BY tt.embedding <=> query_embedding
    LIMIT match_count * 2
  ),
  tt_keyword AS (
    SELECT
      tt.id,
      tt.thread_name AS tt_title,
      left(coalesce(tt.core_thesis, ''), 200) AS tt_snippet,
      ts_rank_cd(tt.fts, ts_query) AS score,
      row_number() OVER (ORDER BY ts_rank_cd(tt.fts, ts_query) DESC) AS rank
    FROM thesis_threads tt
    WHERE tt.fts @@ ts_query
      AND (filter_tables IS NULL OR 'thesis_threads' = ANY(filter_tables))
      AND (filter_status IS NULL OR tt.status = filter_status)
      AND (filter_date_from IS NULL OR tt.created_at >= filter_date_from)
      AND (filter_date_to IS NULL OR tt.created_at <= filter_date_to)
    ORDER BY ts_rank_cd(tt.fts, ts_query) DESC
    LIMIT match_count * 2
  ),
  tt_combined AS (
    SELECT
      'thesis_threads'::text AS source_table,
      coalesce(s.id, k.id) AS record_id,
      coalesce(s.tt_title, k.tt_title) AS title,
      coalesce(s.tt_snippet, k.tt_snippet) AS snippet,
      s.rank::int AS semantic_rank,
      k.rank::int AS keyword_rank,
      coalesce(s.score, 0.0)::float AS semantic_score,
      coalesce(k.score, 0.0)::float AS keyword_score,
      (
        semantic_weight * coalesce(1.0 / (rrf_k + s.rank), 0.0) +
        keyword_weight * coalesce(1.0 / (rrf_k + k.rank), 0.0)
      )::float AS combined_score
    FROM tt_semantic s
    FULL OUTER JOIN tt_keyword k ON s.id = k.id
  ),

  -- =========================================
  -- Actions Queue: semantic + keyword search
  -- =========================================
  aq_semantic AS (
    SELECT
      aq.id,
      aq.action AS aq_title,
      coalesce(aq.action_type, '') || ': ' || left(coalesce(aq.reasoning, ''), 150) AS aq_snippet,
      1 - (aq.embedding <=> query_embedding) AS score,
      row_number() OVER (ORDER BY aq.embedding <=> query_embedding) AS rank
    FROM actions_queue aq
    WHERE aq.embedding IS NOT NULL
      AND (filter_tables IS NULL OR 'actions_queue' = ANY(filter_tables))
      AND (filter_status IS NULL OR aq.status = filter_status)
      AND (filter_date_from IS NULL OR aq.created_at >= filter_date_from)
      AND (filter_date_to IS NULL OR aq.created_at <= filter_date_to)
    ORDER BY aq.embedding <=> query_embedding
    LIMIT match_count * 2
  ),
  aq_keyword AS (
    SELECT
      aq.id,
      aq.action AS aq_title,
      coalesce(aq.action_type, '') || ': ' || left(coalesce(aq.reasoning, ''), 150) AS aq_snippet,
      ts_rank_cd(aq.fts, ts_query) AS score,
      row_number() OVER (ORDER BY ts_rank_cd(aq.fts, ts_query) DESC) AS rank
    FROM actions_queue aq
    WHERE aq.fts @@ ts_query
      AND (filter_tables IS NULL OR 'actions_queue' = ANY(filter_tables))
      AND (filter_status IS NULL OR aq.status = filter_status)
      AND (filter_date_from IS NULL OR aq.created_at >= filter_date_from)
      AND (filter_date_to IS NULL OR aq.created_at <= filter_date_to)
    ORDER BY ts_rank_cd(aq.fts, ts_query) DESC
    LIMIT match_count * 2
  ),
  aq_combined AS (
    SELECT
      'actions_queue'::text AS source_table,
      coalesce(s.id, k.id) AS record_id,
      coalesce(s.aq_title, k.aq_title) AS title,
      coalesce(s.aq_snippet, k.aq_snippet) AS snippet,
      s.rank::int AS semantic_rank,
      k.rank::int AS keyword_rank,
      coalesce(s.score, 0.0)::float AS semantic_score,
      coalesce(k.score, 0.0)::float AS keyword_score,
      (
        semantic_weight * coalesce(1.0 / (rrf_k + s.rank), 0.0) +
        keyword_weight * coalesce(1.0 / (rrf_k + k.rank), 0.0)
      )::float AS combined_score
    FROM aq_semantic s
    FULL OUTER JOIN aq_keyword k ON s.id = k.id
  ),

  -- =========================================
  -- Companies: semantic + keyword search
  -- =========================================
  co_semantic AS (
    SELECT
      co.id,
      co.name AS co_title,
      coalesce(co.sector, '') || ' | ' || coalesce(co.deal_status, '') AS co_snippet,
      1 - (co.embedding <=> query_embedding) AS score,
      row_number() OVER (ORDER BY co.embedding <=> query_embedding) AS rank
    FROM companies co
    WHERE co.embedding IS NOT NULL
      AND (filter_tables IS NULL OR 'companies' = ANY(filter_tables))
      AND (filter_date_from IS NULL OR co.created_at >= filter_date_from)
      AND (filter_date_to IS NULL OR co.created_at <= filter_date_to)
    ORDER BY co.embedding <=> query_embedding
    LIMIT match_count * 2
  ),
  co_keyword AS (
    SELECT
      co.id,
      co.name AS co_title,
      coalesce(co.sector, '') || ' | ' || coalesce(co.deal_status, '') AS co_snippet,
      ts_rank_cd(co.fts, ts_query) AS score,
      row_number() OVER (ORDER BY ts_rank_cd(co.fts, ts_query) DESC) AS rank
    FROM companies co
    WHERE co.fts @@ ts_query
      AND (filter_tables IS NULL OR 'companies' = ANY(filter_tables))
      AND (filter_date_from IS NULL OR co.created_at >= filter_date_from)
      AND (filter_date_to IS NULL OR co.created_at <= filter_date_to)
    ORDER BY ts_rank_cd(co.fts, ts_query) DESC
    LIMIT match_count * 2
  ),
  co_combined AS (
    SELECT
      'companies'::text AS source_table,
      coalesce(s.id, k.id) AS record_id,
      coalesce(s.co_title, k.co_title) AS title,
      coalesce(s.co_snippet, k.co_snippet) AS snippet,
      s.rank::int AS semantic_rank,
      k.rank::int AS keyword_rank,
      coalesce(s.score, 0.0)::float AS semantic_score,
      coalesce(k.score, 0.0)::float AS keyword_score,
      (
        semantic_weight * coalesce(1.0 / (rrf_k + s.rank), 0.0) +
        keyword_weight * coalesce(1.0 / (rrf_k + k.rank), 0.0)
      )::float AS combined_score
    FROM co_semantic s
    FULL OUTER JOIN co_keyword k ON s.id = k.id
  ),

  -- =========================================
  -- Union all tables and final ranking
  -- =========================================
  all_results AS (
    SELECT * FROM cd_combined
    UNION ALL
    SELECT * FROM tt_combined
    UNION ALL
    SELECT * FROM aq_combined
    UNION ALL
    SELECT * FROM co_combined
  )

  SELECT
    r.source_table,
    r.record_id,
    r.title,
    r.snippet,
    r.semantic_rank,
    r.keyword_rank,
    r.semantic_score,
    r.keyword_score,
    r.combined_score
  FROM all_results r
  ORDER BY r.combined_score DESC
  LIMIT match_count;

END;
$$;


-- =============================================================================
-- SECTION 9: Single-Table Search Functions (convenience)
-- =============================================================================
-- For cases where callers want to search within a single table type
-- without the overhead of the full cross-table hybrid search.

CREATE OR REPLACE FUNCTION search_content_digests(
  query_text text,
  query_embedding vector(1024),
  match_count int DEFAULT 10
)
RETURNS TABLE (
  id int,
  title text,
  channel text,
  score float
)
LANGUAGE sql
AS $$
  SELECT
    cd.id,
    cd.title,
    cd.channel,
    (
      0.7 * (1 - (cd.embedding <=> query_embedding)) +
      0.3 * coalesce(ts_rank_cd(cd.fts, plainto_tsquery('english', query_text)), 0)
    )::float AS score
  FROM content_digests cd
  WHERE cd.embedding IS NOT NULL
  ORDER BY score DESC
  LIMIT match_count;
$$;

CREATE OR REPLACE FUNCTION search_thesis_threads(
  query_text text,
  query_embedding vector(1024),
  match_count int DEFAULT 10
)
RETURNS TABLE (
  id int,
  thread_name text,
  core_thesis text,
  conviction text,
  score float
)
LANGUAGE sql
AS $$
  SELECT
    tt.id,
    tt.thread_name,
    left(tt.core_thesis, 300),
    tt.conviction,
    (
      0.7 * (1 - (tt.embedding <=> query_embedding)) +
      0.3 * coalesce(ts_rank_cd(tt.fts, plainto_tsquery('english', query_text)), 0)
    )::float AS score
  FROM thesis_threads tt
  WHERE tt.embedding IS NOT NULL
  ORDER BY score DESC
  LIMIT match_count;
$$;


-- =============================================================================
-- SECTION 10: Backfill Helper
-- =============================================================================
-- Queue all existing rows for embedding generation. Run once after deploying
-- the Edge Function and setting the VOYAGE_API_KEY secret.
-- This function manually enqueues all non-embedded rows into pgmq.

CREATE OR REPLACE FUNCTION util.backfill_embeddings()
RETURNS TABLE (table_name text, rows_queued bigint)
LANGUAGE plpgsql
AS $$
DECLARE
  cd_count bigint := 0;
  tt_count bigint := 0;
  aq_count bigint := 0;
  co_count bigint := 0;
BEGIN
  -- Backfill content_digests
  WITH queued AS (
    SELECT pgmq.send(
      'embedding_jobs',
      jsonb_build_object(
        'id', cd.id,
        'schema', 'public',
        'table', 'content_digests',
        'contentFunction', 'embedding_input_content_digests',
        'embeddingColumn', 'embedding'
      )
    )
    FROM content_digests cd
    WHERE cd.embedding IS NULL
  )
  SELECT count(*) INTO cd_count FROM queued;

  -- Backfill thesis_threads
  WITH queued AS (
    SELECT pgmq.send(
      'embedding_jobs',
      jsonb_build_object(
        'id', tt.id,
        'schema', 'public',
        'table', 'thesis_threads',
        'contentFunction', 'embedding_input_thesis_threads',
        'embeddingColumn', 'embedding'
      )
    )
    FROM thesis_threads tt
    WHERE tt.embedding IS NULL
  )
  SELECT count(*) INTO tt_count FROM queued;

  -- Backfill actions_queue
  WITH queued AS (
    SELECT pgmq.send(
      'embedding_jobs',
      jsonb_build_object(
        'id', aq.id,
        'schema', 'public',
        'table', 'actions_queue',
        'contentFunction', 'embedding_input_actions_queue',
        'embeddingColumn', 'embedding'
      )
    )
    FROM actions_queue aq
    WHERE aq.embedding IS NULL
  )
  SELECT count(*) INTO aq_count FROM queued;

  -- Backfill companies (currently 0 rows, but ready)
  WITH queued AS (
    SELECT pgmq.send(
      'embedding_jobs',
      jsonb_build_object(
        'id', co.id,
        'schema', 'public',
        'table', 'companies',
        'contentFunction', 'embedding_input_companies',
        'embeddingColumn', 'embedding'
      )
    )
    FROM companies co
    WHERE co.embedding IS NULL
  )
  SELECT count(*) INTO co_count FROM queued;

  RETURN QUERY
  SELECT 'content_digests'::text, cd_count
  UNION ALL
  SELECT 'thesis_threads'::text, tt_count
  UNION ALL
  SELECT 'actions_queue'::text, aq_count
  UNION ALL
  SELECT 'companies'::text, co_count;
END;
$$;


-- =============================================================================
-- POST-MIGRATION MANUAL STEPS (do NOT include in automated migration):
-- =============================================================================
-- 1. Add project URL to Vault (run in SQL Editor):
--    SELECT vault.create_secret(
--      'https://llfkxnsfczludgigknbs.supabase.co',
--      'project_url'
--    );
--
-- 2. Deploy the Edge Function (from Mac terminal):
--    cd /path/to/project && supabase functions deploy embed
--
-- 3. Set Voyage AI API key as Edge Function secret:
--    supabase secrets set VOYAGE_API_KEY=<your-voyage-api-key>
--
-- 4. Run the backfill (in SQL Editor):
--    SELECT * FROM util.backfill_embeddings();
--
-- 5. Verify embeddings are populating (wait ~30s, then check):
--    SELECT id, title, embedding IS NOT NULL AS has_embedding
--    FROM content_digests;
--
-- 6. Test hybrid search (requires a query embedding from Voyage AI):
--    SELECT * FROM hybrid_search(
--      'agentic AI infrastructure',
--      '<embedding_vector>'::vector(1024),
--      10
--    );
-- =============================================================================
