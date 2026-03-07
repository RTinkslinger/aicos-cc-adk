> **STALE — Cowork-era artifact.** Superseded by `docs/source-of-truth/` and `CLAUDE.md`. This file is preserved for historical context only.

# AI CoS v6 Artifacts Index
# Last updated: March 4, 2026 — Session 037
# Single reference point for all critical configuration artifacts

## What is v6?
Milestone release. v5's "What's Next?" action optimizer + v6's **Layered Persistence Architecture** — self-documenting, self-auditing instruction persistence across 6 layers. 7-step session close checklist. Cowork operating rules baked into skill. Coverage map with auto-audit every 5 sessions.
Built on System Vision v3. Applied across all three Claude surfaces on March 4, 2026.

---

## Artifact Map

### 1. AI CoS Skill (Cowork / Claude Desktop)
- **Version:** v6.2.0
- **Source of truth:** `skills/ai-cos-v6-skill.md`
- **Packaged bundle:** `ai-cos-v6.2.0.skill`
- **Installed in Cowork:** ⏳ Pending (packaged Session 037)
- **Key change (v6.2.0):** Session 037: Subagent context gap fix (template library, spawning checklist, CLAUDE.md §F). Audit v1.3.0 with template correctness. Multi-layer persistence for subagent rules. L0a/L0b surface distinction.
- **How to update:** Edit `ai-cos-v6-skill.md` → `mkdir -p /tmp/pkg/ai-cos && cp source.md /tmp/pkg/ai-cos/SKILL.md && cd /tmp/pkg && zip -r output.skill ai-cos/` → `present_files` → double-click to install

### 2. Notion Mastery Skill (Cowork / Claude Desktop)
- **Version:** v1.2.0
- **Source of truth:** `.skills/skills/notion-mastery/SKILL.md`
- **Packaged bundle:** `notion-mastery-v1.2.0.skill`
- **Installed in Cowork:** ✅ Yes (Session 032)
- **Key change (v1.2.0):** Semantic pattern-based description (triggers on tool usage patterns, not keywords). `view://UUID` bulk-read pattern. All broken methods documented.
- **How to update:** Edit `.skills/skills/notion-mastery/SKILL.md` → package as ZIP → install

### 3. User Preferences (Claude.ai)
- **Source of truth:** `docs/claude-user-preferences-v6.md`
- **Live in Claude.ai:** Yes (updated March 3, 2026)
- **How to update:** Edit the doc → copy-paste into Claude.ai → Settings → User Preferences

### 4. Memory Entries (Claude.ai)
- **Source of truth:** `docs/claude-memory-entries-v6.md`
- **Entries:** 18 total (updated Session 037 — added #17 Session Behavioral Audit, #18 Subagent Handling Rules)
- **Live in Claude.ai:** ✅ All 18 entries pasted (user updated #17-18 in session 037)
- **How to update:** Edit the doc → manually edit each entry in Claude.ai → Settings → Memory

### 5. CLAUDE.md (Claude Code / Cowork project context)
- **Location:** `CLAUDE.md` (root of AI CoS folder)
- **Updated:** Session 037 (section F subagent spawning protocol, last session ref)
- **How to update:** Edit directly — Claude Code and Cowork auto-load it

### 6. CONTEXT.md (Master context — all surfaces)
- **Location:** `CONTEXT.md` (root of AI CoS folder)
- **Updated:** Session 037 (session log entry, header update)
- **How to update:** Edit directly — skill Step 1 loads this first

### 7. Cowork Global Instructions
- **Source of truth:** `docs/cowork-global-instructions-v6.md`
- **Version:** v6.2.0 (updated Session 037 — 8-step close checklist, subagent handling section, v6 artifact refs)
- **Live in Cowork:** ✅ Yes (user pasted v6.2.0 in session 037)
- **Location:** Claude Desktop → Settings → Cowork → Global Instructions

### 8. System Vision
- **Location:** `docs/aakash-ai-cos-system-vision-v3.md`
- **Version:** v3 (the conceptual foundation for all v5 artifacts)

---

## Claude.ai Memory Entries (18 total)

| # | Topic | Last Updated |
|---|-------|-------------|
| 1 | Identity & Roles | Session 024 |
| 2 | AI CoS Vision ("What's Next?") | Session 024 |
| 3 | Four Priority Buckets | Session 024 |
| 4 | IDS Methodology | Session 024 |
| 5 | Key People & Tools | Session 024 |
| 6 | Working Style & Thesis Threads | Session 024 |
| 7 | AI CoS Build Architecture | Session 024 |
| 8 | Feedback Loop | Session 024 |
| 9 | New Thesis → Notion write-through | Session 024 |
| 10 | Deep Research Protocol | Session 024 |
| 11 | Content Pipeline Review | Session 024 |
| 12 | Portfolio Actions Review | Session 024 |
| 13 | Action Scoring Model | Session 024 |
| 14 | Notion Skill Semantic Trigger | Session 032 |
| 15 | Layered Persistence Architecture | Session 033 |
| 16 | Cowork Operating Rules (Repeated Mistakes) | Session 033 |
| 17 | Session Behavioral Audit | Session 037 |
| 18 | Subagent Handling Rules | Session 037 |

---

## Version History

| Version | Date | Key Change |
|---------|------|------------|
| v1 | Mar 1 | Initial skill, "network strategist" |
| v2 | Mar 1 | Added Notion IDs, IDS methodology, thesis threads |
| v3 | Mar 1 | Added Content Pipeline, Portfolio Actions, cross-surface protocols |
| v4 | Mar 2 | HTML digests, deploy pipeline, notion-mastery skill reference |
| **v5** | **Mar 3** | **"What's Next?" action optimizer reframe. Action Scoring Model. Full action space.** |
| **v5b** | **Mar 3** | **Session Lifecycle Management: checkpoints, close checklist, trigger words in skill description.** |
| **v5.1.0** | **Mar 4** | **Build Roadmap triggers added (Session 031). AI CoS skill packaged with Build Roadmap request type.** |
| **v5.2.0** | **Mar 4** | **Notion Quick Ref block added to ai-cos. notion-mastery v1.2.0 with semantic patterns. 5-layer defense. Memory #14.** |
| **v5.3.0** | **Mar 4** | **Layered Persistence Architecture. Cowork Operating Ref in ai-cos. 7-step close checklist. Memory #15 + #16. Coverage map + audit protocol.** |
| **v6.0.0** | **Mar 4** | **Milestone release. All artifacts bumped to v6. Layered persistence + self-documenting audit architecture. 16 Memory entries. 7-step close. Cowork operating rules in-skill.** |
| **v6.1.0** | **Mar 4** | **Parallel development Phase 0. File classification, 6 operational rules, subagent allowlist protocol, 3-layer enforcement, Build Roadmap parallel workflow. Close checklist 8-step.** |
| **v6.2.0** | **Mar 4** | **Session Behavioral Audit v1.1.0. Mandatory Step 1c + on-demand. Trial-and-error detection. Subagent delegation for close. Parallel dev Phase 1 validated.** |
| **v6.2.0-s037** | **Mar 4** | **Subagent context gap fix: template library (4 templates), spawning checklist (§F), audit v1.3.0 with template correctness. Multi-layer persistence for subagent rules. L0a/L0b surface distinction.** |

---

## Quick Checklist (run after any v-bump)
- [ ] `skills/ai-cos-v6-skill.md` written
- [ ] `.skill` packaged as ZIP and installed in Claude Desktop
- [ ] `docs/claude-user-preferences-v6.md` updated if identity changed
- [ ] `docs/claude-memory-entries-v6.md` updated and entries synced in Claude.ai
- [ ] `.skills/skills/notion-mastery/SKILL.md` updated if Notion patterns changed
- [ ] `CLAUDE.md` updated (Last Session + any new rules)
- [ ] `CONTEXT.md` updated (build state + session log)
- [ ] This file (`docs/v6-artifacts-index.md`) updated with new versions
