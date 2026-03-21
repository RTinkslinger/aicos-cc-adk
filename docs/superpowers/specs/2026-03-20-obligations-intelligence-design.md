# Obligations Intelligence — Cindy's Core EA Capability
*Created: 2026-03-20*

Obligations Intelligence is what transforms Cindy from a communications observer into a best-in-class Executive Assistant. It tracks every commitment Aakash makes and every commitment made to him, across all four observation surfaces, and ensures nothing falls through the cracks. This is the system that makes Aakash's professional relationships compound rather than decay.

---

## 1. Architecture Overview

### Where Obligations Sit

```
OBSERVATION LAYER (Cindy processes interactions from 4 surfaces)
  Email, WhatsApp, Granola, Calendar
       | interactions with extracted signals
       v
OBLIGATION DETECTION (Cindy — this spec)
  Scan every interaction for commitment signals
  Create obligation records with type, person, description, due date
  Compute comms priority (staleness, relationship tier, source reliability)
       | obligation records in Postgres
       v
STRATEGIC OVERLAY (Megamind)
  Apply strategic context to obligation priority
  Thesis connections, portfolio health, competitive pressure, ROI
  Override to P0 for time-sensitive strategic opportunities
       | blended priority = 60% Cindy + 40% Megamind
       v
CIR INTEGRATION (Continuous Intelligence Refresh)
  New obligation -> propagation event -> re-rank related actions
  Obligation fulfilled -> update relationship metrics
  Obligation overdue -> escalate priority
       | real-time updates via Supabase triggers
       v
INTERFACE LAYER
  WebFront (/cindy): Obligations Dashboard, Follow-Up Feed, Cindy Insights
  CAI: "You have 3 overdue obligations — Rahul is waiting on your term sheet feedback"
  WhatsApp (future): Proactive push for urgent obligations
```

### Relationship to Existing System Components

| Component | How Obligations Interact |
|-----------|------------------------|
| **Cindy (interactions)** | Every processed interaction is scanned for obligation signals. Obligations reference `interactions.id` as provenance. |
| **Megamind (strategy)** | Receives obligation priority requests from Cindy. Applies strategic overlay. Can override priority to P0. Returns adjusted priority. |
| **ENIAC (scoring)** | Obligation-sourced actions enter `actions_queue` like any other action. ENIAC scores them. Obligations add staleness/urgency metadata that ENIAC can factor in. |
| **Datum Agent (people)** | Obligations link to `network.id`. If an obligation references an unmatched person, normal Datum flow applies. |
| **CIR (propagation)** | New obligations and status changes are CIR events. Overdue obligations trigger propagation to re-rank connected actions. |
| **Actions Queue** | An obligation can spawn an action (e.g., "Follow up with X about Y"). The action references the obligation. Completing the action can fulfill the obligation. |
| **WebFront** | Three new views under `/cindy` for obligation management. |

### Design Principles

1. **Detection over declaration.** Cindy detects obligations from interaction signals. Aakash does not need to manually log commitments. The system infers them from what was said.

2. **Two-sided accountability.** Track both what Aakash owes others AND what others owe him. This dual view is what makes a great EA — knowing both sides of every commitment.

3. **Blended priority.** Cindy knows relationship dynamics (comms priority). Megamind knows strategic context (strategic priority). Neither alone produces the right ranking. The blend does.

4. **Staleness is the killer metric.** An obligation that sits outstanding for 7 days without progress is a relationship risk. Staleness drives urgency more than initial priority.

5. **Obligations are NOT actions.** An obligation is a commitment between two people. An action is a task to fulfill it. One obligation can spawn multiple actions. Fulfilling an action can resolve an obligation, but they are different entities.

---

## 2. Obligations Data Model

### Core Schema

```sql
CREATE TABLE obligations (
    id SERIAL PRIMARY KEY,

    -- Who
    person_id INTEGER NOT NULL,
        -- FK to network.id — the other party in the obligation
    person_name TEXT NOT NULL,
        -- Denormalized for quick display (avoid JOIN on every WebFront render)
    person_role TEXT,
        -- Denormalized: role_title from network table

    -- What
    obligation_type TEXT NOT NULL CHECK (obligation_type IN ('I_OWE_THEM', 'THEY_OWE_ME')),
        -- I_OWE_THEM: Aakash committed to do something for this person
        -- THEY_OWE_ME: This person committed to do something for Aakash
    description TEXT NOT NULL,
        -- Human-readable: "Send term sheet feedback to Rahul"
        -- or "Rahul to send updated cap table"
    category TEXT NOT NULL DEFAULT 'follow_up',
        -- 'send_document' | 'reply' | 'schedule' | 'follow_up' | 'introduce' |
        -- 'review' | 'deliver' | 'connect' | 'provide_info' | 'other'

    -- Source (provenance)
    source TEXT NOT NULL,
        -- 'email' | 'whatsapp' | 'granola' | 'calendar' | 'manual'
    source_interaction_id INTEGER,
        -- FK to interactions.id — which interaction this was detected from
    source_quote TEXT,
        -- The exact text that triggered detection: "I'll send you the deck by Friday"
    detection_method TEXT NOT NULL DEFAULT 'explicit',
        -- 'explicit' — clear verbal/written commitment
        -- 'implied' — inferred from unanswered message, meeting etiquette, etc.
        -- 'manual' — Aakash created it manually

    -- Timing
    detected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        -- When Cindy detected this obligation
    due_date TIMESTAMPTZ,
        -- Explicit deadline if stated ("by Friday"), or inferred ("next week" = +7 days)
        -- NULL if no deadline mentioned — staleness tracking applies instead
    due_date_source TEXT,
        -- 'explicit' — stated in interaction: "by Friday"
        -- 'inferred' — Cindy inferred from context: "next week", "soon"
        -- 'etiquette' — social norm: reply within 48h, follow up within 1 week
        -- NULL if no due date

    -- Status lifecycle
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN (
        'pending', 'fulfilled', 'overdue', 'cancelled', 'snoozed', 'escalated'
    )),
        -- pending: active, not yet fulfilled
        -- fulfilled: completed (manually marked or auto-detected)
        -- overdue: past due_date or staleness threshold exceeded
        -- cancelled: no longer relevant (meeting cancelled, deal passed, etc.)
        -- snoozed: temporarily hidden (snooze_until timestamp)
        -- escalated: Megamind flagged as strategically critical
    status_changed_at TIMESTAMPTZ DEFAULT NOW(),
    fulfilled_at TIMESTAMPTZ,
    fulfilled_method TEXT,
        -- 'manual' | 'auto_detected' | 'action_completed'
        -- auto_detected: Cindy saw a follow-up interaction that resolves this
        -- action_completed: linked action in actions_queue marked Done
    fulfilled_evidence TEXT,
        -- What resolved it: "Email sent on March 22 — interaction #456"
    snooze_until TIMESTAMPTZ,
        -- If snoozed: when to resurface

    -- Priority (Cindy's comms priority)
    cindy_priority REAL NOT NULL DEFAULT 0.5,
        -- 0.0-1.0 — Cindy's assessment based on relationship, staleness, type, source
    cindy_priority_factors JSONB,
        -- {
        --   "relationship_tier": "portfolio_founder",
        --   "relationship_tier_weight": 0.30,
        --   "staleness_weight": 0.25,
        --   "obligation_type_weight": 0.20,
        --   "source_reliability_weight": 0.15,
        --   "recency_weight": 0.10,
        --   "computed_at": "2026-03-20T10:00:00Z"
        -- }

    -- Priority (Megamind's strategic overlay)
    megamind_priority REAL,
        -- 0.0-1.0 — Megamind's strategic assessment (NULL until Megamind processes)
    megamind_priority_factors JSONB,
        -- {
        --   "thesis_connection": "Agentic AI Infrastructure",
        --   "portfolio_health": "green",
        --   "competitive_pressure": false,
        --   "strategic_roi": 0.72,
        --   "override_to_p0": false,
        --   "computed_at": "2026-03-20T10:05:00Z"
        -- }
    megamind_override BOOLEAN DEFAULT FALSE,
        -- TRUE if Megamind overrode to P0 for time-sensitive strategic opportunity

    -- Blended priority (final ranking)
    blended_priority REAL GENERATED ALWAYS AS (
        CASE
            WHEN megamind_override THEN 1.0
            WHEN megamind_priority IS NOT NULL
                THEN (cindy_priority * 0.6) + (megamind_priority * 0.4)
            ELSE cindy_priority
        END
    ) STORED,
        -- 60% Cindy (relationship dynamics) + 40% Megamind (strategic context)
        -- But Megamind can override to 1.0 for P0 strategic urgency

    -- Staleness tracking
    staleness_days INTEGER GENERATED ALWAYS AS (
        CASE
            WHEN status IN ('pending', 'overdue', 'escalated')
                THEN EXTRACT(DAY FROM (NOW() - detected_at))::INTEGER
            ELSE 0
        END
    ) STORED,

    -- Context
    context JSONB,
        -- {
        --   "thesis_connection": "Agentic AI Infrastructure",
        --   "company": "Composio",
        --   "company_id": 15,
        --   "deal_stage": "Series A",
        --   "relationship_history": "3 meetings in last 2 weeks",
        --   "related_obligations": [12, 15],  -- other obligations with same person
        --   "related_action_id": 55  -- linked actions_queue item
        -- }

    -- Linked action (if an action was created to fulfill this obligation)
    linked_action_id INTEGER,
        -- FK to actions_queue.id — the action that, when completed, fulfills this obligation

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Primary query: active obligations sorted by blended priority
CREATE INDEX idx_obligations_active ON obligations(blended_priority DESC)
    WHERE status IN ('pending', 'overdue', 'escalated');

-- Query: obligations by person (for "what do I owe X?" / "what does X owe me?")
CREATE INDEX idx_obligations_person ON obligations(person_id, status);

-- Query: obligations by type (split view: I_OWE vs THEY_OWE)
CREATE INDEX idx_obligations_type ON obligations(obligation_type, status, blended_priority DESC)
    WHERE status IN ('pending', 'overdue', 'escalated');

-- Query: overdue obligations (staleness alerts)
CREATE INDEX idx_obligations_overdue ON obligations(due_date)
    WHERE status = 'pending' AND due_date IS NOT NULL AND due_date < NOW();

-- Query: snoozed obligations ready to resurface
CREATE INDEX idx_obligations_snoozed ON obligations(snooze_until)
    WHERE status = 'snoozed' AND snooze_until IS NOT NULL;

-- Query: obligations by source interaction (for dedup and provenance)
CREATE INDEX idx_obligations_source ON obligations(source_interaction_id)
    WHERE source_interaction_id IS NOT NULL;

-- Query: obligations with Megamind override (P0 strategic urgency)
CREATE INDEX idx_obligations_megamind_override ON obligations(updated_at DESC)
    WHERE megamind_override = TRUE AND status IN ('pending', 'escalated');

-- Full-text search on description
CREATE INDEX idx_obligations_description_fts ON obligations
    USING gin(to_tsvector('english', description));
```

### Status Lifecycle

```
                    +--------+
                    | pending |<----- detected by Cindy
                    +----+---+
                         |
            +------------+------------+
            |            |            |
            v            v            v
       +---------+  +--------+  +---------+
       | overdue |  | snoozed|  |fulfilled|
       +----+----+  +---+----+  +---------+
            |            |
            v            v
       +-----------+  (resurfaces
       | escalated |   as pending)
       +-----+-----+
             |
             v
       +-----------+
       | fulfilled | or | cancelled |
       +-----------+    +-----------+

Transitions:
  pending -> fulfilled    : Aakash marks done, or auto-detected resolution
  pending -> overdue      : due_date passed, or staleness > threshold (7 days for I_OWE, 14 for THEY_OWE)
  pending -> snoozed      : Aakash snoozes for N days
  pending -> cancelled    : Meeting cancelled, deal passed, context invalidated
  overdue -> fulfilled    : Late but done
  overdue -> escalated    : Megamind flags strategic urgency, or 14+ days overdue
  overdue -> cancelled    : No longer relevant
  snoozed -> pending      : Snooze period expired (snooze_until < NOW())
  escalated -> fulfilled  : Finally resolved
  escalated -> cancelled  : No longer relevant
```

### Staleness Thresholds

| Obligation Type | Warning (days) | Overdue (days) | Escalation (days) |
|----------------|---------------|----------------|-------------------|
| I_OWE_THEM (explicit) | 3 | 5 | 10 |
| I_OWE_THEM (implied) | 5 | 7 | 14 |
| THEY_OWE_ME (explicit) | 5 | 10 | 21 |
| THEY_OWE_ME (implied) | 7 | 14 | 30 |

Rationale: I_OWE obligations are more urgent because Aakash's reputation is at stake. THEY_OWE obligations can wait longer because nudging too early is pushy. Explicit commitments are more urgent than implied ones.

---

## 3. Detection Algorithms

### 3.1 Obligation Detection Pipeline

Every interaction that Cindy processes (email, WhatsApp, Granola, calendar) passes through the obligation detection pipeline AFTER the standard signal extraction pipeline. This is an additional processing step, not a replacement.

```
Cindy processes interaction (existing pipeline)
    |
    v
Standard signal extraction: action items, thesis signals, relationship signals
    |
    v
OBLIGATION DETECTION (new step):
    1. Scan interaction text for obligation patterns (NLP)
    2. Classify: I_OWE_THEM or THEY_OWE_ME
    3. Extract: who, what, when (if stated)
    4. Dedup: check existing obligations for this person + similar description
    5. Create obligation record
    6. Compute Cindy priority
    7. Route to Megamind for strategic overlay (if high significance)
    |
    v
Write to obligations table
```

### 3.2 Email Detection Patterns

**Explicit I_OWE_THEM (Aakash committed to do something):**

| Pattern | Category | Example |
|---------|----------|---------|
| "I'll send you..." / "Let me send..." | send_document | "I'll send you the term sheet by Friday" |
| "I'll get back to you on..." / "Let me circle back..." | reply | "Let me get back to you on the valuation question" |
| "I will follow up..." / "Will circle back..." | follow_up | "Will circle back next week on the IC timeline" |
| "Let me introduce you to..." / "I'll connect you with..." | introduce | "Let me introduce you to our cybersecurity portfolio founder" |
| "I'll review..." / "Let me look at..." | review | "I'll review the deck this weekend" |
| "I'll schedule..." / "Let me set up..." | schedule | "Let me set up a call with our IC" |
| "I'll share..." / "Will forward..." | send_document | "I'll share the market research with you" |
| First person future tense + action verb | (varies) | "I will check with the team and revert" |

**Explicit THEY_OWE_ME (someone committed to do something for Aakash):**

| Pattern | Category | Example |
|---------|----------|---------|
| "I'll send you..." (from someone else) | send_document | "I'll send you the updated cap table tomorrow" |
| "Could you send me..." (Aakash requesting) | send_document | "Could you send me the latest financials?" |
| "Please share..." (Aakash requesting) | provide_info | "Please share the Q4 numbers when available" |
| "Looking forward to receiving..." | deliver | "Looking forward to receiving the reference list" |
| "Will get back to you..." (from someone else) | reply | "Will get back to you on the follow-on terms" |
| "[Name] to send..." / "[Name] will..." | (varies) | "Rahul to send pitch deck next week" |

**Implied I_OWE_THEM (inferred from behavior patterns):**

| Pattern | Category | Detection Logic |
|---------|----------|----------------|
| Unanswered email (48h+) where last message was from them | reply | `SELECT * FROM interactions WHERE source='email' AND thread_id=X ORDER BY timestamp DESC LIMIT 1` -> if sender != Aakash AND age > 48h |
| Meeting happened, no follow-up email within 48h | follow_up | Calendar event + no email interaction with attendees in 48h post-meeting |
| Calendar invite accepted but no prep/context sent | follow_up | For important meetings (portfolio founders, thesis-related) where Aakash accepted but hasn't sent any preparation material |

**Implied THEY_OWE_ME (inferred from behavior patterns):**

| Pattern | Category | Detection Logic |
|---------|----------|----------------|
| Unanswered email (48h+) where last message was from Aakash | reply | Last message in thread from Aakash, no response in 48h |
| Message with "?" sent by Aakash, no reply | reply | Aakash sent a question (contains "?"), no response detected |
| Action item assigned to someone in meeting | deliver | Granola action item assigned to non-Aakash attendee |

### 3.3 WhatsApp Detection Patterns

Same patterns as email, adapted for conversational format:

**Explicit I_OWE_THEM:**
- "Will share..." / "Let me check and get back..."
- "I'll send the..." / "Sending you..."
- Response to a direct request that Aakash acknowledged but hasn't fulfilled

**Explicit THEY_OWE_ME:**
- "I'll send you..." / "Will forward..."
- "Let me check and revert..."
- "Will share by [day]..."

**Implied (WhatsApp-specific):**
- Unread messages from important contacts (portfolio founders, deal-related) older than 24h -> possible I_OWE_THEM
- Messages Aakash sent containing "?" with no reply after 48h -> possible THEY_OWE_ME
- Group chat where someone volunteered to do something for Aakash -> THEY_OWE_ME

### 3.4 Granola (Meeting) Detection Patterns

Meeting transcripts are the richest source of obligations because people make verbal commitments in meetings.

**Explicit I_OWE_THEM:**
- Action items assigned to "Aakash" / "me" / "I will" / "I'll"
- "I'll have my team look into..." / "Let me check with..."
- "I'll send you..." / "Will share..."
- "I'll schedule a follow-up..." / "Let me set up..."
- Aakash's microphone utterances containing first-person future commitments

**Explicit THEY_OWE_ME:**
- Action items assigned to other attendees
- "[Name] to..." / "[Name] will..."
- "I'll get that to you..." (from other speaker, `source: "system"`)
- "We'll send over..." / "Our team will prepare..."

**Mutual obligations:**
- "Let's schedule a follow-up" -> both parties share the obligation
- "Let's set up a meeting with [third party]" -> both parties
- For mutual obligations, create TWO records: one I_OWE (scheduling responsibility typically falls to the one with the EA) and one THEY_OWE (the other party's share)

**Granola-specific extraction:**
```
FOR each utterance in transcript:
    IF utterance contains future_commitment_pattern:
        IF utterance.source == "microphone":
            # Aakash speaking -> I_OWE_THEM
            create_obligation(type='I_OWE_THEM', source_quote=utterance.text)
        ELIF utterance.source == "system":
            # Other person speaking -> THEY_OWE_ME
            create_obligation(type='THEY_OWE_ME', source_quote=utterance.text)

# Also check Granola's AI-generated action items
FOR each action_item in meeting.action_items:
    IF action_item is assigned to Aakash:
        create_obligation(type='I_OWE_THEM')
    ELSE:
        create_obligation(type='THEY_OWE_ME')
```

### 3.5 Calendar Detection Patterns

Calendar itself produces fewer direct obligations, but triggers obligation inference:

**Post-meeting follow-up etiquette (implied I_OWE_THEM):**
- External meeting happened but no follow-up detected in email/WhatsApp within 48h
- Applies only to meetings with:
  - Portfolio founders (relationship_tier check)
  - Deal-flow contacts (companies DB deal_status check)
  - Thesis-relevant people
- Does NOT apply to: internal meetings, casual coffees, large group events

**Pre-meeting obligation inference:**
- Meeting scheduled with someone Aakash has open obligations to -> surface as "before this meeting, you owe [person] [item]"
- Meeting scheduled where someone owes Aakash something -> surface as "at this meeting, ask about [item]"

### 3.6 NLP Pattern Matching

Cindy uses Claude's language understanding for obligation detection rather than regex. The prompt instruction within Cindy's processing pipeline:

```
After extracting standard signals (action items, thesis signals, etc.),
scan this interaction for OBLIGATIONS:

An obligation is a commitment between Aakash and another person.

For each detected obligation, extract:
1. type: I_OWE_THEM (Aakash committed to do something) or
         THEY_OWE_ME (someone committed to do something for Aakash)
2. person: who is the other party
3. description: what was committed (concise, action-oriented)
4. category: send_document | reply | schedule | follow_up | introduce |
             review | deliver | connect | provide_info | other
5. due_date: if mentioned (explicit date or relative: "by Friday", "next week")
6. source_quote: the exact words that create this obligation
7. detection_method: explicit (clear verbal commitment) or implied (behavioral inference)
8. confidence: 0.0-1.0 how confident you are this is a real obligation

Only create obligations with confidence >= 0.7.
Do NOT create obligations for:
  - Generic pleasantries ("Let's catch up sometime")
  - Vague intentions without specifics ("We should do something together")
  - Internal team operations (Z47/DeVC team coordination)
  - Obligations already tracked (check existing obligations for this person)
```

### 3.7 Deduplication

Before creating an obligation, check for existing obligations with the same person and similar description:

```sql
-- Check for potential duplicates
SELECT id, description, status, detected_at
FROM obligations
WHERE person_id = $1
  AND status IN ('pending', 'overdue', 'snoozed', 'escalated')
  AND (
    -- Exact match on source interaction (same email/message/meeting)
    source_interaction_id = $2
    -- Or similar description (fuzzy)
    OR similarity(description, $3) > 0.6
  )
LIMIT 5;
```

If a duplicate is found:
- Same interaction ID -> skip (already detected)
- Similar description from different interaction -> UPDATE existing record with new evidence (append source_quote, update detected_at if newer)
- Different description from same person -> create new record (person can have multiple outstanding obligations)

### 3.8 Auto-Fulfillment Detection

When Cindy processes a new interaction, she also checks whether it resolves any existing obligations:

```
FOR each existing pending obligation with this person:
    IF new_interaction resolves obligation:
        # E.g., Aakash sent an email with attachment -> resolves "send deck to X"
        # E.g., person sent financial data -> resolves "X to send financials"
        UPDATE obligations SET
            status = 'fulfilled',
            fulfilled_at = NOW(),
            fulfilled_method = 'auto_detected',
            fulfilled_evidence = 'Resolved by interaction #' || new_interaction.id
        WHERE id = obligation.id;
```

Resolution signals:
- I_OWE (send_document) + Aakash sent email with attachment to this person -> fulfilled
- I_OWE (reply) + Aakash sent email/message to this person's thread -> fulfilled
- I_OWE (schedule) + Calendar event created with this person -> fulfilled
- I_OWE (introduce) + Email with both parties included -> fulfilled
- THEY_OWE (send_document) + Person sent email with attachment to Aakash -> fulfilled
- THEY_OWE (reply) + Person replied to Aakash's message -> fulfilled
- THEY_OWE (deliver) + Relevant document/info received from person -> fulfilled

---

## 4. Priority Reasoning (Cindy + Megamind)

### 4.1 Cindy's Comms Priority (0.0 - 1.0)

Cindy calculates priority based on relationship context and obligation urgency. She understands the social dynamics of professional relationships.

```
cindy_priority(obligation) =
    relationship_tier_weight * 0.30 +
    staleness_weight         * 0.25 +
    obligation_type_weight   * 0.20 +
    source_reliability_weight * 0.15 +
    recency_weight           * 0.10
```

**Factor 1: Relationship Tier (30% weight)**

| Tier | Weight | Who |
|------|--------|-----|
| Portfolio founder | 1.0 | Founders of companies Z47/DeVC has invested in |
| Active deal contact | 0.9 | People in companies with deal_status = active pipeline |
| GP/Partner (other fund) | 0.85 | Co-investors, syndicate partners, other VC GPs |
| Thesis-connected person | 0.75 | People linked to active thesis threads |
| DeVC Collective member | 0.7 | Members of the DeVC network |
| Network contact (known) | 0.5 | People in Network DB but no special tier |
| Cold/new contact | 0.3 | First interaction, no relationship history |

Source: `network.archetype` + `network.relationship_tier` + company linkage from `companies.deal_status`

**Factor 2: Staleness (25% weight)**

| Staleness (days) | Weight |
|-----------------|--------|
| 0-2 | 0.2 |
| 3-5 | 0.5 |
| 5-7 | 0.7 |
| 7-10 | 0.85 |
| 10-14 | 0.95 |
| 14+ | 1.0 |

Staleness applies only to pending/overdue obligations. Exponential urgency curve: obligations get progressively more urgent the longer they sit.

**Factor 3: Obligation Type (20% weight)**

| Type | Weight | Rationale |
|------|--------|-----------|
| I_OWE_THEM | 0.8 | Proactive EA: prioritize what Aakash owes. His reputation. |
| THEY_OWE_ME | 0.5 | Lower urgency: nudging is less critical than delivering. |

Within I_OWE_THEM:
- send_document: 0.9 (tangible deliverable, easy to verify)
- reply: 0.85 (someone is waiting)
- introduce: 0.8 (involves a third party's time)
- schedule: 0.75 (logistics)
- review: 0.7 (internal work)
- follow_up: 0.65 (general follow-through)

**Factor 4: Source Reliability (15% weight)**

| Detection Method | Weight | Rationale |
|-----------------|--------|-----------|
| explicit (verbal/written commitment) | 1.0 | Clear promise — must be honored |
| implied (behavioral inference) | 0.5 | May not be a real obligation |
| manual (user-created) | 0.9 | Aakash explicitly tracked it |

**Factor 5: Recency (10% weight)**

More recently detected obligations get a slight boost to prevent them from being buried by stale items.

| Age | Weight |
|-----|--------|
| Today | 1.0 |
| 1-3 days | 0.8 |
| 3-7 days | 0.6 |
| 7+ days | 0.4 |

### 4.2 Megamind's Strategic Overlay (0.0 - 1.0)

Megamind receives obligation priority requests from Cindy (via `cindy_signal` type in `cai_inbox`) and applies strategic context.

```
megamind_priority(obligation) =
    thesis_connection_weight    * 0.30 +
    portfolio_health_weight     * 0.25 +
    competitive_pressure_weight * 0.25 +
    strategic_roi_weight        * 0.20
```

**Factor 1: Thesis Connection (30% weight)**

| Condition | Weight |
|-----------|--------|
| Person/company connected to Active thesis with conviction >= "Evolving Fast" | 1.0 |
| Person/company connected to Active thesis with any conviction | 0.7 |
| Person/company connected to Exploring thesis | 0.4 |
| No thesis connection | 0.2 |

**Factor 2: Portfolio Health (25% weight)**

| Condition | Weight |
|-----------|--------|
| Portfolio company in red health (needs intervention) | 1.0 |
| Portfolio company in yellow health (needs attention) | 0.7 |
| Portfolio company approaching follow-on decision | 0.8 |
| Portfolio company in green health | 0.3 |
| Non-portfolio | 0.2 |

Source: Companies DB deal_status + any recent portfolio signals from Content Agent

**Factor 3: Competitive Pressure (25% weight)**

| Condition | Weight |
|-----------|--------|
| Other VCs actively courting this founder (known from signals) | 1.0 |
| Company is in active fundraise (term sheet stage) | 0.9 |
| Company has upcoming board meeting / BRC | 0.8 |
| No competitive pressure detected | 0.2 |

**Factor 4: Strategic ROI (20% weight)**

Megamind's core calculation: what is the ROI of fulfilling this obligation vs other uses of Aakash's time? Uses the same `strategic_roi()` function from the Megamind design spec, applied to the obligation's context.

### 4.3 The Blend

```
blended_priority = CASE
    WHEN megamind_override = TRUE THEN 1.0    -- Megamind P0 override
    WHEN megamind_priority IS NOT NULL
        THEN (cindy_priority * 0.60) + (megamind_priority * 0.40)
    ELSE cindy_priority                       -- Megamind hasn't assessed yet
END
```

**Why 60/40 in favor of Cindy:**
- Cindy processes EVERY obligation in real-time. She has complete coverage.
- Megamind only processes obligations routed to it (high significance). Many obligations never reach Megamind.
- Relationship dynamics (Cindy's domain) are the primary driver of "should I respond to this person NOW?"
- Strategic context (Megamind's domain) is a multiplier, not the base signal.

**Megamind P0 Override:**
Megamind can set `megamind_override = TRUE` for time-sensitive strategic opportunities. Examples:
- Company in active fundraise where competing VC is closing -> fulfilling Aakash's obligations becomes urgent
- Portfolio company in crisis -> all obligations to that founder get P0
- Deal window closing (BRC deadline, term sheet expiry) -> related obligations escalate

### 4.4 Routing: Which Obligations Go to Megamind

Not every obligation needs strategic assessment. Route to Megamind only when:

| Condition | Route to Megamind? |
|-----------|-------------------|
| Person is portfolio founder | YES |
| Person is connected to active deal (deal_status = active pipeline) | YES |
| Person is connected to Active thesis | YES |
| Obligation is overdue (> staleness threshold) | YES |
| Cindy priority > 0.7 | YES |
| Obligation is I_OWE_THEM + person relationship_tier >= partner | YES |
| Person is new contact with no relationship history | NO |
| Obligation is THEY_OWE_ME with staleness < 7 days | NO |
| Obligation detected from social WhatsApp conversation | NO |

For obligations NOT routed to Megamind, `megamind_priority` stays NULL and `blended_priority` = `cindy_priority`.

---

## 5. Cindy Alerts — WebFront Design

### Route Structure

```
/cindy                 -- Obligations Dashboard (primary view)
/cindy/feed            -- Follow-Up Feed (chronological action list)
/cindy/insights        -- Cindy Insights (analytics and patterns)
```

### 5.1 View 1: Obligations Dashboard (`/cindy`)

The primary view. Split into two columns: what Aakash owes others (left) and what others owe Aakash (right). This dual view is the signature EA capability.

```
/cindy

+--------------------------------------------------------------------------+
|  Obligations                          [8 pending] [3 overdue]             |
|  [All] [Overdue] [Snoozed]           [+ Manual obligation]              |
+--------------------------------------------------------------------------+
|                                                                            |
|  +----- YOU OWE (5) ------+          +----- THEY OWE (3) ------+        |
|  |                         |          |                          |        |
|  | [P0] OVERDUE 7d         |          | [P1] 3 days              |        |
|  | Rahul Sharma            |          | Sarah Lee                |        |
|  | CTO, Composio           |          | Ops, Composio            |        |
|  | "Send term sheet        |          | "Send updated cap table" |        |
|  |  feedback"              |          |                          |        |
|  | Detected: Mar 13        |          | Detected: Mar 17         |        |
|  | Source: Granola          |          | Source: Email             |        |
|  | Thesis: Agentic AI      |          |                          |        |
|  |                         |          | [Nudge]  [Done]  [x]     |        |
|  | [Done] [Snooze] [x]     |          |                          |        |
|  +-------------------------+          +--------------------------+        |
|  |                         |          |                          |        |
|  | [P1] 4 days             |          | [P1] 5 days              |        |
|  | Vikram Vaidyanathan     |          | Karan Vaidya             |        |
|  | GP, Z47                 |          | Founder, StartupX        |        |
|  | "Share cybersecurity     |          | "Send reference list     |        |
|  |  thesis update"         |          |  for CTO hire"           |        |
|  |                         |          |                          |        |
|  | [Done] [Snooze] [x]     |          | [Nudge]  [Done]  [x]     |        |
|  +-------------------------+          +--------------------------+        |
|  |                         |          |                          |        |
|  | [P2] 1 day              |          | [P2] 1 day               |        |
|  | Priya Mehta             |          | Aakrit Pandey            |        |
|  | Investor, Accel         |          | DeVC                     |        |
|  | "Reply to co-invest     |          | "Share pipeline data     |        |
|  |  inquiry"               |          |  for March cohort"       |        |
|  |                         |          |                          |        |
|  | [Done] [Snooze] [x]     |          | [Nudge]  [Done]  [x]     |        |
|  +-------------------------+          +--------------------------+        |
|                                                                            |
+--------------------------------------------------------------------------+
```

**Component Specification:**

**ObligationCard:**
- Person avatar (from Network DB, or initials fallback)
- Person name + role (denormalized on obligation record)
- Priority badge: P0 (red), P1 (orange), P2 (yellow), P3 (gray)
- Overdue indicator: red bar + "OVERDUE Xd" if status = overdue
- Staleness indicator: "X days" since detection
- Description: 1-2 lines, truncated with ellipsis
- Source badge: Email / WhatsApp / Granola / Calendar / Manual
- Thesis badge: if connected to active thesis (from context JSONB)
- Action buttons (44x44px touch targets):
  - "Done" (mark fulfilled) -> green checkmark
  - "Snooze" (snooze 1/3/7 days) -> clock icon, dropdown on tap
  - "x" (cancel) -> requires confirmation tap
  - "Nudge" (THEY_OWE only) -> generate draft follow-up (future: opens email/WhatsApp draft)

**Filters:**
- Status: All | Overdue | Snoozed
- Person: type-ahead search
- Source: Email | WhatsApp | Granola | Calendar | Manual
- Priority: P0 | P1 | P2 | P3
- Category: send_document | reply | schedule | follow_up | introduce | etc.

**Sort:** By blended_priority DESC (default). Alternative: by staleness_days DESC, by due_date ASC.

**Data source:**
```sql
SELECT o.*, n.email, n.phone, n.archetype
FROM obligations o
JOIN network n ON o.person_id = n.id
WHERE o.status IN ('pending', 'overdue', 'escalated')
ORDER BY o.blended_priority DESC
LIMIT 50;
```

### 5.2 View 2: Follow-Up Feed (`/cindy/feed`)

Chronological feed of follow-up suggestions. Each item is a sentence-level recommendation with context, making it scannable on mobile.

```
/cindy/feed

+--------------------------------------------------------------------------+
|  Follow-Up Feed                                        [12 suggestions]   |
+--------------------------------------------------------------------------+
|                                                                            |
|  +--- TODAY ----------------------------------------------------------+  |
|  |                                                                      |  |
|  |  [P0] Follow up with Rahul Sharma about term sheet feedback         |  |
|  |  Portfolio founder, Composio | Waiting 7 days | Source: Granola      |  |
|  |  "You promised term sheet feedback in the March 13 meeting.         |  |
|  |   Rahul is likely waiting. Composio is in active Series A."         |  |
|  |  [Send follow-up]  [Mark done]  [Snooze 1d]                        |  |
|  |                                                                      |  |
|  |  [P1] Ask Sarah Lee about cap table update                          |  |
|  |  Ops, Composio | They owe you | 3 days | Source: Email              |  |
|  |  "Sarah committed to sending updated cap table in the March 17      |  |
|  |   email thread. No follow-up received."                              |  |
|  |  [Send reminder]  [Mark done]  [Snooze 3d]                          |  |
|  |                                                                      |  |
|  +--------------------------------------------------------------------+  |
|                                                                            |
|  +--- YESTERDAY -------------------------------------------------------+  |
|  |                                                                      |  |
|  |  [P1] Share cybersecurity thesis update with VV                      |  |
|  |  GP, Z47 | You owe | 4 days | Source: WhatsApp                     |  |
|  |  "VV asked for the latest cybersecurity thesis thinking in the       |  |
|  |   March 16 WhatsApp conversation."                                   |  |
|  |  [Send update]  [Mark done]  [Snooze 1d]                            |  |
|  |                                                                      |  |
|  +--------------------------------------------------------------------+  |
|                                                                            |
|  +--- EARLIER THIS WEEK -----------------------------------------------+  |
|  |  ... (grouped by day, collapsible)                                   |  |
|  +--------------------------------------------------------------------+  |
|                                                                            |
+--------------------------------------------------------------------------+
```

**FeedItem Component:**
- Priority badge + one-line action statement
- Person context line: name, role, company | obligation direction | staleness | source
- Reasoning paragraph: 2-3 sentences explaining WHY this follow-up matters. Includes:
  - The original commitment (source_quote)
  - How long it's been outstanding
  - Strategic context if available (thesis, deal stage, portfolio health)
- Action buttons: "Send follow-up" / "Send reminder" (generates draft), "Mark done", "Snooze Nd"

**Grouped by day** for chronological scanning. Most urgent at the top of each day group.

**Data source:**
```sql
SELECT o.*,
    CASE
        WHEN o.status = 'overdue' THEN 'overdue'
        WHEN o.staleness_days >= 5 THEN 'warning'
        ELSE 'normal'
    END as urgency_level
FROM obligations o
WHERE o.status IN ('pending', 'overdue', 'escalated')
ORDER BY o.blended_priority DESC, o.detected_at DESC
LIMIT 30;
```

### 5.3 View 3: Cindy Insights (`/cindy/insights`)

Analytics dashboard showing obligation patterns. Helps Aakash understand his follow-through habits and relationship maintenance.

```
/cindy/insights

+--------------------------------------------------------------------------+
|  Cindy Insights                                                            |
+--------------------------------------------------------------------------+
|                                                                            |
|  +--- Summary --------------------------------------------------------+  |
|  |                                                                      |  |
|  |  Outstanding: 12 obligations (8 I-owe, 4 they-owe)                  |  |
|  |  Overdue: 3 (all I-owe, avg 8 days overdue)                         |  |
|  |  Fulfilled this week: 7                                              |  |
|  |  Created this week: 5                                                |  |
|  |  Net trend: -2 (resolving faster than creating)                      |  |
|  |                                                                      |  |
|  +--------------------------------------------------------------------+  |
|                                                                            |
|  +--- Top Waiting On You -------------------------------------------+    |
|  |                                                                    |    |
|  |  1. Rahul Sharma (Composio) — 3 pending items, longest: 7 days   |    |
|  |  2. Vikram V. (Z47) — 2 pending items, longest: 4 days           |    |
|  |  3. Karan Vaidya (StartupX) — 1 pending item, 5 days             |    |
|  |                                                                    |    |
|  +--------------------------------------------------------------------+  |
|                                                                            |
|  +--- You're Waiting On -----------------------------------------------+  |
|  |                                                                      |  |
|  |  1. Sarah Lee (Composio) — cap table, 3 days                        |  |
|  |  2. Aakrit Pandey (DeVC) — pipeline data, 1 day                     |  |
|  |                                                                      |  |
|  +--------------------------------------------------------------------+  |
|                                                                            |
|  +--- Response Patterns -----------------------------------------------+  |
|  |                                                                      |  |
|  |  Your avg fulfillment time: 3.2 days                                 |  |
|  |  Fastest: Email replies (avg 1.1 days)                               |  |
|  |  Slowest: Document sends (avg 5.8 days)                              |  |
|  |                                                                      |  |
|  |  Most responsive to: Portfolio founders (avg 2.1 days)               |  |
|  |  Least responsive to: Thesis contacts (avg 6.3 days)                 |  |
|  |                                                                      |  |
|  +--------------------------------------------------------------------+  |
|                                                                            |
|  +--- Weekly Trend (4 weeks) ------------------------------------------+  |
|  |                                                                      |  |
|  |  [Bar chart: obligations created vs fulfilled per week]              |  |
|  |  Week 11: Created 8, Fulfilled 6 (net +2)                           |  |
|  |  Week 12: Created 5, Fulfilled 9 (net -4)                           |  |
|  |  Week 13: Created 7, Fulfilled 7 (net 0)                            |  |
|  |  Week 14: Created 5, Fulfilled 7 (net -2)                           |  |
|  |                                                                      |  |
|  +--------------------------------------------------------------------+  |
|                                                                            |
+--------------------------------------------------------------------------+
```

**Insights Queries:**

```sql
-- Summary stats
SELECT
    COUNT(*) FILTER (WHERE status IN ('pending', 'overdue', 'escalated')) as outstanding,
    COUNT(*) FILTER (WHERE status IN ('pending', 'overdue', 'escalated') AND obligation_type = 'I_OWE_THEM') as i_owe_count,
    COUNT(*) FILTER (WHERE status IN ('pending', 'overdue', 'escalated') AND obligation_type = 'THEY_OWE_ME') as they_owe_count,
    COUNT(*) FILTER (WHERE status = 'overdue') as overdue_count,
    COUNT(*) FILTER (WHERE status = 'fulfilled' AND fulfilled_at > NOW() - INTERVAL '7 days') as fulfilled_this_week,
    COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '7 days') as created_this_week,
    AVG(staleness_days) FILTER (WHERE status = 'overdue') as avg_overdue_days
FROM obligations;

-- Top people waiting on Aakash
SELECT person_name, person_role,
    COUNT(*) as pending_count,
    MAX(staleness_days) as longest_wait
FROM obligations
WHERE obligation_type = 'I_OWE_THEM'
    AND status IN ('pending', 'overdue')
GROUP BY person_id, person_name, person_role
ORDER BY pending_count DESC, longest_wait DESC
LIMIT 5;

-- Avg fulfillment time by category
SELECT category,
    AVG(EXTRACT(EPOCH FROM (fulfilled_at - detected_at)) / 86400)::NUMERIC(5,1) as avg_days
FROM obligations
WHERE status = 'fulfilled' AND fulfilled_at IS NOT NULL
    AND fulfilled_at > NOW() - INTERVAL '90 days'
GROUP BY category
ORDER BY avg_days DESC;
```

---

## 6. Cindy vs Megamind: Alert Differentiation

### Core Distinction

| Dimension | Cindy Alerts | Megamind Actions |
|-----------|-------------|-----------------|
| **Domain** | Comms obligations (who owes what to whom) | Strategic ROI optimization (what should Aakash do next) |
| **Trigger** | Interaction signals across 4 surfaces | Content analysis, thesis changes, cascade events |
| **Intelligence type** | Relationship-aware, etiquette-driven | Portfolio-aware, thesis-driven |
| **Examples** | "Follow up with X about term sheet" | "Research Company Y for new cap table thesis" |
| | "X is waiting on your intro to Y" | "Schedule deep-dive with Company Z -- conviction shifting" |
| | "You promised to send the deck by Friday" | "Re-evaluate thesis A -- new contra evidence found" |
| | "3 people waiting on you, longest: 7 days" | "Action space diverging -- 15 new, 3 resolved this week" |
| **Priority logic** | Relationship tier + staleness + obligation type | ENIAC raw score + thesis momentum + diminishing returns |
| **Time horizon** | Days (obligation staleness) | Weeks (strategic assessment, convergence) |
| **Action model** | "Fulfill this specific commitment" | "Investigate this strategic opportunity" |
| **Failure mode** | Damaged relationship, lost trust | Missed opportunity, suboptimal time allocation |

### How They Interact

```
Cindy detects obligation: "Send term sheet feedback to Rahul (Composio)"
    |
    v
Cindy computes comms priority: 0.75
    (portfolio founder x 1.0, staleness 7d x 0.85, I_OWE x 0.8, explicit x 1.0)
    |
    v
Routes to Megamind (portfolio founder, active deal)
    |
    v
Megamind adds strategic context:
    "Composio connected to Agentic AI thesis (Evolving Fast).
     Series A in progress. Competing VC (Accel) also in discussion.
     Fulfilling this obligation is strategically critical."
    Megamind priority: 0.92
    megamind_override: TRUE (competitive pressure + active deal)
    |
    v
Blended priority: 1.0 (P0 override)
    |
    v
Surfaces on WebFront with strategic context:
    "[P0 OVERDUE] Follow up with Rahul Sharma about term sheet feedback
     Portfolio founder, Composio | Agentic AI thesis | Competing VC active
     7 days outstanding — originally promised in March 13 meeting"
```

### What Each Agent Owns

| Responsibility | Owner |
|---------------|-------|
| Detecting obligations from interactions | Cindy |
| Computing comms priority (staleness, relationship, type) | Cindy |
| Auto-detecting obligation fulfillment | Cindy |
| Computing strategic priority (thesis, portfolio, competition) | Megamind |
| P0 override for time-sensitive strategic opportunities | Megamind |
| Showing obligations on WebFront | WebFront (reads from obligations table) |
| User actions (done, snooze, cancel) | WebFront Server Actions |
| Staleness-driven overdue transitions | pg_cron (mechanical, in-database) |
| Obligation convergence tracking | Cindy Insights (aggregation queries) |

---

## 7. CLAUDE.md Updates

### 7.1 Cindy CLAUDE.md — Additions

Add the following section after "## 7. Signal Extraction Templates" in Cindy's CLAUDE.md:

```markdown
## 7.5 Obligation Detection (MANDATORY processing step)

After extracting standard signals from every interaction, scan for OBLIGATIONS.

### What Is an Obligation
A commitment between Aakash and another person. Two types:
- **I_OWE_THEM**: Aakash committed to do something for someone
- **THEY_OWE_ME**: Someone committed to do something for Aakash

### Detection Process (every interaction)

1. Scan interaction text for commitment patterns:
   - Explicit: "I'll send...", "Will follow up...", "Let me get back to you..."
   - Implied: Unanswered emails (48h+), meeting without follow-up (48h+)
2. For each detected obligation, extract:
   - type (I_OWE_THEM / THEY_OWE_ME)
   - person_id (resolve via people linking)
   - description (concise, action-oriented)
   - category (send_document/reply/schedule/follow_up/introduce/review/deliver/connect/provide_info)
   - due_date (if mentioned — explicit date or relative like "next week")
   - source_quote (exact words creating the obligation)
   - confidence (0.0-1.0, only create if >= 0.7)
3. Dedup: check obligations table for existing obligations with same person + similar description
4. Create obligation record
5. Compute cindy_priority using the 5-factor formula
6. If person is portfolio founder, active deal, or thesis-connected: route to Megamind via cindy_signal

### Auto-Fulfillment Check
When processing a NEW interaction, also check whether it resolves any EXISTING obligations with the same person. Examples:
- Aakash sent email -> resolves I_OWE reply/send_document obligations to that person
- Person sent document -> resolves THEY_OWE send_document obligations from that person
- Calendar event created with person -> resolves I_OWE schedule obligations

### Obligation Categories
send_document | reply | schedule | follow_up | introduce | review | deliver | connect | provide_info | other

### Priority Formula
```
cindy_priority = relationship_tier(0.30) + staleness(0.25) + obligation_type(0.20) + source_reliability(0.15) + recency(0.10)
```

### Tables You Now Write (additional)

| Table | Access | Purpose |
|-------|--------|---------|
| `obligations` | Read + Write | Track all detected obligations |

### ACK Addition
Add to every ACK:
```
- [count] obligations detected ([I-owe], [they-owe])
- [count] obligations auto-fulfilled
```
```

### 7.2 Megamind CLAUDE.md — Additions

Add the following section after "## 4. Three Work Types" in Megamind's CLAUDE.md:

```markdown
### Type 4: Obligation Priority Assessment

When the Orchestrator sends you cindy_signal messages with obligation context:

1. Read the obligation(s) from the obligations table
2. Load thesis thread context for connected companies/people
3. Load portfolio health signals for connected companies
4. Check for competitive pressure (other VCs, active fundraise, upcoming BRC)
5. Calculate strategic priority using the 4-factor formula:
   - Thesis connection (0.30)
   - Portfolio health (0.25)
   - Competitive pressure (0.25)
   - Strategic ROI (0.20)
6. Write megamind_priority and megamind_priority_factors to obligations table
7. If time-sensitive strategic opportunity: set megamind_override = TRUE
8. If obligation is connected to an open depth-graded action: note the connection

### Obligation Override Rules
You may set megamind_override = TRUE (forcing blended_priority to 1.0) when:
- Company is in active fundraise with competing VC engagement
- Portfolio company is in crisis (red health)
- Deal window is closing (BRC deadline, term sheet expiry within 5 days)
- Obligation connects to a cascade that resolved actions but needs human follow-through

### Tables You Now Write (additional)

| Table | Access | Purpose |
|-------|--------|---------|
| `obligations` (megamind_priority, megamind_priority_factors, megamind_override) | Write | Strategic overlay on Cindy's obligations |
```

---

## 8. WebFront Component Specification

### 8.1 Server Actions

```typescript
// Mark obligation as fulfilled
async function markObligationFulfilled(obligationId: number, evidence?: string) {
  await supabase
    .from('obligations')
    .update({
      status: 'fulfilled',
      fulfilled_at: new Date().toISOString(),
      fulfilled_method: 'manual',
      fulfilled_evidence: evidence || 'Marked done by user on WebFront',
      status_changed_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    })
    .eq('id', obligationId);
}

// Snooze obligation for N days
async function snoozeObligation(obligationId: number, days: number) {
  const snoozeUntil = new Date();
  snoozeUntil.setDate(snoozeUntil.getDate() + days);

  await supabase
    .from('obligations')
    .update({
      status: 'snoozed',
      snooze_until: snoozeUntil.toISOString(),
      status_changed_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    })
    .eq('id', obligationId);
}

// Cancel obligation
async function cancelObligation(obligationId: number, reason?: string) {
  await supabase
    .from('obligations')
    .update({
      status: 'cancelled',
      fulfilled_evidence: reason || 'Cancelled by user',
      status_changed_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    })
    .eq('id', obligationId);
}

// Create manual obligation
async function createManualObligation(input: {
  personId: number;
  type: 'I_OWE_THEM' | 'THEY_OWE_ME';
  description: string;
  category: string;
  dueDate?: string;
}) {
  const person = await supabase
    .from('network')
    .select('person_name, role_title')
    .eq('id', input.personId)
    .single();

  await supabase.from('obligations').insert({
    person_id: input.personId,
    person_name: person.data?.person_name,
    person_role: person.data?.role_title,
    obligation_type: input.type,
    description: input.description,
    category: input.category,
    source: 'manual',
    detection_method: 'manual',
    due_date: input.dueDate,
    due_date_source: input.dueDate ? 'explicit' : null,
    cindy_priority: 0.6, // Manual obligations get moderate base priority
    cindy_priority_factors: {
      relationship_tier: 'manual_entry',
      note: 'User-created obligation, moderate default priority',
    },
  });
}

// Fetch obligations for dashboard
async function fetchObligations(filters: {
  type?: 'I_OWE_THEM' | 'THEY_OWE_ME';
  status?: string[];
  priority?: string;
  personId?: number;
}) {
  let query = supabase
    .from('obligations')
    .select('*, network!person_id(email, phone, archetype, linkedin)')
    .in('status', filters.status || ['pending', 'overdue', 'escalated'])
    .order('blended_priority', { ascending: false });

  if (filters.type) query = query.eq('obligation_type', filters.type);
  if (filters.personId) query = query.eq('person_id', filters.personId);

  return query.limit(50);
}
```

### 8.2 Realtime Subscriptions

```typescript
// Subscribe to obligation changes for real-time updates
const channel = supabase
  .channel('obligations-changes')
  .on(
    'postgres_changes',
    {
      event: '*',
      schema: 'public',
      table: 'obligations',
      filter: "status=in.(pending,overdue,escalated)",
    },
    (payload) => {
      // Refresh obligation list on any change
      invalidateObligationCache();
    }
  )
  .subscribe();
```

### 8.3 Mobile-First Design Notes

- **Touch targets:** All action buttons are 44x44px minimum. Snooze dropdown appears on tap, not hover.
- **Swipe actions:** Swipe right to mark done (green). Swipe left to snooze (yellow). Long press for cancel (with confirmation).
- **Card density:** Each obligation card is 80-100px height. Show 4-5 cards per screen on mobile.
- **Split view:** On mobile, "You Owe" and "They Owe" tabs (not side-by-side columns). On desktop (768px+), side-by-side columns.
- **Priority badges:** Color-coded circles: P0 = red filled, P1 = orange filled, P2 = yellow outlined, P3 = gray outlined.
- **Overdue indicator:** Red left border on card + "OVERDUE Xd" badge in red.

### 8.4 WebFront Phase Integration

Obligations pages fit as **Phase 3.5b** alongside Cindy's `/comms` pages:

| Phase | Feature | Dependency |
|-------|---------|------------|
| 1 | Action Triage + Semantic Search | (current) |
| 2 | Thesis Interaction | Phase 1 |
| 2.5 | Megamind: Strategic Overview | Phase 1 + Megamind |
| 3 | Pipeline Status | Phase 1 |
| 3.5a | Cindy: /comms pages | Phase 1 + Cindy agent |
| **3.5b** | **Cindy: /cindy obligations pages** | **Phase 3.5a (interactions data) + obligations table** |
| 4 | Agent Messaging | Phase 1 |

---

## 9. CIR Integration

### 9.1 New CIR Triggers

The `obligations` table gets CIR change detection triggers, consistent with the living-system-architecture spec:

```sql
-- CIR trigger on obligations table
CREATE TRIGGER cir_detect_change_obligations
  AFTER INSERT OR UPDATE ON obligations
  FOR EACH ROW
  EXECUTE FUNCTION cir_detect_change();
```

### 9.2 CIR Propagation Rules

```sql
INSERT INTO cir_propagation_rules
(source_table, field_pattern, event_type, significance, propagation_targets, route_to_megamind, notes) VALUES

-- New obligation detected
('obligations', '*', 'insert', 'medium', ARRAY['actions_queue', 'network'], FALSE,
 'New obligation — update related actions priority, update network interaction metrics'),

-- Obligation fulfilled
('obligations', 'status', 'update', 'medium', ARRAY['network'], FALSE,
 'Fulfilled obligation — update relationship strength metrics. condition: NEW.status = fulfilled'),

-- Obligation goes overdue
('obligations', 'status', 'update', 'high', ARRAY['actions_queue'], TRUE,
 'Overdue obligation — escalate related actions, notify Megamind. condition: NEW.status = overdue'),

-- Megamind override applied
('obligations', 'megamind_override', 'update', 'high', ARRAY['actions_queue'], FALSE,
 'P0 override — re-rank connected actions immediately. condition: NEW.megamind_override = true'),

-- Priority change
('obligations', 'blended_priority', 'update', 'low', ARRAY[]::TEXT[], FALSE,
 'Priority change — no propagation, WebFront picks up via Realtime');
```

### 9.3 Propagation Effects

**New obligation created:**
- Tier 1 (mechanical): If the obligation has a `linked_action_id`, boost that action's `user_priority_score` by adding an obligation urgency factor.
- Tier 2 (strategic): No Megamind routing for new obligations (they route via the cindy_signal path instead).

**Obligation goes overdue:**
- Tier 1 (mechanical): Find actions connected to this person/company. Boost priority scores.
- Tier 2 (strategic): Route to Megamind via cai_inbox. Megamind evaluates whether this overdue obligation has strategic implications.

**Obligation fulfilled:**
- Tier 1 (mechanical): Update network relationship metrics (last_interaction_at, interaction_count_30d). If there was a linked action, mark it as Done if not already.
- Tier 2 (strategic): No Megamind routing for fulfillment (positive signal, no intervention needed).

### 9.4 Staleness Processor (pg_cron)

A pg_cron job runs every hour to transition obligations from pending to overdue:

```sql
-- Scheduled: every hour
CREATE OR REPLACE FUNCTION obligations_staleness_check()
RETURNS TABLE(transitioned int, resurfaced int)
LANGUAGE plpgsql AS $$
DECLARE
  v_transitioned int := 0;
  v_resurfaced int := 0;
BEGIN
  -- Transition pending -> overdue (explicit due_date passed)
  UPDATE obligations
  SET status = 'overdue',
      status_changed_at = NOW(),
      updated_at = NOW()
  WHERE status = 'pending'
    AND due_date IS NOT NULL
    AND due_date < NOW();
  GET DIAGNOSTICS v_transitioned = ROW_COUNT;

  -- Transition pending -> overdue (staleness threshold exceeded, no due_date)
  UPDATE obligations
  SET status = 'overdue',
      status_changed_at = NOW(),
      updated_at = NOW()
  WHERE status = 'pending'
    AND due_date IS NULL
    AND (
      (obligation_type = 'I_OWE_THEM' AND detection_method = 'explicit'
        AND detected_at < NOW() - INTERVAL '5 days')
      OR
      (obligation_type = 'I_OWE_THEM' AND detection_method = 'implied'
        AND detected_at < NOW() - INTERVAL '7 days')
      OR
      (obligation_type = 'THEY_OWE_ME' AND detection_method = 'explicit'
        AND detected_at < NOW() - INTERVAL '10 days')
      OR
      (obligation_type = 'THEY_OWE_ME' AND detection_method = 'implied'
        AND detected_at < NOW() - INTERVAL '14 days')
    );
  v_transitioned := v_transitioned + ROW_COUNT;

  -- Resurface snoozed obligations
  UPDATE obligations
  SET status = 'pending',
      snooze_until = NULL,
      status_changed_at = NOW(),
      updated_at = NOW()
  WHERE status = 'snoozed'
    AND snooze_until IS NOT NULL
    AND snooze_until < NOW();
  GET DIAGNOSTICS v_resurfaced = ROW_COUNT;

  RETURN QUERY SELECT v_transitioned, v_resurfaced;
END;
$$;

-- Schedule: every hour
SELECT cron.schedule(
  'obligations-staleness-check',
  '0 * * * *',
  $$SELECT * FROM obligations_staleness_check();$$
);
```

---

## 10. Implementation Plan

### Phase 0: Database Schema (S, 1-3 hours)
**Dependencies:** Supabase access

- [ ] Run migration: create `obligations` table with all columns and indexes
- [ ] Install CIR trigger on obligations table
- [ ] Add CIR propagation rules for obligations
- [ ] Schedule pg_cron staleness check job (hourly)
- [ ] Verify: INSERT test obligation, confirm CIR trigger fires, staleness processor runs

### Phase 1: Obligation Detection in Cindy (M, 3-8 hours)
**Dependencies:** Phase 0, Cindy agent running (from cindy-design Phase 1+)

- [ ] Update Cindy's CLAUDE.md with obligation detection instructions
- [ ] Add obligation detection as post-processing step in each surface pipeline
- [ ] Implement NLP-based pattern matching for explicit obligations
- [ ] Implement Cindy priority computation (5-factor formula)
- [ ] Implement deduplication check before obligation creation
- [ ] Create `skills/cindy/obligation-detection.md` with patterns and examples
- [ ] Test: process a Granola transcript with clear commitments, verify obligations created
- [ ] Test: process an email thread, verify I_OWE and THEY_OWE obligations detected
- [ ] Test: verify dedup prevents duplicate obligations from same interaction

### Phase 2: Auto-Fulfillment Detection (S, 1-3 hours)
**Dependencies:** Phase 1

- [ ] Add auto-fulfillment check to Cindy's interaction processing
- [ ] When processing new interaction, scan existing obligations for same person
- [ ] Match fulfillment signals (email sent -> reply obligation resolved, etc.)
- [ ] Test: create I_OWE reply obligation, then process follow-up email from Aakash, verify auto-fulfillment

### Phase 3: Megamind Strategic Overlay (M, 3-8 hours)
**Dependencies:** Phase 1, Megamind agent running (from megamind-design)

- [ ] Update Megamind's CLAUDE.md with Type 4 work (obligation priority assessment)
- [ ] Implement routing logic: high-significance obligations -> Megamind via cindy_signal
- [ ] Implement Megamind's 4-factor strategic priority computation
- [ ] Implement P0 override logic for time-sensitive strategic opportunities
- [ ] Test: create obligation for portfolio founder, verify Megamind overlay applied
- [ ] Test: create obligation during active fundraise, verify P0 override

### Phase 4: Implied Obligation Detection (M, 3-8 hours)
**Dependencies:** Phase 1, Calendar surface active (cindy-design Phase 1)

- [ ] Implement unanswered email detection (48h+ staleness on email threads)
- [ ] Implement meeting-without-follow-up detection (calendar event + no email in 48h)
- [ ] Implement WhatsApp unanswered question detection
- [ ] Add safeguards: don't create implied obligations for internal meetings, social conversations
- [ ] Test: leave an email unanswered for 48h, verify implied I_OWE obligation created
- [ ] Test: complete a meeting with no follow-up email, verify implied obligation created

### Phase 5: WebFront /cindy Pages (L, 1-3 sessions)
**Dependencies:** Phase 1-3, WebFront Phase 1 (Supabase connection)

- [ ] Create `/cindy` route with Obligations Dashboard (split You Owe / They Owe)
- [ ] Create `/cindy/feed` route with Follow-Up Feed
- [ ] Create `/cindy/insights` route with analytics
- [ ] Server Actions: markFulfilled, snooze, cancel, createManual
- [ ] Supabase Realtime subscriptions for obligation changes
- [ ] Mobile-first: swipe gestures, 44px touch targets, tab-based mobile layout
- [ ] Manual obligation creation form (person type-ahead + description + category + due date)
- [ ] Test: obligation created by Cindy appears on dashboard within 60s
- [ ] Test: mark obligation as done, verify status updates live
- [ ] Test: snooze obligation, verify it resurfaces after snooze period

### Phase 6: Calendar Pre-Meeting Obligation Surfacing (S, 1-3 hours)
**Dependencies:** Phase 1, Calendar surface active

- [ ] When assembling pre-meeting context, query obligations for each attendee
- [ ] Surface "Before this meeting: you owe [person] [items]" in context assembly
- [ ] Surface "At this meeting: ask about [items they owe you]" in context assembly
- [ ] Test: obligation exists for meeting attendee, verify it shows in pre-meeting brief

### Build Sequence

```
Phase 0 (schema) --> Phase 1 (detection) --> Phase 2 (auto-fulfillment)
                                    |
                              Phase 3 (Megamind overlay)
                                    |
                              Phase 4 (implied detection)
                                    |
                              Phase 5 (WebFront)
                                    |
                              Phase 6 (pre-meeting surfacing)
```

**Critical path:** Phase 0 -> Phase 1. Detection is the core capability.

**Value delivery:**
- After Phase 1: Obligations are detected and tracked. Cindy knows what Aakash owes and what's owed to him.
- After Phase 2: Obligations auto-resolve when the commitment is fulfilled. Less manual maintenance.
- After Phase 3: Strategic context from Megamind ensures the RIGHT obligations get prioritized.
- After Phase 4: Implied obligations catch the commitments people make implicitly. The EA safety net.
- After Phase 5: Aakash has a visual dashboard for obligation management. The EA interface.
- After Phase 6: Pre-meeting briefs include obligation context. Walk into every meeting knowing what's outstanding.

### Total Effort Estimate

| Phase | Effort | Dependency |
|-------|--------|------------|
| Phase 0: Schema | S (1-3h) | Supabase access |
| Phase 1: Detection | M (3-8h) | Phase 0 + Cindy running |
| Phase 2: Auto-fulfillment | S (1-3h) | Phase 1 |
| Phase 3: Megamind overlay | M (3-8h) | Phase 1 + Megamind running |
| Phase 4: Implied detection | M (3-8h) | Phase 1 + Calendar surface |
| Phase 5: WebFront | L (1-3 sessions) | Phase 1-3 + WebFront Phase 1 |
| Phase 6: Pre-meeting | S (1-3h) | Phase 1 + Calendar surface |
| **Total** | **M-L (14-34 hours)** | |

---

## 11. Edge Cases

### Duplicate Obligations

| Scenario | Handling |
|----------|---------|
| Same commitment mentioned in email AND meeting | Dedup by person_id + description similarity (>0.6). Keep the one with richer source_quote. |
| "I'll send the deck" mentioned 3 times in a thread | Single obligation. Subsequent mentions reinforce but don't duplicate. |
| Two different people both promise to send the same document | Two obligations (different person_id). They're independent commitments. |
| Aakash promises something to the same person he already promised | Dedup check catches it. If different thing, new obligation. If same thing, existing obligation gets fresh timestamp. |

### Cancelled Meetings

| Scenario | Handling |
|----------|---------|
| Meeting cancelled before it happens | All pre-meeting obligations tied to that meeting stay (they're from prior interactions, not the meeting itself). |
| Meeting cancelled AND the deal is dead | Obligations tied to that deal should be cancelled. Cindy detects deal_status change via CIR and prompts: "Deal with [company] passed. Cancel 3 related obligations?" |
| Meeting rescheduled | Due dates on associated obligations should shift. Auto-detect via Calendar event update (sequence > 0). |

### Changed Deadlines

| Scenario | Handling |
|----------|---------|
| "Actually, I'll need it by next Friday instead" | Cindy detects the updated deadline in a follow-up interaction. Updates due_date on existing obligation. |
| Person says "no rush" after originally setting a deadline | Cindy detects the relaxation. Clears due_date. Obligation falls to staleness-based tracking. |
| Aakash asks for extension | Interaction detected. If I_OWE, update due_date. If THEY_OWE, no change needed. |

### Vacation / Out of Office

| Scenario | Handling |
|----------|---------|
| Aakash is on vacation | Manual: snooze all obligations for vacation duration. Future: auto-detect OOO from calendar. |
| Other party is OOO | Cindy detects OOO auto-reply in email. Snooze THEY_OWE obligations until return date. |

### Ambiguous Obligations

| Scenario | Handling |
|----------|---------|
| "We should catch up soon" | NOT an obligation. Too vague, no specific commitment. Confidence < 0.7. |
| "Let me think about it" | Borderline. Create with detection_method='implied', lower priority. |
| "I'll try to get to it" | Weak commitment. Create with confidence 0.5-0.7 depending on context. If below 0.7, skip. |
| Group meeting where "someone" will do something | Only create if a specific person is identified. "Someone should follow up" = no obligation. "Rahul, can you follow up?" = THEY_OWE. |

### Obligation Chains

| Scenario | Handling |
|----------|---------|
| Aakash owes intro to X, but first needs info from Y | Two obligations: I_OWE (intro to X) + THEY_OWE (info from Y). Store relationship in context.related_obligations. |
| Fulfilling one obligation creates another | Natural flow. E.g., sending deck (obligation fulfilled) -> person reviews and asks questions (new obligation detected from follow-up email). |

### High Volume Scenarios

| Scenario | Handling |
|----------|---------|
| Board meeting generates 15 action items | All become obligations. Group by person on the dashboard for easier management. |
| WhatsApp batch has 50 conversations | Only extract obligations from deal/portfolio/thesis conversations (not social/operational). Limit to 20 conversations per batch (existing Cindy guard). |
| Person has 10+ pending obligations | Surface as "X has 10 items waiting" in Cindy Insights. Suggest batch resolution. |

---

## 12. UX Inspiration: What Makes a Great EA Alerts Interface

### The Gold Standard: Human EA Behavior

The best EAs do three things that Cindy's Obligations Intelligence replicates:

1. **They track both sides.** A great EA doesn't just track what their executive owes. They track what's owed TO the executive and proactively follow up. The split view (You Owe / They Owe) mirrors this dual awareness.

2. **They escalate by relationship importance.** A great EA knows that a portfolio founder waiting 3 days is more urgent than a cold contact waiting 10 days. The relationship-tier weighting in Cindy's priority model encodes this judgment.

3. **They surface obligations in context.** "Before your meeting with Rahul, you owe him term sheet feedback from last week's discussion." Pre-meeting obligation surfacing is the EA's killer feature.

### Design Principles for the Interface

**Principle 1: Glanceability.**
Aakash checks this on his phone between meetings. He needs to see the top 3 obligations in 2 seconds. The dashboard card format (person + obligation + staleness + priority) enables this.

**Principle 2: Zero-tap insight.**
The feed view provides enough context per item that Aakash can decide whether to act WITHOUT tapping into a detail view. The reasoning paragraph ("You promised term sheet feedback in the March 13 meeting. Rahul is likely waiting.") is the EA whispering in his ear.

**Principle 3: One-tap resolution.**
"Mark done" is one tap. "Snooze" is one tap + duration selection. No forms, no modals, no text entry required for the 90% case. The interface gets out of the way.

**Principle 4: Staleness as visual urgency.**
The longer an obligation sits, the more visually urgent it becomes. Fresh obligations are calm. 3-day obligations get an orange tint. 7-day obligations get a red border. This mirrors how a great EA would escalate their tone: from gentle reminder to "you REALLY need to handle this."

**Principle 5: Strategic context is additive, not primary.**
The base obligation ("send deck to Rahul") is always the primary text. Megamind's strategic context ("Active Series A, competing VC") is a secondary line. The EA tells you WHAT to do first, THEN why it matters strategically. Never the reverse.

### Anti-Patterns to Avoid

- **Do NOT make it look like a to-do app.** Obligations are relationship commitments, not tasks. The language should be relational ("Rahul is waiting on your feedback") not transactional ("Send feedback to Rahul").
- **Do NOT notify on every obligation.** Push notifications only for: P0 overrides, obligations becoming overdue, pre-meeting obligation surfacing. Everything else is pull (dashboard/feed).
- **Do NOT auto-send follow-ups.** Cindy observes, she doesn't act. The "Send follow-up" button should draft a message, not send it. Aakash controls outbound communication.
- **Do NOT show cancelled/fulfilled obligations prominently.** They clutter the active view. Archived behind a filter toggle. Only current obligations matter.
- **Do NOT treat all obligations equally.** A term sheet feedback to a portfolio founder is NOT the same priority as a thesis document to a thesis contact. The blended priority model exists for this reason.

---

## Appendix A: Obligation Priority Worked Examples

### Example 1: Portfolio Founder — Overdue I_OWE

```
Obligation: "Send term sheet feedback to Rahul Sharma"
Type: I_OWE_THEM
Person: Rahul Sharma (CTO, Composio) — portfolio founder
Source: Granola transcript, March 13 meeting
Staleness: 7 days
Detection: explicit ("I'll review and send feedback by end of this week")

Cindy priority:
  relationship_tier: portfolio_founder = 1.0 * 0.30 = 0.300
  staleness: 7 days = 0.85 * 0.25 = 0.213
  obligation_type: I_OWE + send_document = 0.8 * 0.9 * 0.20 = 0.144
  source_reliability: explicit = 1.0 * 0.15 = 0.150
  recency: 7 days = 0.4 * 0.10 = 0.040
  TOTAL: 0.847

Megamind overlay:
  thesis_connection: Agentic AI (Active, Evolving Fast) = 1.0 * 0.30 = 0.300
  portfolio_health: green (but active Series A) = 0.5 * 0.25 = 0.125
  competitive_pressure: Accel also in discussion = 1.0 * 0.25 = 0.250
  strategic_roi: high = 0.8 * 0.20 = 0.160
  TOTAL: 0.835
  megamind_override: TRUE (competing VC + active deal)

Blended: 1.0 (override)
Display: [P0 OVERDUE 7d] Send term sheet feedback to Rahul Sharma
```

### Example 2: New Contact — Low Priority THEY_OWE

```
Obligation: "Send reference list for CTO hire"
Type: THEY_OWE_ME
Person: Karan Vaidya (Founder, StartupX) — thesis contact, first interaction
Source: Email thread, March 17
Staleness: 3 days
Detection: explicit ("I'll send you the reference list by Monday")

Cindy priority:
  relationship_tier: thesis_connected = 0.75 * 0.30 = 0.225
  staleness: 3 days = 0.5 * 0.25 = 0.125
  obligation_type: THEY_OWE = 0.5 * 0.20 = 0.100
  source_reliability: explicit = 1.0 * 0.15 = 0.150
  recency: 3 days = 0.8 * 0.10 = 0.080
  TOTAL: 0.680

Megamind: not routed (THEY_OWE + staleness < 7 days + not portfolio)

Blended: 0.680 (Cindy only)
Display: [P2] Karan Vaidya to send reference list — 3 days
```

### Example 3: Implied Obligation — Meeting Without Follow-Up

```
Obligation: "Follow up after meeting with Priya Mehta"
Type: I_OWE_THEM
Person: Priya Mehta (Investor, Accel) — GP/Partner
Source: Calendar event March 18, no email/WhatsApp follow-up detected
Staleness: 2 days
Detection: implied (meeting etiquette — no follow-up within 48h)

Cindy priority:
  relationship_tier: GP/Partner = 0.85 * 0.30 = 0.255
  staleness: 2 days = 0.2 * 0.25 = 0.050
  obligation_type: I_OWE + follow_up = 0.8 * 0.65 * 0.20 = 0.104
  source_reliability: implied = 0.5 * 0.15 = 0.075
  recency: 2 days = 0.8 * 0.10 = 0.080
  TOTAL: 0.564

Megamind: not routed (low priority, implied)

Blended: 0.564 (Cindy only)
Display: [P2] Follow up with Priya Mehta after March 18 meeting — 2 days
```

---

## Appendix B: SQL Helper Functions

### Compute Cindy Priority

```sql
CREATE OR REPLACE FUNCTION compute_cindy_priority(
    p_person_id INTEGER,
    p_obligation_type TEXT,
    p_category TEXT,
    p_detection_method TEXT,
    p_detected_at TIMESTAMPTZ
)
RETURNS REAL
LANGUAGE plpgsql AS $$
DECLARE
    v_relationship_tier REAL := 0.5;
    v_staleness REAL := 0.2;
    v_type_weight REAL := 0.5;
    v_source_weight REAL := 0.5;
    v_recency REAL := 0.4;
    v_staleness_days INTEGER;
    v_archetype TEXT;
    v_has_portfolio BOOLEAN;
    v_has_active_deal BOOLEAN;
BEGIN
    -- Relationship tier
    SELECT archetype INTO v_archetype FROM network WHERE id = p_person_id;

    SELECT EXISTS(
        SELECT 1 FROM companies c
        JOIN network n ON n.id = p_person_id
        WHERE c.deal_status ILIKE '%portfolio%'
    ) INTO v_has_portfolio;

    SELECT EXISTS(
        SELECT 1 FROM companies c
        JOIN network n ON n.id = p_person_id
        WHERE c.deal_status ILIKE '%active%' OR c.deal_status ILIKE '%pipeline%'
    ) INTO v_has_active_deal;

    IF v_has_portfolio THEN v_relationship_tier := 1.0;
    ELSIF v_has_active_deal THEN v_relationship_tier := 0.9;
    ELSIF v_archetype IN ('Founder', 'CXO') THEN v_relationship_tier := 0.75;
    ELSIF v_archetype IN ('Angel', 'Advisor') THEN v_relationship_tier := 0.7;
    ELSE v_relationship_tier := 0.5;
    END IF;

    -- Staleness
    v_staleness_days := EXTRACT(DAY FROM (NOW() - p_detected_at))::INTEGER;
    v_staleness := CASE
        WHEN v_staleness_days <= 2 THEN 0.2
        WHEN v_staleness_days <= 5 THEN 0.5
        WHEN v_staleness_days <= 7 THEN 0.7
        WHEN v_staleness_days <= 10 THEN 0.85
        WHEN v_staleness_days <= 14 THEN 0.95
        ELSE 1.0
    END;

    -- Obligation type
    IF p_obligation_type = 'I_OWE_THEM' THEN
        v_type_weight := CASE p_category
            WHEN 'send_document' THEN 0.9
            WHEN 'reply' THEN 0.85
            WHEN 'introduce' THEN 0.8
            WHEN 'schedule' THEN 0.75
            WHEN 'review' THEN 0.7
            WHEN 'follow_up' THEN 0.65
            ELSE 0.6
        END * 0.8;
    ELSE
        v_type_weight := 0.5;
    END IF;

    -- Source reliability
    v_source_weight := CASE p_detection_method
        WHEN 'explicit' THEN 1.0
        WHEN 'manual' THEN 0.9
        WHEN 'implied' THEN 0.5
        ELSE 0.5
    END;

    -- Recency
    v_recency := CASE
        WHEN v_staleness_days = 0 THEN 1.0
        WHEN v_staleness_days <= 3 THEN 0.8
        WHEN v_staleness_days <= 7 THEN 0.6
        ELSE 0.4
    END;

    RETURN (v_relationship_tier * 0.30) +
           (v_staleness * 0.25) +
           (v_type_weight * 0.20) +
           (v_source_weight * 0.15) +
           (v_recency * 0.10);
END;
$$;
```

---

## Appendix C: Cost Model

### Incremental Cost of Obligations Intelligence

Obligations Intelligence adds processing time to Cindy's existing interaction pipelines. It does NOT create a new agent or a new service.

| Component | Added Cost | Notes |
|-----------|-----------|-------|
| Obligation detection (per interaction) | +$0.005 | ~200 extra tokens for obligation scan per interaction |
| Auto-fulfillment check (per interaction) | +$0.002 | Quick SQL query + match logic |
| Cindy priority computation | $0 | SQL function, runs in-database |
| Megamind overlay (per routed obligation) | +$0.02 | ~5-10 obligations/week routed to Megamind |
| pg_cron staleness check | $0 | In-database, runs hourly |
| CIR propagation | $0 | In-database triggers, existing infrastructure |

**Monthly projection:**

| Scenario | Added Cost | Why |
|----------|-----------|-----|
| Light (5 obligations/day, 1 Megamind route) | ~$3-4/month | Incremental Cindy tokens + occasional Megamind |
| Medium (10 obligations/day, 3 Megamind routes) | ~$5-8/month | More detection + more strategic assessment |
| Heavy (20 obligations/day, 5 Megamind routes) | ~$8-12/month | High-interaction week |

This is incremental cost on top of Cindy's base cost ($10-16/month from cindy-design). Total Cindy cost with obligations: $13-28/month.

---

## Appendix D: Data Flow Summary

```
INTERACTION ARRIVES (any surface)
    |
    v
Cindy standard pipeline (people linking, signal extraction)
    |
    v
OBLIGATION DETECTION (new processing step)
    |-- Scan for commitment patterns (NLP)
    |-- Classify I_OWE / THEY_OWE
    |-- Extract who, what, when
    |-- Dedup check
    |-- Create obligation record
    |-- Compute cindy_priority
    |
    v
AUTO-FULFILLMENT CHECK
    |-- Query existing obligations for same person
    |-- Match fulfillment signals
    |-- Auto-resolve matched obligations
    |
    v
ROUTING (selective)
    |-- Portfolio founder? -> cindy_signal to Megamind
    |-- Active deal? -> cindy_signal to Megamind
    |-- High priority? -> cindy_signal to Megamind
    |-- Otherwise -> Cindy priority only
    |
    v
MEGAMIND (when routed)
    |-- 4-factor strategic priority
    |-- P0 override check
    |-- Write megamind_priority to obligations table
    |
    v
CIR (automatic)
    |-- New obligation -> propagation event
    |-- Status change -> propagation event
    |-- Overdue -> escalation event
    |
    v
INTERFACE (WebFront + CAI)
    |-- /cindy dashboard (Realtime subscription)
    |-- /cindy/feed (chronological suggestions)
    |-- /cindy/insights (analytics)
    |-- Pre-meeting briefs (obligation context per attendee)
    |-- CAI notifications (overdue alerts, P0 overrides)
```
