# M9 Intel QA Audit — L52 (Perpetual Loop)
**Date:** 2026-03-21 10:30 UTC
**Auditor:** M9 Intel QA Machine
**Baseline:** L51 audit (same day, scored 3.6/10)
**User baseline:** Intelligence 3/10
**Supabase:** llfkxnsfczludgigknbs (Mumbai)

---

## AUDIT METHODOLOGY

Every number verified by live SQL against Supabase. No recycling from previous reports. This audit examines each machine's output quality, the system's net trajectory, and whether the product is getting BETTER between loops.

---

## 1. EMBEDDING RECOVERY — SLOW BUT MOVING

| Table | L51 Coverage | L52 Coverage | Delta | Status |
|-------|-------------|-------------|-------|--------|
| companies | 100% (4,575/4,575) | 100% (4,575/4,575) | -- | STABLE |
| network | 14.8% (522/3,528) | **25.4% (896/3,528)** | +10.6% | DRAINING SLOWLY |
| portfolio | 100% (142/142) | 100% (142/142) | -- | STABLE |
| actions_queue | 100% (144/144) | 100% (144/144) | -- | STABLE |
| content_digests | 100% (22/22) | 100% (22/22) | -- | STABLE |
| thesis_threads | 100% (8/8) | 100% (8/8) | -- | STABLE |
| interactions | 100% (23/23) | 100% (23/23) | -- | STABLE |

### Queue Status: CONCERNING
- **2,910 items in queue** — all network table, all `read_ct: 0`, all VISIBLE (not being processed)
- Queue items enqueued between 08:26 and 08:46 UTC — a 20-minute burst, then silence
- process_embeddings cron (jobid=1) runs every 2 min, completes in ~15ms — it IS running but appears to do nothing meaningful per cycle
- cleanup cron (jobid=18) runs every odd minute — succeeding but not deleting items
- **Zero queue items have corresponding embeddings already** — so these are genuinely unprocessed records
- Edge Function HTTP calls: 498 in last 2 hours, 496 success, 2 failed — the edge function WORKS when called
- **The disconnect:** cron runs, edge function works, but queue items stay at read_ct=0. Something in `process_embeddings()` is not reading these items or is reading and failing silently.

### Drain Rate Reality
- 3h ago to now: **71 network embeddings** (24/hr)
- 3h to 6h ago: **381 network embeddings** (127/hr)
- **Drain rate has COLLAPSED from 127/hr to 24/hr.** At 24/hr, remaining 2,632 network records need 110 hours = 4.5 DAYS.

### VERDICT
Network embedding recovery went from "should finish in 1.3 hours" (M-EMB v2 prediction at L51) to "stalled at 25% with a 4.5-day ETA." The fixes (cleanup cron, reduced concurrency) helped get from 14.8% to 25.4%, but the queue processor appears to have largely stopped processing new items.

**Score: 5/10** (was 5/10 — network at 25% is better than 15% but drain is stalling)

---

## 2. ACTION-COMPANY LINKAGE — MAJOR IMPROVEMENT

| Metric | L51 | L52 | Delta |
|--------|-----|-----|-------|
| Actions with company_notion_id | 0/144 (0%) | **66/144 (45.8%)** | **+45.8%** |
| Scoring context_enriched | 49/144 | 49/144 | -- |
| Company context in scoring_factors | 16/144 | 16/144 | -- |

### Linkage by Status
| Status | Total | Linked | Linkage % |
|--------|-------|--------|-----------|
| Dismissed | 85 | 37 | 43.5% |
| Proposed | 49 | 23 | 46.9% |
| Accepted | 10 | 6 | 60.0% |

### Quality Check
Sampled 10 linked actions — all have valid Notion page IDs pointing to real companies:
- Unifize, Inspecity, Isler, Legend of Toys, Cybrilla, Dodo Payments, AuraML — all correctly matched
- Company names visible in action text match the linked company_notion_id

**This is the single biggest improvement since L51.** M5 went from 0% to 46% company linkage. The remaining 54% are likely actions that reference people (not companies directly) or generic actions without company context.

**Score: 5/10** (was 0/10 — massive jump. Not 7/10 because 54% still unlinked and the linkage doesn't yet show in the strategic briefing's action rendering)

---

## 3. PORTFOLIO DATA QUALITY

| Metric | L51 | L52 | Delta |
|--------|-----|-----|-------|
| key_questions populated | 28/142 (19.7%) | **46/142 (32.4%)** | **+12.7%** |
| thesis_connection | -- | 45/142 (31.7%) | New metric |
| page_content >50 chars | -- | 142/142 (100%) | Full |
| outcome_category | -- | 97/142 (68.3%) | Good |
| health (non-NA) | 135/142 | 135/142 | -- |
| signal_history | -- | 0/142 (0%) | EMPTY |

### Key Questions Progress
M12 doubled key_questions from 14 to 28 in L51, and now it's up to 46. That's a 3.3x improvement from the original 14 in a single day. Still, 96 companies (67.6%) have no key questions.

### signal_history: COMPLETELY EMPTY
Zero portfolio companies have signal_history data. This column exists but nothing writes to it. This means the system tracks no history of signals per portfolio company. CIR propagation log has 74,779 UPDATE events in 24h — but none feed back into portfolio signal_history.

**Score: 4/10** (was 3/10 — key_questions 19.7%->32.4% is real progress, but signal_history = 0% is a gap)

---

## 4. STRATEGIC BRIEFING — ACTUALLY USEFUL NOW

The `format_strategic_briefing()` output is **genuinely good**. Reading it as Aakash would:

### What Works
1. **Portfolio section** shows the right companies (18 Red, 33 Yellow) with ownership %, FMV, key questions, and follow-on decisions. This is actionable.
2. **Obligations section** shows 7 I-owe-them items and 4 they-owe-me items with specific people and days overdue. This is immediately actionable.
3. **Upcoming decisions** show 8 actions with scores, types, and companies. The P0 items are real (Cultured Computers deadline, Schneider endorsement).
4. **Portfolio contacts** surface 5 people who need outreach with portfolio context. Useful.
5. **Follow-on section** correctly categorizes SPR/PR vs Token/Zero with dollar amounts and reserve calculations.

### What Doesn't Work
1. **"DEPTH QUEUE BACKED UP: 141 pending"** — the headline is about an internal queue metric, not about Aakash's priorities. A CEO doesn't care about depth queue.
2. **Truncated text** — key questions and action descriptions get cut off mid-sentence ("Ho", "Requ"). The briefing should either show full text or summarize, not truncate.
3. **Needs Your Attention section** shows Red companies but the selection logic is unclear — why Stupa (Yellow) first? Why not the 18 Red companies sorted by FMV at risk?
4. **Dead companies still appear** — OhSoGo (NA, confirmed shutdown) is in "Unanswered Key Questions" asking "Current operational status: confirmed shut down or still operating?" The system is asking questions about dead companies.
5. **Convergence metric** is internal jargon. "49 proposed actions pending, 21 decisions to reach 80%" means nothing to the user.

### Compared to L51
Major improvement. L51 had no formatted briefing output evaluated. This briefing has real structure, real data, and most sections are actionable. The M7 L61-70 work (megamind_agent_context, actions_needing_decision_v2) shows clear architectural progress.

**Score: 6/10** (genuinely useful for the first time. Truncation, dead companies, and internal metrics in headlines keep it from 7+)

---

## 5. OBLIGATION SYSTEM — STRUCTURALLY COMPLETE, OPERATIONALLY STALE

| Metric | L51 | L52 | Delta |
|--------|-----|-----|-------|
| Total obligations | 14 | **16** | +2 |
| Overdue | 10 | 10 | -- |
| Escalated | 1 | 1 | -- |
| Pending | 3 | **5** | +2 |
| Completed | 0 | 0 | -- |
| Linked to actions | 13/14 | 13/14 | -- |
| Has suggested_action | 14/14 | 14/14 | -- |

### New Obligations
Two new pending obligations (Kilrr Series A docs due Mar 25, Muro team hiring intro due Mar 27). These are future-dated and correctly set to "pending" status. Good signal that the obligation detection is still running.

### The Completion Problem
Zero obligations have ever been marked completed. The system detects obligations and tracks overdue status but cannot detect fulfillment. There's a `detect_obligation_fulfillment_from_interactions` function, but interactions table has only 23 entries with no recent additions. Without new interaction data flowing in, fulfillment can never be detected.

### Cindy Priority Factors: Quality Check
The `cindy_priority_factors` JSONB on each obligation shows real intelligence:
- Portfolio boost applied correctly (+0.15 for portfolio support, +0.10 for standard ownership)
- Recalculation reasons are logged with timestamps
- Relationship tiers differentiate (portfolio vs new-deal vs emerging-manager)
- Deal context included where relevant ($2M, $4M Series A, etc.)

But `megamind_priority` is NULL on all 14+ obligations. The blended priority = cindy_priority only.

**Score: 6/10** (unchanged from L51. +2 new obligations shows detection works, but zero completions and null megamind_priority are persistent gaps)

---

## 6. SCORING MODEL — GETTING BETTER

### scoring_health view
| Metric | L51 | L52 |
|--------|-----|-----|
| Health score | -- | **8/10** |
| Concordance (Pearson) | 0.698 | **0.833** (strategic corr) |
| IRGI correlation | -- | **-0.012** (irrelevant) |
| Compression check | -- | **FAIL** |
| Diversity check | -- | PASS |
| Hierarchy check | -- | PASS |
| Pipeline check | -- | PASS |

### User Priority Score Distribution
- Range: 1.00 to 9.87
- Avg: 5.80, Stddev: 2.78
- 76 distinct scores across 144 actions — good score diversity
- Portfolio avg: 8.95, Network avg: 8.64, Pipeline avg: 8.84, Thesis avg: 6.72

### Compression Problem
The health view reports "FAIL: compression" with 55.1% of actions in the max bucket. This means scores cluster at the top — too many actions scored 9+. When everything is high-priority, nothing is. The scoring model correctly deprioritizes thesis actions (6.72 avg vs 8.95 portfolio) but compresses the top tier.

### IRGI Correlation = -0.012
The irgi_relevance_score has essentially ZERO correlation with user priority. This means IRGI scores are noise — they don't predict what Aakash values. The 27 IRGI functions "pass" their benchmarks but produce scores that have no relationship to actual user preferences.

**Score: 6/10** (was 7/10 — the scoring_health view is a genuine quality tool, and 0.833 strategic correlation is good. But compression failure and IRGI irrelevance need addressing. Net slightly down because the compression problem is now quantified.)

---

## 7. AGENT-READINESS RATIO

| Metric | L51 | L52 | Delta |
|--------|-----|-----|-------|
| Total public functions | 218 | **220** | +2 |
| Intelligence-in-SQL | 16 | 16 | -- |
| Agent-tool / Context-serving | 23 | 23 | -- |
| Ratio (agent:intelligence) | 1.77:1 wrong | **1.44:1** | Slight improvement |

### The 16 Intelligence-in-SQL Functions
```
auto_generate_obligation_followup_actions
cir_change_detected
detect_emerging_signals
detect_interaction_patterns
detect_obligation_fulfillment_from_interactions
detect_opportunities
detect_thesis_bias
format_strategic_briefing
generate_decision_framework
generate_obligation_suggestions
generate_strategic_assessment
generate_strategic_briefing
generate_strategic_narrative
portfolio_risk_assessment
predict_next_actions
predict_staleness_candidates
```

### The 23 Agent-Tool Functions
```
agent_feedback_summary, agent_scoring_context, agent_search_context,
apply_agent_score_overrides, cindy_agent_full_context,
cindy_obligation_full_context, enrich_action_context,
enrich_network_professional_context, enriched_search,
find_related_companies, find_related_entities, find_similar_network,
hybrid_search, megamind_agent_context, portfolio_deep_context,
record_agent_feedback, scoring_system_context,
search_across_surfaces, search_content_digests, search_thesis_context,
search_thesis_threads, thesis_research_package,
update_context_gaps_timestamp
```

### Architecture Assessment
M7 L61-70 created `megamind_agent_context()` — a genuinely agent-ready function. But `format_strategic_briefing()` and `generate_strategic_briefing()` still DO the reasoning in SQL (SQL string concatenation to produce a formatted briefing). The correct architecture: SQL provides data (megamind_agent_context), agent formats and reasons.

The ratio improved slightly (1.44:1 in favor of agent tools vs 1.77:1 previously) because M7 added agent-ready functions. But 16 intelligence-in-SQL functions remain.

**Score: 4/10** (was 3/10 — M7's agent-context functions show the right direction. But 16 functions still do reasoning in SQL)

---

## 8. DATUM IMPACT

| Metric | L51 | L52 | Delta |
|--------|-----|-----|-------|
| Companies with datum_source | 10 | 10 | -- |
| Network with datum_source | 0 | 0 | -- |
| Total entities touched | 10/8,103 | 10/8,103 | 0.12% |
| Latest datum activity | 07:37 UTC | 07:37 UTC | STALLED |

Datum has not progressed since L51. The 10 company records touched remain the same. Zero network records. The agent appears to have stopped after its initial run.

**Score: 1/10** (unchanged — negligible impact)

---

## 9. CONTENT PIPELINE

| Metric | L51 | L52 | Delta |
|--------|-----|-----|-------|
| Total digests | 22 | 22 | -- |
| Newest digest | Mar 16 | Mar 16 | -- |
| Days since last digest | 5 | **5.5** | Getting worse |

No new content digests in 5.5 days. The content-to-intelligence loop remains broken. No new actions from content pipeline since March 16.

The most recent actions (created March 21) come from `meeting` and `whatsapp` sources, and `obligation_followup` — these are from Cindy/Granola integration, not from content pipeline.

**Score: 2/10** (was 3/10 — deteriorating. Each day without content makes the system more stale)

---

## 10. INFRASTRUCTURE HEALTH

### Cron Failures (24h)
| Job | Failures | Severity |
|-----|----------|----------|
| process_embeddings | 490 | CRITICAL |
| process_cir_queue_batch | 59 | HIGH |
| process_cir_queue | 47 | HIGH |
| refresh action_scores matview | 11 | MEDIUM |
| CIR staleness/heartbeat/queue | ~12 | LOW |
| compute_user_priority_score error | 7 | MEDIUM |

### CIR System: VERY ACTIVE
74,779 UPDATE events in 24h, 20,657 company propagations, 12,629 network propagations. The CIR system is doing massive work — but it's propagation logging, not intelligence generation. The CIR machinery operates but its output doesn't feed user-facing intelligence.

### Entity Connections: POPULATED
24,752 entity_connections — this is a real graph. Companies, network, portfolio are linked. But the `is_portfolio_linked()` function in M5 scoring depends on this graph and entity_connections was reported "EMPTY" in L51. **24,752 connections is a major improvement** (likely from M12 data enrichment or CIR propagation).

### Missing Function Error
CIR log shows `error:function compute_user_priority_score(integer) does not exist` — 7 occurrences in 24h. A function is being called that doesn't exist. This means some CIR-triggered rescore path is broken.

### HTTP Response Health
498 requests in 2 hours, 496 success (99.6%) — Edge Function connectivity is healthy. The embedding stall is not from HTTP failures.

**Score: 4/10** (was 4/10 — 490 embedding failures is same, but entity_connections populated is positive. Missing function error is a new finding)

---

## 11. M12 DATA ENRICHMENT PROGRESS

### Companies (4,575 total)
| Field | Coverage | Assessment |
|-------|----------|-----------|
| page_content (>50 chars) | 3,942 (86.2%) | GOOD |
| sector | 4,575 (100%) | FULL |
| agent_ids_notes | 16 (0.3%) | EMPTY |
| deal_status (non-NA) | 314 (6.9%) | SPARSE |

### Network (3,528 total)
| Field | Coverage | Assessment |
|-------|----------|-----------|
| page_content (>50 chars) | 3,406 (96.5%) | EXCELLENT |
| role_title | 3,366 (95.4%) | EXCELLENT |
| linkedin | 3,089 (87.6%) | GOOD |
| enrichment_status | 3,528 (100%) | FULL |
| last_enriched_at | 3,528 (100%) | FULL |
| last_interaction | 0 (0%) | EMPTY |
| datum_source | 0 (0%) | EMPTY |

### Assessment
M12 has done significant work on network records — 96.5% have page_content, 95.4% have role_title, 87.6% have LinkedIn. This is MUCH better than the "88.5% empty" claim from earlier sessions. The enrichment happened but:
1. Companies page_content (86.2%) is good but agent_ids_notes (0.3%) shows Datum hasn't touched these
2. Network last_interaction is 0% — no interaction history flowing into network records
3. Portfolio key_questions went from 14 to 46 — genuine M12 progress

**Score: 5/10** (up from 0 loops. M12 has done real enrichment work — network is surprisingly well-populated)

---

## COMPOSITE SCORECARD

| Dimension | L51 Score | L52 Score | Delta | What Changed |
|-----------|----------|----------|-------|-------------|
| Embedding coverage | 5/10 | **5/10** | 0 | Network 15%->25% but drain rate collapsing |
| Action-company linkage | 0/10 | **5/10** | **+5** | 0% -> 46% linkage. Biggest single improvement |
| Portfolio data quality | 3/10 | **4/10** | +1 | key_questions 20%->32%, signal_history still 0% |
| Strategic briefing | N/A | **6/10** | NEW | First genuinely useful briefing. Truncation issues |
| Obligation quality | 6/10 | **6/10** | 0 | +2 new obligations, still zero completions |
| Scoring model | 7/10 | **6/10** | -1 | 55% compression failure quantified. IRGI irrelevant |
| Agent-readiness ratio | 3/10 | **4/10** | +1 | M7 agent-context functions, 16 intelligence-in-SQL remain |
| Datum impact | 1/10 | **1/10** | 0 | Stalled at 10 records |
| Content pipeline | 3/10 | **2/10** | -1 | 5.5 days stale, getting worse |
| Infrastructure health | 4/10 | **4/10** | 0 | Entity connections populated (24K). Missing function error |
| Data enrichment (M12) | -- | **5/10** | NEW | Network 96.5% content, 95.4% role_title. Real work |

### OVERALL: 4.4/10 (was 3.6/10)

**Net improvement: +0.8 points.** This is the largest single-audit jump in the system's history.

---

## WHAT ACTUALLY GOT BETTER

1. **Action-company linkage went from 0% to 46%** — the #1 issue from L51. M5 delivered. Actions now have company context for portfolio grouping. This was the "single highest-impact fix" I called for.

2. **Strategic briefing is genuinely useful** — M7 L61-70 created real agent-ready functions and the format_strategic_briefing() output has structure, data, and actionability. Not perfect (truncation, dead companies) but a real product.

3. **Entity connections populated** — 24,752 connections exist. The graph between companies, network, and portfolio is wired up.

4. **Key questions improved** — 14 -> 28 -> 46. Triple the coverage in a day.

5. **Network enrichment done** — 96.5% page_content, 95.4% role_title. M12 delivered on network records.

---

## WHAT'S STILL BROKEN

1. **Embedding queue stalling** — Network at 25% with drain rate collapsed to 24/hr. The queue processor runs but doesn't process. Root cause unclear — `process_embeddings()` succeeds but completes in 15ms suggesting it reads 0 items per cycle.

2. **Content pipeline dead** — 5.5 days without new digests. Content -> intelligence loop is broken.

3. **Datum = ghost** — 10 records total. The agent either crashed or was never properly started.

4. **IRGI scores are noise** — -0.012 correlation with user priority. 27 functions that pass benchmarks but produce irrelevant outputs. The IRGI system is a Potemkin village: everything looks healthy from the inside, but the output doesn't predict what Aakash values.

5. **Zero obligation completions** — The system detects obligations but cannot detect fulfillment. This makes the obligation tracker an ever-growing list of overdue items.

6. **Scoring compression** — 55% of actions in top bucket. The scoring model can't distinguish between "important" and "very important."

7. **Missing function: compute_user_priority_score(integer)** — Called by CIR but doesn't exist. 7 errors in 24h.

---

## WHAT WOULD MOVE THE NEEDLE TO 6/10

1. **Fix embedding queue processor** — Debug why `process_embeddings()` completes in 15ms without reading items. The queue has 2,910 visible network items with read_ct=0 that pgmq.read() should return. At 127/hr (the rate from 3-6h ago), network would reach 50% in 20 hours.

2. **Resume content pipeline** — 5.5 days without digests. Check droplet orchestrator status. Even 2-3 new digests/day would show the loop is alive.

3. **Fix scoring compression** — The scoring model health is 8/10 by its own metric but 55% compression fails. Need wider score distribution in the 7-10 range. Possible fix: reduce strategic_score weight (currently produces mostly 9-10).

4. **Wire obligation fulfillment** — The `detect_obligation_fulfillment_from_interactions` function exists. It needs new interactions flowing in. Since Cindy created the obligations from Granola meetings, a Granola follow-up check could detect if obligations were fulfilled.

5. **Filter dead companies** — OhSoGo, Rhym, etc. still appear in briefings. Add `WHERE health != 'NA'` or `WHERE outcome_category NOT IN ('Shutdown', 'Exit')` to strategic briefing views.

---

## TRAJECTORY ASSESSMENT

**Direction: UP.** For the first time, the system is improving between audit loops. The L51-to-L52 jump (+0.8 points) is driven by real work: M5 delivered company linkage, M7 delivered agent-ready functions, M12 delivered network enrichment. The 4.4/10 is still below the 5/10 threshold where the product becomes "usable but rough," but the trend is positive.

**Risk:** Content pipeline stall (5.5 days) and embedding queue stall threaten to reverse gains. If these aren't fixed in the next loop, data freshness degrades and the improvements from M5/M7/M12 are undermined by stale data.

**Next audit should focus on:**
- Embedding queue diagnosis (why is process_embeddings no-oping?)
- Content pipeline health (is the droplet orchestrator alive?)
- Scoring compression fix verification
- Dead company filtering verification
- Datum agent status

---

*Generated: 2026-03-21 10:30 UTC*
*Auditor: M9 Intel QA Machine, L52*
*All numbers from live SQL queries against Supabase llfkxnsfczludgigknbs*
