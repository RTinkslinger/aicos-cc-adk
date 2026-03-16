# CC Skills to ADK Porting — Analysis

## Short Answer

**Yes, Agent SDK has skills. No, they don't work the same way. Porting is partial.**

## The Key Difference

| | Claude Code Skills | Agent SDK Skills |
|---|---|---|
| **Location** | `.claude/skills/` (same) | `.claude/skills/` (same) |
| **Format** | Markdown + YAML frontmatter (same) | Markdown + YAML frontmatter (same) |
| **Triggering** | CC's context-matching system auto-detects when to load | Claude sees the skill descriptions and **decides itself** whether to invoke |
| **Loading** | Progressive — description loaded first, full content on demand | Same — progressive, on-demand |
| **Auto-trigger rules** | Frontmatter `description` is parsed by CC's trigger engine before Claude sees the message | No trigger engine. Claude reads the description and makes a judgment call |

The files are the same format. The **invocation mechanism** is different.

## What Ports Directly

A CC skill file like `a11y-audit/SKILL.md` would **load and work** in an Agent SDK app if:

1. `setting_sources=["project"]` is set (so it reads `.claude/skills/`)
2. `"Skill"` is in the `allowed_tools` list
3. The skill doesn't depend on CC-specific features (hooks, other plugins, slash commands)

The **content** ports. The expertise, the methodology, the domain knowledge — that's just markdown. Claude reads it and applies it regardless of whether it's CC or Agent SDK.

## What Doesn't Port

**Auto-triggering.** CC has a pre-Claude matching system that decides "this message mentions accessibility, load the a11y skill." Agent SDK doesn't have this. Claude has to notice the skill exists (from its description) and decide to use it. This is less reliable — especially for skills with subtle trigger conditions.

**Skill-to-skill orchestration.** In CC, skill A can reference skill B. The superpowers system chains skills (brainstorming → writing-plans → executing-plans). Agent SDK has no equivalent orchestration layer — you'd need to build it in application code.

**Plugin ecosystem.** CC skills can live inside plugins with hooks, MCP servers, commands, and agents. Agent SDK has no plugin system — you'd wire these up programmatically (MCP servers via `mcp_servers` param, hooks via `hooks` param, subagents via `AgentDefinition`).

## If You Wanted CC-Style Auto-Triggering in Agent SDK

You'd build it at the application layer:

```python
# Pseudo-code — application-level trigger matching
@hook("UserPromptSubmit")
def inject_skills(prompt):
    for skill in load_skill_descriptions():
        if skill_matches(prompt, skill.description):
            return {"additionalContext": skill.full_content}
```

This is a `UserPromptSubmit` hook that reads skill descriptions, pattern-matches against the user's prompt, and injects the matching skill content before Claude sees the message. Essentially reimplementing CC's trigger engine.

## Bottom Line

| Question | Answer |
|---|---|
| Can Agent SDK agents have skills? | Yes — same file format, same directory |
| Do they work identically to CC? | No — no auto-trigger engine, Claude decides when to use them |
| Can CC skills be ported? | The files copy over directly. Triggering reliability will drop unless you build a trigger system in application code. |
| Is it worth porting? | For simple knowledge-transfer skills (domain expertise, methodology) — yes, trivial. For skills with complex trigger conditions or CC-specific dependencies (hooks, plugins, commands) — significant rework. |

## Reference

- Agent SDK docs: `/Users/Aakash/Claude Projects/Aakash AI CoS CC ADK/docs/research/claude-agent-sdk-reference/`
- Skills Factory: `/Users/Aakash/Claude Projects/Skills Factory/`
