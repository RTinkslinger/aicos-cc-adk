# Search UX Design Spec: AI CoS WebFront

**Date:** 2026-03-20
**Author:** Search UX Design Session
**Status:** Design Spec (pre-implementation)
**Depends on:** `2026-03-20-webfront-product-design.md`, `2026-03-20-shadcn-component-composition.md`

---

## Design Philosophy

Search is the nervous system of AI CoS. It connects every entity (4,635 companies, 3,728 people, 142 portfolio companies, 8 thesis threads, 115 actions, 22 digests) into a single addressable space. The design references three products:

1. **Spotlight (macOS)** -- Instant results as you type, grouped by category, one keystroke to launch. Zero friction entry.
2. **Linear** -- Structured search results with rich metadata inline. Filters that feel like commands, not forms.
3. **Bloomberg Terminal** -- Every entity is a node in a graph. Click any entity, see every connection. Density over whitespace.

**Core constraints:**
- 150ms target for first result (debounce 150ms, server response <300ms)
- Six entity types with wildly different cardinalities (8 thesis vs 4,635 companies)
- Existing `hybrid_search` RPC (pgvector + FTS) already handles actions, thesis, digests, and companies
- Network and portfolio tables exist in Postgres but are not yet indexed for search
- Mobile-first: search must work on a phone screen with one-handed use

---

## 1. Instant Search (Cmd+K Enhanced)

### 1.1 Current State

The existing `CommandPalette.tsx` (585 lines) provides:
- Cmd+K trigger with backdrop overlay
- 300ms debounce, POST to `/api/search`
- Results grouped by type (action, thesis, digest, company) with type icons/colors
- Recent searches in localStorage (5 max)
- Keyboard nav (arrow keys + Enter)
- Company results open `CompanyBrief` side panel instead of navigating

**Gaps in current implementation:**
- Only 4 entity types (missing: network people, portfolio)
- No fuzzy matching (exact ILIKE only in text fallback)
- No rich preview metadata (just title + subtitle + snippet)
- No result count per group
- No "frequently accessed" tracking (only recent searches)
- No type-ahead filter commands (e.g., typing "company:" to scope)
- 300ms debounce (should be 150ms)
- No Enter-to-full-search-page behavior

### 1.2 Enhanced Command Palette -- Wireframe

```
+------------------------------------------------------------------+
|  [Q] Search everything...                    [spinner]  [ESC]     |
|------------------------------------------------------------------|
|  COMMANDS          (when query starts with > or /)                |
|  > Go to Actions                                    [G] [A]      |
|  > Go to Thesis                                     [G] [T]      |
|  > Triage pending actions (7)                       Enter         |
|------------------------------------------------------------------|
|  RECENT SEARCHES   (empty query, no commands)                     |
|  [clock] anthropic agent sdk                                      |
|  [clock] sequoia partner                                          |
|------------------------------------------------------------------|
|  COMPANIES         4 results                        [square]      |
|  Anthropic          AI Safety & Infrastructure    Series D        |
|  LangChain          Developer Tools               Series B        |
|  Cursor             AI-Native IDE                  Series B        |
|  Replit             Cloud Development              Series B        |
|------------------------------------------------------------------|
|  PEOPLE            3 results                        [person]      |
|  Dario Amodei       CEO @ Anthropic                Strong         |
|  Harrison Chase     CEO @ LangChain                Medium         |
|  Vinod K            Partner @ Sequoia              Strong         |
|------------------------------------------------------------------|
|  PORTFOLIO         1 result                         [briefcase]   |
|  Anthropic          Green | Fund Priority          Series D       |
|------------------------------------------------------------------|
|  THESIS            1 result                         [diamond]     |
|  AI Agents Will...  Active | High                   3 open Qs    |
|------------------------------------------------------------------|
|  ACTIONS           2 results                        [bolt]        |
|  Investigate Ant... P0 | Research                   Proposed      |
|  Schedule follow... P1 | Meeting                    Proposed      |
|------------------------------------------------------------------|
|  DIGESTS           1 result                         [circle]      |
|  The State of AI... ENIAC                           9.2 rel       |
|------------------------------------------------------------------|
|  [up][down] Navigate    [Enter] Open    [Esc] Close    [Cmd+Enter] Full results  |
+------------------------------------------------------------------+
```

### 1.3 Result Type Configuration

Each entity type has a distinct visual signature. Extend the existing `TYPE_CONFIG`:

```typescript
const TYPE_CONFIG: Record<string, {
  icon: string;       // Unicode symbol
  label: string;      // Group header
  color: string;      // CSS variable
  priority: number;   // Sort order in results (lower = higher)
  maxResults: number; // Max results shown in palette
}> = {
  company: {
    icon: "\u25A0",        // filled square
    label: "Companies",
    color: "var(--color-green)",
    priority: 1,
    maxResults: 5,
  },
  person: {
    icon: "\u25CB",        // circle (will be replaced by avatar)
    label: "People",
    color: "var(--color-cyan)",
    priority: 2,
    maxResults: 5,
  },
  portfolio: {
    icon: "\u25B2",        // triangle
    label: "Portfolio",
    color: "var(--color-amber)",
    priority: 3,
    maxResults: 3,
  },
  thesis: {
    icon: "\u25C6",        // diamond
    label: "Thesis",
    color: "var(--color-violet)",
    priority: 4,
    maxResults: 3,
  },
  action: {
    icon: "\u26A1",        // lightning
    label: "Actions",
    color: "var(--color-flame)",
    priority: 5,
    maxResults: 5,
  },
  digest: {
    icon: "\u25CB",        // circle
    label: "Digests",
    color: "var(--color-cyan)",
    priority: 6,
    maxResults: 3,
  },
};
```

**Result ordering within groups:**
- Companies: by name match quality (exact start > contains), then alphabetical
- People: by relationship_strength (Strong > Medium > New), then name
- Portfolio: by health (Green > Yellow > Red), then name
- Thesis: by status (Active first), then conviction descending
- Actions: by relevance_score descending, then priority
- Digests: by created_at descending, then relevance_score

### 1.4 Rich Result Row -- Per Type

Each result row shows type-specific metadata inline. All rows share a common structure:

```
[type indicator]  [primary text]  [secondary text]  [metadata badges]  [action hint]
```

#### Company Result Row

```
[green square]  Anthropic          AI Safety & Infrastructure    [Series D]  [4,635 total]
                ^-- name (t1)      ^-- sector (t3)               ^-- stage badge (cyan)
```

**Data fields:** `name` (title), `sector` (subtitle), `stage` (badge), `deal_status` (if in pipeline)
**Click behavior:** Navigate to `/portfolio/{id}` if portfolio company, else open CompanyBrief panel

#### Person Result Row

```
[DA avatar]  Dario Amodei         CEO @ Anthropic               [Strong]
             ^-- full_name (t1)   ^-- role @ company (t3)       ^-- relationship badge (green)
```

**Data fields:** `full_name` (title), `role` + `current_company` (subtitle), `relationship_strength` (badge)
**Click behavior:** Open PersonBrief panel (new -- modeled after CompanyBrief)
**Avatar:** 24px circle with initials, colored by name hash (reuse CompanyBrief avatar logic)

#### Portfolio Result Row

```
[green dot] [amber triangle]  Anthropic    Green | Fund Priority    [Series D]  [$2.5M entry]
                              ^-- name      ^-- health | today       ^-- stage   ^-- entry_cheque
```

**Data fields:** `portfolio_co` (title), `health` + `today` (subtitle with dots), `current_stage` (badge), `entry_cheque` (monospace)
**Click behavior:** Navigate to `/portfolio/{id}`

#### Thesis Result Row

```
[violet diamond]  AI Agents Will Transform...    Active | High    [3 open, 1 answered]
                  ^-- thread_name (t1)           ^-- status|conviction  ^-- key_question_summary
```

**Data fields:** `thread_name` (title), `status` + `conviction` (subtitle), `key_question_summary` (trailing metadata)
**Click behavior:** Navigate to `/thesis/{id}`

#### Action Result Row

```
[flame bolt] [P0]  Investigate Anthropic's enterprise...    Research | Proposed    [8.2]
                    ^-- action text (t1)                    ^-- type | status       ^-- score
```

**Data fields:** `action` (title), `action_type` + `status` (subtitle), `relevance_score` (monospace badge), `priority` (colored left badge)
**Click behavior:** Navigate to `/actions/{id}` or open ActionDetailSheet

#### Digest Result Row

```
[cyan circle]  The State of AI Agents 2026    ENIAC    [9.2]    2d ago
               ^-- title (t1)                 ^-- channel (t3)  ^-- rel score  ^-- relative date
```

**Data fields:** `title` (title), `channel` (subtitle), `relevance_score` (badge), `created_at` (relative time)
**Click behavior:** Navigate to `/d/{slug}`

### 1.5 Scoped Search (Type Filters)

Users can prefix their query to scope results to a single type:

| Prefix | Scope | Example |
|--------|-------|---------|
| `c:` or `company:` | Companies only | `c:anthropic` |
| `p:` or `person:` | People only | `p:dario` |
| `t:` or `thesis:` | Thesis only | `t:agents` |
| `a:` or `action:` | Actions only | `a:research` |
| `d:` or `digest:` | Digests only | `d:ENIAC` |
| `pf:` or `portfolio:` | Portfolio only | `pf:green` |
| `>` or `/` | Commands only | `>triage` |

**Implementation:** Parse query in the API route before passing to search functions. Strip prefix, set `filters.tables` accordingly. Show active scope as a dismissable badge next to the search input.

**Visual treatment of scope badge:**
```
[Q] [company X]  anthropic_                    [ESC]
     ^-- dismissable pill, colored by type
```

### 1.6 Command Mode

When query starts with `>` or `/`, switch to command mode. Show navigation and action commands instead of entity search results.

**Command list (static + dynamic):**

| Command | Action | Shortcut |
|---------|--------|----------|
| Go to Actions | Navigate `/actions` | `G` then `A` |
| Go to Thesis | Navigate `/thesis` | `G` then `T` |
| Go to Portfolio | Navigate `/portfolio` | `G` then `P` |
| Go to Digests | Navigate `/` | `G` then `D` |
| Triage pending actions (N) | Navigate `/actions?status=Proposed&view=card` | -- |
| Toggle view mode | Switch card/list in current context | `V` |
| Show keyboard shortcuts | Open shortcut help dialog | `?` |

Dynamic commands (populated from data):
- "Triage pending actions (7)" -- only when pending count > 0
- "Resume thesis: [thread_name]" -- for each Active thesis

### 1.7 Recent Searches + Frequently Accessed

**Recent searches** (existing, enhance):
- Store last 8 (up from 5)
- Show with clock icon and relative time: `"anthropic" -- 2h ago`
- Clear individual entries (X button on hover)
- Clear all button at bottom of section

**Frequently accessed** (new):
- Track entity access in localStorage: `{ entityType, entityId, title, url, accessCount, lastAccessed }`
- Show top 5 most-accessed entities when palette opens with empty query
- Deduplicate with recent searches (if an entity was just searched, don't show it in frequent too)
- Section header: "FREQUENTLY ACCESSED" with count

**localStorage schema:**
```typescript
interface AccessEntry {
  type: SearchResult["type"];
  id: number;
  title: string;
  subtitle: string | null;
  url: string;
  accessCount: number;
  lastAccessed: number; // Unix timestamp
}

// Key: "aicos-access-log"
// Max entries: 50 (LRU eviction)
// Scoring: accessCount * 0.7 + recency * 0.3 (where recency = 1.0 for today, decays over 14 days)
```

### 1.8 Keyboard Interactions

| Key | Action | Context |
|-----|--------|---------|
| `Cmd+K` / `Ctrl+K` | Open/close palette | Global |
| `Arrow Up/Down` | Navigate results | Palette open |
| `Enter` | Open selected result | Palette open, result selected |
| `Cmd+Enter` | Open full search results page | Palette open, query entered |
| `Escape` | Close palette (or clear query first) | Palette open |
| `Tab` | Cycle through result groups | Palette open |
| `Backspace` on empty | Remove scope filter badge | Palette open, scoped |
| `/` | Open palette (if not in input) | Global |

**New behavior -- Escape cascade:**
1. First Escape: If query has text, clear query (don't close)
2. Second Escape: Close palette

**New behavior -- Cmd+Enter:**
Navigates to `/search?q={query}` full results page. Palette closes. This is the bridge to the full search experience.

### 1.9 Animation & Transitions

**Palette open:**
- Backdrop: opacity 0 -> 0.6, 150ms ease-out
- Dialog: scale 0.97 -> 1.0 + opacity 0 -> 1, 150ms ease-out
- Input auto-focus after 50ms (avoid Flash of Unfocused Input)

**Palette close:**
- Backdrop: opacity 0.6 -> 0, 100ms ease-in
- Dialog: opacity 1 -> 0, 100ms ease-in

**Result group reveal (when results load):**
- Each group fades in with 30ms stagger: opacity 0 -> 1 + translateY(4px) -> 0, 150ms ease-out
- Loading spinner: appears after 200ms (avoid flash for fast responses)

**Result selection:**
- Selected row: background transitions to `rgba(255,255,255,0.04)`, 80ms ease-out
- No scale/transform on selection (keeps layout stable for keyboard navigation)

---

## 2. Search Results Page (`/search?q=...`)

### 2.1 When It Activates

The full search page activates when:
1. User presses `Cmd+Enter` from the command palette
2. User navigates directly to `/search?q=term`
3. User presses `Enter` on an empty palette (shows all entities)

This page shows comprehensive results with filtering, pagination, and rich cards.

### 2.2 Page Layout -- Wireframe

```
+------------------------------------------------------------------+
|  SEARCH                                                [Cmd+K]    |
|  ┌──────────────────────────────────────────────────────────┐     |
|  │  Q  "anthropic"                                     [X]  │     |
|  └──────────────────────────────────────────────────────────┘     |
|                                                                   |
|  [All (11)] [Companies (4)] [People (3)] [Portfolio (1)]          |
|  [Thesis (1)] [Actions (2)] [Digests (1)]                         |
|------------------------------------------------------------------|
|                                                                   |
|  --- COMPANIES (4) -----------------------------------------------  |
|  ┌──────────────────────┐  ┌──────────────────────┐              |
|  │ Anthropic             │  │ Anthropic Capital    │              |
|  │ AI Safety & Infra     │  │ Investment Fund      │              |
|  │ Series D | Pipeline   │  │ Series A | Tracking  │              |
|  │ Thesis: AI Agents,    │  │ Thesis: --           │              |
|  │         Foundation    │  │ People: 2 linked     │              |
|  │ People: 5 linked     │  │ Actions: 0           │              |
|  │ Actions: 3 pending   │  │                      │              |
|  └──────────────────────┘  └──────────────────────┘              |
|  ┌──────────────────────┐  ┌──────────────────────┐              |
|  │ Anthropic Ventures   │  │ Anthropic Research   │              |
|  │ ...                  │  │ ...                  │              |
|  └──────────────────────┘  └──────────────────────┘              |
|                                                                   |
|  --- PEOPLE (3) --------------------------------------------------  |
|  ┌──────────────────────┐  ┌──────────────────────┐              |
|  │ [DA] Dario Amodei    │  │ [JC] Janine Clark    │              |
|  │ CEO @ Anthropic      │  │ VP Eng @ Anthropic   │              |
|  │ Relationship: Strong │  │ Relationship: Medium │              |
|  │ Last meeting: Mar 12 │  │ Last meeting: --     │              |
|  │ Thesis: AI Agents    │  │ Thesis: --           │              |
|  └──────────────────────┘  └──────────────────────┘              |
|                                                                   |
|  --- THESIS (1) --------------------------------------------------  |
|  ┌──────────────────────────────────────────────────────────┐     |
|  │ AI Agents Will Transform Enterprise Software             │     |
|  │ Active | High Conviction | 12 FOR, 3 AGAINST             │     |
|  │ Key Cos: Anthropic, LangChain, Cursor, CrewAI            │     |
|  │ Open Qs: 3 | Last evidence: 2d ago                       │     |
|  │ Connected: 5 actions (2 pending), 8 digests               │     |
|  └──────────────────────────────────────────────────────────┘     |
|                                                                   |
|  [Load More]  (if more results exist)                             |
+------------------------------------------------------------------+
```

### 2.3 Tab Bar

Horizontal tab strip with count badges. Sticky below the search input on scroll.

```typescript
interface SearchTab {
  key: "all" | "company" | "person" | "portfolio" | "thesis" | "action" | "digest";
  label: string;
  count: number;
  color: string;
}
```

**"All" tab behavior:**
- Shows results from every type, each in its own section
- Sections ordered by TYPE_CONFIG.priority
- Each section shows up to maxResults, with "Show all N" link to switch to that tab
- Total count is the sum across all types

**Individual tab behavior:**
- Shows only that type's results
- No max limit (paginated at 20)
- Richer cards with more metadata than the "All" view
- Sort controls visible: relevance (default), name A-Z, date newest, date oldest

### 2.4 Result Cards -- Per Type (Full Page Variants)

Cards on the full page are richer than palette results. They show connection counts and cross-entity linkages.

#### Company Card (Full Page)

```
+------------------------------------------+
|  [green square] Anthropic        Series D |
|  AI Safety & Infrastructure               |
|  ─────────────────────────────────────    |
|  Thesis: AI Agents (High), Foundation     |
|          Models (Medium)                  |
|  People: 5 linked (2 Strong, 3 Medium)   |
|  Actions: 3 pending (1 P0, 2 P1)         |
|  Pipeline: Active | Bucket 1              |
|  Last Activity: 2d ago                    |
+------------------------------------------+
```

**Fields:** name, sector, stage, linked thesis (with conviction), linked people count (by strength), pending action count (by priority), pipeline status, bucket, last activity
**Click:** Opens company entity detail view (Section 3)
**Card width:** 2 columns on desktop (>= 768px), 1 column on mobile

#### Person Card (Full Page)

```
+------------------------------------------+
|  [DA]  Dario Amodei                       |
|  CEO @ Anthropic                          |
|  ─────────────────────────────────────    |
|  Relationship: Strong                     |
|  Companies: Anthropic (current)           |
|  Thesis: AI Agents, Foundation Models     |
|  Actions: 2 involving (1 pending)         |
|  Last meeting: Mar 12, 2026              |
+------------------------------------------+
```

**Fields:** full_name, role, current_company, relationship_strength, linked companies, linked thesis, action count, last_meeting_date
**Click:** Opens person entity detail view (Section 3)
**Avatar:** 36px circle, colored by name hash, shows initials

#### Portfolio Card (Full Page)

```
+------------------------------------------+
|  [green dot] Anthropic      Fund Priority |
|  Health: Green | Stage: Series D          |
|  ─────────────────────────────────────    |
|  Ownership: 2.5% | Entry: $2.5M          |
|  Follow-on: Committed                    |
|  Founders: Dario Amodei, Daniela Amodei  |
|  Thesis: AI Agents (High)                |
|  Actions: 3 (2 pending)                  |
|  Check-in: Quarterly                     |
+------------------------------------------+
```

**Fields:** portfolio_co, health, today, current_stage, ownership_pct, entry_cheque, follow_on_decision, linked founders, linked thesis, action count, check_in_cadence
**Click:** Navigate to `/portfolio/{id}`

#### Thesis Card (Full Page)

```
+----------------------------------------------------------+
|  [violet diamond] AI Agents Will Transform Enterprise SW  |
|  Active | High Conviction                                 |
|  ─────────────────────────────────────────────────────    |
|  "Enterprise adoption of AI agents is accelerating        |
|   faster than any prior software paradigm shift..."       |
|                                                           |
|  Evidence: 12 FOR | 3 AGAINST | 2 NEUTRAL                |
|  ████████████░░░░  (ratio bar: green | flame)             |
|                                                           |
|  Key Companies: Anthropic, LangChain, Cursor, CrewAI      |
|  Open Questions: 3 | Last evidence: 2d ago                |
|  Connected: 5 actions (2 pending), 8 digests              |
+----------------------------------------------------------+
```

**Fields:** thread_name, status, conviction, core_thesis (first 2 lines), evidence counts (for/against/neutral), evidence ratio bar, key_companies, key_question_summary, action count, digest count
**Click:** Navigate to `/thesis/{id}`
**Card width:** Full width (1 column)

#### Action Card (Full Page)

Reuse existing `ActionCard.tsx` component with the current card-depth treatment. No change needed -- the existing action cards are well-designed.

#### Digest Card (Full Page)

Reuse existing digest list item styling from the home page. Add channel badge and relevance score.

### 2.5 Search Results API Enhancement

The current `/api/search` route only searches actions, thesis, digests, and companies. Enhance to include network (people) and portfolio.

**New `SearchResult` type (extend existing):**

```typescript
export interface SearchResult {
  id: number;
  type: "action" | "thesis" | "digest" | "company" | "person" | "portfolio";
  title: string;
  subtitle: string | null;
  snippet: string | null;
  score: number;
  metadata: Record<string, unknown>;
  url: string;
}
```

**New `SearchResponse` type (extend existing):**

```typescript
export interface SearchResponse {
  results: SearchResult[];
  counts: Record<string, number>;  // NEW: count per type
  query: string;
  method: "hybrid" | "text";
  total: number;
}
```

**API route changes (`/api/search/route.ts`):**
1. Accept `type` filter parameter to scope to a single entity type
2. Accept `limit` and `offset` for pagination on the full results page
3. Return `counts` object with result count per type (for tab badges)
4. Add network and portfolio tables to the search function

**Search function changes (`search.ts`):**

Add two new search branches in `textSearchAll`:

```typescript
// Search network (people)
if (tables.includes("network")) {
  // Search: full_name, role, current_company
  // Return: full_name as title, role + company as subtitle
  // Metadata: relationship_strength, last_meeting_date
  // URL: /search?entity=person&id={id} (or open PersonBrief)
}

// Search portfolio
if (tables.includes("portfolio")) {
  // Search: portfolio_co
  // Return: portfolio_co as title, health + today as subtitle
  // Metadata: health, today, current_stage, ownership_pct, entry_cheque
  // URL: /portfolio/{id}
}
```

**Hybrid search RPC changes:**
The existing `hybrid_search` Postgres function needs extension to include network and portfolio tables. This requires a Supabase migration. If the RPC cannot be modified immediately, the text fallback handles all 6 types.

### 2.6 Fuzzy Matching

The current search uses ILIKE (exact substring match). For a 4,635 company database, typo tolerance is critical.

**Strategy -- trigram similarity (pg_trgm):**

Postgres already supports `pg_trgm` via Supabase. Add a trigram index to searchable text columns:

```sql
-- Companies
CREATE INDEX idx_companies_name_trgm ON companies USING gin (name gin_trgm_ops);

-- Network
CREATE INDEX idx_network_name_trgm ON network USING gin (full_name gin_trgm_ops);
CREATE INDEX idx_network_company_trgm ON network USING gin (current_company gin_trgm_ops);

-- Portfolio
CREATE INDEX idx_portfolio_name_trgm ON portfolio USING gin (portfolio_co gin_trgm_ops);
```

**Query pattern:**
```sql
SELECT *, similarity(name, $1) AS sim
FROM companies
WHERE name % $1 OR name ILIKE '%' || $1 || '%'
ORDER BY sim DESC, name
LIMIT 10;
```

The `%` operator (trigram similarity) provides typo tolerance. Combined with ILIKE for exact substring matches (which users expect to always work).

**Threshold:** `SET pg_trgm.similarity_threshold = 0.2;` (permissive -- better to show a fuzzy match than nothing)

**Client-side fuzzy (fallback):**
If the RPC/trigram approach is not available, implement client-side fuzzy matching using a simple Levenshtein distance for short queries (< 3 words). Cache the full entity name list (companies + people) client-side on first load (~200KB for 8,000 names). This is acceptable for a single-user app.

### 2.7 State Management

```typescript
interface SearchPageState {
  query: string;
  activeTab: "all" | "company" | "person" | "portfolio" | "thesis" | "action" | "digest";
  results: SearchResult[];
  counts: Record<string, number>;
  loading: boolean;
  sortBy: "relevance" | "name" | "date_newest" | "date_oldest";
  page: number;        // For pagination
  hasMore: boolean;    // Whether more results exist
}
```

**URL state:** Query params drive the page state. `?q=anthropic&tab=company&sort=name&page=2` is a valid URL that restores full state on reload.

**Data fetching:** Server component does initial fetch based on URL params. Client component handles subsequent tab switches, pagination, and sort changes via the existing POST `/api/search` endpoint.

---

## 3. Entity Detail Views

### 3.1 Architecture Decision: Panel vs Page

Entity detail views use a **responsive panel pattern**:
- **Desktop (>= 1024px):** Right-side sheet panel (480px wide), similar to existing `CompanyBrief.tsx`. Content area shifts left to make room.
- **Tablet (768-1023px):** Full-width overlay sheet from right.
- **Mobile (< 768px):** Bottom drawer (Vaul), swipe-down to dismiss.

**Why panel over page navigation:**
- Preserves search context (user can see results behind the panel)
- Faster back-and-forth between entities
- Consistent with the existing CompanyBrief pattern
- Keyboard shortcut `Escape` to close, no browser back needed

**Exception:** Thesis detail uses the existing full page (`/thesis/{id}`) because it has too much content for a panel. The panel shows a thesis summary card with a "View full detail" link.

### 3.2 Company Detail View

Extends the existing `CompanyBrief.tsx` with additional sections. The CompanyBrief is already well-designed (728 lines) with health badge, metrics grid, founders, thesis connections, and actions.

**New sections to add:**

#### Connection Graph Strip

A horizontal bar showing all connected entities with counts:

```
┌─────────────────────────────────────────────────────────┐
│  [5 People]  [2 Thesis]  [3 Actions]  [1 Portfolio]    │
│  [2 Digests]                                            │
└─────────────────────────────────────────────────────────┘
```

Each badge is clickable: scrolls to that section within the panel.

#### Intelligence Section

```
+----------------------------------------------------------+
|  --- INTELLIGENCE ----------------------------------------  |
|  Bucket: Discover New (Bucket 1)    Confidence: 0.87      |
|  Pipeline: Active Tracking                                 |
|                                                           |
|  Thesis Relevance:                                         |
|  AI Agents           ████████░░  0.92  (explicit)         |
|  Foundation Models   █████░░░░░  0.61  (vector)           |
|  Developer Tools     ███░░░░░░░  0.38  (text_overlap)     |
+----------------------------------------------------------+
```

**Data source:** `fetchActionBucket()` for bucket routing, `fetchActionThesisRelevance()` for thesis relevance scores, `fetchRelatedCompanies()` for similar companies.

#### Activity Timeline

Chronological interleaving of all interactions with this company:

```
+----------------------------------------------------------+
|  --- TIMELINE --------------------------------------------  |
|  Mar 18  [action]  Investigate enterprise adoption  [P0]  |
|  Mar 15  [digest]  "The State of AI Agents 2026"          |
|  Mar 12  [action]  Schedule call with Dario       [P1]    |
|  Mar 10  [thesis]  Evidence added to AI Agents thread     |
|  Mar 05  [digest]  "Anthropic Series D Deep Dive"         |
+----------------------------------------------------------+
```

**Data source:** Combine results from `fetchPortfolioActions()`, thesis mentions via `fetchPortfolioThesis()`, and digest mentions. Sort by date descending. Each entry links to its entity detail.

**Timeline entry anatomy:**
- Date: `font-mono text-[10px]`, muted
- Type badge: Colored dot matching entity type color
- Description: `text-[13px]`, t1
- Metadata: Priority badge for actions, channel for digests
- Vertical connector line between entries (2px, colored by type)

#### Research File Preview

If `research_file_path` exists on the portfolio entry, show a preview of the deep research file:

```
+----------------------------------------------------------+
|  --- DEEP RESEARCH (available) ---------------------------  |
|  20-page research file last updated Mar 15, 2026         |
|  Sections: Market Analysis, Competitive Landscape,        |
|            Technical Moat Assessment, Financial Model      |
|  [Open Full Research]                                      |
+----------------------------------------------------------+
```

**Note:** This section is a stub for now -- deep research files live on disk, not in Postgres. The panel shows the existence and links to the file. Full rendering is a v2 feature.

### 3.3 Person Detail View (New)

A new `PersonBrief.tsx` component, modeled after `CompanyBrief.tsx`. Opens as a right panel (desktop) or bottom drawer (mobile).

#### Wireframe

```
+----------------------------------------------------------+
|  [Open full page ->]                              [X]     |
|                                                           |
|  [DA]  Dario Amodei                                       |
|  CEO @ Anthropic                                          |
|  [Strong]  [LinkedIn ->]                                  |
|                                                           |
|  --- KEY INFO --------------------------------------------  |
|  ┌──────────────┐  ┌──────────────┐                      |
|  │ Relationship  │  │ Last Meeting │                      |
|  │ Strong        │  │ Mar 12       │                      |
|  └──────────────┘  └──────────────┘                      |
|                                                           |
|  --- COMPANIES -------------------------------------------  |
|  Anthropic (current)                [-> company detail]   |
|                                                           |
|  --- THESIS CONNECTIONS ----------------------------------  |
|  AI Agents            Active | High    [-> thesis]        |
|  Foundation Models    Active | Medium  [-> thesis]        |
|                                                           |
|  --- RECENT ACTIONS --------------------------------------  |
|  Schedule call with Dario    P1 | Proposed  [-> action]   |
|  Follow up on partnership    P2 | Accepted  [-> action]   |
|                                                           |
|  --- NETWORK ---------------------------------------------  |
|  Also at Anthropic:                                       |
|  [DC] Daniela Clark   COO        Medium                  |
|  [JC] Janine Clark    VP Eng     Medium                  |
|                                                           |
|  [View Full Profile]                                      |
+----------------------------------------------------------+
```

#### Data Requirements

```typescript
interface PersonBriefData {
  person: NetworkRow;
  companies: Array<{
    id: number;
    name: string;
    isCurrent: boolean;
    // From portfolio if linked
    health?: string;
    today?: string;
  }>;
  thesisConnections: Array<{
    id: number;
    thread_name: string;
    conviction: string | null;
    status: string | null;
  }>;
  recentActions: Array<{
    id: number;
    action: string;
    priority: string;
    status: string;
  }>;
  networkPeers: Array<{
    id: number;
    full_name: string | null;
    role: string | null;
    relationship_strength: string | null;
  }>;
}
```

**API endpoint:** New route `GET /api/network/{id}/brief` that fetches the person, their company, related thesis threads (via company name matching against `key_companies`), actions mentioning them (via `action.ilike.%name%`), and other people at the same company.

#### Cross-Entity Navigation

Every entity link within a person brief is clickable and opens the corresponding brief panel:
- Company name -> CompanyBrief panel
- Thesis thread -> Navigate to `/thesis/{id}`
- Action -> Navigate to `/actions/{id}` or ActionDetailSheet
- Network peer -> Replace current PersonBrief with the peer's brief (panel content swaps, back button appears)

**Panel navigation stack:**
Maintain a simple stack of `{ type, id }` entries. Clicking a linked entity pushes to the stack. A back arrow appears in the panel header. Escape pops the stack or closes the panel if stack is empty.

```typescript
interface PanelState {
  stack: Array<{ type: "company" | "person"; id: number }>;
  currentIndex: number;
}
```

### 3.4 Thesis Detail (Enhanced Summary Card)

Thesis threads have their own full page (`/thesis/{id}`) per the existing implementation and the product design spec. When accessed from search, the panel shows a summary card instead of the full command center.

```
+----------------------------------------------------------+
|  AI Agents Will Transform Enterprise Software             |
|  [Active]  [SaaS Infrastructure]  [AI/ML]                |
|                                                           |
|  CONVICTION: ━━━━━━━━━━━━━━━━░░░░ High  (+0.3 in 14d)   |
|                                                           |
|  "Enterprise adoption of AI agents is accelerating..."    |
|                                                           |
|  Evidence: 12 FOR | 3 AGAINST                             |
|  ████████████████░░░░░ (ratio bar)                        |
|                                                           |
|  Key Questions: 3 open, 1 answered                        |
|  Connected: 5 actions, 8 digests, 4 companies             |
|                                                           |
|  [View Full Thesis Command Center ->]                     |
+----------------------------------------------------------+
```

This is a read-only preview. All editing happens on the full thesis page.

---

## 4. Cross-Entity Graph

### 4.1 Design Direction

A visual force-directed graph showing how entities connect. This is a **v2 feature** -- not MVP. But the data model and link infrastructure should be built now so the graph can be layered on later.

### 4.2 Entity Linkage Model

The graph needs explicit edges. Currently, linkages are implicit (text matching, ILIKE queries). Define an explicit link model:

```typescript
interface EntityLink {
  sourceType: "company" | "person" | "portfolio" | "thesis" | "action" | "digest";
  sourceId: number;
  targetType: "company" | "person" | "portfolio" | "thesis" | "action" | "digest";
  targetId: number;
  linkType: string;       // e.g., "works_at", "thesis_relevance", "mentioned_in"
  strength: number;       // 0.0 - 1.0
  metadata?: Record<string, unknown>;
}
```

**Known link types and their data sources:**

| Link Type | Source -> Target | Data Source | Strength Metric |
|-----------|-----------------|-------------|-----------------|
| `works_at` | Person -> Company | network.current_company ILIKE company.name | 1.0 (explicit) |
| `founded` | Person -> Portfolio | portfolio.led_by_ids contains person.id | 1.0 (explicit) |
| `thesis_relevance` | Company -> Thesis | thesis.key_companies ILIKE company.name | Vector similarity score |
| `thesis_relevance` | Action -> Thesis | action.thesis_connection = thesis.thread_name | 1.0 (explicit) |
| `source_content` | Action -> Digest | action.source_content ILIKE digest.slug | 1.0 (explicit) |
| `portfolio_of` | Portfolio -> Company | portfolio.company_name_ids | 1.0 (explicit) |
| `mentioned_in` | Company -> Digest | digest.digest_data JSON contains company name | Text match confidence |
| `mentioned_in` | Company -> Action | action.action ILIKE company.name | Text match confidence |
| `related_company` | Company -> Company | find_related_companies RPC | Vector similarity score |

### 4.3 Graph Visualization (v2 Spec)

**Technology:** `@visx/network` (visx) or `d3-force` for the layout engine. SVG rendering for crisp display on all DPIs.

**Node types with visual encoding:**

| Entity Type | Shape | Size | Color | Label |
|-------------|-------|------|-------|-------|
| Company | Circle | 20-40px (by action count) | `--color-green` | Company name |
| Person | Circle with border | 16-28px | `--color-cyan` | Initials |
| Portfolio | Circle with fill | 24-36px (by ownership %) | `--color-amber` | Company name |
| Thesis | Diamond | 28-40px (by evidence count) | `--color-violet` | Thread name (truncated) |
| Action | Small circle | 8-12px | `--color-flame` | Hidden (tooltip only) |
| Digest | Small circle | 8-12px | `--color-cyan` | Hidden (tooltip only) |

**Edge types:**

| Link Type | Style | Color |
|-----------|-------|-------|
| `works_at` | Solid, 2px | `--color-t3` |
| `founded` | Solid, 3px | `--color-amber` |
| `thesis_relevance` | Dashed, 1.5px | `--color-violet` |
| `source_content` | Dotted, 1px | `--color-cyan` |
| `portfolio_of` | Solid, 2.5px | `--color-amber` |
| `mentioned_in` | Dotted, 1px, low opacity | `--color-t3` at 0.3 |

**Interactions:**
- Click node: Opens entity detail panel (right side)
- Hover node: Highlights all connected edges and nodes
- Drag node: Repositions (d3-force allows pinning)
- Scroll: Zoom
- Double-click: Center and zoom to node
- Filter controls: Toggle entity types on/off, filter by thesis thread

**Layout:**
- Full viewport minus navigation
- Force simulation: charge -300, link distance 100, collision radius = node size + 10
- Simulation runs for 300 ticks then stops (no perpetual motion)
- Nodes cluster naturally by connectivity

**Performance guardrails:**
- Max 500 nodes rendered simultaneously
- Actions and digests hidden by default (shown on hover of connected entity)
- Canvas rendering fallback if > 200 nodes (SVG performance degrades)
- Debounce zoom/pan events at 16ms (60fps)

### 4.4 Graph Route

```
/graph                    -- Full graph, all entities
/graph?thesis=3           -- Filtered to thesis ID 3 and connected entities
/graph?company=42         -- Centered on company 42
/graph?person=17          -- Centered on person 17
```

---

## 5. Component Hierarchy

### 5.1 New Components Required

```
src/components/
  search/
    CommandPaletteV2.tsx          -- Enhanced command palette (replaces CommandPalette.tsx)
    SearchResultRow.tsx           -- Single result row (used in palette and full page)
    SearchResultCard.tsx          -- Rich card (used on full page)
    SearchInput.tsx               -- Shared search input with scope badge
    ScopeFilterBadge.tsx          -- Dismissable type filter badge
    SearchTabs.tsx                -- Tab bar with count badges
    SearchPage.tsx                -- Full search results page client component
    RecentSearches.tsx            -- Recent + frequently accessed section
    AccessTracker.ts              -- localStorage access tracking utility

  entity/
    PersonBrief.tsx               -- Person detail panel (new, mirrors CompanyBrief)
    EntityPanel.tsx               -- Responsive wrapper: Sheet (desktop) / Drawer (mobile)
    EntityPanelStack.tsx          -- Navigation stack manager for panel drill-through
    ConnectionGraph.tsx           -- Entity link count strip (horizontal badges)
    ActivityTimeline.tsx          -- Chronological activity feed per entity
    IntelligenceSection.tsx       -- Bucket routing + thesis relevance display

  graph/
    EntityGraph.tsx               -- Force-directed graph (v2)
    GraphControls.tsx             -- Filter/zoom controls (v2)
    GraphNode.tsx                 -- Node renderer (v2)
    GraphEdge.tsx                 -- Edge renderer (v2)
```

### 5.2 Modified Existing Components

```
src/components/
  CommandPalette.tsx              -- REPLACE with search/CommandPaletteV2.tsx
  CompanyBrief.tsx                -- ADD: ConnectionGraph, ActivityTimeline, IntelligenceSection

src/lib/supabase/
  search.ts                      -- ADD: network and portfolio search functions
  types.ts                       -- ADD: PersonBriefData, enhanced SearchResult type

src/app/
  search/page.tsx                -- NEW: Full search results page
  api/search/route.ts            -- MODIFY: Add type filter, pagination, counts
  api/network/[id]/brief/route.ts -- NEW: Person brief data endpoint
```

### 5.3 Shared Utilities

```
src/lib/
  search/
    access-tracker.ts            -- localStorage access frequency tracking
    fuzzy.ts                     -- Client-side fuzzy matching (Levenshtein fallback)
    parse-query.ts               -- Query parsing (scope prefix extraction)
    entity-links.ts              -- Entity linkage resolver (for graph + connection counts)
```

---

## 6. Data Requirements Per View

### 6.1 Command Palette (Instant Search)

| Data Needed | Source | Latency Budget |
|-------------|--------|---------------|
| Search results (all 6 types) | POST `/api/search` -> `hybrid_search` RPC or `textSearchAll` | < 300ms total |
| Result counts per type | Same response, `counts` field | Included |
| Recent searches | localStorage | 0ms (sync) |
| Frequently accessed | localStorage | 0ms (sync) |
| Commands list | Static (hardcoded) | 0ms |
| Pending action count | Cached from last fetch or dedicated RPC | < 100ms |

### 6.2 Search Results Page

| Data Needed | Source | Latency Budget |
|-------------|--------|---------------|
| Paginated results for active tab | POST `/api/search` with type + offset + limit | < 500ms |
| Counts for all tabs | Same response, `counts` field | Included |
| Entity connection counts (for cards) | Computed server-side per result | Included in search response metadata |

### 6.3 Company Detail Panel

| Data Needed | Source | Latency Budget |
|-------------|--------|---------------|
| Company base data | Existing CompanyBrief API (`/api/portfolio/{id}/brief`) | < 300ms |
| Linked thesis threads | `fetchPortfolioThesis(companyName)` | Included in brief |
| Linked people | `fetchCompanyFounders(company)` | Included in brief |
| Recent actions | `fetchPortfolioActions(companyName)` | Included in brief |
| Bucket routing | `fetchActionBucket(actionId)` -- per action | Lazy load |
| Thesis relevance scores | `fetchActionThesisRelevance(actionId)` | Lazy load |
| Activity timeline | Aggregate of actions + thesis mentions + digest mentions | < 500ms |

### 6.4 Person Detail Panel

| Data Needed | Source | Latency Budget |
|-------------|--------|---------------|
| Person base data | `network` table by ID | < 200ms |
| Current company details | `companies` or `portfolio` table by name match | Included |
| Thesis connections | `thesis_threads` where key_companies ILIKE company name | < 300ms |
| Recent actions | `actions_queue` where action/reasoning ILIKE person name | < 300ms |
| Network peers | `network` where current_company matches | < 200ms |
| Combined brief | NEW API: `/api/network/{id}/brief` | < 500ms total |

### 6.5 Entity Graph (v2)

| Data Needed | Source | Latency Budget |
|-------------|--------|---------------|
| All entity nodes (filtered) | Batch query across all tables | < 1000ms |
| All entity links | Computed from linkage rules | < 1000ms |
| Total: < 500 nodes + edges | Server-side aggregation | < 2000ms first load |

---

## 7. Supabase Migration Requirements

### 7.1 Immediate (for search MVP)

```sql
-- 1. Enable pg_trgm extension (if not already)
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- 2. Add trigram indexes for fuzzy search
CREATE INDEX IF NOT EXISTS idx_network_fullname_trgm
  ON network USING gin (full_name gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_network_company_trgm
  ON network USING gin (current_company gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_portfolio_name_trgm
  ON portfolio USING gin (portfolio_co gin_trgm_ops);

-- 3. Add text search indexes (FTS) for network and portfolio
CREATE INDEX IF NOT EXISTS idx_network_fullname_fts
  ON network USING gin (to_tsvector('english', coalesce(full_name, '')));

CREATE INDEX IF NOT EXISTS idx_portfolio_name_fts
  ON portfolio USING gin (to_tsvector('english', coalesce(portfolio_co, '')));
```

### 7.2 Enhanced hybrid_search RPC (extend existing)

The existing `hybrid_search` RPC handles actions, thesis, digests, and companies. Extend it to include network and portfolio:

```sql
-- Add to the existing hybrid_search function body:

-- Network people search
UNION ALL
SELECT
  n.id,
  'person'::text AS result_type,
  n.full_name AS title,
  COALESCE(n.role, '') || ' @ ' || COALESCE(n.current_company, '') AS subtitle,
  NULL AS snippet,
  -- Score: combination of text similarity + relationship strength bonus
  (CASE WHEN n.full_name ILIKE '%' || search_query || '%' THEN 10 ELSE 0 END
   + CASE WHEN n.current_company ILIKE '%' || search_query || '%' THEN 5 ELSE 0 END
   + CASE WHEN n.relationship_strength = 'Strong' THEN 3
          WHEN n.relationship_strength = 'Medium' THEN 1
          ELSE 0 END
  )::real AS score,
  jsonb_build_object(
    'relationship_strength', n.relationship_strength,
    'last_meeting_date', n.last_meeting_date,
    'role', n.role,
    'current_company', n.current_company
  ) AS metadata,
  '/search?entity=person&id=' || n.id AS url
FROM network n
WHERE (filter_tables IS NULL OR 'network' = ANY(filter_tables))
  AND (n.full_name ILIKE '%' || search_query || '%'
       OR n.current_company ILIKE '%' || search_query || '%'
       OR n.role ILIKE '%' || search_query || '%')

-- Portfolio search
UNION ALL
SELECT
  p.id,
  'portfolio'::text AS result_type,
  p.portfolio_co AS title,
  COALESCE(p.health, 'Unknown') || ' | ' || COALESCE(p.today, 'Unknown') AS subtitle,
  NULL AS snippet,
  (CASE WHEN p.portfolio_co ILIKE '%' || search_query || '%' THEN 10 ELSE 0 END
   + CASE WHEN p.health = 'Green' THEN 3
          WHEN p.health = 'Yellow' THEN 1
          ELSE 0 END
  )::real AS score,
  jsonb_build_object(
    'health', p.health,
    'today', p.today,
    'current_stage', p.current_stage,
    'ownership_pct', p.ownership_pct,
    'entry_cheque', p.entry_cheque,
    'follow_on_decision', p.follow_on_decision
  ) AS metadata,
  '/portfolio/' || p.id AS url
FROM portfolio p
WHERE (filter_tables IS NULL OR 'portfolio' = ANY(filter_tables))
  AND p.portfolio_co ILIKE '%' || search_query || '%'
```

### 7.3 Deferred (for graph v2)

```sql
-- Entity links materialized view
-- Precomputes all cross-entity relationships for graph rendering
CREATE MATERIALIZED VIEW entity_links AS
  -- person -> company (works_at)
  SELECT
    'person' AS source_type, n.id AS source_id,
    'company' AS target_type, c.id AS target_id,
    'works_at' AS link_type,
    1.0 AS strength
  FROM network n
  JOIN companies c ON n.current_company ILIKE '%' || c.name || '%'

  UNION ALL

  -- thesis -> company (relevance)
  -- Derived from thesis.key_companies text field
  -- Implementation depends on structured key_companies data

  UNION ALL

  -- action -> thesis (connection)
  SELECT
    'action' AS source_type, a.id AS source_id,
    'thesis' AS target_type, t.id AS target_id,
    'thesis_connection' AS link_type,
    1.0 AS strength
  FROM actions_queue a
  JOIN thesis_threads t ON a.thesis_connection ILIKE '%' || t.thread_name || '%'
  WHERE a.thesis_connection IS NOT NULL;

-- Refresh periodically
-- REFRESH MATERIALIZED VIEW CONCURRENTLY entity_links;
```

---

## 8. Performance Budget

| Interaction | Target | Measurement Point |
|-------------|--------|-------------------|
| Palette open | < 100ms | From keydown to input focused |
| First result visible | < 450ms | From first keystroke (150ms debounce + 300ms API) |
| Full results page load | < 800ms | From navigation to first content paint |
| Entity panel open | < 400ms | From click to panel visible with data |
| Graph render (v2) | < 2000ms | From navigation to stable graph layout |
| Fuzzy match (client) | < 50ms | From keystroke to filtered results |

**Optimization strategies:**

1. **Debounce:** 150ms for palette (down from 300ms). Short enough to feel instant, long enough to avoid flooding the server.

2. **Prefetch:** When palette opens, prefetch counts for all entity types with an empty-string count query. This makes tab badge counts appear immediately on the full results page.

3. **Stale-while-revalidate:** Cache search results client-side (Map<queryHash, { results, timestamp }>). Show stale results immediately while fetching fresh ones. TTL: 30 seconds.

4. **Progressive loading:** On the full results page, fetch the active tab first (< 300ms), then fetch counts for other tabs in the background.

5. **Entity panel cache:** Cache the last 5 entity brief responses. If the user clicks the same entity again, show cached data immediately while revalidating.

6. **Name list cache (for fuzzy):** Fetch all company + person names on first palette open. Store in a module-level variable. ~200KB for 8,000 names. Revalidate every 5 minutes.

---

## 9. Accessibility

### 9.1 Command Palette

- `role="dialog"` with `aria-modal="true"` on the palette container
- `role="combobox"` on the search input with `aria-expanded`, `aria-controls`, `aria-activedescendant`
- `role="listbox"` on the results container
- `role="option"` on each result row with `aria-selected` for the active item
- `role="group"` on each section with `aria-label` set to the section name
- Screen reader announcement when results change: `aria-live="polite"` region with "N results found" text
- Focus trap within the palette when open
- Scope badge: `aria-label="Searching in Companies. Press backspace to remove filter."`

### 9.2 Entity Panels

- `role="dialog"` with `aria-modal="true"` and `aria-label` set to entity name
- Focus moves to panel when it opens, returns to trigger when it closes
- Panel navigation stack: back button has `aria-label="Go back to previous entity"`
- All link badges have descriptive aria-labels: "View thesis: AI Agents Will Transform Enterprise Software"

### 9.3 Search Results Page

- Tab bar uses `role="tablist"` with `role="tab"` and `role="tabpanel"`
- Count badges use `aria-label`: "Companies tab, 4 results"
- Sort controls are accessible as `<select>` elements with labels
- Pagination uses `aria-label="Page 2 of 5"` on navigation controls

### 9.4 Color Independence

Every piece of information encoded in color is also encoded in text:
- Entity type: Icon + color + text label
- Priority: `P0` text + flame color
- Health: `Green` text + green color
- Relationship: `Strong` text + green badge
- Conviction: `High` text + green bar

---

## 10. Implementation Priority

### Phase A: Search MVP (extends current palette)

**Scope:** Get all 6 entity types searchable from the command palette. Minimum viable rich results.

| Task | Files | Effort | Depends On |
|------|-------|--------|------------|
| A1. Add network/portfolio to `textSearchAll` | `search.ts` | S | -- |
| A2. Extend `SearchResult` type for person + portfolio | `types.ts` | XS | -- |
| A3. Update `/api/search` with type filter + counts | `route.ts` | S | A1, A2 |
| A4. Extend `hybrid_search` RPC (Supabase migration) | SQL migration | M | -- |
| A5. Add trigram indexes (Supabase migration) | SQL migration | S | -- |
| A6. Update `CommandPalette.tsx` for 6 types + rich rows | `CommandPalette.tsx` | M | A3 |
| A7. Reduce debounce to 150ms | `CommandPalette.tsx` | XS | A6 |
| A8. Add scope prefix parsing (`c:`, `p:`, etc.) | `CommandPalette.tsx` + `parse-query.ts` | S | A6 |

### Phase B: Full Search Page

| Task | Files | Effort | Depends On |
|------|-------|--------|------------|
| B1. Create `/search/page.tsx` route | New page | M | A3 |
| B2. Build `SearchTabs` with count badges | New component | S | B1 |
| B3. Build `SearchResultCard` per entity type | New component | M | B1 |
| B4. Add Cmd+Enter to navigate to full results | `CommandPalette.tsx` | XS | B1 |
| B5. URL state management (query params) | `SearchPage.tsx` | S | B1 |
| B6. Pagination | `SearchPage.tsx` + API | S | B5 |

### Phase C: Entity Detail Panels

| Task | Files | Effort | Depends On |
|------|-------|--------|------------|
| C1. Create `PersonBrief.tsx` (mirrors CompanyBrief) | New component | M | A1 |
| C2. Create `/api/network/{id}/brief` endpoint | New route | S | C1 |
| C3. Add `ActivityTimeline` to CompanyBrief | New component | M | -- |
| C4. Add `ConnectionGraph` strip to CompanyBrief | New component | S | -- |
| C5. Add `IntelligenceSection` to CompanyBrief | New component | M | -- |
| C6. Build `EntityPanelStack` for drill-through navigation | New component | S | C1 |
| C7. Wire person results to PersonBrief panel | `CommandPalette.tsx` | S | C1, C6 |

### Phase D: Intelligence & Polish

| Task | Files | Effort | Depends On |
|------|-------|--------|------------|
| D1. Frequently accessed tracking | `access-tracker.ts` | S | -- |
| D2. Command mode (`>` prefix) | `CommandPalette.tsx` | S | A8 |
| D3. Escape cascade (clear query first) | `CommandPalette.tsx` | XS | A6 |
| D4. Client-side fuzzy matching fallback | `fuzzy.ts` | S | -- |
| D5. Search result animations (staggered reveal) | `CommandPalette.tsx` | XS | A6 |

### Phase E: Entity Graph (v2)

| Task | Files | Effort | Depends On |
|------|-------|--------|------------|
| E1. Entity links materialized view | SQL migration | M | A4 |
| E2. Graph data endpoint | New API route | M | E1 |
| E3. `EntityGraph` component with d3-force | New component | L | E2 |
| E4. Graph route `/graph` | New page | S | E3 |
| E5. Filter controls (by thesis, entity type) | New component | S | E4 |

### Why This Order

- **Phase A** is the highest-leverage change. Going from 4 searchable types to 6 (adding 3,728 people and 142 portfolio companies) transforms the palette from "search content" to "search everything."
- **Phase B** gives users a place to land when they want comprehensive results, not just a quick lookup.
- **Phase C** makes search results actionable -- clicking a person or company shows their full context and connections.
- **Phase D** adds the refinements that make search feel world-class (fuzzy matching, access tracking, commands).
- **Phase E** is the visualization layer that makes the intelligence graph tangible. Deferred because it requires the most new infrastructure and the entity links need to be reliable first.

---

## Appendix A: shadcn/ui Component Mapping

| Search Feature | shadcn Component | Notes |
|----------------|-----------------|-------|
| Command palette wrapper | `Command` + `CommandDialog` | Replace hand-built palette |
| Search input | `CommandInput` | Built-in keyboard nav |
| Result groups | `CommandGroup` + `CommandSeparator` | Section headers with dividers |
| Result rows | `CommandItem` | Auto-filtering, keyboard selection |
| Empty state | `CommandEmpty` | "No results found" |
| Shortcut hints | `CommandShortcut` + `Kbd` | Right-aligned key badges |
| Entity panel (desktop) | `Sheet` | Right-side slide-in |
| Entity panel (mobile) | `Drawer` | Bottom swipe-up (Vaul) |
| Tab bar | `Tabs` + `TabsList` + `TabsTrigger` | With count badges |
| Scope filter badge | `Badge` (dismissable variant) | Colored by type |
| Loading states | `Skeleton` + `Spinner` | Card-shaped skeletons |
| Tooltips on graph nodes | `Tooltip` + `TooltipContent` | Entity preview on hover |
| Sort dropdown | `Select` | Relevance, name, date |

**Decision: Replace or enhance `CommandPalette.tsx`?**

Replace. The current component is a hand-built dialog (585 lines). The shadcn `Command` component (based on cmdk) provides built-in fuzzy filtering, keyboard navigation, section grouping, and empty states. Migrating to it reduces code by ~40% while gaining features. The existing TYPE_CONFIG, recent search logic, and CompanyBrief integration transfer directly.

---

## Appendix B: Search Response Schema (Full)

```typescript
// POST /api/search
// Request
interface SearchRequest {
  query: string;                    // Search text (max 200 chars)
  filters?: {
    tables?: string[];              // Scope to specific types
    status?: string;                // For actions
    date_from?: string;             // ISO date
    date_to?: string;               // ISO date
    thesis_id?: number;             // Filter by thesis connection
    relationship_strength?: string; // For people
    health?: string;                // For portfolio
  };
  limit?: number;                   // Default: 20, max: 50
  offset?: number;                  // For pagination
  include_counts?: boolean;         // Return counts per type (default: true)
}

// Response
interface SearchResponse {
  results: SearchResult[];
  counts: {
    company: number;
    person: number;
    portfolio: number;
    thesis: number;
    action: number;
    digest: number;
    total: number;
  };
  query: string;
  method: "hybrid" | "text" | "trigram";
  total: number;
  has_more: boolean;
}

interface SearchResult {
  id: number;
  type: "action" | "thesis" | "digest" | "company" | "person" | "portfolio";
  title: string;
  subtitle: string | null;
  snippet: string | null;
  score: number;
  metadata: Record<string, unknown>;
  url: string;
}
```

---

## Appendix C: Entity Counts (Current)

| Entity Type | Count | Postgres Table | Indexed for Search |
|-------------|-------|----------------|-------------------|
| Companies | 4,635 | `companies` | Partial (hybrid_search RPC) |
| Network (People) | 3,728 | `network` | No (needs migration) |
| Portfolio | 142 | `portfolio` | No (needs migration) |
| Thesis Threads | 8 | `thesis_threads` | Yes (hybrid_search RPC) |
| Actions | 115 | `actions_queue` | Yes (hybrid_search RPC) |
| Content Digests | 22 | `content_digests` | Yes (hybrid_search RPC) |
| **Total** | **8,650** | | |

The search must handle 8,650 entities across 6 types. The largest tables (companies: 4,635, network: 3,728) need trigram indexes for acceptable fuzzy search performance.

---

## Appendix D: Design Token Reference (Search-Specific)

| Element | Token | Value |
|---------|-------|-------|
| Palette backdrop | `rgba(0,0,0,0.6)` + `backdrop-filter: blur(4px)` | Existing |
| Palette card bg | `var(--color-card)` = `#0f0f16` | Existing |
| Palette border | `rgba(255,255,255,0.08)` | Existing |
| Selected result bg | `rgba(255,255,255,0.04)` | Existing |
| Scope badge (company) | `bg: rgba(105,240,174,0.1)`, `text: var(--color-green)` | New |
| Scope badge (person) | `bg: rgba(0,229,255,0.08)`, `text: var(--color-cyan)` | New |
| Scope badge (portfolio) | `bg: rgba(255,171,0,0.08)`, `text: var(--color-amber)` | New |
| Scope badge (thesis) | `bg: rgba(179,136,255,0.08)`, `text: var(--color-violet)` | New |
| Scope badge (action) | `bg: rgba(255,87,34,0.08)`, `text: var(--color-flame)` | New |
| Scope badge (digest) | `bg: rgba(0,229,255,0.08)`, `text: var(--color-cyan)` | New |
| Tab active | `border-bottom: 2px solid var(--color-flame)` | New |
| Tab count badge | `bg: rgba(255,255,255,0.06)`, `text: var(--color-t2)` | New |
| Graph node hover | `filter: brightness(1.3)` + `box-shadow: 0 0 12px {type-color}` | v2 |

---

## Appendix E: File Inventory (What Exists, What's New)

### Existing Files to Modify

| File | Change | Impact |
|------|--------|--------|
| `src/components/CommandPalette.tsx` | Replace with shadcn Command or extend for 6 types | High |
| `src/lib/supabase/search.ts` | Add network + portfolio search, fuzzy matching | High |
| `src/lib/supabase/types.ts` | Add PersonBriefData, extend SearchResult type | Medium |
| `src/app/api/search/route.ts` | Add type filter, pagination, counts response | Medium |
| `src/components/CompanyBrief.tsx` | Add ConnectionGraph, Timeline, Intelligence sections | Medium |

### New Files to Create

| File | Purpose | Phase |
|------|---------|-------|
| `src/app/search/page.tsx` | Full search results page (server component) | B |
| `src/components/search/SearchPage.tsx` | Client component for search results | B |
| `src/components/search/SearchTabs.tsx` | Tab bar with count badges | B |
| `src/components/search/SearchResultCard.tsx` | Rich result card per entity type | B |
| `src/components/entity/PersonBrief.tsx` | Person detail panel | C |
| `src/components/entity/EntityPanelStack.tsx` | Panel navigation stack | C |
| `src/components/entity/ActivityTimeline.tsx` | Chronological activity feed | C |
| `src/components/entity/ConnectionGraph.tsx` | Entity link count strip | C |
| `src/components/entity/IntelligenceSection.tsx` | Bucket routing + thesis relevance | C |
| `src/app/api/network/[id]/brief/route.ts` | Person brief data endpoint | C |
| `src/lib/search/access-tracker.ts` | Frequently accessed tracking | D |
| `src/lib/search/fuzzy.ts` | Client-side fuzzy matching | D |
| `src/lib/search/parse-query.ts` | Query scope prefix parsing | A |
