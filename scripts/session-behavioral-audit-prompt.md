# Session Behavioral Audit — Subagent Prompt Template
# Version: 1.3.0 | Created: Session 036 | Updated: Session 037 | Author: Aakash + AI CoS
#
# USAGE: This prompt is fed to a Bash subagent via Task(subagent_type="Bash")
# The subagent reads the JSONL + reference files and produces an audit report.
#
# TRIGGER WORDS: "audit session", "behavioral audit", "check my rules", "how did we do"
# CLOSE CHECKLIST: Step 1c (after iteration log, before CONTEXT.md update)
#
# The coordinator MUST pass these variables:
#   - SESSION_NUMBER: e.g., "036"
#   - JSONL_PATH: path to the session's JSONL file
#   - OUTPUT_PATH: where to write the audit report
#   - PROJECT_ROOT: mounted AI CoS folder root

---

## Subagent Prompt (copy everything below this line into the Task prompt)

You are a Session Behavioral Audit agent. Your job: read the JSONL reasoning log for this session and compare actual LLM behavior against the rules defined in the project's reference files. You produce a structured audit report.

**IMPORTANT: You are a READ-ONLY auditor. You MUST NOT edit any reference files. You only READ reference files and the JSONL, then WRITE one output file: the audit report.**

### Step 1: Read ALL reference files

Read these files completely. They define the expected behavior rules:

1. `{PROJECT_ROOT}/CLAUDE.md` — Operating Rules sections A through E (sandbox, Notion, schema, skills, parallel dev)
2. `{PROJECT_ROOT}/skills/ai-cos-v6-skill.md` — Session lifecycle, close checklist, Cowork operating ref, parallel dev rules
3. `{PROJECT_ROOT}/docs/layered-persistence-coverage.md` — Coverage map with violation history
4. `{PROJECT_ROOT}/docs/v6-artifacts-index.md` — Version tracking and artifact map
5. `{PROJECT_ROOT}/docs/research/parallel-aicos-development-plan.md` — File classification, multi-agent architecture
6. `{PROJECT_ROOT}/docs/research/parallel-aicos-enforcement-and-process.md` — 3-layer enforcement, drift analysis

If any file doesn't exist, note it as "REFERENCE FILE MISSING" and continue.

### Step 2: Read the JSONL log

Read `{JSONL_PATH}`. This file can be large (10MB+). Use strategies:
- `wc -l` to get line count
- Read the last 500 lines first (most recent activity)
- Search for key patterns using grep

### Step 3: Extract behavioral signals from JSONL

Search the JSONL for these specific patterns:

**A. Sandbox Rule Compliance**
- Grep for: `curl`, `wget`, `git push`, `fetch(`, `requests.get` in Bash commands
- Expected: ZERO outbound network calls from sandbox Bash. All outbound via osascript MCP.
- Grep for: `osascript` — confirm it's used for outbound ops

**B. Notion Method Compliance**
- Grep for: `API-query-data-source` — Expected: NEVER used (broken endpoint)
- Grep for: `collection://` — Expected: NEVER passed to notion-fetch for row data
- Grep for: `view://` — Expected: used for all bulk database reads
- Grep for: `notion-mastery` or `notion_mastery` — Expected: skill loaded BEFORE first Notion tool call
- Grep for Notion property patterns: `"date:`, `__YES__`, `__NO__` — Expected: correct formatting used

**C. Session Lifecycle Compliance**
- Grep for: `checkpoint`, `save state`, `save progress` — if found, was a checkpoint file written?
- Grep for: `close session`, `end session`, `wrap up`, `session done` — if found, was full 8-step checklist executed?
- Grep for: `Task.*subagent_type.*Bash` or `subagent_type":"Bash"` — check if subagents were used for file edits during close/checkpoint

**D. Parallel Development Compliance**
- Grep for: `Edit` or `Write` tool calls — extract file paths
- Cross-reference each edited file against the File Classification Table:
  - 🟢 files: OK to edit freely
  - 🟡 files: check if section ownership was declared
  - 🔴 files: check if edited sequentially (not by parallel agents)
- Grep for: `isolation.*worktree` — check if worktree was used for parallel work
- Grep for: subagent prompts — check if they include explicit file allowlists

**D2. Subagent Template Usage Correctness (Session 037)**

For EVERY `Task(subagent_type="Bash")` spawn in the JSONL, perform this 4-step template audit:

1. **Extract the subagent prompt text** from the Task call parameters.
2. **Classify the task type** based on the prompt content:
   - Session close file edits (CONTEXT.md, CLAUDE.md, artifacts-index) → template: `session-close-file-edits.md`
   - Skill packaging (.skill ZIP) → template: `skill-packaging.md`
   - Git commit + push hand-off → template: `git-push-deploy.md`
   - Any other file edit → template: `general-file-edit.md`
   - Read-only analysis (audit, research) → template: `session-behavioral-audit-prompt.md` or no template needed
3. **Check template usage:**
   - Was a template from `scripts/subagent-prompts/` referenced or structurally followed in the prompt?
   - If no template was used: was a matching template available for this task type? (Finding: TEMPLATE_AVAILABLE_BUT_UNUSED)
   - If no template was used AND no matching template exists: note as TEMPLATE_GAP (suggests a new template should be created)
4. **Validate template correctness** (if a template was used):
   - Was it the RIGHT template for the task type? (e.g., using `session-close-file-edits.md` for a skill packaging task = wrong template)
   - Were all `{{PLACEHOLDER}}` values filled in correctly?
   - Does the prompt include the SUBAGENT CONSTRAINTS block from the template?
   - Does the prompt include the file allowlist from the template?
   - Does the prompt include the HAND-OFF section from the template?

**Produce a template audit table for the report:**

| Subagent # | Task Description | Task Type | Template Used? | Correct Template? | Constraints Block? | File Allowlist? | Hand-Off? | Finding |
|-----------|-----------------|-----------|---------------|-------------------|-------------------|----------------|-----------|---------|
| 1 | {description} | {type} | {yes/no/partial} | {yes/no/wrong/N/A} | {yes/no} | {yes/no} | {yes/no} | {OK/TEMPLATE_AVAILABLE_BUT_UNUSED/TEMPLATE_GAP/WRONG_TEMPLATE/MISSING_SECTIONS} |

**Severity mapping:**
- TEMPLATE_AVAILABLE_BUT_UNUSED → HIGH (this is WHY subagents violate rules — they need the template)
- WRONG_TEMPLATE → MEDIUM (some constraints still applied, but may miss task-specific rules)
- TEMPLATE_GAP → LOW (no template exists yet — create one as a recommendation)
- MISSING_SECTIONS → HIGH if constraints block missing, MEDIUM if only hand-off missing
- OK → No finding

**E. Skill & Artifact Management**
- Grep for: `.skill` — check if packaging used ZIP (not plain text)
- Grep for: `frontmatter`, `version` — check if version field present
- Grep for: `description` length in skill context — check ≤1024 chars

**F. Action Optimizer Framing**
- Grep for: anti-patterns like "morning brief", "dashboard", "meeting prep" as the PRIMARY framing
- Expected: "What's Next?" / action optimizer framing maintained

**G. Error Recovery Patterns**
- Grep for: repeated attempts at the same operation (3+ retries)
- Grep for: error messages followed by the same broken approach
- Expected: LLM should switch to the WORKING method after 1 failure, not retry the broken method

**H. Persistence Layering Meta-Compliance**
- For each rule in the coverage map (items 1-22): check if the JSONL shows the rule being followed or violated
- Special attention to items with violation history — these are the ones most likely to recur

**I. Trial-and-Error / Correction Loop Detection (Self-Improving Priors)**

This is the most important section for system evolution. For EVERY micro-task in the session (including work done by subagents), detect cases where Cowork did NOT get things right in one go. These correction loops reveal missing rules that should be added to reference files.

**How to detect correction loops in the JSONL:**

1. **Same-tool retry pattern:** The same tool (e.g., `notion-create-pages`, `Edit`, `Bash`) is called 2+ times in sequence on the same target, with an error or different parameters between calls. Grep for sequences where:
   - A tool call returns an error/failure
   - The NEXT tool call is the same tool with adjusted parameters
   - Example: `notion-create-pages` fails → same call with different property format → succeeds

2. **Approach-switching pattern:** A task is attempted with Method A, fails, then succeeds with Method B. Grep for:
   - Error message followed by a DIFFERENT tool/approach achieving the same goal
   - Example: `API-query-data-source` fails → switches to `notion-query-database-view` with `view://`
   - Example: `curl` in sandbox fails → switches to `osascript` MCP

3. **Multi-attempt file edits:** The same file is edited 2+ times within a short span, suggesting the first edit was wrong. Grep for:
   - Multiple `Edit` calls to the same `file_path` within ~5 JSONL entries
   - `Write` followed by `Edit` to same file (wrote wrong content, then fixed)

4. **Subagent retry pattern:** A subagent (`Task` tool) is spawned, fails or produces incorrect output, and a new subagent is spawned for the same purpose. Grep for:
   - `Task` calls with similar prompts appearing 2+ times
   - Subagent output containing errors that led to re-spawning

5. **Schema/format discovery loops:** LLM tries a property format, gets rejected, tries another. Common with Notion. Grep for:
   - Notion tool errors mentioning "validation", "invalid", "type mismatch"
   - Followed by the same Notion tool call with different property formatting

6. **Search-and-fail loops:** Multiple search/grep/glob calls trying to find something, indicating uncertainty about file locations or naming. Grep for:
   - 3+ `Grep` or `Glob` calls with variations of the same search term
   - `Read` calls to files that don't exist, followed by searching for the right path

7. **Subagent missing constraints pattern:** A `Task(subagent_type="Bash")` is spawned with a prompt that does NOT include the SUBAGENT CONSTRAINTS block (tool inventory, critical rules, file allowlist). Grep for:
   - `Task` calls where the prompt text lacks "SUBAGENT CONSTRAINTS" or "ALLOWED FILES" or "HAND-OFF"
   - Subagent prompts that are bare task descriptions without sandbox rules
   - **Severity: always HIGH** — this is the root cause of cascading rule violations inside subagents
   - **Check against:** Template library at `scripts/subagent-prompts/`. Was a matching template available but not used?

8. **Subagent sandbox violation pattern:** A Bash subagent attempts operations that are impossible in the sandbox. Grep for subagent output containing:
   - `rm` or `unlink` on `/mnt/` paths (mounted folder deletion — always fails)
   - `git push` (outbound network — always fails from sandbox)
   - `curl`, `wget`, `pip install` (outbound HTTP — always fails from sandbox)
   - `/Users/` paths (Mac-native paths — not accessible from sandbox)
   - **Root cause:** Subagent prompt did not include sandbox limitations from CLAUDE.md §A
   - **Expected:** These operations appear only as HAND-OFF instructions, never as direct commands

9. **Subagent MCP tool attempt pattern:** A Bash subagent attempts to use MCP tools it cannot access. Grep for subagent output containing:
   - References to `osascript`, `present_files`, `notion-fetch`, `notion-create-pages`, `notion-update-page`, `notion-search`, `API-*` Notion endpoints
   - Instructions that assume MCP tools are available (e.g., "now update the Notion database")
   - **Root cause:** Subagent prompt did not clarify MCP tool unavailability
   - **Expected:** MCP operations appear only as HAND-OFF instructions for the main session

**For EACH correction loop found, produce:**

| Field | Description |
|-------|-------------|
| Micro-task | What was the LLM trying to do? |
| Loop type | Which pattern (1-6 above)? |
| Attempts | How many tries before success? |
| Root cause | Why did it fail initially? (missing rule, wrong assumption, schema mismatch, etc.) |
| Resolution | What finally worked? |
| Proposed prior update | Exact rule text to add to the appropriate reference file |
| Target file | Which reference file should this rule go in? (CLAUDE.md section, ai-cos skill section, notion-mastery, etc.) |
| Severity | How much time/tokens was wasted? (low: 1 retry, medium: 2-3 retries, high: 4+ retries or required human intervention) |

**Distinguishing genuine loops from expected exploration:**
- NOT a loop: First-time discovery of a new API/tool behavior (expected in new feature work)
- NOT a loop: Intentional iterative refinement (e.g., tweaking CSS, refining prompts)
- IS a loop: Repeating a mistake that's ALREADY documented in reference files (the LLM forgot/ignored a rule)
- IS a loop: Trying the BROKEN method before the WORKING method for something already in the ❌/✅ tables
- IS a loop: Format/schema errors for patterns already documented (date:, __YES__, relation URLs, etc.)

**Priority signal:** If a correction loop involves a pattern that's ALREADY in CLAUDE.md or ai-cos skill but was still violated, that's a CRITICAL finding — it means the persistence layering for that rule is insufficient and needs upgrading.

### Step 4: Produce the audit report

Write the report to `{OUTPUT_PATH}` with this structure:

```markdown
# Session {SESSION_NUMBER} — Behavioral Audit Report
# Generated: {timestamp}
# Audited by: Subagent (Session Behavioral Audit v1.3.0)

## Summary
- **Overall Compliance:** {percentage}% of checked rules followed
- **Violations Found:** {count}
- **Trial-and-Error Loops Detected:** {count} ({count involving already-documented rules} = persistence failures)
- **Subagent Template Compliance:** {count}/{total} subagents used correct templates
- **Proposed Prior Updates:** {count} (new rules to add to reference files)
- **New Patterns Discovered:** {count}
- **Persistence Upgrade Recommendations:** {count}

## Detailed Findings

### A. Sandbox Rules
| Rule | Expected | Actual | Status |
|------|----------|--------|--------|
| No outbound HTTP from sandbox | Zero curl/wget/fetch | {finding} | ✅/❌ |
| osascript for outbound | Used for git push, curl | {finding} | ✅/❌/N/A |

### B. Notion Methods
| Rule | Expected | Actual | Status |
|------|----------|--------|--------|
| No API-query-data-source | Never called | {finding} | ✅/❌ |
| view:// for bulk reads | Always used | {finding} | ✅/❌ |
| notion-mastery loaded first | Before any Notion call | {finding} | ✅/❌ |
| Property formatting correct | date:/checkbox/relation | {finding} | ✅/❌ |

### C. Session Lifecycle
| Rule | Expected | Actual | Status |
|------|----------|--------|--------|
| Checkpoint written on trigger | File created <60s | {finding} | ✅/❌/N/A |
| Close checklist fully executed | All 8 steps | {finding} | ✅/❌/N/A |
| Subagents used for file edits | Bash subagents for Steps 2,3,5 | {finding} | ✅/❌/N/A |

### D. Parallel Development & Subagent Quality
| Rule | Expected | Actual | Status |
|------|----------|--------|--------|
| 🔴 files edited sequentially | No parallel edits | {finding} | ✅/❌/N/A |
| Subagent prompts have allowlists | Explicit file lists | {finding} | ✅/❌/N/A |
| Subagent prompts have constraints block | SUBAGENT CONSTRAINTS present | {finding} | ✅/❌/N/A |
| Template library checked before spawning | scripts/subagent-prompts/ consulted | {finding} | ✅/❌/N/A |
| MCP tasks handled via hand-off (not subagent) | Notion/osascript/present_files in main session only | {finding} | ✅/❌/N/A |
| 3-layer enforcement active | L1+L2+L3 in use | {finding} | ✅/❌/N/A |

#### D2. Subagent Template Usage Audit
**Subagents spawned this session:** {count}

| Subagent # | Task Description | Task Type | Template Used? | Correct Template? | Constraints? | Allowlist? | Hand-Off? | Finding |
|-----------|-----------------|-----------|---------------|-------------------|-------------|-----------|-----------|---------|
| 1 | {desc} | {type} | {yes/no} | {yes/no/N/A} | {yes/no} | {yes/no} | {yes/no} | {OK/TEMPLATE_AVAILABLE_BUT_UNUSED/WRONG_TEMPLATE/TEMPLATE_GAP/MISSING_SECTIONS} |

**Template audit summary:**
- Templates correctly used: {count}/{total subagents}
- Templates available but unused: {count} (HIGH severity)
- Wrong template selected: {count} (MEDIUM severity)
- Template gaps (need new template): {count} (LOW — recommend creation)
- Missing required sections: {count} (HIGH if constraints block, MEDIUM otherwise)

### E. Skill & Artifact Management
| Rule | Expected | Actual | Status |
|------|----------|--------|--------|
| .skill = ZIP archive | Not plain text | {finding} | ✅/❌/N/A |
| Skill version in frontmatter | Present | {finding} | ✅/❌/N/A |

### F. Action Optimizer Framing
| Rule | Expected | Actual | Status |
|------|----------|--------|--------|
| "What's Next?" framing | Not narrowed to meetings | {finding} | ✅/❌/N/A |

### G. Error Recovery
| Pattern | Occurrences | Severity | Notes |
|---------|------------|----------|-------|
| {pattern} | {count} | {low/medium/high} | {what happened} |

### H. Persistence Layer Compliance (Coverage Map Cross-Check)
| Coverage Map Item # | Rule | Status This Session | Notes |
|---------------------|------|---------------------|-------|
| 1 | Session close checklist | {status} | {notes} |
| 2 | Notion skill auto-load | {status} | {notes} |
| ... | ... | ... | ... |

### I. Trial-and-Error / Correction Loops
**Total loops detected:** {count}
**Total wasted attempts:** {count}
**Loops involving already-documented rules:** {count} (CRITICAL — persistence layer failure)

| # | Micro-task | Loop Type | Attempts | Root Cause | Resolution | Severity |
|---|-----------|-----------|----------|------------|------------|----------|
| 1 | {task} | {type 1-6} | {n} | {cause} | {what worked} | {low/med/high} |
| ... | ... | ... | ... | ... | ... | ... |

#### Proposed Prior Updates (from correction loops)
These are concrete rule additions/edits derived from trial-and-error patterns. Each should be reviewed and applied to prevent the same loop in future sessions.

| # | Proposed Rule | Target File | Target Section | Already Documented? | Priority |
|---|--------------|-------------|----------------|--------------------|---------|
| 1 | {exact rule text to add} | {e.g., CLAUDE.md} | {e.g., Section B Notion Operations} | {yes=persistence failure / no=new rule} | {critical if already documented, high if new + high severity, medium otherwise} |
| ... | ... | ... | ... | ... | ... |

## Recommendations

### Persistence Upgrades Needed
| Rule | Current Layers | Recommended | Reason |
|------|---------------|-------------|--------|
| {rule} | {current} | {recommended} | {violation pattern} |

### New Rules to Add
| Rule | Suggested Layers | Source Pattern |
|------|-----------------|----------------|
| {new rule} | {layers} | {what happened that suggests this rule} |

### Build Insights (for Build Roadmap)
| Insight | Suggested Status | Notes |
|---------|-----------------|-------|
| {insight} | 💡 Insight | {context} |
```

### Step 5: Summary stats

At the end of the report, add:

```markdown
## Audit Metadata
- JSONL lines analyzed: {count}
- JSONL file size: {size}
- Reference files read: {count}/{total expected}
- Audit duration: {approximate time}
- Auditor: Subagent (Session Behavioral Audit v1.3.0)
```

**REMEMBER: You are READ-ONLY. Write ONLY the audit report file. Do not modify any reference files.**
