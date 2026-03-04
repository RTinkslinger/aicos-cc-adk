# Cowork Instructions: Aakash AI CoS

## How to Start

When Aakash opens this folder in Cowork, start by reading these files in order:
1. This file (`COWORK_INSTRUCTIONS.md`)
2. `SESSION_001_SUMMARY.md` — full context from the planning interview
3. `README.md` — project overview

Then tell Aakash you have full context and are ready to begin the understanding phase.

## Current Phase: Understanding (Network Taxonomy Discovery)

We are NOT building yet. We are learning.

### The Goal
Build a grounded, data-informed relationship taxonomy model by studying Aakash's actual network data in Notion, interviewing him, and doing case-by-case breakdowns.

### Step 1: Explore the Notion Network DB
- Use the Notion connector to search and access DeVC's Network DB and Companies DB
- Study the schema: what fields exist? What categories/tags are used?
- Understand the data quality: how complete are records? What's missing?
- Count records, identify patterns, look at how relationships are categorized today
- Document findings in `docs/iteration-logs/`

### Step 2: Interview Aakash with Real Data
- Pull specific people from the Network DB and ask Aakash about them
- "Tell me about this person — what's the relationship, how did you meet, why do they matter?"
- Look for edge cases: people who span multiple categories, relationships that are hard to classify
- Understand the implicit mental model Aakash uses to think about his network
- Pay attention to the language he uses — his natural categories may differ from the preliminary taxonomy

### Step 3: Case-by-Case Breakdowns
- Pick 20-30 diverse examples from the DB and go deep on each
- For each: what category are they, what's the interaction history, what value flows between you, what would ideal AI CoS support look like for this relationship?
- Identify patterns: do natural clusters emerge that differ from the preliminary 11-category taxonomy?

### Step 4: Build the Taxonomy Model
- Synthesize findings into a final relationship taxonomy
- For each category: definition, typical interaction pattern, data needs, AI CoS requirements
- Validate with Aakash — does this match how he actually thinks about his network?
- Document as a formal deliverable in `docs/research/`

### Step 5: Then (and only then) plan the build
- Use the validated taxonomy to design the network data model
- Design skills and workflows that match actual relationship patterns
- Update the master plan

## Key Connectors to Use
- **Notion:** For accessing DeVC Network DB and Companies DB. This is the primary data source for the understanding phase.
- **Granola:** For reviewing recent meeting notes if helpful for understanding interaction patterns.
- **Web search:** For enriching context about specific people when doing case-by-case breakdowns.

## Documentation Discipline
Every Cowork session should produce or update:
- An iteration log in `docs/iteration-logs/` with session date, what was explored, what was learned
- Any new findings added to research docs in `docs/research/`
- Updated open questions

## What NOT to Do
- Do NOT build skills, plugins, or MCP servers yet
- Do NOT create scheduled tasks or automations yet
- Do NOT design workflows until the taxonomy is validated
- Do NOT assume the preliminary 11-category taxonomy is correct — it's a hypothesis to be tested against real data

## Aakash's Working Style
- He prefers to be asked clarifying questions — lots of them
- He leads a multifaceted life (builder + investor) — keep both contexts in mind
- He's adept at coding and AI/ML — no need to simplify technical concepts
- He values the iterate-then-build approach — patchy exploration first, enterprise build later
- He wants to be deeply involved in the understanding phase, not just review outputs

## Project Principles
1. **First nail understanding, then start building**
2. **Document everything** — Phase B depends on Phase A learnings
3. **Portability** — any data model should work in G-Sheets and transfer to Attio
4. **Network-first** — everything flows from the network
5. **Real data over theory** — derive taxonomy from actual Notion data, not assumptions
