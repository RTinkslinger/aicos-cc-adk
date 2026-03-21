# Persistent Agent SDK Pattern — Definitive Reference

**Source:** Deep research (ultra processor, 2026-03-21). 21 sources including Anthropic official docs.
**Use:** Agent Build Review specialist benchmark. Machine loops reference.

## The Pattern: ClaudeSDKClient = Agent IS Claude Code

The agent runs Claude's autonomous loop INTERNALLY. Python = lifecycle only.

```python
# RIGHT: Python manages lifecycle, Claude reasons autonomously
async with ClaudeSDKClient(options=ClaudeAgentOptions(
    setting_sources=["project"],  # Loads CLAUDE.md + skills
    allowed_tools=["Bash", "Read", "Write", "Edit", "Grep", "Glob", "Agent", "Skill", ...],  # ALL tools
    permission_mode="dontAsk",  # Fully autonomous
)) as client:
    await client.query("Your heartbeat prompt")
    # Claude handles EVERYTHING from here
```

## Agent Has Same Capabilities as Claude Code
- Bash, Read, Write, Edit, Grep, Glob, Agent (subagents), Skills
- Reads CLAUDE.md from cwd via setting_sources=["project"]
- Loads skills from .claude/skills/
- Hooks for lifecycle (PreToolUse, PostToolUse, PreCompact, Stop)
- Built-in compaction + session resume
- Concurrent read-only tool execution
- The agent REASONS about tool chaining — not following scripts

## Tool Permissions
- Main agents (Cindy, Datum, Megamind, ENIAC): ALL tools allowed. No restrictions.
- Subagents: over-tool if anything — enable tools even if "maybe needed"
- permission_mode="dontAsk" for autonomous operation

## CLAUDE.md = Objectives, Not Scripts
- WHO the agent is, WHAT to achieve
- Boundaries and collaboration model
- Anti-patterns
- NOT: step-by-step processing loops

## Skills = Rich Reference
- Tool signatures with WHEN to use
- Patterns of success (suggestive)
- Anti-patterns (what NOT to do)
- Progressive disclosure (<500 lines, link to reference docs)
- Agent loads on demand based on frontmatter matching

## The WRONG Pattern (DO NOT BUILD)
```python
# WRONG: Python tool-loop
while True:
    response = client.messages.create(tools=tool_definitions)
    if response.stop_reason == "tool_use":
        result = execute_tool(response.content)  # Python decides
        messages.append(result)  # Python manages state
```
This disables: concurrent execution, programmatic tool calling (37% token savings), session resumption, compaction.

## Production Primitives
- PreCompact hook → save checkpoint before context wipe
- session_id → persist for resume across restarts
- Subagents via AgentDefinition with specialized (but generous) toolsets
- OpenTelemetry for observability
