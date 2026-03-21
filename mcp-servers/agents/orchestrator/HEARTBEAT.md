# Heartbeat Checklist

Follow ALL steps every heartbeat.

---

## Step 1: Check for Checkpoint

```bash
ls state/orc_checkpoint.md 2>/dev/null
```

If exists: read it, absorb state, delete it, log `resumed from checkpoint, session #N`.

---

## Step 2: Inbox Check

```bash
psql $DATABASE_URL -t -A -c "SELECT id, type, content, metadata FROM cai_inbox WHERE processed = FALSE ORDER BY created_at"
```

If messages exist, **route by type**:

### Routing Rules

| Type Pattern | Route To | Bridge Tool |
|-------------|----------|-------------|
| `datum_person` | Datum Agent | `send_to_datum_agent` |
| `datum_company` | Datum Agent | `send_to_datum_agent` |
| `datum_entity` | Datum Agent | `send_to_datum_agent` |
| `datum_image` | Datum Agent | `send_to_datum_agent` |
| `datum_meeting_entities` | Datum Agent | `send_to_datum_agent` |
| `strategy_assessment` | Megamind Agent | `send_to_megamind_agent` |
| `strategy_review` | Megamind Agent | `send_to_megamind_agent` |
| `strategy_*` (any strategy prefix) | Megamind Agent | `send_to_megamind_agent` |
| `cindy_email` | Cindy Agent | `send_to_cindy_agent` |
| `cindy_whatsapp` | Cindy Agent | `send_to_cindy_agent` |
| `cindy_meeting` | Cindy Agent | `send_to_cindy_agent` |
| `cindy_calendar` | Cindy Agent | `send_to_cindy_agent` |
| `cindy_gap_filled` | Cindy Agent | `send_to_cindy_agent` |
| `cindy_granola_poll` | Cindy Agent | `send_to_cindy_agent` |
| `cindy_calendar_poll` | Cindy Agent | `send_to_cindy_agent` |
| `cindy_signal` | Megamind Agent | `send_to_megamind_agent` |
| Everything else (track_source, research_request, general, ...) | Content Agent | `send_to_content_agent` |

### Datum Batching Rule

If there are 3+ `datum_*` messages in the inbox, batch them into a single prompt to the Datum Agent rather than sending one-by-one. Format:

> Process entity batch (3 inbox messages):
> 1. [id=42, type=datum_person] Rahul Sharma, CTO at Composio
> 2. [id=43, type=datum_company] Track Composio - AI agent tooling
> 3. [id=44, type=datum_entity] Entity batch from content pipeline

### Cindy Batching Rule

If there are 3+ `cindy_*` messages (excluding `cindy_signal`) in the inbox, batch them into a single prompt to the Cindy Agent. Format:

> Process communication batch (3 inbox messages):
> 1. [id=50, type=cindy_email] Email from rahul@composio.dev — Re: Series A follow-up
> 2. [id=51, type=cindy_email] Email from sarah@composio.dev — Composio deck attached
> 3. [id=52, type=cindy_calendar] Calendar poll — check for new events

### Processing Steps

1. Separate inbox messages into datum_* group, cindy_* group (excluding cindy_signal), strategy_*/cindy_signal group, and content group
2. For datum_* messages: combine into prompt, call `send_to_datum_agent`
3. For cindy_* messages (excluding cindy_signal): combine into prompt, call `send_to_cindy_agent`
4. For strategy_*/cindy_signal messages: combine into prompt, call `send_to_megamind_agent`
5. For content messages: combine into prompt, call `send_to_content_agent`
6. If any tool returned "busy", skip that group — retry next heartbeat
7. If tool returned "Prompt sent", mark the relayed IDs as processed:
   ```bash
   psql $DATABASE_URL -c "UPDATE cai_inbox SET processed = TRUE, processed_at = NOW() WHERE id IN (42, 43)"
   ```

If no messages: skip.

---

## Step 3: Content Pipeline Check (scheduled — every 12 hours)

**Skip this step entirely if `send_to_content_agent` returned "busy" in Step 2.**

```bash
cat /opt/agents/content/state/last_pipeline_run.txt 2>/dev/null
```

If file missing OR timestamp >12 hours old:
- Call `send_to_content_agent`: "Run your content pipeline cycle. Check watch list for new content, analyze, score, and publish."
- If tool returned "busy", skip — content agent is still working.

If <12 hours: skip.

**Note:** On-demand processing happens via inbox relay (Step 2). This scheduled check is just a catch-up for the watch list.

---

## Step 3b: Agent Action Depth Grading Check

```bash
psql $DATABASE_URL -t -A -c "
  SELECT id, action, relevance_score, thesis_connection, action_type
  FROM actions_queue
  WHERE assigned_to = 'Agent'
    AND status = 'Proposed'
    AND id NOT IN (SELECT action_id FROM depth_grades)
  ORDER BY relevance_score DESC
  LIMIT 5"
```

If results: compose depth grading prompt listing each action (id, text, ENIAC score, thesis), call `send_to_megamind_agent`. If Megamind busy, skip — retry next heartbeat.

If no results: skip.

---

## Step 3c: Approved Depth Execution Check

```bash
psql $DATABASE_URL -t -A -c "
  SELECT dg.id, dg.action_id, dg.approved_depth, dg.execution_prompt, dg.execution_agent
  FROM depth_grades dg
  WHERE dg.execution_status = 'approved'
  ORDER BY dg.created_at
  LIMIT 3"
```

If results: for each approved grade, route the `execution_prompt` to the specified agent (`execution_agent` = 'content' -> `send_to_content_agent`, 'datum' -> `send_to_datum_agent`). Then update the grade:

```bash
psql $DATABASE_URL -c "UPDATE depth_grades SET execution_status = 'executing', updated_at = NOW() WHERE id = $GRADE_ID"
```

If target agent is busy, skip that grade — retry next heartbeat.

If no results: skip.

---

## Step 3d: Cascade Trigger Check

```bash
psql $DATABASE_URL -t -A -c "
  SELECT dg.id, dg.action_id, aq.action, aq.thesis_connection
  FROM depth_grades dg
  JOIN actions_queue aq ON dg.action_id = aq.id
  WHERE dg.execution_status = 'completed'
    AND dg.id NOT IN (SELECT trigger_source_id FROM cascade_events WHERE trigger_type = 'depth_completed')
  LIMIT 1"
```

If results: compose cascade trigger prompt with the completed action details, call `send_to_megamind_agent`. If Megamind busy, skip — retry next heartbeat.

If no results: skip.

---

## Step 3e: Strategic Assessment Check (daily)

```bash
psql $DATABASE_URL -t -A -c "
  SELECT created_at FROM strategic_assessments
  ORDER BY created_at DESC LIMIT 1"
```

If no results (never assessed) OR last assessment > 24 hours old:
- Call `send_to_megamind_agent`: "Run daily strategic assessment."
- If Megamind busy, skip — retry next heartbeat.

If < 24 hours: skip.

---

## Step 3f: Cindy Scheduled Triggers

### Granola poll (every 30 min)

```bash
cat /opt/agents/cindy/state/last_granola_poll.txt 2>/dev/null
```

If file missing OR timestamp > 30 minutes old:
- Write `cindy_granola_poll` to cai_inbox:
  ```bash
  psql $DATABASE_URL -c "INSERT INTO cai_inbox (type, content, metadata, processed, created_at) VALUES ('cindy_granola_poll', 'Poll Granola MCP for new meeting transcripts', '{}', FALSE, NOW())"
  ```
- Update timestamp:
  ```bash
  echo "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > /opt/agents/cindy/state/last_granola_poll.txt
  ```

If < 30 minutes: skip.

### Calendar poll (every 30 min)

```bash
cat /opt/agents/cindy/state/last_calendar_poll.txt 2>/dev/null
```

Same pattern with `cindy_calendar_poll` type and `last_calendar_poll.txt`.

### Context gap detection (daily at 8 PM IST / 14:30 UTC)

```bash
cat /opt/agents/cindy/state/last_gap_scan.txt 2>/dev/null
```

If file missing OR timestamp > 24 hours old, AND current UTC hour is >= 14:
- Write `cindy_gap_scan` to cai_inbox. Cindy scans past 24h calendar events for gaps.
- Update `last_gap_scan.txt`.

If < 24 hours: skip.

---

## Step 4: Traces Compaction Check

```bash
cat state/orc_iteration.txt
```

If divisible by 30 and > 0: read `COMPACTION_PROTOCOL.md` and follow it.

---

## Step 5: Iteration Log

Write one-line summary to `state/orc_last_log.txt`.
