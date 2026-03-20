# Next Iterations Plan: What More Can We Build
**Date:** 2026-03-20
**Status:** Strategic backlog -- prioritized by "What's Next?" loop closure

---

## Current State Audit

### What Exists (Built)

| Area | Status | Key Files |
|------|--------|-----------|
| **App Shell** | Shipped | `AppShell.tsx`, `Sidebar.tsx`, `BottomNav.tsx`, `TopBar.tsx`, `MobileTopBar.tsx` |
| **Command Palette** | Shipped | `CommandPalette.tsx` -- hybrid search (vector + text), recent searches, keyboard nav |
| **Home Dashboard** | Shipped | `page.tsx` -- QuickStatsBar, PriorityActionsStrip, ThesisMomentum, PortfolioHealthOverview, RecentActivityFeed |
| **Actions Page** | Shipped | `actions/page.tsx` -- bucket summary, filters, list + triage toggle |
| **Triage Stack** | Shipped | `TriageStack.tsx` (37KB) -- swipe gestures, keyboard shortcuts (a/d/s/j/k/z/?/v), undo toast, card expand, progress bar, completion state, scoring bars, adversarial perspectives |
| **Action Detail** | Shipped | `actions/[id]/page.tsx` -- full detail + triage controls |
| **Thesis Grid** | Shipped | `thesis/page.tsx` -- conviction gauges, evidence bars, momentum sort, bucket tags, pending action badges |
| **Thesis Detail** | Shipped | `thesis/[id]/page.tsx` (1290 lines) -- conviction gauge with direction indicator, evidence timeline from intelligence layer, bull/bear toggle, key questions with open/answered split, action suggestions (RPC), related companies (vector similarity), adversarial analysis with lens triads + polarity pairs, connected digests/actions |
| **Portfolio Page** | Shipped | `portfolio/page.tsx` -- health bar, status breakdown, company list with client-side filters |
| **Portfolio Detail** | Shipped | `portfolio/[id]/page.tsx` -- company detail with linked founders, actions, thesis |
| **Digest Pages** | Shipped | `/d/[slug]` -- full digest rendering with linked actions |
| **Search API** | Shipped | `api/search/route.ts` + `api/search/related/route.ts` -- hybrid search RPC + text fallback |
| **Intelligence Queries** | Shipped | `queries.ts` -- action scores, thesis relevance, bucket routing, related companies, thesis evidence, action suggestions (all via Supabase RPC) |
| **PWA Manifest** | Shipped | `manifest.json` -- standalone, start_url=/actions, icons referenced |
| **Pull-to-Refresh** | Shipped | `PullToRefreshIndicator.tsx` + `usePullToRefresh.ts` |
| **Keyboard System** | Shipped | `useTriageKeyboard.ts` -- context-aware shortcuts for triage mode |

### What the Design Docs Specified but Was NOT Built

| Feature | Design Doc Source | Status |
|---------|-------------------|--------|
| **Keyboard Shortcut Help Dialog** (`?` overlay) | Product Design sec 4.2, shadcn sec 4.1 | NOT BUILT -- `?` toggles card expand in triage, no global shortcut help |
| **Keyboard Hint Bar** (desktop, bottom of viewport) | Product Design sec 1.2 | NOT BUILT -- no persistent hint bar showing context shortcuts |
| **Card/List Dense View Toggle** | Product Design sec 1.3-1.4, sec 4 | PARTIAL -- toggle exists but list mode is basic, no sort headers or side panel |
| **List Mode: Sort Column Headers** | Product Design sec 1.3 | NOT BUILT -- no clickable sort by score, priority, time, type |
| **List Mode: Side Panel Detail** (desktop) | Product Design sec 4 | NOT BUILT -- clicking list row navigates to /actions/[id], no slide-in panel |
| **Batch Selection + Floating Action Bar** | Product Design sec 1.3 | NOT BUILT -- no checkbox multi-select or batch accept/dismiss |
| **Activity Feed Page** (`/feed`) | Product Design sec 4.3 | NOT BUILT -- RecentActivityFeed exists on home, no dedicated `/feed` route |
| **People/Network View** (`/portfolio/people`) | Product Design sec 3.3 | NOT BUILT -- no people page, network table queried for company founders only |
| **Thesis Quick Evidence Capture** | Product Design sec 2.3 | NOT BUILT -- no "Add evidence" form on thesis detail |
| **Thesis Evidence Unified/Split Toggle** | Product Design sec 2.3 | PARTIAL -- ThesisDetailClient has bull/bear toggle, but not unified chronological vs split toggle |
| **Devil's Advocate Toggle** (`b` key) | Product Design sec 2.3 | PARTIAL -- adversarial analysis rendered inline, no toggle/panel mechanism |
| **Conviction History Sparkline** | Product Design sec 2.3 | NOT BUILT -- no SVG sparkline of conviction changes over time |
| **Service Worker / Offline Caching** | Product Design sec 5.1 | NOT BUILT -- manifest exists, no SW registration |
| **PWA Icons** | Product Design sec 5.1 | REFERENCED but likely missing (`/icon-192.png`, `/icon-512.png` not verified) |
| **Haptic Feedback** | Product Design sec 6.3 | NOT BUILT |
| **Reduced Motion Support** | Product Design sec 6.2 | NOT BUILT -- no `prefers-reduced-motion` media queries |
| **Relationship Graph** (v2) | Product Design sec 3.5 | NOT BUILT -- explicitly marked v2 |
| **Notification Center** (v2) | Product Design sec 4.4 | NOT BUILT -- explicitly marked v2 |
| **Sonner Toast Integration** | shadcn composition plan | NOT BUILT -- custom UndoToast instead of Sonner |
| **shadcn Component Migration** | shadcn composition plan | NOT STARTED -- all components are hand-built |

---

## Prioritized Backlog

### P0 -- This Session: Close the "What's Next?" Loop

These are the features that make the triage flow production-ready and close the feedback loop so the system starts learning from Aakash's decisions.

---

#### P0-1: Keyboard Shortcut Help Dialog
**What:** Global `?` shortcut opens a modal showing all available keyboard shortcuts, grouped by context (Global, Triage, Thesis, Navigation). Uses the design from the shadcn composition plan -- a Dialog with ShortcutRow components showing key badges.
**Why:** Without discoverability, the keyboard system is invisible. The design doc specifies this as the primary discovery mechanism. Currently `?` is used for card expand in triage -- need to move help to `Shift+?` or a dedicated `?` button in the top bar.
**What builds it:** Frontend agent. Pure UI component, no backend.
**Complexity:** XS (1-2 hours). Static content, simple Dialog component.
**Files:** New `KeyboardShortcutHelp.tsx`, modify `AppShell.tsx` to register global `?` listener.

---

#### P0-2: Keyboard Hint Bar (Desktop)
**What:** Fixed bar at the bottom of the viewport (40px), glass-morphism background, showing contextual shortcut hints. Content changes based on current page context: triage card mode shows `a accept d dismiss s defer ? detail j/k navigate z undo`, list mode shows `Space select Shift+A accept all v card view`, etc.
**Why:** This is the "always visible" complement to the help dialog. Product design doc specifies it as the primary affordance for keyboard users. Without it, the app feels like a website, not a tool.
**What builds it:** Frontend agent. Needs a simple context provider to track current page/mode.
**Complexity:** S (2-3 hours). Component + context wiring.
**Files:** New `KeyboardHintBar.tsx`, new `KeyboardContext.tsx` provider, modify `AppShell.tsx`.

---

#### P0-3: Batch Selection + Floating Action Bar (List Mode)
**What:** In list mode, each action card gets a checkbox. Selecting one or more reveals a floating action bar at the bottom: "N selected [Accept All] [Dismiss All] [Clear]". Keyboard: `Space` toggles selection, `Shift+A` batch accept, `Shift+D` batch dismiss.
**Why:** The card-by-card triage is great for focused review, but sometimes Aakash wants to scan 20 low-score actions and batch-dismiss them. The design doc calls this "the batch processing use case." Without it, dismissing 15 low-score actions takes 15 individual swipes.
**What builds it:** Frontend agent. Needs client-side selection state + batch server action.
**Complexity:** M (3-5 hours). Selection state, floating bar animation, batch triage server action.
**Files:** Modify `ActionListClient.tsx` and `ActionsPageClient.tsx`, new `BatchActionBar.tsx`, modify `triage.ts` to add `batchTriageActions()`.

---

#### P0-4: Action Outcome Rating (Gold/Helpful/Unknown)
**What:** After an action is Accepted, show a lightweight rating UI (3 buttons: Gold star, Helpful check, Skip). This feeds the `action_outcomes` preference store which calibrates ENIAC's scoring model over time.
**Why:** This is THE compounding mechanism. Without outcome data, the scoring model never improves. The ENIAC APM brief explicitly calls out "Good WebFront experience: Outcome rating is frictionless (one tap)." The `action_outcomes` table exists but has no writer.
**What builds it:** Frontend agent + backend (server action). Small UI, one new server action.
**Complexity:** S (2-3 hours). Three buttons + `rateOutcome()` server action writing to `action_outcomes`.
**Files:** Modify `ActionDetailTriage.tsx` to show rating after accept, new `rateOutcome()` in `triage.ts`.

---

#### P0-5: List Mode Sort Headers
**What:** In list view, the column header row becomes clickable sort controls. Sort by: Score (desc default), Priority, Time (newest/oldest), Type. Visual indicator for active sort column + direction.
**Why:** Scanning 100+ actions in a flat list is useless without sort controls. The design doc specifies this. Currently the list is always sorted by relevance_score desc with no user control.
**What builds it:** Frontend agent. Client-side sort on already-fetched data.
**Complexity:** S (1-2 hours). Sort state + array sort functions.
**Files:** Modify `ActionListClient.tsx` or `ActionsBucketList.tsx`, modify `ActionFilterBar.tsx`.

---

### P1 -- Next Session: Deepen Intelligence

These features leverage the IRGI infrastructure (vector search, 8,000+ embeddings, 6 intelligence functions) to surface insights that a flat list/card UI cannot.

---

#### P1-1: People/Network View (`/portfolio/people`)
**What:** New page showing the 3,339 network contacts. Card grid with initials avatar, name, role/company, relationship strength badge, last activity date, thesis connections as violet pills. Search + filter by company, role, relationship tier. Click opens a person detail panel.
**Why:** 3,339 embedded network rows are sitting in Supabase doing nothing for the UI. The Network DB fuels Bucket 3 (DeVC Collective). Without a people view, this entire priority bucket is invisible. The design doc specifies this at `/portfolio/people`.
**What builds it:** Frontend agent (page + components) + backend (query functions already partially exist: `fetchCompanyFounders` queries `network` table).
**Complexity:** M (4-6 hours). New page, person card component, search, filters. Data queries are straightforward SELECT.
**Files:** New `portfolio/people/page.tsx`, new `PersonCard.tsx`, new `fetchNetworkContacts()` in `queries.ts`.

---

#### P1-2: "People You Should Meet" Recommendations
**What:** On the home dashboard and on thesis detail pages, show a "Suggested Contacts" section. Uses vector similarity: given a thesis thread's embedding, find the top 5 most similar people from the `network` table. Display as person cards with similarity scores and reasoning ("Connected via AI Agents thesis -- similar to 3 portfolio founders").
**Why:** This is the "intelligence layer" promise: the system cross-references 3,339 people against 6 thesis threads and surfaces who matters. Currently this intelligence is trapped in embeddings. An `find_related_people` RPC function (or the existing hybrid_search targeting network table) can power this.
**What builds it:** Backend agent (new RPC function or Edge Function) + frontend agent (component).
**Complexity:** M (3-5 hours). New RPC `find_related_people(p_query_text, p_limit)` + frontend component.
**Files:** New Supabase migration for RPC, new `SuggestedContacts.tsx`, modify thesis detail page and home page.

---

#### P1-3: Thesis Quick Evidence Capture
**What:** At the top of the thesis evidence timeline, a collapsed "Add evidence" input. Click to expand: text area, direction selector (FOR/AGAINST/MIXED), strength selector (IDS notation: ++/+/+?/?/-), source text input, Save button. Writes to `thesis_threads.evidence_for` or `evidence_against` via a server action.
**Why:** The thesis page is currently read-only. Aakash sees evidence in the timeline but can't capture new evidence without going to Notion or asking an agent. The design doc specifies this as the primary thesis interaction. Even an MVP that appends to the text field is valuable.
**What builds it:** Frontend agent (form component) + backend (server action to append evidence).
**Complexity:** S (2-3 hours). Form UI, server action to UPDATE thesis_threads SET evidence_for = evidence_for || new_text.
**Files:** New `AddEvidenceForm.tsx`, new `addEvidence()` server action, modify thesis detail page.

---

#### P1-4: Sector Heatmap / Companies by Sector View
**What:** On the portfolio page (or a new `/portfolio/sectors` tab), show companies grouped by sector with color-coded health indicators. Each sector row shows: sector name, company count, health distribution bar, average score. Click to expand and see individual companies.
**Why:** 4,635 companies are in Supabase. A flat list is unusable at that scale. Sector grouping provides the first useful aggregation view. This turns "we have data" into "we have insight."
**What builds it:** Frontend agent + backend (a simple GROUP BY query on companies table by sector).
**Complexity:** S (2-3 hours). Aggregation query + collapsible sector rows.
**Files:** Modify `portfolio/page.tsx` to add sector tab, new `SectorHeatmap.tsx`, new `fetchCompaniesBySector()` in `queries.ts`.

---

#### P1-5: Conviction Trend Sparkline
**What:** On thesis grid cards and thesis detail page, render a tiny SVG sparkline (80x20px) showing conviction level changes over time. Data source: the evidence timeline's timestamps + sentiment direction gives a proxy for conviction movement.
**Why:** The design doc specifies this. Currently conviction is a single static label. The sparkline shows whether a thesis is gaining or losing momentum -- critical for the "Evolving Fast" signal.
**What builds it:** Frontend agent. Pure SVG component, data already available from evidence timeline.
**Complexity:** S (2-3 hours). SVG polyline from evidence timestamp + sentiment data.
**Files:** New `ConvictionSparkline.tsx`, modify thesis grid and detail pages.

---

#### P1-6: Content Agent Reprocessing Strategy
**What:** A plan (not a code feature) for reprocessing the existing 22 digests + 115 actions through the new intelligence infrastructure. The reprocessing would:
1. Re-embed all 22 digests with the current Voyage AI model (ensures embedding consistency)
2. Re-score all 115 actions using the `score_action_thesis_relevance` and `route_action_to_bucket` RPCs
3. Compare new scores vs old scores and flag significant deltas
4. Generate a "reprocessing report" showing what changed

**Why:** The existing 22 digests and 115 actions were generated WITHOUT the intelligence infra (no vector search, no bucket routing, no thesis relevance scoring). The new RPCs and functions would produce different (better) bucket assignments and thesis connections. This is a one-time cleanup that aligns historical data with the current system.
**What builds it:** Backend agent (Python script on droplet or SQL migration). Not a WebFront feature.
**Complexity:** M (3-5 hours). Script to iterate through existing records and call RPCs.
**Files:** New `scripts/reprocess_intelligence.py` or SQL migration.

---

#### P1-7: Deal Flow Funnel Analytics
**What:** A visual funnel showing how actions flow: Proposed -> Accepted/Dismissed -> Done/Rated. Show conversion rates at each step. Optionally broken down by bucket. Simple bar chart or funnel diagram on the home dashboard or a dedicated analytics page.
**Why:** Without funnel metrics, you can't tell if the system is producing valuable actions. "50% acceptance rate" vs "10% acceptance rate" tells you whether ENIAC's scoring model is calibrated. This is the meta-intelligence about the system itself.
**What builds it:** Frontend agent. Aggregation query on actions_queue by status.
**Complexity:** S (2-3 hours). Status distribution query + simple SVG funnel visualization.
**Files:** New `FunnelAnalytics.tsx`, new `fetchFunnelStats()` in `queries.ts`, add to home page.

---

### P2 -- Later: Nice-to-Haves

These improve polish, performance, and power-user features. Not decision-driving.

---

#### P2-1: Service Worker + Offline Caching
**What:** Register a service worker. Cache strategy: network-first for data (actions, thesis), cache-first for static assets. Offline fallback page: "You're offline. Last synced [timestamp]." Show cached action count.
**Why:** PWA installability requires more than just a manifest -- the SW is what makes it feel native. But Aakash is rarely offline (always on phone/WiFi), so this is a polish item, not a blocker.
**What builds it:** Frontend agent. Service worker registration + Next.js SW integration.
**Complexity:** M (3-5 hours). SW code, cache management, offline page.
**Files:** New `public/sw.js` or use next-pwa, modify `layout.tsx`.

---

#### P2-2: List Mode Side Panel (Desktop)
**What:** On desktop in list mode, clicking an action opens a right-side slide-in panel (Sheet pattern) with the full action detail, without navigating away from the list. J/K keys move selection and update the panel. This is the Linear-inspired split view.
**Why:** Full-page navigation for action detail breaks the triage flow on desktop. A slide-in panel lets you scan the list, drill into details, and triage without losing list context. Marked P2 because the card triage stack handles the primary use case already.
**What builds it:** Frontend agent. Sheet component + keyboard navigation wiring.
**Complexity:** M (4-6 hours). Panel component, list-panel state sync, keyboard navigation.
**Files:** New `ActionSidePanel.tsx`, modify `ActionsPageClient.tsx`.

---

#### P2-3: Activity Feed Dedicated Page (`/feed`)
**What:** New route at `/feed` with a full activity timeline. Group events by day. Each event: color dot by type, summary text, detail text, relative time. Data source: derived from changes to actions_queue, thesis_threads, and content_digests tables by comparing timestamps.
**Why:** The home dashboard has RecentActivityFeed showing 5 items. A dedicated feed page shows the full system activity. This is the "living system" proof -- the feed shows ENIAC is working even when Aakash isn't actively triaging. Marked P2 because the home feed covers the 80% case.
**What builds it:** Frontend agent. Page + server-side aggregation.
**Complexity:** M (3-4 hours). Page layout, day grouping, timestamp comparison logic.
**Files:** New `feed/page.tsx`, new `fetchActivityFeed()` in `queries.ts`.

---

#### P2-4: Co-Investor Analysis
**What:** For portfolio companies, show which other investors co-invested. Data source: companies/portfolio table investor fields. Aggregate across portfolio to show "Investor X co-invested in 4 of your companies" patterns. Visualize as a simple table or network mini-graph.
**Why:** Co-investor patterns reveal relationship leverage ("You share 4 cap tables with Sequoia, but only met with their partner once"). Requires Companies DB investor fields to be populated, which they may not be yet.
**What builds it:** Backend (aggregation query) + frontend (table/visualization).
**Complexity:** M (4-6 hours). Depends on investor data availability.
**Files:** New `CoInvestorAnalysis.tsx`, new query functions.

---

#### P2-5: Competitive Landscape Mapping
**What:** For each thesis thread, show a 2x2 or cluster visualization of related companies by sector/stage. Uses vector similarity between companies within the same thesis connection. Helps identify white space and overlaps.
**Why:** With 4,635 embedded companies, the vector space encodes competitive proximity. Surfacing this visually answers "who else is in this space?" without manual research. Marked P2 because the related companies section on thesis detail partially covers this.
**What builds it:** Backend (cluster computation) + frontend (d3 or simple CSS grid).
**Complexity:** L (6-8 hours). Cluster algorithm + visualization.
**Files:** New visualization component, new RPC for company clustering.

---

#### P2-6: Automated Daily Digest Email
**What:** A scheduled function that runs daily at 7am. Summarizes: N new actions proposed since yesterday (top 3 by score), any thesis conviction changes, pipeline health stats. Sends via Resend or similar to Aakash's email.
**Why:** Reduces the need to open the app proactively. The system comes to Aakash instead of waiting for him to check. Marked P2 because the PWA + mobile triage is the primary surface, and email adds a secondary channel.
**What builds it:** Backend agent (Supabase Edge Function or cron on droplet). No frontend.
**Complexity:** M (3-5 hours). Aggregation query + email template + scheduling.
**Files:** New Edge Function or cron script, email template.

---

#### P2-7: Thesis Health Alerts
**What:** When a thesis thread shows a conviction drop signal (more AGAINST than FOR evidence in the last 14 days, or no new evidence in 30 days for an Active thread), surface a warning banner on the thesis page and optionally push a notification.
**Why:** Conviction decay is invisible without alerts. An Active thesis that hasn't received evidence in a month might need attention or should be moved to Exploring/Parked. This is the "system enforces its own maintenance" principle.
**What builds it:** Backend (detection query) + frontend (banner component).
**Complexity:** S (2-3 hours). SQL query for decay detection, conditional banner.
**Files:** New `ThesisHealthAlert.tsx`, new `detectThesisDecay()` query.

---

#### P2-8: Reduced Motion + Haptic Feedback
**What:** Wrap all animations in `@media (prefers-reduced-motion: reduce)` -- disable card swipe physics, scoring bar animations, conviction gauge build. Add `navigator.vibrate` calls on triage decisions (accept: 10ms pulse, dismiss: 10-30-10ms double pulse).
**Why:** Accessibility compliance (WCAG 2.2 AA). The design doc explicitly requires this. Haptic feedback is a nice touch for mobile triage.
**What builds it:** Frontend agent. CSS additions + small JS utility.
**Complexity:** XS (1-2 hours). CSS media queries + vibrate utility function.
**Files:** Modify `globals.css`, new `haptic.ts` utility.

---

#### P2-9: Supabase Realtime for Live Updates
**What:** Subscribe to `actions_queue` INSERT events via Supabase Realtime. When a new action is proposed by ENIAC (pipeline running on droplet), the WebFront shows a "N new actions" toast or badge update without requiring a page refresh.
**Why:** Currently the pipeline runs every 5 minutes, but Aakash has to refresh to see new actions. Realtime subscription makes the system feel alive. Marked P2 because pull-to-refresh works and the content pipeline frequency is low enough.
**What builds it:** Frontend agent. Supabase client-side realtime subscription.
**Complexity:** S (2-3 hours). Realtime channel setup, badge update logic, toast notification.
**Files:** New `useRealtimeActions.ts` hook, modify `AppShell.tsx` for badge updates.

---

#### P2-10: ISR for Digest Pages
**What:** Convert `/d/[slug]` pages from SSG (current) to ISR with a 60-second revalidation. This means digest pages are statically generated but re-validate periodically, so new digests published by the pipeline appear without a full redeploy.
**Why:** Currently digest pages are rebuilt on every deploy. ISR would allow content to update between deploys. Marked P2 because the pipeline triggers a git push + Vercel deploy anyway, so the practical gap is small (~15 seconds).
**What builds it:** Frontend agent. Configuration change in page route.
**Complexity:** XS (30 minutes). Add `revalidate` export to digest page.
**Files:** Modify `d/[slug]/page.tsx`.

---

#### P2-11: Network Graph Visualization (v2)
**What:** Force-directed graph using d3-force or @visx/network. Nodes: Companies (cyan), People (violet), Thesis (amber). Edges: weighted by relationship strength (vector similarity). Click node opens entity detail panel. Zoom/pan with touch and mouse. Filter by thesis thread.
**Why:** The ultimate "intelligence made visible" feature. With 4,635 companies + 3,339 people + 6 thesis threads, the network graph reveals clusters and relationships invisible in list views. Marked P2/v2 because it's high complexity and the list views cover most use cases.
**What builds it:** Frontend agent (d3) + backend (graph data query).
**Complexity:** L-XL (8-16 hours). Force simulation, node rendering, interaction handling, data preparation.
**Files:** New `portfolio/graph/page.tsx`, new graph components, new RPC for edge data.

---

#### P2-12: shadcn Component Migration
**What:** Incrementally replace hand-built UI components with shadcn/ui equivalents. Priority order: Badge (replace hand-styled spans), Card (standardize containers), Sonner (replace custom UndoToast), Skeleton (standardize loading states), Tooltip (add to score explanations), Sheet (for side panels).
**Why:** The shadcn composition plan was written but never executed. The current hand-built components work but don't benefit from the shadcn ecosystem (consistent theming, accessibility primitives, future updates). This is a quality-of-life improvement, not a feature gap.
**What builds it:** Frontend agent. Incremental replacement, one component type at a time.
**Complexity:** M-L total (1-2 hours per component type, 6 priority types = 6-12 hours total). Should be done across multiple sessions.
**Files:** `npx shadcn@latest init` + `add` commands, then modify existing components.

---

## Caching Strategy Recommendation

| Layer | Strategy | Rationale |
|-------|----------|-----------|
| **Static assets** | Immutable cache (Vercel default) | CSS, JS, fonts, images don't change between deploys |
| **Digest pages** | ISR with 60s revalidation (P2-10) | Content changes infrequently, stale-while-revalidate is fine |
| **Actions/Thesis data** | `force-dynamic` (current) + client prefetch | Triage decisions must be fresh; prefetch next 3 cards for perceived speed |
| **Search API** | No cache | Query-dependent, low latency already (31ms to Supabase Mumbai) |
| **Intelligence RPCs** | Cache with 5-minute TTL | Thesis relevance and bucket routing don't change frequently; memoize on client |
| **Home dashboard stats** | 30-second revalidation | Stats change slowly; ISR-like pattern using `unstable_cache` or `revalidatePath` |

---

## Build Order Rationale

**P0 items close the feedback loop.** Without outcome rating (P0-4), the system never learns. Without batch operations (P0-3), list mode is incomplete. Without shortcut discoverability (P0-1, P0-2), the keyboard system is invisible. These are the gap between "website" and "product."

**P1 items deepen intelligence.** The infrastructure exists (8,000+ embeddings, 6 RPCs, vector search) but the UI only uses a fraction of it. People view (P1-1) and recommendations (P1-2) activate the Network DB. Evidence capture (P1-3) makes the thesis system bidirectional. Reprocessing (P1-6) aligns historical data with the current system. These turn "we have data" into "we have insight."

**P2 items are polish and power features.** Each one improves the experience but none are decision-driving. They should be picked up opportunistically when capacity exists or when a P0/P1 item naturally leads into them (e.g., building the side panel while working on list mode).

---

## Estimated Session Plan

| Session | Items | Total Effort |
|---------|-------|-------------|
| **This session** | P0-1, P0-2, P0-4, P0-5 | ~8 hours |
| **Next session** | P0-3, P1-1, P1-3, P1-5 | ~12 hours |
| **Session +2** | P1-2, P1-4, P1-7, P2-7 | ~10 hours |
| **Session +3** | P1-6, P2-1, P2-3, P2-8 | ~10 hours |
| **Ongoing** | P2-2, P2-9, P2-10, P2-12 | Incremental |
| **Future** | P2-4, P2-5, P2-6, P2-11 | When capacity exists |
