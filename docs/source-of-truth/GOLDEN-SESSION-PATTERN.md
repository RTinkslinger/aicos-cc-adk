# Golden System Pattern v2 — MUST FOLLOW, DO NOT SKIP FROM CONTEXT AT ANY COST

**Sources:** Golden session 1 (2026-03-20, `0dff47d4`) + Golden pattern 2 (2026-03-21, last 60 min of `c494bed0`).
**This file is loaded by CLAUDE.md at the top. Non-negotiable. Read the ENTIRE file.**

---

## 1. THE ABSOLUTE FOUNDATIONS

### 1a. Agents Do ALL Thinking — SQL/Python = Plumbing ONLY

Claude Agent SDK agents (ENIAC, Datum, Cindy, Megamind) do ALL intelligence work — reasoning, scoring, risk assessment, strategic analysis, obligation prioritization, intelligence generation. They use Claude model power with full context, tools, skills, MCPs.

SQL functions = simple data access TOOLS that agents call (fetch, aggregate, join, store results). Python scripts = plumbing (lifecycle.py, deploy.sh, systemd, cron, data movement). WebFront renders AGENT OUTPUT stored in DB, not raw SQL function results.

**Test:** If you're about to write SQL that "scores", "assesses", "recommends", "detects", or "predicts" — STOP. That logic belongs in an agent. The existing SQL functions are ENABLERS — inputs that agents reason about.

**Agent architecture:** Agents are PERSISTENT Claude Agent SDK ClaudeSDKClient processes on the droplet. NOT ephemeral. NOT Python scripts with API calls. They REASON about how to achieve objectives, not follow step-by-step scripts.

### 1a-ii. HOW AGENTS ARE BUILT (HARDCODED — violated 100+ times)

**Agent CLAUDE.md = OBJECTIVES + IDENTITY + BOUNDARIES. NOT step-by-step instructions.**

```
CORRECT (objective-driven, agent reasons):
  "Your objective: detect obligations from unprocessed interactions, extract strategic
   signals, and surface intelligence to the fleet. You have 33 SQL tools and 4 skills.
   Reason about HOW to achieve your objectives each session."

WRONG (script-following, no reasoning):
  "Step 1: SELECT * FROM interactions WHERE cindy_processed = FALSE
   Step 2: For each row, extract obligations
   Step 3: INSERT INTO obligations table"
```

**The component architecture:**

| Component | What It Contains | How Agent Uses It |
|-----------|-----------------|-------------------|
| **CLAUDE.md** | Objectives, identity, boundaries, collaboration model, anti-patterns | Agent reads at start, understands WHO it is and WHAT to achieve |
| **Skills** | Rich reference: tool signatures, WHEN to use, patterns of success, anti-patterns | Agent loads on demand when tackling a specific objective |
| **Tools (SQL)** | Data access functions with signatures | Agent calls via psql when it REASONS it needs data |
| **Hooks** | Lifecycle, compaction, iteration logging | System-level behaviors, not agent-directed |

**Skills are REFERENCE MATERIAL, not scripts:**
- Known successful patterns = "patterns of success" (suggestive, not mandatory)
- Known failures = "anti-patterns" (what NOT to do)
- Tool signatures with WHEN to use each (agent decides IF and HOW to chain)
- The agent REASONS about tool chaining to achieve objectives. It is NOT following a script.

**Machine loops build ALL of these TOGETHER:**
- Build SQL tool → write skill teaching agent how to use it → update CLAUDE.md objectives → all in one loop
- Skills and tools grow together — never tools without skills, never skills without tools
- Agent CLAUDE.md evolves as capabilities grow (new objectives, refined boundaries)
- Hooks added for lifecycle quality gates
- NEVER write step-by-step processing instructions in CLAUDE.md
- NEVER build Python scripts that encode intelligence logic
- NEVER create ephemeral agents (subprocess API calls)

### 1b. Machine Loop ≠ Agent Doing Work

| Term | What It Is | Example |
|------|-----------|---------|
| **Machine loop** | CC session that BUILDS and IMPROVES an agent or infrastructure | M4 machine loop improves Datum agent's code, skills, tools |
| **Agent** | Claude Agent SDK persistent process on droplet, runs AUTONOMOUSLY | Datum agent runs 24/7, does data ops on its own |
| **Machine loop output** | Better agent code, skills, tools, WebFront, infrastructure | Datum now auto-detects embedding gaps |
| **Agent output** | Intelligence produced by the running agent | Datum auto-enriched 50 companies overnight |

**M4 builds Datum. Datum runs autonomously.** When a temp machine fixes something one-time, M4 incorporates that fix LOGIC into Datum's build so Datum handles it autonomously next time.

### 1c. Machines Are Perpetual Evolution Loops

Each machine loops forever with internal specialist steps. Not fix-it agents. EVOLUTION:
- ~70% new capabilities + ~30% quality/context inputs per loop
- The loop never ends. There is no "done." There is only "better."
- Adding a new machine = trivial. User says "add X" → spawn it. No ceremony.

### 1d. Machines Are Intertwined

Every machine's output is every other machine's input:
```
M12 enriches data → M6 search improves → M5 scoring better
  → M7 depth grades smarter → M1 ranking reshapes
    → User feedback → M5 preference learning → cycle forever
```

### 1e. User Is The ONLY Judge

Machine self-grades are meaningless. System reported 9.6/10 while user experienced 3/10. If user says 3/10, it's 3/10. Technical health ≠ product quality.

---

## 2. THE MACHINE LIST

### Permanent Machines (perpetual evolution)

| Machine | What It BUILDS/IMPROVES | What Runs AUTONOMOUSLY |
|---------|------------------------|----------------------|
| **M1 WebFront** | digest.wiki Next.js frontend | Deployed site on Vercel |
| **M4 Datum** | Datum agent (Agent SDK) — code, skills, tools | Datum on droplet — autonomous data ops |
| **M5 Scoring** | Scoring infrastructure (SQL tools for agents) | Scoring functions called by agents |
| **M6 IRGI** | Intelligence retrieval infrastructure | IRGI functions used by ENIAC agent |
| **M7 Megamind** | Megamind agent (Agent SDK) — CO-STRATEGIST across EVERYTHING | Megamind on droplet — autonomous strategy |
| **M8 Cindy** | Cindy agent (Agent SDK) — EA intelligence | Cindy on droplet — autonomous EA |
| **M9 Intel QA** | Quality auditing across all machines | Continuous quality gate |
| **M10 CIR** | Nervous system (triggers, propagation, health) | CIR in Postgres (triggers, crons, queues) |
| **M11 Obligations** | Obligation tracking infrastructure | Obligation system used by Cindy |
| **M12 Data Enrichment** | Data quality + enrichment → then Datum ongoing | Enriched data feeds all machines |
| **M-Backend** | Backend infra OUTSIDE Agent SDK (Python, deploy, systemd, cron) | Deployment pipeline, infra on droplet |

### Temp Machines (one-time outcome, dissolve when done)

Spawn for specific problems. When done, fix LOGIC goes into permanent machine's agent build.

### Agent Email Scope
- Cindy's email = `cindy.aacash@agentmail.to` via AgentMail API (on droplet)
- User forwards/CCs relevant emails to Cindy
- Gmail MCP is NOT for scanning user's mailbox. User's work email is Outlook.

---

## 3. THE PERPETUAL LOOP PATTERN (Golden Pattern 2)

### How Machines Run (current working pattern)

Machines are launched as **perpetual background agents**. They loop internally with their own specialist chain until context exhausts. Then the orchestrator relaunches them with updated cross-machine context.

```python
# Launch ALL permanent machines as perpetual loops — IN PARALLEL
Agent("M1-perpetual", prompt="You are M1... PERPETUAL LOOP... DO NOT ASK — EXECUTE")
Agent("M4-perpetual", prompt="You are M4... PERPETUAL LOOP...")
Agent("M5-perpetual", ...)
# ... all 9+ machines simultaneously

# As each completes (context exhaustion):
# 1. Check feedback store
# 2. Report new feedback to user inline
# 3. Relaunch with updated context
# 4. Machine keeps evolving
```

### Each Machine's Internal Loop (6 specialist steps)

```
EACH LOOP (all within ONE perpetual machine agent):

STEP 1: CHECK FEEDBACK (MANDATORY FIRST)
  → Run: SELECT * FROM get_machine_feedback('M{N}')
  → Address feedback, then mark_feedback_processed for each

STEP 2: PRODUCT LEADERSHIP
  → What problems exist? What should improve?
  → Suggest PROBLEMS and EXPLORATORY DIRECTIONS

STEP 3: RESEARCH + THINK
  → Study the data. What patterns? What's missing?
  → Study best-in-class products (Linear, Superhuman)

STEP 4: BUILD
  → Implement the improvement
  → For WebFront: deploy after every loop

STEP 5: REVIEW (within the loop)
  → Test. Check edge cases. Score quality honestly.

STEP 6: CROSS-MACHINE SYNC
  → What did this loop produce that other machines need?
  → Report for orchestrator to diffuse
  → START NEXT LOOP immediately
```

### Orchestrator Spawns Separate Review Agents At MILESTONES Only

The machine's internal review specialist handles routine checks. Orchestrator spawns SEPARATE review agents (QA, UX, Aakash perspective) at:
- WebFront milestones (every 2-3 loops)
- Major architectural changes
- User-triggered reviews

---

## 4. FEEDBACK SYSTEM (MANDATORY INFRASTRUCTURE)

### SQL Functions (already deployed to Supabase)

```sql
-- Get unprocessed feedback for a machine
SELECT * FROM get_machine_feedback('M1');

-- Mark as processed after addressing
SELECT mark_feedback_processed(11, 'M1');
```

### Every Machine Prompt MUST Include:

```
## FIRST — Check for user feedback (MANDATORY):
Run: SELECT * FROM get_machine_feedback('M{N}')
If results: address in your loop, then mark_feedback_processed for each.
```

### Orchestrator MUST Do At Every Machine Relaunch:

1. Query `get_machine_feedback('M{N}')` for the machine being relaunched
2. If new feedback: **REPORT TO USER IN CHAT** ("Your feedback on /comms was picked up by M8: [preview]")
3. Include feedback text in the machine's relaunch prompt
4. This is INFRASTRUCTURE, not discipline. Zero trust in orchestrator remembering.

### Feedback Widget (live on digest.wiki)

- Floating button bottom-left on every page
- Thumbs up/down, category (UX/Intelligence/Data/Bug), free text
- Auto-captures page path + machine sources (page→machine mapping)
- Stores to `user_feedback_store` via Server Action
- `context` JSONB includes `machine_sources` for routing

### Feedback Timeline (session-level)

Create `docs/feedback-timeline-YYYY-MM-DD.md` at session start. Append all user feedback with timestamps. At pause: analyze patterns, feed reasoned analysis to machines.

---

## 5. ORCHESTRATOR BEHAVIOR

The orchestrator (CC main thread) is the BRAIN:

### 5a. Context Diffusion
Route machine outputs to other machines. M12 enriched companies → tell M6. M7 found join bug → tell M5. User says "obligation cards should tell stories" → route to M8 + M1.

### 5b. User Feedback Routing
1. Capture to feedback timeline (timestamped)
2. Route to relevant machines via SendMessage (if running) or next launch prompt
3. Check `get_machine_feedback()` at every relaunch

### 5c. Temp Machine Spawning
One-time problem → spawn temp machine with "loop till outcome" mandate → dissolve when done → permanent machine incorporates the fix logic.

### 5d. Task Dashboard
Maintain live TaskCreate/TaskUpdate showing all machines and their state. User needs visibility above the chat.

### 5e. WebFront Deploys
M1 deploys after EVERY loop. User tests live on digest.wiki.

### 5f. Cindy + Datum Collaboration
- Cindy = EA intelligence + user interaction. Datum = data ops + enrichment + quality.
- Before creating DB entries: cross-reference ALL data sources (Granola, WhatsApp, web, LinkedIn, existing DB)
- If <90% confidence → Cindy asks user via WebFront gap-filling (smart contextual questions, not forms)
- If >=90% → Datum creates with ALL fields populated. No garbage entries.
- Better no entry than a garbage entry.

---

## 6. CRITICAL LEARNINGS

| # | Learning | Impact |
|---|---------|--------|
| 1 | Agents think, SQL/Python = plumbing | #1 recurring violation. 100+ times. |
| 2 | Machine loop BUILDS agents, doesn't DO their work | Most misunderstood concept |
| 3 | Machine self-grades are lies | System said 9.6/10, user said 3/10 |
| 4 | Datum runs EVERY session | Neglected = garbage data everywhere |
| 5 | Deploy WebFront every M1 loop | User is sole consumer, tests live |
| 6 | Feedback system = infrastructure, not discipline | Orchestrator WILL forget without SQL enforcement |
| 7 | Data richness is the bottleneck | 85+ columns exist, functions used 5. Now fixed (142/142 enriched) |
| 8 | Stories not data | "You offered to meet Mohit" not "Overdue 11 days" |
| 9 | Progressive disclosure L0→L1→L2 | Not every card needs full treatment |
| 10 | No garbage DB entries | Better no entry than first-name-only garbage |
| 11 | Gmail out of scope | Cindy reads her AgentMail inbox only |
| 12 | Backend = light plumbing | lifecycle.py, systemd, deploy.sh. No reasoning in code. |
| 13 | WhatsApp needs full ingestion | Per-chat markdown, hybrid searchable, not 8 summaries |
| 14 | Agents use reasoning + tools (MCP, Skills, Bash, web search) | Not Python pipelines |
| 15 | "Shall I proceed?" = violation | Machines EXECUTE. They don't ask. |

---

## 7. MACHINE PROMPT TEMPLATE

```
You are M{N} {NAME} MACHINE. PERPETUAL LOOP. DO NOT ASK — EXECUTE.

## Supabase: `llfkxnsfczludgigknbs` | `mcp__plugin_supabase_supabase__execute_sql`

## FIRST — Check for user feedback (MANDATORY):
Run: SELECT * FROM get_machine_feedback('M{N}')
If results: address in your loop, then mark_feedback_processed for each.

## Remember: You BUILD the {Name} agent. These functions are TOOLS for the agent's autonomous operation.

## Current state: {what was just done, key metrics}

## Cross-machine context: {what other machines recently built}

## User feedback to incorporate: {from feedback timeline}

## Keep looping — evolve:
- {specific evolution directions}
- {what would make the agent's autonomous life better}

KEEP LOOPING. Write to `docs/audits/YYYY-MM-DD-m{n}-perpetual.md` when done.
```

---

## 8. SESSION START CHECKLIST

```
1. Read CHECKPOINT.md → know each machine's state
2. Read THIS FILE (GOLDEN-SESSION-PATTERN.md) → the ENTIRE file
3. Read TRACES.md → current iteration/sprint
4. Create docs/feedback-timeline-YYYY-MM-DD.md
5. Create task dashboard (TaskCreate for each machine, set in_progress)
6. Launch ALL permanent machines as PERPETUAL loops — IN PARALLEL
   - Each prompt includes: feedback check, cross-machine context, product context
7. Include product context (CONTEXT.md, depth grading, conviction, user triage)
8. NEVER neglect Datum (M4)
9. Deploy M1 after every loop
10. Check get_machine_feedback() at EVERY machine relaunch
11. Report new feedback to user INLINE in chat
12. Capture user feedback to timeline with timestamps
```

---

## 9. WHAT "RESUME MACHINERIES" MEANS

When the user says "resume machineries" or "start machines" or "keep looping":

1. Read CHECKPOINT.md for machine states
2. Read this file for the pattern
3. Create feedback timeline
4. Create task dashboard
5. Launch ALL 9+ permanent machines as perpetual background agents — ALL IN PARALLEL
6. Each machine prompt includes: feedback check SQL, cross-machine context, "DO NOT ASK — EXECUTE"
7. As machines complete (context exhaustion): check feedback → report → relaunch
8. Route user feedback in real-time
9. Never stop until user says "pause" or "sync" or "stop"
