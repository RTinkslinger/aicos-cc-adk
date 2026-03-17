# CC ↔ CAI Maximum Sync Architecture v2
## With Bidirectional Inbox Protocol, Auto-Init, and Backward Compatibility

**Date:** March 11, 2026  
**Version:** 2.0  
**Author:** Claude (CAI) — for Aakash Kumar  
**Status:** Architecture Final → Ready for Phased Implementation

---

## 1. Design Principles

1. **CC is primary, CAI is companion** — CC owns project state; CAI reads and communicates
2. **Zero maintenance** — CC manages its own sync lifecycle automatically
3. **Works when Mac sleeps** — all shared state lives in cloud (Git + Notion + MCP server)
4. **New projects auto-setup** — `claude init` + git wires everything
5. **Existing projects migrate cleanly** — one-time backward compat script
6. **Inbox is a first-class primitive** — bidirectional, time-series, append-only communication log

---

## 2. The Sync Stack (Four Layers)

```
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 3: cc-state-mcp (build in CC — future)                  │
│  Deep state: code search, file read, structured queries        │
│  Drops in on top of Layers 0-2                                 │
├─────────────────────────────────────────────────────────────────┤
│  LAYER 2: Notion "CC Project States" DB                        │
│  High-level state: project summaries, status, last session     │
│  CC writes on session close → CAI reads via Notion MCP         │
├─────────────────────────────────────────────────────────────────┤
│  LAYER 1: CAI Projects + GitHub Repo Sync                      │
│  Deep state: CLAUDE.md, code files, state.json, inbox          │
│  CC pushes to GitHub → CAI reads via Project knowledge base    │
├─────────────────────────────────────────────────────────────────┤
│  LAYER 0: CAI Memory                                           │
│  Always-on: project names, categories, key context             │
│  Instant awareness in every CAI conversation                   │
└─────────────────────────────────────────────────────────────────┘
```

Each layer is independently useful. Together they provide full-spectrum sync.

---

## 3. The `.claude/sync/` Directory Standard

Every CC project gets this directory structure. This is the **contract** between surfaces.

```
project-root/
├── CLAUDE.md                    # Existing — project instructions (already standard)
├── .claude/
│   ├── settings.json            # Existing — CC project settings
│   ├── settings.local.json      # Existing — local overrides (gitignored)
│   ├── rules/                   # Existing — scoped rules
│   └── sync/                    # NEW — the CC↔CAI sync directory
│       ├── state.json           # Machine-readable project state snapshot
│       ├── inbox.jsonl          # Bidirectional time-series communication log
│       ├── project.json         # Project registry metadata (name, category, etc.)
│       └── .gitkeep
├── .gitignore                   # Ensures sync/ is tracked, local files excluded
└── (project code files)
```

### 3.1 `state.json` — Project State Snapshot

Updated by CC on every session close. CAI reads this to understand current project state.

```json
{
  "schema_version": "1.0",
  "project": {
    "name": "ai-cos-mcp",
    "category": "ai-cos",
    "description": "AI Chief of Staff MCP server — action optimizer",
    "repo_url": "https://github.com/aakash/ai-cos-mcp"
  },
  "state": {
    "status": "active",
    "last_session": {
      "number": 47,
      "timestamp": "2026-03-11T23:45:00+05:30",
      "summary": "Implemented bidirectional action sync with Notion. Fixed scoring model edge case for follow-on decisions.",
      "duration_minutes": 120
    },
    "current_tasks": [
      "Content pipeline v5 scoring integration",
      "Action sync retry queue optimization"
    ],
    "recent_decisions": [
      {
        "decision": "Switched to Redis for action queue caching",
        "rationale": "Notion API rate limits were causing sync delays",
        "date": "2026-03-11"
      }
    ],
    "blocked_on": [],
    "next_session_priorities": [
      "Test content pipeline end-to-end",
      "Review CAI inbox for pending decisions"
    ],
    "key_files_changed_last_session": [
      "src/pipelines/content.py",
      "src/scoring/action_model.py"
    ]
  },
  "architecture": {
    "summary": "FastAPI MCP server deployed on Railway. Postgres for persistent state, Notion for user-facing data, Redis for caching. Bidirectional sync with Notion databases.",
    "stack": ["Python", "FastAPI", "PostgreSQL", "Redis", "Notion API"],
    "key_patterns": [
      "MCP tool dispatch via FastMCP",
      "Dual-write: Postgres + Notion",
      "Action scoring model: 7-factor weighted"
    ]
  },
  "updated_at": "2026-03-11T23:45:00+05:30",
  "updated_by": "cc"
}
```

### 3.2 `inbox.jsonl` — The Bidirectional Communication Protocol

This is the core innovation. The inbox is an **append-only, time-series log** of messages between surfaces. Each line is a JSON object representing one communication.

**Design:**
- Append-only JSONL (JSON Lines) — each line is independent
- Both CC and CAI can write to it
- CC writes via direct file append → git push
- CAI writes via GitHub API (Layer 3: MCP server) or manual paste for now
- Messages are never deleted, only read-acknowledged
- Acts as a persistent communication channel AND an audit trail

**Message Schema:**

```json
{
  "id": "msg_20260311_234500_cc_001",
  "timestamp": "2026-03-11T23:45:00+05:30",
  "source": "cc",
  "type": "decision",
  "priority": "normal",
  "content": "Switched action queue caching from direct Notion reads to Redis. Reduces p95 latency from 2.3s to 180ms.",
  "context": {
    "session": 47,
    "files_affected": ["src/cache/redis_client.py", "src/sync/action_sync.py"]
  },
  "ack": null
}
```

**Message Types:**

| Type | Source | Purpose | Example |
|---|---|---|---|
| `decision` | CC or CAI | Architecture/design decision made | "Switched to Redis for caching" |
| `question` | CC or CAI | Asking the other surface for input | "Should we use Redis or Memcached?" |
| `answer` | CC or CAI | Response to a question | "Redis — better for our pub/sub needs" |
| `task` | CAI → CC | Action item for next CC session | "Implement webhook for GitHub state updates" |
| `status` | CC → CAI | Session boundary state update | "Session 47 closed. Pipeline 80% complete." |
| `note` | CC or CAI | General context/observation | "Found that Notion API has a 3 req/s limit" |
| `research` | CAI → CC | Research findings relevant to project | "Deep research on MCP auth patterns attached" |
| `flag` | CC or CAI | Urgent attention needed | "Scoring model producing negative scores for edge case" |
| `ack` | CC or CAI | Acknowledging receipt of a message | References original msg id |

**Priority Levels:**
- `urgent` — surface should process ASAP on next session start
- `normal` — process when convenient
- `low` — informational, no action needed

**Acknowledgment Protocol:**
When a surface processes an inbox message, it appends an `ack`:

```json
{
  "id": "msg_20260312_0900_cc_ack_001",
  "timestamp": "2026-03-12T09:00:00+05:30",
  "source": "cc",
  "type": "ack",
  "content": "Processed: Switching to Redis confirmed and implemented.",
  "references": "msg_20260311_234500_cai_003"
}
```

**CC Session Lifecycle Integration:**

On Session Start:
1. `git pull` to get latest inbox entries
2. Filter for unacknowledged messages where source != "cc"
3. Surface pending items to the developer
4. Process and ack as appropriate

On Session Close:
1. Append `status` message with session summary
2. Append any `decision` messages for decisions made this session
3. `git push` to make messages available to CAI

**CAI Reading the Inbox:**
- Layer 1: CAI Project syncs the repo → can read inbox.jsonl directly from knowledge base
- Layer 2: Notion DB has "last inbox summary" field updated by CC
- Layer 3: cc-state-mcp has `get_inbox(project, since, unacked_only)` tool

**CAI Writing to the Inbox (before Layer 3 is built):**
- Option A: User manually adds a message (tells CC in next session)
- Option B: CAI generates the JSONL line, user pastes into a GitHub file edit
- Option C: CAI uses GitHub MCP to commit directly to the inbox file
- Layer 3: cc-state-mcp has `write_to_inbox(project, type, content, priority)` tool

### 3.3 `project.json` — Project Registry Metadata

```json
{
  "schema_version": "1.0",
  "name": "ai-cos-mcp",
  "display_name": "AI Chief of Staff MCP Server",
  "category": "ai-cos",
  "description": "Action optimizer MCP server for the AI CoS system",
  "repo_url": "https://github.com/aakash/ai-cos-mcp",
  "cai_project": "AI CoS Build",
  "notion_page_id": null,
  "created_at": "2025-09-15",
  "sync_enabled": true,
  "tags": ["mcp", "fastapi", "notion", "ai-cos"]
}
```

---

## 4. Auto-Init: New Project Setup

When CC creates a new project (`claude init` or manual setup), the sync infrastructure should be created automatically.

### 4.1 Init Script: `cc-sync-init`

This is a CC slash command or hook that runs during project initialization:

```
/sync-init --name "my-project" --category "personal" --cai-project "Personal Builds"
```

**What it does:**

1. Creates `.claude/sync/` directory with template files:
   - `state.json` (initialized with project metadata)
   - `inbox.jsonl` (empty)
   - `project.json` (filled from args)

2. Updates `.gitignore` to ensure sync files are tracked:
   ```
   # Track sync directory
   !.claude/sync/
   # But ignore local-only files
   .claude/settings.local.json
   ```

3. If git remote exists:
   - Commits sync files: `git add .claude/sync/ && git commit -m "feat: initialize CC↔CAI sync"`
   - Pushes to remote

4. If no git remote:
   - Creates repo (prompts for GitHub org/name)
   - Sets up remote
   - Initial push

5. Updates Notion "CC Project States" DB (if Layer 2 is active):
   - Creates new entry with project metadata

6. Outputs confirmation:
   ```
   ✅ CC↔CAI sync initialized for "my-project"
   - .claude/sync/ created with state.json, inbox.jsonl, project.json
   - Git remote: https://github.com/aakash/my-project
   - CAI Project mapping: "Personal Builds"
   - Notion DB entry: created
   
   Next: Add this repo to your CAI Project "Personal Builds" knowledge base
   ```

### 4.2 Session Hooks: Auto-Sync on Close

Add to CC's session close checklist (or implement as a post-session hook):

```
# Added to session close checklist (after existing steps)
Step N: CC↔CAI Sync
  a. Update .claude/sync/state.json with session summary
  b. Append status message to .claude/sync/inbox.jsonl
  c. Append decision messages for any decisions made this session
  d. git add .claude/sync/ && git commit -m "sync: session {N} state update"
  e. git push
  f. Update Notion CC Project States DB entry (if Layer 2 active)
  ✅ Sync complete
```

### 4.3 Session Start Hook: Inbox Check

```
# Added to session start
Step 0: CC↔CAI Inbox Check
  a. git pull (get latest inbox entries from CAI)
  b. Parse .claude/sync/inbox.jsonl
  c. Filter: source != "cc" AND no ack from "cc"
  d. If pending messages exist:
     "📬 You have {N} unread messages from CAI:
      - [urgent] task: Implement webhook for GitHub state updates
      - [normal] decision: Confirmed Redis approach for caching
      - [low] note: Deep research on MCP auth patterns available"
  e. Process and ack as session proceeds
```

---

## 5. Backward Compatibility: Migrating Existing Projects

### 5.1 Migration Script: `cc-sync-migrate`

For existing CC projects that don't have the sync infrastructure:

```
/sync-migrate --category "ai-cos" --cai-project "AI CoS Build"
```

**What it does:**

1. **Detects existing state:**
   - Reads CLAUDE.md for project context
   - Reads auto-memory (MEMORY.md) for accumulated knowledge
   - Reads recent session logs (if using iteration logs)
   - Checks git status (has remote? which branch?)

2. **Creates `.claude/sync/` directory:**
   - `project.json` from detected metadata
   - `state.json` populated from CLAUDE.md + MEMORY.md context
   - `inbox.jsonl` with an initial "migration" message:
     ```json
     {
       "id": "msg_migration_001",
       "timestamp": "2026-03-12T...",
       "source": "cc",
       "type": "status",
       "priority": "normal",
       "content": "Project migrated to CC↔CAI sync protocol. Previous state reconstructed from CLAUDE.md and auto-memory. {N} sessions of history available in iteration logs.",
       "context": {"migration": true, "prior_sessions": 47}
     }
     ```

3. **Ensures git remote exists:**
   - If local-only: prompts to create GitHub repo
   - If remote exists: verifies push access

4. **Updates .gitignore** (non-destructive, appends rules)

5. **Registers in Notion** (if Layer 2 active)

6. **Outputs migration report:**
   ```
   ✅ "ai-cos-mcp" migrated to CC↔CAI sync protocol
   
   Detected state:
   - CLAUDE.md: 289 lines of project context ✓
   - Auto-memory: 47 session learnings ✓
   - Git remote: github.com/aakash/ai-cos-mcp ✓
   - Iteration logs: 47 sessions found ✓
   
   Created:
   - .claude/sync/state.json (populated from existing context)
   - .claude/sync/inbox.jsonl (initialized with migration message)
   - .claude/sync/project.json (metadata registered)
   
   State reconstructed — verify state.json accuracy before first push.
   ```

### 5.2 Batch Migration

For migrating all existing projects at once:

```
/sync-migrate-all
```

Scans `~/.claude/projects/` for all known projects, runs migration on each, generates a summary report.

---

## 6. CAI Projects Structure

### 6.1 Four CAI Projects

| CAI Project Name | Category | CC Projects Mapped | GitHub Repos |
|---|---|---|---|
| **AI CoS Build** | ai-cos | ai-cos-mcp, related repos | github.com/aakash/ai-cos-mcp, ... |
| **Investing Tools** | investing | DeVC tools, Z47 analysis | github.com/aakash/devc-*, ... |
| **Personal Builds** | personal | Side projects, experiments | github.com/aakash/*, ... |
| **Content & Research** | content | Content pipeline, research tools | github.com/aakash/content-*, ... |

### 6.2 CAI Project Instructions Template

Each CAI Project gets custom instructions that make it sync-aware:

```
You are working in the context of Aakash's "{PROJECT_NAME}" project group.

## CC↔CAI Sync Protocol
This project is synced with Claude Code (CC) via GitHub repos. Key files:
- `.claude/sync/state.json` — current project state (updated by CC on session close)
- `.claude/sync/inbox.jsonl` — bidirectional communication log between CC and CAI
- `CLAUDE.md` — project instructions and architecture context

## Reading Project State
When asked about project state, check state.json first. It contains:
- Current tasks, recent decisions, architecture summary
- Last session number and summary
- Next session priorities

## The Inbox Protocol
The inbox is a time-series communication log. When you want to communicate
something to CC (a decision, question, task, or note):
1. Format it as a JSONL message with the inbox schema
2. Note the message for the user to commit to the repo
3. Or (when Layer 3 MCP is available) write directly via cc-state-mcp

Message types: decision, question, answer, task, status, note, research, flag, ack

## Reading the Inbox
Check inbox.jsonl for recent messages from CC. Look for:
- Unacknowledged messages from CC that need CAI response
- Status updates from recent sessions
- Questions CC has asked

## Repos Connected
{LIST_OF_REPOS}

Always check "Sync now" is current before deep technical discussions.
```

---

## 7. Notion "CC Project States" Database Schema (Layer 2)

### 7.1 Database Properties

| Property | Type | Purpose |
|---|---|---|
| Project Name | Title | Project identifier |
| Category | Select | ai-cos / investing / personal / content |
| Status | Select | Active / Paused / Archived |
| Description | Rich text | One-line project description |
| Last Session # | Number | Most recent CC session number |
| Last Session Summary | Rich text | What happened in the last session |
| Last Updated | Date | Timestamp of last sync |
| Current Tasks | Rich text | Active work items |
| Next Priorities | Rich text | What CC will work on next |
| Blocked On | Rich text | Blockers (empty if none) |
| Inbox Pending (CAI→CC) | Number | Count of unacked messages from CAI |
| Inbox Pending (CC→CAI) | Number | Count of unacked messages from CC |
| Git Repo | URL | GitHub repo link |
| CAI Project | Select | Which CAI Project this maps to |
| Stack | Multi-select | Tech stack tags |
| Architecture Summary | Rich text | Current architecture overview |

### 7.2 Views

- **Active Projects** — filter: Status = Active, sort: Last Updated desc
- **Inbox Dashboard** — filter: Inbox Pending > 0, sort: priority
- **By Category** — grouped by Category

---

## 8. Updated Full Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│                         YOUR MAC (CC)                                │
│                                                                      │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐     │
│  │ Project: ai-cos │  │ Project: devc   │  │ Project: xyz    │     │
│  │ .claude/sync/   │  │ .claude/sync/   │  │ .claude/sync/   │     │
│  │  ├ state.json   │  │  ├ state.json   │  │  ├ state.json   │     │
│  │  ├ inbox.jsonl  │  │  ├ inbox.jsonl  │  │  ├ inbox.jsonl  │     │
│  │  └ project.json │  │  └ project.json │  │  └ project.json │     │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘     │
│           │                    │                    │                │
│  On init: /sync-init creates structure automatically                │
│  On close: auto-update state.json + inbox + git push                │
│  On start: git pull + inbox check for CAI messages                  │
│  Migration: /sync-migrate for existing projects                     │
└───────────┬────────────────────┬────────────────────┬───────────────┘
            │ git push           │ git push           │ git push
            ▼                    ▼                    ▼
┌──────────────────────────────────────────────────────────────────────┐
│                        GITHUB (shared bus)                           │
│                                                                      │
│  Each repo contains .claude/sync/ tracked in git                     │
│  inbox.jsonl is append-only — both surfaces write to it             │
│  state.json is overwritten by CC on each session close              │
│                                                                      │
│  Webhook (future): notify MCP server of pushes                      │
└───────┬──────────────────────┬───────────────────────┬──────────────┘
        │                      │                       │
        │ GitHub integration   │ Notion API            │ MCP HTTP
        ▼                      ▼                       ▼
┌─────────────────┐  ┌──────────────────┐  ┌──────────────────────────┐
│ CAI Projects    │  │ Notion DB        │  │ cc-state-mcp (Layer 3)   │
│ (Layer 1)       │  │ (Layer 2)        │  │ (future — build in CC)   │
│                 │  │                  │  │                          │
│ 4 Projects with │  │ "CC Project      │  │ Tools:                   │
│ GitHub repos    │  │  States" DB      │  │ - get_project_state()    │
│ connected to    │  │                  │  │ - get_inbox()            │
│ knowledge base  │  │ High-level       │  │ - write_to_inbox()       │
│                 │  │ state summaries  │  │ - search_code()          │
│ CAI reads code, │  │ for quick CAI    │  │ - get_file()             │
│ state.json,     │  │ awareness        │  │ - list_projects()        │
│ inbox.jsonl     │  │                  │  │                          │
│ directly        │  │ CAI reads via    │  │ Deployed alongside       │
│                 │  │ Notion MCP       │  │ ai-cos-mcp               │
└────────┬────────┘  └────────┬─────────┘  └────────────┬─────────────┘
         │                    │                         │
         └────────────────────┼─────────────────────────┘
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    CAI (web / mobile)                                 │
│                                                                      │
│  Layer 0: Memory — always knows project names, categories, context   │
│  Layer 1: Projects — can read full repos including sync/ files       │
│  Layer 2: Notion — quick high-level state via Notion MCP             │
│  Layer 3: MCP — deep queries, write to inbox, search code            │
│                                                                      │
│  "What's the current state of my AI CoS project?"                    │
│  "Add a task to the ai-cos inbox: implement webhook auth"            │
│  "Show me unacked inbox messages across all projects"                │
│  "I decided to use Redis for the queue — note this for CC"           │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 9. Phased Implementation Plan

### Phase 0: CAI Memory Setup (Today, 10 minutes)
**Surface: CAI**  
**Dependency: None**

- [ ] Add CC project names, categories, and key context to CAI memory
- [ ] Establish terminology: CC, CAI, inbox, sync protocol
- [ ] Memory entries for each active CC project

**Outcome:** Every CAI conversation immediately knows about CC projects.

---

### Phase 1A: CAI Projects + GitHub Connection (Today, 30 minutes)
**Surface: CAI web browser**  
**Dependency: GitHub repos exist for all CC projects**

- [ ] Create 4 CAI Projects (AI CoS Build, Investing Tools, Personal Builds, Content & Research)
- [ ] Authenticate GitHub in Claude.ai (if not already)
- [ ] Connect repos to appropriate CAI Projects
- [ ] Configure file selection (prioritize: CLAUDE.md, .claude/sync/*, key architecture files)
- [ ] Write project instructions for each (using template from Section 6.2)
- [ ] Test: start a chat in "AI CoS Build" project, ask about architecture

**Outcome:** CAI can read CC project code and context via GitHub sync.

---

### Phase 1B: Git Remotes for All Projects (Today, 30 minutes)
**Surface: CC terminal**  
**Dependency: None**

- [ ] Audit all 4-7 CC projects for git remote status
- [ ] Create GitHub repos for any local-only projects
- [ ] Push all projects to remote
- [ ] Verify: each project accessible at github.com/aakash/*

**Outcome:** All CC projects have GitHub remotes — prerequisite for everything else.

---

### Phase 2A: Sync Directory Standard (CC — this week)
**Surface: CC**  
**Dependency: Phase 1B**

- [ ] Create `.claude/sync/` directory structure in one project (ai-cos-mcp as pilot)
- [ ] Manually create state.json, inbox.jsonl, project.json from templates
- [ ] Test the format: push to GitHub, verify CAI Project can read it
- [ ] Iterate on schema if needed

**Outcome:** Validated sync directory format in one project.

---

### Phase 2B: Auto-Init Script (CC — this week)
**Surface: CC**  
**Dependency: Phase 2A validated**

- [ ] Build `/sync-init` slash command or script
- [ ] Inputs: project name, category, CAI project mapping
- [ ] Creates .claude/sync/ with templates
- [ ] Handles git remote creation if needed
- [ ] Updates .gitignore
- [ ] Test: init a new test project, verify full setup

**Outcome:** New projects auto-setup with one command.

---

### Phase 2C: Backward Compatibility Migration (CC — this week)
**Surface: CC**  
**Dependency: Phase 2B**

- [ ] Build `/sync-migrate` command
- [ ] Detects existing CLAUDE.md, auto-memory, iteration logs
- [ ] Populates state.json from existing context
- [ ] Creates inbox.jsonl with migration message
- [ ] Test: migrate ai-cos-mcp (most complex project)
- [ ] Run on all existing projects
- [ ] Build `/sync-migrate-all` for batch operation

**Outcome:** All existing projects have sync infrastructure.

---

### Phase 3A: Session Lifecycle Hooks (CC — week 2)
**Surface: CC**  
**Dependency: Phase 2C**

- [ ] Add to session close checklist:
  - Update state.json
  - Append status + decision messages to inbox.jsonl
  - Git commit + push sync files
- [ ] Add to session start:
  - Git pull
  - Parse inbox for unacknowledged CAI messages
  - Surface pending items
- [ ] Test full cycle: close CC session → open CAI → see updated state

**Outcome:** Automatic sync on every session boundary.

---

### Phase 3B: Notion "CC Project States" DB (CC + CAI — week 2)
**Surface: Both**  
**Dependency: Phase 2C**

- [ ] Create Notion database with schema from Section 7
- [ ] Record the data source ID
- [ ] Add to CC session close: update Notion entry for active project
- [ ] Add to CAI: query via Notion MCP for quick state checks
- [ ] Test: "What's the status of my CC projects?" from CAI mobile

**Outcome:** High-level project awareness via Notion, queryable from any CAI surface.

---

### Phase 4: cc-state-mcp Server (CC — weeks 3-4)
**Surface: CC build, deploy to cloud**  
**Dependency: Phases 1-3 complete**

- [ ] Build MCP server (FastAPI, deploy alongside ai-cos-mcp)
- [ ] Core tools: get_project_state, get_inbox, write_to_inbox, list_projects
- [ ] Advanced tools: get_file, search_code, get_recent_changes
- [ ] Connect to CAI as MCP server
- [ ] Test bidirectional inbox from CAI mobile → CC picks up on next session

**Outcome:** Full programmatic sync. CAI can read deep state and write to inbox without manual steps.

---

### Phase 5: Polish & Compound (CC — weeks 4-6)
**Surface: Both**  
**Dependency: Phase 4**

- [ ] Inbox analytics: "show me all decisions across projects this week"
- [ ] Cross-project queries: "what's blocked across all projects?"
- [ ] GitHub webhook → MCP cache invalidation for near-real-time freshness
- [ ] CAI memory auto-update from inbox highlights
- [ ] Inbox → Action Queue integration (inbox tasks auto-score for AI CoS)
- [ ] Document entire system in CONTEXT.md

**Outcome:** Self-maintaining, self-improving sync infrastructure.

---

## 10. Inbox Power Plays (Future Possibilities)

Once the inbox protocol is established, it becomes a platform for powerful patterns:

### 10.1 Cross-Surface Decision Trail
Every architectural decision is captured with context, regardless of which surface it was made on. Query: "Show me all decisions about the scoring model across CC and CAI."

### 10.2 Async Pair Programming
CAI does research while you sleep → writes findings + recommendations to inbox → CC picks up and implements next morning. Full context preserved.

### 10.3 Action Queue Integration
Inbox `task` messages auto-feed into the AI CoS Action Queue. CAI research → generates task → scores it → adds to Action Queue → CC picks up highest-scored tasks.

### 10.4 Multi-Project Orchestration
Inbox messages can reference other projects. "The auth pattern in project-X should be adopted in project-Y" — cross-project awareness via inbox.

### 10.5 Time-Series Analytics
The append-only nature of inbox.jsonl creates a full audit trail. Analyze velocity, decision patterns, communication frequency between surfaces over time.

### 10.6 Thesis Thread Connection
Inbox messages tagged with thesis thread IDs create automatic connections between code work and investment thesis evolution.

---

## 11. What This Architecture Doesn't Solve

| Gap | Why | When It Gets Solved |
|---|---|---|
| Real-time sync | Git push is session-boundary, not real-time | Layer 3 MCP with GitHub webhooks (Phase 4-5) |
| CAI running CC commands | CAI can't invoke CC while Mac sleeps | Cloud CC when Anthropic ships it (H2 2026?) |
| Shared conversation history | CC and CAI sessions are separate | No solution yet — inbox is the workaround |
| CAI editing CC files directly | Can only write to inbox, not code files | Layer 3 MCP could enable this via GitHub API |
| Automatic CAI Project sync | Still need to click "Sync now" | GitHub webhook → CAI API (not available yet) |

---

## 12. Thesis & Action Queue Connections

**Thesis:** Agentic AI Infrastructure — this project IS the thesis in action. We're building the harness layer between AI surfaces because it doesn't exist natively. Validates that middleware/orchestration is where durable value lives.

**Actions to Score:**

| Action | Impact | Score Est. |
|---|---|---|
| Set up CAI Projects with GitHub repos (Phase 1A) | Immediate sync, zero code | 8 |
| Build /sync-init auto-setup (Phase 2B) | Unlocks zero-friction new projects | 8 |
| Migrate existing projects (Phase 2C) | Full backward compat | 7 |
| Session lifecycle hooks (Phase 3A) | Automatic, zero maintenance sync | 9 |
| Build cc-state-mcp (Phase 4) | Full programmatic bidirectional sync | 9 |
| Inbox → Action Queue integration (Phase 5) | Inbox becomes AI CoS input stream | 8 |
