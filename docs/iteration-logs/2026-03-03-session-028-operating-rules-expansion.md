# Session 028 — Operating Rules Expansion + digest.wiki Integration
**Date:** 2026-03-03
**Surface:** Cowork

## What Happened

### 1. Comprehensive Operating Rules Audit
- Mined ALL 27 session iteration logs + SKILL.md via sub-agents
- Expanded CLAUDE.md from 8 sandbox-only rules → 35 rules across 4 categories:
  - A. Cowork Sandbox (8 rules — infrastructure)
  - B. Notion Operations (11 rules — sessions 2-6, 17-18, 27)
  - C. Schema & Data Integrity (6 rules — sessions 17, 21, 27)
  - D. Skill & Artifact Management (6 rules — sessions 24-26)
- Every rule cites its source session
- Elevated core principle: "LLM output pipelines need runtime normalization, not just prompt engineering"

### 2. Deploy Path Consolidation
- Deleted duplicate Vercel Deploy Hook (webhook ID 598873586)
- Confirmed 0 webhooks remain — single path: GitHub Action only

### 3. File Compaction
- DEPLOY-PLAN.md: 236 → 26 lines
- CONTEXT.md: cleaned stale dual-deploy references

### 4. digest.wiki Domain Integration
- Verified digest.wiki resolves to same Vercel deployment as aicos-digests.vercel.app
- Added "Digest URL" (type: URL) property to Content Digest DB schema
- Populated all 15 Notion pages (12 unique titles + 3 duplicates) with `https://digest.wiki/d/{slug}` URLs
- Updated CLAUDE.md and CONTEXT.md references from aicos-digests.vercel.app → digest.wiki
- Validated 3 spot-checks: Notion Digest URL field matches live digest.wiki pages

## Files Modified
1. `CLAUDE.md` — 95→134 lines. Operating rules expansion, core principle, digest.wiki refs
2. `CONTEXT.md` — deployment refs updated to digest.wiki, Layer 1 memory ref updated
3. `DEPLOY-PLAN.md` — 236→26 lines (compacted)
4. `docs/session-checkpoints/2026-03-03-session-028-checkpoint.md`
5. `docs/session-checkpoints/2026-03-03-session-028-checkpoint-2.md`

## Notion Changes
- Content Digest DB: Added "Digest URL" property, populated 15 pages

## Key Decisions
- Historical session log entries in CONTEXT.md left with original aicos-digests.vercel.app URLs (they document what was true at the time)
- Duplicate Notion pages (3 found) updated with same Digest URL as their canonical counterparts
- Core LLM normalization principle placed ABOVE all subsections in Operating Rules

## AI CoS Learnings
- Notion Content Digest DB had more pages than expected (15 vs 12) — 3 duplicates from earlier pipeline runs. Future pipeline should deduplicate or flag duplicates.
- Custom domain adds a layer of professional sharability for WhatsApp-first workflow
