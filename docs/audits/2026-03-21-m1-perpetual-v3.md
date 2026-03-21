# M1 WebFront Perpetual Loop v3 — 2026-03-21

## Loop Summary

5 deploys in this loop. Focus: wire M7 contradictions data into WebFront, mobile responsive fixes, memo dedup, smarter home page filtering, and end-to-end verification of obligation buttons.

## Deploys

| # | Commit | Change | Files |
|---|--------|--------|-------|
| 1 | `fd4310c` | Strategic contradictions section on /strategy | strategy/page.tsx, queries.ts, types.ts |
| 2 | `3ccb143` | Contradictions alert strip on command center home | page.tsx |
| 3 | `775af2b` | Mobile responsive grids at 375px | strategy/page.tsx, page.tsx |
| 4 | `fb1483e` | Deduplicate contradictions from briefing memo | strategy/page.tsx |
| 5 | `2e1202d` | Filter terminal-status companies from attention list | PortfolioHealthOverview.tsx |

## What Was Built

### 1. Strategic Contradictions Section (/strategy)
- New dedicated section between the briefing memo and strategic overview
- Data sourced from `briefing_history.assessment_jsonb.contradictions`
- Shows type badges (INVISIBLE, CONFLICTED, STALE) with color coding
- Summary stats bar: Red count, Yellow count, FMV at risk, decisions to 80%
- All companies clickable -- links to `/portfolio/{id}` via name-to-ID lookup
- Currently 20 contradictions from M7's `format_strategic_briefing v2.0`

### 2. Contradictions Alert on Home Page
- Compact strip below Portfolio Health overview
- Shows count ("20 posture inconsistencies"), FMV at risk, link to /strategy
- Responsive: stacks vertically on mobile, inline on desktop
- Cross-surface intelligence -- contradictions visible without navigating to /strategy

### 3. Mobile Responsive Fixes (375px)
- Portfolio risk tier grid: `grid-cols-4` -> `grid-cols-2 sm:grid-cols-4`
- Contradictions stats grid: same fix
- Home contradictions alert: `flex-row` -> `flex-col sm:flex-row`, hide arrow on mobile

### 4. Memo Deduplication
- Section "1.5 STRATEGIC CONTRADICTIONS" in the briefing memo text is now filtered out during parsing
- Prevents duplicate display since we have the dedicated interactive section above
- Logic: detect `## X.X STRATEGIC CONTRADICTIONS` header, skip all lines until next `## N.` section

### 5. Smarter Home Page Attention Companies
- Filtered out companies with terminal statuses (Capital Return, Exited, Deadpool)
- Within same health tier, prefer companies with active statuses over "NA"
- Previously showed PowerEdge (Capital Return) which doesn't need active management

## Verifications

### Thesis Bias Data (all 8 theses verified)
- All 8 thesis threads have `bias_summary` entries
- `detect_thesis_bias()` RPC returns correct data for all IDs (1-7, 11)
- Thesis detail page renders all flag combinations correctly:
  - confirmation_bias (thesis 11, severity HIGH)
  - possible_bias (thesis 1, 3, severity MEDIUM)
  - source_bias, stale_evidence, thin_evidence, conviction_mismatch all handled
- No rendering gaps

### Obligation Action Buttons (comms page)
- **Code path verified end-to-end** through server action + Supabase schema analysis
- All 4 button flows write correct columns:
  - Dismiss -> `status: "dismissed"`, `fulfilled_method: "user_dismissed"`
  - Fulfill -> `status: "fulfilled"`, `fulfilled_method: method`
  - Reschedule -> `due_date: newDate`, `due_date_source: "user_rescheduled"`, `status: "pending"`
  - Follow-up -> creates action in `actions_queue`, updates obligation `status: "reminded"`
- All columns exist in schema (verified via `information_schema.columns`)
- `revalidatePath("/comms")` called after each action for page refresh

### Live Site Verification
- /strategy: Contradictions section renders with 20 items, all linked to portfolio pages
- /: Contradictions alert strip shows "20 posture inconsistencies, $3.2M at risk"
- All portfolio links resolve correctly (BiteSpeed=35, YOYO=161, etc.)

## New Queries Added
- `fetchStrategicContradictions()` — reads `briefing_history.assessment_jsonb`
- `lookupPortfolioIdsByName()` — resolves company names to portfolio IDs

## New Types Added
- `StrategicContradiction` — `{ type: string; company: string }`
- `BriefingHistoryRow` — full briefing_history table row type

## What Remains for Next Loop
- Progressive disclosure L2 ("chat with me") — scoped conversational UX per item
- Calendar-linked home page — needs Cindy calendar integration (M8 dependency)
- Portfolio detail page: show contradiction status if this company is in the contradictions list
- Network page evolution — currently functional but thin on intelligence
- Further mobile audit: test ObligationCardClient action buttons at 375px
- Cross-machine sync: wire M12 enrichment data (69/142 rich content) into company detail pages

## Machine Scores
- UX: 7.0 (up from 6.5 — contradictions add real intelligence to strategy page)
- Mobile: 7.5 (grid fixes prevent squeeze at 375px)
- Data wiring: 8.5 (M7 contradictions fully integrated, M5/M12 data available but not yet wired)
- Intelligence density: 7.0 (contradictions surface real portfolio posture issues, not generic data)
