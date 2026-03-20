# Datum Agent Lifecycle Verification — M4 Loop 5
*Verified: 2026-03-20*
*Auditor: Claude Opus 4.6*

---

## Verdict: DEPLOY READY

---

## 1. Code Quality

| Check | Result |
|-------|--------|
| AST parse | PASS — `python3 -c "import ast; ast.parse(...)"; print('AST OK')` |
| `start_datum_client` (L497) | Present, follows exact pattern of `start_content_client` |
| `stop_datum_client` (L505) | Present, identical pattern to `stop_content_client` |
| `restart_datum_client` (L514) | Present, identical pattern — calls stop, bump_session, reset_manifest_tokens, start, clear flag |
| `_read_datum_response` (L283) | Present inside `create_bridge_server`, mirrors `_read_content_response` exactly |
| `send_to_datum_agent` @tool (L313) | Present, registered in bridge server (L344) |
| `build_datum_options` (L436) | Present, well-configured |
| `datum_busy` flag (L50) | Present in `ClientState`, checked at L320, set at L328, cleared in finally block at L303 |
| Fire-and-forget pattern | PASS — `asyncio.create_task(_read_datum_response())` at L331 |

---

## 2. Pattern Consistency — Datum vs Content

Compared `build_datum_options()` (L436-462) vs `build_content_options()` (L377-433):

| Aspect | Content | Datum | Match? |
|--------|---------|-------|--------|
| Model | claude-sonnet-4-6 | claude-sonnet-4-6 | Yes |
| Permission mode | dontAsk | dontAsk | Yes |
| Thinking | 10K tokens | 5K tokens | Intentional (lighter) |
| Max turns | 50 | 30 | Intentional (lighter) |
| Budget | $5.0 | $2.0 | Intentional (lighter) |
| MCP servers | Web Tools | Web Tools | Yes |
| Subagents (Agent tool) | Yes (web-researcher, content-worker) | No | Intentional (no delegation needed) |
| Skill tool | Yes | Yes | Yes |
| Env vars | +FIRECRAWL_API_KEY | No FIRECRAWL | Correct — datum doesn't need Firecrawl |
| Hook pattern | PostToolUse with live log | PostToolUse with live log | Yes |
| setting_sources | ["project"] | ["project"] | Yes |

**Asymmetries found: 0 bugs.** All differences are intentional and documented in the integration report.

### Bridge Tool Symmetry

| Pattern | Content | Datum | Match? |
|---------|---------|-------|--------|
| Null client check → error | L253-256 | L314-317 | Yes |
| Busy flag check → busy msg | L259-261 | L320-322 | Yes |
| Set busy before query | L267 | L328 | Yes |
| `await client.query()` | L269 | L330 | Yes |
| `asyncio.create_task(reader)` | L270 | L331 | Yes |
| Exception → clear busy + error | L272-277 | L333-338 | Yes |
| Return "Prompt sent" | L280 | L340 | Yes |
| Response reader: AssistantMessage logging | L228 | L287 | Yes |
| Response reader: ResultMessage + token tracking | L229-236 | L289-296 | Yes |
| Response reader: COMPACT_NOW detection | L237-239 | L297-299 | Yes |
| Response reader: finally → clear busy + idle log | L242-244 | L303-304 | Yes |

**Perfect structural symmetry.** No asymmetry bugs.

---

## 3. Orchestrator CLAUDE.md & HEARTBEAT.md

| Check | Result |
|-------|--------|
| `mcp__bridge__send_to_datum_agent` in capabilities table | PASS — Section 2 |
| Section 5b documenting datum routing | PASS — full routing rules, batching, prompt format |
| Anti-patterns include datum routing rules | PASS — Rules #2, #9, #10 cover datum misrouting |
| HEARTBEAT.md routing table | PASS — 5 datum_* types mapped to Datum Agent |
| HEARTBEAT.md batching rule | PASS — 3+ datum_* messages batched into single prompt |
| Processing steps handle both agent groups | PASS — Step 2 separates into datum group + content group |
| Busy retry logic documented | PASS — "If either tool returned busy, skip that group" |

---

## 4. Deploy Readiness

| Check | Result |
|-------|--------|
| `deploy.sh` header mentions datum | PASS — L6: "content agent + datum agent" |
| `deploy.sh` output mentions `live-datum.sh` | PASS — L137 |
| `live-datum.sh` exists | PASS — follows `live-content.sh` pattern exactly (trap, touch, tail -n20 -f) |
| rsync covers `datum/` directory | PASS — rsync syncs `./` with only explicit exclusions; `datum/` is not excluded |
| `datum/state/` excluded from rsync | PASS — `--exclude='*/state/'` protects runtime state |
| `datum/state/datum_session.txt` | PASS — exists, value: 1 |
| `datum/state/datum_iteration.txt` | PASS — exists, value: 0 |
| `datum/CLAUDE.md` | PASS — exists |
| Datum hooks | PASS — 3 hooks present (stop-iteration-log, prompt-manifest-check, pre-compact-flush) |
| No new systemd service needed | PASS — datum runs inside orchestrator process |
| No new env vars needed | PASS — uses existing DATABASE_URL + ANTHROPIC_API_KEY |

### Deploy Steps

1. `cd mcp-servers/agents && bash deploy.sh` — syncs code, bootstraps, restarts orchestrator
2. Orchestrator picks up new `lifecycle.py` with datum support on restart
3. Send test: `psql $DATABASE_URL -c "INSERT INTO cai_inbox (type, content) VALUES ('datum_person', 'Test Person, CTO at TestCo')"`
4. Watch: `ssh -t root@aicos-droplet /opt/agents/live-datum.sh`

---

## 5. Main Loop Integration

| Check | Result |
|-------|--------|
| Datum client started in `run_agent()` (L586-589) | PASS — after content, before orchestrator |
| Datum compaction check in heartbeat loop (L606-607) | PASS — mirrors content compaction check |
| Datum client stopped in finally block (L652) | PASS — after content stop |
| Datum client stopped in `main()` shutdown (L677) | PASS — after content stop |
| Orc allowed_tools includes datum bridge (L362) | PASS — `mcp__bridge__send_to_datum_agent` |

---

## Summary

All 5 verification dimensions pass. The Datum Agent integration is a clean, symmetric extension of the established Content Agent pattern with zero structural bugs. The lighter resource allocation (5K thinking, 30 turns, $2.0 budget) is appropriate for entity processing workloads. Deploy infrastructure (deploy.sh, live-datum.sh, state files, hooks) is complete.

**Verdict: DEPLOY READY.**
