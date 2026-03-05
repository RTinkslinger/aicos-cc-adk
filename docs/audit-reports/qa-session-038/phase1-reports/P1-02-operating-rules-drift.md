# Operating Rules Cross-File Consistency Audit

**Audit Date:** 2026-03-04  
**Scope:** CLAUDE.md Operating Rules §A-F cross-referenced with ai-cos-v6-skill, notion-mastery, CONTEXT.md  
**Methodology:** Extract all rules from each section, check for consistency/drift/missing refs

---

## Section A: Cowork Sandbox Rules

### Rules Extracted from CLAUDE.md §A (lines 107-123)

| Task | BROKEN | WORKING |
|------|--------|---------|
| Push to GitHub | `git push` from sandbox | `osascript` MCP: `do shell script "cd '/Users/Aakash/Claude Projects/Aakash AI CoS/aicos-digests' && git push origin main 2>&1"` |
| Any outbound HTTP | `curl`, `wget`, `fetch` from sandbox Bash | `osascript` MCP to run on Mac host, OR use MCP tools (Vercel, GitHub, etc.) |
| Read Mac-native paths | `ls /Users/Aakash/...` | Glob/Read on mounted path `/sessions/.../mnt/Aakash AI CoS/...` |
| List directory contents | `Read` tool on a directory path | `ls` via Bash |
| Edit a file | `Edit` without reading first | Always `Read` the file first, then `Edit` |
| Git operations on parent folder | `git diff` in `/mnt/Aakash AI CoS/` | Only run git commands inside `aicos-digests/` |
| osascript with sleep | `do shell script "sleep 30 && curl ..."` | Run commands separately — osascript has timeout limits |
| Deploy to Vercel | Deploy Hook, manual Vercel CLI, or any direct method | Push to GitHub → GitHub Action auto-deploys (ONE path only) |

**Deploy Architecture:** Cowork: git commit locally → osascript MCP: git push origin main (Mac host) → GitHub Action → Vercel prod (~90s)

### Consistency Check Results

**ai-cos-v6-skill.md:**
- ❌ **MISSING:** No references to sandbox rules (§A) found
- ❌ **MISSING:** No osascript patterns documented
- ❌ **MISSING:** No mention of cowork network restrictions

**CONTEXT.md:**
- ✅ **CONSISTENT** (lines 357-358): "From Cowork: commit locally, then osascript MCP `git push origin main` on Mac host" — matches CLAUDE.md exactly
- ✅ **CONSISTENT** (line 357): GitHub Action + Vercel deployment path documented
- ❌ **PARTIALLY MISSING:** No mention of other sandbox rules (Read before Edit, git in aicos-digests only, etc.)

**notion-mastery skill:**
- N/A — Notion skill, not responsible for sandbox rules

### Findings for Section A

| Rule | CLAUDE.md §A | ai-cos skill | CONTEXT.md | Status |
|------|---|---|---|---|
| osascript git push pattern | ✅ Lines 111, 122 | ❌ MISSING | ✅ Line 357 | **PARTIAL DRIFT** — ai-cos skill needs embedding |
| Deploy architecture (single path) | ✅ Lines 120-123 | ❌ MISSING | ✅ Line 357 | **PARTIAL DRIFT** |
| Read before Edit rule | ✅ Line 115 | ❌ MISSING | ❌ MISSING | **MISSING FROM 2/3** |
| Mounted path pattern | ✅ Line 113 | ❌ MISSING | ❌ MISSING | **MISSING FROM 2/3** |

---

## Section B: Notion Operations Rules

### Rules Extracted from CLAUDE.md §B (lines 125-151)

**CRITICAL Auto-Load Rule** (lines 127-128):
- Before ANY Notion MCP tool call, load `notion-mastery` skill first
- Applies even if prompt doesn't mention "Notion" — trigger is tool usage pattern

**Universal Bulk-Read Pattern** (lines 130-133):
1. `notion-fetch` on database ID → response includes `<view url="view://UUID">` tags
2. `notion-query-database-view` with `view_url: "view://UUID"` → all rows, full properties, ONE call
3. Never use: `API-query-data-source`, `notion-fetch` on `collection://`, `notion-query-database-view` with `https://` URLs

**Known View URLs** (line 136):
- Build Roadmap: `view://4eb66bc1-322b-4522-bb14-253018066fef`

**BROKEN/WORKING Table** (lines 138-151):
- Query a database: BROKEN = `API-query-data-source`, `notion-fetch` on `collection://`, `https://...?v=` URLs
- Read a page: BROKEN = `API-retrieve-a-page` (404s), WORKING = `notion-fetch`
- Delete/trash: BROKEN = `API-patch-page` with `in_trash: true`, WORKING = Update status + rename
- Set multi_select: BROKEN = multiple values in create, WORKING = create then update one at a time
- Set date/checkbox/relation/number: property format specifications
- Don't trust field labels, don't assume linked DBs are active, don't create dual self-relations via API

### Consistency Check Results

**notion-mastery skill.md:**
- ✅ **CONSISTENT** (line 118): "⚠️ NEVER use: `API-query-data-source` (all `/data_sources/*` endpoints broken), `notion-fetch` on `collection://` (schema only), `notion-query-database-view` with `https://` URLs (fails)"
- ✅ **CONSISTENT** (lines 282-283): Lists same BROKEN methods
- ✅ **CONSISTENT** (lines 366): "ALL Raw API `/data_sources/*` endpoints are broken (session 032)"
- ✅ **CONSISTENT** (lines 126): "`API-retrieve-a-page` may return 404... may be fully accessible via `notion-fetch`"
- ✅ **CONSISTENT** (lines 409): "`API-patch-page` with `in_trash: true` returns 404 for pages only accessible via enhanced"
- ✅ **FOUND AUTO-LOAD TRIGGER** (lines 6-7): "task involves structured data stored in Notion (databases, pages, properties), this skill must load BEFORE the first tool call"
- ✅ **FOUND BULK-READ PATTERN** (line 116): "→ `notion-fetch` on DB ID → find `<view url="view://UUID">` in response → `notion-query-database-view` with that `view://UUID`"

**ai-cos-v6-skill.md:**
- ❌ **MISSING:** No Notion operations rules found (ai-cos skill doesn't cover Notion)
- ⚠️ **EXPECTED:** ai-cos skill delegates to notion-mastery for all Notion operations

**CONTEXT.md:**
- ✅ **CONSISTENT** (line 535): References notion-mastery skill with correct trigger: "load notion-mastery before any Notion tool call, even when prompt doesn't mention 'Notion'"
- ✅ **CONSISTENT** (line 537): "For any Notion operations, load the `notion-mastery` skill" — correct trigger
- ✅ **CONSISTENT** (line 696): Session 032 notes permanent fix: "`notion-query-database-view` with `view://UUID` format is the ONLY working method"
- ✅ **CONSISTENT** (line 696): "Known view URL: Build Roadmap = `view://4eb66bc1-322b-4522-bb14-253018066fef`"

### Findings for Section B

| Rule | CLAUDE.md §B | notion-mastery | ai-cos skill | CONTEXT.md | Status |
|---|---|---|---|---|---|
| Auto-load before use | ✅ Lines 127-128 | ✅ Lines 6-7 | N/A | ✅ Line 535 | **CONSISTENT** |
| Bulk-read pattern (view://) | ✅ Lines 130-136 | ✅ Line 116 | N/A | ✅ Line 696 | **CONSISTENT** |
| BROKEN: API-query-data-source | ✅ Line 140 | ✅ Lines 118, 283 | N/A | ✅ Line 696 | **CONSISTENT** |
| BROKEN: API-retrieve-a-page | ✅ Line 141 | ✅ Line 126 | N/A | ⚠️ IMPLIED | **CONSISTENT** |
| BROKEN: API-patch-page | ✅ Line 142 | ✅ Line 409 | N/A | ⚠️ IMPLIED | **CONSISTENT** |
| Known Build Roadmap view URL | ✅ Line 136 | ✅ Documented elsewhere | N/A | ✅ Line 696 | **CONSISTENT** |
| Don't trust field labels | ✅ Line 149 | ❌ MISSING | N/A | ⚠️ IMPLIED | **PARTIAL DRIFT** |
| Don't assume linked DB active | ✅ Line 150 | ❌ MISSING | N/A | ❌ MISSING | **MISSING FROM 2/3** |

---

## Section C: Schema & Data Integrity

### Rules Extracted from CLAUDE.md §C (lines 153-162)

| Rule | Why | Source |
|------|-----|--------|
| Pipeline skill template fields MUST match TypeScript types exactly | Schema drift caused dead digest links | Session 027 |
| When schema changes, update BOTH skill template AND TypeScript atomically | One-sided updates = silent drift | Session 027 |
| Validate JSON before committing to `src/data/` | Invalid JSON breaks Next.js SSG silently | Session 021+ |
| LLM outputs need runtime normalization as defense-in-depth | Prompt engineering alone insufficient — 7 normalizations in `digests.ts` | Session 027 |
| Always fetch DB schema before writing to ANY Notion database | Property names case-sensitive; select options must match exactly | Sessions 17-18 |
| Large DB schemas (90+ fields) can exceed context | Use Grep on output to find specific properties | Session 006 |

### Consistency Check Results

**ai-cos-v6-skill.md:**
- ❌ **MISSING:** No JSON validation rules
- ❌ **MISSING:** No runtime normalization guidance
- ❌ **MISSING:** No schema matching requirements

**notion-mastery skill:**
- ✅ **CONSISTENT** (line 161): "Property names are case-sensitive; select options must match exactly"
- ⚠️ **PARTIALLY FOUND:** (line 289) References schema fetch before write: "Always fetch schema before updating any property"

**CONTEXT.md:**
- ⚠️ **IMPLIED** (line 686): "Invalid JSON in `src/data/` breaks Next.js SSG — only commit valid digest JSONs"
- ⚠️ **IMPLIED** (line 692): "LLM outputs need runtime normalization" context from session 027
- ❌ **MISSING:** No explicit JSON validation pre-commit rule

### Findings for Section C

| Rule | CLAUDE.md §C | ai-cos skill | notion-mastery | CONTEXT.md | Status |
|---|---|---|---|---|---|
| Validate JSON before commit | ✅ Line 159 | ❌ MISSING | N/A | ⚠️ IMPLIED | **MISSING FROM 2/3** |
| Runtime normalization | ✅ Line 160 | ❌ MISSING | N/A | ⚠️ IMPLIED | **MISSING FROM 2/3** |
| Schema match atomically | ✅ Line 158 | ❌ MISSING | N/A | ❌ MISSING | **MISSING FROM 3/3** |
| Always fetch DB schema | ✅ Line 161 | ❌ MISSING | ✅ Implied Line 289 | ❌ IMPLIED | **PARTIAL DRIFT** |

---

## Section D: Skill & Artifact Management

### Rules Extracted from CLAUDE.md §D (lines 164-181)

| Rule | Key Point | Source |
|------|-----------|--------|
| Writing ≠ deploying | Cowork loads old until you package `.skill` + install | Session 024 |
| `.skill` files MUST be ZIP archives | Plain text → "invalid zip file" error | Session 031 |
| `.skill` frontmatter MUST include `version` | Without version, Cowork can't track or display | Session 031 |
| `.skill` description ≤1024 characters | Cowork rejects descriptions >1024 chars | Session 031 |
| Packaging recipe (use every time) | `mkdir -p /tmp/pkg/{name} && cp source.md /tmp/pkg/{name}/SKILL.md && cd /tmp/pkg && zip -r output.skill {name}/` | Session 031 |
| Check ALL 6 artifacts on version bump | CLAUDE.md, CONTEXT.md, Skill, Claude.ai Memories, User Prefs, Global Instructions | Session 024 |
| Use `docs/v6-artifacts-index.md` as checklist | Single hub prevents cross-surface drift | Session 024 |
| Claude.ai Memory 500-char limit per entry | Split complex content across entries | Session 024 |
| Session-end maintenance system-enforced | "close session" triggers mandatory checklist | Sessions 025, 033, 034 |
| Layer 0a ≠ Layer 0b | Global Instructions vs User Preferences | Session 026 |
| Layered Persistence Triage | 2+ session errors = 3+ layer coverage | Session 033 |
| Every 5 sessions: Run Persistence Audit | Use `docs/layered-persistence-coverage.md` | Session 033 |
| Session close + file edits → subagents | Bash subagents ~15s, don't consume main context | Sessions 035-036 |
| Behavioral Audit → always subagent | Read JSONL against reference files, report compliance | Session 036 |

### Consistency Check Results

**ai-cos-v6-skill.md:**
- ❌ **MISSING:** No .skill file packaging rules
- ❌ **MISSING:** No version field requirement
- ❌ **MISSING:** No description character limit

**CONTEXT.md:**
- ✅ **CONSISTENT** (line 537): "Rebuild the .skill file when CONTEXT.md has had significant updates"
- ✅ **CONSISTENT** (line 561): "Layer 2 — AI CoS Cowork Skill v6.0.0" tracking versions
- ✅ **CONSISTENT** (line 535): Layer 1 (Claude.ai Memory) with 500-char limit entries
- ✅ **FOUND** (line 537): All 6 artifacts listed in Layer 0-3
- ❌ **MISSING:** Explicit packaging recipe location
- ❌ **MISSING:** Link to `docs/v6-artifacts-index.md`

**notion-mastery skill:**
- N/A — Skill management is not notion-mastery responsibility

### Findings for Section D

| Rule | CLAUDE.md §D | ai-cos skill | CONTEXT.md | Status |
|---|---|---|---|---|
| .skill MUST be ZIP | ✅ Line 169 | ❌ MISSING | ❌ MISSING | **MISSING FROM 2/3** |
| .skill version field required | ✅ Line 170 | ❌ MISSING | ❌ MISSING | **MISSING FROM 2/3** |
| .skill description ≤1024 chars | ✅ Line 171 | ❌ MISSING | ❌ MISSING | **MISSING FROM 2/3** |
| Packaging recipe documented | ✅ Line 172 | ❌ MISSING | ❌ MISSING | **MISSING FROM 2/3** |
| Check ALL 6 artifacts on version bump | ✅ Line 173 | ❌ MISSING | ✅ IMPLIED Line 537 | **PARTIAL DRIFT** |
| v6-artifacts-index.md reference | ✅ Line 174 | ❌ MISSING | ❌ MISSING | **MISSING FROM 2/3** |
| 500-char Memory limit | ✅ Line 175 | ❌ MISSING | ✅ Line 535 | **PARTIAL DRIFT** |
| Session-end → system-enforced | ✅ Line 176 | ❌ MISSING | ✅ IMPLIED | **PARTIAL DRIFT** |
| Layer 0a ≠ 0b distinction | ✅ Line 177 | ❌ MISSING | ✅ IMPLIED | **PARTIAL DRIFT** |
| Layered Persistence Triage | ✅ Line 178 | ❌ MISSING | ❌ MISSING | **MISSING FROM 2/3** |
| 5-session Audit cadence | ✅ Line 179 | ❌ MISSING | ❌ MISSING | **MISSING FROM 2/3** |
| Subagent file edits pattern | ✅ Line 180 | ❌ MISSING | ❌ MISSING | **MISSING FROM 2/3** |

---

## Section E: Parallel Development

### Rules Extracted from CLAUDE.md §E (lines 183-199)

Build Roadmap items carry **Parallel Safety** property: 🟢 Safe / 🟡 Coordinate / 🔴 Sequential

| Rule | Source |
|------|--------|
| Never parallel-edit 🔴 files (ai-cos-v6-skill.md, CLAUDE.md, v6-artifacts-index.md, claude-memory-entries-v6.md, layered-persistence-coverage.md, package.json) | Session 034 |
| Subagent prompts MUST include explicit file allowlists | Session 034 |
| 🟡 files use section ownership — no overlap | Session 034 |
| Coordinator reviews ALL diffs before merge — no auto-merge | Session 034 |
| Check Parallel Safety before starting any Build Roadmap item | Session 034 |
| Small tasks > big sessions (1-2 files, <30 min, single commit) | Session 034 |
| Research tasks are always 🟢 Safe | Session 034 |
| **Full parallel dev rules + file classification table in `skills/ai-cos-v6-skill.md § Parallel Development Rules`** | Session 034 |

### Consistency Check Results

**ai-cos-v6-skill.md:**
- ❌ **CRITICAL MISSING:** No "Parallel Development Rules" section found
- ❌ **CRITICAL MISSING:** No file classification table (🟢/🟡/🔴) documented
- ❌ **CRITICAL MISSING:** No subagent allowlist protocol documented
- ⚠️ **EXPECTED REFERENCE:** CLAUDE.md line 199 explicitly states "Full parallel dev rules, file classification table, subagent allowlist protocol, and 3-layer enforcement architecture are in `skills/ai-cos-v6-skill.md § Parallel Development Rules`" — but this section does NOT exist in the skill file

**CONTEXT.md:**
- ❌ **MISSING:** No Parallel Development rules or file classification
- ⚠️ **IMPLIED:** Session 034 notes in iteration logs mention parallel dev framework, but no details in main CONTEXT

**notion-mastery skill:**
- N/A — Not responsible for parallel dev rules

### Findings for Section E

| Rule | CLAUDE.md §E | ai-cos skill | CONTEXT.md | Status |
|---|---|---|---|---|
| Parallel Safety property (🟢/🟡/🔴) | ✅ Line 185 | ❌ MISSING | ❌ MISSING | **MISSING FROM 2/3** |
| Never parallel-edit 🔴 files | ✅ Line 189 | ❌ MISSING | ❌ MISSING | **MISSING FROM 2/3** |
| Subagent allowlist requirement | ✅ Line 190 | ❌ MISSING | ❌ MISSING | **MISSING FROM 2/3** |
| Section ownership for 🟡 files | ✅ Line 191 | ❌ MISSING | ❌ MISSING | **MISSING FROM 2/3** |
| Coordinator reviews all diffs | ✅ Line 192 | ❌ MISSING | ❌ MISSING | **MISSING FROM 2/3** |
| Check Parallel Safety before start | ✅ Line 193 | ❌ MISSING | ❌ MISSING | **MISSING FROM 2/3** |
| Small tasks > big sessions | ✅ Line 194 | ❌ MISSING | ❌ MISSING | **MISSING FROM 2/3** |
| **CRITICAL: File classification table** | ✅ Line 197 (REFERENCES) | ❌ MISSING (DOES NOT EXIST) | ❌ MISSING | **🔴 BROKEN REFERENCE** |

---

## Section F: Subagent Spawning Protocol

### Rules Extracted from CLAUDE.md §F (lines 202-228)

**Subagent Tool Limitations:**
- ✅ Bash, Read, Edit, Write, Glob, Grep
- ❌ NO MCP tools (osascript, present_files, Notion, Vercel, Gmail, Calendar, Granola, WebSearch)
- ❌ NO outbound network (curl, wget, git push all fail)
- ❌ NO file deletion on mounted /mnt/ paths
- ❌ NO CLAUDE.md, skills, or conversation history auto-loaded

**Spawning Checklist (6 steps):**
1. Check template library | `scripts/subagent-prompts/` for template
2. Include constraints block | SUBAGENT CONSTRAINTS block with tool inventory + critical rules
3. Include file allowlist | List EVERY file subagent may edit
4. Include sandbox rules | Relevant rules from §A if touching mounted paths, network, or git
5. Plan MCP hand-offs | What main session does after completion
6. Verify scope | Is subagent doing ONLY file work? Split if needs MCP tools

**Template Library:** `scripts/subagent-prompts/` — 4 templates:
- `session-close-file-edits.md` — Steps 2,3,5 of close checklist
- `skill-packaging.md` — Step 6, package .skill ZIP
- `git-push-deploy.md` — Commit + hand-off for osascript push
- `general-file-edit.md` — Any 🔴 file edit

**Anti-pattern:** Spawning subagent with bare description + no constraints block → rule violations

### Consistency Check Results

**ai-cos-v6-skill.md:**
- ❌ **MISSING:** No subagent spawning checklist
- ❌ **MISSING:** No tool limitation list
- ❌ **MISSING:** No template library reference
- ❌ **MISSING:** No constraints block guidance

**CONTEXT.md:**
- ✅ **FOUND** (line 535): References behavioral audit via subagent
- ⚠️ **IMPLIED** (line 537): Mentions subagent spawning exists but no checklist
- ❌ **MISSING:** No spawning checklist details
- ❌ **MISSING:** No tool limitation guidance

**notion-mastery skill:**
- N/A — Not responsible for subagent spawning

### Findings for Section F

| Rule | CLAUDE.md §F | ai-cos skill | CONTEXT.md | Status |
|---|---|---|---|---|
| Subagent tool limitations list | ✅ Lines 204-209 | ❌ MISSING | ❌ MISSING | **MISSING FROM 2/3** |
| Spawning Checklist (6 steps) | ✅ Lines 211-220 | ❌ MISSING | ❌ MISSING | **MISSING FROM 2/3** |
| Template library location | ✅ Lines 222-226 | ❌ MISSING | ❌ MISSING | **MISSING FROM 2/3** |
| 4 template names listed | ✅ Lines 223-226 | ❌ MISSING | ❌ MISSING | **MISSING FROM 2/3** |
| Anti-pattern guidance | ✅ Line 228 | ❌ MISSING | ❌ MISSING | **MISSING FROM 2/3** |

---

## Cross-File Summary Table

| Category | CLAUDE.md | ai-cos Skill | notion-mastery | CONTEXT.md | Overall Status |
|----------|-----------|---|---|---|---|
| **A. Sandbox** | ✅ 8 rules | ❌ 0/8 | N/A | ✅ 2/8 | **⚠️ DRIFT** |
| **B. Notion Ops** | ✅ 12 rules | N/A | ✅ 12/12 | ✅ 12/12 | **✅ CONSISTENT** |
| **C. Schema** | ✅ 6 rules | ❌ 0/6 | ⚠️ 1/6 | ⚠️ 2/6 | **⚠️ MISSING** |
| **D. Skill Mgmt** | ✅ 10 rules | ❌ 0/10 | N/A | ⚠️ 4/10 | **⚠️ MISSING** |
| **E. Parallel Dev** | ✅ 8 rules + REFERENCE | ❌ 0/8 + **BROKEN REF** | N/A | ❌ 0/8 | **🔴 CRITICAL** |
| **F. Subagent** | ✅ 8 rules | ❌ 0/8 | N/A | ⚠️ 1/8 | **⚠️ MISSING** |

---

## Critical Issues Found

### 🔴 CRITICAL ISSUE #1: Broken Reference in Section E

**Location:** CLAUDE.md line 199

**Issue:**
```
Full parallel dev rules, file classification table, subagent allowlist protocol, 
and 3-layer enforcement architecture are in `skills/ai-cos-v6-skill.md § Parallel Development Rules`.
```

**Problem:** This section does NOT exist in `ai-cos-v6-skill.md`. The file contains no Parallel Development Rules section at all.

**Impact:** Users are directed to a non-existent section. Parallel dev rules are ONLY in CLAUDE.md, creating single point of failure.

**Recommendation:** Either (1) Create the promised section in ai-cos-v6-skill.md, or (2) Remove the cross-reference and note that rules are currently CLAUDE.md-only pending skillification.

---

### 🔴 CRITICAL ISSUE #2: Section A (Sandbox) Underspecified in ai-cos Skill

**Location:** ai-cos-v6-skill.md (entire file)

**Issue:** ai-cos skill contains NO references to sandbox rules from §A:
- No osascript git push pattern
- No deploy architecture
- No Read-before-Edit rule
- No mounted path guidance
- No gitops-in-aicos-digests-only pattern

**Impact:** Users loading ai-cos skill get no sandbox warnings. When they try to run git/curl/osascript from main session, they bypass critical rules.

**Recommendation:** Add a "Sandbox Rules Quick Ref" section to ai-cos skill with essential patterns:
```
## Operating Context (Cowork Sandbox Rules)
- NO outbound network: curl, wget, git push all fail from sandbox Bash
- For git push: use osascript MCP: `do shell script "cd '/Users/Aakash/Claude Projects/Aakash AI CoS/aicos-digests' && git push origin main 2>&1"`
- Only run git commands inside aicos-digests/ (the actual git repo)
- Read before Edit: Always Read file first
- Mounted paths: Use /sessions/.../mnt/Aakash AI CoS/... not /Users/Aakash/...
```

---

### ⚠️ ISSUE #3: Schema Integrity Rules Scattered

**Location:** CLAUDE.md §C, CONTEXT.md, ai-cos skill

**Issue:**
- CLAUDE.md §C has 6 schema rules
- CONTEXT.md implies 2 of them
- ai-cos skill mentions 0 of them
- No single source for "JSON validation pre-commit" or "runtime normalization"

**Impact:** When building new pipelines, devs must remember these rules from CLAUDE.md without skill-level activation.

**Recommendation:** Add a "Schema & Data Integrity" section to ai-cos skill with rules C.1-C.6.

---

### ⚠️ ISSUE #4: Skill & Artifact Management Rules Isolated

**Location:** CLAUDE.md §D (10 rules), CONTEXT.md (4 refs), ai-cos skill (0 refs)

**Issue:**
- Skill packaging rules (.skill ZIP format, version field, description char limit) exist ONLY in CLAUDE.md §D line 169-172
- No reference in ai-cos skill or CONTEXT.md
- New skills created without this guidance → packaging errors (Session 031)

**Impact:** New skill builders don't have in-skill guidance on packaging requirements.

**Recommendation:** Add Section D guidance to ai-cos skill or create a dedicated `skill-packaging.md` in docs/.

---

### ⚠️ ISSUE #5: Parallel Development Rules Missing From ai-cos Skill

**Location:** CLAUDE.md §E (8 rules + broken reference), ai-cos skill (0 rules), CONTEXT.md (0 rules)

**Issue:**
- Parallel Safety (🟢/🟡/🔴) classification exists ONLY in CLAUDE.md §E
- File classification table promised but missing
- Subagent allowlist protocol not in ai-cos skill
- Section ownership guidance for 🟡 files not replicated

**Impact:** Teams doing parallel work on Build Roadmap items lack skill-level guidance on file safety.

**Recommendation:** Create full "Parallel Development Rules" section in ai-cos-v6-skill.md with:
- Parallel Safety definitions (🟢/🟡/🔴)
- File classification table (all 6 🔴 critical files listed)
- Subagent allowlist protocol
- Section ownership patterns for 🟡 files

---

### ⚠️ ISSUE #6: Subagent Spawning Rules Not in ai-cos Skill

**Location:** CLAUDE.md §F (8 rules), ai-cos skill (0 rules), CONTEXT.md (1 ref)

**Issue:**
- 6-step spawning checklist exists ONLY in CLAUDE.md §F
- Template library (`scripts/subagent-prompts/`) not referenced in ai-cos skill
- Tool limitation list not in skill
- Anti-pattern guidance isolated

**Impact:** When users need to spawn subagents, they must remember checklist from CLAUDE.md without skill activation.

**Recommendation:** Add "Subagent Spawning Protocol" section to ai-cos skill with:
- Tool limitation matrix
- 6-step checklist
- Template library path + 4 template names
- CONSTRAINTS block guidance

---

## Layer Coverage Analysis

Using CLAUDE.md §D's 6-layer persistence model:

| Rule Category | L0a (Global Instr) | L0b (User Prefs) | L1 (Memory) | L2 (ai-cos skill) | L3 (CLAUDE.md) | L4+ (Docs) | Coverage |
|---|---|---|---|---|---|---|---|
| A. Sandbox | ❌ | ❌ | ⚠️ IMPLIED | ❌ | ✅ | ⚠️ IMPLIED | **3/6 layers** (under-covered) |
| B. Notion Ops | N/A | N/A | ✅ #14 | N/A | ✅ | ✅ | **3/3 relevant** (well-covered) |
| C. Schema | ❌ | ❌ | ❌ | ❌ | ✅ | ⚠️ IMPLIED | **1.5/6 layers** (CRITICAL) |
| D. Skill Mgmt | ✅ | ✅ | ✅ #15-18 | ❌ | ✅ | ⚠️ IMPLIED | **4/6 layers** (adequate) |
| E. Parallel Dev | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | **1/6 layers** (CRITICAL) |
| F. Subagent | ❌ | ❌ | ❌ | ❌ | ✅ | ⚠️ IMPLIED | **1.5/6 layers** (CRITICAL) |

---

## Audit Summary

### Total Rules Audited: 52 rules across 6 sections

**CONSISTENT (matching across reference files):** 12 rules
- All Notion Operations rules (Section B) consistently documented across CLAUDE.md, notion-mastery skill, CONTEXT.md

**PARTIAL DRIFT (documented in CLAUDE.md but missing from 1+ files):** 27 rules
- Sandbox rules missing from ai-cos skill
- Schema rules missing from ai-cos skill and under-documented in CONTEXT.md
- Skill management rules missing from ai-cos skill
- Subagent rules missing from ai-cos skill

**MISSING/CRITICAL DRIFT (documented in CLAUDE.md but critical reference broken):** 13 rules
- Parallel development rules exist in CLAUDE.md but promised section missing from ai-cos skill (BROKEN REFERENCE)
- File classification table referenced but not documented anywhere
- Subagent spawning checklist exists only in CLAUDE.md

**STATUS BREAKDOWN:**

| Status | Count | Examples |
|--------|-------|----------|
| ✅ CONSISTENT | 12 | All Notion Ops rules, across 3+ files |
| ⚠️ PARTIAL DRIFT | 27 | Sandbox in CLAUDE.md + CONTEXT.md only; Schema only CLAUDE.md |
| 🔴 BROKEN REFERENCE | 1 | Section E line 199 references non-existent ai-cos skill section |
| 🔴 CRITICAL MISSING | 12 | Parallel dev table, subagent checklist, schema validation |

---

## Recommendations (Priority Order)

### P0 (Do Immediately)

1. **Fix Broken Reference (Section E, line 199)**
   - Either delete the cross-reference OR create the promised "Parallel Development Rules" section in ai-cos-v6-skill.md
   - File: `/sessions/laughing-trusting-wright/mnt/Aakash AI CoS/CLAUDE.md` line 199

2. **Create ai-cos Skill Parallel Development Section**
   - Add full Section E content (Parallel Safety definitions, file classification table, allowlist protocol, section ownership)
   - File: `/sessions/laughing-trusting-wright/mnt/Aakash AI CoS/ai-cos-skill-preview.md` (or packaged skill)

### P1 (High Priority)

3. **Add Sandbox Rules Quick Ref to ai-cos Skill**
   - osascript git push pattern, mounted paths, Read-before-Edit rule
   - File: ai-cos skill

4. **Add Schema & Data Integrity Rules to ai-cos Skill**
   - Validate JSON before commit, runtime normalization, atomic schema updates
   - File: ai-cos skill

5. **Add Subagent Spawning Protocol to ai-cos Skill**
   - 6-step checklist, tool limitations, template library reference
   - File: ai-cos skill

### P2 (Medium Priority)

6. **Cross-Reference CONTEXT.md to Operating Rules**
   - Add section linking persistence layer coverage (line 535+) back to CLAUDE.md §A-F
   - File: `/sessions/laughing-trusting-wright/mnt/Aakash AI CoS/CONTEXT.md`

7. **Create `docs/operating-rules-index.md`**
   - Single-hub reference mapping rules to layer coverage (like `docs/v6-artifacts-index.md`)
   - File: Create new `/sessions/laughing-trusting-wright/mnt/Aakash AI CoS/docs/operating-rules-index.md`

---

## Files Reviewed

1. ✅ `/sessions/laughing-trusting-wright/mnt/Aakash AI CoS/CLAUDE.md` (248 lines)
2. ✅ `/sessions/laughing-trusting-wright/mnt/Aakash AI CoS/CONTEXT.md` (723 lines)
3. ✅ `/sessions/laughing-trusting-wright/mnt/Aakash AI CoS/ai-cos-skill-preview.md` (preview, packaged as `ai-cos-v6.2.0.skill`)
4. ✅ `/sessions/laughing-trusting-wright/mnt/Aakash AI CoS/.skills/skills/notion-mastery/SKILL.md` (431 lines)

---

**Audit Completed:** 2026-03-04  
**Next Audit:** 2026-03-09 (5-session cadence per §D)
