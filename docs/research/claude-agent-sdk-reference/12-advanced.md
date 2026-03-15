# Advanced Features — Outputs, Cost, Checkpointing, Skills, Plugins, Errors

**Source:** platform.claude.com/docs/en/agent-sdk/ (structured-outputs, cost-tracking, file-checkpointing, skills, plugins, slash-commands, python)

## Structured Outputs

Force JSON schema on agent output:

```python
options = ClaudeAgentOptions(
    output_format={
        "type": "json_schema",
        "schema": {
            "type": "object",
            "properties": {
                "summary": {"type": "string"},
                "score": {"type": "number"},
            },
            "required": ["summary", "score"],
        },
    }
)
```

Result available in `ResultMessage.structured_output`. NOT streamed — only in final message.

## Cost Tracking

```python
async for message in query(prompt="...", options=options):
    if isinstance(message, ResultMessage):
        print(f"Cost: ${message.cost_usd}")
        print(f"Tokens: {message.total_input_tokens} in, {message.total_output_tokens} out")
        print(f"Turns: {message.num_turns}")
```

Budget guardrails:
```python
options = ClaudeAgentOptions(
    max_budget_usd=2.0,  # Dollar ceiling
    max_turns=20,         # Turn limit
)
```

When exceeded: `ResultMessage` with subtype `error_max_budget_usd` or `error_max_turns`.

## File Checkpointing

Track and rewind file changes:

```python
options = ClaudeAgentOptions(enable_file_checkpointing=True)

# After task, rewind changes if needed
async with ClaudeSDKClient(options=options) as client:
    await client.query("Refactor auth module")
    # ... review result ...
    await client.rewind_files()  # Undo all file changes
```

## Effort Level

Controls reasoning depth per turn:

```python
options = ClaudeAgentOptions(effort="medium")  # "low"|"medium"|"high"|"max"
```

Lower effort = fewer tokens = lower cost. Use "low" for simple tasks (file listing, grep). Default: unset in Python (model default), "high" in TypeScript.

## Thinking Configuration

```python
# Adaptive thinking (auto-determines depth)
options = ClaudeAgentOptions(thinking={"type": "adaptive"})

# Fixed budget
options = ClaudeAgentOptions(thinking={"type": "enabled", "budget_tokens": 16000})

# Disabled
options = ClaudeAgentOptions(thinking={"type": "disabled"})
```

**Note:** Extended thinking + streaming are incompatible. StreamEvents not emitted when thinking is enabled.

## Skills

Filesystem markdown files in `.claude/skills/` loaded on demand:

```python
options = ClaudeAgentOptions(
    setting_sources=["project"],           # Discover skills
    allowed_tools=["Skill", "Read"],       # Must include "Skill"
)
```

Skills are model-invoked (Claude decides when to use based on context), progressive (load on demand), and composable.

**Skills vs Subagents vs Custom Tools:**

| Feature | Skills | Subagents | Custom Tools |
|---------|--------|-----------|--------------|
| Definition | Filesystem (.claude/skills/) | Filesystem or programmatic | Programmatic only |
| Invocation | Claude decides based on context | Claude decides based on task | Claude calls as function |
| Content | Instructions + resources | Agent personality + prompt | Executable code |
| Loading | Progressive (on-demand) | Full context | Runtime registration |
| SDK Config | `setting_sources=["project"]` | `agents={}` dict | `mcp_servers={}` dict |

## Plugins

Load Claude Code plugins programmatically:

```python
options = ClaudeAgentOptions(
    plugins=[
        {"type": "local", "path": "./my-plugin"},
        {"type": "local", "path": "/absolute/path/to/plugin"},
    ]
)
```

Plugin directory requires `.claude-plugin/plugin.json` manifest. Can include skills, commands, agents, hooks, MCP servers.

## Slash Commands

Send slash commands as prompt strings:

```python
# Compact context
async for msg in query(prompt="/compact", options=options):
    pass

# Clear history
async for msg in query(prompt="/clear", options=options):
    pass
```

Available commands listed in `SystemMessage` with subtype `"init"`.

## Error Handling

```python
from claude_agent_sdk import (
    ClaudeSDKError,       # Base error
    CLINotFoundError,     # CLI not installed
    CLIConnectionError,   # Connection issues
    ProcessError,         # Process failed (has exit_code)
    CLIJSONDecodeError,   # JSON parsing issues
)

try:
    async for message in query(prompt="Hello"):
        pass
except CLINotFoundError:
    print("CLI not found")
except ProcessError as e:
    print(f"Process failed: exit code {e.exit_code}")
except CLIJSONDecodeError as e:
    print(f"JSON parse error: {e}")
```

## Model Selection

```python
options = ClaudeAgentOptions(
    model="claude-sonnet-4-6",           # Primary model
    fallback_model="claude-haiku-4-5",   # Fallback if primary fails
)
```

If not set, SDK uses Claude Code's default (depends on auth method and subscription).

## Environment Variables

```python
options = ClaudeAgentOptions(
    env={"CUSTOM_VAR": "value"},  # Additional env vars
    cwd="/opt/web-agent",         # Working directory
)
```

The `ANTHROPIC_API_KEY` must be in the process environment (or set via `env` dict).

## Sandbox Settings

```python
options = ClaudeAgentOptions(
    sandbox=SandboxSettings(
        # Configure sandbox behavior programmatically
        # See TypeScript SDK reference for full SandboxSettings type
    )
)
```
