# Agent SDK Architecture — Agent Loop, Messages, Context

**Source:** platform.claude.com/docs/en/agent-sdk/overview, agent-loop

## How the Agent Loop Works

The SDK runs the same execution loop that powers Claude Code. When you start an agent:

1. **Receive prompt** — Claude receives your prompt + system prompt + tool definitions + conversation history. SDK yields `SystemMessage` with subtype `"init"` containing session metadata.
2. **Evaluate and respond** — Claude evaluates and may respond with text, request tool calls, or both. SDK yields `AssistantMessage`.
3. **Execute tools** — SDK runs each requested tool and collects results. Each set of tool results feeds back to Claude. Hooks can intercept/modify/block before execution.
4. **Repeat** — Steps 2-3 repeat. Each full cycle = one turn. Continues until Claude produces a response with no tool calls.
5. **Return result** — SDK yields final `AssistantMessage` (no tool calls) then `ResultMessage` with text, token usage, cost, session ID.

## Message Types

Five core types:

| Type | What it carries | When yielded |
|------|----------------|--------------|
| `SystemMessage` | Session metadata, init info | Session start, compaction |
| `AssistantMessage` | Claude's text + tool call requests | Each turn |
| `UserMessage` | Tool results fed back to Claude | After tool execution |
| `ResultMessage` | Final text, usage, cost, session_id | Loop end |
| `StreamEvent` | Raw API streaming events | When partial messages enabled |

### ResultMessage subtypes

| Subtype | Meaning |
|---------|---------|
| `success` | Task completed normally |
| `error_max_turns` | Hit max_turns limit |
| `error_max_budget_usd` | Hit budget limit |
| `error` | General error |

Check `stop_reason` field: `end_turn` (normal), `max_tokens` (output limit), `refusal` (model declined).

## Turns

A turn = one round trip: Claude produces output with tool calls → SDK executes tools → results feed back. Turns continue until Claude produces output with NO tool calls.

Multiple tool calls in a single turn: read-only tools (`Read`, `Glob`, `Grep`, MCP tools marked read-only) run concurrently. State-modifying tools (`Edit`, `Write`, `Bash`) run sequentially.

**Custom tools default to sequential.** To enable parallel: mark as read-only via `readOnlyHint` in Python `@tool` decorator.

## Context Window

Everything accumulates across turns: system prompt, tool definitions, conversation history, tool inputs/outputs.

**What consumes context:**
- System prompt: small fixed cost, always present
- CLAUDE.md files: full content every request (but prompt-cached after first)
- Tool definitions: each tool adds its schema
- Conversation history: grows each turn
- Skill descriptions: short summaries; full content loads on demand

### Automatic Compaction

When context approaches limit, SDK summarizes older history to free space. Emits `SystemMessage` with subtype `"compact_boundary"`. Persistent rules belong in CLAUDE.md (re-injected every request), not initial prompt.

**Customize compaction:**
- Summarization instructions in CLAUDE.md (free-form section telling compactor what to preserve)
- `PreCompact` hook: run custom logic before compaction
- Manual: send `/compact` as prompt string

### Keep Context Efficient
- **Use subagents** for subtasks (fresh context, only summary returns to parent)
- **Be selective with tools** — use `tools` field on AgentDefinition to scope minimum set
- **Watch MCP server costs** — each server adds all tool schemas to every request

## SDK vs Client SDK (raw anthropic API)

```python
# Client SDK: YOU implement the tool loop
response = client.messages.create(...)
while response.stop_reason == "tool_use":
    result = your_tool_executor(response.tool_use)
    response = client.messages.create(tool_result=result, **params)

# Agent SDK: Claude handles tools autonomously
async for message in query(prompt="Fix the bug in auth.py"):
    print(message)
```

The Agent SDK handles: tool execution, context management, retries, compaction, permissions, hooks. You just consume the stream.
