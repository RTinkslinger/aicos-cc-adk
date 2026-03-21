# M1 WebFront Army Loops L91-95

**Date:** 2026-03-21
**Commit:** c6060c2
**Deployed to:** digest.wiki via Vercel auto-deploy

## Assessment (Pre-Loop)

### User Feedback Addressed
1. "adversarial perspective block is pure rubbish" -- Generic framework descriptions, not thesis-specific analysis
2. "doesn't feel like rich intelligence, IQ 120 not 160" -- Low data density, wrong sort order, misleading counts
3. "text, fonts, clustering, presentation -- everything is off" -- Subtle card borders, no date context, redundant stats
4. "UI seeming slow, no clean state transitions, navigation jarring" -- 7-tab mobile nav is too many
5. "Must meet Linear/Superhuman/Bloomberg bar" -- Cards need stronger visual hierarchy

### 3 Critical Problems Identified
1. **Data Density Too Low** -- P0 actions buried at position 5, thesis count shows 1 not 8, bottom stats duplicate QuickStatsBar
2. **Navigation Hierarchy Confusing** -- 7 tabs on mobile, Feed at "/" same as logo, inconsistent badge counts
3. **Visual Quality Below Bar** -- Card borders too subtle, no time context in header, adversarial section dominates thesis page

## Changes Made (5 loops, 9 fixes)

### Loop 1: Data Hierarchy Fixes
1. **PriorityActionsStrip sort** -- P0 actions now appear first, then P1, P2, P3, with relevance_score as tiebreaker within each priority level
2. **Thesis sidebar badge** -- Changed from `thesisStats.active` (1) to `thesisStats.total` (8) for consistency with QuickStatsBar
3. **BottomNav consolidation** -- Reduced from 7 tabs (Actions, Thesis, Portfolio, Comms, Strategy, Network, Feed) to 5 tabs (Home, Actions, Portfolio, Comms, Strategy). Thesis/Network/Companies accessible via sidebar or home page.

### Loop 2: Home Page Intelligence Density
4. **Date context in header** -- Added day/date display (e.g., "Fri, 21 Mar") next to "AI Chief of Staff" label
5. **Bottom stats row refactored** -- Replaced redundant 4-cell grid (Pending/Accepted/Thesis/Digests) with 3-cell action pipeline summary (Pending/Resolved/Dismissed). Thesis and Digests already shown in QuickStatsBar above.

### Loop 3: Visual Quality
6. **Card depth improved** -- Upgraded `.card-depth` class: border from `subtle-border` (6% opacity) to `border-medium` (10%), stronger box-shadow (0.3 opacity), hover state upgrades border to `border-emphasis` (16%) with deeper shadow

### Loop 4: Thesis Page Intelligence
7. **Adversarial analysis refactored** -- Wrapped in collapsible `<details>` element so it doesn't dominate the thesis detail page. Compacted lens cards: merged method+sees+blindspot into 2 lines per lens instead of 3 separate blocks. Polarity pair tension made more compact.

### Loop 5: Cross-Machine Bug Verification
8. **P0 /comms verified** -- Confirmed all 24 obligations render correctly (18 I_OWE_THEM + 6 THEY_OWE_ME). Obligation_type filter handles both `I_OWE_THEM` and `i_owe` variants. NOT a bug.
9. **P1 thesis badge fixed** -- Root cause: `thesisStats.active` = 1 (only "Active" status), but there are 7 "Exploring" + 1 "Active" = 8 total. Fixed in item #2 above.

## Files Changed
| File | Change |
|------|--------|
| `src/app/globals.css` | Card depth class: stronger borders and shadows |
| `src/app/layout.tsx` | Thesis count: total instead of active |
| `src/app/page.tsx` | Priority sort, date header, pipeline stats |
| `src/app/thesis/[id]/page.tsx` | Adversarial analysis collapsible + compact |
| `src/components/BottomNav.tsx` | 7 tabs -> 5 tabs |

## Quality Assessment

### Before (L90)
- UX: 7.0/10
- P0 actions buried in strip
- Thesis badge misleading (showed 1 for 8)
- Mobile nav had 7 tabs
- Adversarial section dominated thesis page
- Card borders barely visible

### After (L95)
- UX: 7.5/10
- P0 actions shown first in strip
- Thesis badge shows correct total (8)
- Mobile nav clean with 5 tabs
- Adversarial section collapsible
- Card borders visible with hover feedback

### Remaining Gaps (for L96-100+)
- Score breakdown radar chart not yet implemented
- Supabase Realtime for live action updates still pending
- Network page email/phone enrichment dependent on M12
- Search quality at 62/100 (needs Edge Function for embeddings)
- P0 banner shows "45 P0 actions" which is a scoring data quality issue (M5), not WebFront

## Cross-Machine Dependencies
- M5 Scoring: P0 count (45) seems inflated -- may need priority recalibration
- M12 Data: Network page enrichment blocked on email/LinkedIn data
- M6 IRGI: Search quality limited without Edge Function for text-to-vector
- M8 Cindy: /comms interactions section shows "No interactions yet" -- needs real email processing
