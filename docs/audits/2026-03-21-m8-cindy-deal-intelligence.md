# M8 Cindy: Deal Intelligence Loop
**Date:** 2026-03-21 | **Machine:** M8 Cindy | **Loop:** 5

## Feedback Processed
- **ID 20** (user, /comms page): "Quivly is a portfolio company. Deal negotiations happening. Poor reasoning."
  - Root cause: WhatsApp deal signals existed but no obligations generated, no deal momentum section on /comms, interaction linked_companies showed integer IDs instead of names, portfolio data gaps (ops_prio null, current_stage null)

## Changes Made

### SQL Functions (Supabase)
1. **`cindy_deal_obligation_generator()`** (NEW) — Auto-creates deal follow-up obligations from WhatsApp deal signals. Finds interactions with deal_signals, matches to companies via linked_companies, resolves primary contact (CEO > founder > CTO), creates obligations with portfolio-aware priority (0.95 for portfolio, 0.9 for P0, etc.). Idempotent: skips companies with existing obligations in last 7 days.
2. **`cindy_system_report()`** (v2.0 -> v2.1) — Added `deal_velocity` section (hot_deals, active_deals, deal_obligations, deal_obligations_overdue) and `deal_health` to overall_health.
3. **`cindy_agent_skill_registry()`** (v3.2 -> v3.3) — Added intel-6 (deal obligation auto-generator), updated obligation count, deal velocity stats.

### Cron Jobs
- **Job 27**: `cindy_deal_obligation_generator()` runs daily at 6am UTC

### Data Fixes
- **Quivly** (companies id=380): ops_prio P0, current_stage pre-seed, page_content enriched with deal/founder info
- **Soulside** (companies id=443): ops_prio P1, current_stage seed
- **2 obligations created**: Quivly (Tanay Agrawal, P0.95, due Mar 24), Soulside (Surabhi Bhandari, P0.95, due Mar 24)

### Frontend (aicos-digests)
1. **Company ID resolution** (queries.ts) — `fetchInteractionsWithSignals` now resolves integer company IDs to names via batch lookup. Already committed in prior session.
2. **Deal Momentum section** (page.tsx) — New section on /comms showing all active portfolio deals with velocity status (HOT/WARM/COOLING), obligation counts, deal trail snippets, channels, ownership %. Already committed.
3. **`deal_followup` obligation rendering** (page.tsx) — Story builder for deal obligations with portfolio-aware context ("Active deal activity on Quivly (1.0% ownership). Tanay's team has active-deal signals."). "Check in" action button. Portfolio company badges in linked entities (green vs cyan).
4. **Portfolio company badges** (page.tsx) — Linked entity badges show "Portfolio" suffix with green styling when company has pipeline_status='Portfolio'. Already committed.

### Deployed
- digest.wiki: All commits pushed and live via Vercel Git Integration

## System State After
| Metric | Before | After |
|--------|--------|-------|
| Cindy system version | 2.0 | 2.1 |
| Skill registry | v3.2 (13 skills) | v3.3 (14 skills) |
| Deal obligations | 0 | 2 |
| Quivly ops_prio | null | P0 |
| Quivly current_stage | null | pre-seed |
| /comms deal section | none | 5 active deals visible |
| linked_companies rendering | integer IDs | company names |

## Feedback Response
The "poor reasoning" on Quivly was caused by a gap between signal detection (deal_signals existed) and action generation (no obligations created). Fixed by:
1. Auto-generating obligations from deal signals
2. Surfacing deal velocity data on /comms
3. Enriching portfolio data for active deal companies
4. Resolving company IDs to names in the UI
