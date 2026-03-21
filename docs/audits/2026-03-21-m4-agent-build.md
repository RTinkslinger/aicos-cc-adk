# M4 Datum Agent Build Audit

**Date:** 2026-03-21
**Machine:** M4 (Datum)
**Loop:** Agent file build (bridging SQL tools to agent knowledge)

---

## Problem

18 sessions built 14 autonomous SQL functions in Postgres for Datum. Zero agent files
were written. The Datum agent running on the droplet has no idea these tools exist.
It cannot call `datum_daily_maintenance()`, `datum_garbage_detector()`, or any of the
enrichment functions because its CLAUDE.md and skills do not reference them.

## What Was Built

### 3 New Skill Files

| File | Lines | Purpose |
|------|-------|---------|
| `skills/datum/data-quality.md` | ~230 | Teaches Datum how to use 6 maintenance SQL functions: `datum_daily_maintenance()`, `datum_data_quality_check()`, `datum_garbage_detector()`, `datum_consistency_enforcer()`, `datum_stale_action_detector()`, `datum_notion_drift_check()`. Includes interpretation rules, action protocols, ACK formats, notification patterns. |
| `skills/datum/enrichment.md` | ~260 | Teaches Datum how to use 5 enrichment SQL functions + 2 reporting functions: `datum_signal_propagator()`, `datum_network_signal_enricher()`, `datum_thesis_auto_backfill()`, `datum_cross_entity_linker()`, `datum_company_name_deduplicator()`, `datum_entity_health()`, `datum_thesis_coverage()`. Includes M12 loop pattern, monitoring queries, merge SQL patterns. |
| `skills/datum/identity-resolution.md` | ~200 | Teaches Datum confidence gating (>=0.90 act, 0.70-0.89 ask, <0.70 skip), create-vs-not-create decision matrix, cross-surface identity stitching, datum_request lifecycle, `datum_resolve_pseudo_ids()` usage, Cindy collaboration protocol. |

### Datum CLAUDE.md Updates

1. **SQL Tool Inventory table** — All 14 functions listed with signatures, return types, and purpose. Organized into 3 categories: Maintenance & Quality (6), Enrichment & Linking (5), Identity Resolution (3).

2. **Skills reference table** — All 6 datum skills (3 existing + 3 new) with load triggers.

3. **Confidence Gating Protocol** — Inline reference: >=0.90 act, 0.70-0.89 ask, <0.70 skip.

4. **3 new input types** — `datum_maintenance`, `datum_enrichment`, `datum_quality_check` with full processing instructions.

5. **4 new notification types** — `maintenance_complete`, `maintenance_alert`, `quality_report`, `enrichment_progress`.

### Orchestrator CLAUDE.md Updates

- Added new datum message types to routing rules
- Added daily maintenance trigger instruction

## SQL Functions Inventory (14 total)

| # | Function | Category |
|---|----------|----------|
| 1 | `datum_daily_maintenance()` | Maintenance (master) |
| 2 | `datum_data_quality_check()` | Maintenance |
| 3 | `datum_garbage_detector()` | Maintenance |
| 4 | `datum_consistency_enforcer()` | Maintenance |
| 5 | `datum_stale_action_detector()` | Maintenance |
| 6 | `datum_notion_drift_check()` | Maintenance |
| 7 | `datum_signal_propagator()` | Enrichment |
| 8 | `datum_network_signal_enricher()` | Enrichment |
| 9 | `datum_thesis_auto_backfill()` | Enrichment |
| 10 | `datum_cross_entity_linker()` | Enrichment |
| 11 | `datum_company_name_deduplicator()` | Enrichment |
| 12 | `datum_resolve_pseudo_ids()` | Identity |
| 13 | `datum_entity_health()` | Identity/Reporting |
| 14 | `datum_thesis_coverage()` | Reporting |

## Before/After

| Aspect | Before | After |
|--------|--------|-------|
| SQL tools Datum knows about | 0 | 14 |
| Datum skill files | 3 (processing, dedup, people-linking) | 6 (+data-quality, +enrichment, +identity-resolution) |
| Maintenance input types | 0 | 3 (datum_maintenance, datum_enrichment, datum_quality_check) |
| Notification types | 8 | 12 (+4 maintenance/quality types) |
| Confidence gating documented | Implicit in CLAUDE.md | Explicit protocol with thresholds |
| M12 loop pattern documented | Not documented | Full 8-step loop pattern in enrichment skill |
| Orchestrator routing for datum_maintenance | Not supported | Supported + daily trigger |

## Next Steps

1. **Deploy to droplet** — `cd mcp-servers/agents && bash deploy.sh` to sync these files
2. **Test maintenance trigger** — Send `datum_maintenance` via Orchestrator inbox
3. **Run M12 loop** — Trigger `datum_enrichment` and measure improvement deltas
4. **Monitor** — Check notifications table for Datum agent maintenance reports
5. **Iterate** — Add more specialized skills as usage patterns emerge
