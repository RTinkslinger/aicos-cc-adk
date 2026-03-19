# Milestone 3: Web Tools MCP + Research + Three-Agent Architecture Foundation
**Iterations:** 1-3 | **Dates:** 2026-03-15

## Summary
Built and deployed the Web Tools MCP server (5 tools, port 8001, Cloudflare Tunnel at web.3niac.com) with cookie sync infrastructure and SPA handling. Conducted deep research (6 ultra reports) on Agent SDK production patterns, multi-agent orchestration, and web intelligence extraction strategies.

## Key Decisions
- Jina Reader as primary scraper (free), Firecrawl as fallback (API key required)
- `wait_after_ms` for SPA empty content (React hydration fires after `networkidle`)
- cloudflared reads /etc/cloudflared/config.yml when running as systemd service
- ClaudeSDKClient (not query()) for long-lived agents
- SDK MCP for in-process tools, external MCP for remote tools
- Kill static waits → readiness ladder: deterministic selector > MutationObserver > LCP > framework markers > time fallback
- Strategy cache + UCB bandit for adaptive site learning

## Iteration Details

### Iteration 1 - 2026-03-15
**Phase:** Web Tools MCP Server — Build & Deploy
**Focus:** Scaffold, build, and deploy web-tools-mcp with 5 tools

**Changes:** `mcp-servers/web-tools-mcp/server.py` (new — 5 tools), `pyproject.toml`, `deploy.sh`, `tests/test_tools.py`, `.mcp.json` (added endpoint), `LEARNINGS.md` (3 patterns)
**Infrastructure:** systemd service on port 8001, Cloudflare Tunnel at web.3niac.com, Google Chrome 146 installed, dpkg /etc/environment fix
**Decisions:**
- Jina search (s.jina.ai) requires API key → removed, Firecrawl-only search
- cloudflared reads /etc/cloudflared/config.yml (not ~/.cloudflared/) when running as systemd service
- /etc/environment had stale `PATH=/root/.deno/bin` breaking all dpkg — fixed

### Iteration 2 - 2026-03-15
**Phase:** Web Tools MCP Server — Cookie Sync + SPA Fix
**Focus:** Cookie pipeline Mac→droplet, fix empty content on JS-heavy SPAs

**Changes:** `server.py` (added `wait_after_ms` param to web_browse), `~/.ai-cos/scripts/cookie-sync.sh` (deployed + fixed rsync flag + root@ prefix + added x.com/substack.com domains), `.mcp.json` (already done iter 1), `LEARNINGS.md` (2 new patterns)
**Infrastructure:** Firecrawl .env configured, browser_cookie3 installed on Mac, daily cron at 6am, /opt/ai-cos/cookies/ on droplet with 5 domain cookie files
**Decisions:**
- SPA empty content root cause: `networkidle` fires before React hydration → added `wait_after_ms=3000` default delay
- macOS rsync lacks `--chmod` flag → removed from cookie-sync.sh
- Tailscale SSH requires explicit `root@` in rsync target

### Iteration 3 - 2026-03-15
**Phase:** Research — Agent SDK + Web Intelligence Mastery
**Focus:** Deep research (6 ultra reports) on Agent SDK production patterns, multi-agent orchestration, MCP integration, SPA/PWA extraction, agent adaptation, and anti-detection

**Changes:** `docs/research/2026-03-15-agent-web-mastery/` (7 new files — index + 6 report summaries)
**Decisions:**
- Architecture clarified: web-tools-mcp = Layer 3 (hands), WebAgent (Agent SDK) = Layer 4 (brain). Agent-as-MCP-tool pattern for cross-surface access.
- ClaudeSDKClient (not query()) for long-lived agents. SDK MCP for in-process tools, external MCP for remote.
- Kill static waits → readiness ladder: deterministic selector > MutationObserver > LCP > framework markers > time fallback
- Strategy cache + UCB bandit for adaptive site learning. MCP Strategy Registry for cross-agent knowledge sharing.
