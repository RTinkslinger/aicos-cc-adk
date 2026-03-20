# ENIAC APM Brief
*Associate Product Manager reference for ENIAC (Content + Thesis Agent) build*
*Last updated: 2026-03-19*

---

## What Is ENIAC

ENIAC is the **content and thesis specialist agent** within the AI CoS system. It processes content from Aakash's information surfaces, connects it to his investment thesis threads, portfolio, and network — and proposes scored actions.

ENIAC answers: **"Given what I just learned from this content, what should Aakash (or his agents) DO about it?"**

ENIAC is one of three planned agents:
- **ENIAC** — Content + thesis intelligence → action suggestions
- **Meetings Agent** (TBD) — Real-world interactions (Granola, calendar, people) → action suggestions
- **Action Strategist** (TBD) — Prioritizes and manages the action queue across all sources (ENIAC + Meetings Agent + Aakash's own inputs)

This APM brief covers ENIAC and its WebFront (digest.wiki action layer) only.

---

## The 4 Priority Buckets

Every action ENIAC proposes maps to one or more of these. They define WHY an action matters.

| # | Bucket | What It Means | Fueled By |
|---|--------|--------------|-----------|
| 1 | **New Cap Tables** | Get on amazing new companies' cap tables. Find investable companies. | **Companies DB** (not yet fully built/populated) |
| 2 | **Deepen Existing Cap Tables** | Continuous IDS on portfolio for follow-on / ownership-increase decisions. Competitive intel, market shifts, founder signals. | Portfolio DB + Companies DB |
| 3 | **DeVC Collective** | Grow the DeVC Collective pipeline: Community → External → Core. Find, qualify, and advance people through this funnel. | **Network DB** (not yet fully built/populated) |
| 4 | **Thesis Evolution** | Evolve investment thesis lines. New frameworks, contrarian views, cross-domain connections. Lower priority when conflicting with 1-3, highest when capacity exists. | Thesis Tracker |

**Important:** Buckets 1 and 3 depend on data models (Companies DB, Network DB) that are not yet fully built. Until they are, ENIAC operates with whatever context is available — but the architecture should assume these will be rich, queryable data sources.

---

## What ENIAC Does Today

### Input Sources
- **1 regular source:** YouTube playlist (20VC + curated watch list)
- **On-demand:** URLs sent via CAI → `cai_inbox` → Orchestrator → ENIAC

### Processing Pipeline
```
Content in → Fetch full text/transcript
           → Load active thesis threads from Postgres
           → Run analysis framework (6-step):
              1. Relevance assessment (which buckets?)
              2. Essence extraction (arguments, data, frameworks, quotes, predictions)
              3. Thesis connection mapping (evidence for/against, key questions)
              4. Portfolio connection check
              5. Action proposal + scoring
              6. Watch sections (video timestamps)
           → Score each action (5-factor model)
           → Publish:
              A. digest.wiki (JSON → git push → Vercel)
              B. Postgres (content_digests, actions_queue, thesis_threads, notifications)
              C. Preference store (action_outcomes for calibration)
```

### Output: The DigestData JSON
Each piece of content produces a structured digest containing:
- **Thesis connections** — per-thread: evidence direction, strength, key questions answered/raised, conviction assessment, investment implications
- **Portfolio connections** — companies mentioned/implied, conviction impact
- **Essence notes** — core arguments, data points, frameworks, key quotes, predictions
- **Contra signals** — things that challenge existing thesis views (explicitly high-value)
- **Rabbit holes** — tangential topics worth exploring
- **Watch sections** — specific timestamps worth watching (video content)
- **Connected buckets** — which priority buckets this content serves
- **Net newness** — how novel: Mostly New / Additive / Reinforcing / Contra / Mixed
- **Proposed actions** — each scored, typed, assigned, with reasoning

---

## Action Scoring — Current Heuristic

```
Score = (0.25 x bucket_impact) + (0.25 x conviction_change) + (0.20 x time_sensitivity) + (0.15 x action_novelty) + (0.15 x effort_vs_impact)
```

All factors 0-10. Thresholds: >=7 surface, 4-6 low-confidence, <4 context only.

**This is a starting heuristic, not gospel.** The APM should iterate on it as we build:
- Watch which actions Aakash rates as "Gold" vs "Dismissed" — what factor profiles do they have?
- Consider adding/removing factors as data accumulates
- Consider non-linear scoring (e.g., a single 10 on conviction_change might matter more than balanced 6s)
- The preference store (`action_outcomes` table) exists for this calibration loop

### Thesis-Weighted Modifier
Actions touching Active thesis threads get +1 on conviction_change factors. This is how Aakash's human attention signal (Status = Active) influences AI prioritization.

---

## Thesis Architecture — Direction

**Current:** Thesis threads are rows in Postgres `thesis_threads` table + Notion pages. Evidence, key questions, and implications are stored as text fields in the DB row.

**Proposed direction:** Each thesis gets its own `.md` file for the full living trail:
- Evidence blocks (append-only, timestamped, IDS notation)
- Key questions with `[OPEN]/[ANSWERED]` lifecycle
- Investment implications (evolving)
- Contra signals
- Connected companies and people

The `thesis_threads` DB table becomes a **quick-reference index** (name, conviction, status, connected buckets, last updated, file path) — not the source of truth for the detailed trail.

**Why:** Markdown is a natural format for the kind of structured-but-flowing content that thesis evidence represents. DB fields are clunky for append-only evidence trails. Files are also natively accessible to Claude agents (Read/Write tools) without psql.

**Status:** Idea stage. Needs design work before implementation.

---

## WebFront (digest.wiki) — ENIAC's Action Layer

### What Exists
- digest.wiki — SSG digest pages at `/d/{slug}`, auto-deployed on git push
- Supabase connection verified (Server Component → Mumbai, 31ms)
- 115 actions in queue, 22 digests published

### What We're Building (Phase 1A)
- `/actions` page — list actions with filters (status, priority, thesis connection) and sort
- Server Actions — `triageAction()` (accept/dismiss), `rateOutcome()` (Gold/Helpful/Unknown), `deferAction()`
- Realtime — new actions appear live via Supabase Realtime
- Related Actions on digest pages — link `/d/{slug}` to its spawned actions

### What Comes After
- Phase 1B: Semantic search (vector columns + Auto Embeddings + hybrid search)
- Phase 1C: Rendering updates (hybrid SSG + dynamic server components)
- Phase 2+: Thesis detail pages, portfolio views, action strategist integration

---

## Key Data Models and Their Status

| Data Model | Status | Used By ENIAC | Notes |
|-----------|--------|--------------|-------|
| `content_digests` | Live, 22 rows | Read + Write | Full DigestData JSON per content item |
| `actions_queue` | Live, 115 rows | Write | Scored actions proposed by ENIAC |
| `thesis_threads` | Live, 8 rows | Read + Write | Evidence append, conviction management |
| `action_outcomes` | Live | Write | Preference store — calibration loop |
| Companies DB | Notion, partially populated | Read (future) | Fuels Bucket 1. Needs Postgres mirror or API. |
| Network DB | Notion, partially populated | Read (future) | Fuels Bucket 3 (DeVC Collective funnel). |
| Portfolio DB | Notion, populated | Read (future) | Fuels Bucket 2. |

**Key gap:** ENIAC currently has no programmatic access to Companies DB, Network DB, or Portfolio DB beyond what's in its thesis thread context. As these get built out and connected, ENIAC's analysis quality will step-change.

---

## Build Priorities — What to Work On

### Now (in progress)
1. **WebFront `/actions` page** — Accept/dismiss/rate. This closes the feedback loop.
2. **Semantic search foundation** (IRGI Phase A) — Vector columns, Auto Embeddings, hybrid search function

### Next
3. **Thesis `.md` file architecture** — Design and migrate from DB-only to file-based evidence trails
4. **Scoring iteration** — Analyze first batch of action outcomes, refine heuristic
5. **Multi-source content** — RSS, web articles, podcasts (beyond YouTube)
6. **Companies DB connection** — Enable ENIAC to cross-reference content against Companies DB for Bucket 1

### Later
7. **Network DB connection** — Enable Bucket 3 (DeVC Collective) intelligence
8. **Portfolio DB connection** — Richer Bucket 2 analysis
9. **Action auto-execution** — Agent-assigned actions that ENIAC or subagents can execute autonomously
10. **Cross-content reasoning** — "This video + these 3 thesis threads + this portfolio company" semantic retrieval (IRGI Phase B+)

---

## Quality Bars

### Good ENIAC analysis
- Correct thesis connections (not fabricated)
- Honest relevance scoring (Low is valuable signal, don't inflate)
- At least 1 scored action per Medium+ relevance content
- Contra signals surfaced when present (never suppressed)
- Essence notes that a time-pressed investor can scan in 30 seconds

### Good action proposal
- Specific and actionable (not vague "research X")
- Correctly assigned (Aakash vs Agent)
- Score reflects actual value (calibrated by outcome data over time)
- Reasoning explains WHY, not just WHAT

### Good WebFront experience
- Aakash can triage 10 actions in under 2 minutes on mobile
- Live updates (no refresh needed)
- Clear connection between content → thesis → action
- Outcome rating is frictionless (one tap)

---

## Anti-Patterns

- Don't treat all content as equally important. Honest "Low" scores are calibration signal.
- Don't fragment thesis threads. If content fits an existing thread, update it — don't create a new one.
- Don't suppress contra signals. They're worth more than weak confirmations.
- Don't over-engineer scoring before we have outcome data. Ship the heuristic, iterate with real feedback.
- Don't build desktop-first. Aakash lives on mobile and WhatsApp.
- Don't conflate bucket names with thesis thread names. "New Cap Tables" is a bucket. "Agentic AI Infrastructure" is a thesis thread.
- Don't assume Companies DB and Network DB exist as queryable stores yet. Design for them, but gracefully degrade without them.

---

## Open Questions for APM to Track

1. Should thesis evidence live in `.md` files, Postgres, or both? What's the migration path?
2. What's the right scoring model after we have 50+ outcome-rated actions?
3. How should ENIAC handle content that's relevant but not thesis-connected? (General market intelligence)
4. When Companies DB and Network DB are queryable, how does ENIAC's analysis framework change?
5. What's the right trigger for "Evolving Fast" conviction? Velocity of evidence accumulation — but what threshold?
6. Should the WebFront show thesis conviction trends over time? (Conviction graph per thread)
