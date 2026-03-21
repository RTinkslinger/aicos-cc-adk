# Person Intelligence — Cindy Agent Skill

## Purpose

This skill teaches Cindy how to use the SQL person intelligence functions to build
deep profiles of individuals, draft contextual nudge messages, analyze communication
preferences, and resolve people across surfaces. These are Cindy's "know the person"
capabilities.

---

## Available SQL Functions

### 1. `cindy_person_intelligence(p_person_id integer) -> jsonb`

**What it does:** Returns a comprehensive intelligence profile for a single person.
Aggregates: network record, interaction history, obligations (active + fulfilled),
thesis connections, deal involvement, communication patterns, and relationship signals.

**When to use:** Pre-meeting context assembly (the core data source for per-attendee
briefs). When Aakash asks "Tell me about [person]." When Megamind needs person context
for strategic reasoning.

**Usage:**
```bash
psql $DATABASE_URL -t -A -c "SELECT cindy_person_intelligence(42);" | jq .
```

**Return structure:**
```json
{
  "person": {
    "id": 42,
    "person_name": "Rahul Sharma",
    "role_title": "CEO, Composio",
    "email": "rahul@composio.dev",
    "phone": "+91...",
    "archetype": "founder",
    "linkedin": "https://linkedin.com/in/...",
    "notion_id": "..."
  },
  "interaction_summary": {
    "total": 23,
    "by_surface": { "email": 12, "granola": 5, "whatsapp": 6 },
    "first_interaction": "2025-11-15",
    "last_interaction": "2026-03-20",
    "interaction_frequency": "weekly",
    "engagement_trend": "increasing"
  },
  "obligations": {
    "i_owe_active": [ { "id", "description", "category", "due_date", "days_overdue" } ],
    "they_owe_active": [ { "id", "description", "category", "due_date" } ],
    "fulfillment_rate": { "i_owe": 0.85, "they_owe": 0.72 }
  },
  "deal_context": {
    "company": "Composio",
    "stage": "Series A evaluation",
    "thesis_connections": ["Agentic AI Infrastructure"],
    "conviction": "Evolving Fast"
  },
  "communication_profile": {
    "preferred_surface": "email",
    "preferred_times": [10, 14],
    "response_latency_hours": 4.2,
    "initiative_ratio": 0.6
  },
  "recent_interactions": [
    { "id": 123, "source": "email", "summary": "...", "timestamp": "2026-03-20" }
  ],
  "relationship_signals": {
    "warmth": "high",
    "last_positive_signal": "2026-03-18",
    "risk_flags": []
  }
}
```

---

### 2. `person_communication_profile(p_person_id integer) -> jsonb`

**What it does:** Focused view of a person's communication patterns — surface preferences,
response times, active hours, message length patterns, and topic affinity. This is a
subset of person_intelligence focused specifically on HOW this person communicates.

**When to use:** When drafting nudge messages (know the right surface and tone). When
detecting communication anomalies (suddenly stopped responding on their preferred surface).

**Usage:**
```bash
psql $DATABASE_URL -t -A -c "SELECT person_communication_profile(42);" | jq .
```

**Return structure:**
```json
{
  "person_id": 42,
  "person_name": "Rahul Sharma",
  "preferred_surface": "email",
  "surface_history": {
    "email": { "count": 12, "avg_response_hours": 4.2, "last_used": "2026-03-20" },
    "whatsapp": { "count": 6, "avg_response_hours": 1.5, "last_used": "2026-03-19" },
    "granola": { "count": 5, "last_used": "2026-03-18" }
  },
  "active_hours": [9, 10, 11, 14, 15, 16],
  "timezone_guess": "IST",
  "response_pattern": "fast_responder|normal|slow_responder|variable",
  "initiative_balance": {
    "they_initiate_pct": 60,
    "aakash_initiates_pct": 40
  }
}
```

---

### 3. `cindy_draft_nudge_message(p_obligation_id integer) -> jsonb`

**What it does:** Generates a draft nudge message for an obligation. Takes into account
the obligation type, the person's communication profile, the relationship tier, and
the context of the original interaction. Returns a draft message with suggested surface.

**When to use:** After obligation triage identifies an obligation that needs a nudge.
Cindy drafts the message; Aakash sends it (Cindy is an observer, not an actor).

**Usage:**
```bash
psql $DATABASE_URL -t -A -c "SELECT cindy_draft_nudge_message(42);" | jq .
```

**Return structure:**
```json
{
  "obligation_id": 42,
  "person_name": "Rahul Sharma",
  "obligation_type": "I_OWE_THEM",
  "obligation_description": "Send updated term sheet",
  "suggested_surface": "email",
  "draft_message": "Hi Rahul, Following up on our discussion — I wanted to send over the updated term sheet. [Attach term sheet]. Let me know if you have questions.",
  "tone": "professional_warm",
  "reasoning": "Email preferred for document sharing. Person responds within 4h on email."
}
```

**Important:** Cindy NEVER sends messages. The draft goes into a notification:
```sql
INSERT INTO notifications (source, type, content, metadata, created_at)
VALUES ('Cindy', 'nudge_draft',
        'Draft nudge for Rahul Sharma: Send updated term sheet (via email)',
        $draft_json, NOW());
```

---

### 4. `cindy_resolution_gaps() -> jsonb`

**What it does:** Identifies people in the network table who have incomplete cross-surface
identity resolution. Example: person has email but no phone, or phone but no email.
These gaps prevent Cindy from linking interactions across surfaces.

**When to use:** Periodically (weekly) to identify resolution gaps that Datum Agent
should fill. Also after processing a batch that introduced new people.

**Usage:**
```bash
psql $DATABASE_URL -t -A -c "SELECT cindy_resolution_gaps();" | jq .
```

**Return structure:**
```json
{
  "gaps": [
    {
      "person_id": 42,
      "person_name": "Rahul Sharma",
      "has_email": true,
      "has_phone": false,
      "has_linkedin": false,
      "surfaces_seen_on": ["email", "granola"],
      "surfaces_missing": ["whatsapp"],
      "enrichment_priority": "high"
    }
  ],
  "total_gaps": 25,
  "high_priority_gaps": 8
}
```

---

### 5. `cindy_resolve_with_company_context() -> jsonb`

**What it does:** Uses company context to resolve ambiguous person matches. When a name
matches multiple network records, this function narrows by checking which companies are
in active deal flow or recent interactions.

**When to use:** During people resolution (Tier 5 of the resolution algorithm). When
name-only matching returns multiple candidates.

**Usage:**
```bash
psql $DATABASE_URL -t -A -c "SELECT cindy_resolve_with_company_context();" | jq .
```

---

### 6. `cindy_cross_link_people_interactions() -> jsonb`

**What it does:** Finds interactions where people were participants but were not linked
via people_interactions records. Creates the missing links. This is a repair function
for gaps in the people-interaction graph.

**When to use:** After detecting data quality issues or as a periodic maintenance task.

**Usage:**
```bash
psql $DATABASE_URL -t -A -c "SELECT cindy_cross_link_people_interactions();" | jq .
```

---

### 7. `cindy_network_creation_suggestions() -> jsonb`

**What it does:** Identifies people who appear in interactions but have no network record.
These are candidates for Datum Agent to create. Returns the person's identifiers and
the interactions they appeared in.

**When to use:** After processing batches with new participants. Feed suggestions into
`datum_person` inbox messages.

**Usage:**
```bash
psql $DATABASE_URL -t -A -c "SELECT cindy_network_creation_suggestions();" | jq .
```

---

## Person Intelligence Workflow

### Pre-Meeting Context Assembly (enhanced)

When assembling context for an upcoming meeting:

```
For each attendee:
  1. Resolve person_id via email (Calendar provides emails)
  2. Run cindy_person_intelligence(person_id)
     -> Full profile: interactions, obligations, deals, relationship
  3. Run person_communication_profile(person_id)
     -> How this person communicates, preferred times, response patterns
  4. Check for open obligations with this person
     -> "You owe Rahul: send term sheet (3 days overdue)"
  5. Synthesize (LLM reasoning):
     -> What should Aakash know before this meeting?
     -> What are the open loops?
     -> What thesis questions could this meeting answer?
  6. Store context_assembly JSON on the calendar interaction record
```

### Nudge Message Workflow

After obligation triage identifies obligations needing nudges:

```
1. For each obligation marked for nudge:
   a. cindy_draft_nudge_message(obligation_id)
      -> Get draft with suggested surface and tone
   b. Reason (LLM): Is this draft appropriate? Adjust tone/content?
   c. Write notification with the draft for Aakash

2. Never send messages directly. Always draft + notify.
```

### Resolution Gap Filling

Weekly maintenance task:

```
1. Run cindy_resolution_gaps()
   -> Find people with incomplete cross-surface identity
2. Run cindy_network_creation_suggestions()
   -> Find interaction participants without network records
3. For each gap/suggestion:
   Write datum_person to cai_inbox for Datum Agent
4. Run cindy_cross_link_people_interactions()
   -> Repair missing people-interaction links
```

---

## Anti-Patterns

- Never call cindy_person_intelligence for every person in a batch. Use it only for
  high-priority people (meeting attendees, obligation counterparties, deal contacts).
- Never send nudge messages directly. Cindy is an observer.
- Never create network records directly. Route all new people through Datum Agent.
- Never skip resolution gap checks after processing batches with new participants.
- Never use person_communication_profile to guess whether someone is ignoring Aakash.
  Declining response rates have many explanations. Flag the pattern, don't interpret.
