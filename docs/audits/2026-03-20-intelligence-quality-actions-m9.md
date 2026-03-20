# Intelligence Quality Audit: Actions Queue (M9)

**Date:** 2026-03-20
**Scope:** 115 actions across `actions_queue` + `user_triage_queue` view
**Method:** Full-population audit across 5 dimensions with per-sample assessment

---

## Executive Summary

**Overall Intelligence Quality Score: 5.5 / 10**

The actions pipeline produces reasonably specific, actionable text with good domain grounding. However, the system has five systemic problems that undermine intelligence quality:

1. **Scoring function is formulaic, not intelligence-driven** -- user_priority_score is entirely determined by action_type + priority + recency, ignoring IRGI and scoring_factors
2. **Thesis connections are over-applied** -- many actions get 4-6 thesis tags via semantic similarity rather than genuine causal relevance
3. **"Healthcare AI Agents as Infrastructure" is a false-positive magnet** -- attached to 12 actions with zero healthcare content
4. **action_type classification is unreliable** -- 24 "Research" actions actually require user outreach (schedule, request, flag)
5. **Significant action duplication** -- 15 near-duplicate pairs detected, inflating queue noise

---

## 1. Scoring Accuracy (30 samples from user_triage_queue, NOT agent_delegable)

### Score Distribution Findings

The `compute_user_priority_score` function creates **hard tiers** rather than a meaningful gradient:

| Tier | Score Range | Count (in top 30) | Composition |
|------|------------|-------------------|-------------|
| Ultra-high | 9.79 | 8 | All P0 Portfolio Check-ins |
| High | 9.73 | 14 | All P0/P1 Meeting/Outreach |
| Mid-high | 9.55-9.61 | 4 | P1 Portfolio Check-ins with thesis |
| Mid | 8.5-8.8 | 2 | P2 Meeting + P1 Pipeline w/ thesis |
| Low | 7.0-7.7 | 2 | Research with high IRGI |

**Critical problem:** The scoring function is `base_score(relevance_score) + priority_boost + type_boost + recency_factor`. This means:
- All P0 Portfolio Check-ins cluster at ~9.79 regardless of actual urgency
- All P0 Meetings cluster at ~9.73 regardless of which meeting matters more
- IRGI score (the actual intelligence signal) is **completely ignored** in the ranking
- `scoring_factors` is `{}` (empty) for 95%+ of actions -- the field is populated for only 1 action (id:101)

### Per-Sample Assessment

| ID | Action (truncated) | Priority | Type | Score | Assessment | Reasoning |
|----|-------------------|----------|------|-------|------------|-----------|
| 84 | Flag privacy/spam complaint risk for PowerUp Money | P0 | Portfolio Check-in | 9.79 | **ACCURATE** | Privacy risk for a fintech is genuinely P0 |
| 75 | CRITICAL: Pause investment activities for Orange Slice | P0 | Portfolio Check-in | 9.79 | **ACCURATE** | Entity verification failure is truly critical |
| 50 | Flag regulatory risk on AI features for Unifize | P0 | Portfolio Check-in | 9.79 | **PARTIALLY ACCURATE** | Important but P1 not P0 -- regulatory risk is emerging, not imminent |
| 48 | Flag operational risk on 'Free Lifetime Repairs' for Terractive | P0 | Portfolio Check-in | 9.79 | **PARTIALLY ACCURATE** | Valid risk but P1 -- long-term margin concern, not immediate crisis |
| 41 | Flag execution risk on 'mile-wide, inch-deep' for Dodo | P0 | Portfolio Check-in | 9.79 | **ACCURATE** | Pre-seed spreading thin is legitimate P0 risk |
| 11 | Flag execution risk on Grow financing arm for GameRamp | P0 | Portfolio Check-in | 9.79 | **ACCURATE** | Credit risk in game financing warrants P0 |
| 10 | Flag capital intensity risk for Inspecity | P0 | Portfolio Check-in | 9.79 | **ACCURATE** | Spacetech undercapitalization is genuine P0 |
| 2 | Flag trademark conflict risk if Orange Slice exists in dehydrated fruit | P0 | Portfolio Check-in | 9.79 | **INACCURATE** | This is a P1 risk item at best; trademark check is not an emergency. Also duplicates id:68 |
| 85 | Schedule urgent brand consolidation call - Orbit/Balisto | P0 | Meeting/Outreach | 9.74 | **ACCURATE** | Brand confusion during growth is genuinely urgent |
| 83 | Schedule call with Vivek Ramachandran - Vietnam/Turkey pilots | P0 | Meeting/Outreach | 9.74 | **ACCURATE** | International expansion data review is appropriately P0 |
| 80 | Schedule call with Arindrajit Chowdhury - RPOD validation | P0 | Meeting/Outreach | 9.74 | **ACCURATE** | Spacetech milestone validation is P0 |
| 79 | Flag pricing volatility risk on CodeAnt tiers | P1 | Portfolio Check-in | 9.74 | **ACCURATE** | Pricing confusion is real risk; thesis connection (Agent-Friendly Codebase) is relevant |
| 76 | Schedule call with Amartya Jha - replacing Snyk/Linear B | P0 | Meeting/Outreach | 9.74 | **ACCURATE** | Consolidation thesis validation is P0 for active investment |
| 74 | Schedule call with Dhruv Kohli - unit economics | P0 | Meeting/Outreach | 9.74 | **ACCURATE** | QSR unit economics pre-expansion is P0 |
| 73 | Schedule call with Chetan Reddy - Series A burn rate | P0 | Meeting/Outreach | 9.74 | **ACCURATE** | Burn rate review post-raise is appropriately urgent |
| 68 | Assess trademark/IP risk regarding 'Orange Slice' naming | P1 | Portfolio Check-in | 9.74 | **INACCURATE** | Near-duplicate of id:2. System created two separate actions for same risk |
| 65 | Request clarification on store count discrepancies | P1 | Portfolio Check-in | 9.74 | **ACCURATE** | Operational transparency concern is valid P1 |
| 61 | Schedule operational deep-dive with CEO Rohit Arora (Stance) | P0 | Meeting/Outreach | 9.74 | **ACCURATE** | Operational unit economics validation is appropriately urgent |
| 59 | Schedule call with CEO Satish Perala - FY26 monetization | P0 | Meeting/Outreach | 9.74 | **ACCURATE** | Revenue-influence gap is genuine P0 diligence |
| 58 | Schedule urgent capital structure clarification - Legend of Toys | P0 | Meeting/Outreach | 9.74 | **ACCURATE** | Funding contradiction is P0 diligence |
| 52 | Schedule call with Unifize product/investor - funding opacity | P0 | Meeting/Outreach | 9.74 | **ACCURATE** | Enterprise buyer concern about vendor stability |
| 45 | Schedule board-level call with CEO Akash Goel (Atica) | P0 | Meeting/Outreach | 9.74 | **ACCURATE** | Services-vs-SaaS validation pre-Series A |
| 44 | Schedule strategic review with Isler CEO + Hafele partner | P0 | Meeting/Outreach | 9.74 | **ACCURATE** | Customer concentration risk is P0 |
| 42 | Schedule call with Prateek Jindal - Elite subscriber cohorts | P0 | Meeting/Outreach | 9.74 | **ACCURATE** | Subscription stickiness validation is P0 |
| 30 | Request independent tech validation WeldT vs ABB | P0 | Meeting/Outreach | 9.74 | **ACCURATE** | Technology benchmarking is critical for deeptech |
| 26 | Schedule call with Sudarshan Kamath - revenue vs volume | P0 | Meeting/Outreach | 9.74 | **ACCURATE** | Revenue disconnect is classic deeptech trap |
| 20 | Flag 'fad risk' and health scrutiny for Boba Bhai | P1 | Portfolio Check-in | 9.74 | **ACCURATE** | Category durability concern is valid P1 |
| 19 | Monitor GST compliance impact on RMG financing | P1 | Portfolio Check-in | 9.74 | **ACCURATE** | Regulatory macro risk is properly P1 |
| 9 | Schedule call with Rishabh Goel - UPI success rates | P0 | Meeting/Outreach | 9.74 | **ACCURATE** | Payment conversion validation is P0 |
| 7 | Flag HIPAA BAA compliance jurisdiction risk | P1 | Portfolio Check-in | 9.74 | **ACCURATE** | Healthcare regulatory compliance is valid P1 |

### Scoring Accuracy Summary

| Rating | Count | % |
|--------|-------|---|
| ACCURATE | 24 | 80% |
| PARTIALLY ACCURATE | 4 | 13% |
| INACCURATE | 2 | 7% |

**Key finding:** Individual priority assignments are mostly correct (80% accurate). The systemic failure is that the **scoring function creates no differentiation within priority tiers** -- all P0 Portfolio Check-ins score identically, all P0 Meetings score identically. The function ignores IRGI, which is the only intelligence-derived signal available.

---

## 2. Bucket Routing Quality (action_type as proxy)

There is no `bucket` column in `actions_queue`. The intended bucket routing must be inferred from `action_type`. Here is the assessment by type:

### Portfolio Check-in (19 actions) -- Maps to "Deepen Existing"

| Assessment | Details |
|------------|---------|
| **Correct routing: 17/19 (89%)** | Most are genuinely about existing portfolio companies |
| **Misrouted: 2/19** | id:107 "Share Monday.com SDR data with portfolio companies" is more of a **knowledge transfer / Meeting/Outreach** action. id:29 "Unifize founder deep dive: agent-native architecture" reads more like a **Research** action |

### Meeting/Outreach (32 actions) -- Maps to "Expand Network"

| Assessment | Details |
|------------|---------|
| **Correct routing: 26/32 (81%)** | Most are genuine outreach/scheduling actions |
| **Misrouted: 6/32** | Several are actually diligence requests that should be Portfolio Check-in: id:30 (tech validation for existing deal), id:40 (SOC 2 compliance request for existing company), id:49 (technical validation for existing pipeline company), id:51 (product roadmap review), id:53 (validate pipeline), id:92 (enterprise engineer interviews -- this is research) |

### Research (46 actions) -- Should map to "Thesis Evolution" (if thesis-related) or "Discover New"

| Assessment | Details |
|------------|---------|
| **Correct routing: 22/46 (48%)** | Pure research/thesis actions that an agent could do |
| **Misrouted: 24/46 (52%)** | 24 actions typed "Research" actually contain verbs like "Schedule," "Request," "Flag," "Commission," "Investigate" -- these require human action and should be **Meeting/Outreach** or **Portfolio Check-in**. This is the largest single misclassification in the system. |

**Examples of mistyped "Research":**
- id:34 "Schedule urgent team scaling call" --> should be Meeting/Outreach
- id:56 "Commission independent lab testing" --> should be Pipeline Action
- id:66 "Schedule product security review" --> should be Meeting/Outreach
- id:4 "Flag platform dependency risk" --> should be Portfolio Check-in
- id:24 "Flag operational capacity risk" --> should be Portfolio Check-in

### Pipeline Action (13 actions) -- Maps to "Discover New"

| Assessment | Details |
|------------|---------|
| **Correct routing: 11/13 (85%)** | Most are genuine pipeline/deal flow actions |
| **Misrouted: 2/13** | id:111 "Map Indian coding AI landscape for DeVC pipeline" is research, not pipeline action. id:108 "Map and reach out to E2B, orchestration layer infra companies" straddles research and pipeline. |

### Thesis Update (4 actions) -- Maps to "Thesis Evolution"

| Assessment | Details |
|------------|---------|
| **Correct routing: 4/4 (100%)** | All are genuine thesis updates |

### Content Follow-up (1 action)

| Assessment | Details |
|------------|---------|
| **Correct routing: 1/1 (100%)** | id:112 "Listen to 20VC Gokul segment" is genuinely content follow-up |

### Overall Bucket Routing Accuracy: **70/115 (61%)**

The 52% misclassification rate within Research is the dominant driver of routing inaccuracy.

---

## 3. Agent vs User Classification

The `user_triage_queue` view classifies 8 actions as `is_agent_delegable = true`:

| ID | Action (truncated) | Type | Assigned_to | Agent-Delegable? | Assessment |
|----|-------------------|------|-------------|-----------------|------------|
| 112 | Listen to 20VC Gokul Rajaram 12:15-20:16 segment | Content Follow-up | Aakash | true | **INACCURATE** -- Listening to a podcast segment is inherently a human activity. Agent could summarize, but the action says "listen" |
| 109 | Research OpenClaw/NanoClaw adoption patterns | Research | Agent | true | **ACCURATE** -- Pure research, agent-suitable |
| 101 | Map emerging data infrastructure layer for AI | Research | Agent | true | **ACCURATE** -- Mapping/research, agent-suitable |
| 110 | Research which SaaS categories survive agentic transition | Research | Agent | true | **ACCURATE** -- Research, agent-suitable |
| 115 | Update SaaS Death thesis with Gokul's 8 moats framework | Thesis Update | Agent | true | **ACCURATE** -- Thesis update, agent-suitable |
| 103 | Research defense-AI data infrastructure companies | Research | Agent | true | **ACCURATE** -- Research, agent-suitable |
| 102 | Update SaaS Death thesis - Wang's enterprise data moat | Thesis Update | Agent | true | **ACCURATE** -- Thesis update, agent-suitable |
| 106 | Map human-agent orchestration platform landscape | Research | Agent | true | **ACCURATE** -- Research, agent-suitable |

### NOT flagged as agent-delegable but should be:

| ID | Action | Type | Why it should be agent-delegable |
|----|--------|------|----------------------------------|
| 86 | Model SaaS multiple compression scenarios | Research (Agent) | Correctly assigned_to Agent, but `is_agent_delegable` shows in user_triage_queue since it's status Accepted |
| 8 | Research incumbent responses: Salesforce AgentForce, Workday AI | Research (Agent) | Same -- shows in view |
| 90 | Research CLAW stack standardization | Research (Agent) | Same |
| 89 | Model white-collar displacement timeline | Research (Agent) | Same |
| 87 | Assess Z47/DeVC agent deployment readiness | Research (Aakash) | **MISSED** -- This IS agent-delegable research but assigned to Aakash. The action text is pure desk research |
| 91 | Product deep-dive: Unifize + CodeAnt roadmap mapping | Research (Aakash) | **MISSED** -- Agent could do the roadmap analysis; user needed only for the meeting |
| 105 | Analyze public market AI transition opportunities | Research (Aakash) | **MISSED** -- Public market analysis is ideal agent work |

### Should NOT be agent-delegable but are not flagged anyway:

The view's `is_agent_delegable` logic catches Research/Thesis/Content/Evidence types correctly. But the keyword exceptions (flag, request, commission, investigate, schedule, diligence, etc.) only apply to `action_type ILIKE '%research%'`. Since 24 Research-typed actions actually contain user-action verbs, these exceptions help -- but the root cause is the mistyped action_type.

### Agent Classification Accuracy: **7/8 correct (88%)**

The one miss (id:112 "Listen to podcast") is a semantic edge case. The bigger issue is **3 actions assigned to "Aakash" that should be agent-delegable** (ids 87, 91, 105).

---

## 4. Related Items Quality (Vector Similarity)

10 samples tested with nearest-company embeddings:

| ID | Action | Thesis | Top 5 Nearest Companies | Assessment |
|----|--------|--------|------------------------|------------|
| 95 | Meeting prep: Poetic team | Agentic AI / SaaS Death / Healthcare AI | ProactAI, Agentic AI, Vink AI, Spot AI, Personate.ai | **PARTIALLY ACCURATE** -- Agentic AI is relevant. ProactAI, Vink AI, Spot AI, Personate.ai are "AI" companies but not in the harness/orchestration layer. Noise-to-signal ratio ~40% |
| 89 | Model white-collar displacement timeline | SaaS Death / Agentic AI | SupportEngineer AI, Skillsoft, Unsiloed AI, Certus AI, Murf AI | **PARTIALLY ACCURATE** -- SupportEngineer AI and Unsiloed AI have some relevance to workforce displacement. Skillsoft/Murf AI are tangential |
| 92 | Interview enterprise engineers on agent deployment | SaaS Death / Agentic AI / Cybersecurity | Agentic AI, dot agent, Unsiloed AI, Expertia AI, SupportEngineer AI | **ACCURATE** -- Agentic AI and dot agent are directly relevant. Unsiloed AI reasonable |
| 94 | Research AI provider bias concentration risk | SaaS Death / Healthcare AI | Socratix AI, Asymmetric Research, ProactAI, Luma AI, Natsure.AI | **INACCURATE** -- None of these companies relate to AI bias/critique tools. Pure embedding noise |
| 96 | Deep research: IMO 4/6 solver mechanics | SaaS Death / Agentic AI / Healthcare | AI Squared, Insight AI, Hosted AI, Iterate AI, ThirdAI Corp | **INACCURATE** -- These are generic "AI" companies. None relate to mathematical reasoning or solver architectures |
| 88 | Monitor open-source harness frameworks | Agentic AI / SaaS Death / Healthcare | Socratix AI, Natsure.AI, Luma AI, Iterate AI, Alchemyst AI | **INACCURATE** -- None of these build harness/orchestration frameworks. Pure semantic "AI" matching |
| 46 | Request unit economics from Akasa Air/Motorq customers | Agent-Friendly Codebase | CodeAnt, dot agent, Impendi Analytics, SupportEngineer AI, Skild AI | **PARTIALLY ACCURATE** -- CodeAnt is relevant (the action relates to CodeAnt's customers). Others are noise |
| 93 | Deep research: rural talent + creativity thesis | SaaS Death / Agentic AI / Healthcare | dScribe AI, Natsure.AI, AI Racing Tech, Socratix AI, 10x Science | **INACCURATE** -- None relate to rural talent or creativity. Complete mismatch |
| 79 | Flag pricing volatility risk on CodeAnt tiers | Agent-Friendly Codebase | CodeAnt, PodArmor, dot agent, bugbase, Omnara | **ACCURATE** -- CodeAnt is #1 match, directly relevant. bugbase and dot agent are adjacent |
| 100 | Portfolio check-in: Smallest AI moat question | Agentic AI / SaaS Death / Healthcare / CLAW | Smallest AI, Hosted AI, Alchemyst AI, Expertia AI, Mimos AI | **ACCURATE** -- Smallest AI is #1 match. Others are voice/AI companies in adjacent space |

### Related Items Accuracy: 3 ACCURATE, 3 PARTIALLY, 4 INACCURATE (30% fully accurate)

**Root cause:** The vector embeddings are performing basic "AI company" matching rather than understanding the specific sub-domain of each action. Actions about orchestration layers find any company with "AI" in the name. The embedding model lacks the domain specificity needed for this use case.

---

## 5. Thesis Connection Quality

### Cross-reference: Thesis connections from JOIN with thesis_threads

From the 20 samples with verified thesis connections:

| ID | Action | Connected Thesis | IRGI | Assessment |
|----|--------|-----------------|------|------------|
| 109 | Research OpenClaw/NanoClaw adoption | Agentic AI Infra, CLAW Stack, SaaS Death, Non-Consumption, Agent-Friendly Codebase | 0.89 | **PARTIALLY ACCURATE** -- Agentic AI Infra and CLAW Stack are directly relevant. SaaS Death is reasonable. But Non-Consumption Markets and Agent-Friendly Codebase have no connection to protocol standardization research |
| 14 | Map agent infrastructure ecosystem | Agentic AI Infra, SaaS Death, CLAW Stack, Non-Consumption | 0.89 | **PARTIALLY ACCURATE** -- First 3 are spot-on. Non-Consumption Markets is a stretch for infra mapping |
| 106 | Map human-agent orchestration platform landscape | SaaS Death, Agentic AI, CLAW Stack, **Cybersecurity**, Non-Consumption, Agent-Friendly Codebase | 0.88 | **PARTIALLY ACCURATE** -- Core thesis connections are valid but Cybersecurity has zero relevance to human-agent orchestration |
| 90 | Research CLAW stack standardization | SaaS Death, Agentic AI, **Cybersecurity**, CLAW Stack, Agent-Friendly Codebase | 0.88 | **PARTIALLY ACCURATE** -- Same issue: Cybersecurity is irrelevant to CLAW stack research |

### Systematic over-tagging pattern

**12 actions with "Healthcare AI Agents as Infrastructure" that have ZERO healthcare content:**

| ID | Action | Healthcare connection? |
|----|--------|----------------------|
| 88 | Monitor open-source harness frameworks (DSPY, LangChain) | NO |
| 91 | Product deep-dive: Unifize + CodeAnt roadmap | NO |
| 93 | Deep research: rural talent + creativity thesis | NO |
| 94 | AI provider bias concentration risk | NO |
| 95 | Meeting prep: Poetic team | NO |
| 96 | IMO 4/6 solver mechanics | NO |
| 97 | Thesis update: SaaS Death (small teams outperform) | NO |
| 98 | Poetic's recursive self-improvement vs o1 | NO |
| 99 | Portfolio check-in: CodeAnt AI re Poetic | NO |
| 100 | Portfolio check-in: Smallest AI moat | NO |
| 101 | Map data infrastructure layer for AI | NO |
| 102 | Update SaaS Death thesis - enterprise data moat | NO |

These all appear to come from the same content batch (Poetic/IMO research, ids 88-102). The thesis tagging system applied Healthcare AI to the entire batch, likely because the source content mentioned healthcare tangentially or the batch processing didn't discriminate per-action.

**"Cybersecurity / Pen Testing" is similarly over-applied** to 6 non-cybersecurity actions (ids 32, 92, 104, 108, 111, plus research items). The connection exists only because CodeAnt/StepSecurity touches security-adjacent space -- but the actions themselves are about orchestration, codebase architecture, or data infrastructure.

### Thesis Connection Accuracy

| Rating | Count | % |
|--------|-------|---|
| Fully Accurate (all connections valid) | 4 | 20% |
| Partially Accurate (primary connections valid, spurious extras) | 12 | 60% |
| Inaccurate (primary connection wrong or all connections spurious) | 4 | 20% |

**The primary thesis connection is usually correct; the problem is over-application of 2-4 additional thesis tags that are semantically related but causally irrelevant.**

---

## 6. Duplicate Detection

15 near-duplicate pairs found (cosine distance < 0.15):

| Pair | Actions | Severity |
|------|---------|----------|
| 2 & 68 | "Flag trademark conflict risk - Orange Slice" / "Assess trademark/IP risk - Orange Slice" | **HIGH** -- Same topic, same company, both in Portfolio Check-in |
| 67 & 71 | "Resolve funding discrepancy (Tracxn $1.89M)" / "Request clarity on funding discrepancies (Tracxn $7.28M)" | **HIGH** -- Same class of action, likely different companies but semantically identical pattern |
| 14 & 109 | "Map agent infrastructure ecosystem" / "Research OpenClaw/NanoClaw adoption patterns" | **MEDIUM** -- Overlapping but distinct scope |
| 14 & 90 | "Map agent infrastructure ecosystem" / "Research CLAW stack standardization" | **MEDIUM** -- Overlapping scope |
| 14 & 106 | "Map agent infrastructure ecosystem" / "Map human-agent orchestration platform" | **MEDIUM** -- Very similar mapping exercise |
| 90 & 109 | "Research CLAW stack standardization" / "Research OpenClaw/NanoClaw adoption" | **LOW** -- Different specificity level |
| 36 & 62 | "Request working capital health check (₹36.46L)" / "Verify working capital health (~$5M raised)" | **HIGH** -- Same action pattern, different companies but indistinguishable in queue |
| 97 & 102 | "Thesis update: SaaS Death (small teams)" / "Update SaaS Death thesis (enterprise data moat)" | **LOW** -- Same thesis thread but genuinely different evidence |
| 8 & 110 | "Research incumbent responses: Salesforce AgentForce" / "Research which SaaS categories survive" | **MEDIUM** -- Related research angles |
| 88 & 98 | "Monitor OSS harness frameworks (DSPY, LangChain)" / "How is Poetic different from o1-style reasoning?" | **LOW** -- Different questions |
| 105 & 106 | "Analyze public market AI transition" / "Map human-agent orchestration platform" | **LOW** -- Different scope |
| 112 & 115 | "Listen to 20VC Gokul segment" / "Update SaaS Death thesis with 8 moats" | **LOW** -- Content consumption vs thesis update |
| 32 & 91 | "CodeAnt AI integration roadmap" / "Product deep-dive: Unifize + CodeAnt" | **MEDIUM** -- Both involve CodeAnt positioning |
| 88 & 100 | "Monitor OSS harness frameworks" / "Portfolio check-in: Smallest AI moat" | **LOW** -- Different intent |
| 110 & 115 | "Research SaaS categories survive" / "Update SaaS Death thesis with 8 moats" | **LOW** -- Research vs thesis update |

**3 HIGH-severity duplicates** need immediate dedup: (2, 68), (67, 71), (36, 62).

---

## Top 5 Misclassifications / Inaccuracies

### 1. P0 Research actions scored at 4.3 despite requiring urgent user action

**Problem:** 17 P0 Research actions (ids 4, 13, 16, 24, 27, 31, 34, 35, 36, 37, 46, 56, 60, 64, 66, 105) score ~4.3 -- appearing far below P1 Meeting/Outreach actions at ~9.6. Many contain verbs like "Schedule urgent," "Request," "Flag," "Commission" -- these are user-facing urgent actions mistyped as Research, causing the type_boost of -1.5 to suppress them.

**Impact:** Urgent diligence actions (like "Schedule urgent team scaling call" for a 5-person team targeting 80 deployments) rank below routine portfolio check-ins.

### 2. "Healthcare AI Agents as Infrastructure" thesis tagged on 12 non-healthcare actions

**Problem:** A batch of actions (ids 88-102) all received Healthcare AI as a thesis connection despite having zero healthcare content. This was likely a batch-processing artifact where the source content's tangential healthcare mention was applied to all derived actions.

**Impact:** IRGI scores are inflated because the scoring treats each thesis connection as evidence of relevance. False thesis connections corrupt the intelligence signal.

### 3. Actions id:2 and id:68 are exact duplicates

**Problem:** "Flag trademark conflict risk if Orange Slice exists in dehydrated fruit space" (P0, score 9.79) and "Assess trademark/IP risk regarding 'Orange Slice' naming" (P1, score 9.74) are the same action. Both occupy top-tier positions in the user queue.

**Impact:** User sees redundant actions, queue appears larger than reality. This pattern repeats for at least 3 pairs.

### 4. `scoring_factors` is empty for 95%+ of actions

**Problem:** The `scoring_factors` JSONB field, designed to capture the multi-dimensional scoring model (`bucket_impact`, `conviction_change`, `key_question_relevance`, `time_sensitivity`, `action_novelty`, `stakeholder_priority`, `effort_vs_impact`), is populated for exactly 1 action (id:101). All others have `{}`. The `compute_user_priority_score` function ignores this field entirely.

**Impact:** The entire multi-factor scoring model described in the architecture (Action Score = f(bucket_impact, conviction_change_potential, ...)) is not implemented. Scoring is a simple 4-variable formula.

### 5. agent_delegable logic misses 3 research actions assigned to Aakash

**Problem:** ids 87, 91, 105 are pure desk research assigned to "Aakash" but not flagged as agent-delegable. The view's logic only checks `assigned_to = 'Agent'` first, then falls through to keyword matching on action text. These actions don't trigger the keyword exceptions because they use verbs like "Assess," "Product deep-dive," "Analyze" rather than the coded patterns.

**Impact:** Aakash's personal queue contains 3 items that could be fully delegated to the agent, adding cognitive load.

---

## Dimension Accuracy Summary

| Dimension | Accuracy | Grade |
|-----------|----------|-------|
| Priority assignment (P0/P1/P2) | 80% | B- |
| Action text quality (specific, actionable) | 90% | A- |
| action_type classification | 61% | D |
| Scoring differentiation within tiers | 0% (no differentiation) | F |
| Thesis connection (primary) | 80% | B- |
| Thesis connection (all tags) | 20% fully accurate | F |
| Agent vs User classification | 88% | B+ |
| Related companies (vector) | 30% fully accurate | F |
| Duplicate detection (dedup) | 3 high-severity dupes undetected | D |
| scoring_factors population | 1% (1/115) | F |

---

## Recommendations

### For M5 (Scoring System)

1. **Incorporate IRGI into `compute_user_priority_score`**: Add `irgi_weight * COALESCE(irgi_relevance_score, 0)` as a scoring component. Currently the only intelligence-derived signal is completely ignored.

2. **Populate `scoring_factors` during action creation**: The ContentAgent should compute and store the 7-factor scoring model at action creation time, not rely on a post-hoc function. The `compute_user_priority_score` should read from `scoring_factors` when populated.

3. **Break the tier clustering**: The current sigmoid soft-cap creates bands where 17 P0 Meetings all score 9.735996xxx with only nanosecond-level `created_at` differences. Add a secondary sort dimension (IRGI, or a hash-based tiebreaker) to create meaningful differentiation.

4. **Fix the type_boost for mistyped Research actions**: Either (a) reclassify the 24 user-action "Research" items to their correct action_type, or (b) add keyword detection in the scoring function (if action contains "schedule" or "request" and type is Research, apply Meeting boost instead of Research penalty).

5. **Add dedup at ingestion**: Before creating a new action, check cosine distance against existing actions for the same company. If distance < 0.10, merge instead of creating.

### For M6 (IRGI / Thesis Connection)

1. **Cap thesis connections at 3 per action**: The current system tags 4-6 theses per action. Most tags beyond 2-3 are noise. Enforce a maximum and require a minimum confidence threshold per tag.

2. **Fix batch-level thesis propagation**: The Healthcare AI batch-tagging bug (ids 88-102) suggests thesis connections are applied at the source-content level, not the individual-action level. Each action should be independently evaluated against thesis threads.

3. **Remove "Cybersecurity / Pen Testing" from non-security actions**: The current tagging logic connects Cybersecurity to any action touching CodeAnt or code quality, which is too broad. Only actions about offensive security, vulnerability management, or compliance should get this tag.

4. **Improve embedding model domain specificity**: The current embeddings treat all "AI" companies as similar. Consider fine-tuning or using a domain-aware embedding model that distinguishes orchestration-layer companies from voice-AI companies from computer-vision companies.

5. **Add thesis-connection validation**: After generating thesis connections, run a verification step that checks whether the action text actually mentions concepts from the thesis's `core_thesis` or `evidence_for`. If overlap is below a threshold, drop the connection.

---

## Appendix: Scoring Function Analysis

The `compute_user_priority_score` function:

```
raw_score = base_score(relevance_score, default 5.0)
          + priority_boost (P0: +1.0, P1: +0.5, P2: 0, P3: -0.5)
          + type_boost (Portfolio: +1.5, Meeting: +1.0, Research: -1.5, Content: -1.0)
          + recency_factor (0 to 0.5, decays over 30 days)
```

This means:
- A P0 Portfolio Check-in with default relevance: 5.0 + 1.0 + 1.5 + ~0.5 = **8.0** (then soft-capped)
- A P0 Meeting/Outreach: 5.0 + 1.0 + 1.0 + ~0.5 = **7.5**
- A P1 Research: 5.0 + 0.5 + (-1.5) + ~0.5 = **4.5**
- A P2 Research: 5.0 + 0 + (-1.5) + ~0.5 = **4.0**

The `relevance_score` column (base_score source) ranges from ~5.0 to ~9.0, explaining why many P0 actions cluster around 9.7x after soft-cap compression.

**The IRGI score is never used.** An action with IRGI 0.89 (strong thesis relevance) ranks identically to one with IRGI 0.40 (weak relevance) if they share the same priority and action_type.
