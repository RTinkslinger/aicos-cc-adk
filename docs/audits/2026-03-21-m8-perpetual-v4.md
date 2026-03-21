# M8 Cindy Machine -- Perpetual Loop v4 Audit
**Date:** 2026-03-21 | **Loops:** L91-94 | **Status:** COMPLETE

## Executive Summary

4 loops responding to user feedback on the home page portfolio health section. Created `cindy_companies_needing_attention()` -- a composite scoring function that ranks portfolio companies by overdue obligations, P0 actions, health status, interaction recency, deal signals, and ops priority. Audited the daily briefing v3 ONE THING logic and found a ranking flaw. Analyzed 23 network creation suggestions for auto-creation safety. Documented the cross-source multi-channel gap.

**User feedback:** "Portfolio health section on home page -- companies I'm neither scheduled to meet, prep would be for just before a meeting. List should show companies with critical P0 actions."

**Key insight from feedback:** The home page attention list should NOT show companies because they're scheduled for meetings (that's meeting prep, handled at meeting time). It should show companies needing proactive attention NOW -- overdue obligations, P0 actions, Red health with no recent interaction.

## Loop 91: `cindy_companies_needing_attention()`

### New Function Created (Function #51)

**Purpose:** Rank portfolio companies by composite attention score. Feeds the home page "Needs Your Attention" list with Cindy intelligence data.

**Scoring Model (0-100):**

| Signal | Points | Max | Weight |
|--------|--------|-----|--------|
| P0 actions (each) | 15 | 30 | Highest |
| Overdue obligations (each) | 8 (+4 if I_OWE_THEM) | 25 | High |
| Max overdue days | 1 per 3 days | 10 | Medium |
| Health: Red | 20 | 20 | High |
| Health: Yellow | 5 | 5 | Low |
| Ops Priority: P0 | 10 | 10 | Medium |
| Ops Priority: P1 | 5 | 5 | Low |
| No interaction >60d | 10 | 10 | Medium |
| No interaction >30d | 5 | 5 | Low |
| Active deal signals | 5 | 5 | Low |
| Fumes date <30d | 10 | 10 | Medium |

**Threshold:** Score >= 15 triggers attention. Companies below 15 are background-healthy.

**Test Results (top 10):**

| Rank | Company | Score | Health | Reason |
|------|---------|-------|--------|--------|
| 1 | **Unifize** | 50 | Green | 2 P0 actions + P0 ops |
| 2 | **Emomee** | 40 | Red | Red health + P0 ops |
| 3 | **AuraML** | 38 | Green | 3 overdue I_OWE_THEM + deal signals |
| 4 | **Orbit Farming** | 35 | Green | 1 P0 action + P0 ops |
| 5 | **Atica** | 35 | Green | 1 P0 action + P0 ops |
| 6 | **BiteSpeed** | 35 | Red | Red health + P1 ops |
| 7 | **Legend of Toys** | 35 | Green | 1 P0 action + P0 ops |
| 8 | **CodeAnt** | 35 | Green | 1 P0 action + P0 ops + 6 total actions |
| 9 | **YOYO AI** | 35 | Red | Red health + P1 ops |
| 10 | **Terractive** | 35 | Green | 1 P0 action + P0 ops |

**Summary stats:**
- 70 companies scored >= 15 (threshold too low for home page -- use `p_limit` parameter to cap at 5-7)
- 10 companies have P0 actions
- 2 companies have overdue obligations
- 8 Red health companies
- Average attention score: 16.8
- Max attention score: 50 (Unifize)

**Key design decisions:**
1. **Composite scoring, not single-signal filtering.** A Red health company with P0 ops priority (Emomee: 40) should rank above a generic Red health company (Coffeee.io: 30).
2. **I_OWE_THEM overdue > THEY_OWE_ME overdue.** The user's brand is on the line for things they owe. Extra +4 points per I_OWE obligation.
3. **Deal signals boost.** Active deal signals on a company mean there's live momentum that could be helped or harmed.
4. **Excludes dead/exited companies.** Only active portfolio.
5. **Returns obligation + action details.** The frontend can render inline action items.

**Function signature:** `cindy_companies_needing_attention(p_limit INT DEFAULT 10) RETURNS JSONB`

**Return shape:**
```json
{
  "generated_at": "...",
  "total_scored": 119,
  "threshold": 15,
  "companies": [
    {
      "portfolio_id": 156,
      "company": "Unifize",
      "company_id": 3604,
      "health": "Green",
      "ops_prio": "P0",
      "attention_score": 50,
      "reason": "2 P0 actions",
      "signals": { "p0_actions": 2, "overdue_obligations": 0, ... },
      "obligations": [],
      "actions": [{ "id": 50, "action": "...", "priority": "P0" }]
    }
  ],
  "summary": {
    "companies_needing_attention": 70,
    "companies_with_p0_actions": 10,
    "companies_with_overdue": 2,
    "red_health_total": 8
  }
}
```

**Performance:** Not yet benchmarked (first run succeeds, sub-second).

### How M1 Should Consume This

The home page `page.tsx` currently builds `portfolioAttentionList` by string-matching action text against portfolio company names (lines 100-146). This is fragile -- misses companies whose names don't appear in the action text.

**Recommended change for M1:**
1. Add a query function: `fetchCompaniesNeedingAttention()` that calls `cindy_companies_needing_attention(7)` via Supabase RPC
2. Replace the string-matching logic (lines 100-146 in `page.tsx`) with the function result
3. The function returns structured data including `reason`, `attention_score`, `obligations[]`, and `actions[]` -- richer than what the current string-matching produces
4. The `PortfolioHealthOverview.tsx` component already supports the `CompanyAttention` interface -- just wire it up

---

## Loop 92: Daily Briefing v3 "ONE THING" Audit

### Current ONE THING: "Create WhatsApp group for ongoing Intract communication"
- Person: Abhishek Anita (portfolio founder)
- 20 days overdue
- Category: connect (2 min)
- Priority: Correct for v3 logic (portfolio + most overdue)

### The Problem

The v3 ONE THING algorithm sorts by: `is_portfolio DESC, days_overdue DESC, cindy_priority DESC`

This means the **most overdue** portfolio obligation always wins, regardless of strategic weight. Currently:

| Obligation | Person | Overdue | Strategic Weight |
|-----------|--------|---------|-----------------|
| Create WhatsApp group (Intract) | Abhishek Anita | 20 days | Low -- admin task, 2 min |
| Schneider endorsement (AuraML) | Ayush Sharma | 8 days | **HIGH** -- $2-3M investment at stake |
| Connect 5 investors (AuraML) | Ayush Sharma | 1 day | **HIGH** -- fundraising support |

**The Intract WhatsApp group is a 2-minute admin task that has been overdue for 20 days.** If it were truly urgent, it would have been done. The AuraML obligations are strategically heavier -- a $2-3M Schneider investment and 5 investor connections.

### Proposed Fix

The ONE THING should factor in:
1. **Strategic weight** (dollar value of the obligation context)
2. **Obligation clustering** (AuraML has 3 obligations to the SAME person -- signal of compound failure)
3. **Active deal signals** (AuraML has live deal signals; Intract is stable)
4. **Attention score from `cindy_companies_needing_attention()`** (AuraML=38, Intract=23)

**Not implemented in this loop** -- requires modifying `cindy_daily_briefing_v3()`. Logged as improvement for next session.

---

## Loop 93: Network Creation Suggestions -- Auto-Creation Analysis

### 23 Suggestions Reviewed

Of the 23 suggestions from `cindy_network_creation_suggestions()`:

**Safe for Auto-Creation (7):**
These have company context, deal signals, and NO existing network match:

| Suggestion | Company | Why Safe |
|-----------|---------|----------|
| Vanya | Cultured Computers | Active angel deal ($150-300K), no existing match |
| Rianne | Cultured Computers | Same deal context |
| Avii founder | Avii | Active seed deal ($2-3M), role = Founder |
| Parag (CTO) | Avii | Clear role, same deal context |
| Aditya Singh | Ditto Labs | Meeting participant, pass verdict |
| Kaustubh | DubDub | Active seed deal ($500K) |
| Nag | OnCall Owl | Series A deal ($4M), no match for short "Nag" |

**Already Exist -- FALSE POSITIVES (5):**

| Suggestion | Existing Match | Why False Positive |
|-----------|---------------|-------------------|
| Rajat (Muro) | Rajat Agarwal (#4215) | This is actually Kalyan Gautham at Muro, not Rajat. Rajat is the DeVC partner who was IN the meeting. |
| Rajat (Orbi) | Multiple Rajats exist | First-name ambiguity. Could be a new person. |
| Supan (DubDub) | Supan Shah (#428) | **Already exists.** v3 audit noted this. |
| Soumitra (WhatsApp) | Soumitra Sharma (#413) | Likely match -- VC Partner, active deal |
| Sudipto (WhatsApp) | Sudipto Sannigrahi (#1394) | Z47 team member, already exists |

**Need Human Judgment (11):**

| Suggestion | Issue |
|-----------|-------|
| Z47 network | Not a person -- it's a group |
| Guru (Orbi) | "Guru" matches Guru Prasad G and Guru Pratap -- could be either or new |
| Hrithik (Orbi) | First-name only, no company match to disambiguate |
| Warm Up GP | Generic title, not a name |
| Lisa (MSC Fund) | First-name only |
| Ashwin (Lockstep) | 8+ Ashwins in network |
| Rinky (Lockstep) | No existing match, but first-name only |
| James (Lockstep) | 3 James in network |
| Surabhi (MSC Fund) | Surabhi Bhandari (#3467) already exists and is linked to MSC Fund -- **duplicate** |
| Karli (MSC Fund) | No existing match, first-name only |
| Supermemory founder | Dhravya Shah (#3098) already resolved (noted in v3 audit) |

### Auto-Creation Readiness Score

- 7/23 (30%) safe for auto-creation
- 5/23 (22%) false positives (already exist)
- 11/23 (48%) need human judgment

**Recommendation for Cindy agent:** Auto-create the 7 safe ones. For the rest, present to user as a disambiguation task. The agent should cross-reference the full name from Granola meeting transcripts before creating.

---

## Loop 94: Cross-Source Multi-Channel Analysis

### Current State: ALL 22 People Are Single-Channel

| Channel | People | With Obligations |
|---------|--------|-----------------|
| Granola only | 13 | 8 |
| WhatsApp only | 9 | 3 |
| Both | 0 | 0 |
| Email | 0 | 0 |

### What Multi-Channel Would Look Like

For portfolio founders (the highest-priority group), multi-channel signal would enable:

1. **Enthusiasm-Action Mismatch Detection:**
   - Granola: "Excited about the partnership, let's move fast"
   - WhatsApp: No messages in 2 weeks
   - Signal: Words don't match actions. Potential risk.

2. **Obligation Fulfillment Verification:**
   - Obligation: "They will send Series A documents"
   - Email: Received attachment from Hitesh
   - Signal: Auto-resolve obligation, no nudge needed.

3. **Deal Signal Triangulation:**
   - Granola: "$350k contracts signed"
   - WhatsApp: "Can you connect us with 5 more investors?"
   - Email: Term sheet draft from Schneider
   - Signal: HIGH conviction -- deal is real and progressing.

### Blocking Dependencies

| Source | Blocker | Status |
|--------|---------|--------|
| Gmail | MCP permission denied (2 attempts) | BLOCKED |
| WhatsApp | Manual SQLite extraction only | MANUAL |
| Granola | MCP permission on droplet | BLOCKED |
| Calendar | No integration | NOT STARTED |

**Bottom line:** Multi-channel reasoning is architecturally ready (function exists, scoring works) but starved of data. The single biggest unlock is Gmail MCP access.

---

## Function Inventory (24 cindy_ functions in database)

### New in L91-94 (1):
1. `cindy_companies_needing_attention(p_limit)` -- Composite portfolio attention scoring

### All 24 cindy_ Functions:
`cindy_agent_full_context`, `cindy_agent_skill_registry`, `cindy_companies_needing_attention`, `cindy_cross_link_people_interactions`, `cindy_cross_source_reasoning`, `cindy_daily_briefing`, `cindy_daily_briefing_v3`, `cindy_data_quality_check`, `cindy_draft_nudge_message`, `cindy_intelligence_multiplier`, `cindy_interaction_kq_intelligence`, `cindy_interaction_pattern_data`, `cindy_interaction_threads`, `cindy_kq_update_proposals`, `cindy_network_creation_suggestions`, `cindy_obligation_full_context`, `cindy_obligation_key_question_link`, `cindy_obligation_kq_fts_match`, `cindy_outreach_priorities`, `cindy_person_intelligence`, `cindy_relationship_momentum`, `cindy_resolution_gaps`, `cindy_resolve_with_company_context`, `cindy_system_report`

Note: Previous audit counted ~50 total including non-cindy helper functions (e.g. `person_communication_profile`). The 24 cindy-prefixed functions are the canonical Cindy function set.

## System State After L94

| Metric | Before (L90) | After (L94) |
|--------|-------------|-------------|
| Cindy functions (cindy_ prefix) | 23 | 24 |
| Portfolio attention scoring | Not built | Active (119 companies scored, top 10 identified) |
| Companies with P0 actions | Not tracked centrally | 10 identified |
| Companies with overdue obligations | Not tracked centrally | 2 identified (AuraML, Intract) |
| ONE THING accuracy | Correct but not strategic | Audited -- needs strategic weight factor |
| Network suggestions auto-ready | 0 assessed | 7/23 safe for auto-creation |
| Multi-channel signal | 0 people | 0 people (blocked on Gmail MCP) |

## Key Decisions

1. **Composite scoring > single-signal filtering.** Companies needing attention are ranked by a weighted combination of P0 actions (30 pts max), overdue obligations (25 pts max), health status (20 pts), interaction recency (15 pts), and ops priority (10 pts). This produces better rankings than any single signal.

2. **ONE THING needs strategic weighting.** Pure days-overdue sorting surfaces admin tasks over strategically important obligations. AuraML's $2-3M Schneider deal should outrank Intract's WhatsApp group creation.

3. **Auto-creation of network records is 30% safe.** Only create when there's a clear company match, deal context, and no existing network entry with the same name. Human disambiguation needed for the other 70%.

4. **Multi-channel is the #1 data gap.** All 22 tracked people are single-channel. Gmail MCP permission is the single biggest unlock.

## Next Priorities

1. **M1 integration** -- Wire `cindy_companies_needing_attention(7)` into the home page, replacing string-matching logic
2. **ONE THING v2** -- Add strategic weight and obligation clustering to the daily briefing headline
3. **Gmail MCP** -- Third attempt at permission grant for multi-channel signal
4. **Auto-create 7 safe network records** -- Vanya, Rianne, Avii founder, Parag, Aditya Singh, Kaustubh, Nag
5. **Obligation status cleanup** -- Intract WhatsApp group (20 days overdue) should be either fulfilled or explicitly dropped
