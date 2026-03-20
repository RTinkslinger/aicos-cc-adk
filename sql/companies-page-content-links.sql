-- Companies Page Content Links
-- Generated: 2026-03-20
-- Purpose: Add page_content_path column and link to extracted MD files
-- DO NOT EXECUTE without review - prepared SQL only

-- Step 1: Add the column
ALTER TABLE companies ADD COLUMN IF NOT EXISTS page_content_path TEXT;

-- Step 2: Update paths for companies with extracted page content
-- Batch 1: Rich content pages (extensive notes, scoring, meeting notes)
UPDATE companies SET page_content_path = 'companies-pages/10medz.md' WHERE id = 9;
UPDATE companies SET page_content_path = 'companies-pages/ablecredit.md' WHERE id = 22;
UPDATE companies SET page_content_path = 'companies-pages/aerodome-technologies-private-limited.md' WHERE id = 25;
UPDATE companies SET page_content_path = 'companies-pages/alteon-energy.md' WHERE id = 33;
UPDATE companies SET page_content_path = 'companies-pages/alter-ai.md' WHERE id = 34;

-- Batch 2: Pages with notes (some real content)
UPDATE companies SET page_content_path = 'companies-pages/agara.md' WHERE id = 26;
UPDATE companies SET page_content_path = 'companies-pages/akrid.md' WHERE id = 29;
UPDATE companies SET page_content_path = 'companies-pages/alben-d-souzas-company.md' WHERE id = 30;
UPDATE companies SET page_content_path = 'companies-pages/arjun-junejas-company.md' WHERE id = 40;
UPDATE companies SET page_content_path = 'companies-pages/arya-pathaks-company-na.md' WHERE id = 42;

-- Batch 3: Template-only pages (scaffolding structure, no filled-in notes)
UPDATE companies SET page_content_path = 'companies-pages/10vc.md' WHERE id = 10;
UPDATE companies SET page_content_path = 'companies-pages/10x-science.md' WHERE id = 11;
UPDATE companies SET page_content_path = 'companies-pages/360-one.md' WHERE id = 13;
UPDATE companies SET page_content_path = 'companies-pages/abhinav-sharmas-new-company.md' WHERE id = 20;
UPDATE companies SET page_content_path = 'companies-pages/abhishek-konas-company.md' WHERE id = 21;
UPDATE companies SET page_content_path = 'companies-pages/activate-ai.md' WHERE id = 23;
UPDATE companies SET page_content_path = 'companies-pages/adityas-vc-fund.md' WHERE id = 24;
UPDATE companies SET page_content_path = 'companies-pages/ahead-vc.md' WHERE id = 27;
UPDATE companies SET page_content_path = 'companies-pages/allter.md' WHERE id = 31;
UPDATE companies SET page_content_path = 'companies-pages/ankur-capital.md' WHERE id = 36;
UPDATE companies SET page_content_path = 'companies-pages/arrakis.md' WHERE id = 41;

-- Blank pages (no content extracted - these exist in Notion but have no body text):
-- id=12: 10x Science (YC W26) - blank page
-- id=14: 3one4 Capital - blank page
-- id=15: 8X Ventures - blank page
-- id=28: AJVC Fund - blank page
-- id=32: Alphonse Daudet highschool - blank page
-- id=35: Ambak - blank page (note: Portfolio company, content may be in Portfolio Interaction Notes)
-- id=37: Annamalaiyar Matriculation Higher Secondary School - blank page
-- id=38: Answers AI - blank page (note: Portfolio company, content may be in Portfolio Interaction Notes)
-- id=39: Arali Ventures - blank page

-- Test pages (skipped):
-- id=16: [TEST] Explicit Parent
-- id=17: [TEST] Migration
-- id=18: [TEST] Migration
-- id=19: [TEST] Visual Check v2

-- Verification query:
-- SELECT id, name, page_content_path FROM companies WHERE page_content_path IS NOT NULL ORDER BY name;

-- Stats from first 30 companies processed:
-- Total fetched: 30 (excluding 4 test pages)
-- Pages with content (saved): 21
-- Blank/empty pages (skipped): 9
-- Content breakdown:
--   Rich (extensive notes): 5 pages
--   Notes (some content): 5 pages
--   Template only (scaffolding): 11 pages
--
-- NOTE: Only 30 of ~545 companies have been processed in this batch.
-- Remaining companies (IDs 43-104 from first SQL query, plus IDs 105+)
-- need to be fetched and processed in subsequent runs.
