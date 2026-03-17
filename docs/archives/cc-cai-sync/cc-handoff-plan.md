# CC↔CAI Sync: CC Handoff Plan
## What to Do in CC First, Then Come Back to CAI

**Date:** March 12, 2026  
**Context:** This plan follows the architecture design session in CAI (chat: `[sync, builder] CC↔CAI Maximum Sync — Architecture Design & Deep Interview`). The architecture docs (v2.0 + v2.1 addendum) and deep research report are in the same `docs/` folder as this file.

---

## Pre-Read (Before Starting CC Work)

CC should read these docs in order:
1. `cc-cai-sync-architecture-v2.md` — full architecture, inbox protocol, phased plan
2. `cc-cai-sync-architecture-v2.1-addendum.md` — revised project model, tags, Cash Build System note
3. `deep-research-cc-cai-sync.md` — landscape research (reference, not required reading)

---

## Step 1: Enumerate All CC Projects

**Goal:** Produce a complete list of all CC projects with their status.

For each project, capture:
- Project name (as used in CC)
- Path on disk
- Git repo status: has remote? URL? Or local-only?
- Category/zone mapping: Build (Zone 1), Research (Zone 2), or Ops (Zone 3)
- Active or dormant?
- Brief one-liner description

**Output:** A `projects-registry.json` or markdown table that becomes the source of truth for the sync system.

**Why this matters:** CAI needs this list to set up Projects with GitHub connections (Layer 1). The sync system needs it for project.json files and Notion DB entries.

---

## Step 2: Ensure Git Remotes on All Projects

**Goal:** Every active CC project has a GitHub remote.

For each project from Step 1:
- If remote exists: verify it's up to date (`git push`)
- If local-only: create GitHub repo and push
- Ensure `.gitignore` is clean

**Output:** All projects accessible at github.com/[username]/*

---

## Step 3: Examine Cash Build System Hook Architecture

**Goal:** Understand existing hook trigger points so CC↔CAI sync integrates naturally.

Questions to answer:
- What command(s) make up the Cash Build System?
- What events trigger hooks? (file changes? manual? Notion writes? session close?)
- What state do hooks update? (roadmap DB? build status? other Notion DBs?)
- How are hooks implemented? (CC hooks config? shell scripts? custom commands?)
- What's the execution context? (inline in session? async? subagent?)
- At which points during a session do hooks fire?

**Output:** Document the hook architecture so sync triggers can be designed to fire alongside existing hooks. Add this understanding to the architecture docs.

**Key principle from architecture:** Sync should fire at the SAME trigger points as Cash Build System, not just session close. Don't design sync hooks independently — they're an additional output of the existing hook system.

---

## Step 4: Pilot `.claude/sync/` Directory on One Project

**Goal:** Validate the sync directory format on the most complex project (likely ai-cos-mcp).

Create in the pilot project:
```
.claude/sync/
├── state.json      # Populate from current project state
├── inbox.jsonl     # Initialize empty (or with migration message)
├── project.json    # Project registry metadata
└── .gitkeep
```

Use the schemas from architecture v2.0 Section 3 for file formats.

**Test:** Push to GitHub. Verify the files are readable. This validates the format before building automation.

**Output:** Validated sync directory in one project, pushed to GitHub.

---

## Step 5: Build `/sync-init` Command

**Goal:** One command to set up sync infrastructure for any new project.

```
/sync-init --name "my-project" --category "ai-cos" --cai-project "AI CoS MCP Server"
```

What it does:
1. Creates `.claude/sync/` with template files
2. Populates project.json from arguments
3. Initializes state.json with project metadata
4. Creates empty inbox.jsonl
5. Updates .gitignore to track sync files
6. Git commit + push
7. Outputs confirmation with next steps

See architecture v2.0 Section 4.1 for full spec.

---

## Step 6: Build `/sync-migrate` for Existing Projects

**Goal:** One-time migration of existing projects to the sync standard.

```
/sync-migrate --category "ai-cos" --cai-project "AI CoS MCP Server"
```

What it does:
1. Detects existing CLAUDE.md, auto-memory, iteration logs
2. Creates `.claude/sync/` directory
3. Populates state.json from existing context
4. Creates inbox.jsonl with migration message
5. Creates project.json from detected metadata
6. Git commit + push

See architecture v2.0 Section 5 for full spec.

After pilot works, build `/sync-migrate-all` for batch migration.

---

## Step 7: Run Migration on All Projects

**Goal:** All existing projects have sync infrastructure.

Run `/sync-migrate` on each project from Step 1 list.
Verify each: state.json accurate? inbox.jsonl initialized? Git pushed?

---

## Step 8: Design Sync Hooks (Integrated with Cash Build System)

**Goal:** CC↔CAI sync fires automatically at the right moments.

Based on Step 3 findings, add sync as a hook in Cash Build System:
- Update state.json at same trigger points as existing state hooks
- Append to inbox.jsonl for decisions and status updates
- Git push sync files (batched with other pushes if applicable)
- Session start: git pull + inbox check for CAI messages

**This is the most important step for "zero maintenance" sync.**

---

## What to Bring Back to CAI

When Steps 1-4 are complete (at minimum), return to CAI with:

1. **Projects registry** — complete list of CC projects with names, GitHub URLs, zone mappings
   → CAI will set up Projects with GitHub connections (Layer 1A)

2. **Cash Build System hook findings** — what triggers exist, how they work
   → CAI will update architecture docs accordingly

3. **Any refinements** to zone mappings, tag taxonomy, or architecture
   → CAI will incorporate into the system

4. **Confirmation that pilot `.claude/sync/` works** on at least one project
   → CAI will verify it's readable from GitHub integration in Projects

---

## Phased Priority

| Priority | Step | Effort | Unlocks |
|---|---|---|---|
| **Do first** | Step 1: Enumerate projects | 15 min | Everything else |
| **Do first** | Step 2: Git remotes | 30 min | Layer 1 (CAI Projects) |
| **Do first** | Step 4: Pilot sync directory | 20 min | Validates format |
| **Then** | Step 3: Cash Build System analysis | 30 min | Proper hook design |
| **Then** | Step 5: /sync-init | 1-2 hours | New project automation |
| **Then** | Step 6: /sync-migrate | 1-2 hours | Existing project compat |
| **Then** | Step 7: Run all migrations | 30 min | Full coverage |
| **Last** | Step 8: Sync hooks | 2-4 hours | Zero-maintenance sync |

**Minimum to bring back to CAI:** Steps 1, 2, and 4 complete. That's ~1 hour of CC work and unlocks Layer 1 setup in CAI.

---

## Reference: Key File Schemas

See architecture v2.0 Section 3 for complete schemas:
- `state.json` — Section 3.1
- `inbox.jsonl` — Section 3.2 (message types: decision, question, answer, task, status, note, research, flag, ack)
- `project.json` — Section 3.3
