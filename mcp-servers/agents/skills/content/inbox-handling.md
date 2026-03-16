# Inbox Handling Skill

Instructions for processing messages from the CAI Inbox. Aakash sends instructions via Claude.ai (CAI), which writes to the `cai_inbox` Postgres table. The Content Agent reads and processes these messages.

---

## Inbox Check Protocol

Check the inbox every 1-minute cycle:

```bash
psql $DATABASE_URL -c "SELECT id, message_type, content, metadata, priority, created_at FROM cai_inbox WHERE NOT processed ORDER BY CASE priority WHEN 'urgent' THEN 1 WHEN 'normal' THEN 2 WHEN 'low' THEN 3 END, created_at ASC;"
```

If no unprocessed messages, do nothing. Move to the next scheduled task.

---

## Message Types and Routing

### track_source

**Purpose:** Aakash wants to track a new content source (person, channel, publication).

**Example:**
```json
{
  "type": "track_source",
  "content": "@pmarca on X",
  "metadata": {"platform": "twitter", "handle": "pmarca"}
}
```

**Processing:**
1. Add the source to the watch list: `/opt/agents/data/watch_list.json`
2. Immediately fetch recent content from the source (if feasible).
3. Analyze using content analysis skill.
4. Write notification: "Now tracking @pmarca on X. Found 3 recent posts, 1 is thesis-relevant."

### research_request

**Purpose:** Aakash wants deep research on a topic, company, or person.

**Example:**
```json
{
  "type": "research_request",
  "content": "Research Composio's enterprise traction and MCP integration depth",
  "metadata": {"company": "Composio", "thesis": "Agentic AI Infrastructure"}
}
```

**Processing:**
1. This is a Class 2 task -- delegate to web-researcher subagent (run_in_background).
2. Subagent conducts multi-step web research.
3. When complete, analyze findings using content analysis skill.
4. Score any proposed actions using scoring skill.
5. Write results to Postgres (content_digests table, actions table).
6. Write notification with summary of findings.

### thesis_update

**Purpose:** Aakash provides a manual thesis observation or conviction signal.

**Example:**
```json
{
  "type": "thesis_update",
  "content": "Met 3 founders this week all building on MCP. Conviction strengthening.",
  "metadata": {"thesis": "Agentic AI Infrastructure", "signal": "++"}
}
```

**Processing:**
1. Load thesis-reasoning skill.
2. Find the referenced thesis thread in Postgres.
3. Append the evidence (with IDS notation from metadata).
4. Update key questions if any are addressed.
5. If conviction change seems warranted, recommend it (but do NOT set it autonomously).
6. Write notification confirming the update.

```bash
psql $DATABASE_URL -c "UPDATE thesis_threads SET evidence_for = evidence_for || E'\n[NEW $(date +%Y-%m-%d)] ++ Met 3 founders building on MCP (manual signal from Aakash). Source: CAI Inbox', notion_synced = FALSE WHERE thread_name = 'Agentic AI Infrastructure';"
```

### watch_list_add

**Purpose:** Add a source to the content watch list.

**Example:**
```json
{
  "type": "watch_list_add",
  "content": "Add this YouTube channel to my watch list",
  "metadata": {"url": "https://youtube.com/@channelname", "name": "Channel Name"}
}
```

**Processing:**
1. Read current watch list from `/opt/agents/data/watch_list.json`.
2. Add the new entry with metadata.
3. Write updated watch list.
4. Write notification: "Added Channel Name to watch list."

### watch_list_remove

**Purpose:** Remove a source from the content watch list.

**Example:**
```json
{
  "type": "watch_list_remove",
  "content": "Stop tracking this source",
  "metadata": {"url": "https://youtube.com/@channelname"}
}
```

**Processing:**
1. Read current watch list.
2. Find and remove the matching entry.
3. Write updated watch list.
4. Write notification: "Removed Channel Name from watch list."

### general

**Purpose:** Catch-all for messages that don't fit other types.

**Example:**
```json
{
  "type": "general",
  "content": "What thesis threads have had evidence updates this week?"
}
```

**Processing:**
1. Interpret the request.
2. Execute using available tools and skills.
3. Write results to notifications table for CAI to read.

---

## Watch List Management

### File location
`/opt/agents/data/watch_list.json`

### Schema
```json
{
  "sources": [
    {
      "name": "Source Name",
      "platform": "youtube|twitter|substack|podcast|web",
      "url": "https://source-url",
      "added_at": "2026-03-15T10:00:00Z",
      "added_by": "CAI",
      "check_interval_min": 60,
      "last_checked": "2026-03-15T09:00:00Z",
      "active": true
    }
  ],
  "last_updated": "2026-03-15T10:00:00Z"
}
```

### Operations

**Add source:**
```bash
# Read, modify, write back
python3 -c "
import json
with open('/opt/agents/data/watch_list.json') as f:
    wl = json.load(f)
wl['sources'].append({
    'name': 'New Source',
    'platform': 'youtube',
    'url': 'https://youtube.com/@channel',
    'added_at': '$(date -u +%Y-%m-%dT%H:%M:%SZ)',
    'added_by': 'CAI',
    'check_interval_min': 60,
    'last_checked': None,
    'active': True
})
wl['last_updated'] = '$(date -u +%Y-%m-%dT%H:%M:%SZ)'
with open('/opt/agents/data/watch_list.json', 'w') as f:
    json.dump(wl, f, indent=2)
"
```

**Remove source:**
```bash
python3 -c "
import json
with open('/opt/agents/data/watch_list.json') as f:
    wl = json.load(f)
wl['sources'] = [s for s in wl['sources'] if s['url'] != 'https://target-url']
wl['last_updated'] = '$(date -u +%Y-%m-%dT%H:%M:%SZ)'
with open('/opt/agents/data/watch_list.json', 'w') as f:
    json.dump(wl, f, indent=2)
"
```

---

## Processing Protocol

For every unprocessed inbox message:

1. **Read** the message from cai_inbox.
2. **Route** based on `message_type` (see routing table above).
3. **Execute** the appropriate processing steps.
4. **Mark processed:**
   ```bash
   psql $DATABASE_URL -c "UPDATE cai_inbox SET processed = TRUE, processed_at = NOW() WHERE id = {message_id};"
   ```
5. **Notify** (write to notifications table for significant outcomes):
   ```bash
   psql $DATABASE_URL -c "INSERT INTO notifications (notification_type, title, body, source_agent, created_at) VALUES ('inbox_processed', 'Processed: {summary}', '{detailed result}', 'ContentAgent', NOW());"
   ```

---

## Priority Handling

Messages have a priority field: `urgent`, `normal`, `low`.

- **urgent:** Process immediately, before any scheduled content cycle work.
- **normal:** Process in FIFO order during inbox check cycle.
- **low:** Process only after all normal messages and scheduled work.

The query in "Inbox Check Protocol" already sorts by priority.

---

## Error Handling

If processing a message fails:
1. Do NOT mark it as processed.
2. Log the error to the notifications table.
3. It will be retried on the next 1-minute cycle.
4. After 3 consecutive failures on the same message, mark it as processed and write an error notification:
   ```bash
   psql $DATABASE_URL -c "UPDATE cai_inbox SET processed = TRUE, processed_at = NOW(), error = 'Failed after 3 attempts: {error details}' WHERE id = {message_id};"
   ```

Track retry count:
```bash
psql $DATABASE_URL -c "SELECT id, content, COALESCE(retry_count, 0) as retries FROM cai_inbox WHERE NOT processed AND COALESCE(retry_count, 0) >= 3;"
```
