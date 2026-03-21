# Datum Agent Build Review — M4 Loop 3
*Reviewed: 2026-03-20*
*Reviewer: Claude Opus 4.6 (subagent)*

---

## Executive Summary

The Datum Agent build is **solid and production-ready for Phase 0 + Phase 1 (Core Agent MVP)**. The CLAUDE.md is comprehensive for headless operation, SQL migrations are verified live on Supabase, hooks follow established patterns, and skills use correct column names. A few issues found -- mostly minor inconsistencies between the design spec and the final build (correctly resolved in favor of actual DB schema).

**Overall: PASS with 3 minor issues for Loop 4.**

---

## 1. CLAUDE.md Quality

**Verdict: PASS**

### Comprehensiveness for Headless Agent
- 639 lines covering 15 sections -- comparable to Content Agent (633 lines, 18 sections)
- Identity section clearly states "You are NOT an assistant" and "no human in the loop"
- Processing flow is deterministic: Parse > Dedup > Enrich > Write > Datum Requests > Report
- Every response requires structured ACK -- same pattern as Content Agent
- Error handling is thorough (input errors, dedup edge cases, web enrichment errors, DB errors, capacity protection)

### Input Types Coverage
- **PASS**: All 5 input types covered: `datum_person`, `datum_company`, `datum_entity` (batch), `datum_image`, Pipeline Action
- Pipeline Actions include status transition SQL (In Progress -> Done)
- Batch processing is capped at 20 entities with overflow notification

### Dedup Algorithm
- **PASS**: 4-tier algorithm clearly specified in CLAUDE.md Section 4.2 + dedicated skill file
- Tier 1: LinkedIn/Domain exact match (confidence 1.0)
- Tier 2: Exact name match (confidence 0.95)
- Tier 3: Embedding similarity (0.80 threshold for persons, 0.85 for companies)
- Tier 4: Name-only fallback (0.50-0.70, always ASK_USER)
- Auto-merge threshold at 0.90 is explicitly enforced as anti-pattern #8

### DB Column Names
- **PASS**: CLAUDE.md correctly uses `person_name`, `role_title`, `home_base` (TEXT[]), `linkedin` throughout
- Explicit warnings at multiple points: Section 3 query patterns, Section 5 enrichment priorities, Section 12 archetype taxonomy
- Verified against live DB: no `name`, `role`, `city`, `company`, or `linkedin_url` columns exist on the `network` table

### Depth Level Handling (from Megamind)
- **NOT PRESENT**: The CLAUDE.md does not mention `depth_level` or any Megamind-specific depth handling
- **Assessment**: This is acceptable for Phase 1 MVP. Depth levels would be relevant for Phase 2 (web enrichment) where different depth levels could control enrichment aggressiveness. Can be added in a future loop.

### Anti-Patterns
- **PASS**: 15 anti-patterns listed (vs. 15 for Content Agent). All critical ones present:
  - Never create duplicates
  - Never overwrite with NULLs
  - Never import Python DB modules
  - Never skip ACK
  - Never auto-merge below 0.90
  - Never exceed rate limits
  - Never guess LinkedIn URLs (important -- guessed URLs fail silently)

### Minor Issue #1: ACK Example Uses Wrong Column Names
In Section 4 Step 6 (Report Back), the ACK example says:
```
- Filled: name, company, role, linkedin_url, city (5/13 fields).
- Web enriched: linkedin_url, city (2 fields via LinkedIn scrape).
```
These should reference the actual column names (`person_name`, `role_title`, `linkedin`, `home_base`) for consistency. While ACK text is human-readable (not SQL), using incorrect column references could confuse the agent about which fields were actually filled.

**Severity: Low.** The agent's SQL queries all use correct names. The ACK is just a summary string.

---

## 2. SQL Migrations

**Verdict: PASS -- all verified live**

### datum_requests Table
- **PRESENT**: 17 columns, all matching the migration file exactly
- id (SERIAL), entity_type (TEXT NOT NULL), entity_id (INTEGER NOT NULL), field_name (TEXT NOT NULL)
- source_context, current_value, suggested_value, suggestion_confidence (REAL), suggestion_source
- merge_candidate_ids (ARRAY), merge_type (TEXT)
- status (TEXT, default 'pending'), answer, answered_by, answered_at (TIMESTAMPTZ)
- created_at, updated_at (TIMESTAMPTZ, default NOW())
- **0 rows** (fresh table, confirmed)

### Indexes on datum_requests
- `idx_datum_requests_status` -- partial index on status WHERE pending (WebFront queries)
- `idx_datum_requests_entity` -- composite on (entity_type, entity_id)
- `idx_datum_requests_entity_field` -- partial composite for dedup check WHERE pending
- All 3 confirmed present

### Network Table Alterations
All 6 new columns confirmed present:
- `enrichment_status` (TEXT)
- `enrichment_source` (TEXT)
- `last_enriched_at` (TIMESTAMPTZ)
- `aliases` (ARRAY)
- `datum_source` (TEXT)
- `datum_created_at` (TIMESTAMPTZ)
- Pre-existing columns confirmed: `person_name`, `role_title`, `home_base` (ARRAY), `linkedin`, `embedding` (USER-DEFINED/vector)

### Companies Table Alterations
All 8 new columns confirmed present:
- `enrichment_status`, `enrichment_source`, `last_enriched_at`
- `domain` (TEXT) with unique partial index `idx_companies_domain_unique`
- `aliases` (ARRAY)
- `datum_source`, `datum_created_at`
- `embedding` (pre-existing from IRGI Phase A)

### Network Embedding Infrastructure
3 triggers confirmed on the network table:
- `embed_network_on_insert` -> `queue_embeddings` (AFTER INSERT)
- `embed_network_on_update` -> `queue_embeddings` (AFTER UPDATE of person_name, role_title, home_base)
- `clear_network_embedding_on_update` -> `clear_column` (BEFORE UPDATE)
- HNSW index `idx_network_embedding` confirmed present

### Migration File Quality
- Idempotent (IF NOT EXISTS / ADD COLUMN IF NOT EXISTS throughout)
- Well-commented with execution notes and verification queries
- Correctly documents the design spec deviation: "The design spec assumed generic column names (name, role, city, linkedin_url). Actual columns are: person_name, role_title, home_base, linkedin."

---

## 3. Hooks

**Verdict: PASS**

### Pattern Consistency with Content Agent

| Aspect | Content Agent | Datum Agent | Match? |
|--------|--------------|-------------|--------|
| Hook types | Stop, UserPromptSubmit, PreCompact | Stop, UserPromptSubmit, PreCompact | YES |
| settings.json structure | Identical nesting | Identical nesting | YES |
| Path prefix | `/opt/agents/content/.claude/hooks/` | `/opt/agents/datum/.claude/hooks/` | YES |
| AGENT variable | `content` | `datum` | YES |

### stop-iteration-log.sh
- Correctly sets `AGENT="datum"`
- Reads from `state/datum_last_log.txt`, writes to shared traces
- Increments `datum_iteration.txt`
- Identical logic to content agent version (minus pipeline timestamp logic, which is content-specific)
- **Correct**: No pipeline timestamp logic -- datum agent is on-demand, not pipeline-driven

### prompt-manifest-check.sh
- Correctly sets `AGENT="datum"`
- Token threshold at 100K (same as content)
- Injects COMPACTION REQUIRED instruction
- **Correct**: No pipeline detection logic (content agent checks for "pipeline cycle" in prompt text; datum agent does not need this)

### pre-compact-flush.sh
- Correctly sets `AGENT="datum"`
- Emergency checkpoint writer -- identical logic to content
- Recovery instructions are slightly different: "Resume normal entity processing" vs "Resume normal heartbeat operation"
- **Correct adaptation**

### settings.json
- Properly structured with all 3 hook types
- Paths point to `/opt/agents/datum/.claude/hooks/` (droplet deployment path)
- Format matches content agent exactly

---

## 4. Skills

**Verdict: PASS with 1 minor issue**

### datum-processing.md

**Column names**:
- Network table section explicitly lists: `person_name` (NOT "name"), `role_title` (NOT "role"), `linkedin` (NOT "linkedin_url"), `home_base` TEXT[] (NOT "city")
- All SQL examples in the skill use correct column names
- Processing checklist is complete (11 steps in correct order)

**Schema accuracy**: `datum_requests` schema in the skill matches the live DB exactly (17 columns, same types, same defaults)

**Input coverage**: Text, URL, Batch parsing patterns all documented

### Minor Issue #2: datum-processing.md Input Parsing Uses Generic Names
In the "Text Input" parsing section (lines 11-20), the parsed output uses generic field names:
```
Parsed:
  type: person
  name: Rahul Sharma
  role: CTO
  company: Composio
```
These are conceptual parsing outputs (not DB columns), but using `name` / `role` / `company` could confuse the agent when it then needs to map to `person_name` / `role_title` (which embeds company). The mapping from parsed fields to actual columns is not explicitly documented in the skill.

**Severity: Low.** The CLAUDE.md's Section 3 query patterns show the correct INSERT syntax, and the column reference table in the skill is explicit. But adding a "Parsed Field -> DB Column" mapping table would eliminate ambiguity.

### dedup-algorithm.md

- 4-tier algorithm with correct SQL for each tier
- **All SQL uses correct column names**: `person_name`, `role_title`, `linkedin` in SELECT statements
- Embedding similarity thresholds: 0.80 for persons, 0.85 for companies (correctly different)
- Merge protocol with COALESCE pattern documented
- Conflict handling (trivial vs meaningful differences) documented
- Array field merging SQL is correct
- Decision flowchart is clear ASCII art
- Special cases (job changes, rebrands, transliterations, batch) all covered

### Skill Path Issue
The CLAUDE.md references skills at `skills/datum/dedup-algorithm.md` and `skills/datum/datum-processing.md`. The actual files are at `skills/datum/` under the agents directory. This is correct -- skills are loaded relative to the agent workspace via the Skill tool. However, the design spec referenced `skills/data/datum-schema.md` and `skills/data/dedup-algorithm.md` (different directory). The build correctly placed them in `skills/datum/` which is more logical (agent-specific skills).

**Note**: The CLAUDE.md Section 3 references `skills/datum/datum-processing.md` which matches the actual path. The design spec's `skills/data/` path was correctly overridden.

---

## 5. Lifecycle Integration Plan

**Verdict: PASS**

### Completeness
- 16 sections covering every aspect of lifecycle.py integration
- Implementation order is logical and dependency-aware (12 ordered steps)
- Testing plan covers 6 scenarios including edge cases (busy, crash, compaction, batching)

### @tool Bridge Pattern
- `send_to_datum_agent` follows exact same pattern as `send_to_content_agent`
- Background response reader (`_read_datum_response`) correctly handles COMPACT_NOW detection
- Busy-check pattern matches content agent
- Error handling matches content agent

### On-Demand Activation
- **Correctly documented**: Datum Agent is inbox-triggered ONLY (no heartbeat/pipeline cycle)
- Content Agent is heartbeat-triggered + inbox-triggered
- This is called out explicitly in Section 12 with rationale

### Budget Rationale
- max_budget_usd = 2.0 (vs Content Agent 5.0) -- reasonable for shorter operations
- max_turns = 30 (vs Content Agent 50) -- reasonable for entity processing
- thinking = 5000 tokens (vs Content Agent 10000) -- reasonable for dedup decisions
- All justified with clear reasoning

### Deployment Impact
- No new systemd service needed (runs inside existing lifecycle.py)
- No new env vars needed
- deploy.sh rsync already covers the datum/ directory
- Manifest tracking auto-creates datum entry

---

## 6. Design Spec Compliance

**Verdict: PASS -- build correctly deviates from spec where spec was wrong**

### What Was Built (Phase 0)

| Spec Item | Built? | Notes |
|-----------|--------|-------|
| datum_requests table | YES | All 17 columns, 3 indexes, live on Supabase |
| ALTER TABLE network | YES | 6 new columns + embedding triggers |
| ALTER TABLE companies | YES | 7 new columns + domain unique index |
| Agent directory structure | YES | CLAUDE.md, CHECKPOINT_FORMAT.md, .claude/, state/, live.log |
| Hooks (3) | YES | stop, prompt-manifest-check, pre-compact-flush |
| Skills (2) | YES | datum-processing.md, dedup-algorithm.md |
| Lifecycle integration plan | YES | 16-section plan with implementation order |

### Correctly Resolved Design Spec Issues

The design spec (written before schema discovery) assumed generic column names. The build correctly resolved these:

| Spec Assumed | Actual (Build Used) | Resolution |
|-------------|--------------------|----|
| `name` column on network | `person_name` | Correct -- used actual name |
| `role` column on network | `role_title` (contains "Role at Company") | Correct -- used actual name |
| `city` column on network | `home_base` TEXT[] (array, not scalar) | Correct -- used actual name + type |
| `linkedin_url` column on network | `linkedin` (pre-existing, 3247 values) | Correct -- used actual name, documented that linkedin_url was created then dropped |
| `company` column on network | No separate column (embedded in `role_title`) | Correct -- CLAUDE.md explains the format |
| `embedding_input` column on network | Not needed (trigger uses `embedding_input_network()` function) | Correct -- IRGI pattern uses functions, not columns |
| UNIQUE index on linkedin | Not possible (existing duplicates) | Correct -- documented in migration comments |

### What Was Deferred

| Spec Phase | Status | Notes |
|------------|--------|-------|
| Phase 0: Infrastructure | **COMPLETE** | All migrations ran, directory created |
| Phase 1: Core Agent (MVP) | **READY** | CLAUDE.md written, skills in place, hooks ready. lifecycle.py integration not yet coded (plan written) |
| Phase 2: Web Enrichment | DEFERRED | Web Tools MCP is in the options builder but enrichment strategy is prompt-only (no code) |
| Phase 3: Embedding Dedup | DEFERRED | Infrastructure ready (triggers, HNSW index). Algorithm documented. Testing deferred. |
| Phase 4: WebFront Datum Tab | DEFERRED | Design spec has full wireframe. No Next.js code written yet. |
| Phase 5: Content Pipeline Integration | DEFERRED | datum_entity inbox type defined but Content Agent not yet modified |
| Phase 6: Autonomous Action Execution | DEFERRED | Design only |

### Spec vs Build: Dedup Algorithm
The spec had a "3-tier" algorithm (Tier 1: LinkedIn/Domain, Tier 2: Exact Name+Company, Tier 3: Embedding). The build expanded to **4 tiers** by adding Tier 4 (Name-Only Fallback) -- an improvement over the spec. The spec's Tier 2 combined "exact name + company" but since the network table has no separate `company` column, the build correctly adjusted Tier 2 to name-only exact match (case-insensitive on `person_name`).

---

## 7. Cross-Cutting Issues

### Minor Issue #3: `datum_requests` Read Access
The CLAUDE.md Section 3 (Database Access) shows `datum_requests` with "Read + Write" access. However, the design spec Section 3 shows it as "Write" only. The CLAUDE.md is correct here -- the agent needs to READ datum_requests to check for existing pending requests before creating duplicates (dedup pattern shown in Section 4 Step 5). The design spec was too restrictive.

### Notifications Table
The CLAUDE.md includes a `source` column in notification inserts (`'DatumAgent'`), while the Content Agent uses no explicit source column (just `type`, `content`, `metadata`, `created_at`). Need to verify the notifications table has a `source` column. Looking at the CLAUDE.md insert pattern:
```sql
INSERT INTO notifications (source, type, content, metadata, created_at)
```
This should be verified. If `source` doesn't exist, all notification inserts will fail.

**Verified**: The `notifications` table DOES have a `source` column (varchar). The Datum Agent's notification SQL is correct. No action needed.

---

## Summary Scorecard

| Section | Verdict | Issues |
|---------|---------|--------|
| 1. CLAUDE.md Quality | **PASS** | #1: ACK example uses generic column names (low severity) |
| 2. SQL Migrations | **PASS** | All verified live on Supabase |
| 3. Hooks | **PASS** | Consistent with content agent patterns |
| 4. Skills | **PASS** | #2: Parsing output uses generic names, missing field->column mapping (low) |
| 5. Lifecycle Plan | **PASS** | Complete, actionable, correct @tool pattern |
| 6. Design Spec Compliance | **PASS** | Correctly resolved spec errors; appropriate deferrals |

---

## Recommendations for Loop 4

### Must Fix (before lifecycle.py integration)
- None. The `notifications.source` column was verified present (varchar). All SQL patterns are correct.

### Should Fix (quality improvements)
1. **Add parsed-field-to-column mapping** in datum-processing.md skill -- small table mapping `name -> person_name`, `role+company -> role_title`, `city -> home_base`, `linkedin_url -> linkedin`
2. **Update ACK examples** in CLAUDE.md Section 4.6 to use actual column names for consistency

### Nice to Have (future loops)
4. **Add depth_level handling** for Megamind integration (Phase 2+)
5. **Add `e_e_priority` to enrichment status computation** -- it is listed as P1 but not checked in the enrichment_status logic in Section 6
6. **Consider adding `archetype` to person enrichment status computation** -- it was P1 in the design spec but downgraded in the build. Clarify intentional vs accidental.
