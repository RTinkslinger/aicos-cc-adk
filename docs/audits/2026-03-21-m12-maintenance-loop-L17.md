# M12 Data Enrichment: Maintenance Loop L17

**Date:** 2026-03-21
**Machine:** M12 Data Enrichment
**Loop type:** Quality monitoring, garbage cleanup, thesis backfill, embedding drain verification

---

## Executive Summary

Maintenance loop: 14 garbage network entries deleted, 12 duplicate companies deleted, 853 companies backfilled with thesis_thread_links (from 0%), 5 portfolio thesis_connections backfilled, 1 duplicate action dismissed, 36 merged-company status labels fixed. Embedding queue was stalled at 252 pending -- confirmed actively draining, reached 0 by end of loop. All embeddings now 100% across all entity types.

---

## Actions Taken

### 1. Garbage Network Entry Cleanup (-14 entries)
Deleted 14 entries that were organizations or garbage, not people:
- 12 org_entry_in_network: InBound, VSS, Fireside, V3, Sequoia, Antler, Bluestone, Kettleborough Ventures, Upekkha, All In Capital, Wolfpack, AUM Ventures
- 1 multi_person_entry: "Pratyush Singh, Mofid Ansari, and Rajat Dangi"
- 1 empty_name_garbage: blank name entry
- Cleaned 48 associated entity_connections + identity_map references first

### 2. Duplicate Company Cleanup (-12 entries)
Deleted 12 companies marked M12-v2-duplicate or M4-v7-flagged-duplicate:
- 10x Science (YC W26), Bidflow (YC S25), Polymorph (YC W26), Stykite (Techstars '24), Riverbank (YC S25), Alt-X (YC F25), Sciloop (YC F25), Rovr (YC F25), Piris Labs (YC W26), o11 (YC W26), ritivel (YC W26), WeldT
- All had been merged into canonical entries in prior loops
- 19 associated entity_connections cleaned first

### 3. Thesis Thread Links Backfill (+853 companies)
Backfilled `thesis_thread_links` on companies from entity_connections `thesis_relevance`:
- Before: 0/4567 companies (0.0%) had thesis_thread_links
- After: 853/4567 companies (18.7%) have thesis_thread_links
- Each link includes thesis_id, thread_name, strength, connection_type
- Sourced from 1,075 thesis_relevance connections in entity_connections

### 4. Portfolio Thesis Connection Backfill (+5 companies)
Backfilled `thesis_connection` on portfolio from entity_connections:
- Cybrilla -> Cybersecurity / Pen Testing
- Flytbase -> AI-Native Non-Consumption Markets | Cybersecurity / Pen Testing | USTOL / Aviation / Deep Tech Mobility
- Grvt -> AI-Native Non-Consumption Markets
- Spydra -> Cybersecurity / Pen Testing
- Uravu Labs -> AI-Native Non-Consumption Markets
- Portfolio thesis coverage: 64.8% -> 68.3%

### 5. Merged Status Label Fix (36 companies)
Fixed 36 companies with confusing `M12-v2-merged` enrichment_status (these are the merge WINNERS, not duplicates). Relabeled to `M12-L50-enriched`.

### 6. Duplicate Action Dismissed (1 action)
Action #141 (OVERDUE AuraML endorsement) dismissed as duplicate of #119 (same obligation).

### 7. Embedding Queue Verification
- Queue entered loop with 252 pending company embeddings
- Confirmed edge function healthy (all 200 responses, 0 failed jobs)
- Processing rate: ~75 embeddings per 2 minutes
- Queue drained to 0 by end of loop
- All entity types now at 100% embedding coverage

---

## Before/After Metrics

| Metric | Before | After | Delta |
|--------|--------|-------|-------|
| Companies total | 4,579 | 4,567 | -12 (duplicates removed) |
| Companies embedding | 94.5% (252 missing) | 100.0% | +5.5% |
| Companies thesis_links | 0.0% | 18.7% (853) | +18.7% |
| Companies garbage/duplicate | 48 | 0 | -48 |
| Network total | 3,527 | 3,513 | -14 (garbage removed) |
| Network embedding | 100% | 100% | stable |
| Network garbage | 14 | 0 | -14 |
| Portfolio thesis_pct | 64.8% | 68.3% | +3.5% |
| Portfolio embedding | 100% | 100% | stable |
| Entity connections | 23,783 | 23,716 | -67 (orphan cleanup) |
| Entity connections orphaned | 67 | 0 | -67 |
| Embedding queue | 252 | 0 | drained |
| Actions duplicates | 1 | 0 | -1 |

### Quality Checks (all pass)

| Check | Status |
|-------|--------|
| Orphaned entity_connections | 0 |
| Garbage entries (network) | 0 |
| Garbage entries (companies) | 0 |
| Stale proposed actions | 0 |
| Pseudo-ID count | 0 |
| Exit consistency | OK |
| Embedding queue | 0 (drained) |

### Remaining Gaps (require Datum agent web enrichment)

| Gap | Count | Notes |
|-----|-------|-------|
| Companies thin content (<50 chars) | 609 | Need web scraping for richer data |
| Companies missing website | 3,805 (83.3%) | Mostly NA/bulk pipeline entries |
| Companies missing type | 3,859 (84.5%) | Same cohort |
| Companies missing domain | 3,809 (83.3%) | Same cohort |
| Portfolio missing thesis | 45 (31.7%) | Many non-AI companies, expected gap |
| Network missing last_interaction | 3,477 (98.9%) | Cindy agent needed for interaction tracking |
| Network missing email | 2,434 (69.3%) | LinkedIn enrichment candidate |

---

## System State

- Embedding cron: healthy (every 2 min, processing correctly)
- All datum_* functions: operational
- datum_data_quality_check: all OK except portfolio_thesis WARNING (68.3%)
- datum_company_name_deduplicator: 49 prefix_suffix matches flagged, all reviewed as distinct entities (different Notion pages)
- No new duplicates needing merge
