# Session 027 — Deploy Pipeline Fix & Schema Drift Root-Cause
**Date:** 2026-03-03
**Surface:** Cowork
**Trigger:** "hygiene stuff" → discovered dead Vercel digest links

## What Happened
User asked for general system hygiene. Discovered all HTML digest links on Vercel were dead/returning errors. Root-caused to THREE separate issues in the git → GitHub → Vercel deploy pipeline.

## Issues Found & Fixed

### Issue 1: Uncommitted digest files
- 4 digest JSON files existed locally but were never committed/pushed
- Fix: `git add` + commit + push via osascript

### Issue 2: Missing GitHub webhook
- Vercel's GitHub integration webhook was completely absent from the repo
- Created Vercel Deploy Hook + GitHub webhook manually via API
- Also updated expired `VERCEL_TOKEN` GitHub secret for the GitHub Action

### Issue 3: Schema drift between pipeline skill and TypeScript types (ROOT CAUSE)
- Pipeline skill template (`skills/youtube-content-pipeline/SKILL.md`) used different field names than the frontend TypeScript types expected
- LLM also sometimes deviated from its own skill template (e.g. `core_argument` string instead of `core_arguments` array)
- **Two-pronged fix:**
  1. Updated skill template to match TypeScript types exactly (field names, enum values)
  2. Expanded normalization layer in `digests.ts` (7 normalizations) as defense-in-depth

### Field Mapping (skill template → TypeScript types)
| Old (Skill) | New (Types) | Status |
|---|---|---|
| `challenge` | `what` | Fixed |
| `thread_name` | `thread` | Fixed |
| `quote` | `text` | Fixed |
| `key_question_impact` | `key_question` | Fixed |
| `validates/challenges` | `validate/challenge` | Fixed |
| `action_type` | `type` | Fixed |
| `Tangential` | `Weak` | Fixed |
| `new_angle` | `mixed` | Fixed |

## Key Files Modified
- `aicos-digests/src/lib/digests.ts` — Expanded normalization layer
- `aicos-digests/src/app/d/[slug]/page.tsx` — Optional chaining for safety
- `skills/youtube-content-pipeline/SKILL.md` — Template aligned to TypeScript types

## Commits
- `d01ba1f` — Initial normalization + optional chaining + uncommitted files
- `566088c` — Full schema drift normalization expansion

## Result
- All 12 digests returning HTTP 200 on production
- Dual deploy (webhook + GitHub Action) both working
- Future pipeline runs will produce correctly-named fields
- Normalization layer catches LLM drift as defense-in-depth

## System Hygiene Diagnostic (partial)
- CONTEXT.md: current (Session 026)
- Iteration logs: 16 entries, healthy
- Session checkpoints: folder exists, no entries yet (first use pending)
- Scripts: all operational
- No stale files or broken references detected
- Remaining: Cowork Global Instructions need paste into Claude Desktop settings

## AI CoS Connection
- The schema drift bug is a direct learning for the AI CoS build: **LLM outputs need runtime normalization as defense-in-depth**, not just prompt engineering. The skill template is the "ideal" but the normalization layer is the "safety net."
- This is an instance of the broader pattern: any pipeline that depends on LLM-structured output needs a validation/normalization layer between raw output and consumer (frontend, database, etc.).
- **Action:** Consider adding a JSON schema validator to `publish_digest.py` as a pre-publish gate (P2).
