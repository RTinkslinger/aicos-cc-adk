# query() vs ClaudeSDKClient

**Source:** platform.claude.com/docs/en/agent-sdk/python, quickstart

## Choosing Between Them

| Feature | `query()` | `ClaudeSDKClient` |
|---------|-----------|-------------------|
| Session | Creates new each time | Reuses same session |
| Conversation | Single exchange | Multiple exchanges in context |
| Connection | Managed automatically | Manual control |
| Hooks | Supported (SDK 0.1.x+) | Supported |
| Custom Tools | Supported | Supported |
| Interrupts | Not supported | Supported via `interrupt()` |
| Continue Chat | New session each time | Maintains conversation |
| Use Case | One-off tasks | Continuous conversations |

**When to use `query()`:**
- One-off tasks that don't need conversation history
- Independent tasks without cross-exchange context
- Simple automation scripts
- When you want a fresh start each time

**When to use `ClaudeSDKClient`:**
- Continuing conversations with context
- Follow-up questions building on previous responses
- Interactive applications, chat interfaces
- Session control and lifecycle management
- Response-driven logic (next action depends on Claude's response)

## query() Usage

```python
import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, TextBlock, ResultMessage

async def main():
    async for message in query(
        prompt="Find and fix bugs in auth.py",
        options=ClaudeAgentOptions(
            allowed_tools=["Read", "Edit", "Glob"],
            permission_mode="acceptEdits",
            system_prompt="You are a senior Python developer.",
            max_turns=10,
            max_budget_usd=1.0,
        ),
    ):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(block.text)
        elif isinstance(message, ResultMessage):
            print(f"Done: {message.subtype}")

asyncio.run(main())
```

## ClaudeSDKClient Usage

```python
import asyncio
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, AssistantMessage, TextBlock

async def main():
    options = ClaudeAgentOptions(
        system_prompt="You are a helpful assistant",
        max_turns=5,
    )

    async with ClaudeSDKClient(options=options) as client:
        # First query
        await client.query("Read the auth module")
        async for msg in client.receive_response():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        print(block.text)

        # Follow-up in same context
        await client.query("Now find all callers")
        async for msg in client.receive_response():
            pass  # Process response

asyncio.run(main())
```

## ClaudeAgentOptions — All Fields

```python
@dataclass
class ClaudeAgentOptions:
    tools: list[str] | ToolsPreset | None = None
    allowed_tools: list[str] = field(default_factory=list)
    disallowed_tools: list[str] = field(default_factory=list)
    system_prompt: str | SystemPromptPreset | None = None
    permission_mode: PermissionMode | None = None  # "default"|"acceptEdits"|"plan"|"bypassPermissions"
    model: str | None = None
    fallback_model: str | None = None
    max_turns: int | None = None
    max_budget_usd: float | None = None
    cwd: str | Path | None = None
    mcp_servers: dict[str, McpServerConfig] | str | Path = field(default_factory=dict)
    hooks: dict[HookEvent, list[HookMatcher]] | None = None
    agents: dict[str, AgentDefinition] | None = None
    can_use_tool: CanUseTool | None = None
    env: dict[str, str] = field(default_factory=dict)
    add_dirs: list[str | Path] = field(default_factory=list)
    setting_sources: list[SettingSource] | None = None  # ["user", "project", "local"]
    sandbox: SandboxSettings | None = None
    plugins: list[SdkPluginConfig] = field(default_factory=list)
    thinking: ThinkingConfig | None = None
    effort: Literal["low", "medium", "high", "max"] | None = None
    include_partial_messages: bool = False
    fork_session: bool = False
    resume: str | None = None
    continue_conversation: bool = False
    user: str | None = None
    betas: list[SdkBeta] = field(default_factory=list)
    output_format: dict[str, Any] | None = None
    cli_path: str | Path | None = None
    enable_file_checkpointing: bool = False
    # Deprecated
    max_thinking_tokens: int | None = None
    max_buffer_size: int | None = None
```

### Key Notes
- `allowed_tools` is a **permission allowlist**, NOT a tool restriction. Unlisted tools still exist — they fall through to `permission_mode` and `can_use_tool`.
- To **block** tools, use `disallowed_tools`. Deny rules checked first, override everything including `bypassPermissions`.
- `setting_sources` must include `"project"` to load CLAUDE.md files.
- If `tools` is not set, agent has access to full Claude Code toolset.
