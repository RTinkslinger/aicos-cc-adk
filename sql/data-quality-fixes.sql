-- Data Quality Fixes — M2 Loop 2
-- Date: 2026-03-20
-- Database: Supabase llfkxnsfczludgigknbs (Mumbai)
-- Executed by: Claude Code (automated)

-- ============================================================
-- FIX 1: Trim Trailing Whitespace (59 rows across 3 tables)
-- ============================================================

-- 1a: Companies names (20 rows affected)
UPDATE companies SET name = TRIM(name) WHERE name != TRIM(name);

-- 1b: Companies websites (0 rows — already clean)
UPDATE companies SET website = TRIM(website) WHERE website IS NOT NULL AND website != TRIM(website);

-- 1c: Network person names (11 rows affected)
UPDATE network SET person_name = TRIM(person_name) WHERE person_name != TRIM(person_name);

-- 1d: Portfolio company names (28 rows affected)
UPDATE portfolio SET portfolio_co = TRIM(portfolio_co) WHERE portfolio_co != TRIM(portfolio_co);

-- 1e: Fix non-breaking spaces (U+00A0) that TRIM doesn't catch
-- Multiwoven in companies (id: 288)
UPDATE companies SET name = 'Multiwoven' WHERE id = 288;
-- Tractor Factory in portfolio (id: 153)
UPDATE portfolio SET portfolio_co = 'Tractor Factory' WHERE id = 153;

-- ============================================================
-- FIX 2: Delete Test Rows (9 rows deleted)
-- ============================================================

-- Preserved legitimate companies: LambdaTest (id:5272), Testmint AI (id:4384)
DELETE FROM companies
WHERE name IN (
  '[TEST] Explicit Parent',       -- id: 16
  '[TEST] Migration',             -- ids: 17, 18
  '[TEST] Visual Check v2',       -- id: 19
  'TEST — Delete Me',             -- ids: 3643, 3644
  'ToC Test Page',                -- id: 3543
  'PantoMax (Test Co)',           -- id: 3014
  'SkillBridge Test Co'           -- id: 3537
);

-- ============================================================
-- FIX 3: Resolve Portfolio-to-Companies Name Mismatches (25/26 resolved)
-- ============================================================

-- Strategy: Update portfolio.portfolio_co to match companies.name canonical form
-- This ensures JOIN on LOWER(TRIM(name)) succeeds

-- 3a: Simple name mismatches (singular/plural, spacing, suffixes)
UPDATE portfolio SET portfolio_co = 'Eight Network' WHERE id = 54;         -- was 'Eight Networks'
UPDATE portfolio SET portfolio_co = 'ElecTrade (f.k.a. Hatch N Hack)' WHERE id = 55;  -- was 'ElecTrade'
UPDATE portfolio SET portfolio_co = 'Kubesense (f.k.a Tyke)' WHERE id = 88;  -- was 'Kubesense (Tyke)'
UPDATE portfolio SET portfolio_co = 'Multiwoven' WHERE id = 102;           -- exact match after NBSP fix
UPDATE portfolio SET portfolio_co = 'StepSecurity' WHERE id = 144;         -- was 'Step Security'

-- 3b: FKA aliases — portfolio had new name, companies had old name (or different FKA format)
UPDATE portfolio SET portfolio_co = 'Orbit Farming' WHERE id = 32;         -- was 'Ballisto AgriTech (f.k.a. Orbit Farming)'
UPDATE portfolio SET portfolio_co = 'Mindforest' WHERE id = 33;            -- was 'BetterPlace fka Mindforest'
UPDATE portfolio SET portfolio_co = 'Snowmountain AI' WHERE id = 123;      -- was 'Qwik Build (f.k.a Snowmountain)'
UPDATE portfolio SET portfolio_co = 'ReplyAll (PRBT)' WHERE id = 128;      -- was 'ReplyAll (f.k.a. PRBT)'
UPDATE portfolio SET portfolio_co = 'Stance Health (f.k.a. HealthFlex)' WHERE id = 142;  -- was 'Stance Health (f.k.a HealthFlex)' (missing period)
UPDATE portfolio SET portfolio_co = 'Patcorn' WHERE id = 148;              -- was 'Tejas (f.k.a Patcorn)'
UPDATE portfolio SET portfolio_co = 'AeroDome Technologies Private Limited' WHERE id = 159;  -- was 'VyomIC (f.k.a. AeroDome)'

-- 3c: Companies has variant names (with suffixes, FKA format, etc.)
UPDATE portfolio SET portfolio_co = 'Answers AI' WHERE id = 25;            -- was 'Answers.ai'
UPDATE portfolio SET portfolio_co = 'Dataflos (f.k.a. Blockfenders)' WHERE id = 36;  -- was 'Blockfenders'
UPDATE portfolio SET portfolio_co = 'Coffeee.io' WHERE id = 45;            -- was 'Coffeee'
UPDATE portfolio SET portfolio_co = 'Dodo Pay' WHERE id = 52;              -- was 'Dodo Payments'
UPDATE portfolio SET portfolio_co = 'DreamSpan (f.k.a. DreamSleep)' WHERE id = 53;  -- was 'DreamSleep'
UPDATE portfolio SET portfolio_co = 'Recrew AI (f.k.a. Gloroots)' WHERE id = 68;  -- was 'Gloroots'
UPDATE portfolio SET portfolio_co = 'Material Depot (YC W22)' WHERE id = 95;  -- was 'Material Depot'
UPDATE portfolio SET portfolio_co = 'NuPort Robotics' WHERE id = 106;      -- was 'NuPort'
UPDATE portfolio SET portfolio_co = 'Pinegap AI' WHERE id = 114;           -- was 'Pinegap'
UPDATE portfolio SET portfolio_co = 'Revspot.AI' WHERE id = 130;           -- was 'Revspot'
UPDATE portfolio SET portfolio_co = 'UGX AI' WHERE id = 155;               -- was 'UGX'
UPDATE portfolio SET portfolio_co = 'Rilo (f.k.a. Workatoms)' WHERE id = 160;  -- was 'Workatoms'

-- REMAINING UNMATCHED (1): 'Terra' (id:150) — no exact match in companies table
-- Candidates: Terra Motors (1905), Terra.do (477), Terractive (478) — needs manual resolution

-- ============================================================
-- FIX 4: Company Dedup (59 groups, 61 rows deleted)
-- ============================================================

-- Strategy: For each duplicate name group, keep the row with highest data richness
-- (most non-null fields across: website, sector, type, priority, venture_funding,
--  pipeline_status, deal_status, jtbd, sells_to, smart_money, research_file_path, founding_timeline)
-- On tie, keep the lowest ID.

-- Full dedup query:
WITH dupes AS (
  SELECT LOWER(TRIM(name)) as norm_name
  FROM companies
  GROUP BY LOWER(TRIM(name))
  HAVING count(*) > 1
),
scored AS (
  SELECT c.id, LOWER(TRIM(c.name)) as norm_name,
    (CASE WHEN c.website IS NOT NULL THEN 1 ELSE 0 END +
     CASE WHEN c.sector IS NOT NULL THEN 1 ELSE 0 END +
     CASE WHEN c.type IS NOT NULL THEN 1 ELSE 0 END +
     CASE WHEN c.priority IS NOT NULL THEN 1 ELSE 0 END +
     CASE WHEN c.venture_funding IS NOT NULL THEN 1 ELSE 0 END +
     CASE WHEN c.pipeline_status IS NOT NULL AND c.pipeline_status != 'NA' THEN 1 ELSE 0 END +
     CASE WHEN c.deal_status IS NOT NULL AND c.deal_status != 'NA' THEN 1 ELSE 0 END +
     CASE WHEN c.jtbd IS NOT NULL THEN 1 ELSE 0 END +
     CASE WHEN c.sells_to IS NOT NULL THEN 1 ELSE 0 END +
     CASE WHEN c.smart_money IS NOT NULL THEN 1 ELSE 0 END +
     CASE WHEN c.research_file_path IS NOT NULL THEN 1 ELSE 0 END +
     CASE WHEN c.founding_timeline IS NOT NULL THEN 1 ELSE 0 END) as richness
  FROM companies c
  JOIN dupes d ON LOWER(TRIM(c.name)) = d.norm_name
),
keepers AS (
  SELECT DISTINCT ON (norm_name) id as keep_id, norm_name
  FROM scored
  ORDER BY norm_name, richness DESC, id ASC
)
DELETE FROM companies c
USING scored s
LEFT JOIN keepers k ON s.norm_name = k.norm_name AND s.id = k.keep_id
WHERE c.id = s.id AND k.keep_id IS NULL;

-- Notable deletions:
-- Swiggy: kept id 1291 (richness 1), deleted 4458 & 4761
-- Betterhood: kept id 1478 (richness 4), deleted 1481 & 1482
-- CRED: kept id 112, deleted 1936
-- Flipkart: kept id 593, deleted 4146
-- Zomato: kept id 4571 (richness 4), deleted 1004 (richness 1)

-- ============================================================
-- FIX 5: Generate page_content_path for Companies (467 rows updated)
-- ============================================================

-- Slugification: LOWER(name) → replace non-alphanumeric with hyphens → collapse multiple hyphens → strip leading/trailing hyphens
-- Path format: 'companies-pages/{slug}.md'
-- Matched against 526 files in companies-pages/ directory

UPDATE companies
SET page_content_path = 'companies-pages/' ||
  REGEXP_REPLACE(
    REGEXP_REPLACE(
      REGEXP_REPLACE(
        LOWER(name),
        '[^a-z0-9]+', '-', 'g'
      ),
      '-+', '-', 'g'
    ),
    '(^-|-$)', '', 'g'
  ) || '.md'
WHERE REGEXP_REPLACE(
    REGEXP_REPLACE(
      REGEXP_REPLACE(
        LOWER(name),
        '[^a-z0-9]+', '-', 'g'
      ),
      '-+', '-', 'g'
    ),
    '(^-|-$)', '', 'g'
  ) IN (
    -- [526 slug values from companies-pages/ directory listing]
    -- See full list in audit report
  )
AND page_content_path IS NULL;

-- 467 of 526 files matched to company rows
-- 59 files unmatched due to accented characters, apostrophes, or edge case slug differences
