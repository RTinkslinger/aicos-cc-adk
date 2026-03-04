# Session 005: Portfolio Pages, Scoring Framework & Founder Classification

**Date:** March 1, 2026
**Interface:** Cowork (continuation from Session 004)
**Phase:** Understanding (Steps 1–3 — Companies DB Record-Level Analysis, Scoring Framework Discovery, Founder Classification Decoding)

---

## Summary

Examined 8 Companies DB records across different Pipeline Statuses (Portfolio, Pass Forever, NA, Acquired/Shut Down/Defunct, DeVC Concept Prospect). Major discoveries: the full Spiky Score + EO/FMF/Thesis/Price scoring framework (template exists but rarely filled in Notion), the implicit EF/EO/FF founder classification system, two-era page format shift (pre vs post Sep 2024), BRC notation patterns, and critical data fragmentation finding — scoring and assessment data is scattered across Notion comments, messaging apps, email, and verbal channels.

---

## Companies DB Records Examined (8 Records)

### Record-by-Record Analysis

#### 1. JustAMoment AI (`1a629bcc`)
- **Pipeline Status:** Acquired/Shut Down/Defunct
- **Deal Status:** NA
- **JTBD:** All Pending
- **Priority:** P2
- **Sector:** Financial Services | Sector Tags: AI, Sales
- **Key Finding:** Has the full post-Sep 2024 template (RM's structured format). Includes auto-generated "Conversation Prep Research" section with Founders & Background, Market Map (In CRM + Web Research), 15 Suggested Questions, Previous Meeting Summary, Key Risks. Scoring tables present but **completely empty**.

#### 2. App0 (`1ba29bcc`)
- **Pipeline Status:** Pass Forever
- **Priority:** P1
- **Deal Status:** NA
- **JTBD:** All Pending
- **Key Finding:** Has template + actual meeting notes from intro conversation. Content: Cloud Lending Solutions founder ($140M exit), building AI agents for ecommerce, 10 customers, targeting $1.5-2M ARR. Demonstrates the kind of substantive meeting notes that exist. Scoring tables **empty**.

#### 3. Fibr AI (`18c29bcc`)
- **Pipeline Status:** Pass Forever
- **Priority:** P2
- **Sector:** SaaS | Sector Tags: AI, Marketing
- **Key Finding:** Template with scoring sections but no notes filled in. Has populated Investors (VCs, Micros) and Angels relations.

#### 4. Insta Astro (`0e7ff359`) ✓ PORTFOLIO
- **Pipeline Status:** Portfolio
- **Venture Funding:** Pre-Seed
- **Founding Timeline:** H2 2020
- **Last Round:** $2.3M, H1 2024
- **Key Finding:** **Old-format page** (pre-template era). Raw meeting notes with rich operational data: revenue metrics (3.45 cr, 40% GM), unit economics (CAC Rs 148, LTV Rs 510), competitive positioning vs Astrotalk, round details (15 cr raise → 115-125 cr pre → 5 cr room). Has Portfolio Interaction Notes relation. Demonstrates the depth of notes that exist for portfolio companies.

#### 5. Finsire (`7a21914d`) ✓ PORTFOLIO
- **Pipeline Status:** Portfolio
- **Deal Status:** In Strike Zone
- **Venture Funding:** Seed
- **Sells To:** Financial Services, Mid Market
- **Type:** SMB
- **Key Finding:** Has 7 Meeting Notes links, 1 Pending Task, Portfolio Interaction Notes relation, and a Vault Link (SharePoint). Content is brief intro-email style. 7 Angels, 2 Investors (VCs, Micros) populated. Demonstrates the linked-DB ecosystem for active portfolio companies.

#### 6. OnArrival (`854f0f7c`) — CRITICAL RECORD
- **Pipeline Status:** Pass Forever
- **Deal Status:** In Strike Zone
- **Priority:** P1
- **JTBD:** ALL DONE (1PE Done, 2PE Done, MPE Done, BRCs Done)
- **Key Finding:** **Confirms Pipeline Status and Deal Status are independent dimensions.** In Strike Zone = thesis/sweet spot fit. Pass Forever = investment decision. A company can be perfect for DeVC's thesis but still passed. Has rich BRC content in collapsible toggles:
  - Reference from Gowri (Antler India Portfolio Director): "Top decile" founder assessment
  - Reference from Gautam S (GP @ Inuka VC): Detailed investment thesis evolution and founder anecdotes
- Pre-template format with DeVC IP POC, Alums relations, Vault Link populated.

#### 7. Arthum (`3fb75f71`)
- **Pipeline Status:** NA
- **Deal Status:** NA
- **Sector:** Financial Services, Lending
- **Sells To:** Consumers
- **Key Finding:** Single BRC demonstrating the `+`/`?` notation pattern:
  - `+` = strengths
  - `?` = concerns/questions
  - Bold **summary** with underlined verdict
  - Example verdict: "weak ref overall. Understands the segment very well but no followership and ability to scale is missing. Closing the thread and passing."
- Has Vault Link.

#### 8. LottoG (`1af29bcc`)
- **Pipeline Status:** Pass Forever
- **Deal Status:** DeVC Concept Prospect
- **Priority:** P0🔥
- **JTBD:** 1PE Done, 2PE Done, DE Done, MPE Pending, BRCs Pending
- **Key Finding:** 3 rich reference checks with bilingual (English + Hindi/Hinglish) content:
  - From Sachin (Probo): "insanely spikey and clearly the highest energy founder I have met"
  - From Ujjwal Soni (competitions CG 2020)
  - From Ujjwal Kalra (WestBridge, IIT-B senior)
- Has 2 Pending Tasks. Scoring template present but **empty**. Demonstrates a high-priority deal that progressed deeply through JTBD but ultimately passed.

---

## Major Discovery 1: Scoring Framework (Template-Level)

### Spiky Score
7 criteria, each scored, with an overall binary assessment {0, 0.5, 1}:

| Criterion | Max Score |
|---|---|
| Identifiable Spike | 2 |
| Bold & Ambitious | 1 |
| Clear & Insightful Thinker | 2 |
| Relentless & Grit | 1 |
| High rate of growth | 1 |
| Execution excellence | 2 |
| High ownership | 1 |
| **Overall** | **{0, 0.5, 1}** |

### EO/FMF/Thesis/Price Score (out of 40)

| Dimension | Max | Notes |
|---|---|---|
| FMF (Founder-Market Fit) | 10 | How well the founder fits the market they're attacking |
| EO (Experienced Operator) | 10 | See EF/EO/FF classification below |
| Thesis | 10 | Alignment with DeVC/Z47 investment thesis |
| Price | 10 | Post-money valuation scoring (inverse — lower = better) |
| **Total** | **40** | |

### Price Scoring Scale
| Post-Money Valuation | Score |
|---|---|
| Sub $6M | 10 |
| $6-10M | 8 |
| $10-15M | 6 |
| $15-25M | 4 |
| $25M+ | 2 |

### Critical Finding: Scoring Data Fragmentation
**Scores are almost never filled in within Notion.** All 8 records examined had empty scoring tables. Aakash confirmed: "Some scoring in notion pages for companies would be there though sparse. Look at comments in a company page too — sometimes these would be there merged into more notes and views. They are passed around in messaging apps, mail, verbally and more. **Record keeping and thoroughness and depth of work on scoring needs to improve in the firm.**"

This is a major AI CoS opportunity — capturing, structuring, and centralizing scoring data that currently scatters across channels.

---

## Major Discovery 2: EF/EO/FF Founder Classification System

**Previously unknown implicit mental model** (NOT a formal DB field):

| Code | Full Name | Definition |
|---|---|---|
| **EF** | Experienced Founder | Builders who have seen all of 0→1, 1→10, and 10→∞ in business themselves |
| **EO** | Experienced Operator | People who have some experience (could have been founders too before) but never scaled to outcome |
| **FF** | First-time Founder | Raw founders with limited to none business operating experience |

**Key Insight:** The "EO" in the scoring framework's "EO/FMF/Thesis/Price" refers specifically to the Experienced Operator dimension — how much operational experience the founder brings. The 10-point EO score system has additional dimensions beyond the basic classification.

**This is an implicit assessment — a mental model applied during evaluation, not captured as a structured field in any DB.**

---

## Major Discovery 3: Two-Era Page Format

### Pre-September 2024 Format
- Raw, unstructured meeting notes
- Inline BRC content in collapsible toggles
- Revenue metrics, unit economics, competitive data mixed with meeting notes
- Examples: Insta Astro, OnArrival, Arthum

### Post-September 2024 Format (RM's Template)
Created by Rahul Mathur (RM, VP at DeVC). Structured sections:
1. **Table of Contents**
2. **READ ME** — Template usage instructions
3. **Deck insights**
4. **Intro Conversation** — Attendees / Notes / Scoring / De-brief
5. **Follow-up Conversation** — Same structure
6. **Next Conversation** — Same structure
7. **Z47 Conversation** — Same structure
8. **Conversation Prep Research** (auto-generated):
   - Founders & Background
   - Market Map (In CRM + Web Research)
   - Suggested Questions (typically ~15)
   - Previous Meeting Summary
   - Key Risks

Examples: JustAMoment AI, App0, Fibr AI, LottoG

---

## Major Discovery 4: BRC Notation Patterns

Across examined records, BRC entries follow a consistent notation:
- **`+`** = Strengths / positive signals
- **`?`** = Concerns / questions / red flags
- **Bold summary** with underlined verdict text
- **Bilingual content** — English mixed with Hindi/Hinglish (especially in informal references)
- **Structure:** Source person identification → relationship context → structured +/? notes → bold verdict

---

## Interview Findings (Rounds 12-13)

### Round 12 (Scoring & Classification)
1. **Scoring location:** Sparse in Notion pages. Also in page comments, messaging apps, email, verbal. "Record keeping needs to improve in the firm."
2. **EO decoded:** EO = Experienced Operator. Plus revealed full EF/EO/FF classification (see above). This is the most significant new mental model discovered since the DeVC Relationship archetypes.
3. **Conversation Prep Research:** Built by someone on team. Aakash wants AI leverage eventually but NOT now. **"First priority for Claude is clear and it's all about network priorities and everything flowing from that."**
4. **Deal Status + Pipeline Status:** Confirmed exactly independent. In Strike Zone = thesis fit. Pass Forever = investment decision. Both can coexist.

### Round 13 (Data Sources & Linked DBs)
1. **Score location (expanded):** Notion page comments are a key source — "Look at comments in a company page too sometimes these would be there merged into more notes and views."
2. **EF/EO/FF:** Confirmed as "implicit assessment" — mental model, not a formal field.
3. **Notes DBs:**
   - Portfolio DB = "surely relevant"
   - Portfolio Interaction Notes DB = "could be relevant" (not built by Aakash)
   - Meeting Notes DB = "was built with a vision to map all meetings and meeting notes and tag them to person/company but it didn't take off." Aakash: "Maybe Claude will help realise the vision to its fullest without execution challenges."
4. **The Vault:** SharePoint-based document hub. Organized by sector: `DeVC/Sourcing, Eval & Strategy/Sourcing/Leads/{Sector}/{Company}`. "Eventually Claude would have access to it once I deploy Claude Enterprise."

---

## Updated Evaluation Stack (Revised with Session 005 Findings)

| Layer | People (Network DB) | Companies (Companies DB) |
|---|---|---|
| Identity | Role, Location, Background, Schools | Sector, Funding, Type, Sells To |
| Assessment | RM reflections (++/??, SM/WM), Cash notes, Leverage | JTBD eyes (1PE/2PE/MPE), BRCs (+/?), EF/EO/FF (implicit), Spiky Score, EO/FMF/Thesis/Price |
| Classification | DeVC Relationship (13 archetypes), Collective Flag | Pipeline Status (full funnel), Deal Status (3D matrix), Priority (P0-P2) |
| Value | Folio Franchise, Sourcing Attribution | Smart Money?, Angels, Investors, Known Portfolio |
| Health | R/Y/G, E/E Priority | Tracking cadence (7/30/90/180), Action Due?, Surface to collective |
| Documentation | Inline notes, comments | Meeting notes (two eras), BRC toggles, Vault links, Comments |

---

## Data Fragmentation Map (AI CoS Opportunity Areas)

| Data Type | Current Location(s) | Structured in DB? |
|---|---|---|
| Pipeline Status | Companies DB (Status field) | ✅ Yes |
| Deal Status | Companies DB (Status field) | ✅ Yes |
| JTBD Status | Companies DB (Multi-select) | ✅ Yes |
| DeVC Relationship | Network DB (Select) | ✅ Yes |
| Scoring (Spiky + EO/FMF/Thesis/Price) | Notion page body (template), page comments, messaging apps, email, verbal | ❌ Mostly unstructured |
| BRC Results | Notion page body (toggles), email, WhatsApp | ❌ Partially structured |
| EF/EO/FF Classification | Mental model only | ❌ Not captured |
| Meeting Notes | Notion page body (two formats), Meeting Notes DB (underused) | ⚠️ Partially |
| Portfolio Interactions | Portfolio Interaction Notes DB | ⚠️ Unknown depth |
| Deal Documents | The Vault (SharePoint) | ✅ Organized by sector |
| RM's Assessment (Network) | Inline notes in Network DB | ⚠️ Unstructured text |
| Universal Verdicts (Yes/SM/WM/M/M+/No) | Scattered across notes | ❌ Not captured |

---

## Open Questions (Updated)

### Resolved in This Session
- ✅ What do actual portfolio company pages look like? (Two eras: raw notes pre-Sep 2024, RM template post-Sep 2024)
- ✅ What is the scoring framework? (Spiky Score + EO/FMF/Thesis/Price out of 40)
- ✅ What does EO mean? (Experienced Operator — part of EF/EO/FF classification)
- ✅ Are Deal Status and Pipeline Status independent? (Yes, confirmed with real data)
- ✅ Where is scoring data? (Scattered: Notion pages/comments, messaging, email, verbal)
- ✅ What is Conversation Prep Research? (Auto-generated meeting prep, built by team member)
- ✅ What are the Notes DBs? (Meeting Notes DB = underused vision; Portfolio Interaction Notes DB = relevant but unclear)
- ✅ What is The Vault? (SharePoint doc hub, organized by sector)

### Still Open
1. **Notion page comments** — Need to examine actual comments on company pages (Aakash said scoring lives there too)
2. **Portfolio DB** — Aakash confirmed "surely relevant" but unexplored
3. **Portfolio Interaction Notes DB** — "Could be relevant" (not built by Aakash)
4. **Finance DB** (`9b59fd98`) — What does it track?
5. **Corp Dev DB** (`59c31a93`) — What does it track?
6. **Pending Tasks DB** (`1b829bcc`) — Is this active? How used?
7. **Full deal flow walk-through** — Trace one company from pipe to portfolio through both DBs
8. **Total record counts** in Network DB and Companies DB
9. **"Anti Folio" Pipeline Status** — What makes a company anti-folio?
10. **"Surface to collective" date field** — What triggers surfacing? Manual or automated?
11. **HIL Review process** — What is "To Review" vs "Reviewed"?
12. **Formulas** — How do AIF/USA, Money In, Ownership % calculate?
13. **Meeting Notes DB schema** — What fields does it have? How was it envisioned?
14. **The EO 10-point scoring dimensions** — What specific sub-dimensions make up the EO score?

---

## Cumulative Progress (Sessions 001-005)

| Dimension | Status |
|---|---|
| Network DB schema (40+ fields) | ✅ Fully mapped |
| Companies DB schema (49 fields) | ✅ Fully mapped |
| All 13 DeVC Relationship archetypes | ✅ Fully decoded |
| Deal Status 3D matrix | ✅ Decoded (Speed × Timing × Pull) |
| JTBD "Pair of Eyes" model | ✅ Decoded |
| BRC process | ✅ Documented |
| Scoring framework | ✅ Discovered (Spiky + EO/FMF/Thesis/Price) |
| Founder classification (EF/EO/FF) | ✅ Decoded (implicit mental model) |
| Page format eras | ✅ Identified (pre vs post Sep 2024) |
| Data fragmentation map | ✅ Initial mapping complete |
| Linked DBs explored | ⚠️ 0 of 5+ explored |
| Record-level examination | ⚠️ 8 Companies, ~29 Network examined |
| Total record counts | ❌ Unknown |
| Real deal end-to-end trace | ❌ Not yet done |
| Notion page comments | ❌ Not yet examined |
| Formal taxonomy model | ❌ Not yet started |
| Interview rounds completed | 13 total (Rounds 1-7 Network, 8-11 Companies schema, 12-13 scoring & classification) |

---

## Next Steps

1. **Examine Notion page comments** on company pages — Aakash flagged this as a scoring data source
2. **Explore Portfolio DB** — Aakash confirmed "surely relevant"
3. **Count total records** in both primary DBs
4. **Explore remaining linked DBs** — Finance, Corp Dev, Portfolio Interaction Notes, Pending Tasks, Meeting Notes
5. **Trace a real deal end-to-end** through both DBs
6. **Ask about remaining unknowns** — Anti Folio, Surface to collective, HIL Review, EO scoring dimensions
7. **Begin drafting formal taxonomy model** — sufficient data now exists for initial synthesis
