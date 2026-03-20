-- Search Intelligence Fixes (M9 Audit Loop 2)
-- Date: 2026-03-20
-- Fixes: C1 (network in hybrid_search), C4 (vector path in find_related_companies),
--        thesis over-tagging (ids 88-102), materialized view refresh

-- ============================================================================
-- FIX 1: Add Network table to hybrid_search()
-- Issue: C1 — 3,722 people unsearchable via primary search API
-- ============================================================================

CREATE OR REPLACE FUNCTION public.hybrid_search(
  query_text text,
  query_embedding vector,
  match_count integer DEFAULT 20,
  keyword_weight double precision DEFAULT 0.3,
  semantic_weight double precision DEFAULT 0.7,
  filter_tables text[] DEFAULT NULL::text[],
  filter_status text DEFAULT NULL::text,
  filter_date_from timestamp with time zone DEFAULT NULL::timestamp with time zone,
  filter_date_to timestamp with time zone DEFAULT NULL::timestamp with time zone
)
RETURNS TABLE(
  source_table text,
  record_id integer,
  title text,
  snippet text,
  semantic_rank integer,
  keyword_rank integer,
  semantic_score double precision,
  keyword_score double precision,
  combined_score double precision
)
LANGUAGE plpgsql
AS $function$
DECLARE
  ts_query tsquery;
  rrf_k int := 60;
BEGIN
  ts_query := plainto_tsquery('english', query_text);

  RETURN QUERY

  WITH
  -- === Content Digests ===
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
    LIMIT match_count * 2
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

  -- === Thesis Threads ===
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

  -- === Actions Queue ===
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

  -- === Companies ===
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

  -- === Network (NEW — added in M9 Loop 2) ===
  nw_semantic AS (
    SELECT
      nw.id,
      nw.person_name AS nw_title,
      coalesce(nw.current_role, '') || ' | ' || coalesce(array_to_string(nw.home_base, ', '), '') AS nw_snippet,
      1 - (nw.embedding <=> query_embedding) AS score,
      row_number() OVER (ORDER BY nw.embedding <=> query_embedding) AS rank
    FROM network nw
    WHERE nw.embedding IS NOT NULL
      AND (filter_tables IS NULL OR 'network' = ANY(filter_tables))
      AND (filter_date_from IS NULL OR nw.created_at >= filter_date_from)
      AND (filter_date_to IS NULL OR nw.created_at <= filter_date_to)
    ORDER BY nw.embedding <=> query_embedding
    LIMIT match_count * 2
  ),
  nw_keyword AS (
    SELECT
      nw.id,
      nw.person_name AS nw_title,
      coalesce(nw.current_role, '') || ' | ' || coalesce(array_to_string(nw.home_base, ', '), '') AS nw_snippet,
      ts_rank_cd(nw.fts, ts_query) AS score,
      row_number() OVER (ORDER BY ts_rank_cd(nw.fts, ts_query) DESC) AS rank
    FROM network nw
    WHERE nw.fts @@ ts_query
      AND (filter_tables IS NULL OR 'network' = ANY(filter_tables))
      AND (filter_date_from IS NULL OR nw.created_at >= filter_date_from)
      AND (filter_date_to IS NULL OR nw.created_at <= filter_date_to)
    ORDER BY ts_rank_cd(nw.fts, ts_query) DESC
    LIMIT match_count * 2
  ),
  nw_combined AS (
    SELECT
      'network'::text AS source_table,
      coalesce(s.id, k.id) AS record_id,
      coalesce(s.nw_title, k.nw_title) AS title,
      coalesce(s.nw_snippet, k.nw_snippet) AS snippet,
      s.rank::int AS semantic_rank,
      k.rank::int AS keyword_rank,
      coalesce(s.score, 0.0)::float AS semantic_score,
      coalesce(k.score, 0.0)::float AS keyword_score,
      (
        semantic_weight * coalesce(1.0 / (rrf_k + s.rank), 0.0) +
        keyword_weight * coalesce(1.0 / (rrf_k + k.rank), 0.0)
      )::float AS combined_score
    FROM nw_semantic s
    FULL OUTER JOIN nw_keyword k ON s.id = k.id
  ),

  all_results AS (
    SELECT * FROM cd_combined
    UNION ALL
    SELECT * FROM tt_combined
    UNION ALL
    SELECT * FROM aq_combined
    UNION ALL
    SELECT * FROM co_combined
    UNION ALL
    SELECT * FROM nw_combined
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
$function$;


-- ============================================================================
-- FIX 2: Rewrite find_related_companies() with vector similarity path
-- Issue: C4 — WHERE FALSE disabled vector path, function was trigram-only
-- Change: New signature takes company_id (integer) instead of text query.
--         Uses source company's embedding for cosine similarity search.
--         Falls back to trigram on company name if no embedding exists.
-- ============================================================================

-- Drop old text-based signature
DROP FUNCTION IF EXISTS public.find_related_companies(text, integer);

CREATE OR REPLACE FUNCTION public.find_related_companies(
  p_company_id integer,
  p_limit_n integer DEFAULT 10
)
RETURNS TABLE(
  company_id integer,
  company_name text,
  similarity double precision,
  sector text
)
LANGUAGE plpgsql
STABLE SECURITY DEFINER
SET search_path TO 'public', 'extensions'
AS $function$
DECLARE
  v_company_embedding vector(1024);
  v_company_name text;
BEGIN
  -- Get the source company's embedding
  SELECT c.embedding, c.name
  INTO v_company_embedding, v_company_name
  FROM companies c
  WHERE c.id = p_company_id;

  -- If company not found, return empty
  IF v_company_name IS NULL THEN
    RETURN;
  END IF;

  -- If company has no embedding, fall back to trigram on name
  IF v_company_embedding IS NULL THEN
    RETURN QUERY
    SELECT
      c.id AS company_id,
      c.name AS company_name,
      ROUND(similarity(v_company_name, COALESCE(c.name, ''))::numeric, 4)::FLOAT AS similarity,
      c.sector
    FROM companies c
    WHERE c.id != p_company_id
      AND similarity(v_company_name, COALESCE(c.name, '')) > 0.1
    ORDER BY similarity(v_company_name, COALESCE(c.name, '')) DESC
    LIMIT p_limit_n;
    RETURN;
  END IF;

  -- Primary path: vector cosine similarity
  RETURN QUERY
  SELECT
    c.id AS company_id,
    c.name AS company_name,
    ROUND((1.0 - (c.embedding <=> v_company_embedding))::numeric, 4)::FLOAT AS similarity,
    c.sector
  FROM companies c
  WHERE c.id != p_company_id
    AND c.embedding IS NOT NULL
    AND (1.0 - (c.embedding <=> v_company_embedding)) > 0.3
  ORDER BY c.embedding <=> v_company_embedding
  LIMIT p_limit_n;
END;
$function$;


-- ============================================================================
-- FIX 3: Remove spurious "Healthcare AI Agents as Infrastructure" thesis tag
-- Issue: Batch artifact — actions 88-102 all tagged with Healthcare thesis
--        regardless of actual content. Only affects non-healthcare actions.
-- ============================================================================

-- Remove Healthcare tag (pipe-delimited) from non-healthcare actions
UPDATE actions_queue
SET thesis_connection = REPLACE(thesis_connection, '|Healthcare AI Agents as Infrastructure', '')
WHERE id BETWEEN 88 AND 102
  AND thesis_connection LIKE '%|Healthcare AI Agents as Infrastructure%'
  AND action NOT ILIKE '%health%'
  AND action NOT ILIKE '%medical%'
  AND action NOT ILIKE '%hospital%'
  AND action NOT ILIKE '%patient%'
  AND action NOT ILIKE '%clinical%';

-- Clean up any leading/trailing pipes
UPDATE actions_queue
SET thesis_connection = TRIM(BOTH '|' FROM thesis_connection)
WHERE (thesis_connection LIKE '|%' OR thesis_connection LIKE '%|')
  AND id BETWEEN 88 AND 102;


-- ============================================================================
-- FIX 4: Refresh materialized view
-- ============================================================================

REFRESH MATERIALIZED VIEW CONCURRENTLY action_scores;


-- ============================================================================
-- VALIDATION QUERIES
-- ============================================================================

-- Test hybrid_search with network filter
-- SELECT source_table, record_id, title, LEFT(snippet, 60), semantic_rank, combined_score
-- FROM hybrid_search(
--   'founder CEO venture',
--   (SELECT embedding FROM network WHERE person_name = 'Nithin Kamath' LIMIT 1),
--   10, 0.3, 0.7, ARRAY['network']
-- );

-- Test find_related_companies with Swiggy
-- SELECT * FROM find_related_companies(
--   (SELECT id FROM companies WHERE name = 'Swiggy' LIMIT 1)
-- );

-- Verify thesis over-tagging cleaned
-- SELECT id, thesis_connection FROM actions_queue WHERE id BETWEEN 88 AND 102;
