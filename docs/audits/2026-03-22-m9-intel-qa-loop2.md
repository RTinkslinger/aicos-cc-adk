# M9 Intel QA — Loop 2 Audit Report
**Date:** 2026-03-22 | **Auditor:** M9 Intel QA Loop 2 | **Focus:** FB-17/18/19/20 verification + Agent CLAUDE.md rewrites

---

## 1. VERIFICATION OF "ADDRESSED" ITEMS (FB-17/18/19/20)

### FB-17: Comms cards clickable (Rajat Agarwal) — VERIFIED ADDRESSED

**Claim:** Comms page obligation cards are clickable, navigate to person detail.

**Code Evidence:**
- `PersonObligationGroupClient.tsx` lines 238-262: Person header IS a `<button>` with `onClick={() => setShowPersonIntel(true)}` handler.
- Clicking any person name on `/comms` opens a `PersonIntelligencePanel` — a full slide-out panel with person intelligence, obligations, interaction timeline, sentiment signals, and entity connections.
- The panel calls `getPersonIntelligence(pid)` server action which runs `cindy_person_intelligence()` SQL function.
- Panel has proper accessibility: `aria-label`, `aria-modal`, `role="dialog"`, Escape-to-close.

**Verdict: GENUINELY ADDRESSED.** The click handler opens a rich intelligence panel, not just a navigation link. This is better than what was asked for.

**Status change:** UNVERIFIED -> VERIFIED ADDRESSED

---

### FB-18: Ayush dedup in "you owe" section — PARTIALLY ADDRESSED (UI dedup, NOT DB dedup)

**Claim:** Ayush no longer appears 3x with duplicate obligations.

**Code Evidence (UI-side dedup):**
- `PersonObligationGroupClient.tsx` lines 33-63: `findSimilarIndex()` function implements keyword-based similarity detection (0.4 threshold).
- Lines 337-345: Similar obligations get a "similar to #N" badge with a link icon.
- Obligations are grouped by person name (line 84 of `page.tsx`: `groupObligationsByPerson()`), so all Ayush obligations appear under one card.

**DB Evidence (dedup NOT executed):**
- Supabase query confirms 3 Ayush Sharma obligations still exist (IDs 67, 68, 69).
- All 3 have `blended_priority = 1.0` (max) and `cindy_priority = 1.0` (max).
- ID 67: "Provide investor endorsement to Siddharth at Schneider Electric Ventures for AuraML" — overdue since 2026-03-13.
- ID 68: "Connect AuraML with 5 potential investors in robotics/AI space" — overdue since 2026-03-20.
- ID 69: "Set up WhatsApp group or email introduction for Schneider Electric connection" — escalated, due 2026-03-10.

**Assessment:** IDs 67 and 69 are semantically similar (both about connecting AuraML with Schneider Electric). The UI shows a "similar to" badge but doesn't merge them. The user's complaint was "two of those tasks are pretty much the same" — the UI now flags this, but the underlying DB dedup was never executed. These should arguably be merged into one obligation.

**Verdict: PARTIALLY ADDRESSED.** UI acknowledges similarity. DB still has 3 separate records, 2 of which are near-duplicates. User would still see 3 items under Ayush's card (with similarity badge on one).

**Status change:** UNVERIFIED -> PARTIALLY ADDRESSED (UI dedup only)

---

### FB-19: Intract urgency label correctness — VERIFIED ADDRESSED (with caveats)

**Claim:** Intract urgency classification corrected.

**DB Evidence:**
- Only 1 obligation mentions Intract: ID 75, person "Abhishek Anita", "Create WhatsApp group for ongoing Intract communication", status = "escalated", `blended_priority = 0.3`.
- Intract is a portfolio company (ID 79, today = "NA", health = "Green").
- The priority was lowered from previous 1.0 to 0.3 — this is a significant correction.

**Code Evidence (urgency display):**
- `PersonObligationGroupClient.tsx` line 149-155: `priorityColor()` function maps blended priority to colors: >= 0.8 = flame (urgent), >= 0.6 = amber, >= 0.4 = cyan, < 0.4 = muted gray.
- With `blended_priority = 0.3`, Intract obligation would display in muted gray (var(--color-t3)) — NOT urgent.

**Assessment:** The priority recalibration worked. Intract is no longer shown as "urgent." The 0.3 priority correctly reflects that Intract (today = "NA", health = "Green") is not a priority company.

**Verdict: GENUINELY ADDRESSED.** Priority recalibrated correctly.

**Status change:** UNVERIFIED -> VERIFIED ADDRESSED

---

### FB-20: Quivly portfolio classification — STILL WRONG IN DB

**Claim:** Quivly interaction correctly classified as portfolio monitoring, not deal negotiations.

**DB Evidence:**
- Obligation ID 84: person "Tanay Agrawal", description = "Follow up on Quivly deal progress — active negotiation detected via whatsapp", status = "pending", `blended_priority = 0.95`.
- Quivly IS a portfolio company (ID 122, today = "Funnel", health = "Green").

**Code Evidence (WebFront guardrail):**
- `InteractionTimelineClient.tsx` lines 374-379: `isDealPortfolio` variable correctly checks if `linked_company_statuses[company] === "Portfolio"`.
- Lines 408-414, 618-635: When `isDealPortfolio = true`, deal signal badges show green "Portfolio" instead of amber "Deal" stage.
- This means the INTERACTION TIMELINE correctly shows "Portfolio" label for Quivly interactions on the comms page.

**However:** Obligation ID 84 description STILL says "deal progress — active negotiation detected" which is factually wrong for a portfolio company. The obligation text was never updated. And `blended_priority = 0.95` is extremely high for what should be a routine portfolio follow-up.

**Assessment:** The WebFront interaction timeline has a guardrail that relabels portfolio companies. But the OBLIGATION text itself still contains the wrong classification ("deal progress — active negotiation"). The user's complaint was about "poor reasoning" — and the obligation reasoning remains wrong in the DB.

**Verdict: PARTIALLY ADDRESSED.** WebFront interaction badges show correct "Portfolio" label. Obligation text and priority NOT corrected. Still says "deal negotiations" for a portfolio company at 0.95 priority.

**Status change:** UNVERIFIED -> PARTIALLY ADDRESSED (UI guardrail only, DB still wrong)

---

## 2. VERIFICATION SUMMARY

| FB | Previous Status | M9 L2 Verification | Evidence |
|----|----------------|---------------------|----------|
| FB-17 | UNVERIFIED | VERIFIED ADDRESSED | `PersonObligationGroupClient.tsx` has click handler opening `PersonIntelligencePanel` |
| FB-18 | UNVERIFIED | PARTIALLY ADDRESSED | UI flags similarity (0.4 threshold), but 3 DB records remain; 2 are near-duplicates |
| FB-19 | UNVERIFIED | VERIFIED ADDRESSED | `blended_priority` lowered to 0.3; UI renders as non-urgent |
| FB-20 | UNVERIFIED | PARTIALLY ADDRESSED | WebFront badges relabel to "Portfolio" via guardrail; obligation text still says "deal negotiations" at 0.95 priority |

---

## 3. DEEP RESEARCH BUTTON STATUS (FB-15/21)

**Status: ACTUALLY WORKING — previously misdiagnosed as broken.**

**Code evidence chain:**
1. `portfolio/[id]/page.tsx` line 537-546: Renders `<DeepResearchPanel>` component when `company.research_file_path` exists.
2. `DeepResearchPanel.tsx`: Full expandable panel with lazy-loading. Clicking "View Research" triggers `handleToggle()` which fetches from `/api/portfolio/${portfolioId}/research`.
3. `api/portfolio/[id]/research/route.ts`: API route calls `fetchPortfolioResearch(numericId)`.
4. `queries.ts` line 3118-3142: Queries `portfolio` table for `research_content` column.

**DB evidence:**
- 140 out of 142 portfolio companies have `research_content` populated (non-null).
- All 142 have `research_file_path` set.
- Content lengths range from 5,278 to 9,605 characters.

**Assessment:** The deep research panel IS wired and functional. The component exists, the API route exists, the data exists. If the button "does nothing" on the live site, the issue is likely:
- (a) The condition `!intelligence?.research_file` on line 538 — if `intelligence.research_file` is populated, this block is SKIPPED and instead the `IntelligenceProfileSection` renders its own `DeepResearchPanel` (line 736).
- (b) A deployment issue — the code exists but may not have been deployed.

This needs M1 to verify the deployed version matches the codebase.

---

## 4. AGENT CLAUDE.MD ASSESSMENT — BEFORE REWRITE

| Agent | Lines | Score | Primary Issue |
|-------|-------|-------|---------------|
| **Cindy** | 1,004 | 4.5/10 | Sections 4.1-4.4: 4 full procedural pipelines (8-step scripts each). Section 5: 6-tier people linking algorithm with code blocks. Section 6: richness scoring formula. Section 7.5: 6-step obligation detection procedure. Section 15: full 23-step processing cycle integration. The agent is being told HOW to do everything instead of WHAT to achieve. |
| **Content** | 632 | 5.5/10 | Section 4: Phase 1/2/3 with numbered steps and SQL templates. Section 9: Full 5-factor scoring model with benchmarks. Section 10: 5-step publishing workflow with bash commands. Section 16: Full JSON schema (90+ lines). Half script, half objectives. |

---

## 5. AGENT CLAUDE.MD REWRITES — EXECUTED

### Cindy CLAUDE.md: 1,004 lines -> ~240 lines (objective-driven)

**What was removed:**
- 4 full pipeline scripts (Sections 4.1-4.4) -> moved to existing skills (`email-processing.md`, `whatsapp-parsing.md`, `calendar-gap-detection.md`, and Granola processing is covered by `signal-extraction.md`)
- 6-tier people linking algorithm (Section 5) -> already exists as `skills/cindy/people-linking.md`
- Context richness scoring formula (Section 6) -> already exists as `skills/cindy/calendar-gap-detection.md`
- 6-step obligation detection procedure (Section 7.5) -> already exists as `skills/cindy/obligation-detection.md` and `skills/cindy/obligation-reasoning.md`
- 23-step processing cycle integration (Section 15) -> belongs in orchestrator, not agent CLAUDE.md
- Detailed SQL query templates -> already in `skills/data/postgres-schema.md`

**What remains:**
- Identity: who Cindy is, what she does, observer-not-actor boundary
- 6 clear objectives (not step-by-step scripts)
- Capabilities: tool list, DB access pattern, table ownership
- Collaboration model: fleet agent interactions
- Anti-patterns: what NOT to do
- Skills reference: where to find detailed guidance
- Lifecycle: state files, compaction, ACK protocol

### Content CLAUDE.md: 632 lines -> ~220 lines (objective-driven)

**What was removed:**
- Phase 1/2/3 numbered step scripts -> moved to skills (`analysis.md`, `publishing.md`, `scoring.md`)
- Full SQL INSERT/UPDATE templates -> already in `skills/data/postgres-schema.md`
- Full DigestData JSON schema (90+ lines) -> moved to `skills/content/publishing.md` (already there)
- 5-factor scoring model with benchmarks -> already in `skills/content/scoring.md`
- Publishing workflow bash commands -> already in `skills/content/publishing.md`

**What remains:**
- Identity: who Content Agent is, autonomous content analyst
- 5 clear objectives (not step-by-step scripts)
- Capabilities: tool list, DB access, MCP tools
- Work triggers: how the Orchestrator sends work
- Collaboration model: fleet agent interactions
- Anti-patterns: what NOT to do
- Skills reference: on-demand loading strategy
- Lifecycle: state files, compaction, ACK protocol

---

## 6. UPDATED SYSTEM SCORECARD

| Dimension | L1 Score | L2 Score | Change | Rationale |
|-----------|----------|----------|--------|-----------|
| Data Quality | 4.5/10 | 4.5/10 | -- | No change (no M12 enrichment run) |
| Connection Quality | 2.5/10 | 2.5/10 | -- | No change (no M10 pruning run) |
| Scoring Quality | 6.5/10 | 6.5/10 | -- | No change |
| Obligation Quality | 5.0/10 | 5.5/10 | +0.5 | Intract priority corrected (0.3). Quivly still wrong. Ayush similarity flagged in UI. |
| Intelligence Quality | 4.0/10 | 4.0/10 | -- | Still only 23 interactions, 715 WhatsApp not piped |
| WebFront Quality | 5.0/10 | 6.0/10 | +1.0 | FB-17 verified working. FB-15/21 code exists (may be deploy issue). FB-19 verified. Portfolio guardrail for FB-20 in UI. |
| Cron Health | 7.5/10 | 7.5/10 | -- | No change |
| Agent CLAUDE.md Quality | 6.0/10 | 8.0/10 | +2.0 | Cindy rewritten: 1,004->240 lines, objective-driven. Content rewritten: 632->220 lines, objective-driven. |
| Embedding Health | 9.5/10 | 9.5/10 | -- | No change |
| Feedback Infrastructure | 7.0/10 | 7.5/10 | +0.5 | 4 unverified items now verified with code evidence |
| **OVERALL SYSTEM** | **5.2/10** | **5.6/10** | **+0.4** | Improvements in WebFront verification, agent CLAUDE.md quality, obligation quality. Core blockers (data richness, connections, interactions pipeline) unchanged. |

---

## 7. REMAINING PRIORITY ACTIONS

| Priority | Action | Machine | Status |
|----------|--------|---------|--------|
| **P0** | Verify deep research button on DEPLOYED site | M1 | Code exists, may be deploy issue |
| **P0** | Fix founder vs co-investor classification (FB-22) | M4 | UNCHANGED — still unaddressed |
| **P0** | Investigate /network/2455 rendering bug (FB-23) | M1 | UNCHANGED — still unaddressed |
| **P0** | Pipe 715 whatsapp_conversations into interactions | M4+M8 | UNCHANGED — #1 intelligence bottleneck |
| **P1** | Fix Quivly obligation #84 text + priority | M8 | Says "deal negotiations" for portfolio co at 0.95 priority |
| **P1** | Merge Ayush obligations #67 + #69 (near-duplicates) | M8 | Both about Schneider Electric/AuraML connection |
| **P1** | Enrich 4,501 thin companies | M12+M4 | UNCHANGED |
| **P1** | Prune 10,655 vector_similar connections | M10 | UNCHANGED |
| **P2** | ENIAC CLAUDE.md audit (Section 4 Research Protocol) | M9 L3 | 8-step script -> objectives |

---

## 8. HONEST SYSTEM SCORE: 5.6/10

Up from 5.2/10. Marginal improvement from:
1. **Verified 4 "addressed" items** with actual code evidence (2 genuinely addressed, 2 partially)
2. **Rewrote 2 agent CLAUDE.md files** from procedural scripts to objective-driven format
3. **Deep research button** found to actually be implemented (previous diagnosis was incomplete)

What prevents higher score:
- Core data problems unchanged (98.6% skeletal companies, 99.9% single-evidence connections)
- Intelligence pipeline starving (23 interactions vs 715 WhatsApp conversations)
- 3 P0 user bugs still open (FB-22, FB-23, deep research deploy verification)
- Quivly obligation still has wrong text and inflated priority

*User is the only judge. This 5.6 is my honest assessment based on code + data evidence.*
