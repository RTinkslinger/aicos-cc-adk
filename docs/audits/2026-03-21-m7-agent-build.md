# M7 Megamind Agent Build Audit — 2026-03-21

## Problem Statement

Prior M7 sessions built 45 SQL functions, 4 views, and extensive Postgres-side
intelligence tooling for Megamind. However, the Megamind agent running on the droplet
had **zero knowledge** of these tools. The agent's CLAUDE.md and skill files documented
reasoning protocols (depth grading algorithm, cascade steps, strategic ROI formula) but
contained no reference to the SQL functions that implement those protocols.

**Gap:** Agent knew WHAT to do but not HOW to do it efficiently. It was writing raw
queries from scratch instead of calling pre-built functions.

## What Was Done

### 1. Skills Inventory (Before)

Existing skill files (3):
- `skills/megamind/strategic-reasoning.md` — ROI calculation, diverge/converge, DB table schemas
- `skills/megamind/depth-grading.md` — Auto-grading algorithm, execution prompts, trust ramp
- `skills/megamind/cascade-protocol.md` — Cascade algorithm steps, blast radius, convergence rules

**SQL function references: ZERO**

### 2. New Skill Files Created (4)

| File | Purpose | Key Functions Documented |
|------|---------|------------------------|
| `skills/megamind/strategic-briefing.md` | Briefing pipeline, narrative engine, decision support | `format_strategic_briefing()`, `generate_strategic_briefing()`, `generate_strategic_narrative()`, `latest_briefing()`, `narrative_score_explanation()`, `generate_decision_framework()`, `detect_opportunities()` |
| `skills/megamind/portfolio-risk.md` | Risk assessment, decision queue, convergence simulation, network map | `portfolio_risk_assessment()`, `actions_needing_decision_v2()`, `simulate_convergence()`, `compute_portfolio_strategic_score()`, `recalibrate_strategic_scores()`, `apply_strategic_recalibration()`, `strategic_network_map()` |
| `skills/megamind/depth-automation.md` | Auto-refresh grades, stale dismissal, cascade dedup | `auto_refresh_depth_grades()`, `auto_dismiss_stale_actions()`, `cascade_dedup_guard()`, `regrade_on_strategic_change()` [trigger] |
| `skills/megamind/cascade-functions.md` | Cascade creation, impact analysis, obligation cascades | `create_cascade_event()`, `cascade_impact_analysis()`, `process_obligation_cascade()`, `auto_generate_obligation_followup_actions()`, obligation health/audit/fulfillment functions |

### 3. CLAUDE.md Updates

Replaced the incomplete section 12 (5 function stubs) with:

- **Section 12: Skills Reference** — Full skill file index with "when to load which skill" matrix
- **Section 13: SQL Functions Inventory (COMPLETE)** — All 45 functions organized by category (Briefing, Decision, Portfolio, Scoring, Depth Automation, Cascade, Obligation, Triggers, Views) with args, returns, and purpose
- **Section 14: Collaboration Model** — What Megamind reads from other agents, what other agents read from Megamind

### 4. SQL Functions Cataloged

Total functions available to Megamind: **45**

| Category | Count | Key Functions |
|----------|-------|---------------|
| Briefing & Narrative | 6 | `format_strategic_briefing`, `generate_strategic_narrative`, `narrative_score_explanation` |
| Decision & Opportunity | 3 | `actions_needing_decision_v2`, `generate_decision_framework`, `detect_opportunities` |
| Portfolio & Risk | 2 | `portfolio_risk_assessment`, `strategic_network_map` |
| Scoring & Recalibration | 3 | `compute_portfolio_strategic_score`, `recalibrate_strategic_scores`, `apply_strategic_recalibration` |
| Depth Automation | 3 | `auto_refresh_depth_grades`, `auto_dismiss_stale_actions`, `cascade_dedup_guard` |
| Cascade & Convergence | 4 | `create_cascade_event`, `cascade_impact_analysis`, `simulate_convergence`, `generate_strategic_assessment` |
| Obligation | 11 | `process_obligation_cascade`, `auto_generate_obligation_followup_actions`, obligation health/audit/fulfillment suite |
| Triggers | 2 | `regrade_on_strategic_change`, `process_cascade_event` |

Views: 4 (`strategic_briefing`, `decision_frameworks`, `megamind_convergence`, `strategic_recommendations`)

## Skill File Total (After)

| Skill File | Lines | Status |
|------------|-------|--------|
| `strategic-reasoning.md` | 248 | Existing — unchanged |
| `depth-grading.md` | 272 | Existing — unchanged |
| `cascade-protocol.md` | 314 | Existing — unchanged |
| `strategic-briefing.md` | 148 | NEW |
| `portfolio-risk.md` | 151 | NEW |
| `depth-automation.md` | 131 | NEW |
| `cascade-functions.md` | 186 | NEW |

## Impact

**Before:** Megamind agent had to construct all queries from scratch using raw SQL patterns
in its CLAUDE.md. No awareness of pre-built functions. Strategic briefing, cascade impact
analysis, convergence simulation, portfolio risk assessment — all required manual query composition.

**After:** Megamind knows about all 45 SQL functions, when to use each, and how to chain them
in workflows. Each skill file includes:
- Function signatures with exact parameter names and types
- Return types (TABLE, jsonb, text, integer, void)
- Bash invocation examples ready to copy
- Workflow sequences showing how functions chain together
- "When to use" decision matrix

The agent can now call `cascade_impact_analysis(event_id)` instead of writing 30-line
blast radius queries. It can call `simulate_convergence(decisions)` before committing
cascade results instead of manually checking convergence math. It can generate formatted
briefings via `format_strategic_briefing()` instead of string-building in its response.

## Files Modified

- `/mcp-servers/agents/megamind/CLAUDE.md` — Sections 12-14 replaced/added
- `/mcp-servers/agents/skills/megamind/strategic-briefing.md` — NEW
- `/mcp-servers/agents/skills/megamind/portfolio-risk.md` — NEW
- `/mcp-servers/agents/skills/megamind/depth-automation.md` — NEW
- `/mcp-servers/agents/skills/megamind/cascade-functions.md` — NEW

## User Feedback

No M7 feedback found in `get_machine_feedback('M7')`.

## Next Loop Priorities

1. **Deploy to droplet** — `deploy.sh` syncs `mcp-servers/agents/` to `/opt/agents/`. After deploy, Megamind will pick up new skills on next session start.
2. **Test function calls** — Verify Megamind can load and use the new skill files in a real depth grading or cascade session.
3. **Cross-machine sync** — Notify M1 WebFront that new views/functions are available for dashboard integration (especially `megamind_convergence`, `strategic_recommendations`).
4. **Missing skill: Cindy signal integration** — Megamind reads Cindy's obligation and interaction signals but has no skill file documenting the interaction data model. Next loop should add `skills/megamind/cindy-signals.md`.
