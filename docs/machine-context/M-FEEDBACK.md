# M-FEEDBACK — Feedback Routing Machine Context
*Last updated: 2026-03-22. NEW MACHINE. 0 loops completed. Infrastructure built, awaiting first run.*

---

## Product Vision Context

M-FEEDBACK is the **product organization** of the AI CoS. When a user submits feedback from the WebFront or interacts with agents (implicit feedback), the feedback touches the FINAL EXPERIENCE -- it simultaneously involves UI, intelligence, data quality, scoring, and agent reasoning. A single piece of feedback like "this person's info is wrong" decomposes into: data quality issue (M4), intelligence gap (M8), rendering problem (M1), and possibly a scoring miscalibration (M5).

**Why a dedicated machine:** The CC orchestrator lacks the depth to properly decompose user feedback into component-specific tasks. M-FEEDBACK runs product org specialist agents that analyze feedback the way a product team at a best-in-class company would -- identifying root causes across multiple layers and routing actionable tasks to the right machines.

**What the user cares about:** Every piece of feedback Aakash gives -- whether through the WebFront widget, through agent interactions, or through CC chat -- gets properly analyzed, decomposed, and routed to the right machine for resolution. Nothing falls through cracks. Nothing gets marked "addressed" without real verification. The system LEARNS from his feedback.

---

## Accumulated Decisions

### Pre-Loop — Architecture Design

**Two feedback types identified:**
1. **Explicit feedback** (WebFront widget): User clicks feedback button on a specific page/card. Stored in `user_feedback_store` table. Contains: page, section, item_id, item_type, rating (1-5), text. Currently 37 items.
2. **Implicit feedback** (agent interactions): User dismisses an obligation, accepts an action, overrides a suggestion, selects a company from a picker. Stored in `cindy_conversation_log` table (and equivalents for other agents). This is the RL signal -- what the user actually DOES versus what the system suggested.

**Product org specialist agents defined:**
| Specialist | Role in Feedback Analysis |
|------------|--------------------------|
| **Product Manager** | Prioritize feedback by user impact. Categorize: bug, data quality, intelligence gap, UX issue, product vision. Map to machine backlog. |
| **UX Researcher** | Identify interaction patterns across feedback. "Dumb dump" (FB-29, FB-35, FB-36) = recurring theme of data-without-intelligence. Surface systemic UX issues. |
| **Data Analyst** | Trace data quality issues. When user says "this is wrong," determine: is the source data wrong (M4/M12), is the rendering wrong (M1), is the reasoning wrong (agent machines), or is the scoring wrong (M5)? |
| **Engineering Lead** | Identify technical root causes. Scroll-lock bugs (FB-37), null guard crashes (FB-23), dismiss flow broken (FB-32) -- these are engineering problems with clear fixes. Route with specificity. |

**Feedback decomposition flow:**
```
user_feedback_store / cindy_conversation_log
  --> M-FEEDBACK reads new unprocessed items
  --> Product Manager: categorize + prioritize
  --> UX Researcher: identify patterns across items
  --> Data Analyst: trace root causes
  --> Engineering Lead: identify technical fixes
  --> Decompose into component-specific tasks
  --> Route to machine backlogs (machine_backlog table or direct context injection)
```

**Infrastructure built:**
- `user_feedback_store` table: 37 items, with page/section/rating/text/processed_by fields
- `get_machine_feedback(machine_name)` SQL function: returns pending feedback for a specific machine
- `mark_feedback_processed(feedback_id, machine_name)` SQL function: marks feedback as processed
- `cindy_conversation_log` table: 5-mode function (log, history_person, history_obligation, recent, patterns)
- Hooks spec written (`docs/superpowers/specs/2026-03-22-hooks-for-machines.md`) with 7 hooks, 3 directly supporting M-FEEDBACK:
  - Hook #1: Pre-Agent — inject M-FEEDBACK decomposed tasks into machine agents as additionalContext
  - Hook #4: SessionStart — run M-FEEDBACK first on "resume machineries" to ensure fresh feedback
  - Hook #5: UserPromptSubmit — detect CC chat feedback and auto-log + route

---

## Patterns of Success

*(Projected from feedback tracker analysis and product patterns -- to be validated in first loops)*

1. **Categorize before routing.** Every feedback item needs a category (bug, data quality, intelligence gap, UX issue, product vision) before routing. FB-22 "founders wrong" looks like a bug but is actually a data quality issue with the `led_by_ids` vs `current_people_ids` distinction.
2. **Trace the full stack.** "This person's info is wrong" can be: wrong in Notion (source), wrong in Supabase (sync), wrong in rendering (WebFront), or wrong in reasoning (agent). M-FEEDBACK must trace through all layers.
3. **Identify feedback themes, not just individual items.** FB-29, FB-35, FB-36 all say the same thing: "dumb dump" -- data without intelligence. The theme is more valuable than the individual items because it points to a systemic issue (all detail views lack "what to do" suggestions).
4. **Explicit feedback > implicit feedback for prioritization.** The user took time to write feedback in the widget. That's higher signal than a dismiss click. But implicit feedback at scale (100+ dismissals of a certain pattern) becomes very high signal.
5. **Route with context, not just task IDs.** When routing FB-22 to M4, include: what the user said, what the root cause is, what the fix approach should be, and what other feedback items are related. Machines without context produce half-fixes.

---

## Anti-Patterns (Learned)

1. **Do NOT mark feedback "addressed" without verified evidence.** M9 L1 found that FB-17/18/19/20 were all "marked as addressed" without code change evidence. "Addressed" requires: code change committed, deployed to live, and user-verifiable.
2. **Do NOT route feedback without decomposition.** A single feedback item often touches 2-3 machines. FB-26 ("similar companies off") required M1 (rendering), M4 (backend function), and M12 (data enrichment). Routing to just one machine produces incomplete fixes.
3. **Do NOT trust machine self-grades on feedback resolution.** The system reported 8.3/10 while the user experienced 3/10 (previous session). Machine self-assessment of "addressed" is unreliable. M9 QA must independently verify.
4. **Do NOT batch feedback processing at session end.** Feedback should be processed at session START (before machines launch) so every machine starts with awareness of its pending feedback items. Hook #4 enforces this.
5. **Do NOT conflate explicit and implicit feedback.** Explicit: user says "this is wrong." Implicit: user dismisses an action. They inform differently -- explicit tells you about quality, implicit tells you about relevance/preference. Separate analysis paths.

---

## Cross-Machine Context

### What M-FEEDBACK Produces (consumed by others)
| Consumer | What | Current State |
|----------|------|---------------|
| **All Machines** | Decomposed, categorized feedback tasks with root cause analysis and routing context | Not yet producing -- 0 loops run. 37 items pending in user_feedback_store. |
| **M9 QA** | Feedback verification queue | M9 should verify that machines actually addressed routed feedback. M-FEEDBACK flags unverified "addressed" claims. |
| **CC Orchestrator** | Feedback processing status | Orchestrator can check M-FEEDBACK's output to know which machines have pending feedback work. |

### What M-FEEDBACK Consumes (from others)
| Producer | What | Impact |
|----------|------|--------|
| **WebFront feedback widget** | Explicit user feedback | `user_feedback_store` table. 37 items. Page-level, section-level, and card-level feedback with optional rating and text. |
| **Agent conversation logs** | Implicit user feedback | `cindy_conversation_log` + equivalents. Every dismiss, accept, override, selection is an implicit signal about system quality. |
| **CC chat** | Direct user feedback in conversation | Hook #5 will detect feedback-like language and auto-log. Currently not captured. |
| **M9 QA** | Verification results | M9 audits whether "addressed" items are actually fixed. M-FEEDBACK uses this to flag regressions and reopen items. |

---

## Current Focus

**First loop: Process all 37 existing feedback items.**

**Feedback items by status (from FEEDBACK-TRACKER-LIVE.md):**
- 25 verified addressed -- analyze WHAT was done, extract patterns for machine learning
- 3 unaddressed P1 -- FB-33 (contextual options, backend done needs UI), FB-34 (text input, transformative), FB-36 (interaction summarization, partial)
- 2 system-level unaddressed -- FB-3 (3,800+ thin companies), FB-4 (connection evidence quality)
- 2 partially addressed -- FB-29 (interaction quality), FB-24 (person data thin)
- 2 enhancement requests -- FB-27 (AddSignal evolution), FB-34 (also enhancement)
- 3 unaddressed P2 -- FB-2 (intelligence quality), FB-29 (network interaction content), ENIAC CLAUDE.md

**First loop plan:**
1. **Product Manager agent:** Read all 37 items. Categorize each. Identify which of the 25 "addressed" items produced patterns useful for other machines.
2. **UX Researcher agent:** Identify the 4-5 systemic themes (current known: "dumb dump" theme, identity resolution theme, conversational UX vision, AddSignal positive signal, data quality crisis).
3. **Data Analyst agent:** For the 12 unaddressed/partial items, trace root cause through the stack. Determine: which layer is the bottleneck? Data → M4/M12. Rendering → M1. Reasoning → M7/M8/ENIAC. Scoring → M5.
4. **Engineering Lead agent:** For bug-type items, identify specific code changes needed. For infrastructure items, identify which hooks from the hooks spec should be built first.
5. **Output:** Decomposed task list routed to machines. Each task has: source feedback item(s), category, root cause analysis, suggested approach, priority, target machine.

**Post-first-loop:**
- Begin processing implicit feedback from `cindy_conversation_log`
- Build the feedback → machine routing hooks (#1 and #4 from hooks spec)
- Establish continuous processing cadence: run at session start + every N loops
