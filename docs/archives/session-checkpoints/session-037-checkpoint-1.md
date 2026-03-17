# Session 037 — Checkpoint 1
**Saved:** 2026-03-04
**Session focus:** Subagent context gap diagnosis + structural fixes

## What's Done
1. ✅ Session 036 close checklist completed (Notion 403 on Build Roadmap writes — manual entry needed)
2. ✅ Orphaned files deleted (7 docs + 4 old .skill files) via osascript
3. ✅ **Fix 1:** Template library created at `scripts/subagent-prompts/` — 4 templates + README
4. ✅ **Fix 2:** Spawning Checklist confirmed in CLAUDE.md §F (already existed from 036 close)
5. ✅ **Fix 3:** "Subagent Tool Limitations (Session 037)" section added to `ai-cos-v6-skill.md` in Parallel Development Rules — full CAN/CAN'T inventory, template library ref, hand-off protocol, spawning checklist
6. ✅ **Fix 4:** Behavioral audit prompt upgraded to v1.2.0 — patterns 7-9 (missing constraints, sandbox violations, MCP attempts) + expanded Section D table

## What's In Progress
- Multi-layer persistence propagation for subagent handling rules (user flagged as super critical)
- Audit enhancement: check whether subagents received correct template when one was available

## What's Pending (Parked — waiting for user go-ahead)
- Update `docs/cowork-global-instructions-v6.md` (7→8 step)
- Update `docs/claude-memory-entries-v6.md` (add #17 for behavioral audit)
- Update `docs/v6-artifacts-index.md` (memory paste status + #17)

## Key Files Modified This Session
- `scripts/subagent-prompts/README.md` (NEW)
- `scripts/subagent-prompts/session-close-file-edits.md` (NEW)
- `scripts/subagent-prompts/skill-packaging.md` (NEW)
- `scripts/subagent-prompts/git-push-deploy.md` (NEW)
- `scripts/subagent-prompts/general-file-edit.md` (NEW)
- `skills/ai-cos-v6-skill.md` (added Subagent Tool Limitations subsection)
- `scripts/session-behavioral-audit-prompt.md` (v1.1.0 → v1.2.0, patterns 7-9 + Section D expansion)

## Key Decisions
- User explicitly said: implement subagent fixes FIRST, park file updates as test case for AFTER
- User said: don't use subagents while implementing the subagent fix itself
- User flagged: subagent handling rules need ALL-LAYER persistence (super critical)
- User flagged: audit should validate template usage correctness per subagent spawn

## Current Layer Coverage for Subagent Rules
- L3 CLAUDE.md §F: ✅ Spawning Checklist (6 steps) + template library ref
- L2 ai-cos skill: ✅ Subagent Tool Limitations section (CAN/CAN'T, templates, hand-off, checklist)
- L1 Claude.ai Memory: ❌ No entry yet
- L0a Cowork Global Instructions: ❌ No mention yet
- L0b User Preferences: ❌ No mention yet
- Audit (behavioral): ✅ Patterns 7-9 + Section D table (v1.2.0)
- Coverage map: ❌ Not yet added as tracked item
