# Add CC↔CAI Sync Tools to ai-cos-mcp

> **For Claude:** This is a plan seeding document — read fully before implementation. Use superpowers:writing-plans to produce a detailed task-level plan from this.

**Date:** 2026-03-12
**Source:** CC↔CAI Sync System project (handoff from cc-cai-sync repo)
**Destination:** ai-cos-cc-adk — extend existing ai-cos-mcp server
**Priority:** High — unblocks bidirectional CAI↔CC communication

---

## 1. Why This Exists

The CC↔CAI sync system is deployed. Three projects (AI CoS, Flight Mode, Skills Factory) have `.claude/sync/` directories with `state.json`, `inbox.jsonl`, and `project.json` pushed to GitHub. Sync hooks fire on SessionStart (pull) and Stop (push). CC→CAI direction works: CAI reads sync files from GitHub via Projects.

**The gap:** CAI cannot write back. CAI Projects have read-only GitHub access — no write tools exposed. The inbox protocol is designed as bidirectional, but CAI has no path to append messages.

**What was tried and rejected:**
- **Notion bridge** — adds a translation layer (CAI → Notion DB → CC reads → inbox.jsonl). Creates dual storage, schema mismatch, doesn't scale to future capabilities. Workaround, not architecture.
- **GitHub MCP from CAI** — doesn't exist. CAI's GitHub connector is read-only, no tools.
- **Manual copy-paste** — CAI drafts JSONL, user pastes into CC. Works (validated in testing) but defeats the "zero maintenance" design principle.

**What the architecture always planned:** Layer 3 — a `cc-state-mcp` server that CAI calls to read/write project state. Originally scoped as a separate server. This plan implements it as 4 new tools on the existing `ai-cos-mcp` server instead, since the infrastructure already exists.

---

## 2. Findings from CC↔CAI Sync Validation

### What works (validated 2026-03-12)
- **sync-pull.sh** — detects unread CAI messages on SessionStart, outputs to Claude context
- **sync-push.sh** — updates state.json mechanical fields, appends status to inbox, git commits and pushes
- **Double-stop dedup** — push marker prevents duplicate inbox entries within 120s
- **Ack flow** — acknowledged messages no longer flagged as unread
- **CAI reading** — CAI successfully reads state.json and inbox.jsonl from GitHub Projects, understands the protocol, generates valid JSONL responses

### Bug found and fixed
- `sync-pull.sh` line 31: ack detection looked for `.references` but ack messages use `.context.references[]?`. Fixed in all 4 deployed copies and reference implementation. Commit: `9d6abeb` in cc-cai-sync repo.

### What doesn't work
- **CAI → CC writes** — no automated path. CAI composed a perfect JSONL message but had no way to commit it to the repo.
- **GitHub connector reliability** — CAI's GitHub integration doesn't expose tools, only file browsing. Occasionally flaky on file access.

---

## 3. Decision: Extend ai-cos-mcp, Don't Build Separate Server

**Rationale:**
1. ai-cos-mcp already runs on the droplet with FastMCP, has Cloudflare Tunnel, and is connected to CAI as an MCP server
2. Zero new infrastructure — no new deployment, no new MCP connection, no new auth
3. The sync tools need the same GitHub access the server already has (or can trivially add)
4. Clean extraction to a separate server is possible later if the tool count or concerns warrant it
5. Follows the project's build principle: "infrastructure follows friction"

**What changes:**
- `server.py` gains 4 new tool functions (see Section 4)
- A new `lib/sync.py` module handles git operations and file I/O
- Server needs GitHub access (SSH key or token) to clone/pull/push synced repos
- `projects-registry.json` from the cc-cai-sync repo is the source of truth for which projects are synced

---

## 4. Tool Specifications

### 4.1 `cos_sync_projects_list()`

**Purpose:** List all CC projects registered for sync, with their status.

**Returns:**
```json
{
  "projects": [
    {
      "name": "ai-cos-cc-adk",
      "display_name": "AI Chief of Staff CC ADK",
      "zone": "build",
      "sync_status": "active",
      "repo_url": "https://github.com/RTinkslinger/aicos-cc-adk",
      "last_updated": "2026-03-12T22:38:48Z"
    }
  ],
  "total": 3,
  "synced": 3
}
```

**Source:** Read from a local copy of `projects-registry.json` (cloned from cc-cai-sync repo), enriched with `updated_at` from each project's `state.json`.

---

### 4.2 `cos_sync_state_read(project: str)`

**Purpose:** Read current state.json for a project. Git pulls before reading for freshness.

**Parameters:**
- `project` (str, required) — project name from registry (e.g., `"ai-cos-cc-adk"`, `"flight-mode"`, `"skills-factory"`)

**Returns:** The full parsed `state.json` content.

**Behavior:**
1. Validate project name exists in registry
2. `git pull --ff-only --quiet` in the project's cloned repo
3. Read and return `.claude/sync/state.json`

---

### 4.3 `cos_sync_inbox_read(project: str, unacked_only: bool = True, source: str | None = None, limit: int = 20)`

**Purpose:** Read inbox messages with filtering.

**Parameters:**
- `project` (str, required) — project name
- `unacked_only` (bool, default True) — if True, exclude messages that have been acknowledged
- `source` (str, optional) — filter by source: `"cc"`, `"cai"`, or None for all
- `limit` (int, default 20) — max messages to return (newest first)

**Returns:**
```json
{
  "project": "ai-cos-cc-adk",
  "messages": [...],
  "total": 5,
  "unacked": 2
}
```

**Behavior:**
1. Git pull for freshness
2. Parse inbox.jsonl line by line
3. Build ack index (message IDs that have been acknowledged)
4. Filter by source and ack status
5. Return newest first, limited

---

### 4.4 `cos_sync_inbox_append(project: str, type: str, priority: str, content: str, context: dict | None = None)`

**Purpose:** Append a message to a project's inbox from CAI. This is the critical write tool.

**Parameters:**
- `project` (str, required) — project name
- `type` (str, required) — one of: `decision`, `question`, `answer`, `task`, `status`, `note`, `research`, `flag`, `ack`
- `priority` (str, default `"normal"`) — one of: `urgent`, `normal`, `low`
- `content` (str, required) — message content
- `context` (dict, optional) — arbitrary context (references, topic, files, etc.)

**Returns:**
```json
{
  "status": "appended",
  "message_id": "msg_20260312_150000_cai_question",
  "project": "ai-cos-cc-adk",
  "pushed": true
}
```

**Behavior:**
1. Validate project name and message type
2. Git pull (avoid conflicts)
3. Generate message ID: `msg_{YYYYMMDD}_{HHMMSS}_cai_{type}`
4. Construct JSONL message with `source: "cai"`, current timestamp
5. Append to `.claude/sync/inbox.jsonl`
6. `git add` + `git commit -m "sync: CAI inbox message ({type})"` + `git push`
7. Return confirmation with message ID

**Critical: This is the tool that closes the bidirectional loop.** When CAI calls this, CC's next `sync-pull.sh` will detect the message and surface it in Claude's context.

---

## 5. Implementation Architecture

### File structure (new files only)
```
mcp-servers/ai-cos-mcp/
├── lib/
│   └── sync.py          # Git operations, file I/O, message construction
├── server.py            # Add 4 new @mcp.tool() functions
└── repos/               # Cloned synced repos (gitignored)
    ├── aicos-cc-adk/    # Symlink or clone
    ├── flight-mode/
    └── skills-factory/
```

### Git access strategy

The server needs to pull and push to 3 GitHub repos. Options:

**Option A: Clone repos on droplet**
- One-time `git clone` for each synced repo into `repos/`
- Tools do `git pull` before reads, `git add/commit/push` for writes
- Needs SSH key or GitHub token with push access
- Pros: simple, familiar. Cons: disk space, clone maintenance.

**Option B: GitHub API directly**
- Use PyGitHub or raw GitHub REST API
- Read files via `GET /repos/{owner}/{repo}/contents/.claude/sync/inbox.jsonl`
- Write via `PUT /repos/{owner}/{repo}/contents/.claude/sync/inbox.jsonl` (requires base64 encoding, SHA for updates)
- Pros: no local clones. Cons: more complex for JSONL append (read-modify-write via API), rate limits.

**Recommended: Option A (clone repos).** Simpler, matches the existing `git pull/push` pattern used by sync hooks. The repos are small (sync files are < 10KB each).

### Config

Add to `.env` on the droplet:
```bash
# CC↔CAI Sync
SYNC_REGISTRY_REPO=https://github.com/RTinkslinger/cc-cai-sync.git
SYNC_REPOS_DIR=/path/to/repos
GITHUB_TOKEN=ghp_...  # or use SSH key already configured
```

The registry repo is cloned once and pulled periodically to stay current on which projects are synced.

---

## 6. Data Flow (End-to-End)

### CAI → CC (the new path this enables)
```
CAI chat: "Add a task to AI CoS: implement webhook auth"
    │
    ▼
cos_sync_inbox_append(project="ai-cos-cc-adk", type="task", ...)
    │
    ▼
MCP server: git pull → append JSONL → git commit → git push
    │
    ▼
GitHub: aicos-cc-adk repo updated with new inbox.jsonl line
    │
    ▼
CC starts session → sync-pull.sh → git pull → detects unread CAI message
    │
    ▼
Claude sees: "CC↔CAI SYNC: 1 unread message(s) from CAI:
  [normal] task: implement webhook auth"
```

### CC → CAI (existing path, unchanged)
```
CC session ends → sync-push.sh → updates state.json + inbox → git push
    │
    ▼
GitHub: repo updated
    │
    ▼
CAI: cos_sync_state_read("ai-cos-cc-adk") → fresh state
     cos_sync_inbox_read("ai-cos-cc-adk") → sees CC messages
```

---

## 7. Edge Cases and Failure Modes

| Scenario | Handling |
|----------|----------|
| Git push conflict (CC and CAI write simultaneously) | Pull with rebase before push. JSONL is append-only so conflicts are rare — only on the same line, which shouldn't happen. Retry once on failure. |
| Server can't reach GitHub | Return error with `"pushed": false`. Message is still appended locally — next successful push will include it. |
| Invalid project name | Return 400-style error listing valid project names. |
| Inbox.jsonl gets large | Not a near-term concern (JSONL lines are ~300 bytes). At 10 messages/day, 1 year = ~1MB. Can add `--since` filtering and archival later. |
| Repos out of date on droplet | Every read tool does `git pull` first. Write tools do pull before append. Staleness window is seconds. |
| Mac asleep, CC can't pull immediately | By design — messages queue in GitHub. CC picks them up on next session start. |

---

## 8. Acceptance Criteria

1. **CAI can list synced projects** — `cos_sync_projects_list()` returns 3 projects with correct metadata
2. **CAI can read project state** — `cos_sync_state_read("ai-cos-cc-adk")` returns current state.json
3. **CAI can read inbox** — `cos_sync_inbox_read("ai-cos-cc-adk", unacked_only=True)` correctly filters
4. **CAI can write to inbox** — `cos_sync_inbox_append(...)` appends valid JSONL, commits, pushes
5. **CC detects CAI messages** — after CAI writes, CC's `sync-pull.sh` surfaces the message on next session
6. **Round-trip test** — CAI writes question → CC reads it → CC writes answer → CAI reads it

---

## 9. Reference Materials

All in the cc-cai-sync repo (`https://github.com/RTinkslinger/cc-cai-sync`):

| File | What it contains |
|------|-----------------|
| `docs/cc-cai-sync-architecture-v2.md` | Full architecture spec — Layer 3 definition, inbox protocol, Phase 4 spec |
| `docs/cc-cai-sync-architecture-v2.2-addendum.md` | CBS analysis, sync hook design, deployment guide |
| `hooks/sync-pull.sh` | Reference SessionStart hook — shows inbox parsing and ack detection |
| `hooks/sync-push.sh` | Reference Stop hook — shows state.json update and JSONL append pattern |
| `projects-registry.json` | Project registry — source of truth for synced projects |
| `docs/zone1-cai-project-instructions.md` | CAI Project instructions for all 4 projects |

### Inbox message schema (for `cos_sync_inbox_append` to construct)
```json
{
  "id": "msg_{YYYYMMDD}_{HHMMSS}_cai_{type}",
  "timestamp": "ISO 8601",
  "source": "cai",
  "type": "decision|question|answer|task|status|note|research|flag|ack",
  "priority": "urgent|normal|low",
  "content": "string",
  "context": { "references": [], "topic": "", ... },
  "ack": null
}
```

### Existing server pattern to follow
Current tools in `server.py` use this pattern:
```python
@mcp.tool()
def cos_tool_name(param: str) -> dict:
    """Docstring that CAI sees as tool description."""
    try:
        result = lib_function(param)
        return {"status": "ok", "data": result}
    except Exception as e:
        return {"error": str(e)}
```

The sync tools should follow the same pattern — `@mcp.tool()` decorator, typed params, dict return, error handling.

---

## 10. What This Unblocks

Once these 4 tools are deployed:
- **Bidirectional inbox is live** — CAI can write questions, decisions, tasks directly to any project's inbox
- **GitHub connector becomes optional** — CAI reads state via MCP tools, not GitHub file browser
- **Async pair programming** — CAI does research, writes findings to inbox, CC picks up next session
- **Action Queue integration** (Phase 5) — CAI-generated inbox tasks can auto-feed into the AI CoS scoring pipeline
- **Cross-project orchestration** — CAI can write to any synced project's inbox from any CAI Project
