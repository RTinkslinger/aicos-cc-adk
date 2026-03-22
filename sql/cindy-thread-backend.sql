-- M8 Cindy: Thread Backend — Agent-User Communication RPCs
-- Created: 2026-03-22
-- Applied: 2026-03-22 via Supabase MCP execute_sql
--
-- Purpose: Cindy's version of the agent thread system.
-- Shared tables (agent_tasks, agent_task_messages) + 5 Cindy-specific RPCs.
-- Same pattern as Datum but tuned for EA communication tasks.
--
-- Spec: docs/superpowers/specs/2026-03-22-agent-thread-ui-contract.md
--
-- Dependencies:
--   - obligations table (existing)
--   - network table (existing)
--   - companies table (existing)
--   - portfolio table (existing)
--   - entity_connections table (existing)
--   - interactions table (existing)
--   - people_interactions table (existing)
--   - cindy_person_intelligence() function (existing)
--
-- Also includes:
--   - FB-31 fix: cindy_obligation_portfolio_enricher() + updated cindy_deal_obligation_generator()
--   - Briefing fix: cindy_daily_briefing_v3() relationship_pulse key name fix (label -> momentum_label)
--   - Briefing enhancement: cooling_relationships section added to daily briefing

-- =============================================================================
-- PART 1: Shared Tables (agent_tasks + agent_task_messages)
-- =============================================================================

CREATE TABLE IF NOT EXISTS agent_tasks (
  id SERIAL PRIMARY KEY,
  agent TEXT NOT NULL,  -- 'datum', 'cindy', 'megamind'
  user_input TEXT NOT NULL,
  status TEXT DEFAULT 'pending',  -- pending, processing, needs_input, done, failed
  context JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  resolved_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_agent_tasks_agent_status ON agent_tasks(agent, status);
CREATE INDEX IF NOT EXISTS idx_agent_tasks_created ON agent_tasks(created_at DESC);

CREATE TABLE IF NOT EXISTS agent_task_messages (
  id SERIAL PRIMARY KEY,
  task_id INT REFERENCES agent_tasks(id) ON DELETE CASCADE,
  sender TEXT NOT NULL,  -- 'user' or agent name
  type TEXT NOT NULL,    -- text, company_picker, person_picker, diff_view, candidate_cards, confirmation, status_update, field_edit, multi_select, priority_rank
  content JSONB NOT NULL,
  response JSONB,  -- user's response
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_agent_task_messages_task ON agent_task_messages(task_id, created_at);


-- =============================================================================
-- PART 2: cindy_task_create(user_input, context) -> task_id
-- =============================================================================
-- Classifies user input into task types and creates a task with initial ack message.
-- Types: draft_message, schedule_followup, resolve_obligation, relationship_query, communication_brief

CREATE OR REPLACE FUNCTION cindy_task_create(
  p_user_input TEXT,
  p_context JSONB DEFAULT '{}'
)
RETURNS JSONB
LANGUAGE plpgsql
AS $fn$
DECLARE
  v_task_id INT;
  v_task_type TEXT;
  v_initial_message_id INT;
BEGIN
  v_task_type := CASE
    WHEN p_user_input ILIKE '%draft%' OR p_user_input ILIKE '%write%email%' OR p_user_input ILIKE '%compose%' THEN 'draft_message'
    WHEN p_user_input ILIKE '%reschedule%' OR p_user_input ILIKE '%schedule%' OR p_user_input ILIKE '%followup%' OR p_user_input ILIKE '%follow up%' OR p_user_input ILIKE '%follow-up%' THEN 'schedule_followup'
    WHEN p_user_input ILIKE '%obligation%' OR p_user_input ILIKE '%resolve%' OR p_user_input ILIKE '%clear%' OR p_user_input ILIKE '%dismiss%' THEN 'resolve_obligation'
    WHEN p_user_input ILIKE '%status%' OR p_user_input ILIKE '%relationship%' OR p_user_input ILIKE '%history%' OR p_user_input ILIKE '%what%know%' THEN 'relationship_query'
    WHEN p_user_input ILIKE '%brief%' OR p_user_input ILIKE '%context%' OR p_user_input ILIKE '%prep%' OR p_user_input ILIKE '%meeting%' THEN 'communication_brief'
    ELSE 'relationship_query'
  END;

  INSERT INTO agent_tasks (agent, user_input, status, context)
  VALUES ('cindy', p_user_input, 'processing', p_context || jsonb_build_object('task_type', v_task_type))
  RETURNING id INTO v_task_id;

  INSERT INTO agent_task_messages (task_id, sender, type, content)
  VALUES (v_task_id, 'cindy', 'status_update', jsonb_build_object(
    'status', 'received',
    'message', CASE v_task_type
      WHEN 'draft_message' THEN 'Got it. Drafting message now...'
      WHEN 'schedule_followup' THEN 'On it. Checking context and suggesting times...'
      WHEN 'resolve_obligation' THEN 'Looking into this obligation...'
      WHEN 'relationship_query' THEN 'Pulling relationship intelligence...'
      WHEN 'communication_brief' THEN 'Assembling communication brief...'
      ELSE 'Processing your request...'
    END,
    'task_type', v_task_type
  ))
  RETURNING id INTO v_initial_message_id;

  RETURN jsonb_build_object(
    'task_id', v_task_id, 'task_type', v_task_type,
    'status', 'processing', 'initial_message_id', v_initial_message_id,
    'created_at', NOW()
  );
END;
$fn$;


-- =============================================================================
-- PART 3: cindy_task_list(status) -> tasks[]
-- =============================================================================

CREATE OR REPLACE FUNCTION cindy_task_list(
  p_status TEXT DEFAULT 'all'
)
RETURNS JSONB
LANGUAGE plpgsql
AS $fn$
DECLARE
  v_tasks JSONB;
BEGIN
  SELECT COALESCE(jsonb_agg(
    jsonb_build_object(
      'id', t.id, 'user_input', t.user_input, 'task_type', t.context->>'task_type',
      'status', t.status, 'created_at', t.created_at, 'resolved_at', t.resolved_at,
      'message_count', (SELECT COUNT(*) FROM agent_task_messages m WHERE m.task_id = t.id),
      'needs_response', (SELECT COUNT(*) > 0 FROM agent_task_messages m
        WHERE m.task_id = t.id AND m.sender = 'cindy' AND m.response IS NULL AND m.type NOT IN ('text', 'status_update')),
      'last_message', (SELECT jsonb_build_object('id', m.id, 'sender', m.sender, 'type', m.type,
        'preview', CASE WHEN m.type = 'text' THEN LEFT(m.content->>'message', 100)
          ELSE m.type || ': ' || LEFT(m.content::text, 80) END, 'created_at', m.created_at)
        FROM agent_task_messages m WHERE m.task_id = t.id ORDER BY m.created_at DESC LIMIT 1)
    ) ORDER BY
      CASE t.status WHEN 'needs_input' THEN 0 WHEN 'processing' THEN 1 WHEN 'pending' THEN 2 WHEN 'done' THEN 3 WHEN 'failed' THEN 4 END,
      t.created_at DESC
  ), '[]'::jsonb)
  INTO v_tasks
  FROM agent_tasks t
  WHERE t.agent = 'cindy' AND (p_status = 'all' OR t.status = p_status);

  RETURN jsonb_build_object(
    'tasks', v_tasks,
    'counts', jsonb_build_object(
      'total', jsonb_array_length(v_tasks),
      'needs_input', (SELECT COUNT(*) FROM agent_tasks WHERE agent = 'cindy' AND status = 'needs_input'),
      'processing', (SELECT COUNT(*) FROM agent_tasks WHERE agent = 'cindy' AND status = 'processing'),
      'pending', (SELECT COUNT(*) FROM agent_tasks WHERE agent = 'cindy' AND status = 'pending'),
      'done', (SELECT COUNT(*) FROM agent_tasks WHERE agent = 'cindy' AND status = 'done')
    )
  );
END;
$fn$;


-- =============================================================================
-- PART 4: cindy_task_thread(task_id) -> task + messages[]
-- =============================================================================

CREATE OR REPLACE FUNCTION cindy_task_thread(p_task_id INT)
RETURNS JSONB
LANGUAGE plpgsql
AS $fn$
DECLARE
  v_task JSONB;
  v_messages JSONB;
BEGIN
  SELECT jsonb_build_object('id', t.id, 'user_input', t.user_input, 'task_type', t.context->>'task_type',
    'status', t.status, 'context', t.context, 'created_at', t.created_at, 'resolved_at', t.resolved_at)
  INTO v_task FROM agent_tasks t WHERE t.id = p_task_id AND t.agent = 'cindy';

  IF v_task IS NULL THEN
    RETURN jsonb_build_object('error', 'Task not found', 'task_id', p_task_id);
  END IF;

  SELECT COALESCE(jsonb_agg(jsonb_build_object(
    'id', m.id, 'sender', m.sender, 'type', m.type, 'content', m.content,
    'response', m.response,
    'awaiting_response', (m.sender = 'cindy' AND m.response IS NULL AND m.type NOT IN ('text', 'status_update')),
    'created_at', m.created_at
  ) ORDER BY m.created_at), '[]'::jsonb)
  INTO v_messages FROM agent_task_messages m WHERE m.task_id = p_task_id;

  RETURN jsonb_build_object('task', v_task, 'messages', v_messages, 'message_count', jsonb_array_length(v_messages));
END;
$fn$;


-- =============================================================================
-- PART 5: cindy_task_respond(task_id, message_id, response) -> next_message
-- =============================================================================
-- Processes user response to a Cindy thread message.
-- Handles: confirmation (approve/reject), candidate_cards, person_picker, diff_view.

CREATE OR REPLACE FUNCTION cindy_task_respond(p_task_id INT, p_message_id INT, p_response JSONB)
RETURNS JSONB
LANGUAGE plpgsql
AS $fn$
DECLARE
  v_message RECORD;
  v_next_message_id INT;
  v_action TEXT;
BEGIN
  SELECT m.*, t.status as task_status, t.context as task_context
  INTO v_message FROM agent_task_messages m JOIN agent_tasks t ON t.id = m.task_id
  WHERE m.id = p_message_id AND m.task_id = p_task_id AND t.agent = 'cindy';

  IF v_message IS NULL THEN RETURN jsonb_build_object('error', 'Message not found or not a Cindy task'); END IF;
  IF v_message.response IS NOT NULL THEN RETURN jsonb_build_object('error', 'Already responded', 'existing_response', v_message.response); END IF;

  UPDATE agent_task_messages SET response = p_response WHERE id = p_message_id;
  v_action := COALESCE(p_response->>'action', 'unknown');

  IF v_message.type = 'confirmation' THEN
    IF v_action = 'approve' THEN
      INSERT INTO agent_task_messages (task_id, sender, type, content) VALUES (p_task_id, 'cindy', 'text',
        jsonb_build_object('message', 'Done. ' || CASE v_message.task_context->>'task_type'
          WHEN 'draft_message' THEN 'Message marked ready to send.'
          WHEN 'resolve_obligation' THEN 'Obligation resolved.'
          WHEN 'schedule_followup' THEN 'Follow-up scheduled.' ELSE 'Action completed.' END))
      RETURNING id INTO v_next_message_id;
      IF v_message.content ? 'obligation_id' THEN
        UPDATE obligations SET status = 'fulfilled', fulfilled_at = NOW(), fulfilled_method = 'cindy_thread',
          fulfilled_evidence = 'User approved via Cindy task thread #' || p_task_id
        WHERE id = (v_message.content->>'obligation_id')::int;
      END IF;
      UPDATE agent_tasks SET status = 'done', resolved_at = NOW() WHERE id = p_task_id;
    ELSE
      INSERT INTO agent_task_messages (task_id, sender, type, content) VALUES (p_task_id, 'cindy', 'text',
        jsonb_build_object('message', 'Got it, not proceeding. Want me to try a different approach?'))
      RETURNING id INTO v_next_message_id;
      UPDATE agent_tasks SET status = 'needs_input' WHERE id = p_task_id;
    END IF;
  ELSIF v_message.type = 'candidate_cards' THEN
    INSERT INTO agent_task_messages (task_id, sender, type, content) VALUES (p_task_id, 'cindy', 'confirmation',
      jsonb_build_object('message', 'Confirming your selection: ' || COALESCE(p_response->>'selected_label', 'option selected'),
        'selected', p_response->'selected', 'confirm_action', v_message.task_context->>'task_type'))
    RETURNING id INTO v_next_message_id;
    UPDATE agent_tasks SET status = 'needs_input' WHERE id = p_task_id;
  ELSIF v_message.type = 'person_picker' THEN
    INSERT INTO agent_task_messages (task_id, sender, type, content) VALUES (p_task_id, 'cindy', 'status_update',
      jsonb_build_object('status', 'processing', 'message', 'Using ' || COALESCE(p_response->>'selected_name', 'selected person') || '. Processing...'))
    RETURNING id INTO v_next_message_id;
    UPDATE agent_tasks SET status = 'processing' WHERE id = p_task_id;
  ELSIF v_message.type = 'diff_view' THEN
    IF v_action = 'approve' THEN
      INSERT INTO agent_task_messages (task_id, sender, type, content) VALUES (p_task_id, 'cindy', 'text', jsonb_build_object('message', 'Changes applied.'))
      RETURNING id INTO v_next_message_id;
      UPDATE agent_tasks SET status = 'done', resolved_at = NOW() WHERE id = p_task_id;
    ELSE
      INSERT INTO agent_task_messages (task_id, sender, type, content) VALUES (p_task_id, 'cindy', 'text',
        jsonb_build_object('message', 'Changes discarded. Let me know if you want to try differently.'))
      RETURNING id INTO v_next_message_id;
      UPDATE agent_tasks SET status = 'needs_input' WHERE id = p_task_id;
    END IF;
  ELSE
    INSERT INTO agent_task_messages (task_id, sender, type, content) VALUES (p_task_id, 'user', 'text',
      jsonb_build_object('message', COALESCE(p_response->>'message', p_response::text)))
    RETURNING id INTO v_next_message_id;
  END IF;

  RETURN jsonb_build_object('success', true, 'task_id', p_task_id, 'message_id', p_message_id,
    'next_message_id', v_next_message_id, 'task_status', (SELECT status FROM agent_tasks WHERE id = p_task_id));
END;
$fn$;


-- =============================================================================
-- PART 6: cindy_task_auto_process(task_id) -> Cindy's EA brain
-- =============================================================================
-- Generates contextual thread messages based on task type.
-- Pulls from: network, companies, portfolio, obligations, interactions, entity_connections.
-- NOTE: This is SQL plumbing. The Claude SDK Cindy agent generates richer responses.

-- [Full function body deployed to Supabase — see execute_sql call in session log]
-- Function handles: relationship_query, resolve_obligation, schedule_followup, draft_message, communication_brief


-- =============================================================================
-- PART 7: cindy_obligation_portfolio_enricher()
-- =============================================================================
-- FB-31 fix: Cross-references ALL obligations with portfolio DB.
-- Ensures portfolio founders always have portfolio context on their obligations.
-- Sets canonical person_role from network.role_title.

-- [Full function body deployed to Supabase — see execute_sql call in session log]


-- =============================================================================
-- PART 8: cindy_deal_obligation_generator() — FB-31 fix
-- =============================================================================
-- Updated to always use network.role_title (canonical) for person_role.
-- Added is_portfolio_founder flag to context.
-- Previously could pick up wrong role from interaction context.

-- [Full function body deployed to Supabase — see execute_sql call in session log]


-- =============================================================================
-- PART 9: cindy_daily_briefing_v3() — Cooling relationships + key name fix
-- =============================================================================
-- Fixed: relationship_pulse used p->>'label' but momentum returns p->>'momentum_label'
-- Added: cooling_relationships section with portfolio_cooling + non_portfolio_attention
-- Fixed: days_since_contact cast (numeric::int instead of direct int, handles decimals)

-- [Full function body deployed to Supabase — see execute_sql call in session log]
