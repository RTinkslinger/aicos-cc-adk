# Datum Enrichment Skill

How to run autonomous data enrichment: signal propagation, thesis backfill,
cross-entity linking, and network signal enrichment.
Load this skill when processing enrichment work, running M12 Data Enrichment loops,
or when the Orchestrator triggers enrichment-related messages.

---

## Overview

Datum has 5 SQL functions for enrichment. These propagate intelligence across entities,
backfill missing connections, and build the entity graph. They are the engine behind
M12 Data Enrichment.

**Key principle:** Enrichment is continuous, not one-shot. Every loop improves coverage.
Run these functions, measure delta, log progress.

---

## 1. datum_signal_propagator()

Propagates signals across portfolio, companies, and related entities.
The core mechanism for keeping signal_history current.

```bash
psql $DATABASE_URL -c "SELECT * FROM datum_signal_propagator();"
```

**Returns:** `(operation TEXT, affected_count INTEGER, details TEXT)`

**Operations performed (in order):**

| Operation | What It Does |
|-----------|-------------|
| `exit_signal_propagation` | Portfolio companies marked as exited but missing exit signal in signal_history get one |
| `company_signal_mirror` | Portfolio signal_history is mirrored to the linked companies table entry |
| `red_health_warning` | Active portfolio companies with `health = 'Red'` get a daily risk signal (only one per day) |
| `external_signal_propagation` | Portfolio external_signal field values are added to signal_history (deduped) |

### When to run

- After portfolio data changes (new exits, health changes)
- After Notion sync brings new portfolio data
- As part of `datum_daily_maintenance()` (which calls it automatically)
- When you notice signal_history is empty on portfolio companies

### Interpreting results

- `no_op` with `affected_count = 0` means all signals are already up to date
- Any positive count means new signals were propagated
- After running, check coverage:
  ```bash
  psql $DATABASE_URL -c "
    SELECT COUNT(*) as total,
           COUNT(CASE WHEN signal_history IS NOT NULL AND signal_history::text NOT IN ('[]','null','') THEN 1 END) as with_signals,
           ROUND(100.0 * COUNT(CASE WHEN signal_history IS NOT NULL AND signal_history::text NOT IN ('[]','null','') THEN 1 END) / COUNT(*), 1) as pct
    FROM portfolio;"
  ```

---

## 2. datum_network_signal_enricher()

Enriches network members with signals from their associated portfolio companies.
Network members who work at (current or past) portfolio companies inherit
company-level intelligence.

```bash
psql $DATABASE_URL -c "SELECT * FROM datum_network_signal_enricher();"
```

**Returns:** `(check_name TEXT, people_updated INTEGER, details TEXT)`

**What it does:**
1. Finds network members linked to portfolio companies via `entity_connections`
   (connection_type: current_employee, past_employee, affiliated_with)
2. For each person, builds a `portfolio_association` signal containing:
   - Company name, relationship type, health, status, stage, priority, external signal
3. Adds this signal to the person's `signal_history` (only if they don't already have
   a `portfolio_association` type signal)
4. Reports coverage: how many network members now have signals

### Dependencies

- Requires `entity_connections` to be populated first (run `datum_cross_entity_linker()`)
- Requires portfolio to have data (company_name_id links to companies)

### When to run

- After `datum_cross_entity_linker()` adds new employee links
- After portfolio data changes
- As part of M12 enrichment loop
- Goal: get network signal coverage from ~0.6% toward 50%+

### Monitoring coverage

```bash
psql $DATABASE_URL -c "
  SELECT
    COUNT(*) as total_network,
    COUNT(CASE WHEN signal_history IS NOT NULL AND signal_history::text NOT IN ('[]','null','') THEN 1 END) as with_signals,
    ROUND(100.0 * COUNT(CASE WHEN signal_history IS NOT NULL AND signal_history::text NOT IN ('[]','null','') THEN 1 END) / COUNT(*), 1) as pct
  FROM network;"
```

---

## 3. datum_thesis_auto_backfill()

Backfills thesis_connection on actions from their linked portfolio companies.
If a portfolio company has a thesis and an action is linked to that company but
has no thesis, the thesis is inherited.

```bash
psql $DATABASE_URL -c "SELECT * FROM datum_thesis_auto_backfill();"
```

**Returns:** `(operation TEXT, affected_count INTEGER, details TEXT)`

**Operations:**
| Operation | What |
|-----------|------|
| `actions_thesis_backfill` | Actions linked to portfolio companies inherit their thesis_connection |
| `unlinked_active_actions` | Count of active actions with no company link (informational) |

### When to run

- After new actions are created by Content Agent or Cindy
- After portfolio thesis_connection is updated via Notion sync
- As part of `datum_daily_maintenance()` (automatic)
- Goal: get actions thesis coverage from current level toward 70%+

### Monitoring

```bash
psql $DATABASE_URL -c "
  SELECT
    COUNT(*) as total,
    COUNT(CASE WHEN thesis_connection IS NOT NULL AND thesis_connection != '' THEN 1 END) as with_thesis,
    ROUND(100.0 * COUNT(CASE WHEN thesis_connection IS NOT NULL AND thesis_connection != '' THEN 1 END) / COUNT(*), 1) as pct
  FROM actions_queue
  WHERE status NOT IN ('Dismissed', 'expired');"
```

---

## 4. datum_cross_entity_linker()

Builds and maintains the `entity_connections` graph. This is the backbone of
cross-entity intelligence. Links people to companies, portfolio to companies,
actions to companies.

```bash
psql $DATABASE_URL -c "SELECT * FROM datum_cross_entity_linker();"
```

**Returns:** `(operation TEXT, records_processed INTEGER, details TEXT)`

**Link types created:**

| Operation | Source | Target | Connection Type | Strength |
|-----------|--------|--------|-----------------|----------|
| `new_current_employee_links` | network | company | current_employee | 0.9 |
| `new_past_employee_links` | network | company | past_employee | 0.6 |
| `new_portfolio_investment_links` | portfolio | company | portfolio_investment | 1.0 |
| `new_action_company_links` | action | company | action_references | 0.8 |
| `total_entity_connections` | — | — | — | Total count |

**How it works:**
- Reads `network.current_company_ids` and `network.past_company_ids` (arrays of Notion page IDs)
- Joins to companies via `notion_page_id`
- Creates entity_connections rows for missing links
- Also links portfolio to companies, and actions to companies
- All operations use `NOT EXISTS` subqueries — safe to run repeatedly (idempotent)

### Dependencies

- Network members need `current_company_ids` / `past_company_ids` populated (from Notion sync)
- Companies need `notion_page_id` (from Notion sync or UUID generation)
- Portfolio needs `company_name_id` linking to companies

### When to run

- After new entities are created (new network members, new companies)
- After Notion sync brings new company associations
- Before `datum_network_signal_enricher()` (signals need links to propagate)
- As part of `datum_daily_maintenance()` (automatic)

### Monitoring

```bash
psql $DATABASE_URL -c "
  SELECT connection_type, COUNT(*) as cnt
  FROM entity_connections
  GROUP BY connection_type
  ORDER BY cnt DESC;"
```

---

## 5. datum_company_name_deduplicator()

Finds potential duplicate companies by name matching. Does NOT auto-merge — returns
candidates for review.

```bash
psql $DATABASE_URL -c "SELECT * FROM datum_company_name_deduplicator();"
```

**Returns:** `(company_a_id INTEGER, company_a_name TEXT, company_b_id INTEGER, company_b_name TEXT, similarity_score NUMERIC, match_reason TEXT)`

**Match types:**
| Reason | Score | Example |
|--------|-------|---------|
| `exact_name_match` | 1.0 | "Composio" vs "Composio" (different IDs) |
| `normalized_match` | 0.9 | "Open AI" vs "OpenAI" |
| `prefix_suffix_match` | 0.75 | "Aurva" vs "Aurva AI" |

### Acting on results

For each duplicate pair:

1. **Score >= 0.9:** High confidence. Auto-merge is likely correct.
   - Pick the record with more data (more filled fields, has Notion page ID)
   - Merge the other record's unique data into the winner
   - Mark loser as `pipeline_status = 'Merged/Duplicate'`
   - Update all entity_connections, actions, portfolio referencing the loser

2. **Score 0.75-0.89:** Medium confidence.
   - Create a datum_request with both IDs for user confirmation
   - Do NOT auto-merge

3. **Same company, different records:** Check if one is in portfolio/pipeline.
   - Portfolio-linked record always wins as the canonical entry

### Merge SQL pattern

```sql
-- After user confirms merge (company B into company A)
-- 1. Move entity connections
UPDATE entity_connections SET target_id = $winner_id
WHERE target_type = 'company' AND target_id = $loser_id;

-- 2. Move action references
UPDATE actions_queue SET company_notion_id = (SELECT notion_page_id FROM companies WHERE id = $winner_id)
WHERE company_notion_id = (SELECT notion_page_id FROM companies WHERE id = $loser_id);

-- 3. Merge data fields (COALESCE)
UPDATE companies SET
  website = COALESCE(website, (SELECT website FROM companies WHERE id = $loser_id)),
  sector = COALESCE(sector, (SELECT sector FROM companies WHERE id = $loser_id)),
  description = COALESCE(description, (SELECT description FROM companies WHERE id = $loser_id)),
  updated_at = NOW()
WHERE id = $winner_id;

-- 4. Mark loser
UPDATE companies SET pipeline_status = 'Merged/Duplicate', updated_at = NOW()
WHERE id = $loser_id;
```

---

## 6. datum_entity_health()

Per-entity-type health metrics. Shows fill rates for all important fields.

```bash
psql $DATABASE_URL -c "SELECT * FROM datum_entity_health();"
```

**Returns:** `(entity_type TEXT, metric TEXT, total_count INTEGER, filled_count INTEGER, pct NUMERIC, status TEXT)`

**Entity types and metrics:**

| Entity | Metrics Checked |
|--------|----------------|
| companies | total, has_notion_page_id, has_website, has_page_content, has_signal_history |
| portfolio | total, has_signal_history, has_thesis, has_page_content |
| network | total, has_embedding, has_signal_history |
| actions | total, has_company_link, has_thesis, pseudo_id_count |

### Using for M12 planning

Run this to identify the biggest enrichment gaps:

```bash
psql $DATABASE_URL -c "
  SELECT entity_type, metric, pct, status
  FROM datum_entity_health()
  WHERE status IN ('WARNING', 'CRITICAL')
  ORDER BY entity_type, pct ASC;"
```

The lowest-percentage CRITICAL metrics are your highest-priority enrichment targets.

---

## 7. datum_thesis_coverage()

Maps thesis threads to portfolio companies and actions. Shows which theses
have strong data backing and which are orphaned.

```bash
psql $DATABASE_URL -c "SELECT * FROM datum_thesis_coverage();"
```

**Returns:** `(thesis TEXT, portfolio_count INTEGER, action_count INTEGER, active_portfolio INTEGER, exited_portfolio INTEGER)`

### Interpretation

| Pattern | Meaning |
|---------|---------|
| High portfolio_count, low action_count | Thesis has companies but agents aren't generating actions for it |
| Low portfolio_count, high action_count | Thesis is generating actions but few portfolio companies map to it |
| 0 portfolio_count, 0 action_count | Orphaned thesis — may need archiving or evidence review |
| High exited_portfolio | Thesis may be past its peak — check if still Active |

---

## M12 Enrichment Loop Pattern

When running M12 Data Enrichment as a permanent machinery loop:

```
1. MEASURE: Run datum_entity_health() + datum_data_quality_check()
   → Identify worst metrics (biggest gaps)

2. FIX LINKS: Run datum_cross_entity_linker()
   → Build missing entity graph connections

3. PROPAGATE: Run datum_signal_propagator() + datum_network_signal_enricher()
   → Push signals through the entity graph

4. BACKFILL: Run datum_thesis_auto_backfill()
   → Connect actions to thesis threads

5. DEDUP: Run datum_company_name_deduplicator()
   → Find and resolve duplicates

6. CLEANUP: Run datum_garbage_detector()
   → Identify and handle garbage entries

7. MEASURE AGAIN: Run datum_entity_health() + datum_data_quality_check()
   → Compare to step 1. Log improvement deltas.

8. REPORT: Write audit entry with before/after metrics
```

Each loop should show measurable improvement. If a metric plateaus, that enrichment
source is exhausted — the remaining gaps need web enrichment or user input.
