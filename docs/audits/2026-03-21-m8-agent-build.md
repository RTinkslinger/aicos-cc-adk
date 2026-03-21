# M8 Cindy Agent Build Audit — 2026-03-21

## Problem Statement

Previous M8 sessions built 33 SQL functions in Postgres but wrote ZERO agent-facing
files. The Cindy agent on the droplet had no way to discover or use these functions.
The SQL layer was complete; the agent instruction layer was missing.

## What Was Built

### 4 New Skill Files (agent-facing documentation for SQL functions)

| File | Functions Covered | Purpose |
|------|-------------------|---------|
| `skills/cindy/obligation-triage.md` | 10 functions | Obligation lifecycle: triage, audit, batch action, nudge drafting |
| `skills/cindy/interaction-analysis.md` | 5 functions | Cross-source reasoning, key question intelligence, threads |
| `skills/cindy/ea-briefing.md` | 6 functions | Daily briefing, outreach priorities, relationship momentum, deal velocity |
| `skills/cindy/person-intelligence.md` | 7 functions | Person profiles, communication patterns, nudge drafts, resolution gaps |

Each skill file includes:
- Function signatures with argument types and return types
- JSON return structure documentation
- Usage examples (psql commands)
- Complete workflow instructions (step-by-step sequences)
- Anti-patterns specific to each domain
- Integration points with other agents

### Updated Cindy CLAUDE.md (3 new sections added)

**Section 15: SQL Intelligence Functions (33 functions)**
- Complete function registry organized into 5 categories:
  - Obligation Management (10 functions)
  - Interaction Analysis (5 functions)
  - EA Briefing & Dashboard (6 functions)
  - Person Intelligence (7 functions)
  - System & Quality (5+1 legacy functions)
- Processing cycle integration map showing when each function is called
- psql usage patterns for all argument types (none, integer, jsonb, text)

**Section 16: Collaboration with Fleet Agents**
- Cindy <-> Datum Agent boundary (intelligence vs data ops, confidence gating)
- Cindy <-> Megamind signal routing rules
- Cindy <-> Content Agent scope separation
- Cindy <-> ENIAC/Actions Queue flow

**Section 17: Skills Reference**
- Complete skill file index (11 files total: 4 new + 7 existing)
- Skill loading strategy (which skills to load for which task)

## SQL Function Inventory (33 total)

### Obligation Management
1. `cindy_obligation_full_context(integer)` -> jsonb
2. `generate_obligation_suggestions(integer)` -> jsonb
3. `obligation_staleness_audit()` -> jsonb
4. `obligation_batch_action(jsonb)` -> jsonb
5. `obligation_health_summary()` -> jsonb
6. `obligation_fulfillment_rate()` -> jsonb
7. `obligation_urgency_multiplier(actions_queue)` -> numeric
8. `obligation_deliverable_phrase(text, text)` -> text
9. `cindy_obligation_key_question_link()` -> jsonb
10. `cindy_obligation_kq_fts_match(integer)` -> jsonb

### Interaction Analysis
11. `cindy_interaction_pattern_data(integer)` -> jsonb
12. `cindy_interaction_kq_intelligence()` -> jsonb
13. `cindy_cross_source_reasoning()` -> jsonb
14. `cindy_interaction_threads()` -> jsonb
15. `cindy_kq_update_proposals()` -> jsonb

### EA Briefing & Dashboard
16. `cindy_daily_briefing_v3()` -> jsonb
17. `cindy_outreach_priorities()` -> jsonb
18. `cindy_relationship_momentum()` -> jsonb
19. `cindy_deal_velocity()` -> jsonb
20. `cindy_autonomous_ea_dashboard()` -> jsonb
21. `cindy_companies_needing_attention(integer)` -> jsonb

### Person Intelligence
22. `cindy_person_intelligence(integer)` -> jsonb
23. `person_communication_profile(integer)` -> jsonb
24. `cindy_draft_nudge_message(integer)` -> jsonb
25. `cindy_resolution_gaps()` -> jsonb
26. `cindy_resolve_with_company_context()` -> jsonb
27. `cindy_cross_link_people_interactions()` -> jsonb
28. `cindy_network_creation_suggestions()` -> jsonb

### System & Quality
29. `cindy_agent_full_context()` -> jsonb
30. `cindy_agent_skill_registry()` -> jsonb
31. `cindy_system_report()` -> jsonb
32. `cindy_data_quality_check()` -> jsonb
33. `cindy_intelligence_multiplier(actions_queue)` -> numeric
34. `cindy_daily_briefing()` -> jsonb (legacy v1)

## Existing Infrastructure Confirmed

### Python Fetchers (plumbing — already built)
- `cindy/email/fetcher.py` — AgentMail API -> interaction_staging
- `cindy/granola/fetcher.py` — Granola MCP JSON -> interaction_staging
- `cindy/whatsapp/extractor.py` — ChatStorage.sqlite -> interaction_staging
- `cindy/calendar/fetcher.py` — .ics files -> interaction_staging

### Existing Skills (LLM reasoning patterns — already built)
- `skills/cindy/obligation-detection.md` — Obligation detection patterns by surface
- `skills/cindy/obligation-reasoning.md` — Deep obligation reasoning, dedup, auto-fulfillment
- `skills/cindy/signal-extraction.md` — Action items, thesis/deal/relationship signals
- `skills/cindy/calendar-gap-detection.md` — Context gap detection, richness scoring
- `skills/cindy/email-processing.md` — Email parsing, thread tracking
- `skills/cindy/people-linking.md` — Cross-surface identity resolution
- `skills/cindy/whatsapp-parsing.md` — WhatsApp extraction, privacy constraints

### Agent Infrastructure
- `cindy/.claude/settings.json` — Stop hook, PromptManifest hook, PreCompact hook
- `cindy/state/` — Iteration tracking, session management, last log
- `cindy/CHECKPOINT_FORMAT.md` — Compaction format
- `cindy/obligations/__init__.py` — Obligations module stub

## Gap Assessment

### Now Complete
- SQL function layer (33 functions in Postgres)
- Agent skill files (11 total covering all functions)
- Agent CLAUDE.md with function registry, collaboration rules, skill loading strategy
- Python fetchers for all 4 surfaces
- Hook infrastructure (Stop, PromptManifest, PreCompact)

### Still Needed (next loop)
1. **AgentMail setup** — cindy.aacash@agentmail.to not yet configured. Email fetcher needs a live inbox.
2. **Calendar API integration** — calendar/fetcher.py handles .ics files but not Google Calendar API incremental sync
3. **WhatsApp extraction cron** — Mac-side cron job for daily iCloud backup extraction not set up
4. **Deployment** — `deploy.sh` syncs to droplet but Cindy is not yet in the orchestrator lifecycle
5. **Test data** — No real interactions in the database yet. Need end-to-end test with sample data.
6. **Orchestrator integration** — Cindy needs to be registered in lifecycle.py alongside Content Agent

## User Feedback

No M8 feedback found in `get_machine_feedback('M8')`.
