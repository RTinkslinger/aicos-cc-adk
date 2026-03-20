# Data Quality Fixes — Machine 2 Loop 2
**Date:** 2026-03-20
**Database:** Supabase `llfkxnsfczludgigknbs` (Mumbai region)
**Executor:** Claude Code (automated SQL)
**Input:** Loop 1 audit report (`2026-03-20-data-quality-m2-loop1.md`)
**SQL archive:** `sql/data-quality-fixes.sql`

---

## Summary

| Fix | Before | After | Improvement |
|-----|--------|-------|-------------|
| **Trailing whitespace** | 59 rows contaminated | 0 rows | 100% resolved |
| **Test rows** | 9 junk rows in companies | 0 | 9 deleted |
| **Portfolio cross-ref** | 26 unmatched (of 143) | 1 unmatched (of 142) | 25 resolved (96%) |
| **Company duplicates** | 59 groups / 61 excess rows | 0 duplicates | 100% resolved |
| **page_content_path** | 0 / 4,635 companies | 467 / 4,565 companies | 0% → 10.2% |
| **Companies total** | 4,635 | 4,565 | -70 rows (9 test + 61 dupes) |

---

## Fix 1: Trim Trailing Whitespace

**Baseline:** 20 companies, 28 portfolio, 11 network rows with trailing whitespace.

**Action:**
- `TRIM(name)` on companies.name → 20 rows fixed
- `TRIM(website)` on companies.website → 0 rows (already clean)
- `TRIM(person_name)` on network.person_name → 11 rows fixed
- `TRIM(portfolio_co)` on portfolio.portfolio_co → 28 rows fixed

**Additional discovery:** 2 rows had Unicode non-breaking spaces (U+00A0) that `TRIM()` doesn't catch:
- `Multiwoven\u00A0` in companies (id: 288) → manually corrected
- `Tractor Factory\u00A0` in portfolio (id: 153) → manually corrected

**Result:** 0 whitespace contamination remaining across all 3 tables.

---

## Fix 2: Delete Test Rows

**Baseline:** 11 rows matching `%TEST%` pattern.

**Analysis:** 2 were legitimate companies (preserved):
- LambdaTest (id: 5272) — real company, pipeline_status: NA
- Testmint AI (id: 4384) — real company, pipeline_status: Pass Forever

**Deleted (9 rows):**
| ID | Name | Reason |
|----|------|--------|
| 16 | [TEST] Explicit Parent | Test infrastructure |
| 17 | [TEST] Migration | Test infrastructure |
| 18 | [TEST] Migration | Test infrastructure (duplicate) |
| 19 | [TEST] Visual Check v2 | Test infrastructure |
| 3014 | PantoMax (Test Co) | Test data |
| 3537 | SkillBridge Test Co | Test data |
| 3543 | ToC Test Page | Test infrastructure |
| 3643 | TEST — Delete Me | Explicitly marked for deletion |
| 3644 | TEST — Delete Me | Explicitly marked for deletion (dup) |

**Safety check:** No FK constraints reference companies table — no cascade risk.

---

## Fix 3: Resolve Portfolio-to-Companies Name Mismatches

**Baseline:** 26 portfolio companies unmatched against companies table (after whitespace trim).

**Strategy:** Update `portfolio.portfolio_co` to match the canonical `companies.name` exactly, since companies is the master table.

### Resolution Details

**Simple mismatches (5):**
| Portfolio (old) | Companies (canonical) | Match Type |
|---|---|---|
| Eight Networks | Eight Network | Singular/plural |
| ElecTrade | ElecTrade (f.k.a. Hatch N Hack) | Missing FKA suffix |
| Kubesense (Tyke) | Kubesense (f.k.a Tyke) | Different parenthetical format |
| Step Security | StepSecurity | Spacing |
| Tractor Factory | Tractor Factory | Fixed by NBSP removal |

**FKA alias reversals — portfolio had new name, companies had old/different name (7):**
| Portfolio (old) | Companies (canonical) | Notes |
|---|---|---|
| Ballisto AgriTech (f.k.a. Orbit Farming) | Orbit Farming | Companies uses old name |
| BetterPlace fka Mindforest | Mindforest | Companies uses old name |
| Qwik Build (f.k.a Snowmountain) | Snowmountain AI | Companies uses old name + suffix |
| ReplyAll (f.k.a. PRBT) | ReplyAll (PRBT) | Different parenthetical format |
| Stance Health (f.k.a HealthFlex) | Stance Health (f.k.a. HealthFlex) | Missing period in "f.k.a" |
| Tejas (f.k.a Patcorn) | Patcorn | Companies uses old name |
| VyomIC (f.k.a. AeroDome) | AeroDome Technologies Private Limited | Companies uses full legal name |

**Company name variants (12):**
| Portfolio (old) | Companies (canonical) | Match Type |
|---|---|---|
| Answers.ai | Answers AI | Dot vs space |
| Blockfenders | Dataflos (f.k.a. Blockfenders) | Company rebranded |
| Coffeee | Coffeee.io | Missing .io suffix |
| Dodo Payments | Dodo Pay | Name variant |
| DreamSleep | DreamSpan (f.k.a. DreamSleep) | Company rebranded |
| Gloroots | Recrew AI (f.k.a. Gloroots) | Company rebranded |
| Material Depot | Material Depot (YC W22) | Missing batch suffix |
| NuPort | NuPort Robotics | Missing suffix |
| Pinegap | Pinegap AI | Missing AI suffix |
| Revspot | Revspot.AI | Missing .AI suffix |
| UGX | UGX AI | Missing AI suffix |
| Workatoms | Rilo (f.k.a. Workatoms) | Company rebranded |

**Multiwoven** (1): matched after NBSP fix in both companies and portfolio tables.

**Remaining unmatched (1):** `Terra` (portfolio id: 150)
- Candidates in companies: Terra Motors (1905), Terra.do (477), Terractive (478), TerraShare (1795), Terrakotta.ai (3008)
- None are a clear match — needs manual resolution in Loop 3

**Result:** 141 of 142 portfolio companies now match (99.3%, up from 82.4%).

---

## Fix 4: Company Dedup

**Baseline:** 59 duplicate-name groups (57 doubles + 2 triples = 61 excess rows).

**Method:** Data richness scoring across 12 key fields:
`website, sector, type, priority, venture_funding, pipeline_status (non-NA), deal_status (non-NA), jtbd, sells_to, smart_money, research_file_path, founding_timeline`

For each group: keep the row with highest richness score. On tie, keep the lowest ID (oldest record).

**61 rows deleted.** Notable resolutions:

| Company | Kept | Deleted | Richness (kept/deleted) |
|---------|------|---------|------------------------|
| Swiggy | 1291 | 4458, 4761 | 1 / 1, 1 |
| Betterhood | 1478 | 1481, 1482 | 4 / 4, 1 |
| CRED | 112 | 1936 | 0 / 0 |
| Flipkart | 593 | 4146 | 0 / 0 |
| Zomato | 4571 | 1004 | 4 / 1 |
| Freshworks | 3489 | 4145 | 4 / 0 |
| Pinch | 3477 | 4214 | 7 / 2 |
| Lexi | 1953 | 3204 | 7 / 5 |
| Pulse | 2436 | 2267 | 7 / 5 |

**Safety analysis:**
- No FK constraints reference the companies table
- 7 network rows reference deleted companies' `notion_page_id` via `current_company_ids` text array — these are soft references and will not break queries, but represent dangling pointers
- Notion remains the source of truth for these relationships

**Result:** 0 duplicate name groups remaining in companies.

---

## Fix 5: Generate page_content_path for Companies

**Baseline:** 0 of 4,635 companies had `page_content_path` (100% null).

**Method:**
1. Listed 526 `.md` files in `companies-pages/` directory
2. Slugified company names: `LOWER(name)` → replace `[^a-z0-9]+` with `-` → collapse multiple hyphens → strip leading/trailing hyphens
3. Matched slugified names against file slugs
4. Set `page_content_path = 'companies-pages/{slug}.md'` for matches

**Result:** 467 of 4,565 companies now have `page_content_path` (10.2%).

**59 files unmatched** (526 - 467) — likely due to:
- Accented characters in company names (e.g., French school names)
- Apostrophes that slugify differently
- Edge cases in slug generation (e.g., `'s` in names)

These can be resolved with manual mapping in Loop 3.

---

## Final State (Post All Fixes)

### Row Counts
| Table | Before | After | Change |
|-------|--------|-------|--------|
| companies | 4,635 | 4,565 | -70 (9 test + 61 dupes) |
| network | 3,728 | 3,728 | No change |
| portfolio | 142 | 142 | No change |
| content_digests | 22 | 22 | No change |
| thesis_threads | 8 | 8 | No change |
| actions_queue | 115 | 115 | No change |
| **Total** | **8,650** | **8,580** | **-70** |

### Cross-Reference Integrity
| Check | Before | After |
|-------|--------|-------|
| Portfolio → Companies match | 117/143 (81.8%) | **141/142 (99.3%)** |
| Trailing whitespace | 59 rows | **0 rows** |
| Company duplicates | 59 groups | **0 groups** |
| Test/junk rows | 9 | **0** |
| Companies page_content_path | 0/4,635 (0%) | **467/4,565 (10.2%)** |

### Embedding Coverage (unchanged — all pre-existing)
| Table | Total | Embedded | Coverage |
|-------|-------|----------|----------|
| companies | 4,565 | 4,565 | 100.0% |
| network | 3,728 | 3,728 | 100.0% |
| portfolio | 142 | 142 | 100.0% |
| thesis_threads | 8 | 8 | 100.0% |
| actions_queue | 115 | 115 | 100.0% |
| content_digests | 22 | 22 | 100.0% |

---

## Remaining Gaps for Loop 3

### Critical
1. **`Terra` portfolio orphan** — 1 remaining unmatched portfolio company. Needs manual disambiguation (Terra Motors vs Terra.do vs other).
2. **Companies `page_content_path` at 10.2%** — 4,098 companies still missing. Only 526 files exist on disk (from portfolio-focused page generation). Need to generate pages for remaining high-priority companies.
3. **`last_interaction` 100% null in network** (3,728 rows) — not addressed in this loop (requires Notion meeting notes data).
4. **`website` 94.5% null in companies** — not addressed (requires web enrichment pipeline).

### High
5. **59 unmatched page files** — slug generation edge cases for accented/special characters. Manual mapping needed.
6. **7 network rows with dangling company references** — `current_company_ids` pointing to deleted duplicate `notion_page_id` values. Could update to point to kept row's `notion_page_id`.
7. **Network duplicates** (259 groups) — not addressed in this loop. Many are legitimate same-name-different-person. Requires LinkedIn/notion_page_id dedup check.
8. **`computed_conviction_score` 100% null** — scoring model not yet deployed.

### Medium
9. **Actions queue priority format inconsistency** — mix of "P1 - This Week" (55) and legacy "P1" (4). Quick normalization needed.
10. **Portfolio `key_questions` 90.1% null** — critical for AI-driven portfolio intelligence.
11. **Portfolio `current_stage` 26.8% null** — operational gap for portfolio monitoring.
