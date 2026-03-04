---
name: full-cycle
description: "On-demand meta-orchestrator — runs ALL AI CoS pipeline tasks in correct dependency order with human checkpoints. Trigger: 'run full cycle', 'full cycle', 'run everything', 'run all pipelines', 'process everything', 'run the full loop', 'catch up on everything'"
version: "1.0"
last_updated: "2026-03-04 (Session 030)"
---

# Full Cycle — AI CoS Meta-Orchestrator

You are running a **full cycle** of all AI CoS pipeline tasks. This is the on-demand equivalent of letting all scheduled tasks run in their natural order, but executed NOW in a single interactive session with human checkpoints.

**Core principle:** This is a DAG (directed acyclic graph), not a flat list. Each step declares its dependencies. Execute steps only after all dependencies are satisfied. If a step has no work to do, skip it cleanly and move to the next.

---

## PIPELINE REGISTRY

This registry is the single source of truth for what "full cycle" executes. **When any session adds a new scheduled task or pipeline step, it MUST also add an entry here.** This is how the command evolves.

```
STEP | NAME                    | DEPENDS ON | RUNS WHERE   | HUMAN CHECKPOINT | SCHEDULED EQUIVALENT
─────┼─────────────────────────┼────────────┼──────────────┼──────────────────┼─────────────────────
  0  │ Pre-flight check        │ (none)     │ Cowork       │ No               │ (none)
  1  │ YouTube extraction      │ 0          │ Mac (osascr) │ Yes — confirm    │ launchd / manual `yt`
  2  │ Content Pipeline        │ 1          │ Cowork       │ Yes — review     │ process-youtube-queue (9 PM)
  3  │ Back-propagation sweep  │ 2          │ Cowork       │ No               │ back-propagation-sweep (10 AM)
```

**Reading the registry:**
- Steps are executed in numerical order, but ONLY after all steps listed in DEPENDS ON are complete
- HUMAN CHECKPOINT = Yes means pause and wait for Aakash before proceeding
- RUNS WHERE tells you what execution method to use
- SCHEDULED EQUIVALENT links to the cron/launchd job this replaces on-demand

### Adding a new step (instructions for future sessions)
1. Assign the next step number
2. Declare dependencies (which prior steps must complete first)
3. Specify execution method (Cowork, Mac osascript, Notion-only)
4. Decide if human checkpoint is needed (if step changes data Aakash hasn't reviewed, yes)
5. Link to the scheduled equivalent if one exists
6. Add the execution instructions in the STEP EXECUTION section below

---

## EXECUTION FLOW

When triggered, run these steps in order. Present a brief plan first, then execute.

### Opening message to Aakash:
```
Running full cycle. Here's the plan:
  0. Pre-flight check (verify queue, Notion access)
  1. YouTube extraction (Mac → queue folder)  ⏸ confirm
  2. Content Pipeline (analyze → PDF digests → Notion → actions)  ⏸ review actions
  3. Back-propagation sweep (Done actions → Content Digest update)

Starting Step 0...
```

---

### Step 0: Pre-flight Check
**Dependencies:** none
**Checkpoint:** no

Verify the system is ready:
1. **Queue folder accessible** — Check `queue/` folder exists and is readable: `ls /sessions/*/mnt/*AI*CoS/queue/`
2. **Notion accessible** — Test with a lightweight fetch: `notion-fetch` on any known page ID
3. **Check for unprocessed queue files** — `ls queue/*.json` (not in `processed/`). Count them.
4. **Check for pending content actions** — Quick query: are there Content Digest entries with Action Status = "Pending" that haven't been reviewed yet?

Report status:
```
Pre-flight ✅
  Queue folder: accessible
  Notion: connected
  Unprocessed queue files: X
  Pending content reviews: Y
```

If queue folder is empty AND no pending reviews AND no Done actions to sweep → **"Nothing to process. Full cycle complete — system is current."** Exit cleanly.

---

### Step 1: YouTube Extraction
**Dependencies:** Step 0
**Runs on:** Mac bare metal via osascript
**Checkpoint:** YES — confirm before proceeding

Run the `yt` CLI on Aakash's Mac to fetch new YouTube content:

```
osascript MCP: do shell script "cd '/Users/Aakash/Claude Projects/Aakash AI CoS' && ./scripts/yt 2>&1"
```

This fetches playlist metadata + transcripts and saves JSON to the `queue/` folder.

**After extraction, report:**
```
Step 1: YouTube extraction complete
  New videos found: X
  [list video titles]

⏸ Proceed with analysis? (Or adjust — e.g., "skip video 3", "also process last 7 days")
```

Wait for Aakash's confirmation. He may want to:
- Proceed with all videos
- Skip certain videos
- Adjust the extraction window (e.g., `yt 7` for 7 days)
- Add specific URLs (e.g., `yt --urls <URL>`)

**If no new videos found:** Report "No new videos in queue" and skip to Step 3 (back-propagation sweep may still have work).

---

### Step 2: Content Pipeline
**Dependencies:** Step 1 (or skip to here if Step 1 found nothing but unprocessed files exist from a prior extraction)
**Runs on:** Cowork (this session)
**Checkpoint:** YES — review proposed actions

Load and execute the `youtube-content-pipeline` skill. This is the full v4 pipeline:
- Load queue JSON files
- Build shared context (Portfolio, Thesis, Pipeline, Previous Digests)
- Parallel subagent analysis (one per video)
- Generate PDF digests + HTML digests
- Write to Content Digest DB (with dedup guard)
- Route actions to Actions Queue (with Source Digest + Thesis relations)
- Present interactive review

**The pipeline's own Step 6 (interactive review) IS the human checkpoint.** Aakash will:
- Review each proposed action
- Accept, dismiss, or modify
- The pipeline handles all Notion writes

**After pipeline completes, report:**
```
Step 2: Content Pipeline complete
  Videos processed: X
  Actions proposed: Y (Z accepted, W dismissed)
  PDF digests generated: X
  HTML digests published: X
```

---

### Step 3: Back-propagation Sweep
**Dependencies:** Step 2 (actions may have just been moved to Done if Aakash marked them during review)
**Runs on:** Cowork (this session)
**Checkpoint:** no

Execute the back-propagation sweep logic directly (don't wait for the scheduled task):

1. Fetch all Actions Queue pages via `notion-fetch` on `collection://1df4858c-6629-4283-b31d-50c5e7ef885d`
2. Filter client-side for Status = "Done" with non-empty Source Digest relation
3. For each match, check Content Digest current Action Status (idempotency guard)
4. Update eligible Content Digest entries to "Actions Taken"

**Report:**
```
Step 3: Back-propagation sweep complete
  Done actions found: X
  With Source Digest relation: Y
  Already propagated (skipped): Z
  Newly propagated: N
```

---

## COMPLETION SUMMARY

After all steps complete, present a single summary:

```
Full cycle complete ✅

  Step 0: Pre-flight ✅
  Step 1: YouTube extraction — X new videos
  Step 2: Content Pipeline — X processed, Y actions (Z accepted)
  Step 3: Back-propagation — N entries updated

System is current. Next scheduled runs:
  - Content Pipeline: [next run time from scheduled task]
  - Back-propagation: [next run time from scheduled task]
```

---

## PARTIAL RUNS

Aakash may want to run only part of the cycle:
- **"just run the sweep"** → Skip to Step 3 only
- **"just process the queue"** → Steps 0 + 2 only (skip extraction, use existing queue files)
- **"extract and stop"** → Steps 0 + 1 only
- **"run from step 2"** → Steps 2 + 3 (assumes queue already populated)

The DAG supports partial execution — just skip steps and their dependents as needed. Always run Step 0 (pre-flight) regardless.

---

## EVOLUTION PROTOCOL

**This skill MUST be updated when:**
1. A new scheduled task is created → Add a step to the PIPELINE REGISTRY
2. A scheduled task is removed → Remove or mark deprecated in PIPELINE REGISTRY
3. A dependency changes (e.g., new task depends on an existing step) → Update DEPENDS ON
4. A new human checkpoint is needed → Update HUMAN CHECKPOINT column
5. Execution instructions change (e.g., new osascript command) → Update the step's section

**Convention:** When updating, increment the version in the frontmatter and update `last_updated`. This makes it easy to spot drift between the skill and the actual scheduled tasks.

**Self-check:** At the start of every full cycle, compare the PIPELINE REGISTRY against `list_scheduled_tasks` output. If there's a mismatch (a scheduled task exists that isn't in the registry, or vice versa), warn Aakash:
```
⚠️ Registry drift detected:
  - Scheduled task "X" exists but is not in the full-cycle registry
  - Registry step Y has no matching scheduled task

Consider updating the full-cycle skill to stay in sync.
```
