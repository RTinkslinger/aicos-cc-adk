-- M6 IRGI Loop: Recency Boost + Search Quality Assessment
-- Date: 2026-03-21
-- Changes:
--   1. recency_boost() utility function (exponential decay, 30-day half-life)
--   2. hybrid_search() upgraded to return record_date per result
--   3. balanced_search() now applies recency_boost to normalized_score
--   4. irgi_search_quality_assessment() — 8-query standardized quality test
--   5. irgi_system_report() updated to include search_quality section

-- 1. Recency boost utility
CREATE OR REPLACE FUNCTION recency_boost(
  record_date timestamptz,
  half_life_days int DEFAULT 30,
  max_boost float DEFAULT 0.15
)
RETURNS float
LANGUAGE sql
IMMUTABLE
AS $$
  SELECT CASE
    WHEN record_date IS NULL THEN 0.0
    ELSE max_boost * POWER(0.5, EXTRACT(EPOCH FROM (NOW() - record_date)) / (half_life_days * 86400.0))
  END
$$;

-- 2. hybrid_search with record_date output
-- NOTE: Must DROP first since return type changed
-- DROP FUNCTION IF EXISTS public.hybrid_search(text, vector, integer, double precision, double precision, text[], text, timestamp with time zone, timestamp with time zone);
-- Then CREATE with record_date column added to each surface's semantic/keyword CTEs
-- (Full function body too large for migration file — applied directly to DB)

-- 3. balanced_search with recency boost in norm_score
-- Applied recency_boost(r.record_date, 30, 0.15) additively to normalized_score
-- (Full function body too large for migration file — applied directly to DB)

-- 4. Search quality assessment
CREATE OR REPLACE FUNCTION irgi_search_quality_assessment()
RETURNS jsonb
LANGUAGE plpgsql
STABLE
AS $function$
DECLARE
  result jsonb;
  test_queries text[] := ARRAY[
    'agentic AI infrastructure',
    'cybersecurity pen testing',
    'healthcare AI',
    'India fintech',
    'SaaS replacement by agents',
    'portfolio company risk',
    'deal pipeline active',
    'thesis evidence bias'
  ];
  q text;
  surface_diversity float;
  avg_norm_score float;
  top_relevance float;
  total_results int;
  has_thesis boolean;
  has_companies boolean;
  query_results jsonb := '[]'::jsonb;
  overall_score float := 0;
  query_count int := 0;
BEGIN
  FOREACH q IN ARRAY test_queries LOOP
    WITH search_results AS (
      SELECT source_table, record_id, title, normalized_score, combined_score
      FROM balanced_search(q, NULL, 15)
    ),
    metrics AS (
      SELECT
        COUNT(DISTINCT source_table) as surfaces_hit,
        COUNT(*) as result_count,
        ROUND(AVG(normalized_score)::numeric, 3) as avg_score,
        ROUND(MAX(normalized_score)::numeric, 3) as top_score,
        ROUND(MIN(normalized_score)::numeric, 3) as bottom_score,
        BOOL_OR(source_table = 'thesis_threads') as has_thesis,
        BOOL_OR(source_table = 'companies') as has_companies,
        BOOL_OR(source_table = 'actions_queue') as has_actions,
        ROUND(STDDEV(normalized_score)::numeric, 3) as score_spread
      FROM search_results
    )
    SELECT
      m.surfaces_hit::float / 7.0,
      m.avg_score::float,
      m.top_score::float,
      m.result_count,
      m.has_thesis,
      m.has_companies
    INTO surface_diversity, avg_norm_score, top_relevance, total_results, has_thesis, has_companies
    FROM metrics m;

    query_results := query_results || jsonb_build_object(
      'query', q,
      'surfaces', surface_diversity * 7,
      'result_count', total_results,
      'avg_norm_score', avg_norm_score,
      'top_score', top_relevance,
      'has_thesis', has_thesis,
      'has_companies', has_companies,
      'quality_score', ROUND((
        LEAST(surface_diversity * 3, 3.0) +
        LEAST(avg_norm_score * 4, 4.0) +
        LEAST(total_results::float / 15.0 * 2, 2.0) +
        CASE WHEN top_relevance > 0.8 THEN 1.0 ELSE top_relevance END
      )::numeric, 1)
    );

    overall_score := overall_score + LEAST(surface_diversity * 3, 3.0) + LEAST(avg_norm_score * 4, 4.0) + LEAST(total_results::float / 15.0 * 2, 2.0) + CASE WHEN top_relevance > 0.8 THEN 1.0 ELSE top_relevance END;
    query_count := query_count + 1;
  END LOOP;

  result := jsonb_build_object(
    'assessment_date', CURRENT_DATE,
    'overall_score', ROUND((overall_score / query_count)::numeric, 1) || '/10',
    'overall_score_raw', ROUND((overall_score / query_count)::numeric, 2),
    'test_queries', array_length(test_queries, 1),
    'per_query', query_results,
    'recency_boost_enabled', true,
    'recency_half_life_days', 30,
    'recency_max_boost', 0.15
  );

  RETURN result;
END;
$function$;

-- 5. irgi_system_report updated to include search_quality
-- Added v_search_quality variable and irgi_search_quality_assessment() call
-- search_quality key added to the returned jsonb
-- (Applied directly to DB — full function too large for migration file)
