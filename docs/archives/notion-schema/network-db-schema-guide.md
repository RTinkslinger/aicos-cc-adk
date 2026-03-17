# Network DB — Schema Guide & Agent Context Model

> **Purpose:** This document is the definitive reference for any AI agent (Claude, custom Agent SDK, enrichment pipelines) working with Aakash Kumar's Network DB in Notion. It captures not just column names and types, but the *semantic meaning*, *business intent*, and *query patterns* for each field — learned through direct interview with Aakash (Session 040, March 2026).

> **Notion Data Source ID:** `6462102f-112b-40e9-8984-7cb1e8fe5e8b`
> **Parent Database URL:** `https://www.notion.so/d5f52503f23447b09701d9b354af9d1a`
> **Default View URL:** `view://2638c865-9881-4b0a-80e1-63e2c78dff18`
> **Total Columns:** 44 (41 in schema + 3 view-only: Batch, Company Stage, Sector Classification)
> **Richest Entry (benchmark):** Abhishek Goyal — 27/40 fields populated

---

## What This DB Represents

The Network DB is the **people universe** for Aakash's investing practice across Z47 ($550M AUM) and DeVC ($60M, India's first decentralized VC). Every person Aakash and the team interact with — founders, angels, VCs, operators, LPs, advisors — lives here. It is the relational backbone connecting to Companies DB, Portfolio DB, Tasks Tracker, and Events DBs.

**Who populates it:** Multiple people across Z47 and DeVC teams. Should also be enriched from external sources (LinkedIn, Tracxn, Crunchbase). Today it is sparsely populated in many fields — the aspiration is continuous enrichment.

**13 Conceptual Archetypes** (from CONTEXT.md — not a single column today, distributed across fields):
Founder, DF (Domain Fighter), CXO, Operator, Angel, Collective Member, LP, Academic, Journalist, Government, Advisor, EXT Target, Other.
> ⚠️ **Gap:** No single "Archetype" column exists. Collective Flag covers 5 archetypes. The rest are inferred from combinations of Current Role, Investorship, DeVC Relationship, and Prev Foundership. A dedicated Archetype field would simplify querying.

---

## Column Reference (Grouped by Semantic Domain)

### A. Identity & Basic Info

| Column | Type | Values/Format | Semantic Meaning | Query Patterns |
|--------|------|---------------|------------------|----------------|
| **Name** | Title (text) | Full name | Person's name. No special conventions. | Exact match, contains search |
| **Linkedin** | URL (text) | LinkedIn profile URL | **Primary unique identifier** for a person across databases. Notion `url` is canonical within Notion only. | Dedup key, enrichment join key |
| **Current Role** | Select | ~40 values: Founder CEO, CTO, VC Partner, Angel Investor, etc. | Role at their current company. For pure investors (e.g., "Angel Investor"), there may be no associated company — this is their LinkedIn job title. | Filter by role type. "Angel Investor" ≠ has a company. |
| **Current Co** | Relation → Companies DB | Page URLs (multi-value) | Current company/companies. Multi-value because some people hold multiple roles. Can include "stealth", "family office" etc. from enrichment that aren't real Companies DB entries. **Should be populated but often isn't.** | Join to Companies DB for company details. Handle null gracefully. |
| **Past Cos** | Relation → Companies DB | Page URLs (multi-value) | Notable/meaningful past companies. Not exhaustive career history — just the ones worth tracking. More populated = better. | Career pattern analysis, shared-company graph |
| **Home Base** | Multi-select | Bangalore, NCR, Mumbai, Bay Area, East Coast, Singapore, Chennai, Pune, etc. | Prominent locations where they operate. Multi-select for people who split time across cities. | Trip planning ("who's in Bay Area"), geo clustering |
| **Local Network** | Multi-select | India, US, NA | **Firm-level classification** — which Z47/DeVC geographic team manages this relationship. NOT where the person lives (that's Home Base). | Team routing, regional pipeline views |
| **Schools** | Relation → Companies DB | Page URLs | Educational institutions attended. Schools are stored as entities in Companies DB (two-DB data model). | Alumni network queries, pattern matching |

### B. Investor Profile & Activity

| Column | Type | Values/Format | Semantic Meaning | Query Patterns |
|--------|------|---------------|------------------|----------------|
| **Investorship** | Multi-select | Syndicate, VC, Occasional, Super Angel, Freq Angel, Na | Classifies their investing style/frequency. A person can be both a founder AND a Super Angel. **Syndicate** = runs a syndicate. **VC** = has an institutional fund. **Occasional** = sometimes invests individually. **Super Angel** = invests a lot. **Freq Angel** = pretty frequent. | "Show me all super angels" "Who runs syndicates" |
| **Investing Activity** | Select | High, Med, Low, Na | **Recent** view of investing frequency. Gauged from interactions with them, interactions with founders they've backed, personal knowledge. More dynamic than Investorship. | "Who's actively deploying right now" |
| **Angel Folio** | Relation → Companies DB | Page URLs (multi-value) | Companies this person has angel-invested in. **Sparsely populated** — no single source of truth. Updated opportunistically through interactions and triage. | Co-investment pattern analysis, portfolio overlap |
| **In Folio Of** | Multi-select | MPI, Cash, NA, DeVC Core, DeVC, DeVC Ext | **Who has backed this person** when they were a founder. MPI = Z47 (legacy name). Cash = Aakash personally (angel investments). DeVC Core/Ext = backed by someone in the DeVC collective. **Not about co-investing — about being a portfolio founder.** | "Show me founders we've backed" "Who in network is a Z47 portfolio founder" |
| **Folio Franchise** | Multi-select | India Consumer, B2B Comm, SaaS, AI, Commerce, Health, Fintech, Climate, Defense🛡️, Aerospace✈️, etc. | Sectors they are **known for investing in** and have high pull with founders — i.e., founders actively want them on cap table. Investor reputation by domain. | "Who's the go-to angel for fintech deals" "Sector-matched co-investor search" |
| **Prev Foundership** | Multi-select | Active Founder 5M+, Past Founder 5M+, Past 0 to 1, Exited Founder, Active Early Stage, NA | Captures founder history. **5M+** = raised more than $5M in that venture. **Past 0 to 1** = built something early-stage that likely didn't scale. **Exited Founder** = sold/exited a company. **Active Early Stage** = currently an early-stage founder. | "Exited founders who are now angels" "Active founders raising 5M+" |
| **Operating Franchise** | Multi-select | Consumer, Commerce, SaaS, DeepTech, Health, Fintech, Creator, B2B Comm, Consumer Tech, etc. | Sectors they know how to **build and operate** in. Their builder/operator expertise. **Different from Folio Franchise** (investing reputation). Someone might operate in SaaS but invest in Consumer. | "Who can advise our portfolio company on SaaS ops" |

### C. Relationship & Engagement Classification

| Column | Type | Values/Format | Semantic Meaning | Query Patterns |
|--------|------|---------------|------------------|----------------|
| **R/Y/G** | Select | Red, Yellow, Green, Unclear | Relationship health and warmth of connection **as a firm** (across Z47 and DeVC, primarily DeVC). Green = strong, active. Yellow = warm but could be better. Red = cold/strained. | "Who's gone Red that we should re-engage" "Green relationships in Bay Area" |
| **E/E Priority** | Select | P0🔥, P1, P2, P3 | **Engagement & Escalation priority.** Drives how urgently the team should engage to **move R/Y/G upward**. High priority = this person is high-value as a DeVC collective member or as a backable founder, and we need more engagement. | "P0 people I haven't met this month" Action scoring input |
| **DeVC Relationship** | Multi-select | DeVC Core, Core Target, DeVC Ext, Ext Target, DeVC Community, Comm Target, DeVC LP, LP Target, NA, Tier 1 VC, Micro VC, MPI IP, Founder, Met | Position in the **DeVC ecosystem funnel**. Community → Ext → Core are funnel stages (wider → deeper entrenchment in collaborative investing). **Target** suffix = aspiration, not current state. **MPI IP** = investment professionals at Z47. **Founder** = a founder engaged with but not in any DeVC tier. **Met** = single interaction only. | "Core members in Bangalore" "Ext Targets to convert" Funnel conversion tracking |
| **DeVC POC** | People (user IDs) | Notion user references | Primary **point of contact** on the DeVC team for this person. | "Who owns this relationship" Team workload balancing |
| **Engagement Playbook** | Multi-select | Programmatic Dealflow, Solo Capitalist | **How** to engage this person. **Programmatic Dealflow** = share continuously curated investment opportunities with them. **Solo Capitalist** = they have a meaningful portfolio, engage with depth/thesis-level discussions. | Engagement strategy routing |
| **Collective Flag** | Multi-select | Solo GP, Micro VC GP, Founder Angel, Operator Angel, LP cheque candidate | Their **archetype within the DeVC Collective** model. Captures what kind of participant they are. Covers 5 of the 13 conceptual archetypes. | "All Founder Angels" Collective composition analysis |

### D. Value & Attribution Tracking

| Column | Type | Values/Format | Semantic Meaning | Query Patterns |
|--------|------|---------------|------------------|----------------|
| **Leverage** | Multi-select | Evaluation, Coverage, Underwriting | What value they bring to the deal process. **Coverage** = additive dealflow. **Evaluation** = strong at evaluating opportunities. **Underwriting** = sound investment decisions with risk/reward thinking. (Schema-only — may not appear in all views. Possibly sparse.) | "Who can help evaluate this deal" Matching people to deal stages |
| **Sourcing Attribution** | Relation → Portfolio DB | Page URLs | Which portfolio companies this person **sourced/referred** to you. Tracks the referral. | Attribution analysis, "who's our best sourcer" |
| **Participation Attribution** | Relation → Portfolio DB | Page URLs | Which portfolio deals this person **co-invested in**. | Co-investment network, "who participates most" |
| **Led by?** | Relation → Portfolio DB | Page URLs | Which DeVC portfolio companies this person **led the investment in** and pulled DeVC into. Stronger than sourcing — they led and invited. | "Who's led deals for us" Lead investor relationships |
| **Sourcing/Flow/HOTS** | Select | High, Med, Low, Na | Rates the **method and quality of their information access**. **Sourcing** = actively sources deals. **Flow** = has high inbound dealflow. **HOTS** = "Heard On The Street" — good view of what's happening, in the flow of information. High/Med/Low rates the quality regardless of method. | "High-quality information sources" Intelligence network mapping |
| **Customer For** | Multi-select | Ad-tech, Mar-tech, Commerce Enablement, AI Infra, Lo/No Code, Dev Tools, Data Stack, Productivity, B2B Comm, Biz Apps, NA | This person (or their company) could be a **customer/buyer** for companies in these SaaS categories. Demand-side tag. | "Who could be a customer for our AI Infra portfolio company" GTM support for portfolio |
| **Piped to DeVC** | Relation → Companies DB | Page URLs | Companies this person has **referred into the DeVC pipeline**. | Pipeline attribution, "who feeds our funnel" |

### E. Events, Content & Relationship Touchpoints

| Column | Type | Values/Format | Semantic Meaning | Query Patterns |
|--------|------|---------------|------------------|----------------|
| **Big Events Invite** | Checkbox-style | ["Yes"] or empty | Should this person be on the **shortlist/guestlist** for big events (LP meets, DeVC summits, Z47 portfolio events). Forward-looking intent, not historical. | Event invite list generation |
| **C+E Speaker** | Relation → Events DB | Page URLs | Events where this person has been a **speaker** (C+E = Content & Events). | "Who's spoken at our events" Speaker sourcing |
| **C+E Attendance** | Relation → Events DB | Page URLs | Events this person has **attended** (not as speaker). | Event engagement tracking |
| **Meeting Notes** | Relation → Meeting Notes DB | Page URLs | Links to meeting notes entries. DB exists and is relevant — should persist as the place where all meeting notes (links to files or CRM entries) are stored. | Meeting history lookup |
| **Tasks Pending** | Relation → Tasks Tracker | Page URLs | **Open action items** related to this person. This is the singular column for capturing all tasks with a person. | "What do I owe this person" "Open items with P0 contacts" |
| **Network Tasks?** | Relation → separate tracker | Page URLs | **Deprecated/ignore.** Linked to a point-in-time list. Tasks Pending should be the single source. | — |
| **Unstructured Leads** | Relation → separate DB | Page URLs | **Legacy field.** Was for cases without a company name. Now handled in Companies DB as "XYZ's new company" placeholders. Long-term solve TBD. | — |

### F. Sector & Market Classification

| Column | Type | Values/Format | Semantic Meaning | Query Patterns |
|--------|------|---------------|------------------|----------------|
| **Sector Classification** | Select/Text | Sector labels | Classification of their **current company's** sector. View-only column (not in base schema — may be a formula or linked property). | Company sector filtering |
| **Company Stage** | Select/Text | Stage labels | Stage of their **current company** (seed, Series A, growth, etc.). View-only column. | "Founders at Series A companies" |
| **Batch** | Text | e.g., "YCS25", "SPC US" | Accelerator/incubator cohort they were part of. Tracks membership in programs like YC, SPC, etc. View-only column. | "YC founders in network" Cohort-based outreach |
| **SaaS Buyer Type** | Multi-select | SMB, Mid Market, Enterprise, NA | How their current company would be classified **from the lens of a SaaS seller** — what market segment do they represent as a buyer. | GTM targeting, "Enterprise buyers in our network" |
| **YC Partner Portfolio** | Relation → Companies DB | Page URLs | For people who attended YC: which **YC partner** they were in the portfolio of. Only relevant for YC alumni. | YC partner relationship mapping |

### G. System & Deprecated Fields

| Column | Type | Semantic Meaning | Status |
|--------|------|------------------|--------|
| **url** | System | Notion page URL. Canonical ID within Notion. | Active (system) |
| **createdTime** | System | When page was created. | System-generated, not actively used |
| **Last edited time** | System | Last modification timestamp. | System-generated, not actively used. Potential for staleness detection. |
| **Venture Partner? (old)** | Relation → Portfolio DB | **Deprecated.** Original purpose unclear. Ignore. | Deprecated |
| **Network Tasks?** | Relation | **Deprecated.** Use Tasks Pending instead. | Deprecated |

---

## Natural Language → Query Translation Guide

This section helps agents translate human questions into the right column filters.

### People Discovery Queries

| Natural Language | Columns to Query | Logic |
|-----------------|------------------|-------|
| "Who should I meet in Bay Area?" | Home Base = "Bay Area", E/E Priority, R/Y/G | Filter by location, sort by priority |
| "Show me all super angels" | Investorship contains "Super Angel" | Direct multi-select filter |
| "Founders we've backed" | In Folio Of contains any of [MPI, Cash, DeVC Core, DeVC, DeVC Ext] | Multi-select filter |
| "Who's gone cold?" | R/Y/G = "Red" OR R/Y/G = "Unclear" | Select filter |
| "DeVC Core members in India" | DeVC Relationship contains "DeVC Core", Local Network contains "India" | Compound filter |
| "People from YC" | Batch contains "YC" | Text search |
| "Who can help evaluate AI deals?" | Leverage contains "Evaluation", Folio Franchise contains "AI" | Compound filter |
| "Active founders raising money" | Prev Foundership contains "Active Founder 5M+" OR "Active Early Stage" | Multi-select filter |
| "Who has good dealflow?" | Sourcing/Flow/HOTS = "High" | Select filter |
| "Exited founders now angel investing" | Prev Foundership contains "Exited Founder", Investorship contains any angel type | Compound filter |

### Attribution & Value Queries

| Natural Language | Columns to Query | Logic |
|-----------------|------------------|-------|
| "Who sourced the most deals?" | Sourcing Attribution (count relations) | Aggregate by person |
| "Who leads deals for us?" | Led by? (non-empty) | Filter for populated field |
| "Who's a customer for our dev tools company?" | Customer For contains "Dev Tools" | Multi-select filter |
| "Who's referred companies to DeVC?" | Piped to DeVC (non-empty) | Filter for populated field |

### Engagement & Action Queries

| Natural Language | Columns to Query | Logic |
|-----------------|------------------|-------|
| "P0 people I haven't engaged recently" | E/E Priority = "P0🔥", Last edited time < threshold | Priority + staleness |
| "Who should we invite to the summit?" | Big Events Invite = ["Yes"] | Checkbox filter |
| "Open tasks with network contacts" | Tasks Pending (non-empty) | Filter for populated relation |
| "Who owns the relationship with X?" | DeVC POC | People field lookup |

---

## Enrichment Guide

Fields most amenable to automated enrichment from external sources:

| Field | Source | Method |
|-------|--------|--------|
| Linkedin | Manual / Scraping | Primary key — populate first |
| Current Role | LinkedIn API / Enrichment service | Profile headline parsing |
| Current Co | LinkedIn / Tracxn / Crunchbase | Current experience section |
| Past Cos | LinkedIn | Past experience (notable only) |
| Home Base | LinkedIn location | Geo parsing |
| Schools | LinkedIn education | Education section |
| Angel Folio | Crunchbase / Tracxn | Investment history |
| Batch | Crunchbase / YC directory | Accelerator listings |
| Company Stage | Tracxn / Crunchbase | Funding stage data |
| Sector Classification | Tracxn / Crunchbase | Company classification |

Fields that **must be human-populated** (subjective/relational):
R/Y/G, E/E Priority, DeVC Relationship, Collective Flag, Engagement Playbook, Leverage, Sourcing/Flow/HOTS, Customer For, Folio Franchise, Operating Franchise, In Folio Of, Investorship, Investing Activity, Local Network, Big Events Invite.

---

## Schema Gaps & Recommendations

1. **No "Archetype" column** — 13 archetypes exist conceptually but are scattered across Collective Flag, Current Role, Investorship, and DeVC Relationship. A dedicated Archetype select field would simplify querying.
2. **Email / Phone missing** — No contact info columns. Important for enrichment pipelines and direct outreach.
3. **Last Interaction Date missing** — System timestamps don't capture this. A "Last Meaningful Interaction" date would power staleness detection and "who am I underweighting?" analysis.
4. **Venture Partner? (old) and Network Tasks?** — Deprecated. Can be hidden/removed to reduce clutter.
5. **Unstructured Leads** — Legacy workaround. Long-term: evaluate if a "placeholder company" pattern in Companies DB is sufficient, or if a lightweight "pre-company" entity is needed.
6. **Leverage field** — May be duplicate or underused. Verify if actively populated; if not, consolidate with another field or deprecate.

---

## Cross-DB Relations Map

```
Network DB (People)
├── Current Co ──────→ Companies DB
├── Past Cos ────────→ Companies DB
├── Schools ─────────→ Companies DB (institutions as entities)
├── Angel Folio ─────→ Companies DB
├── Piped to DeVC ───→ Companies DB
├── YC Partner Portfolio → Companies DB
├── Led by? ─────────→ Portfolio DB
├── Participation Attribution → Portfolio DB
├── Sourcing Attribution → Portfolio DB
├── In Folio Of ─────→ (multi-select, not relation)
├── Meeting Notes ───→ Meeting Notes DB
├── Tasks Pending ───→ Tasks Tracker
├── C+E Speaker ─────→ Events DB
├── C+E Attendance ──→ Events DB
└── Unstructured Leads → Legacy DB (deprecated)
```

---

*Generated: Session 040, March 5, 2026*
*Source: Direct interview with Aakash Kumar + Notion schema extraction*
*Version: 1.0*
