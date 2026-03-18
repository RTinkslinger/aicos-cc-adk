# Pending Items

Extracted 2026-03-16 from plans archive. Items still relevant to current running system.

---

## Critical

- [x] **COMPACTION_PROTOCOL.md + CHECKPOINT_FORMAT.md not on disk** (from Plan 2, Tasks 9-10)
  **Resolved 2026-03-18:** Files exist on disk at `orchestrator/COMPACTION_PROTOCOL.md`, `orchestrator/CHECKPOINT_FORMAT.md`, and `content/CHECKPOINT_FORMAT.md`. Created before 2026-03-16 but pending items doc was never updated.

- [x] **Content agent `last_pipeline_run.txt` never written** (from Plan 3, Bug 8 in iteration 11)
  **Fixed 2026-03-18:** Hook-based deterministic fix. UserPromptSubmit detects "pipeline cycle" → sets flag. Stop hook checks flag + ACK contains "Pipeline" → writes timestamp. Stale flags from crash/compaction cleaned without false timestamps. 13/13 tests pass. See `docs/reference/content-agent-hook-lifecycle-2026-03-18.md`.

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
