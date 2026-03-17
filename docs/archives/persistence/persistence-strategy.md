> **STALE — Cowork-era artifact.** Claude Code uses `CLAUDE.md` + `CONTEXT.md` + auto memory (`~/.claude/projects/*/memory/`). This file is preserved for historical context only. See `docs/source-of-truth/` for current system state.

# AI CoS Persistence Strategy — How Context Lives Across All Surfaces
# Created: March 2, 2026

---

## The Architecture: 3 Layers of Persistence

### Layer 1: Claude.ai Memory (Broadest Reach)
**What:** ~8 memory entries that persist across ALL Claude.ai conversations (web, mobile, desktop)
**Where:** Settings → Memory in Claude.ai
**Coverage:** Every Claude conversation, whether AI CoS related or not
**Content:** Identity, vision, four buckets, IDS methodology, key people, working style, thesis threads, feedback loop reminder
**File:** `docs/claude-memory-entries.md` — copy each entry into Claude.ai Memory

### Layer 2: AI CoS Cowork Skill (Deep Context for Cowork)
**What:** The ai-cos skill that triggers aggressively on any investing/network/meeting topic
**Where:** Installed in Cowork as a .skill file
**Coverage:** Any Cowork session where an AI CoS-related trigger word appears
**Content:** Full SKILL.md with inline essential context + pointer to CONTEXT.md for full detail
**Key fix (v2):** No longer depends on a dead session path. Dynamically finds CONTEXT.md or falls back to inline context.
**File:** `skills/ai-cos-v2.skill` — install this to replace the current skill

### Layer 3: CLAUDE.md (Claude Code Context)
**What:** Project-level context file that Claude Code reads automatically
**Where:** Root of the Aakash AI CoS project folder
**Coverage:** Any Claude Code session working in this project
**Content:** Quick orientation + Notion IDs + anti-patterns + pointers to CONTEXT.md
**File:** Already exists at project root as `CLAUDE.md`

### Layer 0: Cowork User Preferences (Baseline)
**What:** Short preference blurb shown to Claude in every Cowork session
**Where:** Cowork app settings
**Current:** "ask clarifying questions. I run a multi faceted life where I both build and invest."
**Recommended update:** See below

---

## Action Items

### 1. Add Claude.ai Memory Entries (DO THIS FIRST)
Go to claude.ai → Settings → Memory → Add each entry from `docs/claude-memory-entries.md`
This gives ALL Claude conversations baseline context about who you are and the AI CoS vision.

### 2. Install Updated AI CoS Skill
In Cowork, install `skills/ai-cos-v2.skill` to replace the current skill.
This fixes the dead session path and adds inline fallback context.

### 3. Update Cowork User Preferences
In Cowork settings, update your user preferences to:

```
I run a multifaceted life as both a builder and investor. I'm MD at Z47 ($550M) and DeVC ($60M). I'm building an AI Chief of Staff system — a network strategist that optimizes my meeting allocation. Every interaction is also a learning session that feeds into the AI CoS build. Ask clarifying questions. I'm adept at coding (Claude Code daily), finance, and AI/ML. When I reference IDS, buckets, pipeline, thesis, collective, scoring, or network optimization, load the ai-cos skill. Key context: I meet 7-8 people/day, live on WhatsApp/mobile, and my primary operating methodology is IDS (Increasing Degrees of Sophistication).
```

### 4. CLAUDE.md Already Exists
The CLAUDE.md at project root is already good for Claude Code sessions.

---

## The Feedback Loop: How Every Interaction Compounds

### During Any Session:
1. Complete the task at hand (research, automation, analysis, etc.)
2. At session end, ask: "Did this session produce any learnings for the AI CoS system?"
3. If yes:
   - **New thesis thread discovered?** → Add to CONTEXT.md "Thesis Threads" section
   - **New pattern in how Aakash works?** → Add to CONTEXT.md "Operational Playbooks" section
   - **New tool/integration discovered?** → Add to CONTEXT.md or update SKILL.md
   - **Build state changed?** → Update CONTEXT.md "Current Build State" section
   - **New Notion IDs found?** → Add to CONTEXT.md "Notion Data Architecture" section
4. Update the "Last Updated" date in CONTEXT.md

### Periodic Reviews:
- **Weekly:** Scan iteration logs for patterns that should be distilled into CONTEXT.md
- **Monthly:** Review Claude.ai Memory entries — do they still reflect current priorities and thesis threads?
- **After major sessions:** Update the SKILL.md inline context if CONTEXT.md has evolved significantly, rebuild .skill file

### The Principle:
CONTEXT.md is the living brain. Claude.ai Memory is the ambient awareness. The skill is the activation mechanism. Every session that touches any of these makes the next session smarter.
