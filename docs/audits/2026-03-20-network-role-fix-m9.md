# Network Role Fix - Emergency P0

**Date:** 2026-03-20
**Severity:** P0 - Critical data corruption
**Database:** Supabase `llfkxnsfczludgigknbs` / `network` table

## Bug Summary

All 3,722 rows in the `network` table had `current_role = 'postgres'` -- the PostgreSQL system function `current_role` resolved instead of the table column, due to an unquoted reference in a SQL statement (likely during a mass upsert or migration).

## Root Cause

PostgreSQL has a built-in function `current_role` that returns the current database user (in Supabase's case, `'postgres'`). When SQL references `current_role` without quoting (`"current_role"`), PostgreSQL interprets it as the system function, not the column name.

The corruption was likely caused by a SQL statement like:
```sql
-- BAD: current_role resolves to system function 'postgres'
UPDATE network SET current_role = current_role WHERE ...;
-- or
INSERT INTO network (..., current_role, ...) VALUES (..., current_role, ...);
```

The correct form requires quoting:
```sql
-- GOOD: quotes force column reference
UPDATE network SET "current_role" = 'Co-Founder CEO' WHERE ...;
```

## Investigation

| Check | Result |
|-------|--------|
| Rows with `current_role = 'postgres'` | 3,722 (100%) |
| Other columns corrupted | None (person_name, linkedin, ryg, etc. all clean) |
| Rows with notion_page_id | 3,320 |
| Rows without notion_page_id | 402 |
| Recovery data available | Yes -- `network-full-export.json` (3,339 entries with Notion properties) |

## Recovery Process

1. **Source data:** `sql/data/network-full-export.json` -- Notion API export with raw property structure
2. **Extraction:** Parsed `Current Role` select property from each entry's Notion properties
3. **Coverage:** 2,829 entries with valid roles out of 3,339 total (510 had NULL role in Notion)
4. **Method:**
   - First, set all `current_role = 'postgres'` to NULL
   - Then, applied UPDATE via `fill-final` SQL batch files + direct VALUES-based UPDATEs
   - All UPDATEs used properly quoted `"current_role"` column name

## Result

| Metric | Before | After |
|--------|--------|-------|
| `current_role = 'postgres'` | 3,722 | **0** |
| Valid non-NULL roles | 0 | **3,225** |
| NULL roles (no data in Notion) | 0 | **497** |

### Role Distribution (Top 10)

| Role | Count |
|------|-------|
| Co-Founder CEO | 1,090 |
| Founder | 432 |
| Co-founder | 369 |
| Co-Founder CTO | 285 |
| Co-Founder COO | 230 |
| VC Partner | 168 |
| CEO | 72 |
| Co-Founder | 55 |
| CTO | 52 |
| IP @ VC | 44 |

## 497 NULL Roles Breakdown

- 0 rows without notion_page_id (all 402 such rows got roles from other import paths)
- 497 rows with notion_page_id but no Current Role set in Notion source data
- These are genuinely empty in the source -- not a recovery gap

## Prevention

**MANDATORY for all future SQL touching the `network` table:**

1. Always quote `"current_role"` in SQL -- it collides with the PostgreSQL system function
2. The existing `fill-final` SQL files already use correct quoting
3. Any ORM or migration code that generates SQL for this column must use quoted identifiers
4. Consider renaming the column to `role` or `person_role` to eliminate the collision entirely (future migration)

## Files Referenced

- Recovery data: `sql/data/network-full-export.json`
- Original fill SQL: `sql/data/fill-final/000-current_role.sql` through `009-current_role.sql`
- Notion export: `sql/data/network-notion-export.json` (529 entries, supplementary)
