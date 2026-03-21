# M5+M6 Intelligence Optimization Loops 7-10 / 6-10

**Date:** 2026-03-20
**Machine:** M5 (Scoring) Loops 7-10 + M6 (IRGI) Loops 6-10
**Status:** COMPLETE

---

## M5 Loop 7: IRGI Integration into Priority Score
**Result:** IRGI relevance score integrated as a centered scaling factor.
- Mapping: irgi range 0.40-0.89 -> factor range -0.2 to +0.78
- High thesis-aligned actions boosted, low-alignment actions penalized
- All 115 action scores updated

## M5 Loop 8: Multi-Factor Weighted Model
**Result:** Full 6-factor weighted model deployed.

| Factor | Weight | Source |
|--------|--------|--------|
| time_sensitivity | 0.15 | scoring_factors JSON |
| conviction_change_potential | 0.20 | scoring_factors JSON |
| stakeholder/bucket_impact | 0.20 | scoring_factors JSON |
| effort_vs_impact | 0.15 | scoring_factors JSON |
| action_novelty | 0.10 | scoring_factors JSON |
| irgi_relevance | 0.20 | irgi_relevance_score column |

- Auto-normalizes mixed 0-1 / 0-10 scales (111 actions on 0-1, 4 legacy on 0-10)
- Domain adjustments: type boost (portfolio +1.2, network +0.8, thesis -1.2, content -0.8), priority boost, recency decay (30-day window)
- Sigmoid soft cap at edges (never hard-clips)

## M5 Loop 9: Calibration Pass
**Result:** Score distribution verified as healthy.

| Metric | Value |
|--------|-------|
| Range | 5.22 - 9.52 |
| Mean | 7.89 |
| StdDev | 1.01 |
| Distinct buckets | 35 |
| Ceiling hits (>=9.9) | 0 |

**Top 10:** All Portfolio Check-in actions (Unifize, CodeAnt AI, Smallest AI, Highperformr, Confido Health)
**Bottom 10:** All Research/Thesis Update actions (SaaS compression, rural talent, AI provider bias)
**Verdict:** Correctly surfaces portfolio/network actions for user triage, sinks agent-delegable research.

## M5 Loop 10: Preference Learning Verification
**Result:** End-to-end feedback loop verified and integrated.
- `update_preference_from_outcome()`: gold (+0.3), helpful (+0.1), skip (-0.2) outcomes tested
- Running weighted average with sample_count works correctly
- `compute_user_priority_score()` now reads from `preference_weight_adjustments` table
- Fixed NULL propagation bug in SELECT INTO (COALESCE wrapper on separate variable)
- Dimensions tracked: action_type, priority, source, thesis_connection

## M6 Loop 6: Company Embedding Enrichment
**Result:** `embedding_input_companies()` enriched with 5 new fields.

| Field | Records with data | Previously in embedding |
|-------|-------------------|------------------------|
| sector_tags | 1,531 | No |
| type | varies | No |
| sells_to | varies | No |
| venture_funding | varies | No |
| smart_money | varies | No |

- Triggers updated to fire on all new columns
- Embedding input now ~2-3x richer for companies with these fields

## M6 Loop 7: Re-embedding
**Result:** 1,521 companies queued for re-embedding.
- Pipeline processed via pgmq edge function (asynchronous)
- 30 remaining at final check (from 1,447 initially)
- New embeddings include richer semantic content

## M6 Loop 8: Network in Intelligence Functions
**Result:** `suggest_actions_for_thesis()` enhanced with network suggestions.
- New Type 5 suggestion: vector similarity between thesis embedding and network person embeddings
- Tested with Agentic AI Infrastructure thesis: surfaced 2 relevant CTO contacts (similarity 0.68-0.69)
- Function coverage: 3 of 4 key intelligence functions now network-aware
  - `hybrid_search`: had network (5 tables searched)
  - `find_related_entities`: had network (entity_connections + company refs + vector)
  - `suggest_actions_for_thesis`: **NEW** network suggestions added
  - `find_related_companies`: company-only (by design -- companies-to-companies similarity)

## M6 Loop 9: Bias Detection Enhancement
**Result:** `detect_thesis_bias()` enhanced with 3 new checks.

| Check | Description | New? |
|-------|-------------|------|
| confirmation_bias | Zero contra evidence | Existing |
| possible_bias | >5x FOR:AGAINST ratio | Existing |
| source_bias | Single evidence source | Existing |
| stale_evidence | No update in 30+ days | **NEW** |
| conviction_mismatch | High conviction + thin evidence, or Low conviction + strong evidence | **NEW** |
| thin_evidence | <3 total data points (non-New theses) | **NEW** |
| severity | CRITICAL/HIGH/MEDIUM/LOW/OK ranking | **NEW** |

**Current bias state:**
- AI-Native Non-Consumption Markets: **HIGH** (zero contra, New conviction)
- Cybersecurity / Pen Testing: **MEDIUM** (10:1 ratio)
- Agentic AI Infrastructure: **MEDIUM** (5.25:1 ratio)
- All others: OK

Bias flags persisted to `thesis_threads.bias_flags` JSONB column.

## M6 Loop 10: Full IRGI Verification
**Result:** All 8 intelligence functions verified end-to-end.

| Function | Status | Network-aware |
|----------|--------|---------------|
| compute_user_priority_score | PASS | via IRGI |
| score_action_thesis_relevance | PASS | No (thesis<->action) |
| suggest_actions_for_thesis | PASS | YES (new) |
| detect_thesis_bias | PASS | N/A |
| search_content_digests | PASS | N/A |
| search_thesis_threads | PASS | N/A |
| find_related_companies | PASS | No (by design) |
| find_related_entities | PASS | YES |

**Score Independence:** IRGI vs user_priority correlation = **-0.0613** (essentially independent, confirming they measure different dimensions)

---

## Summary of Changes

### Functions Modified
1. `compute_user_priority_score()` -- 6-factor model + IRGI + preference learning
2. `embedding_input_companies()` -- 5 new fields (sector_tags, type, sells_to, venture_funding, smart_money)
3. `suggest_actions_for_thesis()` -- network contact suggestions via vector similarity
4. `detect_thesis_bias()` -- 3 new checks (stale_evidence, conviction_mismatch, thin_evidence) + severity

### Triggers Modified
- `clear_companies_embedding_on_update` -- expanded column list
- `embed_companies_on_update` -- expanded column list

### Data Updated
- 115 action scores re-computed with multi-factor model
- 1,521 company embeddings re-queued (enriched input)
- 8 thesis bias_flags persisted
- Preference learning table tested (test data cleaned)
