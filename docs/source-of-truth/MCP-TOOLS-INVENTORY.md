# MCP Tools Inventory
*Last Updated: 2026-03-17*

Tool directory, routing rules, and guardrails for the AI CoS MCP servers.

---

## Access Surfaces

| Surface | Server | Connection |
|---------|--------|-----------|
| **Claude.ai** | State MCP | Remote MCP connector → `https://mcp.3niac.com/mcp` |
| **Claude.ai** | Web Tools MCP | Remote MCP connector → `https://web.3niac.com/mcp` |
| **Claude Code** | State MCP | `.mcp.json` → `http://aicos-droplet:8000/mcp` (Tailscale) |
| **Claude Code** | Web Tools MCP | `.mcp.json` → `http://aicos-droplet:8001/mcp` (Tailscale) |
| **Content Agent** | Both | Bash + psql for Postgres, skills for workflow patterns |

---

## Tool Routing Rules

| Database | Read Tool | Write Tool |
|----------|-----------|------------|
| **Thesis Tracker** | `cos_get_thesis_threads` (State MCP) | `cos_create_thesis_thread`, `cos_update_thesis` (State MCP) |
| **Content Digest** | `cos_get_recent_digests` (State MCP) | Pipeline only (no manual writes) |
| **Actions Queue** | `cos_get_actions` (State MCP) | Notion MCP for status changes (accept/dismiss) |

Use Notion MCP directly for: Companies DB, Network DB, Portfolio DB, Build Roadmap, Tasks Tracker.

**Conviction guardrail:** Never set the `conviction` parameter on thesis tools from Claude Code. Provide evidence and ask Aakash if conviction should change.

---

## State MCP (port 8000)

Lightweight CAI window into system state. 5 tools.

| Tool | Purpose |
|------|---------|
| `health_check` | Server + database connectivity check |
| `get_state` | Read system state: thesis threads, inbox, notifications |
| `create_thesis_thread` | Create new thesis thread (write-ahead: Postgres first, then Notion) |
| `update_thesis` | Update thesis with new evidence (write-ahead) |
| `post_message` | Send message to CAI inbox (async relay to Content Agent) |

---

## Web Tools MCP (port 8001)

Browser automation, scraping, search, and monitoring. 11 tools.

| Tool | Purpose |
|------|---------|
| `health_check` | Server health check |
| `web_scrape` | Extract content from URL (Firecrawl or Playwright fallback) |
| `web_browse` | Navigate and interact with pages via Playwright |
| `web_search` | Web search via Firecrawl |
| `web_task` | Async agent task: submit complex web work, poll for result (CAI pattern) |
| `web_screenshot` | Capture page screenshot |
| `extract_transcript` | Extract transcript from video URL |
| `extract_youtube` | Extract YouTube video metadata + transcript |
| `watch_url` | Monitor URL for changes |
| `cookie_status` | Check cookie freshness for authenticated domains |
| `fingerprint` | Get browser fingerprint details |

---

## External MCPs (via Claude.ai)

| MCP | Purpose |
|-----|---------|
| **Notion Enhanced Connector** | Structured data: fetch, search, create, update, query views |
| **Notion Raw API** | Block-level ops: get/patch block children |
| **Granola** | Meeting transcripts: query, list, get transcript |
| **Google Calendar** | Schedule context: events, free time |
| **Gmail** | Communications: read, search, draft |
| **Vercel** | Deploy: logs, project management |
