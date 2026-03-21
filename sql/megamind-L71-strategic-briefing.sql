-- Megamind L71: format_strategic_briefing()
-- Date: 2026-03-21
-- Purpose: Transform raw JSON from generate_strategic_narrative() into a readable
--          chief-of-staff memo. Produces plain TEXT that Aakash can read in 2 minutes
--          and know what to do today.
--
-- Sections:
--   1. NEEDS YOUR ATTENTION — Top 7 urgent portfolio companies (runway, Red, P0)
--   2. UPCOMING DECISIONS — Top 8 actions needing accept/dismiss with recommendations
--   3. PORTFOLIO HEALTH — Follow-on decisions (SPR/PR vs Token/Zero), unanswered questions
--   4. PEOPLE TO REACH OUT TO — Overdue obligations (I owe / they owe), upcoming, key contacts
--
-- Design: SQL produces the MEMO directly — no agent layer needed for formatting.
-- The function calls generate_strategic_narrative() 3x internally (portfolio_attention,
-- upcoming_decisions, network_priorities) and formats all data into readable text.

CREATE OR REPLACE FUNCTION format_strategic_briefing(p_date date DEFAULT CURRENT_DATE)
RETURNS TEXT
LANGUAGE plpgsql AS $$
DECLARE
  v_portfolio JSONB;
  v_decisions JSONB;
  v_network JSONB;
  v_memo TEXT := '';
  v_section TEXT;
  r RECORD;
  v_counter INT;
BEGIN
  v_portfolio := generate_strategic_narrative('portfolio_attention');
  v_decisions := generate_strategic_narrative('upcoming_decisions');
  v_network := generate_strategic_narrative('network_priorities');

  -- HEADER
  v_memo := v_memo || E'━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n';
  v_memo := v_memo || '  STRATEGIC BRIEFING — ' || to_char(p_date, 'DD Mon YYYY') || E'\n';
  v_memo := v_memo || E'  AI Chief of Staff | Megamind\n';
  v_memo := v_memo || E'━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n';

  v_memo := v_memo || 'Portfolio: $' || COALESCE(
    to_char((v_portfolio->'headline_data'->>'total_portfolio_fmv')::numeric / 1000000, 'FM9.99') || 'M FMV', 'unknown') || E'\n';
  v_memo := v_memo || 'Best-case exposure: $' || COALESCE(
    to_char((v_portfolio->'headline_data'->>'total_best_case')::numeric / 1000000, 'FM999.9') || 'M', 'unknown') || E'\n';
  v_memo := v_memo || (v_portfolio->'headline_data'->>'red_count') || ' Red, '
    || (v_portfolio->'headline_data'->>'yellow_count') || ' Yellow companies. '
    || '$' || COALESCE(to_char((v_portfolio->'headline_data'->>'fmv_at_risk')::numeric / 1000000, 'FM9.99') || 'M FMV at risk.', 'unknown') || E'\n';
  v_memo := v_memo || 'Convergence: ' || (v_decisions->'convergence_projection'->>'proposed_remaining') || ' proposed actions pending, '
    || (v_decisions->'convergence_projection'->>'decisions_to_80pct') || ' decisions to reach 80%.' || E'\n\n';

  -- SECTION 1: NEEDS YOUR ATTENTION
  v_memo := v_memo || E'## 1. NEEDS YOUR ATTENTION\n';
  v_memo := v_memo || E'─────────────────────────────────────────────────\n';

  v_counter := 0;
  FOR r IN
    SELECT
      elem->>'company' as company,
      elem->>'health' as health,
      round((elem->>'ownership_pct')::numeric, 1) as ownership,
      elem->>'fumes_date' as fumes_date,
      (elem->>'days_until_fumes') as days_fumes_raw,
      elem->>'follow_on_decision' as follow_on,
      elem->>'scale_of_business' as scale,
      elem->>'key_questions' as key_q,
      elem->>'high_impact' as high_impact,
      COALESCE((elem->>'fmv_carried')::numeric, 0) as fmv,
      COALESCE((elem->>'best_case_value')::numeric, 0) as best_val,
      COALESCE((elem->>'cash_in_bank')::numeric, -1) as cash,
      elem->>'ops_priority' as ops_prio,
      elem->>'note_on_deployment' as deploy_notes
    FROM jsonb_array_elements(v_portfolio->'urgent_attention') elem
    ORDER BY
      CASE WHEN elem->>'fumes_date' IS NOT NULL AND (elem->>'days_until_fumes')::int < 90 THEN 0 ELSE 1 END,
      CASE elem->>'health' WHEN 'Red' THEN 0 ELSE 1 END,
      CASE WHEN elem->>'ops_priority' LIKE 'P0%' THEN 0 WHEN elem->>'ops_priority' = 'P1' THEN 1 ELSE 2 END,
      (COALESCE((elem->>'ownership_pct')::numeric, 0)) DESC
    LIMIT 7
  LOOP
    v_counter := v_counter + 1;
    v_memo := v_memo || E'\n' || v_counter || '. ' || r.company;
    v_memo := v_memo || ' [' || r.health || ']';
    IF r.ops_prio IS NOT NULL THEN
      v_memo := v_memo || ' ' || r.ops_prio;
    END IF;
    v_memo := v_memo || ' | ' || r.ownership || '% ownership';
    IF r.fmv > 0 THEN
      v_memo := v_memo || ' | $' || to_char(r.fmv, 'FM999,999') || ' FMV';
    END IF;
    v_memo := v_memo || E'\n';

    IF r.fumes_date IS NOT NULL AND r.days_fumes_raw IS NOT NULL THEN
      IF (r.days_fumes_raw)::int < 0 THEN
        v_memo := v_memo || '   RUNWAY EXPIRED ' || abs((r.days_fumes_raw)::int) || ' days ago (' || r.fumes_date || ')' || E'\n';
      ELSE
        v_memo := v_memo || '   RUNWAY: ' || (r.days_fumes_raw)::int || ' days remaining (fumes ' || r.fumes_date || ')' || E'\n';
      END IF;
    END IF;

    IF r.follow_on IS NOT NULL THEN
      v_memo := v_memo || '   Follow-on: ' || r.follow_on;
      IF r.deploy_notes IS NOT NULL THEN
        v_memo := v_memo || ' — ' || LEFT(r.deploy_notes, 120);
      END IF;
      v_memo := v_memo || E'\n';
    END IF;

    IF r.scale IS NOT NULL AND r.scale != '' AND r.scale != 'NA' THEN
      v_memo := v_memo || '   Scale: ' || r.scale || E'\n';
    END IF;

    IF r.best_val > 0 THEN
      v_memo := v_memo || '   Best case: $' || to_char(r.best_val / 1000, 'FM999,999') || 'K' || E'\n';
    END IF;

    IF r.key_q IS NOT NULL AND LENGTH(r.key_q) > 5 THEN
      v_memo := v_memo || '   Key question: ' || LEFT(REPLACE(SPLIT_PART(r.key_q, E'\n', 1), '- ', ''), 120) || E'\n';
    END IF;

    IF r.high_impact IS NOT NULL AND LENGTH(r.high_impact) > 3 THEN
      v_memo := v_memo || '   Your lever: ' || LEFT(REPLACE(r.high_impact, E'\n', ' | '), 120) || E'\n';
    END IF;
  END LOOP;

  v_memo := v_memo || E'\n';

  -- SECTION 2: UPCOMING DECISIONS
  v_memo := v_memo || E'\n## 2. UPCOMING DECISIONS\n';
  v_memo := v_memo || E'─────────────────────────────────────────────────\n';

  v_counter := 0;
  FOR r IN
    SELECT
      elem->>'action' as action,
      elem->>'type' as atype,
      elem->>'priority' as priority,
      (elem->>'strategic_score')::numeric as score,
      (elem->>'days_open')::int as days_open,
      elem->>'recommendation' as recommendation,
      elem->'company_context'->>'company_name' as related_company,
      elem->'company_context'->>'health' as company_health
    FROM jsonb_array_elements(v_decisions->'decision_queue') elem
    ORDER BY (elem->>'impact_score')::numeric DESC
    LIMIT 8
  LOOP
    v_counter := v_counter + 1;
    v_memo := v_memo || E'\n' || v_counter || '. [' || COALESCE(r.priority, '?') || '] ' || LEFT(r.action, 180) || E'\n';
    v_memo := v_memo || '   Type: ' || COALESCE(r.atype, 'Unknown') || ' | Score: ' || r.score || ' | Open ' || r.days_open || 'd' || E'\n';
    IF r.related_company IS NOT NULL THEN
      v_memo := v_memo || '   Company: ' || r.related_company || ' [' || COALESCE(r.company_health, '?') || ']' || E'\n';
    END IF;
    IF r.recommendation IS NOT NULL AND LENGTH(r.recommendation) > 5 THEN
      v_memo := v_memo || '   -> ' || LEFT(r.recommendation, 150) || E'\n';
    END IF;
  END LOOP;

  IF jsonb_array_length(COALESCE(v_decisions->'stale_candidates', '[]'::jsonb)) > 0 THEN
    v_memo := v_memo || E'\n   STALE (21+ days, no obligation): ';
    v_section := '';
    FOR r IN
      SELECT elem->>'action' as action, (elem->>'days_open')::int as days_open
      FROM jsonb_array_elements(v_decisions->'stale_candidates') elem
      ORDER BY (elem->>'days_open')::int DESC LIMIT 5
    LOOP
      IF v_section != '' THEN v_section := v_section || '; '; END IF;
      v_section := v_section || LEFT(r.action, 60) || ' (' || r.days_open || 'd)';
    END LOOP;
    v_memo := v_memo || v_section || E'\n';
  END IF;

  v_memo := v_memo || E'\n';

  -- SECTION 3: PORTFOLIO HEALTH - FOLLOW-ON DECISIONS
  v_memo := v_memo || E'\n## 3. PORTFOLIO HEALTH — FOLLOW-ON DECISIONS\n';
  v_memo := v_memo || E'─────────────────────────────────────────────────\n';

  v_memo := v_memo || E'\n  ACTIVE FOLLOW-ON (SPR/PR):\n';
  FOR r IN
    SELECT
      elem->>'company' as company,
      elem->>'health' as health,
      round((elem->>'ownership_pct')::numeric, 1) as ownership,
      (elem->>'room_to_deploy')::numeric as room,
      COALESCE((elem->>'best_case_value')::numeric, 0) as best_val,
      elem->>'notes' as notes
    FROM jsonb_array_elements(v_decisions->'investment_decisions') elem
    WHERE elem->>'decision' IN ('SPR', 'PR')
    ORDER BY (elem->>'ownership_pct')::numeric DESC
  LOOP
    v_memo := v_memo || '  - ' || r.company || ' [' || r.health || '] '
      || r.ownership || '% own';
    IF r.room IS NOT NULL AND r.room > 0 THEN
      v_memo := v_memo || ' | $' || to_char(r.room, 'FM999,999') || ' deployable';
    END IF;
    IF r.best_val > 0 THEN
      v_memo := v_memo || ' | best: $' || to_char(r.best_val / 1000000, 'FM9.9') || 'M';
    END IF;
    v_memo := v_memo || E'\n';
    IF r.notes IS NOT NULL THEN
      v_memo := v_memo || '    ' || LEFT(r.notes, 120) || E'\n';
    END IF;
  END LOOP;

  v_memo := v_memo || E'\n  TOKEN/ZERO (minimal/no follow-on):\n';
  FOR r IN
    SELECT
      elem->>'company' as company,
      elem->>'health' as health,
      round((elem->>'ownership_pct')::numeric, 1) as ownership,
      COALESCE((elem->>'best_case_value')::numeric, 0) as best_val
    FROM jsonb_array_elements(v_decisions->'investment_decisions') elem
    WHERE elem->>'decision' = 'Token/Zero'
    ORDER BY (elem->>'ownership_pct')::numeric DESC
    LIMIT 10
  LOOP
    v_memo := v_memo || '  - ' || r.company || ' [' || r.health || '] '
      || r.ownership || '% own';
    IF r.best_val > 0 THEN
      v_memo := v_memo || ' | best: $' || to_char(r.best_val / 1000000, 'FM9.9') || 'M';
    END IF;
    v_memo := v_memo || E'\n';
  END LOOP;

  IF jsonb_array_length(COALESCE(v_portfolio->'unaddressed_questions', '[]'::jsonb)) > 0 THEN
    v_memo := v_memo || E'\n  UNANSWERED KEY QUESTIONS (no active actions):\n';
    v_counter := 0;
    FOR r IN
      SELECT
        elem->>'company' as company,
        elem->>'health' as health,
        round((elem->>'ownership_pct')::numeric, 1) as ownership,
        elem->>'questions' as questions
      FROM jsonb_array_elements(v_portfolio->'unaddressed_questions') elem
      ORDER BY (elem->>'ownership_pct')::numeric DESC
      LIMIT 5
    LOOP
      v_counter := v_counter + 1;
      v_memo := v_memo || '  ' || v_counter || '. ' || r.company || ' [' || r.health || '] '
        || r.ownership || '%: '
        || LEFT(REPLACE(SPLIT_PART(r.questions, E'\n', 1), '- ', ''), 130) || E'\n';
    END LOOP;
  END IF;

  v_memo := v_memo || E'\n';

  -- SECTION 4: PEOPLE TO REACH OUT TO
  v_memo := v_memo || E'\n## 4. PEOPLE TO REACH OUT TO\n';
  v_memo := v_memo || E'─────────────────────────────────────────────────\n';

  v_memo := v_memo || E'\n  YOU OWE THEM (overdue):\n';
  v_counter := 0;
  FOR r IN
    SELECT
      elem->>'person' as person,
      elem->>'role' as role,
      elem->>'description' as description,
      (elem->>'days_overdue')::int as days_overdue
    FROM jsonb_array_elements(v_network->'obligation_hotspots') elem
    WHERE elem->>'type' = 'I_OWE_THEM' AND elem->>'status' IN ('overdue', 'escalated')
    ORDER BY (elem->>'days_overdue')::int DESC NULLS LAST
    LIMIT 7
  LOOP
    v_counter := v_counter + 1;
    v_memo := v_memo || '  ' || v_counter || '. ' || r.person;
    IF r.role IS NOT NULL THEN
      v_memo := v_memo || ' (' || LEFT(r.role, 40) || ')';
    END IF;
    v_memo := v_memo || ' — ' || COALESCE(r.days_overdue::text, '?') || 'd overdue' || E'\n';
    v_memo := v_memo || '     ' || LEFT(r.description, 130) || E'\n';
  END LOOP;

  v_memo := v_memo || E'\n  THEY OWE YOU (follow up):\n';
  v_counter := 0;
  FOR r IN
    SELECT
      elem->>'person' as person,
      elem->>'role' as role,
      elem->>'description' as description,
      (elem->>'days_overdue')::int as days_overdue
    FROM jsonb_array_elements(v_network->'obligation_hotspots') elem
    WHERE elem->>'type' = 'THEY_OWE_ME' AND elem->>'status' IN ('overdue', 'escalated')
    ORDER BY (elem->>'days_overdue')::int DESC NULLS LAST
    LIMIT 5
  LOOP
    v_counter := v_counter + 1;
    v_memo := v_memo || '  ' || v_counter || '. ' || r.person;
    IF r.role IS NOT NULL THEN
      v_memo := v_memo || ' (' || LEFT(r.role, 40) || ')';
    END IF;
    v_memo := v_memo || ' — ' || COALESCE(r.days_overdue::text, '?') || 'd overdue' || E'\n';
    v_memo := v_memo || '     ' || LEFT(r.description, 130) || E'\n';
  END LOOP;

  v_memo := v_memo || E'\n  COMING UP (pending):\n';
  v_counter := 0;
  FOR r IN
    SELECT
      elem->>'person' as person,
      elem->>'role' as role,
      elem->>'description' as description,
      elem->>'due_date' as due_date
    FROM jsonb_array_elements(v_network->'obligation_hotspots') elem
    WHERE elem->>'status' = 'pending'
    ORDER BY (elem->>'blended_priority')::numeric DESC
    LIMIT 5
  LOOP
    v_counter := v_counter + 1;
    v_memo := v_memo || '  ' || v_counter || '. ' || r.person;
    IF r.role IS NOT NULL THEN
      v_memo := v_memo || ' (' || LEFT(r.role, 40) || ')';
    END IF;
    v_memo := v_memo || ' — due ' || LEFT(r.due_date, 10) || E'\n';
    v_memo := v_memo || '     ' || LEFT(r.description, 130) || E'\n';
  END LOOP;

  v_memo := v_memo || E'\n  KEY PORTFOLIO CONTACTS (no recent interaction):\n';
  v_counter := 0;
  FOR r IN
    SELECT
      elem->>'name' as person,
      elem->>'narrative' as narrative,
      (elem->>'importance')::numeric as importance
    FROM jsonb_array_elements(v_network->'top_strategic_people') elem
    WHERE (elem->>'portfolio_connections')::int > 0
      AND (elem->>'obligations')::int = 0
    ORDER BY (elem->>'importance')::numeric DESC
    LIMIT 5
  LOOP
    v_counter := v_counter + 1;
    v_memo := v_memo || '  ' || v_counter || '. ' || r.narrative || E'\n';
  END LOOP;

  -- FOOTER
  v_memo := v_memo || E'\n';
  v_memo := v_memo || E'━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n';
  v_memo := v_memo || 'Generated: ' || NOW()::text || E'\n';
  v_memo := v_memo || E'Source: Megamind format_strategic_briefing() v1.0-L71\n';
  v_memo := v_memo || E'━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n';

  RETURN v_memo;
END;
$$;
