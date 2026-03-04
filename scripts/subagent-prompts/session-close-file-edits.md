# Template: Session Close File Edits
# Use for: Steps 2 (CONTEXT.md), 3 (CLAUDE.md), 5 (v6-artifacts-index.md) of close checklist
# Fill in {{PLACEHOLDERS}} before sending to subagent

## SUBAGENT CONSTRAINTS (MANDATORY — DO NOT VIOLATE)

You are a Bash subagent running in a Linux VM sandbox. You have:
- ✅ Bash, Read, Edit, Write, Glob, Grep tools
- ❌ NO MCP tools (no osascript, no present_files, no Notion, no web access)
- ❌ NO ability to delete files on mounted folders (rm fails silently or errors)
- ❌ NO outbound network (no curl, wget, git push)
- ❌ NO access to Mac-native paths (/Users/...) — use mounted paths only

CRITICAL RULES:
- Always Read a file BEFORE editing it
- Use `ls` via Bash for directory listings (not Read tool on directories)
- Do NOT attempt file deletion on /sessions/.../mnt/ paths
- Do NOT attempt git operations outside aicos-digests/ subfolder
- If a task requires MCP tools, output "HAND-OFF: [description]" for main session

## WORKING DIRECTORY
/sessions/practical-cool-hopper/mnt/Aakash AI CoS

## ALLOWED FILES (edit ONLY these, nothing else)
1. `CONTEXT.md` — Update header line + add session log entry
2. `CLAUDE.md` — Replace Last Session section only
3. `docs/v6-artifacts-index.md` — Update version numbers + add history row

Do NOT edit any other files.

## SESSION CONTEXT

Session number: {{SESSION_NUMBER}}
Session title: {{SESSION_TITLE}}
Timestamp: {{TIMESTAMP}}
Version bump: {{OLD_VERSION}} → {{NEW_VERSION}}
Defining feature: {{DEFINING_FEATURE}}

### Session summary for CONTEXT.md log entry:
{{CONTEXT_LOG_ENTRY}}

### Last Session replacement block for CLAUDE.md:
{{CLAUDE_MD_LAST_SESSION_BLOCK}}

### Artifacts index changes:
- Header line: "Session {{OLD_SESSION}}" → "Session {{SESSION_NUMBER}}"
- ai-cos version: "{{OLD_VERSION}}" → "{{NEW_VERSION}}"
- Packaged bundle: "ai-cos-{{OLD_VERSION}}.skill" → "ai-cos-{{NEW_VERSION}}.skill"
- Key change line: {{KEY_CHANGE_LINE}}
- CLAUDE.md updated line: "Session {{OLD_SESSION}}" → "Session {{SESSION_NUMBER}}"
- CONTEXT.md updated line: "Session {{OLD_SESSION}}" → "Session {{SESSION_NUMBER}}"
- New version history row: {{VERSION_HISTORY_ROW}}

## EXECUTION ORDER
1. Read CONTEXT.md → find header line and session log section → edit both
2. Read CLAUDE.md → find "## Last Session:" → replace entire section
3. Read docs/v6-artifacts-index.md → apply all version changes

## HAND-OFF TO MAIN SESSION
After completion, main session must handle:
- Step 1b: Notion Build Roadmap insight entries (requires MCP)
- Step 6: present_files on packaged .skill (requires MCP)
- Step 7: Notion Build Roadmap metadata update (requires MCP)
