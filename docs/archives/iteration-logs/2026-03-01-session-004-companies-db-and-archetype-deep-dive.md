# Session 004: Companies DB Schema & Full Archetype Deep-Dive

**Date:** March 1, 2026
**Interface:** Cowork (continuation from Session 003)
**Phase:** Understanding (Steps 1–3 — Deep Schema Exploration, Companies DB Analysis, Full Archetype Interview)

---

## Summary

Completed full exploration of the Companies DB schema (49 fields) and conducted 4 additional interview rounds (Rounds 8-11) with Aakash. All 13 DeVC Relationship archetypes are now decoded. Major discoveries about the Deal Status 3D matrix, the BRC (Blind Reference Check) process, the "pair of eyes" evaluation model, and the strategic importance of school alumni networks for deal flow capture.

---

## Companies DB Schema Analysis (49 fields)

### Field Distribution by Type
| Type | Count | Key Fields |
|---|---|---|
| Relation | 17 | Biggest category — links to Network DB (8), self-referencing (2), and other DBs (7) |
| Select | 8 | Including Pipeline Status groups, Deal Status, Sector, Smart Money, etc. |
| Multi-select | 4 | JTBD, Batch, Sector Tags (~150 values), Sells To |
| Status | 3 | Pipeline Status, Deal Status, Deal Status @ Discovery |
| Formula | 3 | AIF/USA, Money In, Ownership % |
| Rollup | 3 | AIF/USA, Money In, Ownership % (rollup versions) |
| URL | 3 | Website, Vault Link, Deck if link |
| Number | 2 | Last Round $M, Money Committed |
| Date | 2 | Action Due?, Surface to collective |
| Other | 4 | Created by, Last edited time, Name (title), DeVC IP POC (person) |

### Key Structural Fields

#### Pipeline Status (Full Deal Funnel)
```
[TO_DO]          Screen → Mining → NA
[IN_PROGRESS]    Passive Screening → Active Screening → Evaluating →
                 Parked → Tracking_7 → Tracking_30 → Tracking_90 → Tracking_180 →
                 To Pass → To Win and Close
[COMPLETE]       Won & Closing → Portfolio | Pass variants → Lost → Anti Folio →
                 Acquired/Shut Down/Defunct
```

**Pass variants:** Pass | Surface | Top Up, Passed Last Track For Next, Pass Forever, Process Miss, Missed without screen, Struggling to Win, Lost, Anti Folio

#### Deal Status (3-Dimensional Matrix) — DECODED
Three independent dimensions encoded in status values:

1. **Speed** = How likely the round will close
   - `Likely Fast` = Round closing quickly
   - `Slow` = Round taking time
   - `Forming` = Round still forming
   - `Muted` = Limited activity

2. **Timing** = When in the deal lifecycle DeVC got plugged in
   - `Early` = Got in early in the round process
   - `Late` = Got plugged in later

3. **Pull** = DeVC's ability to win allocation in a competitive scenario (NOT conviction)
   - `High` = Strong pull for allocation
   - `Med` = Moderate pull
   - `Low` = Weak pull

This creates a 3D matrix: `Speed | Timing | Pull` → e.g., "Likely Fast | Early | High" = fast-closing round, got in early, strong allocation pull.

Plus special statuses:
- `DeVC Concept Prospect` = Very early, pre-round stage
- `DeVC Lean In Prospect` = Leaning in before round forms
- `DeVC forming round` = DeVC actively forming the round
- `In Strike Zone` = In DeVC's sweet spot
- `Closing + Option` / `Closing + Late` = Final closing stages
- `Portfolio` = Done, in portfolio

#### JTBD — "Pair of Eyes" Evaluation Process (CRITICAL)
The mental model is about how many independent evaluations a deal has received:

| Stage | Meaning |
|---|---|
| 1PE | One Pair of Eyes — single evaluator has assessed |
| 2PE | Two Pairs of Eyes — second independent evaluation |
| MPE | Multiple Pairs of Eyes — broader team assessment |
| BRCs | Blind Reference Checks — network-sourced founder assessment |
| DE | Deal Execution (may have been added by team, Aakash uncertain) |

Each has Pending/Done states. **Key insight:** This is NOT a sequential pipeline — it's a checklist of jobs to be done. A deal might need 2PE before BRCs, or MPE and BRCs simultaneously.

#### BRC Process (Critical Network↔Companies Intersection)
**Blind Reference Check = talking to people the founder has worked with in the past**

Process:
1. Identify companies a founder has been at
2. Search the Network DB for connections to those companies
3. Leverage those connections to reach people who've seen the founder in action
4. Capture signals about: strengths, weaknesses, decision-making style, how they work with people, execution patterns

**Example from Aakash:** "A founder could be at company X in past, and that company is in the angel portfolio of Revant. I can ping Revant to help me get a BRC from the founder of that company or connect to the relevant person."

**Key finding:** BRC results are often scattered in communication tools (email, WhatsApp) — not captured in the DB. This is a major AI CoS opportunity.

### Relations Between Companies DB and Network DB (8 links)

| Field | Direction | Purpose |
|---|---|---|
| Current People | Companies → Network | Who currently works at this company |
| Angels | Companies → Network | Angels who invested in this company |
| Alums | Companies → Network | Former employees now in the network |
| MPI Connect | Companies → Network | Z47/MPI's connections to this company |
| Domain Eval? | Companies → Network | IC/expert who can evaluate the company's domain |
| Piped From | Companies → Network | Who sourced/piped this deal |
| Met by? | Companies → Network | Which GP/team member first met the founder |
| Shared with | Companies → Network | Who the deal has been shared with for evaluation |
| YC Partner | Companies → Network | The YC partner for YC batch companies |
| 🌐 Network DB | Companies → Network | Generic catch-all Network DB link |

### Self-Referencing Relations (Companies → Companies)

| Field | Purpose |
|---|---|
| Investors (VCs, Micros) | Links a company to VC firms that invested in it |
| Known Portfolio | Links a VC firm to its portfolio companies |

**Critical insight:** VC firms are tracked AS companies in the Companies DB. So "Sequoia India" would be a record with Known Portfolio linking to all tracked Sequoia-backed companies. This means the Companies DB is both a deal pipeline AND a market intelligence system.

### Other Notable Fields

| Field | Values | Meaning |
|---|---|---|
| **Smart Money?** | Tier 1, Tier 1.5, Smart Money | Quality of existing investors on cap table |
| **Type** | SMB, Mid Market, Enterprise, VC, Micro VC, Startup | Company classification |
| **Batch** | YC S23-W26, SPC India/USA, Localhost India, Lossfunk 1-6, EF India | Accelerator batch tracking |
| **Sector** | SaaS 💻, B2B 🏢, Consumer 🧑, Financial Services 🏦, Frontier 🚀, VC, Financial Services 💰 | High-level sector |
| **Sector Tags** | ~150 granular tags | Ultra-specific sector classification |
| **Sells To** | Consumers, Brands, Enterprise, SMB, etc. (19 values) | Customer type |
| **Venture Funding** | Pre-Seed through Listed, plus Bootstrapped/Raising/Angels | Funding stage |
| **Priority** | P0🔥, P1, P2 | Deal priority |
| **Surface to collective** | Date field | When to surface the deal to DeVC collective |
| **HIL Review?** | To Review, Reviewed | Human-in-the-Loop review tracking |

---

## Full DeVC Relationship Archetype Breakdown (All 13 Decoded)

### The Core Hierarchy (3 levels)

| Level | Description | Key Behaviors |
|---|---|---|
| **DeVC Core** | Highest trust. Would co-invest even blindly. Deep partnership. Strong pull for portfolio support. | Active co-sourcing, co-evaluation, co-investment. Deep platform engagement. |
| **DeVC Community** | Frequent sourcing and evaluation partners. Not yet at core depth. | Regular deal flow exchange, BRC participation, event attendance. |
| **DeVC Ext** | Extended network. Sporadic sourcing, evaluation, input. | Occasional deal sharing, light-touch relationship. |

### The Funnel Progression (Target = Destination)

| Target Type | Destination | Meaning |
|---|---|---|
| **Core Target** | DeVC Core | Person being cultivated toward Core membership |
| **Comm Target** | DeVC Community | Person being cultivated toward Community membership |
| **Ext Target** | DeVC Ext | Person being cultivated toward Ext membership |

"Target" = the destination this person is being assessed for. Transition is organic/judgment-based — no formal gate.

### VC Classifications (Firm-Level, Not Relationship-Level)

| Category | Definition |
|---|---|
| **Tier 1 VC** | Well-established funds with good-strong brands (Sequoia, Accel, Lightspeed, etc.) |
| **Micro VC** | Smaller funds but still playing for 10%+ ownership at entry. Can do up to $10M cheques. |

**Critical distinction:** These classify the FIRM someone works at. A person at a Tier 1 VC can simultaneously have DeVC Relationship = DeVC Ext (or any other relationship level). The two dimensions are independent.

**Aakash's key insight:** "DeVC's totally collaborative model of small entry ownership allows us to be extremely open architecture and collaborative" — this is WHY DeVC can partner with Tier 1 VCs without competitive tension.

### LP Classifications

| Category | Definition |
|---|---|
| **LP Target** | Person who could potentially become an LP in Z47 or DeVC |
| **DeVC LP** | Person who IS already an LP in an existing DeVC fund |

Dual classification is normal and expected. GPs at other funds are often also LPs — "I am myself a GP at my funds but also an LP in other funds" (Aakash).

### Other Categories

| Category | Definition |
|---|---|
| **MPI IP** | Investment Professional at Matrix Partners India (Z47's former brand). These are team members at Z47. |
| **Founder** | ALL founders in the network, regardless of deal pipeline status. Not limited to active pipeline. |
| **Met** | Catch-all. Anyone who doesn't fit other categories. Entry point for new contacts. |

### Collective Flag vs DeVC Relationship (Confirmed Independent)
- **DeVC Relationship** = Relationship to the DeVC collective/platform (funnel position)
- **Collective Flag** = Structural role within the DeVC collective: Solo GP, Micro VC GP, Founder Angel, Operator Angel, LP cheque candidate

These are separate classification dimensions. A DeVC Core person might be flagged as a Founder Angel in their Collective Flag.

---

## Additional Discoveries

### 1. Schools as Strategic Network-Building Targets
The Schools relation is NOT just for tracking alumni connections — it's strategic:
- Most founders from a school hit up alums who are founders themselves
- Strong alumni affinity creates natural deal flow channels
- DeVC uses this to identify WHERE to focus network build-out to capture school-based deal flow
- **Aakash's example:** "I am from IIT Bombay... and an ex-founder deeply plugged into the IIT B ecosystem. Many founders from IIT B reach out to me for guidance."

This means Schools is a **deal flow capture strategy tool**, not just a contact attribute.

### 2. Engagement Playbook = Investing Style Classification
Values like "Programmatic Dealflow" and "Solo Capitalist" classify how someone engages with the investing ecosystem — their approach to sourcing and investing.

### 3. C+E = Community + Events
The C+E Speaker and C+E Attendance fields track participation in DeVC's Community + Events programming.

### 4. VC Firms as Companies DB Records
VC firms are tracked in the Companies DB with self-referencing relations. This means the Companies DB serves dual purpose:
- **Deal Pipeline:** Tracking companies through sourcing → evaluation → investment
- **Market Intelligence:** Mapping the VC ecosystem, who invested where, portfolio overlaps

### 5. The Deep Interconnection
Aakash confirmed the two DBs are "more interconnected" than two separate dimensions. The relationship between a person and a company isn't just a foreign key — it's a multi-dimensional graph:
- A person can be: Current employee, former alum, angel investor, domain evaluator, deal source, BRC reference, shared evaluator
- A company can be: A startup in pipeline, a VC firm, a portfolio company, a reference company for BRCs

---

## Interview Findings (Rounds 8-11)

### Round 8 (Archetype Deep-Dive)
1. **Tier 1 VC vs Micro VC**: Firm-level classification independent of DeVC Relationship. Tier 1 = established/branded funds. Micro VC = smaller but still 10%+ ownership, up to $10M cheques.
2. **LP tracking**: LP Target = potential LP in Z47 or DeVC. DeVC LP = existing LP. Dual classification normal.
3. **Founder**: ALL founders, not just pipeline. Collective Flag is a separate dimension.
4. **Met**: Catch-all for everyone else.

### Round 9 (Companies DB Deep-Dive)
1. **Deal Status 3D matrix**: Speed × Timing × Pull (not conviction)
2. **Tracking stages**: Cadence-based follow-up windows (7/30/90/180 days)
3. **JTBD decoded**: "Pair of Eyes" model. 1PE/2PE/MPE = evaluation breadth. BRC = Blind Reference Check. DE = Deal Execution (team-added).
4. **Network↔Company links**: Met by? = first GP contact. Domain Eval? = domain expert for assessment.

### Round 10 (BRC & Strategy)
1. **BRC process**: Leverages the network graph to find people who've worked with founders. Results often in email/WhatsApp (not DB).
2. **Smart Money?**: Cap table quality classification (Tier 1 / Tier 1.5 / Smart Money).
3. **VC firms in Companies DB**: Yes, self-referencing. Creates a market map alongside the deal pipeline.
4. **Engagement Playbook**: Investing style classification.

### Round 11 (Integration & Big Picture)
1. **Deal flow confirmed**: Pipe → Screen → Evaluate → Track → Win → Portfolio (with BRCs and multiple eyes throughout)
2. **C+E = Community + Events**
3. **Schools = Strategic deal flow capture** (not just contact metadata)
4. **Network + Companies = deeply interconnected graph** (not two separate tables)

---

## Updated Open Questions

### Resolved in This Session
- ✅ All 13 DeVC Relationship archetypes fully decoded
- ✅ Companies DB full schema analyzed (49 fields)
- ✅ Deal Status 3D matrix explained (Speed × Timing × Pull)
- ✅ JTBD = "Pair of Eyes" evaluation + BRC + Deal Execution
- ✅ BRC process documented
- ✅ Smart Money? = cap table quality
- ✅ Engagement Playbook = investing style
- ✅ C+E = Community + Events
- ✅ Schools = strategic deal flow capture tool
- ✅ VC firms tracked in Companies DB with self-referencing relations

### Still Open
1. **Full deal flow walk-through with a real example** — trace one company from pipe to portfolio through both DBs
2. **How many total records** in Network DB and Companies DB? (Still uncounted)
3. **The Finance DB** (💰 Finance DB relation) — what does it track?
4. **Corp Dev DB** (linked from Companies) — what does it track?
5. **Meeting Notes DB and Portfolio Interaction Notes DB** — how do these relate to inline notes?
6. **Pending Tasks DB** — is this active? How is it used?
7. **"Surface to collective" date field** — what triggers surfacing? Is this manual or automated?
8. **"Anti Folio" Pipeline Status** — what makes a company anti-folio?
9. **How does Pipeline Status interact with Deal Status?** — are they independently set or correlated?

---

## Key Insights for Taxonomy Design

### The Graph Model
The data model is fundamentally a **multi-relational graph**, not two tables:

```
[Person] ←→ [Company]
   ↕              ↕
[Person] ←→ [Company]
```

With edge types including: works-at, invested-in, sourced, evaluated, referenced, shared-with, piped-from, met-by, alumni-of.

### The Three Temporal Dimensions
1. **Pipeline time**: Where a deal is in the funnel (Screen → Portfolio)
2. **Relationship time**: Where a person is in the DeVC funnel (Met → Target → Member)
3. **Tracking cadence**: How often to interact (7/30/90/180 days)

### The Evaluation Stack
For both people and companies, there's a multi-layered evaluation:

| Layer | People (Network DB) | Companies (Companies DB) |
|---|---|---|
| Identity | Role, Location, Background | Sector, Funding, Type |
| Assessment | RM reflections, Cash notes, Leverage | JTBD eyes, BRCs, Deal Status |
| Classification | DeVC Relationship, Collective Flag | Pipeline Status, Priority |
| Value | Folio Franchise, Sourcing Attribution | Smart Money, Angels, Investors |
| Health | R/Y/G, E/E Priority | Tracking cadence, Action Due |

### The BRC Loop (Most Important Network↔Company Intersection)
```
Company in pipeline → Identify founder's past companies →
  Search Network DB for connections to those companies →
    Leverage connections for Blind Reference Checks →
      Results inform JTBD (BRC Done) and ultimately Deal Status
```

This is where the AI CoS could add the most immediate value: automating the BRC discovery process and capturing results that currently scatter across email and WhatsApp.

---

## Next Steps

1. **Begin drafting the formal taxonomy model** — we now have enough data (29+ records, 11 interview rounds, full schema analysis of both DBs) to synthesize
2. **Count total records** in both DBs to understand scale
3. **Trace a real deal** through both DBs end-to-end
4. **Explore the linked DBs** (Finance, Corp Dev, Meeting Notes, Portfolio Interaction Notes, Pending Tasks) to understand the full workspace graph
5. **Begin identifying AI CoS opportunity areas** — where does the most value leak happen? (Likely: BRC capture, follow-up tracking, meeting prep context assembly, classification maintenance)
