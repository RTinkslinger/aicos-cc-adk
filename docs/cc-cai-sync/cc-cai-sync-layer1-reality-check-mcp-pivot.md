# CC↔CAI Sync — Layer 1 Reality Check & MCP Pivot
## Addendum: What We Learned About CAI's Connector Limitations

**Date:** March 12, 2026  
**Context:** Testing Zone 1 CAI Projects revealed fundamental limitations in our Layer 1 (GitHub sync) and Layer 2 (Notion sync) approaches. CC is building a plan to extend ai-cos-mcp as the primary sync surface.

---

## 1. What We Found: GitHub in CAI

### The Assumption
Architecture v2.0 assumed CAI could read `.claude/sync/` files from GitHub repos connected to Projects. Claude has web_fetch, GitHub MCP is listed in connectors, repos are public — should be straightforward.

### The Reality
**GitHub in CAI is NOT an MCP tool connector.** It is a UI-driven content picker.

Confirmed through direct testing across all 4 CAI Projects:
- Claude inside projects could NOT programmatically access any repo files
- Claude saw the project instructions mentioning state.json, inbox.jsonl etc. but had no way to fetch them
- All 4 projects failed the same way — Claude suggested manual file upload or pasting content

**How GitHub actually works in CAI:**
- It's a UI file browser: you click "+" → "Add from GitHub" → manually select files
- Selected files get injected into Claude's context as static text
- Claude CANNOT call GitHub tools to browse repos, read files, or search code
- It syncs file contents only (no commit history, PRs, metadata)
- You must click "Sync now" manually to refresh after repo changes
- There is a file count/size limit on what can be added

**How this differs from Notion in CAI:**
- Notion IS a true MCP connector with callable tools (notion-search, notion-fetch, notion-create-pages, notion-update-page, etc.)
- Claude can programmatically read, write, query, and update Notion without any UI action
- This is why Notion-based operations (thesis tracker, actions queue, build roadmap) work seamlessly

**The confusion:**
- GitHub appears alongside Notion under "Connectors" in settings — implying equal capability
- In reality they are fundamentally different integration types
- Multiple users have reported this confusion (GitHub issues document it)
- This misled our architecture design

### Impact on Layer 1
Layer 1 (CAI Projects + GitHub repo sync) as designed in v2.0 is **not viable for automated sync.** It can work as a manual reference layer (add key files via UI, click sync periodically) but cannot be the primary programmatic sync path.

---

## 2. What We Found: Notion as Sync Layer

### The Assumption
Layer 2 (Notion "CC Project States" DB) was designed as a complementary high-level state layer. Notion MCP IS a real tool connector — Claude can query it programmatically.

### The Limitation
While Notion MCP works for querying existing databases (thesis tracker, build roadmap, actions queue), using it as the PRIMARY sync surface has issues:

- **Rate limits:** Notion API has rate limits that constrain frequent updates
- **Latency:** Notion queries are slow compared to direct file/API access
- **Schema rigidity:** Notion DB properties are fixed schema — state.json is flexible JSON
- **Rich content limits:** Notion rich text properties have character limits — can't store full session summaries, architecture descriptions, or inbox message histories
- **Not designed for machine-to-machine sync:** Notion is a human-facing tool being repurposed as a sync backend

### What Notion IS Good For
- Thesis Tracker (AI-managed, query-on-demand) — works great
- Build Roadmap (structured items with status) — works great
- Actions Queue (structured actions with scoring) — works great
- High-level project status dashboard — works fine

### What Notion IS NOT Good For
- Primary sync transport for state.json (flexible, nested JSON)
- Inbox protocol (append-only JSONL time-series)
- Deep project state with architecture summaries, file lists, decision logs
- Anything requiring fast, frequent programmatic read/write

---

## 3. What Actually Works: web_fetch on Public Repos

### The Discovery
During the CAI-side architecture session, Claude successfully read state.json and inbox.jsonl from ALL repos using:
```
web_fetch → https://raw.githubusercontent.com/RTinkslinger/{repo}/main/.claude/sync/state.json
```

This worked perfectly — fast, complete, no UI action needed.

### The Limitation
- **Rate limits:** web_fetch can hit rate limits on repeated calls within a session
- **Not a tool Claude reliably uses:** Claude in project contexts doesn't automatically know to web_fetch raw GitHub URLs unless explicitly told
- **Public repos only:** If repos go private, raw.githubusercontent.com requires auth
- **Fragile:** Depends on GitHub's raw content serving, not a designed API

### Verdict
web_fetch on raw URLs is a viable **fallback** for standalone chats where memory entries provide the URL pattern. It's NOT a reliable primary sync mechanism for project-level work.

---

## 4. The Real Answer: Extend ai-cos-mcp

### Why MCP Extension Is Correct
ai-cos-mcp is already:
- A true MCP server that CAI can call programmatically (like Notion)
- Deployed on cloud infrastructure (always-on, Mac-independent)
- Connected to CAI as an MCP connector with callable tools
- Running on the same infra as Postgres, content pipeline, etc.

Adding sync tools to ai-cos-mcp gives CAI the same level of programmatic access to project state that it has to Notion databases — but without Notion's limitations.

### Tools to Add

| Tool | Purpose | Direction |
|---|---|---|
| `cos_get_project_state(project)` | Read state.json contents for any project | CC → CAI |
| `cos_get_inbox(project, since?, unacked_only?)` | Read inbox messages, filter by date/ack status | CC → CAI |
| `cos_write_to_inbox(project, type, content, priority)` | Write a message to a project's inbox | CAI → CC |
| `cos_list_projects()` | List all registered CC projects with status | CC → CAI |
| `cos_get_file(project, path)` | Read any file from a project repo | CC → CAI |
| `cos_ack_inbox(project, message_id)` | Acknowledge an inbox message | CAI → CC |

### How It Works
1. CC pushes state.json + inbox.jsonl to GitHub (existing sync hooks — already built)
2. ai-cos-mcp reads from GitHub repos (via GitHub API or cloned repos on server)
3. CAI calls ai-cos-mcp tools to read state, check inbox, write messages
4. CC pulls on next session start (sync-pull.sh — already built)

### What This Replaces
- Layer 1 (GitHub in CAI Projects): No longer needed for sync. GitHub UI can still be used manually for loading reference docs into project knowledge.
- Layer 2 (Notion CC Project States DB): Not needed. ai-cos-mcp serves the same purpose with better data fidelity.
- Layer 3 was always planned as cc-state-mcp — this just merges it into ai-cos-mcp instead of building a separate server.

### Revised Layer Model

```
BEFORE (v2.0-v2.2):
  L0: CAI Memory (always-on awareness) 
  L1: CAI Projects + GitHub UI sync (broken for programmatic access)
  L2: Notion CC Project States DB (limited by Notion constraints)
  L3: cc-state-mcp (future separate server)

AFTER (v3 — this pivot):
  L0: CAI Memory (always-on awareness) — UNCHANGED
  L1: ai-cos-mcp sync tools (programmatic, reliable, always-on) — NEW PRIMARY
  L2: Notion (existing DBs only — thesis, actions, roadmap) — SCOPED DOWN
  L3: GitHub repos (raw storage + CC push/pull) — DEMOTED TO TRANSPORT
  
  Optional: GitHub UI in CAI Projects for manual reference doc loading
  Optional: web_fetch as fallback for standalone chats
```

---

## 5. What's Already Built & What's Reusable

### Fully Reusable (No Changes Needed)
- **sync-pull.sh** — CC session start: git pull + inbox check. Works as-is.
- **sync-push.sh** — CC session close: state.json update + inbox append + git push. Works as-is.
- **Prompt-type Stop hook** — Claude updates semantic fields in state.json. Works as-is.
- **.claude/sync/ directory standard** — state.json, inbox.jsonl, project.json schemas. All good.
- **Inbox protocol** — message types, ack protocol, JSONL format. All good.
- **projects-registry.json** — project enumeration and metadata. Good.
- **CAI Memory entries (19)** — identity, methodology, sync architecture, project registry. Good.

### Needs Modification
- **CAI Project instructions** — remove assumption that Claude reads GitHub files directly. Add reference to ai-cos-mcp sync tools.
- **Architecture docs** — update Layer model to reflect MCP-primary approach.
- **Memory entry #2** — update 4-layer stack description to reflect new layer model.
- **Memory entry #19** — web_fetch pattern becomes fallback, not primary.

### New Build Required
- **ai-cos-mcp sync tools** — the 6 tools listed above. CC builds this.
- **GitHub repo access from server** — ai-cos-mcp needs to read files from GitHub (API or clone).

---

## 6. Lessons Learned

1. **Test assumptions before building on them.** We designed 3 architecture versions assuming GitHub in CAI was a programmatic tool. A 5-minute test in the first session would have caught this.

2. **"Connected" doesn't mean "callable."** GitHub shows as "Connected" in CAI settings alongside Notion, Gmail, etc. But it's a fundamentally different type of integration. Settings UI is misleading.

3. **The MCP connector pattern is the only reliable programmatic path in CAI.** If Claude needs to call a tool at runtime, it must be an MCP server. GitHub integration, web_fetch, and file uploads are all human-initiated or fragile.

4. **Notion is great for what it's designed for.** Thesis tracker, actions queue, build roadmap — all work well because they're structured data that humans also use. Repurposing Notion as a machine-to-machine sync transport was the wrong abstraction.

5. **Consolidate, don't proliferate.** Instead of building a separate cc-state-mcp server (Layer 3 in original plan), extending ai-cos-mcp is simpler — one MCP server for CAI to connect to, one codebase to maintain, one deployment to manage.

6. **The sync files and hooks are solid infrastructure.** state.json, inbox.jsonl, sync-pull.sh, sync-push.sh — all validated and working. The transport layer (how CAI reads them) was the gap, not the format or the CC-side automation.

7. **Build methodology validated: "infrastructure follows friction."** We hit the friction. Now we build the infrastructure. Not before.

---

## 7. Updated Build Priority

| Priority | What | Status |
|---|---|---|
| **DONE** | CC sync hooks (sync-pull.sh, sync-push.sh, prompt hook) | ✅ Deployed on 3/4 projects |
| **DONE** | .claude/sync/ directory standard + schemas | ✅ Validated on all projects |
| **DONE** | CAI Memory entries (19 entries) | ✅ Live |
| **DONE** | projects-registry.json | ✅ Complete |
| **NOW** | Extend ai-cos-mcp with sync tools | CC building plan |
| **THEN** | Update CAI Project instructions to reference MCP tools | After MCP tools deployed |
| **THEN** | Update memory entries #2 and #19 | After MCP tools deployed |
| **THEN** | Full end-to-end test: CC close → ai-cos-mcp → CAI reads state | Verification |
| **PARKED** | Zone 2 & Zone 3 CAI Projects | After sync verified |
| **PARKED** | QMD intelligent retrieval | After sync verified |
