# M4 Datum Audit — Loop 1 Comprehensive Data Quality Report

**Date:** 2026-03-21
**Agent:** M4 Datum (Loop 1)
**Supabase Project:** `llfkxnsfczludgigknbs`

---

## Executive Summary

Datum has been neglected. This audit reveals a system with strong structural foundations but massive data quality gaps that undermine every downstream machine. The headline numbers:

- **Portfolio DB:** 142 companies. key_questions at 19.7% (28/142), high_impact at 23.2% (33/142) — M12's claimed counts are CORRECT, M9 was citing stale data
- **Companies DB:** 4,575 entries. Only 0.6% (27) have substantial page_content (>500 chars). 65.4% are template stubs (<200 chars). Embedding 100% but built on garbage data
- **Network DB:** 3,528 people. Embedding coverage CRASHED to 21.1% (746/3528) — up from the reported 10.5% crash but still catastrophic. Email at 30.6%, phone at 2.0%
- **Entity Connections:** 26,573 links across 20 types. NOT empty (previous report was wrong). But quality varies wildly
- **Cross-DB Linkages:** Portfolio-to-Companies 99.3% linked. Actions company_notion_id is 0% (0/144). Interaction person resolution 32.8% (20/61 participants)

**Overall Data Health Grade: D+** — Structural plumbing works, but the data flowing through it is thin, templated, and incomplete.

---

## 1. Portfolio DB (142 companies)

### Field Population Matrix

| Field | Filled | Total | % | Assessment |
|-------|--------|-------|---|------------|
| portfolio_co (name) | 142 | 142 | 100% | Complete |
| health | 141 | 142 | 99.3% | Near-complete |
| entry_cheque | 141 | 142 | 99.3% | Near-complete |
| ownership_pct | 141 | 142 | 99.3% | Near-complete |
| research_file_path | 142 | 142 | 100% | All have paths |
| page_content | 142 | 142 | 100% | All have content (quality varies) |
| page_content_path | 142 | 142 | 100% | All have paths |
| embedding | 142 | 142 | 100% | Full coverage |
| enrichment_metadata | 142 | 142 | 100% | Full coverage |
| signal_history | 142 | 142 | 100% | Full coverage |
| last_round_valuation | 134 | 142 | 94.4% | Good |
| entry_round_valuation | 133 | 142 | 93.7% | Good |
| check_in_cadence | 131 | 142 | 92.3% | Good |
| hc_priority | 113 | 142 | 79.6% | Acceptable |
| current_stage | 104 | 142 | 73.2% | Needs work |
| outcome_category | 97 | 142 | 68.3% | Gaps |
| scale_of_business | 81 | 142 | 57.0% | Major gap |
| thesis_connection | 45 | 142 | 31.7% | Weak |
| **high_impact** | **33** | **142** | **23.2%** | **CRITICAL GAP** |
| note_on_deployment | 31 | 142 | 21.8% | Critical gap |
| **key_questions** | **28** | **142** | **19.7%** | **CRITICAL GAP** |
| action_due_date | 9 | 142 | 6.3% | Near-empty |
| external_signal | 2 | 142 | 1.4% | Effectively empty |
| fumes_date | 1 | 142 | 0.7% | Effectively empty |

### M12 vs M9 Discrepancy — RESOLVED

M12 claimed key_questions=28 and high_impact=33. M9 said "still 14 and 21." **M12 is correct.** Current DB shows exactly 28 key_questions and 33 high_impact populated. M9 was reading stale cached data or querying before M12's enrichment run landed.

### key_questions Quality Check

Sampled 5 entries. Quality is HIGH where populated — these are genuine, actionable strategic questions:
- Terractive: "Have the founders been compounding on strategic thinking and process..."
- Apptile: "What is the MRR and growth rate? What is the conversion rate from Core to Pro tier?"
- Legend of Toys: "Revenue/margin disclosure: what are actual financials behind the $2.6B market opportunity?"

**The problem is coverage (28/142 = 19.7%), not quality.**

### high_impact Quality Check

Mixed quality. Some are rich ("AI-native Shopify app builder with 5.0/5 rating. 500+ brands globally. Strong founder DNA"), others are skeletal ("1. Brand guide session w/ MS done", "1. Follow-on fundraise"). Quality varies from one-liners to multi-sentence strategic context.

### Portfolio Status/Health Breakdown

| Health | Count | % |
|--------|-------|---|
| Green | 84 | 59.2% |
| Yellow | 33 | 23.2% |
| Red | 18 | 12.7% |
| NA | 6 | 4.2% |
| NULL | 1 | 0.7% |

**Exited/Deadpooled identification:** The `pstatus` field shows:
- "Acquired / Shut Down": 5 companies
- "Find Home / Wind Down": 11 companies (+ 2 with mixed statuses)
- Health=NA: 6 companies (likely exited)
- **Total inactive/exited: ~16-22 companies (11-15% of portfolio)**

### page_content Quality

| Range | Count | % | Assessment |
|-------|-------|---|------------|
| <200 chars | 29 | 20.4% | Template stubs (just name, sector, ownership) |
| 200-500 chars | 92 | 64.8% | Structured fields only, no narrative |
| >500 chars | 21 | 14.8% | Has executive summary, funding detail |
| >1000 chars | 28 | 19.7% | Rich content |
| >1500 chars | 11 | 7.7% | Full Notion detail import |

**Notion page detail contents (comments, notes) are NOT imported.** Zero entries contain "comment" keyword. Only 1 contains "notes." The page_content is synthesized structured data, not raw Notion page exports. 15 entries have an "EXECUTIVE SUMMARY" section from research enrichment.

### Research Files

All 142 `research_file_path` values point to `/portfolio-research/<slug>.md`. 253 files exist in the directory (extras are non-portfolio companies). Sampled 3:
- `terractive.md`: 94 lines, deep research report from Parallel Deep Research
- `apptile.md`: 94 lines, same quality
- `legend-of-toys.md`: 102 lines, same quality

**All research files are readable and substantial.**

---

## 2. Companies DB (4,575 entries)

### Field Population Matrix

| Field | Filled | Total | % | Assessment |
|-------|--------|-------|---|------------|
| name | 4,575 | 4,575 | 100% | Complete |
| notion_page_id | 4,565 | 4,575 | 99.8% | 10 missing |
| sector | 4,575 | 4,575 | 100% | All classified |
| deal_status | 4,572 | 4,575 | 99.9% | Near-complete |
| pipeline_status | 4,572 | 4,575 | 99.9% | Near-complete |
| embedding | 4,575 | 4,575 | 100% | Full (but based on thin data) |
| enrichment_metadata | 4,575 | 4,575 | 100% | Full |
| enrichment_source | 4,395 | 4,575 | 96.1% | Good |
| page_content | 4,575 | 4,575 | 100% | All have SOMETHING |
| priority | 1,309 | 4,575 | 28.6% | Sparse |
| sector_tags | 1,541 | 4,575 | 33.7% | One-third |
| sells_to | 798 | 4,575 | 17.4% | Sparse |
| website | 759 | 4,575 | 16.6% | Sparse |
| domain | 757 | 4,575 | 16.5% | Sparse |
| type | 707 | 4,575 | 15.5% | Sparse |
| venture_funding | 655 | 4,575 | 14.3% | Sparse |
| hil_review | 544 | 4,575 | 11.9% | Very sparse |
| page_content_path | 526 | 4,575 | 11.5% | Very sparse |
| founding_timeline | 386 | 4,575 | 8.4% | Near-empty |
| smart_money | 28 | 4,575 | 0.6% | Effectively empty |
| money_committed | 22 | 4,575 | 0.5% | Effectively empty |
| research_file_path | 21 | 4,575 | 0.5% | Effectively empty |
| datum_source | 10 | 4,575 | 0.2% | Effectively empty |
| computed_conviction_score | 0 | 4,575 | 0.0% | EMPTY |

### page_content Quality — THE CRITICAL PROBLEM

| Range | Count | % | Assessment |
|-------|-------|---|------------|
| **<200 chars (template)** | **2,993** | **65.4%** | **Just name + sector + maybe alumni** |
| 200-500 chars (medium) | 1,555 | 34.0% | Some structure |
| **>500 chars (substantial)** | **27** | **0.6%** | **Tiny fraction with real data** |

Sample template content (typical <200 char entry):
```
Litifer
Sector: Consumer
```
That's 26 characters. This is not "data" — it's a placeholder.

Sample substantial content (>500 chars):
```
Highperformr AI (SaaS)
https://www.highperformr.ai/
Sells to: Mid Market, Enterprise
Tags: Marketing, AI, Social...
Founded: H2 2023
Funding: Large Seed | Last round: $3.5M | Smart money: Tier 1.5
--- Portfolio Intelligence ---
Portfolio company: Highperformr AI | Green | post product...
```

**65.4% of the Companies DB is template-grade data. Embeddings are built on this thin content, meaning vector search quality is fundamentally compromised for 2,993 companies.**

### Sector Distribution

| Sector | Count | % |
|--------|-------|---|
| Consumer | 1,083 | 23.7% |
| SaaS | 913 | 20.0% |
| Financial Services | 592 | 12.9% |
| B2B | 506 | 11.1% |
| **Other** | **420** | **9.2%** |
| Frontier | 372 | 8.1% |
| Venture Capital Firm | 351 | 7.7% |
| Education | 338 | 7.4% |

**420 companies (9.2%) still classified as "Other."** Not catastrophic but a meaningful unclassified bucket.

### Enrichment Status

| Status | Count | % |
|--------|-------|---|
| enriched_l26 | 3,315 | 72.5% | Base enrichment |
| enriched_l26_fields | 1,118 | 24.4% | Field-level enrichment |
| M12-L50-enriched | 133 | 2.9% | Latest M12 enrichment |
| research_enriched | 9 | 0.2% | Deep research |

Only 133 companies (2.9%) received the latest M12 enrichment pass. The vast majority are at the base level.

---

## 3. Network DB (3,528 people)

### Field Population Matrix

| Field | Filled | Total | % | Assessment |
|-------|--------|-------|---|------------|
| person_name | 3,527 | 3,528 | 99.97% | 1 missing name |
| page_content | 3,528 | 3,528 | 100% | All have SOMETHING |
| enrichment_status | 3,528 | 3,528 | 100% | All enriched |
| enrichment_source | 3,479 | 3,528 | 98.6% | Good |
| source | 3,525 | 3,528 | 99.9% | Good |
| role_title | 3,366 | 3,528 | 95.4% | Good |
| notion_page_id | 3,239 | 3,528 | 91.8% | 289 missing |
| linkedin | 3,089 | 3,528 | 87.6% | Good |
| email | 1,079 | 3,528 | 30.6% | Weak |
| **embedding** | **746** | **3,528** | **21.1%** | **CRITICAL — 78.9% missing** |
| page_content_path | 239 | 3,528 | 6.8% | Very sparse |
| phone | 72 | 3,528 | 2.0% | Near-empty |
| ryg | 36 | 3,528 | 1.0% | Near-empty |
| last_interaction_at | 29 | 3,528 | 0.8% | Near-empty |
| relationship_status | 0 | 3,528 | 0.0% | EMPTY |
| datum_source | 0 | 3,528 | 0.0% | EMPTY |
| has_recent_interactions | 0 | 3,528 | 0.0% | EMPTY |

### Embedding Crisis

Embedding coverage is at **21.1%** (746/3,528). This was previously reported as crashing to 10.5% — it has partially recovered but is still far from functional.

Breakdown by enrichment status:
| Enrichment Status | Total | Has Embedding | % |
|-------------------|-------|---------------|---|
| enriched_l40 | 2,747 | 707 | 25.7% |
| enriched_l41 | 459 | 3 | 0.7% |
| M12-L52-enriched | 322 | 36 | 11.2% |

**The l41 enrichment batch (459 people) has almost zero embeddings (0.7%).** The M12 batch is slightly better at 11.2% but still terrible. The l40 base batch has the best coverage at 25.7%.

### page_content Quality

| Range | Count | % |
|-------|-------|---|
| <50 chars | 118 | 3.3% |
| 50-100 chars | 213 | 6.0% |
| 100-200 chars | 1,228 | 34.8% |
| 200-300 chars | 1,713 | 48.6% |
| 300-500 chars | 251 | 7.1% |
| >500 chars | 5 | 0.1% |

Average: 204 chars. Max: 557 chars. **Only 5 people have substantial page_content.** The bulk (83.4%) is 100-300 chars of structured fields only.

### Company Links

| Metric | Count | % |
|--------|-------|---|
| Has current_company_ids | 3,069 | 87.0% |
| Has past_company_ids | 1,814 | 51.4% |
| No current company | 459 | 13.0% |
| Has meeting_notes | 0 | 0.0% |

**meeting_note_ids is completely empty for all 3,528 people.** No meeting notes are linked to network contacts.

### Role Title Quality

Roles are real and properly categorized (not corrupted):
- Co-Founder CEO: 1,079 (30.6%)
- Founder: 412 (11.7%)
- Co-founder: 330 (9.4%)
- Co-Founder CTO: 284 (8.0%)
- Co-Founder COO: 228 (6.5%)
- VC Partner: 166 (4.7%)
- NULL: 162 (4.6%)

Minor normalization issues: "Co-Founder CEO" vs "Founder & CEO" vs "Founder CEO" vs "Co-Founder & CEO" (4 variants of the same role). But not corrupt.

---

## 4. Cross-DB Linkages

### Portfolio <-> Companies

| Metric | Value |
|--------|-------|
| Portfolio companies linked via entity_connections | 142/142 (100%) |
| Portfolio names matched to companies DB by name | 141/142 (99.3%) |
| **Missing match** | **"Terra" (portfolio) has no name match in companies DB** |

One company ("Terra") has a portfolio entry but no matching companies DB entry. Likely a naming inconsistency (portfolio calls it "Terra", companies DB may use "Terra.do" or full legal name).

### Network <-> Companies

Entity connections show:
- `current_employee` links: 3,062
- `past_employee` links: 2,898
- `affiliated_with` links: 59
- `interaction_linked` (network-company): 19

**87.0% of network people have current_company_ids populated** (from Notion relations). Entity_connections table adds computed linkages on top.

### Actions <-> Companies

| Metric | Value | Assessment |
|--------|-------|------------|
| **company_notion_id** | **0/144 (0%)** | **COMPLETELY EMPTY** |
| source_digest_notion_id | 0/144 (0%) | COMPLETELY EMPTY |
| thesis_connection | 54/144 (37.5%) | Partial |

**This confirms M7's flag: company_notion_id is 0% on all 144 actions.** No action is linked to a company. This means you cannot ask "what actions relate to company X?" — the linkage simply doesn't exist.

### Interactions <-> Network

| Metric | Value | Assessment |
|--------|-------|------------|
| Total participants across 23 interactions | 61 | |
| Total linked_people | 20 | 32.8% resolution rate |
| Interactions with no linked people | 7/23 (30.4%) | |
| Interactions with no linked companies | 5/23 (21.7%) | |

**Person resolution rate: 32.8%** (20 of 61 participants resolved to network IDs). 7 interactions have zero people linked. This means 2/3 of interaction participants are unresolved.

### Obligations <-> Network

| Metric | Value | Assessment |
|--------|-------|------------|
| Obligations total | 14 | |
| person_id populated | 14/14 (100%) | Perfect |
| person_id valid (found in network) | 14/14 (100%) | All resolve |
| linked_action_id | 13/14 (92.9%) | Near-complete |
| megamind_priority | 0/14 (0%) | Never set |

Obligations have excellent person linkage. But megamind_priority is never set — blended_priority falls back to cindy_priority alone.

### Entity Connections Summary

| Connection Type | Source | Target | Count |
|----------------|--------|--------|-------|
| vector_similar | company | company | 6,867 |
| sector_peer | company | company | 3,108 |
| vector_similar | network | company | 3,079 |
| current_employee | network | company | 3,062 |
| past_employee | network | company | 2,898 |
| vector_similar | company | thesis | 2,000 |
| vector_similar | network | network | 1,998 |
| inferred_via_company | network | thesis | 1,479 |
| thesis_relevance | thesis | company | 1,077 |
| similar_embedding | company | company | 291 |
| thesis_relevance | portfolio | thesis | 287 |
| portfolio_investment | portfolio | company | 142 |
| thesis_relevance | action | thesis | 138 |
| affiliated_with | network | company | 59 |
| similar_embedding | network | network | 33 |
| interaction_linked | network | company | 19 |
| co_occurrence | thesis | thesis | 18 |
| discussed_in | interaction | company | 10 |
| co_attendance | network | network | 5 |
| vector_similar | network | thesis | 3 |

**Total:** 26,573 connections across 3,756 unique sources and 4,709 unique targets.
**Network people with ZERO connections:** Only 2 (out of 3,528).
**Previous claim that entity_connections is EMPTY was incorrect.** It has 26,573 records.

---

## 5. Notion Detail Pages

### page_content_path Coverage

| Table | Has Path | Total | % |
|-------|----------|-------|---|
| Portfolio | 142 | 142 | 100% |
| Companies | 526 | 4,575 | 11.5% |
| Network | 239 | 3,528 | 6.8% |

### Are These Real Notion Exports?

**No.** Based on content analysis:

- **Portfolio page_content:** Synthesized structured data (ownership, health, cadence, stage) generated by enrichment processes. NOT raw Notion page exports. No comments, no embedded blocks, no user-authored notes. The longest entries (~1700 chars) have "EXECUTIVE SUMMARY" sections from research enrichment.

- **Companies page_content:** Similarly synthesized. Template entries are just "Name\nSector: X". Substantial entries add funding, key people, portfolio intelligence. No Notion comments or page body text.

- **Network page_content:** Synthesized profiles. Name, role, location, email, current/past companies, portfolio intelligence blurbs. Not raw Notion exports.

**The page_content_path files** (e.g., `network-pages/chetan-reddy.md`) point to markdown files but these also appear to be enrichment-generated rather than Notion API page exports. They match the page_content field content.

**Conclusion: No Notion detail page content (comments, user notes, embedded blocks) has been imported into Postgres.** Everything in page_content is agent-synthesized from structured fields.

---

## 6. Identity Resolution Infrastructure

### Identity Map

| Metric | Value |
|--------|-------|
| Total identity entries | 11,004 |
| Distinct network people covered | 3,528 (100%) |
| Average identifiers per person | 3.1 |

| Identifier Type | Count | Coverage |
|----------------|-------|----------|
| name | 3,525 | 99.9% |
| notion_page_id | 3,239 | 91.8% |
| url (LinkedIn) | 3,089 | 87.6% |
| email | 1,079 | 30.6% |
| phone | 72 | 2.0% |

The identity_map table is well-populated and provides multi-surface resolution. Every network person has at least one identifier. The main gap is email (only 30.6%) and phone (2.0%).

---

## 7. Supporting Tables Status

| Table | Rows | Assessment |
|-------|------|------------|
| content_digests | 22 | 100% field coverage, healthy |
| thesis_threads | 8 | 100% core fields, key_question_summary at 37.5% |
| obligations | 14 | Good linkage, megamind_priority empty |
| interactions | 23 | 32.8% person resolution, good embedding |
| identity_map | 11,004 | Well-populated |
| entity_connections | 26,573 | Rich graph, 20 connection types |
| cir_state | Active | Latest update today |
| sync_metadata | Active | Last full sync 2026-03-20 |

---

## 8. Sync Health

| Table | Last Synced | Last Updated | Gap |
|-------|-------------|--------------|-----|
| portfolio | 2026-03-20 09:49 | 2026-03-21 10:25 | ~24h |
| companies | 2026-03-20 10:29 | 2026-03-21 09:44 | ~23h |
| network | 2026-03-20 10:35 | 2026-03-21 08:46 | ~22h |
| actions_queue | 2026-03-19 04:40 | 2026-03-21 10:24 | **~54h** |
| thesis_threads | 2026-03-19 04:50 | 2026-03-21 07:16 | **~50h** |

Actions and thesis have not synced from Notion in over 2 days. Portfolio/companies/network last synced yesterday.

---

## 9. Critical Findings — Priority Ordered

### P0 — System-Breaking Issues

1. **Network embeddings at 21.1%** — Vector search, similarity matching, and all semantic operations fail for 78.9% of network contacts. The l41 batch (459 people) has 0.7% embedding coverage.

2. **Actions company_notion_id at 0%** — No action is linked to a company. This breaks all company-contextualized action queries. M7 was right.

3. **Companies page_content 65.4% template** — 2,993 of 4,575 companies have content under 200 characters. Embeddings built on "Litifer\nSector: Consumer" provide zero semantic value.

### P1 — High Impact Gaps

4. **Portfolio key_questions at 19.7%** — Only 28 of 142 portfolio companies have key questions populated. Quality is high where populated but 114 companies have zero strategic questions tracked.

5. **Portfolio high_impact at 23.2%** — Only 33 of 142. The scoring model relies on this field.

6. **Interaction person resolution at 32.8%** — Two-thirds of meeting participants are not resolved to network contacts.

7. **No Notion page body content imported** — Comments, user notes, embedded blocks from Notion are not in Postgres. All page_content is agent-synthesized.

8. **Actions/thesis sync stale (50+ hours)** — Notion-to-Postgres sync for actions and thesis has been stale for over 2 days.

### P2 — Important Gaps

9. **Network meeting_note_ids at 0%** — No meeting notes linked to any network contact.

10. **Companies "Other" sector at 9.2%** — 420 companies unclassified.

11. **Portfolio external_signal at 1.4%** — The external signal enrichment pipeline is not running.

12. **Megamind_priority on obligations at 0%** — Blended scoring degrades to cindy-only.

13. **Companies computed_conviction_score at 0%** — Field exists but never populated.

14. **Network relationship_status at 0%** — Field exists but never populated.

15. **Portfolio "Terra" has no Companies DB match** — Naming inconsistency.

---

## 10. Recommendations for M12 Data Enrichment

1. **Fix network embeddings first** — The l41 batch (459 people at 0.7% coverage) needs immediate re-embedding. Then sweep the remaining 2,782 unembedded contacts.

2. **Enrich companies page_content** — 2,993 template entries need real content: website scraping, funding data, team info. Without this, company embeddings are meaningless.

3. **Populate actions company_notion_id** — Parse action text / thesis connections to infer company links. This unlocks company-level action views.

4. **Scale portfolio key_questions and high_impact** — From 28/33 to target 100+ each. These directly feed M5 scoring.

5. **Import Notion page body content** — Use Notion API to pull page blocks, comments, and embedded content for all portfolio and key companies. This is untapped intelligence.

6. **Fix sync staleness** — Actions queue and thesis threads haven't synced in 50+ hours. Investigate cron/agent health.

---

*Generated by M4 Datum Audit Agent, Loop 1. All data queried directly from Supabase project `llfkxnsfczludgigknbs` on 2026-03-21.*
