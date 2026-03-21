# M5 Scoring Machine: Agent Skill Build Audit

**Date:** 2026-03-21
**Machine:** M5 Scoring
**Loop Type:** Agent Skill Build
**Model Version:** v5.2-L96

---

## What Was Built

Three comprehensive skill files created at `mcp-servers/agents/skills/scoring/`:

### 1. `scoring-model.md` (Scoring Model Skill)
Teaches agents how the entire scoring system works:
- Model architecture: base factors, z-score normalization, multiplicative boosts, sigmoid cap
- All 7 base factors with weights (strategic_score highest at 0.20)
- All 17 multipliers with ranges, conditions, and rationale
- Time decay mechanics (0.97^(d-14) after 14 days)
- Sigmoid wall at 8.0 for top-end granularity
- Score confidence interpretation
- How to read `agent_scoring_context()` output
- Multiplier patterns to check (type penalty, verb pattern, portfolio health)
- Score thresholds: >=7 surface, 4-6 low-confidence, <4 context only
- Priority hierarchy: Portfolio > Pipeline > Thesis > Content

### 2. `scoring-tools.md` (Scoring SQL Tools Skill)
Complete reference for every scoring-related SQL function:
- 8 categories: Core scoring, Explanation, Monitoring/Health, Trends, Overrides, Preferences, Individual multipliers, Related functions
- All function signatures with input/output types
- Example queries with expected output shapes
- Common agent workflows: "Is this score right?", "Top actions?", "System healthy?", "What changed?"
- 11 individual multiplier helper functions documented

### 3. `scoring-feedback.md` (Scoring Feedback & Preference Learning Skill)
Teaches agents how to participate in the scoring feedback loop:
- Agent identity requirements (megamind, eniac, datum, cindy, orchestrator)
- 6 feedback types with use cases
- When to write vs. when not to write feedback
- 3 detailed agent feedback examples (Megamind strategic, Cindy obligation, ENIAC research quality)
- Preference learning system: 4 dimensions, running average, outcome deltas
- Verb pattern learning explanation
- Acceptance rate learning
- Full feedback loop architecture diagram
- 7 guardrails documented

---

## System State at Time of Build

| Metric | Value |
|--------|-------|
| Proposed Actions | 31 |
| Total Actions | 144 |
| Health Score | 10/10 |
| Distinct Scores | 31 |
| Score Range | 4.63 - 9.23 |
| Avg Score | 7.41 |
| Score StdDev | 1.58 |
| Top Bucket (9-10) | 12.9% |
| Feedback Records | 2 |
| Preference Rows | 12 |
| Score History Records | 227 |

### Regression Test Results (22 tests)

| Result | Count | Details |
|--------|-------|---------|
| PASS | 20 | All core tests passing |
| FAIL | 2 | preference_weights_safe, confidence_populated |

**Failing tests:**
1. `preference_weights_safe` — 12 preference rows, some with sample_count < 10. These are legitimate early-stage learning rows (2-8 samples). Not a bug — the system needs more user decisions to build confidence. The low-sample rows include "Thesis Update" (2), "Pipeline" (2), "P0" emoji variant (2), "Pipeline/Deals" (4), empty priority (6), "P2" (8).

2. `confidence_populated` — 8 actions with default confidence (0.5). All are OVERDUE obligation-generated actions (IDs 139-146) that lack enriched scoring_factors. These need context enrichment to compute proper confidence.

### Priority Hierarchy (Healthy)
- Portfolio avg: 8.70
- Pipeline avg: 7.16
- Thesis avg: 6.95
- Network avg: 6.56

### Multiplier Activity
- Cindy intelligence: 11 actions with signal
- Thesis momentum: 17 actions with signal
- Portfolio health: 7 actions with signal
- Financial urgency: 1 action with signal
- Key question: 6 actions with match
- Verb pattern: 10 actions with signal
- Interaction coverage: 100%

---

## Version Note

Model version strings are inconsistent:
- `compute_user_priority_score()` comments: v5.2 (has thesis_breadth_multiplier, 17th multiplier)
- `explain_score()` model_version field: 'v5.1-L96'
- `agent_scoring_context()` model_version field: 'v5.1-L96'
- `narrative_score_explanation()` model_version field: 'v5.1-L96'
- `scoring_health` view: 'v5.1-L96'

The code IS v5.2 (thesis_breadth is live as the 17th multiplier), but the version strings weren't all updated. Cosmetic issue, no functional impact.

---

## Files Created

| File | Path | Lines |
|------|------|-------|
| scoring-model.md | `mcp-servers/agents/skills/scoring/scoring-model.md` | ~220 |
| scoring-tools.md | `mcp-servers/agents/skills/scoring/scoring-tools.md` | ~280 |
| scoring-feedback.md | `mcp-servers/agents/skills/scoring/scoring-feedback.md` | ~250 |

---

## Impact

Before this build, no agent had a skill file for scoring. Agents had to query functions blind without understanding the model architecture, multiplier meanings, or how to write feedback. Now all 4 agents (megamind, eniac, datum, cindy) plus the orchestrator have complete documentation of:
- How scores are computed (for reasoning about whether a score is appropriate)
- Every SQL function available (for querying and monitoring)
- How to influence scores (for the agent feedback loop)
- The preference learning system (for understanding user behavior signals)
