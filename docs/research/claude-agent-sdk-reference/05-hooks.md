# Hooks — Lifecycle Interception

**Source:** platform.claude.com/docs/en/agent-sdk/hooks, claude-code-features

## Overview

Hooks are callbacks that fire at specific points in the agent loop. They run in your application process (not inside the agent's context window) so they don't consume context.

**Two types:**
- **Programmatic hooks:** Python callback functions passed to `query()` or `ClaudeSDKClient`
- **Filesystem hooks:** Shell commands in `.claude/settings.json`, loaded via `settingSources`

Both run during the same lifecycle. Filesystem hooks fire in main agent AND subagents. Programmatic hooks are scoped to main session only.

## Hook Events

| Event | When it fires | Common uses |
|-------|--------------|-------------|
| `PreToolUse` | Before a tool executes | Validate inputs, block dangerous commands, modify inputs |
| `PostToolUse` | After a tool returns | Audit outputs, trigger side effects, logging |
| `UserPromptSubmit` | When a prompt is sent | Inject additional context |
| `Stop` | When the agent finishes | Validate result, save session state |
| `SubagentStart` | When a subagent spawns | Track parallel tasks |
| `SubagentStop` | When a subagent completes | Aggregate results |
| `PreCompact` | Before context compaction | Archive full transcript |
| `Notification` | General notifications | Monitoring |
| `PermissionRequest` | When permission is needed | Custom approval UI |

## Hook Callback Signature

```python
async def my_hook(
    input_data: dict[str, Any],     # Hook-specific input (tool_name, tool_input, etc.)
    tool_use_id: str | None,        # ID of the tool call being intercepted
    context: HookContext,           # Session metadata
) -> dict[str, Any]:                # Return {} to allow, or decision dict
    ...
```

## PreToolUse — Block/Allow/Modify

```python
async def security_check(input_data, tool_use_id, context):
    tool_name = input_data["tool_name"]
    tool_input = input_data["tool_input"]

    if tool_name == "Bash" and "rm -rf" in str(tool_input.get("command", "")):
        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": "Dangerous command blocked",
            }
        }

    # Modify input (redirect writes to sandbox)
    if tool_name == "Write":
        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow",
                "updatedInput": {
                    **tool_input,
                    "file_path": f"/sandbox{tool_input.get('file_path', '')}",
                },
            }
        }

    return {}  # Allow (empty dict = proceed)
```

## PostToolUse — Audit/Log

```python
async def log_tool_results(result_data, tool_use_id, context):
    tool_name = result_data.get("tool_name")
    print(f"[AUDIT] {tool_name} completed")
    return {}  # PostToolUse hooks return {} (no decisions)
```

## UserPromptSubmit — Inject Context

```python
async def add_context(input_data, tool_use_id, context):
    from datetime import datetime
    return {
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": f"[Timestamp: {datetime.now().isoformat()}]",
        }
    }
```

## Registering Hooks

```python
from claude_agent_sdk import ClaudeAgentOptions, HookMatcher

options = ClaudeAgentOptions(
    hooks={
        "PreToolUse": [
            HookMatcher(hooks=[security_check]),                    # All tools
            HookMatcher(matcher="Bash", hooks=[bash_validator]),    # Bash only
            HookMatcher(matcher="Write|Edit", hooks=[audit_writes]), # Write or Edit
        ],
        "PostToolUse": [
            HookMatcher(hooks=[log_tool_results]),  # All tools
        ],
        "UserPromptSubmit": [
            HookMatcher(hooks=[add_context]),
        ],
    }
)
```

**Matcher patterns:** regex against tool name. `"Bash"` matches Bash, `"Write|Edit"` matches either, `".*"` matches all.

## When to Use Which Hook Type

| Hook type | Best for |
|-----------|----------|
| **Filesystem** (settings.json) | Sharing between CLI and SDK; supports `command`, `http`, `prompt`, `agent` types; fires in main agent + subagents |
| **Programmatic** (callbacks) | Application-specific logic; structured decisions; in-process; scoped to main session only |

## Key Behaviors

- Hooks run in your process, NOT in Claude's context — no context cost
- A `PreToolUse` hook that rejects a tool prevents execution; Claude receives rejection as tool result
- Returning `{}` (empty dict) = allow the tool to proceed
- Hooks cannot be used to auto-approve tools that `disallowed_tools` blocks
- Multiple hooks on same event all run; any deny = denied
