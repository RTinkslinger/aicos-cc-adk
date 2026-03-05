# AI Chief of Staff — Architecture Brainstorm Session Summary (Enhanced)
**March 2026 · Claude.ai Session · Memory-only → Enhanced with Cowork ground truth**
> Original drafted from session memory alone. This version corrected and augmented against CONTEXT.md, CLAUDE.md, vision docs v1-v3, and 39 sessions of iteration logs.

---

## 1. Starting Point — What Existed Before This Session

### What Was Already Built
- **Layered persistence architecture (Session 012, refined through 033):** Global Instructions (Layer 0a), User Preferences (Layer 0b), Claude.ai Memories (Layer 1, 16 entries), AI CoS Skill v6.2.0 (Layer 2), CLAUDE.md (Layer 3), CONTEXT.md as the living brain. Cross-surface coverage map tracked in `docs/layered-persistence-coverage.md`, version sync tracked in `docs/v6-artifacts-index.md`.
- **Notion as primary structured data layer:**
  - Actions Queue (data source `1df4858c-6629-4283-b31d-50c5e7ef885d`) — single sink for ALL action types with relations to Portfolio DB, Thesis Tracker, and Content Digest DB
  - Build Roadmap (data source `6e1ffb7e-01f1-4295-a7ea-67d5c9216d8f`) — 7-state insights-led kanban with 22 items, parallel safety classification (🟢/🟡/🔴), self-relation dependencies
  - Content Digest DB (data source `df2d73d6-e020-46e8-9a8a-7b9da48b6ee2`) — stores AI-analyzed content with thesis/portfolio connections
  - Companies DB (49 fields, data source `1edda9cc-df8b-41e1-9c08-22971495aa43`) — Deal Status 3D matrix (pipeline stage × conviction × active/inactive)
  - Network DB (40+ fields, data source `6462102f-112b-40e9-8984-7cb1e8fe5e8b`) — 13 archetypes
  - Portfolio DB (94 fields, data source `4dba9b7f-e623-41a5-9cb7-2af5976280ee`)
  - Thesis Tracker (data source `3c8d1a34-e723-4fb1-be28-727777c22ec6`) — shared state between Claude.ai and Cowork with sync protocol
  - Tasks Tracker, Finance DB
- **Content Pipeline v4 (Sessions 014-017):** YouTube → Mac extractor (`scripts/youtube_extractor.py` via launchd at 8:30 PM) → JSON queue → Cowork parallel subagent analysis → PDF digests + HTML digests → Content Digest DB → Actions Queue (with Source Digest relation). Daily scheduled task at 9 PM. Full Cycle orchestrator (`skills/full-cycle/SKILL.md`) with DAG-based dependency ordering.
- **IDS (Increasing Degrees of Sophistication)** methodology fully decoded: notation system (+, ++, ?, ??, +?, -), conviction spectrum (100% Yes → Pass Forever), Spiky Score (7×1.0), EO/FMF/Thesis/Price (4×/10), 7 IDS context types.
- **Action Scoring Model (CONTEXT.md):** 7 factors (bucket_impact, conviction_change_potential, key_question_relevance, time_sensitivity, action_novelty, stakeholder_priority, effort_vs_impact). Thresholds: ≥7 surface, 4-6 low-confidence, <4 context enrichment only.
- **People Scoring Model (subset for meeting-type actions):** 9 factors (bucket_relevance, current_ids_state, time_sensitivity, info_gain_potential, network_multiplier, thesis_intersection, relationship_temp, geographic_overlap, opportunity_cost).
- **Subagent-delegated session close** (Session 035-036): 8-step checklist using Bash subagents to avoid context compaction death spiral.
- **Subagent prompt templates** in `scripts/subagent-prompts/` (4 templates: session-close-file-edits, skill-packaging, git-push-deploy, general-file-edit) + behavioral audit prompt template (`scripts/session-behavioral-audit-prompt.md`).
- **digest.wiki (Session 019):** Next.js 16 + TypeScript + Tailwind v4 Vercel frontend. Live at https://digest.wiki. SSG renders mobile-friendly, WhatsApp-shareable digests. Single deploy path: commit → osascript git push → GitHub Action → Vercel production (~90s).
- **Granola** for meeting transcription — 7-8 meetings/day, Granola MCP tools connected (query_granola_meetings, get_meeting_transcript, list_meetings, get_meetings).
- **Parallel development system (Sessions 034-039):** Local git repo at AI CoS root. Branch lifecycle (create → work → complete → review → merge → close). File classification (🟢 Safe / 🟡 Coordinate / 🔴 Sequential). Worktree-based isolation tested. `scripts/branch_lifecycle.sh` CLI with full-auto, worktree-create/clean/list. 2-step roadmap gate before any code changes.
- **Deep research enrichment (Session 015):** All 20 Fund Priority companies researched via Parallel AI, files in `portfolio-research/`, 76 actions generated.
- **Notion Mastery Skill v1.2.0 (Sessions 018, 032):** Universal cross-surface Notion operation reference. `view://UUID` bulk-read pattern. Auto-loads before any Notion tool call.
- **6 active thesis threads** in Thesis Tracker: Agentic AI Infrastructure, Cybersecurity/Pen Testing, USTOL/Aviation, SaaS Death/Agentic Replacement (High conviction), CLAW Stack, Healthcare AI Agents.
- Cowork as primary build surface, Claude Code for daily coding work.

### Known Gaps Going In
- No retrieval layer — meeting history and session logs not queryable beyond Granola MCP full-text search
- No cross-session memory beyond CONTEXT.md, Notion, and Claude.ai Memories (16 entries)
- All automation triggered by Aakash or simple cron — nothing running autonomously with reasoning in background
- Cowork hooks not portable to Claude.ai/mobile (hooks are CLI-only)
- No feedback loop — accept/reject on suggested actions captured in Notion (Status field) but not structured for preference learning injection into agent reasoning
- **No Attio** — network data lives entirely in Notion Network DB. The brainstorm session incorrectly assumed Attio as CRM source of truth; this was corrected.
- Scoring models defined but not implemented as code — `scripts/action_scorer.py` (172 lines) created in Session 039 but not yet wired into Content Pipeline
- No vector/embedding layer — LLM-as-matcher using Notion + company index in prompt. Strategy: add vector DB when triggered by second signal source (Granola), 500+ companies, or need for sub-second retrieval.

---

## 2. Key Questions That Drove The Session

**Q1: Can Claude Code hooks work in Cowork?**
No. Hooks are CLI-only. This forced the MCP-as-hook-layer design.

**Q2: Would QMD give a meaningful retrieval unlock for meeting history?**
Yes for immediate value on Granola transcripts. But local-only — can't follow data to cloud. pgvector on droplet is the cloud-native replacement. *Ground truth note:* Granola MCP already provides server-side transcript access (`query_granola_meetings`, `get_meeting_transcript`), which may reduce QMD's value proposition to zero for meeting retrieval specifically.

**Q3: If moving to cloud DB + MCP, does QMD still work?**
Only for Granola (still local). Everything else migrates. Long-term: pgvector or equivalent replaces QMD entirely. *Ground truth note:* Since Granola MCP exposes transcripts server-side, QMD may be entirely unnecessary. Validate whether Granola MCP semantic search is sufficient before investing in local QMD.

**Q4: With Agent SDK, would the MCP still be useful?**
Critical. They compose. Agent SDK is the execution runtime. MCP is the tool layer. Agent SDK without MCP = Claude has only built-in tools. MCP without Agent SDK = no autonomous execution. *Ground truth confirms:* Current architecture already uses MCP extensively — Notion MCP (Enhanced Connector + Raw API), Granola MCP, Google Calendar MCP, Gmail MCP, Vercel MCP, Explorium MCP, browser automation MCPs. These would compose into Agent SDK runners.

**Q5: What is the right build path — Agent SDK + MCP + cloud, or simpler?**
Agent SDK + MCP + cloud is correct. But Agent SDK portion is narrow specialist runners, not a general agent. Build MCP tools first, designed headlessly. Agent SDK wires on top later. *Ground truth note:* This aligns with vision-v3's build order — Phase 1-2 (Content Pipeline + Action Frontend) before Phase 3-4 (Knowledge Store + Multi-Surface including Agent SDK runners).

**Q6: Would Claude mobile interaction be AI-rich if powered by MCP?**
Yes, but the richness comes from the data layer being continuously enriched by Agent SDK runners — not from the mobile interface itself. *Ground truth note:* This is already partially true — Claude.ai Memories (#11, #12) enable "review my content actions" and "review my portfolio actions" queries against Notion, but without the enrichment that autonomous runners would provide.

**Q7: Three separate Agent SDK runners or one unified agent?**
One orchestrator, multiple specialist subagents. Single entry point, single deployment, isolated execution. Mirrors existing Claude Code subagent pattern — just running autonomously on droplet. *Ground truth note:* The pattern is proven across 39 sessions. Content Pipeline already uses orchestrator + parallel Task subagents (one per video). Session close uses Bash subagents with prompt templates. The Agent SDK version would be this same pattern running autonomously.

**Q8: Is Agent SDK just a fancy cron job?**
For deterministic data movement, yes — use cron + Python script. Agent SDK earns its keep when intermediate results change what happens next: post-meeting signal extraction, content-to-thesis connection reasoning, IDS update from new information. The loop + tools combo mid-reasoning is the primitive you can't replicate with scripts.

**Q9: Can I interact with my custom Agent SDK agent via Claude mobile?**
Not natively as a persistent agent. But Claude mobile + MCP IS the conversational interface. State lives in Postgres (or Notion in Phase 1). Execution happens in Agent SDK. Conversation happens via MCP. WhatsApp is the push channel for proactive summaries.

**Q10: Is Agent SDK critical for the real AI CoS vision?**
Yes — and the session initially undersold this. The core loop (Observe → Reason → Act → Learn → Repeat) requires the learning mechanism. The preference store feeding every Agent SDK reasoning session is what makes the system compound. Without it, you have smart one-shot reasoning but no improvement over time. *Ground truth note:* Vision-v3 defines the Learning Loop: accept/dismiss ratios per company × action type → weight adjustment, meeting outcomes → revealed preference learning, nightly consolidation → cluster/merge/promote/archive, thesis thread tracking → which threads generate most acted-on signals.

---

## 3. Key Decisions Made

### Decision 1: MCP Server as Cross-Surface Hook Layer
Claude Code hooks don't work in Cowork or Claude.ai. The MCP server replicates hook behaviors across all surfaces: context injection at session start, action logging, state sync, scoring. FastMCP in Python (~200 lines). Deploy to URL. Connected from Claude Code, Claude.ai, Cowork, Claude desktop.

*Ground truth augmentation:* Today, MCP tools are already connected per surface (Notion MCP, Granola MCP, Calendar MCP, etc). A custom `ai-cos-mcp` server would consolidate cross-cutting logic (context loading, action scoring, preference injection) into a single endpoint rather than scattering it across skill prompts and CONTEXT.md.

### Decision 2: Cloud Infrastructure — Droplet + Postgres + Sync
**Three phases:**
- Phase 1: MCP server + Notion as backend (current integration pattern continues)
- Phase 2: Add Postgres for high-frequency tables (actions_queue, content_digest, thesis_signals, session_log). Notion syncs as UI layer. Latency: Notion API 200-800ms → Postgres <5ms.
- Phase 3: Web UI for on-demand triggers. Agent SDK runner layer. Notion for human-only tables.

$12/month Digital Ocean droplet (1 vCPU, 2GB RAM). Tailscale for secure networking. Sync worker: dirty flag pattern, 60s batch cycle, respects Notion rate limits.

*Ground truth augmentation:* Notion rate limits are a real constraint already encountered in sessions. The `view://UUID` bulk-read pattern (Session 032 discovery) was a workaround for API limitations. Postgres would eliminate this bottleneck. Current Notion data volume: ~200 companies, ~400 network contacts, ~112 actions, ~20 content digests, ~6 thesis threads, ~22 build items.

### Decision 3: Vector/Semantic Search — Directional, Not Final
pgvector on Postgres is the reference architecture. Decision to be revisited when retrieval use cases are more fully defined. Architecture designed so retrieval layer is swappable behind `cos_search()` in MCP.

*Ground truth augmentation:* Vision-v3 strategy is explicit: "Start with LLM-as-matcher (Notion + company index in the prompt). Add vector DB when triggered by: second signal source (Granola), 500+ companies, or need for sub-second retrieval." None of these triggers have fired yet, so vector DB remains correctly deferred.

### Decision 4: Surface Migration
- **Build:** Claude Code (hooks, CLAUDE.md, subagents, Tailscale to droplet)
- **Consume:** Claude.ai mobile/desktop (MCP-connected, mobile-friendly)
- **Automate:** Agent SDK runners on droplet (no human in loop)

Cowork deprecated gradually — move scheduled tasks to Agent SDK runner, stop opening Cowork, verify nothing missed after 2 weeks.

*Ground truth note:* Cowork is currently the primary build surface (39 sessions). Deprecation should be phased carefully — Cowork has capabilities that Claude Code doesn't (browser automation, Vercel deployment, file presentation). The MCP server + Agent SDK combination would need to replicate these before deprecation.

### Decision 5: Agent SDK — Narrow Runners, Not General Agent
The OpenClaw deployment test showed: general-purpose agents with computers produce slop on open-ended work. Claude Code with human in loop produces quality. The discipline: Agent SDK only executes what has already been designed in Claude Code. It never designs.

Runners identified: PostMeetingAgent, ContentAgent, OptimiserAgent, IngestAgent, SyncAgent.

*Ground truth augmentation:* Vision-v1 identified 7 specialist agents (Signal Catcher, Meeting Intelligence, Network Weaver, Thesis Tracker, Calendar Intelligence, Pipeline Manager, Portfolio Watcher) + Orchestrator. The brainstorm's 5 runners are a pragmatic consolidation. Mapping: PostMeetingAgent ≈ Meeting Intelligence, ContentAgent ≈ Pipeline Manager + Signal Catcher (content), OptimiserAgent ≈ Network Weaver + Calendar Intelligence, IngestAgent ≈ Signal Catcher (manual), SyncAgent = new (infrastructure).

### Decision 6: Preference Store as Learning Foundation
The most critical missing primitive. Must exist before first Agent SDK runner writes its first action. Learning mechanism: not ML training, not fine-tuning. Emergent from injecting Aakash's full accept/reject decision history into every Agent SDK reasoning session before it reasons.

Key insight: after 6 months, the preference store makes AI CoS measurably better at predicting Aakash's actions than after 6 days. This is the compounding mechanism.

*Ground truth augmentation:* The Actions Queue already captures accept/reject decisions via Status field (Proposed → Accepted/Dismissed). Content Digest DB captures action lifecycle via the state contract (Pending → Reviewed → Actions Taken → Skipped). The preference store would formalize this into a structured table optimized for injection into reasoning context. Vision-v3 calls this the Learning Loop.

---

## 4. What This Session Did NOT Have Access To (Resolved)

| Gap | Resolution |
|-----|-----------|
| Exact current state of what is built vs designed vs planned | CONTEXT.md has full build state through Session 039. Build Roadmap DB has 22 items with status tracking. |
| DeVC collective funnel stages and product logic | CONTEXT.md defines Deal Flow Funnel (TOFU/MOFU/BOFU) and 7 DeVC Collective Sourcing channels. See Doc 2 Enhanced. |
| Full vision document | Three vision docs exist: v1 (Dec 2024, 7-agent Tier 2 design), v2 (Jan 2025, "Who Should I Meet Next?"), v3 (Mar 2026, "What's Next?" full action space). |
| Content Pipeline v5 implementation details | v4 is current and live. v5 is planned: full portfolio coverage (200+ companies), semantic matching, impact scoring, multi-source readiness. |
| Impact score definition and current formula | Action Scoring Model IS the impact score — 7 factors, thresholds ≥7/4-6/<4. See CONTEXT.md. |
| Relationship temperature scoring model | Not formally modeled. `relationship_temp` is one of 9 factors in People Scoring Model, described as "warm/cold? last interaction? trend?" Design needed. |
| Network graph current schema in Attio vs Notion | **No Attio.** Network data lives entirely in Notion Network DB (40+ fields, 13 archetypes). Companies in Companies DB (49 fields). Portfolio in Portfolio DB (94 fields). |
| X / LinkedIn ingestion work | No clean API. Vision-v1 identifies authenticated browser approach. Current path: manual screenshot/URL drop → IngestAgent (future). Explorium MCP provides some LinkedIn data enrichment. |
| Granola auto-export path | Granola MCP tools (`query_granola_meetings`, `get_meeting_transcript`) provide server-side access. No filesystem export needed. |

---

## 5. Build Roadmap Items Added or Identified This Session

| Item | Priority | Layer | Size | Status | Ground Truth Notes |
|------|----------|-------|------|--------|-------------------|
| Source Digest relation field in Actions Queue | P0 | Data/Schema | XS | ✅ Shipped (Session 017) | Already live in Notion |
| Preference Store — action_outcomes table | P0 | Data/Schema | S | To build | New — not yet in Notion or Postgres |
| QMD install + Granola index | P0 | Operating Interface | XS | **Reconsider** | Granola MCP may make this unnecessary |
| pgvector on droplet — cloud-native retrieval layer | P2 | Infrastructure | M | Deferred per vision-v3 | Trigger: 2nd signal source, 500+ companies, or sub-second retrieval need |
| MCP server — cross-surface hook layer | P1 | Infrastructure | S | To build | `ai-cos-mcp` custom server |
| Cloud infrastructure — DO droplet + Postgres + sync | P1 | Infrastructure | L | To build | Phase 2 of cloud migration |
| Agent SDK runner scaffolding | P2 | Infrastructure | M | To build | After MCP server is stable |
| Surface migration — Claude Code primary, Cowork deprecation | P2 | Operating Interface | S | To plan | Needs capability gap analysis first |
| Wire action_scorer.py into Content Pipeline | P1 | Intelligence | S | Next (from Session 039) | Script exists (172 lines), needs integration |
| Persistence audit (deferred from Session 038) | P0 | Operations | XS | Overdue | Every-5-session protocol |
