> **STALE — Cowork-era artifact.** Superseded by `docs/source-of-truth/` and `CLAUDE.md`. This file is preserved for historical context only.

# AI CoS v5 Artifacts Index
# Last updated: March 4, 2026 — Session 033
# Single reference point for all critical configuration artifacts

## What is v5?
System Vision v3 reframe: "What's Next?" action optimizer (not "Who should I meet next?" network strategist).
Applied across all three Claude surfaces on March 3, 2026.

---

## Artifact Map

### 1. AI CoS Skill (Cowork / Claude Desktop)
- **Version:** v5.3.0
- **Source of truth:** `skills/ai-cos-v5-skill.md`
- **Packaged bundle:** `ai-cos-v5.3.0.skill`
- **Installed in Cowork:** ⏳ Pending (packaged Session 033, awaiting install)
- **Key change (v5.3.0):** Cowork Operating Ref block (sandbox, deploy, Notion formatting, skill packaging). 7-step close checklist (added artifacts index + skill packaging steps). Layered persistence coverage.
- **How to update:** Edit `ai-cos-v5-skill.md` → `mkdir -p /tmp/pkg/ai-cos && cp source.md /tmp/pkg/ai-cos/SKILL.md && cd /tmp/pkg && zip -r output.skill ai-cos/` → `present_files` → double-click to install

### 2. Notion Mastery Skill (Cowork / Claude Desktop)
- **Version:** v1.2.0
- **Source of truth:** `.skills/skills/notion-mastery/SKILL.md`
- **Packaged bundle:** `notion-mastery-v1.2.0.skill`
- **Installed in Cowork:** ✅ Yes (Session 032)
- **Key change (v1.2.0):** Semantic pattern-based description (triggers on tool usage patterns, not keywords). `view://UUID` bulk-read pattern. All broken methods documented.
- **How to update:** Edit `.skills/skills/notion-mastery/SKILL.md` → package as ZIP → install

### 3. User Preferences (Claude.ai)
- **Source of truth:** `docs/claude-user-preferences-v5.md`
- **Live in Claude.ai:** Yes (updated March 3, 2026)
- **How to update:** Edit the doc → copy-paste into Claude.ai → Settings → User Preferences

### 4. Memory Entries (Claude.ai)
- **Source of truth:** `docs/claude-memory-entries-v5.md`
- **Entries:** 16 total (updated Session 033 — #14 Notion Skill Semantic Trigger, #15 Layered Persistence Architecture, #16 Cowork Operating Rules)
- **Live in Claude.ai:** ⏳ #14 pending paste, #15 pending paste, #16 pending paste
- **How to update:** Edit the doc → manually edit each entry in Claude.ai → Settings → Memory

### 5. CLAUDE.md (Claude Code / Cowork project context)
- **Location:** `CLAUDE.md` (root of AI CoS folder)
- **Updated:** Session 033 (persistence audit check, triage principle, 7-step checklist rule)
- **How to update:** Edit directly — Claude Code and Cowork auto-load it

### 6. CONTEXT.md (Master context — all surfaces)
- **Location:** `CONTEXT.md` (root of AI CoS folder)
- **Updated:** Session 033 (layered persistence coverage map, audit protocol, 7-step checklist, layer descriptions updated)
- **How to update:** Edit directly — skill Step 1 loads this first

### 7. Cowork Global Instructions
- **Source of truth:** `docs/cowork-global-instructions-v1.md`
- **Version:** v1.1 (updated Session 033 — 7-step close checklist)
- **Live in Cowork:** ✅ Yes
- **Location:** Claude Desktop → Settings → Cowork → Global Instructions

### 8. System Vision
- **Location:** `docs/aakash-ai-cos-system-vision-v3.md`
- **Version:** v3 (the conceptual foundation for all v5 artifacts)

---

## Claude.ai Memory Entries (16 total)

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

---

## Quick Checklist (run after any v-bump)
- [ ] `skills/ai-cos-v5-skill.md` written
- [ ] `.skill` packaged as ZIP and installed in Claude Desktop
- [ ] `docs/claude-user-preferences-v5.md` updated if identity changed
- [ ] `docs/claude-memory-entries-v5.md` updated and entries synced in Claude.ai
- [ ] `.skills/skills/notion-mastery/SKILL.md` updated if Notion patterns changed
- [ ] `CLAUDE.md` updated (Last Session + any new rules)
- [ ] `CONTEXT.md` updated (build state + session log)
- [ ] This file (`docs/v5-artifacts-index.md`) updated with new versions
