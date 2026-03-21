# M8 Cindy Machine -- Perpetual Loop v2 Audit
**Date:** 2026-03-21 | **Loops:** 12-19 (8 loops) | **Status:** COMPLETE

## Executive Summary

Eight loops transforming Cindy's communication quality from robotic to EA-grade. Rewrote nudge message generation with context-aware templates, noun-phrase extraction, meeting references, and tone calibration. Built relationship momentum scoring (0-10 scale combining obligation health, contact recency, and portfolio weight). Upgraded daily briefing with portfolio risk alerts, cooling relationship warnings, and resolution gap tracking. Built safe cross-linking function with company-context guards. Identified and cleaned 13 false-positive people-interaction links from naive first-name matching.

**Headline improvement:** "You have 5 critical obligations" -> "5 critical obligations. 5 portfolio relationships at risk. Block 30 minutes."

## Loop 12-13: Nudge Message Quality Revolution

### Problem
Old nudge messages were unusable:
- "Hey Supan, wanted to follow up on the send deck and demo video. Any update?" (truncated, robotic)
- "Hey Surabhi, wanted to follow up on the msc fund to add aakash to data room and send pitch. Any update?" (raw obligation text, lowercase, truncated)

### Solution
Built 3 new functions working together:

**`cindy_draft_nudge_message(obligation_id)`** -- Context-aware message generator for THEY_OWE_ME obligations:
- References the source meeting ("our call on Feb 24")
- Uses proper channel (whatsapp vs email) based on interaction source
- Calibrates tone (casual < friendly-reminder < direct < warm-professional) based on overdue severity and portfolio connection
- Scales message urgency by days overdue (3/7/14/21+ day tiers)
- Returns channel, subject, tone, deliverable, and EA advisory note

**`obligation_deliverable_phrase(description, person_name)`** -- Extracts the noun-phrase deliverable:
- "DubDub founders to send deck and demo video" -> "the deck and demo video"
- "MSC Fund to add Aakash to data room and send pitch deck" -> "the data room access and pitch deck"
- "OnCall Owl to follow up on Series A round participation details" -> "the Series A round participation details"
- Handles compound patterns: "add X to Y and send Z" -> "the Y access and Z"

**`clean_obligation_description(description, person_name)`** -- UPGRADED:
- Now handles multi-word entity prefixes: "MSC Fund to add..." -> "Add..."
- Capitalizes first letter of result
- Verb guard: won't strip verb-led descriptions (Introduce, Provide, Create, etc.)

### Before vs After

| Person | BEFORE | AFTER |
|--------|--------|-------|
| Supan Shah | "Hey Supan, wanted to follow up on the send deck and demo video. Any update?" | "Hi Supan, checking in on the deck and demo video. It's been a few weeks since our call on Feb 24 -- is this still in the works?" |
| Surabhi Bhandari | "Hey Surabhi, wanted to follow up on the msc fund to add aakash to data room and send pitch. Any update?" | "Hi Surabhi, checking in on the data room access and pitch deck. It's been a few weeks since our call on Feb 26 -- is this still in the works?" |
| Sujoy Golan | "Hey Sujoy, wanted to follow up on the oncall owl to follow up on series a round particip. Any update?" | "Hey Sujoy -- following up from our call on Feb 23. Were you able to get the Series A round participation details sorted?" |
| Hitesh Bhagia | N/A | "Hey Hitesh -- quick follow-up from our chat on Mar 21. Any update on the Series A documents?" |

## Loop 14: Staleness Audit Integration

Rewired `obligation_staleness_audit()` to use `cindy_draft_nudge_message()` instead of hardcoded template. Nudge candidates in the daily briefing now include: `draft_message`, `channel`, `subject`, `tone`, `deliverable`.

## Loop 15: People-Interaction Cross-Linking (with false positive cleanup)

### Problem
Every person had exactly 1 interaction linked (people_interactions). Many appear in multiple meetings.

### v1 Attempt -- Naive First-Name Matching
Ran a first-name prefix match against 4000+ person network. Created 19 links, **13 were false positives**:
- Person 3544 (empty name) matched everything (11 false links)
- "Soumitra" matched wrong Soumitra (Bhadra vs Sharma)
- "Rajat" at Orbi meeting matched Rajat Piplewar at BhuMe (wrong company)
- "Ashwin" at RSA event matched wrong Ashwin Pandian

### v2 -- Company-Context Guard
Rewrote `cindy_cross_link_people_interactions()` with strict rules:
- Full names (2+ words): exact match, high confidence (0.95)
- First-name-only + unique in network: safe match (0.85)
- First-name-only + multiple candidates: require company context match via `linked_companies -> companies -> network.current_company_ids` (0.75)
- First-name-only + multiple candidates + no company context: skip and log as ambiguous

**v2 result:** 1 new link (Surabhi Bhandari, unique first name), 4 correctly skipped as ambiguous, 0 false positives.

### Cleanup
Deleted all 13 false positive links from v1 run.

## Loop 16: Resolution Gaps Report

**`cindy_resolution_gaps()`** -- Surfaces all unresolved participants with company context for agent/human resolution.

Current state: 27 unresolved participants across 23 interactions (14 fully resolved).

| Difficulty | Count | Examples |
|-----------|-------|---------|
| needs_company_lookup | 11 | "DeVC team", "Kilrr team", "Intract founders" |
| no_network_entry | 12 | Vanya, Rianne, Lisa, Karli, Warm Up GP |
| few_candidates | 2 | Names with 2-3 matches |
| ambiguous | 2 | "Rajat" (10 candidates), "Ashwin" (9 candidates) |

**Key insight:** First-name resolution for VC/founder networks is fundamentally an LLM task, not a SQL pattern matching task. The Cindy AGENT should handle these using meeting context, company associations, and relationship graph reasoning.

## Loop 17: Interaction Threading

**`cindy_interaction_threads()`** -- Groups interactions by company and person, showing cross-channel patterns.

Current state: 20 company threads, 22 person threads, 0 cross-channel (because data is sparse -- each person has 1 interaction). Function is built and ready for when data volume grows with Gmail integration and ongoing Granola/WhatsApp ingestion.

## Loop 18: Relationship Momentum

**`cindy_relationship_momentum()`** -- Combines interaction patterns with obligation health into a 0-10 momentum score.

**Scoring formula:**
```
momentum = 10
  - min(days_since_contact / 7, 5)    # -0 to -5 for staleness
  - overdue_count * 1.5                # -1.5 per overdue obligation
  - max_overdue_days / 10              # extra penalty for very overdue
  + 2 if portfolio                     # boost for portfolio relationships
  + 1 if warming, -1 if cooling        # trend modifier
```

**Labels:** STRONG (8+) | HEALTHY (6-8) | ATTENTION (4-6) | WEAK (2-4) | CRITICAL (0-2)

**Current distribution:**
| Label | Count | Notable People |
|-------|-------|---------------|
| CRITICAL | 2 | Mohit Gupta (0.7), Supan Shah (1.8) |
| WEAK | 1 | Surabhi Bhandari (2.7) |
| ATTENTION | 5 | Ayush Sharma (4.8), Sujoy Golan (5.3), Abhishek Anita (5.4) |
| HEALTHY | 3 | Sambhav Jain, Ritik Agrawal, Arjun Gupta |
| STRONG | 11 | Rajat Agarwal, Kalyan Gautham, Madhav Tandon, Soumitra Sharma |

**Recommended actions per person:** FULFILL_OBLIGATIONS (portfolio + I_OWE) | FULFILL | NUDGE (they_owe + stale) | CHECK_IN (portfolio + stale) | RECONNECT | MAINTAIN | MONITOR

## Loop 19: Daily Briefing Upgrade

Rewrote `cindy_daily_briefing()` with:
1. **Smarter headline** incorporating both obligation and relationship health: "5 critical obligations. 5 portfolio relationships at risk. Block 30 minutes."
2. **Relationship health summary**: total contacts, strong/weak/critical counts, portfolio at risk, cooling
3. **Portfolio alerts**: from momentum data, showing company name + specific issue
4. **Cooling relationships**: all people with declining engagement > 14 days
5. **Resolution gap count**: in system health section
6. **Data quality check**: in system health section
7. **Quick wins**: now prioritize portfolio founders first, include `is_portfolio` flag

**Performance:** 435ms (up from 51ms due to momentum + resolution gap sub-calls). Acceptable for once-daily use.

## Function Inventory (38 total + 2 views + 1 cron job)

### New in this session (7):
1. `cindy_draft_nudge_message(obligation_id)` -- Context-aware THEY_OWE nudge messages
2. `obligation_deliverable_phrase(desc, name)` -- Noun-phrase extraction for natural language
3. `cindy_cross_link_people_interactions()` -- Safe people-interaction cross-linking
4. `cindy_resolution_gaps()` -- Unresolved participant report
5. `cindy_interaction_threads()` -- Cross-source interaction threading
6. `cindy_relationship_momentum()` -- 0-10 momentum scoring with portfolio context
7. `clean_obligation_description()` -- UPGRADED with multi-word entity prefixes + capitalization

### Modified in this session (2):
8. `obligation_staleness_audit()` -- Wired to use `cindy_draft_nudge_message()`
9. `cindy_daily_briefing()` -- Added relationship health, portfolio alerts, cooling warnings

### Pre-existing (29):
`cindy_agent_full_context()`, `cindy_obligation_full_context()`, `cindy_interaction_pattern_data()`, `cindy_person_intelligence()`, `cindy_outreach_priorities()`, `cindy_data_quality_check()`, `cindy_system_report()`, `cindy_intelligence_multiplier()`, `person_communication_profile()`, `detect_interaction_patterns()`, `detect_obligation_fulfillment_candidates()`, `detect_obligation_fulfillment_from_interactions()`, `generate_obligation_suggestions()`, `obligation_batch_action()`, `update_obligation_statuses()`, `resolve_interaction_participants_v2()`, `resolve_participant()`, `resolve_interaction_participants()`, `fulfill_obligation()`, `obligation_fulfillment_rate()`, `obligation_health_summary()`, `obligation_urgency_multiplier()`, `interaction_intelligence_score()`, `interaction_intelligence_report()`, `interaction_recency_boost()`, `interactions_fts_trigger()`, `detect_emerging_signals()`, `detect_opportunities()`, `detect_thesis_bias()`

## Performance Summary

| Function | Execution Time | Status |
|----------|---------------|--------|
| `cindy_draft_nudge_message(74)` | <15ms | PASS |
| `obligation_deliverable_phrase(...)` | <1ms | PASS |
| `clean_obligation_description(...)` | <1ms | PASS |
| `cindy_cross_link_people_interactions()` | <100ms | PASS |
| `cindy_resolution_gaps()` | <50ms | PASS |
| `cindy_interaction_threads()` | <40ms | PASS |
| `cindy_relationship_momentum()` | <200ms | PASS |
| `cindy_daily_briefing()` | 435ms | PASS (once-daily) |

## System State After This Session

| Metric | Before | After |
|--------|--------|-------|
| Cindy functions | 32 | 38 |
| Nudge message quality | Robotic, truncated | EA-grade, context-aware |
| Relationship momentum | Not tracked | 0-10 scoring, 22 contacts |
| Portfolio risk visibility | None in briefing | 5 alerts with company+issue |
| People-interactions links | 20 | 22 (after false positive cleanup) |
| Resolution gaps identified | Unknown | 27 documented |
| Cross-link false positive rate | N/A | 0% (v2 with guards) |
| Daily briefing sections | 9 | 12 |
| Daily briefing performance | 51ms | 435ms (richer) |
| Data quality | CLEAN | CLEAN |

## What This Enables

1. **Morning 7am briefing**: `cindy_daily_briefing()` now gives a complete EA morning report with portfolio risk alerts, human-quality nudge drafts, relationship momentum, and resolution gap awareness
2. **Nudge execution**: Draft messages from `cindy_draft_nudge_message()` are copy-pasteable to WhatsApp/email with appropriate tone and context
3. **Relationship triage**: `cindy_relationship_momentum()` surfaces CRITICAL/WEAK relationships that need immediate action, with specific recommended actions
4. **Resolution improvement**: `cindy_resolution_gaps()` tells the Cindy agent exactly which participants need resolution and why (company context available, multiple candidates, no network entry)
5. **Cross-linking safety**: `cindy_cross_link_people_interactions()` can be run repeatedly without creating false positives

## Key Decisions

1. **Nudge messages use noun phrases, not verb phrases.** "Checking in on the deck and demo video" not "checking in on send deck and demo video." The `obligation_deliverable_phrase()` function strips verbs to extract what was promised.

2. **First-name-only cross-linking requires company context.** After 13/19 false positives from naive matching, the v2 function only matches ambiguous first names when the person's company appears in the interaction's linked_companies. Unique first names (only 1 match in 4000+ person network) are safe to match.

3. **Resolution gaps are an AGENT task, not SQL.** The 27 unresolved participants (Ashwin at RSA, Rajat at Orbi, Lisa at MSC Fund) need contextual reasoning that SQL can't do. The `cindy_resolution_gaps()` function surfaces them for the Cindy agent to handle with LLM reasoning.

4. **Daily briefing performance trade-off accepted.** 435ms vs 51ms is fine for a once-daily function. The relationship_momentum and resolution_gaps sub-calls add rich context worth the compute.

## Next Priorities

1. **Gmail integration**: Grant Gmail MCP permission to ingest email interactions. This is the biggest data source gap.
2. **Cindy agent on droplet**: Wire `cindy_daily_briefing()` + `cindy_relationship_momentum()` + `cindy_draft_nudge_message()` as the agent's session toolkit
3. **WhatsApp automation**: Current extraction is manual sqlite3 queries. Need scheduled pipeline on Mac
4. **Resolution agent task**: Use `cindy_resolution_gaps()` output to resolve the 27 unlinked participants via LLM reasoning
5. **Nudge execution**: Wire nudge drafts to actual email/WhatsApp sending (AgentMail API for email, WhatsApp still TBD)
6. **Interaction dedup**: Check if WhatsApp extraction creates duplicates on re-run
7. **M5 integration**: Feed momentum scores into action scoring (people with WEAK/CRITICAL momentum should boost related action priorities)
