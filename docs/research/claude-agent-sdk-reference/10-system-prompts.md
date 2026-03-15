# System Prompts — CLAUDE.md, Presets, Custom

**Source:** platform.claude.com/docs/en/agent-sdk/modifying-system-prompts, claude-code-features

## Four Methods (in order of recommendation)

### Method 1: CLAUDE.md (Project Instructions)
Persistent, version-controlled, shared via git. Loaded when `setting_sources=["project"]`.

```markdown
# CLAUDE.md
## Code Style
- Use TypeScript strict mode
- Always include docstrings
## Commands
- Build: `npm run build`
- Test: `npm test`
```

```python
options = ClaudeAgentOptions(
    setting_sources=["project"],  # REQUIRED to load CLAUDE.md
    allowed_tools=["Read", "Edit"],
)
```

**CLAUDE.md locations:**
| Level | Location | When loaded |
|-------|----------|-------------|
| Project root | `<cwd>/CLAUDE.md` or `<cwd>/.claude/CLAUDE.md` | `setting_sources` includes `"project"` |
| Project rules | `<cwd>/.claude/rules/*.md` | `setting_sources` includes `"project"` |
| Parent dirs | CLAUDE.md in directories above cwd | `setting_sources` includes `"project"` |
| Child dirs | CLAUDE.md in subdirectories | On demand when agent reads files there |
| Local (gitignored) | `<cwd>/CLAUDE.local.md` | `setting_sources` includes `"local"` |
| User | `~/.claude/CLAUDE.md` | `setting_sources` includes `"user"` |

**IMPORTANT:** The `claude_code` system prompt preset does NOT automatically load CLAUDE.md. You MUST set `setting_sources`.

### Method 2: Preset with Append
Keep Claude Code's built-in prompt + add your instructions:

```python
options = ClaudeAgentOptions(
    system_prompt={
        "type": "preset",
        "preset": "claude_code",
        "append": "Always include docstrings. Use async/await patterns.",
    }
)
```

Preserves: tool usage instructions, safety instructions, code style, environment context.

### Method 3: Custom System Prompt (String)
Replace default entirely:

```python
options = ClaudeAgentOptions(
    system_prompt="You are a web intelligence agent specializing in content extraction."
)
```

**WARNING:** Loses built-in tool instructions, safety instructions, and environment context. Must add these yourself if needed.

### Method 4: Output Styles (Persistent Files)
Saved as markdown files in `~/.claude/output-styles/` or `.claude/output-styles/`. Reusable across sessions.

## Comparison

| Feature | CLAUDE.md | Preset+Append | Custom String | Output Styles |
|---------|-----------|---------------|---------------|---------------|
| Persistence | Per-project file | Session only | Session only | Saved files |
| Default tools | Preserved | Preserved | **Lost** | Preserved |
| Built-in safety | Maintained | Maintained | **Must add** | Maintained |
| Customization | Additions only | Additions only | Complete control | Replace default |
| Version control | With project | With code | With code | Yes |

## For Our WebAgent

Best approach: **Custom system prompt** (Method 3) since we're building a specialized agent with only custom MCP tools (no Claude Code built-in tools needed). The agent doesn't need Read/Write/Edit/Bash — it has web_browse/web_scrape/web_search.

Alternative: **Preset with append** (Method 2) if we want Claude Code's built-in reasoning patterns while adding our web-specific instructions.

## settingSources

Controls which filesystem settings the SDK loads:

| Source | What it loads |
|--------|--------------|
| `"project"` | Project CLAUDE.md, rules, skills, hooks, settings.json |
| `"user"` | User CLAUDE.md, rules, skills, settings |
| `"local"` | CLAUDE.local.md, settings.local.json |

To match full Claude Code CLI behavior: `setting_sources=["user", "project", "local"]`
