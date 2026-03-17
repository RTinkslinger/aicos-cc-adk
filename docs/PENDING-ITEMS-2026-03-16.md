# Pending Items

Extracted 2026-03-16 from plans archive. Items still relevant to current running system.

---

## Critical

- [ ] **COMPACTION_PROTOCOL.md + CHECKPOINT_FORMAT.md not on disk** (from Plan 2, Tasks 9-10)
  **Why still needed:** Orchestrator CLAUDE.md references `state/COMPACTION_PROTOCOL.md` (Section 7: "Read COMPACTION_PROTOCOL.md") and `state/CHECKPOINT_FORMAT.md`. Content CLAUDE.md references `state/CHECKPOINT_FORMAT.md`. These files don't exist on disk -- compaction instructions are currently only in the CLAUDE.md prose, but agents are told to read these files. When context compaction fires, the agent will try to Read a nonexistent file.

- [ ] **Content agent `last_pipeline_run.txt` never written** (from Plan 3, Bug 8 in iteration 11)
  **Why still needed:** Identified as a bug in iteration 11 but not confirmed fixed. The orchestrator's `has_work()` pre-check reads this file to decide if pipeline is overdue. If the content agent never writes it, the orchestrator triggers pipeline every heartbeat cycle (12hr guard helps, but the file should be written).

- [ ] **Content agent dedup guard on first run** (from Plan 3, Bug 9 in iteration 11)
  **Why still needed:** On fresh start, content agent processes all historical content from watch list sources (no since-date guard). The Postgres-as-queue `ON CONFLICT (url) DO NOTHING` prevents duplicate digests, but the agent still wastes time fetching and attempting to insert URLs that already exist. A since-date guard (e.g., only fetch content from last 48h on first run) would prevent wasted cycles.

## Nice-to-have

- [ ] **Sync Agent re-enable when needed** (from Plan 1, Task 17-18)
  **Why still needed:** Sync Agent code exists (runner.py, system_prompt.md, sync skills, infra/sync-agent.service) but is stopped+disabled on droplet and removed from deploy.sh. When Notion bidirectional sync is needed again, re-add to deploy.sh and re-enable. Currently not blocking anything since content_digests backfill was done manually and thesis updates flow Postgres-only.

- [ ] **Web Tools MCP async task E2E test** (from Plan 1, Task 20 Step 5)
  **Why still needed:** The async task pattern (web_task_submit -> web_task_status -> web_task_result) was built and deployed but never E2E tested from CAI. This is the path CAI uses for complex web research. Low risk since the underlying web tools work, but the submit/poll/retrieve flow is unvalidated.

- [ ] **Deploy cleanup of stale files on droplet** (from Plan 3, Bug 3 in iteration 11)
  **Why still needed:** deploy/cleanup.sh was added to address this, but the specific cleanup rules should be verified. Old files (e.g., system_prompt.md) persisted on droplet after deploy because rsync doesn't delete files not in source. The cleanup script should handle this but may need entries for newly-obsolete files.

- [ ] **State MCP `get_state(thesis)` column verification** (from iteration 9 fix)
  **Why still needed:** thesis.py had column name mismatches (name->thread_name, key_questions->key_question_summary) fixed in iteration 9. The fix was deployed, but no automated test covers the actual Postgres column names. If the schema drifts, the same silent failure will recur.
