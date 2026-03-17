# Handoff: Stop Hook JSON Validation Failures

**From:** ai-cos-cc-adk session (2026-03-13)
**To:** cc-cai-sync project
**Priority:** Normal — affects every session close

---

## Problem

Every session close on ai-cos-cc-adk shows **2 Stop hook errors** reported as **"JSON validation failed"** by Claude Code v2.1.75.

## Analysis Performed

### Hook inventory (Stop event, execution order)

| # | Source | Type | Script/Prompt |
|---|--------|------|---------------|
| 1 | Project `settings.local.json` | prompt | CBS: TRACES.md / LEARNINGS.md / Build Roadmap check |
| 2 | Project `settings.local.json` | prompt | Cross-Sync: update `state.json` semantic fields + write to `inbox.jsonl` via `sync-write.sh` |
| 3 | Project `settings.local.json` | command | `sync-push.sh`: mechanical `state.json` update, status message to `inbox.jsonl`, git commit+push |
| 4 | Global `settings.json` | command | `afplay Hero.aiff` + macOS notification |

User reports 5 hooks, we found 4 in settings. 5th may be internal CC processing or how CC counts prompt-hook-triggered tool calls.

### Command hooks ruled out

Both command hooks (#3, #4) were tested exhaustively:
- Shell profile (`~/.zshrc`): no unconditional echo/printf — clean
- `sync-push.sh`: zero stdout, exit 0 in all scenarios (empty changes, pending changes, dirty tree)
- `afplay` + `osascript` hook: zero stdout, exit 0
- `git commit --quiet` and `git push --quiet`: confirmed zero stdout

**Conclusion: the 2 command hooks are NOT the source of the errors.**

### Prompt hooks are the source

Claude Code docs confirm: when a command exits 0 and stdout contains non-JSON text, CC reports "json validation failed." The prompt hooks (#1, #2) instruct Claude to perform tool calls during Stop. Specifically:

**Hook #2 (Cross-Sync)** tells Claude to:
1. Edit `state.json` semantic fields — Claude can malform the JSON
2. Run `echo '{...}' | sync-write.sh inbox.jsonl` — Claude constructs JSON by hand inside a Bash echo command

`sync-write.sh` validates strictly:
- Required fields: `id`, `source`, `type`, `content` (non-empty strings)
- Type must be one of: `decision|question|answer|task|status|note|research|flag|ack`
- `ack` messages need `context.references` as array

Claude consistently fails at: missing required fields, using invalid types (e.g., `"update"`, `"sync"`), double-escaping issues in Bash echo.

### Root cause

The Cross-Sync prompt hook asked Claude to construct raw JSON inside a Bash `echo` command with no template, no field list, and no valid types reference. Claude had to guess the schema every time.

## Changes Already Made (in ai-cos-cc-adk)

### 1. `sync-pull.sh` line 28: `--rebase` → `--ff-only`

```diff
- git pull --rebase --quiet 2>/dev/null
+ git pull --ff-only --quiet 2>/dev/null
```

**Why:** `git pull --rebase` fails on dirty working trees (modified `.mcp.json`, `CLAUDE.md` are always dirty). Caused `SessionStart:startup hook error`. Also inconsistent with repo's `--ff-only` discipline.

### 2. `sync-push.sh` line 94: `--rebase` → `--ff-only`

```diff
- git pull --rebase --quiet 2>/dev/null
+ git pull --ff-only --quiet 2>/dev/null
```

**Why:** Same issue as above, during Stop sequence.

### 3. Cross-Sync prompt hook — added JSON template

Added explicit template with all required fields and valid types list to the prompt in `settings.local.json`. The old prompt just said `echo '{...}'` with zero schema guidance.

New prompt includes:
```
echo '{"id":"msg_YYYYMMDD_HHMMSS_cc_SLUG","timestamp":"YYYY-MM-DDTHH:MM:SSZ","source":"cc","type":"TYPE","priority":"normal","content":"Your message here","context":{}}' | sync-write.sh inbox.jsonl

Valid types (use ONLY these): decision, question, answer, task, status, note, research, flag, ack
```

## Recommended Further Fix (not yet implemented)

**Move inbox writes entirely into `sync-push.sh`** and remove the Bash echo instruction from the Cross-Sync prompt hook. Rationale:

- `sync-push.sh` already writes status messages to `inbox.jsonl` using `jq` (reliable, never fails validation)
- The prompt hook only needs to update `state.json` semantic fields via Edit (which Claude handles well)
- Eliminates Claude constructing raw JSON in Bash entirely — the fragile part
- The prompt hook would still tell Claude to update `state.json` semantic fields, but inbox writes would be fully automated by the command hook

This requires updating:
1. `sync-push.sh` — read semantic fields from `state.json` to build richer status messages
2. Cross-Sync prompt in `settings.local.json` — remove inbox.jsonl write instructions
3. Possibly `sync-write.sh` — still useful for cross-project writes, but same-project writes move to the command hook

## Files Referenced

All paths relative to ai-cos-cc-adk:
- `.claude/settings.local.json` — hook definitions (Stop, SessionStart, PreToolUse)
- `.claude/hooks/sync-pull.sh` — SessionStart command hook
- `.claude/hooks/sync-push.sh` — Stop command hook
- `.claude/hooks/sync-write.sh` — validated inbox write helper
- `.claude/sync/state.json` — session state (valid JSON, confirmed)
- `.claude/sync/inbox.jsonl` — message inbox (all lines valid, confirmed)
- `~/.claude/settings.json` — global hooks (backup check, notification)
