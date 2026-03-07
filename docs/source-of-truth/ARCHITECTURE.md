# Architecture
*Last Updated: 2026-03-07*

Three-layer architecture, runners, integrations, and component status for the AI CoS system.

---

## System Overview

The AI CoS is a persistent, autonomous system that answers **"What's Next?"** for Aakash Kumar (MD at Z47 / $550M fund + MD at DeVC / $60M fund). It optimizes across his full stakeholder and action space: meetings, content consumption, research, thesis building, and portfolio management.

**Core architecture:** Three layers — Observation (signal sources), Intelligence (runners + tools), Interface (how Aakash interacts). All layers read/write from a shared State layer (hybrid Notion + Postgres).

**Core principle:** Claude mobile is the primary conversational interface. Agent SDK runners enrich underlying state continuously so that when Aakash asks "what's next?", Claude reasons over rich, current, preference-calibrated data.

---

## Architecture Diagram

```
OBSERVATION LAYER (Signal Sources)
  YouTube/RSS [LIVE]     Granola MCP [CONNECTED]    Calendar MCP [CONNECTED]
  Gmail MCP [CONNECTED]  digest.wiki [LIVE]         X/LinkedIn [MANUAL]
  Screenshots [MANUAL]   WhatsApp [FUTURE]
                 | normalized Signals
                 v
INTELLIGENCE LAYER (Runners + Tools)
  ContentAgent [LIVE]         SyncAgent [LIVE]
  PostMeetingAgent [PLANNED]  OptimiserAgent [PLANNED]
  IngestAgent [PLANNED]
       | reads preference store before every reasoning session
       v
TOOL LAYER (ai-cos-mcp + existing MCPs)
  17 custom MCP tools [LIVE]
  Notion MCP, Granola MCP, Calendar MCP, Gmail MCP [CONNECTED]
       | reads/writes
       v
STATE LAYER
  Notion (8 DBs — human interface, SoT for human fields)
  Postgres (7 tables — preference store, sync state, enrichments)
  Thesis Tracker (AI-managed conviction engine)
       | surfaces to
       v
INTERFACE LAYER
  Claude mobile [LIVE]      Claude desktop [LIVE]
  digest.wiki [LIVE]        Notion [LIVE]
  Claude Code [LIVE]        WhatsApp [FUTURE]

         LEARNING LOOP
    accept/reject -> action_outcomes
    -> preference injection -> better proposals
    -> compound over time
```

---

## Layer 1: Observation (Signal Sources)

| Source | Signal Type | Status | Integration Details |
|--------|------------|--------|-------------------|
| **YouTube/RSS** | Content → thesis signals | LIVE (autonomous) | Droplet cron every 5 min. yt-dlp extraction → ContentAgent → publish. Cookies from Safari, expire every 1-2 weeks. |
| **Granola** | Meeting signals, IDS updates | CONNECTED (not automated) | Granola MCP: `query_granola_meetings`, `get_meeting_transcript`. 7-8 meetings/day. Processing pipeline not yet built. |
| **Google Calendar** | Location + schedule context | CONNECTED (not automated) | Google Calendar MCP. Powers geographic overlap factor in People Scoring Model. |
| **Gmail** | Founder updates, investor comms | CONNECTED (not automated) | Gmail MCP. Raw access only, not processed by agents. |
| **digest.wiki** | Revealed preferences (accept/reject) | LIVE (partial) | Currently surfaces content digests. Action accept/dismiss UX planned. |
| **Notion** | Action outcomes, manual edits | LIVE | Enhanced Connector MCP + Raw API. Source of truth for human-managed structured data. |
| **X / LinkedIn** | Thesis signals, network signals | MANUAL | No clean API. Screenshots/URLs via IngestAgent (future). |
| **WhatsApp** | Response signals, async comms | FUTURE | Primary communication channel, no API integration yet. |

**Key principle: Same Brain, Different Eyes.** The Intelligence Engine runs the same flow for all sources: match → retrieve context → analyze → score → generate actions → present.

---

## Layer 2: Intelligence (Runners + Tools)

### Runners

| Runner | Status | Trigger | What It Does |
|--------|--------|---------|-------------|
| **ContentAgent** | LIVE | New content in `queue/` (YouTube JSON). Cron every 5 min. | Calls Claude API with structured prompt. Produces DigestData JSON: thesis connections with conviction assessments, portfolio connections with actions, contra signals, rabbit holes, scored actions. Creates new thesis threads autonomously. |
| **SyncAgent** | LIVE | Cron every 10 min. | Orchestrates: thesis status sync (Notion → Postgres), actions bidirectional sync, retry queue drain, change detection, action generation from changes. |
| **PostMeetingAgent** | PLANNED | New Granola transcript detected | Extracts IDS signals (+, ++, ?, ??, +?, -), updates conviction trail, detects open commitments, identifies new people for Network DB, scores follow-up actions. |
| **OptimiserAgent** | PLANNED | Nightly cron + on-demand ("what's next?") | Re-scores full action queue, surfaces dormant connections, "best person to meet today" reasoning, gap analysis ("you're underweighting bucket 2"). |
| **IngestAgent** | PLANNED | Manual (screenshot drop, URL) | Profile screenshot → structured Network DB entry. Post URL → thesis signal extraction. |

**Runner design principle:** Narrow specialists, not general agents. Runners execute what has been designed in Claude Code. They never design. The ContentAgent pattern is proven: extraction → Claude API analysis → Notion writes → digest.wiki publish → git push → Vercel deploy, every 5 min, no human in the loop.

### ContentAgent Pipeline Detail

```
YouTube Playlist (polled every 5 min)
  → yt-dlp extraction (with cookies)
  → Dedup check (processed_videos.json)
  → Relevance classification
  → Transcript fetch (youtube-transcript-api + yt-dlp fallback)
  → Claude Analysis (claude-sonnet-4, content_analysis.md prompt)
    - Reads: thesis threads, portfolio context, preferences, CONTEXT.md
    - Produces: DigestData JSON per video
  → Three parallel output tracks:
    A) digest.wiki: JSON → git push → Vercel auto-deploy (~15s)
    B) Notion: Content Digest DB + Actions Queue + Thesis Tracker updates
    C) Preference Store: action_outcomes logging
```

### MCP Tool Layer

The `ai-cos-mcp` server provides 17 tools (see MCP-TOOLS-INVENTORY.md). It complements existing MCPs:

| MCP | Tools Used | Status |
|-----|-----------|--------|
| **ai-cos-mcp** | 17 custom tools (health, context, scoring, thesis CRUD, data access, sync, observability) | LIVE |
| **Notion Enhanced Connector** | notion-fetch, notion-search, notion-create-pages, notion-update-page, notion-query-database-view | LIVE |
| **Notion Raw API** | API-get-block-children, API-patch-block-children (block-level ops) | LIVE |
| **Granola** | query_granola_meetings, get_meeting_transcript, list_meetings | CONNECTED |
| **Google Calendar** | Calendar events, scheduling, free time | CONNECTED |
| **Gmail** | Read, search, draft emails | CONNECTED |
| **Vercel** | Deploy, logs, project management | CONNECTED |

### Scoring Models

**Action Scoring Model (7 factors):**
```
Action Score = f(bucket_impact, conviction_change_potential, key_question_relevance,
                 time_sensitivity, action_novelty, stakeholder_priority, effort_vs_impact)
```
Thresholds: >=7 surface, 4-6 low-confidence, <4 context enrichment only.
Implementation: `scripts/action_scorer.py` (172 lines). NOT yet wired into Content Pipeline.

**People Scoring Model (9 factors, subset for meeting-type actions):**
```
Person Score = f(bucket_relevance, current_ids_state, time_sensitivity,
                 info_gain_potential, network_multiplier, thesis_intersection,
                 relationship_temp, geographic_overlap, opportunity_cost)
```

### Learning Loop (Preference Store)

`action_outcomes` table in Postgres. Every accept/reject with scoring factor snapshots. Injected into reasoning sessions via `cos_get_preferences()` before proposals. No ML training — structured history in context. After 6 months the system is measurably better at predicting what Aakash will act on.

---

## Layer 3: Interface

| Surface | Use Case | Powered By | Proactive? | Status |
|---------|---------|------------|-----------|--------|
| **Claude mobile** | "What's next?", action review, thesis discussion | MCP over Notion/Postgres state | No (Aakash initiates) | LIVE |
| **Claude desktop** | Same as mobile, larger context | MCP over Notion/Postgres state | No | LIVE |
| **digest.wiki** | Content digests, future: accept/reject actions | Vercel SSG → JSON data | No | LIVE |
| **Notion** | Action triage, thesis notes, build roadmap | Direct Notion + runner syncs | No | LIVE |
| **Claude Code** | Primary build surface, hooks, CLAUDE.md | CLI + hooks + Tailscale | No | LIVE |
| **WhatsApp** | Proactive push: pre-meeting briefs, signal alerts | Agent SDK runner → WA API | YES | FUTURE |

---

## AI-Managed Conviction Engine (Thesis Tracker)

The Thesis Tracker is not a passive database — it's an AI-managed conviction engine. All fields are written by AI except Status (human-only: Active/Exploring/Parked/Archived).

**Conviction Spectrum (6 levels, two axes):**
- Maturity axis: New → Evolving → Evolving Fast (thesis still forming)
- Strength axis: Low → Medium → High (well-formed thesis, assessed on evidence)

**Key Questions lifecycle:** Stored as `[OPEN]` page content blocks. When evidence answers a question, marked `[ANSWERED]` with citation. Automated by ContentAgent.

**Autonomous thread creation:** When content analysis reveals a genuinely new investment thesis, ContentAgent creates a new thread at Conviction="New".

**Active threads (6+):** Agentic AI Infrastructure, Cybersecurity/Pen Testing, USTOL/Aviation, SaaS Death/Agentic Replacement (High conviction), CLAW Stack, Healthcare AI Agents.

---

## Detailed Reference

- **Full architecture spec:** `docs/architecture/architecture-v0.3.md`
- **Full vision narrative:** `docs/architecture/vision-v5.md`
- **Data sovereignty:** `docs/architecture/DATA-SOVEREIGNTY.md`
- **Droplet runbook:** `docs/architecture/DROPLET-RUNBOOK.md`
- **Repo navigation:** `docs/architecture/REPO-GUIDE.md`
