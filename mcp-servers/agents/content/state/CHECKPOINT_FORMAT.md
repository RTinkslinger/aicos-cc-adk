# Checkpoint Format

When you receive COMPACTION REQUIRED, write to `state/content_checkpoint.md`:

```
# Checkpoint — $content | Session #{N} | Iteration {M}
*Written: YYYY-MM-DD HH:MM UTC*

## Current State
- Watch list: {N sources, M active}
- Last pipeline run: {timestamp}

## Recent Analysis Context
- Last content analyzed: {title/source}
- Thesis threads updated this session: {list}
- Actions created this session: {count, highest score}

## Pending Work
- {in-progress subagent tasks}
- {partially processed inbox messages}

## Recent Context (last 5 iterations)
- it {N}: {summary}
- ...

## Key Facts
- {thesis connections discovered this session}
- {watch list changes made}
- {error states or blocked sources}
```

After writing, end response with: **COMPACT_NOW**

## On Session Restart
If `state/content_checkpoint.md` exists:
1. Read it — from your previous session
2. Absorb the state
3. Delete the file
4. Log: `resumed from checkpoint, session #N`
