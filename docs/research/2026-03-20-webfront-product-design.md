# WebFront v4 Product Design: Action Optimizer Dashboard

**Date:** 2026-03-20
**Author:** Product Design Session
**Status:** Design Spec (pre-implementation)

---

## Design Philosophy

Three principles govern every decision in this document:

1. **Density over decoration.** Every pixel either shows data or enables a decision. No hero sections, no marketing copy, no spacer divs. If Bloomberg Terminal is 10 and a landing page is 0, we are building a 7.
2. **Keyboard-first, touch-native.** Desktop users never touch the mouse. Mobile users never tap more than twice to complete a core action. These are not conflicting goals -- they are two input modes for the same interaction model.
3. **Progressive disclosure, not progressive hiding.** The default view shows enough to decide. Detail is one keystroke or tap away. No information is hidden behind "View More" links -- it is collapsed behind disclosure triangles or overlays that expand in-place.

The design language inherits from the existing system: `--color-bg: #08080c`, five accent colors (flame, amber, cyan, violet, green), JetBrains Mono for data, Instrument Serif for headlines, DM Sans for body. Glass-morphism for floating surfaces. Card-depth shadows for layered content.

---

## 1. Action Triage Flow

This is the core product experience. Everything else exists to feed this loop.

### 1.1 User Journey Map

```
Entry: User opens app (PWA home screen or digest.wiki)
  |
  v
[Action Count Badge] -- "7 pending" shown in bottom nav or header
  |
  v
[Triage View] -- Card stack (default) or list (toggle)
  |
  +--> [Card Mode] -- Single action, full context, swipe/keyboard
  |     |
  |     +--> Read action title + priority + thesis tag (0.5s)
  |     +--> Decide: enough info? -- YES --> Accept/Dismiss/Defer
  |     |                          -- NO  --> Expand reasoning (?)
  |     +--> [Expanded] -- AI reasoning, scoring bars, source, related
  |     |     +--> Decide --> Accept/Dismiss/Defer
  |     |     +--> [Undo Toast] -- 5s window, single tap to reverse
  |     +--> Next card auto-advances
  |
  +--> [List Mode] -- Checkbox multi-select, batch operations
        |
        +--> Scan, check items, batch accept/dismiss
        +--> Floating action bar with count + buttons
```

### 1.2 Card Mode -- Wireframe Description

The card stack occupies the full viewport minus the top nav (56px) and bottom nav (mobile, 64px) or keyboard hint bar (desktop, 40px).

#### Card Anatomy (Collapsed -- Default)

```
+------------------------------------------------------------------+
|  [P0]  [Research]  [Proposed]                      Score: 8.2    |
|                                                                   |
|  Investigate Anthropic's enterprise adoption in     [thesis tag]  |
|  banking vertical -- contradicts existing...                      |
|                                                                   |
|  "Agent SDK adoption in enterprise is 3x faster     2h ago       |
|   than expected..."                                               |
|                                                                   |
|  ┌─ Related: AI Agents thesis (3 actions) ──────────────────┐    |
|  └──────────────────────────────────────────────────────────-┘    |
|                                                                   |
|  [ Accept (a) ]  [ Dismiss (d) ]  [ Defer (s) ]                 |
+------------------------------------------------------------------+
```

**Layout rules:**
- Top row: Priority badge (left-colored), action type badge, status badge, score (right-aligned, monospace). All `font-mono text-[10px]`.
- Title: `text-[17px] font-semibold leading-snug`, max 3 lines before truncation. Color: `--color-t1`.
- Thesis tag: Pill badge in violet, positioned after title text or on its own line if wrapping.
- Reasoning preview: First 2 lines of AI reasoning. `text-[14px] text-t2`. Italic to distinguish from action text.
- Context strip: One-line summary of related items. Monospace, muted. Shows thesis name + action count.
- Action buttons: Three equal-width buttons in a row. Min-height 48px (touch target). Positioned at card bottom with 16px padding.
  - Accept: green tint bg, green text, green border
  - Dismiss: neutral bg, t3 text, subtle border
  - Defer: violet tint bg, violet text, violet border
- Card border: 3px left border colored by priority (flame=P0, amber=P1, cyan=P2, violet=P3)
- Card background: `--color-card` with `card-depth` shadow treatment
- Card max-width: 640px, centered. Full-width on mobile with 16px horizontal margin.

#### Card Anatomy (Expanded -- After pressing `?` or tapping expand area)

The card expands in-place (no page navigation). New sections slide in below the reasoning preview with a 200ms ease-out transition.

```
+------------------------------------------------------------------+
|  [collapsed card content above]                                   |
|                                                                   |
|  --- AI REASONING -----------------------------------------------  |
|  Full reasoning text, no truncation. text-[14px] text-t2.       |
|  Can be 3-10 lines.                                              |
|                                                                   |
|  --- SOURCE INTELLIGENCE ----------------------------------------  |
|  Source content with cyan left border. Links to digest if avail.  |
|                                                                   |
|  --- SCORING BREAKDOWN ------------------------------------------  |
|  Bucket Impact         ████████░░  8.0                           |
|  Conviction Change     ██████░░░░  6.0                           |
|  Time Sensitivity      █████████░  9.0                           |
|  Action Novelty        ███████░░░  7.0                           |
|  Effort vs Impact      ████████░░  8.0                           |
|                                                                   |
|  --- ADVERSARIAL PERSPECTIVE ------------------------------------  |
|  [Risk Architect]  [Timing Strategist]  [Network Thinker]        |
|  Brief lens method text for each, in colored cards.              |
|                                                                   |
|  [ Accept (a) ]  [ Dismiss (d) ]  [ Defer (s) ]                 |
+------------------------------------------------------------------+
```

**Expanded sections use `<details>` elements** with custom styling (no browser markers). Each section header is a `font-mono text-[10px] tracking-[1.5px] uppercase` label with a thin horizontal rule.

#### Card Stack Behavior

- Cards are stacked with only the current card fully visible. The next card peeks 8px behind the top card (visible as a darker strip at the bottom), creating depth.
- After triage decision: current card exits with a directional animation:
  - Accept: slides right 100% with opacity fade, 250ms ease-out. Card border pulses green briefly.
  - Dismiss: slides left 100% with opacity fade, 250ms ease-out. Card desaturates during exit.
  - Defer: slides down 60px then fades, 200ms ease-out.
- Next card scales up from 0.97 to 1.0 and moves up, 200ms ease-out.
- When stack is empty: show completion state with stats ("Triaged 7 actions. 4 accepted, 2 dismissed, 1 deferred.") and a link to list view.

#### Progress Indicator

A thin horizontal bar at the very top of the card area. Shows N of M where M = total pending actions. Color: `--color-flame`. Height: 2px. Animates width on each triage decision.

### 1.3 List Mode -- Wireframe Description

Toggled via `v` key (desktop) or a segmented control at top (card | list). List mode shows the existing `ActionListClient` layout but enhanced.

```
+------------------------------------------------------------------+
|  [Card | List]  Filter: [Status v] [Priority v] [Type v]  Q: 7  |
+------------------------------------------------------------------+
|  [ ] P0 | Research | Investigate Anthropic's en...    8.2  2h    |
|  [ ] P1 | Meeting  | Schedule follow-up with...      7.1  1d    |
|  [x] P0 | Thesis   | Update conviction on AI...      8.8  3h    |
|  [x] P1 | Content  | Review new Sequoia report...    6.4  1d    |
|  ...                                                              |
+------------------------------------------------------------------+
|  2 selected    [ Accept All ]  [ Dismiss All ]  [ Clear ]        |
+------------------------------------------------------------------+
```

**Enhancements over current implementation:**
- Denser rows: Single-line per action with truncation. `text-[13px]`. No expanded reasoning in list view.
- Inline score display: Right-aligned monospace number.
- Relative time: Far right column, monospace, muted.
- Row click: Opens card detail (expanded view) as a side panel on desktop or pushes card view on mobile.
- Checkbox column: 44px wide, visible only when any row is in Proposed status.
- Sort column headers: Click to sort by score, priority, time, type.

### 1.4 Interaction Specifications

#### Keyboard Shortcuts (Desktop)

| Key | Action | Context |
|-----|--------|---------|
| `a` | Accept current action | Card mode |
| `d` | Dismiss current action | Card mode |
| `s` | Defer current action (lower priority) | Card mode |
| `?` | Toggle expanded detail | Card mode |
| `j` | Next action (skip without triaging) | Card mode |
| `k` | Previous action (go back) | Card mode |
| `z` or `Ctrl+Z` | Undo last triage decision | Global (within 5s window) |
| `v` | Toggle card/list view | Actions page |
| `f` | Focus filter bar | List mode |
| `Enter` | Open selected action detail | List mode |
| `Space` | Toggle checkbox selection | List mode (with focus on row) |
| `Shift+a` | Accept all selected | List mode (with selection) |
| `Shift+d` | Dismiss all selected | List mode (with selection) |
| `Esc` | Close expanded detail / clear selection | Both modes |

**Keyboard hint bar (desktop only):** Fixed to bottom of viewport, 40px tall. Glass-morphism background. Shows contextual hints:
- Card mode: `a accept  d dismiss  s defer  ? detail  j/k navigate  z undo`
- List mode: `Space select  Shift+A accept all  Shift+D dismiss all  v card view`
- Text: `font-mono text-[10px]`, keys in `px-1.5 py-0.5 rounded bg-elevated` badges.

#### Mobile Gestures

| Gesture | Action | Feedback |
|---------|--------|----------|
| Swipe right (>60px threshold) | Accept | Card tilts 5deg clockwise, green glow on right edge |
| Swipe left (>60px threshold) | Dismiss | Card tilts -5deg counter-clockwise, muted overlay |
| Swipe down (>40px threshold) | Defer | Card shifts down, violet pulse at bottom |
| Tap card body | Expand/collapse detail | Section slide animation |
| Tap action button | Direct triage | Button press animation (scale 0.97) |
| Pull down from top | Refresh actions list | Standard pull-to-refresh spinner |
| Long press | Enter multi-select mode | Haptic feedback (if available) |

**Swipe physics:** The card follows finger position with `transform: translateX()` during drag. Opacity decreases linearly from 1.0 to 0.3 as displacement increases from 0 to threshold. Beyond threshold, the card snaps to exit with spring physics (CSS `transition: transform 200ms cubic-bezier(0.2, 0, 0, 1)`).

**Visual tilt during swipe:** `transform: rotate(Ndeg)` where N = displacement / 40, clamped to [-8, 8] degrees. Creates a natural "flicking" feel.

### 1.5 Undo System

Every triage decision (accept, dismiss, defer) triggers a 5-second undo window.

**Undo toast anatomy:**
```
+--------------------------------------------------+
|  Action accepted    [Undo]    [======---]  3s    |
+--------------------------------------------------+
```

- Position: Fixed bottom, centered horizontally, 16px above bottom nav (mobile) or keyboard hint bar (desktop).
- Background: `rgba(15,15,22,0.97)` with blur backdrop.
- Border: `1px solid rgba(255,87,34,0.3)` (flame accent).
- Content: Status text (mono, 12px, t1) + Undo button (mono, 12px, bold, flame) + countdown progress bar.
- Countdown bar: 2px tall, flame-colored, shrinks from 100% to 0% over 5s with linear animation.
- Stacking: If multiple undos are pending, show only the most recent. Previous pending actions are committed immediately.
- Z-index: 50, above all other floating elements.

**Undo behavior:**
1. On triage decision: optimistic UI update (card exits, next card advances). Start 5s timer.
2. During window: no server call yet. Decision stored in client state.
3. On undo: reverse animation (card slides back in from exit direction). Previous state restored. Timer cleared.
4. On timeout: commit to server via `triageAction()` server action. Toast fades out.
5. On new triage decision while undo is pending: commit previous decision immediately, start new undo window.

### 1.6 State Management

**Card mode state:**
```typescript
interface TriageState {
  actions: ActionRow[];           // Full list of pending actions
  currentIndex: number;           // Index in the filtered list
  expandedDetail: boolean;        // Card expanded state
  viewMode: 'card' | 'list';     // Toggle
  pendingUndo: {                  // Undo window
    actionId: number;
    decision: 'Accepted' | 'Dismissed';
    previousIndex: number;
    timer: ReturnType<typeof setTimeout>;
  } | null;
  triageHistory: Array<{         // For j/k navigation and undo
    actionId: number;
    decision: string;
    timestamp: number;
  }>;
  stats: {                       // Running triage stats for session
    accepted: number;
    dismissed: number;
    deferred: number;
  };
}
```

**Data fetching:**
- Initial load: Server component fetches `fetchActions({ status: 'Proposed' })` sorted by `relevance_score desc`.
- After triage: Client-side optimistic removal from array. Server action fires after undo window.
- Refresh: Pull-to-refresh (mobile) or `r` key (desktop) re-fetches from server.

**Loading states:**
- Initial: Skeleton card with pulsing bars (3 lines of varying width). Same card dimensions.
- Between actions: No loading state -- next card is already rendered behind current.
- After triage commit: No visible loading -- optimistic update handles the gap.
- Error: Toast notification at bottom. "Failed to save decision. Retrying..." with auto-retry after 3s.

**Empty states:**
- No pending actions: Full-viewport centered illustration-free message. "All caught up. 0 actions pending." with stats from this session. Link to "View all actions" (list mode, all statuses).
- Error loading: "Couldn't load actions. Pull to refresh." with retry button.

---

## 2. Thesis Command Center

### 2.1 User Journey Map

```
Entry: /thesis or tap Thesis in bottom nav
  |
  v
[Thesis Grid] -- All threads, sorted by status + conviction
  |
  +--> Tap/click thread
  |
  v
[Thesis Detail] -- Command Center layout
  |
  +--> [Evidence Timeline] -- Left rail (desktop) / top section (mobile)
  |     +--> Scrollable timeline of FOR and AGAINST signals
  |     +--> Each entry: date, signal text, IDS notation, source
  |     +--> Add evidence button at top (quick capture)
  |
  +--> [Conviction Panel] -- Right rail (desktop) / sticky section (mobile)
  |     +--> Gauge visualization
  |     +--> Direction indicator (trending up/down/stable)
  |     +--> Key questions checklist
  |     +--> Devil's advocate toggle
  |
  +--> [Connected Entities] -- Below fold
        +--> Companies, people, actions, digests linked to this thesis
```

### 2.2 Thesis Grid (List Page) -- Enhanced

The current grid is adequate but needs density improvements.

**Changes from current:**
- Add a sort control: `conviction` (default), `updated`, `action count`.
- Add a filter: `Active` / `Exploring` / `All` (default: Active).
- Evidence ratio bar: Below conviction gauge on each card, show a horizontal stacked bar: green portion (FOR) | flame portion (AGAINST). Proportional to evidence counts.
- Pending actions badge: If thesis has pending actions, show a small amber dot badge with count.

### 2.3 Thesis Detail -- Command Center Layout

This is a two-column layout on desktop (evidence timeline left, conviction + questions right) that collapses to single column on mobile.

#### Desktop Layout (>=768px)

```
+------------------------------------------------------------------+
|  <- All Thesis Threads                                            |
|                                                                   |
|  AI Agents Will Transform Enterprise Software         [Active]    |
|  [SaaS Infrastructure] [AI/ML]                                   |
|                                                                   |
|  ┌─────────────────────── CONVICTION ──────────────────────────┐  |
|  │  [New][Evolving][Evolving Fast][Low][Medium][HIGH]          │  |
|  │                                             ^^^^ (current)  │  |
|  │  Direction: +0.3 in last 14d  (trending up arrow)           │  |
|  └─────────────────────────────────────────────────────────────┘  |
|                                                                   |
|  "Enterprise adoption of AI agents is accelerating faster         |
|   than any prior software paradigm shift..."                      |
|                                                                   |
|  ┌── EVIDENCE TIMELINE ──┐  ┌── KEY QUESTIONS ──────────────┐    |
|  │                        │  │                                │    |
|  │  [+ Add Evidence]      │  │  [ ] What's the churn rate    │    |
|  │                        │  │      for agent-first products? │    |
|  │  Mar 18 ++ Agent SDK   │  │                                │    |
|  │  adoption 3x...        │  │  [x] Is there a defensible    │    |
|  │  src: ENIAC pipeline   │  │      moat in agent infra?     │    |
|  │                        │  │      > Yes, via...             │    |
|  │  Mar 15 +? Mixed       │  │                                │    |
|  │  signals on enterprise │  │  [ ] How do agents affect     │    |
|  │  buyer readiness...    │  │      existing SaaS margins?    │    |
|  │                        │  │                                │    |
|  │  Mar 12 - Counter      │  │  [3 open, 1 answered]         │    |
|  │  evidence from legacy  │  │                                │    |
|  │  vendor interviews     │  ├── DEVIL'S ADVOCATE ───────────┤    |
|  │                        │  │                                │    |
|  │  [show 5 more...]      │  │  [Bull Case]  |  [Bear Case]  │    |
|  │                        │  │                                │    |
|  └────────────────────────┘  │  BULL: Agent adoption is      │    |
|                              │  following mobile's curve...   │    |
|  ┌── CONNECTED INTELLIGENCE ─│                                │    |
|  │  Companies: Anthropic,   ││  BEAR: Enterprise procurement │    |
|  │  LangChain, ...          ││  cycles haven't shortened...  │    |
|  │                          │└────────────────────────────────┘    |
|  │  People: [person tags]   │                                     |
|  │  Actions: 5 (2 pending)  │                                     |
|  │  Digests: 8 related      │                                     |
|  └──────────────────────────┘                                     |
+------------------------------------------------------------------+
```

#### Evidence Timeline Detail

The timeline is the primary content column. It replaces the current static evidence FOR/AGAINST split with a unified chronological view.

**Timeline entry anatomy:**
```
+------------------------------------------------------------------+
|  Mar 18  ++                                                       |
|  Agent SDK enterprise adoption exceeds 3x initial forecasts.      |
|  Source: ENIAC Content Pipeline - "The State of AI Agents 2026"   |
+------------------------------------------------------------------+
```

- Date: `font-mono text-[10px]`, muted (`--color-t3`).
- IDS notation: Displayed as a colored badge next to date. `++` in green, `-` in flame, `?` in amber. Uses existing `idsDisplay()` function.
- Signal text: `text-[14px]`, `--color-t2`.
- Source: `font-mono text-[10px]`, `--color-t3`. If from a digest, hyperlinked to `/d/[slug]`.
- Timeline connector: 2px vertical line on the left, colored by evidence direction (green for FOR entries, flame for AGAINST, amber for mixed). Uses existing `.timeline-line` CSS but with conditional coloring.
- Entries sorted chronologically (newest first).

**Unified view vs split view toggle:**
- Default: Unified chronological (all evidence interleaved by date)
- Toggle (`e` key or tap header): Split view (FOR column | AGAINST column side-by-side, as current)
- The toggle is a small `[Unified | Split]` segmented control below the section header.

**Quick capture (add evidence):**
At the top of the timeline, a collapsed input field.

```
+------------------------------------------------------------------+
|  [+ Add evidence note]                                            |
+------------------------------------------------------------------+
```

Tap/click to expand:

```
+------------------------------------------------------------------+
|  Evidence text:                                                   |
|  ┌──────────────────────────────────────────────────────────┐     |
|  │ Type your evidence note here...                          │     |
|  └──────────────────────────────────────────────────────────┘     |
|  Direction: [FOR] [AGAINST] [MIXED]    Strength: [++ + +? ? -]   |
|  Source: [text input]                                             |
|  [ Cancel ]  [ Save Evidence ]                                    |
+------------------------------------------------------------------+
```

This writes to the thesis's `evidence_for` or `evidence_against` field via a new server action. MVP can append to the text field; v2 should use structured evidence entries.

#### Conviction Meter -- Enhanced

The current stepped bar visualization is good. Add:

**Direction of travel indicator:**
Below the gauge, show a small trend arrow with numeric delta.
- Calculate from evidence entries in last 14 days: more FOR = trending up, more AGAINST = trending down.
- Display: Arrow icon (up/down/flat) + "+0.3" or "-0.1" in mono text. Color matches direction (green up, flame down, amber flat).

**Conviction history sparkline:**
A tiny 80px x 20px sparkline below the gauge showing conviction changes over time (last 30 days). Built with SVG `<polyline>`. Color: current gauge color.

#### Key Questions -- Enhanced Checklist

Current implementation is good. Add:

- **Reorder by status:** Open questions first, answered below with a divider.
- **Quick toggle:** Click the dot/checkbox to mark a question as answered (opens a brief answer input).
- **Priority dot:** Open questions that drive high-priority actions get a flame-colored pulsing dot (existing `.pulse-dot` CSS).
- **Link to actions:** If a key question maps to a pending action, show a small link badge next to it.

#### Devil's Advocate View

A new section that synthesizes the bull and bear case from existing evidence.

**Layout:** Two-column panel (or tabbed on mobile).
- **Bull Case:** Aggregates all FOR evidence into a narrative paragraph. Generated from evidence_for entries. Highlighted in green-tinted card.
- **Bear Case:** Aggregates all AGAINST evidence into a counter-narrative. Highlighted in flame-tinted card.
- **Tension line:** Between the two columns, show the most relevant `PolarityPair.tension` string from `POLARITY_PAIRS`.

**Content source:** Pre-computed by the content pipeline (stored in a new `bull_bear_summary` field on thesis_threads), or rendered client-side from evidence entries as a fallback.

**Toggle:** `b` key (desktop) or tap section header (mobile). When toggled, the evidence timeline and key questions slide left, and the bull/bear panel slides in from the right with a 250ms transition.

### 2.4 Interaction Specifications

| Key | Action | Context |
|-----|--------|---------|
| `e` | Toggle evidence view (unified/split) | Thesis detail |
| `b` | Toggle devil's advocate panel | Thesis detail |
| `n` | Add new evidence (focus input) | Thesis detail |
| `q` | Focus key questions section | Thesis detail |
| `j/k` | Navigate between evidence entries | Thesis detail |
| `1-6` | Jump to conviction step (read-only display) | Thesis detail |

### 2.5 State Management

```typescript
interface ThesisDetailState {
  thesis: ThesisRow;
  evidenceView: 'unified' | 'split';
  showBullBear: boolean;
  evidenceEntries: EvidenceEntry[];  // Parsed from evidence_for + evidence_against
  keyQuestions: KeyQuestion[];
  connectedActions: ActionRow[];
  connectedDigests: DigestRow[];
  addEvidenceForm: {
    open: boolean;
    text: string;
    direction: 'for' | 'against' | 'mixed';
    strength: string;     // IDS notation
    source: string;
  } | null;
}
```

**Data fetching:** Server component pre-fetches all data (thesis, actions, digests). Evidence parsing happens server-side via `parseEvidence()`. Client components handle view toggles and evidence addition.

---

## 3. Portfolio Intelligence

### 3.1 User Journey Map

```
Entry: /portfolio or Portfolio tab in bottom nav
  |
  v
[Portfolio Hub] -- Two panels: Companies + People
  |
  +--> [Companies View]
  |     +--> Grid of company cards
  |     +--> Search + filter (sector, thesis, score)
  |     +--> Click card --> Company Detail
  |
  +--> [People View]
  |     +--> List of contacts
  |     +--> Search + filter (company, role, relationship)
  |     +--> Click card --> Person Detail
  |
  +--> [Relationship Graph] (v2 -- not MVP)
        +--> Force-directed graph of entities
        +--> Click node --> Entity detail panel
```

### 3.2 Companies View

This is a new page (`/portfolio/companies`). Data source: Companies DB via Supabase (table: `companies` or fetched from existing Notion integration).

#### Company Card Anatomy

```
+------------------------------------------+
|  [Anthropic]                    [Score]   |
|  AI Safety & Infrastructure               |
|  ─────────────────────────────────────    |
|  Thesis: AI Agents, Foundation Models     |
|  Stage: Series D  |  Sector: AI/ML       |
|  Last Activity: 3d ago                    |
|  Actions: 2 pending                       |
+------------------------------------------+
```

- Name: `text-[16px] font-semibold`, `--color-t1`
- Category/sector: `text-[12px]`, `--color-t2`
- Thesis connections: Violet pills (same style as action thesis tags)
- Score: Right-aligned numeric value in monospace. Color by range (>=7 green, 4-6 amber, <4 muted).
- Stage + Sector: Mono badges, `text-[10px]`
- Last Activity: Relative date, muted
- Pending actions: Amber badge if > 0

**Grid layout:** 2 columns on desktop, 1 on mobile. Cards use `card-depth` treatment.

#### Company Detail Panel

Slides in as a right panel on desktop (480px wide) or pushes as a new page on mobile.

Content sections:
1. **Header:** Company name, sector, stage, website link
2. **Thesis Connections:** List of connected thesis threads with conviction badges
3. **Recent Activity:** Timeline of actions, digests, and meetings related to this company
4. **Key Metrics:** If available from the Companies DB (deal size, valuation, etc.)
5. **People at Company:** List of contacts from Network DB linked to this company
6. **Open Actions:** Filtered action list for this company

### 3.3 People View

New page (`/portfolio/people`). Data source: Network DB.

#### Person Card Anatomy

```
+------------------------------------------+
|  [VV]  Vinod Vishwanathan                 |
|  Partner @ Sequoia Capital                |
|  ─────────────────────────────────────    |
|  Relationship: Strong                     |
|  Last Meeting: Mar 12                     |
|  Thesis: AI Agents, SaaS Infra           |
+------------------------------------------+
```

- Initials avatar: 36px circle with first letter(s), colored by hash of name
- Name: `text-[15px] font-semibold`
- Role + Company: `text-[13px]`, `--color-t2`
- Relationship strength: Color-coded badge (Strong=green, Medium=amber, New=cyan)
- Last meeting: Relative date
- Thesis connections: Violet pills

#### Person Detail Panel

Same slide-in pattern as company detail.

Content:
1. **Header:** Name, role, company, contact info
2. **Relationship Timeline:** Meetings, emails, actions involving this person
3. **Thesis Overlap:** Shared investment interests
4. **Company Connections:** Other people at the same company or related companies
5. **Open Actions:** Actions assigned to or involving this person

### 3.4 Smart Search

A search input at the top of the portfolio page that searches across companies, people, thesis threads, and actions simultaneously.

**Input:** Single text field, `font-mono text-[14px]`. Placeholder: "Search companies, people, thesis..."
**Results:** Grouped by entity type with section headers. Max 5 results per type. Each result shows entity name + subtitle + type badge.
**Shortcut:** `/` key focuses the search input from anywhere on the portfolio page.

### 3.5 Relationship Graph (v2)

Not in MVP. Design direction for future:
- Force-directed graph using `d3-force` or `@visx/network`
- Nodes: Companies (cyan), People (violet), Thesis (amber)
- Edges: Weighted by relationship strength, colored by type
- Click node: Opens entity detail panel
- Zoom/pan with touch and mouse
- Filter by thesis thread to see a subgraph

### 3.6 State Management

```typescript
interface PortfolioState {
  view: 'companies' | 'people' | 'graph';
  searchQuery: string;
  searchResults: {
    companies: CompanyResult[];
    people: PersonResult[];
    thesis: ThesisRow[];
    actions: ActionRow[];
  } | null;
  selectedEntity: {
    type: 'company' | 'person';
    id: string;
  } | null;
  filters: {
    sector?: string;
    thesis?: string;
    relationship?: string;
  };
}
```

---

## 4. Global Navigation + Command Palette

### 4.1 Navigation Architecture

#### Desktop: Top Nav (Enhanced)

The current top nav is minimal (logo + 3 links). Enhance to:

```
+------------------------------------------------------------------+
|  AI CoS    Digests  Actions(7)  Thesis  Portfolio    [Cmd+K] [?] |
+------------------------------------------------------------------+
```

- Add "Portfolio" link
- Add pending action count badge on "Actions" link (amber dot with number)
- Add command palette trigger button (`Cmd+K` label in muted mono)
- Add help button (`?`) that shows keyboard shortcut overlay
- Keep glass-morphism nav style
- Nav height: 56px

#### Mobile: Bottom Navigation

Replace the top nav with a fixed bottom tab bar on viewports <768px.

```
+------------------------------------------------------------------+
|  [Actions]     [Thesis]     [Portfolio]     [Feed]               |
|   (badge:7)                                                       |
+------------------------------------------------------------------+
```

- 4 tabs with icon + label
- Active tab: flame-colored icon + label + 2px top bar
- Inactive: `--color-t3`
- Height: 64px + safe area inset (for notched phones)
- Background: glass-morphism (same as current nav)
- Badge on Actions tab: amber circle with pending count
- Icons: Simple line icons (not emoji). Designed to be legible at 20px.
  - Actions: lightning bolt
  - Thesis: layers/stack
  - Portfolio: briefcase
  - Feed: bell/activity

#### Top Nav on Mobile

When bottom nav is present, the top area becomes a slim context bar:

```
+------------------------------------------------------------------+
|  AI CoS                                           [search] [Cmd] |
+------------------------------------------------------------------+
```

- 44px tall
- Logo left, search icon + command palette icon right
- Glass-morphism background

### 4.2 Command Palette (Cmd+K)

A full-screen overlay (modal) that provides instant access to any entity, action, or view.

#### Wireframe

```
+------------------------------------------------------------------+
|                                                                   |
|  ┌──────────────────────────────────────────────────────┐        |
|  │  > Search actions, thesis, companies, commands...    │        |
|  └──────────────────────────────────────────────────────┘        |
|                                                                   |
|  RECENT                                                           |
|  > AI Agents thesis thread              Thesis                    |
|  > Investigate Anthropic enterprise     Action                    |
|  > Content Pipeline Health Check        Digest                    |
|                                                                   |
|  COMMANDS                                                         |
|  > Triage pending actions               Go to view               |
|  > View all thesis threads              Go to view               |
|  > Toggle dark/light mode               Setting                  |
|                                                                   |
+------------------------------------------------------------------+
```

**Behavior:**
- **Trigger:** `Cmd+K` (Mac) / `Ctrl+K` (other). Also accessible via button in nav.
- **Input:** Auto-focused text field. Mono font. Placeholder cycles through suggestions.
- **Results:** Grouped into sections: Recent (last 5 visited entities), Actions (matching pending actions), Thesis (matching threads), Companies, People, Commands (static list of navigation shortcuts).
- **Navigation:** Arrow keys to move selection, Enter to navigate, Esc to close.
- **Instant filtering:** Results filter as you type. 100ms debounce.
- **Result anatomy:** Entity name + type badge (right-aligned, colored by type) + optional subtitle.
- **Overlay:** Full viewport, `rgba(8, 8, 12, 0.8)` backdrop with blur. Palette centered, max-width 560px, max-height 420px.
- **Animation:** Palette scales from 0.95 to 1.0 and fades in, 150ms ease-out. Backdrop fades in 100ms.

**Command list (static):**

| Command | Action |
|---------|--------|
| Triage pending actions | Navigate to /actions card view, Proposed filter |
| View all actions | Navigate to /actions |
| View thesis threads | Navigate to /thesis |
| View portfolio | Navigate to /portfolio |
| View digests | Navigate to / |
| Toggle view mode | Switch card/list in current context |
| Refresh data | Re-fetch current page data |

### 4.3 Activity Feed

New page/section accessible from the Feed tab (mobile) or a dedicated route `/feed`.

#### Feed Anatomy

```
+------------------------------------------------------------------+
|  ACTIVITY FEED                                      Last 7 days  |
|                                                                   |
|  TODAY                                                            |
|  [flame dot]  3 new actions proposed by ENIAC        2h ago      |
|               AI Agents (2), Content Pipeline (1)                 |
|                                                                   |
|  [green dot]  Thesis conviction updated: AI Agents   4h ago      |
|               Evolving Fast -> High                               |
|                                                                   |
|  [cyan dot]   New digest published                   6h ago      |
|               "The State of AI Agents 2026"                       |
|                                                                   |
|  YESTERDAY                                                        |
|  [amber dot]  5 actions triaged (3 accepted)         1d ago      |
|                                                                   |
|  [violet dot] New evidence added to 2 thesis threads 1d ago      |
|                                                                   |
+------------------------------------------------------------------+
```

**Feed items:** Grouped by day. Each item has:
- Color dot (by type: flame=actions, green=thesis, cyan=digests, amber=triage, violet=evidence)
- Summary text: `text-[14px]`, `--color-t1`
- Detail text: `text-[12px]`, `--color-t2`
- Relative time: `font-mono text-[10px]`, `--color-t3`, right-aligned

**Data source:** Derived from changes to actions_queue, thesis_threads, and content_digests tables. Computed server-side by comparing timestamps.

**Feed is the lowest-priority feature** -- it provides value but is not decision-driving like triage or thesis views.

### 4.4 Notification Center (v2)

Not in MVP. Future design direction:
- Badge count on Feed tab showing unread notifications
- Push notifications via PWA service worker for:
  - New P0 actions proposed
  - Thesis conviction changes
  - Pipeline failures or stale data
- Notification preferences page

---

## 5. Mobile-First Considerations

### 5.1 PWA Configuration

The app must be installable as a PWA. Required additions to `layout.tsx`:

**manifest.json requirements:**
- `display: "standalone"` (no browser chrome)
- `theme_color: "#08080c"` (matches bg)
- `background_color: "#08080c"`
- App icon: "AI CoS" monogram in flame color on dark bg, 192px and 512px variants
- `start_url: "/actions"` (triage is the primary entry point, not digests)
- `scope: "/"`

**Service worker:**
- Cache strategy: Network-first for data (actions, thesis), cache-first for static assets
- Offline fallback page: "You're offline. Last synced [timestamp]." with cached data if available

### 5.2 Mobile Layout Principles

1. **Bottom nav always visible** -- 64px + safe area. Never hidden by scroll.
2. **Cards are edge-to-edge** -- 16px horizontal padding, no additional card margin. Maximize content width.
3. **Touch targets >= 48px** -- Every interactive element. The current 44px minimum is acceptable but 48px is preferred.
4. **No hover states** -- All `:hover` styles must be behind `@media (hover: hover)` queries.
5. **Swipe zones** -- Left/right swipe on action cards conflicts with browser back gesture. Solution: swipe zone starts at 44px from left edge of card (not screen edge). Browser gesture uses the leftmost 20px of viewport.
6. **Pull-to-refresh** -- Custom implementation on all list/feed views. Threshold: 60px pull distance. Shows a small spinner icon.
7. **System font stack fallback** -- If custom fonts fail to load, use system-ui. Don't block render on font loading.

### 5.3 Mobile Triage Flow

The card stack on mobile is the hero interaction. Specific mobile adaptations:

- Card height: Fills viewport minus top bar (44px) and bottom nav (64px). Content scrolls within the card if expanded.
- Swipe indicators: When dragging, show a subtle gradient glow on the edge the card is moving toward (green on right edge for accept, muted on left for dismiss).
- Button size: Accept/Dismiss/Defer buttons are 52px tall on mobile (vs 48px desktop).
- One-handed use: All critical interactions reachable in the bottom 60% of viewport. The action title and buttons are always visible without scrolling.

### 5.4 Widget / Quick Actions (v2)

Not in MVP. Future:
- iOS widget showing pending action count + top P0 action
- Share extension: Share a URL into AI CoS and it creates a content pipeline entry
- Shortcut integration: "Hey Siri, what's my top action" reads the #1 pending action

---

## 6. Micro-Interaction Specifications

### 6.1 Animation Inventory

| Element | Trigger | Animation | Duration | Easing |
|---------|---------|-----------|----------|--------|
| Card triage (accept) | Swipe right or `a` key | translateX(110%) + opacity(0) + rotate(3deg) | 250ms | ease-out |
| Card triage (dismiss) | Swipe left or `d` key | translateX(-110%) + opacity(0) + rotate(-3deg) | 250ms | ease-out |
| Card triage (defer) | Swipe down or `s` key | translateY(60px) + opacity(0) | 200ms | ease-out |
| Next card advance | After triage exit | scale(0.97 -> 1.0) + translateY(8px -> 0) | 200ms | cubic-bezier(0.2, 0, 0, 1) |
| Card expand detail | `?` key or tap | height auto transition using CSS grid trick | 250ms | ease-out |
| Undo toast enter | After triage | translateY(8px -> 0) + opacity(0 -> 1) | 200ms | ease-out |
| Undo toast exit | After 5s or undo | opacity(1 -> 0) | 150ms | ease-in |
| Undo countdown | During undo window | scaleX(1 -> 0) on progress bar | 5000ms | linear |
| Command palette open | Cmd+K | scale(0.95 -> 1) + opacity(0 -> 1) | 150ms | ease-out |
| Command palette close | Esc | opacity(1 -> 0) | 100ms | ease-in |
| Bottom nav badge | New actions | scale(0 -> 1) + brief bounce | 300ms | spring |
| Scoring bar fill | On mount (detail view) | scaleX(0 -> 1), staggered per bar | 600ms + 80ms stagger | ease-out |
| Conviction gauge step | On mount | opacity(0 -> 1), staggered per step | 400ms + 60ms stagger | ease-out |
| Evidence entry reveal | On scroll into view | opacity(0 -> 1) + translateY(12px -> 0) | 350ms | ease-out |
| Filter active state | On select | border-color transition + subtle glow | 150ms | ease-out |
| Card depth hover | Mouse enter (desktop) | border-color rgba transition + shadow spread | 150ms | ease-out |
| Batch bar enter | First selection | translateY(100% -> 0) + opacity(0 -> 1) | 250ms | ease-out |

### 6.2 Animation Rules

1. **Only animate `transform` and `opacity`.** Never animate width, height, margin, padding, top, left. This is enforced in the CSS guidelines.
2. **Stagger reveals, don't scatter them.** When multiple elements animate (scoring bars, evidence entries), use sequential stagger delays, not random timing.
3. **One hero animation per view.** The card triage swipe is the hero for actions. The conviction gauge build is the hero for thesis. Don't compete.
4. **Reduced motion:** Honor `prefers-reduced-motion`. Disable all animations except opacity fades. Implement via `@media (prefers-reduced-motion: reduce)`.
5. **No spring physics in CSS.** Use `cubic-bezier(0.2, 0, 0, 1)` for snap-back effects. True spring physics only via JS (Framer Motion or manual RAF) for the card swipe interaction.

### 6.3 Haptic Feedback (Mobile)

Where supported (`navigator.vibrate`):
- Accept action: Single short pulse (10ms)
- Dismiss action: Double short pulse (10ms, 30ms gap, 10ms)
- Undo: Single medium pulse (20ms)
- Swipe threshold crossed: Single short pulse (10ms)

### 6.4 Sound Design (Opt-in)

All sounds are off by default. Can be enabled in settings.
- Accept: Brief ascending two-note chime
- Dismiss: Muted single click
- Undo: Reverse swoosh
- Volume: 15% max. Never jarring.

---

## 7. Prioritized Build Order

### Phase 1: Triage Core (Ship first -- highest impact)

**Scope:** Card-stack triage view with keyboard shortcuts. This is the single most important feature.

| Task | Files | Effort |
|------|-------|--------|
| 1a. Card stack component with swipe gestures | New: `TriageCardStack.tsx` | M |
| 1b. Keyboard shortcut system (global handler) | New: `useKeyboardShortcuts.ts` hook | S |
| 1c. Undo toast with countdown bar | Enhance: `ActionDetailTriage.tsx` pattern | S |
| 1d. Card expand/collapse with section details | New: `TriageCardExpanded.tsx` | S |
| 1e. Keyboard hint bar (desktop) | New: `KeyboardHintBar.tsx` | XS |
| 1f. Card exit animations (accept/dismiss/defer) | CSS + component state | S |
| 1g. Empty state (all caught up) | In card stack component | XS |
| 1h. Progress indicator bar | In card stack component | XS |

**Ship target:** This alone transforms the app from "website" to "product."

### Phase 2: Command Palette + Enhanced Navigation

| Task | Files | Effort |
|------|-------|--------|
| 2a. Command palette component (`Cmd+K`) | New: `CommandPalette.tsx` | M |
| 2b. Bottom navigation (mobile) | New: `BottomNav.tsx`, modify `layout.tsx` | S |
| 2c. Responsive nav (top on desktop, bottom on mobile) | Modify `Nav.tsx` | S |
| 2d. Pending action badge on nav | Modify `Nav.tsx`, `BottomNav.tsx` | XS |
| 2e. PWA manifest + service worker | New: `manifest.json`, `sw.ts` | S |

### Phase 3: Thesis Command Center Enhancement

| Task | Files | Effort |
|------|-------|--------|
| 3a. Unified evidence timeline | Modify `thesis/[id]/page.tsx` | M |
| 3b. Quick evidence capture form | New: server action + form component | S |
| 3c. Conviction direction indicator + sparkline | Modify thesis detail page | S |
| 3d. Devil's advocate bull/bear panel | New: `BullBearPanel.tsx` | M |
| 3e. Enhanced key questions with toggle | Modify thesis detail page | S |
| 3f. View mode toggle (unified/split) | Modify thesis detail page | XS |

### Phase 4: List Mode + Batch Operations Enhancement

| Task | Files | Effort |
|------|-------|--------|
| 4a. Card/list view toggle | Modify actions page | S |
| 4b. Dense list row component | New or modify `ActionCard.tsx` | S |
| 4c. Sort column headers | Modify `ActionFilterBar.tsx` | S |
| 4d. Side panel detail (desktop list mode) | New: `ActionSidePanel.tsx` | M |

### Phase 5: Portfolio Intelligence (New Section)

| Task | Files | Effort |
|------|-------|--------|
| 5a. Portfolio page with companies grid | New: `portfolio/page.tsx` | M |
| 5b. Company card component | New: `CompanyCard.tsx` | S |
| 5c. Person card component | New: `PersonCard.tsx` | S |
| 5d. Portfolio search | New: search component + queries | M |
| 5e. Entity detail panel | New: `EntityDetailPanel.tsx` | M |
| 5f. People view | New: `portfolio/people/page.tsx` | S |

### Phase 6: Activity Feed + Polish

| Task | Files | Effort |
|------|-------|--------|
| 6a. Activity feed page | New: `feed/page.tsx` | M |
| 6b. Feed data aggregation (server-side) | New: `lib/feed/queries.ts` | M |
| 6c. Reduced motion support | CSS media query additions | XS |
| 6d. Haptic feedback integration | Utility function | XS |
| 6e. Relationship graph (v2) | New: `portfolio/graph/page.tsx` | L |

### Why This Order

1. **Phase 1 (Triage Core)** delivers the highest-leverage change. The card-stack with keyboard shortcuts transforms the app from a data viewer into a decision-making tool. Aakash will use this multiple times per day.

2. **Phase 2 (Navigation)** makes the app feel like a real product. Command palette gives power users instant access. Bottom nav makes mobile usable. PWA makes it installable.

3. **Phase 3 (Thesis Enhancement)** deepens the analytical layer. The current thesis pages are already good -- this phase makes them exceptional with the timeline and bull/bear views.

4. **Phase 4 (List Mode)** serves the "batch processing" use case. Some days you want to triage 20 actions quickly without the card ceremony.

5. **Phase 5 (Portfolio)** extends the system to entities that currently live only in Notion. This is where the "intelligence layer" starts to emerge.

6. **Phase 6 (Feed + Polish)** is the "living system" layer. The feed shows the system is working even when you're not actively triaging.

---

## 8. Technical Implementation Notes

### 8.1 Client-Side Gesture Library

For the card swipe interaction, use Framer Motion's `useDragControls` or a lightweight alternative like `@use-gesture/react`. The key requirements:
- Velocity-aware threshold (fast flick = trigger even at 30px, slow drag = require 60px)
- Spring-back animation when drag is below threshold
- Direction locking (once you start swiping right, vertical movement is ignored)

### 8.2 Keyboard Shortcut Architecture

Implement a global `useKeyboardShortcuts` hook that:
- Registers shortcuts by context (triage, list, thesis, global)
- Respects focus: no shortcuts when typing in an input/textarea
- Shows the keyboard hint bar with active context shortcuts
- Handles modifier keys (Cmd, Shift, Ctrl)

```typescript
// Usage pattern
useKeyboardShortcuts({
  context: 'triage',
  shortcuts: {
    'a': { action: handleAccept, label: 'Accept' },
    'd': { action: handleDismiss, label: 'Dismiss' },
    's': { action: handleDefer, label: 'Defer' },
    '?': { action: toggleExpand, label: 'Detail' },
    'j': { action: nextCard, label: 'Next' },
    'k': { action: prevCard, label: 'Previous' },
    'z': { action: handleUndo, label: 'Undo' },
  },
});
```

### 8.3 Data Prefetching Strategy

For the card stack, prefetch the next 3 actions' detail data (related actions, thesis connections, scoring) while the user is reading the current card. This eliminates the perceived latency when expanding details.

Use React's `use()` hook with a `Promise` that starts fetching in the background:

```typescript
// Start fetching next cards' details in parallel
const prefetchPromises = actions
  .slice(currentIndex + 1, currentIndex + 4)
  .map(a => fetchActionDetail(a.id));
```

### 8.4 CSS Architecture Notes

- **Container queries** for component responsiveness (card layout changes based on card width, not viewport)
- **CSS custom properties** for all colors (already done)
- **`prefers-reduced-motion`** media query wrapping all animation declarations
- **`@supports (backdrop-filter: blur())` ** for graceful degradation of glass-morphism on older browsers
- **No new fonts** -- stick with the existing Instrument Serif / DM Sans / JetBrains Mono stack. The Geist mention in the brief is noted but the existing stack is distinctive and well-implemented.

### 8.5 Accessibility Notes

- All keyboard shortcuts must be discoverable (via `?` overlay and keyboard hint bar)
- Screen reader: card triage announces "Action [N] of [M]. [Action title]. Priority [P]. Press A to accept, D to dismiss."
- Focus management: after card exit, focus moves to next card. After modal close, focus returns to trigger.
- Color is never the only differentiator -- all status/priority indicators also have text labels
- Swipe gestures have button alternatives (the Accept/Dismiss/Defer buttons are always visible)

---

## Appendix A: Design Token Reference

These are the existing tokens from `globals.css` that all new components should use:

| Token | Value | Use |
|-------|-------|-----|
| `--color-bg` | `#08080c` | Page background |
| `--color-card` | `#0f0f16` | Card/panel background |
| `--color-elevated` | `#16161f` | Elevated surface (popovers, command palette) |
| `--color-subtle-border` | `rgba(255,255,255,0.06)` | Default borders |
| `--color-flame` | `#ff5722` | P0 priority, primary accent, brand |
| `--color-amber` | `#ffab00` | P1 priority, warnings, pending states |
| `--color-cyan` | `#00e5ff` | P2 priority, info, exploring |
| `--color-violet` | `#b388ff` | P3 priority, thesis connections, defer |
| `--color-green` | `#69f0ae` | Accepted, evidence FOR, positive |
| `--color-t1` | `#eeedf2` | Primary text |
| `--color-t2` | `#908e9b` | Secondary text |
| `--color-t3` | `#56545f` | Tertiary text, labels |

## Appendix B: Page Route Map

```
/                     -- Home (digest list + stats)
/actions              -- Action triage (card stack default, list toggle)
/actions/[id]         -- Action detail (keep existing, enhance with keyboard)
/thesis               -- Thesis grid
/thesis/[id]          -- Thesis command center
/portfolio            -- Portfolio hub (companies default)
/portfolio/people     -- People view
/feed                 -- Activity feed
/d/[slug]             -- Digest detail (keep existing)
```

## Appendix C: Existing Component Reuse Map

| Existing Component | Reuse In | Modifications Needed |
|-------------------|----------|---------------------|
| `ActionCard.tsx` | List mode rows | Add dense/compact variant prop |
| `ActionDetailTriage.tsx` | Card stack triage buttons | Extract button group as shared component |
| `ActionFilterBar.tsx` | List mode filters | Add sort controls |
| `Nav.tsx` | Desktop nav | Add portfolio link, badge, cmd+k button |
| `DigestClient.tsx` | Feed page (digest entries) | None -- reference only |
| `priorityAccent()` | Everywhere | Extract to shared `lib/colors.ts` |
| `statusStyle()` | Everywhere | Extract to shared `lib/colors.ts` |
| `lensAccent()` | Thesis views | Already scoped correctly |
| `card-depth` CSS class | All new cards | No change |
| `nav-glass` CSS class | Bottom nav, command palette backdrop | No change |
| `scoring-bar-fill` CSS | Card expanded view, thesis detail | No change |
