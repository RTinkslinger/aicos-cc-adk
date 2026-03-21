# Skill: Strategic Briefing & Narrative Tools

SQL functions and views available for generating strategic briefings, narratives,
and decision support for Aakash. These run in Postgres — call via `psql $DATABASE_URL`.

---

## Convergence Helper

### get_convergence_ratio()

**Signature:** `get_convergence_ratio() RETURNS numeric`
**No arguments.**

Canonical convergence ratio used by ALL functions. Ensures consistent definition:
- **Open:** Proposed, Accepted, In Progress (actions still needing work)
- **Resolved:** Dismissed, Done, expired (actions no longer active)
- **Critical:** Accepted is NOT resolved. It means user accepted but action still needs execution.

```bash
psql $DATABASE_URL -t -A -c "SELECT get_convergence_ratio();"
```

---

## Daily Briefing Pipeline

### generate_strategic_briefing()

**Signature:** `generate_strategic_briefing() RETURNS jsonb`
**No arguments.**

Produces a full JSONB briefing with sections:
- `top_actions` (10 highest-priority actions)
- `thesis_momentum` (all 8 thesis threads with conviction + velocity)
- `portfolio_health` (total companies, green/yellow/red counts, red_companies list)
- `recent_cascades` (cascade events from last 48h)
- `convergence` (current ratio, trend, proposed_remaining count)
- `obligation_alerts` (overdue obligations with person + days)
- `recommendations` (actionable suggestions)

```bash
psql $DATABASE_URL -t -A -c "SELECT generate_strategic_briefing();"
```

### format_strategic_briefing(p_date)

**Signature:** `format_strategic_briefing(p_date date DEFAULT CURRENT_DATE) RETURNS text`

Transforms the raw JSONB briefing into a formatted plain-text memo for Aakash.
v5.0 — Structured as 8 sections with human-readable scores:

1. **NEEDS YOUR ATTENTION** — Red/urgent portfolio companies with runway, follow-on status, key questions
2. **CONTRADICTIONS** — Red + SPR, Red + zero actions, expired runway, silent winners, idle SPR room
3. **DECISIONS** — Top actions needing Aakash's decision. Scores displayed as `/10` (strategic_score * 10)
4. **KEY QUESTIONS NEEDING ACTION** — Portfolio companies with key questions but zero open actions
5. **FOLLOW-ON** — SPR/PR companies with ownership + room to deploy; Token/Zero companies
6. **THESIS** — All thesis threads with bias flags, conviction, open action counts
7. **OBLIGATION FOLLOW-UPS** — Pending obligation-generated actions. Scores displayed as `/10`
8. **PEOPLE** — You-owe / they-owe / coming-up obligations by person

Header includes convergence health indicator: `[HEALTHY/OK/WARN/CRITICAL ratio]`.
Internally calls `generate_strategic_narrative()` 3 times with different focus modes.

```bash
# Today's briefing
psql $DATABASE_URL -t -A -c "SELECT format_strategic_briefing();"

# Specific date
psql $DATABASE_URL -t -A -c "SELECT format_strategic_briefing('2026-03-20');"
```

### latest_briefing()

**Signature:** `latest_briefing() RETURNS TABLE(briefing_date, briefing_text, assessment_jsonb, created_at)`

Retrieves the most recent stored briefing from `briefing_history`. Use when you need
the last briefing without regenerating.

```bash
psql $DATABASE_URL -t -A -c "SELECT briefing_text FROM latest_briefing();"
```

### store_daily_briefing()

**Signature:** `store_daily_briefing() RETURNS void`

Generates and stores briefing to `briefing_history` table. Called by pg_cron daily.
You should NOT call this manually — it runs automatically. But you can query the result:

```bash
psql $DATABASE_URL -c "SELECT briefing_date, created_at FROM briefing_history ORDER BY created_at DESC LIMIT 5;"
```

---

## Strategic Narrative Engine

### generate_strategic_narrative(p_focus)

**Signature:** `generate_strategic_narrative(p_focus text DEFAULT 'portfolio_attention') RETURNS jsonb`

The workhorse behind `format_strategic_briefing()`. Generates focused narrative sections.

**Focus modes:**

| p_focus | Returns | Purpose |
|---------|---------|---------|
| `'portfolio_attention'` | `urgent_attention[]`, `headline_data` | Red companies, runway issues, follow-on decisions |
| `'upcoming_decisions'` | `decision_queue[]`, `investment_decisions[]`, `convergence_projection` | Actions needing Aakash, investment decision pipeline |
| `'network_priorities'` | `obligation_hotspots[]`, `relationship_gaps[]` | People obligations, interaction gaps, priority contacts |

```bash
# Portfolio attention
psql $DATABASE_URL -t -A -c "SELECT generate_strategic_narrative('portfolio_attention');"

# Upcoming decisions
psql $DATABASE_URL -t -A -c "SELECT generate_strategic_narrative('upcoming_decisions');"

# Network priorities
psql $DATABASE_URL -t -A -c "SELECT generate_strategic_narrative('network_priorities');"
```

### narrative_score_explanation(p_action_id)

**Signature:** `narrative_score_explanation(p_action_id bigint) RETURNS jsonb`

Generates a human-readable explanation of WHY an action has its current strategic score.
Breaks down all scoring components with reasoning.

```bash
psql $DATABASE_URL -t -A -c "SELECT narrative_score_explanation(55);"
```

Returns JSONB with component breakdown:
- `eniac_component` (raw score contribution)
- `thesis_component` (momentum contribution)
- `info_marginal_value` (diminishing returns state)
- `portfolio_component` (portfolio exposure)
- `time_component` (freshness/decay)
- `narrative` (plain-text explanation)

---

## Strategic Views (pre-computed, queryable)

### strategic_briefing

Calls `generate_strategic_briefing()`. Use for quick access:

```bash
psql $DATABASE_URL -c "SELECT * FROM strategic_briefing;"
```

### decision_frameworks

All pending Ultra-depth actions with structured decision frameworks:

```bash
psql $DATABASE_URL -c "SELECT * FROM decision_frameworks;"
```

### megamind_convergence

Current convergence health metrics:

```bash
psql $DATABASE_URL -c "SELECT * FROM megamind_convergence;"
```

### strategic_recommendations

Active strategic recommendations:

```bash
psql $DATABASE_URL -c "SELECT * FROM strategic_recommendations;"
```

---

## Decision Support

### generate_decision_framework(p_action_id)

**Signature:** `generate_decision_framework(p_action_id integer) RETURNS jsonb`

For any action (especially Ultra-depth), generates a structured decision framework:
- `pros` — reasons to pursue
- `cons` — reasons to skip/defer
- `key_questions` — what must be answered
- `recommended_next_step` — specific next action
- `thesis_context` — connected thesis state
- `portfolio_context` — portfolio company relevance

```bash
psql $DATABASE_URL -t -A -c "SELECT generate_decision_framework(55);"
```

### detect_opportunities()

**Signature:** `detect_opportunities() RETURNS jsonb`

Cross-cutting opportunity analysis:
- `thesis_clusters` — portfolio companies grouped by thesis
- `cross_thesis_opportunities` — companies at 3+ thesis intersections
- `high_conviction_pipeline` — top actions on Very High/High conviction theses
- `relationship_hotspots` — network people connected to 2+ companies
- `strategic_insights` — synthesized observations

```bash
psql $DATABASE_URL -t -A -c "SELECT detect_opportunities();"
```

---

## When to Use Each Function

| Situation | Function |
|-----------|----------|
| Orchestrator asks for daily assessment | `format_strategic_briefing()` then store result |
| Need raw data for cascade analysis | `generate_strategic_narrative('portfolio_attention')` |
| Explaining a depth grade decision | `narrative_score_explanation(action_id)` |
| Presenting Ultra action to Aakash | `generate_decision_framework(action_id)` |
| Looking for cross-thesis patterns | `detect_opportunities()` |
| Quick convergence check | `SELECT * FROM megamind_convergence;` |
| Finding what needs Aakash's attention | `actions_needing_decision_v2()` |
| Retrieving yesterday's briefing | `SELECT * FROM latest_briefing();` |
