# Prior Art — AI CoS Build History

Chronological record of everything built, discovered, and decided. For future CC sessions to understand what was tried, what works, and what's reusable.

**IMPORTANT:** Reusable items are pointers, not approvals. Always verify with the user before reusing any pattern, code, or approach from this file.

---

## Era 1: Foundation (Sessions 1-11, Mar 1-2 2026)

### Notion DB Schemas (4 databases mapped)
- **What:** Full schema mapping — Network DB (40+ fields, 13 DeVC Relationship archetypes, 2000+ records), Companies DB (49 fields, 20+ pipeline stages, Deal Status 3D matrix, ~150 sector tags, 2000+ records), Portfolio DB (94 fields, reserve modeling, EF/EO/FF classification, 17 views), Finance DB (23 fields, rollup/view only)
- **Status:** Active — IDs in CLAUDE.md, schemas in CONTEXT.md
- **Reusable:** All field names, select values, relation structures. Pipeline funnel stages, Deal Status dimensions, JTBD checklist model. Verify with user before reusing.

### DeVC Scoring Framework (IP Pack)
- **What:** Complete scoring rubrics — Spiky Score (7 criteria), EO Score (10pts/7 dims), FMF Score (10pts/6 dims), Thesis Score (10pts/5+1 dims with Negative=0 gate), Price Score (10pts). Cheque Size Decision Matrix. Fund I retrospective (83 investments).
- **Status:** Active — canonical investment process, rarely filled in Notion (fragmented across channels)
- **Reusable:** All rubrics, cheque matrix, Fund I learnings (Spiky=0 → 37.5% Avoid). Verify with user before reusing.

### IDS Methodology (7 context types)
- **What:** Analyzed 9 training files. 7 IDS types: New Investment, Follow-on, Portfolio Follow-on, Hiring, EF Mining, Seed Deal, BRC-focused. +/++/?/?? notation, conviction spectrum, time-stamped compounding, multi-source triangulation.
- **Status:** Active — core operating methodology for Z47/DeVC
- **Reusable:** Notation system, conviction spectrum, 6 key IDS principles. Companies DB pages = primary IDS repository. Verify with user before reusing.

### 5-Surface Signal Capture Problem
- **What:** 5 capture surfaces (X bookmarks, LinkedIn saves, Medium/YouTube, WhatsApp self-channel, phone screengrabs) with leakage at every transition. 7-8 meetings/day, Granola captures ~10-15%.
- **Status:** Active problem — core AI CoS opportunity
- **Reusable:** Signal flow diagrams, leakage points, volume data. Verify with user before reusing.

### Network OS Reframe
- **What:** AI CoS reframed from productivity tool to "Network Operating System." 1000-2000 active relationships, 11 categories, outbound-first. WS0 with 6 layers.
- **Status:** Superseded by "Action Optimizer" framing — network-centricity preserved
- **Reusable:** Relationship taxonomy, network scale data. Verify with user before reusing.

### Team Shorthand & Key People
- **What:** Z47 GPs: VV, RA, Avi, Cash (Aakash), TD, RBS. DeVC: RM (primary data author), DC. EA: Sneha. MPI=Matrix Partners India (Z47 former brand). User IDs decoded.
- **Status:** Active
- **Reusable:** All abbreviation mappings. Verify with user before reusing.

### Granola Meeting Notes (33 meetings + 100+ archive)
- **What:** Aakash's annotation pattern (Overall: [Verdict] + rationale), real-time scoring for 15+ companies, 30+ deal verdicts, 15+ referral sources, portfolio health metrics.
- **Status:** Active data source (~10-15% meeting coverage)
- **Reusable:** Annotation format, 5 common pass pattern categories, referral sources. Verify with user before reusing.

---

## Era 2: Content Pipeline + Data Sovereignty (Sessions 17-39, Mar 2-5 2026)

### Content Pipeline v4-v5
- **What:** Parallel subagent pipeline: YouTube extraction → Claude analysis → digest JSON → Notion + Actions Queue + Thesis updates. Moved from Mac (v4) to droplet (v5) with yt-dlp extraction, cron, publishing to digest.wiki.
- **Status:** Superseded by v3 persistent agent Postgres-as-queue pipeline
- **Reusable:** Multi-DB write pattern, PDF digest generation, LLM output normalization layer (7-rule field mapping). Verify with user before reusing.

### Actions Queue Architecture
- **What:** Single sink for ALL action types. State machine: Pending → Reviewed → Actions Taken → Skipped. Thesis + Source Digest relations. One-way back-propagation.
- **Status:** Active — Actions Queue DB (1df4858c) live in Notion
- **Reusable:** Single-sink routing, relation-based back-propagation, state machine design. Verify with user before reusing.

### Data Sovereignty (Milestone 2)
- **What:** Public MCP endpoint (mcp.3niac.com), Postgres write-ahead backing (7 tables), bidirectional Notion sync with field-level ownership, change detection engine, SyncAgent on 10-min cron, 17 MCP tools.
- **Status:** Active infrastructure — MCP endpoint + Postgres live. SyncAgent disabled.
- **Reusable:** Write-ahead pattern, field ownership model (Status=droplet, Outcome=Notion), change detection rules. Verify with user before reusing.

### Notion Bulk-Read Pattern (view:// protocol)
- **What:** Only working bulk-read: `notion-fetch` on DB ID → get `view://UUID` → `notion-query-database-view`. All other methods broken.
- **Status:** Active — canonical Notion read pattern
- **Reusable:** Two-step pattern, known view URLs. Verify with user before reusing.

### Build Roadmap DB
- **What:** Self-contained Notion DB (6e1ffb7e). 12-property schema, 7-state emoji kanban, 5 Epics.
- **Status:** Active — daily use
- **Reusable:** Insights-led kanban, emoji-prefixed selects, read/write recipes. Verify with user before reusing.

### Parallel Development Infrastructure
- **What:** File safety classification (Safe/Coordinate/Sequential), 3-layer enforcement, branch_lifecycle.sh, worktree isolation. Subagent context gap discovered: Bash subagents receive ONLY prompt, not CLAUDE.md/skills. 4-block template mitigation.
- **Status:** Active — branch_lifecycle.sh + 4-block subagent protocol in daily use
- **Reusable:** File safety heuristic, subagent protocol (CONSTRAINTS/FILE ALLOWLIST/TASK/SUCCESS CRITERIA). Verify with user before reusing.

### digest.wiki + Vercel Deploy
- **What:** Custom domain live. Git push → Vercel auto-deploy (~15s). Deploy hook as backup.
- **Status:** Active
- **Reusable:** Git push → auto-deploy pattern. Verify with user before reusing.

---

## Era 3: Agent Architecture (Milestone 3 Iterations 1-5, Mar 15 2026)

### Web Tools MCP Server
- **What:** 5 tools (browse, scrape, search, screenshot, task). Firecrawl for search. Systemd on port 8001, Cloudflare Tunnel at web.3niac.com.
- **Status:** Active (restructured in v2.2 with task_store.py + tools.py)
- **Reusable:** Firecrawl-only search, Cloudflare Tunnel config patterns. Verify with user before reusing.

### Cookie Sync Infrastructure
- **What:** cookie-sync.sh: browser_cookie3 extraction → rsync to droplet daily. 5 domains.
- **Status:** Active (daily cron)
- **Reusable:** Mac rsync quirks (no --chmod, needs root@ for Tailscale). Verify with user before reusing.

### SPA Fix (wait_after_ms)
- **What:** networkidle fires before React hydration. Added wait_after_ms (3000ms default). Confirmed 3x.
- **Status:** Active. Readiness ladder (selector > MutationObserver > LCP > framework markers > time) identified as better approach.
- **Reusable:** Time-based delay as stopgap, readiness ladder as target. Verify with user before reusing.

### WebAgent (Standalone, anthropic SDK)
- **What:** Full agent with manual tool loop (not Agent SDK). 8 lib modules, 19 tests, OOM-hardened systemd.
- **Status:** Superseded by v2.2 (Web = MCP, not agent). Code in Archives/mcp-servers-v1/web-agent/
- **Reusable:** Stealth/fingerprint patterns, strategy cache (SQLite UCB bandit), per-tool timeouts, browser reconnect pattern. Verify with user before reusing.

### Three-Agent Architecture v1
- **What:** 3-agent split (Web/Content/Sync), 4-vantage audit (57 findings, 15 themes), monorepo scaffold (63 files, 9,358 lines).
- **Status:** Superseded by v2.2. Monorepo structure + audit themes survived.
- **Reusable:** Audit themes (idempotency, circuit breaker, structured logging, rate limiter, session pool). Verify with user before reusing.

### Deep Research (6 Ultra Reports)
- **What:** Agent SDK fundamentals, multi-agent orchestration, MCP integration, SPA/PWA extraction, agent adaptation (UCB bandit), anti-detection.
- **Status:** Active reference at docs/research/2026-03-15-agent-web-mastery/
- **Reusable:** ClaudeSDKClient for long-lived agents, SDK MCP for in-process tools, strategy cache pattern. Verify with user before reusing.

---

## Era 4: Persistent Agents (Milestone 3 Iterations 6-12, Mar 15-16 2026)

### v2.2 Architecture Redesign
- **What:** CC-parallel principles. Agents get Bash/Read/Write/Skills like CC. Web = MCP not agent. State MCP (5 tools). CAI = async relay via Postgres inbox.
- **Status:** Core principles active. Implementation evolved to v3 persistent agents.
- **Reusable:** CC-as-harness principle, skills-based intelligence, Postgres inbox pattern. Verify with user before reusing.

### v3 Persistent Agents
- **What:** lifecycle.py manages two ClaudeSDKClients. @tool bridge (create_sdk_mcp_server). CLAUDE.md-driven identity (setting_sources=["project"]). Filesystem hooks (matcher group nesting). Traces compaction.
- **Status:** Active — deployed and running
- **Reusable:** lifecycle.py pattern, @tool bridge, CLAUDE.md as agent identity, hook schema. Verify with user before reusing.

### Async @tool Bridge
- **What:** Synchronous bridge blocked orchestrator 10+ min. Fixed: asyncio.create_task + content_busy flag.
- **Status:** Active
- **Reusable:** Fire-and-forget for long-running delegation, busy-flag concurrency guard. Verify with user before reusing.

### Postgres-as-Queue Pipeline
- **What:** content_digests table with status column (queued/processing/published/failed). 3-phase: discover → process → wrap. INSERT ON CONFLICT for dedup. Notion decoupled.
- **Status:** Active
- **Reusable:** Status-column state machine, content-driven inbox routing. Verify with user before reusing.

### Python Pre-Check Cost Optimization
- **What:** Python checks inbox + pipeline timestamp before LLM call. If no work → skip query() entirely. $0 idle heartbeats.
- **Status:** Active — idle heartbeats cost $0
- **Reusable:** Pre-check-before-LLM pattern for any periodic agent. Verify with user before reusing.

### Dead Session Auto-Restart
- **What:** 2 consecutive zero-turn heartbeats → session dead (budget exhausted) → auto-restart with fresh budget.
- **Status:** Active
- **Reusable:** Zero-turn detection pattern for any persistent agent. Verify with user before reusing.

### Deploy SOP (3-Phase)
- **What:** SYNC (rsync + tools + skills) → BOOTSTRAP (idempotent seed) → CLEANUP (remove stale) + RESTART. Static docs separated from runtime state. DROPLET-MANIFEST.md tracks everything.
- **Status:** Active
- **Reusable:** 3-phase deploy pattern, bootstrap.sh idiom, manifest-driven ops. Verify with user before reusing.

### Live Logging (PostToolUse Hooks)
- **What:** Programmatic PostToolUse hooks write tool calls + results to live.log in real-time. AssistantMessage extraction captures ThinkingBlock + TextBlock after each turn.
- **Status:** Active
- **Reusable:** PostToolUse hook for real-time visibility, combined with AssistantMessage parsing. Verify with user before reusing.

### Permission Mode for Headless Agents
- **What:** bypassPermissions blocked as root. acceptEdits still prompts. dontAsk + allowed_tools = correct pattern.
- **Status:** Active
- **Reusable:** dontAsk + explicit allowed_tools for any headless agent on root. Verify with user before reusing.

### Filesystem Hook Schema
- **What:** SDK requires matcher group nesting: `{"hooks": {"Stop": [{"hooks": [{"type": "command", "command": "..."}]}]}}`. Flat structure silently loads 0 matchers.
- **Status:** Active — critical knowledge
- **Reusable:** Always use nested matcher group format. Verify with user before reusing.
