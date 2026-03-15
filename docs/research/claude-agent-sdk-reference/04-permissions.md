# Permissions — Modes, Rules, Callbacks

**Source:** platform.claude.com/docs/en/agent-sdk/permissions, user-input

## Permission Evaluation Order

When Claude requests a tool, the SDK checks in this order:

1. **Deny rules** (`disallowed_tools`) — checked first, always block, override everything including `bypassPermissions`
2. **Allow rules** (`allowed_tools`) — auto-approve listed tools
3. **Permission mode** — fallback behavior for unlisted tools
4. **`can_use_tool` callback** — runtime approval function
5. **Hooks** (`PreToolUse`) — custom code to allow/deny/modify

## Permission Modes

```python
PermissionMode = Literal["default", "acceptEdits", "plan", "bypassPermissions"]
```

| Mode | Behavior | Use Case |
|------|----------|----------|
| `default` | Requires `canUseTool` callback for approval | Interactive apps with custom approval |
| `acceptEdits` | Auto-approves file edits (Write, Edit), prompts for others | Trusted dev workflows |
| `plan` | No tool execution, Claude proposes only | Code review mode |
| `dontAsk` | Auto-denies anything not in `allowed_tools` | **Autonomous headless agents** |
| `bypassPermissions` | All tools run without prompts | Sandboxed CI only, blocked as root |

**For autonomous agents: use `dontAsk` + `allowed_tools`.**

## Allow and Deny Rules

```python
options = ClaudeAgentOptions(
    allowed_tools=["Read", "Grep", "mcp__tools__web_browse"],  # Auto-approved
    disallowed_tools=["Bash(rm -rf *)"],  # Always blocked
)
```

**Critical:** `allowed_tools` is a permission allowlist, NOT a tool restriction. Unlisted tools still exist in Claude's toolset — they fall through to `permission_mode` and `can_use_tool`. To prevent unlisted tools from running, use `permission_mode="dontAsk"`.

### Scoped Rules

Tools can be scoped with patterns:
- `"Bash(npm:*)"` — allow only npm commands via Bash
- `"Edit(/src/**)"` — allow edits only in /src/
- `"Write(/output/**)"` — allow writes only in /output/
- `"Read(./.env*)"` in disallowed — block reading .env files

## can_use_tool Callback

Runtime permission function for dynamic approval:

```python
async def can_use_tool(
    tool_name: str,
    tool_input: dict[str, Any],
    context: ToolPermissionContext
) -> PermissionResultAllow | PermissionResultDeny:
    if tool_name in ["mcp__tools__web_browse", "mcp__tools__web_scrape"]:
        return PermissionResultAllow(updated_input=tool_input)
    return PermissionResultDeny(message=f"{tool_name} not approved")

options = ClaudeAgentOptions(can_use_tool=can_use_tool)
```

## Layered Security Pattern

```python
options = ClaudeAgentOptions(
    # Layer 1: Allowlist
    allowed_tools=["Read", "mcp__tools__web_scrape"],
    # Layer 2: Denylist
    disallowed_tools=["Bash(rm *)"],
    # Layer 3: Permission mode
    permission_mode="dontAsk",
    # Layer 4: Hooks for fine-grained control
    hooks={"PreToolUse": [HookMatcher(matcher="Bash", hooks=[security_check])]},
    # Layer 5: Dynamic callback
    can_use_tool=permission_callback,
)
```

## For Autonomous Agents (No Human in Loop)

The gold standard pattern:

```python
options = ClaudeAgentOptions(
    # Only our custom MCP tools are auto-approved
    allowed_tools=[
        "mcp__web__web_browse",
        "mcp__web__web_scrape",
        "mcp__web__web_search",
        "mcp__web__cookie_status",
    ],
    # Block everything dangerous
    disallowed_tools=["Bash", "Write", "Edit"],
    # Deny anything not explicitly allowed — NO prompts
    permission_mode="dontAsk",
    # Cost guardrails
    max_turns=20,
    max_budget_usd=2.0,
)
```

This ensures:
- Only our custom tools run (via allowed_tools)
- Built-in dangerous tools are blocked (via disallowed_tools)
- Nothing else can sneak through (dontAsk denies all unlisted)
- Cost is bounded (max_turns + max_budget_usd)
