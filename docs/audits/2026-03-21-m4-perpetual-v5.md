# M4 Datum Machine -- Perpetual Loop v5
**Date:** 2026-03-21
**Machine:** M4 (Datum)
**Loop:** Perpetual v5

---

## Executive Summary

This loop executed 5 major operations: built 5 new autonomous SQL functions (total: 12), enriched 330 network members with portfolio association signals (signal coverage 0.6% -> 9.7%), merged 8 duplicate company pairs (total merged: 10), added 10 new entity_connections via cross-entity linker, and created the master `datum_daily_maintenance()` orchestrator function. Network embeddings reached 100%. Companies embeddings reached 99.8%.

---

## Operations Executed

### 1. Network Signal Enrichment (330 people updated)
**What:** Network table had only 22/3,528 members with signals (0.6%). 330 members are connected to portfolio companies via entity_connections (current_employee, past_employee, affiliated_with).
**Tool Built:** `datum_network_signal_enricher()` (Tool #8)
**Action:** For each network member linked to a portfolio company, generated a `portfolio_association` signal containing:
- Company name, health status, current status, stage, priority, external signals
- Relationship type (current_employee, past_employee, affiliated_with)
- Multiple portfolio associations aggregated per person
**Result:** Network signal coverage: **343/3,528 (9.7%)** (was 22/3,528 = 0.6%). +321 people enriched.
**Idempotent:** Function checks for existing `portfolio_association` signals before updating.

### 2. Company Duplicate Detection & Merge (8 pairs)
**Tool Built:** `datum_company_name_deduplicator()` (Tool #9)
**Detection method:** Three strategies:
- Exact case-insensitive name match (1.0 score)
- Normalized match -- remove spaces/dots, lowercase (0.9 score)
- Prefix/suffix match -- "Company" vs "Company (YC W26)" (0.75 score)

**Found 8 normalized duplicates (all merged):**

| Keep (Winner) | Merge (Loser) | Reason |
|--------------|---------------|--------|
| Cloud Chef (2069) | CloudChef (2922) | More content |
| Goldsetu (5261) | Gold Setu (1032) | More content |
| LTI Mindtree (926) | LTIMindtree (4097) | More content |
| Ressl AI (3921) | ressl.ai (2110) | Has website, active pipeline |
| Sigmantic AI (2366) | SigmanticAI (2752) | Much more content |
| StepSecurity (604) | Step Security (5337) | Portfolio company, has website |
| Verbaflo AI (4686) | VerbaFlo.AI (2640) | Much more content |
| ZestMoney (5191) | Zest Money (4134) | More content |

**Merge process:** Rerouted all entity_connections from loser -> winner, deleted duplicate links, marked losers as `Merged/Duplicate` with merge note in page_content.
**Result:** Total merged companies: **10** (2 from v4 + 8 from v5).

**Also found 50 prefix/suffix matches** (not merged -- most are intentionally different entities like "Samsung" vs "Samsung R&D Institute India", or "Stealth" vs "Stealth (Shrenik Bohra)").

### 3. Stale Action Detection
**Tool Built:** `datum_stale_action_detector()` (Tool #10)
**Categories detected:**
```
stale_proposed_high_priority   11   avg 15.0 days   IDs: 10,11,41,45,46,48,50,58,75,79,85
stale_proposed_standard         0   -
accepted_no_outcome             0   -
duplicate_theme_clusters        6   IDs: 46,50,75,105,119,141
needs_scoring                   0   -
```
**Finding:** 11 high-priority proposed actions have been waiting 15 days for triage. All are Portfolio Check-in or Meeting/Outreach type. 6 actions share identical thesis connections and could be consolidated.

### 4. Cross-Entity Linker
**Tool Built:** `datum_cross_entity_linker()` (Tool #11)
**Operations:**
- Ensures network `current_company_ids` arrays are reflected in entity_connections
- Ensures network `past_company_ids` arrays are reflected in entity_connections
- Ensures all portfolio companies have `portfolio_investment` connections
- Ensures all action `company_notion_id` references have `action_references` connections

**Result:** Added 3 new action->company links on first run, then 2 more current_employee + 5 past_employee links found from merged duplicate rerouting. Total entity_connections: **23,734** (was 23,732).

### 5. Master Daily Maintenance Orchestrator
**Tool Built:** `datum_daily_maintenance()` (Tool #12)
**What:** Single function that runs all maintenance operations in sequence:
1. Consistency enforcer (auto-fix known issues)
2. Pseudo-ID resolution (fix any new pg:XXXX references)
3. Thesis auto-backfill (propagate thesis from portfolio to actions)
4. Cross-entity linker (ensure all relationships are in entity_connections)
5. Signal coverage check (portfolio companies without signals)
6. Stale action summary (proposed >7 days)
7. Duplicate tracking (merged companies count)
8. Data freshness (active companies not updated in 30 days)

**Agent usage:** Datum agent calls `datum_daily_maintenance()` on every heartbeat. Single call, comprehensive report.

---

## Autonomous SQL Function Suite (12 total)

| # | Function | Purpose | Created |
|---|----------|---------|---------|
| 1 | `datum_data_quality_check()` | 10-check health monitor | v3 |
| 2 | `datum_thesis_coverage()` | Thesis-to-portfolio gap analysis | v3 |
| 3 | `datum_signal_propagator()` | Propagate signals: exits, health, external | v4 |
| 4 | `datum_resolve_pseudo_ids()` | Fix pg:XXXX references in actions | v4 |
| 5 | `datum_thesis_auto_backfill()` | Backfill action thesis from portfolio | v4 |
| 6 | `datum_entity_health()` | Comprehensive entity health (16 metrics) | v4 |
| 7 | `datum_consistency_enforcer()` | Master check-and-fix (6 checks, auto-repair) | v4 |
| 8 | `datum_network_signal_enricher()` | Propagate portfolio signals to network | **v5 NEW** |
| 9 | `datum_company_name_deduplicator()` | Fuzzy name matching for duplicate detection | **v5 NEW** |
| 10 | `datum_stale_action_detector()` | Detect stale/duplicate actions needing triage | **v5 NEW** |
| 11 | `datum_cross_entity_linker()` | Ensure all relationships in entity_connections | **v5 NEW** |
| 12 | `datum_daily_maintenance()` | Master daily orchestrator (runs 1-7 + checks) | **v5 NEW** |

### Agent Autonomy Ladder
```
Heartbeat (every run):     datum_daily_maintenance()
On data change:            datum_signal_propagator() + datum_cross_entity_linker()
Weekly:                    datum_company_name_deduplicator() + datum_network_signal_enricher()
On demand:                 datum_entity_health() + datum_data_quality_check()
Diagnostic:                datum_stale_action_detector() + datum_thesis_coverage()
```

---

## Final Data Quality Dashboard

| Metric | v4 | v5 | Delta |
|--------|-----|-----|-------|
| Portfolio signal coverage | 100% (142) | **100% (142)** | -- |
| Companies signal coverage | 3.3% (152) | **3.3% (152)** | -- |
| Network signal coverage | 0.6% (22) | **9.7% (343)** | **+9.1pp** |
| Network embedding | 89.5% (3,156) | **100% (3,528)** | **+10.5pp** |
| Companies embedding | 98.4% (4,505) | **99.8% (4,569)** | **+1.4pp** |
| Actions thesis rate | 69.4% | **69.4%** | -- |
| Pseudo-ID count | 0 | **0** | -- |
| Entity connections | 23,732 | **23,734** | +2 |
| Known duplicates | 2 | **10** | +8 merged |
| Stale proposed (>7d) | 11 | **11** | Needs user triage |
| Autonomous tools | 7 | **12** | +5 new |

### datum_data_quality_check() (final)
```
unlinked_actions       INFO     5      -
actions_thesis_rate    OK       144    69.4%
portfolio_thesis_pct   WARNING  92     64.8%
portfolio_website_pct  OK       141    99.3%
portfolio_funding_pct  OK       97     68.3%
exit_consistency       OK       0      -
network_embedding_pct  OK       3528   100.0%   (was 89.5%)
entity_connections     OK       23734  -
stale_proposed         OK       11     -
companies_embedding    OK       4569   99.8%    (was 98.4%)
```

### datum_entity_health() (final)
```
companies  total                4579   4579   100%    OK
companies  has_notion_page_id   4579   4579   100%    OK
companies  has_website          4579   759    16.6%   CRITICAL
companies  has_page_content     4579   3943   86.1%   WARNING
companies  has_signal_history   4579   152    3.3%    INFO
portfolio  total                142    142    100%    OK
portfolio  has_signal_history   142    142    100%    OK
portfolio  has_thesis           142    92     64.8%   WARNING
portfolio  has_page_content     142    142    100%    OK
network    total                3528   3528   100%    OK
network    has_embedding        3528   3528   100%    OK       (was 89.5%)
network    has_signal_history   3528   343    9.7%    INFO     (was 0.6%)
actions    total                144    144    100%    OK
actions    has_company_link     144    113    78.5%   CRITICAL
actions    has_thesis           144    100    69.4%   OK
actions    pseudo_id_count      0      0      -       OK
```

### datum_daily_maintenance() (first run)
```
consistency_known_duplicates             NEEDS_ATTENTION  10   informational
consistency_consistency_check_complete   OK               0    all resolved
pseudo_id_resolution                     OK               0    -
thesis_actions_thesis_backfill           OK               0    -
thesis_unlinked_active_actions           ENRICHED         15   active actions no company
linker_new_current_employee_links        LINKED           2    from network arrays
linker_new_past_employee_links           LINKED           5    from network arrays
linker_new_portfolio_investment_links    OK               0    -
linker_new_action_company_links          OK               0    -
linker_total_entity_connections          LINKED           23734
signals_portfolio_missing                OK               0    -
stale_actions_7d                         WARNING          11   need triage
known_duplicates                         INFO             10   -
stale_companies_30d                      OK               0    -
```

---

## Unlinked Actions Analysis (31 total, 15 active)

Verified all 31 unlinked actions. None are bugs -- they are legitimately company-agnostic:
- **Research actions** (17): Thesis-level research spanning multiple companies (CLAW stack, SaaS Death mapping, agent infrastructure)
- **Portfolio Check-in** (6): Fund-level operational tasks (capital transfers, unit economics requests)
- **Thesis Update** (3): Cross-cutting thesis evolution
- **Meeting/Outreach** (3): People-based, not company-based
- **Content Follow-up** (1): Podcast segment listening
- **Pipeline Action** (1): Ecosystem mapping

**Recommendation:** These should remain unlinked. The `actions_has_company_link CRITICAL (78.5%)` status in datum_entity_health should be reframed -- the 31 unlinked actions are correct. True linkage rate for company-specific actions is 100%.

---

## Next Loop Priorities

1. **Companies website: 16.6% CRITICAL** -- 3,820 companies missing websites. Page_content does NOT contain URLs (verified). Requires web search API calls per company. M12/Datum agent territory.
2. **Portfolio thesis: 50 unmapped** -- Needs new thesis threads (Financial Services, Consumer Brands, B2B Marketplaces) or explicit accept as thesis-agnostic.
3. **Network signal_history: 9.7%** -- 343/3,528 enriched via portfolio associations. Next source: Cindy comms data (email/WhatsApp/calendar). Can also mine page_content for role-based signals.
4. **Companies signal_history: 3.3%** -- 152/4,579. Non-portfolio companies need deal signal extraction.
5. **Stale actions: 11 at 15 days** -- Need user triage (accept/dismiss). Not a Datum issue.
6. **Duplicate monitoring** -- 50 prefix/suffix matches flagged, not auto-merged. Run `datum_company_name_deduplicator()` monthly for new entries.
7. **datum_entity_health threshold tuning** -- Reframe `actions_has_company_link` threshold from CRITICAL to OK (31 are correctly unlinked).
