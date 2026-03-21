-- IRGI L73-74: Performance Optimization + deal_intelligence_brief
-- Date: 2026-03-21
-- Machine: M6 IRGI
--
-- L73: Two-phase keyword optimization for hybrid_search v5
--   Problem: term_coverage_boost called on ALL OR-matched rows (1144 companies,
--   308 network) = ~67ms overhead per query.
--   Fix: Pre-filter by raw ts_rank_cd (cheap, ~11ms) to get top kw_limit*2 candidates,
--   then apply term_coverage_boost only on that subset (~60 rows).
--   Result: hybrid_search 217ms -> 97ms (-55%). Same ranking results.
--
-- L74: deal_intelligence_brief — new agent tool
--   Purpose: Full deal assessment for any company (pipeline or portfolio).
--   Used by ENIAC/Megamind to evaluate whether a company deserves attention.
--   Returns: thesis fit, competitive context, network connections, investors,
--   deal signals, portfolio data, and agent recommendation.
--   Latency: 16ms. Bug fix: PL/pgSQL RECORD IS NOT NULL doesn't work as expected
--   for SELECT INTO — use FOUND variable instead.

------------------------------------------------------------
-- L73: hybrid_search v5 — two-phase keyword optimization
-- Changes from v4:
--   - co_keyword CTE: split into co_raw_top (raw ts_rank_cd) + co_keyword (boost on subset)
--   - nw_keyword CTE: same split into nw_raw_top + nw_keyword
--   - All other CTEs unchanged (small tables, boost overhead negligible)
------------------------------------------------------------
-- Full function deployed via execute_sql. See Supabase for canonical source.
-- Key pattern:
--
-- co_raw_top AS (
--   SELECT co.id, co.name, co.fts,
--     ts_rank_cd(co.fts, ts_query, 32) AS raw_score
--   FROM companies co WHERE co.fts @@ ts_query
--   ORDER BY raw_score DESC LIMIT kw_limit * 2
-- ),
-- co_keyword AS (
--   SELECT r.id, r.co_title, r.co_snippet,
--     r.raw_score * (1.0 + term_coverage_boost(r.fts, query_text)) AS score,
--     row_number() OVER (...) AS rank
--   FROM co_raw_top r
--   ORDER BY score DESC LIMIT kw_limit
-- )

------------------------------------------------------------
-- L74: deal_intelligence_brief
------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.deal_intelligence_brief(
  p_company_id INT
)
RETURNS JSONB
LANGUAGE plpgsql STABLE
SET search_path TO 'public', 'extensions'
AS $function$
DECLARE
  result JSONB;
  v_company RECORD;
  v_portfolio RECORD;
  v_company_name TEXT;
  v_is_portfolio BOOLEAN := FALSE;
  v_thesis_connections JSONB;
  v_competitive_context JSONB;
  v_network_connections JSONB;
  v_investor_overlap JSONB;
  v_deal_signals JSONB;
  v_agent_directive JSONB;
BEGIN
  SELECT c.name INTO v_company_name FROM companies c WHERE c.id = p_company_id;
  IF v_company_name IS NULL THEN RETURN jsonb_build_object('error', 'Company not found'); END IF;

  SELECT c.* INTO v_company FROM companies c WHERE c.id = p_company_id;

  -- Portfolio lookup: use FOUND (not IS NOT NULL) for RECORD types
  SELECT p.* INTO v_portfolio FROM portfolio p WHERE LOWER(p.portfolio_co) = LOWER(v_company_name);
  v_is_portfolio := FOUND;

  -- Thesis connections via entity_connections graph
  SELECT COALESCE(jsonb_agg(jsonb_build_object(
    'thesis_name', tt.thread_name,
    'thesis_id', tt.id,
    'connection_strength', ROUND(ec.strength::numeric, 3),
    'connection_type', ec.connection_type,
    'conviction', tt.conviction,
    'status', tt.status
  ) ORDER BY ec.strength DESC), '[]'::jsonb)
  INTO v_thesis_connections
  FROM entity_connections ec
  JOIN thesis_threads tt ON tt.id = ec.target_id
  WHERE ec.source_id = p_company_id
    AND ec.source_type = 'company'
    AND ec.target_type = 'thesis';

  -- Competitive context: top 5 similar companies
  SELECT COALESCE(jsonb_agg(jsonb_build_object(
    'name', c2.name,
    'sector', c2.sector,
    'deal_status', c2.deal_status,
    'pipeline', c2.pipeline_status,
    'similarity', ROUND((1 - (v_company.embedding <=> c2.embedding))::numeric, 3),
    'is_portfolio', EXISTS(SELECT 1 FROM portfolio p WHERE LOWER(p.portfolio_co) = LOWER(c2.name)),
    'funding', c2.venture_funding,
    'last_round', c2.last_round_amount
  ) ORDER BY v_company.embedding <=> c2.embedding), '[]'::jsonb)
  INTO v_competitive_context
  FROM (
    SELECT c2.* FROM companies c2
    WHERE c2.id != p_company_id AND c2.embedding IS NOT NULL AND v_company.embedding IS NOT NULL
    ORDER BY v_company.embedding <=> c2.embedding
    LIMIT 5
  ) c2;

  -- Network connections via entity_connections
  SELECT COALESCE(jsonb_agg(jsonb_build_object(
    'person_name', nw.person_name,
    'person_id', nw.id,
    'role', nw.role_title,
    'connection_type', ec.connection_type,
    'strength', ROUND(ec.strength::numeric, 3),
    'priority', nw.e_e_priority,
    'ryg', nw.ryg,
    'last_interaction', nw.last_interaction_at::date
  ) ORDER BY ec.strength DESC), '[]'::jsonb)
  INTO v_network_connections
  FROM entity_connections ec
  JOIN network nw ON nw.id = ec.source_id
  WHERE ec.target_id = p_company_id
    AND ec.source_type = 'network'
    AND ec.target_type = 'company'
  LIMIT 10;

  -- Investor overlap
  SELECT COALESCE(jsonb_agg(jsonb_build_object(
    'investor_name', c2.name,
    'investor_id', c2.id,
    'investor_sector', c2.sector
  )), '[]'::jsonb)
  INTO v_investor_overlap
  FROM companies c2
  WHERE v_company.investor_company_ids IS NOT NULL
    AND c2.notion_page_id = ANY(v_company.investor_company_ids);

  v_deal_signals := COALESCE(v_company.signal_history, '{}'::jsonb);

  -- Agent directive
  v_agent_directive := jsonb_build_object(
    'is_portfolio', v_is_portfolio,
    'has_thesis_fit', jsonb_array_length(v_thesis_connections) > 0,
    'thesis_count', jsonb_array_length(v_thesis_connections),
    'competitive_density', (SELECT COUNT(*) FROM companies c2 WHERE c2.sector = v_company.sector AND c2.embedding IS NOT NULL),
    'network_coverage', (SELECT COUNT(*) FROM entity_connections ec WHERE ec.target_id = p_company_id AND ec.source_type = 'network' AND ec.target_type = 'company'),
    'data_richness', CASE
      WHEN LENGTH(COALESCE(v_company.page_content, '')) > 500 THEN 'RICH'
      WHEN LENGTH(COALESCE(v_company.page_content, '')) > 100 THEN 'MODERATE'
      WHEN LENGTH(COALESCE(v_company.page_content, '')) > 0 THEN 'THIN'
      ELSE 'EMPTY'
    END,
    'pipeline_stage', COALESCE(v_company.pipeline_status, 'unknown'),
    'deal_status', COALESCE(v_company.deal_status, 'unknown'),
    'recommendation', CASE
      WHEN v_is_portfolio AND v_portfolio.health = 'Red' THEN 'URGENT: Portfolio company in Red health. Prioritize.'
      WHEN v_is_portfolio AND v_portfolio.fumes_date IS NOT NULL AND v_portfolio.fumes_date < CURRENT_DATE + INTERVAL '90 days' THEN 'URGENT: Portfolio company approaching fumes date.'
      WHEN v_is_portfolio THEN 'MONITOR: Active portfolio company. Check key questions.'
      WHEN jsonb_array_length(v_thesis_connections) >= 2 THEN 'HIGH FIT: Strong thesis alignment (' || jsonb_array_length(v_thesis_connections) || ' theses). Deep-dive recommended.'
      WHEN jsonb_array_length(v_thesis_connections) = 1 THEN 'THESIS FIT: Aligns with one thesis. Worth initial research.'
      WHEN v_company.priority IN ('High', 'Core') THEN 'PRIORITY: Marked high priority. Investigate.'
      ELSE 'STANDARD: Run initial screening. Check thesis relevance.'
    END
  );

  result := jsonb_build_object(
    'company_id', v_company.id,
    'name', v_company_name,
    'sector', v_company.sector,
    'website', v_company.website,
    'deal_status', v_company.deal_status,
    'pipeline_status', v_company.pipeline_status,
    'funding', v_company.venture_funding,
    'last_round', v_company.last_round_amount,
    'last_round_timing', v_company.last_round_timing,
    'founding_timeline', v_company.founding_timeline,
    'sells_to', v_company.sells_to,
    'jtbd', v_company.jtbd,
    'smart_money', v_company.smart_money,
    'priority', v_company.priority,
    'notion_page_id', v_company.notion_page_id,
    'content_richness', LENGTH(COALESCE(v_company.page_content, '')),
    'portfolio_data', CASE WHEN v_is_portfolio THEN jsonb_build_object(
      'health', v_portfolio.health,
      'ownership_pct', v_portfolio.ownership_pct,
      'entry_cheque', v_portfolio.entry_cheque,
      'scale_of_business', v_portfolio.scale_of_business,
      'fumes_date', v_portfolio.fumes_date,
      'cash_in_bank', v_portfolio.cash_in_bank,
      'key_questions', v_portfolio.key_questions,
      'high_impact', v_portfolio.high_impact,
      'check_in_cadence', v_portfolio.check_in_cadence,
      'research_file_path', v_portfolio.research_file_path
    ) ELSE NULL END,
    'thesis_connections', v_thesis_connections,
    'competitive_context', v_competitive_context,
    'network_connections', v_network_connections,
    'investors', v_investor_overlap,
    'deal_signals', v_deal_signals,
    'agent_directive', v_agent_directive
  );

  RETURN result;
END;
$function$;
