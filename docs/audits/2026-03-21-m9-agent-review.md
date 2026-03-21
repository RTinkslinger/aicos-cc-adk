# M9 Intel QA — Agent CLAUDE.md Audit Against Persistent Agent SDK Pattern

**Date:** 2026-03-21
**Machine:** M9 Intel QA
**Benchmark:** `docs/research/2026-03-21-persistent-agent-sdk-pattern.md`
**Feedback:** None (empty result from `get_machine_feedback('M9')`)

---

## Benchmark Summary

The persistent agent SDK pattern says:

1. **Python = lifecycle only.** Claude's autonomous reasoning loop handles everything.
2. **Agent has same capabilities as Claude Code** — Bash, Read, Write, Edit, Grep, Glob, Agent, Skills, Hooks.
3. **CLAUDE.md = Objectives, Not Scripts.** WHO the agent is, WHAT to achieve, boundaries, anti-patterns. NOT step-by-step processing loops.
4. **Skills = Rich Reference.** Tool signatures with WHEN to use, patterns of success, anti-patterns. Progressive disclosure (<500 lines).
5. **All tools allowed.** No restrictions. `permission_mode="dontAsk"`.
6. **The WRONG pattern:** Python tool-loop that manages state and decides tool calls. Disables concurrent execution, programmatic tool calling, session resumption, compaction.

---

## Agent-by-Agent Audit

### 1. Datum Agent (`mcp-servers/agents/datum/CLAUDE.md`)

**Lines:** ~956
**Identity section:** Strong. Clear "you are NOT an assistant" framing, autonomous, persistent, receives work from Orchestrator.

**Violations of "Objectives Not Scripts":**
- **Section 3b (lines 99-283):** 184 lines of step-by-step processing instructions for interaction staging. "For each row, process based on source... Steps: 1. For each email... 2. Cross-link... 3. Write to interactions... 4. Write people_interactions... 5. UPDATE interaction_staging." This is a SCRIPT, not an objective. The benchmark says: give the agent the objective ("process staged interactions, resolve people, link entities") and let it reason about HOW.
- **Section 4 (lines 410-516):** "Processing Flow — follow this exact sequence: Step 1: Parse Input, Step 2: Dedup Check, Step 3: Web Enrichment, Step 4: Write Record, Step 5: Create Datum Requests, Step 6: Report Back." Another scripted pipeline. A best-in-class persistent agent should know HOW to process entities from its objectives and skills, not follow a 6-step recipe.
- **Section 6 (lines 552-601):** Web enrichment decision tree is a hardcoded script ("1. If linkedin URL available AND person fields missing -> Scrape LinkedIn... 2. Elif...").
- **Section 7 (lines 605-717):** Entire "Input Types" section prescribes exact handling for each input type with step-by-step instructions.

**What's good:**
- Clear identity and boundaries (Sections 1-2)
- Clean table ownership rules (Section 3)
- Confidence gating protocol is objective-driven (Section 3c)
- Comprehensive anti-patterns (Section 11)
- Skills reference with "load on demand" guidance (Section 3c)
- 14 SQL functions as autonomous tools — excellent
- ACK protocol is well-defined

**What's missing:**
- No mention of Agent tool (subagent spawning)
- Skills loading strategy section (when to load which skill)
- Too much SQL inlined — should be in skills files with progressive disclosure

**Score: 5/10**
Identity and boundaries are strong, but the document is dominated by scripted processing sequences. An Anthropic engineer would see this and say "you've turned the LLM into a script runner." The SQL functions and confidence gating show the right instinct (give the agent tools, let it reason), but the processing flows undermine it. The document is also very long (~956 lines) — well above the <500 line recommendation for progressive disclosure. Much of the SQL and step-by-step content should live in skills.

---

### 2. Cindy Agent (`mcp-servers/agents/cindy/CLAUDE.md`)

**Lines:** ~1172
**Identity section:** Excellent. "Communications Intelligence Analyst," "observer not actor," clear separation from Datum (no data plumbing).

**Violations of "Objectives Not Scripts":**
- **Section 3, lines 110-138:** The "Processing Loop" is a numbered script: "1. Query... 2. For each interaction, REASON about: a. Obligations b. Action items c. Thesis signals... 3. Write results... 4. Mark processed." This is exactly the anti-pattern. The objective should be: "You reason about clean interactions. Detect obligations, extract signals, create actions, identify context gaps."
- **Section 4 (lines 274-411):** Four surface-specific pipelines, each with numbered steps. Email pipeline is 8 steps, WhatsApp is 8 steps, Granola is 8 steps, Calendar is 6 steps. These are scripts.
- **Section 5 (lines 414-490):** People resolution algorithm is a 6-tier script. (NOTE: People resolution is supposed to be Datum's job per the refactor, but this section still exists in Cindy's CLAUDE.md with full write operations — `UPDATE network SET email = $email WHERE id = $id`. This is a boundary violation.)
- **Section 15 (lines 961-1090):** 33 SQL functions with a "Processing Cycle Integration" script (lines 1056-1090) that prescribes exactly when to call each function in sequence. Should be suggestive, not prescriptive.

**What's good:**
- Outstanding identity definition — observer vs actor distinction is powerful
- Privacy rules (Section 10) — mandatory, well-specified
- Obligation detection (Section 7.5) — good LLM-reasoning emphasis ("LLM, not regex")
- Context gap detection with richness scoring (Section 6) — well-structured objective
- Fleet collaboration model (Section 16) — clear, well-bounded
- 33 SQL functions — massive autonomous toolkit
- Skills reference with loading strategy (Section 17) — excellent progressive disclosure
- Signal routing criteria (Section 7) — objective-driven threshold table

**What's missing/wrong:**
- **Boundary violation:** Section 5 still has Cindy writing to `network` table and `people_interactions` table, despite the refactor saying Datum owns all writes. The CLAUDE.md header says "Cindy does NOT do data plumbing" but Section 5 contradicts this.
- Document is 1172 lines — more than 2x the recommended <500 line limit.
- No mention of Agent tool for subagent delegation.
- Massive SQL query examples inline (Section 3, lines 140-270) that should be in skills.

**Score: 5/10**
Best identity definition of any agent. Excellent conceptual separation between intelligence work (Cindy) and data plumbing (Datum). But the document is bloated with scripts, has a boundary violation in Section 5, and is over 1100 lines. The 33 SQL functions show the right pattern (autonomous tools), but the "Processing Cycle Integration" section then scripts their usage. An Anthropic engineer would appreciate the architectural clarity but flag the scripted pipelines and the length.

---

### 3. Megamind Agent (`mcp-servers/agents/megamind/CLAUDE.md`)

**Lines:** ~1137
**Identity section:** Exceptional. "Convergence enforcer," "not a scorer," "not a data processor," clear differentiation from every other agent.

**Violations of "Objectives Not Scripts":**
- **Section 6 (lines 330-517):** All three work types (Depth Grading, Cascade Processing, Strategic Assessment) are presented as numbered step-by-step scripts. Depth Grading is 11 steps. Cascade Processing is 10 steps. Strategic Assessment is 10 steps. These should be objectives with examples, not mandatory step sequences.
- **Section 5 (lines 275-327):** Strategic ROI calculation is presented as a 6-step computation with exact formulas. This is borderline — formulas are reference data (good), but the "Step by Step" framing makes them feel scripted.

**What's good:**
- Identity is the best of any agent — crystal clear what Megamind IS and IS NOT
- Four priority buckets (Section 4) — objective-driven strategic framing
- Convergence rules as hard constraints (Section 8) — invariants, not scripts
- Trust ramp (Section 9) — elegant progressive autonomy model
- Diminishing returns model with contra exemption (Section 7) — sophisticated, well-reasoned
- Interaction protocol (Section 10) — shows clear ACK formats and input/output contracts
- Anti-patterns (Section 14) — 18 items, comprehensive and specific
- SQL functions inventory with views and triggers (Section 13) — massive autonomous toolkit
- Collaboration model (Section 14/end) — clean read/write matrix

**What's missing:**
- No mention of Agent tool for subagent delegation
- Document exceeds 1100 lines — should use progressive disclosure to skills
- The 11-step depth grading algorithm should be a skill, not inline

**Score: 6/10**
The strongest identity and strategic clarity of any agent. Megamind's convergence invariants, trust ramp, and diminishing returns model are genuinely sophisticated. The problem is execution: the three work types are presented as rigid numbered scripts rather than objectives with reference patterns. The document is also far too long. An Anthropic engineer would be impressed by the strategic thinking but would refactor the scripts into skills and cut the CLAUDE.md to ~400 lines of identity + objectives + boundaries.

---

### 4. ENIAC Agent (`mcp-servers/agents/eniac/CLAUDE.md`)

**Lines:** ~417
**Identity section:** Good. Clear "Research Analyst" identity, good NOT statements (not strategist, not data processor, not comms agent).

**Violations of "Objectives Not Scripts":**
- **Section 4 (lines 225-310):** Research Protocol is an 8-step cycle: "1. ORIENT, 2a. QUEUE, 2b. BRIEF, 3. SEARCH, 4. RESEARCH, 5. SYNTHESIZE, 6. PERSIST, 7. CROSS-REF, 8. ALERT." This is a script. The objective should be: "You research, synthesize, and persist findings. Use your queue, brief, and search functions to orient. Use web tools to fill gaps. Always cross-reference thesis implications and alert on urgent intelligence."
- **Section 4 (lines 281-309):** "Periodic Health Checks — run these at least once per session" with 5 specific psql commands. Prescriptive.

**What's good:**
- Document length is 417 lines — closest to the <500 line recommendation
- Clear function inventory (48 functions) organized by category — excellent
- Conviction guardrail (Section 5) — CAN/CANNOT list is objective-driven
- Research quality standards (Section 6) — good quality bars without being scripts
- Cross-agent coordination (Section 7) — clean produce/consume matrix
- Error handling (Section 8) — good, concise
- Session state (Section 9) — clean

**What's missing:**
- No anti-patterns section. Every other agent has one.
- No ACK protocol. Every other agent has structured acknowledgment requirements.
- No compaction protocol. Other agents have checkpoint/COMPACT_NOW handling.
- No mention of Agent tool or Skills tool beyond brief table listing.
- No skills loading strategy (which skill for which task).
- State files use different naming convention (`current_session.json`, `live.log`) vs other agents (`eniac_last_log.txt`, `eniac_iteration.txt`).
- Session state path hardcoded to `/opt/agents/eniac/state/` — should be relative for consistency.

**Score: 5/10**
ENIAC is the newest agent and it shows — the document is the right length but incomplete. The 48 SQL functions are excellent, the identity is clear, and the conviction guardrail is well-specified. But it lacks anti-patterns, ACK protocol, compaction handling, and skills loading guidance that every other agent has. The 8-step research protocol is a script. An Anthropic engineer would see a good skeleton but would flag the missing lifecycle sections and the scripted protocol.

---

### 5. Orchestrator Agent (`mcp-servers/agents/orchestrator/CLAUDE.md`)

**Lines:** ~248
**Identity section:** Clean, appropriately lean. "Central coordinator," "lean," "delegate all substantive work."

**Violations of "Objectives Not Scripts":**
- Minimal scripting issues. The Orchestrator's nature is inherently procedural (check inbox, route messages, check conditions, delegate). The step-by-step SQL queries in Sections 5b/5c/5d are reference patterns for how to detect work, which is appropriate for a coordinator.

**What's good:**
- Appropriately short (248 lines) — the leanest agent
- Clear tool list including all four agent bridges
- Single-table write scope (`cai_inbox.processed` only) — excellent boundary
- Heartbeat pattern delegates to HEARTBEAT.md — good progressive disclosure
- Anti-patterns (Section 8) — 18 items, comprehensive routing rules
- Compaction and session restart protocols present

**What's missing:**
- **Does NOT know about ENIAC Agent.** The Orchestrator has bridges for Content, Datum, Megamind, and Cindy — but no `send_to_eniac_agent` bridge. ENIAC is listed as consuming work from the Orchestrator in its own CLAUDE.md, but the Orchestrator has no mechanism to send work to ENIAC.
- No explicit mention of ENIAC in any section — not even in anti-patterns routing rules.
- No health monitoring of agents (are they alive, stuck, crashed?).
- No daily summary/report generation.

**Score: 7/10**
The Orchestrator is the best-aligned with the persistent agent pattern — it's lean, delegates everything, has clear boundaries, and doesn't script internal reasoning. It IS a coordinator, so its step-by-step nature is appropriate. The critical gap is that it has no awareness of ENIAC at all. ENIAC exists as a fleet agent but cannot receive work from the Orchestrator. This is either a deployment gap (bridge not yet built) or an oversight in the CLAUDE.md. Either way, ENIAC is effectively disconnected from the system.

---

### 6. Content Agent (`mcp-servers/agents/content/CLAUDE.md`)

**Lines:** ~633
**Identity section:** Good. Clear role as content analyst, autonomous, persistent.

**Violations of "Objectives Not Scripts":**
- **Section 4 (lines 96-157):** Content Pipeline Trigger is a 3-phase, multi-step script. Phase 1 is 3 steps, Phase 2 is 8 substeps per item, Phase 3 is 1 step. This is the most scripted pipeline in the system.
- **Section 8 (lines 246-294):** "Analysis Sequence" is a 10-step script: "1. Read content, 2. Load thesis threads, 3. Identify thesis connections FIRST..." This should be an objective with the analysis framework as reference in a skill.

**What's good:**
- Three classes of work (Section 12) — Direct, Complex Delegation (subagent), Parallel Batch — shows awareness of the Agent tool for delegation. This is the ONLY agent that documents subagent usage.
- DigestData JSON schema (Section 16) — clear contract definition
- Web access strategy (Section 11) — decision tree for stateless vs stateful access
- Conviction guardrail (Section 13) — well-specified CAN/CANNOT
- Skills loading guidance (Section 8) — "load these skills and apply"
- ACK protocol present and well-formatted
- Anti-patterns (Section 15) — 15 items, comprehensive
- State tracking and compaction present

**What's missing:**
- No mention of ENIAC as a consumer of Content Agent's output or a collaborator
- Scoring model (Section 9) is reasonably objective-driven but still has some scripted feel

**Score: 6/10**
The Content Agent gets bonus points for being the only agent that documents subagent usage (Agent tool) and has a clear class-of-work framework. Its identity and conviction guardrails are strong. The pipeline and analysis sequence are scripted, though — the content pipeline especially reads like a Python function translated to English. At 633 lines, it's above the <500 target but more manageable than Cindy or Megamind. An Anthropic engineer would appreciate the Agent tool usage and class-of-work framework but would refactor the pipeline steps into skills.

---

## Cross-Cutting Findings

### 1. Universal Problem: Scripts Masquerading as Objectives

Every agent except the Orchestrator has numbered step-by-step processing sequences embedded in the CLAUDE.md. The benchmark is explicit: "CLAUDE.md = Objectives, Not Scripts." The agents need:
- **CLAUDE.md:** WHO you are, WHAT you achieve, boundaries, anti-patterns (~300-500 lines)
- **Skills:** HOW to do specific tasks, with tool signatures and patterns (~500 lines each, loaded on demand)

**Recommended fix:** Extract all numbered processing sequences into skill files. Replace them in CLAUDE.md with 2-3 sentence objective statements. Example: "When you receive staged interactions, resolve all participants to network IDs, link entities, write clean interaction records, and mark staging rows processed. Load `skills/datum/staging-processing.md` for the resolution algorithm and SQL patterns."

### 2. Document Length

| Agent | Lines | Target | Over? |
|-------|-------|--------|-------|
| Orchestrator | 248 | <500 | No |
| ENIAC | 417 | <500 | No |
| Content | 633 | <500 | Yes (1.3x) |
| Datum | 956 | <500 | Yes (1.9x) |
| Megamind | 1137 | <500 | Yes (2.3x) |
| Cindy | 1172 | <500 | Yes (2.3x) |

Cindy and Megamind are more than double the recommended length. The excess is almost entirely scripted processing sequences and inline SQL that should be in skills.

### 3. ENIAC Is Disconnected

ENIAC has no bridge in the Orchestrator. It cannot receive work from the system. The Orchestrator's CLAUDE.md mentions 4 bridges (Content, Datum, Megamind, Cindy) but not ENIAC. This is a structural gap.

### 4. Agent Tool Usage

Only the Content Agent documents subagent usage (Agent tool). The benchmark says all main agents should have ALL tools allowed. The other agents should document when they might spawn subagents for complex tasks.

### 5. Cindy Boundary Violation

Cindy's Section 5 (People Linking Algorithm, lines 414-490) includes code to write to the `network` table and `people_interactions` table. This contradicts:
- The Cindy+Datum refactor (Section 3 header: "People resolution is Datum's job")
- The table ownership rules (Section 3: network writes = Datum Agent)
- The identity statement ("You do NOT do data plumbing")

Section 5 appears to be a legacy artifact from before the Cindy+Datum refactor. It should be removed or reduced to read-only patterns.

---

## Summary Scorecard

| Agent | Score | Key Strength | Key Weakness |
|-------|-------|-------------|-------------|
| Orchestrator | **7/10** | Lean, delegates everything, clean boundaries | No ENIAC bridge, no health monitoring |
| Megamind | **6/10** | Best identity + strategic sophistication | 11-step scripts, 1137 lines |
| Content | **6/10** | Only agent with Agent tool + class-of-work framework | Pipeline is a script |
| Datum | **5/10** | 14 SQL functions, confidence gating | Processing flows are scripts, 956 lines |
| Cindy | **5/10** | Best identity definition, 33 SQL functions | Boundary violation, 4 scripted pipelines, 1172 lines |
| ENIAC | **5/10** | Right length, 48 SQL functions, good skeleton | Missing anti-patterns, ACK, compaction; disconnected from Orchestrator |

**System Average: 5.7/10**

### Would This Impress the Agent SDK Team?

**Not yet.** The identity definitions would impress — they show deep understanding of autonomous agent design. The SQL function toolkits would impress — giving agents 14-48 autonomous database functions is exactly right. The convergence invariants and trust ramp in Megamind would impress.

But the scripted processing sequences would concern them. The Agent SDK exists so Claude can REASON about tool chaining, not follow hardcoded step-by-step instructions. An agent that follows "Step 1... Step 2... Step 3..." is using ~10% of the SDK's capability. The whole point of `setting_sources=["project"]` + `permission_mode="dontAsk"` is that the agent reads objectives and autonomously figures out the execution path.

### Priority Fixes (Ranked)

1. **ENIAC bridge in Orchestrator** — ENIAC is disconnected. Critical gap.
2. **Extract scripts to skills** — Move all numbered processing sequences from CLAUDE.md into skill files. Cut CLAUDE.md to <500 lines per agent.
3. **Remove Cindy Section 5** — Legacy boundary violation. People linking is Datum's job.
4. **Add missing ENIAC sections** — Anti-patterns, ACK protocol, compaction, skills loading strategy.
5. **Document Agent tool usage** — All agents should document when subagent delegation is appropriate.
6. **Standardize state file naming** — ENIAC uses `current_session.json`/`live.log` while others use `{agent}_last_log.txt`/`{agent}_iteration.txt`.
