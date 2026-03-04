# Session 026 — Cowork Global Instructions
**Date:** March 3, 2026
**Duration:** Short session (~10 min)
**Trigger:** Aakash discovered empty Global Instructions field in Claude Desktop → Settings → Cowork and asked if it should be populated for AI CoS context.

## What Was Done

### 1. Created Cowork Global Instructions (new persistence layer)
Identified that Global Instructions is a separate field from User Preferences — it fires in every Cowork session before any skill loads. This is the right place for operational directives (how to operate) vs. User Preferences (who Aakash is).

**Three sections in Global Instructions:**
1. **Session Hygiene** — Checkpoint and close checklist triggers baked in at the global level. Works even in non-AI-CoS sessions.
2. **Project Context** — CONTEXT.md location pointer, skill loading rules (notion-mastery for Notion, ai-cos for investing work).
3. **Operating Principles** — Mobile-first, IDS methodology, every interaction = learning session, ask clarifying questions.

### 2. Updated Persistence Architecture
Renamed Layer 0 → Layer 0a (Global Instructions) + Layer 0b (User Preferences). Documented the distinction: 0a = operational directives, 0b = identity baseline. Updated CONTEXT.md and v5-artifacts-index.md.

### 3. Files Created/Modified
- **Created:** `docs/cowork-global-instructions-v1.md` (source of truth for Global Instructions text)
- **Modified:** `CONTEXT.md` (Layer 0 → 0a/0b split in Persistence Architecture)
- **Modified:** `docs/v5-artifacts-index.md` (added item #6: Cowork Global Instructions)

### Key Decision
Global Instructions vs. User Preferences distinction:
- **Global Instructions (Layer 0a):** HOW to operate — session hygiene, project pointers, operational rules
- **User Preferences (Layer 0b):** WHO Aakash is — identity, roles, trigger words, methodology

### Status
- ✅ Global Instructions pasted into Claude Desktop → Settings → Cowork → Global Instructions (confirmed by Aakash)

## No Thesis Changes
No new thesis threads discovered or updated this session.
