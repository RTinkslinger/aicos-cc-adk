# Checkpoint
*Written: 2026-03-06 10:30 IST*

## Current Task
Public MCP endpoint buildout (Phase 1 of DATA-SOVEREIGNTY.md) — Cloudflare Tunnel + thesis/digest/actions MCP tools + Claude.ai integration.

## Progress
- [x] Cloudflare Tunnel set up (mcp.3niac.com → droplet:8000, systemd, auto-TLS)
- [x] 5 new MCP tools added: cos_create_thesis_thread, cos_update_thesis, cos_get_thesis_threads, cos_get_recent_digests, cos_get_actions (9 total)
- [x] server.py switched to streamable-http transport
- [x] Claude.ai connected as remote MCP connector (https://mcp.3niac.com/mcp)
- [x] Tested from Claude.ai: cos_get_thesis_threads, cos_get_recent_digests, cos_get_actions confirmed working
- [x] CUSTOM-MCP-SETUP-HTTP.md created (full setup guide)
- [x] DATA-SOVEREIGNTY.md updated (Layer 0, 6-phase plan)
- [x] Claude.ai memory entries updated to v7.1.0 (19 entries, MCP routing + conviction guardrail)
- [x] Memory entries pasted into Claude.ai Settings
- [x] Committed: f547331 (server.py, notion_client.py, DATA-SOVEREIGNTY.md, CUSTOM-MCP-SETUP-HTTP.md, CLAUDE.md, LEARNINGS.md)
- [x] Build Roadmap: QA task created (P1/Planned) for full MCP tool response validation
- [ ] Phase 1 step 1g: Add ai-cos-mcp to Claude Code `.mcp.json` (Tailscale or tunnel endpoint)
- [ ] Phase 1 step 1h: Update CLAUDE.md prompts ("use cos_* tools for thesis, not Notion MCP directly")
- [ ] Full QA of all MCP tool response payloads from Claude.ai (correctness, edge cases)
- [ ] Commit memory-entries.md v7.1.0 + CHANGELOG.md + LEARNINGS.md update

## Key Decisions (not yet persisted)
- **Conviction guardrail**: Claude.ai should never set the `conviction` parameter on thesis tools — must ask Aakash. Persisted in memory-entries.md but not yet in CLAUDE.md.
- **MCP tool routing rule**: Thesis Tracker = all reads+writes via cos_* tools. Content Digest + Actions Queue = reads via cos_* tools, writes still via Notion MCP. Persisted in memory-entries.md #19.
- **Build Roadmap Source field options**: actual values are "Session Insight", "AI CoS Relevance Note", "User Request", "Bug/Regression", "Architecture Decision", "External Inspiration" — logged to LEARNINGS.md but CLAUDE.md recipe not yet updated.
- **No Postgres for thesis yet**: MCP tools are a pass-through routing layer (droplet → Notion API). Phase 2 adds thesis_threads Postgres table with write-ahead pattern.

## Next Steps
1. Commit uncommitted files: `claude-ai-sync/memory-entries.md`, `claude-ai-sync/CHANGELOG.md`, `LEARNINGS.md`
2. Phase 1 step 1g: Add MCP config for Claude Code (`.mcp.json` or project settings)
3. Phase 1 step 1h: Add CLAUDE.md guidance that thesis writes prefer cos_* tools
4. Update CLAUDE.md Build Roadmap recipe with correct Source field options
5. QA all 9 MCP tool responses from Claude.ai (Build Roadmap task exists)

## Context
- Tunnel ID: `a381fcd4-b7fa-4226-8615-a77cfa498d09`
- Domain: `3niac.com` (Cloudflare Registrar), DNS: `mcp.3niac.com`
- Droplet config: `/etc/cloudflared/config.yml`, service: `cloudflared.service`
- MCP endpoint: `https://mcp.3niac.com/mcp` (FastMCP default path)
- TRACES.md: Milestone 2, Iteration 1 already written
- Sprint: 2
- LEARNINGS.md: 3 patterns (emoji select values, Epic options, Source field options)
