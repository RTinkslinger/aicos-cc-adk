# Building Production-Grade Claude Agents on Headless Linux

**Source run:** `trun_...ae34733a5c50e8b2`
**Date:** 2026-03-15

## Key Concepts

- **ClaudeSDKClient vs query()** — `ClaudeSDKClient` manages full agent lifecycle (sessions, tool registration, context); `query()` is the stateless single-shot API for simple prompts without session management.
- **@tool decorator** — Registers Python functions as agent-callable tools with automatic schema generation from type hints and docstrings.
- **create_sdk_mcp_server** — Wraps an existing MCP server for in-process use by the SDK, eliminating IPC overhead while preserving the MCP tool interface.
- **AgentDefinition subagents** — Define child agents with scoped tool access and system prompts; the parent orchestrates delegation without sharing full context.
- **PreToolUse / PostToolUse hooks** — Intercept tool calls for validation, logging, rate limiting, or result transformation before/after execution.
- **max_turns / max_budget_usd** — Hard guardrails on agent execution. `max_turns` caps tool-call loops; `max_budget_usd` sets a dollar ceiling on token spend per run.
- **systemd with CPUQuota / MemoryMax** — Production deployment pattern: run agents as systemd services with resource cgroups to prevent runaway processes on shared infrastructure.
- **Session resume via session_id** — Pass a prior `session_id` to resume conversation state, enabling multi-step workflows across process restarts.
- **compact_boundary for context compaction** — Marks a point in the conversation where earlier context can be summarized, keeping the agent within context limits on long-running tasks.

## Top 5 References

1. Anthropic Agent SDK documentation — `anthropic.com/docs/agent-sdk`
2. Claude Code architecture (open-source reference) — `github.com/anthropics/claude-code`
3. systemd resource control — `systemd.io/RESOURCE_CONTROL/`
4. MCP specification — `modelcontextprotocol.io/specification`
5. Anthropic cookbook: production agents — `github.com/anthropics/anthropic-cookbook`
