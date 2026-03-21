# Action Queue Regeneration Audit
**Date:** 2026-03-21
**Machine:** TEMP - Action Regeneration (one-time)

---

## 1. Pre-Cleanup State

| Status | Total | Stale (>14d) | Today | Avg Score |
|--------|-------|-------------|-------|-----------|
| Proposed | 42 | 18 | 12 | ~5.8 |
| Accepted | 10 | 9 | 0 | 5.73 |
| Dismissed | 93 | 66 | 11 | 3.90 |
| **Total** | **145** | **93** | **23** | — |

Stale rate across all statuses: 64%. Stale rate in live queue (Proposed): 43%.

---

## 2. Stale Actions Dismissed (8 total)

### Superseded by Accepted Actions (4)
| ID | Action | Score | Superseded By |
|----|--------|-------|---------------|
| 76 | Schedule call with Amartya Jha (CEO) to discuss path to replacing Snyk/Linear B | 3.95 | Accepted #32 (CodeAnt integration roadmap) + #99 (Poetic question) |
| 52 | Schedule call with Unifize product/investor to clarify funding opacity | 4.88 | Accepted #29 (Unifize founder deep dive) |
| 26 | Schedule call with CEO Sudarshan Kamath — revenue vs volume disconnect | 3.33 | Accepted #100 (Smallest AI moat check-in) |
| 37 | Request detailed customer case study from Dallas Renal Group | 3.02 | Accepted #78 (Confido Health AI agent strategy) |

### Stale & Low-Value (3)
| ID | Action | Score | Reason |
|----|--------|-------|--------|
| 9 | Schedule call with Rishabh Goel (CEO) to review UPI merchant success rate data | 3.48 | Narrow sub-question; broader #41 (product scope risk) still active |
| 61 | Schedule operational deep-dive with CEO Rohit Arora (Stance Health) | 4.57 | Stale 15d, can be regenerated with richer data |
| 59 | Schedule call with CEO Satish Perala — Cybrilla FY26 monetization plan | 4.10 | Stale 15d, can be regenerated with richer data |

### Duplicate (1)
| ID | Action | Score | Duplicate Of |
|----|--------|-------|-------------|
| 134 | Loop in Rahul (DeVC) on Levocred evaluation | 6.12 | #121 (Review Levocred pitch deck + involve Rahul, score 9.69) |

---

## 3. Stale Actions KEPT (11)

These are 15+ days old but represent genuine active risks worth preserving:

| ID | Action | Score | Why Keep |
|----|--------|-------|----------|
| 46 | Request detailed unit economics from Akasa Air and Motorq customers (CodeAnt) | 6.44 | Real validation gap; CodeAnt is BREAKOUT candidate |
| 50 | Flag regulatory risk on AI features for Unifize | 5.40 | Novel FDA/ISO risk; not covered by accepted #29 |
| 75 | CRITICAL: Pause investment activities for Orange Slice | 5.81 | Entity verification failure — must not be lost |
| 48 | Flag operational risk on 'Free Lifetime Repairs' for Terractive | 5.60 | Unique margin risk; Terractive is in onboarding |
| 79 | Flag pricing volatility risk on CodeAnt tiers | 4.98 | Enterprise readiness concern; CodeAnt is high-priority |
| 58 | Resolve bootstrapped vs $1.79M funding contradiction for Legend of Toys | 4.14 | Due diligence integrity issue |
| 10 | Flag capital intensity risk for Inspecity | 4.56 | Real spacetech funding gap |
| 85 | Brand consolidation call — Orbit vs Balisto transition | 4.77 | Active confusion harming growth |
| 45 | Board-level call with Atica CEO — unit economics/tech leverage | 3.72 | Services-vs-SaaS diagnostic |
| 11 | Flag execution risk on Grow financing arm for GameRamp | 3.51 | Financing moat validation |
| 41 | Flag mile-wide, inch-deep product scope risk for Dodo Payments | 3.30 | Pre-seed scope risk |

---

## 4. Post-Cleanup State

| Status | Total | Stale (>14d) | Today | Avg Score |
|--------|-------|-------------|-------|-----------|
| Proposed | 34 | 11 | 11 | 6.26 |
| Accepted | 10 | 9 | 0 | 5.73 |
| Dismissed | 100 | 80 | 18 | 3.90 |
| **Total** | **144** | **100** | **29** | — |

### Current Proposed Queue by Action Type
| Type | Count | Avg Score |
|------|-------|-----------|
| Pipeline/Deals | 2 | 9.77 |
| Portfolio/Support | 4 | 8.72 |
| Portfolio Check-in | 9 | 6.98 |
| Meeting/Outreach | 4 | 6.86 |
| Pipeline Action | 2 | 8.61 |
| Research | 5 | 4.48 |
| Thesis Update | 2 | 2.71 |
| Pipeline | 2 | 2.24 |
| Meeting | 1 | 5.66 |
| Portfolio | 1 | 5.97 |
| Content Follow-up | 1 | 2.71 |
| Network/Relationships | 1 | 4.26 |

### Top 10 Actions (by score)
1. **10.00** — Make investment decision on Cultured Computers (P0, deadline)
2. **9.58** — Review Levocred pitch deck + involve Rahul
3. **8.95** — Connect AuraML with 5 investors
4. **8.74** — Provide Schneider Electric endorsement for AuraML
5. **8.33** — Share Monday.com SDR-to-agent data with portfolio
6. **8.12** — Map Indian coding AI infrastructure for DeVC
7. **7.70** — Share Wang interview with CodeAnt AI founder
8. **7.49** — Map emerging data infrastructure layer for AI
9. **7.07** — Introduce Muro/Rajat to Z47 human capital team
10. **6.86** — Map/reach out to E2B, orchestration layer infra

---

## 5. Accepted Actions — Staleness Warning

10 Accepted actions, 9 are 15+ days old. None have been executed. These should either be:
- **Completed** (outcomes recorded)
- **Returned to Proposed** (if not started)
- **Dismissed** (if no longer relevant)

| ID | Action | Score | Age |
|----|--------|-------|-----|
| 29 | Unifize founder deep dive | 10.00 | 15d |
| 32 | CodeAnt AI integration roadmap | 8.60 | 15d |
| 55 | Highperformr positioning review | 8.45 | 15d |
| 78 | Confido Health: AI agent strategy inquiry | 7.83 | 15d |
| 95 | Meeting prep: reach out to Poetic team | 6.28 | 15d |
| 99 | CodeAnt: Poetic harness-layer question | 5.81 | 15d |
| 100 | Smallest AI: moat question | 5.50 | 15d |
| 92 | Interview 5-10 enterprise engineers | 2.09 | 15d |
| 14 | Map agent infrastructure ecosystem | 1.00 | 15d |
| 113 | Map portfolio against Gokul's 8 Moats | 1.78 | 5d |

---

## 6. Data Available for Agent-Based Action Generation

**Action generation is the job of agents (Cindy, ENIAC, Megamind), not SQL.** Below is what's available for those agents to use.

### Rich Data Now Available
| Source | Count | Notes |
|--------|-------|-------|
| Portfolio companies with key_questions | 93 | 5-question sets per company |
| Portfolio companies with high_impact | 95 | Strategic levers and signals |
| Portfolio companies with research files | 142 | All have research_file_path |
| Companies (pipeline) with research files | 21 | Deep research available |
| Total obligations | 14 | All have linked_action_id except 1 |
| Open obligations | 14 | 7 overdue, 3 escalated, 4 pending |
| Interactions | 23 | Meeting/call context |
| Thesis threads | 8 | 1 Active, 7 Exploring |
| Strategic assessments | 16 | |
| Context gaps | 6 | Known unknowns |
| Cascade events | 29 | Cross-entity triggers |

### Critical Gap: 73 Portfolio Companies Have Key Questions but NO Action

73 healthy (Green/Yellow) portfolio companies have populated `key_questions` fields but zero corresponding Proposed or Accepted actions. These are the primary fuel for agent-generated actions.

### High-Signal Uncovered Companies (BREAKOUT/EXIT signals, no action)
| Company | Signal | Health |
|---------|--------|--------|
| **cocreate** | BREAKOUT: INR 204 Cr revenue, 1,019% growth | Green |
| **Boba Bhai** | BREAKOUT: 6x revenue, 90 stores profitable | Green |
| **Insta Astro** | POTENTIAL EXIT via Flipkart acquisition | Green |
| **Morphing Machines** | Deep-tech silicon milestone in 12-24 months | Green |
| **AeroDome** | Deep-tech space, defense dual-use | Green |
| **NuPort Robotics** | ADAS retrofit, government validation | Yellow |

### Obligation Coverage
13 of 14 open obligations already have linked actions. Only 1 is unlinked:
- **Kilrr Series A documents** (Hitesh Bhagia, due Mar 25, pending) — no linked action

### What Agents Should Generate
1. **ENIAC (Research Analyst):** Portfolio key_question investigations for the 73 uncovered companies, prioritized by: (a) BREAKOUT/EXIT signals, (b) health=Red warning signals, (c) upcoming fundraise timeline
2. **Cindy (Comms Intelligence):** Obligation-derived actions for the 1 unlinked obligation; meeting prep actions from recent interactions
3. **Megamind (Strategist):** Thesis evidence gap actions (8 threads, most at Exploring/Medium conviction); cross-portfolio pattern actions (e.g., AI agent adoption check across all SaaS portfolio companies)

### Portfolio Red Health Companies (18) — Agent Opportunity
These companies have health=Red. 12 are in "Find Home / Wind Down" status (already being managed). The remaining 6 may need monitoring actions:
- BiteSpeed (Red, Find Home / Wind Down)
- Boxpay (Red, Find Home / Wind Down)
- CarbonStrong (Red, Raise 3 months)
- Coffeee.io (Red, Raise 6 months)
- ElecTrade (Red, Find Home / Wind Down)
- Emomee (Red, Find Home / Wind Down)
- GoCredit (Red, Find Home / Wind Down)
- HealthCred (Red, Raise 6 months)
- iBind Systems (Red, Raise 12 months)
- Manufacture AI (Red, no status)
- Mantys (Red, Find Home / Wind Down)
- Mindforest (Red, Find Home / Wind Down)
- Navo (Red, Raise 6 months)
- ofScale (Red, Find Home / Wind Down)
- PowerEdge (Red, Onboarding)
- Puch AI (Red, Acquired/Shut Down)
- Recrew AI (Red, Raise 6 months)
- YOYO AI (Red, In Closing / Paperwork)

---

## 7. Summary

| Metric | Before | After | Delta |
|--------|--------|-------|-------|
| Total Proposed | 42 | 34 | -8 |
| Stale Proposed (>14d) | 18 | 11 | -7 |
| Stale % of Proposed | 43% | 32% | -11pp |
| Avg Proposed Score | ~5.8 | 6.26 | +0.46 |
| Dismissed (total) | 93 | 100 | +7 (stale) +1 (dup) |
| Duplicate pairs resolved | 0 | 1 | +1 |

**Net result:** Queue is cleaner. 7 stale actions dismissed (4 superseded, 3 low-value). 1 duplicate resolved. 11 stale actions intentionally retained as valid portfolio risks. Average score improved from ~5.8 to 6.26.

**Remaining debt:** 10 Accepted actions (9 stale) need triage — either complete, return to Proposed, or dismiss. 73 portfolio companies have rich key_questions data but no corresponding actions — this is the primary fuel for agent-generated actions via M7/M8 machine loops.
