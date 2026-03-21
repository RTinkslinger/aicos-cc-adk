# Cindy + Datum Refactor Plan
*2026-03-20 — Correcting the agent architecture*
*STATUS: COMPLETED 2026-03-20*

## The Problem

Python processors (`email_processor.py`, `granola/processor.py`) contain signal extraction logic (regex patterns for action items, deal signals, thesis signals, obligation detection) that should be **Claude agent reasoning**. This violates Design Principle #6: "Python is lifecycle plumbing only."

Additionally, M12 Data Enrichment loops (one-time backfill, harmonization, entity linking) are running as CC subagents doing SQL — they should be **Datum agent work**.

## The Correct Architecture

```
RAW DATA EXTRACTION (Python scripts — plumbing only):
  whatsapp/extractor.py  → reads ChatStorage.sqlite → stages raw conversations
  email/fetcher.py       → calls AgentMail API → stages raw emails
  granola/fetcher.py     → calls Granola API → stages raw meeting data
  calendar/fetcher.py    → reads .ics / Granola cache → stages raw events

         ↓ Raw data in interaction_staging table ↓

DATUM (Claude Agent SDK — data & ops):
  → Resolves people: phone→network, email→network, name→network (6-tier algorithm)
  → Links conversations to companies, portfolio, thesis
  → Handles group chat participant mapping
  → Dedup, enrichment, embedding refresh
  → Backfill & harmonization (the M12 work)
  → Writes CLEAN, LINKED data to interactions table with proper foreign keys

         ↓ Clean, linked data ↓

CINDY (Claude Agent SDK — intelligent EA):
  → Reads clean interactions (already linked to people/companies by Datum)
  → Reasons about: WHO OWES WHOM WHAT (LLM, not regex)
  → Detects obligations (LLM reasoning, not regex)
  → Extracts signals (deal, thesis, relationship — LLM, not patterns)
  → Creates actions in actions_queue
  → Identifies context gaps
  → Routes thesis signals to Megamind
```

## What Was Done

### 1. Database Infrastructure
- [x] Created `interaction_staging` table with staging workflow columns
- [x] Added `cindy_processed` and `datum_staged_id` columns to `interactions` table
- [x] Created indexes for processing queries
- [x] Cleaned 11 regex-processed sample rows from interactions

### 2. Python Processors → Thin Fetchers
- [x] `email/email_processor.py` (785L) → `email/fetcher.py` (330L): pure AgentMail API + parse + stage
- [x] `granola/processor.py` (1069L) → `granola/fetcher.py` (280L): pure parse + stage
- [x] `whatsapp/extractor.py` (982L) → rewritten (380L): pure SQLite read + stage (no signals)
- [x] Created `calendar/fetcher.py` (250L): pure .ics parse + stage
- [x] Deleted `email/obligation_extractor.py` (393L) — regex obligation detection
- [x] Deleted `obligations/obligation_detector.py` (780L) — regex obligation detection
- [x] Deleted `calendar/ics_processor.py` (578L) — had people resolution inline
- [x] Updated all `__init__.py` files for new fetcher imports

### 3. Datum CLAUDE.md Updates
- [x] Added `interaction_staging`, `interactions`, `people_interactions` to tables
- [x] Added Section 3b: Interaction Staging Pipeline with full processing specs
- [x] Added Section 3c: M12 Data Enrichment as permanent machinery
- [x] Added `datum_staging_process` input type
- [x] Added 6-tier people resolution algorithm (moved from Cindy)
- [x] Added cross-surface identity stitching documentation
- [x] Updated skills reference to include `people-linking.md`

### 4. Cindy CLAUDE.md Updates
- [x] Changed identity from "Communications Observer" to "Communications Intelligence Analyst"
- [x] Added "You do NOT do data plumbing" principle
- [x] Updated table access: removed people resolution writes, added cindy_processed workflow
- [x] Added processing loop documentation (read unprocessed → LLM reason → mark processed)
- [x] Updated skills reference: removed people-linking, added obligation-reasoning + signal-extraction

### 5. New Skills Created
- [x] `skills/cindy/obligation-reasoning.md` — LLM-based obligation detection spec
- [x] `skills/cindy/signal-extraction.md` — LLM-based signal extraction spec
- [x] `skills/datum/people-linking.md` — 6-tier resolution (moved from cindy)

### 6. Orchestrator Updates
- [x] HEARTBEAT.md: Added Step 3f (Datum staging check) and Step 3g (Cindy intelligence check)
- [x] CLAUDE.md: Updated Cindy description and added anti-patterns 17-18
- [x] New flow: staging → Datum → Cindy (sequential, not parallel)

### 7. Deployment
- [x] Deployed to droplet via deploy.sh (all 3 services healthy)
- [x] Deleted old processor files from droplet
- [x] Cleaned __pycache__ artifacts

## Line Count Summary

| Before | After | Delta |
|--------|-------|-------|
| `email_processor.py` 785L | `email/fetcher.py` 330L | -455L |
| `obligation_extractor.py` 393L | DELETED | -393L |
| `granola/processor.py` 1069L | `granola/fetcher.py` 280L | -789L |
| `obligation_detector.py` 780L | DELETED | -780L |
| `whatsapp/extractor.py` 982L | `whatsapp/extractor.py` 380L | -602L |
| `ics_processor.py` 578L | `calendar/fetcher.py` 250L | -328L |
| **Total: 4,587L** | **Total: 1,240L** | **-3,347L regex removed** |

New skills: `obligation-reasoning.md` + `signal-extraction.md` = ~350L of LLM reasoning guidance.
