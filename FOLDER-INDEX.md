# AI CoS Project — Folder Index

*Auto-generated: 2026-03-05 | Session 040*

## Root — Core Files

| File | Purpose |
|---|---|
| `CONTEXT.md` | Single source of truth — master context for all sessions |
| `CLAUDE.md` | Operating rules, anti-patterns, Notion IDs, session history |
| `COWORK_INSTRUCTIONS.md` | Cowork-specific onboarding instructions |
| `ai-cos-v6.2.0.skill` | Current packaged ai-cos skill (ZIP) |
| `notion-mastery-v1.2.0.skill` | Current packaged notion-mastery skill (ZIP) |

## Root — Stray / Cleanup Candidates

| File | What it is | Action |
|---|---|---|
| `ai-cos-skill-preview.md` | Draft skill file, redundant with installed skill | → `docs/session-001-artifacts/` or delete |
| `ziAmr2ZQ`, `ziFWhB2E`, `ziPCTIhM`, `zivNSN1x` | Temp skill ZIP build artifacts (today) | Delete |

---

## `/aicos-digests/` — HTML Digest Site

Next.js 16 app, live at **https://digest.wiki**. Has its own GitHub repo. Deploy: push to `main` → GitHub Action → Vercel.

## `/analysis/`

Ad-hoc analysis outputs (Klarna CEO analysis, quick references).

## `/data/`

Placeholder directories from session 1 (`deal-history/`, `network/`). Currently empty — live data is in Notion.

## `/digests/`

PDF digest outputs from Content Pipeline. 9 files including iterative redesigns of the "Cursor is Obsolete" digest.

## `/docs/`

All documentation, organized by type:

| Subfolder | Contents |
|---|---|
| `adr/` | Architecture Decision Records (1 file) |
| `audit-reports/` | Session QA audit reports (sessions 036-038) |
| `iteration-logs/` | Session logs, 001 through 039 (25 files) |
| `notion-schema/` | Network DB schema guide |
| `persistence/` | Layered persistence artifacts — memory entries, user prefs, global instructions, coverage map, artifacts index |
| `plan-versions/` | Historical plan docs |
| `plans/` | Active plans (build roadmap, content pipeline v5) |
| `research/` | Research docs (Granola integration, vector architecture, parallel dev, subagent diagnostics) |
| `session-001-artifacts/` | Early project artifacts archived from root (PLAN, README, SESSION_001_SUMMARY, DEPLOY-PLAN, project ZIP, portfolio xlsx) |
| `session-checkpoints/` | Mid-session pickup files (23 files across sessions 016-039) |
| `stack-discoveries/` | Connector landscape research |
| `vision/` | System vision docs v1-v3 |

**Duplicates to clean up:**

- `docs/stack docs/` and `docs/stack-docs/` — identical contents (LinkedIn & X, M365 research). Keep `stack-docs/`, delete `stack docs/`.
- `docs/qa-audit-session-038/` and `docs/audit-reports/qa-session-038/` — identical. Keep `audit-reports/`, delete the root-level duplicate.

## `/logs/`

YouTube extractor stderr/stdout logs.

## `/mcp-servers/`, `/models/`, `/plugins/`, `/templates/`

Empty placeholder directories from session 1 scaffolding. Not actively used.

## `/portfolio-research/`

Individual company research files — 20 portfolio companies (Confido, GameRamp, Codeant, PowerUp, Smallest AI, etc.).

## `/queue/`

Content Pipeline queue. `pipeline-run-log.md` + `processed/` with 5 YouTube extraction JSONs (Mar 1-4).

## `/scripts/`

Operational scripts — the engine room:

| Script | Purpose |
|---|---|
| `youtube_extractor.py` | YouTube transcript extraction (runs via launchd) |
| `process_youtube_queue.py` | Content Pipeline analysis |
| `publish_digest.py` | JSON → Notion + digest site publish |
| `content_digest_pdf.py` | PDF digest generation |
| `action_scorer.py` | Action scoring model (session 039) |
| `dedup_utils.py` | Deduplication utilities (session 039) |
| `branch_lifecycle.sh` | Git branch lifecycle CLI for parallel dev |
| `auto_push.sh` | Auto-push helper |
| `validate-skill-package.sh` | Skill ZIP validation |
| `setup_youtube_cron.sh` | Launchd cron setup |
| `notify_digest_template.py` | Notion digest template |
| `yt` | YouTube CLI wrapper |
| `subagent-prompts/` | Bash subagent prompt templates (4 templates) |
| `session-behavioral-audit-prompt.md` | Audit prompt template |
| `*.plist` | macOS launchd configs |

## `/skills/`

Skill source files and packaged versions:

| Item | Status |
|---|---|
| `ai-cos-v6-skill.md` | **Current** source (v6) |
| `ai-cos-v2/3/4/5*.skill` | Historical versions |
| `full-cycle/SKILL.md` | Full cycle orchestrator skill |
| `parallel-deep-research/SKILL.md` | Deep research skill |
| `youtube-content-pipeline/SKILL.md` | Content pipeline skill |
| `SKILL.md.updated` | Stray temp file — delete |
| `ziZlZits`, `zidvu6Bv`, `ziswthao` | Stray skill ZIP artifacts — delete |

## `/Training Data/`

IDS methodology training samples — emails (.eml) and docs (.pdf) for Confido, xPay, Boba Bhai, Flent, etc. Used for training the AI CoS on Aakash's investing patterns.

---

## Summary: Cleanup Opportunities

1. **Delete 7 stray `zi*` files** — 4 in root, 3 in `skills/` (temp ZIP artifacts)
2. **Delete `ai-cos-skill-preview.md`** from root (redundant)
3. **Delete `docs/stack docs/`** (duplicate of `docs/stack-docs/`)
4. **Delete `docs/qa-audit-session-038/`** (duplicate of `docs/audit-reports/qa-session-038/`)
5. **Delete `skills/SKILL.md.updated`** (stray temp)
6. **Consider archiving** old skill versions (`v2-v5`) into a `skills/archive/` subfolder
7. **Consider archiving** iterative digest PDFs (`REDESIGNED_v1-v4`) keeping only latest
8. **Empty dirs** (`data/`, `mcp-servers/`, `models/`, `plugins/`, `templates/`) — keep or remove based on future plans
