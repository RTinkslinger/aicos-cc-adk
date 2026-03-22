# Hooks Spec for Machine Enforcement
*2026-03-22 — Hooks that ENFORCE machine behaviors, not just instruct them*

## Principle
Instructions in CLAUDE.md drift and get ignored. Hooks execute shell scripts that BLOCK or INJECT — they can't be skipped.

## Hooks Needed

### 1. Pre-Agent Hook: Inject M-FEEDBACK Decomposed Tasks
**Event:** PreToolUse on Agent
**What it does:** Before ANY machine agent launches, query `feedback_decomposition` for pending tasks targeted at that machine. Inject as `additionalContext` so the machine MUST see its feedback tasks.
**Why hooks:** Without this, machines launch without checking feedback. With instructions alone, they "forget" to check. The hook FORCES the context in.

### 2. Pre-Agent Hook: Check Implicit Feedback
**Event:** PreToolUse on Agent
**What it does:** For agent machines (M4/M7/M8/M-ENIAC), also query the agent's `cindy_conversation_log` or equivalent for recent user decisions (dismissals, acceptances, overrides). Inject as context.
**Why hooks:** Implicit feedback is the RL signal. Without hooks, machines never read it.

### 3. Post-Agent Hook: Verify Feedback Was Addressed
**Event:** PostToolUse on Agent (when machine completes)
**What it does:** Check if the machine's output mentions addressing any of its pending feedback items. If not, warn the orchestrator.
**Why hooks:** Machines claim to address feedback but skip items. This catches it.

### 4. SessionStart Hook: M-FEEDBACK Auto-Run
**Event:** SessionStart (on "resume machineries")
**What it does:** Before launching machines, run M-FEEDBACK first to process any new WebFront feedback since last session. This ensures ALL machines start with fresh decomposed tasks.
**Why hooks:** Without this, feedback from between sessions gets lost.

### 5. UserPromptSubmit Hook: Feedback Detection
**Event:** UserPromptSubmit
**What it does:** Detect when user's CC message is feedback (contains keywords like "wrong", "broken", "off", "should be", "why is", "fix", "improve"). Auto-log to feedback timeline and route to M-FEEDBACK.
**Why hooks:** User gives feedback in CC chat that never reaches machines. This captures it.

### 6. Pre-Agent Hook: Deploy Verification
**Event:** PreToolUse on Agent (for M1 WebFront)
**What it does:** Before M1 launches, check if previous deploy is live on Vercel (state=READY). If not, block until resolved.
**Why hooks:** Prevents M1 from building on top of a failed deploy.

### 7. Stop Hook: Agent File Deploy Check
**Event:** Stop
**What it does:** If agent CLAUDE.md or skill files were modified, check if deploy.sh was run. Warn if not.
**Why hooks:** Two sessions of agent file changes went undeployed to droplet. This prevents it.

## Implementation Priority
1. **#1 (M-FEEDBACK inject)** — highest impact, ensures feedback reaches machines
2. **#4 (SessionStart M-FEEDBACK)** — ensures fresh feedback on resume
3. **#7 (Deploy check)** — prevents the "deployed to Mac not droplet" gap
4. **#2 (Implicit feedback)** — RL signal for agent improvement
5. **#5 (CC feedback detection)** — captures CC chat feedback
6. **#3 (Post-agent verify)** — accountability
7. **#6 (Deploy verification)** — M1 safety
