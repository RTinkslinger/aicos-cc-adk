# Obligations Intelligence Build — Phase 0 + Phase 1 Report

**Date:** 2026-03-20
**Milestone:** M11 Loop 2
**Spec:** `docs/superpowers/specs/2026-03-20-obligations-intelligence-design.md`

---

## Phase 0: Schema (Supabase)

### Table Created: `obligations`

**Database:** Supabase `llfkxnsfczludgigknbs`

30 columns total:

| Column | Type | Notes |
|--------|------|-------|
| id | SERIAL PK | Auto-increment |
| person_id | INTEGER NOT NULL | FK to network.id |
| person_name | TEXT NOT NULL | Denormalized |
| person_role | TEXT | Denormalized |
| obligation_type | TEXT NOT NULL | CHECK: I_OWE_THEM / THEY_OWE_ME |
| description | TEXT NOT NULL | Human-readable commitment |
| category | TEXT NOT NULL | Default: follow_up |
| source | TEXT NOT NULL | email/whatsapp/granola/calendar/manual |
| source_interaction_id | INTEGER | FK to interactions.id |
| source_quote | TEXT | Exact triggering text |
| detection_method | TEXT NOT NULL | Default: explicit |
| detected_at | TIMESTAMPTZ NOT NULL | Default: NOW() |
| due_date | TIMESTAMPTZ | Nullable if no deadline |
| due_date_source | TEXT | explicit/inferred/etiquette |
| status | TEXT NOT NULL | CHECK: 6 valid statuses |
| status_changed_at | TIMESTAMPTZ | |
| fulfilled_at | TIMESTAMPTZ | |
| fulfilled_method | TEXT | manual/auto_detected/action_completed |
| fulfilled_evidence | TEXT | Resolution provenance |
| snooze_until | TIMESTAMPTZ | |
| cindy_priority | REAL NOT NULL | Default: 0.5 |
| cindy_priority_factors | JSONB | Factor breakdown |
| megamind_priority | REAL | NULL until Megamind processes |
| megamind_priority_factors | JSONB | |
| megamind_override | BOOLEAN | Default: FALSE |
| blended_priority | REAL GENERATED | 60% Cindy + 40% Megamind, or 1.0 on override |
| context | JSONB | Thesis, company, deal context |
| linked_action_id | INTEGER | FK to actions_queue.id |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

### Generated Column

`blended_priority` is a STORED generated column:
```sql
CASE
    WHEN megamind_override THEN 1.0
    WHEN megamind_priority IS NOT NULL
        THEN (cindy_priority * 0.6) + (megamind_priority * 0.4)
    ELSE cindy_priority
END
```

### Staleness: View Instead of Generated Column

**Design spec called for:** `staleness_days` as a STORED generated column using `NOW()`.
**Actual implementation:** `obligations_with_staleness` view that computes `staleness_days` at query time.

**Reason:** PostgreSQL requires STORED generated column expressions to be IMMUTABLE. `NOW()` is STABLE (changes within a transaction), not IMMUTABLE. A stored generated column using `NOW()` would freeze at INSERT time and never update, which defeats the purpose. The view computes staleness correctly at every query.

### Indexes (9 total, including PK)

| Index | Type | Purpose |
|-------|------|---------|
| obligations_pkey | UNIQUE btree(id) | Primary key |
| idx_obligations_active | btree(blended_priority DESC) WHERE status IN (pending/overdue/escalated) | Dashboard primary query |
| idx_obligations_person | btree(person_id, status) | Per-person lookup |
| idx_obligations_type | btree(obligation_type, status, blended_priority DESC) WHERE active | Split view queries |
| idx_obligations_overdue | btree(due_date) WHERE pending + due_date NOT NULL | Staleness processor |
| idx_obligations_snoozed | btree(snooze_until) WHERE snoozed + snooze_until NOT NULL | Resurface processor |
| idx_obligations_source | btree(source_interaction_id) WHERE NOT NULL | Dedup + provenance |
| idx_obligations_megamind_override | btree(updated_at DESC) WHERE override + active | P0 urgency queries |
| idx_obligations_description_fts | GIN(to_tsvector) | Full-text search |

**Index note:** Design spec had `idx_obligations_overdue` with `AND due_date < NOW()` in the WHERE clause. This was changed to `AND due_date IS NOT NULL` because `NOW()` is not immutable and cannot be used in partial index predicates. The staleness processor query applies the `< NOW()` filter at runtime, which still uses this index effectively.

### Verification

Both verification queries executed successfully:
- `information_schema.columns` returned all 30 columns with correct types and defaults
- `pg_indexes` returned all 9 indexes with correct definitions

---

## Phase 1: Cindy CLAUDE.md Update

### File Modified: `mcp-servers/agents/cindy/CLAUDE.md`

**Changes:**

1. **Section 3 (Database Access):** Added `obligations` table to "Tables You Read AND Write" with access level "Read + Write" and purpose "Obligation detection, auto-fulfillment, priority computation"

2. **New Section 7.5:** "Obligation Detection (MANDATORY processing step)" added between Section 7 (Signal Extraction) and Section 8 (Interaction with Fleet Agents). Contains:
   - Definition of obligations (I_OWE_THEM / THEY_OWE_ME)
   - 6-step detection process (scan, extract, dedup, create, compute priority, route)
   - Auto-fulfillment check logic with SQL template
   - Category reference
   - Additional table declaration (obligations: Read + Write)
   - ACK format addition (obligation counts + auto-fulfillment counts)
   - Exclusion rules (no pleasantries, no vague intentions, no internal ops, confidence >= 0.7)

### Skill Created: `mcp-servers/agents/skills/cindy/obligation-detection.md`

Full domain knowledge file covering:
- Detection patterns for all 4 surfaces (email, WhatsApp, Granola, calendar)
- Obligation record schema with INSERT template
- 5-factor Cindy priority formula with weight tables
- Deduplication logic with SQL
- Auto-fulfillment detection with resolution signal matrix
- Megamind routing criteria
- Confidence threshold (>= 0.7)
- Staleness thresholds by type and detection method
- ACK format addition

---

## Files Produced

| File | Purpose |
|------|---------|
| `sql/obligations-build.sql` | Full SQL migration (table + view + indexes) |
| `mcp-servers/agents/cindy/CLAUDE.md` | Updated with Section 7.5 + obligations table access |
| `mcp-servers/agents/skills/cindy/obligation-detection.md` | Cindy skill for obligation detection |
| `docs/audits/2026-03-20-obligations-build-m11-loop2.md` | This report |

---

## Deviations from Design Spec

| Spec | Actual | Reason |
|------|--------|--------|
| `staleness_days` STORED generated column | `obligations_with_staleness` view | `NOW()` is not IMMUTABLE; stored generated column would freeze at INSERT time |
| `idx_obligations_overdue` with `due_date < NOW()` | Same index without `< NOW()` | `NOW()` not allowed in partial index predicates; filter applied at query time |

Both deviations are functionally equivalent. The view and query-time filtering produce identical results to what the spec intended, without the PostgreSQL immutability constraint violations.

---

## Not Yet Implemented (Future Phases)

- CIR trigger on obligations table (Phase 0 stretch)
- CIR propagation rules (Phase 0 stretch)
- pg_cron staleness check job (Phase 0 stretch)
- `compute_cindy_priority()` SQL function from Appendix B (Phase 1 stretch)
- Megamind CLAUDE.md updates for Type 4 work (Phase 3)
- WebFront /cindy pages (Phase 5)
