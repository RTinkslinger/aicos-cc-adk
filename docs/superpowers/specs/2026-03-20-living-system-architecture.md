# Living System Architecture: Continuous Intelligence Refresh (CIR) Layer
*Created: 2026-03-20*

The Continuous Intelligence Refresh layer is what makes the AI CoS a living system rather than a batch processor. It detects changes as they happen, propagates their effects through the intelligence graph incrementally, and ensures every entity in the system reflects the latest state of the world -- without brute-force reprocessing.

---

## 1. Architecture Overview

### The Problem

The AI CoS currently has two modes: **batch processing** (Machine 6 re-scored all 115 actions) and **pipeline processing** (Content Agent processes queue items sequentially). Neither is designed for continuous operation where changes from any agent cascade through the entire intelligence graph in real time.

When Cindy observes a meeting with a portfolio founder, three things should happen within minutes:
1. The person's `last_interaction_date` and `relationship_strength_score` update
2. Connected thesis threads re-evaluate based on new interaction signals
3. Related actions reprioritize (the "check in with Founder X" action should resolve, and new actions may emerge from meeting insights)

Today, these cascades either don't happen or require manual intervention. CIR makes them automatic.

### Where CIR Fits

```
OBSERVATION LAYER (Signal Sources)
  Email, WhatsApp, Granola, Calendar, Content, Screenshots, User Feedback
                 | raw signals
                 v
INTELLIGENCE LAYER (Agents)
  Orchestrator ─> Content Agent, Datum, Megamind, Cindy
                 | structured data writes to Postgres
                 v
    ┌─────────────────────────────────────────────────────┐
    │              CIR LAYER (this spec)                   │
    │                                                      │
    │  DETECT ──> PROPAGATE ──> RE-RANK ──> NOTIFY        │
    │  (triggers)  (incremental)  (Megamind)  (surfaces)   │
    │                                                      │
    │  Lives inside Postgres (triggers + pgmq + pg_cron)   │
    │  + Megamind Agent (strategic reasoning)               │
    │  + ENIAC functions (mechanical scoring)               │
    └─────────────────────────────────────────────────────┘
                 | change events, re-ranked actions, notifications
                 v
INTERFACE LAYER
  WebFront (real-time via Supabase Realtime)
  CAI (via State MCP notifications)
  WhatsApp (via proactive push)
```

### Design Principle: Detect Mechanically, Reason Strategically

CIR uses a **two-tier architecture**:

**Tier 1 (Mechanical, in-database):** Supabase triggers detect changes and enqueue them. pg_cron processes queues. SQL functions compute incremental scores. This tier is fast, cheap, and handles 90% of propagation. Cost: effectively zero (runs inside existing Supabase instance).

**Tier 2 (Strategic, agent-powered):** When a change is significant enough to warrant reasoning -- conviction shifts, cascade re-ranking, strategic reassessment -- the event is routed to Megamind via the existing inbox pattern. This tier is smart, slower, and handles the 10% that requires judgment. Cost: ~$6-10/month (already budgeted in Megamind design).

This split means the system doesn't burn Claude API credits on "update a timestamp" but does apply full reasoning power to "this meeting changed the conviction picture for an active thesis."

---

## 2. Change Detection Layer

### 2.1 Detection Strategy: Supabase Triggers + pgmq

Every table in the intelligence graph gets an AFTER INSERT/UPDATE trigger that:
1. Identifies what changed (field-level diff)
2. Determines if the change is propagation-worthy (not every UPDATE matters)
3. Enqueues a change event to the `change_propagation` pgmq queue

This builds on the existing pattern: the Auto Embeddings pipeline already uses triggers -> pgmq -> pg_cron -> Edge Function. CIR adds a second queue for intelligence propagation.

### 2.2 Change Event Schema

```sql
-- Change events flow through pgmq as JSONB messages
{
  "event_id": "uuid",           -- Unique event identifier
  "source_table": "text",       -- Which table changed
  "record_id": "integer",       -- PK of the changed record
  "event_type": "text",         -- insert | update | delete | outcome
  "changed_fields": ["text"],   -- Which fields changed (UPDATE only)
  "old_values": {},             -- Previous values for changed fields
  "new_values": {},             -- New values for changed fields
  "significance": "text",       -- low | medium | high | critical
  "timestamp": "timestamptz",   -- When the change occurred
  "source_agent": "text"        -- Which agent/surface caused this
}
```

### 2.3 Significance Classification

Not all changes are equal. A trigger function classifies significance to prevent propagation storms:

| Table | Field(s) Changed | Significance | Why |
|-------|-------------------|-------------|-----|
| `thesis_threads` | `conviction` | **critical** | Conviction change cascades to all connected actions, companies, and Megamind |
| `thesis_threads` | `status` (Active <-> Parked) | **critical** | Status change activates/deactivates entire thesis action space |
| `thesis_threads` | `evidence_for`, `evidence_against` | **high** | New evidence may shift conviction, needs Megamind assessment |
| `thesis_threads` | `key_questions_json` | **medium** | Question answered = potential conviction movement |
| `actions_queue` | `status` (any transition) | **high** | Action lifecycle change affects convergence metrics |
| `actions_queue` | `outcome` (Gold/Helpful/Skip) | **high** | Preference feedback = scoring model calibration |
| `actions_queue` | `relevance_score` | **medium** | Score change may shift ranking |
| `content_digests` | `status` = 'published' | **high** | New published digest = new intelligence entering system |
| `content_digests` | `digest_data` | **medium** | Re-analysis updated the digest content |
| `network` | `relationship_tier`, `last_interaction_date` | **medium** | People signals cascade to connected companies/actions |
| `companies` | `deal_status` | **high** | Pipeline progression affects portfolio bucket priorities |
| `companies` | `agent_ids_notes` | **medium** | New IDS signal = entity enrichment |
| `interactions` | INSERT (new) | **medium** | New interaction from Cindy = people + thesis signals |
| `depth_grades` | `execution_status` = 'completed' | **high** | Completed agent work = cascade trigger for Megamind |
| `cascade_events` | INSERT (new) | **low** | Cascade completed = log event, no further propagation |
| `action_outcomes` | INSERT (new) | **high** | New preference data = scoring recalibration |
| `*` | `embedding` column | **none** | Embedding updates are mechanical, no propagation needed |
| `*` | `updated_at`, `last_synced_at` | **none** | Housekeeping fields, no propagation |
| `*` | `notion_synced` | **none** | Sync flag, no propagation |

### 2.4 Trigger Design

One generic trigger function handles all tables. Table-specific behavior comes from configuration, not separate trigger functions.

```sql
-- Propagation significance rules stored as data, not code
CREATE TABLE cir_propagation_rules (
    id SERIAL PRIMARY KEY,
    source_table TEXT NOT NULL,
    field_pattern TEXT NOT NULL,      -- field name or '*' for INSERT
    event_type TEXT NOT NULL,         -- insert | update
    significance TEXT NOT NULL,       -- none | low | medium | high | critical
    propagation_targets TEXT[] NOT NULL, -- which entity types to update
    condition_sql TEXT,               -- optional: extra condition (e.g., "NEW.status = 'published'")
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

The trigger function checks the rules table to determine whether and how to enqueue:

```sql
CREATE OR REPLACE FUNCTION cir_detect_change()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
DECLARE
  changed_fields TEXT[];
  significance TEXT;
  targets TEXT[];
  old_vals JSONB;
  new_vals JSONB;
BEGIN
  -- For INSERT, all fields are "changed"
  IF TG_OP = 'INSERT' THEN
    -- Look up rules for this table + INSERT
    SELECT r.significance, r.propagation_targets
    INTO significance, targets
    FROM public.cir_propagation_rules r
    WHERE r.source_table = TG_TABLE_NAME
      AND r.event_type = 'insert'
      AND r.enabled = TRUE
    ORDER BY
      CASE r.significance
        WHEN 'critical' THEN 1
        WHEN 'high' THEN 2
        WHEN 'medium' THEN 3
        WHEN 'low' THEN 4
        ELSE 5
      END
    LIMIT 1;

    IF significance IS NULL OR significance = 'none' THEN
      RETURN NEW;
    END IF;

    PERFORM pgmq.send(
      queue_name => 'change_propagation',
      msg => jsonb_build_object(
        'source_table', TG_TABLE_NAME,
        'record_id', NEW.id,
        'event_type', 'insert',
        'changed_fields', '[]'::jsonb,
        'old_values', '{}'::jsonb,
        'new_values', to_jsonb(NEW),
        'significance', significance,
        'propagation_targets', to_jsonb(targets),
        'timestamp', NOW()
      )
    );
    RETURN NEW;
  END IF;

  -- For UPDATE, detect which fields changed
  -- (field-level diff logic uses hstore comparison)
  -- Skip if only housekeeping fields changed
  -- Skip if embedding column changed (handled by Auto Embeddings)
  -- Determine significance from highest-matching rule
  -- Enqueue if significance > none

  RETURN NEW;
END;
$$;
```

### 2.5 Why Not WAL-Based Detection

Supabase offers logical replication / WAL-based change capture, but it has drawbacks for this use case:
- **Overhead:** WAL captures ALL changes including housekeeping fields. Triggers can filter before enqueuing.
- **Complexity:** Requires a separate consumer service to decode WAL. Triggers stay inside Postgres.
- **Latency:** WAL streaming has variable lag. Triggers fire synchronously after commit.
- **Cost:** A WAL consumer would need a dedicated service on the droplet. Triggers use existing infra.

WAL-based detection makes sense at 100K+ rows/day. At current volumes (~50-200 changes/day), triggers are simpler, cheaper, and lower latency.

---

## 3. Incremental Propagation Engine

### 3.1 The Propagation Graph

Changes propagate through the intelligence graph along defined paths. Each path has a mechanical tier (SQL function) and an optional strategic tier (Megamind assessment).

```
                    ┌───────────────────────────────────┐
                    │         CHANGE SOURCE              │
                    └───────────┬───────────────────────┘
                                │
          ┌─────────────────────┼─────────────────────────┐
          v                     v                          v
   CONTENT CHANGE         ENTITY CHANGE            PREFERENCE CHANGE
   (digest published,     (person updated,         (outcome rated,
    thesis evidence)       company enriched)         action decided)
          │                     │                          │
          v                     v                          v
   ┌──────────────┐   ┌──────────────┐           ┌──────────────┐
   │ Match thesis │   │ Update       │           │ Recalibrate  │
   │ connections  │   │ connections  │           │ scoring      │
   │ Score actions│   │ Surface      │           │ weights      │
   │ Route bucket │   │ meeting prep │           │              │
   └──────┬───────┘   └──────┬───────┘           └──────┬───────┘
          │                   │                          │
          └───────────────────┼──────────────────────────┘
                              v
                    ┌──────────────────┐
                    │ RE-RANK actions  │
                    │ (if significant) │
                    └────────┬─────────┘
                             v
                    ┌──────────────────┐
                    │ NOTIFY surfaces  │
                    └──────────────────┘
```

### 3.2 Per-Entity-Type Update Logic

#### When a New Content Digest Is Published

**Trigger:** `content_digests.status` changes to `'published'`

**Mechanical (Tier 1):**
1. Auto-embed (already handled by IRGI triggers -- no CIR work needed)
2. Run `score_action_thesis_relevance()` for any actions that reference this digest
3. Run `route_action_to_bucket()` for new actions created by the Content Agent
4. Update `action_scores` materialized view (REFRESH CONCURRENTLY)
5. Increment `thesis_threads.evidence_for` or `evidence_against` if digest has thesis connections

**Strategic (Tier 2):**
6. If digest is connected to an Active thesis with conviction >= "Evolving Fast": enqueue for Megamind cascade assessment
7. If digest produced > 3 new actions: enqueue for Megamind convergence check

**Implementation:** pg_cron job processes the `change_propagation` queue every 30 seconds. For content digests, it calls a SQL function that executes steps 1-5. Steps 6-7 write to `cai_inbox` for Orchestrator routing to Megamind.

#### When a Thesis Thread Changes

**Trigger:** `thesis_threads` conviction, evidence, status, or key_questions change

**Mechanical (Tier 1):**
1. Auto-re-embed (IRGI trigger handles this)
2. Find all open actions connected to this thesis: `SELECT id FROM actions_queue WHERE thesis_connection ILIKE '%' || thread_name || '%' AND status IN ('Proposed', 'Accepted')`
3. Re-run `compute_user_priority_score()` for affected actions
4. Update `user_priority_score` column
5. Refresh `action_scores` materialized view

**Strategic (Tier 2):**
6. **Conviction change:** Always route to Megamind. This is a cascade trigger (see Megamind design sec 4.1).
7. **Status change to Parked/Archived:** Megamind should consider resolving connected actions.
8. **Key question answered:** Route to Megamind for re-assessment of thesis momentum.

#### When an Action Outcome Is Recorded

**Trigger:** `actions_queue.outcome` changes from `'Unknown'` to `'Gold'`/`'Helpful'`/`'Skip'`, OR new `action_outcomes` row inserted

**Mechanical (Tier 1):**
1. Insert/update `action_outcomes` preference record with scoring factor snapshot
2. Recalculate `preference_weight_adjustments` (see Section 5 -- Preference Learning)
3. Apply adjusted weights to `compute_user_priority_score()` for same-type actions

**Strategic (Tier 2):**
4. If outcome is `'Gold'`: Megamind should analyze what made this valuable (pattern extraction)
5. Every 10th outcome: trigger Megamind strategic assessment to check if scoring model drift has occurred

#### When a Network Person Is Updated

**Trigger:** `network` table update on `relationship_tier`, `last_interaction_date`, or Cindy writes new interaction

**Mechanical (Tier 1):**
1. Auto-re-embed (once network embedding triggers are installed)
2. Find companies linked to this person: `SELECT company_id FROM network WHERE id = person_id`
3. Find actions referencing this person (via `action` text or `company_notion_id`)
4. Update `compute_user_priority_score()` if relationship signals changed (network/outreach type boost)

**Strategic (Tier 2):**
5. If person is a portfolio founder AND last interaction > 30 days: surface "check-in needed" action
6. If person is connected to an Active thesis: route relationship signal to Megamind

#### When a Company Is Enriched

**Trigger:** `companies` table update on `deal_status`, `agent_ids_notes`, `sector`, or `jtbd`

**Mechanical (Tier 1):**
1. Auto-re-embed (IRGI trigger handles this)
2. Find thesis threads connected to this company
3. If `deal_status` changed: re-run bucket routing for connected actions
4. Refresh `action_scores` materialized view

**Strategic (Tier 2):**
5. If `deal_status` advanced in pipeline: route to Megamind for strategic assessment
6. If new IDS notes contain contra signals: flag for Megamind contra evaluation

#### When Agent Work Completes (Depth Grade Completed)

**Trigger:** `depth_grades.execution_status` changes to `'completed'`

**Mechanical (Tier 1):**
1. Mark the source action as done/updated
2. Track execution cost

**Strategic (Tier 2):**
3. **Always** route to Megamind for cascade re-ranking (this is Megamind's Type 2 work, already designed)

### 3.3 Propagation Processor (pg_cron)

The propagation processor is a pg_cron job that runs every 30 seconds, reading from the `change_propagation` pgmq queue and executing the appropriate mechanical tier updates.

```sql
-- Scheduled: every 30 seconds
-- Processes up to 20 change events per batch
CREATE OR REPLACE FUNCTION cir_process_propagation(
  batch_size int DEFAULT 20
)
RETURNS TABLE(processed int, routed_to_megamind int, errors int)
LANGUAGE plpgsql
AS $$
DECLARE
  msg RECORD;
  p_processed int := 0;
  p_routed int := 0;
  p_errors int := 0;
BEGIN
  FOR msg IN
    SELECT msg_id, message
    FROM pgmq.read('change_propagation', 300, batch_size)
  LOOP
    BEGIN
      -- Dispatch to table-specific propagation function
      CASE msg.message->>'source_table'
        WHEN 'content_digests' THEN
          PERFORM cir_propagate_content_digest(msg.message);
        WHEN 'thesis_threads' THEN
          PERFORM cir_propagate_thesis_thread(msg.message);
        WHEN 'actions_queue' THEN
          PERFORM cir_propagate_action(msg.message);
        WHEN 'network' THEN
          PERFORM cir_propagate_network(msg.message);
        WHEN 'companies' THEN
          PERFORM cir_propagate_company(msg.message);
        WHEN 'action_outcomes' THEN
          PERFORM cir_propagate_outcome(msg.message);
        WHEN 'depth_grades' THEN
          PERFORM cir_propagate_depth_grade(msg.message);
        WHEN 'interactions' THEN
          PERFORM cir_propagate_interaction(msg.message);
        ELSE
          -- Unknown table, log and skip
          NULL;
      END CASE;

      -- Route high/critical events to Megamind via cai_inbox
      IF msg.message->>'significance' IN ('high', 'critical') THEN
        INSERT INTO cai_inbox (content, processed)
        VALUES (
          'strategy_cascade: ' || msg.message->>'source_table' ||
          ' ' || msg.message->>'event_type' ||
          ' record_id=' || msg.message->>'record_id' ||
          ' significance=' || msg.message->>'significance',
          FALSE
        );
        p_routed := p_routed + 1;
      END IF;

      -- Delete processed message from queue
      PERFORM pgmq.delete('change_propagation', msg.msg_id);
      p_processed := p_processed + 1;

    EXCEPTION WHEN OTHERS THEN
      p_errors := p_errors + 1;
      -- Message remains in queue for retry (visibility timeout = 300s)
    END;
  END LOOP;

  RETURN QUERY SELECT p_processed, p_routed, p_errors;
END;
$$;
```

### 3.4 Propagation Rate Limiting

To prevent storms (e.g., bulk import of 500 companies triggering 500 propagation events):

1. **Deduplication window:** If the same `(source_table, record_id)` appears in the queue within 60 seconds, merge into a single event (take the union of changed_fields, highest significance).
2. **Batch ceiling:** Process max 20 events per 30-second cycle. Overflow stays in queue for next cycle.
3. **Megamind throttle:** Max 5 `strategy_cascade` inbox messages per hour. Beyond that, queue them in a `cir_megamind_backlog` table for the next Megamind heartbeat.
4. **Matview refresh throttle:** `action_scores` refresh max once per 60 seconds (tracked by `cir_last_matview_refresh` config key).

---

## 4. Connection Formation and Renewal

### 4.1 How Connections Form

Connections between entities are implicit (via vector similarity) and explicit (via foreign keys and text references). CIR manages both.

**Implicit connections (vector similarity):**
- When a new entity gets embedded, its nearest neighbors across all tables shift
- The existing `hybrid_search` function already finds cross-table neighbors
- CIR adds a materialized "connections" layer that pre-computes these for fast lookup

**Explicit connections (references):**
- `actions_queue.thesis_connection` text references thesis thread names
- `actions_queue.company_notion_id` links to companies
- `network.company_id` links people to companies
- `thesis_threads.key_companies` text references company names

### 4.2 Entity Connection Table

```sql
CREATE TABLE entity_connections (
    id SERIAL PRIMARY KEY,

    -- Source entity
    source_table TEXT NOT NULL,
    source_id INTEGER NOT NULL,

    -- Target entity
    target_table TEXT NOT NULL,
    target_id INTEGER NOT NULL,

    -- Connection metadata
    connection_type TEXT NOT NULL,
        -- 'vector_similarity' | 'explicit_reference' | 'co_occurrence' | 'interaction'
    strength REAL NOT NULL DEFAULT 0.5,
        -- 0.0-1.0. Initial value depends on connection_type.
        -- vector_similarity: cosine similarity score
        -- explicit_reference: 0.8 (strong by default)
        -- co_occurrence: 0.3 + 0.1 per additional co-occurrence
        -- interaction: based on recency and frequency
    last_evidence_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        -- When was this connection last reinforced by evidence
    evidence_count INTEGER NOT NULL DEFAULT 1,
        -- How many independent signals support this connection
    decay_factor REAL NOT NULL DEFAULT 1.0,
        -- Multiplied into strength over time. Starts at 1.0, decays toward 0.

    -- Dedup
    UNIQUE(source_table, source_id, target_table, target_id, connection_type),

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_entity_connections_source
  ON entity_connections(source_table, source_id);
CREATE INDEX idx_entity_connections_target
  ON entity_connections(target_table, target_id);
CREATE INDEX idx_entity_connections_strength
  ON entity_connections(strength DESC) WHERE decay_factor > 0.1;
```

### 4.3 Connection Formation Algorithm

When a new entity enters the system (INSERT trigger fires):

```
FUNCTION form_connections(new_entity):

  1. WAIT for embedding (check embedding column is NOT NULL, retry after 30s)

  2. FIND vector neighbors:
     FOR each searchable_table IN [content_digests, thesis_threads, actions_queue, companies, network]:
       results = SELECT id, 1 - (embedding <=> new_entity.embedding) AS similarity
                 FROM searchable_table
                 WHERE embedding IS NOT NULL
                   AND (table, id) != (new_entity.table, new_entity.id)
                 ORDER BY embedding <=> new_entity.embedding
                 LIMIT 5

       FOR each result WHERE similarity > THRESHOLD:
         UPSERT entity_connections SET strength = similarity

  3. FIND explicit references:
     -- Table-specific: check text fields for name matches
     -- e.g., if new entity is a company, check thesis_threads.key_companies
     -- if new entity is an action, check thesis_connection text

  4. IF any connection has strength > 0.8 AND target is an Active thesis:
     -- This entity is strategically significant
     -- Route to Megamind for assessment via cai_inbox
```

**Similarity thresholds (tuned for current data volume):**

| Connection Type | Threshold | Rationale |
|----------------|-----------|-----------|
| content_digest <-> thesis_thread | 0.65 | Broad match -- content is often tangentially related |
| action <-> thesis_thread | 0.60 | Actions are often derived from thesis context |
| company <-> thesis_thread | 0.70 | Higher bar -- false company-thesis links are noise |
| company <-> company | 0.75 | Competitive similarity needs higher threshold |
| person <-> thesis_thread | 0.65 | People connect loosely to thesis spaces |
| any <-> any (default) | 0.70 | General threshold |

These thresholds should be recalibrated after 3 months of operation using the preference feedback loop (connections to highly-rated actions get boosted, connections to dismissed actions get weakened).

### 4.4 Connection Decay and Renewal

Connections are not permanent. They decay without reinforcement and strengthen with repeated evidence.

**Decay schedule (pg_cron, daily at 2 AM):**

```sql
CREATE OR REPLACE FUNCTION cir_decay_connections()
RETURNS TABLE(decayed int, removed int)
LANGUAGE plpgsql AS $$
DECLARE
  v_decayed int;
  v_removed int;
BEGIN
  -- Apply daily decay
  -- Decay rate: 0.98 per day for active connections (evidence < 30 days old)
  -- Decay rate: 0.95 per day for stale connections (evidence 30-90 days old)
  -- Decay rate: 0.90 per day for ancient connections (evidence > 90 days old)
  UPDATE entity_connections
  SET decay_factor = decay_factor * CASE
    WHEN last_evidence_at > NOW() - INTERVAL '30 days' THEN 0.98
    WHEN last_evidence_at > NOW() - INTERVAL '90 days' THEN 0.95
    ELSE 0.90
  END,
  updated_at = NOW()
  WHERE decay_factor > 0.1;

  GET DIAGNOSTICS v_decayed = ROW_COUNT;

  -- Remove connections with effective strength < 0.05
  -- (strength * decay_factor < 0.05)
  DELETE FROM entity_connections
  WHERE strength * decay_factor < 0.05;

  GET DIAGNOSTICS v_removed = ROW_COUNT;

  RETURN QUERY SELECT v_decayed, v_removed;
END;
$$;
```

**Renewal on evidence:** When CIR detects a change that reinforces an existing connection (e.g., a new digest mentions a company already connected to a thesis), the connection is renewed:

```sql
UPDATE entity_connections
SET
  last_evidence_at = NOW(),
  evidence_count = evidence_count + 1,
  decay_factor = LEAST(1.0, decay_factor + 0.1),  -- Partial restoration
  strength = LEAST(1.0, strength + 0.02 * evidence_count)  -- Slight boost per repetition
WHERE source_table = $1 AND source_id = $2
  AND target_table = $3 AND target_id = $4;
```

**Breaking connections:** Connections are broken (not just decayed) when evidence explicitly contradicts them:
- A thesis is Parked/Archived: all connections from that thesis decay at 5x rate
- An action is Dismissed with a feedback note mentioning "not relevant": connection to thesis weakens by 0.3
- A company's deal_status moves to "Passed": connections to active thesis threads weaken

---

## 5. Preference Learning Loop

### 5.1 Current State

The `action_outcomes` table exists and stores accept/reject decisions with scoring factor snapshots. The `compute_user_priority_score()` function applies static type-based boosts. These are disconnected -- outcomes are recorded but don't feed back into scoring.

### 5.2 The Feedback Cycle

```
Aakash rates action (Gold/Helpful/Skip/Dismiss)
    |
    v
action_outcomes row created (with scoring_factors snapshot)
    |
    v
CIR detects INSERT on action_outcomes (high significance)
    |
    v
preference_weight_adjustments recalculated (SQL function)
    |
    v
compute_user_priority_score() reads adjusted weights
    |
    v
Similar future actions score differently
    |
    v
Aakash sees better-calibrated proposals
    |
    v
(cycle repeats, compound improvement)
```

### 5.3 Preference Weight Adjustments

A simple approach that works with small datasets (no ML training required):

```sql
CREATE TABLE preference_weight_adjustments (
    id SERIAL PRIMARY KEY,
    dimension TEXT NOT NULL UNIQUE,
        -- 'action_type:Research', 'action_type:Meeting/Outreach',
        -- 'bucket:Discover New', 'thesis:Agentic AI Infrastructure',
        -- 'priority:P0', 'source:Content Pipeline', etc.
    adjustment REAL NOT NULL DEFAULT 0.0,
        -- Added to base score for actions matching this dimension
        -- Positive = Aakash tends to accept/rate highly
        -- Negative = Aakash tends to dismiss/skip
    sample_count INTEGER NOT NULL DEFAULT 0,
        -- How many outcomes inform this adjustment
    confidence REAL NOT NULL DEFAULT 0.0,
        -- 0.0-1.0. Low confidence = small adjustment effect.
        -- Confidence = 1 - (1/sqrt(sample_count + 1))
    last_recalculated TIMESTAMPTZ DEFAULT NOW()
);
```

**Recalculation function (called by CIR when new outcome arrives):**

```sql
CREATE OR REPLACE FUNCTION cir_recalculate_preference_weights()
RETURNS void
LANGUAGE plpgsql AS $$
DECLARE
  dim RECORD;
BEGIN
  -- Recalculate per action_type
  FOR dim IN
    SELECT
      'action_type:' || action_type AS dimension,
      COUNT(*) AS n,
      AVG(CASE decision
        WHEN 'accepted' THEN
          CASE feedback_note  -- proxy for outcome rating
            WHEN 'Gold' THEN 1.0
            WHEN 'Helpful' THEN 0.5
            ELSE 0.2
          END
        WHEN 'dismissed' THEN -0.5
        WHEN 'deferred' THEN -0.1
        ELSE 0.0
      END) AS avg_sentiment
    FROM action_outcomes
    WHERE decided_at > NOW() - INTERVAL '90 days'  -- rolling 90-day window
    GROUP BY action_type
    HAVING COUNT(*) >= 3  -- minimum sample size
  LOOP
    INSERT INTO preference_weight_adjustments (dimension, adjustment, sample_count, confidence, last_recalculated)
    VALUES (
      dim.dimension,
      dim.avg_sentiment * 2.0,  -- Scale: avg sentiment of 0.5 -> +1.0 boost
      dim.n,
      1.0 - (1.0 / sqrt(dim.n + 1.0)),
      NOW()
    )
    ON CONFLICT (dimension) DO UPDATE SET
      adjustment = EXCLUDED.adjustment,
      sample_count = EXCLUDED.sample_count,
      confidence = EXCLUDED.confidence,
      last_recalculated = NOW();
  END LOOP;

  -- Similar loops for bucket, thesis, priority, source dimensions
  -- (omitted for brevity but same pattern)
END;
$$;
```

### 5.4 Integrating Preferences into Scoring

The existing `compute_user_priority_score()` function adds a preference adjustment:

```sql
-- Addition to compute_user_priority_score:
-- After computing raw_score from base + priority_boost + type_boost + recency_factor:

-- Preference adjustment (from learning loop)
preference_adj := 0.0;
SELECT SUM(pw.adjustment * pw.confidence)
INTO preference_adj
FROM preference_weight_adjustments pw
WHERE pw.dimension IN (
  'action_type:' || action_row.action_type,
  'priority:' || action_row.priority
  -- extend with bucket, thesis dimensions as available
)
AND pw.sample_count >= 5;  -- Only apply well-supported adjustments

raw_score := raw_score + COALESCE(preference_adj, 0.0);
```

### 5.5 What This Is NOT

This is not ML. It is a weighted running average of historical outcomes projected onto scoring dimensions. It works because:
- The action space has clear categorical dimensions (type, bucket, priority, thesis)
- The feedback signal is discrete and clean (Gold/Helpful/Skip/Dismiss)
- The data volume is small (50-200 outcomes over months, not millions)
- The adjustment is additive and bounded, so it can't destabilize scoring

ML would be warranted when:
- Outcome volume exceeds 1,000+ with clear patterns
- Interaction effects between dimensions matter (e.g., "Research + Agentic AI = always Gold but Research + Healthcare AI = always Skip")
- The system needs to predict outcomes for novel combinations not seen before

At that point, a simple logistic regression or gradient-boosted tree trained on `action_outcomes` with `scoring_factors` JSONB as features would be the next step. See Section 10 (ML Opportunities).

---

## 6. Continuous Mode for Each Machine (M1-M9)

The original system uses 9 "machines" for batch processing. CIR transforms each into a continuous stream:

### M1: Signal Ingestion
**Batch mode:** YouTube/RSS extraction every 5 minutes via cron
**Continuous mode:** No change needed. The 5-minute cron is already continuous enough. Extraction produces `content_digests` rows with status='pending'. CIR doesn't touch ingestion.

### M2: Content Analysis
**Batch mode:** Content Agent picks up pending digests sequentially
**Continuous mode:** No change needed. Content Agent already runs continuously via Orchestrator heartbeat. CIR doesn't touch analysis -- it picks up AFTER analysis completes (when status changes to 'published').

### M3: Entity Extraction
**Batch mode:** Content Agent extracts entities during analysis, writes to inbox
**Continuous mode:** CIR adds: when Datum Agent creates/enriches a company or person, the `entity_connections` table is updated automatically. No batch entity extraction pass needed -- entities flow through as they're mentioned.

### M4: Thesis Matching
**Batch mode:** Machine 4 cross-referenced all content against all thesis threads
**Continuous mode with CIR:** When a new digest is published, `score_action_thesis_relevance()` runs for connected actions. When thesis evidence changes, connected actions re-score. No full cross-reference needed -- only the changed entity's connections update.

**Key optimization:** Instead of N_digests x N_theses comparisons, CIR does 1 x (connected theses for this digest). With 8 active theses and ~20 digests/week, this is ~160 comparisons/week vs the theoretical 8x22 = 176 if done in batch. The savings grow as data volume increases.

### M5: Action Scoring
**Batch mode:** Machine 5 scored all 115 actions with the 7-factor model
**Continuous mode with CIR:** Actions are scored at creation time (by Content Agent). CIR incrementally re-scores only when connected entities change. The `user_priority_score` column updates in place. The `action_scores` materialized view refreshes at most once per minute.

**Volume impact:** Instead of re-scoring 115 actions, CIR re-scores ~3-10 actions per change event. At 10 events/day, that's 30-100 re-scores/day vs 115 x (number of batch runs).

### M6: Action Ranking
**Batch mode:** Machine 6 ranked all actions by score, assigned buckets
**Continuous mode with CIR:** Ranking is implicit -- the `user_triage_queue` view always returns actions ORDER BY score DESC. Bucket assignment happens at creation time via `route_action_to_bucket()`. CIR re-routes only when connected thesis or company data changes.

### M7: Depth Grading (new -- Megamind)
**Batch mode:** Never existed
**Continuous mode:** Megamind grades agent-delegated actions as they appear. Already designed as continuous in the Megamind spec.

### M8: Cascade Re-ranking (new -- Megamind)
**Batch mode:** Never existed
**Continuous mode:** CIR triggers Megamind cascade when agent work completes or conviction changes. Already designed as event-driven.

### M9: Strategic Assessment (new -- Megamind)
**Batch mode:** Daily assessment
**Continuous mode:** Daily cadence is appropriate. No change needed. CIR ensures the data Megamind reads for assessment is always current.

---

## 7. Infrastructure Recommendation

### Recommendation: Option D (Hybrid) with Elements of Option E

**Primary: Supabase-native triggers + pgmq + pg_cron for detection and mechanical propagation (Option A)**
**Strategic layer: Megamind Agent for reasoning about significant changes (Option C)**
**Evolution path: Preference learning loop as a proto-ML pipeline (Option E)**

### Why This Combination

| Requirement | Solution | Why Not Alternatives |
|-------------|----------|---------------------|
| **Change detection** | Supabase triggers | WAL is overkill for 50-200 changes/day. Edge Functions have cold starts. |
| **Event queue** | pgmq (already installed) | No new infrastructure. Proven pattern from Auto Embeddings. |
| **Mechanical propagation** | pg_cron + SQL functions | Runs in-database, zero network hops, microsecond latency for score recalculation. |
| **Strategic propagation** | Megamind via cai_inbox | Already designed. Reuses existing routing. Full Claude reasoning for the 10% that needs it. |
| **Preference learning** | SQL aggregation + weight table | Simpler than ML, works with small data, interpretable, no training pipeline needed. |
| **Real-time surfaces** | Supabase Realtime (already available) | WebFront subscribes to table changes. Zero additional infrastructure. |
| **Connection management** | New `entity_connections` table + SQL functions | Lightweight, queryable, decayable. Graph DB (Neo4j) is overkill for current entity count. |

### What Each Option Costs

| Option | Monthly Cost | New Infrastructure | Maintenance |
|--------|-------------|-------------------|-------------|
| **A: Supabase-native** | $0 incremental | None | Trigger + function management |
| **B: Edge Functions** | ~$5-15 (invocations) | Edge Function deploys | Cold start monitoring |
| **C: Dedicated CIR Agent** | ~$20-40 | New ClaudeSDKClient | Token budget management |
| **D: Hybrid (recommended)** | ~$0-5 + Megamind ($6-10) | pgmq queue + SQL functions | Moderate: triggers + Megamind budget |
| **E: ML Pipeline** | $10-30 (training compute) | ML training infra | Model retraining, drift monitoring |

Option D costs effectively nothing beyond the already-planned Megamind budget. The pg_cron jobs and triggers run inside the existing Supabase instance with negligible compute overhead.

### Scaling Considerations

Current volumes: ~145 rows across 4 searchable tables, ~50-200 changes/day.

| Volume Threshold | What Changes |
|-----------------|-------------|
| **<1,000 rows, <500 changes/day** | Current design is perfect. No optimization needed. |
| **1K-10K rows, 500-5K changes/day** | Add connection table partitioning by source_table. Increase pg_cron batch size. |
| **10K-100K rows, 5K-50K changes/day** | Move to LISTEN/NOTIFY for high-frequency tables instead of pgmq. Add connection indexing. |
| **>100K rows, >50K changes/day** | Consider WAL-based detection. Add a dedicated propagation worker on the droplet. |

The system is years away from these thresholds at current growth rates.

---

## 8. Database Schema: New Tables for CIR

### 8.1 Change Propagation Queue

Uses existing pgmq infrastructure. No new table -- just a new queue:

```sql
SELECT pgmq.create('change_propagation');
```

### 8.2 Propagation Rules

```sql
CREATE TABLE cir_propagation_rules (
    id SERIAL PRIMARY KEY,
    source_table TEXT NOT NULL,
    field_pattern TEXT NOT NULL,
        -- Specific field name, or '*' for INSERT events
    event_type TEXT NOT NULL,
        -- 'insert' | 'update'
    significance TEXT NOT NULL CHECK (significance IN ('none', 'low', 'medium', 'high', 'critical')),
    propagation_targets TEXT[] NOT NULL,
        -- Entity types to update: ['thesis_threads', 'actions_queue', 'companies', etc.]
    condition_sql TEXT,
        -- Optional extra SQL condition (e.g., "NEW.status = 'published'")
    route_to_megamind BOOLEAN DEFAULT FALSE,
        -- If TRUE, also sends to Megamind via cai_inbox
    enabled BOOLEAN DEFAULT TRUE,
    notes TEXT,
        -- Human-readable explanation
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Seed with initial rules
INSERT INTO cir_propagation_rules (source_table, field_pattern, event_type, significance, propagation_targets, route_to_megamind, notes) VALUES
-- Content Digests
('content_digests', 'status', 'update', 'high', ARRAY['thesis_threads', 'actions_queue'], TRUE, 'Published digest needs thesis matching + action scoring'),
('content_digests', '*', 'insert', 'low', ARRAY[]::TEXT[], FALSE, 'New pending digest, no propagation until published'),

-- Thesis Threads
('thesis_threads', 'conviction', 'update', 'critical', ARRAY['actions_queue', 'companies'], TRUE, 'Conviction change cascades everywhere'),
('thesis_threads', 'status', 'update', 'critical', ARRAY['actions_queue'], TRUE, 'Active<->Parked affects entire action space'),
('thesis_threads', 'evidence_for', 'update', 'high', ARRAY['actions_queue'], TRUE, 'New evidence may shift conviction'),
('thesis_threads', 'evidence_against', 'update', 'high', ARRAY['actions_queue'], TRUE, 'Contra evidence is always significant'),
('thesis_threads', 'key_questions_json', 'update', 'medium', ARRAY['actions_queue'], FALSE, 'Question answered, moderate significance'),

-- Actions Queue
('actions_queue', 'status', 'update', 'high', ARRAY['thesis_threads'], FALSE, 'Action lifecycle affects convergence'),
('actions_queue', 'outcome', 'update', 'high', ARRAY[]::TEXT[], FALSE, 'Preference signal triggers recalibration'),
('actions_queue', '*', 'insert', 'medium', ARRAY['thesis_threads'], FALSE, 'New action needs scoring + bucket routing'),

-- Action Outcomes
('action_outcomes', '*', 'insert', 'high', ARRAY[]::TEXT[], FALSE, 'Preference data triggers weight recalculation'),

-- Network
('network', 'relationship_tier', 'update', 'medium', ARRAY['companies', 'actions_queue'], FALSE, 'Relationship change affects connected entities'),
('network', 'last_interaction_date', 'update', 'medium', ARRAY['actions_queue'], FALSE, 'Interaction recency affects outreach scoring'),

-- Companies
('companies', 'deal_status', 'update', 'high', ARRAY['thesis_threads', 'actions_queue'], TRUE, 'Pipeline progression is strategically significant'),
('companies', 'agent_ids_notes', 'update', 'medium', ARRAY['thesis_threads'], FALSE, 'IDS enrichment updates thesis connections'),

-- Depth Grades
('depth_grades', 'execution_status', 'update', 'high', ARRAY[]::TEXT[], TRUE, 'Completed agent work triggers Megamind cascade'),

-- Interactions (Cindy)
('interactions', '*', 'insert', 'medium', ARRAY['network', 'actions_queue'], FALSE, 'New interaction updates people signals');
```

### 8.3 Entity Connections Table

(Defined in Section 4.2 above)

### 8.4 Preference Weight Adjustments Table

(Defined in Section 5.3 above)

### 8.5 CIR State Table

```sql
CREATE TABLE cir_state (
    key TEXT PRIMARY KEY,
    value JSONB NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Initial state
INSERT INTO cir_state (key, value) VALUES
    ('last_matview_refresh', '"2026-01-01T00:00:00Z"'),
    ('propagation_stats_today', '{"processed": 0, "routed_to_megamind": 0, "errors": 0}'),
    ('connection_formation_stats', '{"formed": 0, "renewed": 0, "decayed": 0, "removed": 0}'),
    ('preference_recalculation_count', '0'),
    ('megamind_inbox_throttle_count', '0'),
    ('last_connection_decay_run', '"2026-01-01T00:00:00Z"');
```

### 8.6 CIR Propagation Log

For observability -- what did CIR do and when:

```sql
CREATE TABLE cir_propagation_log (
    id SERIAL PRIMARY KEY,
    source_table TEXT NOT NULL,
    record_id INTEGER NOT NULL,
    event_type TEXT NOT NULL,
    significance TEXT NOT NULL,
    actions_taken JSONB NOT NULL,
        -- {
        --   "scores_updated": 3,
        --   "connections_formed": 1,
        --   "connections_renewed": 2,
        --   "routed_to_megamind": true,
        --   "matview_refreshed": false,
        --   "preference_weights_updated": false
        -- }
    processing_time_ms INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Partition by month for easy cleanup
-- (or just DELETE WHERE created_at < NOW() - INTERVAL '90 days' via pg_cron)
CREATE INDEX idx_cir_log_recent ON cir_propagation_log(created_at DESC);
CREATE INDEX idx_cir_log_significance ON cir_propagation_log(significance) WHERE significance IN ('high', 'critical');
```

---

## 9. Supabase Implementation

### 9.1 New pgmq Queue

```sql
SELECT pgmq.create('change_propagation');
```

### 9.2 pg_cron Jobs

```sql
-- Process change propagation queue (every 30 seconds)
SELECT cron.schedule(
  'cir-process-propagation',
  '30 seconds',
  $$SELECT * FROM cir_process_propagation(20);$$
);

-- Decay entity connections (daily at 2 AM IST = 20:30 UTC)
SELECT cron.schedule(
  'cir-decay-connections',
  '30 20 * * *',
  $$SELECT * FROM cir_decay_connections();$$
);

-- Recalculate preference weights (every 6 hours)
SELECT cron.schedule(
  'cir-preference-recalc',
  '0 */6 * * *',
  $$SELECT cir_recalculate_preference_weights();$$
);

-- Clean propagation log (weekly, keep 90 days)
SELECT cron.schedule(
  'cir-log-cleanup',
  '0 3 * * 0',
  $$DELETE FROM cir_propagation_log WHERE created_at < NOW() - INTERVAL '90 days';$$
);

-- Refresh action_scores materialized view (every 60 seconds, only if needed)
SELECT cron.schedule(
  'cir-matview-refresh',
  '60 seconds',
  $$
    DO $$
    DECLARE
      last_refresh TIMESTAMPTZ;
      latest_change TIMESTAMPTZ;
    BEGIN
      SELECT (value #>> '{}')::timestamptz INTO last_refresh
      FROM cir_state WHERE key = 'last_matview_refresh';

      SELECT MAX(updated_at) INTO latest_change
      FROM actions_queue WHERE status = 'Proposed';

      IF latest_change > last_refresh THEN
        REFRESH MATERIALIZED VIEW CONCURRENTLY action_scores;
        UPDATE cir_state SET value = to_jsonb(NOW()::text), updated_at = NOW()
        WHERE key = 'last_matview_refresh';
      END IF;
    END $$;
  $$
);
```

### 9.3 Trigger Installation

```sql
-- Install CIR detection trigger on all intelligence tables
-- The trigger function checks cir_propagation_rules to decide what to do

CREATE TRIGGER cir_detect_change_content_digests
  AFTER INSERT OR UPDATE ON content_digests
  FOR EACH ROW
  EXECUTE FUNCTION cir_detect_change();

CREATE TRIGGER cir_detect_change_thesis_threads
  AFTER INSERT OR UPDATE ON thesis_threads
  FOR EACH ROW
  EXECUTE FUNCTION cir_detect_change();

CREATE TRIGGER cir_detect_change_actions_queue
  AFTER INSERT OR UPDATE ON actions_queue
  FOR EACH ROW
  EXECUTE FUNCTION cir_detect_change();

CREATE TRIGGER cir_detect_change_action_outcomes
  AFTER INSERT ON action_outcomes
  FOR EACH ROW
  EXECUTE FUNCTION cir_detect_change();

CREATE TRIGGER cir_detect_change_network
  AFTER INSERT OR UPDATE ON network
  FOR EACH ROW
  EXECUTE FUNCTION cir_detect_change();

CREATE TRIGGER cir_detect_change_companies
  AFTER INSERT OR UPDATE ON companies
  FOR EACH ROW
  EXECUTE FUNCTION cir_detect_change();

CREATE TRIGGER cir_detect_change_depth_grades
  AFTER UPDATE ON depth_grades
  FOR EACH ROW
  EXECUTE FUNCTION cir_detect_change();

CREATE TRIGGER cir_detect_change_interactions
  AFTER INSERT ON interactions
  FOR EACH ROW
  EXECUTE FUNCTION cir_detect_change();
```

### 9.4 Trigger Ordering

CIR triggers must fire AFTER the Auto Embeddings triggers (which are also AFTER INSERT/UPDATE). PostgreSQL fires AFTER triggers in alphabetical order by trigger name. The `cir_detect_change_*` names sort after `embed_*` and `clear_*` names, so ordering is correct by default.

### 9.5 RLS Considerations

CIR functions use `SECURITY DEFINER` to bypass RLS. The triggers and pg_cron jobs run with the postgres role, which has full access. No RLS changes needed.

---

## 10. ML Opportunities

### 10.1 Where ML Would Help (Future, Not Now)

| Opportunity | Current Solution | ML Alternative | When to Switch |
|-------------|-----------------|---------------|---------------|
| **Action outcome prediction** | Weighted running average by type/bucket | Logistic regression on scoring_factors JSONB | 500+ outcomes with varied types |
| **Thesis conviction forecasting** | Evidence count heuristic | Time-series model on evidence_entries + external signals | 6+ months of conviction history across 10+ theses |
| **People importance scoring** | Static relationship_tier | Graph neural network on interaction graph | 1,000+ interactions logged by Cindy |
| **Content relevance prediction** | Vector similarity + FTS | Fine-tuned classifier on accepted/dismissed content | 200+ content digests with outcome data |
| **Connection strength prediction** | Cosine similarity + decay | Link prediction model on entity_connections | 1,000+ connections with evidence_count > 3 |
| **Aakash time allocation optimization** | Megamind's ROI calculation | Reinforcement learning on action outcomes | 1,000+ outcomes + calendar data |

### 10.2 Where ML Is Overkill (Now and Likely Always)

| Task | Why ML Doesn't Help |
|------|-------------------|
| **Change detection** | Binary: did the field change? Triggers are perfect. |
| **Bucket routing** | 4 buckets with clear keyword signals. Regex + scoring works. |
| **Connection decay** | Exponential decay is a known, well-understood function. |
| **Matview refresh timing** | Conditional refresh is a simple timestamp comparison. |
| **Notification routing** | Rule-based: significance = high -> notify. No learning needed. |

### 10.3 The ML Glide Path

When the preference store has enough data (estimated: 6-9 months of operation, 300-500 outcomes), the upgrade path is:

1. **Export training data:** `SELECT scoring_factors, decision, outcome FROM action_outcomes WHERE decided_at > NOW() - INTERVAL '6 months'`
2. **Train simple model:** Logistic regression or XGBoost. Features = scoring_factors JSONB keys. Target = binary (Gold/Helpful vs Skip/Dismiss).
3. **Deploy as Supabase Edge Function:** Model weights are small (~few KB for logistic regression). Edge Function loads weights and scores in-request.
4. **Replace `compute_user_priority_score()`** with model prediction + a small human override term.
5. **A/B test:** Run model-scored and rule-scored actions side by side. Track acceptance rates.

This requires no new infrastructure. The Edge Function pattern is already established (embeddings use it). The only new cost is occasional model retraining (~monthly, takes seconds for logistic regression on <1K rows).

---

## 11. Agent Integration

### 11.1 How Each Agent Participates in CIR

| Agent | CIR Role | Reads | Writes | Changes Detected By CIR |
|-------|---------|-------|--------|------------------------|
| **Content Agent** | Primary signal producer | content_digests, thesis_threads | content_digests (status, digest_data), thesis_threads (evidence), actions_queue (new actions) | Every write triggers CIR detection |
| **Datum Agent** | Entity enrichment producer | network, companies | network (enrichment fields), companies (enrichment fields), datum_requests | Entity enrichment triggers connection formation |
| **Megamind** | Strategic propagation consumer + producer | actions_queue, thesis_threads, depth_grades, cascade_events, strategic_assessments | depth_grades, cascade_events, strategic_assessments, actions_queue (re-score, resolve) | Completed cascades are logged; CIR doesn't re-trigger on Megamind's writes (no infinite loop) |
| **Cindy** | Interaction signal producer | interactions, network | interactions (new), cai_inbox (signals for Datum/Megamind) | New interaction triggers people update + action re-scoring |
| **Orchestrator** | Router (unchanged) | cai_inbox | cai_inbox (routing) | CIR writes strategy_cascade messages to cai_inbox for Orchestrator routing |

### 11.2 Preventing Infinite Loops

CIR must not create propagation storms where Agent A's write triggers CIR, which writes to cai_inbox, which Orchestrator routes to Agent B, which writes to a table, which triggers CIR again, etc.

**Loop prevention mechanisms:**

1. **Source tracking:** Every change event includes `source_agent`. CIR rules can exclude self-triggered events. E.g., when Megamind updates `actions_queue.relevance_score` during a cascade, the trigger fires but the propagation rule for that field checks `source_agent != 'megamind'` before enqueuing.

2. **Significance dampening:** CIR-initiated changes are classified as `low` significance by default, which means they don't route to Megamind. Only original agent writes produce `high`/`critical` events.

3. **Cascade chain limit:** Already in Megamind design (max 1 follow-up cascade per trigger). CIR enforces this at the queue level: if a change event's source is `cir_propagation`, it's processed mechanically only (no Megamind routing).

4. **Deduplication window:** Same `(table, record_id)` within 60 seconds = merged into single event.

### 11.3 Agent Awareness of CIR

Agents do NOT need to know about CIR. They write to Postgres as usual. CIR is invisible infrastructure, just like Auto Embeddings. This is critical for simplicity -- agents don't coordinate with CIR, they don't wait for propagation, and they don't check CIR state.

The one exception: **Megamind reads `entity_connections`** during cascade processing to determine blast radius. This is a read-only dependency, not coordination.

---

## 12. Cost Model

### 12.1 Supabase Compute Cost

CIR runs entirely inside the existing Supabase instance. No additional compute needed.

| Component | Compute Profile | Cost |
|-----------|----------------|------|
| Change detection triggers | ~1ms per trigger execution, ~50-200/day | Negligible (inside Supabase compute allocation) |
| pgmq queue operations | ~1ms per send/read/delete | Negligible |
| pg_cron propagation processor | Every 30s, processes 0-20 events, ~50-500ms per batch | Negligible |
| pg_cron connection decay | Daily, updates ~100-1000 rows, ~100ms | Negligible |
| pg_cron preference recalc | Every 6h, aggregates ~50-500 rows, ~200ms | Negligible |
| Matview refresh | Every 60s (conditional), ~200ms when executed | Negligible |
| SQL propagation functions | ~5-20ms per function call | Negligible |

**Total incremental Supabase cost: $0.** CIR is pure SQL running inside an existing database. It adds no new services, no new infrastructure, and no external API calls.

### 12.2 Megamind Cost (Already Budgeted)

CIR routes ~2-10 events/day to Megamind for strategic assessment. This falls within Megamind's existing budget of $6-10/month.

| CIR-to-Megamind Event Type | Frequency | Megamind Cost per Event |
|----------------------------|-----------|----------------------|
| Conviction change cascade | ~1-2/week | ~$0.06 |
| Published digest with thesis links | ~3-5/week | ~$0.04 (combined with regular cascade) |
| Deal status progression | ~1-2/month | ~$0.06 |
| Completed depth grade cascade | ~2-5/day | ~$0.06 (already budgeted) |
| 10th outcome trigger | ~1/month | ~$0.10 |

### 12.3 Storage Cost

| Table | Estimated Growth | Storage per Month |
|-------|-----------------|-------------------|
| `cir_propagation_rules` | ~30 rows, static | <1 KB |
| `entity_connections` | ~500 connections growing to ~5K | ~50 KB/month |
| `preference_weight_adjustments` | ~20-50 dimensions, static size | <5 KB |
| `cir_state` | 6 keys, static | <1 KB |
| `cir_propagation_log` | ~50-200 entries/day, 90-day retention | ~5 MB/month |
| pgmq `change_propagation` queue | Transient (processed within 30s) | ~0 (messages deleted after processing) |

**Total incremental storage: ~5 MB/month.** Well within Supabase free tier limits.

### 12.4 Total CIR Cost

| Cost Category | Monthly Cost |
|--------------|-------------|
| Supabase compute (triggers, pg_cron, SQL functions) | $0 |
| Supabase storage (new tables) | $0 (within existing allocation) |
| Megamind strategic routing | $0 (within existing Megamind budget) |
| External API calls | $0 (no external calls) |
| **Total** | **$0 incremental** |

CIR is effectively free. It's pure database logic running inside infrastructure that already exists and is already paid for.

---

## 13. Implementation Plan

### Phase 1: Foundation (S, 1-3 hours)

**Goal:** Install the detection and queue infrastructure. CIR detects changes but doesn't propagate yet.

- [ ] Create `change_propagation` pgmq queue
- [ ] Create `cir_propagation_rules` table with initial rules
- [ ] Create `cir_state` table with initial values
- [ ] Create `cir_propagation_log` table
- [ ] Create `cir_detect_change()` trigger function
- [ ] Install triggers on all 8 tables
- [ ] Verify: INSERT a test row, confirm message appears in pgmq queue
- [ ] Verify: UPDATE a thesis conviction, confirm 'critical' message enqueued

**Validation:** `SELECT * FROM pgmq.read('change_propagation', 0, 100)` shows events after writes to any monitored table.

### Phase 2: Mechanical Propagation (M, 3-8 hours)

**Goal:** CIR processes changes and updates scores/connections incrementally.

- [ ] Create per-table propagation functions (`cir_propagate_content_digest`, `cir_propagate_thesis_thread`, etc.)
- [ ] Create `cir_process_propagation()` master processor
- [ ] Schedule pg_cron job (30-second interval)
- [ ] Implement score re-calculation for affected actions
- [ ] Implement conditional matview refresh
- [ ] Implement Megamind routing for high/critical events (write to cai_inbox)
- [ ] Add deduplication window (60-second merge)
- [ ] Verify: Publish a digest, confirm connected action scores update within 60 seconds
- [ ] Verify: Change thesis conviction, confirm strategy_cascade message in cai_inbox
- [ ] Verify: No propagation storm on bulk update

**Validation:** Change thesis conviction from "Evolving" to "Evolving Fast". Within 60 seconds:
- Connected actions have updated `user_priority_score`
- `action_scores` materialized view is refreshed
- `cai_inbox` has a `strategy_cascade` message for Megamind

### Phase 3: Entity Connections (M, 3-8 hours)

**Goal:** Entities automatically form and maintain connections.

- [ ] Create `entity_connections` table
- [ ] Create `cir_form_connections()` function (called by propagation processor on INSERT events)
- [ ] Implement vector similarity neighbor finding (cross-table)
- [ ] Implement explicit reference detection (text matching)
- [ ] Schedule connection decay pg_cron job (daily)
- [ ] Implement connection renewal on repeated evidence
- [ ] Verify: Insert a new company, confirm connections form to related thesis threads
- [ ] Verify: After 30 days with no reinforcement, connection strength decays
- [ ] Verify: Repeated evidence on same connection strengthens it

**Dependency:** Requires IRGI Phase A embeddings to be populated on all tables. Currently: content_digests and thesis_threads have embeddings. actions_queue and companies may need backfill.

### Phase 4: Preference Learning (S, 1-3 hours)

**Goal:** Action outcomes feed back into scoring.

- [ ] Create `preference_weight_adjustments` table
- [ ] Create `cir_recalculate_preference_weights()` function
- [ ] Schedule pg_cron job (every 6 hours)
- [ ] Modify `compute_user_priority_score()` to read from preference_weight_adjustments
- [ ] Verify: Rate 5 "Research" actions as "Dismiss" -> Research type gets negative adjustment
- [ ] Verify: Rate 3 "Portfolio Check-in" actions as "Gold" -> Portfolio type gets positive adjustment
- [ ] Verify: Adjustment applies to new action scoring

**Dependency:** Requires action outcome data. Currently the `action_outcomes` table exists but the WebFront outcome rating UI (P0-4 in next-iterations-plan) is not yet built. Preference learning activates when the first outcomes arrive.

### Phase 5: Observability and Tuning (S, 1-3 hours)

**Goal:** CIR is observable and tunable.

- [ ] Add propagation stats to `cir_state` (updated by processor)
- [ ] Create a CIR health check function (for Orchestrator or State MCP)
- [ ] Add CIR stats to strategic_assessments (Megamind reads CIR health in daily assessment)
- [ ] Log cleanup pg_cron job
- [ ] Tune thresholds: adjust similarity thresholds, decay rates, significance levels based on first week of operation
- [ ] Document operational runbook (how to disable CIR in emergency, how to replay events)

### Phase 6: WebFront Integration (S, 1-3 hours)

**Goal:** CIR activity is visible on the WebFront.

- [ ] Add Supabase Realtime subscription for `cir_propagation_log` (filter significance >= high)
- [ ] Display recent CIR activity in the Activity Feed on the home dashboard
- [ ] Show entity connection count on company/thesis/person detail pages
- [ ] Show preference weight adjustments on a settings/analytics page (optional)

### Implementation Sequence

```
Phase 1 (foundation)     ─── Phase 2 (mechanical propagation) ─── Phase 5 (observability)
                                       │
                                       ├── Phase 3 (connections) ─── Phase 6 (WebFront)
                                       │
                                       └── Phase 4 (preference learning)
```

**Critical path:** Phase 1 -> Phase 2. Everything else can run in parallel after Phase 2.

**Value delivery:**
- After Phase 1: Change detection is live. You can see what's changing via the queue.
- After Phase 2: The system is alive. Changes propagate incrementally. No more batch re-scoring.
- After Phase 3: Entities automatically find their neighbors. The intelligence graph self-assembles.
- After Phase 4: The system learns from Aakash's decisions. Scoring improves over time.

### Total Effort Estimate

| Phase | Effort | Dependency |
|-------|--------|------------|
| Phase 1: Foundation | S (1-3 hours) | Supabase access |
| Phase 2: Mechanical Propagation | M (3-8 hours) | Phase 1 |
| Phase 3: Entity Connections | M (3-8 hours) | Phase 2 + IRGI embeddings |
| Phase 4: Preference Learning | S (1-3 hours) | Phase 2 + outcome data |
| Phase 5: Observability | S (1-3 hours) | Phase 2 |
| Phase 6: WebFront | S (1-3 hours) | Phase 2 + WebFront Phase 1 |
| **Total** | **M-L (12-26 hours)** | |

---

## Appendix A: Interaction with Existing Infrastructure

### Auto Embeddings Pipeline (No Conflict)

CIR triggers fire AFTER Auto Embeddings triggers (alphabetical ordering). The embedding pipeline is completely independent -- it watches for content changes and generates vectors. CIR watches for ALL changes and propagates intelligence. They share the pgmq extension but use separate queues (`embedding_jobs` vs `change_propagation`).

### Existing change_events Table (Absorbed)

The current `change_events` table (DATA-ARCHITECTURE.md) was designed for the SyncAgent which is disabled. CIR subsumes its function. The `cir_propagation_log` replaces `change_events` with richer metadata. The old table can be dropped once CIR Phase 2 is verified.

### Existing notion_synced Pattern (Unchanged)

CIR does not interfere with the `notion_synced` flag pattern. Agents still write to Postgres first and push to Notion. CIR detects the Postgres write and propagates within Postgres. The Notion sync is a separate concern.

### Megamind Cascade Events (Compatible)

Megamind's cascade re-ranking (designed in megamind-design.md Section 4) is the strategic tier of CIR. When CIR routes a high-significance event to Megamind via `cai_inbox`, the Orchestrator sends it to Megamind, which runs its cascade algorithm and writes to `cascade_events`. CIR detects the cascade_events INSERT but classifies it as `low` significance (no re-propagation), preventing loops.

---

## Appendix B: Failure Modes and Recovery

| Failure Mode | Detection | Recovery |
|-------------|-----------|---------|
| **Trigger fails** | pg_cron monitoring checks queue depth vs expected rate | Re-install trigger. Backfill missed events by scanning updated_at > last_known_good. |
| **pgmq queue grows unbounded** | `SELECT count(*) FROM pgmq.q_change_propagation` exceeds 1000 | Increase batch_size. Check for slow propagation functions. |
| **Propagation function errors** | `cir_propagation_log.errors` counter | Messages retry after visibility timeout (300s). Fix the function. Messages eventually expire. |
| **Megamind inbox flooding** | Throttle counter in `cir_state` | Max 5 strategy_cascade messages/hour. Excess queued in backlog. |
| **Connection table bloat** | `SELECT count(*) FROM entity_connections` exceeds 50K | Increase decay rate. Lower similarity thresholds. Add archival. |
| **Matview refresh lag** | `action_scores` is stale (checked by comparing timestamps) | Force manual refresh: `REFRESH MATERIALIZED VIEW CONCURRENTLY action_scores` |
| **CIR needs emergency disable** | Operational decision | `UPDATE cir_propagation_rules SET enabled = FALSE` disables all rules. No trigger code changes needed. |

---

## Appendix C: CIR Glossary

| Term | Definition |
|------|-----------|
| **CIR** | Continuous Intelligence Refresh -- the system that detects changes and propagates their effects |
| **Change event** | A JSONB message in the pgmq queue representing a detected database change |
| **Significance** | Classification of a change's importance: none/low/medium/high/critical |
| **Mechanical propagation (Tier 1)** | Score recalculation, connection updates, matview refreshes -- done in SQL |
| **Strategic propagation (Tier 2)** | Cascade re-ranking, ROI reassessment -- done by Megamind |
| **Entity connection** | A weighted, decay-able relationship between two entities in the intelligence graph |
| **Preference weight adjustment** | A learned scoring modifier derived from action outcome feedback |
| **Propagation storm** | Uncontrolled chain of change events triggering more change events |
| **Deduplication window** | 60-second window in which multiple changes to the same record merge into one event |
| **Connection decay** | Gradual weakening of entity connections that lack reinforcing evidence |
