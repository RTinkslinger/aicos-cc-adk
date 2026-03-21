# M1 WebFront Perpetual Loop v7 Audit

**Date:** 2026-03-21
**Machine:** M1 WebFront
**Loop:** v7 (perpetual)
**Deploy:** Committed `9283c6f`, pushed to `origin/main`, Vercel auto-deployed to digest.wiki

---

## What Shipped

### 1. Cindy Intelligence Wired into Home Page (Major)

Replaced the naive in-page attention logic (text-matching actions to company names) with `cindy_companies_needing_attention()` RPC -- a multi-signal intelligence function built by M8.

**Before:** Matched action text against company names with string includes. Only detected P0 actions and Red health. No obligation awareness.

**After:** Uses Cindy's multi-signal scoring:
- P0 actions (weighted highest)
- Overdue obligations with days overdue
- Health status (Red/Yellow)
- Days since last interaction
- Deal signals
- Ops priority (P0/P1/P2)
- Key question coverage

**Files changed:**
- `src/lib/supabase/types.ts` -- Added `CindyAttentionResult`, `CindyAttentionCompany`, `CindyAttentionSignals`, `CindyAttentionAction`, `CindyAttentionObligation` types
- `src/lib/supabase/queries.ts` -- Added `fetchCompaniesNeedingAttention()` RPC wrapper
- `src/app/page.tsx` -- Replaced 50-line naive attention builder with Cindy intelligence call
- `src/components/home/PortfolioHealthOverview.tsx` -- Extended `CompanyAttention` type with `attentionScore`, `overdueObligations`, `opsPrio`

**Home page "Needs Your Attention" now shows:**
- Company name with health dot and action count
- Ops priority badge (P0/P1 from Cindy)
- Reason tag (multi-signal: "2 P0 actions", "3 overdue obligations (11d)", "Red health -- needs check-in")
- Overdue obligation count badge
- 7 companies displayed (up from 5)

### 2. M5 v5.2 Score Multiplier Display (Medium)

Updated `ScoreBreakdownBars` and `ActionScoreBreakdownRow` type to show the new v5.2 multipliers.

**New badges in Scoring Breakdown section:**
- Freshness percentage (e.g., "Fresh 3%")
- Interaction recency boost (e.g., "Recency +77%")
- Depth grade (e.g., "Depth L3")
- Portfolio-linked indicator
- Blended score (the final composite, e.g., "Blended 7.5")

**Type additions:** `freshness_pct`, `interaction_recency_boost`, `is_portfolio_linked`, `depth_grade`, `blended_score`

### 3. Mobile Responsiveness Fix (Small)

Restructured attention list from single-row (overflowing at 375px) to two-row layout:
- Row 1: health dot + company name + action count badge
- Row 2: signal badges (ops_prio, reason, overdue count) -- flex-wraps on mobile

---

## Verification

### Live Site (digest.wiki) Verified:
- Home page: Cindy attention list rendering 7 companies with multi-signal badges
- Action detail (/actions/105): M5 v5.2 multiplier badges visible (Fresh 3%, Recency +77%, Depth L3, Blended 7.5)
- Score breakdown: All 6 factors + strategic composite + percentile badges rendering correctly
- Comms page: Obligation action buttons (dismiss, fulfill, reschedule, follow-up) -- server actions are wired to Supabase with proper RLS bypass

### Feedback Widget:
- CHECK constraint verified: includes UX, Intelligence, Data, Bug, General
- Recent feedback entries (5) confirmed in `user_feedback_store`
- Widget submits successfully

### Build:
- TypeScript compilation: clean
- All 20+ routes building successfully

---

## Pages Progressive Disclosure Status

| Page | L0 (Listing) | L1 (Detail) | Status |
|------|:---:|:---:|--------|
| Home `/` | Full dashboard | N/A | Good -- Cindy intelligence, briefing, priority actions |
| Actions `/actions` | Triage queue with scores | `/actions/[id]` with full breakdown | Good |
| Thesis `/thesis` | Landscape cards with momentum/conviction/bias | `/thesis/[id]` with evidence + suggestions | Good |
| Portfolio `/portfolio` | Health grid with filters | `/portfolio/[id]` with founders, actions, intelligence | Good |
| Companies `/companies` | Search + filter list | `/companies/[id]` with pipeline, portfolio link | Good |
| Network `/network` | People list with search | `/network/[id]` with obligations, interactions | Good |
| Comms `/comms` | Obligation cards with action buttons | Person intelligence panel | Good |
| Strategy `/strategy` | Briefing + contradictions | N/A (single page) | Good |

All pages follow L0->L1 progressive disclosure pattern.

---

## Comms Obligation Buttons -- End-to-End Flow

Verified the full flow:
1. `ObligationCard` (server) renders story + suggests action buttons
2. `ObligationCardClient` (client) handles button clicks
3. Server actions in `comms/actions.ts`:
   - `dismissObligation` -> updates status to "dismissed", sets fulfilled_at
   - `fulfillObligation` -> updates status to "fulfilled"
   - `rescheduleObligation` -> updates due_date, resets to "pending"
   - `createFollowUpAction` -> inserts into `actions_queue`, links obligation
4. All actions call `revalidatePath("/comms")` for fresh data
5. Uses `createAdminClient()` (service key, bypasses RLS)

---

## Next Loop Priorities

1. **Cindy attention on portfolio listing page** -- wire the same intelligence into `/portfolio` filter/sort
2. **Mobile testing at 375px** -- full pass on comms page (obligation cards, person intel panel)
3. **Score explanation v5.2** -- update the natural language explanation to reference new multipliers
4. **Action detail page** -- the "Score Intelligence" section still shows "v5.1-L96" label, should update to v5.2
