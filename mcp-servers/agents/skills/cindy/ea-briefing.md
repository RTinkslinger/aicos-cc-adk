# EA Briefing — Cindy Agent Skill

## Purpose

This skill teaches Cindy how to generate daily briefings, outreach priorities,
relationship health reports, and deal velocity intelligence. These are Cindy's
"executive assistant" outputs — the synthesized intelligence products that surface
through notifications and the WebFront dashboard.

---

## Available SQL Functions

### 1. `cindy_daily_briefing_v3() -> jsonb`

**What it does:** Generates Cindy's daily briefing — the single most important output
Cindy produces each day. Aggregates: overdue obligations, upcoming meetings (next 24h)
with context gaps, stale relationships needing outreach, active deal pipeline status,
recent interaction summary, and pending actions.

**When to use:** Triggered by the Orchestrator at the start of each day (or on demand).
This is the "What's Next?" answer from the comms perspective.

**Usage:**
```bash
psql $DATABASE_URL -t -A -c "SELECT cindy_daily_briefing_v3();" | jq .
```

**Return structure:**
```json
{
  "briefing_date": "2026-03-21",
  "overdue_obligations": {
    "i_owe": [ { "id", "person_name", "description", "days_overdue", "category" } ],
    "they_owe": [ { "id", "person_name", "description", "days_overdue" } ]
  },
  "upcoming_meetings": [
    {
      "title": "Composio Series A Discussion",
      "time": "2026-03-21T10:00:00Z",
      "attendees": ["Rahul Sharma", "Sarah Lee"],
      "context_richness": 0.75,
      "context_gaps": ["whatsapp"],
      "pre_meeting_brief_ready": true,
      "open_actions_with_attendees": 2
    }
  ],
  "outreach_needed": [
    { "person_name", "reason": "No interaction in 21+ days", "relationship_tier", "last_interaction" }
  ],
  "deal_pipeline": [
    { "company", "stage", "last_signal", "velocity": "accelerating|stalling|stalled" }
  ],
  "interaction_summary_24h": {
    "emails_processed": 8,
    "meetings_processed": 3,
    "whatsapp_conversations": 12,
    "actions_created": 5,
    "obligations_detected": 3,
    "obligations_fulfilled": 2,
    "thesis_signals": 1
  },
  "pending_actions": [
    { "action", "priority", "assigned_to", "created_at" }
  ]
}
```

**Downstream:** Write a notification summarizing the key items. The WebFront dashboard
reads this directly from the function output.

---

### 2. `cindy_outreach_priorities() -> jsonb`

**What it does:** Returns a prioritized list of people Aakash should reach out to,
ranked by a composite score of: relationship tier, days since last interaction,
open obligations, deal relevance, and thesis connections.

**When to use:** Part of the daily briefing. Also used when Aakash asks "Who should I
reach out to?" or when building the outreach section of the WebFront.

**Usage:**
```bash
psql $DATABASE_URL -t -A -c "SELECT cindy_outreach_priorities();" | jq .
```

**Return structure:**
```json
{
  "outreach_priorities": [
    {
      "person_id": 42,
      "person_name": "Rahul Sharma",
      "role_title": "CEO, Composio",
      "outreach_score": 8.5,
      "reasons": [
        "Portfolio founder, no interaction in 14 days",
        "Open I_OWE obligation: send term sheet",
        "Active deal: Series A follow-on evaluation"
      ],
      "suggested_surface": "whatsapp",
      "last_interaction": { "source": "email", "date": "2026-03-07", "summary": "..." },
      "open_obligations": 2,
      "thesis_connections": ["Agentic AI Infrastructure"]
    }
  ],
  "total_needing_outreach": 12
}
```

---

### 3. `cindy_relationship_momentum() -> jsonb`

**What it does:** Analyzes relationship health across all tracked people. Identifies
relationships with positive momentum (increasing interaction frequency, warm signals),
negative momentum (declining frequency, unanswered messages), and neutral.

**When to use:** Weekly relationship health report. Also feeds the "cooling relationships"
alert system — when a high-value relationship shows negative momentum for 2+ weeks,
route a `cindy_signal` to Megamind.

**Usage:**
```bash
psql $DATABASE_URL -t -A -c "SELECT cindy_relationship_momentum();" | jq .
```

**Return structure:**
```json
{
  "positive_momentum": [
    { "person_id", "person_name", "interaction_trend": "+3 in 7d vs +1 prior 7d", "surfaces": ["email", "granola"] }
  ],
  "negative_momentum": [
    { "person_id", "person_name", "days_since_last": 21, "prior_frequency": "weekly", "relationship_tier": "portfolio_founder" }
  ],
  "stable": [ { "person_id", "person_name" } ],
  "summary": {
    "total_tracked": 150,
    "positive": 12,
    "negative": 8,
    "stable": 130,
    "high_value_at_risk": 3
  }
}
```

**Alert rule:** If any person with `relationship_tier` in
(portfolio_founder, active_deal, lp) shows negative momentum for 14+ days,
write a `cindy_signal` to `cai_inbox`:
```sql
INSERT INTO cai_inbox (type, content, metadata, processed, created_at)
VALUES ('cindy_signal', 'Relationship cooling: [person] — no interaction in [N] days',
        '{"signal_type": "relationship_cooling", "person_id": 42,
          "days_silent": 21, "relationship_tier": "portfolio_founder"}'::jsonb,
        FALSE, NOW());
```

---

### 4. `cindy_deal_velocity() -> jsonb`

**What it does:** Tracks deal pipeline velocity — how fast deals are moving through
stages based on interaction frequency and signal density. Identifies deals that are
accelerating, stalling, or stalled.

**When to use:** Part of the daily briefing. Critical for the Action Optimizer — deals
with declining velocity might need Aakash's attention.

**Usage:**
```bash
psql $DATABASE_URL -t -A -c "SELECT cindy_deal_velocity();" | jq .
```

**Return structure:**
```json
{
  "deals": [
    {
      "company": "Composio",
      "stage": "Series A evaluation",
      "velocity": "accelerating",
      "velocity_score": 8.2,
      "interactions_7d": 5,
      "interactions_prior_7d": 2,
      "latest_signal": "Term sheet discussion in meeting",
      "key_contacts": ["Rahul Sharma", "Sarah Lee"],
      "thesis_connections": ["Agentic AI Infrastructure"],
      "next_milestone": "IC review"
    }
  ],
  "stalling_alerts": [
    { "company": "OtherCo", "days_since_activity": 12, "last_stage": "Due diligence" }
  ]
}
```

---

### 5. `cindy_autonomous_ea_dashboard() -> jsonb`

**What it does:** Returns the full EA dashboard state — combines daily briefing,
outreach priorities, obligation health, relationship momentum, and deal velocity
into a single payload for the WebFront.

**When to use:** When the WebFront `/comms` page loads. This is the "everything at once"
function for the dashboard.

**Usage:**
```bash
psql $DATABASE_URL -t -A -c "SELECT cindy_autonomous_ea_dashboard();" | jq .
```

---

### 6. `cindy_companies_needing_attention(p_limit integer DEFAULT 10) -> jsonb`

**What it does:** Returns companies that need Aakash's attention based on: stale
interactions, open obligations, deal velocity changes, and thesis signal gaps.

**When to use:** Part of the daily briefing and portfolio management workflow.

**Usage:**
```bash
psql $DATABASE_URL -t -A -c "SELECT cindy_companies_needing_attention(5);" | jq .
```

---

## Daily Briefing Workflow

Cindy generates the daily briefing when triggered by the Orchestrator:

```
1. Run cindy_daily_briefing_v3()
   -> Core briefing with overdue obligations, upcoming meetings, pipeline

2. Run obligation_staleness_audit()
   -> Identify obligations needing immediate action

3. Run cindy_outreach_priorities()
   -> Who should Aakash reach out to today?

4. Run cindy_relationship_momentum()
   -> Any high-value relationships cooling?

5. Run cindy_deal_velocity()
   -> Any deals stalling that need attention?

6. Synthesize (LLM reasoning):
   - What are the top 3 things Aakash should do RIGHT NOW?
   - What relationships are at risk?
   - What deals need acceleration?
   - What obligations are overdue?

7. Write notification:
   INSERT INTO notifications (source, type, content, metadata, created_at)
   VALUES ('Cindy', 'daily_briefing', $summary_text, $full_briefing_json, NOW());

8. ACK with briefing summary
```

---

## Anti-Patterns

- Never generate a briefing without running obligation_staleness_audit first.
  Overdue obligations are the highest-priority briefing items.
- Never suppress negative signals (cooling relationships, stalling deals).
  Aakash needs to see problems, not just wins.
- Never include low-priority people in outreach priorities. The function already
  filters by relationship tier, but double-check in LLM reasoning.
- Never write the full briefing JSON into notification content. Write a concise
  summary (3-5 bullet points) with the full JSON in metadata.
