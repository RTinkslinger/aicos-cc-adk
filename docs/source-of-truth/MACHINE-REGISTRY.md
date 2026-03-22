# Machine Registry — Perpetual Machineries v3
*Updated: 2026-03-22. Defines all machines, their pending work, and feedback queues.*

---

## Architecture Principle — Agent Output Model

**The fundamental data flow: raw data sits in SQL tables. Agents reason over it. Agents write outputs to dedicated output tables. WebFront reads those outputs with simple SELECTs.**

```
RAW DATA (SQL tables)          AGENTS (Claude SDK)           AGENT OUTPUTS (SQL tables)        WEBFRONT
┌──────────────────┐          ┌──────────────┐              ┌─────────────────────┐           ┌──────────┐
│ companies        │──read──→ │              │──write──→    │ agent_intelligence  │──SELECT──→│          │
│ network          │──read──→ │  Datum       │──write──→    │ agent_scores        │──SELECT──→│ digest   │
│ portfolio        │──read──→ │  Cindy       │──write──→    │ agent_obligations   │──SELECT──→│  .wiki   │
│ whatsapp_convos  │──read──→ │  Megamind    │──write──→    │ agent_risk_views    │──SELECT──→│          │
│ interactions     │──read──→ │  ENIAC       │──write──→    │ agent_summaries     │──SELECT──→│          │
│ content_queue    │──read──→ │              │              │ agent_recommendations│           │          │
└──────────────────┘          └──────────────┘              └─────────────────────┘           └──────────┘
         ↑                           ↑
    SQL functions              SQL functions
    (utility tools)            (called BY agents)
```

### What lives WHERE

| Layer | Examples | Role |
|-------|----------|------|
| **Raw data tables** | `companies`, `network`, `portfolio`, `whatsapp_conversations`, `interactions`, `content_queue` | Store facts. No intelligence. Populated by pipelines, syncs, user input. |
| **SQL functions (KEEP as tools)** | `search_*()`, `fuzzy_match_*()`, `embedding_similarity()`, `datum_resolve_identity()`, `portfolio_founders()` | Utility infrastructure agents call. Search, retrieval, fuzzy matching, embedding similarity. Pure data access. |
| **SQL functions (KEEP as deterministic computation)** | `compute_action_score()`, `calculate_recency_boost()` | Formula execution with well-defined inputs/outputs. The FORMULA is deterministic; the INPUTS and OVERRIDES come from agents. |
| **SQL functions (DEMOTE/DELETE)** | `*_auto_process()`, `*_generate_intelligence()`, `*_assess_risk()`, `*_detect_*()`, `*_recommend_*()` | These encode reasoning in SQL. That reasoning belongs in agents. Demote to simple data-fetch tools or delete entirely. |
| **Agent output tables** | `agent_intelligence`, `agent_scores`, `agent_obligations`, `agent_risk_views`, `agent_summaries`, `agent_recommendations` | Written exclusively by agents after reasoning. WebFront reads these. Never written by SQL functions. |
| **WebFront** | `digest.wiki` Next.js pages | Simple SELECT from agent output tables. Zero reasoning. Zero complex joins. If a page needs a 15-line SQL query, the agent should have pre-computed that output. |

### Scoring = Hybrid Model

Scoring is the one area where SQL and agents collaborate:
- **SQL formula** (`compute_action_score()`) executes the deterministic scoring formula (bucket_impact * conviction * recency * ...)
- **Agent override**: Agents can write score adjustments, overrides, or context annotations to `agent_scores`
- **WebFront** reads the final merged score (formula result + agent adjustments)

### Search = SQL Infrastructure + Agent Disambiguation

- **SQL infrastructure**: `search_unified()`, `embedding_similarity()`, `fuzzy_match_*()` — fast retrieval
- **Agent disambiguation**: When search returns ambiguous results, agents reason about which result the user meant
- Agents call search SQL functions as tools, then reason about the results

---

## Lifecycle Trigger Chain (Event-Driven Architecture)

```
WhatsApp upsert (new messages land)
    │
    ├──pg_notify('new_whatsapp')──→ Datum agent
    │                                 │
    │                                 ├── resolve identities
    │                                 ├── link to network/companies
    │                                 └── write to `interactions` table
    │                                         │
    │                                         ├──pg_notify('new_interactions')──→ Cindy agent
    │                                         │                                     │
    │                                         │                                     ├── detect obligations
    │                                         │                                     ├── extract relationship signals
    │                                         │                                     ├── synthesize intelligence
    │                                         │                                     └── write to agent output tables
    │                                         │                                             │
    │                                         │                                             └──→ WebFront reads on next load
    │                                         │
    │                                         └──pg_notify('new_interactions')──→ Megamind agent
    │                                                                               │
    │                                                                               ├── strategic pattern detection
    │                                                                               ├── portfolio risk reassessment
    │                                                                               └── write to agent output tables
    │
    └── (batch/polling fallback for non-urgent processing)

Content pipeline (new content extracted)
    │
    └──→ ENIAC agent ──→ thesis analysis ──→ agent output tables ──→ WebFront
```

**Two trigger modes:**
- **Event-driven** (`pg_notify`): For high-priority, real-time chains (new WhatsApp → identity resolution → obligation detection)
- **Polling** (cron/heartbeat): For batch processing, enrichment sweeps, periodic re-scoring

---

## Architecture

```
USER (CC chat)  ──→  CC ORCHESTRATOR  ──→  Routes to machines
                                            ↕
USER (WebFront)  ──→  M-FEEDBACK  ──→  Analyzes with product specialists
                      (Product Org)       ──→  Routes decomposed tasks to machines
```

**CC Orchestrator** handles: direct CC chat inputs, machine launch/relaunch, cross-machine context propagation, task dashboard.

**M-FEEDBACK (NEW)** handles: WebFront feedback analysis using product org specialist agents (Product Manager, UX Researcher, Data Analyst, Engineering Lead). Decomposes user feedback into component-specific tasks and routes to relevant machines with rich context. Reads from `user_feedback_store` + `cindy_conversation_log` (implicit feedback).

**Why M-FEEDBACK is better than CC routing feedback:** User feedback from WebFront is about the FINAL EXPERIENCE — it touches UI + intelligence + data + scoring + agents simultaneously. A dedicated machine with product specialists can properly decompose "this looks wrong" into: UI rendering issue (→M1), data quality gap (→M4/M12), scoring miscalibration (→M5), intelligence reasoning failure (→agent machines), missing skill (→agent machines). CC orchestrator lacks the depth to do this well.

---

## Machine List (12 perpetual + M-FEEDBACK)

### Agent Machines (4) — Build smarter agents

Each agent machine's loop:
1. Check feedback (explicit from M-FEEDBACK + implicit from conversation logs)
2. Product Leadership Assessment (specialist agents analyze gaps)
3. Research (study best-in-class, explore new patterns)
4. Build (SQL tools, skills, CLAUDE.md updates, hooks, subagent configs)
5. Review (verify agent works correctly with new capabilities)
6. Cross-machine sync (propagate changes to dependent machines)

---

### M4 — Datum Agent Machine
**Purpose:** Continuously improve the Datum agent's reasoning, tools, skills, and autonomous capabilities.

**Pending Feedback:**
- FB-25: Thesis links poor quality → semantic matching BUILT but agent needs skill to know WHEN to re-run matching
- FB-26: Similar companies off → `datum_similar_companies()` built, agent needs skill for company similarity reasoning
- FB-22: Founder misclassification → FIXED in SQL, agent needs awareness of `portfolio_founders()` vs `led_by_ids` distinction

**Pending Work:**
- **ARCHITECTURE OVERHAUL: Transition from SQL-generated intelligence to agent-written outputs**
  - `datum_task_auto_process()` → DELETE (reasoning logic). Replace with agent polling `agent_tasks` and reasoning about each task.
  - `datum_resolve_identity()` → KEEP as tool (utility function agents call)
  - `datum_similar_companies()` → KEEP as tool (embedding similarity search)
  - `datum_enrich_*()` functions → DEMOTE to simple data-fetch tools. Agent decides WHAT to enrich and HOW.
  - `datum_merge_*()` functions → KEEP as tools (deterministic merge operations)
  - Agent must WRITE resolution results, enrichment outputs, and data quality assessments to agent output tables
- Wire `lifecycle.py` to poll `agent_tasks` — Datum agent reasons about user tasks (not SQL auto_process)
- Process 30 queued high-value WhatsApp contacts from cai_inbox
- Resolution ceiling: 83 phone-number-only + 79 not-in-network contacts. Agent needs web research capability to resolve.
- 5 real data gap tasks sitting in `/datum` tab for user triage
- 3,800+ skeletal companies need web enrichment (agent's autonomous job)
- Build skills for: identity resolution patterns, merge decision-making, enrichment prioritization
- Fix portfolio-founder links (M4 L6 found 0 portfolio-founder links exist)

**Agent Files:** `mcp-servers/agents/datum/CLAUDE.md` (38 functions), 8 skill files

---

### M7 — Megamind Agent Machine
**Purpose:** Continuously improve Megamind's strategic reasoning, co-strategist capability, and autonomous decision-making.

**Pending Feedback:**
- FB-34: Natural language text input → Megamind should interpret strategic questions from free text
- System feedback: Megamind portfolio_review ignores mentioned company name (returns generic risk instead of AuraML-specific)

**Pending Work:**
- **ARCHITECTURE OVERHAUL: Transition from SQL-generated intelligence to agent-written outputs**
  - `megamind_task_auto_process()` → DELETE (reasoning logic). Agent polls `agent_tasks` and reasons.
  - `megamind_strategic_contradiction_detector()` → DELETE (detection logic belongs in agent reasoning). Keep underlying data-fetch as a tool.
  - `megamind_morning_strategic_context()` → DELETE (intelligence generation). Agent writes strategic context to `agent_intelligence` table.
  - `megamind_portfolio_risk_*()` → DEMOTE to data-fetch tools. Agent reasons about risk and writes to `agent_risk_views`.
  - `megamind_convergence_*()` → KEEP as tools (data retrieval for convergence tracking)
  - Agent must WRITE strategic assessments, contradiction analyses, portfolio risk views, and morning context to agent output tables
- Wire `lifecycle.py` to poll `agent_tasks` — Megamind reasons about strategic questions
- Push convergence past 0.904 (14 Accepted items need human triage or ENIAC execution)
- Content Agent CLAUDE.md was rewritten but needs validation that agent uses it correctly
- Build skills for: strategic contradiction reasoning, portfolio risk assessment patterns, action routing heuristics
- 37 contradictions detected — agent should autonomously investigate and propose resolutions

**Agent Files:** `mcp-servers/agents/megamind/CLAUDE.md` (381 lines, 22 functions), skills TBD

---

### M8 — Cindy Agent Machine
**Purpose:** Continuously improve Cindy's EA intelligence, communication reasoning, and relationship management.

**Pending Feedback:**
- FB-29: Interaction history needs richer intelligence, not raw dump → agent needs better summarization skills
- FB-30: Internal intelligence (Notion, WhatsApp, email) should be on portfolio pages → agent needs cross-source synthesis skill
- FB-33: Contextual options + conversation log for perpetual context → cindy_conversation_log BUILT, needs integration into every interaction point
- FB-34: Free-text command → Cindy should interpret "draft email to X" from natural language
- FB-35: Portfolio founders at risk → section renamed, but intelligence suggestions need to come from agent reasoning
- FB-36: Interaction history "dumb dump" → M1 added relationship arc + key moments, but SUMMARIZATION needs agent intelligence

**Pending Work:**
- **ARCHITECTURE OVERHAUL: Transition from SQL-generated intelligence to agent-written outputs**
  - `cindy_task_auto_process()` → DELETE (reasoning logic). Agent polls `agent_tasks` and reasons.
  - `cindy_obligation_detector()` / `cindy_detect_*()` → DELETE (detection logic belongs in agent reasoning). Keep data-fetch portions as tools.
  - `cindy_relationship_summary()` → DELETE (summarization = agent reasoning). Agent writes summaries to `agent_summaries`.
  - `cindy_interaction_intelligence()` → DELETE (intelligence generation). Agent writes to `agent_intelligence`.
  - `cindy_get_interactions()`, `cindy_get_obligations()` → KEEP as tools (pure data retrieval)
  - `cindy_conversation_log` read/write functions → KEEP as tools
  - Agent must WRITE obligation assessments, relationship summaries, communication intelligence, and recommended actions to agent output tables
- Wire `lifecycle.py` to poll `agent_tasks` — Cindy reasons about communication tasks
- 404 interactions remaining need deeper obligation analysis (processed but not all scanned for obligations)
- Granola MCP unblock on droplet (multi-surface intelligence currently limited)
- Build skills for: obligation detection patterns, relationship story generation, draft message composition
- Wire conversation log into WebFront (every dismiss/accept/respond logs to cindy_conversation_log)
- Cross-reference portfolio DB in ALL obligation processing (Surabhi/Soulside pattern)

**Agent Files:** `mcp-servers/agents/cindy/CLAUDE.md` (224 lines, 46 functions), 11 skill files

---

### M-ENIAC — ENIAC Agent Machine (NEW)
**Purpose:** Continuously improve ENIAC's research analysis, thesis investigation, and autonomous research execution.

**Pending Work:**
- **ARCHITECTURE OVERHAUL: Transition from SQL-generated intelligence to agent-written outputs**
  - `eniac_research_brief()` → KEEP as tool (data retrieval for research context)
  - `eniac_research_queue()` → KEEP as tool (queue management)
  - `eniac_save_research_findings()` → KEEP as tool (write path for agent output)
  - `eniac_auto_analyze_*()` → DELETE if exists (analysis = agent reasoning)
  - `eniac_thesis_relevance_*()` → DEMOTE to data-fetch tools. Agent reasons about thesis relevance and writes to `agent_intelligence`.
  - Agent must WRITE research findings, thesis analyses, company profiles, and competitive analyses to agent output tables
- ENIAC is in `lifecycle.py` but has NEVER run autonomously on the droplet
- CLAUDE.md exists (469 lines, 51 functions) but hasn't been battle-tested
- 7 research actions routed to ENIAC by Megamind — need execution
- Section 4 of CLAUDE.md is still a script (M9 found in L5) — needs objective rewrite
- Build skills for: thesis investigation patterns, company deep research, competitive analysis, web research orchestration
- Wire ENIAC to use Web Tools MCP for autonomous web research
- Build subagent configs: web-researcher, thesis-analyst, company-profiler (defined in lifecycle.py but not tested)

**Agent Files:** `mcp-servers/agents/eniac/CLAUDE.md` (469 lines, 51 functions), 2 skill files

---

### Infrastructure Machines (6) — Continuous system improvement

---

### M1 — WebFront Machine
**Purpose:** Continuously evolve digest.wiki UI/UX. Mobile-first. Renders agent output.

**Pending Feedback:**
- FB-33: Contextual agent interaction from rich content (tap obligation → Cindy thread opens about THAT item with contextual UI, not chat)
- FB-34: Free-text command input on actions page (10x UX vision)
- FB-36: Interaction history summarization (relationship arc added, but deeper agent-powered summarization needed)
- FB-27: AddSignal UX loved (5/5) — evolve and make better, add DB edit capability with audit trail

**Pending Work:**
- **Refactor all data fetching from SQL RPC calls to simple reads from agent output tables**
  - Current state: Pages call complex SQL RPCs that join, filter, score, and format data
  - Target state: Pages do simple `SELECT * FROM agent_intelligence WHERE type = 'obligations' ORDER BY priority`
  - Each page maps to one or two agent output tables — no multi-table joins in the frontend
  - Scoring display reads from `agent_scores` (pre-computed by scoring formula + agent overrides)
  - Intelligence cards read from `agent_intelligence` (pre-written by Cindy/Megamind/ENIAC)
  - Risk views read from `agent_risk_views` (pre-computed by Megamind)
  - Relationship summaries read from `agent_summaries` (pre-written by Cindy)
  - Recommended actions read from `agent_recommendations` (pre-written by agents)
- Integrate threads INTO /comms and /strategy pages (not separate routes) — triggered by tapping cards
- Thread UI renders rich contextual elements, NOT chat bubbles
- Every agent interaction (dismiss, accept, respond) must log to implicit feedback (conversation logs)
- Verify all pages at 375px mobile viewport
- Wire `megamind_morning_strategic_context()` improvements as M7 evolves it
- Action triage page: `action_scores` table is empty — investigate pipeline
- Build file upload on /datum task creation
- Add Cindy/Megamind contextual thread triggers on their respective pages

**Deploys this session:** 14+ commits to digest.wiki

---

### M5 — Scoring Machine
**Purpose:** Continuously evolve the action scoring model.

**Pending Work:**
- Model at v5.5-final, 9.2/10 — strong state
- `action_scores` table is empty — investigate why the pipeline isn't populating it
- Monitor thesis_breadth_multiplier now that 4,560 companies are thesis-linked
- Watch for new interaction patterns from WhatsApp data feeding recency boost
- Next model evolution: consider user implicit feedback (dismiss patterns) as a multiplier calibration signal

**Agent Files:** Scoring skill at `mcp-servers/agents/skills/scoring/scoring-model.md`

---

### M6 — IRGI Machine
**Purpose:** Continuously evolve search, retrieval, and intelligence infrastructure.

**Pending Work:**
- 46/46 benchmark, 9.7/10 — strong state
- `interaction_thesis_xref` still slowest test (17ms, was 1006ms — acceptable but could improve)
- Wire `search_disambiguation()` into agent thread auto-processing (agents call it when resolving ambiguous queries)
- Build search quality monitoring (detect degradation before users notice)
- Consider adding `agent_task_messages` as 9th search surface when table grows

**Agent Files:** ENIAC search skill at `mcp-servers/agents/skills/eniac/eniac-search.md`

---

### M9 — Intel QA Machine
**Purpose:** Honest quality auditing of ALL machine outputs.

**Pending Work:**
- System at 8.3/10 — core blocker is data quality (1.5/10)
- Verify all WebFront pages render correctly on mobile (375px)
- Continue auditing agent CLAUDE.md quality — ENIAC Section 4 still scripted
- Monitor obligation quality as Cindy processes more interactions
- Validate implicit feedback loop (are conversation logs being read by machines?)
- Audit `action_scores` empty table issue

---

### M10 — CIR Machine
**Purpose:** Continuous intelligence refresh, embedding health, connection quality.

**Pending Work:**
- All systems green, grade A — steady state monitoring
- Build auto-embed trigger for `agent_task_messages` table (when it grows)
- Monitor 73 new network entries from WhatsApp for connection formation
- Continue evidence enrichment as new interactions flow in
- Watch for embedding dimension mismatches on any new entity types

---

### M12 — Data Enrichment Machine
**Purpose:** Enrich skeletal entity data. Queues work for Datum agent.

**Pending Work:**
- 3,800+ companies still skeletal (<500 chars) — #1 system bottleneck
- 122 research files now matched, but many companies need WEB enrichment (no local data)
- Pipeline companies (123 "In Strike Zone") need type/sells_to from web research
- Eventually: M12 should queue enrichment tasks for Datum agent (via agent_tasks), not do it itself
- M12's role evolves: identify WHAT needs enrichment → queue for Datum → Datum agent reasons and enriches

---

### M-FEEDBACK — Feedback Routing Machine (NEW)
**Purpose:** Analyze WebFront feedback with product org specialists, decompose into component tasks, route to machines.

**Architecture:**
```
user_feedback_store (explicit)  ──→  M-FEEDBACK
cindy_conversation_log (implicit)  ──→  M-FEEDBACK
                                          ↓
                              Product Org Specialist Agents:
                              ├── Product Manager: prioritize, categorize
                              ├── UX Researcher: identify interaction patterns
                              ├── Data Analyst: trace data quality issues
                              └── Engineering Lead: identify technical root causes
                                          ↓
                              Decomposed tasks routed to:
                              M1 (UI), M4/M8/M7/ENIAC (agents),
                              M5 (scoring), M6 (search), M10 (infra),
                              M12 (data)
```

**Why:** User feedback from WebFront is about the FINAL EXPERIENCE — it touches every component. "This person's info is wrong" → data quality (M4) + intelligence (M8) + rendering (M1). "Score seems off" → scoring model (M5) + data inputs (M4) + display (M1). A product org decomposes this properly.

---

## Feedback Routing Rules

| Feedback Source | Handler | Routes To |
|----------------|---------|-----------|
| CC chat (direct from user) | CC Orchestrator | Relevant machines directly |
| WebFront feedback widget (explicit) | M-FEEDBACK | Decomposed to relevant machines |
| Agent interactions (implicit) | Each agent's conversation log | Agent's own machine + M5 (scoring signal) |

---

## Cross-Machine Dependencies

```
M12 Data Enrichment ──queues──→ M4 Datum Agent
M4 Datum ──data quality──→ M5 Scoring, M6 IRGI, M8 Cindy
M8 Cindy ──intelligence──→ M7 Megamind (strategic synthesis)
M7 Megamind ──priorities──→ M1 WebFront (morning dashboard)
M5 Scoring ──scores──→ M1 WebFront (action triage)
M6 IRGI ──search──→ All agents (tools)
M10 CIR ──embeddings──→ M6 IRGI (semantic search)
M9 Intel QA ──audits──→ All machines (quality feedback)
M-FEEDBACK ──decomposed tasks──→ All machines
M-ENIAC ──research──→ M7 Megamind (thesis intelligence)
```
