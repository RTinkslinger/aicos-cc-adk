# Continuous Enrichment Completion Report — 2026-03-20

## Summary

Ran 3 enrichment loops across all 3 tables (companies, network, portfolio) to find and fix cross-table gaps. The enrichment focused on stitching founders to companies and portfolio entries.

## Table Counts

| Table | Start | End | Delta |
|-------|-------|-----|-------|
| Companies | 545 | 558 | +13 (10 created for missing portfolio companies, 3 from concurrent sync) |
| Network | 725 | 959 | +234 (197 parallel_enrichment + 195 research_extraction from concurrent process + notion_sync) |
| Portfolio | 142 | 142 | 0 |

## Check Results

### Check 1: Founders from Research Files
- Read 30+ portfolio research files to extract founder names
- Cross-referenced all 197 parallel enrichment founders against research files via grep
- Matched and linked **130 founders** to their respective companies

### Check 2: Companies Without Network Connections
- **162 companies** initially without `current_people_ids`
- **142 remain** — these are VCs (3one4 Capital, Axilor, Celesta Capital), schools (Delhi Public School, Dublin High School), large corps (Capital One, Clubhouse), and test entries. Not portfolio companies, so expected to lack people links.
- Only 2 were portfolio companies (Turnover, Rhym) — Rhym now has founders linked via enrichment

### Check 3: Portfolio Companies Without Founders (led_by_ids)
- **47 -> 10** (37 linked)
- Method: Joined portfolio.company_name_id to companies.current_people_ids, propagated to led_by_ids
- Created Intract company entry and linked Abhishek Anita (the only one with a Notion page ID)
- **10 remain**: Kubesense, MiniMines, One Impression, Polytrade, Qwik Build, Rhym, Smallest AI, Spheron Network, Step Security, YOYO AI — these companies have founders in the network table but founders lack Notion page IDs so can't be stored in `led_by_ids` (TEXT[] of Notion UUIDs)

### Check 4: Network People Without Company Links
- Started: 0 with NULL, 223 with empty array `{}`
- **130 parallel enrichment founders linked** to companies via research file matching
- **67 remain unlinked** — these are people mentioned in research files as competitors, partners, or referenced entities (not portfolio founders). E.g., Do Kwon (Terraform Labs), Josh Felser, Aviv Eyal.

### Check 5: Parallel Enrichment Founders Needing Links
- **197 total** parallel enrichment founders existed with empty `current_company_ids`
- **130 linked** (66% completion rate) via research file -> portfolio -> company mapping
- **67 remain** — can't be matched without additional metadata (no source_file field preserved during enrichment)

### Check 6: Missing Embeddings
- **0** missing across all 3 tables (concurrent process handling new entries)

### Check 7: Action Scores
- Refreshed 3 times during the enrichment process

## Companies Created
10 companies were created in the companies table for portfolio entries that had `company_name_id` UUIDs but no matching company record:

| Company | notion_page_id |
|---------|---------------|
| Intract | bf871c87-8593-4a5b-b654-3c5613300f1e |
| Kubesense (Tyke) | 96fb279e-9ba7-4b76-a005-e5f5a0412bbf |
| MiniMines | b027873d-7182-4be2-a7f7-bc740c9aa15c |
| One Impression | 3cb08975-692f-4592-90de-32f55edc32c4 |
| Polytrade | 6d6b5ac6-842b-467f-bfd3-a41f07381847 |
| Qwik Build (f.k.a Snowmountain) | 7e086baf-e130-4405-84cb-d8f531bcba14 |
| Smallest AI | feaeb55a-f08e-4ea0-8042-9d4485e1f57d |
| Spheron Network | c0137edc-bec2-40ae-a514-b06ffea06dc3 |
| Step Security | bc506ab0-f5f8-43da-96c5-bc80ae078a8c |
| YOYO AI (fka Trimpixel) | 328be182-566f-43b8-9461-7c9619fbf4f7 |

## Founder-Company Links Created (130 total)

Key linkages by company:
- **Ambak**: Pranav Khattar, Ashish Lohia
- **Aurva**: Akash Mandal
- **Ballisto/Orbit Farming**: Aishwarya Ramakrishnan
- **Terafac**: Amrit Singh, Anubhi Khandelwal
- **StepSecurity**: Varun Sharma, Ashish Kurmi
- **Smallest AI**: Sudarshan Kamath, Akshat Mandloi
- **Legend of Toys**: Afshaan Siddiqui, Vinay Jaisingh
- **Unifize**: Ben Merton, Avinash Sultanpur, Lakshman Thatai
- **Inspecity**: Arindrajit Chowdhury, Dr. Tausif Shaikh
- **Isler**: Chirag Kakkar, Mudit Mishra
- **Highperformr AI**: Srivatsan Venkatesan, Ramesh Ravishankar
- **Stance Health**: Rohit Arora, Ninad Karandikar
- **Terractive**: Raena Ambani, Rahee Ambani Choksi
- **Solar Ladder**: Manan Mehta
- **Orange Slice**: Kishan Sripada
- **BiteSpeed**: Siddharth Barpanda
- **Potpie**: Aditi Kothari, Dhiren Mathur
- **OnCare**: Amar Sneh
- **Pinegap**: Ankit Varmani, Deepak Sharma
- **ZuAI**: Anubhav Mishra, Arpit Jain
- **Riverline**: Ankit Sanghvi, Jayanth Krishnaprakash
- **MiniMines**: Anupam Kumar
- **Quivly**: Chandrika Maheshwari
- **Revspot**: Darshan Subash, Chirag Wadhera
- **Spydra**: Ashwath Govindan, Manish Tewari
- **Morphing Machines**: Deepak Shapeti, Ranjani Narayan, S.K. Nandy
- **KubeSense**: Venkatesh Radhakrishnan, Guru prasad G
- **SuprSend**: Nikita Navral, Gaurav Verma
- **Measure AI**: Gokula Krishnan Ramachandran
- **RapidClaims**: Dushyant Mishra, Jot Sarup Singh
- **Uravu Labs**: Swapnil Shrivastav, Venkatesh RY, Govinda Balaji
- **Rhym**: Ekta Singh, Gaurav Wadhwani, Gaurav Toora
- **Stellon Labs**: Divam Gupta, Rohan Joshi
- **SalesChat**: Hardik Bavishi
- **Kintsugi**: Jeff Gibson, Pujun Bhatnagar
- **VoiceBit**: Hitesh Kenjale, Jay Patel, Lovre Soric
- **One Impression**: Apaksh Gupta, Jivesh Gupta
- **Kreo**: Ishan Sukul, Himanshu Gupta
- **Navo**: Anshul Singhal, Suparn Goel
- **Coffeee**: Amit Veer, Neha Sharma
- **Prosparity**: Anirudh Dhakar, Saurabh Khodke
- **Crest**: Rahul Vishwakarma, Yogesh Byahatti
- **Gloroots/Recrew**: Mayank Bhutoria, Yamini Jain
- **Finsire**: Subramaniam Chintamani
- **GlamPlus**: Rohan Singh
- **Grexa**: Narendra Agrawal, Arpit Oswal
- **iBind Systems**: Santu Maity, Sanat Bhat
- **Hexo AI**: Kunal Bhatia, Vignesh Baskaran
- **Hotelzify**: Anirudh Ganesh
- **Insta Astro**: Nitin Verma
- **Kairos Computer**: Manas Bam
- **Fliq/EthosX**: Surbhi Singh
- **Klaar**: Sharthok Chakraborty
- **Lane**: Samiksha Agarwal
- **Kavana AI**: Shubham Ratrey
- **Mom's Made**: Sameer Kumar
- **Tejas**: Saijal Rekhani, Sailesh Rekhani
- **Multiwoven**: Subin T P
- **ofScale**: Suvigna Shour, Tarun Kedia
- **Modus Secure**: Somesh Lund, Sunit Gautam
- **Puch AI**: Siddharth Bhatia
- **PowerEdge**: Spencer Bartsch
- **Realfast**: Sidu Ponnappa
- **Nixo**: Priya Khandelwal
- **Nimo Planet**: Rohildev Nattukallingal
- **Material Depot**: Manish Reddy, Sarthak Agrawal
- **Polytrade**: Piyush Gupta
- **QwikBuild**: Pradeep Ayyagari, Nilesh Trivedi
- **Tesora AI**: Vivek Rao
- **YOYO AI**: Nikhil Pandey

## Irreducible Gaps (Structural Limitations)

1. **10 portfolio without led_by_ids**: Founders exist in network but as Postgres-only records (no notion_page_id). The `led_by_ids` field requires Notion UUIDs. Fix requires either: (a) creating Notion entries for these people, or (b) adding a `pg_led_by_ids` integer array column referencing network.id.

2. **67 enrichment founders without company links**: Created during parallel enrichment without source_file metadata. Can't determine which company they belong to. Fix requires: re-running the enrichment with `enrichment_metadata` capturing `{source_company: "..."}`.

3. **142 companies without people**: Expected — these are VCs, schools, corporates, and non-portfolio entities from Notion's Companies DB.

## Concurrent Activity Noted
During this enrichment run, another process (source: `research_extraction_2026-03-20`) was actively inserting ~195 new network entries and generating embeddings. The final counts reflect both this enrichment and the concurrent process.
