# Deep Research: Unifying Claude Code and Claude.ai

**Source:** Parallel AI Ultra Research  
**Run ID:** trun_4719934bf6364778a0cb03bf66411d9d  
**Completed:** 2026-03-12  

---

## Executive Summary

As of March 2026, achieving a unified AI development workflow between Claude Code (the local CLI agent) and Claude.ai (the cloud-based chat interface) requires bridging two fundamentally different execution environments. While Anthropic has rapidly advanced both surfaces, they do not natively share a single, synchronized state backend out of the box. However, by combining new native features like Remote Control with the Model Context Protocol (MCP) and Git-based state management, enterprise teams can build highly effective two-way synchronization architectures.

**Key Strategic Insights:**
- **Remote Control collapses the gap for active sessions:** Claude Code's Remote Control feature now allows users to stream a local CLI session directly to claude.ai/code and mobile apps. The conversation stays in sync across devices while execution and filesystem access remain safely on the local machine.
- **Memory is local-first; share intent via the repository:** Claude Code's auto memory is strictly machine-local and is not shared across cloud environments. To synchronize project awareness, teams must treat CLAUDE.md and .claude/rules/ files committed to the Git repository as the portable "contract" between surfaces.
- **MCP is the universal bridge, but transport matters:** Claude.ai's Messages API connects to remote MCP servers to execute tool calls, but it strictly requires HTTP/SSE endpoints and cannot connect directly to local stdio servers.
- **Claude Code can operate as a headless tool farm:** Running `claude mcp serve` exposes Claude Code's internal tools as an MCP server. This allows external orchestrators, CI/CD pipelines, or Claude.ai (via a proxy) to invoke local agentic operations.
- **Git is the de facto shared state bus:** Using GitHub Actions to publish machine-readable state allows Claude.ai to read project status via MCP, while Claude Code modifies it locally.

## 1. Current State of Integration

### Remote Control Unifies Live Sessions
The most direct integration is Remote Control (`claude remote-control`). The web interface acts as a window into the local session — local MCP servers, tools, and the filesystem remain available without moving data to the cloud.

### The Boundaries of Shared Memory and History
Outside of an active Remote Control session, CC and CAI operate independently:
- **Conversation History:** Not shared between independent CC and CAI sessions
- **Auto Memory:** Machine-local at `~/.claude/projects/<project>/memory/`; not shared across machines or cloud
- **Claude Projects:** In CC, "Projects" = local directories with CLAUDE.md. In CAI, Projects = cloud workspaces. To sync, CLAUDE.md must be committed to version control.

## 2. Git-Based Sync Approaches

### The Repository as Source of Truth
Teams are adopting a "spec-first" loop storing state artifacts in the repo root:
- `STATE.json`: Machine-readable current project status
- `TASKS.md`: Human-readable work log and active tickets
- `CLAUDE.md`: Persistent architectural rules and tool bans

### CI/CD Automation with GitHub Actions
The official `anthropics/claude-code-action` allows GitHub to act as an asynchronous bridge. CI pipelines can run tests, generate a new STATE.json, and upload it as an artifact. Claude.ai can then read this via an MCP GitHub server.

### Webhooks and Reliability
For real-time updates, Git providers use webhooks. Systems must use HMAC SHA-256 verification and event ID deduplication.

## 3. MCP as a Context and State Bridge

### Transport Limitations
- Claude Code: connects to both local stdio and remote HTTP/SSE servers
- Claude.ai Messages API: HTTP only, tool calls only, no stdio

### Ready-Made vs. Custom MCP Servers

| Server Type | Purpose | CAI Compatible? |
|---|---|---|
| Official Git/GitHub | Read repos, manage PRs | Yes (HTTP) |
| Filesystem | Secure local file ops | No (stdio only) |
| MCPProxy | Aggregates, converts stdio→HTTP | Yes |
| Custom State Server | Exposes get/set state tools | Yes (if HTTP) |

## 4. Claude's Memory System Across Surfaces

### CLAUDE.md vs. Auto Memory
1. **CLAUDE.md (Shared Contract):** Written by humans, loaded in full every session, supports @path/to/import syntax. Committed to Git = shared between surfaces.
2. **Auto Memory (Local Accelerator):** Written by Claude, first 200 lines loaded. Machine-local only.

### Memory Bridging Strategies
Developers are building custom MCP memory servers with:
- Pre-compact hooks to save critical state
- Semantic search via vector databases exposed as HTTP MCP servers
- Both CC and CAI query the same shared memory bank

## 5. Remote Control and Headless Claude Code

### Claude Code as MCP Server
`claude mcp serve` exposes internal tools (Bash, Read, Write, Edit, LS, GrepTool, GlobTool) via MCP over stdio.

### Invoking CC from CAI
Requires intermediary since CAI can't talk to stdio:
1. Run `claude mcp serve` locally
2. Use adapter (mcp-stdio-to-streamable-http-adapter or MCPProxy)
3. CAI Messages API connects via HTTP tunnel
4. CAI can emit mcp_tool_use targeting CC's tools

### Safety
Requires Docker/gVisor sandboxing, human-in-the-loop gates, MCP_TIMEOUT settings.

## 6. State-of-the-Art Community Solutions

- **MCPProxy:** OAuth 2.1 auth, Docker isolation, dynamic tool discovery
- **Claude Code MCP Bridge:** Pure message ferry from Claude Desktop to CC CLI
- **Claude Thread Continuity:** Persistent memory across sessions
- **ContextForge:** Unified memory imports from Claude Code, ChatGPT, Knowledge Graph
- **ClaudeSync:** One-way file sync to Claude.ai Projects (potential TOS issues)

### Anthropic Roadmap Signals
- Sonnet 4.6: 1M token context, 14.5hr task horizon
- Vercept acquisition: deeper OS-level integrations coming
- MCP list_changed notifications: dynamic tool updates without restart

## 7. Two-Way Sync Reference Architecture

### Event-Driven Design
- **CC to CAI:** Post-commit hook → event bus → state-store microservice → SSE notification to CAI's MCP connection
- **CAI to CC:** MCP tool call → database write → event to bus → CC local proxy receives update → modifies local CLAUDE.md

### Conflict Resolution
Delta State CRDTs allow incremental state changes to be disseminated over unreliable channels and merged locally without conflicts.

## 8. Implementation Blueprint (90 Days)

**Phase 1 (Weeks 1-2):** Standardize CLAUDE.md and .claude/rules/. Implement claude-code-action in GitHub. Adopt remote-control.

**Phase 2 (Weeks 3-6):** Deploy HTTP-based MCP server connected to Git and issue tracker. Configure CAI Messages API mcp_servers array. Implement list_changed notifications.

**Phase 3 (Weeks 7-12):** Run claude mcp serve on secure runner. Front with MCPProxy for HTTPS + OAuth. Build reconciliation job with idempotency keys.

## References

1. Remote Control docs: https://code.claude.com/docs/en/remote-control
2. Claude Code memory: https://code.claude.com/docs/en/memory
3. MCP connector API: https://platform.claude.com/docs/en/agents-and-tools/mcp-connector
4. Claude Code MCP: https://code.claude.com/docs/en/mcp
5. CC as MCP server guide: https://www.ksred.com/claude-code-as-an-mcp-server-an-interesting-capability-worth-understanding/
6. claude-code-action: https://github.com/anthropics/claude-code-action
7. MCP specification: https://modelcontextprotocol.io/docs/getting-started/intro
8. MCPProxy: https://github.com/smart-mcp-proxy/mcpproxy-go
9. Agent SDK: https://platform.claude.com/docs/en/agent-sdk/overview
10. Claude Code headless: https://code.claude.com/docs/en/headless
