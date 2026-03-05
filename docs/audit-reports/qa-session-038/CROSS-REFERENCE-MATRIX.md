# System Cross-Reference Matrix

This document maps every major artifact and shows which files depend on it or reference it.

---

## Notion Databases (Primary Dependencies)

### Thesis Tracker (`3c8d1a34-e723-4fb1-be28-727777c22ec6`)
**CRITICAL SYNC POINT** — Shared between Claude.ai and Cowork

Referenced in:
- `CLAUDE.md` (lines 27, 136, 239)
- `CONTEXT.md` (lines 159, 242, 280, 384, 460, 470, 545)
- `skills/ai-cos-v6-skill.md` (lines 61, 78, 356, 358, 361)
- `skills/youtube-content-pipeline/SKILL.md` (lines 123, 632)
- `skills/parallel-deep-research/SKILL.md` (line 100)
- `docs/claude-memory-entries-v6.md` (Memory #14, #16)
- `scripts/session-behavioral-audit-prompt.md`

**Created by:** Session 013
**Last touched:** Session 037
**Instances:** 10 files reference it

---

### Build Roadmap DB (`6e1ffb7e-01f1-4295-a7ea-67d5c9216d8f`)
**PRODUCT ROADMAP** — AI CoS build items (self-contained, no external relations)

Referenced in:
- `CLAUDE.md` (lines 30, 34, 36, 40, 54, 58, 136, 239)
- `CONTEXT.md` (lines 462, 626, 695, 696)
- `skills/ai-cos-v6-skill.md` (lines 64, 72, 194, 207, 236, 354, 356, 358, 361)
- `ai-cos-skill-preview.md` (lines 56, 63, 187, 207)
- `docs/iteration-logs/session-031-build-roadmap-db.md`
- `docs/iteration-logs/session-032-notion-fix-skill-defense.md`
- `docs/build-roadmap-plan.md`
- `docs/v6-artifacts-index.md`

**Known View URL:** `view://4eb66bc1-322b-4522-bb14-253018066fef`
**Created by:** Session 031
**Last touched:** Session 037
**Instances:** 12+ files reference it

---

### Content Digest DB (`df2d73d6-e020-46e8-9a8a-7b9da48b6ee2`)
**CONTENT ANALYSIS** — YouTube extraction → thesis/portfolio connections

Referenced in:
- `CLAUDE.md` (line 28, 29)
- `CONTEXT.md` (lines 160, 333, 334, 385, 470)
- `skills/youtube-content-pipeline/SKILL.md` (lines 134, 435, 442, 632)
- `docs/claude-memory-entries-v6.md` (Memory #15)
- `aicos-digests/src/lib/digests.ts`

**Created by:** Session 029
**Last touched:** Session 037
**Instances:** 8 files reference it

---

### Actions Queue (`1df4858c-6629-4283-b31d-50c5e7ef885d`)
**ACTION SINK** — All action types (portfolio, thesis, network, research)

Referenced in:
- `CLAUDE.md` (line 29)
- `CONTEXT.md` (lines 156, 377, 385, 470, 476)
- `skills/youtube-content-pipeline/SKILL.md` (lines 502, 636)
- `skills/full-cycle/SKILL.md` (line 154)
- `docs/claude-memory-entries-v6.md` (Memory #15)

**Created by:** Session 029
**Last touched:** Session 037
**Instances:** 8 files reference it

---

### Portfolio DB (`4dba9b7f-e623-41a5-9cb7-2af5976280ee`)
**PORTFOLIO COMPANIES** — 94 fields, active investments

Referenced in:
- `CLAUDE.md` (line 25)
- `CONTEXT.md` (lines 155, 470, 476)
- `skills/ai-cos-v6-skill.md` (line 59)
- `skills/youtube-content-pipeline/SKILL.md` (lines 55, 635)
- `docs/claude-memory-entries-v6.md` (Memory #15)

**Instances:** 6 files reference it

---

### Companies DB (`1edda9cc-df8b-41e1-9c08-22971495aa43`)
**DEAL PIPELINE** — 49 fields, IDS trail

Referenced in:
- `CLAUDE.md` (line 24)
- `CONTEXT.md` (line 154)
- `skills/youtube-content-pipeline/SKILL.md` (lines 129, 634)

**Instances:** 3 files reference it

---

### Network DB (`6462102f-112b-40e9-8984-7cb1e8fe5e8b`)
**PEOPLE UNIVERSE** — 40+ fields, 13 archetypes

Referenced in:
- `CLAUDE.md` (line 23)
- `CONTEXT.md` (line 153)
- `skills/ai-cos-v6-skill.md` (line 57)

**Instances:** 3 files reference it

---

## Critical Files (Layer 3 — Codebase Instructions)

### CLAUDE.md (25K, 600+ lines)
**MASTER COWORK CONTEXT** — Operating rules, antirepeaters, build state

Depends on:
- All 8 Notion databases
- All active skills (for rule validation)
- `CONTEXT.md` (cross-references)

Referenced by:
- `CONTEXT.md` (cross-reference)
- All iteration logs (Session 024+)
- All checkpoint files
- `docs/v6-artifacts-index.md`
- `scripts/session-behavioral-audit-prompt.md`

**Sections:** Quick Orientation, Anti-Patterns, Notion Operations, Key IDs, Priority Buckets, Operating Rules (A-F), Last Session

**Critical Content:**
- Operating Rules A-F (sandbox, Notion, schema, skills, subagent, parallel dev)
- Build Roadmap Recipes (read/write patterns)
- Subagent Spawning Protocol (§F)
- 40+ antirepeater rules

**Version:** v6.2.0 (Session 037)
**Frequency:** Updated every 2-3 sessions with new operating rules

---

### CONTEXT.md (67K, 1500+ lines)
**MASTER STATE DOCUMENT** — Notion schema, workflow, session history, system architecture

Depends on:
- All 8 Notion databases
- All active skills (for cross-referencing)
- All session iteration logs

Referenced by:
- Every session (required reading at start)
- All iteration logs
- All checkpoint files
- `CLAUDE.md` (cross-reference)
- `docs/v6-artifacts-index.md`

**Key Sections:**
- System Architecture (full diagram)
- Notion Database Schema (all 8 DBs, 450+ properties)
- Workflow (3 surfaces: Claude.ai, Cowork, Claude Code)
- Session Close Checklist (8 steps)
- Full Session History (001-037)
- Persistence Audit Protocol
- Build Roadmap state

**Version:** v6.2.0 (Session 037)
**Update Pattern:** Every session (Steps 2-3 of close checklist)

---

## Skill Files (Layer 2 — Capabilities)

### ai-cos-v6-skill.md (1000+ lines)
**MAIN CAPABILITY SKILL** — Network scoring, portfolio tracking, action optimization, thesis management

Depends on:
- All 8 Notion databases (for IDs + schema)
- `CLAUDE.md` (operating rules)
- `CONTEXT.md` (workflow, schema)
- Full-cycle skill (orchestration reference)

Referenced by:
- Cowork semantic matching (auto-loaded)
- All iteration logs
- `ai-cos-skill-preview.md`
- `docs/v6-artifacts-index.md`

**Packaged as:** `ai-cos-v6.2.0.skill` (ZIP)
**Deployment:** Cowork → auto-loads on semantic match
**Version:** v6.2.0 (Session 037)

---

### youtube-content-pipeline/SKILL.md (829 lines)
**CONTENT PIPELINE** — YouTube extraction, analysis, thesis/portfolio matching

Depends on:
- `CLAUDE.md` (Notion rules)
- `CONTEXT.md` (schema)
- ai-cos-v6-skill (action optimization model)

Referenced by:
- Full-cycle skill (Step 2 of orchestration)
- Iteration logs (content pipeline sessions)
- `docs/content-pipeline-v5-plan.md`

**Deployment:** Cowork → embedded in skills/ directory
**Version:** v5 (Session 027+)

---

### full-cycle/SKILL.md (219 lines)
**META-ORCHESTRATOR** — Runs ALL pipelines in dependency order

Depends on:
- youtube-content-pipeline skill (Step 2)
- ai-cos-v6-skill (action scoring)
- parallel-deep-research skill (optional Step 2b)

Referenced by:
- AI CoS capability list
- Iteration logs (orchestration sessions)

**Orchestration Order:**
1. Pre-flight check (registry drift)
2. YouTube extraction (Mac osascript → content pipeline skill)
3. Content Pipeline analysis
4. Back-propagation sweep (Actions Queue → Content Digest update)

**Version:** v1 (Session 030+)

---

### parallel-deep-research/SKILL.md (124 lines)
**RESEARCH ORCHESTRATION** — Parallel web search across 3 surfaces

Depends on:
- ai-cos-v6-skill (thesis matching)
- Thesis Tracker DB (sync point)

Referenced by:
- Full-cycle skill (optional Step 2b)
- Research capabilities

**Version:** v1 (Session 030+)

---

### notion-mastery/SKILL.md (300+ lines, in `.skills/`)
**NOTION OPERATIONS GUIDE** — Enhanced Connector patterns, recipes, gotchas

Depends on:
- All Notion DB IDs (for reference)
- Operating Rules from CLAUDE.md (for patterns)

Referenced by:
- All Notion MCP tool calls (auto-loaded by Cowork)
- Iteration logs (Notion fix sessions)
- `CLAUDE.md` (semantic trigger)

**Packaged as:** `notion-mastery-v1.2.0.skill` (ZIP)
**Deployment:** Cowork → auto-loads before any Notion MCP call
**Version:** v1.2.0 (Session 032)

---

## Documentation Files (Cross-References)

### docs/v6-artifacts-index.md
**VERSION BUMP CHECKLIST** — Master tracker for all 6 artifact layers

Tracks:
- CLAUDE.md (v6.2.0)
- CONTEXT.md (v6.2.0)
- Claude.ai Memory (18 entries, v6.2.0)
- Claude.ai User Preferences (v6.2.0)
- Cowork Global Instructions (v6.2.0)
- Skills (ai-cos v6.2.0, notion-mastery v1.2.0)

**Purpose:** Ensure no version drift across surfaces
**Frequency:** Updated every session at close
**Last Updated:** Session 037

---

### docs/layered-persistence-coverage.md
**6-LAYER PERSISTENCE STATE** — Maps where each rule/instruction lives

Layers:
1. **L0a** — Cowork Global Instructions (Cowork-only, v6.2.0)
2. **L0b** — Claude.ai User Preferences (Claude.ai-only, v6.2.0)
3. **L1** — Claude.ai Memory (18 entries, v6.2.0)
4. **L2** — Skills (ai-cos, youtube-content-pipeline, full-cycle, parallel-deep-research)
5. **L3** — Codebase (CLAUDE.md, CONTEXT.md)
6. **L4** — Pre-tool hooks (notion-mastery as v1)

**Purpose:** Prevent rule drift across sessions
**Frequency:** Updated every session at close
**Last Updated:** Session 037

---

## Deployment Artifacts

### aicos-digests/ (Next.js 16 app)
**LIVE DIGEST SITE** — https://digest.wiki

Depends on:
- `scripts/publish_digest.py` (publish flow)
- `scripts/process_youtube_queue.py` (input)
- TypeScript schema (`src/lib/types.ts`)

Outputs:
- 12 digest JSON files (`src/data/*.json`)
- Live pages at `https://digest.wiki/d/{slug}`

**Deploy Flow:**
1. Commit locally
2. osascript MCP: `git push origin main`
3. GitHub Action auto-triggers
4. Vercel production (~90s)

**Data Files:**
- agi-po-shen-loh.json
- ben-horowitz-on-what-makes-a-great-founder.json
- ben-marc-10x-bigger.json
- cursor-is-obsolete.json
- design-process-dead-jenny-wen.json
- from-writing-code-to-managing-agents-mihail-eric.json
- how-to-code-with-ai-agents-peter-steinberger.json
- india-saas-50b-2030.json
- nuclear-energy-renaissance.json
- startup-outsmarted-big-ai-labs.json
- the-powerful-alternative-to-fine-tuning-poetic-yc.json
- the-saas-apocalypse-is-here-jerry-murdock.json

---

## Session Documentation (Dependency Chain)

### Iteration Logs
**Path:** `docs/iteration-logs/`

Chain of development:
- Sessions 001-011: Network OS exploration, Notion schema, portfolio model
- Sessions 017, 024-032: Content pipeline v4-v5, artifact alignment, Notion fixes
- Sessions 029-032: Actions Queue, Build Roadmap, skill defense
- Sessions 033-037: Layered persistence, parallel development, subagent context

Each iteration log:
1. References CLAUDE.md + CONTEXT.md rules in effect
2. Documents state changes to Notion (new DBs, schema updates)
3. Creates new checkpoint files
4. Updates artifact versions

---

### Session Checkpoints
**Path:** `docs/session-checkpoints/`

Capture state before/after major changes:
- Pre-refactor state
- Post-milestone state
- Continuation state (multi-session work)

Used by:
- Next session as "pickup" reference
- Behavioral audits (compare expected vs actual state)
- Version control (git history supplement)

---

## External Dependencies

### Python Scripts (data pipeline)
- `scripts/youtube_extractor.py` → requires `yt_dlp` library
- `scripts/process_youtube_queue.py` → reads/writes JSON
- `scripts/publish_digest.py` → git operations, osascript hand-off
- `scripts/content_digest_pdf.py` → PDF generation (unused)
- `scripts/notion_digest_template.py` → legacy template (unused)

### Third-party Services
- **Vercel** — Digest site hosting + auto-deploy from GitHub
- **GitHub** — Git repo + GitHub Actions for CI/CD
- **Notion** — 8 databases + enhanced connector + API

### MCP Tools (Cowork)
- `osascript` — Git push from sandbox to Mac host
- `notion-*` — All Notion operations
- `present_files` — Package and present artifacts
- `API-*` — Raw API calls (mostly broken, avoided)

---

## Dependency Severity

### Critical Path (MUST maintain)
1. CLAUDE.md → Operating rules
2. CONTEXT.md → Master state
3. Build Roadmap DB → Product roadmap
4. Thesis Tracker DB → Thesis sync
5. ai-cos-v6-skill.md → Main capabilities

### High Priority (should maintain)
- All notion-mastery recipes
- Skills (all 4: ai-cos, youtube-content-pipeline, full-cycle, parallel-deep-research)
- Digest site deployment flow

### Medium Priority (nice to maintain)
- Portfolio research files
- Analysis documents
- Stack documentation
- Iteration logs (historical reference)

### Low Priority
- Legacy skill versions (v5, v4, etc.)
- Archived templates
- Unused scripts (PDF generation)

---

## Version Tracking

| Artifact | Current Version | Last Updated | Next Review |
|----------|-----------------|---------------|-------------|
| CLAUDE.md | v6.2.0 | Session 037 | Every session |
| CONTEXT.md | v6.2.0 | Session 037 | Every session |
| ai-cos skill | v6.2.0 | Session 037 | Every 2 sessions |
| notion-mastery skill | v1.2.0 | Session 032 | On-demand |
| youtube-content-pipeline | v5 | Session 027 | On-demand |
| full-cycle | v1 | Session 030 | On-demand |
| parallel-deep-research | v1 | Session 030 | On-demand |
| Layered Persistence | v6 | Session 033 | Every 5 sessions |
| Build Roadmap DB | v1 | Session 031 | Every session |
| Thesis Tracker DB | v1 | Session 013 | Every session |

---

**Last Updated:** Session 037
**Next Audit:** Session 040 (Persistence Audit protocol — every 5 sessions)
