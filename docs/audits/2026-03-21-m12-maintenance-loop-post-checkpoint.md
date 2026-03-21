# M12 Data Enrichment: Maintenance Loop L16

**Date:** 2026-03-21
**Machine:** M12 Data Enrichment
**Loop type:** Quality monitoring, dedup, link building, thin content enrichment

---

## Executive Summary

Maintenance loop: no regressions detected. 23 YC batch suffix duplicates merged (21 standard + 2 edge cases). 50 new entity_connections built. 11 companies with thin page_content enriched to meaningful length. Embedding queue empty. All base metrics stable.

---

## Actions Taken

### 1. YC Batch Suffix Dedup (23 merges)
Merged companies with pattern `X (YC WXX)` -> `X` where the clean-name version was the winner:
- 21 standard batch suffix duplicates (RunAnywhere, MochaCare, Claybird, Deeptrace, etc.)
- PlayVision (YC F25) -> PlayVision
- Rhizome AI (YC W26) -> Rhizome AI
- Fulton Science Academy (case variant) merged
- Feedsco Global Private Limited -> Feedsco Global

All merges followed protocol: entity_connections migrated, data COALESCEd, losers marked `Merged/Duplicate`.

### 2. Entity Connection Building (+50 links)
- 3 new `current_employee` links
- 47 new `past_employee` links (from daily maintenance)
- 18 additional `past_employee` links (from cross-entity linker)
- Total connections: 23,736 -> 23,783

### 3. Thin Content Enrichment
- 633 companies had page_content under 50 chars (just `Name\nSector: X`)
- Rebuilt page_content from all available structured fields for those with extra data
- 11 companies improved to > 50 chars (had hidden data in jtbd, batch, sells_to, etc.)
- 621 remain thin -- these are truly minimal entities (name + sector only, zero other data)
- These require web enrichment by Datum agent to improve further

### 4. Signal Propagation
- All signals up to date (no-op)
- Network signal coverage: 100% (3,527/3,527)
- Portfolio signal coverage: 100% (142/142)

---

## Before/After Metrics

### Entity Health

| Metric | Before | After | Delta |
|--------|--------|-------|-------|
| Companies total | 4,579 | 4,579 | 0 |
| Companies merged/duplicate | 24 | 46 | +22 |
| Companies has_website | 762 (16.6%) | 763 (16.7%) | +1 |
| Companies page_content > 50 | 3,946 (86.2%) | 3,957 (86.4%) | +11 |
| Companies embedding | 100% | 100% | stable |
| Network total | 3,527 | 3,527 | 0 |
| Network embedding | 100% | 100% | stable |
| Network signals | 100% | 100% | stable |
| Portfolio page_content | 100% | 100% | stable |
| Portfolio signals | 100% | 100% | stable |
| Portfolio thesis | 64.8% | 64.8% | stable |
| Actions total | 145 | 145 | 0 |
| Actions company_link | 82.1% | 82.1% | stable |
| Actions thesis | 69.0% | 69.0% | stable |
| Entity connections | 23,736 | 23,783 | +47 |
| Embedding queue | 0 | 0 | clean |

### Quality Checks (all pass)

| Check | Status |
|-------|--------|
| Orphaned entity_connections | 0 |
| Garbage entries | 0 |
| Stale proposed actions | 0 |
| Stale companies (30d) | 0 |
| Pseudo-ID count | 0 |
| Exit consistency | OK |

---

## Remaining Gaps (structural, not regressions)

| Gap | Count | Root Cause | Fix Path |
|-----|-------|------------|----------|
| Companies thin content (<50 chars) | 621 | Minimal entities, zero structured data beyond name+sector | Datum agent web enrichment |
| Companies no website | 3,816 | Most are peripheral network companies, not pipeline | Web enrichment for pipeline companies only |
| Portfolio no thesis | 50 | Missing thesis_connection from Notion | Notion sync or manual assignment by user |
| Actions no company link | 26 | Content-pipeline generated actions without company resolution | Datum agent resolution |
| Network first-name-only with LinkedIn | 7 | Incomplete import from Notion | Datum agent LinkedIn scraping |
| Network duplicates (same name, different roles) | ~60 pairs | Same-name different people across companies | Legitimate, not real duplicates |
| Network garbage (org entries + empty name) | 14 | Orgs stored as network rows in Notion | Flagged, not auto-deleted (Notion sync risk) |

---

## User Feedback (from digest.wiki widget)

5 new feedback entries since last check (ids 17-20), all on `/comms` page:
- **Bug:** Duplicate Ayush entries in "you owe" section (M11 obligations issue)
- **Bug:** Clicking Rajat Agarwal card does nothing (M1 WebFront bug)
- **General:** Intract urgency status wrong -- portfolio but not priority (M5 scoring issue)
- **General:** Quivly deal negotiation reasoning poor (M5/M7 issue)

None are M12 data enrichment issues.

---

## Datum Agent Enrichment Skills Status

All agent files verified present at `mcp-servers/agents/`:
- `datum/CLAUDE.md` -- 233 lines, references all 14 SQL tools
- `skills/datum/autonomous-enrichment.md` -- regression detection, batch dedup, scorecard
- `skills/datum/enrichment.md` -- 5 enrichment SQL functions, loop template
- `skills/datum/data-quality.md` -- 6 maintenance functions
- `skills/datum/dedup-algorithm.md` -- 4-tier dedup
- `skills/datum/identity-resolution.md` -- confidence gating
- `skills/datum/people-linking.md` -- 6-tier people resolution
- `skills/datum/datum-processing.md` -- processing checklist

**Agent build status:** Skills written, CLAUDE.md written. Agent NOT yet deployed to droplet (per CHECKPOINT.md -- requires `deploy.sh`).

---

## Next Loop Priorities

1. **Run datum_daily_maintenance() results action:** 7 first-name-only with LinkedIn -- these need Datum agent to scrape LinkedIn for full names
2. **Monitor new entity ingestion** from content pipeline when restarted
3. **Portfolio thesis backfill** -- 50 portfolio entries need thesis_connection (user/Notion decision, not auto-fillable)
4. **Watch for regressions** on next Notion sync cycle
