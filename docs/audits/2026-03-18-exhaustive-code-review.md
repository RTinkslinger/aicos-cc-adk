# Exhaustive Code Review — Full Deployment
*Date: 2026-03-18*
*Branch: feat/three-agent-architecture*
*Scope: Agents monorepo (51 files, 6,763 lines), digest.wiki (6 files, 1,052 lines), scripts (11 files)*

---

## Summary

92 findings across 5 domains. 13 Critical, 25 High, 33 Medium, 21 Low.

| Severity | Orc+Content | State MCP | Web MCP | Deploy/Infra | Digest Site | Total |
|----------|-------------|-----------|---------|--------------|-------------|-------|
| Critical | 3 | 2 | 1 | 5 | 2 | **13** |
| High | 5 | 4 | 4 | 7 | 5 | **25** |
| Medium | 6 | 5 | 6 | 8 | 8 | **33** |
| Low | 4 | 3 | 4 | 5 | 5 | **21** |

---

## Domain 1: Orchestrator + Content Agent

### Critical

**C1. lifecycle.py:253-254 — `content_busy` leaks on `query()` exception → permanent deadlock**
`content_busy = True` is set before `await query()`. If `query()` raises, `content_busy` is never cleared — `_read_content_response` (which clears it in `finally`) is only created if `query()` succeeds. Every future heartbeat returns "Content agent is still processing" forever. No recovery without restart.
*Fix:* Wrap query + task creation in try/except that resets `content_busy` on failure.

**C2. lifecycle.py:208-223 — COMPACT_NOW scans accumulated TextBlocks, not final message → spurious restarts**
`result_text` accumulates all `TextBlock` content. If "COMPACT_NOW" appears in any intermediate text (e.g., "If you receive COMPACT_NOW, do X"), `content_needs_restart` triggers incorrectly. Wastes budget + loses in-progress state.
*Fix:* Only check `ResultMessage.result` for COMPACT_NOW, not accumulated text.

**C3. lifecycle.py:223 vs 477 — Inconsistent COMPACT_NOW detection between orc and content paths**
Orchestrator checks `msg.result` (line 477). Content agent checks accumulated text (line 223). One of the two is broken. If `msg.result` is authoritative, content detection misses the signal.
*Fix:* Apply `msg.result` check consistently to both paths.

### High

**H1. lifecycle.py:124 — Corrupt manifest.json kills the process**
`json.loads(MANIFEST_PATH.read_text())` throws `JSONDecodeError` on corrupt/partial files. Exception propagates to orchestrator main loop, triggering session restart + token count reset.
*Fix:* try/except in `read_manifest()` with fallback to empty dict.

**H2. lifecycle.py:385-422 — Empty DATABASE_URL silently becomes "always wake agent"**
If DATABASE_URL is unset, psql fails, `int()` raises ValueError, caught by outer except → returns "waking agent to be safe". Burns $0.50/heartbeat indefinitely.
*Fix:* Validate DATABASE_URL at startup. Add `isdigit()` check before `int()`.

**H3. lifecycle.py:500-503 — Exception exit path skips bump_session → manifest token count resets**
After exception, `orc_needs_restart=False` → `bump_session` not called → re-enters loop with same session number → `reset_manifest_tokens` zeros the counter while context continues growing. Suppresses COMPACT_NOW signals.
*Fix:* Always bump session on outer loop re-entry.

**H4. content/CLAUDE.md — Direct contradiction: Section 7 says "You own watch_list.json" vs Anti-Pattern #15 says "Never modify watch_list.json"**
Agent receives conflicting instructions. Section 7 says add sources from inbox; Anti-Pattern #15 says write notification instead.
*Fix:* Remove "You own this file" from Section 7. Anti-Pattern #15 has correct behavior.

**H5. content/stop-iteration-log.sh:61 — Pipeline timestamp depends on word "Pipeline" in agent log**
If agent writes "3 videos analyzed" instead of "Pipeline completed", timestamp check fails silently → `has_work()` sees pipeline as overdue → re-triggers on every heartbeat.
*Fix:* Make CLAUDE.md explicit about required word, or simplify to flag-only detection.

### Medium

**M1. lifecycle.py:275 — No startup log of resolved model name.** Add `logger.info()`.
**M2. lifecycle.py:303-328 — WEB_TOOLS list duplicated in 3 places.** Extract constant.
**M3. orchestrator/CLAUDE.md Section 5 vs Anti-Pattern #7 — Inbox "processed" semantics contradicts itself.** Settle on one definition.
**M4. content/pre-compact-flush.sh:49 — Recovery instruction references non-existent HEARTBEAT.md.** Change to "Read your CLAUDE.md."
**M5. lifecycle.py:53-61 — `_live_log` silently swallows all I/O errors.** Add `logger.warning`.
**M6. settings.json (both) — Hook paths hardcoded to /opt/agents/; local dev hooks silently fail.** Document limitation.

### Low

**L1. lifecycle.py:181-182 — `reset_iteration()` missing `mkdir(parents=True)`.** Crashes on fresh deployment.
**L2. content/CLAUDE.md:239-244 — Watch list schema documents forbidden behavior.** Remove add-source instructions.
**L3. content-worker.md — Skills paths relative, resolve incorrectly.** Use absolute paths.
**L4. orchestrator/CLAUDE.md Section 3 — HEARTBEAT.md indirection costs tokens every heartbeat.** Design observation.

---

## Domain 2: State MCP

### Critical

**C4. tests/test_state_mcp.py:102-108 — `patch_get_pool` fixture makes async function synchronous**
`patch("state.db.thesis.get_pool", return_value=mock_pool)` replaces `async def` with plain MagicMock. `await get_pool()` should raise TypeError. Either tests are failing silently or test runner has unusual behavior. All test results are suspect.
*Fix:* Use `new_callable=AsyncMock`.

**C5. tests/test_state_mcp.py:36-49 — `_thesis_row()` uses wrong field names**
Fixture uses `"name"` and `"key_questions"`. Real DB returns `"thread_name"` and `"key_question_summary"`. Server mapping logic never tested.
*Fix:* Align fixture to real column names.

### High

**H6. db/connection.py:17-23 — Race condition in `get_pool`**
Two concurrent callers can both find `_pool is None` → two pools created → first pool leaked.
*Fix:* Use `asyncio.Lock()`.

**H7. server.py:136-146 — ValueError from DB layer propagates as 500 to CAI**
`update_thesis` raises ValueError on not-found thesis. No try/except → opaque error to caller.
*Fix:* Catch ValueError, return structured error dict.

**H8. db/thesis.py:62-64 — NULL evidence fields cause silent data loss**
`WHEN evidence_for = ''` doesn't match NULL. `NULL || '\n' || $2` = NULL. Evidence silently dropped.
*Fix:* Use `COALESCE(evidence_for, '')`.

**H9. server.py:214 — GET /health always returns ok, never checks DB**
Load balancer probes pass even when Postgres is unreachable.
*Fix:* Add `SELECT 1` check to HTTP health endpoint.

### Medium

**M7. db/connection.py:19 — `os.environ["DATABASE_URL"]` raises bare KeyError.** Add diagnostic message.
**M8. server.py:122 — No `Literal` type on `direction` parameter.** Add `Literal["for", "against", "mixed"]`.
**M9. server.py:53 — Unknown `include` sections silently ignored.** Validate against known set.
**M10. tests — No server-level tests for `create_thesis_thread` or `update_thesis`.** Add tool-layer tests.
**M11. db/notifications.py:77 — `result.split()[-1]` fragile parse.** Add `isdigit()` check.

### Low

**L5. db/inbox.py — `get_pending`/`mark_processed` not exposed as MCP tools.** Document consumer.
**L6. server.py:166 — `post_message` hardcodes `type="message"`.** Document or parameterize.
**L7. inbox.py/notifications.py — Manual `json.dumps` for asyncpg jsonb.** Unnecessary overhead.

---

## Domain 3: Web Tools MCP

### Critical

**C6. SSRF — No URL validation on direct FastMCP tools**
`web_scrape`, `web_browse`, `fingerprint` accept arbitrary URLs. The `input_validation` hook only runs inside agent tasks (via `web_task_submit`). Direct tool calls bypass all validation. Attacker can reach DO metadata endpoint `169.254.169.254`, internal network.
*Fix:* Move URL validation into lib layer. Block RFC-1918, link-local, localhost patterns.

### High

**H10. task_store.py — No task cleanup, unbounded memory growth**
`_tasks` dict grows forever. Each task holds 30KB+ of web content. 1000 tasks = 30MB+. Gradual OOM.
*Fix:* Add TTL-based eviction (1 hour for completed tasks).

**H11. browser.py:197-203 — `evaluate` action allows arbitrary JS execution**
`page.evaluate(text)` with no restrictions. Combined with missing URL validation, can extract authenticated session state.
*Fix:* Remove `evaluate` from FastMCP surface or restrict to safe read-only patterns.

**H12. tools.py:178-218 — `manage_session` exposes full session state (cookies + localStorage)**
Any MCP caller can extract complete storageState for any domain. Session takeover risk.
*Fix:* Restrict to SDK-internal or redact state content.

**H13. lib/strategy.py:23-41 — SQLite single global connection, no health check**
Crash mid-write leaves broken handle. Subsequent calls get exceptions from stale connection.
*Fix:* Add `SELECT 1` health check in `_get_db()`.

### Medium

**M12. hooks.py:33 — `_domain_counts` grows unbounded per unique domain.** Delete empty keys after pruning.
**M13. server.py:91-94 — Task status mutation not through store API.** Add `set_task_running()`.
**M14. lib/extraction.py:191 — Undocumented `--remote-components` yt-dlp flag.** Document or remove.
**M15. agent.py:70 — API key explicitly passed in env dict.** Remove, SDK inherits parent env.
**M16. server.py:98 — Cost tracking always records $0.** Extract cost from ResultMessage.
**M17. lib/sessions.py:40-42 — Cookie files read fully without size guard.** Add size limit.

### Low

**L8. lib/stealth.py — Locale/timezone defined but never applied to browser context.** Pass to `new_context()`.
**L9. lib/monitor.py — `watch_url` is a non-functional stub exposed as real tool.** Return "not implemented" or remove.
**L10. tests/test_tools.py — References removed functions `web_task`, `web_screenshot`.** Tests broken, not running.
**L11. lib/browser.py:292-303 — `_flatten_a11y` defined but never called.** Dead code.

---

## Domain 4: Deploy & Infrastructure

### Critical

**C7. cron/health_check.sh — Checks v1 services (sync-agent, web-agent, content-agent) that don't exist**
If deployed, will attempt to restart non-existent services. May be actively running on droplet via `/etc/cron.d/agents-health`.
*Fix:* Delete file. Check droplet for `/etc/cron.d/agents-health` and remove.

**C8. systemd/install.sh — Installs v1 systemd units and dead cron**
Copies/enables `sync-agent.service`, `web-agent.service`, `content-agent.service` which don't exist in v3.
*Fix:* Delete or update. Add cleanup of old systemd units to `cleanup.sh`.

**C9. scripts/preflight.sh — Checks v1 agents, wrong port mappings**
Port 8000 is now State MCP, not Sync Agent. Preflight passes for wrong reason.
*Fix:* Delete or update for v3 services.

**C10. tests/acceptance.sh — Targets port 8002 (content agent has no HTTP port in v3)**
Checks 6, 7, 8, 9, 18 test non-existent infrastructure. Zero content agent test coverage.
*Fix:* Remove port 8002 tests. Update check #18 for v3 services.

**C11. tests/test_integration.py — TestContentAgent class targets port 8002**
All content agent tests permanently skipped (port never up). Zero automated coverage.
*Fix:* Remove or redesign for v3 (content agent is internal to lifecycle.py, no HTTP surface).

### High

**H14. deploy.sh:28 — rsync source is `./` without enforcing cwd.** Could sync entire repo. Add `cd "$SCRIPT_DIR"`.
**H15. deploy.sh:50-52 — `rsync --delete` on skills/ silently destroys runtime patches.** Add dry-run warning.
**H16. deploy.sh:88-89 — Service readiness failure doesn't abort deploy.** Add `exit 1` on failure.
**H17. auto_push.sh — Wrong repo path (missing "CC ADK").** Fix path or script is dead.
**H18. deploy.sh:59 — Bootstrap/cleanup sequencing trap on iterative deploys.** Document.
**H19. sql/v2.2-migrations.sql:28 — sync_metadata not seeded for cai_inbox/notifications.** Add seed rows.
**H20. scripts/publish_digest.py:37 — Dead Cowork VM session path.** Remove hardcoded path.

### Medium

**M18. deploy.sh:7 — Missing `set -o pipefail`.** Add to match other scripts.
**M19. deploy.sh:32 — Phase 1b tools sync lacks `--delete`.** Stale tools persist.
**M20. acceptance.sh — `bash -c` can't access shell functions.** Use `export -f` or inline curl.
**M21. test_integration.py:308 — Assertion logic inverted.** Fix conditional.
**M22. youtube_extractor.py:75 — `limit: int = None` wrong type annotation.** Use `Optional[int]`.
**M23. youtube_extractor.py:88 — 120s timeout not caught.** Wrap in try/except.
**M24. acceptance.sh:20 — TOTAL=20 hardcoded, can go negative.** Calculate dynamically.
**M25. infra/health_check.sh — Cooldown file doesn't handle non-numeric content.** Add `isdigit` check.

### Low

**L12. setup_youtube_cron.sh:152 — Hardcoded playlist ID in help text.** Cosmetic.
**L13. content_digest_pdf.py — Depends on `reportlab` not in pyproject.toml.** Dead code? Delete or add dep.
**L14. bootstrap.sh:50-56 — Error handling in seed commands.** Low risk.
**L15. validate-skill-package.sh:16 — Missing `set -e`.** Add for safety.
**L16. test_integration.py:86-104 — Module-level HTTP calls during test collection.** Document.

---

## Domain 5: Digest Site (digest.wiki)

### Critical

**C12. digests.ts:15 — Path traversal in `getDigest`**
Slug with `../` reads arbitrary files. Safe in SSG, exploitable if ISR/dynamic rendering added for WebFront.
*Fix:* `const safe = basename(slug)` before path.join.

**C13. digests.ts:18 — Unguarded `JSON.parse` crashes entire build**
One malformed JSON file = no deploy. Pipeline partial writes are realistic.
*Fix:* try/catch with `console.error` + skip.

### High

**H21. d/[slug]/page.tsx:17,41 — `getDigest` called twice per page (metadata + render).** Memoize.
**H22. DigestClient.tsx:1 — 623-line monolithic Client Component.** Extract thin reveal wrapper, keep render as Server Component.
**H23. DigestClient.tsx:10-28 — IntersectionObserver never re-registers on data change.** Add key or dependency.
**H24. digests.ts:7-12 — `readdirSync` crashes if DATA_DIR missing.** Add `existsSync` guard.
**H25. digests.ts:18-99 — Type-unsafe normalisation, `any` throughout.** Type intermediate object or add Zod validation.

### Medium

**M26. DigestClient.tsx — `key={i}` index keys used everywhere.** Use stable unique values.
**M27. DigestClient.tsx:166-181 — Em-dash split assumption.** Normalize or use regex.
**M28. DigestClient.tsx:609-618 — Timezone not pinned, shows client's local time.** Add `timeZone: "UTC"`.
**M29. DigestClient.tsx:609 — "Pipeline v4" hardcoded, should be v5.** Update or derive from data.
**M30. DigestClient.tsx:372-403 — Empty `watch_sections` renders empty section.** Add length guard.
**M31. globals.css:1 — Google Fonts via render-blocking `@import`.** Use `next/font/google`.
**M32. globals.css:35 — `overflow-x: hidden` on body breaks sticky positioning.** Use `overflow-x: clip`.
**M33. DigestClient.tsx:186-194 — Meta chip values as keys, collision risk.** Use index (fixed-length list).

### Low

**L17. DigestClient.tsx:200 — `"t3"` fallback not in AccentColor union.** Add or fix type.
**L18. digests.ts:127-153 — Dead exports never imported.** Remove.
**L19. DigestClient.tsx — 10 sibling `h2` elements, flat heading outline.** Use h3 for sections.
**L20. package.json:9 — ESLint config missing, lint may be no-op.** Add `eslint.config.js`.
**L21. d/[slug]/page.tsx:31 — `publishedTime` could be empty string.** Already guarded by normalisation.

---

## Priority Fix Order

### Immediate (security + data loss)
1. C6: SSRF guard on Web MCP direct tools
2. H11 + H12: Remove `evaluate` and `manage_session` from external FastMCP surface
3. C1: `content_busy` leak fix in lifecycle.py
4. C12 + C13: Path traversal + JSON.parse guard in digests.ts

### This week (correctness + stability)
5. C2 + C3: COMPACT_NOW detection consistency
6. H8: NULL evidence COALESCE fix
7. H7: Structured error returns from State MCP
8. C7-C11: Delete ghost v1 infrastructure (check droplet for active cron)
9. H4: Resolve watch_list.json contradiction
10. C4 + C5: Fix test fixtures (then run tests to see what else surfaces)

### Next sprint (quality + performance)
11. H10: Task store eviction
12. H22: DigestClient Server/Client split
13. M31: Google Fonts → next/font
14. H9: Health endpoint DB check
15. Remaining Medium items

---

## Metrics

- **Files reviewed:** 68
- **Lines reviewed:** ~8,800
- **Review agents:** 5 parallel
- **Review duration:** ~3 minutes wall time
