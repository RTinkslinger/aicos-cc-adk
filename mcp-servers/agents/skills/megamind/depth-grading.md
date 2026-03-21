# Skill: Depth Grading

Domain knowledge for Megamind's depth grading protocol — calibrating how deep to investigate
agent-delegated actions.

---

## The 4 Depth Levels

| Level | Label | Agent Turns | Budget | What Gets Produced |
|-------|-------|-------------|--------|--------------------|
| 0 | **Skip** | 0 | $0.00 | Action dismissed with reasoning. No agent work. |
| 1 | **Scan** | 5-10 | ~$0.10 | 1-paragraph summary. Key data points. Yes/no on further investigation. |
| 2 | **Investigate** | 15-25 | ~$0.50 | 2-3 page structured report. Evidence assessment. Thesis implications. Recommended next actions. |
| 3 | **Ultra** | 40-80 | ~$2.00 | Comprehensive research report. Competitive landscape. Founder assessment. Investment implications. Conviction recommendation. |

---

## Auto-Grading Algorithm

Megamind auto-assigns depth based on strategic context. Aakash can override.

### Step 1: Check Hard Rules

These override score-based grading:

```
IF thesis.status == 'Active' AND thesis.conviction IN ('Evolving Fast', 'High'):
    minimum_depth = 2  # Active high-conviction thesis = always investigate

IF action.type == 'Follow-on Eval':
    minimum_depth = 3  # Follow-on decisions always get ultra

IF action.type == 'Pipeline Action' AND action.assigned_to == 'Agent':
    RETURN depth = 1  # Pipeline maintenance = scan only
```

Query for thesis context:
```sql
SELECT name, conviction, status
FROM thesis_threads
WHERE thread_name = ANY(string_to_array($thesis_connection, '|'))
  AND status IN ('Active', 'Exploring');
```

### Step 2: Compute Strategic Score

Use the 5-component strategic ROI formula from `strategic-reasoning.md`:
1. ENIAC raw score (0.30 weight)
2. Thesis momentum (0.20 weight)
3. Information marginal value with diminishing returns (0.20 weight)
4. Portfolio exposure (0.15 weight)
5. Time decay (0.15 weight)

### Step 3: Score-Based Grading

```
IF strategic_score >= 0.8: depth = 3 (Ultra)
IF strategic_score >= 0.6: depth = 2 (Investigate)
IF strategic_score >= 0.3: depth = 1 (Scan)
IF strategic_score <  0.3: depth = 0 (Skip)
```

### Step 4: Apply Maximum

```
final_depth = max(score_based_depth, minimum_depth)
```

### Step 5: Budget Check

```sql
SELECT COALESCE(SUM(execution_cost_usd), 0) as spent_today
FROM depth_grades
WHERE execution_status = 'completed'
  AND created_at > CURRENT_DATE;
```

- If spent_today > $8.00: cap all new grades at depth 1 (Scan)
- If spent_today > $10.00: cap all new grades at depth 0 (Skip)

### Step 6: Per-Thesis Cap Check

```sql
SELECT assigned_to, COUNT(*) as cnt
FROM actions_queue
WHERE thesis_connection LIKE '%' || $thesis_name || '%'
  AND status IN ('Proposed', 'Accepted', 'In Progress')
GROUP BY assigned_to;
```

- If agent actions >= 3 for this thesis: new agent action queues (status = 'Queued')
- If human actions >= 5 for this thesis: new human action queues

---

## Execution Prompt Templates

### Skip (depth 0)

No execution prompt needed. Instead:
```sql
UPDATE actions_queue SET status = 'Dismissed', updated_at = NOW() WHERE id = $action_id;
```

Write reasoning in depth_grades.reasoning explaining why this was skipped.

### Scan (depth 1)

```
Quick assessment of [TOPIC].

Context: [1-2 sentences of strategic context from Megamind's reasoning]

Deliverable:
- 1 paragraph summary (max 150 words)
- 3-5 key data points
- Yes/No recommendation on further investigation with reasoning

Budget: 5-10 turns, ~$0.10 max.
Do NOT go deep. This is a quick scan to determine if deeper work is warranted.
```

### Investigate (depth 2)

```
Structured research on [TOPIC].

Context: [strategic context including thesis connection, current conviction, key questions]

Cover these specific areas:
1. [Key question 1 from thesis_threads.key_questions]
2. [Key question 2]
3. [Relevant competitive/market context]

Deliverable:
- 2-3 page structured report
- Evidence assessment for connected thesis threads (use IDS notation: ++, +, +?, ?, ??, -)
- Thesis implications (how does this change conviction picture?)
- Recommended next actions (max 2, with score justification)

Budget: 15-25 turns, ~$0.50 max.
Focus on answering the key questions. Do not pad with general background.
```

### Ultra (depth 3)

```
Comprehensive deep dive on [TOPIC].

Context: [full strategic context — thesis connections, portfolio relevance, conviction state,
why this warranted ultra-depth investigation]

Cover ALL of these areas:
1. Company/entity overview and current state
2. Competitive landscape (key competitors, positioning, moats)
3. Founder/team assessment (background, track record, relevant expertise)
4. Market sizing and timing (TAM, growth trajectory, timing thesis)
5. Investment implications for Z47/DeVC
6. Evidence assessment for connected thesis threads
7. Conviction recommendation with supporting evidence
8. Risk factors and contra signals

Deliverable:
- Comprehensive research report (5-10 pages)
- Evidence table with IDS notation
- Conviction recommendation (with current level and recommended level)
- Specific next actions (meetings, deeper research, portfolio implications)

Budget: 40-80 turns, ~$2.00 max.
This is a thorough investigation. Cover all angles. Flag contra signals prominently.
```

---

## Trust Ramp Mechanics

### Current Trust Level

Read from `strategic_config`:
```sql
SELECT value FROM strategic_config WHERE key = 'trust_level';
-- Returns: "manual" | "semi-auto" | "auto"
```

### Behavior by Trust Level

| Trust Level | Depth 0 (Skip) | Depth 1 (Scan) | Depth 2 (Investigate) | Depth 3 (Ultra) |
|-------------|----------------|-----------------|----------------------|------------------|
| **Manual** | Show to Aakash | Show to Aakash | Show to Aakash | Show to Aakash |
| **Semi-auto** | Auto-approve | Auto-approve | Show to Aakash | Show to Aakash |
| **Auto** | Auto-approve | Auto-approve | Auto-approve | Auto-approve |

### How Auto-Approval Works

When trust level permits auto-approval for this depth:
```sql
UPDATE depth_grades SET
  approved_depth = auto_depth,
  approved_by = 'auto',
  approved_at = NOW(),
  execution_status = 'approved',
  updated_at = NOW()
WHERE id = $grade_id;
```

When manual approval required:
- Leave `execution_status = 'pending'`
- Leave `approved_depth = NULL`
- The WebFront Depth Queue page shows pending grades
- Aakash approves/overrides via WebFront Server Action

### Promotion Check (run during strategic assessment)

```sql
SELECT value FROM strategic_config WHERE key = 'trust_stats';
-- Returns: {"total_graded": N, "auto_accepted": N, "overridden": N}
```

```
total = trust_stats.total_graded
acceptance_rate = trust_stats.auto_accepted / total

IF total >= 150 AND acceptance_rate >= 0.90:
    UPDATE strategic_config SET value = '"auto"' WHERE key = 'trust_level';
ELIF total >= 50 AND acceptance_rate >= 0.80:
    UPDATE strategic_config SET value = '"semi-auto"' WHERE key = 'trust_level';
```

---

## Routing Decision

After depth grading, determine which agent executes:

| Action Type | Execution Agent | Reasoning |
|-------------|----------------|-----------|
| Research, thesis evidence, content follow-up | Content Agent (`'content'`) | Content Agent has web tools, analysis skills, publishing |
| Entity enrichment, founder/company data | Datum Agent (`'datum'`) | Datum Agent has entity creation, dedup, web enrichment |
| Competitive landscape, market mapping | Content Agent (`'content'`) | Requires web research and analysis |
| Follow-on evaluation | Content Agent (`'content'`) | Requires comprehensive analysis with thesis context |

Write `execution_agent` to depth_grades so the Orchestrator knows where to route.

---

## Diminishing Returns in Depth Grading

Before grading, always check how many similar actions have been completed recently:

```sql
SELECT COUNT(*) as n
FROM depth_grades
WHERE $thesis_name = ANY(thesis_connections)
  AND execution_status = 'completed'
  AND created_at > NOW() - INTERVAL '14 days';
```

Then compute marginal value:
```
decay = 0.7  -- from strategic_config.diminishing_returns_decay
marginal_value = strategic_score * decay^n
```

Record both `diminishing_returns_n` and `marginal_value` in the depth_grades row.

If marginal_value < 0.3 AND depth > 1: consider downgrading depth.
If marginal_value < 0.15: strongly consider Skip (depth 0) regardless of raw score.

**Exception:** Contra signals are exempt. If the action challenges existing thesis, set n=0
for the marginal value calculation.
