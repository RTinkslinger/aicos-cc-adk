# Subagents — AgentDefinition, Parallel Execution

**Source:** platform.claude.com/docs/en/agent-sdk/subagents

## Overview

Subagents are specialized agents with isolated contexts. Each subagent:
- Starts with fresh conversation (no parent message history)
- Loads its own system prompt and project context (CLAUDE.md)
- Only its final response returns to parent as a tool result
- Parent's context grows by summary, not full subtask transcript

## Programmatic Subagents

```python
from claude_agent_sdk import query, ClaudeAgentOptions, AgentDefinition

options = ClaudeAgentOptions(
    agents={
        "code-reviewer": AgentDefinition(
            description="Expert code reviewer for quality and security.",
            prompt="Analyze code quality and suggest improvements.",
            tools=["Read", "Glob", "Grep"],
        ),
        "test-writer": AgentDefinition(
            description="Test automation expert.",
            prompt="Write comprehensive unit and integration tests.",
            tools=["Read", "Write", "Bash"],
        ),
    },
    allowed_tools=["Read", "Glob", "Grep", "Agent"],  # Must include "Agent"
)

async for message in query(
    prompt="Review auth module and write tests for it",
    options=options,
):
    if hasattr(message, "result"):
        print(message.result)
```

**Critical:** Include `"Agent"` in `allowed_tools` — subagents are invoked via the Agent tool.

## AgentDefinition Configuration

```python
@dataclass
class AgentDefinition:
    description: str      # What the agent does (shown to parent Claude)
    prompt: str           # System prompt / instructions for the subagent
    tools: list[str]      # Tool allowlist for the subagent
```

- `tools` scopes the subagent to minimum needed tools
- Each subagent can have different tool sets
- Subagents inherit MCP servers from parent but can be scoped

## Filesystem-Based Subagents

Create `.claude/agents/my-agent.md`:

```markdown
---
name: database-expert
description: Database optimization and query specialist
tools:
  - Read
  - Bash
---

You are a database expert specializing in SQL query optimization,
schema design, performance tuning, and index optimization.
```

Discovered automatically when `setting_sources=["project"]`.

## What Subagents Inherit

- MCP server configurations (but can be scoped via `tools`)
- Project context (CLAUDE.md, if settingSources enabled)
- Permission mode from parent

What they DON'T inherit:
- Parent's conversation history
- Parent's tool results
- Previous turns

## Tracking Subagent Messages

Messages from subagents include `parent_tool_use_id` field, letting you track which messages belong to which subagent execution.

## Parallel Subagent Execution

Claude can invoke multiple subagents. The main agent decides when to parallelize based on task decomposition.

```python
options = ClaudeAgentOptions(
    agents={
        "security-auditor": AgentDefinition(
            description="Security vulnerability scanner",
            prompt="Identify security vulnerabilities and risks",
            tools=["Read", "Grep"],
        ),
        "performance-analyzer": AgentDefinition(
            description="Performance optimization expert",
            prompt="Identify performance bottlenecks",
            tools=["Read", "Grep", "Bash"],
        ),
    }
)
```
