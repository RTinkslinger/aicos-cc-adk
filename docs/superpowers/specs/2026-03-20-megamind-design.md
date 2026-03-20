# Megamind — Strategic Reasoning Agent Design Specification
*Created: 2026-03-20*

Megamind is the strategic reasoning layer of the AI CoS system. It sits between Aakash and the execution agents, translating high-level intent into optimized task delegation and processing completed work back into strategic insight. It manages the diverge/converge cycle: exploring possibility space broadly, then narrowing to what maximizes ROI on Aakash's time.

---

## 1. Architecture Overview

### Where Megamind Sits

```
INTERFACE LAYER
  Aakash (WebFront + CAI)
       |  strategic intent, depth approvals, feedback
       v
STRATEGIC LAYER
  Megamind (this agent)
    - ROI calculation across full action space
    - Depth grading for agent-delegated tasks
    - Cascade re-ranking after agent output
    - Convergence enforcement
       |  decomposed tasks, depth-calibrated prompts
       v
EXECUTION LAYER
  Orchestrator (lifecycle management, routing)
       |  @tool bridge calls
       v
  ENIAC (scoring)  |  Datum (data)  |  Content Agent (pipeline)  |  [Cindy future]
```

### Relationship to Existing Agents

| Agent | Role | Megamind's Relationship |
|-------|------|------------------------|
| **Orchestrator** | Lifecycle manager, heartbeat-driven routing | Megamind receives work from Orchestrator via @tool bridge. Orchestrator treats Megamind like any other specialist agent. |
| **Content Agent** | Content analysis, thesis updates, action proposals | Megamind reviews Content Agent's proposed actions, applies strategic filters, and can trigger follow-up work. |
| **Datum Agent** | Entity ingestion, enrichment, dedup | Megamind can request entity enrichment as part of strategic assessment (e.g., "enrich this company before I can assess ROI"). |
| **ENIAC** | Scoring functions (action scorer, people scorer) | ENIAC produces raw scores. Megamind applies strategic reasoning ON TOP of scores — it can override, reweight, or contextualize ENIAC's output. |

### Key Design Principle: Megamind Does NOT Replace ENIAC

ENIAC is the scoring engine. It applies the 7-factor action scoring model and the 9-factor people scoring model mechanistically. Megamind is the strategic reasoning layer that interprets scores in context:

- ENIAC says: "This action scores 7.2"
- Megamind says: "This action scores 7.2, but it's connected to a thesis thread where we just completed 2-deep research yesterday. Diminishing returns apply. Effective strategic value: 5.1. Meanwhile, this 6.8-scoring action on an under-explored thesis has higher marginal ROI."

ENIAC computes. Megamind reasons.

---

## 2. Core Algorithms

### 2.1 Strategic ROI Calculation

The fundamental optimization function:

```
ROI(action) = expected_impact(action) x relevance_to_priorities(action)
              ─────────────────────────────────────────────────────────
              time_cost(action) x opportunity_cost(action)
```

Where:
- **expected_impact** = f(ENIAC raw score, thesis connection strength, portfolio exposure, information gain)
- **relevance_to_priorities** = f(bucket alignment, active thesis weight, Aakash's current focus window)
- **time_cost** = f(depth level, agent delegation feasibility, execution complexity)
- **opportunity_cost** = f(what Aakash can NOT do while pursuing this, time sensitivity of alternatives)

This produces a **strategic score** distinct from ENIAC's raw action score. ENIAC's score is one input to `expected_impact`.

### 2.2 Strategic Score Components

| Component | Weight | Source | Computation |
|-----------|--------|--------|-------------|
| ENIAC raw score | 0.30 | `actions_queue.relevance_score` | Normalized 0-1 from ENIAC's 0-10 scale |
| Thesis momentum | 0.20 | `strategic_assessments` | Rate of conviction change on connected threads. Fast-moving threads get higher weight. |
| Information marginal value | 0.20 | `depth_grades` + `cascade_events` | Diminishing returns curve. First research on a topic = high value. Fourth = low. |
| Portfolio exposure | 0.15 | Portfolio DB + Companies DB | Actions touching portfolio companies with upcoming decisions (follow-on, BRC) get multiplier |
| Time decay | 0.15 | `actions_queue.created_at` + `time_sensitivity` | Urgent actions that haven't been acted on lose strategic value as windows close |

### 2.3 The Diverge/Converge Lens

Every signal that enters the system COULD spawn infinite follow-up actions. The system naturally diverges. Megamind's core job is controlled convergence.

**Diverge phase** (system-wide, not Megamind-specific):
- Content Agent processes a video -> proposes 3 actions
- Each action, if executed, generates new information -> could spawn more actions
- Datum Agent enriches an entity -> reveals connections -> more potential actions
- Thesis evidence accumulates -> conviction changes -> portfolio implications -> more actions

**Converge phase** (Megamind's domain):
1. **Filter**: Not all proposed actions deserve attention. Apply strategic ROI threshold.
2. **Cluster**: Group related actions by thesis thread / company / person. Evaluate the cluster, not individual items.
3. **Rank**: Within each cluster, apply diminishing returns. The 3rd "research Company X" action in a week has lower marginal value than the 1st.
4. **Cap**: Enforce a hard ceiling on actions-in-flight per thesis thread (default: 5 human + 3 agent).
5. **Resolve**: Track action completion. Every completed action should net-reduce the open action count, not expand it.

### 2.4 Diminishing Returns Model

```
marginal_value(action, context) = base_value x decay_factor^n

where:
  base_value = ENIAC raw score (normalized 0-1)
  n = number of COMPLETED actions on the same thesis/company/person in the last 14 days
  decay_factor = 0.7 (configurable)
```

Example: If 3 "research Composio" actions have already been completed this fortnight:
- 4th action's marginal value = base_value x 0.7^3 = base_value x 0.343

This does NOT penalize the first action on a new topic. It only kicks in after execution begins producing results.

**Exception: Contra signals.** Actions tagged as contra (challenging existing thesis) are EXEMPT from diminishing returns decay. Contra actions maintain full base_value regardless of how many confirming actions have been completed. This prevents the system from creating echo chambers.

---

## 3. Depth Grading Protocol

### 3.1 What Is Depth Grading

When the Content Agent or ENIAC proposes an agent-delegated action (assigned_to = 'Agent'), Megamind decides HOW DEEP to investigate before execution begins. This prevents the system from either over-investing in low-value research or under-investing in high-value opportunities.

### 3.2 Depth Levels

| Level | Label | Time Equivalent | Agent Turns | Budget | Output |
|-------|-------|-----------------|-------------|--------|--------|
| 0 | **Skip** | 0 | 0 | $0 | Action dismissed with reasoning |
| 1 | **Scan** | ~5 min | 5-10 | $0.10 | 1-paragraph summary, key data points, yes/no on further investigation |
| 2 | **Investigate** | ~30 min | 15-25 | $0.50 | Structured report (2-3 pages), evidence assessment, thesis implications, recommended next actions |
| 3 | **Ultra** | ~2 hours | 40-80 | $2.00 | Comprehensive research report, competitive landscape, founder assessment, investment implications, conviction recommendation |

### 3.3 Auto-Grading Algorithm

Megamind auto-assigns depth based on strategic context. Aakash can override.

```
FUNCTION auto_grade_depth(action) -> depth_level:
    score = strategic_roi(action)

    # Hard rules first
    IF action.thesis_connection AND thesis.status == 'Active' AND thesis.conviction IN ('Evolving Fast', 'High'):
        minimum_depth = 2  # Active high-conviction thesis = always investigate

    IF action.type == 'Follow-on Eval':
        minimum_depth = 3  # Follow-on decisions always get ultra

    IF action.type == 'Pipeline Action' AND action.assigned_to == 'Agent':
        RETURN 1  # Pipeline maintenance = scan only

    # Score-based grading
    IF score >= 0.8:
        depth = 3  # Ultra
    ELIF score >= 0.6:
        depth = 2  # Investigate
    ELIF score >= 0.3:
        depth = 1  # Scan
    ELSE:
        depth = 0  # Skip

    RETURN max(depth, minimum_depth)
```

### 3.4 Full Depth Grading Flow

```
1. ACTION PROPOSED
   Content Agent / ENIAC proposes action (assigned_to = 'Agent')
       |
       v
2. MEGAMIND AUTO-GRADES
   Megamind reads action context, calculates strategic ROI, assigns depth level
   Writes to depth_grades table: {action_id, auto_depth, reasoning, strategic_score}
       |
       v
3. SURFACED TO AAKASH (via WebFront Depth Queue)
   Shows: action description, Megamind's reasoning, auto-assigned depth, depth options
   Aakash can: Accept auto-depth | Override depth | Skip entirely
       |
       v
4. DEPTH APPROVED
   If auto-approved (trust level = auto): skip step 3, proceed immediately
   If manual approval required: wait for Aakash's response
       |
       v
5. EXECUTION
   Megamind translates depth into specific task prompts for the executing agent:
   - Scan: "Quick assessment of [topic]. 1 paragraph. Key data points only."
   - Investigate: "Structured research on [topic]. Cover: [specific questions]. 2-3 page report."
   - Ultra: "Comprehensive deep dive on [topic]. Cover: [full brief]. Include competitive landscape,
     founder assessment, investment implications."
   Routes to Content Agent or Datum Agent via Orchestrator
       |
       v
6. RESULTS RECEIVED
   Executing agent returns results
   Megamind processes results -> cascade re-ranking (see Section 4)
       |
       v
7. RESOLUTION
   Results summarized and surfaced to Aakash
   Action marked Done or escalated (if results warrant human judgment)
   Depth grade logged with actual cost for calibration
```

### 3.5 Trust Ramp for Auto-Approval

Depth grading starts with full manual approval (Aakash approves every depth decision). As calibration data accumulates:

| Trust Level | Trigger | Behavior |
|------------|---------|----------|
| **Manual** | Default (0-50 graded actions) | All depth grades shown to Aakash for approval |
| **Semi-auto** | 50+ graded, >80% acceptance rate on auto-grades | Depth 0-1 auto-approved. Depth 2-3 shown. |
| **Auto** | 150+ graded, >90% acceptance rate | All depths auto-approved. Aakash reviews results, not depth decisions. |

Trust level is stored in `strategic_config` and can be manually overridden by Aakash at any time.

---

## 4. Cascade Re-ranking

### 4.1 What Triggers a Cascade

When agent work completes, the new information may change the strategic landscape. A cascade re-ranking evaluates all related actions in light of new information.

**Cascade triggers:**
1. Agent-delegated action completes (depth 1-3 research returns results)
2. Thesis conviction changes (evidence pushes conviction to new level)
3. New thesis thread created (Content Agent identifies genuinely new pattern)
4. High-value contra signal detected (challenges existing thesis)
5. Portfolio event (funding round, competitor move, founder change detected via content)

### 4.2 Cascade Algorithm

```
FUNCTION cascade_rerank(trigger_event) -> CascadeResult:
    """
    Process a trigger event, re-evaluate related actions, and produce
    net-fewer new actions than existing ones.
    """

    # 1. Identify the blast radius
    affected_threads = get_connected_thesis_threads(trigger_event)
    affected_companies = get_connected_companies(trigger_event)
    affected_people = get_connected_people(trigger_event)

    # 2. Gather all open actions in the blast radius
    open_actions = query_actions(
        status IN ('Proposed', 'Accepted'),
        thesis_connection IN affected_threads
        OR company IN affected_companies
        OR person IN affected_people
    )

    # 3. Re-score each action with new context
    rescored = []
    FOR action IN open_actions:
        new_score = strategic_roi(action, extra_context=trigger_event.results)
        old_score = action.strategic_score
        delta = new_score - old_score

        IF abs(delta) > 0.1:  # Only log meaningful changes
            rescored.append({
                action_id: action.id,
                old_score: old_score,
                new_score: new_score,
                delta: delta,
                reasoning: explain_delta(action, trigger_event)
            })

    # 4. Apply convergence filter to any NEW actions generated
    new_actions = generate_new_actions(trigger_event.results)
    filtered_new = convergence_filter(new_actions, open_actions)

    # 5. Identify actions that should be RESOLVED (closed without execution)
    # because the trigger event made them redundant or irrelevant
    resolved = []
    FOR action IN open_actions:
        IF action_is_redundant(action, trigger_event.results):
            resolved.append(action)
            mark_action_resolved(action, reason="Superseded by cascade from {trigger_event.id}")

    # 6. Log cascade event
    log_cascade_event({
        trigger: trigger_event,
        actions_rescored: len(rescored),
        actions_resolved: len(resolved),
        new_actions_generated: len(filtered_new),
        net_action_delta: len(filtered_new) - len(resolved),
        convergence_check: len(filtered_new) <= len(resolved)  # MUST be true
    })

    RETURN CascadeResult(rescored, resolved, filtered_new)
```

### 4.3 Cascade Output to Aakash

After a cascade, Megamind surfaces a structured summary:

```
CASCADE REPORT — Trigger: Ultra research on Composio completed

RESCORED (3 actions changed):
  - "Research Composio competitive landscape" — 7.2 -> 4.1 (already covered by research)
  - "Reach out to Composio CTO" — 6.5 -> 8.3 (research revealed strong thesis fit)
  - "Review Agentic AI thesis evidence" — 5.8 -> 7.0 (new evidence changes conviction picture)

RESOLVED (2 actions closed):
  - "Add Composio to companies DB" — Done by Datum Agent as part of research
  - "Check Composio funding status" — Answered in research output

NEW (1 action generated):
  - "Schedule intro to Composio CEO via [mutual connection]" — Score 8.1
    Reasoning: Ultra research revealed Series B timing aligns with Z47 check size.
    Thesis: Agentic AI Infrastructure (conviction: Evolving Fast -> recommend Medium)

NET: -1 actions (3 entered, 2 resolved, 1 new = net reduction of 1)
CONVERGENCE: PASS
```

---

## 5. CLAUDE.md Draft — Megamind Agent System Prompt

```markdown
# Megamind — AI CoS Strategic Reasoning Agent

You are **Megamind**, the strategic reasoning layer for Aakash Kumar's AI Chief of Staff
system. You are a persistent, autonomous strategist running on a droplet. You receive work
prompts from the Orchestrator Agent. Your purpose: optimize Aakash's time allocation by
applying diverge/converge reasoning across his full action space.

---

## 1. Identity

**Who you work for:** Aakash Kumar — Managing Director at Z47 ($550M fund) AND Managing
Director at DeVC ($60M fund). His time is his scarcest resource. Every hour he spends on a
low-leverage activity is an hour not spent on a high-leverage one.

**Your role:** Strategic Reasoning Specialist. You sit between Aakash's intent and the
system's execution. You decide WHAT is worth doing, HOW DEEP to go, and WHAT CHANGED after
work completes.

**You are NOT an assistant.** You are an autonomous strategist. You reason about ROI,
opportunity cost, diminishing returns, and convergence. You apply judgment, not just
computation.

**You are NOT a scorer.** ENIAC computes raw scores. You interpret scores in strategic
context. You can override, reweight, or contextualize any raw score with reasoning.

**You are persistent.** You maintain full context within your session. You remember what
depth grades you've assigned, what cascades you've processed, what strategic assessments
you've made. Use this to accumulate strategic understanding.

---

## 2. Capabilities

| Tool | Purpose |
|------|---------|
| **Bash** | Shell commands. `psql $DATABASE_URL` for all DB access. |
| **Read** | Read files |
| **Write** | Write files |
| **Edit** | Edit files |
| **Grep** | Search file contents |
| **Glob** | Find files by pattern |
| **Skill** | Load skill markdown files for domain knowledge |

No web tools. No direct content analysis. Megamind reasons over DATA, not raw content.

---

## 3. Database Access

**Method:** Bash + psql with `$DATABASE_URL`. No Python DB modules.

**Schema reference:** Load `skills/data/postgres-schema.md` for base schemas. Load
`skills/data/megamind-schema.md` for strategic tables.

**Tables you read:**

| Table | Purpose |
|-------|---------|
| `actions_queue` | All proposed and open actions |
| `thesis_threads` | Active thesis threads, conviction, evidence |
| `content_digests` | Recent content analysis for context |
| `action_outcomes` | Preference history (accept/reject patterns) |
| `depth_grades` | Your previous depth decisions |
| `cascade_events` | Your previous cascade results |
| `strategic_assessments` | Your strategic assessment history |

**Tables you write:**

| Table | Purpose |
|-------|---------|
| `depth_grades` | Depth grading decisions |
| `cascade_events` | Cascade re-ranking results |
| `strategic_assessments` | Periodic strategic assessments |
| `notifications` | Summaries for Aakash via CAI |
| `actions_queue` | Status updates (resolve, re-score) |

---

## 4. Three Work Types

### Type 1: Depth Grading
When the Orchestrator sends you new agent-delegated actions for grading:

1. Read the action(s) from actions_queue
2. Load thesis thread context for connected threads
3. Load recent depth_grades and cascade_events for diminishing returns context
4. Calculate strategic ROI for each action
5. Assign depth level (0=Skip, 1=Scan, 2=Investigate, 3=Ultra)
6. Write depth_grades record with reasoning
7. If trust level = auto: compose execution prompt, return for Orchestrator to route
8. If trust level = manual/semi-auto: write to WebFront depth queue for Aakash approval

### Type 2: Cascade Processing
When the Orchestrator sends you completed agent work for cascade analysis:

1. Read the completed action and its results
2. Identify blast radius (connected thesis threads, companies, people)
3. Query all open actions in the blast radius
4. Re-score each affected action with new context
5. Apply convergence filter: new actions generated MUST be <= actions resolved
6. Write cascade_events record
7. Write notification with cascade summary for Aakash
8. If any action requires escalation (human judgment needed): flag it

### Type 3: Strategic Assessment
Periodic (triggered by Orchestrator, ~daily) comprehensive assessment:

1. Query full action space: all open actions across all thesis threads
2. Calculate portfolio-level ROI picture
3. Identify: thesis threads gaining/losing momentum, underserved priority buckets,
   concentration risks (too many actions on one thesis), stale actions (open > 14 days)
4. Produce strategic overview for WebFront
5. Write strategic_assessments record
6. Generate specific recommendations (new depth grades, actions to resolve, focus shifts)

---

## 5. The Four Priority Buckets

Every strategic decision maps back to these:

| # | Bucket | Weight | Your Role |
|---|--------|--------|-----------|
| 1 | New Cap Tables | Highest always | Ensure agent work on company discovery gets adequate depth |
| 2 | Deepen Existing Cap Tables | High always | Flag when portfolio companies need attention based on content signals |
| 3 | New Founders/Companies (DeVC) | High always | Grade entity enrichment tasks for pipeline efficiency |
| 4 | Thesis Evolution | Highest when capacity exists | Balance depth of thesis research against diminishing returns |

---

## 6. Convergence Rules (HARD CONSTRAINTS)

1. **Net action count must trend downward.** Every cascade must resolve >= as many actions
   as it generates. Exceptions require explicit reasoning logged to cascade_events.

2. **Cap per thesis thread.** Maximum 5 human actions + 3 agent actions open per thesis
   thread. New actions beyond the cap auto-queue (status = 'Queued') until slots open.

3. **Diminishing returns decay.** Apply 0.7^n decay to marginal value of repeated actions
   on the same entity/thesis in a 14-day window. EXCEPTION: contra signals are exempt.

4. **Depth budget per day.** Maximum daily agent spend on Megamind-graded work: $10.
   Track cumulative depth budgets and throttle when approaching limit.

5. **Staleness resolution.** Actions open > 14 days with no progress automatically
   downgraded by 1 priority level. Actions open > 30 days flagged for resolution.

6. **No infinite loops.** A cascade can trigger at most ONE follow-up cascade. If the
   follow-up cascade would trigger another, it queues for the next strategic assessment
   instead.

---

## 7. Acknowledgment Protocol

Every response MUST end with a structured ACK:

```
ACK: [summary]
- [item 1]: [action taken]
- [item 2]: [action taken]
- Convergence: [PASS/WARN] (net delta: +N/-N)
```

---

## 8. State Tracking

| File | When to Write |
|------|---------------|
| `state/megamind_last_log.txt` | After every prompt |
| `state/megamind_iteration.txt` | Incremented each prompt |

### Session Compaction
When prompt includes "COMPACTION REQUIRED":
1. Read `CHECKPOINT_FORMAT.md`
2. Write checkpoint to `state/megamind_checkpoint.md`
3. End response with: **COMPACT_NOW**

### Session Restart
If `state/megamind_checkpoint.md` exists:
1. Read it, absorb state, delete it
2. Log: `resumed from checkpoint, session #N`

---

## 9. Anti-Patterns (NEVER Do These)

1. **Never analyze raw content.** That is Content Agent's job. You reason over structured data.
2. **Never set thesis conviction directly.** Recommend conviction changes with evidence.
   Content Agent and Aakash manage conviction.
3. **Never execute actions.** You grade, route, and process results. Execution is for
   Content Agent and Datum Agent.
4. **Never generate more actions than you resolve in a cascade.** Convergence is mandatory.
5. **Never skip diminishing returns.** Every repeated action must be decay-adjusted.
6. **Never auto-approve depth 3 (Ultra) until trust level = auto.** Ultra is expensive.
7. **Never import Python DB modules.** Use Bash + psql exclusively.
8. **Never skip the ACK.** Every response must include structured acknowledgment.
9. **Never ignore convergence warnings.** If net action delta is positive, explain why.
10. **Never modify thesis_threads evidence directly.** Write recommendations, not changes.
11. **Never skip state tracking.** Always write megamind_last_log.txt.
12. **Never ignore COMPACTION REQUIRED.** Write checkpoint + COMPACT_NOW immediately.
```

---

## 6. Database Schema

### New Table: depth_grades

Tracks every depth grading decision Megamind makes.

```sql
CREATE TABLE depth_grades (
    id SERIAL PRIMARY KEY,

    -- What action this grades
    action_id INTEGER NOT NULL,
        -- FK to actions_queue.id
    action_text TEXT NOT NULL,
        -- Cached action description for quick reference

    -- The grading decision
    auto_depth INTEGER NOT NULL,
        -- 0=Skip, 1=Scan, 2=Investigate, 3=Ultra
    approved_depth INTEGER,
        -- NULL until approved. Set by WebFront or auto-approval.
    strategic_score REAL NOT NULL,
        -- Megamind's strategic ROI score (0.0-1.0)
    reasoning TEXT NOT NULL,
        -- Why this depth was assigned

    -- Context snapshot (for calibration)
    eniac_raw_score REAL,
        -- ENIAC's raw action score at grading time
    thesis_connections TEXT[],
        -- Connected thesis thread names
    diminishing_returns_n INTEGER DEFAULT 0,
        -- How many similar actions completed in window
    marginal_value REAL,
        -- After diminishing returns: strategic_score x 0.7^n

    -- Execution tracking
    execution_status TEXT NOT NULL DEFAULT 'pending',
        -- pending | approved | executing | completed | skipped
    execution_agent TEXT,
        -- 'content' | 'datum' | NULL
    execution_prompt TEXT,
        -- The depth-calibrated prompt sent to executing agent
    execution_cost_usd REAL,
        -- Actual cost after completion (for budget tracking)

    -- Approval
    approved_by TEXT,
        -- 'auto' | 'webfront' | 'cai'
    approved_at TIMESTAMPTZ,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- For WebFront Depth Queue (pending grades needing approval)
CREATE INDEX idx_depth_grades_pending ON depth_grades(execution_status) WHERE execution_status = 'pending';

-- For budget tracking (daily spend)
CREATE INDEX idx_depth_grades_daily ON depth_grades(created_at) WHERE execution_status = 'completed';

-- For diminishing returns lookups (recent grades by thesis)
CREATE INDEX idx_depth_grades_thesis ON depth_grades USING gin(thesis_connections);
```

### New Table: cascade_events

Tracks every cascade re-ranking Megamind processes.

```sql
CREATE TABLE cascade_events (
    id SERIAL PRIMARY KEY,

    -- What triggered this cascade
    trigger_type TEXT NOT NULL,
        -- 'depth_completed' | 'conviction_change' | 'new_thesis' | 'contra_signal' | 'portfolio_event'
    trigger_source_id INTEGER,
        -- FK to the triggering record (depth_grades.id, thesis_threads.id, etc.)
    trigger_description TEXT NOT NULL,
        -- Human-readable summary of the trigger

    -- Blast radius
    affected_thesis_threads TEXT[],
    affected_companies TEXT[],
    affected_actions_count INTEGER NOT NULL,
        -- How many open actions were in the blast radius

    -- Results
    actions_rescored INTEGER NOT NULL DEFAULT 0,
        -- How many actions had meaningful score changes (delta > 0.1)
    actions_resolved INTEGER NOT NULL DEFAULT 0,
        -- How many actions were closed as redundant/superseded
    actions_generated INTEGER NOT NULL DEFAULT 0,
        -- How many new actions were created
    net_action_delta INTEGER NOT NULL,
        -- actions_generated - actions_resolved (should be <= 0)

    -- Convergence
    convergence_pass BOOLEAN NOT NULL,
        -- TRUE if net_action_delta <= 0
    convergence_exception_reason TEXT,
        -- If convergence_pass = FALSE, why was the exception allowed?

    -- The full cascade report (for WebFront display)
    cascade_report JSONB NOT NULL,
        -- {
        --   rescored: [{action_id, old_score, new_score, delta, reasoning}],
        --   resolved: [{action_id, reason}],
        --   generated: [{action_text, score, reasoning, thesis_connection}],
        --   summary: "human-readable summary"
        -- }

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- For cascade feed on WebFront (recent cascades)
CREATE INDEX idx_cascade_events_recent ON cascade_events(created_at DESC);

-- For convergence monitoring
CREATE INDEX idx_cascade_events_convergence ON cascade_events(convergence_pass) WHERE convergence_pass = FALSE;
```

### New Table: strategic_assessments

Periodic strategic snapshots Megamind produces.

```sql
CREATE TABLE strategic_assessments (
    id SERIAL PRIMARY KEY,

    -- Assessment type
    assessment_type TEXT NOT NULL,
        -- 'daily' | 'post_cascade' | 'on_demand'

    -- Portfolio-level metrics
    total_open_actions INTEGER NOT NULL,
    total_open_human_actions INTEGER NOT NULL,
    total_open_agent_actions INTEGER NOT NULL,
    actions_resolved_since_last INTEGER NOT NULL,
    actions_generated_since_last INTEGER NOT NULL,

    -- Per-bucket analysis
    bucket_distribution JSONB NOT NULL,
        -- {
        --   "New Cap Tables": {open: 5, resolved_7d: 3, coverage: "adequate"},
        --   "Deepen Existing": {open: 8, resolved_7d: 2, coverage: "heavy"},
        --   ...
        -- }

    -- Per-thesis analysis
    thesis_momentum JSONB NOT NULL,
        -- {
        --   "Agentic AI Infrastructure": {
        --     conviction: "Evolving Fast",
        --     open_actions: 4,
        --     evidence_velocity: "high",
        --     assessment: "Well-covered, diminishing returns applying"
        --   },
        --   ...
        -- }

    -- Flags
    stale_actions INTEGER NOT NULL DEFAULT 0,
        -- Actions open > 14 days
    concentration_warnings TEXT[],
        -- Thesis threads with > 5 human actions open
    underserved_buckets TEXT[],
        -- Buckets with no actions resolved in 7 days

    -- Recommendations
    recommendations JSONB NOT NULL,
        -- [{type: "resolve", action_id: 42, reason: "stale"},
        --  {type: "depth_grade", action_id: 55, recommended_depth: 2, reason: "thesis momentum"},
        --  {type: "focus_shift", from: "Thesis A", to: "Thesis B", reason: "diminishing returns"}]

    -- Convergence health
    convergence_trend TEXT NOT NULL,
        -- 'converging' | 'stable' | 'diverging'
    convergence_ratio REAL NOT NULL,
        -- actions_resolved / actions_generated over last 7 days (should be >= 1.0)

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- For WebFront strategic overview (latest assessment)
CREATE INDEX idx_strategic_latest ON strategic_assessments(created_at DESC);
```

### New Table: strategic_config

System-level configuration for Megamind's behavior.

```sql
CREATE TABLE strategic_config (
    key TEXT PRIMARY KEY,
    value JSONB NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Default configuration
INSERT INTO strategic_config (key, value) VALUES
    ('trust_level', '"manual"'),
    ('trust_stats', '{"total_graded": 0, "auto_accepted": 0, "overridden": 0}'),
    ('daily_depth_budget_usd', '10.0'),
    ('diminishing_returns_decay', '0.7'),
    ('diminishing_returns_window_days', '14'),
    ('action_cap_human_per_thesis', '5'),
    ('action_cap_agent_per_thesis', '3'),
    ('staleness_warning_days', '14'),
    ('staleness_resolution_days', '30'),
    ('cascade_chain_limit', '1');
```

### Auto Embeddings

No new embedding columns needed for Megamind's tables. Megamind reasons over structured data, not free text. It reads embeddings from `content_digests` and `thesis_threads` when needed for semantic similarity lookups during cascade blast radius calculation.

---

## 7. WebFront Integration

### 7.1 Megamind Section on WebFront

Megamind gets its own section on digest.wiki, accessible via top-level navigation. Three pages:

#### Page 1: Strategic Overview (`/strategy`)

The strategic dashboard. Shows the current state of Aakash's action space from Megamind's perspective.

```
/strategy

┌──────────────────────────────────────────────────────────────────┐
│  Strategic Overview                            Last updated: 2m ago│
├──────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌─── Convergence Meter ──────────────────────────────────────┐  │
│  │                                                            │  │
│  │  Actions In (7d): 12     Actions Resolved (7d): 15        │  │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━            │  │
│  │  ████████████████████░░░░░░░░░░  Converging (ratio: 1.25) │  │
│  │                                                            │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  ┌─── Bucket Distribution ────────────────────────────────────┐  │
│  │                                                            │  │
│  │  1. New Cap Tables      ████░░░░  3 open  (adequate)      │  │
│  │  2. Deepen Existing     ████████  8 open  (heavy)         │  │
│  │  3. DeVC Collective     ██░░░░░░  1 open  (underserved)   │  │
│  │  4. Thesis Evolution    ██████░░  5 open  (adequate)      │  │
│  │                                                            │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  ┌─── Thesis Momentum ───────────────────────────────────────┐  │
│  │                                                            │  │
│  │  Agentic AI Infra      ▲▲▲  Evolving Fast  4 actions     │  │
│  │  SaaS Death            ▲▲   Evolving       3 actions     │  │
│  │  Cybersecurity         ▲    Medium         2 actions     │  │
│  │  CLAW Stack            ─    Evolving       1 action      │  │
│  │  USTOL/Aviation        ▼    Low            0 actions     │  │
│  │  Healthcare AI         ─    New            0 actions     │  │
│  │                                                            │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  ┌─── Flags ─────────────────────────────────────────────────┐  │
│  │  ⚠ 3 stale actions (>14d)                                │  │
│  │  ⚠ Bucket 3 underserved (no resolutions in 7d)           │  │
│  │  ✓ No concentration warnings                              │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                    │
└──────────────────────────────────────────────────────────────────┘
```

**Data source:** `strategic_assessments` (latest record) + `actions_queue` (live counts) + `thesis_threads` (current state).

**Rendering:** Server Component (dynamic). Reads from Supabase via `@supabase/ssr`.

#### Page 2: Depth Queue (`/strategy/depth`)

Agent tasks awaiting depth grading (or awaiting Aakash's approval of Megamind's auto-grade).

```
/strategy/depth

┌──────────────────────────────────────────────────────────────────┐
│  Depth Queue                                     [2 pending]      │
├──────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌── Research Composio competitive landscape ────────────────┐  │
│  │                                                            │  │
│  │  Source: Content digest "composio-agent-tooling-2026"     │  │
│  │  Thesis: Agentic AI Infrastructure (Evolving Fast)        │  │
│  │  ENIAC score: 7.2  |  Strategic score: 0.74               │  │
│  │                                                            │  │
│  │  Megamind recommends: INVESTIGATE (depth 2)               │  │
│  │  Reasoning: "Active thesis with fast-moving conviction.   │  │
│  │  First research on this company — no diminishing returns. │  │
│  │  Connected to 2 portfolio companies."                      │  │
│  │                                                            │  │
│  │  ┌──────┐ ┌─────────────┐ ┌───────┐ ┌──────┐            │  │
│  │  │ Skip │ │ Scan (d1)   │ │ INV   │ │ Ultra│            │  │
│  │  │      │ │             │ │ (d2)* │ │ (d3) │            │  │
│  │  └──────┘ └─────────────┘ └───────┘ └──────┘            │  │
│  │                                         * recommended     │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  ─── Recently Graded (5) ─────────────────────────────────────── │
│  │  "Review thesis evidence for SaaS Death"  d1  auto  $0.08  │  │
│  │  "Enrich Composio founders"               d1  auto  $0.05  │  │
│  │  "Ultra: Cybersecurity market map"        d3  manual $1.82 │  │
│  └────────────────────────────────────────────────────────────── │
└──────────────────────────────────────────────────────────────────┘
```

**Data source:** `depth_grades` with `execution_status = 'pending'` for the queue. Recent grades for the history.

**Server Actions:**
- `approveDepthGrade(gradeId: number, approvedDepth: number)` — Accept auto-grade or override
- `skipDepthGrade(gradeId: number)` — Skip entirely

**Realtime:** Supabase subscription on `depth_grades` table for live updates when Megamind creates new grades.

#### Page 3: Cascade Feed (`/strategy/cascades`)

What changed after agent work completed.

```
/strategy/cascades

┌──────────────────────────────────────────────────────────────────┐
│  Cascade Feed                                                     │
├──────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌── 2h ago — Ultra research on Composio completed ──────────┐  │
│  │                                                            │  │
│  │  Trigger: depth_completed (depth 3, $1.82)                │  │
│  │  Blast radius: 1 thesis, 2 companies, 6 actions           │  │
│  │                                                            │  │
│  │  RESCORED: 3 actions                                      │  │
│  │    "Research Composio landscape" 7.2 → 4.1 (covered)     │  │
│  │    "Reach out to Composio CTO" 6.5 → 8.3 (thesis fit!)   │  │
│  │    "Review Agentic AI evidence" 5.8 → 7.0 (new evidence) │  │
│  │                                                            │  │
│  │  RESOLVED: 2 actions (redundant)                          │  │
│  │  NEW: 1 action ("Schedule intro to CEO" — 8.1)           │  │
│  │  NET: -1 actions  ✓ CONVERGING                            │  │
│  │                                                            │  │
│  │  [View full cascade report]                                │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  ┌── 1d ago — Thesis conviction change: SaaS Death ──────────┐  │
│  │  ...                                                       │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                    │
└──────────────────────────────────────────────────────────────────┘
```

**Data source:** `cascade_events` ordered by `created_at DESC`.

**Rendering:** Server Component. Each cascade event rendered from `cascade_report` JSONB.

### 7.2 WebFront Phase Integration

Megamind's WebFront pages fit as **Phase 2.5** in the WebFront roadmap:

| Phase | Feature | Dependency |
|-------|---------|------------|
| 1 | Action Triage + Semantic Search | (current) |
| 2 | Thesis Interaction | Phase 1 |
| **2.5** | **Megamind: Strategic Overview + Depth Queue + Cascade Feed** | **Phase 1 (Supabase) + Megamind agent running** |
| 3 | Pipeline Status | Phase 1 |
| 4 | Agent Messaging | Phase 1 |

The pages depend on the same Supabase infrastructure (PostgREST, Server Actions, Realtime) established in Phase 1.

### 7.3 Implementation Notes

- **Mobile-first design.** Depth Queue is the most interactive page — Aakash approves depths on mobile. Large touch targets (44x44px), swipe-friendly cards.
- **Strategic Overview** is a read-heavy page. Server Component with ISR (revalidate every 5 minutes or on-demand when new strategic_assessment is written).
- **Cascade Feed** is append-only. Server Component with Realtime subscription for new cascade events.
- **Convergence Meter** is the signature UI element. A horizontal bar showing actions-in vs actions-resolved over a rolling 7-day window. Visually communicates whether the system is converging (good) or diverging (needs attention).

---

## 8. Interaction Protocols

### 8.1 Orchestrator -> Megamind

The Orchestrator sends three types of prompts to Megamind via `send_to_megamind_agent`:

**Depth grading request:**
```
Grade these agent-delegated actions for depth:
1. [id=55] "Research Composio competitive landscape" — ENIAC score: 7.2, thesis: Agentic AI Infrastructure
2. [id=56] "Enrich Composio founders in network DB" — ENIAC score: 5.5, thesis: none
3. [id=57] "Review SaaS Death thesis evidence" — ENIAC score: 6.8, thesis: SaaS Death
```

**Cascade trigger:**
```
Agent work completed. Process cascade:
- Completed: depth_grade id=12, action_id=55, depth=2 (Investigate)
- Results summary: [structured summary of what Content Agent found]
- Affected thesis: Agentic AI Infrastructure
```

**Strategic assessment request:**
```
Run daily strategic assessment.
```

### 8.2 Megamind -> Orchestrator (via ACK)

Megamind returns structured results in its ACK that the Orchestrator uses for routing:

**After depth grading (with auto-approval):**
```
ACK: Graded 3 actions.
- id=55: depth 2 (Investigate). Route to Content Agent.
  Prompt: "Structured research on Composio competitive landscape. Cover: key competitors,
  market position, recent funding, founder background. 2-3 page report."
- id=56: depth 1 (Scan). Route to Datum Agent.
  Prompt: "Quick enrichment of Composio founders. Key fields only."
- id=57: depth 1 (Scan). Route to Content Agent.
  Prompt: "Quick review of recent evidence for SaaS Death thesis. 1 paragraph summary."
- Convergence: PASS (net delta: 0)
```

**After cascade:**
```
ACK: Cascade processed. Trigger: depth_completed (id=12).
- Rescored: 3 actions
- Resolved: 2 actions
- Generated: 1 new action (id=62, "Schedule intro to Composio CEO", score 8.1)
- Convergence: PASS (net delta: -1)
- Escalated: 1 action (id=62 requires Aakash — meeting/outreach type)
```

### 8.3 Megamind <-> ENIAC

ENIAC (currently: scoring functions in Supabase + `scoring.py` on droplet) provides raw scores. Megamind reads them from `actions_queue.relevance_score` and `actions_queue.scoring_factors`. Megamind does NOT call ENIAC directly — scores are computed at action creation time by the Content Agent.

When ENIAC matures into its own agent, the protocol becomes:
- Megamind requests re-scoring: writes to `cai_inbox` with type `rescore_action`
- ENIAC re-scores and updates `actions_queue`
- Megamind reads updated scores on next cascade pass

### 8.4 Megamind <-> Datum Agent

Megamind can trigger entity enrichment as part of depth grading. When a depth-graded action requires enriched entity data that doesn't exist yet:

1. Megamind notes the dependency in its depth_grade record
2. Megamind's execution prompt to the Orchestrator includes: "Pre-req: enrich [entity] via Datum Agent first"
3. Orchestrator routes to Datum Agent, then Content Agent sequentially

### 8.5 Megamind <-> Content Agent

No direct interaction. All communication flows through the Orchestrator:
- Megamind grades depth -> Orchestrator sends calibrated prompt to Content Agent
- Content Agent completes work -> Orchestrator triggers Megamind cascade
- Megamind cascade results -> Orchestrator routes new/escalated actions

---

## 9. Convergence Guarantees

### 9.1 Mathematical Invariant

For the system to converge, this must hold over any rolling 7-day window:

```
actions_resolved(7d) >= actions_generated(7d)
```

This is the **convergence ratio**. Healthy system: ratio >= 1.0. Warning zone: 0.8-1.0. Critical: < 0.8.

### 9.2 Enforcement Mechanisms

| Mechanism | What It Does | Where Enforced |
|-----------|-------------|----------------|
| **Cascade convergence check** | Every cascade must resolve >= generate | `cascade_events.convergence_pass` |
| **Per-thesis action cap** | Max 5 human + 3 agent actions per thesis | Megamind depth grading + action generation |
| **Diminishing returns** | 0.7^n decay on repeated actions | Megamind strategic ROI calculation |
| **Staleness auto-downgrade** | >14d open -> priority drops. >30d -> flagged for resolution | Strategic assessment (daily) |
| **Daily depth budget** | Max $10/day on Megamind-graded agent work | `depth_grades.execution_cost_usd` cumulative |
| **Cascade chain limit** | Max 1 follow-up cascade per trigger | Megamind cascade processing logic |
| **Convergence meter** | Visual accountability on WebFront | `strategic_assessments.convergence_ratio` |

### 9.3 What Happens When Convergence Fails

If `convergence_ratio` drops below 0.8 for 3 consecutive days:

1. Megamind flags this in strategic assessment as CRITICAL
2. All new depth grades auto-capped at depth 1 (Scan) until ratio recovers
3. Notification pushed to Aakash: "System is diverging. [X] actions generated vs [Y] resolved in 7 days. Review /strategy for details."
4. Megamind's next strategic assessment includes a "convergence recovery plan" — specific actions to resolve, depth grades to skip, thesis threads to pause

### 9.4 Proof of Convergence

The system converges because:
1. **Input is bounded.** Content sources produce finite signals per day (~5-15 content items).
2. **Branching is damped.** Each content item produces 1-3 actions. Each completed action produces 0-1 new actions (constrained by cascade convergence check).
3. **Decay removes stale items.** Actions that sit unacted for 30 days get auto-resolved.
4. **Budget limits depth.** $10/day caps how much agent work can expand the action space.
5. **Human bandwidth is the final constraint.** Aakash can act on ~5-10 actions per day. The system optimizes for WHICH 5-10, not for generating more.

---

## 10. Production Fleet Overview

### The Four Production Agents

```
┌─────────────────────────────────────────────────────────────────┐
│                    LIFECYCLE MANAGER (lifecycle.py)               │
│  Python process that manages all four ClaudeSDKClient sessions   │
│  Heartbeat: 60s                                                  │
├─────────────┬──────────────┬──────────────┬─────────────────────┤
│             │              │              │                     │
│ ORCHESTRATOR│ CONTENT AGENT│  DATUM AGENT │    MEGAMIND         │
│ (coordinator│ (analysis +  │  (entity     │  (strategic         │
│  + routing) │  pipeline)   │   ingestion) │   reasoning)        │
│             │              │              │                     │
│ Model:      │ Model:       │ Model:       │ Model:              │
│ Sonnet 4    │ Sonnet 4     │ Sonnet 4     │ Sonnet 4            │
│ Effort: low │ Effort: high │ Effort: high │ Effort: high        │
│ Thinking: — │ Thinking:10k │ Thinking: 5k │ Thinking: 10k       │
│ Turns: 15   │ Turns: 50    │ Turns: 30    │ Turns: 25           │
│ Budget:$0.50│ Budget:$5.00 │ Budget:$2.00 │ Budget: $3.00       │
│             │              │              │                     │
│ Tools:      │ Tools:       │ Tools:       │ Tools:              │
│ Bash, R/W/E │ Bash, R/W/E  │ Bash, R/W/E  │ Bash, R/W/E         │
│ Glob, Grep  │ Glob, Grep   │ Glob, Grep   │ Glob, Grep          │
│ Bridge x3   │ Agent, Skill │ Skill        │ Skill               │
│             │ Web MCP (all)│ Web MCP      │ (no web tools)      │
│             │              │              │                     │
│ Workspace:  │ Workspace:   │ Workspace:   │ Workspace:          │
│ orchestrator│ content/     │ datum/       │ megamind/           │
└─────────────┴──────────────┴──────────────┴─────────────────────┘
```

### Agent Communication Flow

```
60s heartbeat
    │
    v
ORCHESTRATOR
    │
    ├─ Check cai_inbox for messages
    │   ├─ datum_* types ──────────> DATUM AGENT (entity work)
    │   ├─ content_* types ────────> CONTENT AGENT (analysis work)
    │   ├─ strategy_* types ───────> MEGAMIND (strategic assessment request)
    │   └─ general/research types ─> CONTENT AGENT (default)
    │
    ├─ Check actions_queue for agent-assigned actions needing depth grading
    │   └─ New agent actions ──────> MEGAMIND (depth grading)
    │
    ├─ Check depth_grades for approved grades needing execution
    │   ├─ Route to Content Agent (research, thesis, content tasks)
    │   └─ Route to Datum Agent (entity enrichment tasks)
    │
    ├─ Check for completed agent work needing cascade processing
    │   └─ Completed work ─────────> MEGAMIND (cascade re-ranking)
    │
    └─ Scheduled pipeline check (every 12h)
        └─ Pipeline trigger ───────> CONTENT AGENT
```

### New Bridge Tools (lifecycle.py additions)

```python
@tool(
    "send_to_megamind_agent",
    "Send strategic work to the persistent Megamind Agent for depth grading, cascade "
    "processing, or strategic assessment. Returns immediately — works in background.",
    {"prompt": str},
)
async def send_to_megamind_agent(args: dict[str, Any]) -> dict[str, Any]:
    # Same pattern as send_to_content_agent and send_to_datum_agent
```

### New ClientState Fields

```python
class ClientState:
    content_client: Any = None
    content_needs_restart: bool = False
    content_busy: bool = False

    datum_client: Any = None
    datum_needs_restart: bool = False
    datum_busy: bool = False

    megamind_client: Any = None        # NEW
    megamind_needs_restart: bool = False # NEW
    megamind_busy: bool = False         # NEW
```

### Megamind Agent Options

```python
MEGAMIND_WORKSPACE = AGENTS_ROOT / "megamind"
MEGAMIND_LIVE_LOG = MEGAMIND_WORKSPACE / "live.log"

def build_megamind_options():
    from claude_agent_sdk import ClaudeAgentOptions, HookMatcher, ThinkingConfigEnabled

    megamind_tool_hook = _make_tool_hook(MEGAMIND_LIVE_LOG)

    return ClaudeAgentOptions(
        model=os.environ.get("AGENT_MODEL", "claude-sonnet-4-6"),
        permission_mode="dontAsk",
        allowed_tools=[
            "Bash", "Read", "Write", "Edit", "Grep", "Glob", "Skill",
        ],
        hooks={"PostToolUse": [HookMatcher(hooks=[megamind_tool_hook])]},
        setting_sources=["project"],
        thinking=ThinkingConfigEnabled(type="enabled", budget_tokens=10000),
        effort="high",
        max_turns=25,
        max_budget_usd=3.0,
        cwd=str(MEGAMIND_WORKSPACE),
        env={
            "ANTHROPIC_API_KEY": os.environ.get("ANTHROPIC_API_KEY", ""),
            "DATABASE_URL": os.environ.get("DATABASE_URL", ""),
        },
    )
```

### Budget Rationale

| Parameter | Value | Why |
|-----------|-------|-----|
| `max_budget_usd` | 3.0 | Strategic reasoning is complex but focused. Higher than Datum (2.0) because cascade processing requires reading multiple action/thesis records and reasoning across them. Lower than Content Agent (5.0) because no web fetching or content analysis. |
| `max_turns` | 25 | Depth grading: 5-8 turns (read actions, read context, compute, write). Cascade: 10-15 turns (read trigger, blast radius query, re-score loop, convergence check, write). Strategic assessment: 15-20 turns (full action space scan). |
| `thinking` | 10000 tokens | Strategic reasoning benefits from extended thinking. Cascade processing and ROI computation involve weighing multiple factors simultaneously. Same as Content Agent. |
| `effort` | high | Strategic decisions affect what Aakash spends his time on. Correctness matters more than speed. |

---

## 11. Implementation Plan

### Phase 0: Infrastructure
**Estimated effort:** S (1-3 hours)
**Dependencies:** Supabase access, existing lifecycle.py

- [ ] Run database migrations (depth_grades, cascade_events, strategic_assessments, strategic_config tables)
- [ ] Verify tables created and indexes applied
- [ ] Create `mcp-servers/agents/megamind/` directory structure:
  ```
  megamind/
    CLAUDE.md
    CHECKPOINT_FORMAT.md
    state/
      megamind_session.txt
      megamind_iteration.txt
      megamind_last_log.txt
    live.log
  ```
- [ ] Create `skills/data/megamind-schema.md` (new table schemas + query patterns)

### Phase 1: Core Agent — Depth Grading (MVP)
**Estimated effort:** M (3-8 hours)
**Dependencies:** Phase 0

- [ ] Write `megamind/CLAUDE.md` (full system prompt from Section 5)
- [ ] Modify `lifecycle.py`: add Megamind ClientState, bridge tool, options builder, lifecycle hooks
- [ ] Modify Orchestrator's `HEARTBEAT.md`: add strategy_* inbox routing + agent-action depth grading check
- [ ] Modify Orchestrator's `CLAUDE.md`: add `send_to_megamind_agent` to capabilities
- [ ] Implement depth grading flow: Orchestrator detects new agent actions -> sends to Megamind -> Megamind grades -> writes depth_grades
- [ ] Test: create agent-assigned action in actions_queue, verify Megamind auto-grades it
- [ ] Test: verify depth_grades record written with reasoning and strategic score
- [ ] Manual mode: all grades require WebFront approval (auto-approval OFF)

### Phase 2: Execution Routing
**Estimated effort:** M (3-8 hours)
**Dependencies:** Phase 1

- [ ] Modify Orchestrator HEARTBEAT.md: check depth_grades for approved grades, compose execution prompts, route to Content Agent or Datum Agent
- [ ] Implement depth-to-prompt translation (Scan/Investigate/Ultra -> calibrated prompt text)
- [ ] Track execution_cost_usd after completion
- [ ] Test: approve a depth grade on WebFront, verify Content Agent receives calibrated prompt
- [ ] Test: verify execution cost tracked after completion

### Phase 3: Cascade Processing
**Estimated effort:** L (1-3 sessions)
**Dependencies:** Phase 2

- [ ] Implement cascade trigger detection in Orchestrator HEARTBEAT.md: completed agent work -> send results to Megamind
- [ ] Implement cascade algorithm in Megamind: blast radius, re-score, convergence filter, resolve
- [ ] Implement convergence check and enforcement
- [ ] Write cascade_events records with full cascade_report JSONB
- [ ] Write notifications with cascade summaries
- [ ] Test: complete a depth-graded action, verify cascade fires and re-ranks related actions
- [ ] Test: verify convergence check passes (resolved >= generated)
- [ ] Test: trigger convergence failure, verify throttling activates

### Phase 4: Strategic Assessment
**Estimated effort:** M (3-8 hours)
**Dependencies:** Phase 1 (depth_grades data), Phase 3 (cascade_events data)

- [ ] Implement daily strategic assessment trigger in Orchestrator (24h interval)
- [ ] Implement full action space scan in Megamind
- [ ] Implement bucket distribution, thesis momentum, and convergence trend analysis
- [ ] Write strategic_assessments records
- [ ] Generate stale action warnings and concentration alerts
- [ ] Test: trigger strategic assessment, verify comprehensive output

### Phase 5: WebFront Pages
**Estimated effort:** L (1-3 sessions)
**Dependencies:** Phase 1-4 (data in tables), WebFront Phase 1 (Supabase connection)

- [ ] Create `/strategy` route with Strategic Overview page
- [ ] Create `/strategy/depth` route with Depth Queue page
- [ ] Create `/strategy/cascades` route with Cascade Feed page
- [ ] Server Actions: approveDepthGrade, skipDepthGrade
- [ ] Supabase Realtime subscriptions for depth_grades and cascade_events
- [ ] Convergence Meter component
- [ ] Mobile-first responsive design (44x44 touch targets)
- [ ] Test: grade action via Megamind, verify it appears in Depth Queue
- [ ] Test: approve depth on WebFront, verify execution triggers
- [ ] Test: cascade completes, verify Cascade Feed updates live

### Phase 6: Trust Ramp + Calibration
**Estimated effort:** S (1-3 hours)
**Dependencies:** Phase 5 (WebFront for manual grading), 50+ graded actions

- [ ] Implement trust level tracking (total graded, acceptance rate)
- [ ] Implement semi-auto promotion (depth 0-1 auto-approved after 50 grades)
- [ ] Implement full auto promotion (all depths auto-approved after 150 grades)
- [ ] Aakash-accessible trust level override on /strategy page
- [ ] Test: verify trust level promotion at threshold

### Build Sequence Summary

```
Phase 0 (infra)     ──> Phase 1 (depth grading) ──> Phase 2 (execution routing)
                                                          │
                                                          v
                                                    Phase 3 (cascades) ──> Phase 4 (assessment)
                                                          │
                                                          v
                                                    Phase 5 (WebFront) ──> Phase 6 (trust ramp)
```

**Critical path:** Phase 0 -> Phase 1 -> Phase 2 -> Phase 3. This gives Megamind its core capability: graded depth execution with cascade feedback.

**Value delivery:**
- After Phase 1: Agent actions are depth-graded instead of fire-and-forget
- After Phase 3: Cascade re-ranking prevents action explosion
- After Phase 5: Aakash has strategic visibility into the full action space

---

## 12. Cost Model

### Per-Operation Token Estimates

| Operation | Input Tokens | Output Tokens | Thinking Tokens | Notes |
|-----------|-------------|---------------|-----------------|-------|
| Depth grading (3 actions) | ~4,000 | ~1,500 | ~3,000 | Read actions + thesis context + compute + write |
| Cascade processing | ~6,000 | ~2,500 | ~5,000 | Read trigger + blast radius + re-score loop + write |
| Strategic assessment | ~10,000 | ~4,000 | ~8,000 | Full action space scan + analysis + recommendations |

### Cost Per Operation (Sonnet 4 pricing: $3/M input, $15/M output)

| Operation | Megamind Cost | Notes |
|-----------|--------------|-------|
| Depth grading (batch of 3) | ~$0.04 | Frequent: 2-5 batches/day |
| Cascade processing | ~$0.06 | 1-3 per day |
| Strategic assessment (daily) | ~$0.10 | Once per day |

### Monthly Projection (Megamind Agent Only)

| Scenario | Volume | Cost |
|----------|--------|------|
| Light (5 depth grades/day, 1 cascade/day) | ~180/month | ~$3-5/month |
| Medium (10 grades/day, 3 cascades/day) | ~400/month | ~$6-10/month |
| Heavy (20 grades/day, 5 cascades/day) | ~750/month | ~$12-18/month |

### Total System Cost with Megamind

| Agent | Current Monthly | With Megamind | Change |
|-------|----------------|---------------|--------|
| Orchestrator | ~$2-5 | ~$3-6 | +$1 (more routing) |
| Content Agent | ~$15-30 | ~$15-30 | No change |
| Datum Agent | ~$10-20 | ~$10-20 | No change |
| **Megamind** | — | **~$6-10** | **New** |
| **Depth-graded agent work** | — | **~$5-15** | **New** (depth execution budget) |
| **Total** | ~$27-55 | ~$39-81 | +$11-26 |

**Note:** The depth-graded agent work cost ($5-15/month) is not Megamind itself — it is the ADDITIONAL Content Agent/Datum Agent work that Megamind authorizes via depth grading. This is capped at $10/day ($300/month theoretical max, but realistic usage is well below that).

### ROI Justification

At medium usage (~$8/month for Megamind itself):
- **Prevents action explosion.** Without convergence enforcement, the content pipeline alone generates 3-5 new actions per day unbounded. With Megamind, net action count converges.
- **Optimizes depth investment.** Without depth grading, every agent research task gets the same effort. With Megamind, $2 ultra-deep research goes where it matters most.
- **Saves Aakash's time.** Strategic assessment + cascade summaries replace manual review of 15-20 individual actions. Estimated: 30 minutes/day saved in action triage.

---

## Appendix A: Directory Structure

```
mcp-servers/agents/
  megamind/
    CLAUDE.md                    # Full system prompt (Section 5)
    CHECKPOINT_FORMAT.md         # Compaction checkpoint format
    state/
      megamind_session.txt       # Session counter
      megamind_iteration.txt     # Iteration counter
      megamind_last_log.txt      # Last operation log
      megamind_checkpoint.md     # Checkpoint (if compaction needed)
    live.log                     # Real-time operation log

  skills/
    data/
      postgres-schema.md         # (existing) Base schema reference
      megamind-schema.md         # (new) Strategic tables + query patterns
```

## Appendix B: Inbox Message Types

| Type | Source | Example Content | Routes To |
|------|--------|----------------|-----------|
| `strategy_assessment` | CAI / Orchestrator scheduled | "Run daily strategic assessment" | Megamind |
| `strategy_depth_grade` | Orchestrator (auto-detected) | "Grade these 3 agent actions for depth" | Megamind |
| `strategy_cascade` | Orchestrator (completed work) | "Agent work completed. Process cascade." | Megamind |
| `strategy_override` | CAI | "Set Composio research to Ultra depth" | Megamind |

## Appendix C: Orchestrator HEARTBEAT.md Additions

```markdown
## Step 2.5: Agent Action Depth Grading Check (NEW)

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

If results exist:
1. Compose depth grading prompt with action details
2. Call `send_to_megamind_agent` with the prompt
3. If Megamind is busy: skip, retry next heartbeat

## Step 2.6: Approved Depth Execution Check (NEW)

```bash
psql $DATABASE_URL -t -A -c "
  SELECT dg.id, dg.action_id, dg.approved_depth, dg.execution_prompt, dg.execution_agent
  FROM depth_grades dg
  WHERE dg.execution_status = 'approved'
  ORDER BY dg.created_at
  LIMIT 3"
```

If results exist:
1. For each approved grade, route execution_prompt to the specified agent
2. Update depth_grades SET execution_status = 'executing'

## Step 2.7: Cascade Trigger Check (NEW)

```bash
psql $DATABASE_URL -t -A -c "
  SELECT dg.id, dg.action_id, aq.action, aq.thesis_connection
  FROM depth_grades dg
  JOIN actions_queue aq ON dg.action_id = aq.id
  WHERE dg.execution_status = 'completed'
    AND dg.id NOT IN (SELECT trigger_source_id FROM cascade_events WHERE trigger_type = 'depth_completed')
  LIMIT 1"
```

If result exists:
1. Compose cascade trigger prompt with completed work details
2. Call `send_to_megamind_agent` with the prompt
3. Update depth_grades SET execution_status = 'cascaded' (or similar marker)
```

## Appendix D: Relationship to ENIAC APM Brief

The ENIAC APM brief (docs/product/eniac-apm-brief.md) describes the "Action Strategist (TBD)" as a planned agent that "prioritizes and manages the action queue across all sources." Megamind IS the Action Strategist, evolved:

| ENIAC Brief Concept | Megamind Implementation |
|---------------------|------------------------|
| Prioritizes action queue | Strategic ROI calculation + re-ranking |
| Manages across all sources | Cascade processing spans all agents' output |
| (not specified) | Depth grading — how deep to investigate |
| (not specified) | Convergence enforcement — prevents explosion |
| (not specified) | Trust ramp — earns autonomy over time |

Megamind fulfills the Action Strategist role while adding depth grading and convergence — capabilities not anticipated in the original APM brief but essential for a system with autonomous agent execution.
