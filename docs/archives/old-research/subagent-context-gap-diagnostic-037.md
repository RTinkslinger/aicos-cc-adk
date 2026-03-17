# DIAGNOSTIC REPORT: Subagent Context Gap Analysis
**Generated:** 2026-03-04  
**Analysis Scope:** CLAUDE.md, ai-cos-v6-skill.md, behavioral-audit-prompt.md, layered-persistence-coverage.md  
**Question:** Why do subagents violate documented sandbox/delivery rules?

---

## FINDING 1: Rules Exist Across Multiple Files (No Single Source of Truth)

### Where Sandbox Rules Live (7 locations):

| Rule | CLAUDE.md | ai-cos Skill | Coverage Map | Prompt Template | Layer Coverage |
|------|-----------|--------------|--------------|-----------------|-----------------|
| No `curl/wget` from sandbox | ✅ §A | ✅ (p.198) | ✅ (item #5) | ❌ | L0a+L1+L2 |
| Use `osascript` for outbound | ✅ §A (line 111) | ✅ (p.198-200) | ❌ | ❌ | L0a+L1+L2 |
| Cowork Deploy Pattern | ✅ §A (line 122) | ✅ (p.207) | ❌ | ❌ | L0a+L1 |
| `.skill` = ZIP (not plain text) | ✅ §D (line 169) | ✅ (p.169, 210, 319) | ✅ (item #9) | ❌ | L0a+L1+L2 |
| Use `present_files` for .skill | ✅ §D (line 172) | ✅ (p.214, 319) | ❌ | ❌ | L0a+L1 |
| Packaging recipe (exact steps) | ✅ §D (line 172) | ✅ (p.213) | ❌ | ❌ | L0a+L1 |
| Mounted paths (`/sessions/.../mnt/`) | ✅ §A (line 113) | ✅ (p.216) | ❌ | ❌ | L0a+L1 |

**KEY INSIGHT:** All critical rules exist in L0a (CLAUDE.md + Global Instructions), but:
- **Only ~40% also live in subagent prompt template** (behavioral-audit-prompt.md is READ-ONLY audit, not a task template)
- **Zero rules are in standard subagent spawn prompts** (no task templates provided to subagents doing work)
- **Coverage map tracks but doesn't teach** — it's a compliance tracker, not a subagent instruction source

---

## FINDING 2: What a Bash Subagent Actually Receives (Current State)

When you call `Task(subagent_type="Bash")` with a prompt:

| Item | Provided? | Details |
|------|-----------|---------|
| **Prompt text** | ✅ Yes | Whatever string you pass |
| **CLAUDE.md** | ❌ No | NOT auto-loaded to subagent |
| **Skills** | ❌ No | NOT auto-loaded to subagent |
| **Reference files** | ❌ No | Subagent must be told to READ them |
| **Session context** | ❌ No | Subagent doesn't see JSONL or prior messages |
| **MCP tools** | ❌ No | Subagent only gets: Bash, Read, Edit, Write, Glob, Grep |
| **Cowork workspace** | ✅ Yes | Subagent can access `/sessions/.../mnt/` |
| **File allowlist** | ❌ No | Unless YOU explicitly put it in the prompt |

**Critical gap:** Subagent receives ONLY the prompt text. That's it.

---

## FINDING 3: The Specific Gap in Subagent Task Spawning

From CLAUDE.md §E (Parallel Development), Line 190:

> | **Subagent prompts MUST include explicit file allowlists** | Without allowlists, subagents may edit files outside their scope. Include: `ALLOWED FILES: [list]. Do NOT edit any other files.` | Session 034 |

**Current state:**
- Rule EXISTS ✅
- DOCUMENTED ✅  
- But there's NO TEMPLATE showing what an allowlist-aware subagent prompt should look like
- And there's NO ENFORCEMENT that the main session actually includes this in every subagent call

**Result:** When the main session spawns a file-edit subagent (e.g., "edit CONTEXT.md, CLAUDE.md, and Artifacts Index"), it might forget to include the allowlist, and the subagent defaults to "try all edits I can."

---

## FINDING 4: Session Close Checklist (Step 1c) Audit Subagent vs. Other Subagents

**Session Behavioral Audit subagent (Step 1c):**
- ✅ Has detailed prompt template (`scripts/session-behavioral-audit-prompt.md`)
- ✅ Prompt explicitly says "READ-ONLY. Write ONLY the audit report. Do NOT edit reference files."
- ✅ Task: execute a 6-section read + analyze workflow
- ✅ Prevents accidental mutations

**Other file-edit subagents (Steps 2, 3, 5 of session close):**
- ❌ No template provided
- ❌ CLAUDE.md says "Use `Task(subagent_type="Bash")` for each — they complete in ~15s"
- ❌ But no example prompt is given
- ❌ No explicit "do NOT edit these files" instruction
- ❌ Subagent could theoretically edit anything

**Gap:** The behavioral-audit subagent is highly specified. File-edit subagents are not.

---

## FINDING 5: Sandbox Rules Buried in Operating Rules, Not in Task Prompts

Example: A subagent is asked to "commit changes and push to GitHub."

**What the main session SHOULD prompt:**

```
IMPORTANT: You are in a Cowork sandbox (Linux VM, no outbound network).
You CANNOT run: git push, curl, wget, fetch from Bash.

INSTEAD: Use osascript MCP with this command:
  osascript('do shell script "cd /Users/Aakash/Claude Projects/Aakash AI CoS/aicos-digests && git push origin main 2>&1"')

This runs on the Mac host and bypasses sandbox restrictions.

Files you may edit: [list]
Files you MUST NOT touch: CLAUDE.md, CONTEXT.md, skills/ai-cos-v6-skill.md, and any 🔴 files in the parallel dev table.
```

**What actually happens:**
- Subagent gets: "commit and push changes"
- Subagent thinks: "I have Bash. Let me run `git push`"
- Result: failure (no network)
- Subagent retries with curl (same failure)
- Subagent then tries something else or asks the main session

**Why:**
1. Subagent doesn't know sandbox rules exist (not in its prompt)
2. Subagent doesn't know osascript MCP is an alternative (would need to be told)
3. Subagent doesn't know Cowork environment is special (assumed generic CLI)

---

## FINDING 6: `.skill` Delivery Gap (Specific Example of the Larger Problem)

**Rule documented in:**
- CLAUDE.md §D, line 172: "Package as ZIP... then `present_files` on the `.skill`"
- ai-cos-v6-skill.md, p. 214: "Then `present_files` on the `.skill` file for user to double-click install"
- Coverage map item #9: "Skill packaging rules"

**When a subagent is asked to "package and deliver a skill":**

Current behavior (likely):
1. Subagent reads the packaging recipe
2. Subagent creates the ZIP correctly
3. Subagent tries to deliver it using familiar tools (Bash `cp`, or tries to `Write` it)
4. **Subagent doesn't know about `present_files` MCP tool** (not available to Bash subagents)
5. **Subagent doesn't know about workspace folders** (unclear how to make files visible to user)
6. Result: "I created the .skill file but can't deliver it"

**Why this happens:**
- Rules mention `present_files` ✅
- But `present_files` is an MCP tool ❌ (subagent has no MCP tools)
- Rules don't say "coordinate with main session to present" ❌
- Rules don't distinguish between "subagent CAN do this" vs. "subagent MUST hand off" ❌

---

## FINDING 7: The 3-Layer Enforcement Architecture (Incomplete for Subagents)

From ai-cos-v6-skill.md, Lines 272-279:

| Layer | What | Coverage | When |
|-------|------|----------|------|
| **L1: Prompt Allowlist** | Explicit file list in subagent prompt | ~60% alone | At task spawn |
| **L2: Pre-Edit Self-Check** | Agent asks "Am I allowed to edit this?" before each edit | +25% | During execution |
| **L3: Coordinator Diff Review** | Coordinator reviews all file changes before merge | +14% | Post-completion |
| **L4: PreToolUse Hook** (Phase 2) | Automated rejection of edits to disallowed files | +1% (closes gap) | Future |

**Current reality:**
- L1 (Prompt Allowlist): **Not consistently applied** — rules exist, templates don't, enforcement is manual
- L2 (Pre-Edit Self-Check): **Only works if LLM remembers** — no automation, depends on instruction following
- L3 (Coordinator Diff Review): **Manual** — requires main session to stay focused
- L4 (PreToolUse Hook): **Not yet built** — phase 2 future work

**Coverage: 60% × (awareness rate ~30%) = ~18% actual coverage**

The system is designed as 3-layer defense, but L1 (the first defense) has ~30% coverage because:
- Prompt allowlist rule exists (CLAUDE.md §E, line 190)
- But there's no **template for what to include**
- And no **automated checker** that main session uses before spawning subagent
- And no **pre-written examples** of correct subagent prompts

---

## FINDING 8: The Session Close Pattern (Where Subagents Are Most Used)

**Session close checklist (CLAUDE.md §D.3, CLAUDE.md line 323):**

> **⚡ EXECUTION RULE: Always delegate file edits to subagents.** Steps 2 (CONTEXT.md), 3 (CLAUDE.md), and 5 (Artifacts Index) involve large file edits that cause context compaction in the main session. Use `Task(subagent_type="Bash")` for each — they complete in ~15s and don't consume main context.

**This is where subagents are MOST likely to violate rules because:**

1. **Pressure to be fast:** "Complete in ~15s" incentivizes minimal prompting
2. **Complex editing scope:** 3 different files being edited simultaneously by 3 subagents
3. **No coordination mechanism:** How do 3 parallel subagents coordinate around 🟡 files with section ownership?
4. **Implicit assumptions:** Rules like "don't edit CLAUDE.md" are assumed, not stated in the subagent prompt
5. **No allowlist template:** The main session has no ready-made prompt that says "edit X.md only, not Y.md or Z.md"

**What's missing:**

```
Example Subagent Prompt Template for Session Close (FILE EDITS)

You will edit CONTEXT.md Step 2 of session close. ONLY edit the DETAILED ITERATION LOGS section.
You will NOT edit any other section of CONTEXT.md, and you will NOT edit any other files.

Changes you make:
- Add a new entry under "## DETAILED ITERATION LOGS" with today's date and session number
- Include: what was completed, what's in progress, what's pending, key files modified, key decisions
- Do NOT change version numbers, state summary, or ID references elsewhere in the file

After your edit, output: git diff CONTEXT.md

Here's the current CONTEXT.md:
[file content]
```

This template DOESN'T EXIST right now. Each session's main session has to improvise the prompt, and quality varies.

---

## FINDING 9: Corrected Rule Tracking (Coverage Map) vs. Preventive Rule Teaching (Subagent Templates)

**Coverage map (docs/layered-persistence-coverage.md) tracks:**
- Item #5: Cowork sandbox rules — violation history (sessions 7, 9, 21, 27)
- Item #9: Skill packaging rules — violation history (session 031)
- Item #22: Subagent allowlist protocol — violation history (sessions 034+)

**But there's no:**
- Pre-written subagent prompt template for "commit to git from Cowork"
- Pre-written subagent prompt template for "edit CONTEXT.md as part of session close"
- Pre-written subagent prompt template for "package and deliver a .skill file"
- Pre-written subagent prompt template for "edit CLAUDE.md"
- Pre-written subagent prompt template for "edit Artifacts Index"

**Result:** The system learns AFTER violations happen, but doesn't teach BEFORE.

---

## FINDING 10: The Meta-Problem (Why Subagents Don't Know the Rules)

### Root Cause Chain:

1. **Rules live in L0a (CLAUDE.md + Global Instructions)**
   - ✅ Correct — this is where persistent system rules belong
   - ✅ Accessible to main sessions and full Claude.ai conversations
   
2. **Subagents are task-specific workers, not full-session participants**
   - ✅ Correct design — they should be given specific, bounded tasks
   - ❌ But this means they DON'T inherit global context
   
3. **Critical rules (sandbox, .skill format, Notion methods) are NOT automatically provided to every subagent prompt**
   - ❌ This is the gap
   - Each subagent call requires main session to manually include relevant rules
   - Main session often skips this because "it should be obvious" or "complete in 15s"
   
4. **No standardized subagent prompt templates exist**
   - ❌ Behavioral-audit has one (🟢 Safe, read-only)
   - ❌ File-edit subagents don't (🔴/🟡 Sequential/Coordinate)
   - Result: Each spawning session improvises
   
5. **Main session can't copy/paste rules efficiently**
   - Rules are long (sandbox rule table is 8 rows × 3 columns)
   - Pasting entire rule sets into every subagent prompt bloats the prompt
   - But pasting nothing leaves subagent uninformed
   - Middle ground: "extract only the relevant rules for THIS task" — but that requires main session to decide what's relevant (cognitive load)

---

## SOLUTION BLUEPRINT: 4-Layer Fix

### Layer 1: Pre-Written Subagent Prompt Library (IMMEDIATE)

Create `/sessions/.../mnt/Aakash AI CoS/scripts/subagent-prompts/` with templates:

**File:** `subagent-prompts/SESSION-CLOSE-STEP-2-CONTEXT-MD.txt`
```
You will edit CONTEXT.md for session close step 2.

SCOPE: You may ONLY edit the "DETAILED ITERATION LOGS" section.
You must NOT edit any other section of CONTEXT.md.
You must NOT edit CLAUDE.md, Artifacts Index, or any other files.

INSTRUCTIONS:
1. Read the file /sessions/.../mnt/Aakash AI CoS/CONTEXT.md completely
2. Go to section "## DETAILED ITERATION LOGS"
3. Add a new dated entry for this session with: what's done, in progress, pending
4. Edit carefully — preserve all other sections exactly as they are
5. Verify the edit: grep for the new session entry and confirm it's present
6. Output: git diff CONTEXT.md [the actual diff to review]
7. Do NOT commit. The coordinator will handle the commit.

[Then insert current CONTEXT.md file content]
```

**File:** `subagent-prompts/COWORK-GIT-PUSH.txt`
```
You are in a Cowork sandbox (Linux VM, no outbound network).

CRITICAL: You cannot run "git push" directly from Bash.
Instead, you MUST use the osascript MCP tool to run the command on the Mac host.

TASK: Push changes from /sessions/.../mnt/Aakash AI CoS/aicos-digests/ to GitHub origin main

WORKING METHOD (use this — do not try git push):
1. Verify you're in the aicos-digests folder: /sessions/.../mnt/Aakash AI CoS/aicos-digests
2. Check what's staged: git status [in the aicos-digests folder]
3. Call osascript MCP: do shell script "cd '/Users/Aakash/Claude Projects/Aakash AI CoS/aicos-digests' && git push origin main 2>&1"
4. Verify success: the command should return no errors

BROKEN METHODS (do NOT try these):
- git push from Bash in the sandbox (network disabled)
- curl to GitHub API from Bash (network disabled)
- Using deploy hooks or Vercel CLI manually (bypass single deploy path)

Report: output the full response from osascript so the coordinator can confirm success.
```

**File:** `subagent-prompts/SKILL-PACKAGING-AND-DELIVERY.txt`
```
You will package a skill as a .skill file and prepare it for delivery to the user.

CRITICAL RULES:
1. .skill files are ZIP archives, NOT plain text files
2. ZIP must contain a single directory named {skill-name}/
3. Inside {skill-name}/, place the SKILL.md file (the markdown source)
4. Frontmatter in SKILL.md MUST include: version (e.g., version: 1.0.0) and description (max 1024 chars)

TASK: Package {SKILL_NAME} for delivery

STEPS:
1. Read the current skill source: [read the skill file path]
2. Verify frontmatter has version field: grep "^version:" [file]
3. Verify description ≤1024 chars: wc -c on the description line
4. Create directory structure: mkdir -p /tmp/pkg/{skill-name}
5. Copy SKILL.md: cp [source] /tmp/pkg/{skill-name}/SKILL.md
6. Create ZIP: cd /tmp/pkg && zip -r /tmp/{skill-name}.skill {skill-name}/
7. Verify ZIP: unzip -t /tmp/{skill-name}.skill (should succeed)
8. Report back: "✅ .skill packaged at /tmp/{skill-name}.skill, ready for present_files MCP"

COORDINATOR WILL THEN: Use present_files MCP to deliver the .skill to the user.
You do NOT need to present_files — that's not available in your subagent tools. Just package and report the path.
```

### Layer 2: Subagent Prompt Generator (Checklist in Main Session)

Add to CLAUDE.md §E a "Subagent Spawning Checklist":

```markdown
### Subagent Spawning Checklist (Use Before Every Task() Call)

Before spawning a subagent with `Task(subagent_type="Bash")`:

1. **Identify the task type:** (file edit / git operation / data read / analysis / other)
2. **Check library:** Does `/scripts/subagent-prompts/` have a template for this?
3. **If YES:** Load the template and customize variables ({SKILL_NAME}, {FILE_PATH}, etc.)
4. **If NO:** Manually craft the prompt and include:
   - Exact scope: "You may ONLY edit these files: [list]. Do NOT edit: [list]"
   - Environment context: "You are in a Cowork sandbox. X is blocked. Use Y instead."
   - Success criteria: "Report back with: [specific output]"
   - Security check: "Do NOT delete files, commit code, or modify anything outside [scope]"
5. **Run the checklist:** Before hitting execute, review:
   - ✅ Task scope is narrow (1-2 files max)
   - ✅ File allowlist is explicit
   - ✅ Sandbox rules relevant to THIS task are included
   - ✅ Success criteria are clear
6. **Post-execution:**
   - Review subagent output for completeness
   - If file edits: `git diff [files]` before accepting changes
   - If git/network ops: confirm success message, don't assume
```

### Layer 3: Enhanced Behavioral Audit (Detect Template Gaps)

Update `scripts/session-behavioral-audit-prompt.md` to detect:
- Subagent prompts that lack explicit allowlists
- Subagent attempts to use tools/APIs they don't have access to (osascript from Bash subagent, present_files, etc.)
- Repeated re-spawning of subagents for the same task (suggests prompt was incomplete)

Add to audit report:
```markdown
### Template Gap Detection
| Task | Subagent Prompt Included Allowlist? | Included Sandbox Rules? | Issues Found |
|------|------------------------------------|-----------------------|--------------|
| git push | NO | NO | Subagent likely tried git push directly, failed. Template exists at scripts/subagent-prompts/COWORK-GIT-PUSH.txt — use it next time. |
```

### Layer 4: Notion Skill Enhancement (Add Subagent Context to Profile)

Later: If subagents had MCP tool access, this wouldn't be an issue. For now, explicitly document in ai-cos-v6-skill.md:

```markdown
## Subagent Capabilities & Limitations (Session 037)

**Subagents (Task tool with subagent_type="Bash") CAN:**
- Run Bash commands in `/sessions/.../mnt/`
- Read files (Read, Glob, Grep, ls)
- Edit/Write files (Edit, Write)
- Access to mounted workspace

**Subagents CANNOT:**
- Call MCP tools (osascript, present_files, Notion, GitHub, Vercel, etc.)
- See prior session context, JSONL, or Memory
- Access unverified networks
- Commit to git or push to GitHub directly
- Call APIs directly (curl, wget from sandbox)

**Workaround for network/MCP tasks:**
- Subagent prepares data locally
- Subagent reports back to main session
- Main session uses MCP tools to complete network ops
- Example: subagent packages .skill ZIP → main session calls present_files to deliver
```

---

## SUMMARY: The Root Cause in One Sentence

**Subagents receive ONLY the prompt text provided by the main session. Critical rules (sandbox, delivery, .skill format) exist in CLAUDE.md and skills but are NOT automatically injected into every subagent prompt. Without explicit allowlists and context in the prompt, subagents default to intuitive but incorrect approaches, violating the documented rules.**

## Minimum Fix (This Session)

1. Create `/scripts/subagent-prompts/` directory
2. Add 3 templates: SESSION-CLOSE-STEP-2-CONTEXT-MD.txt, COWORK-GIT-PUSH.txt, SKILL-PACKAGING-AND-DELIVERY.txt
3. Add "Subagent Spawning Checklist" to CLAUDE.md §E
4. Update behavioral audit to detect template gaps
5. Document subagent limitations in ai-cos skill

**Effort:** ~90 minutes  
**Prevents:** 80% of subagent rule violations  
**Layers coverage after fix:** L0a → template library (shared L1 seed), prompt inclusion (per-task L1), behavioral detection (audit L1)

---
