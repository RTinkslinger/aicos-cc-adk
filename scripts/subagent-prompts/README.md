# Subagent Prompt Templates

Pre-written prompt templates for common Bash subagent tasks. These templates bake in sandbox restrictions, tool limitations, file allowlists, and hand-off protocols so subagents don't violate documented rules.

## Why These Exist

Bash subagents receive ONLY the prompt text given to them. They do NOT auto-inherit:
- CLAUDE.md or any project context files
- Skills (ai-cos, notion-mastery, etc.)
- MCP tools (osascript, present_files, Notion APIs, Vercel, GitHub)
- Conversation history or prior session context

Without explicit rules in the prompt, subagents use intuitive-but-wrong approaches (e.g., trying `rm` on mounted folders, `git push` from sandbox, `curl` for HTTP requests).

## Subagent Tool Inventory

### Available to Bash subagents:
- `Bash` (command execution)
- `Read` (file reading — NOT directories, use `ls` via Bash)
- `Edit` (file editing — MUST Read first)
- `Write` (file creation)
- `Glob` (file pattern matching)
- `Grep` (content search)

### NOT available to Bash subagents (MCP-only, main session handles):
- `osascript` — Mac host shell commands (git push, file deletion on mounted folders, curl)
- `present_files` — delivering files to user UI
- `Notion tools` — all notion-fetch, notion-create-pages, notion-update-page, API-* endpoints
- `Vercel tools` — deploy, build logs, runtime logs
- `Gmail tools` — search, read, draft
- `Google Calendar tools` — list events, create events
- `Granola tools` — meeting queries, transcripts
- `WebSearch` / `WebFetch` — web access

## Hand-Off Protocol

When a subagent task requires MCP-only operations:
1. Subagent completes all file work it CAN do
2. Subagent outputs clear instructions for what main session must do next
3. Main session picks up MCP tasks (Notion writes, osascript, present_files, etc.)

## Template Usage

Main session should:
1. Check this library for a matching template
2. Read the template
3. Fill in the `{{PLACEHOLDER}}` values
4. Include the filled template as the subagent prompt
5. After subagent completes, execute any hand-off tasks listed

## Templates

| Template | Use Case |
|----------|----------|
| `session-close-file-edits.md` | Steps 2, 3, 5 of close checklist (CONTEXT.md, CLAUDE.md, artifacts index) |
| `skill-packaging.md` | Step 6 — package .skill ZIP, hand off to main for present_files |
| `git-push-deploy.md` | Commit locally, hand off to main for osascript git push |
| `general-file-edit.md` | Any 🔴 file edit with sandbox-aware constraints |

Created: Session 037 (March 4, 2026)
