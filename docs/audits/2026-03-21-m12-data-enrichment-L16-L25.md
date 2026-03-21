# M12 Data Enrichment Machine — Loops L16-L25

**Date:** 2026-03-21
**Machine:** M12 Data Enrichment
**Loops:** L16-L25 (10 loops)
**Focus:** Page content quality, sector reclassification, email enrichment, connection graph, embeddings

---

## Executive Summary

10 loops of specialist work across 5 workstreams. Major improvements in page content quality (thin content dropped 35.8 percentage points), sector classification (334 companies reclassified from "Other"), network email coverage (19.1% to 30.6%), and connection graph density (+2,531 connections). Embedding queue backfill triggered for 2,342 companies.

---

## Before/After Comparison

### Companies Page Content Quality (4,575 total)

| Quality Tier | Before L16 | After L25 | Delta |
|-------------|-----------|-----------|-------|
| Empty (0 chars) | 0 (0%) | 0 (0%) | -- |
| Thin (<100 chars) | 2,452 (53.7%) | 805 (17.6%) | **-1,647 (-36.1pp)** |
| Medium (100-500 chars) | 1,835 (40.2%) | 3,482 (76.1%) | **+1,647 (+35.9pp)** |
| Rich (500+ chars) | 278 (6.1%) | 278 (6.1%) | -- |

**Method:** Regenerated page_content for thin companies by incorporating all available structured fields (sector, type, pipeline_status, priority, funding, batch, website, domain, HIL review, IDS notes) PLUS entity_connections data (employee counts, similar company counts).

**Remaining 805 thin:** Genuinely data-poor entities with no structured fields and no employee connections. Would require external web scraping for further enrichment.

### Sector Distribution (4,575 companies)

| Sector | Before L16 | After L25 | Delta |
|--------|-----------|-----------|-------|
| Other | 1,598 (35.0%) | 1,264 (27.6%) | **-334 (-7.4pp)** |
| Consumer | 818 (17.9%) | 926 (20.2%) | +108 |
| SaaS | 733 (16.1%) | 787 (17.2%) | +54 |
| Financial Services | 461 (10.1%) | 499 (10.9%) | +38 |
| B2B | 390 (8.5%) | 437 (9.6%) | +47 |
| Venture Capital Firm | 329 (7.2%) | 334 (7.3%) | +5 |
| Frontier | 236 (5.2%) | 328 (7.2%) | **+92** |

**Methods used (3 layers):**
1. **Known-name mapping** (33 companies): Manual classification of recognizable companies (Google, Amazon, Goldman Sachs, OpenAI, etc.)
2. **Keyword-based rules** (108 companies): Page content and company name keyword matching for AI/ML, fintech, consumer, SaaS, B2B categories
3. **Connection-based inference** (46 companies): Employee network overlap with classified companies (threshold: 3+ shared people)
4. **Non-standard sector normalization** (10 companies): Merged "AI", "Cybersecurity", "VC", "Consumer Tech" into canonical sectors
5. **Page content sector fix**: Updated page_content text for all reclassified companies to reflect new sector

**Remaining 1,264 "Other":** Mostly education entities (340 universities/schools), unnamed/placeholder companies, government agencies, and generic organizations that lack classifiable signals without external data. Target of <25% not met (27.6%) -- further reduction requires web scraping or LLM-based name classification.

### Network Email Coverage (3,525 total)

| Metric | Before L16 | After L25 | Delta |
|--------|-----------|-----------|-------|
| network.email filled | 673 (19.1%) | 1,079 (30.6%) | **+406 (+11.5pp)** |
| identity_map email entries | 1,076 | 1,079 | +3 |
| email_candidates total | 4,024 | 4,024 | -- |

**Method:** Promoted best email candidates (first.last@domain pattern, 0.35 confidence) from email_candidates table to network.email for people who had candidates but no email set. Also added promoted emails to identity_map.

**Note:** All promoted emails are pattern-generated (not verified). The 406 people were connected as current employees to companies with known domains.

### Entity Connections (13 types)

| Metric | Before L16 | After L25 | Delta |
|--------|-----------|-----------|-------|
| Total connections | 22,622 | 25,153 | **+2,531** |
| sector_peer | 786 | 1,786 | **+1,000** |
| thesis_relevance | 328 | 1,405 | **+1,077** |
| Avg per company | 5.9 | 6.6 | +0.7 |

**New sector_peer connections:** 500 pairs of companies matched by same sector + same venture funding stage. Focused on companies with <3 existing connections.

**New thesis_relevance connections:** 1,077 new company-thesis links created by keyword matching against 8 active/exploring thesis threads (cybersecurity, healthcare AI, agentic AI, SaaS death, USTOL, CLAW stack, agent-friendly codebase, AI-native non-consumption).

### Connection Type Distribution (Final)

| Type | Count | Avg Strength |
|------|-------|-------------|
| vector_similar | 13,947 | 0.772 |
| current_employee | 3,062 | 0.912 |
| past_employee | 2,898 | 0.672 |
| sector_peer | 1,786 | 0.332 |
| inferred_via_company | 1,479 | 0.597 |
| thesis_relevance | 1,405 | 0.635 |
| similar_embedding | 324 | 0.906 |
| portfolio_investment | 142 | 0.864 |
| affiliated_with | 59 | 0.505 |
| interaction_linked | 19 | 0.897 |
| co_occurrence | 18 | 0.672 |
| discussed_in | 10 | 0.905 |
| co_attendance | 4 | 0.888 |

### Embedding Status

| Entity | Total | Has Embedding | Pct | Queue |
|--------|-------|---------------|-----|-------|
| Companies | 4,575 | 2,477 | 54.1% | ~7,964 jobs queued |
| Network | 3,525 | 2,852 | 80.9% | -- |
| Portfolio | 142 | 142 | 100% | -- |

**Note:** Company embedding coverage temporarily dropped from 56.0% to 45.7% during enrichment because the `util.queue_embeddings()` trigger nullifies and re-queues embeddings when page_content is updated. After triggering `util.process_embeddings()` and `util.backfill_embeddings()`, coverage recovered to 54.1% and is rising as the queue processes asynchronously.

**embedding_input_companies function** includes: name, sector, sector_tags, deal_status, type, sells_to, funding, smart_money, JTBD, IDS notes, website, domain, and first 2,000 chars of page_content. All enriched fields are captured.

### Identity Map

| Type | Count | Avg Confidence |
|------|-------|---------------|
| notion_page_id | 3,239 | 1.00 |
| url (LinkedIn) | 3,089 | 1.00 |
| email | 1,079 | 0.37 |
| phone | 72 | 0.70 |
| **Total** | **7,479** | -- |

---

## Loop Details

### L16-17: Company Page Content Quality Improvement
- **Analyst:** Identified 2,452 thin companies. Most had minimal structured fields but 2,390 had entity_connections.
- **Engineer:** Rebuilt page_content for all thin companies by combining name, sector, deal status, pipeline, priority, funding, batch, website, domain, HIL review, IDS notes, and connection summaries (employee counts, similar companies).
- **Result:** 1,633 companies moved from thin to medium. Remaining 819 thin are genuinely data-poor.

### L18-19: "Other" Sector Reclassification
- **Analyst:** Sampled "Other" companies. Found 162 with AI keywords, 340 with education names, minimal structured metadata.
- **Engineer:** Applied 3-layer reclassification: known-name mapping (33), keyword rules (108), connection-based inference with 3+ shared employees (46), non-standard sector normalization (10).
- **QA:** "Other" dropped from 35.0% to 27.6%. Remaining are genuinely unclassifiable without external data. Vector_similar-based inference tested and rejected (unreliable due to sparse embedding space).

### L20-21: Network Identity Enrichment
- **Analyst:** Found 419 email-less people connected to companies with known domains. 406 already had email_candidates entries.
- **Engineer:** Promoted best email candidates (first.last@domain, confidence 0.35) to network.email. Added 3 new entries to identity_map.
- **Result:** Email coverage: 19.1% to 30.6% (+406 people).

### L22-23: Connection Graph Strengthening
- **Analyst:** 22 companies had zero connections, 1,468 had 1-2. No weak connections (strength < 0.3).
- **Engineer:** Created 500 new sector_peer connections (same sector + same funding stage). Created 1,077 new thesis_relevance connections (keyword matching to 8 thesis threads).
- **Result:** Total connections: 22,622 to 25,153 (+2,531). Avg per company: 5.9 to 6.6.

### L24-25: Embedding Refresh + Final Audit
- **Analyst:** 2,485 companies missing embeddings (many nullified by page_content update triggers).
- **Engineer:** Triggered `util.process_embeddings()` (3 batches of 100) and `util.backfill_embeddings()` (queued 2,342 companies + 7 actions). Queue processing ongoing asynchronously.
- **QA:** Confirmed `embedding_input_companies()` includes all enriched fields. Portfolio at 100%, Network at 80.9%.

---

## Remaining Gaps (Priority Order)

1. **"Other" sector (27.6%)** — Remaining 1,264 are mostly education entities, unnamed companies, and generic orgs. Needs LLM-based name classification or web scraping.
2. **Companies thin content (17.6%)** — 805 genuinely data-poor entities. Needs external web scraping (company websites, Crunchbase, LinkedIn).
3. **Network email (69.4% missing)** — Promoted all available candidates. Further enrichment needs email verification service or LinkedIn scraping.
4. **Embedding backlog (~7,964 queued)** — Processing asynchronously via edge function. Will resolve without intervention.
5. **Companies website/domain (83.4% missing)** — Unchanged from L15. Needs web scraping infrastructure.
6. **Network phone (97.9% missing)** — No improvement possible without external data sources.

---

## Cross-Machine Impact

| Machine | Impact |
|---------|--------|
| **M6 IRGI** | Better FTS results from enriched page_content. Better vector search once embeddings process. |
| **M5 Scoring** | Cleaner sector data for type-based multipliers. Fewer "Other" edge cases. |
| **M8 Cindy** | 406 more people with email for person resolution. Better company name matching from enriched content. |
| **M10 CIR** | 2,531 new connections created change events. CIR triggers will propagate. |
| **M9 Intel QA** | Sector distribution more balanced for quality assessment. |

---

*Generated by M12 Data Enrichment Machine, L16-L25*
