# Session 003: Deep Schema Exploration & Interview Rounds

**Date:** March 1, 2026
**Interface:** Cowork
**Phase:** Understanding (Steps 1–3 — Explore, Interview, Case-by-Case Breakdowns)

---

## Summary

Expanded the record sample from 6 (Session 002) to 29 records across 8 of 13 DeVC Relationship categories plus many unclassified records. Conducted 4 rounds of interview questions with Aakash. Major structural discoveries about the schema, its maintenance drift, and the real taxonomy that lives in Aakash's (and RM's) head vs. what's in the database.

---

## Records Examined (29 total)

### From Session 002 (6 records)
| Name | DeVC Relationship | Role | Key Signal |
|---|---|---|---|
| Miten Sampat | DeVC Core | CXO | Blank page — power node with no notes |
| Revant Bhate | DeVC Core | Co-Founder CEO | Blank page — 12 Angel Folio entries, High everything |
| Vishesh Rajaram | DeVC Core | VC Partner | Blank page — well-classified Core IC |
| Amit Gupta | DeVC Ext | Angel | Rich RM reflections + action items, DeepTech |
| Kevin Chang | Comm Target | Micro VC GP | RM reflections with verdicts (WM for LP, SM for Ext) |
| Sanchie Shroff | Ext Target | VC Partner | AI summary, "relationship to develop" |

### Session 003 New Records (23 records)

#### Classified Records

| Name | DeVC Relationship | Role | Collective Flag | Notes Type | Key Signal |
|---|---|---|---|---|---|
| Nikhil Basu Trivedi | Ext Target | Micro VC GP | Micro VC GP | Prep + action items | Footwork $225M Fund II, "explore LP cheque" |
| Saurabh Bhatia | Ext Target | Founder Angel | — | Conversation notes | Planning own VC fund, SF landscape intel |
| Nikunj Kothari | Ext Target | Micro VC GP | Micro VC GP | Prep + conversation + actions | Left Khosla for depth-first investing at FPV |
| Aashay Sanghvi | Ext Target | Micro VC GP | — | Cash notes | Haystack VC, "High on humility, rare in this world" |
| Alysha Lobo | Ext Target | — | — | RM reflections + AI summary | Robotics ecosystem builder, operator VC profile |
| Rishabh Jangir | Ext Target | CXO | Founder Angel | Cash notes + Granola link | 5th hire at SkildAI, "expert node for evals" |
| Cindy X Bi | Comm Target | Solo GP | Solo GP | Prep + RM reflections | CapitalX, 200+ investments, validates DeVC thesis |
| Shyamal Anadkat | Comm Target | Operator Angel | — | RM reflections | GM at OpenAI, "Great addition to Collective" |
| Amit Chand | Comm Target | VC Partner | — | RM reflections | BYT Capital, "SM for addition to DeVC Collective" |
| Sameer Brij Verma | LP Target, Micro VC | VC Partner | — | RM reflections | $150M AUM, "NOT a candidate for DeVC Collective" |
| Rajesh Fernandes | DeVC Community | IP @ VC | — | RM reflections + AI transcript | MindGate, ₹100cr fund, "IFF VV has positive view" |
| Subhadeep Mondal | DeVC Ext | VC Partner | — | RM reflections | IIT-KGP syndicate plan, "MAY be a good syndication partner" |
| Vivek Karna | Founder | Co-Founder CEO | — | Reference check | Zivy, "table thumping overall" from reference |
| Shiv Bansal | Founder | Co-Founder CEO | — | Bare profile | Pixie AI for kids, inbound pitch to RM |

#### Unclassified Records (No DeVC Relationship Set)

| Name | Role | Key Properties | Notes Type | Key Signal |
|---|---|---|---|---|
| Vaas Bhaskar | VC Partner | — | RM notes on deals | Elevation Capital, recent deal discussions |
| Dushyant | Business Head | — | One-liner | "Met by Rahul on Feb 21, 2026" — freshest entry |
| Vipul Patel | VC Partner | — | AI meeting summary | IIMA Ventures, DeepTech, rich collaboration discussion |
| Tanay Jaipuria | VC Partner | — | Prep notes only | Wing VC ($600M Fund IV), meeting prep |
| Urvashi Barooah | — | — | Prep + AI summary | Wing VC partner, B2B focused, deal flow collaboration |
| Nitisha Bansal | IP @ VC | Past Cos relation | AI meeting summary | Nexus, extremely detailed strategy discussion with RM |
| Akhilesh Agarwal | IP @ VC | **Leverage: [Coverage, Evaluation]**, Folio Franchise: [DeepTech, Robotics, Aerospace, Semis, Defense] | Handwritten + AI summary | Ex-Blume, now Accel, VERY keen to collaborate |
| Omang Agarwal | Head of Sales | Piped to DeVC, Prev Foundership, Operating Franchise | Short notes | GrowthX operator, old record (2024) |
| Tanay Valia | IP @ VC | Folio Franchise: Defense | AI meeting summary | 360 ONE WAM DeepTech fund, content creator |

---

## Key Discoveries

### 1. DeVC Relationship Categories: Coverage Analysis

Of the 13 possible values in the DeVC Relationship field, our 29-record sample covers 8:

| Category | Count | Status |
|---|---|---|
| DeVC Core | 3 | ✅ Well-represented |
| Core Target | 0 | ❌ NOT FOUND in any search |
| DeVC Ext | 2 | ✅ Found |
| Ext Target | 7 | ✅ Most common category |
| DeVC Community | 1 | ✅ Found |
| Comm Target | 3 | ✅ Found |
| DeVC LP | 0 | ❌ NOT FOUND in any search |
| LP Target | 1 | ✅ Found (dual with Micro VC) |
| Tier 1 VC | 0 | ❌ NOT FOUND in any search |
| Micro VC | 1 | ✅ Found (dual with LP Target) |
| MPI IP | 0 | ❌ NOT FOUND in any search |
| Founder | 2 | ✅ Found |
| Met | 0 | ❌ NOT FOUND in any search |

**5 categories were NOT FOUND despite extensive searching.** This is itself a critical finding — either these categories are very sparsely used (near-zero records) or the classification drift is so severe that records that should be in these categories simply aren't tagged.

Hypothesis: "Core Target" and "Met" are funnel entry points (per Aakash confirming the funnel model), so records may have progressed past them. "DeVC LP" may be tracked elsewhere. "Tier 1 VC" and "MPI IP" may be categories that were designed but barely populated.

### 2. The Leverage Field — Concrete Evidence (IMPORTANT)

**Akhilesh Agarwal** is the first record found with the Leverage field populated: `[Coverage, Evaluation]`

His profile makes the meaning concrete:
- **Coverage** = He covers DeepTech sectors (Robotics, Aerospace, Semis, Defense) — tracked via Folio Franchise
- **Evaluation** = He evaluates founders — his notes show deep founder assessment ("ONLY wants to underwrite techno commercial founder", "Does drinking IDS (MPI style) to understand HOW the founder will behave")

This suggests the Leverage field describes **how a person helps DeVC's investing process**, with three possible values:
- **Coverage** = provides sector expertise and deal flow in specific verticals
- **Evaluation** = helps assess founders and companies (due diligence partner)
- **Underwriting** = helps with investment decision-making (the third value, not yet seen in a record)

Aakash said the hypothesis was "close but not quite" — the nuance may be in how "Underwriting" differs from "Evaluation", or in how these values interact with the DeVC Relationship field.

### 3. Nine Unclassified Records = Structural Confirmation of 30%+ Drift

9 of 29 records (31%) have NO DeVC Relationship set at all. This exactly matches Aakash's "Majority (30%+)" answer. The unclassified records include:
- Active VCs with recent meetings (Vaas Bhaskar, Tanay Jaipuria, Urvashi Barooah)
- Deep collaboration partners (Akhilesh Agarwal — has Leverage and Folio Franchise set but no DeVC Relationship!)
- Fresh contacts (Dushyant — met Feb 21, 2026)
- Older operators (Omang Agarwal — 2024 entry)

**Key pattern**: Even records with rich metadata (Leverage, Folio Franchise, Piped to DeVC) can be completely unclassified in the DeVC Relationship field. The schema drift is selective — some fields get maintained, others don't.

### 4. Five Distinct Note Archetypes (Confirmed & Expanded)

| Archetype | Example | Author | Structure | Key Feature |
|---|---|---|---|---|
| **RM Reflections** | Cindy, Shyamal, Sameer, Alysha | RM | `++` positives, `??` concerns, verdict (SM/WM/etc) | Assessment and classification signals |
| **AI Meeting Summaries** | Nitisha, Urvashi, Tanay V, Vipul | AI (Granola?) | Sections: Background, Discussion, Action Items | Recall and detail capture |
| **Cash (Aakash) Notes** | Aashay, Rishabh, Akhilesh (partial) | Aakash | Informal, pithy observations | Personal assessment signals |
| **Prep Notes** | Tanay J, Nikhil, Nikunj | RM (likely) | Numbered lists of research + talking points | Pre-meeting context |
| **Bare Profiles** | Shiv, Dushyant, Miten, Revant | Various/None | One-liner or empty page | Entry-level or maintained elsewhere |

**New finding**: Some records combine multiple archetypes (e.g., Akhilesh has Cash handwritten + AI summary; Alysha has RM reflections + AI summary + RM notes). The richest records layer prep → conversation → reflections → AI summary.

### 5. RM's Assessment Notation System (Deeper Understanding)

RM's reflections follow a consistent pattern seen across multiple records:

```
++ [positive signal]
++ [positive signal]
?? [concern or question]
→ Verdict: [SM/WM/M+/M/Y/N] for [what they're being assessed for]
```

Examples from this session:
- **Cindy**: `++ DeVC/Z47 platform value proposition also resonates with non-desi GPs`
- **Shyamal**: "Great addition to Collective as Community or even Core member"
- **Amit Chand**: "SM for addition to DeVC Collective"
- **Sameer**: "NOT a candidate for DeVC Collective" (explicit negative)
- **Rajesh**: "Good candidate to add to DeVC Collective IFF VV has a positive view" (conditional)
- **Subhadeep**: "MAY be a good DeVC syndication partner for KGP deals" (tentative)
- **Alysha**: "Surprised by the depth! Worth Sudipto & Naviya speaking"

Key observation: The verdict isn't just Yes/No — it's often **conditional** ("IFF VV has positive view"), **tentative** ("MAY be"), or **scoped** to a specific role ("for LP cheque" vs "for Collective Core" vs "for Collective Ext").

### 6. The "Piped to DeVC" and Attribution Fields as Activity Signals

**Omang Agarwal** is the clearest example of a non-investor network node: Head of Sales with "Piped to DeVC" relation and "Prev Foundership" set. This shows the Network DB isn't just for investors — it tracks anyone who feeds the ecosystem.

The attribution fields (Sourcing Attribution, Participation Attribution, Led by?, Piped to DeVC) form a **value graph** — they track how value flows through the network. This is separate from the relationship classification and could be a key dimension in the taxonomy.

### 7. Granola ↔ Notion Connection Confirmed

**Rishabh Jangir's** record contains an explicit Granola link: `https://notes.granola.ai/d/efeee96e-...`

This confirms:
- Some meeting notes originate in Granola and get linked to Notion
- Others appear to be direct Notion meeting notes (the `<meeting-notes>` blocks)
- The two systems aren't synchronized — records may have one, both, or neither

### 8. RM's Role Is Even Deeper Than "Right Hand"

From the Nitisha Bansal record, RM is taking meetings autonomously and discussing fund strategy in detail. He's not just writing notes — he's representing DeVC/Z47 in external meetings, discussing portfolio strategy, deployment numbers, and investment criteria. The AI summary of his meeting with Nitisha contains extremely detailed fund mechanics.

This means RM is effectively the primary relationship builder for the pipeline, not just a note-taker.

---

## Interview Findings (Rounds 3-4)

### Round 3 Answers
1. **Core people with blank pages**: "Mixed" — Some have notes elsewhere (Granola, WhatsApp etc.), others genuinely don't need them
2. **Unclassified percentage**: "Majority (30%+)" — Classification has drifted significantly
3. **AI summary standards**: "Not sure / it varies" — No single standard across tools
4. **Multi-classification**: "Common dual classification... I had only designed the schema for the DBs, post that data entry, maintenance and everything hasn't been done"
5. **Critical instruction from Aakash**: "You might want to keep learning more about the scheme until you have a thorough understanding"

### Round 4 Answers
1. **RM's role**: "He's my right hand" — deeply involved in all aspects
2. **DeVC Relationship as funnel**: "It's a funnel/progression" — Met → Target → Community/Ext → Core
3. **Leverage field**: "Close but not quite" — hypothesis partially correct, nuance unclear
4. **Note formats**: "Both have value" — RM reflections for assessment, AI summaries for recall

---

## Emerging Patterns for Taxonomy

### Pattern 1: The Actual Funnel (Confirmed by Aakash)
```
[Unknown/Met] → [Comm/Ext] Target → DeVC [Community/Ext] → DeVC Core
```
People progress through stages. "Target" = potential member being evaluated. No "Target" = already decided (member or not).

### Pattern 2: Assessment Dimensions (from RM's reflections)
Every person is being assessed on multiple axes simultaneously:
- **Collective membership**: Core vs Ext vs Community vs Not a candidate
- **LP potential**: LP cheque candidacy (separate from Collective)
- **Sourcing value**: Deal flow, sector coverage, network edge
- **Evaluation capability**: Founder assessment, technical diligence
- **Founder potential**: Future founder trajectory

### Pattern 3: Three Data Authors with Different Styles
- **RM**: Most prolific, uses `++/??/verdict` system, writes reflections + prep + relationship notes
- **Cash (Aakash)**: Occasional pithy observations ("High on humility"), meeting notes with personal assessment
- **AI systems**: Structured summaries with consistent sections, action items, transcript links

### Pattern 4: Value Flow Tracking
The Network DB tracks not just who people ARE but what value they CREATE:
- Piped to DeVC (deal sourcing)
- Sourcing Attribution (who brought what)
- Participation Attribution (who co-invested)
- Angel Folio (their own investments)
- Folio Franchise / Operating Franchise (what sectors they cover)

---

## Open Questions (Updated)

### Resolved from Session 002
- ✅ RM's role: "He's my right hand" — primary data author AND relationship builder
- ✅ Funnel vs flat: Confirmed funnel/progression model
- ✅ Multi-classification: Common and intentional, designed by Aakash
- ✅ Note formats: Both RM reflections and AI summaries valued for different purposes

### Resolved in Round 5 Interview
- ✅ **5 empty categories are a DATA QUALITY problem, not legacy**: Core Target, DeVC LP, Tier 1 VC, MPI IP, and Met SHOULD be populated. They are active conceptual categories that have drifted due to maintenance.
- ✅ **VV = Vikram Vaidyanathan**, one of 6 GPs across the funds. GP shorthand system: VV (Vikram Vaidyanathan), RA (Rajat Agarwal), Avi (Avnish Bajaj), Cash (Aakash). That's 4 of 6 GPs identified.
- ✅ **Target → Member transition is organic/judgment-based**: No formal gate. It happens naturally based on relationship quality and interaction over time.
- ✅ **Leverage field DECODED** (critical for taxonomy):
  - **Coverage** = How plugged in someone is to early-stage founder deal flow, and whether it's ADDITIVE to DeVC's existing deal flow
  - **Evaluation** = How good someone is at evaluating investment opportunities, specifically founder assessment
  - **Underwriting** = Nuanced risk/reward thinking, pricing, and investment sizing capability
  - This maps to the investment process: Sourcing → Assessment → Decision. Coverage = sourcing value, Evaluation = assessment quality, Underwriting = decision sophistication.

### Resolved in Rounds 6-7 Interview
- ✅ **Full GP team identified**: 6 GPs total — VV (Vikram Vaidyanathan), RA (Rajat Agarwal), Avi (Avnish Bajaj), Cash (Aakash), TD (Tarun Davda), RBS/BS (Rajinder)
- ✅ **Team member shorthand**: RM = Rahul Mathur (VP at DeVC, "my right hand"), DC = former VP (no longer at firm)
- ✅ **MPI IP = Investment Professional at Matrix Partners India** (Z47's former brand). Schema was built pre-rebrand.
- ✅ **DeVC Relationship hierarchy DECODED**:
  - **DeVC Core** = Highest trust, would co-invest blindly, deep partnership, strong pull for portfolio support
  - **DeVC Community** = Frequent sourcing/evaluation, not yet core depth
  - **DeVC Ext** = Extended network, sporadic sourcing/evaluation/input
- ✅ **Target = destination-based classification**: Core Target → aiming for Core, Comm Target → aiming for Community, Ext Target → aiming for Ext
- ✅ **Aakash's instruction**: "Explore more. Ask as many clarifying questions. Build a deeper understanding of the DeVC relationship archetypes in full interview session. Also look at schema and taxonomy of Companies DB."

### Resolved in Session 004
- See [Session 004 log](./2026-03-01-session-004-companies-db-and-archetype-deep-dive.md) for all remaining archetype and Companies DB findings.

### Still Open (Carried to Session 004)
1. ~~What is "Engagement Playbook"?~~ → ✅ Investing style classification (Session 004)
2. ~~What are "C+E" events?~~ → ✅ Community + Events (Session 004)
3. ~~How do "Schools" relations work?~~ → ✅ Strategic deal flow capture tool (Session 004)
4. **How does the Companies DB relate to people progression?** → Partially answered in Session 004
5. ~~Who are the remaining 2 GPs?~~ → ✅ TD (Tarun Davda) and RBS/BS (Rajinder)
6. ~~What does "MPI IP" mean exactly?~~ → ✅ Investment Professional at Matrix Partners India

---

## Next Steps (Updated)

→ Continued in [Session 004](./2026-03-01-session-004-companies-db-and-archetype-deep-dive.md)
