# P2-01: Cross-File Reference Integrity Audit

**Date:** 2026-03-04  
**Audit Type:** Cross-file reference resolution (dead links)  
**Scope:** All .md documentation files in AI CoS project  

## Executive Summary

A comprehensive scan of internal file path references across 4 key documentation files identified **80 total references** with **9 broken references** (11% broken, 89% verified).

**Critical Finding:** 5 references point to superseded artifact versions (v1, v5) that have been upgraded to v6. This represents **documentation drift** from the persistence layer upgrade in Session 033.

## Audit Scope

**Files Scanned:**
- CLAUDE.md (operating rules and quick reference)
- CONTEXT.md (master context document)
- docs/v6-artifacts-index.md (artifact registry)
- docs/layered-persistence-coverage.md (persistence tracking)

**Patterns Searched:**
- `scripts/*` files and directories
- `docs/*` files and directories
- `skills/*` files and directories
- `aicos-digests/*` files and directories
- `queue/`, `digests/`, `.skills/`, `.github/` paths

## Results Summary

| Metric | Count |
|--------|-------|
| Total references found | 80 |
| Resolved (exist) | 71 |
| Broken (missing) | 9 |
| Pass rate | 88.75% |

## Broken References (Detailed Analysis)

### Category A: Path Location Errors (2 refs)

**Issue:** References point to incorrect subdirectories within the project.

#### 1. `.github/workflows/deploy.yml` (2 occurrences)

**Locations:**
- CONTEXT.md:357 — "Auto-deploy (single path)" section
- CONTEXT.md:684 — Session 020 session log

**Current Reality:**
- File EXISTS at: `aicos-digests/.github/workflows/deploy.yml`
- Referenced as: `.github/workflows/deploy.yml` (at root level)
- Status: ✅ File exists, but reference is incomplete/imprecise

**Impact:** Low — the file IS deployed and functional. References are technically correct within the aicos-digests subproject context, but doc references omit the subproject prefix.

**Recommendation:** Update CONTEXT.md references to clarify:
- Change: `.github/workflows/deploy.yml`
- To: `aicos-digests/.github/workflows/deploy.yml`

---

#### 2. `skills/notion-mastery/SKILL.md` (1 occurrence)

**Location:**
- CONTEXT.md:492 — Session 018 session log

**Current Reality:**
- File EXISTS at: `.skills/skills/notion-mastery/SKILL.md`
- Referenced as: `skills/notion-mastery/SKILL.md` (missing `.skills/` prefix)
- Status: ✅ File exists, but reference uses incorrect path

**Impact:** Medium — can cause confusion about where the actual source file is located. Users looking for `skills/notion-mastery/SKILL.md` won't find it.

**Recommendation:** Update CONTEXT.md:492 to clarify this is installed in .skills:
- Change: `skills/notion-mastery/SKILL.md`
- To: `.skills/skills/notion-mastery/SKILL.md`

---

### Category B: Superseded Version References (3 refs)

**Issue:** References to older artifact versions (v1, v5) that have been upgraded to v6 in Session 033+. Indicates documentation drift from persistence layer upgrade.

#### 3. `docs/claude-user-preferences-v5.md` (1 occurrence)

**Location:**
- CONTEXT.md:688 — "Layer 0b" artifact list in persistence architecture section

**Current Reality:**
- File DOES NOT EXIST (upgraded to v6)
- Current version: `docs/claude-user-preferences-v6.md` ✅
- Status: ❌ Broken reference to superseded artifact

**Impact:** Medium — suggests outdated layer coverage documentation. The v6 file exists and is current, but reference still points to v5.

**Recommendation:** Update CONTEXT.md:688:
- Change: `docs/claude-user-preferences-v5.md`
- To: `docs/claude-user-preferences-v6.md`

---

#### 4. `docs/claude-memory-entries-v5.md` (2 occurrences)

**Locations:**
- CONTEXT.md:688 — "Layer 1" artifact list
- layered-persistence-coverage.md:75 — "If new Memory entries needed" note

**Current Reality:**
- File DOES NOT EXIST (upgraded to v6)
- Current version: `docs/claude-memory-entries-v6.md` ✅
- Status: ❌ Broken reference to superseded artifact

**Impact:** High — appears in BOTH the master context and the persistence tracking map. Users running persistence audits or updating memory entries would reference the wrong file.

**Recommendation:** Update both files:
- CONTEXT.md:688: Change `docs/claude-memory-entries-v5.md` → `docs/claude-memory-entries-v6.md`
- layered-persistence-coverage.md:75: Change `docs/claude-memory-entries-v5.md` → `docs/claude-memory-entries-v6.md`

---

#### 5. `docs/cowork-global-instructions-v1.md` (1 occurrence)

**Location:**
- CONTEXT.md:690 — "Layer 0a" artifact list in persistence architecture section

**Current Reality:**
- File DOES NOT EXIST (upgraded to v6)
- Current version: `docs/cowork-global-instructions-v6.md` ✅
- Status: ❌ Broken reference to superseded artifact

**Impact:** Medium — again in persistence layer docs. References old v1 instead of current v6.

**Recommendation:** Update CONTEXT.md:690:
- Change: `docs/cowork-global-instructions-v1.md`
- To: `docs/cowork-global-instructions-v6.md`

---

### Category C: Template/Placeholder References (2 refs)

**Issue:** References use template syntax to describe file naming patterns, not actual files.

#### 6-7. Template Paths (Informational)

**Locations:**
- CONTEXT.md:590 — `docs/session-checkpoints/SESSION-{NNN}-CHECKPOINT-{N}.md`
- CONTEXT.md:623 — `docs/iteration-logs/{date}-session-{NNN}-{slug}.md`

**Current Reality:**
- These are TEMPLATES, not literal filenames
- Actual files follow these patterns (verified: 40+ checkpoint and iteration files exist)
- Status: OK — these are documentation templates

**Impact:** None — correctly documented as patterns

**Recommendation:** These references are fine as-is. They correctly use `{placeholder}` syntax to indicate template patterns.

---

## Verification Results by File

### CLAUDE.md
- **Total references:** 17
- **Verified:** 17 (100%)
- **Broken:** 0
- **Status:** ✅ PASS

All operating rules and quick-reference paths resolve correctly.

---

### CONTEXT.md
- **Total references:** 48
- **Verified:** 40 (83%)
- **Broken:** 8
- **Status:** ⚠️ NEEDS FIXES

Issues found:
- 2 incomplete path references (missing subdirectory prefix)
- 3 superseded version references (v1, v5 instead of v6)
- 2 template/placeholder references (acceptable)
- 1 GitHub workflows path imprecision

---

### docs/v6-artifacts-index.md
- **Total references:** 12
- **Verified:** 12 (100%)
- **Status:** ✅ PASS

Artifact registry correctly references all v6 files.

---

### docs/layered-persistence-coverage.md
- **Total references:** 3
- **Verified:** 2 (66%)
- **Broken:** 1
- **Status:** ⚠️ NEEDS FIXES

Issue: References outdated `claude-memory-entries-v5.md` instead of v6.

---

## Critical Categories

### HIGH PRIORITY (Update Now)

1. **Broken memory entries reference in persistence tracking:**
   - `layered-persistence-coverage.md:75`
   - Points to superseded v5 file
   - Used in persistence audits (run every 5 sessions)
   - **Impact:** Audits may reference wrong file

2. **All three v1/v5 references in CONTEXT.md:**
   - Lines 688, 690 (v1 and v5 in persistence architecture section)
   - Indicates drift from Session 033 upgrade to v6
   - **Impact:** Users updating persistence layer see old versions

### MEDIUM PRIORITY (Update Soon)

3. **Incomplete path references:**
   - `.github/workflows/deploy.yml` should be `aicos-digests/.github/workflows/deploy.yml`
   - `skills/notion-mastery/SKILL.md` should be `.skills/skills/notion-mastery/SKILL.md`
   - **Impact:** Users searching for files may not find correct location

---

## Root Cause Analysis

**Primary Issue:** Persistence layer upgraded from v5→v6 in Session 033, but **5 references to old versions** were not updated in CONTEXT.md and persistence tracking map. This is a known anti-pattern (Session 024 rule: "When bumping any artifact version, check ALL 6 artifacts").

**Secondary Issue:** Documentation omits subdirectory context for paths that exist within subproject folders (aicos-digests/.github/, .skills/skills/). References are partially correct but imprecise.

---

## Recommended Fixes

### Fix 1: Update CONTEXT.md (3 changes)

**Line 357:** Update GitHub workflow path
```
OLD: GitHub Action (`.github/workflows/deploy.yml`)
NEW: GitHub Action (`aicos-digests/.github/workflows/deploy.yml`)
```

**Line 492:** Fix notion-mastery path
```
OLD: `skills/notion-mastery/SKILL.md`
NEW: `.skills/skills/notion-mastery/SKILL.md`
```

**Lines 688-690:** Update artifact versions in persistence layer table
```
OLD: 
- v5 docs/claude-user-preferences-v5.md
- v5 docs/claude-memory-entries-v5.md
- v1 docs/cowork-global-instructions-v1.md

NEW:
- v6 docs/claude-user-preferences-v6.md
- v6 docs/claude-memory-entries-v6.md
- v6 docs/cowork-global-instructions-v6.md
```

### Fix 2: Update layered-persistence-coverage.md (1 change)

**Line 75:** Update in "If new Memory entries needed" note
```
OLD: update `docs/claude-memory-entries-v5.md`
NEW: update `docs/claude-memory-entries-v6.md`
```

### Fix 3: Update CONTEXT.md Session 020 log (1 change)

**Line 684:** Fix GitHub workflow path in session notes
```
OLD: GitHub Action (`.github/workflows/deploy.yml`)
NEW: GitHub Action (`aicos-digests/.github/workflows/deploy.yml`)
```

---

## Summary Statistics

| Dimension | Value |
|-----------|-------|
| Total files scanned | 4 |
| Total unique paths checked | 80 |
| Paths that resolve | 71 |
| Broken paths | 9 |
| Critical issues (must fix) | 5 |
| Medium-priority issues | 2 |
| Pass rate | 88.75% |

**Confidence:** High — all broken references have been traced to actual locations or identified as templates.

---

**Audit completed:** 2026-03-04 at 09:25 UTC  
**Auditor:** Bash subagent (cross-file reference verification)  
**Tool:** Python3 path resolution script with regex pattern matching
