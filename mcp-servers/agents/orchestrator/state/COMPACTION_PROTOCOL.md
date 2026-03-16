# Traces Compaction Protocol

You (the orchestrator) are responsible for traces file management.

## When to Check
Every 30 heartbeats (iteration % 30 == 0), check the active traces file size:
```
wc -c < "$(cat /opt/agents/traces/active.txt)"
```

## When to Compact
If the active traces file exceeds 20,000 characters:

1. **Summarize:** Read the entire active traces file. Write a 10-20 line summary
   at the TOP of the file under the `## Summary` heading. Include:
   - Date range covered
   - Key events per agent (what happened, what was dispatched)
   - Any errors or notable decisions
   - Leave the raw iteration logs below the summary as-is.

2. **Archive:** Move the current traces file:
   ```
   mv "$(cat /opt/agents/traces/active.txt)" /opt/agents/traces/archive/
   ```

3. **New file:** Create a new traces file and update the pointer:
   ```
   NEW_FILE="traces/$(date -u +%Y%m%d-%H%M).md"
   echo "# Traces — Started $(date -u +%Y-%m-%d\ %H:%M\ UTC)" > "/opt/agents/$NEW_FILE"
   echo "" >> "/opt/agents/$NEW_FILE"
   echo "## Summary" >> "/opt/agents/$NEW_FILE"
   echo "(written on compaction)" >> "/opt/agents/$NEW_FILE"
   echo "" >> "/opt/agents/$NEW_FILE"
   echo "## Iteration Logs" >> "/opt/agents/$NEW_FILE"
   echo "$NEW_FILE" > /opt/agents/traces/active.txt
   ```

4. **Log:** Write your iteration log: `'traces compaction: archived old file, started new traces'`

## Note
You do NOT update the token manifest — Python lifecycle.py handles that.
Traces compaction (this) and session compaction (hooks + lifecycle.py) are separate systems.
