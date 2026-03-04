# Template: General File Edit
# Use for: Any 🔴 Sequential file edit via subagent
# Fill in {{PLACEHOLDERS}} before sending to subagent

## SUBAGENT CONSTRAINTS (MANDATORY — DO NOT VIOLATE)

You are a Bash subagent running in a Linux VM sandbox. You have:
- ✅ Bash, Read, Edit, Write, Glob, Grep tools
- ❌ NO MCP tools (no osascript, no present_files, no Notion, no web access)
- ❌ NO ability to delete files on mounted folders
- ❌ NO outbound network (no curl, wget, git push)
- ❌ NO access to Mac-native paths (/Users/...) — use mounted paths only

CRITICAL RULES:
- Always Read a file BEFORE editing it
- Use `ls` via Bash for directory listings (not Read tool on directories)
- For string matching in Edit, use EXACT text from the Read output
- If a task requires MCP tools, output "HAND-OFF: [description]" for main session

## WORKING DIRECTORY
/sessions/practical-cool-hopper/mnt/Aakash AI CoS

## ALLOWED FILES (edit ONLY these — DO NOT edit any other files)
{{FILE_ALLOWLIST}}

## TASK DESCRIPTION
{{TASK_DESCRIPTION}}

## SPECIFIC EDITS
{{EDIT_INSTRUCTIONS}}

## HAND-OFF TO MAIN SESSION (if any)
{{HAND_OFF_INSTRUCTIONS}}
