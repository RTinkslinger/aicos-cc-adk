# Cindy+Datum Refactor Audit
*2026-03-20 — Post-refactor verification*

## Summary

The Cindy+Datum refactor separated data plumbing from intelligence reasoning across the
agent fleet. Python processors that mixed API calls, regex signal extraction, people
resolution, and DB writes were decomposed into:

1. **Thin fetchers** (Python) — API/file reading + staging to `interaction_staging`
2. **Datum Agent** (Claude SDK) — people resolution, entity linking, clean data writes
3. **Cindy Agent** (Claude SDK) — LLM-based obligation detection, signal extraction, action creation

## Verification Checklist

### Database
- [x] `interaction_staging` table exists with correct schema (9 core + 8 extra columns)
- [x] `interactions.cindy_processed` column exists (BOOLEAN DEFAULT FALSE)
- [x] `interactions.datum_staged_id` column exists (FK to interaction_staging)
- [x] Indexes created: `idx_staging_datum_pending`, `idx_staging_cindy_pending`, `idx_interactions_cindy_pending`
- [x] 11 regex-processed sample rows cleaned from `interactions` (0 remaining)
- [x] `people_interactions` cleaned (0 remaining)

### Fetcher Files (droplet verified)
- [x] `email/fetcher.py` present on droplet
- [x] `granola/fetcher.py` present on droplet
- [x] `calendar/fetcher.py` present on droplet
- [x] `whatsapp/extractor.py` rewritten on droplet

### Deleted Files (droplet verified)
- [x] `email/email_processor.py` removed from droplet
- [x] `email/obligation_extractor.py` removed from droplet
- [x] `granola/processor.py` removed from droplet
- [x] `obligations/obligation_detector.py` removed from droplet
- [x] `calendar/ics_processor.py` removed from droplet
- [x] `__pycache__` cleaned

### Agent CLAUDE.md Updates
- [x] Datum CLAUDE.md: interaction_staging pipeline documented
- [x] Datum CLAUDE.md: 6-tier people resolution algorithm added
- [x] Datum CLAUDE.md: M12 enrichment as permanent machinery
- [x] Cindy CLAUDE.md: identity updated to Intelligence Analyst
- [x] Cindy CLAUDE.md: table access updated (no more people resolution writes)
- [x] Cindy CLAUDE.md: processing loop documented (LLM reasoning over clean data)
- [x] Orchestrator HEARTBEAT.md: Steps 3f (staging check) and 3g (intelligence check) added
- [x] Orchestrator CLAUDE.md: Cindy description updated, anti-patterns 17-18 added

### Skills
- [x] `skills/cindy/obligation-reasoning.md` created (LLM-based)
- [x] `skills/cindy/signal-extraction.md` created (LLM-based)
- [x] `skills/datum/people-linking.md` copied (moved from cindy)

### Deployment
- [x] Deployed via deploy.sh — all 3 services healthy
- [x] state-mcp :8000 OK
- [x] web-tools-mcp :8001 OK
- [x] orchestrator OK

## Architecture Before vs After

### Before (4,587 lines of mixed concerns)
```
Fetcher+Processor+Intelligence all in one file:
  email_processor.py: API client + regex signals + people resolution + DB writes
  granola/processor.py: parse + regex signals + calendar matching + DB writes
  obligation_extractor.py: regex patterns for 18 obligation types
  obligation_detector.py: regex detection + priority + dedup + auto-fulfillment
  whatsapp/extractor.py: SQLite read + classification + regex signals + DB writes
  ics_processor.py: .ics parse + people resolution + DB writes
```

### After (1,240 lines of pure plumbing + LLM reasoning guidance)
```
Layer 1 - Fetchers (Python, ~1,240L total):
  email/fetcher.py: AgentMail API → interaction_staging
  granola/fetcher.py: JSON parse → interaction_staging
  calendar/fetcher.py: .ics parse → interaction_staging
  whatsapp/extractor.py: ChatStorage.sqlite → interaction_staging

Layer 2 - Datum Agent (Claude SDK, CLAUDE.md instructions):
  interaction_staging → people resolution → interactions (clean)

Layer 3 - Cindy Agent (Claude SDK, CLAUDE.md + skills):
  interactions (clean) → LLM reasoning → obligations + signals + actions
```

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| Datum not processing staging rows | Orchestrator Step 3f checks every heartbeat |
| Cindy not processing clean interactions | Orchestrator Step 3g checks every heartbeat |
| People resolution quality drop | Same 6-tier algorithm, now documented in Datum CLAUDE.md + skill |
| Obligation detection quality | LLM reasoning should be BETTER than regex (catches nuance) |
| Old __pycache__ on droplet | Cleaned during deploy |

## Next Steps

1. First real data test: send a test email to cindy.aacash@agentmail.to, verify staging → Datum → Cindy flow
2. Monitor Orchestrator logs for Steps 3f/3g triggering correctly
3. Compare LLM-detected obligations vs regex-detected (quality baseline)
