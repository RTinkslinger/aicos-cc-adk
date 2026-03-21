# M9 Compression Verification Audit
**Date:** 2026-03-20
**Scope:** Verify M5 scoring compression fix results on `actions_queue`

---

## 1. Score Distribution (Proposed Actions)

| Bucket | Count | % of Total |
|--------|-------|------------|
| 6      | 3     | 3.3%       |
| 7      | 10    | 11.1%      |
| 8      | 54    | 60.0%      |
| 9      | 23    | 25.6%      |
| **Total** | **90** | **100%** |

## 2. Stats by Action Type

| Action Type        | Count | Avg Score | StdDev |
|--------------------|-------|-----------|--------|
| Portfolio Check-in | 36    | 8.64      | 0.32   |
| Meeting/Outreach   | 33    | 7.96      | 0.21   |
| Pipeline Action    | 12    | 7.71      | 0.37   |
| Research           | 6     | 6.94      | 0.79   |
| Content Follow-up  | 1     | 6.53      | --     |
| Thesis Update      | 2     | 6.10      | 0.53   |

## 3. Correlation: user_priority_score vs irgi_relevance_score

**r = -0.413** (moderate negative correlation)

This is unexpected -- higher IRGI relevance correlating with *lower* user priority. Likely artifact: Portfolio Check-ins dominate top scores (avg 8.64) but may have lower IRGI relevance scores since they're operational, not thesis-driven. Worth investigating in a future M9 loop.

## 4. Top 15 Actions

| # | Score | Type | Action (truncated) |
|---|-------|------|--------------------|
| 1 | 9.33 | Portfolio Check-in | Share Monday.com SDR-to-agent data with portfolio... |
| 2 | 9.31 | Portfolio Check-in | Request unit economics from Akasa Air and Motorq... |
| 3 | 9.15 | Portfolio Check-in | Request customer case study from Dallas Renal Group... |
| 4 | 9.03 | Portfolio Check-in | Flag closed-source components audit risk... |
| 5 | 8.98 | Portfolio Check-in | Flag Highperformr platform dependency risk... |
| 6 | 8.96 | Portfolio Check-in | Flag CodeAnt pricing volatility risk... |
| 7 | 8.89 | Portfolio Check-in | Flag regulatory risk on AI features for Unifize... |
| 8 | 8.89 | Portfolio Check-in | Flag operational capacity risk (36-46 employees)... |
| 9 | 8.83 | Portfolio Check-in | Flag Dodo Payments execution risk... |
| 10 | 8.79 | Portfolio Check-in | Request customer cohort retention by vintage... |
| 11 | 8.74 | Portfolio Check-in | Investigate 46% MoM D2C web traffic drop... |
| 12 | 8.74 | Portfolio Check-in | Request life sciences case study... |
| 13 | 8.73 | Portfolio Check-in | Request working capital health check... |
| 14 | 8.73 | Portfolio Check-in | Flag privacy/spam complaint risk for PowerUp... |
| 15 | 8.73 | Portfolio Check-in | Flag GameRamp execution risk... |

## 5. Compression Delta (Before vs After)

| Metric | Before (M5 pre-fix) | After (current) | Delta |
|--------|---------------------|------------------|-------|
| % in buckets 8-9 | **73.9%** | **85.6%** (77/90) | +11.7pp WORSE |
| Bucket spread | 8-9 dominated | 6-9 (but 8-9 still 85.6%) | Marginal improvement at low end |
| Lowest bucket | 8 | 6 | Floor dropped from 8 to 6 |
| StdDev (overall) | ~0.3 (estimated) | Varies 0.21-0.79 by type | More type differentiation |

### Verdict: COMPRESSION STILL PRESENT

The fix **did not resolve compression.** 85.6% of actions land in buckets 8-9, up from the 73.9% baseline. The scoring model still lacks discriminating power in the critical 5-8 range.

**What improved:**
- Some actions now score 6-7 (13 actions, 14.4%) -- previously nearly everything was 8+
- Action types now show clearer separation (Research avg 6.94 vs Portfolio 8.64)
- StdDev varies by type, suggesting the model differentiates *between* types but not *within* types

**What's still broken:**
- Within Portfolio Check-in (n=36), StdDev is only 0.32 -- all crammed into 8.3-9.0
- Within Meeting/Outreach (n=33), StdDev is only 0.21 -- essentially no differentiation
- Top 15 are ALL Portfolio Check-ins, range 8.73-9.33 (0.6 point spread for 15 items)
- No actions in buckets 1-5 at all -- the bottom half of the scale is completely unused

**Root cause hypothesis:** The scoring prompt likely has a floor bias -- it treats all "surfaced" actions as inherently high-priority (7+), rather than using the full 1-10 scale. The model needs to be told that a score of 5 is a valid, useful score for a real action.

---

*Generated: 2026-03-20 | Source: Supabase `actions_queue` table, project `llfkxnsfczludgigknbs`*
