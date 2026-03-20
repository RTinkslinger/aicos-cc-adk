# Data Fix 2: M2 Loop 4 Cleanup
**Date:** 2026-03-20
**Database:** Supabase `llfkxnsfczludgigknbs`

## Fix 1: "Terra" Portfolio Orphan -- NOT AN ORPHAN

Investigation found portfolio row `id=150, portfolio_co="Terra"` has `company_name_id=7f0162b4-1f0f-4501-9ea9-dcd1d0d3f56e` which maps to `companies.id=477` ("Terra.do") via `notion_page_id`. Cross-ref query confirmed **zero portfolio orphans** -- all 142/142 portfolio rows match a company row.

**Action:** None needed.

## Fix 2: "Founder 2" Placeholders -- DELETED

Found 6 junk placeholder records in `network` table:
- IDs: 3202, 3224, 3633, 3215, 3672, 3560
- All had `person_name = 'Founder 2'`, `current_role = 'postgres'`

**Action:** Deleted all 6 rows. Network count: 3728 -> 3722.

## Fix 3: Unmatched Page Content Files -- ALL 59 MATCHED

Previous matching used slug matching that missed 59 files with special characters (apostrophes, ampersands, f.k.a. suffixes, accented chars, dots in names, URL fragments).

**Root cause:** Slugification didn't handle:
- Possessives (`'s` -> `s`): "Abhinav Sharma's new company" -> `abhinav-sharmas-new-company.md`
- f.k.a. patterns: "Dodge AI (f.k.a. Interface AI)" -> `dodge-ai-fka-interface-ai.md`
- Dots in names: "Base14.io" -> `base14io.md`, "Terra.do" -> `terrado.md`
- Ampersands: "Devang & Saurav's company" -> `devang-sauravs-company.md`
- URL fragments: "Faff (" -> `faff-https-wwwtryfaffcom.md`
- R&D notation: "Samsung R&D Institute India" -> `samsung-rd-institute-india.md`
- Renamed companies: "Snowmountain AI" -> `qwik-build-fka-snowmountain.md`

**Action:** Updated `page_content_path` for all 59 companies via 3 batch UPDATE statements (20 + 22 + 17 rows).

Companies matched: 467 -> 526 (all files on disk now have a DB match).

### Full mapping applied:

| Company ID | Company Name | File |
|-----------|-------------|------|
| 20 | Abhinav Sharma's new company | abhinav-sharmas-new-company.md |
| 21 | Abhishek Kona's company | abhishek-konas-company.md |
| 24 | Aditya's VC Fund | adityas-vc-fund.md |
| 30 | Alben D Souza's company | alben-d-souzas-company.md |
| 40 | Arjun Juneja's company | arjun-junejas-company.md |
| 42 | Arya Pathak's company (NA) | arya-pathaks-company-na.md |
| 55 | Base14.io | base14io.md |
| 59 | BillMe Founder's new co | billme-founders-new-co.md |
| 87 | Chandramauli Singh's company | chandramauli-singhs-company.md |
| 120 | Dataflos (f.k.a. Blockfenders) | dataflos-fka-blockfenders.md |
| 122 | Deepak's new company | deepaks-new-company.md |
| 124 | Devang & Saurav's company | devang-sauravs-company.md |
| 128 | Dodge AI (f.k.a. Interface AI) | dodge-ai-fka-interface-ai.md |
| 131 | DreamSpan (f.k.a. DreamSleep) | dreamspan-fka-dreamsleep.md |
| 132 | Drizz.Dev | drizzdev.md |
| 139 | ElecTrade (f.k.a. Hatch N Hack) | electrade-fka-hatch-n-hack.md |
| 151 | Faff ( | faff-https-wwwtryfaffcom.md |
| 159 | Fliq (f.k.a. EthosX) | fliq-fka-ethosx.md |
| 175 | Gobi's company | gobis-company.md |
| 188 | Harshit Madan's new company | harshit-madans-new-company.md |
| 216 | Jaydeep's new company | jaydeeps-new-company.md |
| 221 | K V Ketan's new company | k-v-ketans-new-company.md |
| 225 | kashif's new company | kashifs-new-company.md |
| 256 | Manav (Suvonil Chatterjee's company) | manav-suvonil-chatterjees-company.md |
| 284 | Mom's Made | moms-made.md |
| 301 | Nidhi's company | nidhis-company.md |
| 333 | Pallav Singh's new company | pallav-singhs-new-company.md |
| 340 | PeakXV (f.k.a Sequoia Capital India) | peakxv-fka-sequoia-capital-india.md |
| 358 | Prabhkiran's new company | prabhkirans-new-company.md |
| 359 | Pranay's new company | pranays-new-company.md |
| 373 | Puch AI (f.k.a. TurboML) | puch-ai-fka-turboml.md |
| 383 | Rahul Tarak's Company | rahul-taraks-company.md |
| 385 | Ram J's new company | ram-js-new-company.md |
| 389 | Ravesh's company | raveshs-company.md |
| 390 | Realiti.io | realitiio.md |
| 391 | Recrew AI (f.k.a. Gloroots) | recrew-ai-fka-gloroots.md |
| 397 | Returns (f.k.a. Optionbase) | returns-fka-optionbase.md |
| 399 | Revspot.AI | revspotai.md |
| 404 | Rilo (f.k.a. Workatoms) | rilo-fka-workatoms.md |
| 406 | Riverline (f.k.a Recontact) | riverline-fka-recontact.md |
| 411 | Roy's VC Fund | roys-vc-fund.md |
| 417 | Sai Alisetty's company | sai-alisettys-company.md |
| 420 | Samsung R&D Institute India | samsung-rd-institute-india.md |
| 421 | Sandeep R's new co | sandeep-rs-new-co.md |
| 422 | Satish & Dhawal's company | satish-dhawals-company.md |
| 423 | Satish's VC Fund | satishs-vc-fund.md |
| 435 | Sheta Mittal's company | sheta-mittals-company.md |
| 451 | Sriram's company | srirams-company.md |
| 454 | Stance Health (f.k.a. HealthFlex) | stance-health-fka-healthflex.md |
| 464 | Supercharge.vc | superchargevc.md |
| 477 | Terra.do | terrado.md |
| 483 | Thariq's new company | thariqs-new-company.md |
| 498 | UC Berkeley M.E.T. program | uc-berkeley-management-entrepreneurship-technology-met-program.md |
| 505 | Vaibhav Jain's company | vaibhav-jains-company.md |
| 526 | Xook.ai | xookai.md |
| 531 | Z47 (f.k.a. Matrix Partners India) | z47-fka-matrix-partners-india.md |
| 597 | Kubesense (f.k.a Tyke) | kubesense-tyke.md |
| 601 | Snowmountain AI | qwik-build-fka-snowmountain.md |
| 604 | StepSecurity | step-security.md |

## Fix 4: Final Stats

| Table | Total Rows | Has page_content_path | Has embedding |
|-------|-----------|----------------------|---------------|
| companies | 4,565 | 526 | 4,565 |
| network | 3,722 (-6) | 30 | 3,722 |
| portfolio | 142 | 142 | 142 |

**Portfolio cross-ref:** 142/142 matched to companies (100%).

**Companies page coverage:** 526/4,565 (11.5%) have page content files. All 526 files on disk are now matched. Zero unmatched files remain.

## Remaining Gaps (for Datum Agent)
- 4,039 companies without page content (expected -- only tracked companies get pages)
- 3,692 network entries without page content
- Website backfill, last_interaction enrichment deferred to Datum Agent
