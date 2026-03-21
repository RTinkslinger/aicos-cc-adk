# M4 Datum Machine Loop - 2026-03-21

## Scorecard: GREEN

| Metric | Value | Status |
|--------|-------|--------|
| Overall Health | GREEN | OK |
| Garbage Rate | 0.63% (22/3513) | OK |
| Embedding Coverage | 100% | OK |
| LinkedIn Fill | 88.1% | OK |
| Entity Connections | 23,716 | OK |
| Pending Requests | 1 | OK |
| Unprocessed Staging | 0 | OK |
| Score Overflow (M5 bug) | 32 actions | FLAG |
| Never-Synced Companies | 13 | MONITOR |

## Actions Taken

### Identity Resolution (5 people resolved)
| ID | Before | After | Confidence | Source |
|----|--------|-------|------------|--------|
| 168 | Deepanshu | Deepanshu (EthosX YC S22) | 1.0 | LinkedIn URL match |
| 2533 | Vedant | Vedant (Founder, Harness Insure) | 0.95 | LinkedIn company page |
| 305 | Prabhu | Prabhu Rangarajan (M2P Fintech) | 0.98 | Web search |
| 456 | Vikram | Vikram Shekhawat (ModalX CEO) | 0.98 | Web search |
| 1557 | Kanika | Kanika Agarrwal (India Quotient) | 0.97 | Web search |
| 2255 | Nick | Nick Khormaei (Neuramill CPO) | 0.98 | Web search |
| 4420 | Divyanshi | Divyanshi Chowdhary (Z47 AVP) | 0.97 | LinkedIn posts |

### Duplicate Company Handling (2 confirmed)
| ID | Name | Duplicate Of | Action |
|----|------|-------------|--------|
| 5337 | Step Security | 604 (StepSecurity) | Marked as duplicate |
| 5340 | DubDub | 3611 (Stealth Consumer AI) | Marked as duplicate |

### Domain Enrichment (1 company)
| ID | Name | Domain Added |
|----|------|-------------|
| 5335 | Lockstep | lockstep.vc |

### Datum Request Created (1)
- ID 2951 (Madhur at bono) -> likely Madhur Singal (Harness Insure co-founder). Confidence 0.85 -- needs user confirmation.

### Infrastructure Improvements
1. **datum_daily_maintenance cron job** created (job 28, runs daily at 5:30 AM)
2. **datum_stale_action_detector** improved:
   - Category 4 now returns both sides of duplicate theme pairs
   - New Category 6: score overflow detection (found 32 actions with M5 multiplicative model numeric overflow)
3. **datum_scorecard()** function created -- concise JSON health scorecard with GREEN/YELLOW/RED rating
4. **Datum CLAUDE.md updated**: 14 -> 24 documented SQL tools (added dashboard, context, interaction resolution, search, scorecard categories)

## Findings for Other Machines

### M5 Scoring (CRITICAL)
- 32 actions have `user_priority_score` values with 100+ digits (numeric overflow from multiplicative model)
- Example: action 105 score = 5.831...000 (160+ digits)
- Column type is `numeric` with no precision limit -- the multiplicative model creates unbounded values
- Recommendation: Add `ROUND(score, 6)` or cast to `NUMERIC(10,6)` in the scoring function

### Sync Agent
- All entity types show `sync_status: STALE` (last sync was 2026-03-20 for companies/network, 2026-03-19 for actions/thesis)
- Sync Agent is offline since Mar 17 per CHECKPOINT.md
- 13 companies have never been synced (10 from cindy-m8, 3 from M4-datum-v7)

### Embedding Pipeline
- 227 failures in last 24 hours, all "connection failed" (transient connection pool issues)
- All failures resolved by 08:45 UTC, queue fully drained, 0 pending
- Coverage remains 100% -- no data impact

## Data Quality Summary

| Entity | Total | Key Metric | Value |
|--------|-------|-----------|-------|
| Companies | 4,567 | Domain fill | 16.7% (609 NA-status thin entries expected) |
| Network | 3,513 | LinkedIn fill | 88.1% |
| Portfolio | 142 | Thesis fill | 68.3% |
| Actions | 145 total (23 proposed) | Company linked | 73.9% |
| Entity Connections | 23,716 | Types | 18 |
| Interactions | 23 | All processed | YES |
