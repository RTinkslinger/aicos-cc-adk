# M1 WebFront Perpetual Loop v5 -- Audit Report

**Date:** 2026-03-21
**Machine:** M1 WebFront
**Loop:** v5 (intelligence wiring loop)
**Status:** Deployed to production

---

## What Was Done

### Loop Focus: Wire Live Intelligence Across All Surfaces

This loop wired 4 backend intelligence RPCs into the frontend, connecting data that existed in Supabase but was invisible to the user.

### Changes Made

#### 1. /strategy -- Wire `latest_briefing()` RPC
- **Before:** Used `format_strategic_briefing()` which generates a new memo on every page load
- **After:** Also fetches `latest_briefing()` from `briefing_history` table -- shows the actual v3.0 briefing stored by M7 Megamind, with correct briefing date
- Shows **FRESH** badge when briefing is from today
- Falls back to `format_strategic_briefing()` if no stored briefing exists
- **Files:** `src/app/strategy/page.tsx`

#### 2. /comms -- Wire `cindy_relationship_momentum()` RPC
- **Before:** Only showed obligations and interactions; no relationship health overview
- **After:** New **Relationship Momentum** section between Cindy Intelligence Overview and obligation stats
- Summary bar: strong count, at-risk count, portfolio alerts
- **Portfolio Founders at Risk** alert card for portfolio people with overdue obligations or stale contact
- People grouped by tier: CRITICAL/WEAK (always visible), ATTENTION (collapsed), HEALTHY/STRONG (collapsed)
- Each person row shows: momentum score, trend arrow, days since contact, interaction count, recommended action from Cindy
- Links to network search for each person
- **Live data:** Mohit Gupta (0.7 CRITICAL), Supan Shah (1.8 CRITICAL), Surabhi Bhandari (2.7 WEAK), 5 portfolio alerts, 12 cooling relationships
- **Files:** `src/app/comms/page.tsx`

#### 3. /portfolio/[id] -- Wire `portfolio_intelligence_report()` RPC
- **Before:** Portfolio detail showed metrics, founders, thesis, actions -- but no intelligence completeness or research intelligence
- **After:** New **Research Intelligence** section between Key Metrics and Founders
- Intelligence completeness bar (0-100%) with color coding
- Staleness badge (green/amber/red based on days since update)
- Depth grade badge (ultra/investigate/scan)
- Strategic score display
- Research file indicator with filename
- Thesis links from entity_connections
- Similar companies (vector similarity top 3)
- Key contacts with links to network search
- Latest action with score
- **Files:** `src/app/portfolio/[id]/page.tsx`

#### 4. /network/[id] -- Wire `cindy_person_intelligence()` RPC (inline)
- **Before:** PersonIntelligencePanel existed on /comms as a slide-in panel, but network detail pages had no Cindy intelligence
- **After:** New **Cindy Intelligence** section at top of network detail page (before company sections)
- EA summary narrative (the key insight about this person)
- Communication score (X/10), trend (warming/cooling/stable), attention level
- Interaction patterns: total count, last 30d, channels, deal signal percentage
- Pattern assessment from Cindy
- Connected entities preview (top 6 with type badges)
- **Files:** `src/app/network/[id]/page.tsx`

### Infrastructure Changes

#### New Types (`src/lib/supabase/types.ts`)
- `LatestBriefingRow` -- briefing_date, briefing_text, assessment_jsonb, created_at
- `RelationshipMomentumPerson` -- full person momentum data
- `RelationshipMomentumResult` -- people array, portfolio_alerts, cooling_relationships, summary
- `PortfolioIntelligenceRow` -- 12-field intelligence report per portfolio company

#### New Query Functions (`src/lib/supabase/queries.ts`)
- `fetchLatestBriefing()` -- calls `latest_briefing()` RPC
- `fetchRelationshipMomentum()` -- calls `cindy_relationship_momentum()` RPC
- `fetchPortfolioIntelligenceReport(portfolioId?)` -- calls `portfolio_intelligence_report()` RPC

---

### 5. Home page -- Fix portfolio health attention list (user feedback)

**User feedback:** "Companies on home page in portfolio health section with prep buttons... not meaningful on glance. Prep would ideally be an action just before a meeting."

- **Before:** Showed Red/Yellow companies with PREP buttons (prep makes no sense without calendar)
- **After:** "Needs Your Attention" list ranked by P0 action count, then Red health, then pending action count
- Cross-references proposed actions with portfolio company names to find which companies have critical actions
- Each row shows: health dot, company name, reason tag (e.g. "2 P0 actions", "Red + actions pending"), action count badge
- Links to /portfolio/[id] detail page
- Removed: CompanyBrief slide-over, PREP buttons, client-side state for brief panel
- **Files:** `src/components/home/PortfolioHealthOverview.tsx`, `src/app/page.tsx`

---

## Deployments

### Deploy 1: Intelligence wiring
- **Commit:** `e535a57` on main
- **Deploy ID:** `dpl_AYL6wHt1JAdwHDqfHC1jZLyFhBf4`
- **Status:** READY

### Deploy 2: Feedback fix (portfolio attention list)
- **Commit:** `07cef1f` on main
- **Deploy ID:** `dpl_7vVmXxt9EWaKkBuv1j8ZoEh7hFbF`
- **Status:** READY

Both builds passed clean. Live on digest.wiki.

## Architecture Notes

All 4 RPCs existed in Supabase already -- this loop was purely frontend wiring. No schema changes, no new migrations, no new RPC functions created. The intelligence was being computed but invisible.

**Data flow:**
```
Supabase RPCs (already exist)
  latest_briefing()              -> /strategy page
  cindy_relationship_momentum()  -> /comms page
  portfolio_intelligence_report() -> /portfolio/[id] detail
  cindy_person_intelligence()    -> /network/[id] detail (was only on /comms panel)
```

## What's Next (Loop v6 candidates)

1. **Mobile polish at 375px** -- verify all new sections render correctly on mobile
2. **Wire relationship momentum into home page** -- show CRITICAL people in home dashboard
3. **Portfolio detail: wire company_intelligence_profile()** -- deeper per-company intelligence
4. **Cross-surface linking** -- momentum people on /comms should link to their /network/[id] pages
5. **Search: verify cross-surface bias after M6 fix** -- test /search after M6 patches
