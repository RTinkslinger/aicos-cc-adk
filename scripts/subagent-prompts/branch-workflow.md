# Template: Branch Workflow (Lifecycle CLI Orchestration)
# Use for: Coordinating branch creation, subagent file work, and merge via lifecycle CLI
# This is a MAIN SESSION reference — not a subagent prompt itself
# The lifecycle CLI runs on Mac host via osascript, not inside subagents

## Overview

The lifecycle CLI (`scripts/branch_lifecycle.sh`) handles all git operations via osascript.
Subagents handle file edits only. Main session orchestrates the handoff.

## Pattern A: Single Branch + Subagent

```
# 1. CREATE — main session via osascript
osascript: do shell script "cd '/Users/Aakash/Claude Projects/Aakash AI CoS' && ./scripts/branch_lifecycle.sh create {{BRANCH_NAME}} 2>&1"

# 2. WORK — spawn Bash subagent for file edits (use general-file-edit.md template)
#    Subagent edits files on mounted path, cannot do git operations

# 3. COMMIT — main session via osascript (still on the branch)
osascript: do shell script "cd '/Users/Aakash/Claude Projects/Aakash AI CoS' && git add {{FILES}} && git commit -m '{{MESSAGE}}' 2>&1"

# 4-6. REVIEW + MERGE + CLOSE — main session via osascript
osascript: do shell script "cd '/Users/Aakash/Claude Projects/Aakash AI CoS' && git checkout main && ./scripts/branch_lifecycle.sh full-auto {{BRANCH_NAME}} 2>&1"
```

## Pattern B: Worktree + Parallel Subagents

```
# 1. CREATE WORKTREES — main session via osascript
osascript: do shell script "cd '/Users/Aakash/Claude Projects/Aakash AI CoS' && ./scripts/branch_lifecycle.sh worktree-create {{BRANCH_A}} 2>&1"
osascript: do shell script "cd '/Users/Aakash/Claude Projects/Aakash AI CoS' && ./scripts/branch_lifecycle.sh worktree-create {{BRANCH_B}} 2>&1"

# 2. PARALLEL WORK — spawn multiple Bash subagents, each in their own worktree
#    Subagent A: works in /mnt/Aakash AI CoS/.worktrees/{{SLUG_A}}/
#    Subagent B: works in /mnt/Aakash AI CoS/.worktrees/{{SLUG_B}}/
#    IMPORTANT: Branch slug = branch name with / replaced by - (e.g., feat/my-thing → feat-my-thing)

# 3. COMMIT EACH — main session via osascript
osascript: do shell script "cd '/Users/Aakash/Claude Projects/Aakash AI CoS/.worktrees/{{SLUG_A}}' && git add {{FILES_A}} && git commit -m '{{MESSAGE_A}}' 2>&1"
osascript: do shell script "cd '/Users/Aakash/Claude Projects/Aakash AI CoS/.worktrees/{{SLUG_B}}' && git add {{FILES_B}} && git commit -m '{{MESSAGE_B}}' 2>&1"

# 4-6. CLEAN EACH — main session via osascript (merges + removes worktree + deletes branch)
osascript: do shell script "cd '/Users/Aakash/Claude Projects/Aakash AI CoS' && ./scripts/branch_lifecycle.sh worktree-clean {{BRANCH_A}} 2>&1"
osascript: do shell script "cd '/Users/Aakash/Claude Projects/Aakash AI CoS' && ./scripts/branch_lifecycle.sh worktree-clean {{BRANCH_B}} 2>&1"
```

## Quick Reference: CLI Commands

| Command | Use | Interactive? |
|---------|-----|-------------|
| `create <branch>` | Step 1: Create + checkout branch | No |
| `status` | Show branches + worktrees | No |
| `diff <branch>` | Step 4: Review changes vs main | No |
| `merge <branch>` | Step 5: Merge to main | No |
| `close <branch>` | Step 6: Delete branch | No |
| `full <branch>` | Steps 4-6 with confirmation prompt | Yes — DON'T use via osascript |
| `full-auto <branch>` | Steps 4-6 without prompting | No — USE THIS via osascript |
| `full <branch> --yes` | Same as full-auto | No |
| `worktree-create <branch>` | Create worktree + branch | No |
| `worktree-clean <branch>` | Merge + remove worktree + delete branch | No |
| `worktree-list` | Show active worktrees | No |

## Subagent File Edit Considerations

When spawning subagents for branch/worktree file work:
- Set WORKING DIRECTORY to the worktree path if using worktrees
- File allowlist paths change: `/mnt/Aakash AI CoS/.worktrees/{{SLUG}}/scripts/foo.py`
- Subagent CANNOT run any git commands — all git via main session osascript
- Subagent CANNOT switch branches — it sees whatever branch was checked out

## Notion Build Roadmap Updates

After lifecycle completes, main session updates Notion:
- On create: Status = 🔨 In Progress, Branch = {{BRANCH_NAME}}
- On full-auto/close: Branch = clear, Status = ✅ Shipped

## Branch Naming Convention
- `feat/<feature>` — New feature
- `fix/<bug>` — Bug fix
- `research/<topic>` — Research (always 🟢 Safe)
- `infra/<task>` — Infrastructure
