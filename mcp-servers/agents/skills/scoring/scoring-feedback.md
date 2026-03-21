# Skill: Scoring Feedback & Preference Learning

How agents write feedback to influence scoring, how the preference learning system works, and how to participate in the scoring feedback loop.

---

## Agent Feedback System

Agents can influence action scores by writing feedback to the `agent_feedback_store` table. This creates a transparent record of agent reasoning about scores, and optionally adjusts scores when applied.

### Who Can Write Feedback

| Agent | Allowed | Typical Use |
|-------|---------|-------------|
| `megamind` | Yes | Strategic score disagreements, depth-based adjustments |
| `eniac` | Yes | Research quality signals, thesis relevance corrections |
| `datum` | Yes | Data quality flags, entity linkage corrections |
| `cindy` | Yes | Communication urgency signals, obligation pressure |
| `orchestrator` | Yes | Cross-agent consensus, system-level adjustments |

### Writing Feedback

Use the `record_agent_feedback()` function:

```sql
SELECT record_agent_feedback(
  p_action_id := 42,                -- action to provide feedback on
  p_agent_name := 'megamind',       -- your agent identity
  p_feedback_type := 'score_adjustment',  -- type of feedback
  p_feedback_text := 'This portfolio action should score higher because ownership is 4.5% and there is a board meeting in 3 days.',
  p_suggested_score := 8.5,         -- optional: what you think the score should be
  p_context := '{"reason": "board_meeting_imminent", "ownership_pct": 4.5}'::jsonb  -- optional: structured context
);
```

**Returns:**
```json
{
  "feedback_id": 7,
  "action_id": 42,
  "agent": "megamind",
  "type": "score_adjustment",
  "original_score": 7.23,
  "suggested_score": 8.5,
  "status": "recorded"
}
```

### Feedback Types

| Type | Purpose | Suggests Score? | Applied Automatically? |
|------|---------|----------------|----------------------|
| `score_override` | Hard override — "this score is wrong" | YES (required) | Yes, via `apply_agent_score_overrides()` |
| `score_adjustment` | Soft suggestion — "consider adjusting" | YES (optional) | Yes, via `apply_agent_score_overrides()` |
| `reasoning` | Explain why score seems right or wrong | No | No (informational) |
| `flag` | Flag something concerning about the action | No | No (informational) |
| `endorsement` | Confirm the score looks correct | No | No (informational) |
| `context_note` | Add context that might affect future scoring | No | No (informational) |

### When to Write Feedback

**DO write feedback when:**
1. You have information the scoring model doesn't capture (e.g., a meeting that just happened, a deal about to close)
2. The narrative_score_explanation reveals a missing signal (e.g., no portfolio match found but you know the action is portfolio-related)
3. You detect a scoring anomaly (e.g., a P0 portfolio action scoring below 6.0)
4. You have cross-agent context (e.g., Cindy detected an obligation that isn't linked yet)
5. The verb_pattern_multiplier is penalizing a legitimately important action

**DO NOT write feedback when:**
1. The scoring model is working as designed (thesis actions scoring lower is intentional)
2. You don't have concrete evidence for why the score should change
3. You're just disagreeing with the priority hierarchy (portfolio > pipeline > thesis is by design)
4. The action is already dismissed or completed

### Example: Megamind Detects Strategic Importance

```sql
-- 1. Read the scoring context
SELECT agent_scoring_context(42);

-- 2. Notice the strategic_score is 4.0 but Megamind thinks it should be 8.0
-- 3. Write feedback with reasoning
SELECT record_agent_feedback(
  42,
  'megamind',
  'score_adjustment',
  'Strategic score underestimates this action. The company is in a market consolidation phase and this meeting could determine follow-on allocation. Competitor just raised $50M. Board alignment critical.',
  8.2,
  '{"strategic_reasoning": "market_consolidation", "competitor_event": "Series B $50M", "urgency_driver": "follow_on_decision"}'::jsonb
);
```

### Example: Cindy Detects Obligation Urgency

```sql
SELECT record_agent_feedback(
  55,
  'cindy',
  'flag',
  'Detected overdue obligation from email: Aakash promised to send competitive analysis to CEO by last Friday. This action is connected to fulfilling that promise.',
  NULL,
  '{"obligation_type": "i_owe", "days_overdue": 3, "person": "John Smith", "promise": "competitive analysis"}'::jsonb
);
```

### Example: ENIAC Research Quality Signal

```sql
SELECT record_agent_feedback(
  38,
  'eniac',
  'reasoning',
  'This thesis research action has diminishing returns. 4 similar research tasks completed in last 7 days on the same thesis thread. Marginal value of another research pass is low.',
  NULL,
  '{"diminishing_returns_n": 4, "similar_actions_7d": 4, "marginal_value": 0.3}'::jsonb
);
```

---

## Applying Feedback

Feedback is applied via `apply_agent_score_overrides()`:

```sql
SELECT apply_agent_score_overrides();
```

This processes all pending feedback with `feedback_type IN ('score_override', 'score_adjustment')` and `adjustment_applied = false`. It:
1. Validates the suggested score is within bounds
2. Applies a weighted adjustment (agent consensus if multiple agents agree)
3. Sets `adjustment_applied = true` on processed records
4. Returns a summary of changes

**This runs automatically.** Agents just need to write feedback; the system applies it.

---

## Reading Feedback

### For a Specific Action

```sql
SELECT agent_feedback_summary(42);
```

Returns all feedback for action 42, plus overall agent stats.

### All Recent Feedback

```sql
SELECT agent_feedback_summary();  -- NULL action_id = system-wide summary
```

Returns:
```json
{
  "per_action": null,
  "agent_stats": [
    {
      "agent": "megamind",
      "total_feedback": 15,
      "score_overrides": 3,
      "avg_suggested_delta": 1.2,
      "endorsements": 5,
      "flags": 2,
      "last_feedback_at": "2026-03-21T10:30:00Z"
    }
  ],
  "recent_feedback": [ ... last 20 feedback entries ... ]
}
```

### Narrative Includes Feedback

The `narrative_score_explanation()` function automatically includes recent agent feedback in its output:

```
"Agent feedback: megamind says: 'Strategic score underestimates this action...' (suggests 8.2/10)."
```

This means agent feedback naturally flows into the user-facing score explanations.

---

## Preference Learning System

The preference learning system automatically adjusts scoring weights based on user accept/dismiss behavior. It operates across 4 dimensions.

### How It Works

```
User accepts action → update_preference_from_outcome(action_id, 'helpful')
                     → Boosts weight for that action_type, priority, source, thesis

User dismisses action → update_preference_from_outcome(action_id, 'skip')
                       → Penalizes weight for that action_type, priority, source, thesis
```

### The 4 Preference Dimensions

| Dimension | Example Values | What It Learns |
|-----------|---------------|----------------|
| `action_type` | "Portfolio Check-in", "Thesis Research" | Which action types the user values |
| `priority` | "P0 - Now", "P1 - Next" | Whether priority labels match user behavior |
| `source` | "ContentAgent", "Cindy" | Which sources produce valuable actions |
| `thesis` | "AI Infrastructure", "Vertical SaaS" | Which thesis areas get more attention |

### Storage: `preference_weight_adjustments` Table

```sql
CREATE TABLE preference_weight_adjustments (
  id SERIAL PRIMARY KEY,
  dimension TEXT NOT NULL,          -- 'action_type', 'priority', 'source', 'thesis'
  dimension_value TEXT NOT NULL,    -- e.g., 'Portfolio Check-in'
  weight_adjustment NUMERIC DEFAULT 0,  -- running average: positive = boost, negative = penalize
  sample_count INTEGER DEFAULT 0,   -- how many outcomes contributed to this
  last_updated_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(dimension, dimension_value)
);
```

### Weight Calculation

Uses a running weighted average:
```
new_weight = (old_weight * old_count + delta) / (old_count + 1)
```

Where delta depends on outcome:
| Outcome | Delta |
|---------|-------|
| `gold` | +0.3 |
| `helpful` | +0.1 |
| `skip` | -0.2 |

### Impact on Scores

The `preference_mult` in `compute_user_priority_score()` combines action_type and priority preferences:

```
pa = preference_weight_adjustments['action_type'][this_type]
   + preference_weight_adjustments['priority'][this_priority]
preference_mult = 1.0 + clamp(pa * 0.1, -0.1, +0.1)
```

**Capped at +/-10%.** This prevents runaway preference drift.

### Viewing Current Preferences

```sql
SELECT preference_insights();
```

Returns structured view of all learned preferences with:
- Which dimensions have the strongest signals
- Which values are being boosted vs. penalized
- Sample counts (confidence indicator)

### Direct Queries

```sql
-- See all learned preferences
SELECT dimension, dimension_value,
  ROUND(weight_adjustment, 4) as weight,
  sample_count
FROM preference_weight_adjustments
ORDER BY ABS(weight_adjustment) DESC;

-- See which action types the user prefers
SELECT dimension_value as action_type,
  ROUND(weight_adjustment, 4) as preference,
  sample_count
FROM preference_weight_adjustments
WHERE dimension = 'action_type'
ORDER BY weight_adjustment DESC;
```

---

## Verb Pattern Learning

A specialized form of preference learning that operates on action phrasing patterns.

### How It Works

The `action_verb_pattern_multiplier()` function extracts verb patterns from action text (e.g., "Schedule call with...", "Flag risk in...", "Explore opportunity to...") and checks their historical accept/dismiss rates.

**Historically dismissed patterns get penalized:**
- "flag risk" → users typically dismiss these → penalty
- "schedule call with CEO" → users typically accept → boost

### Impact

The verb_pattern multiplier ranges from ~0.75 (strongly penalized patterns) to ~1.10 (strongly preferred patterns). This catches patterns that other multipliers miss — it's about HOW the action is phrased, not what it's about.

### Why This Matters for Agents

When writing actions, phrase them using patterns that match user behavior:
- **Good:** "Schedule check-in with [person] to discuss [topic]"
- **Risky:** "Flag potential risk in [area]" (often dismissed)
- **Risky:** "Explore broad opportunity in [market]" (too vague, often dismissed)

---

## Acceptance Rate Learning

Another behavioral signal: the `acceptance_mult` looks at the overall accept/dismiss rate for each action_type.

```sql
-- Check current acceptance rates
SELECT action_type,
  COUNT(*) FILTER (WHERE status IN ('Accepted','Done','Completed')) as accepted,
  COUNT(*) FILTER (WHERE status IN ('Dismissed','Rejected','Skipped')) as dismissed,
  COUNT(*) as total,
  ROUND(
    (COUNT(*) FILTER (WHERE status IN ('Accepted','Done','Completed'))
     - COUNT(*) FILTER (WHERE status IN ('Dismissed','Rejected','Skipped'))
    )::numeric / COUNT(*), 2
  ) as acceptance_rate
FROM actions_queue
WHERE status NOT IN ('Proposed')
GROUP BY action_type
HAVING COUNT(*) >= 3
ORDER BY acceptance_rate DESC;
```

Needs at least 3 decided actions per type to activate. Adjusts scores by up to +/-8%.

---

## Full Feedback Loop Architecture

```
1. Action created → compute_user_priority_score() → initial score
2. Agents read agent_scoring_context() → reason about score
3. Agents write record_agent_feedback() → feedback recorded
4. apply_agent_score_overrides() → adjustments applied
5. User accepts/dismisses → update_preference_from_outcome()
6. preference_weight_adjustments updated → preference_mult adjusts
7. verb_pattern_multiplier() and acceptance_mult update from behavior
8. Next scoring cycle incorporates all learned signals
```

**The system gets smarter over time.** Every user decision trains it. Every agent observation enriches it.

---

## Guardrails

1. **Combined multiplier cap: [0.4, 1.35]** — No single action can be boosted or penalized more than 35% from base
2. **Preference cap: +/-10%** — Preference learning can't overwhelm the model
3. **Sample count thresholds** — Preference weights need sample_count >= 1 to activate (test 7 checks >= 10 for safety)
4. **Score bounds: 1.0 to ~9.5** — Sigmoid wall prevents runaway scores
5. **Agent name validation** — Only known agents can submit feedback
6. **Feedback type validation** — Only known types accepted
7. **Multiplier bounds: [0.5, 2.0]** — Individual multiplier functions are checked by regression test 15
