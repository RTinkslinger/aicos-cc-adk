# Datum Data Quality Skill

How to run autonomous data quality checks, maintenance, and garbage cleanup.
Load this skill when running daily maintenance, responding to quality alerts,
or when the Orchestrator triggers a `datum_maintenance` or `datum_quality_check` message.

---

## Overview

Datum has 6 SQL functions for data quality and maintenance. These run inside Postgres
and return structured results. You call them via `psql $DATABASE_URL` and act on the output.

**Key principle:** These functions DO the work. You READ the results, INTERPRET them,
and ESCALATE or LOG as needed. You do not re-implement their logic in bash.

---

## 1. datum_daily_maintenance()

**The master function.** Orchestrates all other maintenance functions in one call.
Run this once per Orchestrator trigger or at least once per day.

```bash
psql $DATABASE_URL -c "SELECT * FROM datum_daily_maintenance();"
```

**Returns:** `(op TEXT, op_status TEXT, op_count INTEGER, op_details TEXT)`

**What it does (in order):**
1. Runs `datum_consistency_enforcer()` — auto-fixes pseudo-IDs, missing notion_page_ids,
   exit status mismatches, signal gaps, thesis backfill gaps
2. Runs `datum_resolve_pseudo_ids()` — fixes broken `pg:` references in actions_queue
3. Runs `datum_thesis_auto_backfill()` — backfills thesis_connection from portfolio
4. Runs `datum_cross_entity_linker()` — builds missing entity_connections links
5. Checks portfolio signal coverage
6. Detects stale actions (>7 days proposed) and auto-expires actions >14 days
7. Reports known duplicates
8. Reports stale companies (not updated in 30 days)
9. Reports network signal coverage percentage
10. Reports raw entities needing enrichment
11. Reports identity resolution candidates (first-name-only with LinkedIn)
12. Runs `datum_garbage_detector()` and reports count

**Status values:** `OK`, `FIXED`, `ENRICHED`, `LINKED`, `CLEANED`, `WARNING`,
`NEEDS_ATTENTION`, `NEEDS_ENRICHMENT`, `NEEDS_CLEANUP`, `INFO`

### How to interpret results

After running, scan the `op_status` column:

| Status | Action Required |
|--------|----------------|
| `OK` | None. Log and move on. |
| `FIXED` / `ENRICHED` / `LINKED` / `CLEANED` | Auto-resolved. Log the count. |
| `WARNING` | Log as warning. If count is high (>20), write a notification. |
| `NEEDS_ATTENTION` | Write a notification for user review. |
| `NEEDS_ENRICHMENT` | Queue enrichment work (see enrichment skill). |
| `NEEDS_CLEANUP` | Run `datum_garbage_detector()` for details, then act. |

### ACK format after maintenance

```
ACK: Daily maintenance completed.
- Consistency: 3 pseudo-IDs resolved, 0 exit mismatches
- Thesis backfill: 5 actions got thesis_connection from portfolio
- Entity links: 12 new current_employee links, 3 portfolio_investment links
- Stale: 8 proposed actions >7 days (2 auto-expired >14d)
- Garbage: 4 entries detected (run cleanup next)
- Network signal coverage: 23%
```

---

## 2. datum_data_quality_check()

Comprehensive quality metrics across all entity types. Use this for health reports
and audits. Does NOT auto-fix — read-only.

```bash
psql $DATABASE_URL -c "SELECT * FROM datum_data_quality_check();"
```

**Returns:** `(check_name TEXT, check_status TEXT, count_value INTEGER, pct_value NUMERIC, details TEXT)`

**Checks performed:**
| Check | What It Measures | Warning Threshold |
|-------|-----------------|-------------------|
| `unlinked_actions` | Actions with no company_notion_id AND no thesis | >10 |
| `actions_thesis_rate` | % of actions with thesis_connection | <50% |
| `portfolio_thesis_pct` | % of portfolio companies with thesis | <50% CRITICAL, <70% WARNING |
| `portfolio_website_pct` | % of portfolio companies with website | <90% |
| `portfolio_funding_pct` | % of portfolio with venture_funding | <60% |
| `exit_consistency` | Exited portfolio with wrong company pipeline_status | Any mismatch |
| `network_embedding_pct` | % of network with embeddings | <80% |
| `entity_connections` | Total entity_connections count | <1000 |
| `stale_proposed` | Proposed actions >7 days old | >20 |
| `companies_embedding_pct` | % of companies with embeddings | <90% |

### When to use

- After a batch enrichment run, to verify improvement
- When writing audit reports
- When the user asks "how's data quality?"
- As input to M12 Data Enrichment loop planning

---

## 3. datum_garbage_detector()

Finds garbage entries in the network table that should be cleaned up.

```bash
psql $DATABASE_URL -c "SELECT * FROM datum_garbage_detector();"
```

**Returns:** `(id INTEGER, person_name TEXT, role_title TEXT, issue TEXT, recommendation TEXT)`

**Issue types detected:**
| Issue | Description | Recommendation |
|-------|-------------|----------------|
| `first_name_only_no_identifiers` | First name only, no Notion page, no LinkedIn, no email | DELETE |
| `empty_name` | NULL or empty person_name | DELETE or INVESTIGATE |
| `multi_person_entry` | Names with commas or "and" (multiple people in one row) | SPLIT or TAG |
| `name_contains_org_suffix` | Person name includes org words (MIT, Inc, Labs, etc.) | CLEAN |

### Acting on garbage results

**NEVER auto-delete.** Instead:

1. For `first_name_only_no_identifiers`:
   - Check if they have any interactions (`people_interactions` table)
   - If no interactions: safe to mark `enrichment_status = 'garbage_candidate'`
   - Write datum_request for user confirmation before actual delete

2. For `empty_name`:
   - Check role_title and email for context
   - If role_title has a name, fix: `UPDATE network SET person_name = extracted_name`
   - If truly empty: mark as garbage_candidate

3. For `multi_person_entry`:
   - Parse the names
   - Create individual records for each person
   - Link them to the same interactions
   - Mark original as `enrichment_status = 'multi_person_entry'`

4. For `name_contains_org_suffix`:
   - Clean the person_name: strip org suffix
   - Move org info to role_title if not already there
   - Mark as `enrichment_status = 'org_entry_in_network'` if it's actually an org

---

## 4. datum_consistency_enforcer()

Auto-fixes consistency issues across tables. Called by `datum_daily_maintenance()`
but can also be run standalone.

```bash
psql $DATABASE_URL -c "SELECT * FROM datum_consistency_enforcer();"
```

**Returns:** `(check_name TEXT, issues_found INTEGER, auto_fixed INTEGER, remaining INTEGER, details TEXT)`

**Auto-fixes performed:**
| Check | Fix |
|-------|-----|
| `pseudo_ids` | Resolves `pg:` references in actions_queue to real notion_page_ids |
| `companies_no_notion_id` | Generates UUIDs for companies missing notion_page_id |
| `exit_consistency` | Updates companies.pipeline_status to match portfolio exit status |
| `signal_gaps` | Runs `datum_signal_propagator()` for portfolio without signals |
| `thesis_backfill` | Runs `datum_thesis_auto_backfill()` for actions missing thesis |
| `known_duplicates` | Reports companies marked Merged/Duplicate (informational only) |

### Safety notes

- `pseudo_ids`: Safe. Replaces broken references with real Notion page IDs.
- `companies_no_notion_id`: Safe. Generates UUIDs only for NULL notion_page_id.
  The UUID is not a real Notion ID, but prevents foreign key issues.
- `exit_consistency`: Safe. Only marks companies as defunct when portfolio confirms exit.
- These are all idempotent — running multiple times is harmless.

---

## 5. datum_stale_action_detector()

Finds actions that need attention: stale, unscored, or duplicative.

```bash
psql $DATABASE_URL -c "SELECT * FROM datum_stale_action_detector();"
```

**Returns:** `(category TEXT, action_count INTEGER, avg_days_old NUMERIC, action_ids INTEGER[], recommendation TEXT)`

**Categories:**
| Category | What | Recommendation |
|----------|------|----------------|
| `stale_proposed_high_priority` | High-score proposed >7 days | Surface to user for triage |
| `stale_proposed_standard` | Standard proposed >7 days | Consider auto-expiring |
| `accepted_no_outcome` | Accepted >14 days, no outcome | Check progress |
| `duplicate_theme_clusters` | Same thesis + type proposed actions | Consolidate |
| `needs_scoring` | Actions with no scores at all | Route to M5 Scoring |

### Acting on stale actions

- **High priority stale:** Write notification: "N high-priority actions waiting >7 days for triage"
- **Standard stale:** `datum_daily_maintenance()` auto-expires these at 14 days
- **Duplicate themes:** Write datum_request asking user to consolidate
- **Needs scoring:** Log for M5 machine to pick up

---

## 6. datum_notion_drift_check()

Checks sync freshness between Postgres and Notion across all entity types.

```bash
psql $DATABASE_URL -c "SELECT * FROM datum_notion_drift_check();"
```

**Returns:** `(entity_type TEXT, total_entities INTEGER, synced INTEGER, possibly_drifted INTEGER, never_synced INTEGER, last_sync_at TIMESTAMPTZ, sync_status TEXT)`

**Entity types checked:** companies, network, portfolio, actions_queue, thesis_threads

**Sync statuses:**
| Status | Meaning | Action |
|--------|---------|--------|
| `OK` | Synced within 24h | None |
| `STALE` | Last sync >24h ago | Write notification suggesting sync run |
| `NEVER_SYNCED` | No sync recorded | Write notification — sync infrastructure may not be set up |

---

## Maintenance Schedule

| Frequency | Function | Trigger |
|-----------|----------|---------|
| Every heartbeat | Check for `datum_maintenance` inbox messages | Orchestrator relay |
| Daily (at minimum) | `datum_daily_maintenance()` | Orchestrator or self-initiated |
| After batch enrichment | `datum_data_quality_check()` | Verify improvement |
| Weekly | `datum_garbage_detector()` + act | Cleanup cycle |
| On demand | `datum_notion_drift_check()` | When sync issues suspected |
| On demand | `datum_stale_action_detector()` | When action queue feels stale |

---

## Notification Patterns

After maintenance, write notifications for anything requiring attention:

```sql
-- High-priority maintenance finding
INSERT INTO notifications (source, type, content, metadata, created_at)
VALUES ('DatumAgent', 'maintenance_alert',
  '4 garbage entries detected, 8 stale actions >7 days, network signal coverage at 23%',
  '{"garbage_count": 4, "stale_actions": 8, "signal_coverage_pct": 23}',
  NOW());

-- Routine maintenance completion
INSERT INTO notifications (source, type, content, metadata, created_at)
VALUES ('DatumAgent', 'maintenance_complete',
  'Daily maintenance: 3 pseudo-IDs resolved, 5 thesis backfilled, 12 entity links created',
  '{"pseudo_ids_fixed": 3, "thesis_backfilled": 5, "links_created": 12}',
  NOW());
```
