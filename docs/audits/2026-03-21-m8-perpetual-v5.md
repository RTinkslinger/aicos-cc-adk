# M8 Cindy Machine -- Perpetual Loop v5 Audit
**Date:** 2026-03-21 | **Loops:** L95-98 | **Status:** COMPLETE

## Executive Summary

4 loops fixing the ONE THING ranking flaw, unblocking Gmail, auto-creating 7 network entries, and assessing Cindy's autonomous EA readiness. The core fix: ONE THING ranking now uses a 6-factor composite score (category impact x financial stakes x obligation type x urgency x ops priority x health) instead of naive `is_portfolio DESC, days_overdue DESC`. Result: Schneider endorsement ($3.3M EV at stake) correctly ranks above WhatsApp group admin task.

**Key result:** "Create WhatsApp group for Intract" (old #1, score 13.8) is now #6. "Provide investor endorsement to Schneider Electric Ventures for AuraML" (new #1, score 52.4) correctly dominates.

---

## Loop 95: ONE THING Ranking Fix

### Problem
The `cindy_daily_briefing_v3()` function's ONE THING selection used:
```sql
ORDER BY is_portfolio DESC, days_overdue DESC, cindy_priority DESC
```
This ranked "Create WhatsApp group for Intract" (20 days overdue, admin task) above "Provide investor endorsement to Schneider Electric Ventures for AuraML" (8 days overdue, deal-critical). Pure chronological overdue = no concept of financial stakes or action impact.

### Fix: 6-Factor Composite `one_thing_score`

```
one_thing_score = category_impact
                  x financial_stakes_multiplier
                  x obligation_type_weight
                  x urgency_factor
                  x ops_priority_boost
                  x health_boost
```

| Factor | Range | Logic |
|--------|-------|-------|
| **Category impact** | 3-10 | provide_info=10, introduce=9, review=8, send_document=6, schedule=5, follow_up=4, connect=3 |
| **Financial stakes** | 1.0-3.0 | `LEAST(3.0, 1.0 + LN(ownership_pct * best_case_outcome) / 15.0)`. AuraML: 2.2% x $150M = $3.3M EV -> 2.0x. Intract: 1.03% x $350M = $3.6M EV -> 2.0x. Falls back to entry_cheque proxy if no best_case data |
| **Obligation type** | 0.8-1.3 | I_OWE_THEM=1.3 (brand at risk), THEY_OWE_ME=0.8 (chase) |
| **Urgency** | 0.8-2.0 | `LEAST(2.0, 1.0 + LN(days_overdue + 1) / 4.0)`. Log-scaled: diminishing returns past 14 days. Not-yet-due = 0.8 penalty |
| **Ops priority** | 1.0-1.5 | P0=1.5, P1=1.3, P2=1.1 |
| **Health** | 1.0-1.3 | Red=1.3, Yellow=1.1 |

### Score Validation (all 14 active obligations)

| Rank | Score | Obligation | Category | Company | Old Rank |
|------|-------|------------|----------|---------|----------|
| 1 | 52.4 | Schneider endorsement for AuraML | provide_info | AuraML | #3 |
| 2 | 35.7 | Connect AuraML with 5 investors | introduce | AuraML | #7 |
| 3 | 24.6 | Circulate MSC Fund materials | review | Soulside | #4 |
| 4 | 20.0 | Involve Rahul in Levocred eval | introduce | Edge Focus | #6 |
| 5 | 16.4 | WhatsApp group for Schneider | connect | AuraML | #3 |
| 6 | 13.8 | WhatsApp group for Intract | connect | Intract | **#1** |
| 7 | 12.7 | MSC Fund data room (THEY_OWE) | send_document | Soulside | #2 |
| 8 | 9.5 | OnCall Owl Series A follow-up | follow_up | Multiwoven | #6 |
| 9 | 9.4 | Muro AI hiring intro | introduce | Muro AI | #12 |
| 10 | 8.5 | DubDub deck (THEY_OWE) | send_document | Stealth | #10 |
| 11 | 8.5 | Levocred deck (THEY_OWE) | send_document | Edge Focus | #11 |
| 12 | 8.4 | Kilrr Series A docs (THEY_OWE) | send_document | Kilrr | #9 |
| 13 | 6.2 | LP chat ideas for Rajat | follow_up | Orbi | #8 |
| 14 | 5.2 | Meet Supermemory founder | schedule | Cloudflare | #13 |

**Why Schneider (52.4) >> Intract WhatsApp (13.8):**
- Category: provide_info (10) vs connect (3) = 3.3x
- Financial stakes: both ~2.0x (similar EV)
- Obligation type: both I_OWE_THEM = 1.3x
- Urgency: 8d overdue (1.55x) vs 20d overdue (1.75x) = Intract slightly higher
- Ops priority: P1 (1.3x) vs NA (1.0x) = AuraML higher
- Net: Schneider = 10 x 2.0 x 1.3 x 1.55 x 1.3 x 1.0 = 52.4. Intract = 3 x 2.0 x 1.3 x 1.75 x 1.0 x 1.0 = 13.8

### Additional Changes to `cindy_daily_briefing_v3()`

1. **`top_actions` array added**: Top 5 I_OWE_THEM obligations by score, giving context below the headline
2. **ONE THING filtered to I_OWE_THEM only**: The ONE THING should only show things Aakash needs to DO, not things he's waiting on
3. **Score exposed in JSON**: Each obligation carries its `one_thing_score` for transparency
4. **`why` messages updated**: Deal-critical actions now show expected value at stake ("3.3M expected value at stake") instead of generic "Your brand is on the line"
5. **`system.gmail_connected: true`**: Reflects Gmail MCP availability
6. **`system.resolution_gaps`**: Dynamic count from `cindy_resolution_gaps()` instead of hardcoded 27

---

## Loop 96: Gmail MCP Unblocked + Email Intelligence

### Gmail MCP Status: CONNECTED

Successfully queried Gmail via `gmail_search_messages` and `gmail_get_profile` tools. Results:
- 201 unread emails (mostly newsletters/updates)
- AgentMail welcome email confirmed (from Adi Singh, Mar 20)
- No deal-relevant emails from portfolio founders in inbox (deal context comes from WhatsApp/Granola)
- Vercel deployment failure notification caught

### Skill Registry Updated (v3.0 -> v3.1)

| Change | Before | After |
|--------|--------|-------|
| Email ingestion (Gmail) | Not listed | **READY** -- Gmail MCP connected via Claude Code |
| Email ingestion (AgentMail) | BLOCKED | **READY** -- API key on droplet |
| Network auto-creation | Not listed | **READY** -- with safety rules |
| Total skills | 10 | 12 |
| Blocked | 2 (Gmail + AgentMail) | 1 (Granola MCP only) |

### Gmail Search Strategies for Cindy

```
from:<portfolio_founder_email> newer_than:7d
subject:deck OR subject:pitch OR subject:investment newer_than:14d
-category:promotions -category:updates -category:social newer_than:3d label:inbox
label:important newer_than:7d
```

---

## Loop 97: Network Auto-Creation (7 entries)

### Analysis of 23 Suggestions

| Category | Count | Action |
|----------|-------|--------|
| Already exist in network | 4 | Dhravya Shah, Supan Shah, Surabhi Bhandari, Rajat Agarwal -- skip |
| Safe to create | 7 | Clear company + context, no ambiguity |
| Unsafe/ambiguous | 12 | First-name-only (Ashwin 13+ matches), group names, unnamed roles, passes -- skip |

### Created Entries

| ID | Name | Company | Source | Deal Context |
|----|------|---------|--------|-------------|
| 4494 | Vanya | Cultured Computers | Granola | $1M raise at $30M cap, Aakash interested $150-300K |
| 4495 | Rianne | Cultured Computers | Granola | Same meeting as Vanya |
| 4496 | Parag | Avii | Granola | CTO, raising $2-3M seed |
| 4497 | Nag | OnCall Owl | Granola | Raising $4M Series A, $2M committed |
| 4498 | Guru | Orbi | Granola | Portfolio co pitch |
| 4499 | Hrithik | Orbi | Granola | Portfolio co pitch |
| 4500 | Rajat (Muro) | Muro AI | Granola | Portfolio co scaling, BNG $320k deal |

**Entity connections created:** 7 network-company links (connection_type='works_at', strength=0.9-0.95)

### Safety Rules Applied

1. Only created entries with known company context (company exists in companies table)
2. Used disambiguated name for "Rajat (Muro)" to avoid collision with 12+ existing Rajats
3. Skipped all first-name-only suggestions without clear company (Ashwin, Lisa, James, etc.)
4. Skipped non-person entries (Z47 network, Warm Up GP)
5. Skipped role-only entries (Avii founder, Supermemory founder)
6. Skipped "pass" verdicts (Aditya Singh at Ditto Labs)

---

## Loop 98: Autonomous EA Assessment

### New Function: `cindy_autonomous_ea_dashboard()`

Created a dashboard function that answers: "What should the Cindy agent DO right now?" Returns:
- **Agent status**: Which channels are connected, skill readiness
- **Immediate tasks**: 4 prioritized tasks with counts (unprocessed interactions, obligation fulfillment checks, nudge drafting, participant resolution)
- **Daily routine**: Morning scan (06:30), interaction processing (every 2h), end-of-day review (18:00)
- **Genuine value actions**: 5 things that make Cindy useful beyond a dashboard

### What Would Make Cindy Genuinely Useful (assessed)

| Action | Value | Status | Gap |
|--------|-------|--------|-----|
| Pre-meeting context assembly | Assemble last interaction, open obligations, deal signals, key questions 5 min before each meeting | NEEDS | Calendar API integration |
| Proactive obligation nudging | Draft contextual follow-ups for THEY_OWE_ME 5+ days overdue | READY | `cindy_draft_nudge_message()` exists |
| Cross-channel signal correlation | Detect WhatsApp+Granola same-person same-week signal mismatches | READY | `cindy_cross_source_reasoning()` exists |
| Deal velocity tracking | Alert when hot deals go cold (no interaction 5+ days during active deal) | PARTIAL | Deal signals exist, velocity computation needed |
| Network introduction matching | Scan network for matching people when founder needs intros | NEEDS | Network embedding search + matching logic |

### Immediate EA Tasks (live data)

- **0 unprocessed interactions** (all caught up)
- **14 open obligations** (7 portfolio overdue)
- **4 THEY_OWE_ME nudge candidates** (Sujoy/OnCall Owl 6d, Mohit/Levocred 20d, Surabhi/MSC 20d, Supan/DubDub 21d)
- **7 unresolved participant interactions** (need `cindy_resolve_with_company_context()`)
- **98 min total clear time** for all obligations

---

## Function Inventory Update

| # | Function | Status | Change |
|---|----------|--------|--------|
| 51 | `cindy_companies_needing_attention()` | Stable | No change (from L91) |
| 52 | `cindy_daily_briefing_v3()` | **UPDATED** | ONE THING ranking fixed with 6-factor composite score |
| 53 | `cindy_agent_skill_registry()` | **UPDATED** | v3.0 -> v3.1: Gmail READY, AgentMail READY, +2 skills |
| 54 | `cindy_autonomous_ea_dashboard()` | **NEW** | Agent task dashboard for autonomous operation |

**Total Cindy functions:** 27 (24 existing + 3 updated/new)

---

## Cross-Machine Impact

| Machine | Impact |
|---------|--------|
| **M1 WebFront** | ONE THING section on home page now shows correct priority. `top_actions` array available for rendering a ranked list. |
| **M5 Scoring** | ONE THING score complements (does not replace) `compute_user_priority_score()`. Different purpose: obligations vs actions. |
| **M12 Data Enrichment** | 7 new network entries (ids 4494-4500) + 7 entity_connections. Network count: 3,525 -> 3,532. |
| **M9 Intel QA** | ONE THING ranking flaw resolved. Previous audit flagged this in v4. |

---

## Metrics

| Metric | Before | After |
|--------|--------|-------|
| ONE THING: Schneider deal rank | #3 | **#1** (score 52.4) |
| ONE THING: Intract WhatsApp rank | **#1** | #6 (score 13.8) |
| Skill registry: ready/total | 7/10 | **11/12** |
| Skills blocked | 2 (Gmail + AgentMail) | **1** (Granola only) |
| Network entries auto-created | 0 | **7** |
| Entity connections added | 0 | **7** |
| Cindy functions total | 24 | **27** |
| Briefing v3 includes score | No | **Yes** |
| Gmail MCP | Not tested | **Connected + tested** |
