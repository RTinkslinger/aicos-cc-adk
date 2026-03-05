# Repository Navigation & Trust Hierarchy

How to navigate 39+ sessions of prior work and know what's authoritative.

---

## Trust Hierarchy

| Tier | What | How to use |
|------|------|------------|
| **Canon** | `docs/architecture/*.md`, `docs/notion/`, `CLAUDE.md`, `CONTEXT.md`, Notion DBs (live data) | Authoritative. Read before building. Architecture docs are evolving — they represent current thinking, not frozen specs. |
| **Reference** | `docs/architecture/engineering-overview-session-040.md`, `docs/iteration-logs/`, `docs/research/`, `docs/plans/`, `scripts/`, `skills/ai-cos-v6-skill.md`, `portfolio-research/`, `docs/persistence/` | Useful prior art. Check before building something new — the problem may have been explored, partially solved, or intentionally deferred. Don't treat as gospel; approaches may be outdated or Cowork-specific. |
| **Historical** | `docs/vision/v1-v3`, old skill versions (`skills/ai-cos-v2-v5*`), `.skills/skills/notion-mastery/` (superseded by `docs/notion/`), `docs/notion-schema/` (moved to `docs/notion/schemas/`), `docs/session-001-artifacts/`, `FOLDER-INDEX.md`, `cowork-claude-old.md`, `docs/persistence/layered-persistence-coverage.md` | Context for how we got here. Don't build on these — the architecture docs supersede them. |

---

## Architecture Docs Quick Map

| File | Covers | Read when |
|------|--------|-----------|
| `doc2-architecture-v0.2-enhanced.md` | Three-layer system, Agent SDK runners, MCP server, Preference Store, Postgres schema, build phases | Planning any new capability or understanding the target architecture |
| `doc3-vision-document.md` | Full vision narrative, the "Why", IDS methodology, interaction model, design principles | Onboarding, framing decisions, understanding Aakash's world |
| `BUILD-SYSTEM.md` | Historical Cowork build system (sessions, subagents, deployment, audit, persistence) | Understanding how things were built. Reference for patterns that may translate to CC. |
| `engineering-overview-session-040.md` | Full engineering overview of everything built through Session 040 (Cowork era). Content Pipeline data flow, DigestData schema, digest site architecture, Full Cycle DAG pattern | Rebuilding or extending existing components. Best sections: §5 (Content Pipeline), §5.2 (DigestData schema), §6 (digest.wiki), §10 (Full Cycle pattern) |
| `doc1-brainstorm-summary-enhanced.md` | Original architecture brainstorm | Historical context only |

These docs are evolving. When you make architectural decisions during a session, update the relevant doc — don't create new ones.

---

## Prior Art Checklist

Before building anything new, check:

1. **`docs/iteration-logs/`** — grep for the feature/concept. A past session may have built, attempted, or intentionally deferred it.
2. **`docs/research/`** — exploratory research, both successful investigations and dead ends.
3. **`docs/plans/`** — existing specs (e.g., Content Pipeline v5 plan already exists).
4. **`scripts/`** — operational scripts already exist. `action_scorer.py`, `dedup_utils.py`, `publish_digest.py` etc. were built in Cowork but the code is valid.
5. **`skills/ai-cos-v6-skill.md`** — the Cowork skill encodes the full AI CoS persona, scoring models, and Notion operations. Useful as a system prompt reference for Agent SDK runners.
6. **Build Roadmap** (Notion) — query before starting work. An item may already exist, be in progress, or have been intentionally deferred.

**Key principle:** Old work is reference, not requirements. A Cowork-era script might work perfectly in CC. A Cowork-era plan might have the right idea but wrong implementation path. Always evaluate against current architecture docs.

---

## Cowork-Specific Patterns (skip or translate)

These patterns from the Cowork era don't apply in Claude Code:

- **`osascript` MCP bridging** — CC has direct shell access
- **`.skill` ZIP packaging** — CC uses CLAUDE.md + skills/ as .md files
- **`/mnt/` mounted paths** — CC uses native Mac paths
- **6-layer persistence model** — CC uses CLAUDE.md + CONTEXT.md + auto memory
- **Bash subagent constraints** — CC subagents have different tool access
- **`present_files` for user downloads** — CC writes directly
- **Cowork scheduled tasks** — CC uses launchd or cron directly
