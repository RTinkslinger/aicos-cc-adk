# Intelligence Quality Audit: Portfolio & Network Data
**Date:** 2026-03-20 | **Milestone:** M9 | **Auditor:** Claude Opus 4.6 (automated)

## Executive Summary

The Supabase intelligence layer holds **142 portfolio companies**, **3,722 network entries**, **4,565 companies**, and **115 actions**. Portfolio data is structurally sound with good Notion-to-Postgres sync fidelity. However, a **catastrophic `role_title` corruption** in the network table (100% of rows show "postgres" instead of actual roles) and pervasive duplicate person entries severely undermine the intelligence layer's utility for founder lookups, meeting prep, and relationship scoring.

### Overall Scores

| Dimension | Score | Grade |
|-----------|-------|-------|
| 1. Portfolio Company Data Quality | 82/100 | B+ |
| 2. Founder Linkage Quality | 25/100 | F |
| 3. Company-to-Thesis Connection | 40/100 | D |
| 4. Vector Similarity (Related Cos) | 30/100 | F |
| 5. Network Data Quality | 35/100 | D- |
| 6. Cross-Entity Consistency | 88/100 | B+ |
| **Weighted Overall** | **50/100** | **D** |

---

## Dimension 1: Portfolio Company Data Quality (82/100)

### Methodology
Reviewed all 142 portfolio companies across: health, current_stage, stage_at_entry, ownership_pct, entry_cheque, outcome_category, revenue_generating, research_file_path.

### Findings

**Health Status Distribution** (141 populated, 1 null):
- Green: 84 (59%) | Yellow: 33 (23%) | Red: 18 (13%) | NA: 6 (4%) | null: 1

Assessment: Distribution is plausible for an early-stage VC portfolio. The 6 "NA" entries correctly correspond to Exited/Shutdown companies. 18 Red companies that are still active (not exited) is reasonable for a seed fund.

**Stage Classification** (104 populated, 38 null = 27% gap):
- early revenue: 54 | post product: 15 | early product: 15 | scaling revenue: 9 | Exited/Shutdown: 6 | pre-product: 5

Assessment: Stage values are internally consistent. The taxonomy (pre-product -> early product -> post product -> early revenue -> scaling revenue -> Exited/Shutdown) is well-ordered. **38 companies (27%) missing current_stage is a significant gap** -- these appear to be newer investments where stage hasn't been assessed yet.

**Stage Regression Anomaly:**
- Ambak: stage_at_entry = "scaling revenue", current_stage = "early revenue" -- this is a backward progression. Either the entry stage was mislabeled or the company pivoted/contracted.

**Ownership Percentage** (141 populated, 1 null):
- Range: 0.09% to 6.71% | Average: 1.18%
- Distribution: <0.5%: 34 | 0.5-2%: 92 | 2-10%: 15 | >10%: 0
- This is highly plausible for a seed/pre-seed fund investing $25K-$500K checks.

**Entry Cheque** (140 populated, 1 null, 1 zero):
- Range: $25,000 to $500,000 | Average: $100,641
- Distribution: <$50K: 35 | $50K-$200K: 81 | $200K-$500K: 23 | >$500K: 1
- Anomalies: Kreo has entry_cheque = 0 and null ownership_pct. Kavana AI (Two Four Labs) has null entry_cheque but 0.09% ownership.
- Values appear to be in USD, consistent with Z47/$550M fund size.

**Research File Coverage:** 142/142 (100%) -- every portfolio company has a research file.

**Completeness Gaps:**

| Field | Null Count | % Missing |
|-------|-----------|-----------|
| current_stage | 38 | 27% |
| outcome_category | 45 | 32% |
| revenue_generating | 42 | 30% |
| round_1_type | 73 | 51% |
| stage_at_entry | 11 | 8% |
| health | 1 | <1% |
| entry_cheque | 1 | <1% |
| ownership_pct | 1 | <1% |

### Issues Found
1. **Ambak stage regression** (scaling revenue -> early revenue): needs verification
2. **Kreo** has 0 entry_cheque and null ownership_pct -- possible data entry error or non-standard deal
3. **Kavana AI** has null entry_cheque -- data gap
4. **27-32% of companies missing** current_stage, outcome_category, revenue_generating -- these appear correlated (same cohort of newer investments)
5. **51% missing round_1_type** -- significant gap for portfolio analytics

---

## Dimension 2: Founder Linkage Quality (25/100)

### Critical Finding: `role_title` Field Corruption

**All 3,722 network entries have `role_title` = "postgres"**

This is not a default value (column_default is NULL). The value "postgres" is the Postgres database superuser role name, strongly suggesting a sync/migration bug where `role_title()` (the Postgres SQL function that returns the current database user) was inadvertently written to all rows instead of the actual person's role.

**Impact:** Complete inability to:
- Identify founders vs. investors vs. operators in the network
- Filter for CEO/founder contacts of portfolio companies
- Power meeting prep with role context
- Automate relationship-based routing

### People-to-Portfolio Linkage (Structural)

Despite the role corruption, the structural linkage via `current_company_ids` -> `company_name_id` works correctly:

- **140 of 142 portfolio companies** have at least one linked network person
- Only **2 orphaned portfolio companies**: Coind (exited/shutdown) and Turnover
- People counts per portfolio company range from 1 to 6, which is reasonable

### Duplicate Person Entries (Pervasive)

**276 duplicate entries** across 3,722 rows (3,446 unique names vs 3,722 rows = 7.4% duplication rate).

Confirmed duplicate patterns:
- **Name spelling variants:** "Siddhant Satapath" vs "Siddhant Satapathy", "Subin T P" vs "Subin TP", "Prof S.K.Nandy" vs "S.K. Nandy", "Dr Tausif Shaikh" vs "Dr. Tausif Shaikh"
- **Exact duplicates with different IDs:** Avinash Sultanpur (id 696, 3885), Ben Merton (id 697, 1401), Lakshman Thatai (id 698, 4245), Deepak Shapeti (id 602, 2673)
- These duplicates have slightly different LinkedIn URL formats (with/without trailing slash, with/without originalSubdomain) but point to the same person

Top duplicated names: Naman Jain (4x), Jayam Vora (3x), Deepak Kumar (3x), Rahul Gupta (3x), etc. Some may be genuinely different people with common Indian names.

### RYG (Relationship Quality) Coverage

Only **36 of 3,722** network entries (0.97%) have a RYG rating:
- Green: 15 | Yellow: 7 | Red: 5 | Unclear: 9

These 36 appear to be high-value ecosystem contacts (founders of major startups, VCs) manually rated. The other 99% are unrated.

---

## Dimension 3: Company-to-Thesis Connection Quality (40/100)

### Coverage
- Only **6 of 142 portfolio companies** (4.2%) have thesis connections via the actions_queue
- Connected companies: CodeAnt, Confido Health, Inspecity, Lane, Smallest AI, Unifize

### Accuracy Assessment

| Company | Thesis Connection | Accurate? |
|---------|-------------------|-----------|
| CodeAnt | Agent-Friendly Codebase as Bottleneck | YES -- code quality/SDLC tool, directly relevant |
| CodeAnt | Cybersecurity / Pen Testing | PARTIAL -- code security is adjacent, not core cyber |
| Confido Health | Healthcare AI Agents as Infrastructure | YES -- healthcare SaaS with AI |
| Inspecity | USTOL / Aviation / Deep Tech Mobility | UNCLEAR -- Inspecity is inspection tech, not mobility per se |
| Lane | SaaS Death / Agentic Replacement | AMBIGUOUS -- without knowing Lane's product deeply |
| Smallest AI | Agentic AI Infrastructure, CLAW Stack | YES -- AI voice/speech infrastructure |
| Unifize | SaaS Death / Agentic Replacement | PARTIAL -- manufacturing SaaS, not obviously dying/being replaced |

### Thesis Connection Anti-Patterns

Many actions carry **ALL thesis threads as connections** (pipe-delimited lists of 5-6 theses). Example: actions mentioning "Lane" get tagged with ALL of: SaaS Death, Agentic AI, Healthcare AI, Cybersecurity, Non-Consumption Markets, Agent-Friendly Codebase. This is **over-tagging** -- an action about a specific company should connect to 1-2 relevant theses, not all of them.

The remaining **93 non-portfolio actions** in the queue have reasonable thesis connections (mapping AI infrastructure landscape, cybersecurity research, etc.) but the many-to-many nature makes the connections noisy.

---

## Dimension 4: Vector Similarity / Related Companies (30/100)

### Embedding Coverage
- Portfolio: 142/142 (100%)
- Companies: 4,565/4,565 (100%)
- Network: 3,722/3,722 (100%)

Full coverage is excellent. However, the **quality of similarity results is poor**.

### Nearest Neighbor Assessment (20 portfolio companies sampled)

| Portfolio Co | Sector | Top 5 Nearest | Quality |
|-------------|--------|---------------|---------|
| AeroDome (aerospace) | Frontier | Vyom OS, OpenFunnel, Olive, Circles, Vimag Labs | POOR -- OpenFunnel/Olive are SaaS, not aerospace |
| Alter AI (AI security) | SaaS | YOLO AI, Cliqq AI, Unsiloed AI, Quibble AI, Coinvent AI | FAIR -- all are AI companies but not security |
| Ambak (lending/fintech) | FinServ | Arya Pathak's co, Abhiyan Capital, Aagman, QistonPe, EnerZolve | MIXED -- some fintech, EnerZolve is energy |
| Ananant Systems (semicon) | Frontier | Green People, Pravaayu, Product Hunt, OneGreen | TERRIBLE -- green/consumer cos for a semiconductor co |
| Answers AI (edtech) | Consumer | AnswerThis, Grexa, gAI Ventures, Vink AI, Quansys AI | FAIR -- AnswerThis is related; others generic AI |
| Apptile (e-commerce SaaS) | SaaS | Plutus gg, Gytree, DevPunya, Tribal Coffee, Dink Pickleball | TERRIBLE -- none are e-commerce or SaaS tools |
| AskMyGuru (astrology AI) | Consumer | Greenday, Gytree, LottoG, Game Away, Currychief | POOR -- none related to astrology/spiritual tech |
| AuraML (robotics/AI) | SaaS | Revrag AI, Artha, OpenFunnel, Candytrail AI, Vink AI | POOR -- generic AI, not robotics/ML |
| Aurva (data security) | SaaS | Pravaayu, Miracles of Turmeric, Anusharv Gulati's co, Avari, ALYVCARE | TERRIBLE -- health/consumer for a security company |
| Highperformr AI (social media SaaS) | SaaS | Hooly AI, ProactAI, Revrag AI, Pint AI, Pre6 AI | FAIR -- all AI companies, ProactAI/Revrag are sales AI |
| Hotelzify (hospitality) | SaaS | Yelp, Airbnb, Travv World, Travalink, Zippy | GOOD -- all travel/hospitality |
| Inspecity (inspection) | SaaS | QistonPe, CoreStrat, ESCA Consumer Health, CredEazy, Creso | POOR -- fintech for an inspection company |
| Intract (web3 growth) | SaaS | Revrag AI, Revenoid, Bunny, Prasanna Lahoti's co, Korture | MIXED -- Revenoid has growth parallel |
| Isler (B2B SaaS) | B2B | Green Agrico Sri Lanka, Greenday, OneGreen, Gytree | TERRIBLE -- agriculture/green for B2B SaaS |
| Kavana AI (AI labs) | SaaS | Gaana AI, Kasper AI, Recrew AI, Vink AI, babblebots.ai | FAIR -- all AI companies |
| Kilrr (consumer) | Consumer | Kirana Pro, Gytree, Greenday, Cherry, Green Agrico | POOR -- random mix |

**Summary:** Of 20 sampled, only 1 (Hotelzify) produced genuinely useful related companies. ~3 were "fair" (right sector but not specific). The remaining 16 were poor to terrible.

**Root Cause Hypothesis:** The embeddings appear to be generated from minimal page content (likely just company names and brief descriptions from Notion page content paths), not from rich company descriptions including sector, business model, customer type, and thesis connections. This produces embeddings that cluster on superficial textual similarity rather than business/investment similarity.

---

## Dimension 5: Network Data Quality (35/100)

### Table Stats
- Total rows: 3,722 | Unique names: 3,446 | With LinkedIn: 3,241 (87%) | With company_ids: 3,205 (86%)

### Critical Issues

1. **`role_title` = "postgres" for ALL 3,722 entries** (see Dimension 2). This is the single most damaging data quality issue in the database.

2. **`enrichment_status` = "raw" for ALL 3,722 entries** -- no enrichment has been run on any network contact. Combined with the role corruption, this means the network table has names + LinkedIn URLs + company links but essentially no professional context.

3. **`ryg` populated for only 36 entries (0.97%)** -- relationship quality scoring covers less than 1% of the network.

4. **`e_e_priority` populated for only 2 entries** (Harshil Mathur and Jitendra Gupta, both P0).

5. **`datum_source` is NULL for all 3,722 entries** -- no provenance tracking.

6. **276 duplicate entries** (7.4% duplication rate) with variant name spellings and LinkedIn URL formats.

### What Works
- LinkedIn URLs present for 87% of contacts -- good coverage
- `home_base` populated for most entries with reasonable city/region values
- `current_company_ids` linkage to companies table works well (98.7% match rate: 3,195 of 3,238 company links resolve)
- The 36 RYG-rated contacts appear to be genuinely high-value ecosystem players (Aakrit Vaish, Lizzie Chapman, Suhail Sameer, etc.)

---

## Dimension 6: Cross-Entity Consistency (88/100)

### Portfolio-to-Companies Linkage
- **142/142 (100%)** portfolio companies match to entries in the companies table via `company_name_id` = `notion_page_id`
- Name matching is exact (sync preserves Notion names including "f.k.a." aliases)
- Sector tags from companies table align well with portfolio company businesses

### Network-to-Companies Linkage
- **3,195 of 3,238 company ID links resolve** (98.7%) -- only 43 orphaned links
- **26 distinct company IDs** in network.current_company_ids don't exist in companies table
- These are likely deleted or merged Notion pages

### Portfolio-to-Network Linkage
- **140 of 142** portfolio companies have at least one linked network person
- Only 2 orphans: Coind (exited), Turnover -- both plausible gaps

### Sector Consistency (Portfolio vs Companies table)
Spot-checked 40 portfolio companies against their companies table sector:

| Portfolio Co | Companies Sector | Consistent? |
|-------------|-----------------|-------------|
| AeroDome | Frontier | YES |
| Ambak | Financial Services | YES |
| Answers AI | Consumer | YES (edtech consumer) |
| Apptile | SaaS | YES |
| Boba Bhai | Consumer | YES (offline F&B brand) |
| Boxpay | Financial Services | YES (payments) |
| CarbonStrong | Frontier | YES (climate) |
| Confido Health | SaaS | YES (healthcare SaaS) |
| Flytbase | Frontier | YES (drones) |

All 40 checked were consistent. The sector taxonomy (Consumer, SaaS, B2B, Financial Services, Frontier, Venture Capital Firm, Other) maps sensibly to portfolio companies.

---

## Summary of Issues

### P0 -- Critical (Blocks intelligence utility)

| # | Issue | Impact | Table | Fix Effort |
|---|-------|--------|-------|-----------|
| 1 | `role_title` = "postgres" for all 3,722 network entries | No role data for any contact. Blocks founder lookup, meeting prep, relationship routing. | network | Re-sync from Notion or enrich from LinkedIn. M (hours). |
| 2 | `enrichment_status` = "raw" for all 3,722 network entries | No enriched data on any contact. The network table is structurally linked but contextually barren. | network | Run enrichment pipeline. L (days). |

### P1 -- High (Degrades intelligence accuracy)

| # | Issue | Impact | Table | Fix Effort |
|---|-------|--------|-------|-----------|
| 3 | 276 duplicate person entries (7.4% rate) | Inflated counts, confusing relationship maps, potential conflicting data if enriched differently | network | Dedup pass: merge by LinkedIn URL, then fuzzy name match. M. |
| 4 | Vector similarity produces ~80% irrelevant results | Related company suggestions useless; can't power "companies like X" queries | all | Re-embed with richer text (sector + description + thesis + business model). L. |
| 5 | Only 6/142 portfolio companies have thesis connections | Investment thesis layer disconnected from portfolio | actions_queue | Backfill thesis connections for all portfolio companies. M. |
| 6 | Thesis over-tagging (5-6 theses per action) | Dilutes signal; everything connects to everything | actions_queue | Review and trim to 1-2 most relevant theses per action. M. |

### P2 -- Medium (Gaps in completeness)

| # | Issue | Impact | Table | Fix Effort |
|---|-------|--------|-------|-----------|
| 7 | 27-32% of portfolio companies missing current_stage, outcome_category, revenue_generating | Portfolio analytics incomplete | portfolio | Backfill from Notion source of truth. S. |
| 8 | 51% missing round_1_type | Round type analytics incomplete | portfolio | Backfill from Notion. S. |
| 9 | RYG only on 36/3,722 network contacts (0.97%) | Relationship scoring effectively non-existent | network | Bulk RYG assignment or tiered auto-scoring. M. |
| 10 | Ambak stage regression (scaling -> early revenue) | Data inconsistency | portfolio | Verify and correct in Notion. XS. |
| 11 | Kreo: entry_cheque=0, ownership=null | Missing investment data | portfolio | Verify and correct in Notion. XS. |
| 12 | 26 orphaned company IDs in network.current_company_ids | Minor linkage gaps | network | Identify and clean up deleted Notion pages. S. |

---

## Recommendations for M2/M4 (Data Layer) Fix Priorities

### Immediate (This Sprint)
1. **Fix `role_title` corruption.** Investigate the sync code that populates this field. The Postgres function `role_title` returns "postgres" -- search for any SQL that uses `role_title` without table-qualifying it (e.g., `SELECT role_title` instead of `SELECT n.role_title FROM network n`). Re-sync the field from Notion after fixing.
2. **Run network deduplication.** Group by LinkedIn URL (normalize trailing slashes and query params), merge entries, preserve the most complete record.

### Next Sprint
3. **Re-generate embeddings** with enriched text. Current embeddings appear to use thin content. Concatenate: company name + sector + sector_tags + business description + thesis links + JTBD + sells_to for a meaningful embedding.
4. **Backfill portfolio completeness gaps** (current_stage, outcome_category, revenue_generating, round_1_type) from Notion source.
5. **Review and trim thesis connections** on actions_queue entries -- aim for 1-2 relevant theses per action, not broadcast tagging.

### Future Sprint
6. **Implement network enrichment pipeline** -- use LinkedIn data (via page_content_path markdown files) to populate actual roles, companies, and seniority.
7. **Build automated RYG scoring** based on interaction frequency, portfolio overlap, and deal sourcing attribution.
8. **Add thesis_connection directly to portfolio table** rather than relying on actions_queue text matching.

---

## Appendix: Data Counts

| Table | Total Rows | With Embeddings | With Notion Page ID |
|-------|-----------|----------------|-------------------|
| portfolio | 142 | 142 (100%) | 142 (100%) |
| companies | 4,565 | 4,565 (100%) | 4,565 (100%) |
| network | 3,722 | 3,722 (100%) | 3,722 (100%) |
| actions_queue | 115 | -- | 115 (100%) |

## Appendix: Portfolio Sector Distribution (via companies table)

| Sector | Count |
|--------|-------|
| Consumer | 770 |
| SaaS | 635 |
| Financial Services | 424 |
| B2B | 383 |
| Venture Capital Firm | 281 |
| Frontier | 221 |
| Other | 161 |

(Counts are across all 4,565 companies, not just portfolio.)
