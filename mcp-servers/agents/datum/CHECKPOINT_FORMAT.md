# Checkpoint Format

When you receive COMPACTION REQUIRED, write to `state/datum_checkpoint.md`:

```
# Checkpoint — $datum | Session #{N} | Iteration {M}
*Written: YYYY-MM-DD HH:MM UTC*

## Current State
- Entities processed this session: {count}
- Records created: {count}
- Records merged: {count}
- Datum requests created: {count}
- Web calls made: {count}

## Recent Processing Context
- Last entity processed: {name/company}
- Pending batch items: {any unprocessed entities from current batch}

## Pending Work
- {in-progress web enrichment}
- {partially processed batch entities}

## Recent Context (last 5 iterations)
- it {N}: {summary}
- ...

## Key Facts
- {dedup decisions made this session}
- {entities that needed user confirmation}
- {error states or blocked enrichment sources}
```

After writing, end response with: **COMPACT_NOW**

## On Session Restart
If `state/datum_checkpoint.md` exists:
1. Read it — from your previous session
2. Absorb the state
3. Delete the file
4. Log: `resumed from checkpoint, session #N`
