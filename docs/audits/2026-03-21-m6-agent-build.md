# M6 IRGI Audit: ENIAC Agent Build

**Date:** 2026-03-21
**Machine:** M6 (IRGI)
**Loop:** Agent file creation (first loop)

---

## Summary

Built the ENIAC research analyst agent from scratch. Prior sessions created 48 SQL
functions (IRGI toolkit) but zero agent files. This session bridges the gap: ENIAC now
has a complete CLAUDE.md identity document, 4 skill files covering all 48 functions,
and a checkpoint format for orchestrator integration.

---

## Files Created (7 files)

### Agent Identity
| File | Size | Purpose |
|------|------|---------|
| `mcp-servers/agents/eniac/CLAUDE.md` | ~17KB | Full agent identity, capabilities, database access, research protocol, quality standards, cross-agent coordination |
| `mcp-servers/agents/eniac/CHECKPOINT_FORMAT.md` | ~1.2KB | Checkpoint state schema for orchestrator handoff |

### Skills (4 files)
| File | Size | Functions Covered | Purpose |
|------|------|-------------------|---------|
| `skills/eniac/eniac-research.md` | ~6KB | `eniac_research_queue`, `eniac_research_brief`, `eniac_save_research_findings` | Research workflow: queue, briefs, persistence |
| `skills/eniac/eniac-search.md` | ~7KB | `agent_search_context`, `balanced_search`, `enriched_balanced_search`, `enriched_search`, `search_across_surfaces`, `search_thesis_context`, `search_content_digests`, `search_thesis_threads` | Cross-surface search with fairness guarantees |
| `skills/eniac/eniac-thesis-analysis.md` | ~8KB | `thesis_health_dashboard`, `thesis_research_package`, `detect_thesis_bias`, `irgi_interaction_thesis_crossref`, `thesis_landscape`, `thesis_momentum_report`, scoring multipliers | Thesis health, bias detection, momentum, cross-refs |
| `skills/eniac/eniac-company-intelligence.md` | ~9KB | `company_intelligence_profile`, `portfolio_deep_context`, `deal_intelligence_brief`, `deal_pipeline_intelligence`, `discover_connections`, `portfolio_intelligence_map`, `portfolio_intelligence_report`, `portfolio_risk_assessment`, `detect_emerging_signals`, `detect_interaction_patterns`, `detect_opportunities`, `network_intelligence_report`, `interaction_intelligence_report`, `scoring_intelligence_report`, `scoring_system_context`, `scoring_validation`, `scoring_regression_test`, `scoring_velocity`, `agent_scoring_context`, `agent_feedback_summary`, `irgi_system_report`, `irgi_benchmark`, `interaction_intelligence_score` | Company/portfolio/deal/detection/scoring/system intelligence |

### Directories Created
- `mcp-servers/agents/eniac/` (agent workspace)
- `mcp-servers/agents/eniac/.claude/` (agent claude config)
- `mcp-servers/agents/eniac/state/` (session state)
- `mcp-servers/agents/skills/eniac/` (skill files)

---

## Architecture Decisions

### 1. Data Model Verification
- Verified `eniac_save_research_findings()` writes to existing tables (companies.page_content,
  thesis_threads.evidence_for/against, entity_connections) rather than a separate findings table
- Updated CLAUDE.md and skill docs to reflect actual data flow
- Documented the `contra_evidence` routing rule for thesis evidence_against

### 2. Function Coverage
- 48 functions documented across 4 skill files
- Every function has: signature, parameters, return type, usage example, and context on when to use
- Functions organized by domain (research ops, search, thesis, company/portfolio)

### 3. Agent Design Pattern
- Follows existing agent pattern (Datum, Megamind, Cindy): identity section, capabilities table,
  database access matrix, protocol instructions, guardrails
- Added ENIAC-specific: research protocol (8-step cycle), quality standards with source hierarchy,
  bias response protocol, conviction guardrail

### 4. Cross-Agent Coordination
- Documented what ENIAC produces for each consumer agent and what it consumes from each producer
- Clear table ownership boundaries with exceptions for eniac_save_research_findings

---

## NOT Done (Requires Separate Session)

### 1. Lifecycle Integration
`lifecycle.py` needs modifications to wire ENIAC as a 5th persistent agent:
- Add `ENIAC_WORKSPACE`, `ENIAC_LIVE_LOG` constants
- Add `eniac_client`, `eniac_busy`, `eniac_needs_restart` to `ClientState`
- Add `_read_eniac_response()`, `send_to_eniac_agent()` bridge tool
- Add `build_eniac_options()` function (model, tools, web MCP, workspace)
- Add ENIAC lifecycle functions (start, stop, restart)
- Add ENIAC startup to `run_agent()` main loop
- Update `create_bridge_server()` to include ENIAC tool
- Update `build_orc_options()` to allow `mcp__bridge__send_to_eniac_agent`
- Update orchestrator CLAUDE.md and HEARTBEAT.md to include ENIAC dispatch

### 2. Research Queue Data
`eniac_research_queue()` may need tuning once real research cycles begin —
priority weights and urgency thresholds should be calibrated against actual usage.

### 3. Embedding Pipeline
`eniac_save_research_findings()` invalidates embeddings (sets to NULL) but doesn't
re-compute them. A separate embedding refresh process is needed.

---

## Quality Assessment

| Dimension | Score | Notes |
|-----------|-------|-------|
| Function coverage | 48/48 | All IRGI + ENIAC + scoring + detection functions documented |
| Skill depth | 8/10 | Every function has examples and context; could add more edge cases |
| Agent identity | 9/10 | Clear boundaries, protocols, guardrails, cross-agent coordination |
| Data model accuracy | 9/10 | Verified against actual function source; corrected initial assumptions |
| Integration readiness | 7/10 | All agent files ready; lifecycle.py integration pending |

---

## Next Loop Priorities

1. **Wire ENIAC into lifecycle.py** — infrastructure task, needs code changes
2. **Update orchestrator CLAUDE.md + HEARTBEAT.md** — add ENIAC dispatch rules
3. **Test research cycle** — run eniac_research_queue, pick item, research, save
4. **Calibrate quality standards** — adjust confidence thresholds based on real output
5. **Add ENIAC to deploy.sh** — ensure eniac/ directory syncs to droplet
