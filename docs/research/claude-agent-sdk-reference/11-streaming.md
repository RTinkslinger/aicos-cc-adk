# Streaming — Real-Time Responses

**Source:** platform.claude.com/docs/en/agent-sdk/streaming-output

## Enable Streaming

```python
options = ClaudeAgentOptions(
    include_partial_messages=True,  # Enable streaming
    allowed_tools=["Read", "Bash"],
)
```

Yields `StreamEvent` messages with raw API events in addition to usual `AssistantMessage` and `ResultMessage`.

## StreamEvent Type

```python
@dataclass
class StreamEvent:
    uuid: str                        # Unique event ID
    session_id: str                  # Session ID
    event: dict[str, Any]            # Raw Claude API stream event
    parent_tool_use_id: str | None   # Parent if from subagent
```

## Event Types

| Event Type | Description |
|------------|-------------|
| `message_start` | Start of new message |
| `content_block_start` | Start of text or tool_use block |
| `content_block_delta` | Incremental update (text chunks, tool input chunks) |
| `content_block_stop` | End of content block |
| `message_delta` | Message-level updates (stop reason, usage) |
| `message_stop` | End of message |

## Stream Text

```python
from claude_agent_sdk.types import StreamEvent

async for message in query(prompt="Explain databases", options=options):
    if isinstance(message, StreamEvent):
        event = message.event
        if event.get("type") == "content_block_delta":
            delta = event.get("delta", {})
            if delta.get("type") == "text_delta":
                print(delta.get("text", ""), end="", flush=True)
```

## Stream Tool Calls

```python
current_tool = None
tool_input = ""

async for message in query(prompt="Read README.md", options=options):
    if isinstance(message, StreamEvent):
        event = message.event
        if event.get("type") == "content_block_start":
            cb = event.get("content_block", {})
            if cb.get("type") == "tool_use":
                current_tool = cb.get("name")
                tool_input = ""
        elif event.get("type") == "content_block_delta":
            delta = event.get("delta", {})
            if delta.get("type") == "input_json_delta":
                tool_input += delta.get("partial_json", "")
        elif event.get("type") == "content_block_stop":
            if current_tool:
                print(f"Tool {current_tool}: {tool_input}")
                current_tool = None
```

## Message Flow (with streaming)

```
StreamEvent (message_start)
StreamEvent (content_block_start) - text block
StreamEvent (content_block_delta) - text chunks...
StreamEvent (content_block_stop)
StreamEvent (content_block_start) - tool_use block
StreamEvent (content_block_delta) - tool input chunks...
StreamEvent (content_block_stop)
StreamEvent (message_delta)
StreamEvent (message_stop)
AssistantMessage - complete message with all content
... tool executes ...
ResultMessage - final result
```

## Limitations

- **Extended thinking** + streaming: StreamEvent not emitted when `max_thinking_tokens` set
- **Structured output**: JSON result only in final `ResultMessage.structured_output`, not streamed
