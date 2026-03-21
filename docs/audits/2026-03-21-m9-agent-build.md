# M9 Intel QA Audit: Agent File Readiness

**Date:** 2026-03-21
**Machine:** M9 Intel QA
**Audit Focus:** Agent file readiness — do the agent CLAUDE.md files and skills reference the 249 SQL functions built by the session?

---

## Executive Summary

**Verdict: MIXED. Strong skill layer being built, but massive gap between SQL functions (249) and agent awareness (partial).**

The session built 249 custom SQL functions in Supabase. Other machines have been writing agent files — CLAUDE.md files exist for 5 agents (Datum, Cindy, Megamind, Content, Orchestrator), and 28 skill files exist across 8 skill domains. However, a structural gap exists:

1. **Agent CLAUDE.md files reference ZERO SQL functions.** They teach agents to use raw `psql` with hand-written queries, not the purpose-built functions.
2. **Newer skill files DO reference SQL functions** — obligation-triage, interaction-analysis, strategic-briefing, data-quality, enrichment, and ENIAC research/search skills all properly teach agents how to call specific SQL functions.
3. **ENIAC has no CLAUDE.md.** The directory exists but is empty (no CLAUDE.md, no hooks, nothing in `.claude/`). Only 2 skill files exist.
4. **There is a two-tier system emerging:** CLAUDE.md files are stale (pre-SQL-function era) while skills are current (post-SQL-function era). An agent reading only its CLAUDE.md would never know the SQL functions exist.

---

## Detailed Findings

### 1. Skill Files Inventory

28 skill files exist, organized by agent/domain:

| Domain | Files | Quality | SQL Function References |
|--------|-------|---------|------------------------|
| `cindy/` | 9 files | HIGH | obligation-triage (9 functions), interaction-analysis (5 functions), but obligation-reasoning, signal-extraction, email-processing, whatsapp-parsing, calendar-gap-detection, people-linking use raw SQL only |
| `datum/` | 5 files | HIGH | data-quality (6 functions), enrichment (5 functions), but datum-processing, dedup-algorithm, people-linking use raw SQL only |
| `megamind/` | 4 files | HIGH | strategic-briefing (8+ functions), but depth-grading, cascade-protocol, strategic-reasoning use raw SQL only |
| `eniac/` | 2 files | HIGH | eniac-research (3 functions), eniac-search (5 functions) — both well-written |
| `content/` | 5 files | MEDIUM | No SQL function references — all raw query patterns |
| `data/` | 1 file | MEDIUM | postgres-schema.md — base schema, no function references |
| `sync/` | 3 files | MEDIUM | No SQL function references |
| `web/` | 5 files | MEDIUM | No SQL function references (appropriate — web tools not SQL) |
| `reasoning/` | 1 file | MEDIUM | No SQL function references |

**Key finding:** The skill files that DO reference SQL functions are well-written. They follow a consistent pattern:
- Function name and signature
- "What it does" explanation
- "When to use" contextual guidance
- Full `psql` usage example
- Return structure documentation

This is the correct pattern. The older skills that use raw SQL queries are now outdated — they hardcode queries that the SQL functions already encapsulate.

### 2. Agent CLAUDE.md Files — Quality Assessment

| Agent | CLAUDE.md | Length | SQL Function Refs | Quality |
|-------|-----------|--------|-------------------|---------|
| **Datum** | YES | 859 lines | **ZERO** | HIGH for raw SQL patterns, but completely unaware of `datum_daily_maintenance()`, `datum_signal_propagator()`, `datum_cross_entity_linker()`, etc. |
| **Cindy** | YES | ~500 lines | **ZERO** | HIGH for reasoning instructions, but unaware of `cindy_obligation_full_context()`, `cindy_interaction_pattern_data()`, `cindy_daily_briefing()`, etc. |
| **Megamind** | YES | ~300 lines | **ZERO** | HIGH for strategic reasoning framework, but unaware of `generate_strategic_briefing()`, `format_strategic_briefing()`, `generate_decision_framework()`, etc. |
| **Content** | YES | ~200+ lines | **ZERO** | MEDIUM — older agent, no SQL function awareness |
| **Orchestrator** | YES | ~100 lines | **ZERO** | ADEQUATE — lean coordinator, may not need SQL functions directly |
| **ENIAC** | **MISSING** | 0 | N/A | **CRITICAL GAP** — directory exists with empty `.claude/` and `state/`, but no CLAUDE.md at all |

### 3. ENIAC Agent Status — CRITICAL GAP

```
eniac/
  .claude/        (empty)
  state/          (empty)
  CLAUDE.md       MISSING
```

ENIAC is defined as the research analyst agent in the fleet. It has:
- 2 skill files (`eniac-research.md`, `eniac-search.md`) that reference 8 SQL functions
- 3 dedicated SQL functions (`eniac_research_queue`, `eniac_research_brief`, `eniac_save_research_findings`)
- No CLAUDE.md to define identity, capabilities, processing flow, or anti-patterns
- No hooks directory
- Empty state directory

An Agent SDK agent launched in this directory would have skills but no identity. It wouldn't know:
- Who it is or what it does
- What tools it has access to (web tools? bash? psql?)
- What tables it can read/write vs. what's off-limits
- How to process work from the Orchestrator
- State tracking and lifecycle patterns
- Error handling

### 4. SQL Function Coverage Analysis

249 custom SQL functions exist. How many are referenced in ANY agent file (CLAUDE.md or skills)?

**Referenced in skills (at least partially documented for agents):**
- Obligation management: ~9 functions (cindy obligation-triage skill)
- Interaction analysis: ~5 functions (cindy interaction-analysis skill)
- Strategic briefing: ~8 functions (megamind strategic-briefing skill)
- Data quality/maintenance: ~6 functions (datum data-quality skill)
- Enrichment/propagation: ~5 functions (datum enrichment skill)
- ENIAC research: ~3 functions (eniac-research skill)
- ENIAC search: ~5 functions (eniac-search skill)

**Total referenced: ~41 of 249 (16%)**

**Categories of unreferenced functions (208 functions, 84%):**
- Scoring model functions (~30): `score_action_thesis_relevance`, `compute_user_priority_score`, `compute_portfolio_strategic_score`, `compute_score_confidence`, `explain_score`, `score_explainer`, `narrative_score_explanation`, `scoring_intelligence_report`, `scoring_validation`, `scoring_regression_test`, `scoring_velocity`, `run_scoring_experiment`, `score_summary_api`, `score_trend`, `refresh_action_scores`, `refresh_active_scores`, `normalize_all_scores`, `normalize_factor`, `snapshot_scores`, etc.
- CIR functions (~12): `cir_dashboard_api`, `cir_full_status`, `cir_system_health`, `cir_self_heal`, `cir_staging_processed`, `cir_obligation_changed`, `cir_change_detected`, `process_cir_queue`, `process_cir_queue_batch`, `process_cir_queue_item`, `process_cir_queue_prioritized`, `record_cir_heartbeat`
- IRGI functions (~3): `irgi_benchmark`, `irgi_system_report`, `irgi_interaction_thesis_crossref`
- Intelligence functions (~20): `deal_intelligence_brief`, `deal_pipeline_intelligence`, `portfolio_intelligence_report`, `portfolio_intelligence_map`, `portfolio_deep_context`, `network_intelligence_report`, `company_intelligence_profile`, `competitive_landscape`, `intelligence_timeline`, `interaction_intelligence_report`, `interaction_intelligence_score`, etc.
- Embedding pipeline functions (~12): `embedding_health_report`, `embedding_queue_health`, `embedding_recovery_dashboard`, `embedding_recovery_status`, `embedding_input_*` (7 functions), `populate_interactions_embedding_input`
- Cascade/convergence functions (~8): `cascade_impact_analysis`, `cascade_dedup_guard`, `create_cascade_event`, `process_cascade_event`, `simulate_convergence`, `process_obligation_cascade`, etc.
- Auto-maintenance/cron functions (~10): `auto_dismiss_stale_actions`, `auto_resolve_stale_actions`, `auto_grade_new_action`, `auto_refresh_depth_grades`, `auto_refresh_priority_score`, `auto_refresh_stale_entities`, `check_cron_health`, `proactive_refresh_stale_entities`, `preemptive_refresh`, etc.
- Relationship/connection functions (~10): `relationship_graph`, `relationship_strength_score`, `build_relationship_pairs`, `strategic_network_map`, `discover_connections`, `find_related_entities`, `find_related_companies`, `connect_orphaned_entities`, etc.
- Thesis/portfolio functions (~15): `thesis_health_dashboard`, `thesis_landscape`, `thesis_momentum_report`, `thesis_research_package`, `thesis_breadth_multiplier`, `thesis_momentum_multiplier`, `aggregate_thesis_evidence`, `detect_thesis_bias`, `update_thesis_indicators`, `update_thesis_bias_flags`, `suggest_actions_for_thesis`, `portfolio_risk_assessment`, `portfolio_health_multiplier`, etc.
- System health functions (~5): `system_health_aggregate`, `data_quality_dashboard`, `connection_pool_status`, `terminate_idle_connections`, etc.
- Other utility functions (~20+): `predict_next_actions`, `predict_staleness_candidates`, `preference_insights`, `update_preference_from_outcome`, `update_preference_from_rating`, `update_preference_weights`, `detect_emerging_signals`, `detect_interaction_patterns`, `detect_opportunities`, `trend_detection`, etc.

### 5. Would an Agent SDK Agent Know What To Do?

Testing the question: "If I launch each agent with its CLAUDE.md + skills, does it know enough to operate?"

| Agent | Identity Clear? | Tools Clear? | DB Boundaries Clear? | Processing Flow Clear? | SQL Functions Accessible? | Overall Readiness |
|-------|----------------|-------------|---------------------|----------------------|--------------------------|-------------------|
| **Datum** | YES | YES | YES | YES | PARTIAL (11/~40 relevant functions via skills) | 70% |
| **Cindy** | YES | YES | YES | YES | PARTIAL (14/~50 relevant functions via skills) | 65% |
| **Megamind** | YES | YES | YES | YES | PARTIAL (8/~25 relevant functions via skills) | 60% |
| **Content** | YES | YES | YES | YES | NO (0 functions, uses raw SQL) | 50% |
| **Orchestrator** | YES | YES | YES | YES | N/A (delegates, doesn't need SQL functions) | 80% |
| **ENIAC** | **NO** | **NO** | **NO** | **NO** | PARTIAL (8 functions via 2 skills, but no CLAUDE.md to tie them together) | **15%** |

### 6. Skill Organization Assessment

Skills are organized by agent, which is correct:

```
skills/
  cindy/        (9 files) — comms intelligence
  content/      (5 files) — content pipeline
  data/         (1 file)  — shared postgres schema
  datum/        (5 files) — entity data ops
  eniac/        (2 files) — research ops
  megamind/     (4 files) — strategic reasoning
  reasoning/    (1 file)  — shared adversarial analysis
  sync/         (3 files) — sync patterns
  web/          (5 files) — web scraping/browsing
```

This is a good structure. Agent-specific skills live in agent directories. Shared skills (data, reasoning, sync, web) are in domain directories. The CLAUDE.md files reference skills by path (e.g., `skills/datum/dedup-algorithm.md`).

---

## Critical Issues (Priority Order)

### P0: ENIAC has no CLAUDE.md
- **Impact:** ENIAC is inoperable as an Agent SDK agent. It has skill files but no identity, capability list, DB access rules, or processing flow.
- **Risk:** Any machine that needs ENIAC research (M10 CIR, M5 Scoring, M6 IRGI) cannot delegate to it.

### P1: CLAUDE.md files don't reference SQL functions
- **Impact:** Agents will write raw SQL queries instead of calling purpose-built functions. This means:
  - Duplicated logic (agent reimplements what the function already does)
  - Inconsistent behavior (raw query vs. function may differ)
  - Missed intelligence (functions often enrich results with context the raw query wouldn't have)
- **Risk:** The 249 SQL functions become dead code if agents don't know they exist.

### P2: 84% of SQL functions have no agent-facing documentation
- **Impact:** 208 functions are invisible to all agents. Even the newer skill files only cover 41 functions.
- **Risk:** Functions like `scoring_intelligence_report()`, `portfolio_risk_assessment()`, `deal_intelligence_brief()` are exactly what agents need but have no skill teaching agents how to use them.

### P3: Content Agent has zero SQL function awareness
- **Impact:** Content Agent still uses raw SQL for everything. It has no skills referencing any of the scoring, thesis, or content-related SQL functions.
- **Risk:** Scoring model improvements (M5) are invisible to the agent that actually scores content.

---

## Recommendations

1. **Write ENIAC CLAUDE.md** — Use the Datum CLAUDE.md as the template. ENIAC needs identity, tool list, DB boundaries, processing flow (queue-based), state tracking, and anti-patterns. The 2 existing skill files provide good function coverage but need a CLAUDE.md wrapper.

2. **Add SQL function registry sections to each CLAUDE.md** — Each agent CLAUDE.md needs a section listing the SQL functions available to it, grouped by purpose. Not full documentation (that's in skills), but a catalog: "For obligation context, load `skills/cindy/obligation-triage.md`. For interaction analysis, load `skills/cindy/interaction-analysis.md`."

3. **Write skill files for uncovered function clusters** — Priority clusters:
   - Scoring model functions -> `skills/content/scoring-functions.md` or `skills/megamind/scoring-tools.md`
   - CIR functions -> `skills/datum/cir-operations.md` or new `skills/cir/` directory
   - Intelligence report functions -> `skills/megamind/intelligence-reports.md`
   - Embedding pipeline functions -> `skills/data/embedding-operations.md`
   - Portfolio/deal functions -> `skills/megamind/portfolio-tools.md`

4. **Deprecate raw SQL patterns in CLAUDE.md** — Where a SQL function exists, the CLAUDE.md should say "use function X" not "write this SQL query." Example: Datum CLAUDE.md has a hand-written 6-tier people resolution algorithm. The function `resolve_participant()` and `resolve_interaction_participants_v2()` already do this.

---

## Metrics

| Metric | Value |
|--------|-------|
| Total SQL functions in Supabase | 249 |
| Functions referenced in any agent file | 41 (16%) |
| Functions unreferenced | 208 (84%) |
| Agent CLAUDE.md files | 5 of 6 agents |
| Skill files total | 28 |
| Skill files referencing SQL functions | 8 (29%) |
| Skill files using raw SQL only | 20 (71%) |
| ENIAC readiness | 15% (directory exists, 2 skills, no CLAUDE.md) |
| Overall agent fleet readiness | ~55% (identity + skills partial, SQL gap) |

---

*M9 Intel QA — honest assessment, no inflation. The skill layer being built is high quality where it exists. The gap is coverage: 84% of the SQL toolkit is invisible to agents.*
