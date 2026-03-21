# M8 Cindy Machine -- Perpetual Loop v6 Audit
**Date:** 2026-03-21 | **Loops:** L99-102 | **Status:** COMPLETE

## Executive Summary

4 loops: resolved 6 participant-interaction gaps (27 to 21), built deal velocity tracker (new function), integrated deal velocity into briefing v3, corrected email architecture (AgentMail not Gmail), updated skill registry to v3.2 with 13 skills.

**Key correction:** Gmail MCP is Aakash's personal mailbox -- out of scope for Cindy. Cindy's email channel is **AgentMail** (`cindy.aacash@agentmail.to`). User forwards relevant emails there. Cindy reads via AgentMail API (key on droplet).

---

## Loop 99: Resolution Gap Fix (27 to 21)

### What Was Done

Inserted 7 `people_interactions` records linking the network entries created in L97 to their source interactions:

| Person (network ID) | Interaction ID | Source | Context |
|---------------------|---------------|--------|---------|
| Rajat/Muro (4500) | 91 | Granola | Muro AI business scaling, BNG $320k |
| Vanya (4494) | 92 | Granola | Cultured Computers |
| Rianne (4495) | 92 | Granola | Cultured Computers |
| Parag (4496) | 104 | Granola | Avii CTO |
| Nag (4497) | 105 | Granola | OnCall Owl |
| Guru (4498) | 95 | Granola | Orbi |
| Hrithik (4499) | 95 | Granola | Orbi |

Also updated `last_interaction_at`, `last_interaction_surface`, `interaction_count_30d`, and `interaction_surfaces` on all 7 network entries.

### Result

- Resolution gaps: **27 -> 21** (6 resolved)
- `likely_match` bucket: **4 -> 0** (all resolved)
- `few_candidates` bucket: **2 -> 1** (1 resolved)
- Remaining breakdown: `needs_company_lookup` 11, `no_network_entry` 7, `ambiguous` 2, `few_candidates` 1

### Why Resolution Matters

The `cindy_resolution_gaps()` function checks `people_interactions` join table, not `interactions.linked_people` array. Previous loop (L97) created network entries and added to `linked_people` but missed `people_interactions` insertion. This loop fixed the actual resolution mechanism.

---

## Loop 100: Deal Velocity Tracker (NEW FUNCTION)

### Problem

Cindy could track individual obligations and deal signals but had no way to answer: "Which portfolio companies are going cold?" The briefing had `deal_momentum` (WhatsApp signals from last 7 days) but not a velocity view across all portfolio companies.

### Solution: `cindy_deal_velocity()`

New function that tracks all 141 portfolio companies and flags the ones with signal (interactions + obligations), ranking by velocity concern.

**Velocity statuses:**

| Status | Criteria | Count |
|--------|----------|-------|
| HOT | Interaction in last 7 days | **3** (Kilrr, Soulside, Quivly) |
| WARM | Interaction 7-14 days ago | **0** |
| COOLING | Interaction 14+ days ago | **2** (AuraML 15d, Intract 25d) |
| COLD_WITH_OBLIGATIONS | No interaction + open obligations | **0** |
| WAITING | No interaction + they-owe obligations | **0** |

**Architecture decisions:**
1. Only shows companies with signal (interactions OR obligations in last 30 days). 136 "no signal" companies are counted but not listed -- the function surfaces what matters, not noise.
2. Joins: `portfolio -> companies (via notion_page_id) -> interactions (via linked_companies array) + obligations (via context->>'company_id')`
3. Includes deal_trail: chronological interaction snippets for each company.

### Live Output Validation

```
AuraML: COOLING (15 days silent)
  - 3 I_OWE obligations, 2 OVERDUE
  - Last: "AI Summit success. Signed $350k contracts. Schneider Electric Ventures..."
  - Ownership: 2.22%, EV: $33,300

Kilrr: HOT (0 days silent)
  - 1 THEY_OWE obligation
  - Last: "Active deal group between DeVC and Kilrr. 5 messages in last 7 days."

Soulside: HOT (0 days silent)
  - "Active deal discussions with DeVC partner Rajat. Topics: Soulside round closed..."

Quivly: HOT (0 days silent)
  - "Active deal group between DeVC and Quivly. 9 messages in last 7 days..."

Intract: COOLING (25 days silent)
  - 1 I_OWE obligation
  - Last: "Portfolio checkin. Shut down Banter and Interact..."
```

**Critical insight:** AuraML is COOLING with the #1 obligation (Schneider endorsement, score 52.4) and 15 days since last interaction. This is the deal most at risk of relationship damage.

---

## Loop 101: Briefing v3 Updated

### Changes to `cindy_daily_briefing_v3()`

1. **`deal_velocity` section added**: Array of active deals with velocity status, channels, obligations
2. **`deal_velocity_summary` section added**: Hot/warm/cooling counts + no-signal count
3. **`gmail_connected: true` REMOVED**: Replaced with correct email architecture
4. **`system.agentmail_inbox`**: `cindy.aacash@agentmail.to`
5. **`system.email_channel`**: `AgentMail (not Gmail)`
6. **`system.resolution_gaps`**: Now shows `21` (down from 27, uses live function)

### Email Architecture Correction (IMPORTANT)

| Component | Correct | Wrong (was stated in v5) |
|-----------|---------|--------------------------|
| Cindy's email source | `cindy.aacash@agentmail.to` (AgentMail API) | Gmail MCP scanning user's mailbox |
| How emails arrive | User forwards/CCs relevant emails to Cindy address | Gmail search scanning inbox |
| API for reading | AgentMail API (key on droplet) | Gmail MCP `gmail_search_messages` |
| User's work email | Outlook (not Gmail) | Assumed Gmail |
| Gmail MCP role | Out of scope for Cindy | Was listed as "connected" |

Gmail MCP connects to Aakash's personal `hi@aacash.me` -- his work email is Outlook. Neither should be scanned by Cindy. Cindy gets email intelligence only through her own inbox (`cindy.aacash@agentmail.to`).

---

## Loop 102: Skill Registry v3.2 + Cindy Agent First Session Spec

### Skill Registry Changes (v3.1 -> v3.2)

| Change | Before | After |
|--------|--------|-------|
| Deal velocity tracking | Not listed | **READY** -- `cindy_deal_velocity()` |
| Email ingestion (Gmail) | READY | **REMOVED** -- out of scope |
| Email ingestion (AgentMail) | READY | **READY** -- with clarified architecture |
| Calendar ingestion | Not listed | **BLOCKED** -- needs .ics forwarding setup |
| Total skills | 12 | **13** |
| Blocked | 1 (Granola) | **1** (Calendar) |

### Cindy Agent First Autonomous Session -- Design Spec

**What the agent would DO in its first 10-minute autonomous session:**

#### Phase 1: Ingest (2 min)
1. Check AgentMail inbox for forwarded emails (AgentMail API)
2. Check Granola for meetings since last run (Granola MCP -- Mac only, blocked on droplet)
3. Check WhatsApp export for new messages (iCloud backup .txt)

#### Phase 2: Process (4 min)
1. For each new interaction: detect obligations, extract deal signals, link participants
2. Run `cindy_resolution_gaps()` -- attempt to resolve `likely_match` gaps automatically
3. Run `cindy_deal_velocity()` -- flag any status changes (HOT->COOLING, new COLD_WITH_OBLIGATIONS)

#### Phase 3: Act (3 min)
1. For THEY_OWE_ME 5+ days overdue: draft nudge messages via `cindy_draft_nudge_message()`
2. For deal velocity alerts: format a 1-line alert per company
3. Generate `cindy_daily_briefing_v3()` if morning run

#### Phase 4: Report (1 min)
1. Post summary to State MCP (`post_message` with type='cindy_report')
2. If urgent (COLD_WITH_OBLIGATIONS or COOLING portfolio): flag for user attention

#### Required Tools
- State MCP (`get_state`, `post_message`) -- for reading/writing agent state
- AgentMail API -- for email ingestion
- Supabase SQL -- for all intelligence functions
- Granola MCP -- for meeting data (Mac sessions only)

#### Guardrails
- NEVER send emails/messages without human approval
- NEVER modify obligation status without evidence
- NEVER scan user's personal email (Gmail or Outlook)
- Resolution confidence < 0.85: flag for human, don't auto-link
- Network creation: only with clear company context, disambiguated names

---

## Function Inventory Update

| # | Function | Status | Change |
|---|----------|--------|--------|
| 51 | `cindy_companies_needing_attention()` | Stable | -- |
| 52 | `cindy_daily_briefing_v3()` | **UPDATED** | +deal_velocity, +deal_velocity_summary, fixed email architecture |
| 53 | `cindy_agent_skill_registry()` | **UPDATED** | v3.1 -> v3.2: +deal_velocity, -Gmail, +calendar blocked |
| 54 | `cindy_autonomous_ea_dashboard()` | Stable | -- |
| 55 | `cindy_deal_velocity()` | **NEW** | Portfolio deal velocity tracking (HOT/WARM/COOLING/COLD) |

**Total Cindy functions:** 28 (27 existing + 1 new)

---

## Cross-Machine Impact

| Machine | Impact |
|---------|--------|
| **M1 WebFront** | `deal_velocity` and `deal_velocity_summary` available for rendering. Could show velocity badges on portfolio page. |
| **M5 Scoring** | Deal velocity COOLING status on AuraML validates Schneider endorsement as #1 priority. Scoring and velocity agree. |
| **M9 Intel QA** | Email architecture corrected. v5 audit stated Gmail was connected -- v6 corrects this. |
| **M12 Data Enrichment** | Resolution gaps down 27->21 via proper people_interactions linking. Still 21 remaining for M12 to address. |

---

## Metrics

| Metric | Before (v5) | After (v6) |
|--------|-------------|------------|
| Resolution gaps | 27 | **21** |
| `likely_match` gaps | 4 | **0** |
| people_interactions records | 31 | **38** (+7) |
| Cindy functions | 27 | **28** (+1 deal_velocity) |
| Skills registry version | v3.1 | **v3.2** |
| Skills total | 12 | **13** |
| Deal velocity: portfolio tracked | 0 | **141** (5 with signal) |
| Deal velocity: HOT | -- | **3** (Kilrr, Soulside, Quivly) |
| Deal velocity: COOLING | -- | **2** (AuraML, Intract) |
| Email architecture | "Gmail connected" (WRONG) | **AgentMail only** (CORRECT) |
| Briefing includes velocity | No | **Yes** |
