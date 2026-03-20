# Parallel Deep Research Results — Disk Scan Audit

**Date:** 2026-03-20
**Objective:** Locate 140+ portfolio company deep research results from Parallel MCP on disk

---

## Executive Finding

**Only 20 company research files exist on disk. The remaining 120+ were never saved locally.** The 20 files were generated during Session 015 (March 1, 2026) in Cowork (Claude.ai desktop), which deep-researched "20 Fund Priority companies." There is no evidence that 140+ company research was ever run or saved — the "140+" figure corresponds to the total DeVC fund portfolio size (~140-150 companies per fund cycle), not to research that was actually executed.

---

## Files Found on Disk

### Primary Location: `portfolio-research/` (20 files)
All created 2026-03-09 23:02 (copied from Archives during initial commit `e94123f`).

| # | File | Company | Sector |
|---|------|---------|--------|
| 1 | `atica.md` | Atica (Orbit AgriTech alias) | Hospitality |
| 2 | `ballisto-agritech.md` | Orbit AgriTech / Higher Orbit Agritech | AgriTech |
| 3 | `boba-bhai.md` | Boba Bhai | QSR / F&B |
| 4 | `codeant-ai.md` | Codeant AI | DevSecOps |
| 5 | `confido-health.md` | Confido Health | Healthcare AI |
| 6 | `cybrilla.md` | Cybrilla | Fintech |
| 7 | `dodo-payments.md` | Dodo Payments | Payments |
| 8 | `gameramp.md` | GameRamp | Gaming |
| 9 | `highperformr-ai.md` | HighPerformr AI | Marketing Tech |
| 10 | `inspecity.md` | InspeCity | Spacetech |
| 11 | `isler.md` | Isler | Consumer / Appliances |
| 12 | `legend-of-toys.md` | Legend of Toys | Consumer / Toys |
| 13 | `orange-slice.md` | Orange Slice | B2B SaaS |
| 14 | `powerup.md` | PowerUp | Wealthtech |
| 15 | `smallest-ai.md` | Smallest.ai | Voice AI |
| 16 | `stance-health.md` | Stance Health | Healthcare |
| 17 | `step-security.md` | Step Security | DevSecOps |
| 18 | `terafac.md` | TeraFac | Industrial AI |
| 19 | `terractive.md` | TerrActive | Consumer / Fashion |
| 20 | `unifize.md` | Unifize | Enterprise Software |

### Duplicate Location: Archives (identical copies)
`/Users/Aakash/Claude Projects/Archives/Aakash AI CoS/portfolio-research/` — same 20 files, same timestamps. This is the original source; the current repo's files were copied from here during repo initialization.

### Related File
`/Users/Aakash/Claude Projects/Archives/Aakash AI CoS/portfolio-research-summary.xlsx` — 20-row spreadsheet with structured data (company name, description, sector, HQ, founded year, investment amounts). Not present in current repo (was in initial commit but since removed or gitignored).

---

## How the 20 Files Were Created

**Session 015 — "Actions Queue + Deep Research Enrichment"** (March 1, 2026)
- Surface: Cowork (Claude.ai desktop app)
- Action: Deep-researched 20 Fund Priority companies
- Output: 76 portfolio actions + 20 research markdown files
- Each file is ~11-18 KB of analyst-grade research with citations

The research was done via Cowork's built-in Parallel deep research capability (not Claude Code's `createDeepResearch` MCP tool). Results were written to the Cowork sandbox filesystem and saved to the project directory.

---

## Directories Searched (Exhaustive)

### Searched — No additional research files found
| Directory | Result |
|-----------|--------|
| `/Users/Aakash/Claude Projects/` (all subdirs) | Only the 20 known files + Archives copies |
| `/Users/Aakash/Documents/` | No research files |
| `/Users/Aakash/Downloads/` | No research files |
| `/Users/Aakash/Desktop/` | No research files |
| `/tmp/` and `/private/tmp/` | No research files |
| `/Users/Aakash/.claude/plugins/cache/` | Plugin code only, no results |
| `/Users/Aakash/.claude/agent-memory/` | Unrelated agent memory files |

### Parallel CLI / Config Directories Found
| Directory | Contents |
|-----------|----------|
| `/Users/Aakash/.local/bin/parallel-cli` | Symlink to binary |
| `/Users/Aakash/.local/share/parallel-cli/` | Binary + Python runtime (no results cache) |
| `/Users/Aakash/.parallel-cli/` | `config.json` (auto_update only) + `update-state.json` |
| `/Users/Aakash/.config/parallel-web-tools/` | `credentials.json` only |
| `/Users/Aakash/.claude/plugins/cache/parallel-agent-skills/` | Plugin source code (skills, commands) |
| `/Users/Aakash/.claude/plugins/marketplaces/parallel-agent-skills/` | Plugin source code |

**Key finding:** Neither the Parallel CLI nor the Parallel MCP plugin stores research results locally. Results exist only on the Parallel platform (accessible via `getResultMarkdown` with a task ID) or in the Claude session that created them.

---

## QMD Search Results

Searched across conversations, subagent-logs, and cc-memories collections. No session log references running deep research on more than 20 companies. The only portfolio research session found is Session 015.

---

## Conclusions

1. **20 files exist, not 140+.** The "140+" figure is the total DeVC portfolio size, not the number of companies that were researched.

2. **No results are cached locally by Parallel.** The Parallel CLI and MCP plugin do not maintain a local result store. Research results live on Parallel's servers and are retrieved via `getResultMarkdown` with the task ID from `createDeepResearch`.

3. **To research the remaining ~120+ companies**, new `createDeepResearch` or `createTaskGroup` calls would need to be made. The Parallel MCP tools are available in this Claude Code session.

4. **The xlsx summary file** exists only in Archives (`/Users/Aakash/Claude Projects/Archives/Aakash AI CoS/portfolio-research-summary.xlsx`) and was not carried forward to the current repo.
