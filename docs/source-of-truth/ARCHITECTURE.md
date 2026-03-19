# Architecture
*Last Updated: 2026-03-19*

The system design: layers, components, how they connect, and the core architectural patterns.

---

## System Overview

The AI CoS is a persistent, autonomous system that answers **"What's Next?"** for Aakash Kumar (MD at Z47 / $550M fund + MD at DeVC / $60M fund). It optimizes across his full stakeholder and action space: meetings, content consumption, research, thesis building, and portfolio management.

**Core architecture:** Three layers — Observation (signal sources), Intelligence (agents + tools), Interface (how Aakash interacts). All layers read/write from a shared State layer (hybrid Notion + Postgres).

**Core principle:** Claude mobile is the primary conversational interface. Persistent agents enrich underlying state continuously so that when Aakash asks "what's next?", Claude reasons over rich, current, preference-calibrated data.

---

## Architecture Diagram

```
OBSERVATION LAYER (Signal Sources)
  YouTube/RSS          Granola           Calendar
  Gmail                digest.wiki       X/LinkedIn
  Screenshots          WhatsApp
                 | normalized Signals
                 v
INTELLIGENCE LAYER (Agents + Tools)
  Orchestrator → Content Agent (persistent ClaudeSDKClients, managed by lifecycle.py)
  State MCP (CAI window)    Web Tools MCP (browser/scrape/search)
       | reads preference store before every reasoning session
       v
STATE LAYER
  Notion (8 DBs — human interface, SoT for human fields)
  Postgres (pipeline state, preferences, sync, inbox, notifications)
  Thesis Tracker (AI-managed conviction engine)
       | surfaces to
       v
INTERFACE LAYER
  Claude mobile         Claude desktop
  digest.wiki           Notion
  Claude Code           WhatsApp

         LEARNING LOOP
    accept/reject -> action_outcomes
    -> preference injection -> better proposals
    -> compound over time
```

---

## Layer 1: Observation (Signal Sources)

Signal sources feed the Intelligence Layer. Each source type produces normalized signals that flow through the same analysis pipeline: match → retrieve context → analyze → score → generate actions → present.

**Signal categories:**
- **Content** — YouTube, RSS, podcasts, articles. Autonomous processing via Content Agent.
- **Meetings** — Granola transcripts. 7-8 meetings/day, each generates IDS signals.
- **Schedule** — Google Calendar. Location + time context for scoring.
- **Communications** — Gmail, WhatsApp. Founder updates, investor comms, async signals.
- **Manual captures** — Screenshots, URLs, bookmarks. Zero-friction capture → structured extraction.
- **Revealed preferences** — digest.wiki accept/reject, Notion action outcomes. Feeds learning loop.

**Key principle: Same Brain, Different Eyes.** The Intelligence Engine runs the same flow for all sources.

---

## Layer 2: Intelligence (Agents + Tools)

### Agent Pattern

Agents are persistent ClaudeSDKClient sessions — same harness as Claude Code. Each agent has its own CLAUDE.md, hooks, Bash access, and tool permissions. Python (lifecycle.py) is lifecycle plumbing: process management, @tool bridge for inter-agent communication, token tracking, session restart on compaction.

Agents access Postgres via Bash + psql (not custom @tools). Skills teach DB schema and workflow patterns. This mirrors CC's extensibility triad: tools + MCPs + skills.

### MCP Tool Layer

MCP servers provide tool access to both agents and Claude.ai:

- **State MCP** — Lightweight CAI window. Thesis state, inbox relay, notifications. See MCP-TOOLS-INVENTORY.md.
- **Web Tools MCP** — Browser automation, scraping, search, cookies, fingerprinting, URL monitoring. See MCP-TOOLS-INVENTORY.md.
- **Notion MCP** — Enhanced Connector + Raw API. Human-managed structured data.
- **External MCPs** — Granola, Calendar, Gmail, Vercel. Connected via Claude.ai.

### Scoring Models

**Action Scoring Model (7 factors):**
```
Action Score = f(bucket_impact, conviction_change_potential, key_question_relevance,
                 time_sensitivity, action_novelty, stakeholder_priority, effort_vs_impact)
```
Thresholds: >=7 surface, 4-6 low-confidence, <4 context enrichment only.

**People Scoring Model (9 factors, subset for meeting-type actions):**
```
Person Score = f(bucket_relevance, current_ids_state, time_sensitivity,
                 info_gain_potential, network_multiplier, thesis_intersection,
                 relationship_temp, geographic_overlap, opportunity_cost)
```

### Learning Loop (Preference Store)

`action_outcomes` table in Postgres. Every accept/reject with scoring factor snapshots. Injected into reasoning sessions before proposals. No ML training — structured history in context. The compound effect: after 6 months the system is measurably better at predicting what Aakash will act on.

---

## Layer 3: Interface

Surfaces through which Aakash interacts with the system. **Primary surfaces: WebFront + CAI.**

- **WebFront (digest.wiki)** — Web frontend. Currently SSG content digests; evolving into a persistent, real-time interaction layer (action triage, thesis dashboard, pipeline status, agent messaging). Vercel-hosted Next.js. See `WEBFRONT.md` for full architecture.
- **CAI (Claude mobile/desktop)** — Primary conversational interface. "What's next?", action review, thesis discussion. Powered by MCP over Supabase Postgres state.
- **Notion** — Structured data management. Build roadmap, manual edits. Human-managed.
- **Claude Code** — Primary build surface. CLI + hooks + CLAUDE.md.
- **WhatsApp** — Proactive push channel: pre-meeting briefs, signal alerts, follow-up reminders.

**Supabase (managed Postgres).** Postgres is on Supabase (ap-south-1 Mumbai, 31ms from droplet). Agents connect via session pooler (`DATABASE_URL`). WebFront connects via `@supabase/ssr` (PostgREST under the hood). Supabase provides: pgvector (semantic search), Realtime (live WebFront updates), PostgREST (auto-generated API), and Auto Embeddings (invisible pipeline: DB trigger → pgmq → pg_cron → Edge Function → Voyage AI → vector column). Agents are pure consumers of embeddings — they write content, vectors appear automatically. See `WEBFRONT.md` and `DATA-ARCHITECTURE.md`.

---

## AI-Managed Conviction Engine (Thesis Tracker)

The Thesis Tracker is not a passive database — it's an AI-managed conviction engine. All fields are written by AI except Status (human-only: Active/Exploring/Parked/Archived).

**Conviction Spectrum (6 levels, two axes):**
- Maturity axis: New → Evolving → Evolving Fast (thesis still forming)
- Strength axis: Low → Medium → High (well-formed thesis, assessed on evidence)

**Key Questions lifecycle:** Stored as `[OPEN]` page content blocks. When evidence answers a question, marked `[ANSWERED]` with citation. Automated by Content Agent.

**Autonomous thread creation:** When content analysis reveals a genuinely new investment thesis, Content Agent creates a new thread at Conviction="New".
