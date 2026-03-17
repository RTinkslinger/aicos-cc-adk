# Session 002: DeVC Notion Network DB Exploration

**Date:** March 1, 2026
**Interface:** Cowork
**Phase:** Understanding (Step 1 — Explore the Notion Network DB)

---

## What Was Explored

Connected to Aakash's Notion workspace and studied three databases:

1. **Network DB** (collection `6462102f`) — the primary people database
2. **Companies DB** (collection `1edda9cc`) — the companies/deal pipeline database
3. **DeVC DeepTech Network** (collection `2b929bcc`) — a specialized subset (deprioritized per Aakash; maintained by a team member, not core to this project)

Fetched and analyzed schema for both primary DBs. Examined 5 individual records in depth: Miten Sampat (DeVC Core IC), Revant Bhate (DeVC Core power node), Vishesh Rajaram (DeVC Core, VC Partner), Amit Gupta (DeVC Ext, angel/deep tech), Kevin Chang (Comm Target, micro VC GP), Sanchie Shroff (Ext Target, VC Partner with future founder potential).

---

## Network DB Schema Summary

~40 fields across these categories:

### Identity & Location
- Name, LinkedIn, Home Base (multi-select: Bangalore, NCR, Mumbai, Bay Area, etc.), Current Role (select with ~40 role types), Current Co (relation to Companies DB)

### DeVC Relationship Classification
- **DeVC Relationship** (multi-select, 13 values): DeVC Core, Core Target, DeVC Ext, Ext Target, DeVC Community, Comm Target, DeVC LP, LP Target, Tier 1 VC, Micro VC, MPI IP, Founder, Met
- **Collective Flag** (multi-select): Solo GP, Micro VC GP, Founder Angel, Operator Angel, LP cheque candidate
- **Investorship** (multi-select): Syndicate, VC, Occassional, Super Angel, Freq Angel

Per Aakash: Collective Flag = their structural role in the DeVC collective. Investorship = their investing behavior/style generally. Both are actively used and serve different purposes.

### Engagement & Health
- **E/E Priority** (select: P0🔥, P1, P2, P3) — temporal engagement priority; moves up and down over time
- **R/Y/G** (select: Red, Yellow, Green, Unclear) — relationship health indicator
- **Sourcing/Flow/HOTS** (select: High, Med, Low, Na) — deal sourcing activity level
- **Investing Activity** (select: High, Med, Low, Na) — how actively they're investing

### Portfolio Context
- **In Folio Of** (multi-select): MPI, Cash, NA, DeVC Core, DeVC, Titan, DeVC Ext — whose portfolio they're connected to
- **Angel Folio** — relation to Companies DB (companies they've angel invested in)
- **Folio Franchise** (multi-select, ~20 values): sector coverage areas
- **Operating Franchise** (multi-select, ~30 values): sector operating experience

### Deal Attribution (all relations)
- **Sourcing Attribution** — who sourced deals via this person
- **Participation Attribution** — deals they participated in
- **Led by?** — deals they led
- **Piped to DeVC** — companies they piped to DeVC

### Other
- **Customer For** (multi-select) — B2B product categories they buy
- **SaaS Buyer Type** — SMB, Mid Market, Enterprise
- **Prev Foundership** — past founder experience classification
- **Big Events Invite**, **C+E Speaker**, **C+E Attendance** — event engagement
- **Meeting Notes**, **Tasks Pending**, **Network Tasks?** — linked relations

---

## Companies DB Schema Summary

~50+ fields. Key categories:

### Pipeline & Deal Status
- **Pipeline Status** — full funnel with 20+ stages from Screen through Portfolio/Pass
- **Deal Status** — parallel deal tracking with speed/timing dimensions (e.g., "Likely Fast | Early | High")
- **Deal Status @ Discovery** — initial classification at first contact
- **JTBD** (Jobs To Be Done) — diligence stage tracking: 1PE/2PE/MPE/BRCs/DE

### Financial
- Venture Funding stage, Last Round $M, Money Committed, Last Round Timing

### Sector
- **Sector** (select, 7 values): SaaS, B2B, Consumer, Financial Services, Frontier, VC, Financial Services (duplicate?)
- **Sector Tags** (multi-select, 150+ granular tags)

### People Relations (all linking to Network DB)
- Current People, MPI Connect, Angels, Piped From, Alums, Domain Eval?, Shared with

### Other
- Batch (YC, SPC, Localhost, Lossfunk, EF), Founding Timeline, Type, HIL Review

---

## Key Discoveries

### 1. The Verdict Taxonomy (CRITICAL — not in any DB field)
Aakash's org uses a universal assessment language for evaluating people and opportunities:
**Yes / Strong Maybe / Maybe+ / Maybe / Weak Maybe / No**

This appears extensively in meeting notes (e.g., "WM for LP cheque", "SM for Collective Core") but is NOT captured in any structured field. This is arguably the most important signal in the system and it's entirely unstructured.

### 2. Multi-Hat People Are the Norm (30-50 "power nodes")
Aakash estimates 30-50 people in his network are deeply multi-dimensional — simultaneously portfolio founders, ICs, deal flow sources, potential LPs, etc. The current DB structure handles this through multiple fields (DeVC Relationship + Collective Flag + Investorship + In Folio Of) but the relationships between these dimensions aren't explicitly modeled.

Example: **Revant Bhate** — DeVC Core, Co-Founder CEO, In Folio Of (Cash + MPI), High Investing Activity, High Sourcing, 12 Angel Folio entries, multiple Sourcing/Participation attributions.

### 3. Relationships Are Trajectories, Not Snapshots
When asked about Sanchie Shroff (who spans VC Partner, potential founder, deal source, potential IC), Aakash said: "She's a relationship to develop." This suggests the taxonomy needs a temporal/trajectory dimension — people aren't just what they are today, but what they're becoming.

### 4. Meeting Notes Are the Richest Signal Source (but scattered)
- Some records have detailed inline notes with RM reflections, prep notes, action items, AI-generated summaries, and full transcripts (e.g., Amit Gupta, Kevin Chang, Sanchie Shroff)
- Some records are blank pages with only structured properties (e.g., Miten Sampat, Revant Bhate)
- Meeting notes live across: inline in Network DB pages, a linked Meeting Notes DB, Granola, and sometimes nowhere
- Per Aakash: "It's scattered everywhere"

### 5. The DeVC Relationship Field Is Partially Maintained
The 13-value DeVC Relationship field was the closest thing to a relationship taxonomy, but it has drifted. Some values are current, others outdated. This confirms the hypothesis that we need to derive a new taxonomy from real data rather than rely on existing fields.

### 6. RM (Rahul Mathur) Is a Key Data Author
Many of the richest records have "RM reflections" and "RM notes" — Rahul Mathur appears to be the primary person writing relationship assessments and meeting notes in the Network DB. Understanding his notation style is important for any AI system that needs to parse this data.

### 7. "Cash" = Aakash's Internal Shorthand
In the "In Folio Of" field, "Cash" refers to Aakash himself. Similarly, "MPI" = Matrix Partners India (now Z47). "RM" = Rahul Mathur.

---

## Emerging Taxonomy Observations

The preliminary 11-category taxonomy from Session 001 maps roughly but imperfectly to the existing data:

| Preliminary Category | Existing DB Representation | Notes |
|---|---|---|
| Angel portfolio founders | Angel Folio relation + Prev Foundership | Partially captured |
| DeVC portfolio founders | Pipeline Status = Portfolio | Well-captured in Companies DB |
| Z47 portfolio founders | In Folio Of = MPI | Captured but Z47 branding may differ |
| Prospective founders | Pipeline Status stages | Well-captured in Companies DB |
| Beyond-strike-zone founders | Pipeline Status = Pass variants? | Unclear mapping |
| Future founders | NOT in any field | Lives in meeting notes only (e.g., Sanchie) |
| Founder-angels (potential ICs) | Collective Flag + Investorship | Partially captured |
| Independent Capitalists | DeVC Relationship = DeVC Core/Ext + Collective Flag | Well-captured |
| Other VCs | DeVC Relationship = Tier 1 VC + Current Role = VC Partner | Partially captured |
| LPs | DeVC Relationship = DeVC LP / LP Target | Captured |
| Operators/executives | Current Role field | Weakly captured — no explicit "hiring network" tag |

**Missing from the DB entirely:**
- The trajectory/development dimension (what someone is becoming)
- The verdict assessment (Yes/SM/M+/M/WM/No)
- Interaction recency and frequency
- Follow-up obligations and their status
- The "why this person matters" narrative

---

## Open Questions for Next Session

1. How many total records are in the Network DB? (Couldn't get a count via current tools)
2. What does the "Engagement Playbook" field (Programmatic Dealflow, Solo Capitalist) mean?
3. What's the "Local Network" field used for in practice?
4. How do "Schools" relations work — is this tracking educational institution connections?
5. Who else on the team (besides RM) writes notes in the Network DB?
6. What's the relationship between the Network DB's "Meeting Notes" relation and Granola?
7. What are "C+E" events? (Community + Engagement? Content + Events?)
8. The "Leverage" field (Coverage, Evaluation, Underwriting) — is this how ICs help DeVC, or how DeVC helps them?

---

## Next Steps

1. **Get total record count** for Network DB and Companies DB
2. **Sample 20-30 diverse records** across all DeVC Relationship categories for case-by-case breakdowns
3. **Deep-dive on the verdict taxonomy** — can we find all instances of Yes/SM/M+/M/WM/No in meeting notes?
4. **Map the meeting notes landscape** — which records have notes, which are bare, where does Granola fit?
5. **Interview Aakash** on 5-10 specific people to understand the mental model behind classification decisions
