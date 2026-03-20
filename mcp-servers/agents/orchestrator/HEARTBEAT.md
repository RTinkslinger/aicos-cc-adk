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
| Everything else (track_source, research_request, general, ...) | Content Agent | `send_to_content_agent` |

### Datum Batching Rule

If there are 3+ `datum_*` messages in the inbox, batch them into a single prompt to the Datum Agent rather than sending one-by-one. Format:

> Process entity batch (3 inbox messages):
> 1. [id=42, type=datum_person] Rahul Sharma, CTO at Composio
> 2. [id=43, type=datum_company] Track Composio - AI agent tooling
> 3. [id=44, type=datum_entity] Entity batch from content pipeline

### Processing Steps

1. Separate inbox messages into datum_* group and content group
2. For datum_* messages: combine into prompt, call `send_to_datum_agent`
3. For content messages: combine into prompt, call `send_to_content_agent`
4. If either tool returned "busy", skip that group — retry next heartbeat
5. If tool returned "Prompt sent", mark the relayed IDs as processed:
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

## Step 4: Traces Compaction Check

```bash
cat state/orc_iteration.txt
```

If divisible by 30 and > 0: read `COMPACTION_PROTOCOL.md` and follow it.

---

## Step 5: Iteration Log

Write one-line summary to `state/orc_last_log.txt`.
