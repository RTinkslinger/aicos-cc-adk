# Claude.ai Sync

This folder contains the current versions of files that need to be manually pasted into Claude.ai Settings.

## How to Update Claude.ai

1. Open Claude.ai → Settings → Memory
2. Delete all existing memory entries
3. Copy the contents of `memory-entries.md` and paste each entry as a separate memory
4. Open Claude.ai → Settings → User Preferences
5. Copy the contents of `user-preferences.md` and paste

## Files

| File | Paste Into | Description |
|------|-----------|-------------|
| `memory-entries.md` | Settings → Memory | 18+ memory entries (one per `## #N` section) |
| `user-preferences.md` | Settings → User Preferences | Identity and interaction prefs |
| `CHANGELOG.md` | — | Version history (don't paste this) |
| `archive/` | — | Previous versions for reference |

## When to Update

Update these files when **architectural changes** happen:
- New infrastructure (servers, databases, integrations)
- New thesis tracker behavior or schema changes
- New runners or agents deployed
- Workflow changes that affect how Claude.ai should behave

The CC session close checklist will prompt: "If architectural changes happened → update `claude-ai-sync/` → tell Aakash to paste."
