# Production Patterns — Deep Research Report

**Source:** Parallel deep research (trun_4719934bf6364778aa54f47886bd8a0f), 2026-03-15
**References:** Official Anthropic docs, claude-agent-sdk-demos, AWS AgentCore integration, third-party guides

## Key Insight

Deploying the Agent SDK in production requires a shift from treating LLMs as stateless APIs to managing them as **persistent, stateful processes**. The SDK operates as a long-running process that executes commands, manages files, and maintains conversational context.

## Architecture Patterns for Containerized Agents

| Pattern | Best For | State Handling | Examples |
|---------|----------|----------------|----------|
| **Ephemeral Sessions** | One-off tasks | New container per task, destroy on complete | Bug fixes, invoice processing, translation |
| **Long-Running Sessions** | Proactive agents | Persistent container maintaining memory | Email triage, Slack bots, live site builders |
| **Hybrid Sessions** | Intermittent interactions | Ephemeral containers hydrated with history on resume | Project managers, deep research agents |
| **Single Containers** | Collaborating agents | Multiple SDK processes in one container | Multi-agent simulations |

## Autonomy Configuration (No Human in Loop)

Autonomy is a **permissioning problem**, not just a prompting challenge.

| Lever | What it does | Production recommendation |
|-------|-------------|--------------------------|
| `allowed_tools` | Auto-approve listed tools | Whitelist minimum required only |
| `permission_mode` | Fallback for unlisted tools | `dontAsk` for headless agents |
| `can_use_tool` | Runtime approval callback | Validate arguments before execution |
| `disallowed_tools` | Always block listed tools | Block all dangerous operations |

## Security Hardening

1. **Isolation:** Run in sandboxed container (Modal, E2B, Fly Machines, Cloudflare)
2. **Network:** `--network none` + proxy for allowlisted domains
3. **Credentials:** Place outside agent boundary — proxy injects API keys, agent never sees secrets
4. **Sandbox providers recommended by Anthropic:** Modal Sandbox, Cloudflare Sandboxes, Daytona, E2B, Fly Machines, Vercel Sandbox

## Cost Management

| Control | Description |
|---------|-------------|
| `max_budget_usd` | Dollar ceiling per session |
| `max_turns` | Cap on agentic turns (tool-use round trips) |
| `ThinkingConfig` | Control extended thinking with `budget_tokens` |
| `effort` | "low"/"medium"/"high"/"max" — lower = fewer tokens |

## Observability via Hooks

For autonomous agents, hooks provide structured logging:
- **Who:** which agent (via `parent_tool_use_id` linking to subagent)
- **What:** tool name
- **When:** timestamp
- **Input/Output:** tool arguments and results

Emit structured logs (JSONL) from `PostToolUse` hooks for complete audit trail.

## Multi-Agent Orchestration

- **Lead Agent** coordinates workflow, delegates via `Agent` tool
- **Subagents** get scoped tools, isolated context, specific prompts
- Parallel execution: Claude decides when to parallelize based on task
- Track lineage via `parent_tool_use_id` on messages

## Production Readiness Checklist

1. Container running in secure sandbox with restricted network egress
2. `allowed_tools` strictly scoped, credentials via proxy (not in agent env)
3. `max_budget_usd` and `max_turns` explicitly set
4. Hooks emitting structured logs for tool usage and subagent lineage
5. Session management configured (resume/fork for long-running tasks)
6. Context compaction strategy for long sessions
7. Rollback/rewind capability via file checkpointing

## Demo Repos (Reference, Not Production)

| Demo | Extract Patterns | Warning |
|------|-----------------|---------|
| **research-agent** | Multi-agent coordination, subagent tracking, structured output | NOT for production — local dev only |
| **hello-world-v2** | V2 Session API, multi-turn, persistence | Needs sandboxing + IAM + budget controls |

**Source repos:**
- github.com/anthropics/claude-agent-sdk-demos
- github.com/anthropics/claude-agent-sdk-python
