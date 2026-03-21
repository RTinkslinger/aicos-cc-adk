# M4 Datum Machine — Perpetual Data Ops Audit
**Date:** 2026-03-21
**Machine:** M4 DATUM (Data Operations)
**Loop:** 1

---

## Executive Summary

Fixed critical data linkage and enrichment gaps across the Postgres knowledge store. Actions-to-companies linkage went from 0% valid to 68% valid (98/144). All 142 portfolio companies now enriched (was 139/142). Network embedding recovery confirmed active and draining. Entity connections healthy (23,250 records, 13 types).

---

## Fixes Applied This Loop

### 1. Action ↔ Company Linkage (CRITICAL FIX)

**Problem discovered:** M5 Scoring linked 66 actions to company IDs, but used **Portfolio DB page IDs** instead of **Companies DB page IDs**. Result: 66/66 linked actions were orphans (0% valid joins to companies table).

**Root cause:** Portfolio table has `notion_page_id` (from Portfolio DB in Notion) and `company_name_id` (from Companies DB in Notion). M5 used `portfolio.notion_page_id` instead of `portfolio.company_name_id` as the company reference.

**Fix:** Remapped all 66 actions through the chain:
```
actions_queue.company_notion_id → portfolio.notion_page_id → portfolio.company_name_id → companies.notion_page_id
```
Result: 66 valid links, 0 orphans.

### 2. Unlinked Actions Resolution (+32 new links)

**Problem:** 78 actions had NULL company_notion_id. Many were from company-specific thesis research or deal-flow meetings but lacked company references.

**Method:** Multi-signal matching:
- CEO/founder name → network table → current_company_ids → companies (9 matches)
- Product/domain references in action text (WeldT, Dallas Renal, PT Pro, Kisan Agri Show) → company identification (14 matches)
- Direct company name mentions with word-boundary matching (9 matches)

**Result:**
| Metric | Before | After |
|--------|--------|-------|
| Total actions | 144 | 144 |
| Validly linked | 0 | 98 |
| Orphan links | 66 | 0 |
| Unlinked | 78 | 46 |
| Link rate | 0% | 68.1% |

**Remaining 46 unlinked:** Correctly unlinked — 27 are macro-thesis research (SaaS Death, CLAW stack, agent deployment, 8 Moats framework), 10 are deal-flow companies not yet in Companies DB (Cultured Computers, DubDub, Lockstep, MSC Fund, Avii, Sierra AI), 5 are obligation follow-ups for those companies, 4 are personal/ops.

### 3. Portfolio Company Enrichment (3 stubs fixed)

| Company | Before | After |
|---------|--------|-------|
| Coind | 197 chars (stub) | 596 chars (enriched from research) |
| Lane | 164 chars (stub) | 586 chars (enriched from research) |
| Potpie | 180 chars (stub) | 682 chars (enriched from research) |

**Result:** 142/142 portfolio companies now have >200 chars page_content (was 139/142).

### 4. Embedding Recovery Verification

**Status:** RECOVERING (not stalled as dashboard reported)

| Table | Total | Embedded | Missing | Coverage |
|-------|-------|----------|---------|----------|
| Companies | 4,575 | 4,556 | 19 | 99.6% |
| Portfolio | 142 | 142 | 0 | 100% |
| Actions Queue | 144 | 144 | 0 | 100% |
| Thesis Threads | 8 | 8 | 0 | 100% |
| Content Digests | 22 | 22 | 0 | 100% |
| Network | 3,528 | 1,281 | 2,247 | 36.3% |

**Network embedding gap:** 2,247 missing. Queue had 2,482 jobs at start, draining to 2,320 during this session (~16 jobs/min). Edge Function is working (200 status on all recent calls). Cron job runs every 2 min processing 5 batches of 15 items. Estimated drain time: ~2.5 hours from session start.

**Root cause of low network coverage:** The `clear_network_embedding_on_update` trigger clears embeddings when `page_content` is updated. Recent bulk page_content enrichment for ~2,400+ network records cleared their embeddings and queued re-embedding. The system is self-healing — just slow.

---

## Data Quality Assessment

### Portfolio ↔ Companies: HEALTHY
- 142/142 portfolio companies have matching companies entries
- All links via `portfolio.company_name_id = companies.notion_page_id` are valid
- No orphans

### Entity Connections: HEALTHY (not empty as audit claimed)
- 23,250 connections across 13 types
- 3,633 unique sources, 4,573 unique targets
- Top types: vector_similar (10,719), sector_peer (3,103), current_employee (3,062), past_employee (2,898)

### Network Roles: CLEAN
- No corrupted role titles (no URLs, HTML, JSON in role_title)
- Role distribution is reasonable: Co-Founder CEO (1,079), Founder (412), Co-founder (330), etc.
- 162 records with NULL role_title (acceptable)

### Network Duplicates: LOW RISK
- Top dupe: "Naman Jain" (4 entries) — 3 are confirmed different people (different companies/notion IDs), 1 is a likely orphan (id=781, no notion_page_id, no companies)
- Other dupes are common Indian names with different company affiliations

### Sync Staleness: ACCEPTABLE
| Table | Staleness | Never Synced |
|-------|-----------|-------------|
| Companies | ~1 day | 10 |
| Network | ~1 day | 3 |
| Portfolio | ~1 day | 0 |
| Actions Queue | ~2 days | 29 |

Not 50+ hours as prior audit stated. SyncAgent is disabled so no automated sync running — staleness grows linearly.

### Companies Content Quality
| Category | Count | % |
|----------|-------|---|
| Good (>500 chars) | 45 | 1.0% |
| Medium (201-500 chars) | 1,537 | 33.6% |
| Small stub (51-200 chars) | 2,360 | 51.6% |
| Tiny (1-50 chars) | 633 | 13.8% |

65% of companies have template stub content. This is expected — the 4,575 companies include the entire deal flow pipeline (4,433 non-portfolio companies). Enriching all of them is a long-term M12 Data Enrichment task, not a data ops fix.

---

## Remaining P0s for Next Loop

1. **Deal-flow companies not in DB:** Cultured Computers, DubDub, Lockstep, MSC Fund, Avii, Sierra AI need to be created in Companies DB (these have active actions referencing them)
2. **Actions Queue sync:** 29 actions never synced to Notion. When SyncAgent re-enables, these will sync.
3. **Network orphan cleanup:** id=781 (Naman Jain, no notion_page_id, no companies) — candidate for removal or merge
4. **Companies never synced:** 10 companies with no last_synced_at — likely Datum-created entries that need initial Notion push

---

## Cross-Machine Signals

- **M5 Scoring:** Action linkage fix means M5's scoring models now have valid company context for 98/144 actions. Re-scoring should improve quality.
- **M9 Intel QA:** Search accuracy should improve as network embeddings recover (36% → 100% over next ~2 hours).
- **M12 Data Enrichment:** 2,993 companies with <200 char content remain the biggest data gap. Portfolio companies are now 100% covered.
- **CIR (M10):** Entity connections are healthy, propagation rules can fire on valid data.
