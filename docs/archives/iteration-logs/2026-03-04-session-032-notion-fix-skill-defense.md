# Session 032 — Notion Systemic Fix + 5-Layer Skill Defense
**Date:** 2026-03-04
**Duration:** ~3 hours (spanned 2 context windows)
**Checkpoints:** 1 (`docs/session-checkpoints/session-032-checkpoint-01.md`)

## Summary

Three-phase infrastructure session: (1) permanently fixed the systemic Notion read/write failure that plagued sessions 2-31, (2) deployed notion-mastery as an auto-loaded Cowork skill, (3) designed and implemented a 5-layer defense strategy for tool-adjacent skill loading when user prompts don't mention "Notion."

## Phase 1 — Notion Systemic Fix

**Root cause:** Contradictory recipes in CLAUDE.md, broken `API-query-data-source` endpoints, and no working bulk-read pattern documented.

**Discovery:** `notion-query-database-view` with `view://UUID` format is the ONLY working method for bulk database reads. All other methods fail:
- `API-query-data-source` → "Invalid request URL" (ALL `/data_sources/*` Raw API endpoints broken)
- `notion-fetch` on `collection://` → returns schema only, no rows
- `notion-query-database-view` with `https://` URLs → invalid URL error

**How to get view URLs:** `notion-fetch` on database ID → response includes `<view url="view://UUID">` tags → use that URL with `notion-query-database-view`.

**Files updated:**
- `CLAUDE.md` — Build Roadmap Recipes rewritten with proven `view://` approach, Operating Rules table expanded with all broken vs working methods, universal bulk-read pattern added
- `.skills/skills/notion-mastery/SKILL.md` — Recipe 4 (bulk read), Recipe 5 (Build Roadmap), Gotcha #2, decision tree all fixed

**Validation:** Build Roadmap (all 17 items) fetched in ONE call using `view://4eb66bc1-322b-4522-bb14-253018066fef`.

## Phase 2 — Skill Deployment

Packaged notion-mastery as `.skill` ZIP (v1.1.0) and presented for Cowork installation. Added `version` field to frontmatter (was missing — Session 031 rule).

## Phase 3 — 5-Layer Skill Defense

**Problem:** notion-mastery won't auto-trigger when prompts don't mention "Notion" (e.g., "review my build roadmap", "process my content queue"). Cowork's skill triggering is description-only semantic matching — no dependency declaration, no tool-usage triggers, no always-on mode.

**Research confirmed:** Description field is the ONLY trigger interface. This is a product gap, not a configuration issue. Skills tend to "undertrigger."

**Solution — 5 layers (all implemented):**

1. **CLAUDE.md (always in context):** Added semantic trigger instruction to Operating Rules § B — "Before making ANY Notion MCP tool call, STOP and load notion-mastery first. This applies even when the user's prompt never mentions 'Notion.'"

2. **Claude.ai Memory #14 (covers mobile/web):** Added entry with semantic trigger instruction for cross-surface coverage.

3. **ai-cos skill v5.2.0 (most common trigger path):** Added compact Notion Quick Ref block with emergency fallback patterns (bulk-read recipe, known view URLs, broken methods, property formatting).

4. **notion-mastery description v1.2.0 (semantic rewrite):** Changed from keyword-based to semantic pattern-based description: "Use this skill whenever ANY task will call Notion MCP tools — even if the user never says 'Notion.'" Includes tool name patterns and database-related task patterns as triggers.

5. **Build Roadmap insight (long-term):** Created "Tool-triggered skill loading" item (page ID: `31929bcc-b6fc-81da-b249-ef9928fc605a`) — flagged as infrastructure wish for Cowork product team.

## Key Decisions

- **Semantic patterns > keyword stuffing:** Project-specific phrases (like "build roadmap") are ever-expanding and not maintainable as skill description trigger words. Pattern-based descriptions (tool names, database-related tasks) are stable.
- **Layered defense degrades gracefully:** CLAUDE.md (always loaded) → ai-cos inline ref (common path) → notion-mastery description (probabilistic). Any single layer failing is covered by others.
- **User's insight:** Semantic trigger instruction should go into Claude.ai memory AND CLAUDE.md, not just the skill description — "always-in-context" layers are more reliable than probabilistic matching.

## Files Created/Modified

| File | Action | Notes |
|------|--------|-------|
| `CLAUDE.md` | Modified | Build Roadmap Recipes rewritten, Operating Rules § B expanded (semantic trigger + universal bulk-read + known view URLs), Last Session updated |
| `.skills/skills/notion-mastery/SKILL.md` | Modified | v1.1.0 → v1.2.0: Recipe 4/5, Gotcha #2, decision tree fixed; description rewritten to semantic patterns |
| `skills/ai-cos-v5-skill.md` | Created | Copied from installed read-only, added Notion Quick Ref block, v5.1.0 → v5.2.0 |
| `ai-cos-v5.2.0.skill` | Created | Packaged ZIP for Cowork installation |
| `notion-mastery-v1.2.0.skill` | Created | Packaged ZIP for Cowork installation |
| `docs/session-checkpoints/session-032-checkpoint-01.md` | Created | Mid-session checkpoint |

## Notion Changes

- Build Roadmap: Created insight "Tool-triggered skill loading" (page `31929bcc-b6fc-81da-b249-ef9928fc605a`)

## Artifact Versions After This Session

| Artifact | Version | Location |
|----------|---------|----------|
| ai-cos skill | v5.2.0 | `skills/ai-cos-v5-skill.md` (source), installed in Cowork |
| notion-mastery skill | v1.2.0 | `.skills/skills/notion-mastery/SKILL.md` (source), installed in Cowork |
| Claude.ai Memory | 14 entries | #14 = Notion skill semantic trigger |
| CLAUDE.md | Updated | Session 032 refs, semantic trigger, bulk-read pattern |
| CONTEXT.md | Updated | Session 032 entry |
| Cowork Global Instructions | v1 (unchanged) | No changes this session |
| Cowork User Preferences | v5 (unchanged) | No changes this session |

## Gotchas Learned

- Cowork skill triggering is description-only — no dependency system, no tool-usage triggers, no always-on mode
- Installed skills at `/mnt/.skills/skills/` are read-only — must package as `.skill` ZIP
- ai-cos source file didn't exist in project folder — only the installed read-only copy existed
- Need to `Read` a file before `Edit` in every case (even in parallel call blocks)

## No Thesis Changes

Infrastructure session — no new thesis threads or conviction changes.

## Build Insight Connection

The "tool-triggered skill loading" insight (Build Roadmap) is a genuine infrastructure gap. If Cowork ever adds dependency declarations or tool-usage-based triggers, it would eliminate the need for 4 of the 5 defense layers.

## Open Items

- Monitor whether the 5-layer defense actually triggers notion-mastery in future sessions
- `docs/v5-artifacts-index.md` referenced in Session 024 but never found in project folder — created this session
