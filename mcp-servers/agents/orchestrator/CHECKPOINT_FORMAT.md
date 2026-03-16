# Checkpoint Format

When you receive a COMPACTION REQUIRED message from the UserPromptSubmit hook,
write your checkpoint to `state/orc_checkpoint.md` following this format.

After writing, end your response with the exact word: COMPACT_NOW

## Template

```
# Checkpoint — $orc | Session #{N} | Iteration {M}
*Written: YYYY-MM-DD HH:MM UTC*

## Current State
- Heartbeat interval: 60s
- Active traces file: {path}
- Content Agent status: {session #, last known state}

## Pending Work
- {anything in progress or queued}
- {unprocessed inbox messages}
- {scheduled but not yet triggered tasks}

## Recent Context (last 5 iterations)
- it {N}: {summary}
- it {N-1}: {summary}
- it {N-2}: {summary}
- it {N-3}: {summary}
- it {N-4}: {summary}

## Key Facts to Remember
- {critical state that would be lost without this checkpoint}
- {agent statuses, error states, blocked items}
```

## On Session Restart

When you start a new session and `state/orc_checkpoint.md` exists:
1. Read it fully — this was written by your previous self
2. Absorb the state into your working memory
3. Delete the checkpoint file (it's now in your context)
4. Continue from where you left off
5. Log: 'resumed from checkpoint, session #{N}'
