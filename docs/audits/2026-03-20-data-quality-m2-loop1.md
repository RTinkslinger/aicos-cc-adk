# Data Quality Audit — Machine 2 Loop 1
**Date:** 2026-03-20
**Database:** Supabase `llfkxnsfczludgigknbs` (Mumbai region)
**Auditor:** Claude Code (automated SQL audit)

---

## Summary

| Metric | Value |
|--------|-------|
| **Total rows across 6 tables** | **8,650** |
| **Overall embedding coverage** | **99.97%** (8,620 / 8,650) |
| **Tables at 100% embedding** | 5 of 6 (network has 1 missing, companies has 0 now) |
| **Company duplicates** | 57 duplicate-name groups (115 excess rows, including 1 triple: Swiggy) |
| **Network duplicates** | 259 duplicate-name groups (540 rows involved) |
| **Portfolio-to-Companies cross-ref gaps** | 26 portfolio companies not found in companies table |
| **Network-to-Notion gaps** | 402 network rows missing `notion_page_id` |
| **Trailing whitespace contamination** | 20 companies, 28 portfolio, 11 network |

### Top Gaps
1. **`page_content_path` completely empty for companies** (4,635/4,635 null) -- enrichment not yet run
2. **`last_interaction` 100% null in network** (3,728/3,728) -- field never populated
3. **`computed_conviction_score` 100% null in companies** (4,635/4,635) -- scoring not deployed
4. **`website` 94.5% null in companies** (4,382/4,635) -- critical for enrichment pipelines
5. **Portfolio cross-ref broken for 26 companies** due to naming mismatches (fka aliases, trailing spaces)

---

## Per-Table Analysis

### 1. companies (4,635 rows, ~76 columns)

**Freshness:** Earliest created: 2024-04-29 | Latest updated: 2026-03-20 11:05 UTC

| Column | Total | Non-Null | Null | Null % | Severity |
|--------|-------|----------|------|--------|----------|
| name | 4,635 | 4,635 | 0 | 0.0% | -- |
| deal_status | 4,635 | 4,635 | 0 | 0.0% | -- |
| pipeline_status | 4,635 | 4,635 | 0 | 0.0% | -- |
| sector | 4,635 | 2,915 | 1,720 | 37.1% | MEDIUM |
| type | 4,635 | 702 | 3,933 | 84.9% | LOW |
| priority | 4,635 | 1,321 | 3,314 | 71.5% | LOW |
| website | 4,635 | 253 | 4,382 | 94.5% | HIGH |
| venture_funding | 4,635 | 663 | 3,972 | 85.7% | LOW |
| smart_money | 4,635 | 28 | 4,607 | 99.4% | LOW |
| research_file_path | 4,635 | 21 | 4,614 | 99.5% | INFO |
| page_content_path | 4,635 | 0 | 4,635 | 100.0% | HIGH |
| computed_conviction_score | 4,635 | 0 | 4,635 | 100.0% | MEDIUM |
| embedding | 4,635 | 4,635 | 0 | 0.0% | -- |
| fts | 4,635 | 4,635 | 0 | 0.0% | -- |
| notion_page_id | 4,635 | 4,635 | 0 | 0.0% | -- |
| created_at | 4,635 | 4,635 | 0 | 0.0% | -- |
| updated_at | 4,635 | 4,635 | 0 | 0.0% | -- |

**Sector distribution (non-null, 2,915 rows):**
| Sector | Count |
|--------|-------|
| Consumer | 782 |
| SaaS | 645 |
| Financial Services | 428 |
| B2B | 388 |
| Venture Capital Firm | 283 |
| Frontier | 226 |
| Other | 163 |

**Pipeline status distribution:**
| Status | Count |
|--------|-------|
| NA | 2,976 |
| Pass Forever | 961 |
| Mining | 163 |
| Portfolio | 140 |
| Missed without screen | 95 |
| Passed Last Track For Next | 50 |
| Acquired/Shut Down/Defunct | 43 |
| Active Screening | 34 |
| Evaluating | 27 |
| Tracking_30 | 22 |
| Passive Screening | 21 |
| Lost | 20 |
| Process Miss | 19 |
| Screen | 18 |
| Anti Folio | 17 |
| Parked | 13 |
| Tracking_7 | 6 |
| Won & Closing | 5 |
| Tracking_90 | 4 |
| Tracking_180 | 1 |

---

### 2. network (3,728 rows, ~53 columns)

**Freshness:** Earliest created: 2026-03-20 09:27 UTC | Latest updated: 2026-03-20 11:14 UTC
(All rows created today -- this is a fresh bulk load)

| Column | Total | Non-Null | Null | Null % | Severity |
|--------|-------|----------|------|--------|----------|
| person_name | 3,728 | 3,728 | 0 | 0.0% | -- |
| current_role | 3,728 | 3,728 | 0 | 0.0% | -- |
| linkedin | 3,728 | 3,247 | 481 | 12.9% | MEDIUM |
| email | 3,728 | 3,728 | 0 | 0.0% | -- |
| phone | 3,728 | 3,728 | 0 | 0.0% | -- |
| ryg | 3,728 | 36 | 3,692 | 99.0% | LOW |
| e_e_priority | 3,728 | 10 | 3,718 | 99.7% | LOW |
| relationship_status | 3,728 | 3,728 | 0 | 0.0% | -- |
| source | 3,728 | 3,728 | 0 | 0.0% | -- |
| notion_page_id | 3,728 | 3,326 | 402 | 10.8% | MEDIUM |
| embedding | 3,728 | 3,727 | 1 | 0.03% | LOW |
| page_content_path | 3,728 | 30 | 3,698 | 99.2% | MEDIUM |
| ids_notes | 3,728 | 3,728 | 0 | 0.0% | -- |
| devc_poc | 3,728 | 562 | 3,166 | 84.9% | LOW |
| last_interaction | 3,728 | 0 | 3,728 | 100.0% | HIGH |
| fts | 3,728 | 3,728 | 0 | 0.0% | -- |
| created_at | 3,728 | 3,728 | 0 | 0.0% | -- |
| updated_at | 3,728 | 3,728 | 0 | 0.0% | -- |

**Note:** 402 network rows have no `notion_page_id` but DO have embeddings (402/402 have embeddings). These may be extracted from relation fields rather than direct Notion sync.

---

### 3. portfolio (142 rows, ~73 columns)

**Freshness:** Earliest created: 2026-03-20 09:49 UTC | Latest updated: 2026-03-20 11:10 UTC
(All rows created today -- fresh bulk load)

| Column | Total | Non-Null | Null | Null % | Severity |
|--------|-------|----------|------|--------|----------|
| portfolio_co | 142 | 142 | 0 | 0.0% | -- |
| company_name_id | 142 | 142 | 0 | 0.0% | -- |
| ownership_pct | 142 | 141 | 1 | 0.7% | LOW |
| entry_cheque | 142 | 141 | 1 | 0.7% | LOW |
| current_stage | 142 | 104 | 38 | 26.8% | MEDIUM |
| stage_at_entry | 142 | 131 | 11 | 7.7% | LOW |
| health | 142 | 141 | 1 | 0.7% | LOW |
| research_file_path | 142 | 142 | 0 | 0.0% | -- |
| page_content_path | 142 | 142 | 0 | 0.0% | -- |
| notion_page_id | 142 | 142 | 0 | 0.0% | -- |
| embedding | 142 | 142 | 0 | 0.0% | -- |
| hc_priority | 142 | 113 | 29 | 20.4% | LOW |
| ops_prio | 142 | 96 | 46 | 32.4% | MEDIUM |
| check_in_cadence | 142 | 131 | 11 | 7.7% | LOW |
| outcome_category | 142 | 97 | 45 | 31.7% | MEDIUM |
| follow_on_decision | 142 | 19 | 123 | 86.6% | LOW |
| investment_timeline | 142 | 139 | 3 | 2.1% | -- |
| key_questions | 142 | 14 | 128 | 90.1% | MEDIUM |
| fts | 142 | 142 | 0 | 0.0% | -- |
| created_at | 142 | 142 | 0 | 0.0% | -- |
| updated_at | 142 | 142 | 0 | 0.0% | -- |

**Health distribution:**
| Health | Count |
|--------|-------|
| Green | 84 (59.2%) |
| Yellow | 33 (23.2%) |
| Red | 18 (12.7%) |
| NA | 6 (4.2%) |
| null | 1 (0.7%) |

---

### 4. content_digests (22 rows, 18 columns)

**Freshness:** Earliest created: 2026-03-16 08:04 UTC | Latest created: 2026-03-16 13:10 UTC
(All from March 16 -- no new digests in 4 days)

| Column | Total | Non-Null | Null | Null % | Severity |
|--------|-------|----------|------|--------|----------|
| title | 22 | 22 | 0 | 0.0% | -- |
| slug | 22 | 22 | 0 | 0.0% | -- |
| url | 22 | 22 | 0 | 0.0% | -- |
| channel | 22 | 22 | 0 | 0.0% | -- |
| status | 22 | 22 | 0 | 0.0% | -- |
| content_type | 22 | 22 | 0 | 0.0% | -- |
| duration | 22 | 22 | 0 | 0.0% | -- |
| upload_date | 22 | 7 | 15 | 68.2% | MEDIUM |
| relevance_score | 22 | 22 | 0 | 0.0% | -- |
| net_newness | 22 | 22 | 0 | 0.0% | -- |
| digest_data | 22 | 22 | 0 | 0.0% | -- |
| digest_url | 22 | 22 | 0 | 0.0% | -- |
| processing_date | 22 | 22 | 0 | 0.0% | -- |
| embedding | 22 | 22 | 0 | 0.0% | -- |
| fts | 22 | 22 | 0 | 0.0% | -- |
| created_at | 22 | 22 | 0 | 0.0% | -- |

**Status distribution:** All 22 are `published`.
**No duplicate URLs found.**

---

### 5. thesis_threads (8 rows, 20 columns)

**Freshness:** Earliest created: 2026-03-06 05:38 UTC | Latest updated: 2026-03-16 13:20 UTC

| Column | Total | Non-Null | Null | Null % |
|--------|-------|----------|------|--------|
| thread_name | 8 | 8 | 0 | 0.0% |
| core_thesis | 8 | 8 | 0 | 0.0% |
| conviction | 8 | 8 | 0 | 0.0% |
| status | 8 | 8 | 0 | 0.0% |
| discovery_source | 8 | 8 | 0 | 0.0% |
| connected_buckets | 8 | 8 | 0 | 0.0% |
| evidence_for | 8 | 8 | 0 | 0.0% |
| evidence_against | 8 | 8 | 0 | 0.0% |
| key_question_summary | 8 | 8 | 0 | 0.0% |
| key_questions_json | 8 | 8 | 0 | 0.0% |
| key_companies | 8 | 8 | 0 | 0.0% |
| investment_implications | 8 | 8 | 0 | 0.0% |
| notion_page_id | 8 | 8 | 0 | 0.0% |
| embedding | 8 | 8 | 0 | 0.0% |
| notion_synced | 8 | 8 | 0 | 0.0% |
| fts | 8 | 8 | 0 | 0.0% |

**ZERO nulls across all columns. Perfect data quality.**

**Conviction distribution:** High (2), Medium (3), New (2), Low (1)
**Status distribution:** Exploring (7), Active (1)

---

### 6. actions_queue (115 rows, 27 columns)

**Freshness:** Earliest created: 2026-03-06 05:53 UTC | Latest updated: 2026-03-20 09:59 UTC

| Column | Total | Non-Null | Null | Null % |
|--------|-------|----------|------|--------|
| action | 115 | 115 | 0 | 0.0% |
| action_type | 115 | 115 | 0 | 0.0% |
| status | 115 | 115 | 0 | 0.0% |
| priority | 115 | 115 | 0 | 0.0% |
| source | 115 | 115 | 0 | 0.0% |
| assigned_to | 115 | 115 | 0 | 0.0% |
| created_by | 115 | 115 | 0 | 0.0% |
| reasoning | 115 | 115 | 0 | 0.0% |
| source_content | 115 | 115 | 0 | 0.0% |
| thesis_connection | 115 | 115 | 0 | 0.0% |
| relevance_score | 115 | 115 | 0 | 0.0% |
| outcome | 115 | 115 | 0 | 0.0% |
| scoring_factors | 115 | 115 | 0 | 0.0% |
| notion_page_id | 115 | 115 | 0 | 0.0% |
| embedding | 115 | 115 | 0 | 0.0% |
| notion_synced | 115 | 115 | 0 | 0.0% |
| fts | 115 | 115 | 0 | 0.0% |

**ZERO nulls across all checked columns. Excellent data quality.**

**Relevance score stats:** Min: 2.53 | Max: 10.0 | Avg: 7.07
**Only 4/115 rows have detailed `scoring_factors` (non-empty JSON).**

**Status distribution:**
| Status | Count |
|--------|-------|
| Proposed | 91 (79.1%) |
| Accepted | 23 (20.0%) |
| Dismissed | 1 (0.9%) |

**Priority distribution:**
| Priority | Count |
|----------|-------|
| P1 - This Week | 55 |
| P0 - Act Now | 44 |
| P2 - This Month | 8 |
| P1 | 4 |
| P2 | 4 |

**Action type distribution:**
| Type | Count |
|------|-------|
| Research | 46 |
| Meeting/Outreach | 32 |
| Portfolio Check-in | 19 |
| Pipeline Action | 13 |
| Thesis Update | 4 |
| Content Follow-up | 1 |

---

## Embedding Coverage Summary

| Table | Total | Embedded | Missing | Coverage |
|-------|-------|----------|---------|----------|
| companies | 4,635 | 4,635 | 0 | **100.0%** |
| network | 3,728 | 3,727 | 1 | **~100.0%** |
| portfolio | 142 | 142 | 0 | **100.0%** |
| thesis_threads | 8 | 8 | 0 | **100.0%** |
| actions_queue | 115 | 115 | 0 | **100.0%** |
| content_digests | 22 | 22 | 0 | **100.0%** |
| **TOTAL** | **8,650** | **8,649** | **1** | **99.99%** |

**Note:** Embedding generation completed during this audit session. Earlier snapshots showed 820 companies and 11 network rows missing embeddings, but by audit completion all had been backfilled except 1 network row.

---

## Cross-Reference Integrity

### Portfolio-to-Companies (by name match)

- **Exact match:** 91 of 142 portfolio companies found in companies table
- **Trimmed match:** 117 of 142 (26 more matched after stripping trailing whitespace)
- **Unmatched:** 26 portfolio companies with no match in companies table

**Unmatched portfolio companies (26):**

| Portfolio Name | Likely Cause |
|----------------|-------------|
| Answers.ai | Name not in companies DB |
| Ballisto AgriTech (f.k.a. Orbit Farming) | FKA alias -- may be under "Orbit Farming" or "Ballisto" |
| BetterPlace fka Mindforest | FKA alias |
| Blockfenders | Name not in companies DB |
| Coffeee | Name not in companies DB |
| Dodo Payments | Trailing space in portfolio |
| DreamSleep | Name not in companies DB |
| Eight Networks | Companies has "Eight Network" (singular) |
| ElecTrade | Name not in companies DB |
| Gloroots | Name not in companies DB |
| Kubesense (Tyke) | Parenthetical alias |
| Material Depot | Name not in companies DB |
| Multiwoven | Name not in companies DB |
| NuPort | Name not in companies DB |
| Pinegap | Name not in companies DB |
| Qwik Build (f.k.a Snowmountain) | FKA alias |
| ReplyAll (f.k.a. PRBT) | FKA alias |
| Revspot | Name not in companies DB |
| Stance Health (f.k.a HealthFlex) | FKA alias |
| Step Security | Name not in companies DB |
| Tejas (f.k.a Patcorn) | FKA alias |
| Terra | Name not in companies DB |
| Tractor Factory | Trailing space in portfolio |
| UGX | Name not in companies DB |
| VyomIC (f.k.a. AeroDome) | FKA alias |
| Workatoms | Trailing space in portfolio |

### Network-to-Notion

- **402 network rows** (10.8%) have no `notion_page_id`
- All 402 DO have embeddings -- they are valid records, likely extracted from Notion relation fields rather than direct page sync

---

## Duplicates Found

### Companies: 57 Duplicate Name Groups (115 rows)

**Triple duplicate (1):** Swiggy (3 rows)

**Double duplicates (56 groups), notable names:**
Accenture, Akunka Foods, Appsflyer, Armor, Berkley Haas Ventures, Betterhood, BhuMe, Buckeye AI, Cardinal, CRED, Credgenics, Digitap, Docura Health, Fibo, Flipkart, Freshworks, Groww, InRisk Insure, Iterative, Jodo, Jugyah, Krvvy, Kulfi, Lexi, M11, Mercor, Microsoft, MochaCare, Movable Voice, Myntra, Namaste, NeoDesh, Orange Collective, Oximy, Pinch, Plan B, Polymorph, Promaft Partners, Rhym, Segwise, Slack, Sponge, TEST -- Delete Me, The Arc, Umrit, Urban Company, Zomato, + educational institutions

**Note:** "TEST -- Delete Me" is a test row that should be cleaned up.

### Network: 259 Duplicate Name Groups (540 rows)

**Top duplicates by count:**
| Name | Count | Likely Cause |
|------|-------|-------------|
| Founder 2 | 6 | Placeholder name |
| Naman Jain | 4 | Common name, different people |
| Mohit Kumar, Raunak Tiwary, Rahul Gupta, Akash Gupta, Jayam Vora, Abhishek Sharma, Pavankumar Kamat, Rahul Sharma, Santu Maity, Rohan Singh, Deepak Kumar, Aditya Patil, Kunal Bhatia, Ayush Sharma, Deepak Sharma, Ritwick Dey | 3 each | Common names or true duplicates |

**Important:** Many of these may be legitimate different people with the same name. Dedup requires checking `notion_page_id` or `linkedin` for true duplicates vs. same-name-different-person.

### Portfolio & Content Digests: No duplicates found.

---

## Trailing Whitespace Contamination

| Table | Affected Rows | Field |
|-------|---------------|-------|
| companies | 20 | `name` |
| portfolio | 28 | `portfolio_co` |
| network | 11 | `person_name` |

This directly causes 26 of the portfolio-to-companies cross-reference failures (trimming fixes them). Sample companies with trailing whitespace: "Simplifin ", "Rumik ", "Eacel AI ", "Eight Network ", "Jolene ".

---

## Data Freshness Summary

| Table | Earliest Created | Latest Updated | Age |
|-------|-----------------|----------------|-----|
| companies | 2024-04-29 | 2026-03-20 11:05 UTC | **Live today** |
| network | 2026-03-20 09:27 | 2026-03-20 11:14 UTC | **Fresh bulk load today** |
| portfolio | 2026-03-20 09:49 | 2026-03-20 11:10 UTC | **Fresh bulk load today** |
| thesis_threads | 2026-03-06 05:38 | 2026-03-16 13:20 UTC | 4 days since update |
| actions_queue | 2026-03-06 05:53 | 2026-03-20 09:59 UTC | **Updated today** |
| content_digests | 2026-03-16 08:04 | 2026-03-16 13:10 UTC | 4 days since last digest |

---

## Gap Priority List

### [CRITICAL]
1. **`page_content_path` 100% null in companies** (4,635 rows) -- portfolio has it at 100%, companies has 0%. This blocks company-level content enrichment and semantic search on company pages.
2. **`last_interaction` 100% null in network** (3,728 rows) -- critical relationship data never synced from Notion.
3. **Portfolio cross-ref broken for 26 companies** -- prevents portfolio-to-pipeline linkage. Root cause: FKA aliases and trailing whitespace.

### [HIGH]
4. **`website` 94.5% null in companies** (4,382/4,635) -- blocks automated enrichment, web scraping, company research.
5. **Company duplicates: 57 groups / 115 rows** -- includes test data ("TEST -- Delete Me") and production duplicates (Swiggy x3, CRED x2, Flipkart x2, Zomato x2).
6. **Trailing whitespace in 59 rows** across 3 tables -- causes join failures and display issues.
7. **`computed_conviction_score` 100% null** (4,635 rows) -- scoring model not yet deployed to companies table.

### [MEDIUM]
8. **Network `notion_page_id` null for 402 rows** (10.8%) -- limits bidirectional Notion sync for these contacts.
9. **Portfolio `current_stage` 26.8% null** (38/142) -- operational gap for portfolio monitoring.
10. **Portfolio `outcome_category` 31.7% null** (45/142) -- limits portfolio analytics.
11. **Portfolio `key_questions` 90.1% null** (128/142) -- critical for AI-driven portfolio intelligence.
12. **Content digests `upload_date` 68.2% null** (15/22) -- metadata gap.
13. **Companies `sector` 37.1% null** (1,720/4,635) -- limits sector-based filtering and analysis.
14. **Actions queue priority inconsistency** -- mix of "P1 - This Week" (55) and legacy "P1" (4) format.

### [LOW]
15. **Network duplicates** (259 groups) -- many may be legitimate same-name-different-person. Needs LinkedIn/notion_page_id dedup check.
16. **Companies `type` 84.9% null** -- low-value field for most rows.
17. **Network `ryg` 99.0% null** -- field barely populated.
18. **Actions `scoring_factors` mostly empty JSON** -- only 4/115 have detailed breakdown.

---

## Recommendations for Loop 2

### Immediate Fixes (Script-able)
1. **Trim trailing whitespace** across companies.name, portfolio.portfolio_co, network.person_name -- fixes 59 rows and resolves ~26 cross-ref failures
2. **Delete test row** "TEST -- Delete Me" from companies (appears twice)
3. **Normalize priority format** in actions_queue -- convert "P1" to "P1 - This Week" and "P2" to "P2 - This Month" (8 rows)
4. **Generate `page_content_path`** for companies -- follow the same pattern used for portfolio (142/142 complete)

### Dedup Strategy
5. **Company dedup** -- for the 57 groups, compare `notion_page_id` to identify true duplicates vs. legitimate same-name entities
6. **Network dedup** -- for the 259 groups, compare `notion_page_id` and `linkedin` fields to separate same-name-different-person from true duplicates. "Founder 2" (6 instances) is clearly placeholder data

### Enrichment Priorities
7. **Backfill `website`** for high-priority companies (Mining, Active Screening, Evaluating, Portfolio) -- currently 253 have websites
8. **Populate `last_interaction`** from Notion meeting notes or relation data
9. **Deploy `computed_conviction_score`** calculation based on deal_status, pipeline_status, and thesis connections
10. **Populate `key_questions`** for portfolio companies from research files

### Cross-Reference Fixes
11. **Resolve 26 portfolio orphans** -- create alias mapping for FKA names or add alternate_names field
12. **Backfill `notion_page_id`** for 402 network rows where possible

---

## SQL Queries Used

All queries executed against project `llfkxnsfczludgigknbs` via `execute_sql`.

```sql
-- Schema discovery
SELECT table_name, column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name IN ('companies', 'network', 'portfolio', 'content_digests', 'thesis_threads', 'actions_queue')
ORDER BY table_name, ordinal_position;

-- Per-table null analysis (example: companies)
SELECT count(*) as total,
  count(*) FILTER (WHERE name IS NULL) as null_name,
  count(*) FILTER (WHERE sector IS NULL) as null_sector,
  count(*) FILTER (WHERE website IS NULL) as null_website,
  count(*) FILTER (WHERE embedding IS NULL) as null_embedding,
  -- ... (all columns checked)
FROM companies;

-- Embedding coverage summary
SELECT 'companies' as tbl, count(*) as total, count(embedding) as has_embed,
  count(*) - count(embedding) as missing, round(100.0 * count(embedding) / count(*), 1) as pct
FROM companies UNION ALL ... (all 6 tables);

-- Duplicate detection
SELECT name, count(*) FROM companies GROUP BY name HAVING count(*) > 1 ORDER BY count(*) DESC;
SELECT person_name, count(*) FROM network GROUP BY person_name HAVING count(*) > 1 ORDER BY count(*) DESC;

-- Cross-reference integrity
SELECT p.portfolio_co FROM portfolio p
LEFT JOIN companies c ON lower(trim(c.name)) = lower(trim(p.portfolio_co))
WHERE c.id IS NULL ORDER BY p.portfolio_co;

-- Distribution queries
SELECT health, count(*) FROM portfolio GROUP BY health ORDER BY cnt DESC;
SELECT status, count(*) FROM actions_queue GROUP BY status;
SELECT pipeline_status, count(*) FROM companies GROUP BY pipeline_status;

-- Freshness
SELECT min(created_at)::text, max(updated_at)::text FROM [each_table];

-- Trailing whitespace detection
SELECT name FROM companies WHERE name != trim(name);
SELECT count(*) FROM portfolio WHERE portfolio_co != trim(portfolio_co);
```
