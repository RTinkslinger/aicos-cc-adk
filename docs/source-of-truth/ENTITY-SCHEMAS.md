# Entity Schemas & Patterns
*Last Updated: 2026-03-17*

Vision-state entity schemas and reusable patterns for the AI CoS system. These represent the target data model — not all fields exist today. See DATA-ARCHITECTURE.md for current implemented schemas.

---

## Entity Schemas

### Person (canonical)

```
Core:           name, aliases[], email[], phone[], linkedin_url
Classification: archetype (13 types), role, company_id (-> Company)
Relationship:   temperature_score, owe_ledger[], owed_ledger[],
                last_interaction_date, interaction_frequency,
                relationship_strength_score
IDS:            ids_notation (+, ++, ?, ??, +?, -)  // per-context
Resolution:     canonical_id, source_ids[], confidence_score,
                last_resolved_at, resolution_method
Sovereignty:    human_fields (name, archetype, temperature),
                agent_fields (confidence, frequency, strength_score)
```

### Company (canonical)

```
Core:           name, aliases[], domain, sector, stage
Thesis:         thesis_thread_ids[], conviction_context
Pipeline:       pipeline_stage, bucket (4 priority buckets)
Resolution:     canonical_id, source_ids[], confidence_score,
                last_resolved_at
IDS:            ids_trail[] // conviction trajectory over time
Sovereignty:    human_fields (name, stage, bucket),
                agent_fields (aliases, confidence, ids_trail)
```

### Action (canonical)

```
Core:           description, action_type, source_runner
Scoring:        score (7-factor), factor_breakdown{},
                classification (surface/low_confidence/context_only)
Lifecycle:      status (Proposed -> Accepted -> In Progress -> Done -> Dismissed),
                proposed_at, decided_at, completed_at
Learning:       outcome_rating, preference_snapshot{},
                was_prediction_correct
Links:          person_id, company_id, thesis_thread_id
```

### Thesis Thread (canonical)

```
Core:           thread_name, core_thesis, conviction_level (6 levels)
Evidence:       evidence_entries[] (text, direction, source, date)
Questions:      key_questions[] (text, status: OPEN/ANSWERED)
Links:          company_ids[], person_ids[], content_digest_ids[]
IDS:            conviction_trajectory[] // over time
Sovereignty:    human_fields (status: Active/Exploring/Parked/Archived),
                agent_fields (conviction, evidence, questions)
```

### Owe/Owed Ledger Entry

```
person_id:      -> Person
direction:      "owe" | "owed"  // I owe them | they owe me
description:    text
source:         meeting_id | manual | email_id
created_at:     timestamp
resolved_at:    timestamp | null
status:         open | resolved | expired
```

---

## IDS Trail — Conviction Trajectory

Structured per-entity IDS signal history over time. Captures how conviction about a company, thesis, or person has evolved.

**Current state:** thesis_threads has evidence_entries (text blobs appended over time) but no structured conviction trajectory.

**Schema:**

```
ids_trail_entry:
    entity_type:  "company" | "thesis" | "person"
    entity_id:    canonical_id
    notation:     "+", "++", "?", "??", "+?", "-"
    context_type: one of 7 IDS context types
    signal_source: runner_id | "manual"
    timestamp:    when the signal was observed
    evidence:     brief text
```

**This enables:**
- "Show me the conviction trajectory for Company X over the last 3 months"
- "Which thesis threads have had the most positive signal momentum?"
- "Which companies have gone from ? to ++ in the last month?"

**Implementation:** JSONB column on thesis_threads and companies tables at +. Separate table at ++ if query patterns demand it.

---

## Runner Pattern

Every runner follows this contract:

```
+-------------------------------------------+
|              RUNNER                        |
|                                            |
|  Input:   Signal(s) from source            |
|  Context: Assembled via psql + skills       |
|  Logic:   Domain-specific analysis         |
|  Output:  Actions + Entity updates         |
|                                            |
|  Reads:   Postgres (preferences, thesis,   |
|           entity context) via psql         |
|                                            |
|  Writes:  Actions Queue (scored)           |
|           Thesis updates (evidence)        |
|           Entity updates (new data)        |
|           Content records (if applicable)  |
|                                            |
|  Runtime: Persistent ClaudeSDKClient       |
|  Trust:   Starts at Suggest, earns up      |
|  Logs:    Structured output for audit      |
+-------------------------------------------+
```

**To create a new runner:**
1. Define the signal source it consumes (following Signal Source Pattern from CAPABILITY-MAP.md cap. 4)
2. Define the entity types it touches
3. Define the actions it can propose
4. Implement using ContentAgent as the reference implementation
5. Start at Suggest trust level — human approves all actions
6. Graduate trust level based on accuracy rate over N actions

**Content Agent as reference implementation:**

```
Signal:     YouTube videos from playlist / subscriptions
Extractor:  yt-dlp + youtube-transcript-api -> JSON
Resolver:   Company/person matching in transcript content
Analyzer:   Persistent ClaudeSDKClient with CLAUDE.md + skills
Output:     Content Digest record, thesis evidence, proposed actions
Writer:     Postgres (content_digests, actions_queue) + Notion + digest.wiki
Runtime:    Persistent session managed by lifecycle.py
Trust:      Auto-act for thesis evidence, Suggest for new thesis threads
```

---

## Data Sovereignty — 3-Actor Model

Extends the field-level ownership rules in DATA-ARCHITECTURE.md with the full actor model.

```
Actor 1: Human (Aakash)
    Surfaces: Notion, Attio (future), mobile
    Owns: name, status, archetype, temperature_score,
          owe/owed entries (manual), pipeline stage, bucket assignment

Actor 2: Agent Layer (Runners, MCP tools)
    Surfaces: Postgres, MCP server
    Owns: confidence_score, ids_trail, interaction_frequency,
          relationship_strength, last_resolved_at, evidence_entries,
          scoring factor breakdowns, aliases

Actor 3: CRM Layer (Notion now, Attio later)
    Role: Shared surface -- both human and agent write here
    Rules: Human fields take precedence on conflict.
           Agent writes to agent-owned fields only.
           Write-ahead pattern: Postgres first, push to Notion.
```

**For every new field added to any entity schema, declare:**
1. Which actor owns it
2. Which surfaces it appears on
3. What happens on conflict
