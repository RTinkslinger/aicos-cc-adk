# M-ENIAC — ENIAC Agent Machine Context
*Last updated: 2026-03-22. NEW MACHINE. 0 loops completed. Agent exists but has never run autonomously.*
*ENIAC ABSORBS Content Agent. One research brain. Dedicated WebFront tab with rich UX.*

---

## Product Vision Context

ENIAC is the **research analyst** of the AI CoS. It is the system's intelligence-gathering layer -- finding, validating, cross-referencing, and persisting research that powers every other agent's decisions.

**ENIAC is a persistent Claude Agent SDK agent on the droplet.** It REASONS about research priorities, thesis evidence, content signals, and company intelligence. Its outputs are WRITTEN to DB tables. WebFront READS those tables. The ENIAC tab on WebFront displays agent-written research findings, thesis evidence, content digests, and research proposals -- it does NOT call SQL functions that generate research summaries at render time.

**ENIAC absorbs the Content Agent.** The content pipeline becomes an ENIAC capability, not a separate pipeline:
- **Extraction mode** (automated, cron-driven): YouTube, articles, content digests, thesis signals. Previously run by Content Agent; now an ENIAC capability.
- **Research mode** (user-triaged): thesis investigation, key questions, company deep dives, competitive analysis.

Both modes produce the same thing: **ENIAC writes research findings and intelligence outputs to DB tables. WebFront reads them.**

**Three interaction streams -- the core model:**

1. **Actions for Aakash (real-world decisions):**
   - "Meet this founder -- their company maps to your Applied AI thesis"
   - "Read this paper -- it challenges your Cybersecurity conviction"
   - User responds: **Accept / Reject / Defer / Not Relevant**

2. **Actions for ENIAC itself (research depth grades):**
   - "Investigate whether Company X's unit economics support SaaS Death thesis"
   - "Find answers to key question: What's the TAM for agent-native developer tools?"
   - User responds with **depth grade:**
     - **Skip** (0) = don't bother
     - **Scan** (1) = one level, surface check
     - **Investigate** (2) = two levels, proper research
     - **Ultra** (3-4) = go very deep, multi-source, comprehensive

3. **Quality signal (RL feedback):**
   - Thumbs up / thumbs down on ENIAC's completed research findings
   - This is the reinforcement learning signal -- ENIAC learns what quality of research Aakash values
   - Persists to feedback store that all machines read

**Dedicated WebFront tab** -- ENIAC has rich content on its tab, all read from agent-written DB outputs:
- Research proposals with reasoning (why this matters to your thesis/portfolio) -- agent writes these
- Depth grading controls (Skip/Scan/Investigate/Ultra) -- user input back to agent
- Active research progress (what ENIAC is working on) -- agent updates status in DB
- Completed findings with evidence quality indicators -- agent writes findings with confidence scores
- Thesis health dashboard (conviction, key questions, evidence gaps) -- agent computes and writes
- Content pipeline status (recent digests, pending extractions) -- agent writes pipeline state
- Thumbs up/down on completed findings -- user feedback persists to DB

**Conviction guardrail:** ENIAC NEVER sets thesis conviction. It saves evidence and lets Aakash decide.

**CAI inbox:** Exists (`cai_inbox`) but deprioritized. Not actively used. All ENIAC interaction via WebFront for now.

---

## Architecture: Agent Writes, WebFront Reads

### How It Works
1. **ENIAC agent runs on droplet** (persistent ClaudeSDKClient via lifecycle.py).
2. **Agent uses SQL tools to FETCH data** -- research queue, thesis context, company records, content extraction results.
3. **Agent REASONS** about what it found -- cross-references sources, evaluates evidence quality, identifies thesis implications, generates research proposals.
4. **Agent WRITES outputs to DB** -- findings, proposals, thesis evidence, content digests, dashboard data.
5. **WebFront READS agent-written outputs** from DB tables. No SQL function generates intelligence at render time.

### SQL Functions: Tools vs Outputs

**CORRECT -- utility tools the agent calls (data access):**
- `eniac_research_queue(p_limit)` -- returns prioritized research backlog (simple query)
- `eniac_research_brief(p_thesis_id, p_company_id)` -- full context package (data aggregation)
- `eniac_save_research_findings(type, id, finding_type, content, source, confidence)` -- persist agent's findings (write plumbing)
- `agent_search_context()`, `balanced_search()`, `enriched_balanced_search()` -- search/retrieval tools
- `company_holistic_search()`, `person_holistic_search()` -- data lookup tools
- Thread RPCs -- communication plumbing

**WRONG -- SQL functions that generate intelligence (should be agent output):**
- `thesis_health_dashboard()` -- if it computes health assessments, that's agent reasoning
- `detect_emerging_signals()`, `detect_interaction_patterns()`, `detect_opportunities()` -- detection = agent reasoning
- `network_intelligence_report()`, `interaction_intelligence_report()` -- intelligence generation = agent output
- `company_intelligence_profile()`, `deal_intelligence_brief()` -- intelligence profiles = agent output
- `detect_thesis_bias()` -- bias detection = agent reasoning

**Target:** Agent calls utility tools to fetch data, reasons about it, writes intelligence outputs to DB. WebFront reads agent outputs. Intelligence-generating SQL functions are deprecated.

---

## Accumulated Decisions

### Pre-Loop -- Agent Design (from M6, M9, and architecture sessions)

**Identity and boundaries:**
- ENIAC is a research analyst, NOT a strategist (Megamind), NOT a data processor (Datum), NOT a communications agent (Cindy)
- ENIAC produces research findings. Other agents consume them.
- ENIAC writes via `eniac_save_research_findings()` ONLY -- never raw INSERT/UPDATE
- Content Agent code/CLAUDE.md to be merged into ENIAC

**51 SQL functions documented in CLAUDE.md:**
- ~15 are utility tools (search, queue, save) -- these STAY as agent tools
- ~36 are intelligence-generating (detect, profile, report, dashboard) -- these should become AGENT OUTPUTS, not SQL computations
- Migration: Agent uses utility tools to fetch data, reasons, writes outputs to DB

**Research toolkit verified (3 core functions -- correct architecture):**
- `eniac_research_queue(p_limit)` -- returns prioritized research backlog (data access tool)
- `eniac_research_brief(p_thesis_id, p_company_id)` -- full context package (data aggregation tool)
- `eniac_save_research_findings(type, id, finding_type, content, source, confidence)` -- persist findings (write plumbing)

**2 skill files created:**
- `skills/eniac/eniac-research.md` -- research queue, briefs, saving findings
- `skills/eniac/eniac-search.md` -- cross-surface search (8 surfaces)
- (2 more needed: `eniac-thesis-analysis.md`, `eniac-company-intelligence.md`)

**Subagent configs defined but untested:**
- `web-researcher` -- multi-step web investigations
- `thesis-analyst` -- thesis health, bias, momentum
- `company-profiler` -- company intelligence gathering

**7 research actions routed by Megamind** awaiting first autonomous run.

---

## Patterns of Success

*(Projected -- to be validated in first loops)*

1. **Agent writes, WebFront reads.** ENIAC writes research findings, thesis evidence, content digests, and proposals to DB tables. WebFront tab reads those outputs. No SQL generates intelligence at render time.
2. **Queue-driven execution.** Check research queue on heartbeat, pick highest-priority item.
3. **Brief before research.** Call `eniac_research_brief()` first to see what's known and what gaps exist (data access tool).
4. **Save with confidence scores (0.0-1.0).** Primary sources 0.85+, secondary 0.75+, inferred 0.4-0.6.
5. **Cross-reference theses.** After every company research, check thesis relevance. Agent reasons about this, not SQL.
6. **Subagents for web, self for DB.** Spawn web-researcher for multi-page investigations.
7. **Depth grades drive research investment.** Skip = don't run. Scan = quick check. Investigate = proper research. Ultra = comprehensive multi-source. Agent reads user's depth grade and calibrates effort accordingly.
8. **Thumbs up/down drives quality learning.** Agent reads accumulated feedback to understand what quality of research Aakash values. This is the RL training signal.

---

## Anti-Patterns (Learned)

1. **SQL functions that generate intelligence.** `detect_emerging_signals()`, `company_intelligence_profile()`, `thesis_health_dashboard()` etc. encode reasoning in SQL. This is WRONG. Agent reasons; SQL fetches data.
2. **WebFront calling SQL that generates research summaries.** WebFront should read pre-computed agent outputs from DB, not trigger intelligence computation at render time.
3. **Section 4 "Research Protocol" is procedural.** MUST be rewritten to objectives. Agent CLAUDE.md defines objectives and boundaries; skills define tools and patterns.
4. **Do NOT make strategic recommendations.** Evidence only. Megamind does strategy.
5. **Do NOT create/modify entities directly.** Datum owns entity lifecycle.
6. **Do NOT run >3 concurrent subagents.** Droplet memory constraint (~3.8GB shared).
7. **Max 3 web search failures before moving on.**
8. **Content pipeline as separate system.** Content extraction is an ENIAC capability, not a separate pipeline with its own agent. One research brain.

---

## Cross-Machine Context

### What ENIAC Produces (writes to DB)
| Consumer | What | How |
|----------|------|-----|
| **M1 WebFront** | ENIAC tab content: research proposals, findings, thesis health, content digests | WebFront READS agent-written outputs from DB tables |
| **M7 Megamind** | Research findings that change strategic picture | Megamind reads ENIAC's findings from DB |
| **M4 Datum** | Enrichment signals (company details, person info from web research) | ENIAC writes signals; Datum picks them up |
| **M8 Cindy** | Context on people/companies before meetings | ENIAC's findings available in DB for Cindy to read |
| **M5 Scoring** | Research quality signals that affect action scoring | ENIAC writes quality indicators; scoring reads them |

### What ENIAC Consumes
| Producer | What |
|----------|------|
| **M7 Megamind** | Research queue items + strategic priorities (7 queued). Megamind writes routing decisions; ENIAC reads them. |
| **M6 IRGI** | All 8 search surfaces (utility tools ENIAC calls) |
| **M10 CIR** | Fresh embeddings |
| **M4 Datum** | Entity records and interaction data |
| **User (WebFront)** | Depth grades on proposed research actions (Skip/Scan/Investigate/Ultra) + thumbs up/down quality feedback. WebFront writes user input to DB; ENIAC reads it. |

---

## Current Focus

**Overhaul to agent-output architecture:**
1. Identify which of the 51 SQL functions are utility tools (keep) vs intelligence-generating (deprecate after agent absorbs).
2. Define the output tables ENIAC writes to (research findings, thesis evidence, content digests, proposals, dashboard data).
3. Ensure WebFront reads from those tables, not from intelligence-generating SQL.

**P0: Rewrite ENIAC agent CLAUDE.md** — current CLAUDE.md (469 lines) lists 51 SQL functions without distinguishing utility tools (~15 KEEP) from intelligence generators (~36 DELETE/DEMOTE). Full rewrite needed: (1) merge Content Agent CLAUDE.md into ENIAC, (2) rewrite Section 4 from procedural script to objectives, (3) define output tables ENIAC writes to, (4) classify SQL functions, (5) add depth grade awareness and RL feedback loop.

**Pre-activation tasks (must complete before running on droplet):**
1. Complete CLAUDE.md rewrite (above)
3. Write remaining skill files (thesis-analysis, company-intelligence)
4. Test subagent configs on droplet
5. Deploy updated agent files via deploy.sh
6. Build ENIAC WebFront tab to read agent outputs from DB (M1's job)

**First loop priorities (after activation):**
1. Process 7 queued research items from Megamind
2. Run thesis health check -- agent reasons about weak theses, writes findings to DB
3. Run content extraction pipeline (absorbed Content Agent capability)
4. Save findings and verify cross-reference with thesis threads
5. Write research proposals for user depth grading (proposals to DB, user grades via WebFront)
