# M1 WebFront Agent Build — 2026-03-21

## Loop Summary

**Commit:** `d4238d7` — M1 v7
**Deployed:** Yes (git push → Vercel auto-deploy)

## Feedback Processed

| ID | Type | Page | Issue | Resolution |
|----|------|------|-------|------------|
| 11 | UX | `/` (Home) | Portfolio health section shows companies with prep buttons for cos not meeting. Wants P0-action-driven list. | Filtered attention list to only P0 actions, overdue obligations, or Red health. Added inline P0 action text per company. |
| 15 | Bug | `/portfolio/52` | "Clicking deep research does nothing" | Research section now links to search page. Duplicate section hidden when intelligence profile covers it. |
| 12 | Bug | `/portfolio/52` | "Ownership number is wrong" | Verified: code is correct (`ownership_pct * 100`). DB stores 0.01 = 1.00%. This is a data accuracy issue, not a display bug. |
| 13-14 | Bug | `/portfolio/52` | Founder name click behavior confusion | Verified: links correctly go to `/network/{id}`. Founders resolve via `led_by_ids`. No code bug found. |

## Changes Made

### 1. Home Page — Attention List Progressive Disclosure
**File:** `src/components/home/PortfolioHealthOverview.tsx`
- Added `AttentionAction` and `AttentionObligation` types to `CompanyAttention` interface
- Each attention card now shows inline P0 action text (line-clamped to 2 lines)
- If no P0 action, shows top overdue obligation with days overdue and person name
- Users can now see *what* the action is without clicking through

### 2. Home Page — Attention List Filtering
**File:** `src/app/page.tsx`
- Cindy RPC returns 70 companies. Previously took top 7 by score (many generic "Needs attention" with 0 actions).
- Now filters to only companies with: P0 actions > 0, overdue obligations > 0, or Red health.
- Result: ~20 companies qualify (vs 70), top 7 shown are all genuinely actionable.

### 3. Portfolio Detail — Research Links Fixed
**File:** `src/app/portfolio/[id]/page.tsx`
- Section F ("Deep Research"): changed from dead-end "Available in AI CoS CLI" to clickable link to `/search?q={company} research`
- Section F now hidden when IntelligenceProfileSection already displays research_file (avoids duplication)
- Intelligence profile's research_file card also now clickable (links to search)

### 4. Performance — Parallel Fetch Optimization
**File:** `src/app/page.tsx`
- Moved `fetchActions(undefined, { field: "created_at", direction: "desc" })` from sequential waterfall into main `Promise.all`
- All 16 data fetches now run in parallel (was 15 parallel + 1 sequential)
- Eliminates ~100-200ms waterfall on home page load

## Remaining Issues

- **Ownership data accuracy** (feedback #12): The display code is correct but the underlying data for some companies may have wrong `ownership_pct` values in Notion/Supabase. This is a M12 (Data Enrichment) concern.
- **Founder link UX** (feedback #13-14): Links work correctly but the transition to network page may feel jarring. Could add a tooltip or hover preview in a future loop.
- **Attention list could show more signal types**: deal signals, days since interaction, key questions count. Currently only P0 actions and overdue obligations get inline display.

## Next Loop Priorities

1. Test obligation action buttons end-to-end (from `/comms` page)
2. Mobile responsiveness audit at 375px across all pages
3. Bundle size analysis — check for unused imports/heavy dependencies
4. Progressive disclosure on portfolio detail — collapsible sections for long action lists
