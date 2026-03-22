# M9 Intel QA — Loop 1 Audit Report
**Date:** 2026-03-22 | **Auditor:** M9 Intel QA | **Method:** Full Supabase data pull + feedback cross-reference + agent CLAUDE.md review

---

## 1. HONEST SYSTEM SCORECARD

| Dimension | Score | Rationale |
|-----------|-------|-----------|
| **Data Quality** | 4.5/10 | 66/4,567 companies (1.4%) have rich content (>500 chars). Average content length 170 chars. This is skeletal. 715 WhatsApp conversations ingested but not harmonized with network/companies. |
| **Connection Quality** | 2.5/10 | 23,716 connections — 99.9% single-evidence. 10,655 are vector_similar (noise). Only 15 interaction_linked connections have >1 evidence. The connection graph is almost entirely auto-generated noise, not intelligence. |
| **Scoring Quality** | 6.5/10 | Accepted avg 8.13 vs Dismissed avg 6.71 — separation exists (1.42 gap) but stddev 2.31 shows reasonable spread. 134/145 actions have relevance scores. User priority score stddev 1.92. Missing: depth grade coverage (142 auto_depth=1, only 3 auto_depth=4). |
| **Obligation Quality** | 5.0/10 | 16 obligations, all have suggested_actions. But: 0 active (all escalated/overdue/fulfilled/pending), 7 overdue with blended_priority=1.0 (ALL maxed out — no differentiation). FB-18 showed Ayush appearing 3x with duplicate obligations. Obligation ID 84 for Quivly says "deal negotiations" despite being a portfolio company (FB-20 regression). |
| **Intelligence Quality** | 4.0/10 | User rated 3-4/10 on 2026-03-21. System self-graded 8.3/10. The gap is the story. Interactions: only 23 total in the interactions table (tiny). Cindy processed all 23 but there are 715 WhatsApp conversations NOT in the interactions table. The intelligence layer has almost no raw material to work with. |
| **WebFront Quality** | 5.0/10 | 3 P0 bugs unaddressed (deep research button dead x2, founder misclassification, /network/2455 bug). Multiple items "marked as addressed" without verified fix (FB-17, FB-18, FB-19, FB-20). Could not verify via Playwright due to browser conflict. |
| **Cron Health** | 7.5/10 | 25 crons active, 97.9% success rate (4,040/4,127 in 24h). 87 failures — mostly connection pool pressure (deadlock in proactive_refresh_stale_entities, connection failed errors). Down from 490+62 failures previously. Improved but deadlock in rescore_related_actions persists. |
| **Agent CLAUDE.md Quality** | 6.0/10 | Datum 9/10, Megamind 9/10 (objective-driven, clean). Cindy 5/10 — 639+ lines of procedural pipeline instructions (Section 4: 4 full pipeline step-by-step scripts, Section 5: full algorithm with code). Content 6/10 — Phase 1/2/3 are procedural scripts. ENIAC 7/10 — mostly objective-driven with function catalog, but Section 4 Research Protocol is step-by-step script. |
| **Embedding Health** | 9.5/10 | Companies 4,567/4,567 (100%), Network 3,513/3,513 (100%), Portfolio 142/142 (100%), Thesis 8/8 (100%). This is excellent and stable. |
| **Feedback Infrastructure** | 7.0/10 | user_feedback_store has 20 items. 3 fully unaddressed (FB-21/22/23). Several "addressed" items have processed_by arrays but no verified fix. Feedback timeline exists for 3/21 and 3/22. Machine feedback routing works. |
| **OVERALL SYSTEM** | **5.2/10** | Weighted: intelligence quality and data quality drag the entire system down. Infrastructure is solid (embeddings, crons, scoring model). But the user-facing product — the intelligence that comes out — is still thin because the data going in is thin. |

---

## 2. CRITICAL FINDINGS

### Finding 1: Data Richness Crisis (BLOCKS EVERYTHING)
- **4,501 out of 4,567 companies** have content under 500 characters. Average 170 chars.
- This means 98.6% of company records are essentially name + one-line description.
- Every machine that queries company data gets garbage in → garbage out.
- FB-3 flagged this. Still unaddressed. M12 enriched portfolio research files (142/142) but the 4,400+ non-portfolio companies remain skeletal.
- **Impact:** Scoring, search, intelligence, thesis matching — all degraded by thin data.

### Finding 2: Connection Graph is 99.9% Noise
- 23,701 out of 23,716 connections have evidence_count = 1 (single evidence).
- 10,655 are vector_similar (auto-generated embedding proximity — not real relationships).
- 3,093 are sector_peer (auto-generated).
- 3,067 current_employee and 2,950 past_employee (from Notion sync, reasonable but still single-evidence).
- Only 15 interaction_linked connections have evidence_count > 1 (real multi-evidence connections).
- **FB-4 is still accurate:** connection noise ratio is WORSE than previously reported (99.9% single-evidence vs 24.9% evidence-based reported earlier — the earlier metric likely measured something different).

### Finding 3: Three P0 User Bugs Still Open
- **FB-21/15:** Deep research button dead across ALL portfolio pages. Reported TWICE. Data exists (142 research files ingested), button not wired. processed_by = [] in Supabase.
- **FB-22:** Founder misclassification. DeVC collective members shown as founders. processed_by = [].
- **FB-23:** /network/2455 bug. Network record exists (Rohan Joshi, Co-founder, Stellon Labs). processed_by = []. Likely a rendering issue on the WebFront.

### Finding 4: Obligation Priority Inflation
- ALL top obligations have blended_priority = 1.0 (maximum). No differentiation.
- 7 obligations are overdue (some since February/early March). None dismissed or resolved.
- Obligation dedup may still have issues — FB-18 reported Ayush appearing 3x. Current data shows 3 Ayush Sharma obligations (IDs 67, 68, 69) — all different descriptions but all maxed at priority 1.0.

### Finding 5: Interactions Table is Tiny
- Only 23 interactions in the `interactions` table. All cindy_processed = TRUE.
- 715 WhatsApp conversations exist in `whatsapp_conversations` but are NOT in the `interactions` table.
- This means Cindy's intelligence layer (obligation detection, signal extraction, context assembly) has almost no input data.
- The WhatsApp → interactions pipeline is broken or never built.

### Finding 6: Agent CLAUDE.md Script-vs-Objective Audit
| Agent | Score | Issue |
|-------|-------|-------|
| **Datum** | 9/10 | Objective-driven. 6 clear objectives, 231 lines. Clean. |
| **Megamind** | 9/10 | Co-strategist identity, 4 objectives, 342 lines. Clean. |
| **ENIAC** | 7/10 | Mostly good. Function catalog is useful reference. Section 4 "Research Protocol" is a step-by-step script (8-step numbered procedure). Should be objectives: "Find gaps, research them, persist findings, cross-reference theses." |
| **Content** | 5.5/10 | Section 4 "How You Receive Work" is a full step-by-step script (Phase 1/2/3 with numbered steps, SQL templates). Section 8 "Analysis Framework" is objective-driven (good). Net: half script, half objectives. |
| **Cindy** | 4.5/10 | 639+ lines. Sections 4.1-4.4 are full procedural pipelines (8-step numbered scripts for each surface). Section 5 is a 6-tier algorithm with code snippets. Section 6 is a scoring formula. Section 7.5 is a 6-step obligation detection procedure. The agent is being treated as a script runner, not a reasoner. Should be: "Observe interactions, extract intelligence, detect obligations, route signals." The HOW should be in skills, not CLAUDE.md. |

### Finding 7: Deadlock Still Occurring
- `proactive_refresh_stale_entities(7)` hit a deadlock in the last 24h:
  - Process 247959 and 247956 deadlocked on `actions_queue` via `rescore_related_actions()`.
  - This is a known issue that was supposedly fixed (connection pool healed) but the root cause — concurrent scoring of the same rows — persists.

---

## 3. VERIFICATION OF "ADDRESSED" ITEMS

Items marked "ADDRESSED" in the feedback tracker that M9 flags as UNVERIFIED:

| FB | Claimed Status | M9 Verification | Issue |
|----|---------------|-----------------|-------|
| FB-17 | ADDRESSED (M1, M8) | UNVERIFIED | "Marked as addressed in context metadata" — no code change evidence, no deploy confirmation |
| FB-18 | ADDRESSED (M1, M8) | PARTIALLY | Obligation dedup logic added to Cindy CLAUDE.md (Section 7.5), but 3 Ayush obligations still exist in DB. UI dedup vs DB dedup unclear. |
| FB-19 | ADDRESSED (M1, M8, M10) | UNVERIFIED | "Marked as addressed" — Intract still has led_by_ids populated in portfolio table. No evidence urgency classification logic changed. |
| FB-20 | ADDRESSED (M1, M8, M10) | PARTIALLY | Quivly obligation ID 84 still says "deal progress — active negotiation detected" despite Quivly being a portfolio company. Portfolio guardrail may exist in code but obligation text wasn't updated. |

---

## 4. SCORING DISTRIBUTION ANALYSIS

| Status | Count | Avg Relevance | Stddev |
|--------|-------|---------------|--------|
| Accepted | 6 | 8.13 | 0.80 |
| Proposed | 23 | 7.78 | 1.04 |
| Done | 3 | 7.34 | 1.26 |
| expired | 11 | 9.33 | 1.61 |
| Dismissed | 102 | 6.71 | 2.52 |

**Assessment:** Separation between Accepted (8.13) and Dismissed (6.71) is 1.42 — reasonable but not strong. The 11 "expired" actions have the HIGHEST average score (9.33) — these are high-relevance actions that nobody acted on and they timed out. This suggests the system is surfacing good actions but the user isn't seeing/triaging them fast enough, or the expiry logic is too aggressive.

Depth grade coverage: 142 actions at auto_depth=1 (scan), only 3 at auto_depth=4 (ultra). 0% user-approved depth grades. The depth grading system exists in DB but is not being used.

---

## 5. HONEST SYSTEM SCORE: 5.2/10

Previous M9 score: 6.9/10. I'm revising DOWN to 5.2/10 because:

1. **Data richness crisis is worse than reported.** 98.6% of companies have skeletal content. This was known but undertreated.
2. **Connection graph is 99.9% noise.** Previously reported as "healed to 8.7" — that metric measured connection pool health, not connection QUALITY. Quality is abysmal.
3. **3 P0 user bugs still open** from 20+ hours ago.
4. **23 interactions in the interactions table** vs 715 WhatsApp conversations not yet piped in. The intelligence layer is starving.
5. **Multiple "addressed" items are unverified.** The tracker overstates fix coverage.

What keeps the score from being lower:
- Embeddings: 100% across all entity types (genuine achievement)
- Cron health: 97.9% success rate
- Scoring model: working with 18 multipliers, reasonable separation
- Infrastructure: 25 crons, 250+ functions, architecture is solid
- WhatsApp pipeline: 715 conversations ingested to dedicated table (data exists, just not piped to intelligence layer)

---

## 6. PRIORITY ACTIONS FOR ALL MACHINES

| Priority | Action | Machine | Why |
|----------|--------|---------|-----|
| **P0** | Wire deep research button on portfolio pages | M1 | Reported TWICE by user. Data exists. Just needs frontend wiring. |
| **P0** | Fix founder vs co-investor classification | M4 | User trust issue. led_by_ids in portfolio table contains non-founders. |
| **P0** | Investigate /network/2455 rendering bug | M1 | User reported explicit bug. Rohan Joshi record exists in DB. |
| **P0** | Pipe whatsapp_conversations into interactions table | M4+M8 | 715 conversations sitting idle. Cindy has 23 interactions to reason over. This is the #1 data bottleneck for intelligence quality. |
| **P1** | Enrich company content (4,501 thin records) | M12+M4 | 98.6% of companies are skeletal. Web enrichment needed. |
| **P1** | Prune noise connections (10,655 vector_similar) | M10 | Connection graph is unusable. Delete or downweight vector_similar connections. |
| **P1** | Fix obligation priority inflation | M8 | All top obligations at blended_priority=1.0. No differentiation = no signal. |
| **P1** | Fix deadlock in rescore_related_actions | M10 | Recurring deadlock on actions_queue. Add row-level locking or serialize. |
| **P2** | Rewrite Cindy CLAUDE.md (script → objectives) | M9 | 639+ lines of procedural scripts. Move pipelines to skill files. CLAUDE.md should be objectives + boundaries only. |
| **P2** | Rewrite Content CLAUDE.md (script → objectives) | M9 | Phase 1/2/3 procedural scripts belong in skill files. |
| **P2** | Verify "addressed" feedback items (FB-17/18/19/20) | M9 | Multiple items claimed as addressed without evidence. Need WebFront verification. |
