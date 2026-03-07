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

## Source of Truth (Most Current)

For the most current and accurate build state, see **`docs/source-of-truth/`**:

| File | Covers |
|------|--------|
| `SYSTEM-STATE.md` | Infrastructure, services, endpoints, crons, credentials |
| `MCP-TOOLS-INVENTORY.md` | All 17 MCP tools with full signatures and routing rules |
| `DATA-ARCHITECTURE.md` | 8 Notion DBs + 7 Postgres tables, schemas, sync patterns |
| `ARCHITECTURE.md` | 3-layer architecture, runners, integrations, scoring models |
| `VISION-AND-DIRECTION.md` | Vision, build phases, current vs ideal, gaps |

These are updated after major deploys and milestone compaction. See `docs/source-of-truth/README.md` for the update protocol.

## Architecture Docs Quick Map

| File | Covers | Read when |
|------|--------|-----------|
| `architecture-v0.3.md` | Three-layer architecture (detailed). Some sections have drifted — see source-of-truth for current state. | Deep architectural understanding beyond what SoT covers |
| `vision-v5.md` | Full vision narrative, the "Why", IDS methodology, design principles | Onboarding, framing decisions, understanding Aakash's world |
| `DATA-SOVEREIGNTY.md` | Field-level ownership rules, sync patterns. Build phases now complete (1-4). | Understanding data ownership model |
| `doc2-architecture-v0.2-enhanced.md` | Cowork-era architecture. Postgres schema superseded by `docs/source-of-truth/DATA-ARCHITECTURE.md`. | Historical context only |
| `doc3-vision-document.md` | Cowork-era vision narrative | Historical context — superseded by `vision-v5.md` |
| `BUILD-SYSTEM.md` | Historical Cowork build system | Understanding Cowork-era patterns |
| `engineering-overview-session-040.md` | Cowork engineering overview. Best sections: Content Pipeline data flow, DigestData schema, digest.wiki arch | Rebuilding or extending existing components |
| `doc1-brainstorm-summary-enhanced.md` | Original architecture brainstorm | Historical context only |

Architecture docs and source-of-truth docs are complementary. Architecture docs have depth and narrative. Source-of-truth docs have current state.

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
