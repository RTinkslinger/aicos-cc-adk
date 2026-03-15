# Sessions — Resume, Fork, Continue

**Source:** platform.claude.com/docs/en/agent-sdk/sessions

## Session Management

Each `query()` call creates or continues a session. Capture `session_id` from `ResultMessage.session_id` to resume later.

### Capture Session ID

```python
session_id = None
async for message in query(
    prompt="Read the auth module",
    options=ClaudeAgentOptions(allowed_tools=["Read", "Glob"]),
):
    if hasattr(message, "subtype") and message.subtype == "init":
        session_id = message.session_id
```

### Resume a Session

```python
async for message in query(
    prompt="Now find all callers",  # "it" = auth module from previous
    options=ClaudeAgentOptions(resume=session_id),
):
    if hasattr(message, "result"):
        print(message.result)
```

Full context from previous turns is restored: files read, analysis performed, actions taken.

### Fork a Session

Branch into a different approach without modifying the original:

```python
options = ClaudeAgentOptions(
    resume=session_id,
    fork_session=True,  # Creates new session ID, preserves context
)
```

### Continue Conversation

```python
options = ClaudeAgentOptions(continue_conversation=True)  # Continue most recent
```

### ClaudeSDKClient Sessions

```python
async with ClaudeSDKClient(options=options) as client:
    await client.query("Start project")
    async for msg in client.receive_response():
        print(msg)

    # Same session, full context preserved
    await client.query("Add authentication")
    async for msg in client.receive_response():
        print(msg)
```

## Session Persistence

Sessions are persisted to disk by default. Set `persist_session=False` to disable (sessions cannot be resumed later).
