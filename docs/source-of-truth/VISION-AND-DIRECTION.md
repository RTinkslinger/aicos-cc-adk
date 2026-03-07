# Vision & Direction
*Last Updated: 2026-03-07*

Where the AI CoS is going, what's built vs. what's not, current approaches vs. ideal, and the gaps.

---

## The Vision

The AI CoS exists to answer **"What's Next?"** — optimizing across Aakash Kumar's full action space (stakeholder actions + intelligence actions) to maximize investment returns. Not a tool Aakash uses — an extension of how he thinks and operates. **Aakash and his AI CoS are a singular entity.**

The question evolved through 5 vision iterations:
- v1: "What happened?" (task automation) → v2: "Who should I meet?" (network optimization) → v3-v5: **"What's Next?"** (full action space optimization)

What v5 adds to the question: the reality of an autonomous system processing signals 24/7, an AI-managed conviction engine evolving thesis threads continuously, and full infrastructure on a cloud droplet.

---

## The Optimization Problem

**Stakeholder Space:** ~200 companies (growing 50-60/yr) + 400+ network contacts across 13 archetypes.

**Action Space:** Stakeholder actions (meetings, calls, emails, intros, follow-ups) + Intelligence actions (content consumption, research, analysis). Both generate new actions in a continuous loop.

**Four Priority Buckets (all actions serve these):**

| Priority | Objective | Weight |
|----------|-----------|--------|
| 1 | New cap tables — get on more amazing companies' cap tables | Highest always |
| 2 | Deepen existing cap tables — continuous IDS on portfolio | High always |
| 3 | New founders/companies — meet potential founders via DeVC pipeline | High always |
| 4 | Thesis evolution — meet people who keep thesis lines evolving | Highest when capacity exists |

---

## Design Principles

1. **WhatsApp-first, mobile-native.** Desktop as primary = failure.
2. **Capture must be zero-friction.** Screengrab-as-memory, WhatsApp-self-as-bookmark. AI CoS must be even lower friction.
3. **IDS is the core methodology.** Every signal compounds into the IDS graph.
4. **Judgment stays with Aakash.** AI CoS never makes investment decisions — it makes Aakash's judgment more effective.
5. **Plumbing serves the optimizer.** Every piece of infrastructure must make "What's Next?" answerable with higher accuracy.
6. **Runners execute what Claude Code designs.** Narrow specialists, not general agents.
7. **The preference store is the compounding mechanism.** Without learning from accept/reject, you have smart one-shot reasoning but no improvement over time.
8. **Each signal source independently improves the loop.** YouTube alone already generates thesis updates and portfolio actions.
9. **Gradual trust building.** Read → Suggest → Act → Auto-act, earned at the category level.
10. **The system enforces its own maintenance.** Build Traces, CLAUDE.md, hooks, session checklists.

---

## Build Phases

### Phase 1: Wire the Intelligence — ~70% COMPLETE

*Make the existing system smarter.*

| Item | Status |
|------|--------|
| Content Pipeline autonomous on droplet | DONE |
| Thesis Tracker conviction engine | DONE |
| ai-cos-mcp server (17 tools) | DONE |
| Preference Store (`action_outcomes` table) | DONE |
| Droplet + Postgres infrastructure | DONE |
| Public MCP endpoint (Cloudflare Tunnel) | DONE |
| Data Sovereignty (Postgres backing, bidirectional sync, change detection) | DONE |
| SyncAgent on cron (10-min cycle) | DONE |
| Wire `action_scorer.py` into Content Pipeline | NOT STARTED |
| Full preference injection into all reasoning sessions | NOT STARTED |

### Phase 2: Action Frontend — NOT STARTED

*Give Aakash a proper triage surface.*

1. Accept/dismiss buttons on digest pages (`digest.wiki/d/{slug}`)
2. Consolidated `/actions` route on digest.wiki — all pending actions, filterable
3. Portfolio dashboard view
4. Thesis tracker view with evidence feed

**Value:** Without a triage surface, increasing action volume overwhelms the chat-based review workflow.

### Phase 3: Autonomous Runners — NOT STARTED

*The system processes all signal types autonomously.*

Build order follows dependency chain:
1. **PostMeetingAgent** — Highest value-add: 7-8 meetings/day, each generates IDS signals
2. **IngestAgent** — Processes manual captures (screengrabs, URLs, bookmarks)
3. **OptimiserAgent** — Full scoring models → ranked lists → gap analysis

### Phase 4: Optimisation + Multi-Surface — NOT STARTED

1. OptimiserAgent production
2. `cos_best_meetings_today()` with full People Scoring Model
3. Relationship temperature scoring
4. WhatsApp integration (proactive push + capture)
5. Vector DB (pgvector, if triggered)

### Phase 5: Always-On Intelligence — NOT STARTED

Continuous signal ingestion, real-time optimization, meeting slot filling, network pulse, thesis convergence detection, 24/7 compound intelligence.

---

## Current Approaches vs. Ideal

| Area | Current Approach | Ideal | Gap |
|------|-----------------|-------|-----|
| **Signal Sources** | YouTube only (autonomous). Granola, Calendar, Gmail connected but not agent-processed. | All sources processed autonomously. WhatsApp as primary I/O channel. | 1 of 8+ signal sources automated. No WhatsApp. |
| **Scoring** | `action_scorer.py` exists (172 lines, 7 factors). Content Pipeline uses its own simpler scoring. | action_scorer.py wired into all pipelines. Preference-calibrated scoring on every action. | Script exists, not wired in. No preference injection into scoring. |
| **Preference Learning** | `action_outcomes` table exists. `cos_get_preferences()` tool exists. | Every reasoning session reads preferences before proposing. Accept/reject history actively calibrates future proposals. | Table exists, tool exists, but not yet injected into all reasoning sessions. |
| **Thesis Management** | AI-managed conviction engine with 6 levels, key questions, evidence accumulation. All writes through MCP tools. | Same — this is close to ideal. Could add vector search over evidence corpus. | No vector search. No cross-thesis pattern detection. |
| **Triage Surface** | Notion (manual status changes) + Claude.ai chat. | digest.wiki with accept/dismiss UX, consolidated `/actions` dashboard, portfolio view. | No action frontend. Action volume increasing without proper triage surface. |
| **Meeting Processing** | Granola MCP connected (can access transcripts). No automated processing. | PostMeetingAgent: every meeting → IDS extraction → conviction updates → follow-up actions. | Granola signals leak between meetings. Biggest signal source not automated. |
| **Network Intelligence** | Notion Network DB (400+ contacts, 40+ fields). No automated enrichment. | OptimiserAgent: "best person to meet in SF", dormant relationship alerts, gap analysis. | No relationship temperature model. No automated network scoring. |
| **Proactive Push** | None. Aakash initiates all interactions. | WhatsApp: pre-meeting briefs, signal alerts, follow-up reminders, weekly synthesis. | No proactive channel at all. |
| **Semantic Search** | LLM-as-matcher (company/thesis lists in prompt context). | pgvector for sub-second retrieval across all data. | Correctly deferred — triggers not yet fired (2nd signal source, 500+ companies, sub-second needs). |
| **Data Sovereignty** | Thesis + Actions: Postgres backing with write-ahead, bidirectional sync, change detection. | Same for Companies/Network/Portfolio (Phase 5). | Companies/Network/Portfolio sync deferred. |
| **Runners** | 2 of 5 live (ContentAgent, SyncAgent). | All 5 running autonomously. | PostMeetingAgent, OptimiserAgent, IngestAgent not built. |

---

## Key Gaps (Prioritized)

### High Priority (Phase 1-2 remaining)

1. **action_scorer.py not wired into pipeline** — Content Pipeline uses its own simpler scoring instead of the 7-factor model
2. **No Action Frontend** — Action volume increasing, no proper triage surface beyond Notion and chat
3. **Preference injection not flowing** — `action_outcomes` data exists but isn't injected into all reasoning sessions

### Medium Priority (Phase 3)

4. **No automated meeting processing** — 7-8 meetings/day, all IDS signals leak. PostMeetingAgent would be highest value-add
5. **No manual capture processing** — Screenshots, URLs sit in bookmarks. IngestAgent would process these

### Lower Priority (Phase 4-5)

6. **No proactive push** — WhatsApp integration for pre-meeting briefs, signal alerts, follow-up reminders
7. **No relationship temperature model** — One of 9 People Scoring factors, not formally modeled
8. **No vector DB** — Correctly deferred until 2nd signal source, 500+ companies, or sub-second retrieval need
9. **Companies/Network/Portfolio not synced to Postgres** — Deferred until agents need local access
10. **No cross-thesis pattern detection** — Multiple signals from different sources pointing to same insight

---

## What 100x Looks Like

**Without AI CoS:** Actions driven by who reaches out, what gets scheduled, what Aakash remembers. ~30-40% optimal allocation.

**With AI CoS (Phase 4+):** Every action slot informed by scored, contextual analysis of entire stakeholder space. System catches what he'd miss: content signals that change conviction, dormant relationships worth re-engaging, thesis threads revealing new opportunities. ~70-80% optimal allocation.

**The flywheel:** Better actions → better IDS → better decisions → better outcomes → better network → even better actions. The Preference Store makes the system smarter with every decision Aakash makes. The compound effect is the point.

---

## Detailed Reference

- **Full vision narrative:** `docs/architecture/vision-v5.md`
- **Full architecture spec:** `docs/architecture/architecture-v0.3.md`
- **Build roadmap (live):** Notion Build Roadmap DB, `view://4eb66bc1-322b-4522-bb14-253018066fef`
- **Build traces:** `TRACES.md` (rolling window), `traces/archive/` (milestones)
