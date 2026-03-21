# M1 WebFront Perpetual Loop v2 Audit

**Date:** 2026-03-21
**Loop Type:** Product Leadership > Research > Build > Review > Deploy
**Deploys in this loop:** 3

---

## What Was Shipped

### Deploy 1: Narrative Score + Person Intelligence Panel
**Commit:** `949bf0e`

1. **ExplainScoreModal: Narrative-first score explanation**
   - Replaced the technical factor-bars-and-multipliers view with a narrative primary view
   - The `narrative_score_explanation()` RPC returns a rich story: portfolio context (ownership %, entry cheque, follow-on decision, health), person context (priority, role), thesis connections (conviction, momentum), obligation pressure, interaction recency, agent feedback
   - Technical breakdown (factor bars, multipliers, formula) moved to collapsible L2 section
   - Narrative sections are styled with semantic colors: green for "why it ranks high", amber for "concerns", violet for "agent perspective"

2. **PersonIntelligencePanel: Full Cindy intelligence on /comms**
   - New slide-in panel triggered by "View intel" button on every obligation card
   - Calls `cindy_person_intelligence()` RPC which aggregates 9 data sources: communication profile, interaction patterns, obligations, interaction timeline, entity connections, relationship graph, related actions, companies context, benchmarks
   - Panel shows: EA summary narrative, communication score + trend + attention level, contact info, obligation balance, pattern assessment, entity connections with strength bars, interaction history with intelligence scores, related actions, sentiment signals
   - Mobile: bottom sheet. Desktop: right-side panel (480px wide)

3. **New query/type infrastructure**
   - `NarrativeScoreResult` and `CindyPersonIntelligence` TypeScript interfaces
   - `fetchNarrativeScoreExplanation()` and `fetchCindyPersonIntelligence()` query functions
   - Server actions: `getNarrativeScoreExplanation()`, `getPersonIntelligence()`, `resolvePersonId()`

### Deploy 2: Worst-Managed Clickable + Mobile Progressive Disclosure
**Commit:** `0ae3c36`

1. **WorstManagedClient: Interactive worst-managed section**
   - "Worst Managed Relationships" section on /comms now has clickable person names
   - Tapping any person opens their full PersonIntelligencePanel
   - Hover feedback on each row

2. **Interaction timeline mobile optimization**
   - Summary text: truncated to 3 lines on mobile (full on desktop) via `line-clamp-3 sm:line-clamp-none`
   - Signal details: collapsed to compact badges (Deal/Relationship/Thesis) on mobile, full DealSignalBadges and RelationshipSignalBadges on desktop
   - Action items: capped at 2 on mobile with "+N more" indicator, full list on desktop

### Deploy 3: Narrative Score on Action Detail Page
**Commit:** `c8b6d61`

1. **Score Intelligence section on action detail page**
   - New "Score Intelligence" section rendered server-side (not lazy-loaded modal)
   - Shows the narrative explanation inline — the story about why this action scores what it does
   - Model version tag and technical metadata (base score, decay factor, age)
   - Loads in parallel with other data via Promise.all — no N+1 queries

---

## What Was Verified

- **Adversarial section on /thesis/[id]:** Confirmed using real `detect_thesis_bias()` RPC data, not templates. Example: "Agentic AI Infrastructure" shows MEDIUM severity with possible_bias at 5.75:1 ratio (23 FOR vs 4 AGAINST)
- **Strategy page N+1:** Confirmed 14 data fetches all in single Promise.all — no waterfall queries
- **Dead companies filtered from home:** Already implemented in previous loop
- **TypeScript:** Zero type errors on full `tsc --noEmit` check
- **Build:** All 3 deploys pass Next.js production build

---

## Architecture Decisions

1. **Narrative as primary, technical as L2:** User feedback was clear — "3/10 intelligence quality" means raw factors aren't useful. The narrative tells a story. Technical breakdown remains accessible for debugging.

2. **Server-side narrative on action detail, client-side on modal:** The action detail page can afford the server-side fetch (loads once). The modal on the actions list page uses a client-side fetch (loads on demand) to avoid fetching narratives for all visible actions.

3. **PersonIntelligencePanel as separate component vs inline:** The panel is reusable — used from ObligationCardClient AND WorstManagedClient. Slide-in panel (not inline) keeps the page flow clean while providing deep intelligence.

4. **resolvePersonId() server action:** The obligation cards have person_name but not person_id. Rather than changing the server-rendered schema, a lightweight lookup resolves name to ID on demand.

---

## What's Next for M1

- Wire `enriched_search()` into the search page (M6 built OR-logic fix)
- /comms interaction timeline: person names should also open intelligence panel
- Home page portfolio section: needs calendar data from M8 Cindy to show upcoming meeting companies
- Performance: consider caching narrative_score_explanation for 5min (it's a heavy RPC with multiple joins)
- The narrative includes raw text like "Concerns: Action is 15 days old — time decay is reducing score. Token/Zero follow-on decision deprioritizes this." — these could be styled as structured callouts like the modal does
