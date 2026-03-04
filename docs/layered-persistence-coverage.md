# Layered Persistence Coverage Map
# Last audited: Session 037 (March 4, 2026)
# Next audit due: Session 038
# Triage principle: instruction violated 2+ times across sessions → upgrade to 3+ layers

## Layer Reference

| Layer | File | Fires When | Persistence |
|-------|------|-----------|-------------|
| 0a | Global Instructions | Every Cowork session (before skills) | Operational directives |
| 0b | User Preferences | Every Cowork session | Identity baseline |
| 1 | Claude.ai Memory (16 entries) | Every Claude.ai conversation | Ambient awareness |
| 2 | ai-cos Skill v6.2.0 | Triggered by investing/action keywords | Deep activation |
| 3 | CLAUDE.md | Every Claude Code / Cowork session with project | Code context |
| — | CONTEXT.md | Loaded by skill Step 1 | Living brain |

## Detailed Coverage

### CRITICAL (must be at 3+ layers)

| # | Instruction Set | 0a | 0b | L1 | L2 | L3 | CTX | Coverage | Violation History |
|---|----------------|----|----|----|----|----|----|----------|-------------------|
| 1 | Session close checklist (8-step + subagent delegation) | ✅ | — | ✅ #15 | ✅ | ✅ | ✅ | 5/6 | Sessions 012-016, 018-023 (missing logs/updates). Session 035: context compaction death spiral → subagent delegation pattern now mandatory |
| 2 | Notion skill auto-load | ✅ | — | ✅ #14 | ✅ | ✅ | ✅ | 5/6 | Sessions 5, 6, 17, 18, 24, 32 (broken Notion calls) |
| 3 | Action optimizer framing | — | ✅ | ✅ #2 | ✅ | ✅ | ✅ | 5/6 | Sessions 1-3 (narrowed to meetings) |
| 4 | Feedback loop (end-of-task) | ✅ | ✅ | ✅ #8 | ✅ | — | ✅ | 5/6 | Rarely violated — well layered |
| 5 | Cowork sandbox rules | — | — | ✅ #16 | ✅ | ✅ | — | 3/6 | Sessions 7, 9, 21, 27 (curl/wget from sandbox) |
| 6 | Deploy architecture | — | — | ✅ #16 | ✅ | ✅ | — | 3/6 | Sessions 21, 27, 28 (wrong deploy method) |
| 7 | Notion property formatting | — | — | ✅ #16 | ✅ | ✅ | — | 3/6 | Sessions 2-6, 17-18, 27 (wrong date/checkbox/relation format) |
| 8 | Session Behavioral Audit (JSONL analysis at close + on-demand) | — | — | — | ✅ | ✅ | — | 2/6 | New in Session 036. Subagent reads JSONL vs reference files, reports expected vs actual behavior. Template: `scripts/session-behavioral-audit-prompt.md` |
| 23 | Subagent handling (tool limits, templates, hand-off, spawning checklist) | ✅ | ✅ | ✅ #18 | ✅ | ✅ | — | 5/6 | Sessions 034-037: root cause of repeated sandbox/Notion/deletion violations. Subagents don't inherit CLAUDE.md/skills/MCP tools — must receive all rules via prompt. Template library: `scripts/subagent-prompts/`. Spawning checklist in CLAUDE.md §F + ai-cos skill. |

### IMPORTANT (target 2+ layers)

| # | Instruction Set | 0a | 0b | L1 | L2 | L3 | CTX | Coverage | Violation History |
|---|----------------|----|----|----|----|----|----|----------|-------------------|
| 9 | Skill packaging rules | — | — | ✅ #16 | ✅ | ✅ | — | 3/6 | Session 031 (plain text instead of ZIP) |
| 10 | Notion bulk-read (view://UUID) | — | — | — | ✅ | ✅ | — | 2/6 | Sessions 2-31 (systemic — wrong methods) |
| 11 | IDS methodology | — | — | ✅ #4 | ✅ | — | ✅ | 3/6 | No violations |
| 12 | Four priority buckets | — | — | ✅ #3 | ✅ | — | ✅ | 3/6 | No violations |
| 13 | Action Scoring Model | — | — | ✅ #13 | ✅ | ✅ | ✅ | 4/6 | No violations |
| 14 | Thesis sync protocol | — | — | ✅ #9 | ✅ | — | ✅ | 3/6 | Session 023 (skipped) |
| 15 | Schema integrity (match types exactly) | — | — | — | — | ✅ | — | 1/6 | Sessions 17, 21, 27 (field name mismatches) |

### STANDARD (1+ layer sufficient)

| # | Instruction Set | 0a | 0b | L1 | L2 | L3 | CTX | Coverage | Violation History |
|---|----------------|----|----|----|----|----|----|----------|-------------------|
| 16 | Content Pipeline review | — | — | ✅ #11 | ✅ | ✅ | ✅ | 4/6 | No violations |
| 17 | Portfolio actions review | — | — | ✅ #12 | ✅ | ✅ | ✅ | 4/6 | No violations |
| 18 | Key people abbreviations | — | — | ✅ #5 | ✅ | ✅ | ✅ | 4/6 | No violations |
| 19 | Deep research protocol | — | — | ✅ #10 | ✅ | ✅ | ✅ | 4/6 | No violations |
| 20 | Build Roadmap management | — | — | — | ✅ | ✅ | ✅ | 3/6 | No violations |

### META

| # | Instruction Set | 0a | 0b | L1 | L2 | L3 | CTX | Coverage |
|---|----------------|----|----|----|----|----|----|----------|
| 21 | Layered persistence architecture | — | — | ✅ #15 | — | ✅ | ✅ | 3/6 |
| 22 | Persistence audit cadence (every 5 sessions) | — | — | ✅ #15 | — | ✅ | ✅ | 3/6 |

## Known Gaps (candidates for next upgrade)

1. **Schema integrity (#15)** — Only in CLAUDE.md (1 layer). Violated in sessions 17, 21, 27. Should be upgraded to Memory + ai-cos skill in next audit.
2. **Notion bulk-read pattern (#10)** — Only in ai-cos skill + CLAUDE.md (2 layers). The most systemically violated pattern (sessions 2-31). Consider adding to Memory.
3. **Session Behavioral Audit (#8)** — Currently only in ai-cos skill + CLAUDE.md (2 layers). Needs Memory entry + Global Instructions for 4-layer coverage. New in Session 036.
4. **Subagent handling (#23)** — ✅ RESOLVED Session 037. Now at 5/6 layers (0a, 0b, L1 #18, L2, L3). Was root cause of cascading violations across sessions 034-037.

## Audit Protocol (run at sessions 038, 043, 048, ...)

1. Read iteration logs for last 5 sessions
2. Grep for patterns: "BROKEN", "failed", "wrong method", "trial", "error", property formatting mistakes, sandbox violations
3. For each pattern found 2+ times: check this coverage map, upgrade layer count if below target
4. Update this file + CONTEXT.md summary table
5. If new Memory entries needed: update `docs/claude-memory-entries-v5.md` and flag for user to paste into Claude.ai
6. If ai-cos skill changed: bump version and package .skill
