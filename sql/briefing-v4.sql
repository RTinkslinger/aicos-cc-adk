-- Megamind Strategic Briefing v4.0
-- Changes from v3.0:
--   1. Fixed NULL return bug (chr(10) instead of E'\n' escaping)
--   2. Rich "Since Last Briefing" diff (Red, Actions, Convergence, Obligations deltas)
--   3. Silent Winners get action recommendations (schedule founder check-in, investigate key Q)
--   4. New Section 2.5: Key Questions Needing Action (top 10 companies with unanswered Qs)
--   5. New Section 5: Obligation Follow-ups (surfacing obligation_followup actions)
--   6. All NULL-prone concatenations wrapped in COALESCE

CREATE OR REPLACE FUNCTION format_strategic_briefing(p_date DATE DEFAULT CURRENT_DATE)
RETURNS TEXT LANGUAGE plpgsql AS $$
DECLARE
  v_portfolio JSONB;
  v_decisions JSONB;
  v_network JSONB;
  v_memo TEXT := '';
  r RECORD;
  v_counter INT;
  v_contradictions_found BOOLEAN := FALSE;
  v_prev_briefing RECORD;
  NL TEXT := chr(10);
  HR TEXT := '─────────────────────────────────────────────────';
BEGIN
  v_portfolio := generate_strategic_narrative('portfolio_attention');
  v_decisions := generate_strategic_narrative('upcoming_decisions');
  v_network := generate_strategic_narrative('network_priorities');

  SELECT * INTO v_prev_briefing FROM briefing_history
  WHERE briefing_date < p_date ORDER BY briefing_date DESC LIMIT 1;

  -- ═══ HEADER ═══
  v_memo := v_memo || '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━' || NL;
  v_memo := v_memo || '  STRATEGIC BRIEFING — ' || to_char(p_date, 'DD Mon YYYY') || NL;
  v_memo := v_memo || '  AI Chief of Staff | Megamind v4.0' || NL;
  v_memo := v_memo || '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━' || NL || NL;
  v_memo := v_memo || 'Portfolio: $' || COALESCE(to_char((v_portfolio->'headline_data'->>'total_portfolio_fmv')::numeric/1000000,'FM9.99') || 'M FMV', 'unknown') || NL;
  v_memo := v_memo || 'Best-case: $' || COALESCE(to_char((v_portfolio->'headline_data'->>'total_best_case')::numeric/1000000,'FM999.9') || 'M', 'unknown') || NL;
  v_memo := v_memo || COALESCE((v_portfolio->'headline_data'->>'red_count'),'?') || ' Red, ';
  v_memo := v_memo || COALESCE((v_portfolio->'headline_data'->>'yellow_count'),'?') || ' Yellow. ';
  v_memo := v_memo || '$' || COALESCE(to_char((v_portfolio->'headline_data'->>'fmv_at_risk')::numeric/1000000,'FM9.99') || 'M at risk.', 'unknown') || NL;
  v_memo := v_memo || 'Convergence: ' || COALESCE((v_decisions->'convergence_projection'->>'proposed_remaining'),'?');
  v_memo := v_memo || ' proposed, ' || COALESCE((v_decisions->'convergence_projection'->>'decisions_to_80pct'),'?') || ' decisions to 80%.' || NL;

  -- ═══ SINCE LAST BRIEFING ═══
  IF v_prev_briefing.assessment_jsonb IS NOT NULL THEN
    v_memo := v_memo || NL || '  SINCE ' || to_char(v_prev_briefing.briefing_date, 'DD Mon') || ':' || NL;

    DECLARE
      v_pr INT := COALESCE((v_prev_briefing.assessment_jsonb->>'red_count')::int, 0);
      v_cr INT := COALESCE((v_portfolio->'headline_data'->>'red_count')::int, 0);
      v_pp INT := COALESCE((v_prev_briefing.assessment_jsonb->>'proposed_remaining')::int, 0);
      v_cp INT := COALESCE((v_decisions->'convergence_projection'->>'proposed_remaining')::int, 0);
      v_pcv NUMERIC := COALESCE((v_prev_briefing.assessment_jsonb->>'convergence_ratio')::numeric, 0);
      v_ccv NUMERIC;
      v_po INT := COALESCE((v_prev_briefing.assessment_jsonb->>'overdue_obligations')::int, 0);
      v_co INT;
    BEGIN
      IF v_cr != v_pr THEN
        v_memo := v_memo || '  Red: ' || v_pr || ' -> ' || v_cr;
        v_memo := v_memo || CASE WHEN v_cr > v_pr THEN ' (WORSE)' ELSE ' (better)' END || NL;
      END IF;
      IF v_cp != v_pp THEN
        v_memo := v_memo || '  Actions: ' || v_pp || ' -> ' || v_cp;
        v_memo := v_memo || CASE WHEN v_cp < v_pp THEN ' (resolved ' || (v_pp - v_cp) || ')' ELSE ' (+' || (v_cp - v_pp) || ' new)' END || NL;
      END IF;
      SELECT convergence_ratio::numeric INTO v_ccv FROM megamind_convergence LIMIT 1;
      IF v_ccv IS NOT NULL AND abs(v_ccv - v_pcv) > 0.01 THEN
        v_memo := v_memo || '  Convergence: ' || round(v_pcv * 100, 1) || '% -> ' || round(v_ccv * 100, 1) || '%' || NL;
      END IF;
      SELECT count(*) INTO v_co FROM obligations WHERE status IN ('overdue','escalated');
      IF v_co != v_po THEN
        v_memo := v_memo || '  Overdue obligations: ' || v_po || ' -> ' || v_co || NL;
      END IF;
    END;
  END IF;
  v_memo := v_memo || NL;

  -- ═══ SECTION 1: NEEDS YOUR ATTENTION ═══
  v_memo := v_memo || '## 1. NEEDS YOUR ATTENTION' || NL || HR || NL;
  v_counter := 0;
  FOR r IN
    SELECT elem->>'company' as company, elem->>'health' as health,
      round((elem->>'ownership_pct')::numeric, 1) as ownership,
      elem->>'fumes_date' as fumes_date, elem->>'days_until_fumes' as dfr,
      elem->>'follow_on_decision' as follow_on,
      elem->>'scale_of_business' as scale,
      elem->>'key_questions' as key_q, elem->>'high_impact' as hi,
      COALESCE((elem->>'fmv_carried')::numeric, 0) as fmv,
      COALESCE((elem->>'best_case_value')::numeric, 0) as bv,
      elem->>'ops_priority' as ops_prio, elem->>'note_on_deployment' as dn
    FROM jsonb_array_elements(v_portfolio->'urgent_attention') elem
    ORDER BY
      CASE WHEN elem->>'fumes_date' IS NOT NULL AND (elem->>'days_until_fumes')::int < 90 THEN 0 ELSE 1 END,
      CASE elem->>'health' WHEN 'Red' THEN 0 ELSE 1 END,
      CASE WHEN elem->>'ops_priority' LIKE 'P0%' THEN 0 WHEN elem->>'ops_priority' = 'P1' THEN 1 ELSE 2 END,
      COALESCE((elem->>'ownership_pct')::numeric, 0) DESC
    LIMIT 7
  LOOP
    v_counter := v_counter + 1;
    v_memo := v_memo || NL || v_counter || '. ' || COALESCE(r.company, '?') || ' [' || COALESCE(r.health, '?') || ']';
    IF r.ops_prio IS NOT NULL THEN v_memo := v_memo || ' ' || r.ops_prio; END IF;
    v_memo := v_memo || ' | ' || COALESCE(r.ownership::text, '?') || '% | $' || to_char(r.fmv, 'FM999,999') || ' FMV' || NL;
    IF r.fumes_date IS NOT NULL AND r.dfr IS NOT NULL THEN
      IF (r.dfr)::int < 0 THEN
        v_memo := v_memo || '   RUNWAY EXPIRED ' || abs((r.dfr)::int) || 'd ago' || NL;
      ELSE
        v_memo := v_memo || '   RUNWAY: ' || (r.dfr)::int || 'd' || NL;
      END IF;
    END IF;
    IF r.follow_on IS NOT NULL THEN
      v_memo := v_memo || '   Follow-on: ' || r.follow_on;
      IF r.dn IS NOT NULL THEN v_memo := v_memo || ' — ' || LEFT(r.dn, 100); END IF;
      v_memo := v_memo || NL;
    END IF;
    IF r.key_q IS NOT NULL AND LENGTH(r.key_q) > 5 THEN
      v_memo := v_memo || '   Key Q: ' || LEFT(REPLACE(SPLIT_PART(r.key_q, NL, 1), '- ', ''), 100) || NL;
    END IF;
  END LOOP;
  v_memo := v_memo || NL;

  -- ═══ SECTION 1.5: CONTRADICTIONS ═══
  v_memo := v_memo || NL || '## 1.5 STRATEGIC CONTRADICTIONS' || NL || HR || NL || NL;

  -- Type 1: Red + SPR
  FOR r IN SELECT p.portfolio_co, p.follow_on_decision, round(p.ownership_pct::numeric * 100, 2) as o, COALESCE(p.fmv_carried, 0) as fmv
    FROM portfolio p WHERE p.health = 'Red' AND p.follow_on_decision IN ('SPR','PR') ORDER BY p.ownership_pct DESC LOOP
    v_contradictions_found := TRUE;
    v_memo := v_memo || '  X ' || r.portfolio_co || ' [Red + ' || r.follow_on_decision || '] ' || r.o || '% | $' || to_char(r.fmv, 'FM999,999') || ' FMV' || NL;
    v_memo := v_memo || '    Doubling down on struggling company.' || NL;
  END LOOP;

  -- Type 2: Red P0/P1 + zero actions
  FOR r IN SELECT p.portfolio_co, COALESCE(p.ops_prio, '?') as ops_prio, round(p.ownership_pct::numeric * 100, 2) as o, COALESCE(p.fmv_carried, 0) as fmv
    FROM portfolio p WHERE p.health = 'Red' AND (p.ops_prio LIKE 'P0%' OR p.ops_prio = 'P1')
    AND NOT EXISTS (SELECT 1 FROM actions_queue aq WHERE aq.status IN ('Proposed','Accepted')
      AND (aq.action ILIKE '%' || LEFT(p.portfolio_co, 15) || '%' OR aq.company_notion_id = p.notion_page_id))
    ORDER BY p.ownership_pct DESC LIMIT 5 LOOP
    v_contradictions_found := TRUE;
    v_memo := v_memo || '  X ' || r.portfolio_co || ' [Red, ' || r.ops_prio || '] ' || r.o || '% | $' || to_char(r.fmv, 'FM999,999') || ' FMV' || NL;
    v_memo := v_memo || '    High-priority Red, ZERO open actions.' || NL;
  END LOOP;

  -- Type 3: Expired fumes
  FOR r IN SELECT p.portfolio_co, COALESCE(p.health, '?') as health, p.fumes_date, (CURRENT_DATE - p.fumes_date) as d
    FROM portfolio p WHERE p.fumes_date IS NOT NULL AND p.fumes_date < CURRENT_DATE - INTERVAL '180 days' LIMIT 3 LOOP
    v_contradictions_found := TRUE;
    v_memo := v_memo || '  X ' || r.portfolio_co || ' [' || r.health || '] fumes ' || r.fumes_date || ' (' || r.d || 'd expired)' || NL;
  END LOOP;

  -- Type 4: Silent winners WITH RECOMMENDATIONS
  FOR r IN SELECT p.portfolio_co, round(p.ownership_pct::numeric * 100, 2) as o, COALESCE(p.fmv_carried::numeric, 0) as fmv,
    p.check_in_cadence, p.key_questions
    FROM portfolio p WHERE p.health = 'Green' AND p.ownership_pct > 0.02
    AND NOT EXISTS (SELECT 1 FROM actions_queue aq WHERE aq.status IN ('Proposed','Accepted') AND aq.action ILIKE '%' || p.portfolio_co || '%')
    ORDER BY p.ownership_pct DESC LIMIT 5 LOOP
    v_contradictions_found := TRUE;
    v_memo := v_memo || '  X ' || r.portfolio_co || ' [Green, ' || r.o || '%] $' || to_char(r.fmv, 'FM999,999') || ' FMV' || NL;
    v_memo := v_memo || '    Silent winner: high ownership, no actions.';
    IF r.check_in_cadence IS NOT NULL THEN v_memo := v_memo || ' Cadence: ' || r.check_in_cadence || '.'; END IF;
    v_memo := v_memo || NL;
    v_memo := v_memo || '    -> Schedule founder check-in' || NL;
    IF r.key_questions IS NOT NULL AND LENGTH(r.key_questions) > 5 THEN
      v_memo := v_memo || '    -> Investigate: ' || LEFT(REPLACE(SPLIT_PART(r.key_questions, NL, 1), '- ', ''), 100) || NL;
    END IF;
  END LOOP;

  -- Type 5: SPR idle (non-Red)
  FOR r IN SELECT p.portfolio_co, COALESCE(p.health, '?') as health, round(p.ownership_pct::numeric * 100, 2) as o,
    p.follow_on_decision, COALESCE(p.room_to_deploy::numeric, 0) as room
    FROM portfolio p WHERE p.follow_on_decision IN ('SPR','PR') AND p.health != 'Red'
    AND NOT EXISTS (SELECT 1 FROM actions_queue aq WHERE aq.status IN ('Proposed','Accepted') AND aq.action ILIKE '%' || p.portfolio_co || '%')
    ORDER BY p.room_to_deploy DESC NULLS LAST LIMIT 5 LOOP
    v_contradictions_found := TRUE;
    v_memo := v_memo || '  X ' || r.portfolio_co || ' [' || r.health || ', ' || COALESCE(r.follow_on_decision, '?') || '] ' || r.o || '%' || NL;
    v_memo := v_memo || '    $' || to_char(r.room, 'FM999,999') || ' deployable, no actions.' || NL;
  END LOOP;

  IF NOT v_contradictions_found THEN v_memo := v_memo || '  No contradictions.' || NL; END IF;
  v_memo := v_memo || NL;

  -- ═══ SECTION 2: DECISIONS ═══
  v_memo := v_memo || NL || '## 2. UPCOMING DECISIONS' || NL || HR || NL;
  v_counter := 0;
  FOR r IN SELECT elem->>'action' as a, elem->>'type' as t, elem->>'priority' as p,
    COALESCE((elem->>'strategic_score')::numeric, 0) as s,
    COALESCE((elem->>'days_open')::int, 0) as d,
    elem->>'recommendation' as rec,
    elem->'company_context'->>'company_name' as co,
    elem->'company_context'->>'health' as ch
    FROM jsonb_array_elements(v_decisions->'decision_queue') elem
    ORDER BY COALESCE((elem->>'impact_score')::numeric, 0) DESC LIMIT 8
  LOOP
    v_counter := v_counter + 1;
    v_memo := v_memo || NL || v_counter || '. [' || COALESCE(r.p, '?') || '] ' || LEFT(COALESCE(r.a, '?'), 150) || NL;
    v_memo := v_memo || '   ' || COALESCE(r.t, '?') || ' | Score: ' || r.s || ' | Open ' || r.d || 'd' || NL;
    IF r.co IS NOT NULL THEN v_memo := v_memo || '   Company: ' || r.co || ' [' || COALESCE(r.ch, '?') || ']' || NL; END IF;
    IF r.rec IS NOT NULL AND LENGTH(r.rec) > 5 THEN v_memo := v_memo || '   -> ' || LEFT(r.rec, 120) || NL; END IF;
  END LOOP;
  v_memo := v_memo || NL;

  -- ═══ SECTION 2.5: KEY QUESTIONS NEEDING ACTION ═══
  v_memo := v_memo || NL || '## 2.5 KEY QUESTIONS NEEDING ACTION' || NL || HR || NL;
  v_counter := 0;
  FOR r IN
    SELECT p.portfolio_co, COALESCE(p.health, '?') as health, round(p.ownership_pct::numeric * 100, 2) as o,
      COALESCE(p.fmv_carried::numeric, 0) as fmv,
      LEFT(REPLACE(SPLIT_PART(p.key_questions, NL, 1), '- ', ''), 100) as top_q,
      p.follow_on_decision
    FROM portfolio p
    WHERE p.key_questions IS NOT NULL AND LENGTH(p.key_questions) > 5
    AND NOT EXISTS (SELECT 1 FROM actions_queue aq WHERE aq.status IN ('Proposed','Accepted')
      AND (aq.action ILIKE '%' || LEFT(p.portfolio_co, 15) || '%' OR aq.company_notion_id = p.notion_page_id))
    ORDER BY p.ownership_pct DESC NULLS LAST LIMIT 10
  LOOP
    v_counter := v_counter + 1;
    v_memo := v_memo || NL || '  ' || v_counter || '. ' || r.portfolio_co || ' [' || r.health || '] ' || r.o || '% | $' || to_char(r.fmv, 'FM999,999') || NL;
    v_memo := v_memo || '     Q: ' || COALESCE(r.top_q, '(no text)') || NL;
    IF r.follow_on_decision IS NOT NULL THEN v_memo := v_memo || '     Follow-on: ' || r.follow_on_decision || NL; END IF;
  END LOOP;
  IF v_counter = 0 THEN v_memo := v_memo || '  All key questions have associated actions.' || NL; END IF;
  v_memo := v_memo || NL;

  -- ═══ SECTION 3: FOLLOW-ON ═══
  v_memo := v_memo || NL || '## 3. PORTFOLIO — FOLLOW-ON' || NL || HR || NL || NL || '  ACTIVE (SPR/PR):' || NL;
  FOR r IN SELECT elem->>'company' as co, COALESCE(elem->>'health', '?') as h,
    round((elem->>'ownership_pct')::numeric, 1) as o,
    COALESCE((elem->>'room_to_deploy')::numeric, 0) as room,
    elem->>'notes' as n
    FROM jsonb_array_elements(v_decisions->'investment_decisions') elem
    WHERE elem->>'decision' IN ('SPR','PR') ORDER BY (elem->>'ownership_pct')::numeric DESC LOOP
    v_memo := v_memo || '  - ' || COALESCE(r.co, '?') || ' [' || r.h || '] ' || r.o || '% own';
    IF r.room > 0 THEN v_memo := v_memo || ' | $' || to_char(r.room, 'FM999,999') || ' deployable'; END IF;
    v_memo := v_memo || NL;
    IF r.n IS NOT NULL THEN v_memo := v_memo || '    ' || LEFT(r.n, 100) || NL; END IF;
  END LOOP;

  v_memo := v_memo || NL || '  TOKEN/ZERO:' || NL;
  FOR r IN SELECT COALESCE(elem->>'company', '?') as co, COALESCE(elem->>'health', '?') as h,
    round((elem->>'ownership_pct')::numeric, 1) as o
    FROM jsonb_array_elements(v_decisions->'investment_decisions') elem
    WHERE elem->>'decision' = 'Token/Zero' ORDER BY (elem->>'ownership_pct')::numeric DESC LIMIT 10 LOOP
    v_memo := v_memo || '  - ' || r.co || ' [' || r.h || '] ' || r.o || '% own' || NL;
  END LOOP;
  v_memo := v_memo || NL;

  -- ═══ SECTION 4: THESIS INTELLIGENCE ═══
  v_memo := v_memo || NL || '## 4. THESIS INTELLIGENCE' || NL || HR || NL;
  FOR r IN
    SELECT tt.thread_name, COALESCE(tt.conviction, '?') as conviction,
      COALESCE(tt.bias_flags::jsonb->>'severity', '?') as severity,
      (tt.bias_flags::jsonb->>'confirmation_bias') as conf_bias,
      (tt.bias_flags::jsonb->>'conviction_mismatch') as conv_mismatch,
      tt.bias_flags::jsonb->>'recommendation' as rec,
      (SELECT count(*) FROM actions_queue aq WHERE aq.status = 'Proposed' AND aq.thesis_connection = tt.thread_name) as oa
    FROM thesis_threads tt
    WHERE tt.bias_flags IS NOT NULL AND tt.bias_flags::jsonb->>'severity' IN ('HIGH','CRITICAL','MEDIUM')
    ORDER BY CASE tt.bias_flags::jsonb->>'severity' WHEN 'CRITICAL' THEN 0 WHEN 'HIGH' THEN 1 ELSE 2 END
  LOOP
    v_memo := v_memo || NL || '  ';
    v_memo := v_memo || CASE r.severity WHEN 'CRITICAL' THEN '!! ' WHEN 'HIGH' THEN '! ' ELSE '~ ' END;
    v_memo := v_memo || r.thread_name || ' [' || r.conviction || '] — ' || r.severity || NL;
    IF r.conf_bias = 'true' THEN v_memo := v_memo || '    Confirmation bias detected.' || NL; END IF;
    IF r.conv_mismatch = 'true' THEN v_memo := v_memo || '    Conviction may not match evidence.' || NL; END IF;
    IF r.rec IS NOT NULL THEN v_memo := v_memo || '    Rec: ' || r.rec || NL; END IF;
    v_memo := v_memo || '    ' || r.oa || ' open actions.' || NL;
  END LOOP;
  FOR r IN
    SELECT tt.thread_name, COALESCE(tt.conviction, '?') as conviction,
      (SELECT count(*) FROM actions_queue aq WHERE aq.status = 'Proposed' AND aq.thesis_connection = tt.thread_name) as oa
    FROM thesis_threads tt
    WHERE tt.bias_flags IS NULL OR tt.bias_flags::jsonb->>'severity' IN ('OK','LOW')
    ORDER BY CASE tt.conviction WHEN 'Very High' THEN 0 WHEN 'High' THEN 1 WHEN 'Medium' THEN 2 ELSE 3 END
  LOOP
    v_memo := v_memo || NL || '  ' || r.thread_name || ' [' || r.conviction || '] — ' || r.oa || ' open actions' || NL;
  END LOOP;
  v_memo := v_memo || NL;

  -- ═══ SECTION 5: OBLIGATION FOLLOW-UPS ═══
  DECLARE v_obl_count INT := 0;
  BEGIN
    v_memo := v_memo || NL || '## 5. OBLIGATION FOLLOW-UPS' || NL || HR || NL;
    FOR r IN SELECT LEFT(aq.action, 140) as a, COALESCE(aq.user_priority_score, 0) as s,
      EXTRACT(DAY FROM NOW() - aq.created_at)::int as age
      FROM actions_queue aq WHERE aq.source = 'obligation_followup' AND aq.status = 'Proposed'
      ORDER BY aq.user_priority_score DESC LIMIT 10 LOOP
      v_obl_count := v_obl_count + 1;
      v_memo := v_memo || NL || '  ' || v_obl_count || '. ' || r.a || NL;
      v_memo := v_memo || '     Score: ' || round(r.s, 1) || ' | ' || r.age || 'd old' || NL;
    END LOOP;
    IF v_obl_count = 0 THEN v_memo := v_memo || '  No outstanding obligation follow-ups.' || NL; END IF;
    v_memo := v_memo || NL;
  END;

  -- ═══ SECTION 6: PEOPLE ═══
  v_memo := v_memo || NL || '## 6. PEOPLE TO REACH OUT TO' || NL || HR || NL || NL || '  YOU OWE THEM (overdue):' || NL;
  v_counter := 0;
  FOR r IN SELECT COALESCE(elem->>'person', '?') as p, elem->>'role' as role,
    COALESCE(elem->>'description', '') as d, COALESCE((elem->>'days_overdue')::int, 0) as ovd
    FROM jsonb_array_elements(v_network->'obligation_hotspots') elem
    WHERE elem->>'type' = 'I_OWE_THEM' AND elem->>'status' IN ('overdue','escalated')
    ORDER BY COALESCE((elem->>'days_overdue')::int, 0) DESC LIMIT 7 LOOP
    v_counter := v_counter + 1;
    v_memo := v_memo || '  ' || v_counter || '. ' || r.p;
    IF r.role IS NOT NULL THEN v_memo := v_memo || ' (' || LEFT(r.role, 40) || ')'; END IF;
    v_memo := v_memo || ' — ' || r.ovd || 'd overdue' || NL || '     ' || LEFT(r.d, 120) || NL;
  END LOOP;

  v_memo := v_memo || NL || '  THEY OWE YOU:' || NL;
  v_counter := 0;
  FOR r IN SELECT COALESCE(elem->>'person', '?') as p, elem->>'role' as role,
    COALESCE(elem->>'description', '') as d, COALESCE((elem->>'days_overdue')::int, 0) as ovd
    FROM jsonb_array_elements(v_network->'obligation_hotspots') elem
    WHERE elem->>'type' = 'THEY_OWE_ME' AND elem->>'status' IN ('overdue','escalated')
    ORDER BY COALESCE((elem->>'days_overdue')::int, 0) DESC LIMIT 5 LOOP
    v_counter := v_counter + 1;
    v_memo := v_memo || '  ' || v_counter || '. ' || r.p;
    IF r.role IS NOT NULL THEN v_memo := v_memo || ' (' || LEFT(r.role, 40) || ')'; END IF;
    v_memo := v_memo || ' — ' || r.ovd || 'd overdue' || NL || '     ' || LEFT(r.d, 120) || NL;
  END LOOP;

  v_memo := v_memo || NL || '  COMING UP:' || NL;
  v_counter := 0;
  FOR r IN SELECT COALESCE(elem->>'person', '?') as p, elem->>'role' as role,
    COALESCE(elem->>'description', '') as d, COALESCE(elem->>'due_date', '?') as due
    FROM jsonb_array_elements(v_network->'obligation_hotspots') elem
    WHERE elem->>'status' = 'pending'
    ORDER BY COALESCE((elem->>'blended_priority')::numeric, 0) DESC LIMIT 5 LOOP
    v_counter := v_counter + 1;
    v_memo := v_memo || '  ' || v_counter || '. ' || r.p;
    IF r.role IS NOT NULL THEN v_memo := v_memo || ' (' || LEFT(r.role, 40) || ')'; END IF;
    v_memo := v_memo || ' — due ' || LEFT(r.due, 10) || NL || '     ' || LEFT(r.d, 120) || NL;
  END LOOP;

  v_memo := v_memo || NL || '  KEY PORTFOLIO CONTACTS (silent):' || NL;
  v_counter := 0;
  FOR r IN SELECT COALESCE(elem->>'narrative', '') as n
    FROM jsonb_array_elements(v_network->'top_strategic_people') elem
    WHERE COALESCE((elem->>'portfolio_connections')::int, 0) > 0 AND COALESCE((elem->>'obligations')::int, 0) = 0
    ORDER BY COALESCE((elem->>'importance')::numeric, 0) DESC LIMIT 5 LOOP
    v_counter := v_counter + 1;
    v_memo := v_memo || '  ' || v_counter || '. ' || r.n || NL;
  END LOOP;

  -- ═══ FOOTER ═══
  v_memo := v_memo || NL || '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━' || NL;
  v_memo := v_memo || 'Generated: ' || NOW()::text || NL;
  v_memo := v_memo || 'Source: Megamind format_strategic_briefing() v4.0' || NL;
  v_memo := v_memo || '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━' || NL;

  RETURN v_memo;
END;
$$;
