# MCP Integration — SDK MCP vs External MCP

**Source:** platform.claude.com/docs/en/agent-sdk/mcp, custom-tools

## Two Types of MCP Servers

### SDK MCP Servers (In-Process)
- Run inside your Python process
- Created with `create_sdk_mcp_server()`
- Tools defined with `@tool` decorator
- Zero IPC overhead
- Best for custom application tools

### External MCP Servers (Subprocess)
- Run as separate processes
- Configured with command + args
- Standard MCP protocol (stdio, SSE, HTTP)
- Best for third-party integrations

## Configuration

```python
options = ClaudeAgentOptions(
    mcp_servers={
        # SDK server (in-process)
        "web": web_tools_server,

        # External server (subprocess, stdio)
        "playwright": {
            "command": "npx",
            "args": ["@playwright/mcp@latest"],
        },

        # External server (HTTP/SSE)
        "remote-api": {
            "type": "http",
            "url": "https://api.example.com/mcp",
        },
    }
)
```

## Tool Naming Convention

All MCP tools follow: `mcp__<server_name>__<tool_name>`

- `server_name` = the key in `mcp_servers` dict
- `tool_name` = the tool's registered name

Examples:
- `mcp__web__web_browse` (SDK server "web", tool "web_browse")
- `mcp__playwright__browser_navigate` (external server "playwright", tool "browser_navigate")

Use this convention in `allowed_tools`:
```python
allowed_tools=["mcp__web__web_browse", "mcp__web__web_scrape"]
```

## MCP Tool Search

For servers with many tools, use tool search to load on-demand instead of preloading all schemas:

```python
# Not yet fully documented for Python SDK
# Concept: only load tool schemas when Claude decides to use them
# Reduces context window cost
```

## Context Cost

Each MCP server adds ALL its tool schemas to every request. Multiple servers with many tools can fill context fast. Strategies:
- Scope subagents to specific MCP servers via `tools` field
- Use tool search for large servers
- Remove servers you don't need per-task
