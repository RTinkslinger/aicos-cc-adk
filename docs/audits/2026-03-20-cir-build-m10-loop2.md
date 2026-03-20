# CIR Build Report — M10 Loop 2
*Executed: 2026-03-20 | Supabase: llfkxnsfczludgigknbs*

## Summary

Deployed the Continuous Intelligence Refresh (CIR) layer — Phase 1 (Foundation) and Phase 2 (Mechanical Propagation). The system is now live and detecting changes across 7 tables, enqueueing propagation events via pgmq, and processing them via pg_cron.

## What Was Deployed

### Phase 1: Foundation

| Component | Status | Details |
|-----------|--------|---------|
| `cir_propagation_rules` | CREATED | 7 cols, 7 seed rules |
| `entity_connections` | CREATED | 12 cols, unique constraint on (source_type, source_id, target_type, target_id, connection_type) |
| `preference_weight_adjustments` | CREATED | 6 cols, unique constraint on (dimension, dimension_value) |
| `cir_state` | CREATED | 3 cols, 4 initial state entries |
| `cir_propagation_log` | CREATED | 7 cols, audit trail for all CIR events |
| Indexes (5) | CREATED | source, target, strength, recent log, pref weights |
| `cir_change_detected()` | CREATED | Generic trigger function — looks up rules, logs, enqueues to pgmq |
| `cir_queue` (pgmq) | CREATED | Message queue for change propagation |
| CIR triggers (7) | INSTALLED | On actions_queue, thesis_threads, content_digests, network, action_outcomes, interactions, companies |

### Phase 2: Mechanical Propagation

| Component | Status | Details |
|-----------|--------|---------|
| `update_preference_from_outcome()` | CREATED | Updates preference weights across 4 dimensions (action_type, priority, source, thesis) using running average |
| `cir-connection-decay` (pg_cron #2) | SCHEDULED | Daily 21:30 UTC — decay connection strengths, prune dead connections |
| `cir-matview-refresh` (pg_cron #3) | SCHEDULED | Every 15 min — refresh `action_scores` materialized view concurrently |
| `cir-staleness-check` (pg_cron #4) | SCHEDULED | Hourly — detect stale Proposed actions (>14 days) |
| `cir-queue-processor` (pg_cron #5) | SCHEDULED | Every 1 min — read, log, archive pgmq messages |

### Propagation Rules (7 seeded)

| # | Source Table | Event | Target Action | Significance |
|---|-------------|-------|--------------|-------------|
| 1 | content_digests | INSERT | rescore_related_actions | medium |
| 2 | thesis_threads | UPDATE | update_thesis_indicators | high |
| 3 | actions_queue | INSERT | process_new_action | medium |
| 4 | action_outcomes | INSERT | update_preference_weights | high |
| 5 | interactions | INSERT | process_new_interaction | medium |
| 6 | network | UPDATE | refresh_person_connections | low |
| 7 | companies | UPDATE | refresh_company_connections | low |

## Adaptations from Spec

1. **No `bucket` column on `actions_queue`** — The spec's preference function referenced `action_rec.bucket`, but `actions_queue` has no `bucket` column. Bucket is computed dynamically in the `action_scores` materialized view via `route_action_to_bucket()`. Replaced with `priority` and added `source` + `thesis_connection` as additional learning dimensions.

2. **No `obligations` table** — The spec included a propagation rule for `obligations.INSERT`. This table does not exist yet. Omitted the rule; can be added when the table is created.

3. **pg_cron minimum interval** — The spec requested 30-second queue processing. pg_cron minimum is 1 minute. Set queue processor to `* * * * *` (every minute). For sub-minute processing, the existing `10 seconds` embedding pattern could be replicated, but 1-minute latency is acceptable for CIR Phase 1.

4. **IST timezone correction** — 3 AM IST = 21:30 UTC (not 21:00). Corrected the cron schedule.

5. **DELETE handling** — The trigger function handles DELETE operations (returns OLD) even though no current rules use DELETE events. Future-proofing.

## Coexistence with Existing Infrastructure

The CIR triggers coexist cleanly with the existing Auto Embeddings pipeline:
- Embedding triggers: `embed_*_on_insert`, `embed_*_on_update`, `clear_*_embedding_on_update`
- CIR triggers: `cir_*` prefix — distinct names, no conflicts
- Both fire on the same events; Postgres executes all AFTER triggers for each row

Two pgmq queues now active:
- `embedding_jobs` — existing auto-embeddings pipeline
- `cir_queue` — CIR change propagation

## Verification Results

| Check | Result |
|-------|--------|
| 5 CIR tables exist | PASS |
| 5 indexes created | PASS |
| 7 propagation rules seeded | PASS |
| 2 functions created (cir_change_detected, update_preference_from_outcome) | PASS |
| 10 trigger events across 7 tables | PASS |
| cir_queue pgmq queue created | PASS |
| 4 pg_cron jobs scheduled (IDs 2-5) | PASS |
| cir_state seeded with 4 entries | PASS |
| action_scores matview has unique index (for CONCURRENTLY) | PASS |

## SQL Artifact

Full idempotent SQL saved to: `sql/cir-build.sql`

## What's Next (Phase 3+)

The current system **detects and logs** all changes but the queue processor only archives messages and logs them. The next phases will:

1. **Wire target_action handlers** — Implement `rescore_related_actions`, `update_thesis_indicators`, `process_new_action`, etc. as actual SQL functions or Edge Function calls
2. **Tier 2 routing** — Route high/critical significance events to Megamind agent via inbox
3. **Seed entity_connections** — Populate initial connections from existing data (vector similarity, thesis links, interaction history)
4. **Integrate preference weights** — Feed `preference_weight_adjustments` into the scoring functions (`route_action_to_bucket`, `score_action_thesis_relevance`)
5. **Create `obligations` table** — Add the missing table + propagation rule
