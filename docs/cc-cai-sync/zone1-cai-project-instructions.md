# Zone 1: CAI Project Instructions
## Ready for CC to create in claude.ai

**Date:** March 12, 2026  
**For:** CC to create 4 CAI Projects with GitHub repos connected

---

## How to Create Each Project

For each project below:
1. Go to claude.ai → Projects → + New Project
2. Set the name as specified
3. Paste the project instructions into "Project Instructions"
4. Add the GitHub repo via "+" in knowledge base → Connect GitHub
5. Select relevant files (prioritize: CLAUDE.md, .claude/sync/*, key architecture files)
6. Done

---

## Project 1: AI CoS Build

**GitHub Repo:** https://github.com/RTinkslinger/aicos-cc-adk  
**Zone:** Build (Zone 1)  
**Priority:** High — primary project, sync pilot complete

### Project Instructions:

```
This is the AI CoS (AI Chief of Staff) build project — Aakash's primary system.

WHAT THIS IS:
An action optimizer answering "What's Next?" across Aakash's full stakeholder and action space. Not a tool — an extension of how he thinks. Built on FastAPI + FastMCP, deployed on Railway with Postgres + Notion dual-write.

CC↔CAI SYNC:
This project has CC↔CAI sync active. Key files in the repo:
- .claude/sync/state.json — current build state (updated by CC on session boundaries)
- .claude/sync/inbox.jsonl — bidirectional communication log between CC and CAI
- .claude/sync/project.json — project metadata
- CLAUDE.md — project instructions and architecture context

WHEN CHATTING HERE:
- Check state.json before discussing current build status or priorities
- Check inbox.jsonl for unacknowledged messages from the other surface
- Reference CLAUDE.md for architecture decisions and patterns
- At end of substantive chats: suggest tags, note cross-project connections, flag inbox-worthy decisions
- Don't hardcode specific tool counts, phase percentages, or scoring details — these evolve. Check state.json for current state.

CONNECTED TO:
- Thesis: Agentic AI Infrastructure (the system validates harness layer thesis)
- Builds: CC↔CAI Sync System (sync infrastructure), Skills Factory (skills used in AI CoS), Content Pipeline (sub-system)
- Ops: Z47/DeVC Investing Ops (AI CoS serves the investing workflow)

KEY NOTION DBS:
- Thesis Tracker: 3c8d1a34 (AI-managed autonomously)
- Actions Queue: 1df4858c
- Build Roadmap: 6e1ffb7e
- Content Digest: df2d73d6
```

---

## Project 2: CC↔CAI Sync System

**GitHub Repo:** https://github.com/RTinkslinger/cc-cai-sync  
**Zone:** Build (Zone 1)  
**Priority:** High — the sync infrastructure itself

### Project Instructions:

```
This is the CC↔CAI Sync System — infrastructure for bidirectional sync between Claude Code and Claude.ai.

WHAT THIS IS:
Architecture docs, sync hook scripts, and handoff plans for keeping CC and CAI aware of each other's project states. 4-layer stack: L0 (CAI memory), L1 (CAI Projects + GitHub sync), L2 (Notion CC Project States DB), L3 (cc-state-mcp server, future).

KEY FILES:
- docs/ — Architecture v2.0, v2.1 addendum, v2.2 addendum (CBS analysis), foundation chat summary
- hooks/ — Reference implementations: sync-pull.sh, sync-push.sh, settings fragment
- projects-registry.json — Complete registry of all CC projects
- cc-handoff-plan.md — Step-by-step implementation plan

THE INBOX PROTOCOL:
Core innovation — append-only JSONL (.claude/sync/inbox.jsonl) as bidirectional time-series communication log. Message types: decision, question, answer, task, status, note, research, flag, ack.

WHEN CHATTING HERE:
- This is meta-infrastructure — conversations here are about the sync system itself
- Reference architecture docs for design decisions
- When discussing improvements, check current implementation state in hooks/
- Flag decisions for inbox if they affect how other projects sync

CONNECTED TO:
- All other build projects (this serves them all)
- Builder's Workshop (meta-learning about multi-surface workflows)
- Agentic AI Infra thesis (validates middleware/harness layer value)
```

---

## Project 3: Flight Mode Plugin

**GitHub Repo:** https://github.com/RTinkslinger/Claude-Code-Flight-Mode  
**Zone:** Build (Zone 1)  
**Priority:** Medium

### Project Instructions:

```
This is Flight Mode — a publishable Claude Code plugin for in-flight WiFi resilience.

WHAT THIS IS:
Micro-task checkpointing, context budgeting, and airline-specific profiles for using Claude Code on unreliable in-flight WiFi. Built as a CC plugin with Bash/JSON/Markdown.

CC↔CAI SYNC:
Once .claude/sync/ is initialized (pending /sync-migrate), state.json and inbox.jsonl will be available. Until then, check CLAUDE.md and repo files for current state.

WHEN CHATTING HERE:
- Check the repo for current build state and ROADMAP.md
- This is a standalone publishable project, not part of AI CoS
- Has full Cash Build System (v1.1-beta) with 6 hooks deployed

CONNECTED TO:
- Skills Factory (plugin development methodology)
- Builder's Workshop (CC plugin patterns and best practices)

NOTION:
- Build Roadmap item ID: bf79137a-3a67-457c-84ce-3578f13c32b7
```

---

## Project 4: Skills Factory

**GitHub Repo:** https://github.com/RTinkslinger/skills-factory  
**Zone:** Build (Zone 1)  
**Priority:** Medium

### Project Instructions:

```
This is Skills Factory — skill development workspace with SKILL-CRAFT methodology.

WHAT THIS IS:
Workspace for developing CC skills and plugins. Uses SKILL-CRAFT methodology with per-skill development logs and an expertise transfer system. Some skills feed into AI CoS, some are general-purpose.

CC↔CAI SYNC:
Once .claude/sync/ is initialized (pending /sync-migrate), state.json and inbox.jsonl will be available. Until then, check CLAUDE.md and repo files for current state.

WHEN CHATTING HERE:
- Check the repo for available skills and development logs
- Has full Cash Build System (v1.1-beta) with 6 hooks deployed
- ROADMAP.md checkout/commit model active

CONNECTED TO:
- AI CoS Build (skills used in AI CoS system)
- Flight Mode (plugin patterns)
- Builder's Workshop (skill development as a meta-learning process)
```

---

## After Creation: Verification Checklist

For each project, verify:
- [ ] Project created with correct name
- [ ] GitHub repo connected and files visible
- [ ] Project instructions pasted
- [ ] Can start a chat and reference repo files
- [ ] For AI CoS: state.json readable, inbox.jsonl accessible

Then return to CC for Steps 6-7:
- Run /sync-migrate on flight-mode and skills-factory
- Push .claude/sync/ files to GitHub
- Verify sync hooks firing on all projects

---

## What's Parked (Zone 2 & Zone 3)

Zone 2 (Research Threads) and Zone 3 (Ops Spaces) are parked until:
1. Zone 1 is fully live with GitHub sync working
2. AI CoS is in sync state (full context available)
3. Deep interviews conducted in CAI with full context loaded
4. Plans produced → CC builds them

This follows the build principle: infrastructure follows friction. Don't build speculatively.
