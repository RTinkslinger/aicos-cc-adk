# Conflict Resolution Skill

Instructions for resolving data conflicts between Postgres and Notion during bidirectional sync.

---

## Core Principle: Field Ownership

Every field has a single owner. The owner's value always wins in a conflict.

### Human-Owned Fields (Notion ALWAYS Wins)

These fields are set by Aakash manually in Notion. If Notion and Postgres disagree, Notion is the source of truth.

| Table | Field | Why Notion Wins |
|-------|-------|----------------|
| `thesis_threads` | `status` | Active/Exploring/Parked/Archived -- Aakash's attention signal. Only he decides. |
| `actions_queue` | `outcome` | Unknown/Helpful/Gold -- Human feedback after action completion. Only Aakash rates. |
| `actions_queue` | `status` (Accepted/Dismissed) | Accept/dismiss is a human decision. Proposed status is set by agents. |

**Sync direction:** Notion -> Postgres (one-way for these fields).

**Protocol:**
```bash
# When Notion status differs from Postgres, Notion wins
psql $DATABASE_URL -c "UPDATE thesis_threads SET status = '{notion_value}', last_synced_at = NOW() WHERE notion_page_id = '{page_id}';"
```

### AI-Written Fields (Timestamp Wins)

These fields are written by agents (ContentAgent, SyncAgent) and can be updated from multiple surfaces (Claude Code, Claude.ai, Content Pipeline). When both Notion and Postgres have been updated:

**Rule:** Most recently updated value wins. Compare `last_synced_at` (Postgres) vs Notion's `last_edited_time`.

| Table | Fields | Typical Writer |
|-------|--------|---------------|
| `thesis_threads` | `conviction`, `evidence_for`, `evidence_against`, `key_questions`, `investment_implications`, `key_companies`, `key_people` | ContentAgent, CAI |
| `actions_queue` | `action`, `reasoning`, `relevance_score`, `source_content`, `thesis_connection` | ContentAgent |
| `content_digests` | All analysis fields | ContentAgent |

**Protocol:**
```bash
# Check which is newer
psql $DATABASE_URL -c "SELECT last_synced_at FROM thesis_threads WHERE notion_page_id = '{page_id}';"
# Compare with Notion's last_edited_time
# If Postgres is newer: push to Notion
# If Notion is newer: pull to Postgres
```

### Evidence Fields (SPECIAL RULE: Always Append, Never Overwrite)

`evidence_for` and `evidence_against` are append-only fields. They accumulate evidence over time.

**Conflict resolution for evidence:**
1. Compare Postgres value and Notion value.
2. If one is a superset of the other (contains all lines plus more), use the superset.
3. If both have unique additions, **merge both** -- append the lines from each that the other is missing.
4. Never delete evidence lines during sync.

**Example:**
```
Postgres evidence_for:
  [2026-03-10] + Signal A
  [2026-03-12] ++ Signal B

Notion evidence_for:
  [2026-03-10] + Signal A
  [2026-03-13] + Signal C   <-- unique to Notion

Merged result:
  [2026-03-10] + Signal A
  [2026-03-12] ++ Signal B
  [2026-03-13] + Signal C
```

---

## Conflict Detection

During each sync cycle, compare Postgres state with Notion state for every synced record:

```bash
# Get all thesis threads that have been synced to Notion
psql $DATABASE_URL -c "SELECT id, notion_page_id, thread_name, status, conviction, evidence_for, evidence_against, last_synced_at FROM thesis_threads WHERE notion_page_id IS NOT NULL;"
```

For each record:
1. Fetch Notion page state (via python3 Notion API script).
2. Compare each field.
3. For any difference, apply the ownership rules above.
4. Log the conflict to `change_events` table.

---

## Conflict Logging

Every conflict detected must be logged, even when automatically resolved:

```bash
psql $DATABASE_URL -c "INSERT INTO change_events (table_name, record_id, notion_page_id, field_name, old_value, new_value, detected_at) VALUES ('{table}', {record_id}, '{notion_page_id}', '{field}', '{postgres_value}', '{notion_value}', NOW());"
```

This creates an audit trail. The `change_events` table records:
- What changed
- What the old value was
- What the new value is
- When the change was detected

Use `processed` boolean to track whether action generation has run on this change.

---

## Sync Direction Summary

| Direction | What Flows | When |
|-----------|-----------|------|
| **Postgres -> Notion** | New rows (notion_synced=FALSE), AI-written field updates | Every sync cycle |
| **Notion -> Postgres** | Human-owned field changes (status, outcome) | Every sync cycle |
| **Both directions** | Evidence fields (merged, append-only) | When either side has additions |

---

## The notion_synced Flag

All tables with Notion sync use a `notion_synced` boolean column:

- **FALSE** = This row has been created or modified in Postgres but not yet pushed to Notion.
- **TRUE** = This row is in sync with Notion.

### Write convention (ALL agents must follow)

When writing to Postgres, always set `notion_synced = FALSE`:

```bash
psql $DATABASE_URL -c "INSERT INTO thesis_threads (..., notion_synced) VALUES (..., FALSE);"
psql $DATABASE_URL -c "UPDATE actions_queue SET reasoning = '...', notion_synced = FALSE WHERE id = {id};"
```

### Sync cycle (Sync Agent only)

1. Find unsynced rows: `WHERE notion_synced = FALSE`
2. Push to Notion via API.
3. On success: `UPDATE ... SET notion_synced = TRUE, last_synced_at = NOW() WHERE id = {id};`
4. On failure: Leave `notion_synced = FALSE`. Will retry next cycle.

```bash
# Find all unsynced thesis threads
psql $DATABASE_URL -c "SELECT id, thread_name FROM thesis_threads WHERE notion_synced = FALSE;"

# After successful Notion push
psql $DATABASE_URL -c "UPDATE thesis_threads SET notion_synced = TRUE, last_synced_at = NOW() WHERE id = {id};"
```

---

## Edge Cases

### New row in Postgres, no Notion page yet
- `notion_page_id IS NULL` AND `notion_synced = FALSE`
- Create a new Notion page. Store the returned page_id.
- Set `notion_page_id = '{new_page_id}', notion_synced = TRUE, last_synced_at = NOW()`

### Row exists in Notion but not in Postgres
- This shouldn't happen in normal operation (Postgres is the primary write target).
- If detected during a full sync: create the Postgres row from Notion data.
- Set `notion_synced = TRUE` since it already exists in Notion.

### Notion page deleted
- If a Notion page that was synced no longer exists:
- Do NOT delete the Postgres row.
- Set a `deleted_in_notion = TRUE` flag (or similar) and notify.
- Aakash may have trashed it intentionally.

### Multiple rapid updates
- If the same field changes multiple times between sync cycles, only the final state matters.
- The sync pushes the current Postgres value, not a history of changes.
- Change history is preserved in `change_events` table.
