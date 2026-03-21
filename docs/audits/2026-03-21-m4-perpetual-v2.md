# M4 Datum Machine - Perpetual Loop v2 Audit
**Date:** 2026-03-21
**Loop:** v2 (continuing from v1 company_notion_id fix + enrichment)

---

## Summary of Actions Taken

### 1. Unlinked Actions: 46 -> 30 (16 resolved)
- **12 linked to existing companies** (Cultured Computers x4, Avii x3, DubDub x2, MSC Fund x2, Lockstep x1) using `pg:ID` format since these companies lack Notion page IDs
- **4 new companies created** in companies DB: WeldT (5342), Sierra AI (5343), Poetic (5344), E2B (5345) -- actions 30, 39, 95, 108 linked
- **Remaining 30 unlinked:** 23 are Research/Thesis type (legitimately no single company), 7 are operational/generic

### 2. Portfolio Exit Status Corrections
- **Obvious Finance:** `pstatus` corrected from "Find Home / Wind Down" to "Acquired / Shut Down" (PhonePe acquisition). `outcome_category` set to "Acquired"
- **Dataflos:** `outcome_category` set to "Acqui-hired" (team joined Lirik)

### 3. M12 Signal Propagation
M12 enriched research files (research_injected=true) but signal_history was empty for all 3 flagged companies. Fixed:
- **Insta Astro:** signal_history now contains "Potential exit opportunity" (upside)
- **cocreate:** signal_history now contains "Breakout trajectory" (upside)
- **Terra:** signal_history now contains "Declining trajectory" (risk)

### 4. Entity Connections: 5 Missing Link Types Built
Previously **zero** connections existed for these critical cross-entity relationships:
| Connection Type | Count Created | Description |
|-----------------|---------------|-------------|
| action_references | 114 | Actions -> Companies they reference |
| led_by | 261 | Portfolio companies -> Network (deal leads) |
| sourced_by | 77 | Portfolio companies -> Network (sourcing attribution) |
| participant | 20 | Interactions -> Network (people involved) |
| discussed_in | +10 (added to existing) | Interactions -> Companies |
| **Total new** | **472** | |

Entity connections went from 23,250 to 23,732.

### 5. Thesis Connection Mapping
Portfolio thesis_connection coverage improved 31.7% -> 40.8% via sector-tag matching:
- Cyber & Security companies -> "Cybersecurity / Pen Testing"
- Healthcare companies -> "Healthcare AI Agents as Infrastructure"
- Aerospace companies -> "USTOL / Aviation / Deep Tech Mobility"
- AI Infrastructure/SDLC companies -> "Agentic AI Infrastructure"

---

## Comprehensive Data Quality Dashboard

### Portfolio DB (142 rows)
| Field | Coverage | Status |
|-------|----------|--------|
| health | 99.3% | GOOD |
| today | 100.0% | COMPLETE |
| outcome_category | 69.7% | NEEDS WORK (43 missing, mostly Funnel) |
| thesis_connection | 40.8% | IMPROVED (was 31.7%) |
| embedding | 100.0% | COMPLETE |
| enriched | 84.5% | GOOD (was 63.4%, M12 enrichment active) |

### Companies DB (4,579 rows)
| Field | Coverage | Status |
|-------|----------|--------|
| name | 100.0% | COMPLETE |
| sector | 100.0% | COMPLETE |
| deal_status | 99.9% | GOOD |
| embedding | 98.6% | GOOD (66 missing, includes 4 just created) |
| website | 16.6% | CRITICAL GAP (3,816 missing) |
| venture_funding | 14.3% | CRITICAL GAP |
| last_round_amount | 7.7% | CRITICAL GAP |

### Network DB (3,528 rows)
| Field | Coverage | Status |
|-------|----------|--------|
| person_name | 99.97% | COMPLETE |
| role_title | 95.4% | GOOD (162 missing) |
| linkedin | 87.6% | GOOD |
| current_company_ids | 87.0% | GOOD |
| embedding | 61.8% | RECOVERING (was 40.5%, now 1,881/3,528) |
| location | 72.0% | FAIR |
| ryg | 1.0% | CRITICAL GAP (only 35 tagged) |

### Actions Queue (144 rows)
| Field | Coverage | Status |
|-------|----------|--------|
| company_link | 78.5% | IMPROVED (was 68.1%) |
| embedding | 100.0% | COMPLETE |
| scored | 80.6% | GOOD |
| synced | 100.0% | COMPLETE |
| triaged | 100.0% | COMPLETE |

### Entity Connections (23,732 rows, 17 types)
| Connection Type | Count | Source Coverage |
|-----------------|-------|----------------|
| vector_similar | 10,719 | Only 11+10 unique sources (LIMITED) |
| sector_peer | 3,103 | 569 unique sources |
| current_employee | 3,062 | 3,031 unique people |
| past_employee | 2,898 | 1,765 unique people |
| thesis_relevance | 1,502 | 112 unique sources |
| inferred_via_company | 1,479 | 660 unique people |
| portfolio_investment | 142 | All 142 portfolio companies |
| led_by | 261 | **NEW** |
| action_references | 114 | **NEW** |
| sourced_by | 77 | **NEW** |
| participant | 20 | **NEW** |

### Sync Status
- **Last sync:** 2026-03-17 08:03 UTC (99 hours ago)
- **Status:** STALE -- Sync Agent disabled since v2.2 architecture redesign
- **Impact:** Notion and Postgres are diverging. Changes in either direction not propagating.

---

## Critical Gaps (Ordered by Impact)

### P0 - Blocking
1. **Sync Agent offline (99+ hours)** -- No Notion <-> Postgres sync since Mar 17. Any changes in Notion are invisible to agents. Any changes in Postgres are invisible in Notion.
2. **Network embeddings 38.2% missing** (1,647 rows) -- Recovery stalled at 08:46 UTC. These people can't participate in semantic search or vector_similar connections.

### P1 - High Impact
3. **Companies DB 83.4% missing websites** (3,816 rows) -- Blocks web enrichment, company research, competitive analysis
4. **Companies DB 85.7% missing funding data** -- Blocks investment analysis, valuation comparisons
5. **Portfolio thesis_connection 59.2% missing** -- 84 companies without thesis mapping limits strategic analysis
6. **5 companies without Notion pages** (Cultured Computers, Avii, DubDub, Lockstep, MSC Fund) -- Created locally, need Notion page creation for full sync
7. **vector_similar connections only seeded for ~20 entities** -- Should cover all 4,579 companies and 3,528 network entries

### P2 - Medium
8. **Network RYG 99% empty** -- No relationship health scoring for network contacts
9. **Portfolio outcome_category 30.3% missing** -- 43 companies without outcome classification
10. **Portfolio signal_history mostly empty** -- Only 3 entries populated (the ones we just fixed)

---

## What Datum Agent Should Handle Autonomously

These are the patterns from this session that should become Datum agent logic:

1. **Action -> Company resolution:** When an action references a company name in its text but has no company_notion_id, attempt fuzzy matching against companies.name. Use min length 5 chars to avoid false positives.
2. **Entity connection maintenance:** On any DB write, check if entity_connections should be updated (new action -> company link, new interaction -> people link, etc.)
3. **Signal propagation:** When M12 enriches portfolio companies, automatically write corresponding signal_history entries from the enrichment_metadata.
4. **Thesis mapping:** Use sector_tags + entity_connections thesis_relevance to auto-suggest thesis_connection for portfolio companies.
5. **Exit status monitoring:** When pstatus changes to "Acquired / Shut Down" or "Find Home / Wind Down", ensure outcome_category is populated.
6. **Embedding recovery:** Monitor for rows with null embeddings and trigger re-embedding.
7. **Sync staleness alerting:** When sync_metadata shows > 24h staleness, flag for intervention.
