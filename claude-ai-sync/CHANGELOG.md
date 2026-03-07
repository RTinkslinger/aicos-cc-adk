# Claude.ai Sync — Changelog

## v7.2.0 — 2026-03-07

**Source-of-truth alignment.** Tool count 9→17, SyncAgent now live, Postgres expanded to 7 tables.

### Memory Entries Changed
| # | Topic | Change |
|---|-------|--------|
| 7 | Build Architecture | UPDATED — 17 MCP tools (was 9), SyncAgent live (10-min cron), Postgres 7 tables |
| 16 | Infrastructure | UPDATED — 7 Postgres tables, SyncAgent cron |

---

## v7.1.0 — 2026-03-06

**MCP tool routing + conviction guardrail.** All thesis/digest/actions operations now route through ai-cos-mcp (mcp.3niac.com) instead of Notion MCP directly. Claude.ai can never set conviction — must ask Aakash.

### Memory Entries Changed
| # | Topic | Change |
|---|-------|--------|
| 7 | Build Architecture | UPDATED — 9 MCP tools, public endpoint via Cloudflare Tunnel |
| 9 | Thesis Management | REWRITTEN — MCP-routed writes, conviction guardrail (never set conviction, ask Aakash) |
| 10 | Research Protocol | UPDATED — use cos_create_thesis_thread instead of Notion direct |
| 12 | Actions Review | UPDATED — use cos_get_actions for reads, Notion for status changes |
| 16 | Infrastructure | UPDATED — Cloudflare Tunnel at mcp.3niac.com |
| 18 | Thesis Protocol | REWRITTEN — MCP routing, conviction guardrail, Connected Buckets options |
| 19 | MCP Tool Routing | NEW — routing rules: which DBs use cos_* tools vs Notion MCP |

---

## v7.0.0 — 2026-03-06

**Major update.** Cowork → Claude Code transition complete. Thesis Tracker redesigned.

### Memory Entries Changed
| # | Topic | Change |
|---|-------|--------|
| 6 | Thesis Tracker | REWRITTEN — AI-managed conviction engine model, new conviction spectrum (New/Evolving/Evolving Fast/Low/Medium/High) |
| 7 | Build Architecture | REWRITTEN — MCP server + ContentAgent live on droplet, Agent SDK era |
| 8 | Feedback Loop | MINOR — added preference store reference |
| 9 | Thesis Management | REWRITTEN — AI creates autonomously, key questions as blocks, no human approval |
| 11 | Content Pipeline | REWRITTEN — autonomous on droplet (cron every 5 min) |
| 14 | Cross-Surface | REWRITTEN — was Notion skill trigger (Cowork), now cross-surface alignment |
| 16 | Infrastructure | REWRITTEN — was Cowork VM rules (obsolete), now droplet infrastructure |
| 17 | Actions Queue | REWRITTEN — was behavioral audit (Cowork), now Actions Queue schema |
| 18 | Thesis Protocol | REWRITTEN — was subagent rules (Cowork), now thesis tracker AI protocol |

### User Preferences Changed
- Removed "load the ai-cos skill" reference (Cowork-era)
- Removed subagent prompt template reference (Cowork-era)
- Added autonomous pipeline reference
- Added Thesis Tracker AI management reference

---

## v6.2.0 — 2026-03-04 (Session 037)

Initial version tracked in this changelog. See `archive/memory-entries-v6.md` for full content.
- 18 entries covering identity, vision, buckets, IDS, people, thesis threads, architecture, feedback loop, research, content pipeline, portfolio review, scoring model, Notion skill trigger, persistence, Cowork rules, behavioral audit, subagent handling
