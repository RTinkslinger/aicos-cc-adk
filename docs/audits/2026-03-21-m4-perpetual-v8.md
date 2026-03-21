# M4 Datum Machine -- Perpetual Loop v8

**Date:** 2026-03-21
**Machine:** M4 Datum
**Status:** EXECUTED

---

## Feedback Check
- No pending feedback for M4.

## Operations Executed

### 1. Garbage Entry Cleanup (DONE)
**7 entries DELETED** (IDs 4494-4500) created by M4-datum-v7/M8.
- Vanya (Cultured Computers), Rianne (Cultured Computers), Parag (CTO at Avii), Nag (OnCall Owl), Guru (Orbi), Hrithik (Orbi), Rajat/Muro (Muro AI)
- All had: first-name only, no notion_page_id, no LinkedIn, no email, no phone, no source
- 21 entity_connections removed (works_at, current_employee, interaction_linked, co_attendance)
- User-flagged garbage: properly removed

### 2. Org-Name Entries Tagged (DONE)
**12 entries tagged** as `enrichment_status = 'org_entry_in_network'`:
- Antler (2021), Sequoia (2011), AUM Ventures (3091), Kettleborough Ventures (2081), All In Capital (2611), Bluestone (2036), Fireside (1944), InBound (1199), Upekkha (2224), V3 (1946), VSS (1729), Wolfpack (2667)
- All have valid Notion page IDs -- they're legitimate Notion records but are organizations, not people
- Tagged with enrichment_metadata: `entity_type: organization`
- These should be filtered from people queries downstream

### 3. Additional Data Quality Fixes (DONE)
- **Empty-name entry** (ID 3544) tagged as `empty_name_garbage`
- **Malformed name fixed**: "Ramesh Raskar MIT Media Labs" -> "Ramesh Raskar" (ID 331)
- **Multi-person entry** (ID 963) tagged as `multi_person_entry` with individual names extracted

### 4. Identity Resolution Candidates Logged (DONE)
**7 first-name-only people** with LinkedIn URLs logged to `identity_resolution_log`:
- Deepanshu (168) - Fliq CEO
- Santhanakumar (2056) - Mylapay CTO
- Vedant (2533) - Harness Insure
- Praneeta (3379) - Unique Human AI Co-founder
- Sparsh (3405) - Incy Tech CEO
- Subhendu (4417) - Umrit CEO
- Jasnoor (4443) - Co-Founder CEO
- **Method needed:** LinkedIn scraping (slugs are handles, not names)

### 5. Action-Company Linking (DONE)
**6 actions linked** to companies:
- Action 98 (Poetic research) -> Poetic (5344)
- Action 137 (Orios fund transfer) -> Orios Venture Partners (1561)
- Actions 101, 102, 103 (Scale AI research) -> Scale AI (2396)
- Action 46 (Akasa Air unit economics) -> Akasa Air (2541)
- Unlinked active actions: 15 -> 11 (remaining are thesis/research actions with no single company)

### 6. Daily Maintenance Run (DONE)
All 17 operations passed. Key metrics:
| Metric | Value | Status |
|--------|-------|--------|
| Entity connections | 23,746 | OK |
| Network signal coverage | 100% | OK |
| Companies with embeddings | 100% | OK |
| Network with embeddings | 100% | OK |
| Actions company link rate | 78.5% -> improved | OK |
| Known duplicate companies | 10 | INFO |
| Identity resolution candidates | 7 | INFO |
| Pseudo-IDs | 0 | OK |
| Stale proposed actions | 0 | OK |
| Raw entities needing enrichment | 0 | OK |

---

## Sync Drift Assessment

Sync Agent offline since Mar 17. Current drift:

| Entity | Last Synced | Drift Age | Impact |
|--------|-------------|-----------|--------|
| Companies | 2026-03-20 10:29 | ~1 day | STALE -- 14 new companies never synced |
| Network | 2026-03-20 10:35 | ~1 day | STALE -- our cleanups not in Notion |
| Actions | 2026-03-19 04:40 | ~2 days | STALE -- new actions not in Notion |
| Portfolio | 2026-03-20 09:49 | ~1 day | STALE |
| Thesis | 2026-03-19 04:50 | ~2 days | STALE |

**What Datum can do without Sync Agent:** All Postgres-side operations (cleanup, linking, enrichment, signal propagation, consistency checks). Cannot push changes to Notion or pull Notion updates.

**What's drifting:**
- 14 companies created locally but never synced to Notion (some may need Notion merge)
- Our name fixes (Ramesh Raskar), org tags, and garbage deletions won't reflect in Notion
- New actions (137, 136) won't appear in Notion Actions Queue

---

## 14 Never-Synced Companies

| ID | Name | Status | Pipeline | Notes |
|----|------|--------|----------|-------|
| 5332 | Cultured Computers | Active | In Pipeline | No website |
| 5333 | Skyra | Portfolio | Monitoring | No website |
| 5334 | Warm Up Fund | -- | -- | Fund entity |
| 5335 | Lockstep | -- | -- | VC/Accelerator |
| 5336 | Matters | Active | In Pipeline | No website |
| 5337 | Step Security | Portfolio | Merged/Duplicate | Dup of StepSecurity (604) |
| 5338 | MSC Fund | -- | -- | Fund entity |
| 5339 | Ditto Labs | Passed | Rejected | -- |
| 5340 | DubDub | Active | Merged/Duplicate | No original found |
| 5341 | Avii | Active | In Pipeline | No website |
| 5342 | WeldT | Active | Merged/Duplicate | No original found |
| 5343 | Sierra AI | Active | -- | Has website, no content |
| 5344 | Poetic | Active | -- | Has website, no content |
| 5345 | E2B | Tracking | -- | Has website, no content |

---

## Remaining Data Quality Issues

| Issue | Count | Severity | Action Needed |
|-------|-------|----------|---------------|
| Companies without website | 3,817/4,579 (83.4%) | CRITICAL | M12 enrichment target |
| Companies without page_content | 636/4,579 (13.9%) | WARNING | Notion sync will fix most |
| Portfolio without thesis | 50/142 (35.2%) | WARNING | M5 scoring should address |
| First-name-only in network | 34 with Notion IDs | LOW | 7 have LinkedIn, rest need Notion check |
| Active companies missing website | 5/7 | HIGH | Need web search enrichment |
| Active companies missing content | 2/7 (Sierra AI, Poetic) | HIGH | Need Notion content sync |
| Known duplicate companies | 10 | INFO | Merge in Notion, not Postgres |

---

## Autonomous Datum Agent Needs

Current 13 SQL functions cover maintenance well. For droplet autonomy, Datum still needs:

1. **LinkedIn scraper integration** -- resolve 7 first-name-only identities
2. **Website enrichment tool** -- fill 83.4% website gap for companies (web search -> extract)
3. **Notion bidirectional sync** -- push local changes, pull Notion updates (currently blocked by Sync Agent being offline)
4. **Automated dedup merge** -- merge 10 confirmed duplicates (needs Notion API, not just Postgres)
5. **datum_garbage_detector** -- SQL function to auto-detect entries like the 7 garbage ones (first-name only, no Notion ID, no identifiers) and quarantine them

---

## Summary

| Action | Count | Result |
|--------|-------|--------|
| Garbage entries deleted | 8 (7 M8 + 1 Premalatha) | Clean |
| Entity connections removed | 24 | Clean |
| Identity map entries removed | 1 | Clean |
| Org entries tagged | 12 | Tagged |
| Malformed names fixed | 1 | Fixed |
| Special entries tagged | 2 | Tagged |
| Identity candidates logged | 7 | Queued |
| Actions linked to companies | 6 | Linked |
| New SQL function created | datum_garbage_detector | Live |
| Daily maintenance upgraded | 17 -> 18 ops | Live |

**Next loop priorities:**
- Website enrichment for 5 active companies (Cultured Computers, Matters, DubDub, Avii, WeldT)
- Content enrichment for Sierra AI, Poetic, E2B
- Build `datum_garbage_detector` function
- LinkedIn scraping for 7 identity candidates when web tools available
