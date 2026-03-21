# Interaction Analysis — Cindy Agent Skill

## Purpose

This skill teaches Cindy how to use the SQL interaction analysis functions to understand
communication patterns, extract key question intelligence from interactions, reason
across multiple data sources, and build thread-level conversation intelligence.

---

## Available SQL Functions

### 1. `cindy_interaction_pattern_data(p_person_id integer) -> jsonb`

**What it does:** Analyzes all interactions with a specific person and returns structured
pattern data: frequency by surface, time-of-day patterns, response latency, topic
distribution, engagement trends, and relationship trajectory.

**When to use:** Before pre-meeting context assembly. When reasoning about relationship
health with a specific person. When Megamind asks for interaction intelligence on a deal
contact.

**Usage:**
```bash
psql $DATABASE_URL -t -A -c "SELECT cindy_interaction_pattern_data(42);" | jq .
```

**Return structure:**
```json
{
  "person_id": 42,
  "person_name": "Rahul Sharma",
  "total_interactions": 23,
  "surface_breakdown": {
    "email": { "count": 12, "last": "2026-03-20", "avg_gap_days": 3.5 },
    "granola": { "count": 5, "last": "2026-03-18" },
    "whatsapp": { "count": 6, "last": "2026-03-19" }
  },
  "time_patterns": { "preferred_hours": [10, 14, 16], "preferred_days": ["Tuesday", "Thursday"] },
  "engagement_trend": "increasing|stable|declining",
  "recent_topics": ["Series A", "product demo", "IC timeline"],
  "avg_response_time_hours": 4.2,
  "relationship_signals": { "warmth": "high", "initiative_ratio": 0.6 }
}
```

**Key insight:** `initiative_ratio` > 0.5 means the person initiates more than Aakash.
High initiative + declining engagement = they're losing interest. Flag this.

---

### 2. `cindy_interaction_kq_intelligence() -> jsonb`

**What it does:** Scans recent interactions for content that answers or progresses active
thesis key questions. Cross-references interaction summaries, thesis signals, and deal
signals against the key_questions field of active thesis threads.

**When to use:** After processing a batch of interactions. Surfaces intelligence that
the content pipeline might miss because it comes from conversations, not published content.

**Usage:**
```bash
psql $DATABASE_URL -t -A -c "SELECT cindy_interaction_kq_intelligence();" | jq .
```

**Return structure:**
```json
{
  "matches": [
    {
      "interaction_id": 123,
      "interaction_source": "granola",
      "interaction_summary": "Composio founders discussed Series A terms...",
      "thesis_thread": "Agentic AI Infrastructure",
      "key_question_matched": "What does the competitive landscape look like?",
      "evidence_snippet": "They mentioned 3 direct competitors...",
      "signal_strength": "strong",
      "direction": "confirming"
    }
  ],
  "total_matches": 5,
  "thesis_threads_touched": ["Agentic AI Infrastructure", "API Economy"]
}
```

**Downstream routing:** For each strong match, write a `cindy_signal` to `cai_inbox`
for Megamind routing. This is how conversation intelligence feeds the thesis system.

---

### 3. `cindy_cross_source_reasoning() -> jsonb`

**What it does:** Identifies cross-surface intelligence opportunities — cases where
combining data from multiple surfaces (email + meeting + WhatsApp) reveals patterns
that no single surface shows alone.

**When to use:** During Cindy's daily reasoning cycle. This is the "connect the dots"
function. It finds things like:
- Email thread about deal terms + meeting transcript discussing same deal = deal acceleration signal
- WhatsApp message from portfolio founder + no email reply in 48h = relationship risk
- Calendar meeting with person + no Granola transcript + no email thread = context gap

**Usage:**
```bash
psql $DATABASE_URL -t -A -c "SELECT cindy_cross_source_reasoning();" | jq .
```

**Return structure:**
```json
{
  "cross_source_patterns": [
    {
      "pattern_type": "deal_acceleration|relationship_risk|context_gap|information_asymmetry",
      "surfaces_involved": ["email", "granola"],
      "person_id": 42,
      "person_name": "Rahul Sharma",
      "description": "Deal discussion in email + meeting, no WhatsApp follow-up",
      "recommended_action": "Follow up via WhatsApp to maintain momentum",
      "signal_strength": "moderate"
    }
  ],
  "total_patterns": 3
}
```

---

### 4. `cindy_interaction_threads() -> jsonb`

**What it does:** Groups interactions into conversation threads across surfaces. A single
deal discussion might span email threads, WhatsApp messages, and meeting transcripts.
This function stitches them into unified thread views.

**When to use:** When assembling context for a person or deal. When investigating the
full history of a conversation topic.

**Usage:**
```bash
psql $DATABASE_URL -t -A -c "SELECT cindy_interaction_threads();" | jq .
```

**Return structure:**
```json
{
  "threads": [
    {
      "thread_topic": "Composio Series A",
      "interactions": [
        { "id": 100, "source": "email", "timestamp": "2026-03-15", "summary": "Initial outreach" },
        { "id": 115, "source": "granola", "timestamp": "2026-03-18", "summary": "First meeting" },
        { "id": 120, "source": "email", "timestamp": "2026-03-19", "summary": "Term sheet follow-up" }
      ],
      "people": [42, 55],
      "companies": [15],
      "status": "active",
      "last_activity": "2026-03-19"
    }
  ]
}
```

---

### 5. `cindy_kq_update_proposals() -> jsonb`

**What it does:** Based on recent interactions, proposes updates to thesis key questions.
Some interactions answer existing key questions, others raise new ones. This function
identifies both.

**When to use:** During the thesis signal routing step. Feed proposals into
`cindy_signal` messages for Content Agent / Megamind to act on.

**Usage:**
```bash
psql $DATABASE_URL -t -A -c "SELECT cindy_kq_update_proposals();" | jq .
```

**Return structure:**
```json
{
  "answered_questions": [
    { "thesis_thread": "Agentic AI Infrastructure", "question": "What is the TAM?", "answer_source": "interaction #123", "evidence": "..." }
  ],
  "new_questions_proposed": [
    { "thesis_thread": "Agentic AI Infrastructure", "proposed_question": "How does Composio handle enterprise auth?", "source_interaction": 123 }
  ]
}
```

---

## Interaction Analysis Workflow

When Cindy processes a batch of interactions:

```
1. Standard processing loop (CLAUDE.md Section 3):
   - Query interactions WHERE cindy_processed = FALSE
   - Extract obligations, action items, thesis signals
   - Mark cindy_processed = TRUE

2. Post-batch analysis (run AFTER standard processing):
   a. cindy_interaction_kq_intelligence()
      -> Route strong matches to cai_inbox as cindy_signal
   b. cindy_cross_source_reasoning()
      -> Surface cross-surface patterns as notifications
   c. cindy_kq_update_proposals()
      -> Route proposals to cai_inbox for thesis management
   d. For high-priority people in this batch:
      cindy_interaction_pattern_data(person_id)
      -> Update relationship signals, detect engagement changes
```

---

## Integration with Pre-Meeting Context Assembly

When assembling pre-meeting context (CLAUDE.md Section 9), enhance with:

```
For each attendee:
  1. cindy_interaction_pattern_data(person_id)
     -> Include engagement_trend, initiative_ratio, preferred_hours
  2. cindy_interaction_threads()
     -> Find active threads involving this person
  3. cindy_cross_source_reasoning()
     -> Surface any cross-source patterns with this person
```

---

## Anti-Patterns

- Never skip the post-batch analysis step. It is where cross-surface intelligence emerges.
- Never call cindy_interaction_pattern_data for every person in a batch — only high-priority
  (portfolio founders, active deal contacts, thesis-connected people).
- Never write interaction kq matches directly to thesis_threads. Route via cindy_signal.
- Never ignore declining engagement trends. Flag them as relationship risk signals.
