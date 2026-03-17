# Session 029 — Checkpoint
**Date:** 2026-03-04

## Design Decisions Made (Action Architecture Redesign)

### Content Digest DB — Action Status state machine (refined)
- `Pending` → Unreviewed inbox (set by pipeline on creation)
- `Reviewed` → All proposed actions triaged (each accepted → routed to tracker, or rejected). Terminal state if no actions accepted or none complete.
- `Actions Taken` → At least one downstream action marked Done (back-propagated from Actions Queue). Only state triggered by external event.
- `Skipped` → Dismissed without review / irrelevant / duplicate

Transitions: Pending → Reviewed | Skipped. Reviewed → Actions Taken. No backward moves. One-way linkage: Content Digest DB only receives "Done" signal from downstream. Dismissals at tracker level don't propagate back.

### Portfolio Actions Tracker → renamed "Actions Queue"
Single action sink for ALL action types (portfolio, thesis, network, research). Schema additions:
- `Thesis` relation → Thesis Tracker (new)
- `Source Digest` relation → Content Digest DB (new)
- `Company` remains but is optional (already is in practice)
An action can relate to a company, a thesis, or both.

### Thesis Tracker — NO changes
Stays as pure conviction/knowledge tracker. Thesis-related actions route through Actions Queue with Thesis relation. No actions embedded in thesis pages.

### Future: RL Loop (deferred)
Track acceptance rate + completion rate per content source, thesis, action type, relevance score. Data contract already satisfied by Source Digest provenance + Status outcomes in Actions Queue.

## What's Done
1. Content Digest DB deduplication (3 duplicates marked [DELETED])
2. Action Status lifecycle documented (current state)
3. Architecture redesign agreed

## What's In Progress
- Schema changes to Portfolio Actions Tracker (rename + add relations)

## Key IDs
- Portfolio Actions Tracker data source: `1df4858c-6629-4283-b31d-50c5e7ef885d`
- Thesis Tracker data source: `3c8d1a34-e723-4fb1-be28-727777c22ec6`
- Content Digest DB data source: `df2d73d6-e020-46e8-9a8a-7b9da48b6ee2`
