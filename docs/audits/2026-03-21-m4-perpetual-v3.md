# M4 Datum Machine — Perpetual Loop v3
**Date:** 2026-03-21
**Machine:** M4 (Datum)
**Loop:** Perpetual v3

---

## Executive Summary

This loop executed 5 enrichment operations, created 2 autonomous SQL functions, and significantly improved data quality across all tables. Key wins: thesis mapping jumped 40.8% -> 64.8%, actions thesis-linking jumped from 37.5% -> 68.8%, 18 exited companies properly marked, 39 companies backfilled with funding data.

---

## Enrichment Operations Executed

### 1. Funding Backfill (39 companies)
**What:** Companies in the companies table had missing `venture_funding` despite portfolio table having `entry_round_raise`, `round_2_raise`, and `stage_at_entry` data.
**Action:** Derived funding descriptions from portfolio round data (e.g., "pre-product ($2.5M)", "Series A ($5.0M)").
**Result:** 39 portfolio companies enriched. Portfolio company funding coverage: 44.4% -> 68.3%.

### 2. Exit Marking Consistency (18 companies)
**What:** Portfolio table marked 19 companies as exited/deadpool, but only 1 (Rhym) was properly marked in companies table (`pipeline_status = 'Acquired/Shut Down/Defunct'`).
**Action:** Updated companies.pipeline_status for all 18 inconsistent records. Also fixed Finsire's deal_status from "In Strike Zone" to "NA".
**Result:** Exit marking is now 100% consistent across portfolio and companies tables.
**Companies fixed:** Digital Paani, Coind, ElecTrade, OfScale, GlamPlus, GoCredit, Bidso, iBind Systems, BoxPay, Obvious Finance, Finsire, OhSoGo, Puch AI, Dataflos, Answers AI, Mindforest, Multiwoven, Manufacture AI.

### 3. Portfolio Thesis Mapping (34 companies)
**What:** Only 58/142 (40.8%) portfolio companies had thesis connections.
**Action:** Analyzed sector, sector_tags, and JTBD for all 84 unmapped companies. Mapped 34 to existing thesis threads based on clear alignment.
**Result:** 92/142 (64.8%) now mapped.
**Mapping by thesis:**
- AI-Native Non-Consumption Markets: 11 (Insta Astro, Felicity, Fondant, GameRamp, Supernova, Renderwolf, Eight Network, Turnover, Caddy, VoiceBit, YOYO AI)
- SaaS Death / Agentic Replacement: 14 (Recrew AI, Coffeee.io, Klaar, SalesChat, SuprSend, Rhym, Hotelzify, GlamPlus, Grexa, Orange Slice, Revspot.AI, ExtraaEdge, Unifize, Lucio AI)
- Agentic AI Infrastructure: 5 (Puch AI, Spheron Network, Morphing Machines, Terafac, Realfast)
- CLAW Stack: 4 (Atica, Dataflos, Patcorn, UGX AI)
- Cybersecurity / Pen Testing: 2 (Aurva, Pinegap AI)

**Remaining 50 unmapped:** Consumer brands (20), Financial Services (14), B2B (9), Frontier/Deep Tech (6), SaaS (1). These are domain-specific investments that don't map to any existing thesis thread. They would need new thesis threads or a "Pre-Thesis" category.

### 4. Actions Thesis Backfill (45 actions)
**What:** 85 actions had company links but no thesis connection.
**Action:** Backfilled thesis_connection from the linked portfolio company's thesis_connection.
**Result:** Actions thesis rate: 37.5% -> 68.8%.

### 5. Kilrr Funding Fix
**What:** Kilrr had round_2_raise ($1.1M) but no round_2_type, causing the funding derivation to return NULL.
**Action:** Manually set to "Seed ($1.1M)".

---

## Cross-Verification Results

### Portfolio <-> Companies DB Linkage
- All 142 portfolio companies have matching companies DB entries (0 orphans)
- All 142 have `portfolio_notion_ids` back-links in companies table
- All 142 enriched: 74 via M12-L50, 68 via research_enriched

### Exit Marking (Multiwoven, Obvious Finance, Dataflos)
| Company | Portfolio Status | Companies Status | Consistent? |
|---------|-----------------|-----------------|-------------|
| Multiwoven | Exited/Shutdown, Exited, Cat B SaaS | Acquired/Shut Down/Defunct | YES |
| Obvious Finance | Exited/Shutdown, Deadpool, Acquired | Acquired/Shut Down/Defunct | YES |
| Dataflos | Exited/Shutdown, Deadpool, Acqui-hired | Acquired/Shut Down/Defunct | YES |

### Entity Connections
- NOT empty (correcting prior checkpoint note)
- 23,732 total connections across 17 types
- Top types: vector_similar (10,719), sector_peer (3,103), current_employee (3,062), past_employee (2,898)
- All evidence is recent (within 30 days)

---

## Final Data Quality Dashboard

| Metric | Before | After | Delta |
|--------|--------|-------|-------|
| Actions link rate | 96.5% | 96.5% | -- |
| Actions thesis rate | 37.5% | 68.8% | +31.3pp |
| Portfolio thesis mapped | 40.8% (58) | 64.8% (92) | +24.0pp |
| Portfolio website coverage | 99.3% | 99.3% | -- |
| Portfolio funding coverage | 44.4% | 68.3% | +23.9pp |
| Exit marking consistency | 1/19 | 19/19 | Fixed |
| Network embedding coverage | 66.1% | 74.6% | +8.5pp (recovering) |
| Entity connections | 23,732 | 23,732 | Healthy |
| Companies embedding coverage | 98.4% | 98.4% | -- |
| Fully unlinked actions | 5 | 5 | Irreducible |

### Autonomous Quality Check Results
```
datum_data_quality_check() output:
  unlinked_actions       INFO     5     -      (3 dismissed, 2 operational)
  actions_thesis_rate    OK       144   68.8%
  portfolio_thesis_pct   WARNING  92    64.8%  (50 need new thesis threads)
  portfolio_website_pct  OK       141   99.3%
  portfolio_funding_pct  OK       97    68.3%
  exit_consistency       OK       0     -      (all exits properly marked)
  network_embedding_pct  WARNING  2631  74.6%  (recovering, was 60%)
  entity_connections     OK       23732 -
  stale_proposed         OK       11    -
  companies_embedding    OK       4506  98.4%
```

---

## Autonomous SQL Tools Created

### 1. `datum_data_quality_check()`
10-check health monitor. Returns check_name, check_status (OK/WARNING/CRITICAL), count_value, pct_value, details.
Checks: unlinked actions, thesis rates, website/funding coverage, exit consistency, embedding coverage, stale actions, entity connections.
**Usage:** `SELECT * FROM datum_data_quality_check();`

### 2. `datum_thesis_coverage()`
Thesis-to-portfolio gap analysis. Returns thesis name, portfolio count, action count, active vs exited breakdown.
**Usage:** `SELECT * FROM datum_thesis_coverage();`

---

## 5 Remaining Unlinked Actions (Irreducible)

| ID | Action | Type | Why Unlinked |
|----|--------|------|--------------|
| 13 | Flag dual-market expansion risk | Portfolio Check-in | No company reference, Dismissed |
| 35 | Night Wolf SKU quality issue | Portfolio Check-in | No company reference, Dismissed |
| 71 | Funding discrepancy ($7.28M) | Portfolio Check-in | No company reference, Dismissed |
| 136 | Ping Aakrit for LP chat | Meeting | Fund-level action, no company |
| 137 | Transfer INR to Madhav Tandon | Portfolio | Fund admin action, no company |

Actions 13/35/71 are dismissed thesis research with empty source_content. Actions 136/137 are fund-level operational items, not company-specific.

---

## Datum Agent Autonomous Loop Spec

The Datum agent should run these checks on every heartbeat:

1. **`datum_data_quality_check()`** — flag any WARNING/CRITICAL to the orchestrator
2. **`datum_thesis_coverage()`** — monitor thesis portfolio distribution
3. **Auto-enrich triggers:**
   - New portfolio entry -> derive funding from round data -> backfill companies.venture_funding
   - Portfolio exit status change -> update companies.pipeline_status
   - New action with company link -> backfill thesis_connection from portfolio
   - New thesis thread created -> re-scan portfolio for mappable companies
4. **Data consistency rules:**
   - portfolio.current_stage/today == companies.pipeline_status alignment
   - portfolio.company_name_id must resolve to a companies.notion_page_id
   - actions_queue.company_notion_id must resolve to a companies.notion_page_id

---

## Next Loop Priorities

1. **Portfolio thesis: 50 unmapped** — Need to determine if new thesis threads should be created (Financial Services, Consumer Brands, B2B Marketplaces) or if these are "thesis-agnostic" investments
2. **Network embeddings: 74.6%** — Still recovering. 897 people without embeddings. Monitor trend.
3. **Companies DB enrichment: 83.4% missing websites** — Only 759/4579 have websites. M12 enriched 74 portfolio cos but 4,437 pipeline/passed companies still lack basic data. Prioritize active pipeline companies.
4. **Portfolio funding: 45 still missing** — 97/142 have funding now, but 45 remain. Some are angel/concept stage without formal rounds.
5. **Action scoring: 28 missing relevance_score** — Should be computed by M5 scoring machine.
