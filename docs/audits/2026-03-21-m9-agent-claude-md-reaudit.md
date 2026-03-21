# M9 Intel QA — Agent CLAUDE.md Re-Audit (Post-Refactor)

**Date:** 2026-03-21
**Machine:** M9 Intel QA (perpetual loop)
**Benchmark:** `docs/research/2026-03-21-persistent-agent-sdk-pattern.md`
**Prior audit:** `docs/audits/2026-03-21-m9-agent-review.md` (system avg 5.7/10)
**Supabase:** `llfkxnsfczludgigknbs`
**Feedback from `get_machine_feedback('M9'):** Empty (no stored feedback)

---

## Context: What Changed Since Prior Audit

The prior audit (same day, earlier session) scored the system 5.7/10 and identified 6 priority fixes. Since then, **two agents were substantially rewritten**:

| Agent | Prior Lines | Current Lines | Delta |
|-------|-------------|---------------|-------|
| Orchestrator | 248 | 247 | -1 (unchanged) |
| Datum | **956** | **232** | **-724 (76% reduction)** |
| Megamind | **1137** | **342** | **-795 (70% reduction)** |
| ENIAC | 417 | 468 | +51 |
| Content | 633 | 632 | -1 (unchanged) |
| Cindy | 1172 | 1004 | -168 (14% reduction) |

Datum and Megamind underwent radical surgery. This re-audit verifies whether the rewrites are objective-driven per the persistent agent SDK pattern.

---

## Benchmark Criteria (from `persistent-agent-sdk-pattern.md`)

1. **CLAUDE.md = Objectives, Not Scripts.** WHO the agent is, WHAT to achieve, boundaries, anti-patterns.
2. **Skills = Rich Reference.** Progressive disclosure, loaded on demand.
3. **All tools allowed.** `permission_mode="dontAsk"`.
4. **Document length:** Target <500 lines. Anything over is a signal that scripts are embedded.
5. **Agent reasons about tool chaining** — not following hardcoded step sequences.

---

## Agent-by-Agent Re-Audit

### 1. Datum Agent — 232 lines (was 956)

**Transformation:** This is the single biggest improvement in the system. The old Datum was 184 lines of step-by-step processing instructions plus a 6-step "Processing Flow" script. All of that is gone.

**What's left (and it's right):**
- Identity (lines 1-16): Clean, autonomous, "NOT a script executor" framing
- Objectives (lines 19-39): Six standing goals stated as outcomes, not procedures
- Capabilities (lines 42-65): Tools + 14 SQL functions listed, not scripted
- Database Boundaries (lines 68-75): Clean read/write matrix
- Skills Reference (lines 78-93): 8 skills with "when to load" guidance + explicit "skills are suggestive, not prescriptive"
- Confidence Gating (lines 97-105): Objective-driven decision framework
- Input Types (lines 109-123): Prompt type -> skill mapping table (suggestive, not scripted)
- Column Name Warnings (lines 127-136): Critical gotchas in a concise table
- Anti-patterns (lines 203-220): 16 items, #16 explicitly says "Never follow processing scripts blindly. Reason about each situation."
- ACK Protocol, Escalation Rules, State Tracking, Collaboration Model: All present, concise

**Violations:**
- None. This CLAUDE.md is now textbook objective-driven.

**What's excellent:**
- Anti-pattern #16 ("Never follow processing scripts blindly") is a meta-instruction that reinforces the SDK pattern
- The "Skills are suggestive, not prescriptive" call-out is exactly right
- Input Types table maps prompt types to skills without prescribing steps — the agent loads the skill and reasons
- 232 lines is well under the <500 target

**Minor gaps:**
- Agent tool listed in capabilities table but no subagent usage guidance (when to spawn, what subagents exist)
- No ENIAC collaboration detail — just "may request entity enrichment"

**Score: 9/10** (was 5/10 — +4 points)

The biggest score jump in the system. From worst to near-best. An Anthropic engineer reviewing this would see a clean, objective-driven agent definition that trusts Claude to reason.

---

### 2. Megamind Agent — 342 lines (was 1137)

**Transformation:** The old Megamind had three work types (Depth Grading, Cascade, Assessment) presented as 11-step, 10-step, and 10-step scripts totaling ~190 lines of prescriptive instructions. All removed.

**What's left:**
- Identity (lines 1-19): Still exceptional — "convergence enforcer," "co-strategist not servant," clear NOT statements
- Objectives (lines 22-66): Four strategic objectives stated as outcomes with bullet points of what to do, not how
- Priority Buckets (lines 69-79): Strategic framing table
- Tools & Capabilities (lines 82-130): Full toolset including Agent tool, clean DB boundaries, column gotchas
- Skills Reference (lines 133-155): 7 skills with path + "when to load" + a skill loading matrix by work type
- SQL Functions Inventory (lines 158-240): 45 functions organized by category — massive autonomous toolkit
- Convergence Rules (lines 243-252): Hard constraints as invariants, not scripts
- Trust Ramp (lines 256-264): Progressive autonomy model
- Collaboration Model (lines 268-287): Clean read/write matrix
- State Tracking (lines 290-303): Standard lifecycle
- ACK Protocol (lines 307-320): With convergence PASS/WARN/FAIL
- Boundaries (lines 323-342): 18 NEVER items

**Violations:**
- None. The scripted processing sequences are gone. The objectives section says "Grade agent-delegated actions for depth" not "Step 1: Query ungraded actions. Step 2: Load thesis context. Step 3..."

**What's excellent:**
- The skill loading matrix (lines 148-155) is a model for all agents — maps work type to required skills
- 45 SQL functions give the agent enormous autonomous capability without prescribing when to call them
- Convergence rules are stated as invariants (mathematical constraints), not process steps
- The "co-strategist" identity is distinctive and powerful — no other agent has this framing

**Minor gaps:**
- No subagent usage guidance despite having Agent tool listed
- The SQL Functions Inventory section (lines 158-240) is 82 lines of function tables. Borderline — could be a skill for progressive disclosure, but since these are the agent's primary tools and it's a reference table (not instructions), it's acceptable.

**Score: 9/10** (was 6/10 — +3 points)

Megamind's strategic sophistication was always high. Now the document matches — identity and objectives without scripted execution paths.

---

### 3. ENIAC Agent — 468 lines (was 417)

**Change:** Grew by 51 lines. The prior audit flagged missing anti-patterns, ACK protocol, compaction, and skills loading guidance.

**Current state:**
- Identity (lines 1-47): Good — clear NOT statements, well-differentiated from other agents
- Capabilities (lines 50-75): Tools + Web Tools MCP
- Database Access (lines 78-220): 48 SQL functions in clean tables, table ownership rules, NEVER-touch rules with exceptions
- Research Protocol (lines 225-310): **Still an 8-step numbered script** ("1. ORIENT, 2a. QUEUE, 2b. BRIEF, 3. SEARCH, 4. RESEARCH, 5. SYNTHESIZE, 6. PERSIST, 7. CROSS-REF, 8. ALERT")
- Periodic Health Checks (lines 281-310): 5 prescriptive psql commands with "run these at least once per session"
- Conviction Guardrail (lines 314-335): Good CAN/CANNOT list
- Research Quality Standards (lines 338-357): Good quality bars
- Subagent Strategy (lines 398-444): **Excellent** — 3 subagent types, parallelization patterns, 6 mandatory rules, prompt template
- Session State (lines 448-468): Different naming convention (`current_session.json`, `live.log`)

**Violations:**
- **Section 4 (lines 225-310):** Research Protocol is still a numbered script. The benchmark says state the objective ("Research, synthesize, and persist findings using your queue, search, and web tools") and let the agent reason about execution order.
- **Health Checks (lines 281-310):** Prescriptive SQL commands with "run at least once per session." Should be objective: "Monitor thesis health, bias, portfolio risk, and emerging signals. Use your health dashboard functions."

**What's still missing from prior audit:**
- Anti-patterns section: Still missing
- ACK protocol: Still missing
- Compaction protocol: Still missing
- State file naming: Still inconsistent (`current_session.json`/`live.log` vs fleet standard `{agent}_last_log.txt`/`{agent}_iteration.txt`)

**What improved:**
- Subagent strategy section (lines 398-444) is new and excellent — best subagent documentation of any agent
- 48 SQL functions with clear table ownership

**Score: 5.5/10** (was 5/10 — +0.5 points)

ENIAC got the subagent section right but still has the scripted research protocol and is missing lifecycle sections that every other agent has. The prior audit's 4 missing-section flags were not addressed. This is the only agent that did NOT receive the "objectives not scripts" refactor.

---

### 4. Content Agent — 632 lines (unchanged)

**No rewrite occurred.** Same assessment as prior audit.

**Violations persist:**
- Section 4 (lines 96-157): Content Pipeline Trigger is a 3-phase multi-step script
- Section 8 (lines 246-294): Analysis Sequence is a 10-step script

**Strengths persist:**
- Three classes of work (Direct, Complex Delegation, Parallel Batch) — best class-of-work framework
- DigestData JSON schema is clear
- Skills loading, ACK, anti-patterns all present

**Score: 6/10** (unchanged)

Content Agent is functional and has good structural elements, but needs the same "objectives not scripts" refactor that Datum and Megamind received.

---

### 5. Cindy Agent — 1004 lines (was 1172)

**Partial reduction** (-168 lines, 14%). Not the radical surgery that Datum and Megamind got.

**Violations persist:**
- **Section 4 (lines 143-400+):** Four surface-specific pipelines (Email 8 steps, WhatsApp 8 steps, Granola 8 steps, Calendar 6 steps) are still full numbered scripts
- **Section 5 (lines 284-357):** People Linking Algorithm is still a 6-tier numbered script with UPDATE network SQL — **boundary violation still present** (Datum owns network writes per the refactor)
- **Section 7.5 (lines 443-498):** Obligation Detection is a 6-step numbered script
- **Section 15 (lines 884-923):** "Processing Cycle Integration" still scripts the SQL function call sequence in a numbered procedure

**What's good (and still good):**
- Identity is the best of any agent — "observer not actor" is a powerful framing
- 33 SQL intelligence functions
- Skills Reference with loading strategy (Section 17, lines 973-1004)
- Fleet collaboration model (Section 16) is clean and well-bounded
- Privacy constraints are well-specified
- Signal routing criteria table (Section 7) is objective-driven

**What's still wrong:**
- **Boundary violation in Section 5:** Cindy's CLAUDE.md still has SQL UPDATE network queries, despite the header saying "You do NOT do data plumbing." Section 5 should reference Datum's people-linking skill or be reduced to read-only lookup patterns.
- At 1004 lines, still 2x the target. The four surface pipelines alone are ~260 lines of scripts that should be in skills.
- No mention of Agent tool for subagent delegation

**Score: 5/10** (unchanged)

Cindy has the best identity definition but the worst script-to-objective ratio. The 168-line reduction came from minor trims, not structural refactoring. The boundary violation in Section 5 remains.

---

### 6. Orchestrator Agent — 247 lines (unchanged)

**No changes.** Same assessment as prior audit.

**Strengths persist:**
- Leanest agent, delegates everything, clean boundaries
- Single-table write scope
- Heartbeat delegation to HEARTBEAT.md

**Gaps persist:**
- **No ENIAC bridge.** The Orchestrator has `send_to_content_agent`, `send_to_datum_agent`, `send_to_megamind_agent`, `send_to_cindy_agent` — but no `send_to_eniac_agent`. ENIAC is disconnected from the system.
- No health monitoring of agents

**Score: 7/10** (unchanged)

---

## Summary Scorecard (Re-Audit)

| Agent | Prior Score | Current Score | Delta | Key Change |
|-------|------------|---------------|-------|------------|
| **Datum** | 5/10 | **9/10** | **+4** | Radical refactor: 956->232 lines, scripts->objectives |
| **Megamind** | 6/10 | **9/10** | **+3** | Radical refactor: 1137->342 lines, scripts->objectives |
| **Orchestrator** | 7/10 | 7/10 | 0 | Unchanged. ENIAC bridge still missing. |
| **Content** | 6/10 | 6/10 | 0 | Unchanged. Pipeline still scripted. |
| **ENIAC** | 5/10 | 5.5/10 | +0.5 | New subagent section. But still scripted + missing lifecycle sections. |
| **Cindy** | 5/10 | 5/10 | 0 | Minor trim (-168 lines). Scripts + boundary violation remain. |

**System Average: 6.9/10** (was 5.7/10 — +1.2 points)

---

## Live Data Cross-Check (Supabase `llfkxnsfczludgigknbs`)

### Scoring Health (current snapshot)

| Metric | Value | Assessment |
|--------|-------|------------|
| Proposed actions | 30 | Healthy count |
| Avg score (proposed) | 7.13 | Compressed high |
| Stddev (proposed) | 0.48 | **CRITICAL: Near-zero spread** |
| Score range (proposed) | 6.4 - 7.8 | **Only 1.4 points of range** |
| Total actions | 145 | |
| Scoring model | v5.1-L96 | |
| Health score | 10/10 | Dashboard says healthy but... |
| Compression | PASS (dashboard) | **Disagree: 0.48 stddev is compressed** |

The scoring model reports health 10/10 and PASS on compression, but 30 Proposed actions spanning only 6.4-7.8 (stddev 0.48) is objectively compressed. The score_health_dashboard's compression check appears to evaluate all actions (145), where the bimodal distribution (dismissed low, proposed high) masks the within-status compression. The Proposed-only subset has almost no discriminating power.

### Thesis Bias (current snapshot)

| Thesis | Conviction | For:Against Ratio | Severity |
|--------|-----------|-------------------|----------|
| Cybersecurity / Pen Testing | Medium | **11.3:1** | HIGH |
| Agentic AI Infrastructure | Very High | **9.8:1** | MEDIUM |
| Agent-Friendly Codebase | Medium | 7.4:1 | OK |
| CLAW Stack | Medium | 5.1:1 | OK |
| Healthcare AI Agents | New | 4.9:1 | LOW (conviction mismatch flagged) |
| USTOL / Aviation | Low | 3.8:1 | OK |
| SaaS Death / Agentic Replacement | High | **2.1:1** | OK (best balanced) |
| AI-Native Non-Consumption Markets | New | **NO CONTRA** | HIGH (confirmation_bias=true) |

Two threads with HIGH bias alerts (AI-Native Non-Consumption Markets at zero contra, Cybersecurity at 11.3:1). SaaS Death / Agentic Replacement is the best-balanced at 2.1:1 — the only thesis where the system is genuinely challenging itself.

---

## Priority Fixes (Ranked)

### 1. Refactor Cindy (HIGH — system bottleneck)
Cindy is now the only agent above 500 lines (1004) and the most script-heavy. Apply the same surgery Datum and Megamind received:
- Extract the 4 surface pipelines (Email, WhatsApp, Granola, Calendar) into skills
- **Remove Section 5 (People Linking Algorithm)** — boundary violation. Reference `skills/datum/people-linking.md` for read-only lookups.
- Extract the "Processing Cycle Integration" numbered procedure into a skill
- Target: ~350 lines (identity + objectives + boundaries + skills reference)

### 2. Refactor Content Agent (HIGH — still scripted)
Content Agent is the second-most scripted. Apply the same pattern:
- Extract the 3-phase Content Pipeline into `skills/content/pipeline.md`
- Extract the 10-step Analysis Sequence into the existing `skills/content/analysis.md`
- Replace with 2-3 sentence objective statements
- Target: ~400 lines

### 3. Refactor ENIAC (MEDIUM — missing lifecycle + scripted)
- Extract the 8-step Research Protocol into `skills/eniac/eniac-research.md` (skill already exists, add the protocol)
- Add anti-patterns section (every other agent has one)
- Add ACK protocol (every other agent has one)
- Add compaction protocol (every other agent has one)
- Standardize state file naming to `eniac_last_log.txt`/`eniac_iteration.txt`
- Target: ~350 lines

### 4. Add ENIAC Bridge to Orchestrator (MEDIUM — structural gap)
ENIAC is the only fleet agent with no Orchestrator bridge. Either:
- Add `send_to_eniac_agent` bridge tool
- Or document how ENIAC receives work (if via a different mechanism)
Without this, ENIAC cannot receive work from the system.

### 5. Scoring Compression Fix (MEDIUM — data quality)
Proposed actions have stddev 0.48 across a 1.4-point range (6.4-7.8). The scoring model needs spread. The health dashboard reports PASS on compression but evaluates all statuses — it should also check within-status compression for Proposed actions.

### 6. Thesis Bias Intervention (LOW — improving)
AI-Native Non-Consumption Markets still has zero contra evidence. Megamind has already intervened (added contra-evidence requirement before conviction can advance). Monitor but no code change needed — the system is self-correcting via M7 interventions.

---

## Would This System Now Impress the Agent SDK Team?

**Datum and Megamind: Yes.** These are exemplary. An Anthropic engineer would see clean objective-driven definitions with rich autonomous toolkits (14 and 45 SQL functions respectively), progressive disclosure to skills, and clear boundaries. Datum's "Skills are suggestive, not prescriptive" and anti-pattern #16 ("Never follow processing scripts blindly") show deep understanding of the pattern.

**Orchestrator: Mostly yes.** Lean coordinator with clean delegation. The ENIAC bridge gap is a deployment issue, not a design issue.

**Cindy, Content, ENIAC: Not yet.** These still have the scripted processing sequences that treat the LLM as a script runner. The scripts especially hurt in Cindy's case because the agent has 33 SQL intelligence functions that should make reasoning autonomous — but the Processing Cycle Integration section then tells it exactly when to call each one.

**The system is half-refactored.** Datum and Megamind show what "right" looks like. Apply the same pattern to the remaining three agents and the system average will reach 8+/10.

---

## M9 Self-Assessment

| Dimension | Score | Notes |
|-----------|-------|-------|
| Actions quality | 6.5/10 | Scores work but are compressed (stddev 0.48). Narrative explanations are rich. |
| Thesis quality | 7.0/10 | 2 bias flags remain. SaaS Death well-balanced. System self-correcting via M7. |
| Search quality | 7.0/10 | 7 surfaces searchable. FTS + trigram. No semantic/embedding search yet. |
| Agent CLAUDE.md quality | 6.9/10 | Two agents at 9/10, three still need refactoring. |
| **Overall M9 Score** | **6.9/10** | Up from 6.0 at L55. Datum/Megamind rewrites are the primary driver. |

**Next loop target:** 7.5/10. Requires Cindy + Content refactors and scoring compression fix.
