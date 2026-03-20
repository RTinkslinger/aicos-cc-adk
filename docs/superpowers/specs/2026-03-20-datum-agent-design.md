# Datum Agent — Design Specification
*Created: 2026-03-20*

The Datum Agent is a persistent ClaudeSDKClient that creates and enriches de-duplicated network and company records in Supabase Postgres. It is the entity ingestion layer — the bridge between raw signals (a name on a screenshot, a LinkedIn URL in chat, a company mentioned in a meeting) and clean, canonical database records.

---

## 1. Architecture Overview

### Where It Fits

```
OBSERVATION LAYER (Signal Sources)
  CAI message → "Add Rahul from Composio"
  Screenshot  → Business card photo
  Meeting     → Granola transcript mentions
  Content     → Companies discussed in digest
                 | raw entity signals
                 v
INTELLIGENCE LAYER
  Orchestrator → Datum Agent (via @tool bridge)
                 Datum Agent:
                   1. Parse raw input
                   2. Dedup against existing records
                   3. Web enrich missing fields
                   4. Write canonical record to Postgres
                   5. Create datum requests for unknowns
                 |
                 v
STATE LAYER
  Postgres: network, companies (enriched records)
  Postgres: datum_requests (human-in-the-loop queue)
                 |
                 v
INTERFACE LAYER
  WebFront (digest.wiki): Datum Requests tab
  CAI: "Added Rahul Sharma (Composio, CTO). 2 datum requests pending."
```

### Relationship to Existing Agents

| Agent | Role | Datum Agent Interaction |
|-------|------|------------------------|
| **Orchestrator** | Central coordinator, heartbeat-driven | Routes `datum_*` inbox messages to Datum Agent via @tool bridge |
| **Content Agent** | Content analysis, thesis updates | Produces entity signals as a *byproduct* of content analysis. Does NOT call Datum Agent directly. Instead, writes entity signals to `cai_inbox` with type `datum_entity`, which the Orchestrator routes. |
| **Datum Agent** | Entity ingestion + enrichment | Consumes entity signals, produces canonical records + datum requests |

### Signal Flow

```
Source                    → Inbox Type              → Orchestrator Routes To
─────────────────────────────────────────────────────────────────────────
CAI: "Add Rahul, CTO..."  → datum_person            → Datum Agent
CAI: "Track Composio"     → datum_company           → Datum Agent
Content Agent: entity ref  → datum_entity (batched)  → Datum Agent
Screenshot: business card  → datum_image             → Datum Agent
Granola: meeting mentions  → datum_meeting_entities  → Datum Agent (future)
```

---

## 2. lifecycle.py Integration

The Datum Agent becomes the third managed ClaudeSDKClient in lifecycle.py. Changes follow the established pattern exactly.

### New State in ClientState

```python
class ClientState:
    content_client: Any = None
    content_needs_restart: bool = False
    content_busy: bool = False

    datum_client: Any = None       # NEW
    datum_needs_restart: bool = False  # NEW
    datum_busy: bool = False          # NEW
```

### New @tool Bridge Function

```python
@tool(
    "send_to_datum_agent",
    "Send entity data to the persistent Datum Agent for dedup, enrichment, and storage. "
    "Returns immediately — datum agent works in background. "
    "If datum agent is busy, returns a busy message.",
    {"prompt": str},
)
async def send_to_datum_agent(args: dict[str, Any]) -> dict[str, Any]:
    # Same pattern as send_to_content_agent
```

### Agent Options Builder

```python
DATUM_WORKSPACE = AGENTS_ROOT / "datum"
DATUM_LIVE_LOG = DATUM_WORKSPACE / "live.log"

def build_datum_options():
    from claude_agent_sdk import ClaudeAgentOptions, HookMatcher, ThinkingConfigEnabled

    datum_tool_hook = _make_tool_hook(DATUM_LIVE_LOG)

    return ClaudeAgentOptions(
        model=os.environ.get("AGENT_MODEL", "claude-sonnet-4-6"),
        permission_mode="dontAsk",
        allowed_tools=[
            "Bash", "Read", "Write", "Edit", "Grep", "Glob", "Skill",
            "mcp__web__web_browse", "mcp__web__web_scrape", "mcp__web__web_search",
            "mcp__web__fingerprint", "mcp__web__check_strategy",
            "mcp__web__manage_session", "mcp__web__validate",
        ],
        mcp_servers={"web": {"type": "http", "url": "http://localhost:8001/mcp"}},
        hooks={"PostToolUse": [HookMatcher(hooks=[datum_tool_hook])]},
        setting_sources=["project"],
        thinking=ThinkingConfigEnabled(type="enabled", budget_tokens=5000),
        effort="high",
        max_turns=30,
        max_budget_usd=2.0,
        cwd=str(DATUM_WORKSPACE),
        env={
            "ANTHROPIC_API_KEY": os.environ.get("ANTHROPIC_API_KEY", ""),
            "DATABASE_URL": os.environ.get("DATABASE_URL", ""),
        },
    )
```

### Lifecycle Changes

1. **Orchestrator `allowed_tools`** gains `"mcp__bridge__send_to_datum_agent"`.
2. **Datum client lifecycle** mirrors content client: start in `run_agent()`, stop in `finally`, restart on `COMPACT_NOW`.
3. **Heartbeat routing** in Orchestrator's `HEARTBEAT.md` adds: check inbox for `datum_*` types, route to Datum Agent.
4. **Pre-check `has_work()`** is unchanged — inbox messages already trigger it.
5. **Manifest tracking** adds `"datum"` agent to token tracking.
6. **Session state** adds `datum/state/datum_session.txt` and `datum/state/datum_iteration.txt`.

### Budget Rationale

| Parameter | Value | Why |
|-----------|-------|-----|
| `max_budget_usd` | 2.0 | Lower than Content Agent (5.0) because datum operations are shorter. Higher than Orchestrator (0.50) because web enrichment can be multi-step. |
| `max_turns` | 30 | Typical datum operation: parse (1-2), dedup (2-3), enrich (5-10), write (2-3), report (1). Batch of 5 entities could hit 20-25 turns. |
| `thinking` | 5000 tokens | Dedup decisions require careful reasoning but are not as complex as content analysis (10000). |
| `effort` | high | Entity resolution correctness is more important than speed. |

---

## 3. CLAUDE.md for the Datum Agent

This is the complete system prompt that would live at `mcp-servers/agents/datum/CLAUDE.md`.

```markdown
# Datum Agent — AI CoS Entity Ingestion

You are the **Datum Agent** for Aakash Kumar's AI Chief of Staff system. You are a persistent,
autonomous entity processor running on a droplet. You receive work prompts from the Orchestrator
Agent. Your purpose: take raw entity signals (names, companies, screenshots, URLs) and produce
clean, de-duplicated, fully enriched records in Postgres.

---

## 1. Identity

**Who you work for:** Aakash Kumar — Managing Director at Z47 ($550M fund) AND Managing Director
at DeVC ($60M fund). His network and company database is his competitive advantage.

**Your role:** Entity Ingestion Specialist. You take messy, incomplete entity references and
produce clean canonical records. You are the gatekeeper of data quality for the network and
companies tables.

**You are NOT an assistant.** You are an autonomous agent. You reason, decide, and act via your
instructions, tools, and skills.

**You are persistent.** You remember entities you've processed within this session. Use this to
avoid re-processing and to accumulate context about entity clusters.

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

Web Tools MCP (HTTP server at localhost:8001):

| MCP Tool | Purpose |
|----------|---------|
| `web_browse` | Playwright navigation for LinkedIn, company sites |
| `web_scrape` | Content extraction from URLs |
| `web_search` | Web search for entity enrichment |
| `fingerprint` | Site classification |
| `check_strategy` | UCB bandit strategy lookup |
| `manage_session` | Session state management |
| `validate` | Content quality scoring |

---

## 3. Database Access

**Method:** Bash + psql with `$DATABASE_URL`. No Python DB modules.

**Schema reference:** Load `skills/data/postgres-schema.md` for base schemas. Load
`skills/data/datum-schema.md` for datum-specific tables and enrichment columns.

**Tables you read/write:**

| Table | Access | Purpose |
|-------|--------|---------|
| `network` | Read + Write | Person records |
| `companies` | Read + Write | Company records |
| `datum_requests` | Write | Fields you cannot fill |
| `notifications` | Write | Status updates to CAI |

---

## 4. Processing Flow

When the Orchestrator sends you an entity signal:

### Step 1: Parse Input

Extract structured fields from raw input. Input types:

| Input Type | Parsing Strategy |
|------------|-----------------|
| Text ("Rahul Sharma, CTO at Composio") | NLP extraction: name, role, company |
| URL (LinkedIn profile) | Fetch + extract structured data |
| URL (company website) | Fetch + extract company info |
| Image (business card, screenshot) | Describe visible text, extract fields |
| Batch (list of entities from content) | Parse each, process sequentially |

After parsing, you have a **candidate record** with partial fields.

### Step 2: Dedup Check

Run the 3-tier dedup algorithm (see Dedup section in skills). This produces one of:

| Result | Action |
|--------|--------|
| **Exact match** | Merge new data into existing record (skip nulls, append notes) |
| **Fuzzy match (single)** | Merge with confidence note. If confidence < 0.85, create datum request asking user to confirm. |
| **Fuzzy match (multiple)** | Create datum request listing candidates, ask user to pick |
| **No match** | Create new record |

### Step 3: Web Enrichment

For every field that is NULL after parsing:

1. If LinkedIn URL is available: scrape LinkedIn (via web_browse with session)
2. If company domain is available: scrape company website
3. If name + company known: web_search for "[name] [company] [role]"
4. Apply rate limiting: max 3 web calls per entity, max 10 per batch

**Do NOT enrich fields that are already filled.** Only fill NULLs.

### Step 4: Write Record

```sql
-- New person
INSERT INTO network (name, company, role, linkedin_url, email, city, archetype,
                     source, enrichment_status, created_at, updated_at)
VALUES (...) RETURNING id;

-- Merge into existing person
UPDATE network SET
  role = COALESCE($new_role, role),
  linkedin_url = COALESCE($new_linkedin, linkedin_url),
  email = COALESCE($new_email, email),
  ...
  enrichment_status = 'enriched',
  updated_at = NOW()
WHERE id = $id;
```

### Step 5: Create Datum Requests

For every field that remains NULL after web enrichment:

```sql
INSERT INTO datum_requests (entity_type, entity_id, field_name, source_context, status, created_at)
VALUES ('person', 42, 'email', 'Parsed from CAI message: "Add Rahul from Composio"', 'pending', NOW());
```

### Step 6: Report Back

```
ACK: Processed 1 entity.
- Created person: Rahul Sharma (Composio, CTO). ID=42.
- Filled: name, company, role, linkedin_url, city (5/13 fields).
- Web enriched: linkedin_url, city (2 fields via LinkedIn scrape).
- Datum requests: email, phone, archetype (3 pending).
```

---

## 5. Dedup Algorithm

Load skill: `skills/data/dedup-algorithm.md`

### For Persons (type: "person")

Tier 1 — LinkedIn URL match (strongest durable key):
```sql
SELECT id, name, company, role FROM network
WHERE linkedin_url = $candidate_linkedin_url;
```
If match: MERGE. Done.

Tier 2 — Exact name + company match:
```sql
SELECT id, name, company, role FROM network
WHERE LOWER(name) = LOWER($candidate_name)
  AND LOWER(company) = LOWER($candidate_company);
```
If match: MERGE. Done.

Tier 3 — Fuzzy name match (embedding similarity):
```sql
SELECT id, name, company, role,
       1 - (embedding <=> $candidate_embedding) as similarity
FROM network
WHERE 1 - (embedding <=> $candidate_embedding) > 0.80
ORDER BY similarity DESC
LIMIT 5;
```
If single match above 0.90: auto-merge with confidence note.
If single match 0.80-0.90: create datum request asking user to confirm merge.
If multiple matches above 0.80: create datum request listing all candidates.
If no match: CREATE new record.

### For Companies (type: "company")

Tier 1 — Domain match (strongest durable key):
```sql
SELECT id, name, domain, sector, stage FROM companies
WHERE domain = $candidate_domain;
```

Tier 2 — Exact name match:
```sql
SELECT id, name, domain, sector, stage FROM companies
WHERE LOWER(name) = LOWER($candidate_name);
```

Tier 3 — Fuzzy name match (embedding similarity):
Same pattern as person, with 0.85 threshold (company names are less ambiguous).

---

## 6. Enrichment Priorities

Not all fields are equally important. Enrichment effort should follow this priority:

### Person Fields (by priority)

| Priority | Fields | Why |
|----------|--------|-----|
| **P0** | name, company, role | Identity. Without these, the record is useless. |
| **P1** | linkedin_url, archetype | Durable key + classification. LinkedIn URL prevents future duplicates. |
| **P2** | email, city | Contact + geographic overlap scoring. |
| **P3** | phone, ids_notes, source | Nice-to-have. Don't burn web calls on these. |

### Company Fields (by priority)

| Priority | Fields | Why |
|----------|--------|-----|
| **P0** | name, domain | Identity. Domain is the durable key. |
| **P1** | sector, stage, description | Classification. Enables thesis matching. |
| **P2** | thesis_thread_ids, pipeline_stage | Investment context. |
| **P3** | aliases, ids_trail | Enrichment. Low urgency. |

**Rule:** Spend web enrichment budget on P0 and P1 fields. Create datum requests for P2
and P3 fields that web enrichment cannot fill.

---

## 7. Acknowledgment Protocol

Every response MUST end with a structured ACK:

```
ACK: [summary]
- [entity 1]: [action] [details]
- [entity 2]: [action] [details]
- Datum requests: [N] pending
```

---

## 8. State Tracking

| File | When to Write |
|------|---------------|
| `state/datum_last_log.txt` | After every prompt |
| `state/datum_iteration.txt` | Incremented each prompt |

### Session Compaction
When prompt includes "COMPACTION REQUIRED":
1. Read `CHECKPOINT_FORMAT.md`
2. Write checkpoint to `state/datum_checkpoint.md`
3. End response with: **COMPACT_NOW**

### Session Restart
If `state/datum_checkpoint.md` exists:
1. Read it, absorb state, delete it
2. Log: `resumed from checkpoint, session #N`

---

## 9. Anti-Patterns (NEVER Do These)

1. **Never create duplicate records.** Run the full dedup algorithm before every INSERT.
2. **Never overwrite existing data with NULLs.** Use COALESCE for merges.
3. **Never skip datum requests.** If a field is unknown after enrichment, create a request.
4. **Never import Python DB modules.** Use Bash + psql exclusively.
5. **Never skip the ACK.** Every response must include structured acknowledgment.
6. **Never web-enrich already-filled fields.** Only fill NULLs.
7. **Never exceed rate limits.** Max 3 web calls per entity, 10 per batch.
8. **Never auto-merge fuzzy matches below 0.90 confidence.** Create a datum request instead.
9. **Never set archetype without evidence.** Use the 13-archetype taxonomy from the Network DB
   schema. If unsure, create a datum request.
10. **Never modify thesis_threads or actions_queue.** That is Content Agent's territory.
11. **Never skip state tracking.** Always write datum_last_log.txt.
12. **Never ignore COMPACTION REQUIRED.** Write checkpoint + COMPACT_NOW immediately.
```

---

## 4. Database Schema

### New Table: datum_requests

The human-in-the-loop queue for data quality. When the Datum Agent cannot fill a field, it creates a datum request. Users answer on WebFront. Answered requests trigger field updates.

```sql
CREATE TABLE datum_requests (
    id SERIAL PRIMARY KEY,

    -- What entity this request is about
    entity_type TEXT NOT NULL,
        -- 'person' or 'company'
    entity_id INTEGER NOT NULL,
        -- FK to network.id or companies.id

    -- What field needs filling
    field_name TEXT NOT NULL,
        -- Column name on the target table (e.g., 'email', 'sector')

    -- Context for the user
    source_context TEXT,
        -- Where this entity came from: "CAI message: Add Rahul from Composio"
    current_value TEXT,
        -- Current value of the field (NULL if empty, shows existing value for correction requests)
    suggested_value TEXT,
        -- Agent's best guess if it has one but is not confident enough to write
    suggestion_confidence REAL,
        -- 0.0-1.0. If > 0.9, agent would have written it directly.
    suggestion_source TEXT,
        -- Where the suggestion came from: "LinkedIn scrape", "web search", "name inference"

    -- Dedup-specific fields (for merge confirmation requests)
    merge_candidate_ids INTEGER[],
        -- If this is a "confirm merge" request, the candidate record IDs
    merge_type TEXT,
        -- 'confirm_merge' | 'pick_match' | 'fill_field'

    -- Lifecycle
    status TEXT NOT NULL DEFAULT 'pending',
        -- pending | answered | skipped | expired
    answer TEXT,
        -- The user's answer (written by WebFront Server Action)
    answered_by TEXT,
        -- 'webfront' | 'cai' | 'auto'
    answered_at TIMESTAMPTZ,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for WebFront queries (pending requests, sorted by recency)
CREATE INDEX idx_datum_requests_status ON datum_requests(status) WHERE status = 'pending';

-- Index for per-entity lookups
CREATE INDEX idx_datum_requests_entity ON datum_requests(entity_type, entity_id);
```

### ALTER TABLE: network

The `network` table exists in Postgres (schema exists, sync deferred per DATA-ARCHITECTURE.md). It needs enrichment columns for the Datum Agent to work effectively.

```sql
-- Enrichment tracking
ALTER TABLE network ADD COLUMN IF NOT EXISTS enrichment_status TEXT DEFAULT 'raw';
    -- raw | partial | enriched | verified
ALTER TABLE network ADD COLUMN IF NOT EXISTS enrichment_source TEXT;
    -- 'datum_agent', 'manual', 'sync'
ALTER TABLE network ADD COLUMN IF NOT EXISTS last_enriched_at TIMESTAMPTZ;

-- Dedup support
ALTER TABLE network ADD COLUMN IF NOT EXISTS linkedin_url TEXT UNIQUE;
    -- Strongest durable key for persons. UNIQUE constraint prevents duplicates at DB level.
ALTER TABLE network ADD COLUMN IF NOT EXISTS aliases TEXT[];
    -- Alternative names, nicknames, transliterations

-- Embedding column for semantic dedup (populated by Supabase Auto Embeddings)
ALTER TABLE network ADD COLUMN IF NOT EXISTS embedding vector(1024);
    -- Voyage AI voyage-3.5, 1024 dimensions. Auto-populated by trigger.
    -- Agent writes name+company+role to embedding_input, vector appears automatically.
ALTER TABLE network ADD COLUMN IF NOT EXISTS embedding_input TEXT;
    -- The text that gets embedded. Format: "{name} | {company} | {role} | {city}"

-- Source tracking
ALTER TABLE network ADD COLUMN IF NOT EXISTS datum_source TEXT;
    -- Where this record originated: 'cai_message', 'content_pipeline', 'meeting', 'manual'
ALTER TABLE network ADD COLUMN IF NOT EXISTS datum_created_at TIMESTAMPTZ;
    -- When the Datum Agent first created/touched this record
```

### ALTER TABLE: companies

Same enrichment pattern for companies.

```sql
-- Enrichment tracking
ALTER TABLE companies ADD COLUMN IF NOT EXISTS enrichment_status TEXT DEFAULT 'raw';
ALTER TABLE companies ADD COLUMN IF NOT EXISTS enrichment_source TEXT;
ALTER TABLE companies ADD COLUMN IF NOT EXISTS last_enriched_at TIMESTAMPTZ;

-- Dedup support
ALTER TABLE companies ADD COLUMN IF NOT EXISTS domain TEXT UNIQUE;
    -- Strongest durable key for companies.
ALTER TABLE companies ADD COLUMN IF NOT EXISTS aliases TEXT[];

-- Embedding column for semantic dedup
ALTER TABLE companies ADD COLUMN IF NOT EXISTS embedding vector(1024);
ALTER TABLE companies ADD COLUMN IF NOT EXISTS embedding_input TEXT;
    -- Format: "{name} | {domain} | {sector} | {description}"

-- Source tracking
ALTER TABLE companies ADD COLUMN IF NOT EXISTS datum_source TEXT;
ALTER TABLE companies ADD COLUMN IF NOT EXISTS datum_created_at TIMESTAMPTZ;
```

### Auto Embeddings Setup

Following the existing Supabase Auto Embeddings pattern (DB trigger -> pgmq -> pg_cron -> Edge Function -> Voyage AI -> vector column):

1. Create DB trigger on `network` and `companies` that fires on INSERT or UPDATE of `embedding_input`
2. Trigger enqueues a message to pgmq
3. pg_cron picks up the message, calls the Edge Function
4. Edge Function calls Voyage AI `voyage-3.5` (1024-dim)
5. Result written back to `embedding` column

This is the same pipeline already running for `content_digests` and `thesis_threads`. Configuration is a Supabase dashboard operation, not agent code.

---

## 5. Dedup Algorithm (Pseudocode)

```
FUNCTION resolve_entity(candidate: CandidateRecord) -> Resolution:
    """
    Returns: { action: 'create' | 'merge' | 'ask_user', target_id?: int, confidence: float }
    """

    IF candidate.type == 'person':
        # Tier 1: LinkedIn URL (exact, strongest)
        IF candidate.linkedin_url IS NOT NULL:
            match = query("SELECT * FROM network WHERE linkedin_url = $1", candidate.linkedin_url)
            IF match:
                RETURN { action: 'merge', target_id: match.id, confidence: 1.0 }

        # Tier 2: Exact name + company
        IF candidate.name AND candidate.company:
            match = query("""
                SELECT * FROM network
                WHERE LOWER(name) = LOWER($1)
                  AND LOWER(company) = LOWER($2)
            """, candidate.name, candidate.company)
            IF match:
                RETURN { action: 'merge', target_id: match.id, confidence: 0.95 }

        # Tier 3: Embedding similarity
        IF candidate.embedding IS NOT NULL:
            matches = query("""
                SELECT id, name, company, role,
                       1 - (embedding <=> $1) as similarity
                FROM network
                WHERE 1 - (embedding <=> $1) > 0.80
                ORDER BY similarity DESC
                LIMIT 5
            """, candidate.embedding)

            IF len(matches) == 0:
                RETURN { action: 'create', confidence: 1.0 }
            ELIF len(matches) == 1 AND matches[0].similarity > 0.90:
                RETURN { action: 'merge', target_id: matches[0].id, confidence: matches[0].similarity }
            ELIF len(matches) == 1 AND matches[0].similarity > 0.80:
                RETURN { action: 'ask_user', candidates: [matches[0].id], confidence: matches[0].similarity }
            ELSE:
                RETURN { action: 'ask_user', candidates: [m.id for m in matches], confidence: max(m.similarity for m in matches) }

        # Tier 4: Name-only fuzzy (last resort, lower confidence)
        matches = query("""
            SELECT * FROM network WHERE LOWER(name) = LOWER($1)
        """, candidate.name)
        IF len(matches) == 1:
            RETURN { action: 'ask_user', candidates: [matches[0].id], confidence: 0.70 }
        ELIF len(matches) > 1:
            RETURN { action: 'ask_user', candidates: [m.id for m in matches], confidence: 0.50 }

        RETURN { action: 'create', confidence: 1.0 }

    ELIF candidate.type == 'company':
        # Tier 1: Domain match (exact, strongest)
        IF candidate.domain IS NOT NULL:
            match = query("SELECT * FROM companies WHERE domain = $1", candidate.domain)
            IF match:
                RETURN { action: 'merge', target_id: match.id, confidence: 1.0 }

        # Tier 2: Exact name match
        match = query("SELECT * FROM companies WHERE LOWER(name) = LOWER($1)", candidate.name)
        IF match:
            RETURN { action: 'merge', target_id: match.id, confidence: 0.95 }

        # Tier 3: Embedding similarity (higher threshold for companies: 0.85)
        # Same pattern as person but with 0.85 threshold
        ...

        RETURN { action: 'create', confidence: 1.0 }
```

### Merge Logic

```
FUNCTION merge_record(existing_id: int, new_data: dict, entity_type: str):
    """
    Merge new data into existing record. COALESCE pattern: never overwrite
    existing non-NULL values with NULL. Only fill gaps or append to array fields.
    """

    FOR field, new_value IN new_data.items():
        IF new_value IS NULL:
            SKIP  # Never write NULLs

        existing_value = get_field(existing_id, field)

        IF existing_value IS NULL:
            # Gap fill: write the new value
            update_field(existing_id, field, new_value)
        ELIF field IN array_fields:  # aliases, etc.
            # Append unique values
            update_array_append(existing_id, field, new_value)
        ELSE:
            # Field already has value. If new value differs, create datum request
            # asking user which is correct.
            IF new_value != existing_value:
                create_datum_request(
                    entity_type=entity_type,
                    entity_id=existing_id,
                    field_name=field,
                    current_value=existing_value,
                    suggested_value=new_value,
                    merge_type='fill_field',
                    source_context=f"New value '{new_value}' differs from existing '{existing_value}'"
                )

    # Update enrichment metadata
    update_field(existing_id, 'enrichment_status', compute_enrichment_status(existing_id))
    update_field(existing_id, 'last_enriched_at', NOW())
    update_field(existing_id, 'updated_at', NOW())

    # Refresh embedding_input for re-embedding
    refresh_embedding_input(existing_id, entity_type)
```

### Embedding Input Construction

```
FUNCTION compute_embedding_input(record, entity_type: str) -> str:
    IF entity_type == 'person':
        parts = [record.name, record.company, record.role, record.city]
        RETURN " | ".join(p for p in parts if p is not None)
    ELIF entity_type == 'company':
        parts = [record.name, record.domain, record.sector, record.description]
        RETURN " | ".join(p for p in parts if p is not None)
```

---

## 6. Web Enrichment Strategy

### Decision Tree

```
FUNCTION enrich_entity(candidate, null_fields: list) -> dict:
    """
    Attempt to fill NULL fields via web research.
    Budget: max 3 web calls per entity, max 10 per batch.
    """
    enriched = {}
    calls_made = 0
    MAX_CALLS = 3

    # Strategy 1: LinkedIn (highest value per call)
    IF 'linkedin_url' IN candidate AND candidate.linkedin_url:
        IF calls_made < MAX_CALLS AND has_unfilled_person_fields(null_fields):
            result = scrape_linkedin(candidate.linkedin_url)
            enriched.update(extract_person_fields(result))
            calls_made += 1

    ELIF candidate.type == 'person' AND candidate.name AND candidate.company:
        # Try to FIND LinkedIn URL
        IF calls_made < MAX_CALLS:
            search_result = web_search(f"{candidate.name} {candidate.company} LinkedIn")
            linkedin_url = extract_linkedin_url(search_result)
            IF linkedin_url:
                enriched['linkedin_url'] = linkedin_url
                # Now scrape it
                IF calls_made < MAX_CALLS:
                    result = scrape_linkedin(linkedin_url)
                    enriched.update(extract_person_fields(result))
                    calls_made += 1
            calls_made += 1

    # Strategy 2: Company website (for company entities or person's company)
    IF candidate.type == 'company' AND candidate.domain:
        IF calls_made < MAX_CALLS AND has_unfilled_company_fields(null_fields):
            result = web_scrape(f"https://{candidate.domain}")
            enriched.update(extract_company_fields(result))
            calls_made += 1

    # Strategy 3: General web search (last resort)
    remaining_nulls = [f for f in null_fields if f not in enriched and f in P0_P1_fields]
    IF remaining_nulls AND calls_made < MAX_CALLS:
        query = construct_search_query(candidate, remaining_nulls)
        result = web_search(query)
        enriched.update(extract_fields_from_search(result, remaining_nulls))
        calls_made += 1

    RETURN enriched
```

### LinkedIn Scraping Constraints

- LinkedIn requires authenticated sessions. Use `manage_session` to load stored session state.
- If session expired (login wall detected), do NOT attempt login. Log "LinkedIn session expired" and skip LinkedIn enrichment.
- Rate limit: max 1 LinkedIn scrape per 30 seconds (respect `check_strategy` guidance).
- Extract: name, headline (role + company), location (city), about section, current experience.
- Do NOT extract: connections count, endorsements, or any data that requires scrolling.

### Enrichment Status Computation

```
FUNCTION compute_enrichment_status(entity_id, entity_type) -> str:
    IF entity_type == 'person':
        required_fields = ['name', 'company', 'role']
        important_fields = ['linkedin_url', 'archetype', 'email', 'city']
    ELSE:
        required_fields = ['name', 'domain']
        important_fields = ['sector', 'stage', 'description']

    filled_required = count_non_null(entity_id, required_fields)
    filled_important = count_non_null(entity_id, important_fields)

    IF filled_required == len(required_fields) AND filled_important == len(important_fields):
        RETURN 'enriched'
    ELIF filled_required == len(required_fields):
        RETURN 'partial'
    ELSE:
        RETURN 'raw'
```

---

## 7. WebFront Integration (Datum Requests Tab)

### User Experience

A new tab on WebFront (digest.wiki) at route `/datum`. Displays pending datum requests grouped by entity, with inline answer UI.

### Page Layout

```
/datum

┌──────────────────────────────────────────────────────────────┐
│  Datum Requests                                    [3 pending]│
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌── Rahul Sharma (Composio) ─── Person ─── 2 requests ──┐  │
│  │                                                        │  │
│  │  EMAIL                                                 │  │
│  │  Source: "CAI message: Add Rahul from Composio"        │  │
│  │  Suggestion: rahul@composio.dev (confidence: 0.72)     │  │
│  │  ┌─────────────────────────┐ ┌──────┐ ┌──────┐        │  │
│  │  │ Type answer...          │ │ Save │ │ Skip │        │  │
│  │  └─────────────────────────┘ └──────┘ └──────┘        │  │
│  │                                                        │  │
│  │  ARCHETYPE                                             │  │
│  │  Source: "Founder? CXO? Role is CTO at Composio"      │  │
│  │  Suggestion: Founder (confidence: 0.65)                │  │
│  │  ┌──────────────────────────────────────┐              │  │
│  │  │ [Founder] [CXO] [Operator] [Other]  │ [Skip]      │  │
│  │  └──────────────────────────────────────┘              │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌── Confirm Merge ──────────────────────────────────────┐  │
│  │                                                        │  │
│  │  "Rahul S." from content pipeline might be the same    │  │
│  │  as "Rahul Sharma" (ID=42). Similarity: 0.87          │  │
│  │                                                        │  │
│  │  Record A: Rahul S., ?, ?                              │  │
│  │  Record B: Rahul Sharma, Composio, CTO                 │  │
│  │                                                        │  │
│  │  ┌─────────┐ ┌──────────────┐ ┌──────────────┐        │  │
│  │  │ Merge   │ │ Keep Separate │ │ Skip         │        │  │
│  │  └─────────┘ └──────────────┘ └──────────────┘        │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  ─── Answered (7) ─── Skipped (2) ──────────────────────── │
└──────────────────────────────────────────────────────────────┘
```

### Implementation (Server Components + Server Actions)

**Read data:** `@supabase/ssr` PostgREST query:
```sql
SELECT dr.*, n.name as entity_name, n.company as entity_company
FROM datum_requests dr
LEFT JOIN network n ON dr.entity_type = 'person' AND dr.entity_id = n.id
WHERE dr.status = 'pending'
ORDER BY dr.created_at DESC;
```

**Answer a request (Server Action):**
```typescript
async function answerDatumRequest(requestId: number, answer: string) {
  // 1. Update datum_request
  await supabase
    .from('datum_requests')
    .update({
      status: 'answered',
      answer: answer,
      answered_by: 'webfront',
      answered_at: new Date().toISOString(),
    })
    .eq('id', requestId);

  // 2. Update the entity field
  const request = await supabase.from('datum_requests').select('*').eq('id', requestId).single();
  const table = request.entity_type === 'person' ? 'network' : 'companies';
  await supabase
    .from(table)
    .update({ [request.field_name]: answer, updated_at: new Date().toISOString() })
    .eq('id', request.entity_id);
}
```

**Merge confirmation (Server Action):**
```typescript
async function confirmMerge(requestId: number, action: 'merge' | 'keep_separate') {
  const request = await supabase.from('datum_requests').select('*').eq('id', requestId).single();

  if (action === 'merge') {
    // Merge records: copy non-null fields from candidate to target
    // Delete the duplicate record
    // Log the merge in change_events
  } else {
    // Mark as "keep separate" — both records confirmed distinct
  }

  await supabase
    .from('datum_requests')
    .update({ status: 'answered', answer: action, answered_by: 'webfront', answered_at: new Date().toISOString() })
    .eq('id', requestId);
}
```

**Realtime:** Supabase Realtime subscription on `datum_requests` table for live updates when the Datum Agent creates new requests while user is viewing the page.

### WebFront Phase Integration

Datum Requests tab would logically fit as **Phase 1.5** or early **Phase 2** in the WebFront roadmap (after Action Triage, before Thesis Interaction). It depends on the same Supabase infrastructure (PostgREST + Server Actions) that Phase 1 establishes.

---

## 8. Error Handling + Edge Cases

### Input Errors

| Error | Handling |
|-------|----------|
| Completely unstructured input ("check this out") | Write notification: "Could not extract entity from input. Please provide a name, company, or URL." |
| Image with no readable text | Write notification: "Could not extract text from image." |
| Invalid URL | Attempt fetch once. If 404/timeout, write notification with error. Create record with available fields only. |
| Empty input | Log and skip. Do not create empty records. |

### Dedup Edge Cases

| Edge Case | Handling |
|-----------|----------|
| Same person, different companies (job change) | If LinkedIn URL matches, MERGE and update company/role. If name-only match, ask user. |
| Transliterated names ("Rahul" vs "Raahul") | Embedding similarity should catch these. Threshold at 0.80 allows for spelling variations. |
| Company name variations ("Z47" vs "Z47 fka Matrix Partners") | Aliases array accumulates variations. Embedding similarity handles fuzzy matching. Domain match is the tie-breaker. |
| Duplicate datum requests | Before creating a datum request, check if one already exists for the same entity_id + field_name + status='pending'. If so, skip. |
| User answers conflict with agent suggestion | User answer always wins. Write user's answer to the entity field. |
| Batch contains duplicates | Process sequentially. Second occurrence will match the first (just-created) record and merge. |

### Web Enrichment Errors

| Error | Handling |
|-------|----------|
| LinkedIn session expired | Log "LinkedIn session expired". Skip LinkedIn enrichment. Create datum requests for fields that would have come from LinkedIn. Write notification suggesting session refresh. |
| Rate limited by website | Log the rate limit. Skip enrichment for this entity. Retry on next batch (if same entity shows up again). |
| Web search returns irrelevant results | Validate results against candidate fields. If name/company don't match, discard. Better to leave a field NULL than fill it wrong. |
| Firecrawl/Playwright failure | Try one alternative method (Jina Reader / curl). If second attempt fails, skip and create datum requests. |

### Database Errors

| Error | Handling |
|-------|----------|
| psql connection failure | Retry once after 2 seconds. If still failing, end with ACK error and request restart. |
| UNIQUE constraint violation (linkedin_url, domain) | This IS a dedup detection. Fetch the existing record and merge. |
| Foreign key violation | Log error. Entity may have been deleted between dedup check and write. Skip and report. |

### Capacity Protection

| Scenario | Guard |
|----------|-------|
| Batch of 50+ entities in one message | Process first 20, write notification "Batch too large. Processed 20/50. Send remaining in next message." |
| Web enrichment taking too long | Timeout per web call: 30 seconds. Total enrichment budget per prompt: 5 minutes. After timeout, proceed with partial enrichment. |
| Embedding not yet populated (new record) | Dedup Tier 3 (embedding similarity) silently skips if embedding is NULL. Falls through to Tier 4 or CREATE. |

---

## 9. Cost Estimate

### Per-Entity Token Budget

| Operation | Input Tokens | Output Tokens | Notes |
|-----------|-------------|---------------|-------|
| Parse input | ~200 | ~100 | Text extraction from raw signal |
| Dedup queries (3 tiers) | ~500 | ~300 | psql commands + result interpretation |
| Web enrichment (avg 2 calls) | ~2000 | ~500 | Web content is bulky; agent must read + extract |
| Write record + datum requests | ~300 | ~400 | SQL construction + ACK |
| **Total per entity** | **~3,000** | **~1,300** | |

### Cost Per Operation

At Sonnet 4 pricing ($3/M input, $15/M output):

| Operation | Cost |
|-----------|------|
| Single entity (no web enrichment) | ~$0.005 |
| Single entity (with web enrichment) | ~$0.03 |
| Batch of 5 entities (mixed) | ~$0.10 |
| Batch of 10 entities (mixed) | ~$0.18 |

### Monthly Projection

| Scenario | Volume | Cost |
|----------|--------|------|
| Light usage (5 entities/day) | ~150/month | ~$3-5/month |
| Medium usage (15 entities/day) | ~450/month | ~$8-15/month |
| Heavy usage (30 entities/day, post-meeting batch) | ~900/month | ~$15-30/month |

### Web Tools MCP Costs (External APIs)

| API | Cost | Budget |
|-----|------|--------|
| Firecrawl (scraping) | ~$0.001/page | Minimal |
| Web search | ~$0.01/search | ~$3-5/month at medium usage |
| Voyage AI embeddings | ~$0.0001/embed | Negligible (Supabase Auto Embeddings) |

**Total estimated cost: $10-20/month at medium usage.** Well within the agent budget constraints.

---

## 10. Implementation Plan

### Phase 0: Infrastructure (Pre-requisite)
**Estimated effort:** S (1-3 hours)
**Dependencies:** None

- [ ] Run database migrations (datum_requests table, ALTER TABLEs on network and companies)
- [ ] Configure Auto Embeddings triggers for network and companies tables (Supabase dashboard)
- [ ] Verify embedding pipeline works: insert test record, confirm vector appears
- [ ] Create `mcp-servers/agents/datum/` directory structure:
  ```
  datum/
    CLAUDE.md
    HEARTBEAT.md           (not needed — Datum Agent is on-demand, not heartbeat-driven)
    CHECKPOINT_FORMAT.md
    state/
      datum_session.txt
      datum_iteration.txt
    live.log
  ```

### Phase 1: Core Agent (MVP)
**Estimated effort:** M (3-8 hours)
**Dependencies:** Phase 0

- [ ] Write `datum/CLAUDE.md` (full system prompt from Section 3)
- [ ] Write `skills/data/datum-schema.md` (datum_requests table schema + query patterns)
- [ ] Write `skills/data/dedup-algorithm.md` (dedup pseudocode as a loadable skill)
- [ ] Modify `lifecycle.py`: add DatumAgent ClientState, bridge tool, options builder, lifecycle hooks
- [ ] Modify `orchestrator/HEARTBEAT.md`: add datum_* inbox type routing
- [ ] Test: send a "datum_person" inbox message, verify record created in network table
- [ ] Test: send duplicate, verify dedup works (exact name match)
- [ ] Test: verify datum_requests created for unfilled fields

### Phase 2: Web Enrichment
**Estimated effort:** M (3-8 hours)
**Dependencies:** Phase 1

- [ ] Add Web Tools MCP to Datum Agent options (already specified in Section 2)
- [ ] Implement LinkedIn scraping strategy (session management, field extraction)
- [ ] Implement company website scraping (domain -> about page -> sector/description)
- [ ] Implement general web search enrichment (name + company -> structured data)
- [ ] Test: send entity with LinkedIn URL, verify enrichment fills fields
- [ ] Test: rate limiting (send 5 entities, verify max 10 web calls total)
- [ ] Test: LinkedIn session expired handling

### Phase 3: Embedding Dedup (Fuzzy Matching)
**Estimated effort:** S (1-3 hours)
**Dependencies:** Phase 0 (Auto Embeddings working), Phase 1

- [ ] Verify embeddings are being generated for network and companies records
- [ ] Test Tier 3 dedup: insert similar-but-not-identical entity, verify fuzzy match
- [ ] Test confidence thresholds: >0.90 auto-merge, 0.80-0.90 ask user, <0.80 create new
- [ ] Test multi-match scenario: verify datum request with multiple candidates

### Phase 4: WebFront Datum Requests Tab
**Estimated effort:** M (3-8 hours)
**Dependencies:** WebFront Phase 1 (Supabase connection established), Phase 1

- [ ] Create `/datum` route in aicos-digests Next.js app
- [ ] Server Component: read pending datum_requests with entity context
- [ ] Server Action: answer a datum request (update entity field + mark answered)
- [ ] Server Action: confirm/reject merge (merge records or keep separate)
- [ ] Server Action: skip a datum request
- [ ] Supabase Realtime subscription for live updates
- [ ] Test: create datum request via psql, verify it appears on WebFront
- [ ] Test: answer request on WebFront, verify entity field updated

### Phase 5: Content Pipeline Integration
**Estimated effort:** S (1-3 hours)
**Dependencies:** Phase 1

- [ ] Modify Content Agent: when content analysis identifies companies/people, write `datum_entity` messages to cai_inbox instead of (or in addition to) inline entity references
- [ ] Define `datum_entity` inbox message format:
  ```json
  {
    "type": "datum_entity",
    "content": "Entity batch from content analysis",
    "metadata": {
      "entities": [
        { "type": "company", "name": "Composio", "context": "Mentioned in AI agent tooling discussion" },
        { "type": "person", "name": "Karan Vaidya", "company": "Composio", "role": "CEO", "context": "Speaker in interview" }
      ],
      "source_digest_slug": "composio-agent-tooling-2026"
    }
  }
  ```
- [ ] Test: content pipeline processes a video mentioning companies, verify datum entities created

---

## 11. Autonomous Action Execution

### The Problem

Today, the Content Agent writes ALL proposed actions to the `actions_queue` — regardless of whether they require human judgment. Thesis evidence review, company research, competitive landscape mapping, and similar "agent work" gets surfaced alongside "call this founder" and "attend this meeting." This creates noise: Aakash sees 10 proposed actions, 6 of which could have been done autonomously by an agent.

### The Boundary: Human Judgment vs. Agent-Executable

The dividing line is whether the action requires Aakash's **relationships, physical presence, or strategic judgment** (human) vs. whether it requires **research, data gathering, or database maintenance** (agent).

| Action Type | Requires | Who Executes | Example |
|------------|----------|--------------|---------|
| Meeting/Outreach | Relationships, presence | **Aakash** | "Call Rahul to discuss Series A" |
| Follow-on Eval | Strategic investment judgment | **Aakash** | "Evaluate follow-on for Composio" |
| Portfolio Check-in | Relationship maintenance | **Aakash** | "Schedule quarterly check-in with Composio team" |
| Research | Web research, data gathering | **Agent** | "Research Composio's competitive landscape" |
| Thesis Update | Evidence assessment | **Agent** | "Review new evidence for Agentic AI thesis" |
| Content Follow-up | Content analysis | **Agent** | "Analyze Composio's latest blog post series" |
| Pipeline Action | Data operations | **Agent** | "Add Composio founders to network DB" |

### How It Works

The Datum Agent does NOT execute actions directly. Instead, the system gains a new **action execution loop** that is conceptually separate from the Datum Agent but shares infrastructure. Here is the design.

#### 1. Content Agent Tags Actions at Creation

When the Content Agent proposes an action, it sets `assigned_to`:
- `'Aakash'` for human-judgment actions
- `'Agent'` for agent-executable actions

This already exists in the Content Agent's CLAUDE.md (Section 9, Assignment Rules). The change is making the system ACT on the assignment.

#### 2. New Inbox Message Type: `execute_actions`

The Orchestrator periodically (every heartbeat where work is detected) checks for agent-assigned actions:

```sql
SELECT id, action, action_type, reasoning, thesis_connection, source_content
FROM actions_queue
WHERE assigned_to = 'Agent'
  AND status = 'Proposed'
ORDER BY CASE priority
  WHEN 'P0 - Act Now' THEN 1
  WHEN 'P1 - This Week' THEN 2
  WHEN 'P2 - This Month' THEN 3
  ELSE 4 END
LIMIT 5;
```

If any exist, the Orchestrator routes them to the appropriate agent:
- `action_type IN ('Research', 'Content Follow-up')` -> Content Agent (via `send_to_content_agent`)
- `action_type IN ('Pipeline Action', 'Thesis Update')` -> Datum Agent (via `send_to_datum_agent`) OR Content Agent, depending on the specific action
- Entity-related Pipeline Actions (adding people/companies) -> Datum Agent

#### 3. Agent Executes and Reports

The receiving agent:
1. Marks the action as `In Progress`:
   ```sql
   UPDATE actions_queue SET status = 'In Progress', updated_at = NOW() WHERE id = $id;
   ```
2. Executes the work (research, data gathering, thesis evidence review, entity creation)
3. Writes results:
   - Research results -> `notifications` table
   - Thesis evidence -> `thesis_threads` table (append to evidence_for/evidence_against)
   - Entity creation -> `network` or `companies` table (via Datum Agent's normal flow)
4. Marks the action as `Done`:
   ```sql
   UPDATE actions_queue SET status = 'Done', updated_at = NOW() WHERE id = $id;
   ```
5. Writes a notification summarizing what was done

#### 4. Escalation Rules (Agent -> Human)

Even agent-assigned actions sometimes need human judgment. The agent MUST escalate (change `assigned_to` to `'Aakash'` and keep status as `Proposed`) when:

| Trigger | Why Escalate | Example |
|---------|-------------|---------|
| Research reveals conviction-changing evidence | Conviction changes require Aakash's full evidence picture | "Research found Composio raised $50M — this changes the Agentic AI thesis" |
| Action requires outreach/intro | Agent cannot make calls or send personal messages | "Research suggests reaching out to Composio CTO" |
| Conflicting evidence found | Strategic judgment needed | "Found both strong positive AND negative signals for thesis" |
| Action scope exceeds budget | Agent should not spend unbounded resources | "Competitive landscape requires 20+ company analysis" |

### Datum Agent's Role in Autonomous Execution

The Datum Agent handles these action types autonomously:

| Action Pattern | Datum Agent Behavior |
|---------------|---------------------|
| "Add [person] to network DB" | Normal Datum Agent flow (parse, dedup, enrich, write) |
| "Add [company] to companies DB" | Normal Datum Agent flow |
| "Enrich [person]'s profile" | Fetch existing record, run web enrichment on null fields |
| "Update [company] with latest info" | Fetch existing record, web-research updates, merge |
| "Link [person] to [company]" | Update person's company field, verify via dedup |

These are all Pipeline Actions that map directly to Datum Agent's core capability. No new logic needed — the Orchestrator just sends the action description as a prompt.

### Thesis Maintenance (Content Agent, not Datum Agent)

Thesis-related autonomous work stays with the Content Agent, which already has:
- Thesis thread querying and evidence management
- IDS methodology and conviction assessment skills
- Content analysis framework for evaluating evidence

What changes: the Content Agent gains a new trigger path. In addition to "Run your content pipeline cycle" and "Process these inbox messages," it can receive "Execute these agent-assigned actions" from the Orchestrator.

Agent-executable thesis actions:
- "Review new evidence for [thesis]" -> Content Agent queries recent content_digests touching that thesis, synthesizes, appends evidence
- "Research [topic] for [thesis]" -> Content Agent spawns web-researcher subagent, writes results as evidence
- "Analyze competitive landscape for [thesis]" -> Content Agent spawns web-researcher, produces research report + evidence updates
- "Update key questions for [thesis]" -> Content Agent reviews evidence vs. open questions, marks answered ones

### What This Does NOT Change

- **Human actions stay human.** Meetings, calls, intros, follow-on evaluations, strategic decisions — always surfaced to Aakash.
- **Conviction changes require human review.** Agent can RECOMMEND conviction changes and provide evidence, but the actual change is either human-set (Status) or escalated (conviction level).
- **Action outcomes still feed RL.** Even agent-executed actions get logged to `action_outcomes` when completed. Over time, this teaches the system which action types agents handle well vs. poorly.
- **Trust starts at Suggest.** Initially, agent-assigned actions could be surfaced on WebFront for Aakash to approve before execution (a checkbox: "auto-execute agent actions" that defaults OFF). Once confidence builds, flip to auto-execute.

### Implementation (Additions to Phase Plan)

This feature adds a **Phase 6** to the implementation plan:

#### Phase 6: Autonomous Action Execution Loop
**Estimated effort:** M (3-8 hours)
**Dependencies:** Phase 1 (Datum Agent core), WebFront Phase 1 (Action Triage for trust ramp)

- [ ] Add `execute_actions` inbox routing to Orchestrator HEARTBEAT.md
- [ ] Add agent-action query to Orchestrator's heartbeat cycle (SQL above)
- [ ] Content Agent: add "Execute these agent-assigned actions" handling to CLAUDE.md
- [ ] Datum Agent: no CLAUDE.md changes needed (Pipeline Actions already match core flow)
- [ ] WebFront: add "Auto-execute agent actions" toggle on /actions page (defaults OFF)
- [ ] When toggle OFF: agent actions show on WebFront with [Approve] [Dismiss] buttons
- [ ] When toggle ON: Orchestrator routes immediately without waiting for approval
- [ ] Logging: every auto-executed action gets an `action_outcomes` entry with `created_by = 'Agent'`
- [ ] Test: create Research action assigned to Agent, verify Content Agent executes it
- [ ] Test: create Pipeline Action (add person), verify Datum Agent executes it
- [ ] Test: verify escalation when agent finds conviction-changing evidence

---

## Appendix A: Directory Structure

```
mcp-servers/agents/
  datum/
    CLAUDE.md                    # Full system prompt (Section 3)
    CHECKPOINT_FORMAT.md         # Compaction checkpoint format
    state/
      datum_session.txt          # Session counter
      datum_iteration.txt        # Iteration counter
      datum_last_log.txt         # Last operation log
      datum_checkpoint.md        # Checkpoint (if compaction needed)
    live.log                     # Real-time operation log

  skills/
    data/
      postgres-schema.md         # (existing) Base schema reference
      datum-schema.md            # (new) Datum-specific schemas + queries
      dedup-algorithm.md         # (new) Dedup algorithm as loadable skill
```

## Appendix B: Inbox Message Types

| Type | Source | Example Content | Metadata |
|------|--------|----------------|----------|
| `datum_person` | CAI | "Add Rahul Sharma, CTO at Composio" | `{ "name": "Rahul Sharma", "company": "Composio", "role": "CTO" }` |
| `datum_company` | CAI | "Track Composio - AI agent tooling" | `{ "name": "Composio", "sector": "AI Infrastructure" }` |
| `datum_entity` | Content Agent | "Entity batch from content analysis" | `{ "entities": [...], "source_digest_slug": "..." }` |
| `datum_image` | CAI | "Business card photo" | `{ "image_url": "..." }` |
| `datum_meeting_entities` | Granola (future) | "People from meeting with Composio" | `{ "meeting_id": "...", "entities": [...] }` |

## Appendix C: Orchestrator Routing Addition

The Orchestrator's `HEARTBEAT.md` needs a new routing rule:

```
## Inbox Routing

For each unprocessed inbox message, route by type:

| Type Pattern | Route To | Bridge Tool |
|-------------|----------|-------------|
| datum_* | Datum Agent | send_to_datum_agent |
| track_source, research_request, general, ... | Content Agent | send_to_content_agent |
```

Orchestrator batches datum messages: if there are 3+ datum_* messages in the inbox, it sends them as a single batch prompt to the Datum Agent rather than one-by-one.

## Appendix D: Datum Agent vs. Entity Resolution Capability

Per CAPABILITY-MAP.md (Capability 1: Entity Resolution), the Datum Agent implements **Entity Resolution +** (Basic):

> Company Index + Person Index: Postgres tables mapping names/aliases to Notion page IDs. LLM-as-matcher for fuzzy resolution.

The embedding similarity dedup (Tier 3) begins to implement **Entity Resolution ++** (Structured):

> Confidence scoring (auto-merge >0.9, flag 0.7-0.9, tentative 0.5-0.7). Alias learning from corrections.

The Datum Agent is the natural home for the Entity Resolution capability to grow over time. As more signal sources feed entity references, the dedup algorithm graduates from + to ++ to +++ without changing the agent's architecture — only its skills and confidence thresholds evolve.
