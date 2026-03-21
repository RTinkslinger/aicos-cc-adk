# M9 Data Completeness Audit

**Date:** 2026-03-20
**Machine:** M9 Intel QA / M12 Data Enrichment
**Source:** Supabase `llfkxnsfczludgigknbs` (Mumbai)

---

## Overall Data Quality Score: 29/100

The system has strong structural foundations (schemas, sync, embeddings) but catastrophic gaps in enrichment data. The three core entity tables are hollowed out: synced from Notion with identifiers and status fields, but missing the descriptive, contact, and analytical data that agents need to reason about entities.

---

## 1. Companies Table (4,565 rows)

| Field | Count | % | Assessment |
|-------|------:|--:|------------|
| **total** | 4,565 | -- | -- |
| embedding | 3,761 | 82.4% | Good |
| sector | 2,875 | 63.0% | Moderate |
| deal_status | 4,565 | 100% | Complete (Notion sync) |
| pipeline_status | 4,565 | 100% | Complete (Notion sync) |
| enrichment_status | 4,565 | 100% | Complete (metadata) |
| thesis_thread_links | 4,565 | 100% | Complete (JSONB, may be empty `{}`) |
| content_connections | 4,565 | 100% | Complete (JSONB, may be empty `{}`) |
| signal_history | 4,565 | 100% | Complete (JSONB, may be empty `{}`) |
| type | 697 | 15.3% | Poor |
| venture_funding | 655 | 14.3% | Poor |
| page_content_path | 526 | 11.5% | Poor |
| founding_timeline | 386 | 8.5% | Very poor |
| website | 241 | 5.3% | Critical gap |
| research_file_path | 21 | 0.5% | Nearly empty |
| domain | 0 | 0.0% | Empty |
| computed_conviction_score | 0 | 0.0% | Empty |

### Companies Diagnosis

- **Structural fields** (deal_status, pipeline_status, enrichment_status) are 100% filled -- these come from Notion sync and are always present.
- **JSONB fields** (thesis_thread_links, content_connections, signal_history) show 100% but are likely initialized as empty `{}` objects -- not meaningful data.
- **Real enrichment data is nearly absent:** only 5.3% have a website, 0% have a domain extracted, 0% have conviction scores computed.
- **Embedding coverage at 82.4%** is the one bright spot -- but embeddings without descriptive content are low-value (embedding what? just the company name?).
- **88.5% of companies have no page content path** -- meaning no Notion page content has been synced to Postgres for most entities.

**Companies enrichment score: 18/100**

---

## 2. Network Table (3,722 rows)

| Field | Count | % | Assessment |
|-------|------:|--:|------------|
| **total** | 3,722 | -- | -- |
| embedding | 3,722 | 100% | Complete |
| enrichment_status | 3,722 | 100% | Complete (metadata) |
| signal_history | 3,722 | 100% | Complete (JSONB, likely empty) |
| meeting_context | 3,722 | 100% | Complete (JSONB, likely empty) |
| linkedin | 3,241 | 87.1% | Good |
| role_title (real, non-"postgres") | 3,218 | 86.5% | Good |
| current_company_ids | 3,205 | 86.1% | Good |
| ryg (Red/Yellow/Green) | 36 | 1.0% | Nearly empty |
| page_content_path | 30 | 0.8% | Nearly empty |
| e_e_priority | 10 | 0.3% | Nearly empty |
| email | 0 | 0.0% | Empty |
| phone | 0 | 0.0% | Empty |
| relationship_status | 0 | 0.0% | Empty |
| last_interaction | 0 | 0.0% | Empty |
| last_interaction_at | 0 | 0.0% | Empty |
| recent_interactions (30d) | 0 | 0.0% | Empty |

### Network Diagnosis

- **Identity fields are solid:** 100% embeddings, 87% LinkedIn URLs, 86% role titles, 86% company links. The Notion sync brought over the basics.
- **Contact data is completely absent:** 0 emails, 0 phone numbers across 3,722 people. This is the single biggest gap for Cindy (communications agent).
- **Relationship intelligence is zero:** 0 RYG scores (beyond 36), 0 relationship statuses, 0 interaction tracking. The system cannot answer "when did I last talk to X?" or "who is going cold?"
- **Page content nearly absent:** only 30/3,722 (0.8%) have Notion page content synced.

**Network enrichment score: 28/100**

---

## 3. Portfolio Table (142 rows)

| Field | Count | % | Assessment |
|-------|------:|--:|------------|
| **total** | 142 | -- | -- |
| embedding | 142 | 100% | Complete |
| page_content_path | 142 | 100% | Complete |
| research_file_path | 142 | 100% | Complete |
| signal_history | 142 | 100% | Complete |
| entry_cheque | 141 | 99.3% | Complete |
| health | 141 | 99.3% | Complete |
| ownership_pct | 141 | 99.3% | Complete |
| entry_round_valuation | 133 | 93.7% | Good |
| check_in_cadence | 131 | 92.3% | Good |
| stage_at_entry | 131 | 92.3% | Good |
| fmv_carried | 110 | 77.5% | Moderate |
| current_stage | 104 | 73.2% | Moderate |
| revenue_generating | 100 | 70.4% | Moderate |
| scale_of_business | 81 | 57.0% | Moderate |
| follow_on_decision | 19 | 13.4% | Poor |
| likely_outcome | 3 | 2.1% | Nearly empty |

### Portfolio Diagnosis

- **By far the healthiest table.** Core investment data (entry cheque, health, ownership, valuation) is 93-100% filled.
- **Operational fields** (cadence, stage_at_entry, research) are 92-100% -- these are actively managed in Notion.
- **Forward-looking fields are weak:** follow_on_decision at 13.4%, likely_outcome at 2.1%. These are the fields Megamind needs for strategic reasoning.
- **FMV at 77.5%** means ~32 portfolio companies have no current fair market value tracked.

**Portfolio enrichment score: 72/100**

---

## 4. Cross-Entity & Intelligence Tables

| Table | Row Count | Assessment |
|-------|----------:|------------|
| entity_connections | 1,298 | Has data |
| cir_propagation_log | 86 | Has data |
| cir_state | 14 | Has data |
| cascade_events | 2 | Minimal |
| strategic_assessments | 1 | Nearly empty |
| depth_grades | 1 | Nearly empty |
| interactions | 0 | Empty |
| obligations | 0 | Empty |

### Cross-Entity Diagnosis

- **entity_connections (1,298 rows):** This is the relationship graph. With 4,565 companies + 3,722 people + 142 portfolio = 8,429 entities, 1,298 connections means an average of 0.15 connections per entity. Extremely sparse.
- **interactions (0 rows):** No interaction history recorded at all. This is the foundation for relationship intelligence, recency scoring, and obligation tracking. Without it, the system is blind to communication patterns.
- **obligations (0 rows):** Cindy's I-owe/they-owe tracking has no data. The schema exists but has never been populated.
- **depth_grades (1 row):** IRGI depth grading has been tested on exactly 1 entity.
- **strategic_assessments (1 row):** Megamind has produced exactly 1 assessment.
- **CIR infrastructure (14 state + 86 propagation):** The Continuous Intelligence Refresh pipeline has some operational data, suggesting it has run but is early-stage.

**Cross-entity score: 8/100**

---

## 5. Scoring Methodology

| Category | Weight | Score | Weighted |
|----------|-------:|------:|---------:|
| Companies enrichment | 30% | 18 | 5.4 |
| Network enrichment | 30% | 28 | 8.4 |
| Portfolio enrichment | 20% | 72 | 14.4 |
| Cross-entity intelligence | 20% | 8 | 1.6 |
| **Total** | **100%** | -- | **29.8** |

**Rounded: 29/100**

### Score Rationale

- Companies and Network together represent 60% of the weight because they are the largest tables and feed every downstream machine (scoring, IRGI, Megamind, Cindy).
- Portfolio gets 20% -- it is the highest-value data but smallest in volume, and already well-maintained.
- Cross-entity tables get 20% -- they represent the intelligence layer that transforms raw entities into actionable insights.

---

## 6. Critical Gaps (Priority Order)

### P0 -- Blocking Multiple Machines

1. **Zero contact data in Network** (0 emails, 0 phones) -- blocks Cindy entirely, degrades all meeting prep and outreach actions.
2. **Zero interactions recorded** -- blocks obligation tracking (M11), relationship scoring (M5), recency-based action scoring, and CIR relationship triggers.
3. **Companies missing website/domain** (5.3% / 0%) -- blocks web enrichment, company research, and automated data gathering.

### P1 -- Degrading Intelligence Quality

4. **entity_connections sparse** (0.15 per entity) -- the relationship graph is too thin for graph-based reasoning, signal propagation, or "who knows who" queries.
5. **No conviction scores computed** (0/4,565 companies) -- scoring model has no output stored.
6. **Network RYG/priority nearly empty** (1% / 0.3%) -- relationship health is untracked for 99% of people.
7. **Portfolio follow_on_decision** (13.4%) and **likely_outcome** (2.1%) -- Megamind cannot do portfolio strategy without forward-looking assessments.

### P2 -- Improvement Opportunities

8. **Companies page_content_path** (11.5%) -- most companies have no synced Notion content in Postgres, limiting semantic search quality.
9. **Network page_content_path** (0.8%) -- same issue, even worse for people.
10. **Companies founding_timeline** (8.5%) and **type** (15.3%) -- basic classification data is largely absent.

---

## 7. Recommendations for M12 Data Enrichment

M12 is the permanent machinery that should fix these gaps. Priority loops:

1. **Contact Harvesting Loop** -- Extract emails from LinkedIn profiles, Notion pages, meeting notes, and email history. Target: 50%+ of Network with email within 2 sprints.
2. **Company Web Enrichment Loop** -- For all 4,565 companies, resolve website URLs, extract domains, pull founding year and description. Use web_scrape/web_search tools.
3. **Interaction Backfill Loop** -- Parse Granola meeting transcripts, email threads, and calendar events to populate the interactions table retroactively.
4. **Entity Connection Builder** -- Cross-reference company-person, person-person, and company-portfolio relationships from existing array fields (current_company_ids, network_ids, etc.) to populate entity_connections.
5. **Conviction Score Computation** -- Run the scoring model across all companies with sufficient data to populate computed_conviction_score.

---

*Audit generated by M9 Intel QA. Next audit recommended after M12 enrichment sprint completes.*
