-- =============================================================================
-- IRGI Scoring Fixes: M6 Loop 2
-- =============================================================================
-- Project: AI CoS (llfkxnsfczludgigknbs, ap-south-1 Mumbai, PG17)
-- Date: 2026-03-20
-- Executed by: Claude Opus 4.6 via Supabase MCP
-- Scope: Fix score compression, bucket misrouting, latent connections, bias detection
--
-- Changes:
--   1. Rewrite score_action_thesis_relevance with weighted combination
--   2. Rewrite route_action_to_bucket with portfolio/network priority
--   3. Tag latent thesis connections via vector similarity
--   4. Create detect_thesis_bias() function
--   5. Refresh materialized views
-- =============================================================================


-- =============================================================================
-- FIX 1: Rewrite score_action_thesis_relevance
-- =============================================================================
-- Problem: Returns flat 0.90 for 39 actions via explicit_connection matching.
--          Zero discrimination between high-quality and mediocre connections.
-- Solution: WEIGHTED combination of 4 methods + conviction/status multipliers.
--   - Vector similarity: 0.50 weight (primary signal)
--   - Explicit connection: 0.20 weight (graduated: 1.0/0.7/0.5, not flat 0.9)
--   - Trigram text overlap: 0.15 weight
--   - Key question match: 0.15 weight
--   - Conviction multiplier: High=1.15, Medium=1.0, New=0.90, Low=0.85
--   - Status multiplier: Active=1.10, Exploring=1.0, Parked=0.70

CREATE OR REPLACE FUNCTION score_action_thesis_relevance(p_action_id INTEGER)
RETURNS TABLE(
    thesis_id INT,
    thesis_name TEXT,
    relevance_score FLOAT,
    match_type TEXT
)
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    v_action_text TEXT;
    v_action_embedding vector;
    v_thesis_conn TEXT;
    v_source_content TEXT;
    v_reasoning TEXT;
BEGIN
    SELECT
        a.action,
        a.embedding,
        a.thesis_connection,
        a.source_content,
        a.reasoning
    INTO v_action_text, v_action_embedding, v_thesis_conn, v_source_content, v_reasoning
    FROM actions_queue a
    WHERE a.id = p_action_id;

    IF v_action_text IS NULL THEN
        RETURN;
    END IF;

    v_action_text := COALESCE(v_action_text, '') || ' ' ||
                     COALESCE(v_thesis_conn, '') || ' ' ||
                     COALESCE(v_source_content, '') || ' ' ||
                     COALESCE(v_reasoning, '');

    RETURN QUERY
    WITH
    -- Method 1: Vector similarity (PRIMARY signal, weight 0.50)
    vector_scores AS (
        SELECT
            t.id,
            t.thread_name,
            t.conviction,
            t.status AS t_status,
            CASE
                WHEN v_action_embedding IS NOT NULL AND t.embedding IS NOT NULL
                THEN 1.0 - (v_action_embedding <=> t.embedding)
                ELSE 0.0
            END AS score
        FROM thesis_threads t
        WHERE v_action_embedding IS NOT NULL AND t.embedding IS NOT NULL
    ),
    -- Method 2: Trigram text similarity (weight 0.15)
    trgm_scores AS (
        SELECT
            t.id,
            GREATEST(
                similarity(v_action_text, t.thread_name),
                similarity(v_action_text, COALESCE(t.core_thesis, '')),
                similarity(v_action_text, COALESCE(t.key_companies, '')),
                similarity(v_action_text, COALESCE(t.evidence_for, '')),
                similarity(v_action_text, COALESCE(t.investment_implications, ''))
            )::FLOAT AS score
        FROM thesis_threads t
    ),
    -- Method 3: Explicit thesis_connection matching (weight 0.20)
    -- GRADUATED scores: exact=1.0, partial=0.7, weak=0.5
    explicit_scores AS (
        SELECT
            t.id,
            CASE
                WHEN v_thesis_conn IS NOT NULL AND v_thesis_conn != '' AND
                    LOWER(v_thesis_conn) LIKE '%' || LOWER(t.thread_name) || '%'
                THEN 1.0
                WHEN v_thesis_conn IS NOT NULL AND v_thesis_conn != '' AND
                    LOWER(t.thread_name) LIKE '%' || LOWER(SPLIT_PART(v_thesis_conn, '|', 1)) || '%'
                THEN 0.7
                WHEN v_thesis_conn IS NOT NULL AND v_thesis_conn != '' AND
                    LOWER(t.core_thesis) LIKE '%' || LOWER(SPLIT_PART(v_thesis_conn, ' - ', 1)) || '%'
                THEN 0.5
                ELSE 0.0
            END AS score
        FROM thesis_threads t
    ),
    -- Method 4: Key question keyword match (weight 0.15)
    kq_scores AS (
        SELECT
            t.id,
            CASE
                WHEN t.key_questions_json IS NOT NULL
                     AND t.key_questions_json->'open' IS NOT NULL
                     AND jsonb_array_length(COALESCE(t.key_questions_json->'open', '[]'::jsonb)) > 0
                THEN (
                    SELECT COALESCE(MAX(similarity(v_action_text, q.value::text)), 0.0)
                    FROM jsonb_array_elements_text(t.key_questions_json->'open') q
                )::FLOAT
                ELSE 0.0
            END AS score
        FROM thesis_threads t
    ),
    -- WEIGHTED COMBINATION + multipliers
    weighted AS (
        SELECT
            vs.id,
            vs.thread_name,
            vs.conviction,
            vs.t_status,
            vs.score AS vec_score,
            COALESCE(es.score, 0.0) AS exp_score,
            COALESCE(ts.score, 0.0) AS trg_score,
            COALESCE(ks.score, 0.0) AS kq_score,
            (0.50 * vs.score +
             0.20 * COALESCE(es.score, 0.0) +
             0.15 * COALESCE(ts.score, 0.0) +
             0.15 * COALESCE(ks.score, 0.0)
            ) AS raw_combined,
            CASE vs.conviction
                WHEN 'High' THEN 1.15
                WHEN 'Medium' THEN 1.00
                WHEN 'New' THEN 0.90
                WHEN 'Low' THEN 0.85
                ELSE 1.00
            END AS conviction_mult,
            CASE vs.t_status
                WHEN 'Active' THEN 1.10
                WHEN 'Exploring' THEN 1.00
                WHEN 'Parked' THEN 0.70
                ELSE 1.00
            END AS status_mult,
            CASE
                WHEN COALESCE(es.score, 0.0) >= 0.7 AND vs.score >= 0.70 THEN 'vector+explicit'
                WHEN COALESCE(es.score, 0.0) >= 0.7 THEN 'explicit_connection'
                WHEN vs.score >= 0.60 THEN 'vector'
                WHEN COALESCE(ks.score, 0.0) > COALESCE(ts.score, 0.0) THEN 'key_question_match'
                ELSE 'text_overlap'
            END AS dominant_type
        FROM vector_scores vs
        LEFT JOIN explicit_scores es ON vs.id = es.id
        LEFT JOIN trgm_scores ts ON vs.id = ts.id
        LEFT JOIN kq_scores ks ON vs.id = ks.id
    )
    SELECT
        w.id AS thesis_id,
        w.thread_name AS thesis_name,
        ROUND(LEAST(1.0, w.raw_combined * w.conviction_mult * w.status_mult)::numeric, 4)::FLOAT AS relevance_score,
        w.dominant_type AS match_type
    FROM weighted w
    WHERE w.raw_combined > 0.05
    ORDER BY relevance_score DESC
    LIMIT 5;
END;
$$;


-- =============================================================================
-- FIX 2: Rewrite route_action_to_bucket
-- =============================================================================
-- Problem: Bucket 4 (Thesis Evolution) gets 55% of actions because:
--   - Research action_type (40% of actions) auto-triggers thesis keywords
--   - Portfolio-specific research misrouted to Bucket 4
-- Solution:
--   - Portfolio research detection (company check-in, flag risk, request data)
--   - Network detection expanded (intro, meet, connect, share)
--   - Thesis signal narrowed to pure thesis work only
--   - User priority rebalancing: B2 x1.5, B3 x1.3, B4 x0.6
--   - Research fallback to Bucket 1 (Discover New)

CREATE OR REPLACE FUNCTION route_action_to_bucket(p_action_id INTEGER)
RETURNS TABLE(
    bucket TEXT,
    confidence FLOAT,
    reasoning TEXT
)
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    v_action TEXT;
    v_action_type TEXT;
    v_thesis_conn TEXT;
    v_source_content TEXT;
    v_reasoning TEXT;
    v_company_notion_id TEXT;
    v_combined_text TEXT;
    v_scoring_factors JSONB;

    v_b1_score FLOAT := 0.0;
    v_b2_score FLOAT := 0.0;
    v_b3_score FLOAT := 0.0;
    v_b4_score FLOAT := 0.0;

    v_has_portfolio_company BOOLEAN := FALSE;
    v_has_new_company_signal BOOLEAN := FALSE;
    v_has_network_signal BOOLEAN := FALSE;
    v_has_thesis_signal BOOLEAN := FALSE;
    v_has_portfolio_research_signal BOOLEAN := FALSE;
BEGIN
    SELECT
        a.action, a.action_type, a.thesis_connection,
        a.source_content, a.reasoning, a.company_notion_id,
        a.scoring_factors
    INTO v_action, v_action_type, v_thesis_conn, v_source_content,
         v_reasoning, v_company_notion_id, v_scoring_factors
    FROM actions_queue a
    WHERE a.id = p_action_id;

    IF v_action IS NULL THEN
        RETURN;
    END IF;

    v_combined_text := LOWER(COALESCE(v_action, '') || ' ' ||
                       COALESCE(v_thesis_conn, '') || ' ' ||
                       COALESCE(v_source_content, '') || ' ' ||
                       COALESCE(v_reasoning, ''));

    -- Portfolio company detection via company_notion_id
    IF v_company_notion_id IS NOT NULL AND v_company_notion_id != '' THEN
        v_has_portfolio_company := EXISTS(
            SELECT 1 FROM portfolio p
            WHERE p.company_name_id = v_company_notion_id
        );
    END IF;

    -- Portfolio-related research detection (even without company_notion_id)
    v_has_portfolio_research_signal := (
        v_combined_text ~ '(check.in|follow.on|board prep|portfolio.*review|portfolio.*company|existing position|ownership|competitive intel|flag.*risk|request.*data|request.*breakdown|request.*detail|request.*case study|verify metric|share.*data.*portfolio|portfolio.*against|ids.*framework|moat.*portfolio|scaling call|working capital|customer.*cohort|product quality|execution risk|team.*call.*founder|dual.market)'
        OR (v_action_type = 'Portfolio Check-in')
        OR (v_action_type = 'Research' AND v_combined_text ~ '(portfolio|unifize|codeant|highperformr|kisan|monday\.com|sierra|amrit|anubhi|dallas renal|night wolf)')
    );

    v_has_new_company_signal := (
        v_combined_text ~ '(new company|discover|pipeline|evaluate|due diligence|scout|deal flow|source|first meeting|intro to.*founder|cap table|investable)'
        OR v_action_type IN ('Pipeline Action')
        OR (v_company_notion_id IS NOT NULL AND NOT v_has_portfolio_company)
    );

    v_has_network_signal := (
        v_combined_text ~ '(collective|community|network|intro|connect|meet|outreach|relationship|devc|extended|core member|funnel|angel|mentor)'
        OR v_action_type IN ('Meeting/Outreach')
    );

    -- Only pure thesis work triggers thesis signal
    v_has_thesis_signal := (
        v_combined_text ~ '(thesis|conviction|evidence review|thesis update|conviction assessment|framework.*evolving|hypothesis.*test)'
        OR v_action_type IN ('Thesis Update')
        OR (v_action_type = 'Content Follow-up')
    );

    -- Bucket 1: Discover New
    IF v_has_new_company_signal THEN v_b1_score := v_b1_score + 0.4; END IF;
    IF v_action_type = 'Pipeline Action' THEN v_b1_score := v_b1_score + 0.3; END IF;
    IF v_combined_text ~ '(new|discover|scout|pipeline|first)' THEN v_b1_score := v_b1_score + 0.15; END IF;
    IF NOT v_has_portfolio_company AND v_company_notion_id IS NOT NULL THEN v_b1_score := v_b1_score + 0.2; END IF;

    -- Bucket 2: Deepen Existing (catches portfolio research)
    IF v_has_portfolio_company THEN v_b2_score := v_b2_score + 0.5; END IF;
    IF v_action_type IN ('Portfolio Check-in', 'Follow-on Eval') THEN v_b2_score := v_b2_score + 0.35; END IF;
    IF v_combined_text ~ '(portfolio|follow.on|ownership|check.in|ids|competitive intel|deepen|existing)' THEN v_b2_score := v_b2_score + 0.2; END IF;
    IF v_has_portfolio_research_signal THEN v_b2_score := v_b2_score + 0.45; END IF;

    -- Bucket 3: Expand Network
    IF v_has_network_signal AND v_combined_text ~ '(collective|devc|community|funnel)' THEN v_b3_score := v_b3_score + 0.4; END IF;
    IF v_action_type = 'Meeting/Outreach' THEN v_b3_score := v_b3_score + 0.3; END IF;
    IF v_combined_text ~ '(intro|connect|meet|network|relationship|outreach|share.*with|reach out)' THEN v_b3_score := v_b3_score + 0.2; END IF;

    -- Bucket 4: Thesis Evolution (only pure thesis work)
    IF v_has_thesis_signal AND NOT v_has_portfolio_research_signal THEN v_b4_score := v_b4_score + 0.3; END IF;
    IF v_action_type = 'Thesis Update' THEN v_b4_score := v_b4_score + 0.35; END IF;
    IF v_combined_text ~ '(thesis update|conviction.*assess|evidence.*review|evidence.*gap|contra signal)' THEN v_b4_score := v_b4_score + 0.2; END IF;
    IF v_action_type = 'Content Follow-up' THEN v_b4_score := v_b4_score + 0.15; END IF;
    IF v_action_type = 'Research' AND NOT v_has_portfolio_research_signal
       AND v_combined_text ~ '(thesis|conviction|evidence.*gather|hypothesis)' THEN
        v_b4_score := v_b4_score + 0.2;
    END IF;

    -- Fallback: Research without signals -> Discover New
    IF v_action_type = 'Research' AND v_b1_score = 0 AND v_b2_score = 0 AND v_b3_score = 0 AND v_b4_score = 0 THEN
        v_b1_score := 0.25;
    END IF;

    -- USER PRIORITY REBALANCING
    v_b2_score := v_b2_score * 1.5;  -- 50% boost for portfolio
    v_b3_score := v_b3_score * 1.3;  -- 30% boost for network
    v_b4_score := v_b4_score * 0.6;  -- 40% penalty for thesis

    v_b1_score := LEAST(v_b1_score, 1.0);
    v_b2_score := LEAST(v_b2_score, 1.0);
    v_b3_score := LEAST(v_b3_score, 1.0);
    v_b4_score := LEAST(v_b4_score, 1.0);

    RETURN QUERY
    SELECT bk.bk_name, bk.bk_conf, bk.bk_reason
    FROM (
        VALUES
            ('Discover New (Bucket 1)'::TEXT, v_b1_score,
             ('Signals: ' ||
                CASE WHEN v_has_new_company_signal THEN 'new_company ' ELSE '' END ||
                CASE WHEN v_action_type = 'Pipeline Action' THEN 'pipeline_action ' ELSE '' END ||
                CASE WHEN NOT v_has_portfolio_company AND v_company_notion_id IS NOT NULL THEN 'non_portfolio_company ' ELSE '' END
             )::TEXT),
            ('Deepen Existing (Bucket 2)'::TEXT, v_b2_score,
             ('Signals: ' ||
                CASE WHEN v_has_portfolio_company THEN 'portfolio_company ' ELSE '' END ||
                CASE WHEN v_action_type IN ('Portfolio Check-in', 'Follow-on Eval') THEN 'portfolio_action_type ' ELSE '' END ||
                CASE WHEN v_has_portfolio_research_signal THEN 'portfolio_research ' ELSE '' END
             )::TEXT),
            ('Expand Network (Bucket 3)'::TEXT, v_b3_score,
             ('Signals: ' ||
                CASE WHEN v_has_network_signal THEN 'network_keywords ' ELSE '' END ||
                CASE WHEN v_action_type = 'Meeting/Outreach' THEN 'meeting_outreach_type ' ELSE '' END
             )::TEXT),
            ('Thesis Evolution (Bucket 4)'::TEXT, v_b4_score,
             ('Signals: ' ||
                CASE WHEN v_has_thesis_signal THEN 'thesis_keywords ' ELSE '' END ||
                CASE WHEN v_action_type IN ('Thesis Update', 'Content Follow-up') THEN 'thesis_action_type ' ELSE '' END
             )::TEXT)
    ) AS bk(bk_name, bk_conf, bk_reason)
    WHERE bk.bk_conf > 0
    ORDER BY bk.bk_conf DESC;
END;
$$;


-- =============================================================================
-- FIX 3: Tag latent thesis connections
-- =============================================================================
-- Problem: 17+ actions connected to AI-Native Non-Consumption Markets by vector
--          similarity but had zero explicit thesis_connection tags.
-- Solution: For all thesis threads, find actions with cosine similarity > 0.75
--           but not tagged in thesis_connection. Append the thesis name.
--
-- Executed in 3 batches:
-- Batch 1: All theses, initial pass (40 connections tagged)
-- Batch 2: AI-Native Non-Consumption Markets targeted (24 more)
-- Batch 3: Agent-Friendly Codebase (9) + CLAW Stack (4) remaining > 0.80
--
-- Total: 77 latent connections created across all theses.


-- =============================================================================
-- FIX 4: Confirmation bias detection function
-- =============================================================================
-- Flags thesis threads with imbalanced evidence (FOR vs AGAINST ratio).
-- Thresholds: CRITICAL (0 contra), HIGH (>5x), MEDIUM (>3x), OK.

CREATE OR REPLACE FUNCTION detect_thesis_bias()
RETURNS TABLE(
  thesis_id int,
  thread_name text,
  for_count int,
  against_count int,
  ratio numeric,
  bias_flag text
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    tt.id,
    tt.thread_name,
    COALESCE(array_length(
      string_to_array(COALESCE(tt.evidence_for, ''), E'\n'), 1), 0) as for_count,
    COALESCE(array_length(
      string_to_array(COALESCE(tt.evidence_against, ''), E'\n'), 1), 0) as against_count,
    CASE WHEN COALESCE(array_length(
      string_to_array(COALESCE(tt.evidence_against, ''), E'\n'), 1), 0) = 0
    THEN 999.0
    ELSE ROUND(
      array_length(string_to_array(COALESCE(tt.evidence_for, ''), E'\n'), 1)::numeric /
      NULLIF(array_length(string_to_array(COALESCE(tt.evidence_against, ''), E'\n'), 1), 0), 2)
    END as ratio,
    CASE
      WHEN COALESCE(array_length(string_to_array(COALESCE(tt.evidence_against, ''), E'\n'), 1), 0) = 0
      THEN 'CRITICAL: Zero contra evidence'
      WHEN array_length(string_to_array(COALESCE(tt.evidence_for, ''), E'\n'), 1) >
           array_length(string_to_array(COALESCE(tt.evidence_against, ''), E'\n'), 1) * 5
      THEN 'HIGH: >5x FOR:AGAINST ratio'
      WHEN array_length(string_to_array(COALESCE(tt.evidence_for, ''), E'\n'), 1) >
           array_length(string_to_array(COALESCE(tt.evidence_against, ''), E'\n'), 1) * 3
      THEN 'MEDIUM: >3x FOR:AGAINST ratio'
      ELSE 'OK'
    END as bias_flag
  FROM thesis_threads tt
  WHERE tt.status IN ('Active', 'Exploring')
  ORDER BY ratio DESC;
END;
$$ LANGUAGE plpgsql;


-- =============================================================================
-- FIX 5: Refresh materialized views
-- =============================================================================
REFRESH MATERIALIZED VIEW action_scores;


-- =============================================================================
-- M6 LOOP 4: IRGI Writeback + thesis_connection Normalization
-- =============================================================================
-- Date: 2026-03-20
-- Executed by: Claude Opus 4.6 via Supabase MCP
-- Scope: Fix 2 issues from M6 Loop 3 verification
--   Fix 1: Write IRGI relevance scores to dedicated column
--   Fix 2: Normalize thesis_connection format (commas, plus signs, free-text)
-- =============================================================================


-- =============================================================================
-- FIX 2: Normalize thesis_connection Format (run BEFORE Fix 1)
-- =============================================================================
-- Problem: 115 actions had thesis_connection values in 4+ inconsistent formats.
--   - 60 single-value entries were free-text hypotheses (not thread names)
--   - 12 comma-delimited, 2 plus-delimited, 6 used short "Healthcare AI Agents"
--   - 23 pipe segments didn't resolve against thesis_threads.thread_name

-- Step 2a: Normalize "Healthcare AI Agents" to canonical "Healthcare AI Agents as Infrastructure"
UPDATE actions_queue
SET thesis_connection = REPLACE(thesis_connection, 'Healthcare AI Agents', 'Healthcare AI Agents as Infrastructure')
WHERE thesis_connection LIKE '%Healthcare AI Agents%'
  AND thesis_connection NOT LIKE '%Healthcare AI Agents as Infrastructure%';

-- Step 2b: Convert commas to pipes in hybrid comma+pipe entries
UPDATE actions_queue
SET thesis_connection = REPLACE(thesis_connection, ', ', '|')
WHERE thesis_connection LIKE '%,%'
  AND thesis_connection LIKE '%|%';

-- Step 2c: Convert commas to pipes in pure comma-delimited entries with valid thread names
UPDATE actions_queue
SET thesis_connection = REPLACE(thesis_connection, ', ', '|')
WHERE thesis_connection LIKE '%,%'
  AND thesis_connection NOT LIKE '%|%'
  AND (
    thesis_connection LIKE '%Agentic AI Infrastructure%'
    OR thesis_connection LIKE '%SaaS Death%'
    OR thesis_connection LIKE '%Healthcare AI%'
    OR thesis_connection LIKE '%Cybersecurity%'
    OR thesis_connection LIKE '%CLAW Stack%'
    OR thesis_connection LIKE '%Agent-Friendly%'
    OR thesis_connection LIKE '%USTOL%'
    OR thesis_connection LIKE '%AI-Native%'
  );

-- Step 2d: Convert " + " to "|" in plus-delimited entries
UPDATE actions_queue
SET thesis_connection = REPLACE(thesis_connection, ' + ', '|')
WHERE thesis_connection LIKE '% + %';

-- Step 2e: Fix remaining short "Healthcare AI Agents" created by + split
UPDATE actions_queue
SET thesis_connection = REPLACE(thesis_connection, 'Healthcare AI Agents', 'Healthcare AI Agents as Infrastructure')
WHERE thesis_connection LIKE '%|Healthcare AI Agents'
  OR thesis_connection LIKE 'Healthcare AI Agents|%'
  OR thesis_connection = 'Healthcare AI Agents';

-- Step 2f: Strip invalid segments from pipe-delimited entries, keeping only valid thread_names
WITH valid_thread_names AS (
  SELECT thread_name FROM thesis_threads
),
pipe_entries AS (
  SELECT aq.id, aq.thesis_connection
  FROM actions_queue aq
  WHERE aq.thesis_connection LIKE '%|%'
),
rebuilt AS (
  SELECT pe.id,
    STRING_AGG(seg.val, '|' ORDER BY seg.ord) AS clean_connection
  FROM pipe_entries pe,
    LATERAL unnest(string_to_array(pe.thesis_connection, '|')) WITH ORDINALITY AS seg(val, ord)
  WHERE EXISTS (SELECT 1 FROM valid_thread_names vtn WHERE vtn.thread_name = TRIM(seg.val))
  GROUP BY pe.id
)
UPDATE actions_queue aq
SET thesis_connection = r.clean_connection
FROM rebuilt r
WHERE aq.id = r.id
  AND aq.thesis_connection != r.clean_connection;

-- Step 2g: Move free-text hypothesis entries to scoring_factors, NULL thesis_connection
-- For entries with broken pipe formatting (originally comma-containing free-text)
UPDATE actions_queue
SET
  scoring_factors = COALESCE(scoring_factors, '{}'::jsonb) || jsonb_build_object('legacy_thesis_note', REPLACE(thesis_connection, '|', ', ')),
  thesis_connection = NULL
WHERE id IN (38, 74, 76);

-- For all remaining single-value free-text entries that don't match any thread_name
UPDATE actions_queue aq
SET
  scoring_factors = COALESCE(scoring_factors, '{}'::jsonb) || jsonb_build_object('legacy_thesis_note', thesis_connection),
  thesis_connection = NULL
WHERE aq.thesis_connection IS NOT NULL
  AND aq.thesis_connection NOT LIKE '%|%'
  AND NOT EXISTS (
    SELECT 1 FROM thesis_threads tt
    WHERE tt.thread_name = aq.thesis_connection
  );


-- =============================================================================
-- FIX 1: IRGI Relevance Score Writeback
-- =============================================================================
-- Problem: relevance_score column holds M5 user_priority_score values (0-10),
--   not IRGI thesis relevance scores (0-1). Correlation was 0.954.
-- Solution: Add dedicated irgi_relevance_score column, compute via IRGI function.

-- Step 1a: Add column
ALTER TABLE actions_queue ADD COLUMN IF NOT EXISTS irgi_relevance_score numeric;

-- Step 1b: Compute IRGI scores for all actions (3 batches)
UPDATE actions_queue aq
SET irgi_relevance_score = (
  SELECT MAX(s.relevance_score) FROM score_action_thesis_relevance(aq.id) s
)
WHERE aq.id BETWEEN 1 AND 40;

UPDATE actions_queue aq
SET irgi_relevance_score = (
  SELECT MAX(s.relevance_score) FROM score_action_thesis_relevance(aq.id) s
)
WHERE aq.id BETWEEN 41 AND 80;

UPDATE actions_queue aq
SET irgi_relevance_score = (
  SELECT MAX(s.relevance_score) FROM score_action_thesis_relevance(aq.id) s
)
WHERE aq.id BETWEEN 81 AND 115;


-- =============================================================================
-- Refresh materialized view post-Loop 4
-- =============================================================================
REFRESH MATERIALIZED VIEW action_scores;


-- =============================================================================
-- Validation Queries (Loop 4)
-- =============================================================================

-- V1: IRGI scores in 0-1 range
-- Expected: min ~0.40, max ~0.89, avg ~0.58, stddev ~0.17, scored=115
SELECT min(irgi_relevance_score), max(irgi_relevance_score),
  avg(irgi_relevance_score)::numeric(5,4), stddev(irgi_relevance_score)::numeric(5,4),
  count(*) FILTER (WHERE irgi_relevance_score IS NOT NULL) as scored
FROM actions_queue;

-- V2: thesis_connection should all resolve (pipe-delimited)
-- Expected: 143 total, 143 resolved, 0 unresolved
WITH pipe_segments AS (
  SELECT aq.id, unnest(string_to_array(aq.thesis_connection, '|')) AS segment
  FROM actions_queue aq WHERE aq.thesis_connection LIKE '%|%'
)
SELECT count(*) as total,
  count(*) FILTER (WHERE EXISTS (SELECT 1 FROM thesis_threads tt WHERE tt.thread_name = TRIM(ps.segment))) as resolved,
  count(*) FILTER (WHERE NOT EXISTS (SELECT 1 FROM thesis_threads tt WHERE tt.thread_name = TRIM(ps.segment))) as unresolved
FROM pipe_segments ps;

-- V3: Correlation should be moderate, NOT 0.95
-- Expected: -0.323 (weak negative)
SELECT corr(user_priority_score::float, irgi_relevance_score::float)::numeric(5,3)
FROM actions_queue
WHERE user_priority_score IS NOT NULL AND irgi_relevance_score IS NOT NULL;
