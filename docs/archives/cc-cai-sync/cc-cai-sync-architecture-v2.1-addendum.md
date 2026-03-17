# CC ↔ CAI Sync Architecture — v2.1 Addendum
## Revised CAI Projects Model, Cash Build System Integration, and Tag-Based Organization

**Date:** March 12, 2026  
**Version:** 2.1 (addendum to v2.0 — this replaces Sections 4.2, 6, and adds new Sections 13-14)  
**Status:** Architecture Final → Ready for Phased Implementation

---

## Changes from v2.0

1. **Section 4.2 (Session Hooks)** — replaced with Cash Build System integration note
2. **Section 6 (CAI Projects Structure)** — completely rewritten based on deep interview
3. **New Section 13** — Tag-Based Organization System (Apple Notes model for CAI)
4. **New Section 14** — Claude's Role in Auto-Suggesting Connections

---

## REVISED: Section 4.2 — Sync Hooks & Cash Build System Integration

### 4.2 Sync Triggers: Beyond Session Close

**Important architectural note:** The v2.0 architecture assumed sync happens at session close.
This is WRONG for Aakash's workflow.

Aakash has an existing **Cash Build System** in CC — a custom command (`/cash-build-system`)
with hooks that update states in Notion (roadmap tracking, etc.) at various points during a
session, NOT only at session close.

**Requirement:** The CC↔CAI sync (state.json update, inbox append, git push) must fire
at the same trigger points as the Cash Build System hooks — on state changes, not just
session boundaries.

**Design implication:** Phase 3A (Session Lifecycle Hooks) CANNOT be designed in isolation.
It requires:

1. **First:** Deep understanding of Cash Build System hook architecture
   - What events trigger hooks? (file changes? Notion writes? manual triggers?)
   - What state do hooks update? (roadmap DB? build status? other?)
   - How are hooks implemented? (git hooks? CC hooks? custom scripts?)
   - What's the execution context? (inline? async? subagent?)

2. **Then:** Design CC↔CAI sync as an ADDITIONAL hook in the same system
   - Sync fires when Cash Build System fires (same trigger points)
   - state.json and inbox.jsonl updates happen alongside existing Notion updates
   - Git push batched with other push operations if applicable

3. **Result:** CC↔CAI sync becomes a natural extension of Cash Build System,
   not a separate mechanism. One hook system, multiple outputs.

**This is a CC-side design task.** CAI cannot design these hooks without first
examining the Cash Build System code. The architecture doc provides the WHAT
(state.json, inbox.jsonl, git push) — CC determines the WHEN and HOW based
on existing hook infrastructure.

**Placeholder for CC:**
```
# In CC, when designing sync hooks:
# 1. Read this architecture doc
# 2. Examine Cash Build System hook architecture
# 3. Add CC↔CAI sync as a hook that fires alongside existing hooks
# 4. Ensure state.json + inbox.jsonl + git push happen at same trigger points
# 5. Session close is ONE trigger, not the ONLY trigger
```

---

## REVISED: Section 6 — CAI Projects Structure

### The Interview Findings

Deep interview with Aakash revealed:

- **Five identities that blur constantly:** Investor, Builder, AI/Agentic Developer, Researcher, Operator
- **Work is a compounding flywheel:** Threads → builds → validation → analysis → evolved threads → new builds
- **Retrieval is associative/fuzzy:** Breadcrumbs + keywords + recognition, not hierarchical navigation
- **Rigid buckets fail:** A conversation about CC↔CAI sync is simultaneously infrastructure, builder-skill, and operator-tooling. It can't live in one folder.
- **Many lightweight projects preferred:** Not 4 mega-containers, but 15-20+ focused context spaces
- **CC builds have their own projects, but research/thinking is more fluid** — with research threads also getting projects when they mature
- **Chats should be taggable/linkable to multiple projects** — Apple Notes model
- **Claude should auto-suggest connections** between chats and projects

### 6.1 The Three-Zone Model

Instead of rigid categories, CAI Projects organize into three natural zones:

```
┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│  ZONE 1: BUILD PROJECTS                                                  │
│  One CAI Project per CC repo/build                                       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐     │
│  │ AI CoS   │ │ CC↔CAI   │ │ Skill    │ │ DeVC     │ │ Content  │     │
│  │ MCP      │ │ Sync     │ │ Factory  │ │ Tools    │ │ Pipeline │     │
│  │ Server   │ │ System   │ │          │ │          │ │          │     │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘     │
│  • GitHub repo connected                                                │
│  • state.json, inbox.jsonl loaded                                       │
│  • CLAUDE.md as project instructions                                    │
│  • Deep code context available                                          │
│  • New ones created as new CC projects emerge                           │
│                                                                          │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ZONE 2: RESEARCH & THINKING THREADS                                     │
│  One CAI Project per sustained research/learning arc                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐     │
│  │ Context  │ │ Agentic  │ │ MCP      │ │ Cyber-   │ │ Deep     │     │
│  │ Engineer-│ │ AI Infra │ │ Ecosystem│ │ security │ │ Tech     │     │
│  │ ing      │ │ Thesis   │ │ Research │ │ Thesis   │ │ Mobility │     │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘     │
│  • No GitHub repo (or optional reference repo)                          │
│  • Knowledge base: key papers, articles, prior research                 │
│  • Project instructions: research context, key questions, thesis state  │
│  • Thesis threads map here naturally                                    │
│  • Created when a topic becomes sustained (not for one-off research)    │
│  • These INFORM builds and RECEIVE evidence from builds                 │
│                                                                          │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ZONE 3: OPERATIONAL SPACES                                              │
│  One CAI Project per ongoing operational function                        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                                │
│  │ Z47/DeVC │ │ Meeting  │ │ Personal │                                │
│  │ Investing│ │ Prep &   │ │ OS &     │                                │
│  │ Ops      │ │ Debrief  │ │ Workflows│                                │
│  └──────────┘ └──────────┘ └──────────┘                                │
│  • Persistent context for recurring activities                          │
│  • Knowledge base: frameworks, templates, key docs                      │
│  • These don't map to CC repos but are always-on contexts               │
│  • Deal analysis, IDS work, meeting prep, fund operations               │
│                                                                          │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ZONE 0: EPHEMERAL (No Project)                                         │
│  Standalone chats — travel, quick queries, one-off questions             │
│  No project context needed. Uses global memory only.                     │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### 6.2 Key Design Principles

**Projects are lightweight and many (15-20+), not heavy and few.**
Creating a new project should feel as easy as creating a new Apple Notes folder.
Don't overthink it — if something becomes a sustained thread of work or thinking,
it gets a project. If it doesn't, it stays ephemeral.

**Projects are context containers, not filing cabinets.**
The primary purpose is: when you start a chat in this project, Claude has the right
background loaded. The secondary purpose is retrieval.

**Projects can be born from chats.**
A standalone chat about "context engineering" that gets deep enough → becomes a
research thread project. You just move the chat (or start a new one) and add the
prior chat's insights to the project knowledge base.

**Projects can die or go dormant.**
Not everything stays active. Projects can be archived when a research thread
concludes or a build ships. They remain searchable but don't clutter active view.

**The flywheel is explicit.**
Build projects and research thread projects reference each other in their
instructions. The AI CoS MCP Server project instructions mention the Agentic AI
Infra thesis thread. The thesis thread's knowledge base contains evidence from
the build. This makes the connections visible to Claude.

### 6.3 Project Instructions Template (Revised)

Each project gets lightweight but structured instructions:

```markdown
## Project: {NAME}
Zone: {build | research | ops}
Status: {active | paused | archived}

## Context
{2-3 sentences on what this is and why it exists}

## Connected To
- Builds: {list of related build projects}
- Threads: {list of related research/thesis threads}
- Ops: {list of related operational spaces}
- Thesis: {thesis tracker thread name, if applicable}

## CC Sync
{For build projects only}
- Repo: {github URL}
- State: check .claude/sync/state.json for current state
- Inbox: check .claude/sync/inbox.jsonl for communications

## Key Context
{Project-specific context Claude needs}

## When Chatting Here
- Check state.json before discussing build status
- Check inbox for pending messages from the other surface
- At end of conversation, suggest which other projects this chat relates to
- If a decision was made, flag it for the inbox
```

### 6.4 Starter Project List

Based on the interview, here's a proposed starting set. Aakash should modify freely:

**Zone 1 — Build Projects:**
| # | Project Name | GitHub Repo | Notes |
|---|---|---|---|
| 1 | AI CoS MCP Server | ai-cos-mcp | The core AI CoS system |
| 2 | CC↔CAI Sync System | cc-cai-sync (or within ai-cos) | This project |
| 3 | Skill Factory | skill-factory (or within ai-cos) | CC skills and plugins |
| 4 | Content Pipeline | content-pipeline (or within ai-cos) | Content processing tools |
| 5 | DeVC Tools | devc-tools | DeVC-specific tooling |
| 6+ | (created as new builds emerge) | | |

**Zone 2 — Research & Thinking Threads:**
| # | Project Name | Notes |
|---|---|---|
| 7 | Agentic AI Infrastructure | Thesis thread — high conviction |
| 8 | Cybersecurity / Pen Testing | Thesis thread |
| 9 | Context Engineering | Learning arc — informs all builds |
| 10 | MCP Ecosystem Deep Dive | Protocol, servers, patterns |
| 11+ | (created as research threads mature) | |

**Zone 3 — Operational Spaces:**
| # | Project Name | Notes |
|---|---|---|
| 12 | Z47/DeVC Investing Ops | Deal analysis, IDS, pipeline, fund ops |
| 13 | Meeting Prep & Debrief | People research, meeting context |
| 14 | Builder's Workshop | Meta-learning about being a better AI developer, system architect |
| 15+ | (created as operational needs emerge) | |

**Zone 0 — Ephemeral:** No projects. Standalone chats. Travel, quick queries, etc.

**Note:** "Builder's Workshop" (Project 14) is where THIS conversation lives.
CC↔CAI sync is a *build* (Project 2), but the thinking/design/research about it
happens in the Builder's Workshop. The build project has the code; the workshop
has the architectural thinking. They're connected but distinct.

---

## NEW: Section 13 — Tag-Based Organization System

### 13.1 The Problem

CAI doesn't have native tags. A chat lives in one Project (or none). But Aakash's
work is associative — a single conversation might be relevant to 3 different projects.
Apple Notes solves this with tags + Smart Folders. We need an equivalent.

### 13.2 The Solution: Convention-Based Tags + Memory + Past Chat Search

Since CAI can't do native tags, we implement tagging through conventions and
Claude's existing capabilities:

**Layer A: Chat Naming Convention**
Every non-ephemeral chat gets a structured name with inline tags:

```
[tag1, tag2] Descriptive Title — Date or Context

Examples:
[ai-cos, context-eng] Designing state sync architecture — Mar 11
[thesis, agentic-infra] Composio deep dive and competitive analysis
[devc, meeting-prep] Pre-meeting research: Company X Series A
[builder, mcp] MCP authentication patterns for remote servers
[ai-cos, sync, builder] CC↔CAI inbox protocol design session
```

**Why this works:**
- Tags in brackets are searchable via CAI's past chat search
- Multiple tags = discoverable from multiple angles
- Descriptive title = the breadcrumb that triggers recognition
- You can search `[ai-cos]` to find all AI CoS-related chats across any project
- You can search `[thesis]` to find all thesis-related work
- You can search `[builder]` to find all meta-learning about being a better developer

**Tag Taxonomy (starter — evolve over time):**

| Tag | Meaning |
|---|---|
| `ai-cos` | AI Chief of Staff system |
| `sync` | CC↔CAI sync system |
| `skill-factory` | Skills and plugins |
| `content` | Content pipeline |
| `devc` | DeVC fund work |
| `z47` | Z47 fund work |
| `thesis` | Thesis thread work |
| `agentic-infra` | Agentic AI infrastructure thesis |
| `cybersec` | Cybersecurity thesis |
| `context-eng` | Context engineering learning |
| `mcp` | MCP protocol/ecosystem |
| `builder` | Meta-learning: being a better developer/architect |
| `meeting-prep` | Pre-meeting research |
| `meeting-debrief` | Post-meeting analysis |
| `ids` | IDS (Increasing Degrees of Sophistication) work |
| `deal` | Specific deal analysis |
| `research` | Deep research session |
| `brainstorm` | Thinking/ideation session |
| `decision` | Decision-making session |

**Layer B: Claude Memory as Tag Index**
Claude's memory (updated periodically) can track significant chats and their tags.
This gives Claude ambient awareness of what's been discussed where.

When you ask "what have I been working on related to context engineering?",
Claude can search past chats for `[context-eng]` AND check memory for related notes.

**Layer C: End-of-Chat Connection Prompt**
At the end of substantive chats, Claude suggests:

```
📎 This conversation connects to:
- [AI CoS MCP Server] — the state sync pattern we discussed applies to action queue
- [Context Engineering] — the inbox protocol is a context engineering pattern
- [Agentic AI Infra thesis] — validates middleware layer thesis

Want me to note any of these connections? Or flag anything for the CC inbox?
```

### 13.3 How Tags Interact with Projects

A chat LIVES in one project (or standalone) but is TAGGED for multiple.

```
Chat: "[ai-cos, sync, builder] CC↔CAI inbox protocol design"
Lives in: "CC↔CAI Sync System" project (Zone 1 build project)
Tagged for: ai-cos, sync, builder
Discoverable from: AI CoS project, Builder's Workshop, Sync project
```

The project provides Claude the RIGHT CONTEXT for the conversation.
The tags provide YOU the retrieval paths to find it later.

**Rule of thumb for where to start a chat:**
- If it's primarily about building/coding → start in the relevant Build project (Zone 1)
- If it's primarily research/thinking → start in the relevant Thread project (Zone 2)
- If it's operational → start in the relevant Ops project (Zone 3)
- If unsure → start standalone, tag it, promote to a project later if it grows

---

## NEW: Section 14 — Claude's Role in Auto-Suggesting Connections

### 14.1 When Claude Should Suggest Connections

Claude auto-suggests project/tag connections when:

1. **End of substantive chat** — "This conversation connects to: [X, Y, Z]"
2. **Cross-project insight** — "This pattern from Context Engineering might apply to your AI CoS build"
3. **Thesis relevance** — "This finding is evidence for/against your [Thesis Thread] thesis"
4. **Inbox-worthy decision** — "This decision should be noted in the [Project] inbox"
5. **New project trigger** — "This topic has come up 3 times now — worth creating a dedicated project?"

### 14.2 How Claude Detects Connections

Claude uses several signals:

- **Project instructions:** Each project lists its connections ("Connected To" section)
- **Tag taxonomy:** When a chat's content matches known tags
- **Memory:** Prior chats and their tags, accumulated context
- **Inbox messages:** Recent decisions/notes from other projects
- **Thesis tracker:** Active thesis threads from Notion
- **State files:** Current state of CC build projects

### 14.3 What Claude Does NOT Do

- Claude does NOT auto-create projects (suggests, user decides)
- Claude does NOT auto-tag without confirmation (suggests tags, user approves)
- Claude does NOT move chats between projects (CAI doesn't support this)
- Claude does NOT auto-write to inbox (flags decisions, user confirms)

---

## Updated Phase Plan (changes only)

### Phase 1A (Revised): CAI Projects Setup

**Before:**
- Create 4 mega-projects by category

**After:**
- Create ~15 starter projects across three zones (see Section 6.4)
- Each build project gets GitHub repo connected
- Each project gets lightweight instructions (Section 6.3 template)
- Establish tag taxonomy (Section 13.2)
- This is a ~60-minute setup, not 30

### Phase 3A (Revised): Sync Hooks

**Before:**
- Add sync to session close checklist

**After:**
- Step 1: Examine Cash Build System hook architecture in CC
- Step 2: Design CC↔CAI sync as additional hook in same system
- Step 3: Sync fires at Cash Build System trigger points, not just session close
- Step 4: Session close is one trigger among several

### New: Phase 1C — Tag Convention Adoption

**Surface: CAI**
**Dependency: Phase 1A**

- [ ] Adopt chat naming convention: `[tag1, tag2] Title`
- [ ] Start tagging new chats going forward
- [ ] Claude begins suggesting connections at end of substantive chats
- [ ] Retroactively tag/rename important recent chats (optional)
- [ ] Evolve tag taxonomy as natural categories emerge

---

## Summary: What Changed from v2.0

| Aspect | v2.0 | v2.1 |
|---|---|---|
| CAI Projects | 4 mega-buckets by category | 15-20+ lightweight projects in 3 zones |
| Organization model | Folder-based hierarchy | Tags + Projects (Apple Notes style) |
| Chat discoveryability | One project per chat | Tags make chats findable from multiple angles |
| Sync triggers | Session close only | Cash Build System hook integration (TBD in CC) |
| Claude's role | Passive context provider | Active connection suggester |
| Research threads | Lumped into categories | First-class projects (Zone 2) |
| New project creation | Rare, heavyweight | Common, lightweight — as easy as a new note |
| Flywheel visibility | Implicit | Explicit via cross-project references + tags |
