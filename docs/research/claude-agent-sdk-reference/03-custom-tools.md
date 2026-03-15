# Custom Tools — @tool, create_sdk_mcp_server, In-Process MCP

**Source:** platform.claude.com/docs/en/agent-sdk/custom-tools, python README

## Overview

Custom tools extend Claude's capabilities with your own functions via **in-process MCP servers**. They run directly in your Python process — no subprocess spawning, no stdio pipes, no IPC overhead.

## Creating Custom Tools

### @tool Decorator

```python
from claude_agent_sdk import tool, create_sdk_mcp_server, ClaudeAgentOptions

@tool("get_weather", "Get current temperature for coordinates", {"latitude": float, "longitude": float})
async def get_weather(args: dict[str, Any]) -> dict[str, Any]:
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"https://api.open-meteo.com/v1/forecast?latitude={args['latitude']}&longitude={args['longitude']}&current=temperature_2m"
        ) as response:
            data = await response.json()
    return {
        "content": [{"type": "text", "text": f"Temperature: {data['current']['temperature_2m']}"}]
    }
```

**@tool signature:** `@tool(name: str, description: str, schema: dict[str, type])`
- `name`: unique identifier
- `description`: what the tool does (shown to Claude)
- `schema`: argument types as dict (e.g., `{"a": float, "b": float}`)

**Return format:** Must return dict with `"content"` key containing list of content blocks:
```python
{"content": [{"type": "text", "text": "result string"}]}
```

For errors:
```python
{"content": [{"type": "text", "text": "Error: ..."}], "is_error": True}
```

### create_sdk_mcp_server

Bundle tools into an in-process MCP server:

```python
server = create_sdk_mcp_server(
    name="my-tools",
    version="1.0.0",
    tools=[get_weather, another_tool],  # Pass decorated functions
)
```

### Register with ClaudeAgentOptions

```python
options = ClaudeAgentOptions(
    mcp_servers={"tools": server},
    allowed_tools=["mcp__tools__get_weather", "mcp__tools__another_tool"],
)
```

**Tool naming convention:** `mcp__<server_name>__<tool_name>`
- `server_name` = the key in `mcp_servers` dict
- `tool_name` = the name from `@tool` decorator

### Parallel Execution

Custom tools default to sequential. To enable parallel execution:
```python
@tool("read_data", "Read data from source", {"key": str}, read_only_hint=True)
async def read_data(args):
    ...
```

Mark as `read_only_hint=True` to allow concurrent execution with other read-only tools.

## Benefits Over External MCP Servers

- **No subprocess management** — runs in same process
- **Better performance** — no IPC overhead
- **Simpler deployment** — single Python process
- **Easier debugging** — all code in same process, direct stacktraces
- **Type safety** — direct Python function calls with type hints

## Mixed Server Support

Use both SDK and external MCP servers together:

```python
options = ClaudeAgentOptions(
    mcp_servers={
        "internal": sdk_server,        # In-process SDK server
        "external": {                  # External subprocess server
            "type": "stdio",
            "command": "external-server"
        }
    }
)
```

## Migration from External Servers

```python
# BEFORE: External MCP server (separate process)
options = ClaudeAgentOptions(
    mcp_servers={
        "calculator": {
            "type": "stdio",
            "command": "python",
            "args": ["-m", "calculator_server"]
        }
    }
)

# AFTER: SDK MCP server (in-process)
from my_tools import add, subtract
calculator = create_sdk_mcp_server(name="calculator", tools=[add, subtract])
options = ClaudeAgentOptions(mcp_servers={"calculator": calculator})
```

## Important: query() vs ClaudeSDKClient for Custom Tools

The Python SDK README states:
> Unlike `query()`, `ClaudeSDKClient` additionally enables **custom tools** and **hooks**, both of which can be defined as Python functions.

**However**, the official docs show custom tools working with `query()` as well via `mcp_servers` parameter. The key requirement is that custom tools need `ClaudeSDKClient` for **hooks** specifically. For tools-only (no hooks), `query()` works.

Verified pattern:
```python
# Works with query()
async for message in query(
    prompt="What's the weather?",
    options=ClaudeAgentOptions(
        mcp_servers={"tools": server},
        allowed_tools=["mcp__tools__get_weather"],
    ),
):
    ...
```
