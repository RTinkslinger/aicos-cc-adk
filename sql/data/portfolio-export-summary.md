# Portfolio DB - Notion Export Summary

**Export Date:** 2026-03-20 02:20
**Total Companies:** 142
**Source:** Notion Portfolio DB (data_source_id: `4dba9b7f-e623-41a5-9cb7-2af5976280ee`)
**Export File:** `sql/data/portfolio-notion-export.json` (243,640 bytes)

## Completeness Note
The Notion API returns max 100 rows per view query. Multiple views were queried to 
collect all rows. 21 views were queried, yielding 142 unique companies. Some views 
still reported `has_more=true` at the 100 row limit, so there may be additional rows 
in the database that were not captured. The actual database may have slightly more entries.

## Sample Rows (first 3)

### 1. Alter AI
- **Page ID:** `26029bcc-b6fc-8118-82a2-f3c44fb1a49d`
- **Notion URL:** https://www.notion.so/26029bccb6fc811882a2f3c44fb1a49d
- **Today:** Funnel
- **UW Decision:** Core Cheque
- **Health:** Yellow
- **Entry Cheque:** 100000
- **Ownership %:** 0.0067
- **Investment Timeline:** Q3 2025
- **AIF/USA:** USA
- **Check-In Cadence:** Quarterly
- **Stage @ entry:** early product
- **Last Round Valuation:** 15000000
- **Entry Round Valuation:** 15000000
- **Follow-on Work Priority:** ['P1']

### 2. Ambak
- **Page ID:** `1308ff1c-5dac-449b-a4ba-a26c02907b3b`
- **Notion URL:** https://www.notion.so/1308ff1c5dac449ba4baa26c02907b3b
- **Today:** Fund Priority
- **UW Decision:** Core Cheque
- **Health:** Green
- **Entry Cheque:** 45000
- **Ownership %:** 0.023399999999999997
- **Investment Timeline:** Q1 2024
- **Current Stage:** early revenue
- **AIF/USA:** AIF
- **HC Priority:** P0🔥
- **Check-In Cadence:** Monthly
- **Stage @ entry:** scaling revenue
- **Last Round Valuation:** 30000000
- **Entry Round Valuation:** 12200000
- **Follow-on Work Priority:** ['NA']

### 3. Ananant Systems
- **Page ID:** `12229bcc-b6fc-80e1-a546-fd05d2a089d7`
- **Notion URL:** https://www.notion.so/12229bccb6fc80e1a546fd05d2a089d7
- **Today:** NA
- **UW Decision:** Community Pool
- **Health:** Green
- **Entry Cheque:** 40000
- **Ownership %:** 0.0034999999999999996
- **Investment Timeline:** Q3 2024
- **Current Stage:** pre-product
- **AIF/USA:** AIF
- **HC Priority:** NA
- **Check-In Cadence:** Monthly
- **Stage @ entry:** pre-product
- **Last Round Valuation:** 11000000
- **Entry Round Valuation:** 11000000
- **Follow-on Work Priority:** ['NA']

## Column Coverage

| Field | Count | Coverage | Type |
|-------|-------|----------|------|
| $500K candidate? | 109/142 | 🟢 77% | str |
| AIF/USA | 130/142 | 🟢 92% | str |
| BU Follow-On Tag | 123/142 | 🟢 87% | str |
| BU Reserve Defend | 36/142 | 🟡 25% | int |
| BU Reserve No Defend | 31/142 | 🔴 22% | int |
| Best case outcome | 96/142 | 🟡 68% | int |
| Cash In Bank | 1/142 | 🔴 1% | int |
| Check-In Cadence | 131/142 | 🟢 92% | str |
| Company Name | 142/142 | 🟢 100% | list |
| Current Stage | 104/142 | 🟡 73% | str |
| Deep Dive | 84/142 | 🟡 59% | str |
| Dilution IF Defend | 38/142 | 🟡 27% | float |
| Dilution IF NO Defend | 38/142 | 🟡 27% | float |
| EF/EO | 98/142 | 🟡 69% | str |
| Earmarked Reserves | 4/142 | 🔴 3% | int |
| Entry Cheque | 140/142 | 🟢 99% | int |
| Entry Round Raise | 77/142 | 🟡 54% | int |
| Entry Round Valuation | 133/142 | 🟢 94% | int |
| External Signal | 2/142 | 🔴 1% | str |
| FMV Carried | 92/142 | 🟡 65% | float |
| FY23-24 Compliance | 29/142 | 🔴 20% | list |
| Follow On Decision | 19/142 | 🔴 13% | str |
| Follow On Outcome | 29/142 | 🔴 20% | list |
| Follow-on Decision | 2/142 | 🔴 1% | str |
| Follow-on Work Priority | 140/142 | 🟢 99% | list |
| Fresh Committed  | 0/142 | 🔴 0% | int |
| Good Case outcome | 38/142 | 🟡 27% | int |
| HC Priority | 113/142 | 🟢 80% | str |
| Health | 141/142 | 🟢 99% | str |
| High Impact | 21/142 | 🔴 15% | str |
| IP Assigned | 74/142 | 🟡 52% | list |
| IP Pull | 110/142 | 🟢 77% | str |
| Introduced to? | 1/142 | 🔴 1% | list |
| Investment Timeline | 139/142 | 🟢 98% | str |
| Key Questions | 14/142 | 🔴 10% | str |
| Last Round Valuation | 130/142 | 🟢 92% | int |
| Last updated | 142/142 | 🟢 100% | str |
| Led by? | 70/142 | 🟡 49% | list |
| Likely Follow On Decision? | 4/142 | 🔴 3% | str |
| Likely Outcome | 3/142 | 🔴 2% | int |
| MD Assigned | 124/142 | 🟢 87% | list |
| Meeting Notes | 1/142 | 🔴 1% | list |
| Next 3 months IC Candidate | 19/142 | 🔴 13% | str |
| Next Round Status | 29/142 | 🔴 20% | list |
| Note on deployment | 31/142 | 🔴 22% | str |
| Ops Prio | 96/142 | 🟡 68% | str |
| Outcome Category | 97/142 | 🟡 68% | str |
| Ownership % | 141/142 | 🟢 99% | float |
| PStatus | 108/142 | 🟢 76% | list |
| Participation Attribution | 35/142 | 🔴 25% | list |
| Portfolio Co | 142/142 | 🟢 100% | str |
| Raised Follow-on funding? | 33/142 | 🔴 23% | str |
| Referenceability  | 109/142 | 🟢 77% | str |
| Reserve Committed | 2/142 | 🔴 1% | int |
| Reserve Deployed | 14/142 | 🔴 10% | int |
| Revenue Generating | 100/142 | 🟡 70% | str |
| Room to deploy? | 25/142 | 🔴 18% | int |
| Round 1 Type | 69/142 | 🟡 49% | str |
| Round 2 Raise | 7/142 | 🔴 5% | int |
| Round 2 Type | 6/142 | 🔴 4% | str |
| Round 2 Val | 6/142 | 🔴 4% | int |
| Round 3 Raise | 1/142 | 🔴 1% | int |
| Round 3 Type | 1/142 | 🔴 1% | str |
| Round 3 Val | 1/142 | 🔴 1% | int |
| Scale of Business | 81/142 | 🟡 57% | str |
| Sourcing Attribution | 59/142 | 🟡 42% | list |
| Spikey | 98/142 | 🟡 69% | str |
| Stage @ entry | 131/142 | 🟢 92% | str |
| Tier 1 and Marquee seed cap table | 56/142 | 🟡 39% | str |
| Timing of Involvement? | 27/142 | 🔴 19% | list |
| Today | 142/142 | 🟢 100% | str |
| UW Decision | 142/142 | 🟢 100% | str |
| Venture Partner? (old) | 12/142 | 🔴 8% | list |
| date:Action Due Date:is_datetime | 0/142 | 🔴 0% | int |
| date:Action Due Date:start | 9/142 | 🔴 6% | str |
| date:Fumes Date:is_datetime | 0/142 | 🔴 0% | int |
| date:Fumes Date:start | 1/142 | 🔴 1% | str |

## Data Quality Notes
- Some company names have trailing spaces (e.g., "Autosana ", "Stellon Labs ")
- `<omitted />` values indicate Notion truncated rich content (relations, rollups, people fields)
- Formula fields (`formulaResult://...`) were excluded from export - these are computed values
- Rollup fields (Angels, etc.) were omitted by Notion API
- Some fields appear under variant names: `Follow On Decision` vs `Follow-on Decision`
- `date:Action Due Date:is_datetime` is always 0 (dates only, no datetimes)
- `Cash In Bank`, `External Signal`, `Fresh Committed` have near-zero coverage (<2%)

## All Company Names (142)

| # | Company | Page ID | Key Status |
|---|---------|---------|------------|
| 1 | Alter AI | `26029bcc-b6f...` | Funnel / Yellow |
| 2 | Ambak | `1308ff1c-5da...` | Fund Priority / Green |
| 3 | Ananant Systems | `12229bcc-b6f...` | NA / Green |
| 4 | Answers.ai | `6001400f-01a...` | Exited / Green |
| 5 | Apptile | `12229bcc-b6f...` | Fund Priority / Yellow |
| 6 | AskMyGuru | `1ce29bcc-b6f...` | Funnel / Green |
| 7 | Atica | `4a47b00b-278...` | Fund Priority / Green |
| 8 | AuraML | `12629bcc-b6f...` | Funnel / Green |
| 9 | Aurva | `b0a4183f-b7c...` | NA / Green |
| 10 | Autosana | `26629bcc-b6f...` | Funnel / Green |
| 11 | Ballisto AgriTech (f.k.a. Orbit Farming) | `f89bbf3c-e64...` | Fund Priority / Green |
| 12 | BetterPlace fka Mindforest | `5773f60a-772...` | Deadpool / Red |
| 13 | Bidso | `a82f579b-874...` | Exited / Yellow |
| 14 | BiteSpeed | `12329bcc-b6f...` | NA / Red |
| 15 | Blockfenders | `12329bcc-b6f...` | Deadpool / NA |
| 16 | Boba Bhai | `c5505a57-4c7...` | Fund Priority / Green |
| 17 | Boost Robotics | `27229bcc-b6f...` | Funnel / Green |
| 18 | Boxpay | `9f90d24e-395...` | Deadpool / Red |
| 19 | Caddy | `2cf29bcc-b6f...` | Funnel / ? |
| 20 | CarbonStrong | `f6b45fd6-6e2...` | NA / Red |
| 21 | Cleevo | `f287330e-570...` | NA / Yellow |
| 22 | cocreate | `27a29bcc-b6f...` | Funnel / Green |
| 23 | CodeAnt | `20f33412-988...` | Fund Priority / Green |
| 24 | Coffeee | `1712226b-ac4...` | NA / Red |
| 25 | Coind | `12329bcc-b6f...` | Deadpool / NA |
| 26 | Confido Health | `12329bcc-b6f...` | Fund Priority / Green |
| 27 | Crackle | `39bd0bab-2f7...` | Funnel / Green |
| 28 | Crest | `12629bcc-b6f...` | Fund Priority / Green |
| 29 | Cybrilla | `f6d99105-85d...` | Fund Priority / Green |
| 30 | Digital Paani | `12329bcc-b6f...` | Deadpool / Yellow |
| 31 | Dodo Payments | `25329bcc-b6f...` | Fund Priority / Green |
| 32 | DreamSleep | `12229bcc-b6f...` | Funnel / Green |
| 33 | Eight Networks | `12729bcc-b6f...` | Capital Return / Green |
| 34 | ElecTrade | `66d85260-718...` | Deadpool / Red |
| 35 | Emomee | `ecc0d0b4-92f...` | NA / Red |
| 36 | ExtraaEdge | `1eb29bcc-b6f...` | NA / Green |
| 37 | Fabriclore | `12229bcc-b6f...` | NA / Green |
| 38 | Felicity | `d9ac844c-5d9...` | Fund Priority / Green |
| 39 | Finsire | `a400347a-c7a...` | Deadpool / Yellow |
| 40 | Fliq (f.k.a. EthosX) | `d9900730-583...` | NA / Yellow |
| 41 | Flytbase | `5d70607f-849...` | NA / Yellow |
| 42 | Fondant | `5639e0c9-dcc...` | Funnel / Yellow |
| 43 | Frizzle | `26629bcc-b6f...` | Funnel / Yellow |
| 44 | GameRamp | `1b429bcc-b6f...` | Fund Priority / Green |
| 45 | Gimi Michi | `2a229bcc-b6f...` | Funnel / Green |
| 46 | GlamPlus | `12229bcc-b6f...` | Deadpool / Yellow |
| 47 | Gloroots | `11229bcc-b6f...` | NA / Red |
| 48 | GoCredit (f.k.a. UniPe) | `97379569-785...` | Deadpool / Red |
| 49 | Grexa | `1b429bcc-b6f...` | NA / Green |
| 50 | Grvt | `66ef4d63-b1c...` | Fund Priority / Green |
| 51 | HealthCred | `c11fe2b3-3e0...` | Capital Return / Red |
| 52 | Hexo AI | `27229bcc-b6f...` | Funnel / Green |
| 53 | Highperformr AI | `12329bcc-b6f...` | Fund Priority / Green |
| 54 | Hotelzify | `12d29bcc-b6f...` | NA / Yellow |
| 55 | iBind Systems | `f62ee6d9-27c...` | Deadpool / Red |
| 56 | Inspecity | `c1b1f6e6-9ae...` | Fund Priority / Green |
| 57 | Insta Astro | `10429bcc-b6f...` | NA / Green |
| 58 | Intract | `28b7bb8e-509...` | NA / Green |
| 59 | Isler | `12d29bcc-b6f...` | Fund Priority / Green |
| 60 | Kairos Computer | `24829bcc-b6f...` | Funnel / Yellow |
| 61 | Kavana AI (Two Four Labs) | `2be29bcc-b6f...` | Funnel / Green |
| 62 | Kilrr | `12229bcc-b6f...` | NA / Green |
| 63 | Kintsugi | `da519cf8-2ef...` | Fund Priority / Green |
| 64 | Klaar | `7721ca28-cd2...` | NA / Yellow |
| 65 | Klaire | `2cc29bcc-b6f...` | Funnel / Green |
| 66 | Kreo | `a4f426ab-176...` | NA / Green |
| 67 | Kubesense (Tyke) | `988c9617-6cd...` | NA / Yellow |
| 68 | Lane | `31929bcc-b6f...` | Funnel / Green |
| 69 | Legend of Toys | `12d29bcc-b6f...` | Fund Priority / Green |
| 70 | Lucio AI | `27229bcc-b6f...` | Funnel / Green |
| 71 | Mantys | `2227425b-073...` | NA / Red |
| 72 | Manufacture AI | `20d29bcc-b6f...` | Deadpool / Red |
| 73 | Marrfa | `f8c6772e-193...` | NA / Green |
| 74 | Material Depot | `12629bcc-b6f...` | Fund Priority / Green |
| 75 | Measure AI | `85a0698b-4e1...` | Funnel / Yellow |
| 76 | Mello | `2b929bcc-b6f...` | Funnel / Green |
| 77 | MiniMines | `12029bcc-b6f...` | NA / Yellow |
| 78 | Modus Secure | `24829bcc-b6f...` | Funnel / Green |
| 79 | Mom’s Made | `1ce29bcc-b6f...` | NA / Green |
| 80 | Morphing Machines | `11c29bcc-b6f...` | Fund Priority / Green |
| 81 | Multiwoven | `4ef63022-7b6...` | Exited / NA |
| 82 | Navo (f.k.a. BizUp) | `44ffdcac-c82...` | NA / Red |
| 83 | Nimo Planet | `29629bcc-b6f...` | Funnel / Green |
| 84 | Nixo | `26629bcc-b6f...` | Funnel / Green |
| 85 | NuPort | `12729bcc-b6f...` | NA / Yellow |
| 86 | Obvious Finance | `12329bcc-b6f...` | Deadpool / NA |
| 87 | Offline | `11529bcc-b6f...` | NA / Green |
| 88 | ofScale | `d09d797d-594...` | Deadpool / Red |
| 89 | OhSoGo | `0d5d7791-401...` | Deadpool / NA |
| 90 | OnCare | `10729bcc-b6f...` | NA / Yellow |
| 91 | One Impression | `12029bcc-b6f...` | NA / Green |
| 92 | Orange Slice | `28729bcc-b6f...` | Fund Priority / Green |
| 93 | Pinegap | `12229bcc-b6f...` | NA / Green |
| 94 | Polytrade | `12129bcc-b6f...` | NA / Green |
| 95 | Potpie | `28f29bcc-b6f...` | Funnel / Green |
| 96 | PowerEdge | `1b429bcc-b6f...` | Capital Return / Red |
| 97 | PowerUp | `1b429bcc-b6f...` | Fund Priority / Green |
| 98 | Prosparity | `7d861f3a-904...` | Funnel / Yellow |
| 99 | Puch AI (f.k.a. TurboML) | `a42bc4dd-7fd...` | Exited / Red |
| 100 | Quash Bugs | `12229bcc-b6f...` | Funnel / Yellow |
| 101 | Quivly | `29629bcc-b6f...` | Funnel / Green |
| 102 | Qwik Build (f.k.a Snowmountain) | `7e5a3d3e-4ec...` | Funnel / Yellow |
| 103 | Rakshan AI | `2ab29bcc-b6f...` | Funnel / Green |
| 104 | RapidClaims | `19e3f345-32c...` | Fund Priority / Green |
| 105 | Realfast | `12129bcc-b6f...` | Fund Priority / Green |
| 106 | Renderwolf | `3cbe6275-5db...` | NA / Yellow |
| 107 | ReplyAll (f.k.a. PRBT) | `1ce29bcc-b6f...` | Funnel / Green |
| 108 | Revenoid | `25429bcc-b6f...` | Funnel / Yellow |
| 109 | Revspot | `12729bcc-b6f...` | NA / Green |
| 110 | Rhym | `12029bcc-b6f...` | Exited / NA |
| 111 | Riverline (f.k.a Recontact) | `1cb29bcc-b6f...` | Funnel / Yellow |
| 112 | SalesChat | `719b834c-df4...` | NA / Yellow |
| 113 | Seeds Finance | `e035403f-248...` | NA / Green |
| 114 | Skydda | `21429bcc-b6f...` | Fund Priority / Green |
| 115 | Smallest AI | `1ce29bcc-b6f...` | Fund Priority / Green |
| 116 | Solar Ladder | `985d62b5-f58...` | NA / Green |
| 117 | Soulside | `32729bcc-b6f...` | Funnel / Green |
| 118 | Spheron Network | `12329bcc-b6f...` | NA / Green |
| 119 | Spybird | `12029bcc-b6f...` | NA / Yellow |
| 120 | Spydra | `3661da3d-6d1...` | NA / Yellow |
| 121 | Stance Health (f.k.a HealthFlex) | `ab1fb93c-99c...` | Fund Priority / Yellow |
| 122 | Stellon Labs | `29629bcc-b6f...` | Fund Priority / Green |
| 123 | Step Security | `4630d9ea-c05...` | Fund Priority / Green |
| 124 | Stupa Sports Analytics | `10e29bcc-b6f...` | NA / Yellow |
| 125 | Supernova | `12329bcc-b6f...` | NA / Green |
| 126 | SuprSend | `41015c80-14a...` | NA / Yellow |
| 127 | Tejas (f.k.a Patcorn) | `12629bcc-b6f...` | Funnel / Green |
| 128 | Terafac | `12729bcc-b6f...` | Fund Priority / Green |
| 129 | Terra | `6ae68b20-1ae...` | NA / Yellow |
| 130 | Terractive | `11829bcc-b6f...` | Fund Priority / Green |
| 131 | Tesora AI | `26629bcc-b6f...` | Fund Priority / Green |
| 132 | Tractor Factory | `12229bcc-b6f...` | NA / Green |
| 133 | Turnover | `7b1b8f76-24a...` | NA / Yellow |
| 134 | UGX | `1f729bcc-b6f...` | Funnel / Green |
| 135 | Unifize | `5c26ae03-837...` | Fund Priority / Green |
| 136 | Uravu Labs | `6b39dc87-827...` | NA / Green |
| 137 | VoiceBit | `2fc29bcc-b6f...` | Funnel / Green |
| 138 | VyomIC (f.k.a. AeroDome) | `1f729bcc-b6f...` | Funnel / Green |
| 139 | Workatoms | `2b829bcc-b6f...` | Funnel / Green |
| 140 | YOYO AI (fka Trimpixel) | `b64eb195-676...` | NA / Red |
| 141 | Ziffi Chess | `21cff989-837...` | Fund Priority / Green |
| 142 | ZuAI | `12229bcc-b6f...` | NA / Green |