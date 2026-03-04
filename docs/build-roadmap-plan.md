# AI CoS Build Roadmap — Design Plan
**Session 031 | 2026-03-04 | Plan only — no implementation**

---

## 1. The Core Question: Separate DB or Extend Actions Queue?

### Your instinct is right — separate it. Here's why, with caveats.

**Arguments FOR separation (strong):**

1. **Read/write performance for Claude.** The Actions Queue will grow with every content pipeline run, meeting, IDS review, and manual entry — hundreds of items/month. When Claude queries it to answer "what should I build next?", it would need to filter through meetings, follow-ups, research tasks, and portfolio check-ins just to find the 20-30 build items. A dedicated DB means every query returns only build-relevant items — faster, cheaper context.

2. **Schema divergence.** Build items need properties that operational actions don't: Dependencies (relation to other build items), Epic/Build Layer grouping, T-shirt sizing, Perceived Impact (multi-horizon), Technical Notes. Cramming these into Actions Queue as optional fields creates a sparse, confusing schema — most actions would have 8+ null fields.

3. **Lifecycle difference.** Operational actions have a tight cycle: Proposed → Accepted → In Progress → Done (days to weeks). Build items have a long tail: Insight → Backlog → Planned → In Progress → Testing → Shipped (weeks to months). Mixing these lifecycles in one kanban makes both harder to read.

4. **Insights-led column.** You want a dedicated suggestion funnel where the AI deposits build ideas. In the Actions Queue, "Proposed" already serves a different purpose (content-derived actions awaiting triage). Overloading "Proposed" with both "call this person" and "build a vector store" creates triage confusion.

**Arguments FOR consolidation (weak but real):**

1. **Single action sink principle.** The whole point of Actions Queue was "one place for all actions." Adding a second DB means two places to check — and the AI CoS needs to know which DB to write to.
2. **Cross-type dependencies.** Some build items generate operational actions ("research Pinecone pricing" is a Research action that serves a build item). With two DBs, you need a relation between them.

**Resolution: Fully separate, no bridge.**

Create a dedicated `Build Roadmap` database. No relation to Actions Queue — they serve completely different domains. Actions Queue = investing/operational actions (meetings, follow-ups, research, content). Build Roadmap = AI CoS product build actions. If building something requires research or a meeting, that's a build task within the roadmap, not something that spawns into the operational queue.

---

## 2. Proposed Schema: Build Roadmap DB

### Core Properties

| Property | Type | Values / Notes |
|----------|------|----------------|
| **Item** | Title | The build item name (e.g., "Semantic matching for Content Pipeline") |
| **Status** | Select | `💡 Insight` → `📋 Backlog` → `🎯 Planned` → `🔨 In Progress` → `🧪 Testing` → `✅ Shipped` → `🚫 Won't Do` |
| **Build Layer** | Select | `Signal Processor` · `Intelligence Engine` · `Operating Interface` · `Infrastructure` · `Data/Schema` · `Skills/Prompts` |
| **Epic** | Select | `Content Pipeline v5` · `Action Frontend` · `Knowledge Store` · `Multi-Surface` · `Meeting Optimizer` · `Always-On` · (+ custom) |
| **Priority** | Select | `P0 - Now` · `P1 - Next` · `P2 - Later` · `P3 - Someday` |
| **T-Shirt Size** | Select | `XS (< 1hr)` · `S (1-3hr)` · `M (3-8hr)` · `L (1-3 sessions)` · `XL (3+ sessions)` |
| **Perceived Impact** | Multi-select | `Short-term (this month)` · `Medium-term (this quarter)` · `Long-term (compounding)` |
| **Dependencies** | Relation (self) | → Build Roadmap (what must ship before this) |
| **Blocked By** | Relation (self) | → Build Roadmap (inverse of Dependencies — auto-synced via dual relation) |
| **Source** | Select | `Session Insight` · `AI CoS Relevance Note` · `User Request` · `Bug/Regression` · `Architecture Decision` · `External Inspiration` |
| **Discovery Session** | Text | Session number where this was identified (e.g., "Session 031") |
| **Technical Notes** | Text | Implementation notes, gotchas, design decisions |
| **Created Time** | Created time | Auto |
| **Last Edited** | Last edited time | Auto |

### Why these properties:

- **Build Layer** maps directly to your 3-layer architecture (Signal Processor, Intelligence Engine, Operating Interface) plus infrastructure concerns. This lets you filter "show me everything in the Intelligence Engine that's not shipped."
- **Epic** maps to your existing build order phases. New epics get added as the system evolves.
- **T-Shirt Size** over story points — you're a solo builder with AI, not a scrum team. T-shirt sizing is faster and sufficiently accurate for planning.
- **Perceived Impact** is multi-select because a single item can have short-term AND long-term impact (e.g., "build dedup guard" is short-term bug fix + long-term pipeline reliability).
- **Dependencies as self-relation** — this is the key structural feature. It enables: (a) dependency chain visualization, (b) "what's unblocked?" queries, (c) build order validation.
- **No external relations** — Build Roadmap is self-contained. No bridge to Actions Queue or Thesis Tracker. Different domains, different lifecycles, clean separation.

---

## 3. Kanban Board Design

### Columns (Status-based)

```
💡 Insight  →  📋 Backlog  →  🎯 Planned  →  🔨 In Progress  →  🧪 Testing  →  ✅ Shipped
```

The `💡 Insight` column is your **insights-led suggestion funnel** — the leftmost column that gets fed automatically and manually.

### How items enter the Insight column:

**Feed 1: AI CoS Relevance Notes (user-triggered)**
When you tell Claude "add this to the build roadmap" or "this is a build insight," Claude creates a page in the Build Roadmap DB with Status = `💡 Insight`, Source = `AI CoS Relevance Note`, and whatever context you provide.

**Feed 2: Cowork Session Observations (semi-automatic)**
At session close (Step 1 of the close checklist — writing the iteration log), Claude already identifies "meta-learnings" and "errors & fixes." The new behavior: if any meta-learning implies a build improvement, Claude also creates a Build Roadmap entry with Status = `💡 Insight`, Source = `Session Insight`, Discovery Session = current session number.

**Feed 3: Bug/Regression Discovery (automatic)**
When Claude hits a known-pattern failure (e.g., "relation format broke again"), it creates an entry with Source = `Bug/Regression` pointing to the session where it occurred.

**Feed 4: Architecture Decisions from planning sessions**
When doing system design (like this session), explicit build items get created with Source = `Architecture Decision`.

### Triage workflow:

Periodically (or on-demand via "review my build roadmap"), Claude queries the Insight column, presents items with context, and you drag them to Backlog (accepted) or Won't Do (rejected). This mirrors your existing "review my actions" pattern but for build items specifically.

### Additional Views (beyond default kanban):

1. **By Epic** — Board grouped by Epic, filtered to non-shipped. "What's left in Content Pipeline v5?"
2. **By Build Layer** — Table grouped by Build Layer. "What's the Intelligence Engine backlog?"
3. **Dependency Chain** — Table sorted by Dependencies count, showing blocked items. "What's unblocked right now?"
4. **Impact × Effort Matrix** — Table with Perceived Impact and T-Shirt Size visible. "What's high-impact + small?"

---

## 4. Integration Points

### A. Session Close Checklist (updated)

Current 5 steps remain. Add a sub-step to Step 1:

> **Step 1b:** If this session produced build insights, meta-learnings about capability gaps, or bug patterns, create entries in Build Roadmap DB with Status = `💡 Insight`.

This is lightweight — most sessions produce 0-2 insights. It's not a heavy lift, it's a habit.

### B. AI CoS Skill Update

The skill (SKILL.md) gets a new request type:

> **H. Build Roadmap Management**
> - "Review my build roadmap" / "what's unblocked?" / "what should I build next?"
> - "Add build insight: [description]"
> - "Show me the Content Pipeline v5 epic"
> → Query Build Roadmap DB. For "what should I build next?", filter to Status = Planned + no unresolved Dependencies + sort by Priority.

### C. Full Cycle Command

No change needed. Full Cycle orchestrates *operational* pipelines (content, back-propagation). Build roadmap review is a separate on-demand action, not part of the daily cycle.

### D. No Actions Queue Interaction

Build Roadmap and Actions Queue are fully independent. If a build item needs research, that's a sub-task or note within the build item itself (via Technical Notes or a child page), not a cross-DB action.

---

## 5. Seed Data: Initial Backlog from Current Build Order

These would be the initial entries, all starting at `📋 Backlog` or `🎯 Planned`:

| Item | Epic | Build Layer | Priority | T-Shirt | Status |
|------|------|-------------|----------|---------|--------|
| Full portfolio coverage (all 200 companies in matching) | Content Pipeline v5 | Intelligence Engine | P1 | L | 📋 Backlog |
| Semantic matching (embedding-based, not keyword) | Content Pipeline v5 | Intelligence Engine | P1 | XL | 📋 Backlog |
| Impact scoring model | Content Pipeline v5 | Intelligence Engine | P2 | L | 📋 Backlog |
| Multi-source ingestion (podcasts, articles, not just YT) | Content Pipeline v5 | Signal Processor | P2 | XL | 📋 Backlog |
| Accept/dismiss actions on digest pages | Action Frontend | Operating Interface | P1 | M | 📋 Backlog |
| Consolidated action dashboard on digest.wiki | Action Frontend | Operating Interface | P2 | L | 📋 Backlog |
| Notion API integration in Vercel (action status updates) | Action Frontend | Infrastructure | P1 | M | 📋 Backlog |
| Vector store for unstructured data (Pinecone/Chroma) | Knowledge Store | Intelligence Engine | P2 | XL | 📋 Backlog |
| Hybrid Notion + vector architecture design | Knowledge Store | Data/Schema | P2 | L | 📋 Backlog |
| Granola meeting integration | Multi-Surface | Signal Processor | P3 | L | 📋 Backlog |
| Email/WhatsApp signal processing | Multi-Surface | Signal Processor | P3 | XL | 📋 Backlog |
| People Scoring Model implementation | Meeting Optimizer | Intelligence Engine | P3 | L | 📋 Backlog |
| "Optimize My Trip" feature | Meeting Optimizer | Operating Interface | P3 | XL | 📋 Backlog |
| Agent SDK migration plan | Always-On | Infrastructure | P3 | XL | 📋 Backlog |
| **Build Roadmap DB setup** | Infrastructure | Data/Schema | P0 | S | 🎯 Planned |
| **Product Roadmap Notion DB creation** | Infrastructure | Data/Schema | P0 | S | 🎯 Planned |

Plus the insight items that would emerge from recent sessions (dedup improvements, back-prop optimizations, etc.).

---

## 6. What This Does NOT Replace

- **Actions Queue** — still handles all operational actions (meetings, follow-ups, research, content). No relation between the two.
- **Build order in CONTEXT.md / CLAUDE.md** — still the narrative description. The Build Roadmap DB is the queryable, structured version.
- **Iteration logs** — still the session record. Build Roadmap items reference sessions, not replace them.
- **Content Pipeline v5 plan doc** — detailed architecture docs remain separate. Build Roadmap items link to them in Technical Notes.

---

## 7. Implementation Steps (for when you approve)

1. **Create the Notion DB** — `Build Roadmap` at AI CoS root level (sibling of Actions Queue, Content Digest)
2. **Add dual self-relation** for Dependencies ↔ Blocked By
3. **Create kanban view** (default, by Status)
4. **Create "By Epic" board view**
5. **Seed initial backlog** from the table in Section 5
6. **Update CONTEXT.md** — add Build Roadmap DB ID, describe its purpose
7. **Update CLAUDE.md** — add Build Roadmap to Key Notion Database IDs, add request type H
8. **Update AI CoS skill** — add Build Roadmap triggers + request type
9. **Update session close checklist** — add Step 1b (moderately aggressive insight capture)
10. **Package updated `.skill` file** and present in Cowork

---

## 8. Resolved Decisions

1. **Parent location:** Root level (sibling of Actions Queue, Content Digest) ✅
2. **Insight capture:** Moderately aggressive — not every meta-learning, but any that clearly implies a build improvement or capability gap ✅
3. **Review cadence:** Purely on-demand ("review my build roadmap") ✅
4. **Emojis:** Keep them in Status values ✅
5. **No external relations:** Build Roadmap is fully self-contained, no bridge to Actions Queue or Thesis Tracker ✅
