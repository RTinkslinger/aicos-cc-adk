# Iteration Log: Session 001 (Continued) — The Network OS Reframe

**Date:** March 1, 2026  
**Interface:** Claude.ai (chat)  
**Plan Version:** 0.2 → 0.3

## The Critical Reframe

When asked "what's the biggest time sink a human CoS would handle first?", Aakash didn't pick any of the four options offered (email triage, meeting prep, deal memos, portfolio tracking). Instead, he reframed:

> "Managing my life around founder, investor interactions. I lead a very networked life and that is my strength. The core of my life's work is my network and my CoS needs to give me the most leverage on that."

This changes the entire architecture. The AI CoS is not a productivity tool — it's a **Network Operating System**.

## Key Findings

### Network Scale & Dynamics
- **1,000–2,000 active relationships** across 11+ categories
- **Outbound-first networker** — #1 source of new relationships is own research (rare among VCs)
- **Interactions mostly unlogged** — new meetings often stay in memory, never hit a system
- **Follow-ups are #1 pain** — things fall through cracks after meetings
- **EA (Sneha) handles logistics** (scheduling, travel, admin) but NOT the intelligence layer

### Relationship Taxonomy Identified
1. Angel portfolio founders (100+ from personal decade)
2. DeVC portfolio founders (140–150/cycle)
3. Z47 portfolio founders (~45/cycle)
4. Prospective founders (active deal pipeline)
5. Beyond-strike-zone founders (deal flow + learning sources)
6. Future founders (operators today, potential founders tomorrow)
7. Founder-angels (potential IC additions)
8. Independent Capitalists (50+ DeVC collective)
9. Other VCs (co-invest, competitive intel)
10. LPs (current + prospective)
11. Operators/executives (hiring network for portcos)

Key insight: people span multiple categories. Data model must support multi-tagging.

### Lines Over Dots Tracking
Currently: unstructured notes in docs and emails. No structured system. This is a massive gap for DeVC's core strategy (1-in-7 follow-on decision depends on accumulated observations).

## Architecture Decisions

### ADR-002: Network OS as Foundation Workstream
- All workstreams (deal flow, portfolio, IC management, content) are specialized views into the network
- WS0 (Network OS) with 6 layers: Capture, Contextualize, Prioritize, Prepare, Follow-Through, Grow
- Sprint plan resequenced: network skills first, then deal/portfolio skills

### ADR-003: Network Data Model (Draft)
- Three core tables: People, Companies, Interactions
- Portable design: works in G-Sheets (Phase A) and transfers to Attio (Phase B)
- Key fields: relationship_strength, relevance_score, follow_up_due, last_interaction
- Multi-category tagging on People (person can be founder + IC + portfolio)

## What Changed in the Plan
- Added "A Network Operating System for Venture" as project tagline
- Created WS0 as foundation workstream with 6 detailed layers
- Added relationship taxonomy table (11 categories with CoS needs)
- Drafted network data model (People, Companies, Interactions tables)
- Resequenced Sprint 1: network-brief + interaction-log + followup-engine as first skills
- Sprint 2 now focused on the follow-through engine (daily digest, going-cold alerts)
- Updated file system: added network-specific skills and data directories

## Still Open
- Team structure at both funds
- Outbound research process details
- Historical deal data location/format
- Attio API access
- Content creation process
- Right to play / right to win

## Files Produced
- `Aakash_AI_CoS_Master_Plan_v03.docx` — Major reframe document
- Updated iteration log (this file)
- ADR-002, ADR-003 referenced (to be written as standalone files)
