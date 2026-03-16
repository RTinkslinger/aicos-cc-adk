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

If messages exist:
1. Combine into numbered prompt
2. Call `send_to_content_agent` with the combined prompt (returns immediately — content agent works in background)
3. If tool returned "busy", skip — content agent is still working on previous prompt
4. If tool returned "Prompt sent", mark all relayed IDs as processed:
   ```bash
   psql $DATABASE_URL -c "UPDATE cai_inbox SET processed = TRUE, processed_at = NOW() WHERE id IN (42, 43)"
   ```

If no messages: skip.

---

## Step 3: Content Pipeline Check

```bash
cat /opt/agents/content/state/last_pipeline_run.txt 2>/dev/null
```

If file missing OR timestamp >5 minutes old:
- Call `send_to_content_agent`: "Run your content pipeline cycle. Check watch list for new content, analyze, score, and publish."
- If tool returned "busy", skip — content agent is still working.

If <5 minutes: skip.

---

## Step 4: Traces Compaction Check

```bash
cat state/orc_iteration.txt
```

If divisible by 30 and > 0: read `state/COMPACTION_PROTOCOL.md` and follow it.

---

## Step 5: Iteration Log

Write one-line summary to `state/orc_last_log.txt`.
