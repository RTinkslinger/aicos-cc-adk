# Checkpoint Format

When you receive COMPACTION REQUIRED, write to `state/megamind_checkpoint.md`:

```
# Checkpoint — $megamind | Session #{N} | Iteration {M}
*Written: YYYY-MM-DD HH:MM UTC*

## Current State
- Depth grades assigned this session: {count}
- Cascades processed this session: {count}
- Strategic assessments this session: {count}
- Actions resolved this session: {count}
- Actions generated this session: {count}
- Net action delta this session: {+/- count}
- Daily budget spent: ${amount}

## Convergence Status
- 7-day ratio: {ratio}
- Trend: {converging | stable | diverging}
- Trust level: {manual | semi-auto | auto}

## Recent Depth Grades (last 5)
- id={X}: action_id={Y}, depth={N}, score={S}, status={status}
- ...

## Recent Cascades (last 3)
- id={X}: trigger={type}, net_delta={N}, convergence={PASS/WARN}
- ...

## Pending Work
- {any depth grades awaiting approval}
- {any cascades queued for next assessment}
- {convergence recovery mode active?}

## Recent Context (last 5 iterations)
- it {N}: {summary}
- ...

## Key Facts
- {thesis threads with momentum changes}
- {budget warnings or limits hit}
- {trust level changes}
- {convergence alerts}
```

After writing, end response with: **COMPACT_NOW**

## On Session Restart
If `state/megamind_checkpoint.md` exists:
1. Read it — from your previous session
2. Absorb the state
3. Delete the file
4. Log: `resumed from checkpoint, session #N`
