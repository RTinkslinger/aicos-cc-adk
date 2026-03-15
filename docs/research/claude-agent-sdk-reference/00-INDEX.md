# Claude Agent SDK — Exhaustive Reference Index

**Source:** Official Anthropic documentation at platform.claude.com/docs/en/agent-sdk/
**SDK Version:** claude-agent-sdk 0.1.48 (Python), CLI 2.1.71
**Date compiled:** 2026-03-15
**Purpose:** Canonical reference for building autonomous agents. MUST be reviewed before any agent code changes.

## Documents

| # | File | Covers | Source Pages |
|---|------|--------|--------------|
| 01 | [architecture.md](01-architecture.md) | Agent loop, message lifecycle, turns, context window, compaction | overview, agent-loop |
| 02 | [query-and-client.md](02-query-and-client.md) | `query()` vs `ClaudeSDKClient`, when to use each, all options | python, quickstart |
| 03 | [custom-tools.md](03-custom-tools.md) | `@tool` decorator, `create_sdk_mcp_server`, in-process MCP, tool schemas | custom-tools |
| 04 | [permissions.md](04-permissions.md) | Permission modes, allowed_tools, disallowed_tools, can_use_tool, evaluation order | permissions |
| 05 | [hooks.md](05-hooks.md) | All hook types, callbacks, matchers, PreToolUse/PostToolUse/Stop patterns | hooks |
| 06 | [hosting-and-deployment.md](06-hosting-and-deployment.md) | Container patterns, systemd, Docker hardening, production architecture | hosting, secure-deployment |
| 07 | [subagents.md](07-subagents.md) | AgentDefinition, programmatic subagents, filesystem agents, parallel execution | subagents |
| 08 | [sessions.md](08-sessions.md) | Resume, fork, continue, session persistence, session IDs | sessions |
| 09 | [mcp-integration.md](09-mcp-integration.md) | External MCP servers, SDK MCP servers, mixed mode, tool naming | mcp |
| 10 | [system-prompts.md](10-system-prompts.md) | CLAUDE.md, output styles, append, custom prompts, settingSources | modifying-system-prompts, claude-code-features |
| 11 | [streaming.md](11-streaming.md) | StreamEvent, partial messages, text streaming, tool call streaming | streaming-output |
| 12 | [advanced.md](12-advanced.md) | Structured outputs, cost tracking, file checkpointing, thinking config, skills, plugins, slash commands, error handling | structured-outputs, cost-tracking, file-checkpointing, skills, plugins, slash-commands |
| 13 | [production-patterns.md](13-production-patterns.md) | Deep research: container architectures, autonomy config, security hardening, cost management, observability, readiness checklist | Parallel deep research + demos repo + third-party guides |

## Key Decisions for Our WebAgent

These are the critical patterns for autonomous agents running in containers:

1. **Permission mode:** `dontAsk` + `allowed_tools` for fully autonomous operation (no human prompts)
2. **Custom tools:** `@tool` decorator + `create_sdk_mcp_server` for in-process tools (zero IPC overhead)
3. **Tool naming:** `mcp__<server_name>__<tool_name>` convention for allowed_tools
4. **Hooks:** `PreToolUse` for guardrails, `PostToolUse` for logging/metrics
5. **System prompt:** Custom string or preset with append — NOT a raw file read
6. **Context management:** `max_turns` + `max_budget_usd` for cost control
7. **query() vs ClaudeSDKClient:** Use `ClaudeSDKClient` when you need hooks or custom tools
8. **Deployment:** Works as root with `dontAsk` mode (verified on our droplet)
