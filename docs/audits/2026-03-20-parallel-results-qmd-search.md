# Parallel Deep Research Results — QMD Search Audit

**Date:** 2026-03-20
**Scope:** Search all QMD collections and local files for past Parallel MCP deep research results
**Method:** QMD lex+vec searches across conversations, subagent-logs, all-projects; grep across all Claude Projects

---

## Executive Summary

**No 140+ company research results were found.** The actual scope of Parallel-sourced portfolio company research is **20 companies** — the "Fund Priority" set researched during Cowork Session 015 (circa 2026-03-02). Beyond portfolio companies, **15 additional non-portfolio Parallel deep research reports** were found across various projects covering topics like agent SDKs, web mastery, OpenClaw, Supabase, context engineering, CC-CAI sync, and skill development.

**Key finding:** Session 015 ran on **Cowork** (Claude Desktop), not Claude Code. Cowork conversation logs are NOT indexed in QMD, so the original Parallel run IDs for the 20 portfolio companies were never captured in searchable logs. The research outputs were saved as markdown files and are intact.

---

## Section 1: Portfolio Company Research (20 companies)

### Origin
- **Session:** Session 015 — "Actions Queue + Deep Research Enrichment"
- **Surface:** Cowork (Claude Desktop) — NOT Claude Code
- **Date:** ~2026-03-02 (Day 2 of the 39-session build sprint)
- **Outcome:** 20 Fund Priority companies deep-researched, 76 portfolio actions generated, Actions Queue DB created

### Research Files

All 20 files stored at `/Users/Aakash/Claude Projects/Aakash AI CoS CC ADK/portfolio-research/`:

| Company | File | Size |
|---------|------|------|
| Atica | `atica.md` | 13.7 KB |
| Ballisto Agritech | `ballisto-agritech.md` | 12.5 KB |
| Boba Bhai | `boba-bhai.md` | 11.5 KB |
| CodeAnt AI | `codeant-ai.md` | 13.5 KB |
| Confido Health | `confido-health.md` | 14.4 KB |
| Cybrilla | `cybrilla.md` | 17.6 KB |
| Dodo Payments | `dodo-payments.md` | 15.6 KB |
| GameRamp | `gameramp.md` | 12.9 KB |
| Highperformr AI | `highperformr-ai.md` | 15.9 KB |
| Inspecity | `inspecity.md` | 13.1 KB |
| Isler | `isler.md` | 15.6 KB |
| Legend of Toys | `legend-of-toys.md` | 15.3 KB |
| Orange Slice | `orange-slice.md` | 12.6 KB |
| PowerUp | `powerup.md` | 15.3 KB |
| Smallest.ai | `smallest-ai.md` | 13.8 KB |
| Stance Health | `stance-health.md` | 11.2 KB |
| StepSecurity | `step-security.md` | 14.3 KB |
| Terafac | `terafac.md` | 12.6 KB |
| Terractive | `terractive.md` | 14.7 KB |
| Unifize | `unifize.md` | 13.6 KB |

**Total:** 20 files, ~290 KB combined
**Last modified:** 2026-03-09 (all files have same timestamp — likely bulk copy/sync)

### Content Structure (verified from `smallest-ai.md`)

Each file follows a consistent deep research format:
- Executive Summary with Key Strategic Insights
- Company Snapshot (table: founded, HQ, founders, employees, backers, core thesis)
- Product & Technology breakdown
- Target Markets & Use Cases
- Competitive Landscape
- Traction & Metrics
- Funding History
- Risk Assessment
- Team Analysis
- Market Dynamics
- Strategic Opportunities
- Citations (numbered reference format)

### Run IDs

**NOT FOUND.** The Parallel `trun_*` IDs for these 20 portfolio research runs are not preserved in any searchable location. This is because:
1. Session 015 ran on **Cowork** (Claude Desktop sandbox)
2. Cowork session logs are not indexed by QMD
3. The research files themselves don't contain run IDs in their headers (unlike later research outputs that adopted a metadata header convention)

---

## Section 2: Non-Portfolio Parallel Deep Research Reports

These are Parallel `createDeepResearch` results found across all projects, with preserved run IDs.

### Reports with Full Run IDs

| # | Topic | Run ID | Date | Processor | Location |
|---|-------|--------|------|-----------|----------|
| 1 | Unifying CC & Claude.ai | `trun_4719934bf6364778a0cb03bf66411d9d` | 2026-03-12 | ultra | `CC - CAI sync/docs/deep-research-cc-cai-sync.md` |
| 2 | Production Patterns (Agent SDK) | `trun_4719934bf6364778aa54f47886bd8a0f` | 2026-03-15 | — | `docs/research/claude-agent-sdk-reference/13-production-patterns.md` |
| 3 | OpenClaw Architecture | `trun_4719934bf6364778aa2e5ec7a1d3c6fc` | 2026-03-16 | ultra | `docs/research/2026-03-16-openclaw-architecture-ultra.md` |
| 4 | Context Engineering Landscape | `trun_4719934bf6364778897fdacb58f1424c` | ~2026-03-15 | ultra | `Documents/IRGI/docs/0.1 context-engineering-landscape-research.md` |
| 5 | AskUserQuestion Spec-Driven Dev | `trun_4719934bf63647789e01dfaa8f737733` | 2026-03-13 | ultra-fast | `Skills Factory/Interview Cash/docs/deep-research-output-askuserquestion.md` |
| 6 | Supabase Agent Capabilities | `trun_4e978fe567d34864a2ff30ae46574b8b` | 2026-03-19 | — | `docs/research/2026-03-19-supabase-agent-capabilities.json` |
| 7 | Supabase New Keys & Agent Mastery | `trun_4e978fe567d34864ab905a9cd710914a` | 2026-03-19 | — | `docs/research/2026-03-19-supabase-new-keys-and-agent-mastery.json` |

### Reports with Partial (Truncated) Run IDs

These are from the Agent Web Mastery research batch (6 deep research runs, 2026-03-15):

| # | Topic | Partial Run ID | Location |
|---|-------|----------------|----------|
| 8 | Agent SDK Fundamentals | `trun_...ae34733a5c50e8b2` | `docs/research/2026-03-15-agent-web-mastery/01-agent-sdk-fundamentals.md` |
| 9 | Multi-Agent Orchestration | `trun_...b008340c571cb475` | `docs/research/2026-03-15-agent-web-mastery/02-multi-agent-orchestration.md` |
| 10 | Agent MCP Integration | `trun_...8e72da218f93bc21` | `docs/research/2026-03-15-agent-web-mastery/03-agent-mcp-integration.md` |
| 11 | SPA/PWA Content Extraction | `trun_...a26d6a581881fe0d` | `docs/research/2026-03-15-agent-web-mastery/04-spa-pwa-content-extraction.md` |
| 12 | Agent Adaptation & Learning | `trun_...a2f508c1d97ad560` | `docs/research/2026-03-15-agent-web-mastery/05-agent-adaptation-learning.md` |
| 13 | Anti-Detection Stealth | `trun_...92e5e3af722acd83` | `docs/research/2026-03-15-agent-web-mastery/06-anti-detection-stealth.md` |

### Reports Without Run IDs (Parallel origin noted in metadata/context but no trun_ preserved)

| # | Topic | Location |
|---|-------|----------|
| 14 | Frontend UX Deep Research | `Skills Factory/Frontend Skills/claude-code-frontend-ux-deep-research.md` |
| 15 | Hooks Deep Research | `Skills Factory/Hooks Mastery/hooks-deep-research.md` |

---

## Section 3: Parallel Usage in Subagent Logs

The subagent log `agent-acompact-c2d1d664d88053a4` (2026-03-15, 5.1hr session) is the heaviest Parallel user found:
- `createDeepResearch`: 8 calls
- `getResultMarkdown`: 7 calls
- `getStatus`: 2 calls

This matches the Agent Web Mastery batch (6 reports) + Production Patterns (1 report) + likely 1 failed/unretrieved run.

Other notable sessions using Parallel:
- `73775099` (2026-03-17): 2 `createDeepResearch`, 13 `getStatus`, 2 `getResultMarkdown` — parallel workflows guide
- `f8b680bd` (2026-03-15): 7 `getStatus` — likely polling for in-progress research
- Multiple compaction subagents reference Parallel usage in tool counts

---

## Section 4: Coverage Assessment

### What Was Found
- **20 portfolio company research files** — all intact, 11-18 KB each, structured and cited
- **13 non-portfolio research reports** with preserved run IDs (7 full, 6 partial)
- **2 additional reports** without run IDs but with Parallel attribution
- **Total unique Parallel deep research outputs:** ~35 (20 portfolio + 15 non-portfolio)

### What Was NOT Found
- **No evidence of 140+ companies being researched.** The claim of 140+ companies appears to be incorrect. The actual portfolio research scope was exactly 20 Fund Priority companies.
- **No run IDs for the 20 portfolio company research runs.** These were generated in Cowork Session 015 which predates QMD indexing and Claude Code usage for this project.
- **No Cowork session logs in QMD.** Sessions 001-039 (the original 5-day build sprint) were all Cowork sessions. Only the session timeline summary and checkpoint documents survive in the archive.

### Where the "140+ companies" Claim May Originate
The Companies DB has 2,000+ records and the Portfolio DB has ~200 companies. The AI CoS pipeline was designed to eventually expand from 20 Fund Priority to full portfolio coverage (200 companies). The Content Pipeline v5 plan explicitly discusses scaling from 20 to 200 companies. But the Parallel deep research was only ever executed on the initial 20.

---

## Appendix: Unique Run IDs Collected

Full IDs (can be used to query Parallel API):
```
trun_4719934bf6364778a0cb03bf66411d9d  (CC-CAI sync)
trun_4719934bf6364778aa54f47886bd8a0f  (Production patterns)
trun_4719934bf6364778aa2e5ec7a1d3c6fc  (OpenClaw)
trun_4719934bf6364778897fdacb58f1424c  (Context engineering)
trun_4719934bf63647789e01dfaa8f737733  (AskUserQuestion)
trun_4e978fe567d34864a2ff30ae46574b8b  (Supabase agent capabilities)
trun_4e978fe567d34864ab905a9cd710914a  (Supabase keys & agent mastery)
```

Partial IDs (suffix only, would need session logs for full ID):
```
trun_...ae34733a5c50e8b2  (Agent SDK fundamentals)
trun_...b008340c571cb475  (Multi-agent orchestration)
trun_...8e72da218f93bc21  (Agent MCP integration)
trun_...a26d6a581881fe0d  (SPA/PWA extraction)
trun_...a2f508c1d97ad560  (Agent adaptation)
trun_...92e5e3af722acd83  (Anti-detection stealth)
```

Result URLs (for Supabase reports):
```
https://platform.parallel.ai/play/deep-research/trun_4e978fe567d34864a2ff30ae46574b8b
https://platform.parallel.ai/play/deep-research/trun_4e978fe567d34864ab905a9cd710914a
```
