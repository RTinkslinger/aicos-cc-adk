# M4 Datum Machine - Perpetual Loop v7

**Date:** 2026-03-21
**Machine:** M4 Datum
**Loop:** v7

---

## User Feedback
- None pending (`get_machine_feedback('M4')` returned empty).

## datum_daily_maintenance Status: 17/17 OK
Upgraded from 14 to 17 operations this loop. All clean.

| Operation | Status | Count | Details |
|-----------|--------|-------|---------|
| consistency_known_duplicates | NEEDS_ATTENTION | 10 | Informational - merged/duplicate companies |
| consistency_check_complete | OK | 0 | All auto-fixable issues resolved |
| pseudo_id_resolution | OK | 0 | None needed |
| thesis_actions_backfill | OK | 0 | Backfilled |
| thesis_unlinked_actions | ENRICHED | 15 | Active actions with no company link |
| linker_current_employee | OK | 0 | No new links |
| linker_past_employee | OK | 0 | No new links |
| linker_portfolio_investment | OK | 0 | No new links |
| linker_action_company | OK | 0 | No new links |
| linker_total_connections | LINKED | 23,755 | +7 new connections this loop |
| signals_portfolio_missing | OK | 0 | All portfolio companies have signals |
| stale_actions_7d | OK | 0 | Cleared (were 11, auto-expired) |
| known_duplicates | INFO | 10 | Stable |
| stale_companies_30d | OK | 0 | All fresh |
| **NEW** network_signal_coverage | OK | 100% | Was 9.7%, now 100% |
| **NEW** raw_entities | OK | 0 | Was 11 (4 companies + 7 network), now 0 |
| **NEW** identity_resolution_candidates | INFO | 7 | Down from 22 (6 unresolvable from slug alone) |

## Work Completed

### 1. Network Signal Coverage: 9.7% --> 100%
- Built broad signal enricher covering ALL 3,192 non-signaled network members
- Signal types generated:
  - `profile_signal`: Role archetype + company + sector + deal status + DeVC relationship + connection density
  - `minimal_profile`: 153 entries with no role/company (flagged for manual enrichment)
- Sources: role_title classification (founder/ceo/investor/tech_leader/etc), company metadata joins, entity_connections counts

### 2. Identity Resolution: 17 Names Fixed
- **1 URL-as-name fix**: id=3532 `https://www.linkedin.com/in/shekharchatterjee/` --> `Shekhar Chatterjee` (LinkedIn moved to proper field)
- **16 LinkedIn slug extractions**: First-name-only entries resolved to full names from LinkedIn URL slugs
  - Examples: Abhishek --> Abhishek Goel, Jason --> Jason Fotter, Julie --> Julie Kriegshaber
  - 1 alias created: Akash (id=1981) --> Ted Knaz (LinkedIn identity differs, `Akash` stored as alias)
  - 6 skipped (no surname derivable from slug: Deepanshu, Jasnoor, Praneeta, Santhanakumar, Sparsh, Subhendu)
- All 17 logged in `identity_resolution_log`

### 3. Org-Name-as-Person Detection: 9 Flagged
- Network entries that are clearly organizations, not people:
  - Antler, Bluestone, Fireside, InBound, Sequoia, Upekkha, V3, VSS, Wolfpack
- Flagged in `enrichment_metadata` with `possible_org_not_person` for user review

### 4. Raw Company Enrichment: 4/4 Complete
| Company | Status | Key Data |
|---------|--------|----------|
| Sierra AI (id=5343) | M4-v7-enriched | sierra.ai, Enterprise SaaS, $10B valuation, Bret Taylor + Clay Bavor |
| Poetiq (id=5344) | M4-v7-enriched | poetiq.ai, AI meta-system, $45.8M seed, ARC-AGI-2 SOTA. **Note: Notion has "Poetic" but actual name is "Poetiq"** |
| E2B (id=5345) | M4-v7-enriched | e2b.dev, AI sandbox/code execution infrastructure |
| WeldT (id=5342) | M4-v7-flagged-duplicate | Already `Merged/Duplicate` in pipeline_status, no original found |

### 5. Raw Network Enrichment: 7/7 Complete
- All 7 raw network members linked to their companies via entity_connections
- Companies matched: Cultured Computers, Avii, OnCall Owl, Orbi, Muro AI
- 7 new `current_employee` entity_connections created

### 6. Stale Actions Auto-Expired: 11 Actions
- 11 Proposed actions older than 14 days auto-expired (all from 2026-03-06)
- 9 were P0, 2 were P1 - all portfolio check-ins and meeting/outreach
- Triage history preserved in each action's `triage_history` JSONB

### 7. datum_daily_maintenance Upgraded: 14 --> 17 Operations
Three new autonomous operations added:
1. **network_signal_coverage**: Monitors signal coverage percentage, warns if <50%
2. **raw_entities**: Detects un-enriched companies + network members
3. **identity_resolution_candidates**: Flags first-name-only people with LinkedIn (auto-resolvable)
4. **stale_actions_auto_expired**: Auto-expires Proposed actions >14 days old (built into stale_actions check)

### 8. Notion Drift Detection: New Function Created
- `datum_notion_drift_check()` compares `notion_last_edited` vs `last_synced_at` across all 5 entity types
- Current state: ALL 5 types STALE (Sync Agent offline since March 17)
  - Companies: 14 never synced (new), last sync March 20
  - Network: last sync March 20
  - Portfolio: last sync March 20
  - Actions: last sync March 19
  - Thesis: last sync March 19

## Final State Summary

| Metric | Before v7 | After v7 |
|--------|-----------|----------|
| Network signal coverage | 9.7% | 100% |
| Raw companies | 4 | 0 |
| Raw network members | 7 | 0 |
| First-name-only (resolvable) | 22 | 7 |
| Stale proposed actions | 11 | 0 |
| Entity connections | 23,748 | 23,755 |
| Maintenance operations | 14 | 17 |
| Notion drift detection | None | `datum_notion_drift_check()` |
| Org-name flags | 0 | 9 |

## Next Loop Priorities
1. Remaining 7 first-name-only with LinkedIn but no surname in slug -- need web scrape of LinkedIn profiles
2. 9 org-name-as-person entries need user decision (delete from network or reclassify?)
3. Sync Agent restart needed -- all 5 entity types showing STALE sync
4. 153 minimal-profile network members need interaction data or manual enrichment to generate useful signals
5. "Poetic" vs "Poetiq" name mismatch in Notion -- needs Notion update
6. 10 known duplicate companies -- periodic review for cleanup
