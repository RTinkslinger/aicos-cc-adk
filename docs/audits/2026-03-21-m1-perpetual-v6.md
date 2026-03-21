# M1 WebFront Perpetual Loop v6 Audit
**Date:** 2026-03-21 | **Deploys:** 2 | **Build:** passing

## Changes Shipped

### Deploy 1: Major feature + bug fixes
**Commit:** `e5dfd18` — M1 v6: wire briefing v4.0 (8 sections), fix ownership%, portfolio context, founder links

#### 1. Strategy Briefing v4.0 (8 sections)
- **Parser upgrade:** `parseMemo()` regex extended from `\d+` to `\d+(?:\.\d+)?` pattern with `[.\s]+` separator to handle both integer sections (`## 1. TITLE`) and decimal sections (`## 2.5 TITLE`)
- **New section accents/icons:** Added icons + colors for sections 2.5 (HelpCircle/amber), 5 (Clock/flame), 6 (Users/cyan)
- **Content parser extensions:** Added `alert` type (X prefix lines), `thesismarker` type (!/ ~ prefix), OVERDUE/Key Q:/Score:/Rec: detail formatters
- **Progressive disclosure:** Sections 1-2.5 open by default, 3+ collapsed
- All 7 non-contradictions sections rendering correctly: 1, 2, 2.5, 3, 4, 5, 6

#### 2. Home Page Briefing Summary Card
- New `BriefingSummary` component wired to `fetchLatestBriefing()` RPC
- Shows headline, freshness badge (FRESH when today), metric pills (Red count, Yellow count, decisions, overdue, key questions)
- Top 3 attention items with health tags
- Links to /strategy for full briefing

#### 3. Action Detail Portfolio Context
- Extended `ExplainScoreResult` type with `portfolio_context` field
- Renders company name (linked), health badge, ownership%, entry cheque, stage, outcome category, best case
- Shows boost reasons as pills with total portfolio boost percentage
- Added global percentile badge ("Top N%") to score metadata

#### 4. Ownership % Fix (Global)
- **Root cause:** `ownership_pct` stored as decimal (0.03 = 3%) but displayed raw
- **Fixed in 8 files:** portfolio detail, portfolio list, company detail, network detail, search, command palette, company brief, action detail
- All now show `(value * 100).toFixed(2)%`

#### 5. Portfolio Detail Bug Fixes (4 user feedback items on /portfolio/52)
- **Bug 1:** Ownership now shows `1.00%` instead of `0.01%`
- **Bug 2/3:** Founder cards now wrapped in `<Link>` to `/network/{id}` — clickable with proper routing
- **Bug 4:** Deep research card redesigned — no longer appears clickable, shows "Available in AI CoS CLI" badge

### Deploy 2: Regex hotfix
**Commit:** `81952e6` — fix: briefing section regex

- The `[.\s]+` separator was critical — the original `\s+` pattern failed because section headers like `## 1. NEEDS` have a dot immediately after the number, not whitespace
- Verified with test: all 8 section formats match correctly

## Verification

### Playwright Testing
- **Home page:** BriefingSummary card renders with metrics, attention items, "FRESH" badge
- **Strategy page:** All 7 briefing sections render as collapsible `<details>` elements with proper icons
- **Portfolio /52:** Ownership shows `1.00%`, founders link to `/network/342` and `/network/134`, deep research shows "Available in AI CoS CLI"
- **Action /50:** Portfolio Context section shows Unifize Green health, 3.0% ownership, $300K invested, Cat C SaaS, Best case $150M, +22% score boost, Top 15%
- **Comms page:** All obligation action buttons present (Respond, Make intro, Handle, Send nudge, Still waiting, Received, Reschedule, Not needed)

### User Feedback
- Checked `user_feedback_store` — no new feedback since 11:24
- Previous 4 bugs on /portfolio/52 all addressed

## Files Changed
```
src/app/page.tsx                          — briefing summary + fetchLatestBriefing
src/app/strategy/page.tsx                 — parseMemo regex, 8-section support, content parsers
src/app/actions/[id]/page.tsx             — portfolio context rendering + percentile
src/app/portfolio/[id]/page.tsx           — ownership fix, founder links, deep research
src/app/companies/[id]/page.tsx           — ownership fix
src/app/network/[id]/page.tsx             — ownership fix
src/app/search/SearchPageClient.tsx       — ownership fix
src/components/home/BriefingSummary.tsx    — NEW: briefing summary card
src/components/CommandPalette.tsx          — ownership fix
src/components/CompanyBrief.tsx            — ownership fix
src/components/PortfolioListClient.tsx     — ownership fix
src/lib/supabase/types.ts                 — portfolio_context type extension
```

## Next Loop Priorities
1. Test all new pages at 375px mobile viewport (need browser_resize permission)
2. Evolve weakest pages: companies list could use more intelligence density
3. Wire obligation action buttons to show success feedback with undo capability
4. Consider adding keyboard shortcuts for briefing section navigation
