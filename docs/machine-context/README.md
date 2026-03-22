# Machine Context Files

Each machine has a persistent context file that accumulates across loops. This is the machine's MEMORY — what it learned, what worked, what failed, what the product leadership agent decided.

## Structure

Each `M{N}.md` file contains:

```markdown
## Product Vision Context
What this machine's component contributes to Aakash's "What's Next?" system.
How it connects to other components. What the user cares about most.

## Accumulated Decisions
Decisions made by product leadership agents across loops. Why they were made.
What was tried and rejected. What patterns work.

## Patterns of Success
What approaches worked well in previous loops. Reuse these.

## Anti-Patterns (Learned)
What was tried and failed. Don't repeat these.

## Cross-Machine Context
What other machines' outputs affect this machine. What this machine
produces that others depend on. Current state of dependencies.

## Current Focus
What the product leadership agent determined is the highest-impact
work for the next loop. Updated at the end of each loop.
```

## Rules
1. Product leadership agent READS this file at the START of every loop
2. Product leadership agent WRITES back insights at the END of every loop
3. Build agents READ but don't write (they follow product leadership direction)
4. Cross-machine context is updated when other machines report outputs
5. File grows over time — compact every 10 loops (keep decisions, drop details)
