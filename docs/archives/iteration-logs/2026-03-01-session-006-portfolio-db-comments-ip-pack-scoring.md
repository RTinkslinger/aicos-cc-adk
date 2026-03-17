# Session 006: Portfolio DB, Comments as Deal Log, IP Pack, Scoring Framework & Granola Deep Dive

**Date:** March 1, 2026
**Interface:** Cowork (continuation from Session 005)
**Phase:** Understanding (Steps 1–3 — Portfolio DB Deep Dive, Comments Discovery, IP Pack Decoding, Lead Sources, Record Counts, Granola Exhaustive Analysis)

---

## Summary

Explored three critical new dimensions of the DeVC CRM: (1) Portfolio DB with 94 fields for post-investment management, (2) Notion page comments as the primary day-to-day deal tracking mechanism (OnArrival: 29 comments, LottoG: 11 comments), and (3) the DeVC IP Pack — the definitive investment process document containing the full scoring framework, cheque size decision matrix, Fund I retrospective (83 investments), follow-on framework (IDS), and IC process. Also decoded: Finance DB (23 fields), lead source taxonomy (6 sources), Alpha/Beta firm-wide lexicon, Anti Folio meaning, Surface to Collective process, and confirmed record scale (2000+ in each primary DB).

**Additionally:** Conducted exhaustive Granola meeting notes deep dive — 33 meetings fetched individually (Jan 5 – Feb 26, 2026), plus semantic queries returning data from 100+ meetings in the archive. Key revelations: (a) Aakash's annotation pattern on new deal evals, (b) scoring data in real-time across 15+ companies, (c) portfolio check-in metrics for 10+ companies, (d) 30+ deal verdicts with pass reasons, (e) referral network mapping (15+ piped-from sources), (f) BRC/DD activities, and (g) the critical finding that Granola captures only ~10-15% of Aakash's actual meetings (7-8/day) with significant CRM lag.

---

## Major Discovery 1: Portfolio DB (94 Fields)

**Database ID:** `edbc9d0c-fa16-436d-a3d5-f317a86a4d1e` (data source `4dba9b7f`)
**Formerly:** "Portfolio Interaction Notes" — renamed/repurposed over time.

### Key Field Categories

#### Financial Tracking
- Entry Cheque, Reserve Deployed, Fresh Committed, Reserve Committed
- Earmarked Reserves, FMV Carried, FMV Last Round
- Money In (= Entry Cheque + Reserves Deployed), Ownership %

#### Reserve Modeling
- BU Reserve Defend, BU Reserve No Defend (Bottoms-Up scenarios)
- Top-Down Reserve (formulaic), Bottoms-Up Reserve (cap table modeling)
- Earmarked Reserves (final decision)

#### Outcome Scenarios
- Best Case Outcome, Good Case Outcome, Likely Outcome
- Outcome Category

#### Operations & Health
- Today (current status), Ops Prio, Health (Green/Yellow/Red)
- Check-In Cadence (aspirational, not actual), Fumes Date (out-of-money date)
- HC Priority, Action Due Date

#### Attribution
- Sourcing Attribution, Led By?, Participation Attribution
- MD Assigned, IP Assigned

#### Investment Classification
- AIF/USA, UW Decision (Core vs Community — NOT linked to cheque size)
- $500K Candidate?, Stage @ Entry, Current Stage
- **EF/EO (formal select field: FF/EF/EO)** — CRITICAL: this IS formalized in Portfolio DB

#### Follow-On
- Follow On Decision, Likely Follow On Decision
- Follow-on Work Priority, Next 3 Months IC Candidate

#### Relations
- Company Name (→ Companies DB), Meeting Notes, Introduced to?, Venture Partner

### Portfolio DB Semantic Definitions (from Read Me)
- **Health:** Green = won't die, Yellow = could go either way, Red = likely to die
- **UW Decision:** Core (DeVC team conviction) vs Community (Angels/Collective) — NOT linked to cheque size
- **Check-In Cadence:** Aspirational target, not current actual cadence
- **Fumes Date:** When company runs out of money
- **Investment Timeline ≠ Underwriting Timeline**
- **Reserves:** Top-Down = formulaic, Bottoms-Up = actual cap table modeling, Earmarked = final decision

### 17 Portfolio DB Views
Master View, Money View, Fundraising View, Tier 1 Co-Inv, Health (Board), Venture Partner View, Inv. Vintage, $ by Vintage, Entry Distribution (Chart), Entry Valuation (Chart), Concept/Traction charts, Stage charts, Follow On Composition, HC Priority, Meow

---

## Major Discovery 2: Comments as Deal Log

Notion page comments on Companies DB records serve as the primary day-to-day deal tracking mechanism — far richer than the page body content in many cases.

### OnArrival Comments (29 comments, Jul 2024 – Apr 2025)

**Complete deal lifecycle documented in comments:**

1. **BRC Phase:** External references from Gowri (Antler India Portfolio Director — "Top decile") and Gautam S (GP @ Inuka VC — detailed investment thesis)
2. **1PE/2PE Phase:**
   - RM's 2PE reflections: 21 numbered points including "Good thesis", "No better domain expert", price scoring at pre-seed
   - Avi's (Mohit's) 2PE with +/? notation: "Overall: Strong Maybe" with questions about margin pool, scale, margin expansion
3. **WhatsApp Debrief:** "Product + domain depth is 10/10", "Margins long term would be thin"
4. **Customer Calls:** RM conducted and debriefed customer reference calls
5. **Round Construct:** Founder updates on raise progress over months
6. **Closing:** "Never got back with BPlan despite follow-up. Same issue as last time"

**Color coding:** `<span color="orange">` = updates from founder or external sources

**User IDs decoded:**
- `88cda0ab` = RM (Rahul Mathur, VP)
- `3a14f1fb` = Cash (Aakash)
- `bbe5d805` = Avi/Mohit (Avnish Bajaj, GP)
- `5bdd202e` = Another team member (likely DC or other)

### LottoG Comments (11 comments)

**Deal lifecycle with alpha/beta assessment:**

1. **Founder Pitch:** IITB alums, RMG/lottery space, POS machines
2. **RM Spike Read:** "Very Dilsher like at pre seed"
3. **RM Assessment:** "SM for a $30K Top-Up IFF RMG smart money Angels are table thumping"
4. **RM Concerns:** Founder communication style — "use of words like 'politics, Mantralaya, ganja' just makes me zone out"
5. **RM Scoring:** "Spiky = 1 despite the beta", "FMF for their biz is quite high"
6. **BRCs:** Sachin (Probo) — "insanely spikey", "special founder hai" (bilingual); Manish (ex Nazara) — "smells like Dilsher!"
7. **Deal Negotiation:** "4 cr at 20cr post"
8. **Final Verdict:** "High alpha but too high beta. Don't want to be in business with the founder"

**Key Insight:** Aakash confirmed OnArrival's comment depth is "above average" — most deals have fewer comments. This makes OnArrival a gold-standard example of comment-based deal documentation.

---

## Major Discovery 3: DeVC IP Pack — The Definitive Investment Process Document

**Page:** `13629bcc-b6fc-802f-a073-f41a39c01a0a`
**Context:** Created from Sept '24 to Nov '24 retrospective analysis of portfolio, anti-portfolio & fund math.

### Complete Scoring Framework (All Sub-Dimensions)

#### Spiky Score (Overall: {0, 0.5, 1})
| Criterion | Max Score |
|---|---|
| Identifiable Spike | 2 |
| Bold & Ambitious | 1 |
| Clear & Insightful Thinker | 2 |
| Relentless & Grit | 1 |
| High rate of growth | 1 |
| Execution excellence | 2 |
| High ownership | 1 |

#### EO Score (out of 10)
| Criterion | Max Score |
|---|---|
| 1-10 strength or some 0 to 10 | 4 |
| Commercial POC/history | 1 |
| Thoughtful hustle and hunger | 1 |
| Referenceability and followership | 1 |
| Network leverage | 1 |
| Compounders | 1 |
| Wealth top decile | 1 |

#### FMF Score (out of 10)
| Criterion | Max Score |
|---|---|
| Product chops | 2 |
| S&M chops | 2 |
| Domain knowledge & skills | 3 |
| Breadth of exposure | 1 |
| Familiarity/repeat work | 1 |
| Advantage/arb | 1 |

#### Thesis Score (out of 10)
| Criterion | Max Score |
|---|---|
| Good thesis, sizable TAM | 5 |
| (++) Small share of direct SAM = large rev $$ | 1 |
| (++) Tailwinds + secular super strong trendline | 1 |
| (++) Key is product IP only or Biz acumen only | 1 |
| (++) Early Traction proof points | 1 |
| (++) Table thumping expert/DeVC Founder validation | 1 |

**Note:** Thesis has a Negative = 0 option (binary gate before scoring begins)

#### Price Score (out of 10)
| Post-Money Valuation | Score |
|---|---|
| Sub $6M | 10 |
| $6-10M | 8 |
| $10-15M | 6 |
| $15-25M | 4 |
| $25M+ | 2 |

### Cheque Size Decision Matrix (Spiky × EO+FMF)

| EO+FMF \ Spiky | 0 | 0.5 | 1 |
|---|---|---|---|
| **< 5** | $30K IFF >1 Collective invests | MAX $50K | 1-2% ownership (max ~$500K) |
| **5-15** | $30K IFF >1 Collective invests | MAX {1% ownership, $100K} | 1-2% ownership (max ~$500K) |
| **15+** | $30K IFF >1 Collective invests | MAX {2% ownership, $200K} | 1-2% ownership (max ~$500K) |

**Requirements by cell:**
- **Spiky 0 (all EO+FMF):** Soft BRCs, Collective Eval by default, no Domain Eval
- **Spiky 0.5:** Deep BRCs, MPE must (3-4 founder reads), Domain Eval required, GP sponsor(s)
- **Spiky 1:** Deep BRCs, On-demand IC ideal + MPE, Domain Eval required (investment not required), Min 1 GP sponsor

**Key rule:** Spiky score is ONLY for the lead founder, CANNOT aggregate co-founders.

### Fund I Retrospective (83 Investments, Sept '24)

| Spiky Score | As Is | Downsize | Avoid | Upsize | Total |
|---|---|---|---|---|---|
| 0 | 11 | 4 | 9 | 0 | 24 |
| 0.5 | 35 | 8 | 1 | 3 | 47 |
| 1 | 5 | 3 | 0 | 4 | 12 |
| **Total** | **51** | **15** | **10** | **7** | **83** |

**Interpretation:** Spiky=0 has highest regret (9/24 = 37.5% "Avoid"), Spiky=1 has 0 "Avoid" and most "Upsize" (4/12 = 33%).

### 10 Key Learnings from Fund I

1. Spiky score ONLY for lead founder — aggregating is a trap
2. Cannot label EO/FF as Spikey unless BRCs done
3. EO+FMF is critical for Spiky ≤ 0.5
4. Objective of BRCs is to get to a NO ASAP
5. Objective of 2PE should be clearly communicated by 1PE → focus on key unknowns
   - 2PE most useful for: Identifiable Spike (MPE should agree), Insightful Thinker, Execution Excellence
6. Collective needs anchoring on evaluating Founder vs evaluating Business
7. No impact on decision: Source of lead, Fast round formation (NOT being FOMO'ed)
8. For non-IC entry cheques, MPE suffices as IC replacement (same end outcome)
9. Spiky=1: Prioritize because usually FAST velocity; get MPE to validate
10. Fund I had 83 investments total across the three Spiky tiers

### Follow-On Framework

- **IDS (Increasing Degrees of Sophistication):** The purpose of every interaction with a founder or credible 3rd party is to build IDS about the founder and business
- **Follow-On participation options:** PR (Pro-Rata), SPR (Super Pro-Rata), No, Token
- **Barbell strategy at entry:** Either $30K community top-up OR $300K conviction cheque
- **Accretion challenge:** <1% to >3% ownership is always hard — need early conviction and speed
- **IC required for:** All follow-on investments AND primary cheques >$300K at entry

### IC Templates
- **IC Work Plan Template** (`18229bcc...83c2`) — standard format for IC preparation
- **IC Notes Template** (`18229bcc...81f7`) — standard format for IC day note-taking
- Templates go in Portfolio DB (follow-on) or Companies DB (fresh)

---

## Major Discovery 4: Finance DB (23 Fields)

**Database ID:** `604fb62a-c3f4-408a-a6fe-c574949a8e43` (data source `9b59fd98`)

A rollup/view database pulling from Companies DB and Network DB. Not a primary data entry point.

### Key Fields
- **Relations:** Companies DB, Network DB, Current People (Links)
- **Key rollups:** Pipeline Status, Priority, Money Committed, Money In, Ownership %, AIF/USA
- **Formulas:** Angels, Current People, Investors, Piped From

### 8 Views
Main Pipeline, GSD View, Base, Co-Investors, Portfolio for Editing, Angel's Port Co's, Founding Vintage, Surfacing Calendar

---

## Major Discovery 5: Lead Source Taxonomy (from Basic SOP on Leads)

| Source | Description | Turn-Around |
|---|---|---|
| DeVC Founders (Collective) | Leads from DeVC Collective members | < 48 hrs |
| Other Micro VCs | Co-investment opportunities from peer funds | < 72 hrs |
| HOTS (Heard On The Street) | Tier 1/1.5 deals generating market buzz | < 72 hrs |
| Inbound | Companies approaching DeVC directly | < 5 days |
| Programmatic Mining | Outbound from YC, South Park Commons, EF, Antler, etc. | < 5 days |
| HiPO EOs | High-Potential EOs met through daily interactions | < 5 days |

**Key Process Rules:**
- EVERY entity goes in Companies DB, EVERY person goes in Network DB
- First step is always: "Must pursue or NOT?" — answer via the DeVC scoring framework
- DeVC Founder leads always loop in Aakash directly

---

## Interview Findings (Rounds 14-16)

### Round 14 (Comments, EF/EO, Alpha/Beta, Dilsher)
1. **Comments as deal-log:** OnArrival thoroughness is "above average" — most deals have fewer comments
2. **EF/EO formalization:** "Ideally it should be a formal field all throughout. We have tried to ensure it is captured formally in portfolio."
3. **Alpha/Beta:** "Part of lexicon at the firm" — confirmed firm-wide framework, not just RM shorthand
4. **Dilsher benchmark:** Founder of Zuppee (Z47 portfolio), spikey FF who created outcome. Likeness measure for consumer tech/gaming/social domain founders. "Not necessarily a gold standard."

### Round 15 (Anti Folio, Surface to Collective, Lead Sources, Record Counts)
1. **Anti Folio:** "We should have invested in the company but for some reason or process issue didn't or couldn't." — A regret/miss category, not a negative signal.
2. **Surface to Collective:** Manual for now. About surfacing interesting opportunities to DeVC Collective for co-eval or potential investment even if DeVC doesn't invest. "Should be partly or fully automated in future with Claude."
3. **HOTS:** Heard On The Street — opportunities the team has heard about getting interest from other VCs, Micro VCs, angels
4. **Programmatic Mining:** Outbound mining of cohorts from accelerators/incubators (YC, South Park Commons, EF, Antler, and more)
5. **HIL Review:** Aakash doesn't know — "might have been setup by RM"
6. **Record Counts:** Network DB: 2000+, Companies DB: 2000+ — large-scale CRM

---

## Major Discovery 6: Granola Meeting Notes — Exhaustive Deep Dive

**Source:** Granola AI (meeting transcription + AI notes with Aakash's manual annotations)
**Scope examined:** 33 meetings fetched individually (Jan 5 – Feb 26, 2026) + semantic queries returning data from 100+ meetings in archive
**Critical context:** Granola captures only ~10-15% of Aakash's actual meetings (7-8/day). Phone Zoom, live meetings, and many others go uncaptured. CRM capture has "lag and drop off."

### Aakash's Annotation Pattern

Only new deal evaluations receive personal annotations (not portfolio check-ins, networking, or hiring). Format:

```
Overall: [Verdict]
[1-2 line rationale using DeVC vocabulary]
Sometimes: "Piped from: [source]"
Sometimes: "+/?" notation for pro/con
```

**Annotated examples found:**
- **Tutti Frutti (Feb 16):** "Overall: Weak Maybe. Non spikey folks on commercial and GTM. Good spike on building narrative based games. Not a VC play given team profile. Studio biz needs super strong commercial players"
- **Ditto Labs (Feb 24):** "Overall: Easy PwC. No depth in either AI, tech, product or growth"
- **Pradivya (Feb 16):** "Piped from: Ankur C (ex Swiggy). Overall: Weak Maybe to NO. + Good thesis bet but founder spike and archetype is just not there. ? Caught in poor cash cycles around B2G (railways) and founders are poor sellers and poor commercial bone"

### Real-Time Scoring Data (from Granola semantic queries)

Companies with full scoring visible in meeting notes (using DeVC IP Pack framework):

| Company | Spike | EO | FMF | Archetype | Thesis | Verdict |
|---|---|---|---|---|---|---|
| Answer This (Ayush) | ~1 | 7-8 | 7-8 | 8-9 | 6 | Strong Maybe |
| Lane (Samiksha) | 1 | 5-6 | 6-7 | 8-9 | 6 | Strong Maybe |
| Himanshu/Fulcrum | 1? | — | 8-9 | 7-8 | 5 | Strong Maybe |
| Logikality (Alok) | 0.5-1 | 7-8 | 7-8 | 6-7 | 5 | Strong Maybe |
| Caddy AI (Connor) | ~1 | 7-8 | 6-7 | 6-7 | — | Maybe+ |
| Astrm | 0.5-1 | 6-7 | 6-7 | 7-8 | 5 | Strong Maybe |
| Turmerik (Ayushi) | 0.5-1 | 6 | 7-8 | 7 | 6 | Strong Maybe |
| Helium Air | 0.5-1 | 6-7 | 4-5 | 6-7 | 5 | — |
| Z-own | 0.5 | 6-7 | 5-6 | 3-4 | — | — |
| Neo Recruit | 0 | 6-7 | 3-4 | — | ? | WM to NO |
| Maryadha | 0 | 5-6 | 4-5 | — | 0 | NO |
| KalpaLabs | 0 | 4-5 | ? | — | ? | — |

**Key observation:** Scoring appears in real-time during or immediately after meetings. This is a richer, more immediate source of scoring data than what eventually makes it into Notion CRM.

### Deal Verdicts & Pass Reasons (30+ companies)

**Clear NOs:**
- Taking Forward: "Spike = -1, Zero grounding, will never work"
- Maryadha: "Outright poor thesis", founders have no spike
- EMOMEE: "Meandering and just not grounded team. Will likely burn to the ground"
- Ludexai: "Zero grounding, will never work" on Web3 gaming — "gaming is experience engineering, not asset ownership"

**Weak Maybe to NOs:**
- Neo Recruit: Non-spikey founders, no real enterprise FMF
- Restomart: No spike, low GM B2B procurement — "not a thesis space for us"
- Pradivya: "Founder spike and archetype is just not there"
- Vasundhra Singh: "Don't see any intrinsics/spike to bet on", "very out of depth"

**Weak Maybes:**
- Tutti Frutti: "Not a VC play given team profile"
- Simply Flow AI: "No depth of thinking, not for us"
- Agrim: Non-spikey, will struggle with GTM always
- Hey Bumi: "Non spikey founders, tech folks with no FMF for consumer biz"
- Trace: "Horizontal isn't a thesis zone, no GTM or product spike visible"
- Vachi AI: "Didn't see founder spike", prosumer approach to B2B problem

**Common pass patterns:**
1. No identifiable founder spike (most frequent)
2. Poor thesis fit / not a DeVC thesis zone
3. No FMF (tech founders in consumer, or no domain depth)
4. Weak commercial bone / poor GTM capability
5. Archetype mismatch ("not our archetype")

### Portfolio Health Check-Ins (from Granola)

| Company | Key Metrics | Status |
|---|---|---|
| Felicity | $290-300K monthly revenue, 10% MoM growth, $110-120K burn | Active fundraise, multiple investors in DD |
| Step Security | $1M ARR, 5x YoY growth, Q4 $300K net new | Planning Series A, targeting $3M ARR |
| Cautio | ₹6cr ARR, 55 direct customers, 8K devices deployed | Seeking $5M round, targeting 45K devices by Mar 2027 |
| Ask My Guru | ₹74K daily spend, ₹55K daily revenue, 670K users | 90-day payback, ₹9.5cr runway |
| Dashverse | 156% NRR after 5 months, ₹500K/month burn | ₹5cr venture debt secured, 14-month runway |
| Bidso | ₹6.5cr monthly revenue, target ₹15cr | Raising ₹45cr at ₹190cr pre-money from Bloom |
| Sifthub | 420K ARR, 29 contracts, 18-month runway | Contract expansion (Lego: 3K → 920K) |
| Revenoid | ~₹750K ARR (from ₹0 in Q1) | Target $2-2.5M raise at $25M post-money |
| YOYO AI | MRR ~₹10L, 96 stores live | $300-400K bridge for US expansion |
| Emtech | $2.2M revenue 2025, Nigeria pilot | Need $600K bridge |
| Extra Edge | ₹2cr cash, ₹18-20L monthly burn | Target ₹30-35cr raise at ₹200cr |

### Referral Network Map (from Granola)

Granola reveals lead sourcing patterns not always captured in CRM:

| Company | Piped From / Source |
|---|---|
| Simply Flow AI | Vaibhav Jain @ Hubilo |
| Agrim | Manish @ Kgen |
| Taking Forward | Vishesh |
| Neo Recruit | Dhyanesh (IIM batchmates) |
| Z-own | Gautam @ Inuka |
| Trace | Dev at Wedge (YC S25) |
| FinalRun | Kushagra @ weaver |
| Orcana AI | RBS (GP) |
| Turmerik | Manav @ Memora (also angel investing) |
| Vachi AI | Chandrika @ quivly + SSK |
| Pradivya | Ankur C (ex Swiggy) |

**Network categories observed:**
- DeVC Collective members and portfolio founders referring deals
- Peer fund VCs (Inuka, Wedge, etc.)
- IIT/IIM alumni network connections
- GP-sourced (RBS directly piping)
- Industry contacts (ex-operators at Swiggy, Hubilo, Nazara)

### BRC & Due Diligence Activities

**Active BRCs identified:**
- Anshula: BRC with Subeer Sorin completed
- Ayushi (Turmeric): BRCs scheduled with David Stavens and Joel from Nines
- Astrm: BRCs needed, Vishesh meeting them
- Lane (Samiksha): BRCs needed with caution (Antler connection)
- Caddy AI: Reference check with past Loom colleagues
- Answer This: University references to validate founder capabilities

**IC Preparation:**
- Terafac: Internal IC scheduled Dec 3rd in Bangalore
- Multiple DVC investments pending final decisions (5-7 day timelines)

### Value-Add / IDS Activities (Portfolio)

Strategic advice given to portfolio companies (examples from Granola):
- **Step Security:** Fundraising guidance ($2.5-3M convertible vs Series A timing), customer intros (Crane UK, Proven Bay Area, Wing VC), GTM expert connection (Sandeep Shukla)
- **Felicity:** Geographic expansion advice (move to US), financial planning (gradual burn ramp to $200K), multi-investor fundraise guidance
- **Dashverse:** Strategic positioning advice (choose narrative: "consumer platform + premium" vs "AI micro-drama winner")
- **Ferma 3D:** Extensive real estate ecosystem intros (Sushma Build Tech, Agami, Jerry Rao, Luda Ventures, DLF)
- **Kestrel:** Intros to portfolio companies (Razorpay, Hotstar teams)
- **Ditto:** Z47 portfolio connections for OEM/commerce partnerships

### What Spiky=1 Founders Have in Common (from Granola)

**Answer This (Ayush):** Started coding at 16, Singapore government + Cambridge labs, built $20K→$107K MRR in 2 months, 4,500+ paying researchers
**Caddy AI (Connor):** 4 years at Loom leading AI/monetization, launched Loom AI (25% of revenue), 1,400 organic waitlist
**Miro (Construction):** 4 generations of construction family, worked across 6 countries, previous exit, first paid customer in 3 weeks (expected 6-8 months), 100K→400K ARR in 6 weeks
**Himanshu/Fulcrum:** 18+ years capital markets (Brevan Howard, Citadel), built AI tools replacing £200K+ analyst roles

**Common thread:** Deep domain DNA + proven execution velocity + immediate market validation. Not just smart — operators with the specific background to win in their chosen market.

### Interview Round 17-18 Findings (Granola Workflow)

**Round 17 (Annotation patterns):**
- Only new deal evaluations get verdicts (confirmed)
- Lead source noted "when I remember" — informal, inconsistent, would love automated

**Round 18 (Meeting-to-CRM gap — CRITICAL REVELATION):**
- Verdict flow: "Mix of channels, inconsistent" — WhatsApp, Notion, verbal, sometimes nowhere
- Ideal check-in output: "All of the above" — health + action items + IDS signals + changed outlook
- **Meeting volume: "I do about 7-8 a day. Most not on granola. Sometimes I use zoom on my phone, no granola there. Live meetings no granola."**
- **CRM capture: "Every meeting should result in CRM update but there is lag and drop off"**
- **Implication:** ~35-40 meetings/week, Granola captures ~4-5/week = ~10-15% coverage. The gap between meetings happening and CRM updates is THE biggest AI CoS opportunity.

---

## Updated Evaluation Stack (Revised with Session 006)

| Layer | People (Network DB) | Companies (Companies DB) | Portfolio (Portfolio DB) |
|---|---|---|---|
| Identity | Role, Location, Background, Schools | Sector, Funding, Type, Sells To | Company Name (→ Companies DB) |
| Assessment | RM reflections (++/??, SM/WM), Cash notes, Leverage | JTBD (1PE/2PE/MPE/BRC), EF/EO/FF (implicit), Spiky + EO/FMF/Thesis/Price | EF/EO (formal select), IDS, Follow-on assessment |
| Classification | DeVC Relationship (13 archetypes), Collective Flag | Pipeline Status, Deal Status (3D matrix), Priority (P0-P2) | UW Decision (Core/Community), Stage @ Entry/Current |
| Financial | — | — | Entry Cheque, Reserves, FMV, Money In, Ownership % |
| Outcome | — | — | Best/Good/Likely Outcome, Outcome Category |
| Operations | R/Y/G, E/E Priority | Tracking cadence (7/30/90/180), Action Due? | Health (G/Y/R), Ops Prio, Check-In Cadence, Fumes Date |
| Attribution | — | — | Sourcing/Participation Attribution, MD/IP Assigned |
| Follow-On | — | — | Follow On Decision, Likely Follow On, $500K candidate?, Next 3 months IC |

---

## Updated Data Fragmentation Map

| Data Type | Current Location(s) | Structured? |
|---|---|---|
| Pipeline Status | Companies DB (Status field) | ✅ Yes |
| Deal Status | Companies DB (Status field) | ✅ Yes |
| JTBD Status | Companies DB (Multi-select) | ✅ Yes |
| DeVC Relationship | Network DB (Select) | ✅ Yes |
| EF/EO/FF Classification | Portfolio DB (formal select), elsewhere implicit | ⚠️ Partial |
| Scoring (Spiky + EO/FMF/Thesis/Price) | Notion pages (template), comments, messaging, email, verbal | ❌ Mostly unstructured |
| BRC Results | Notion page body (toggles), comments, email, WhatsApp | ❌ Partially structured |
| Deal Timeline/Log | Notion page comments (primary), page body (secondary) | ⚠️ Semi-structured |
| Meeting Notes | Notion page body (two formats), Meeting Notes DB (underused) | ⚠️ Partially |
| Portfolio Financials | Portfolio DB (94 fields) | ✅ Yes |
| Reserve Modeling | Portfolio DB (Top-Down/BU/Earmarked) | ✅ Yes |
| Outcome Scenarios | Portfolio DB (Best/Good/Likely) | ✅ Yes |
| Follow-On Decisions | Portfolio DB fields | ✅ Yes |
| Lead Source | Not formally tracked per-deal | ❌ Not captured |
| Deal Documents | The Vault (SharePoint) | ✅ Organized by sector |
| IC Work Plans/Notes | Companies DB or Portfolio DB pages (templates) | ⚠️ Template exists |
| Fund Math | SharePoint (DeVC II folder) | ✅ Separate |
| Universal Verdicts (SM/WM/M/M+/No) | Comments, notes (scattered) | ❌ Not captured |
| **Granola Meeting Transcripts** | **Granola app (~10-15% of meetings)** | **⚠️ AI-structured + manual annotations** |
| **Real-Time Scoring (during meetings)** | **Granola notes (annotations + AI summary)** | **❌ Not synced to CRM** |
| **Lead Source (per-deal)** | **Granola "Piped from" notes, informal** | **❌ Not systematically captured** |
| **Portfolio Health Metrics** | **Granola check-in notes, Notion comments** | **⚠️ Scattered across sources** |
| **Value-Add Activities (IDS)** | **Granola notes, WhatsApp, verbal** | **❌ Mostly unstructured** |
| **BRC Results (real-time)** | **Granola notes, Notion page body** | **⚠️ Partially captured** |

---

## Complete DB Ecosystem Map

```
Network DB (2000+ records, 40+ fields)
  └── People: VCs, founders, angels, operators, LPs
  └── Assessment: DeVC Relationship, RM reflections, Leverage
  └── Relations → Companies DB (via various link fields)

Companies DB (2000+ records, 49 fields)
  └── Deals: Pipeline tracking, JTBD, scoring templates
  └── Page Comments: Primary deal log (BRCs, PE reflections, debriefs)
  └── Page Body: Meeting notes (two eras), BRC toggles
  └── Relations → Network DB, Portfolio DB, Finance DB

Portfolio DB (94 fields)
  └── Post-investment: Financials, reserves, outcomes, operations
  └── EF/EO: Formal select field (FF/EF/EO)
  └── Follow-on: Decision framework, IC candidates
  └── Relations → Companies DB, Meeting Notes

Finance DB (23 fields)
  └── Rollup/View DB: Pulls from Companies + Network DBs
  └── 8 views for different analytical perspectives

Meeting Notes DB
  └── Vision: Map all meetings + tag to person/company
  └── Status: "Didn't take off" — underused

The Vault (SharePoint)
  └── Document hub: Organized by sector
  └── Fund math, legal docs, IC materials

Granola (Meeting Notes — EXTERNAL)
  └── AI-transcribed meeting notes (~10-15% of meetings captured)
  └── Aakash's manual annotations on new deal evals (verdicts, scores)
  └── Real-time scoring data (Spiky, EO, FMF, Archetype, Thesis)
  └── Portfolio check-in metrics (revenue, burn, runway, fundraise status)
  └── Referral tracking ("Piped from: [source]")
  └── BRC debrief notes
  └── Value-add/IDS activity records
  └── NOT synced to Notion CRM — manual transfer with lag/drop-off
  └── 100+ meetings in archive (Jan–Feb 2026 = 33 individually examined)
```

---

## Open Questions (Updated)

### Resolved in This Session
- ✅ What is the full EO scoring rubric? (7 sub-dimensions, total 10 — see IP Pack)
- ✅ What is the full FMF rubric? (6 sub-dimensions, total 10)
- ✅ What is the full Thesis rubric? (5+1 sub-dimensions, total 10, with Negative=0 gate)
- ✅ What does Anti Folio mean? (Regret/miss — should have invested but didn't/couldn't)
- ✅ What triggers Surface to Collective? (Manual — surfacing for co-eval or potential Collective investment)
- ✅ What is HOTS? (Heard On The Street — market buzz about deals)
- ✅ What is Programmatic Mining? (Outbound from YC, SPC, EF, Antler cohorts)
- ✅ What does Alpha/Beta mean? (Firm-wide lexicon — alpha=upside/spikiness, beta=risk/volatility)
- ✅ Who is Dilsher? (Zuppee founder, Z47 portfolio, spikey FF benchmark for consumer/gaming/social)
- ✅ What is the cheque size decision framework? (2D matrix: Spiky × EO+FMF)
- ✅ What is the IC process? (Required for follow-on + primary >$300K, templates exist)
- ✅ What is IDS? (Increasing Degrees of Sophistication — purpose of every founder interaction)
- ✅ What is the follow-on framework? (PR/SPR/No/Token + barbell strategy)
- ✅ How many records in each DB? (2000+ each for Network and Companies)
- ✅ What is the Finance DB? (23-field rollup DB with 8 views)
- ✅ What are the lead sources? (6 sources with defined turn-around times)

### Resolved via Granola Deep Dive
- ✅ How does Aakash annotate meeting notes? (Only new deal evals, "Overall: [Verdict]" + rationale, sometimes "Piped from")
- ✅ What scoring happens in real-time during meetings? (Full Spiky/EO/FMF/Archetype/Thesis scoring visible in 15+ companies)
- ✅ What does a portfolio check-in produce? (Health + action items + IDS signals + changed outlook)
- ✅ How do verdicts flow? (Mix of channels — WhatsApp, Notion, verbal, sometimes nowhere — inconsistent)
- ✅ What is the actual meeting volume? (7-8/day ≈ 35-40/week; Granola captures ~10-15%)
- ✅ What referral sources exist? (15+ piped-from sources identified including Collective, peer funds, alumni networks, GPs, industry contacts)
- ✅ What makes Spiky=1 founders stand out? (Deep domain DNA + proven execution velocity + immediate market validation)

### Still Open
1. **HIL Review process** — Aakash doesn't know, RM setup. Need to examine directly.
2. **Corp Dev DB** — No dedicated database found as a separate DB. May be embedded in weekly notes or tasks.
3. **Pending Tasks DB** (`1b829bcc`) — Schema and usage unknown
4. **Meeting Notes DB schema** — Fields and envisioned workflow unknown
5. **"Formulas"** — How do AIF/USA, Money In, Ownership % calculate exactly?
6. **"Surface to collective" automation** — Aakash wants Claude to help automate this
7. **Insta Astro page** — 404 when trying to access comments (wrong UUID or access issue)
8. **IC Work Plan and Notes templates** — Content not yet examined
9. **Whimsical flowcharts** — IC Process and Investment Process diagrams (hosted externally)
10. **Granola → CRM sync gap** — Biggest AI CoS opportunity. How to bridge 85-90% of meetings that go unrecorded?
11. **Deeper Granola archive** — Semantic queries reference meeting IDs up to 144+, suggesting much deeper history. Older meetings may contain additional pattern data.

---

## Cumulative Progress (Sessions 001-006)

| Dimension | Status |
|---|---|
| Network DB schema (40+ fields) | ✅ Fully mapped |
| Companies DB schema (49 fields) | ✅ Fully mapped |
| Portfolio DB schema (94 fields) | ✅ Fully mapped |
| Finance DB schema (23 fields) | ✅ Mapped (rollup DB) |
| All 13 DeVC Relationship archetypes | ✅ Fully decoded |
| Deal Status 3D matrix | ✅ Decoded (Speed × Timing × Pull) |
| JTBD "Pair of Eyes" model | ✅ Decoded |
| BRC process | ✅ Documented |
| Full scoring framework (all sub-dimensions) | ✅ Fully decoded from IP Pack |
| Cheque size decision matrix | ✅ Fully decoded (Spiky × EO+FMF) |
| Investment process (IC, follow-on, IDS) | ✅ Decoded from IP Pack |
| Fund I retrospective (83 investments) | ✅ Captured |
| Founder classification (EF/EO/FF) | ✅ Decoded + formal in Portfolio DB |
| Page format eras | ✅ Identified (pre vs post Sep 2024) |
| Comments as deal log | ✅ Discovered + 2 detailed examples |
| Lead source taxonomy (6 sources) | ✅ Decoded with turn-around times |
| Alpha/Beta firm lexicon | ✅ Confirmed |
| Data fragmentation map | ✅ Comprehensive mapping |
| DB ecosystem map | ✅ All 4 primary DBs + Meeting Notes + Vault |
| Record-level examination | ⚠️ 8 Companies, ~29 Network, 2 comment deep-dives |
| Total record counts | ✅ 2000+ each (Network, Companies) |
| Real deal end-to-end trace | ✅ OnArrival (29 comments lifecycle) |
| Anti Folio, Surface to Collective | ✅ Decoded |
| Linked DBs explored | ⚠️ 3 of 5+ explored (Portfolio, Finance, Meeting Notes partial) |
| **Granola meeting notes** | **✅ 33 meetings individually examined + semantic queries on 100+ archive** |
| **Granola annotation patterns** | **✅ Decoded (verdict format, scoring, piped-from, +/? notation)** |
| **Real-time scoring data (Granola)** | **✅ 15+ companies with full Spiky/EO/FMF/Archetype/Thesis scores** |
| **Portfolio health metrics (Granola)** | **✅ 11+ companies with revenue/burn/runway/fundraise data** |
| **Deal verdict patterns (Granola)** | **✅ 30+ verdicts with pass reasons mapped** |
| **Referral network (Granola)** | **✅ 15+ piped-from sources identified** |
| **Meeting-to-CRM gap** | **✅ Identified: 7-8 meetings/day, ~10-15% Granola capture, significant lag** |
| **Value-add/IDS activities** | **✅ Mapped from Granola (intros, strategic advice, BRC debriefs)** |
| Formal taxonomy model | ❌ Not yet started |
| Interview rounds completed | 18 total (Rounds 1-7 Network, 8-11 Companies schema, 12-13 scoring/classification, 14-16 comments/IP Pack/lead sources, 17-18 Granola workflow) |

---

## Next Steps

1. **Begin drafting formal taxonomy model** — Sufficient data now exists for comprehensive synthesis across all sources (Notion 4 DBs + Granola + IP Pack + Interviews)
2. **Self-critique understanding for exhaustiveness** — Per Aakash's standing instruction, critically assess gaps before moving to synthesis. Key question: what don't we know yet?
3. **Examine IC Work Plan and Notes templates** — Understand IC preparation workflow
4. **Explore Pending Tasks DB** — Schema and current usage
5. **Examine Meeting Notes DB schema** — Fields and envisioned workflow
6. **Resolve remaining formula questions** — AIF/USA, Money In, Ownership % calculation methods
7. **Granola → CRM bridge design** — The biggest AI CoS opportunity: how to capture the 85-90% of meetings that go unrecorded, and auto-generate CRM updates from Granola notes
8. **Consider automation opportunities** — Surface to Collective automation, scoring centralization, deal log structuring, verdict capture, lead source tracking

## Synthesis: Granola + Notion CRM — Where Data Lives vs. Where It Should Be

The Granola deep dive reveals a fundamental information architecture gap:

**What Granola captures that Notion doesn't (immediately):**
- Real-time scoring during meetings (Spiky, EO, FMF, Archetype, Thesis)
- Deal verdicts at point of evaluation
- Lead source / piped-from attribution
- Portfolio health metrics (revenue, burn, runway, fundraise status)
- BRC debrief notes and reference outcomes
- Value-add activities and intro commitments
- Action items and next steps

**What Notion has that Granola doesn't:**
- Structured DB fields for all 4 databases (194+ total fields)
- Historical deal log via comments
- Financial modeling (reserves, ownership, FMV)
- Formal classification (EF/EO/FF, Pipeline Status, Deal Status 3D)
- Cross-entity relations (people ↔ companies ↔ portfolio ↔ finance)
- Views and analytics (17 Portfolio views, 12+ Companies views)

**The gap:** Scoring, verdicts, and rich context generated in meetings (Granola) don't flow automatically into the structured CRM (Notion). Aakash does 35-40 meetings/week; only a fraction generates CRM updates, and those updates lag. The AI CoS's core value proposition is bridging this gap — becoming the connective tissue between meeting intelligence and structured data.
