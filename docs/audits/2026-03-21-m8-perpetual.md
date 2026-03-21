# M8 Cindy Machine -- Perpetual Loop Audit
**Date:** 2026-03-21 | **Loops:** 11 | **Status:** COMPLETE

## Executive Summary

Eleven loops transforming Cindy from a data tracker into an operational EA reasoning engine. Fixed critical FK mismatch, upgraded person resolution to prevent false matches, built staleness audit with EA-grade prose, built daily briefing aggregation (51ms), built fulfillment detection, built batch action execution, enriched obligation dashboard with inline relationship context, enhanced interaction timeline with obligation linkage, built outreach priority ranking, added snooze-awareness to all functions, and built auto-status transition via pg_cron. All functions under 55ms. 36 Cindy-related functions + 1 new pg_cron job.

## Loop 1: Fix Obligation 66 FK Mismatch

**Problem:** Obligation 66 ("Introduce Muro team to human capital team for hiring support") was linked to person_id 4215 (Rajat Agarwal, DeVC VC Partner). The obligation originated from Granola meeting with "Rajat (Muro)" -- person resolution matched "Rajat" to the most prominent Rajat in the network, not to anyone at Muro AI.

**Root cause:** The `resolve_interaction_participants_v2` METHOD 3 correctly parsed "Rajat (Muro)" and tried to find a "Rajat" at Muro AI. No match (Muro founders: Kalyan Gautham, Gregory Schweickert, Stratos Botis). Fallback methods matched "Rajat" generically to Rajat Agarwal.

**Fix:**
- Updated obligation 66: person_id 4215 -> 3083 (Kalyan Gautham, Muro AI Co-Founder CEO)
- Updated people_interactions record for interaction 91: same FK fix
- Verified via `cindy_obligation_full_context(66)` -- EA briefing now correctly references Muro AI context

## Loop 2: Upgrade Person Resolution -- Company-Aware Fallback + Role Qualifier Detection

**Problem 1:** When "Name (Company)" pattern fails name match, fallthrough methods match to wrong person.
**Fix:** Added METHOD 3b: CEO/Founder fallback at the parenthetical company (0.72 confidence). Added guard: if parenthetical company context exists and resolution fails, DO NOT fall through to generic name methods. Returns `unresolved_with_company_context` instead.

**Problem 2:** "Parag (CTO)" was treated as company name "CTO", matching to random CEO at random company.
**Fix:** Added role qualifier detection. Array of 20+ role titles (CEO, CTO, COO, VP, etc.). When detected, uses deal_company or linked_companies for context instead of treating the qualifier as a company name.

**Before:** "Parag (CTO)" -> Puneet Singh (false positive, wrong company)
**After:** "Parag (CTO)" -> unresolved (correct -- Parag at Avii needs a network entry)

**Resolution stats after upgrade:** 11 unresolved, 5 firstname_prefix (0.60 conf), 2 fuzzy_trigram (0.57 conf). Zero false positives from parenthetical patterns.

## Loop 3: Obligation Staleness Audit

**New function:** `obligation_staleness_audit()` -- EA-grade daily obligation health check.

**Classification rules:**
| Category | Criteria | Action |
|----------|----------|--------|
| AUTO-DISMISS | THEY_OWE_ME, >14 days overdue, no interaction since due, not portfolio | DISMISS (0.9 confidence) |
| NEEDS_NUDGE | THEY_OWE_ME, >3 days overdue, portfolio or high priority | SEND_NUDGE with draft message |
| CRITICAL | I_OWE_THEM, >7 days overdue, portfolio connected | ACT_NOW with time estimate |
| CRITICAL (non-portfolio) | I_OWE_THEM, >14 days overdue | DISMISS_OR_ACT |
| HEALTHY | Not overdue or recently due | Track |

**Current output:** 5 critical, 3 needs_nudge, 1 auto_dismiss, 5 healthy. Total time to clear: 44 min.

**EA headline:** "You have 5 critical obligations. Block 30 minutes to clear the backlog."

**Helper function:** `clean_obligation_description(desc, person_name)` -- strips person/entity name prefixes from obligation descriptions for natural-sounding messages.

**Portfolio detection:** Joins through `entity_connections -> companies -> portfolio` via `notion_page_id` (not integer cast).

## Loop 4: Obligation Fulfillment Detection

**New function:** `detect_obligation_fulfillment_candidates()` -- checks if new interactions contain evidence that an obligation was fulfilled.

**Approach:** Keyword overlap scoring between obligation description and subsequent interaction content + category alignment bonus. Returns candidates with confidence levels (HIGH >0.7, MEDIUM >0.5, LOW >0.3) for user review. Does NOT auto-fulfill (old function was too aggressive).

**Current state:** 0 candidates (correct -- all obligations were created today, no subsequent interactions exist yet). Ready for future data.

## Loop 5: Daily Briefing

**New function:** `cindy_daily_briefing()` -- aggregated EA morning report. Performance: 51ms.

**Returns:**
1. **Headline** -- one-sentence EA summary
2. **Obligation summary** -- total active, critical, nudge, auto-dismiss, time to clear
3. **Critical obligations** -- from staleness audit, with EA notes and time estimates
4. **Nudge candidates** -- THEY_OWE_ME items with draft follow-up messages
5. **Auto-dismiss candidates** -- stale items safe to close
6. **Quick wins** -- I_OWE_THEM items sorted by effort (2-5 min each)
7. **Relationship alerts** -- people with declining engagement, overdue obligations (portfolio-flagged)
8. **Meeting prep** -- obligations due in 3 days with recent interaction context
9. **Fulfillment check** -- auto-detected possible fulfillments
10. **System health** -- interaction count, obligation count, people linked, resolution rate

**Current relationship alerts (4):**
- Ayush Sharma: CRITICAL, 3 things owed, 15 days since contact, portfolio founder
- Abhishek Anita: URGENT, 1 thing owed, 25 days since contact, portfolio founder
- Mohit Gupta: NEEDS_ATTENTION, 1 thing owed, 23 days since contact
- Rajat Agarwal: NEEDS_ATTENTION, 1 thing owed, portfolio

## Loop 6: Batch Action + Dashboard Upgrade

**New function:** `obligation_batch_action(actions JSONB)` -- executes user decisions from briefing recommendations.

**Supported actions:**
| Action | Effect |
|--------|--------|
| `dismiss` | status -> cancelled, records evidence |
| `fulfill` | status -> fulfilled, records timestamp + evidence |
| `snooze` | Sets snooze_until, resets status to pending |
| `escalate` | status -> escalated, bumps priority +0.1 |

**Usage:** `SELECT obligation_batch_action('[{"obligation_id": 71, "action": "dismiss", "evidence": "Mohit never sent deck"}]'::JSONB)`

**Dashboard upgrade:** `obligation_dashboard` view now filters snoozed items and shows snooze state.

## Function Inventory (34 Cindy-related functions)

### New in this session (6):
1. `obligation_staleness_audit()` -- EA daily health check
2. `detect_obligation_fulfillment_candidates()` -- smart fulfillment detection
3. `cindy_daily_briefing()` -- aggregated morning EA report
4. `obligation_batch_action(actions)` -- execute user decisions
5. `clean_obligation_description(desc, name)` -- natural-language description cleaner
6. `resolve_interaction_participants_v2()` -- UPGRADED with role qualifier + company fallback

### Pre-existing (28):
- `cindy_obligation_full_context()`, `cindy_interaction_pattern_data()`, `generate_obligation_suggestions()`, `cindy_person_intelligence()`, `cindy_agent_full_context()`, `person_communication_profile()`, `cindy_system_report()`, `cindy_intelligence_multiplier()`, `cindy_data_quality_check()`, `detect_interaction_patterns()`, `interaction_intelligence_score()`, `obligation_fulfillment_rate()`, `obligation_health_summary()`, `fulfill_obligation()`, `resolve_participant()`, and 13 others

## Performance Summary

| Function | Execution Time | Status |
|----------|---------------|--------|
| `obligation_staleness_audit()` | <30ms | PASS |
| `detect_obligation_fulfillment_candidates()` | <20ms | PASS |
| `cindy_daily_briefing()` | 51ms | PASS |
| `obligation_batch_action(...)` | <15ms | PASS |
| `clean_obligation_description(...)` | <1ms | PASS |
| `resolve_interaction_participants_v2()` | <50ms | PASS |

All under 200ms target.

## System State After This Session

| Metric | Before | After |
|--------|--------|-------|
| Total interactions | 23 | 23 |
| Total obligations | 14 active | 14 active |
| FK mismatches | 1 (obligation 66) | 0 |
| Person resolution false positives | 1 ("Parag (CTO)") | 0 |
| Cindy functions | 31 | 34 |
| Daily briefing available | No | Yes (51ms) |
| Staleness audit available | No | Yes (<30ms) |
| Batch action support | No | Yes |
| Portfolio detection | Broken (type mismatch) | Fixed |

## What This Enables

1. **Morning briefing**: Call `cindy_daily_briefing()` once -- get full EA report with headline, critical items, quick wins, relationship alerts, meeting prep, draft nudge messages
2. **Batch triage**: Use `obligation_batch_action()` to dismiss/fulfill/snooze obligations in bulk from briefing recommendations
3. **Safer resolution**: Person resolution won't false-match when company context is given in parentheses
4. **Fulfillment tracking**: `detect_obligation_fulfillment_candidates()` ready to flag fulfilled obligations as new interactions come in
5. **WebFront integration**: All functions return structured JSONB ready for rendering

## Loop 7: Enriched Obligation Dashboard

Rebuilt `obligation_dashboard` view with inline relationship context:
- `is_portfolio` flag (joins entity_connections -> companies -> portfolio)
- `company_name` and `pipeline_status` from obligation context
- `last_contact_date` and `days_since_contact` from interactions
- `total_interactions` count per person
- `action_short` via `clean_obligation_description()` for UI display
- Snooze filtering: snoozed obligations hidden until snooze expires

**Result:** WebFront /comms page can render full obligation cards with one query -- no cascading lookups needed.

## Loop 8: Enhanced Interaction Timeline

Rebuilt `interaction_timeline` view with:
- `open_obligation_count` and `total_obligation_count` per interaction
- `obligations_summary` -- inline JSONB array of spawned obligations with status, person, and suggested action
- `resolved_people` -- inline JSONB array of resolved participants with names, roles, and confidence
- `resolved_people_count` for quick filtering

**Result:** AuraML meeting (interaction 94) shows 3 open obligations. Muro meeting (91) shows 1 (now correctly linked to Kalyan Gautham).

## Loop 9: Outreach Priority Ranking

**New function:** `cindy_outreach_priorities()` -- ranks all active contacts by outreach urgency.

**Ranking logic:**
1. Portfolio founders with overdue I_OWE obligations (highest priority)
2. Then by days since last contact (most stale first)

**Current top 5:**
| Person | Role | Portfolio | Days Since Contact | I Owe | Reason |
|--------|------|-----------|-------------------|-------|--------|
| Abhishek Anita | CEO, Intract | Yes | 25.3 | 1 | PORTFOLIO: Fulfill before reaching out |
| Ayush Sharma | CEO, AuraML | Yes | 15.0 | 3 | PORTFOLIO: Fulfill before reaching out |
| Rajat Agarwal | VC Partner | Yes | 0.3 | 1 | PORTFOLIO: Fulfill before reaching out |
| Sujoy Golan | CXO, OnCall Owl | Yes | 25.5 | 0 | PORTFOLIO: 26 days since contact |
| Sambhav Jain | COO, Intract | Yes | 25.3 | 0 | PORTFOLIO: 25 days since contact |

## Loop 10: Snooze-Awareness

Updated `obligation_staleness_audit()` to:
- Filter snoozed obligations into a separate `snoozed` array
- Exclude snoozed items from critical/nudge/healthy counts
- Show `total_active` as non-snoozed active obligations
- Include snooze status in EA headline

## Loop 11: Auto-Status Transition + pg_cron Job

**New function:** `update_obligation_statuses()` -- hourly auto-transition:
- `pending` -> `overdue` when due_date passes (respects snooze_until)
- `overdue` -> `escalated` when overdue > 10 days AND portfolio-connected AND I_OWE_THEM
- Escalation bumps cindy_priority by +0.05 (blended_priority auto-recalculates as generated column)
- Regenerates suggestions for newly transitioned obligations

**pg_cron job:** `0 * * * *` (hourly) -- job 22

**First run results:** 2 obligations escalated (Ayush Sharma #69 and Abhishek Anita #75), both portfolio founders with 11+ and 20+ day overdue I_OWE_THEM obligations.

## Function Inventory (36 Cindy-related functions + 2 views + 1 cron job)

### New in this session (11):
1. `obligation_staleness_audit()` -- EA daily health check with snooze-awareness
2. `detect_obligation_fulfillment_candidates()` -- smart fulfillment detection
3. `cindy_daily_briefing()` -- aggregated morning EA report (51ms)
4. `obligation_batch_action(actions)` -- execute user decisions
5. `clean_obligation_description(desc, name)` -- natural-language description cleaner
6. `cindy_outreach_priorities()` -- ranked outreach recommendations
7. `update_obligation_statuses()` -- hourly auto-transition (pg_cron)
8. `resolve_interaction_participants_v2()` -- UPGRADED with role qualifier + company fallback
9. `obligation_dashboard` view -- REBUILT with relationship context + snooze filtering
10. `interaction_timeline` view -- REBUILT with obligation linkage + resolved people
11. pg_cron job 22: hourly obligation status update

### Pre-existing (28):
`cindy_obligation_full_context()`, `cindy_interaction_pattern_data()`, `generate_obligation_suggestions()`, `cindy_person_intelligence()`, `cindy_agent_full_context()`, `person_communication_profile()`, `cindy_system_report()`, `cindy_intelligence_multiplier()`, `cindy_data_quality_check()`, `detect_interaction_patterns()`, `interaction_intelligence_score()`, `obligation_fulfillment_rate()`, `obligation_health_summary()`, `fulfill_obligation()`, `resolve_participant()`, and 13 others

## Performance Summary

| Function | Execution Time | Status |
|----------|---------------|--------|
| `obligation_staleness_audit()` | <30ms | PASS |
| `detect_obligation_fulfillment_candidates()` | <20ms | PASS |
| `cindy_daily_briefing()` | 51ms | PASS |
| `obligation_batch_action(...)` | <15ms | PASS |
| `clean_obligation_description(...)` | <1ms | PASS |
| `cindy_outreach_priorities()` | <40ms | PASS |
| `resolve_interaction_participants_v2()` | <50ms | PASS |

All under 200ms target.

## System State After This Session

| Metric | Before | After |
|--------|--------|-------|
| Total interactions | 23 | 23 |
| Total obligations | 14 active | 14 active |
| FK mismatches | 1 (obligation 66) | 0 |
| Person resolution false positives | 1 ("Parag (CTO)") | 0 |
| Cindy functions | 31 | 37 |
| Daily briefing available | No | Yes (51ms) |
| Staleness audit available | No | Yes (<30ms) |
| Batch action support | No | Yes |
| Outreach ranking | No | Yes |
| Dashboard with relationship context | No | Yes |
| Timeline with obligation linkage | No | Yes |
| Portfolio detection | Broken (type mismatch) | Fixed |

## What This Enables

1. **Morning briefing**: `cindy_daily_briefing()` -- one call, full EA report (headline, criticals, quick wins, relationship alerts, meeting prep, draft nudges)
2. **Batch triage**: `obligation_batch_action()` -- dismiss/fulfill/snooze obligations in bulk
3. **Outreach ranking**: `cindy_outreach_priorities()` -- who needs attention most
4. **Safer resolution**: Person resolution prevents false matches on parenthetical patterns
5. **Fulfillment tracking**: `detect_obligation_fulfillment_candidates()` ready for new interaction data
6. **WebFront integration**: All functions return structured JSONB. Dashboard and timeline views ready for rendering.

## Next Steps

1. **Gmail integration**: Grant Gmail MCP permission to ingest email interactions
2. **AgentMail API key**: Deploy to droplet for autonomous email processing
3. **WebFront**: Wire /comms page to `cindy_daily_briefing()` for briefing card and `cindy_outreach_priorities()` for relationship health panel
4. **Cindy agent**: Use `cindy_daily_briefing()` + `obligation_batch_action()` as session workflow
5. **Granola auto-ingest**: Trigger new meeting processing on Cindy agent heartbeat
6. **Nudge execution**: Wire `needs_nudge` draft messages to email/WhatsApp sending
7. **Scoring integration**: Feed obligation health into M5 action scoring (people with overdue obligations should have their related actions boosted)
