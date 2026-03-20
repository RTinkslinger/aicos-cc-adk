# Checkpoint Format

When you receive COMPACTION REQUIRED, write to `state/cindy_checkpoint.md`:

```
# Checkpoint — $cindy | Session #{N} | Iteration {M}
*Written: YYYY-MM-DD HH:MM UTC*

## Current State
- Interactions processed this session: {count}
- People linked: {count} (matched: {n}, new to Datum: {n})
- Action items extracted: {count}
- Thesis signals identified: {count}
- Context gaps created: {count}
- Context gaps filled: {count}

## Surface Activity This Session
- Email: {count} interactions
- WhatsApp: {count} interactions ({n} conversations)
- Granola: {count} transcripts
- Calendar: {count} events scanned

## Recent Processing Context
- Last interaction processed: {source}: {summary}
- Pending batch items: {any unprocessed items from current batch}

## Pending Work
- {in-progress people resolution}
- {partially processed WhatsApp batch}
- {gaps awaiting retroactive fill}

## Recent Context (last 5 iterations)
- it {N}: {summary}
- ...

## Key Facts
- {people resolution decisions this session}
- {cross-surface links established}
- {notable signals routed to Megamind}
- {error states or blocked sources}
```

After writing, end response with: **COMPACT_NOW**

## On Session Restart
If `state/cindy_checkpoint.md` exists:
1. Read it — from your previous session
2. Absorb the state
3. Delete the file
4. Log: `resumed from checkpoint, session #N`
