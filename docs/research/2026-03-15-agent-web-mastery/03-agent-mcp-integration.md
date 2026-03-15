# Ship Reliable Claude Agents on MCP

**Source run:** `trun_...8e72da218f93bc21`
**Date:** 2026-03-15

## Key Concepts

- **SDK MCP in-process (zero IPC)** — `create_sdk_mcp_server` runs MCP tools inside the agent process. No subprocess spawning, no stdio pipes, no network hops. Eliminates the most common source of MCP failures.
- **Agent-as-MCP-tool pattern** — Expose a full Claude agent as a single MCP tool. Callers invoke it like any tool; internally it runs a multi-turn agent loop. Enables composable agent hierarchies.
- **FastMCP lifespan with session_manager.run()** — Use FastMCP's `lifespan` context manager to initialize shared state (DB connections, caches) once at server start. `session_manager.run()` handles per-session lifecycle.
- **mcp__{server}__{tool} namespacing** — Claude Code's convention for disambiguating tools across multiple MCP servers. Format: `mcp__<server_name>__<tool_name>`. Prevents collisions when agents connect to many servers.
- **5-layer stack** — Agent SDK > MCP Client > Transport (stdio/SSE/Streamable HTTP) > MCP Server > Tool implementations. Understanding which layer failed is critical for debugging.
- **OAuth 2.1 JWTVerifier** — MCP's auth story for remote servers. Verify JWTs on each request; no session cookies. Supports PKCE for public clients (CLI tools, agents).
- **Programmatic tool calling (98.7% token cut)** — Call tools directly from code instead of routing through the LLM. For deterministic workflows (fetch > parse > store), skip the model entirely. Massive cost reduction.
- **Streamable HTTP 7.5ms** — The newest MCP transport. Single HTTP endpoint, supports both request-response and streaming. 7.5ms median latency vs 15ms for SSE. Replaces the deprecated SSE transport.
- **Hub-and-Spoke topology** — One orchestrator agent connects to N MCP servers. Each server owns a domain (Notion, Gmail, browser). The hub routes tasks; spokes execute. Simpler than mesh topologies.

## Top 5 References

1. MCP specification (Streamable HTTP) — `spec.modelcontextprotocol.io/specification/basic/transports`
2. FastMCP documentation — `github.com/jlowin/fastmcp`
3. Anthropic Agent SDK MCP integration — `anthropic.com/docs/agent-sdk/mcp`
4. OAuth 2.1 for MCP — `spec.modelcontextprotocol.io/specification/basic/authorization`
5. Claude Code MCP architecture — `github.com/anthropics/claude-code`
