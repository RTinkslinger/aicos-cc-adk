# M10 CIR Agent Build Audit — 2026-03-21

**Machine:** M10 Continuous Intelligence Refresh
**Task:** Create agent skill files for CIR infrastructure
**Timestamp:** 2026-03-21T17:21Z

---

## System Health Snapshot (at time of build)

| Metric | Value | Status |
|--------|-------|--------|
| Overall Grade | B+ | Healthy |
| Overall Score | 8.7 / 10 | Good |
| Technical Grade | A (10/10) | Excellent |
| Product Grade | B (6.4/10) | Data richness dragging |
| Queue Depth | 0 pending | Clear |
| Dead Letters | 0 | Clear |
| Embedding Coverage | 100% all tables | Recovered |
| Avg Staleness | 9.5 hours | Fresh |
| Total Entities | 8,416 | Tracked |
| Total Connections | 23,743 (18 types) | Rich graph |
| Avg Connection Strength | 0.71 | Healthy |
| Orphan Companies | 214 | Known gap |

### Cron Health Summary

| Health | Jobs | Names |
|--------|------|-------|
| HEALTHY | 9 | connection-decay, log-retention, preemptive-refresh, cron-health-check, depth-grade, self-heal, cleanup-embeddings, pool-cleanup, strategic-briefing |
| GOOD | 5 | process-embeddings (95.2%), queue-processor (93.0%), heartbeat (98.4%), action-entity-map (97.4%), score-refresh (100%), preference-weight (100%), obligation-status (100%), strategic-recal (100%), megamind-dismiss (100%) |
| DEGRADED | 2 | matview-refresh (88.5%), staleness-check (87.5%) |
| FAILING | 4 | normalize-scores (50%), daily-strategic-assessment (0%), staleness-refresh (0%), proactive-staleness-refresh (66.7%) |

**Root cause of failures:** Transient "connection failed" errors (Supabase pooler saturation) and one deadlock in proactive-staleness-refresh (concurrent row lock on actions_queue).

### Propagation 24h Stats

| Metric | Count |
|--------|-------|
| Total Events | 108,292 |
| Company Propagations | 20,664 |
| Network Propagations | 12,630 |
| Thesis Indicator Updates | 6,949 |
| Cascade Events Propagated | 12 |
| Errors | 7 (0.01% error rate) |
| Batch Runs | 142 |

**Error detail:** 7 occurrences of `compute_user_priority_score(integer)` function signature mismatch — expects a row type, not integer. Affects new action processing only (7 actions).

### Dimension Breakdown

| Dimension | Score | Verdict | Key Issue |
|-----------|-------|---------|-----------|
| Embedding Coverage | 10 | HEALTHY | 100% across all tables |
| Data Richness | 1 | SKELETAL | Companies avg 170 chars, Network avg 204 chars, 621 company stubs |
| Connection Quality | 5.2 | NOISY | Only 26% evidence-based (6,171 of 23,743) |
| Agent Readiness | 9.4 | READY | 34/36 IRGI passing, 92.8ms avg latency |
| Propagation | 10 | FLOWING | 0 queue, 0 dead letters |
| Score Accuracy | 5 | COMPRESSED | stddev 1.64, max bucket 28.8% |

---

## Deliverables Created

### 1. `mcp-servers/agents/skills/data/cir-system-health.md`

Agent skill file teaching how to use CIR health monitoring functions:
- `cir_full_status()` — complete system status in one call
- `system_health_aggregate()` — 6 weighted dimensions with grades
- `embedding_recovery_dashboard()` — deep embedding subsystem health
- `embedding_queue_health()` — lightweight queue check
- `cir_cron_health` view — all 24 cron jobs with health ratings
- `cir_self_heal()` — manual self-healing with 6 phases
- Diagnostic queries for queue, errors, connections, staleness, latency
- Escalation checklist for degraded health

### 2. `mcp-servers/agents/skills/data/cir-propagation.md`

Agent skill file teaching how CIR propagation works:
- Architecture overview (trigger -> log -> queue -> process)
- All 11 triggers across 8 tables mapped
- 10 propagation rules with significance levels
- Queue processing pipeline (PGMQ cir_queue)
- All 10 target actions with what each does
- Priority processing tiers (immediate/standard/deferred)
- Cascade events: creation, schema, analysis, auto-propagation
- Entity connections: 18 connection types, schema, decay, querying
- CIR state table: 8 key patterns, 8,416 entries
- Propagation functions: company, network, signal, obligation
- 5 monitoring views
- 4 debugging playbooks

---

## Issues Found

1. **`compute_user_priority_score` signature mismatch** — Function expects row type but queue processor passes integer. 7 errors in 24h. Non-critical (only affects initial action scoring).

2. **Proactive staleness refresh deadlock** — Concurrent `rescore_related_actions()` within `proactive_refresh_stale_entities()` hits deadlock on `actions_queue` table. Needs advisory lock or serialization.

3. **Data richness at 1/10** — Companies average 170 chars, network 204 chars. 621 company stubs (< 50 chars). This is the biggest product quality gap and feeds into connection quality (low evidence).

4. **Connection quality at 5.2/10** — Only 26% of connections are evidence-based. 74% are inferred (vector_similar, sector_peer). M12 Data Enrichment needs to run to fix this.

5. **Score compression** — stddev 1.64 with 28.8% max bucket concentration. Scores cluster too tightly, reducing signal differentiation.

---

## Recommendations

- **Fix `compute_user_priority_score` call** — Change queue processor to pass the full row, not just ID
- **Add advisory lock to proactive staleness refresh** — Prevent deadlock with concurrent score refresh
- **Priority: M12 Data Enrichment** — Data richness is the bottleneck for connection quality and score accuracy
- **Score normalization** — The normalize-scores job is FAILING (50% rate). Fix connection issue or reschedule to avoid pool contention
