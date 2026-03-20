# Thesis Intelligence Quality Audit - M9

**Date:** 2026-03-20
**Scope:** All 8 thesis threads, 43 thesis-connected actions, 10 content digests, 2 Postgres functions
**Audit Type:** Intelligence accuracy review (not UX)

---

## Executive Summary

The thesis intelligence system is **operationally functional** but has **significant accuracy gaps** that degrade decision quality. The core problems:

1. **Confirmation bias is structural** -- 3 of 8 theses have HIGH or CRITICAL bias flags, and the bias detection function itself under-counts the problem
2. **Action-to-thesis connections are over-broad** -- 11 actions are tagged to 5-6 theses simultaneously, diluting signal
3. **Vector similarity for company matching is noisy** -- produces topically adjacent but thesis-irrelevant results for abstract theses
4. **suggest_actions_for_thesis produces false connections** -- the digest gap suggestion logic uses overly loose matching, recommending coding podcasts as USTOL/Aviation follow-ups
5. **62.6% of actions have NO thesis connection** -- 72 of 115 actions are thesis-orphaned

**Overall Intelligence Accuracy Score: 6.2/10**

---

## Section 1: Per-Thesis Assessment

### Thesis 1: Cybersecurity / Pen Testing
| Dimension | Score | Assessment |
|-----------|-------|------------|
| Conviction calibration | 7/10 | "Medium" is appropriate -- strong portfolio proof point (StepSecurity) but thesis scope is still broad |
| Evidence FOR quality | 8/10 | Excellent. StepSecurity metrics are concrete (5x ARR, 4x customers, 13M builds/week). YC batch signals are specific and named. Market data cited ($13.97B, 47% YoY). |
| Evidence AGAINST quality | 3/10 | **Weak.** Only 3 points, all generic ("can you really productize it?", "crowded space"). No specific contra-evidence: no failed companies, no market data showing ceiling, no incumbent counter-moves quantified. |
| Key questions | 7/10 | 3 open questions, all specific and thesis-advancing (StepSecurity category creation, MCP attack surface durability, ARR/timeline) |
| Thesis definition | 7/10 | Well-scoped service-to-platform thesis, but title "Pen Testing" is narrower than actual scope (now covers agent security, MCP governance, supply chain attacks) |
| **Bias flag** | **HIGH** | 10:1 FOR:AGAINST ratio. The bias detection is CORRECT here. |

**Critical finding:** Evidence-against is straw-man quality. The three points are the kind of generic objections someone would generate without research. A credible contra-evidence section would include: (1) specific failures of security-platform transitions (e.g., Rapid7 ARR stagnation), (2) Cisco/Palo Alto MCP product launch details and competitive threat assessment, (3) customer churn data from existing security platforms.

---

### Thesis 2: Healthcare AI Agents as Infrastructure
| Dimension | Score | Assessment |
|-----------|-------|------------|
| Conviction calibration | 5/10 | **"New" is wrong.** Evidence includes Confido 10x growth (150K-1M patients), 80%+ automation rates, PE adoption signals, and multiple content agent enrichments. This should be at least "Medium". |
| Evidence FOR quality | 8/10 | Strong concrete metrics from Confido (portfolio company). Gokul Rajaram Non-Consumption framework is well-attributed. Wang healthcare data regulatory angle is specific. |
| Evidence AGAINST quality | 6/10 | Decent: "976 active competitors" is a concrete number. EHR integration duality (moat OR ceiling) is a genuine insight. Voice-AI-vs-broader-workflow question is legitimately open. |
| Key questions | 2/10 | **0 open key questions.** For a thesis with "New" conviction and active exploration, this is a data quality failure. The key_questions_json has empty open and answered arrays. |
| Thesis definition | 8/10 | Well-scoped: PE-backed rollup platforms + voice AI + EHR integration. Clear investment hook. |
| **Bias flag** | OK | 2.33:1 ratio is reasonable |

**Critical finding:** Conviction label "New" is stale -- does not reflect the accumulated evidence. Either conviction should be upgraded or the evidence is not being synthesized into conviction properly. Also, zero key questions means the suggest_actions function cannot generate its highest-priority suggestion type (research from open questions), degrading action quality downstream.

---

### Thesis 3: Agentic AI Infrastructure
| Dimension | Score | Assessment |
|-----------|-------|------------|
| Conviction calibration | 8/10 | "High" is justified. Dense evidence from multiple credible sources (a16z, Insight Partners, Accel, Scale AI CEO, Anthropic). Portfolio proof points (StepSecurity, CodeAnt). Market validation signals (Cisco AI BOM, Linear MCP). |
| Evidence FOR quality | 9/10 | The strongest evidence section across all theses. Multiple named sources with credentials. Specific data points (E2B 80ms sandbox, $27B Cursor valuation, 3-person vs Google/OpenAI). Clear timestamps showing ongoing accumulation. |
| Evidence AGAINST quality | 7/10 | Genuinely challenging: model providers building own harness layers (vertical integration risk), open-source fragmentation (DSPY, LangChain), and Murdock's own admission that 80% of agent-layer investments return <1.3x. These are not straw-men. |
| Key questions | 5/10 | Only 1 open question ("Do MCP gateway/security companies become part of this thesis or a Cybersecurity sub-thread?"). For a thesis this active, there should be more -- e.g., timing of consolidation, which sub-layers commoditize first, infrastructure vs middleware distinction. |
| Thesis definition | 9/10 | Clearly articulated: harness/orchestration layer, not models or apps. The "connective tissue" framing is precise and investable. |
| **Bias flag** | **HIGH** | 5.25:1 ratio. Bias detection CORRECT but the contra-evidence that exists is higher quality than most theses. The ratio overstates the bias problem here because the AGAINST evidence is substantive. |

**Critical finding:** The bias is VOLUME-based (21 FOR items vs 4 AGAINST), but the AGAINST items are high-quality. The detect_thesis_bias function counts newlines, not evidence quality. This is a function design flaw -- it treats "80% of agent-layer investments return <1.3x" the same as "crowded space" when the former is far more significant.

---

### Thesis 4: SaaS Death / Agentic Replacement
| Dimension | Score | Assessment |
|-----------|-------|------------|
| Conviction calibration | 7/10 | "High" conviction with the most balanced evidence set (1.38:1 ratio). The nuance from Gokul (8 moats framework), Thoma Bravo/Vista counterpoint (Clements), and Lemkin/O'Driscoll's "why we got SaaS apocalypse wrong" all enrich the picture. |
| Evidence FOR quality | 9/10 | Strongest source diversity: Klarna (operational proof), Bret Taylor (platform framing), Jenny Wen/Anthropic (engineering practice), Ben Horowitz (10x market mechanism), Jerry Murdock ($90B AUM credibility), Wang/Scale AI (end of software endorsement). |
| Evidence AGAINST quality | 8/10 | **Best contra-evidence across all theses.** Includes specific counters: Clements saying Thoma Bravo/Vista in "GREAT time", Lemkin/O'Driscoll questioning SaaS apocalypse framing, Murdock's own hedge about Cursor pivot window, Loh's rural access gap, regulatory/compliance drag in healthcare/finance. |
| Key questions | 2/10 | **0 open key questions.** Same problem as Healthcare thesis -- empty arrays despite rich evidence that should generate questions. |
| Thesis definition | 8/10 | Clear and provocative. The evolution from "SaaS dies" to "weak-moat SaaS dies" (Gokul 8-moats nuance) is reflected in evidence but NOT in the core_thesis text, which still reads as blanket replacement. |
| **Bias flag** | OK | 1.38:1 -- the most balanced thesis |

**Critical finding:** The core_thesis text ("Traditional SaaS moats dissolve... Systems of record become commodity backends") is now MORE extreme than the evidence supports. The evidence shows nuanced survival of strong-moat SaaS (Clements, Gokul framework), but the thesis statement has not been updated to reflect this evolution. This is a thesis drift problem -- the evidence matured but the thesis statement stayed at its initial, more aggressive framing.

---

### Thesis 5: USTOL / Aviation / Deep Tech Mobility
| Dimension | Score | Assessment |
|-----------|-------|------------|
| Conviction calibration | 8/10 | "Low" is honest and appropriate. Only 2 evidence-for points (one generic about cost curves, one content-agent injection about Scale AI/DOD). No pipeline companies. |
| Evidence FOR quality | 4/10 | Weak. First point is entirely generic ("Electrification cost curves declining rapidly. Defense budgets globally increasing.") -- no specific data. Second point (Wang/Scale AI/DOD) is tangentially related at best -- it's about defense-AI data infrastructure, not USTOL/aviation specifically. |
| Evidence AGAINST quality | 5/10 | Reasonable for the stage: certification timelines (5-10 years), capital intensity, regulatory risk. But also generic -- no specific companies that failed, no quantified capital requirements. |
| Key questions | 2/10 | **0 open key questions.** For an early "Low" conviction thesis in "Exploring" status, the absence of key questions is a critical gap. The entire purpose of this stage is question generation. |
| Thesis definition | 5/10 | The convergence framing (electrification + defense + logistics) is interesting but lacks sharpness. "Deep tech mobility" is vague. |
| **Bias flag** | OK | 2:1 ratio, but on a tiny evidence base |

**Critical finding:** The content agent injected Wang/Scale AI evidence into this thesis, but it is NOT actually about USTOL/aviation. The evidence is about defense-AI data infrastructure generally. This is a **false attribution** -- the content agent's thesis-matching is overly loose, connecting any defense-adjacent content to the USTOL thesis.

---

### Thesis 6: CLAW Stack Standardization & Orchestration Moat
| Dimension | Score | Assessment |
|-----------|-------|------------|
| Conviction calibration | 6/10 | "Medium" feels high for what is essentially a subset of Thesis 3 (Agentic AI Infrastructure). The evidence is largely the same sources making the same points. |
| Evidence FOR quality | 6/10 | Solid attribution (Murdock, a16z, Wang), but substantially overlaps with Thesis 3 evidence. The CLAW-specific framing (Claude + orchestration + open-source triaging + ARM chips) is in the thesis definition but not well-supported by the evidence, which mostly discusses orchestration generically. |
| Evidence AGAINST quality | 5/10 | Two points, both reasonable (open-source fragmentation, vertical integration risk). Identical to Thesis 3 contra-evidence. |
| Key questions | 1/10 | **0 open key questions.** |
| Thesis definition | 5/10 | **Problematic.** The "CLAW" acronym definition (Claude/reasoning + orchestration + open-source triaging + ARM chips) is highly specific but the evidence doesn't validate these specific components. No evidence addresses ARM chips. "Claude" as the reasoning layer suggests betting on one model provider, which contradicts the "open-source" component. |
| **Bias flag** | OK | 2.5:1 ratio |

**Critical finding:** This thesis has a **differentiation problem** -- it is not clearly distinct from Thesis 3 (Agentic AI Infrastructure). The evidence for both theses overlaps heavily (Murdock, a16z, orchestration layer). The CLAW-specific framing (ARM chips, Claude-specific) is not validated by any evidence. This thesis should either be merged into Thesis 3 as a sub-thread or given truly distinctive evidence.

---

### Thesis 7: Agent-Friendly Codebase as Bottleneck
| Dimension | Score | Assessment |
|-----------|-------|------------|
| Conviction calibration | 7/10 | "Medium" is appropriate. Strong signals from practitioners (Eric, Steinberger) and market validation (Cursor $2B ARR, $27B valuation), but limited to a narrow set of sources. |
| Evidence FOR quality | 7/10 | Good practitioner evidence (Stanford instructor, production experience). Market data point (Cursor $2B ARR). Portfolio relevance (CodeAnt AI). |
| Evidence AGAINST quality | 3/10 | Only 2 points, both generic. "Foundation models improving rapidly" is a hand-wave without evidence. "May be a feature, not a company" is a legitimate question but unresearched. |
| Key questions | 1/10 | **0 open key questions.** |
| Thesis definition | 7/10 | Clear articulation: agent-readiness as bottleneck, tools to measure/improve it. Actionable for deal sourcing. |
| **Bias flag** | OK | 3:1 ratio |

**Critical finding:** The evidence-against needs genuine research. Specific contra-evidence should include: (1) Claude/GPT performance benchmarks on messy vs clean codebases (is the gap actually closing?), (2) GitHub Copilot agent mode adoption data, (3) Cursor's own approach to handling messy code. The current contra-evidence is lazy hypothesis-generation, not research.

---

### Thesis 11: AI-Native Non-Consumption Markets
| Dimension | Score | Assessment |
|-----------|-------|------------|
| Conviction calibration | 6/10 | "New" is appropriate -- single source (Gokul Rajaram), single evidence point. |
| Evidence FOR quality | 6/10 | Well-attributed (Gokul, 20VC, specific timestamp). Names concrete examples (Granola, Gamma). But a single data point supporting an entire thesis is thin. |
| Evidence AGAINST quality | 0/10 | **ZERO evidence against.** No contra-evidence whatsoever. |
| Key questions | 8/10 | 3 open questions, all specific and thesis-advancing: TAM comparison vs displacement, terminal multiple hypothesis, India-specific opportunities for DeVC. Best key_questions of any thesis. |
| Thesis definition | 7/10 | Clear framing: non-consumption (creating new demand) vs displacement (replacing existing). Investment-applicable distinction. |
| **Bias flag** | **CRITICAL** | Zero contra evidence. Bias detection is CORRECT. |

**Critical finding:** This is the newest thesis and its single-source status is expected. However, the key questions are excellent -- they would generate the evidence needed to mature this thesis. The contrast with theses that have 0 key questions despite rich evidence is stark.

---

## Section 2: Evidence Quality Grades

| Thesis | FOR Grade | AGAINST Grade | Balance | Overall |
|--------|-----------|---------------|---------|---------|
| Cybersecurity / Pen Testing | A- | D+ | Poor | C+ |
| Healthcare AI Agents | A- | B- | Fair | B |
| Agentic AI Infrastructure | A | B | Good | A- |
| SaaS Death / Agentic Replacement | A | A- | **Excellent** | A |
| USTOL / Aviation | D+ | C | Fair | D+ |
| CLAW Stack | B- | C | Fair | C+ |
| Agent-Friendly Codebase | B | D+ | Poor | C+ |
| Non-Consumption Markets | B- | F | Critical | D |

**Evidence quality scoring criteria:**
- **A:** Named sources with credentials, specific data points, timestamps, multiple independent signals
- **B:** Named sources, some data, but thinner or more repetitive
- **C:** Generic points that could apply to any thesis, or very thin
- **D:** Missing, straw-man, or factually unsupported
- **F:** Absent

---

## Section 3: Thesis-to-Action Connection Accuracy

### Over-connection Problem

11 actions are tagged to 5-6 theses simultaneously. Specific failures:

| Action ID | Action | # Theses | Problem |
|-----------|--------|----------|---------|
| 87 | "Assess Z47 and DeVC's own agent deployment readiness" | 6 | Why is this tagged to Cybersecurity or USTOL? It is about internal operational readiness. |
| 91 | "Product deep-dive: Unifize + CodeAnt" | 6 | Why Healthcare AI Agents? Neither company operates in healthcare. |
| 106 | "Map human-agent orchestration platform landscape" | 6 | Cybersecurity connection is a stretch -- mapping platforms is not a security action. |
| 108 | "Map and reach out to E2B, orchestration layer infra" | 6 | Cybersecurity tag is false -- E2B sandbox is compute infra, not security. |
| 96 | "Conduct deep research: IMO 4/6 solver mechanics" | 5 | Why Healthcare AI Agents? An IMO math solver has nothing to do with healthcare. |

**Pattern:** The content agent appears to be tagging Cybersecurity and AI-Native Non-Consumption Markets to nearly every AI-related action regardless of actual relevance. These two theses act as "catch-all" tags.

### Under-connection Problem

USTOL / Aviation has only 2 connected actions. One of them (ID 103, "Research defense-AI data infrastructure") is also tagged to Agentic AI Infrastructure and AI-Native Non-Consumption Markets. Only 1 action (ID 3, "Intro to ISRO") is solely about USTOL.

### Relevance Score Analysis

- **Low-confidence connections (<0.6):** Only 2 actions (ID 3 at 0.54, ID 37 at 0.57). The system correctly gives low scores to weak connections, but these actions still appear in results without any filtering threshold.
- **High-confidence connections (>0.85):** 8 actions. Spot-checking confirms these are genuinely relevant (e.g., ID 109 "Research OpenClaw/NanoClaw" at 0.89 for Agentic AI Infra + CLAW Stack -- correct).

**Connection Accuracy Score: 5.5/10** -- high-confidence connections are accurate, but the over-tagging problem and Cybersecurity/Non-Consumption catch-all pattern significantly degrade precision.

---

## Section 4: suggest_actions_for_thesis Function Quality

### Function Design Issues

1. **Digest gap suggestions use overly loose matching.** The function uses `similarity()` with a 0.1 threshold and `ILIKE '%' || v_thread_name || '%'` on `digest_data::text`. This means ANY digest that mentions ANY thesis by name (even in another thesis's connection block) will match. Result: USTOL/Aviation gets "Follow up on: How to code with AI agents" as a suggestion because the digest JSON mentions USTOL tangentially.

2. **Evidence gap detection is character-count based only.** `v_against_length < v_for_length * 0.2` catches gross imbalances but misses quality differences. Thesis 3 (Agentic AI Infra) gets a "Contra research" suggestion despite having the second-best contra-evidence quality.

3. **Company gap suggestions are all-or-nothing.** The function checks if `key_companies IS NOT NULL` and if there are fewer than 5 active actions. It then suggests "Evaluate: [entire key_companies list]" as a single action. For Thesis 5 (USTOL), this produces: "Evaluate: Early exploration -- no specific pipeline companies yet" -- literally suggesting the user evaluate a status message, not a company.

4. **No deduplication against existing actions.** The function checks for action count per thesis but does not check if the SPECIFIC suggested action already exists. The "Follow up on: Gokul Rajaram 8 Moats" suggestion appears for 6 of 8 theses because the digest mentions multiple theses.

### Per-Thesis Suggestion Quality

| Thesis | Suggestions | Accuracy | Notes |
|--------|------------|----------|-------|
| Cybersecurity (1) | 5 | 6/10 | Key question suggestions are good. Digest follow-ups correct. |
| Healthcare (2) | 3 | 5/10 | "Follow up on Druckenmiller" is a stretch for healthcare. Generic conviction review. |
| Agentic AI (3) | 4 | 7/10 | Key question suggestion relevant. Contra research justified. Digest follow-ups correct. |
| SaaS Death (4) | 3 | 5/10 | All generic: two digest follow-ups and a periodic review. No key questions to draw from (0 open). |
| USTOL (5) | 4 | 2/10 | **Worst output.** "Evaluate: Early exploration" is nonsensical. Coding podcast follow-ups are false connections. |
| CLAW Stack (6) | 3 | 6/10 | Temporal digest follow-up is highly relevant. Contra research justified. |
| Agent Codebase (7) | 3 | 5/10 | Digest follow-ups are loosely relevant. Contra research justified. |
| Non-Consumption (11) | 5 | 8/10 | **Best output.** Key questions are specific and actionable. Digest follow-up relevant. |

**suggest_actions overall accuracy: 5.5/10**

---

## Section 5: Bias Detection Accuracy

The `detect_thesis_bias()` function correctly identifies:
- **AI-Native Non-Consumption Markets** (CRITICAL: Zero contra evidence) -- CORRECT
- **Cybersecurity / Pen Testing** (HIGH: >5x FOR:AGAINST ratio) -- CORRECT
- **Agentic AI Infrastructure** (HIGH: >5x FOR:AGAINST ratio) -- PARTIALLY CORRECT (volume bias exists but quality of contra-evidence is high)

### Function Design Flaws

1. **Counts newlines, not evidence items.** The function splits on `\n` and counts array elements. A single evidence item with a paragraph of supporting detail counts as multiple items if it contains line breaks. This inflates FOR counts (which tend to be more verbose) more than AGAINST counts.

2. **No quality weighting.** "Crowded space" counts the same as "80% of agent-layer investments return <1.3x (Murdock, Insight Partners)." A quality-weighted bias score would show Thesis 3's contra-evidence is actually substantive despite the volume imbalance.

3. **Missing MEDIUM tier in results.** The function defines a MEDIUM threshold (>3x ratio) but no thesis currently falls in that range. The jump from OK to HIGH is too large -- Thesis 7 (Agent-Friendly Codebase) at 3:1 is flagged OK despite genuinely weak contra-evidence.

**Bias detection accuracy: 6/10** -- directionally correct but newline-counting is a flawed proxy for evidence balance.

---

## Section 6: Vector Similarity / Company Matching

### Results Assessment

| Thesis | Top 5 Match Quality | Notes |
|--------|---------------------|-------|
| Cybersecurity (1) | **9/10** | StepSecurity (#1, 0.222), Offgrid Security, 56Secure, Kasper AI, Astra Security -- all genuine security companies. Portfolio company ranks first. Excellent. |
| Healthcare AI (2) | **9/10** | Confido Health (#1, 0.228), HealthWorksAI, Pharmie AI, Dental AI -- domain-accurate. Portfolio company ranks first. Excellent. |
| Agentic AI (3) | **5/10** | "Agentic AI" the company (#1) is name-matching, not thesis-matching. dot agent, Unsiloed AI, Hosted AI are generic AI companies with "AI" in the name, not specifically infrastructure plays. |
| SaaS Death (4) | **4/10** | dot agent, Vantara AI, Samora AI -- generic AI agents. Unifize (#9) is relevant (portfolio SaaS company). But the top results are AI-buzzword companies, not SaaS replacement case studies. |
| USTOL / Aviation (5) | **8/10** | Green Propulsion Aero, Skyroot Aerospace, FEDS Drone-powered, Sarla Aviation -- domain-relevant companies. Good embedding quality for this thesis. |
| CLAW Stack (6) | **3/10** | Unsiloed AI, Kestrel AI, Alchemyst AI -- generic AI companies. None are building orchestration/standardization layers. The abstract CLAW concept does not embed well into company-matching. |
| Agent Codebase (7) | **7/10** | Kestrel AI, CodeAnt (#2, portfolio), Unsiloed AI, dot agent, ProactAI -- CodeAnt is relevant. Others are generically AI/agent companies but the domain proximity is closer. |
| Non-Consumption (11) | **2/10** | Gaana AI, Jivi AI, gAI Ventures, Coinvent AI, Brihaspati AI -- these are just Indian AI companies with "AI" in their names. None represent non-consumption market creation. The thesis concept is too abstract for embedding-based matching. |

**Vector similarity accuracy: 5.9/10** -- works well for domain-specific theses (cybersecurity, healthcare, aviation) but fails for abstract/conceptual theses (CLAW, Non-Consumption, SaaS Death). The embeddings match on topical keywords, not on the strategic concept.

---

## Section 7: Structural Issues

### 1. Thesis Overlap / Deduplication

Theses 3 (Agentic AI Infrastructure) and 6 (CLAW Stack) share:
- Same sources (Murdock, a16z, Poetic)
- Same evidence direction
- Same key companies (E2B, Poetic, CodeAnt, StepSecurity)
- Same contra-evidence (open-source fragmentation, vertical integration)

**Recommendation:** Merge Thesis 6 into Thesis 3 as a sub-thread, or clearly delineate the CLAW-specific claims that differentiate it.

### 2. Key Questions Distribution

| Thesis | Open Questions | Status |
|--------|---------------|--------|
| Cybersecurity | 3 | Good |
| Healthcare AI | 0 | **Gap** |
| Agentic AI | 1 | Thin |
| SaaS Death | 0 | **Gap** |
| USTOL / Aviation | 0 | **Gap** |
| CLAW Stack | 0 | **Gap** |
| Agent Codebase | 0 | **Gap** |
| Non-Consumption | 3 | Good |

5 of 8 theses have ZERO open key questions. This directly degrades the suggest_actions function (its highest-priority suggestion type draws from open questions).

### 3. Content Agent Thesis Matching

The content_digests table shows thesis_connections are stored in digest_data JSON with strength ratings ("Strong", "Moderate"). This is good structured data. However, the thesis names in digest connections sometimes differ from the canonical thesis_threads.thread_name:
- "Healthcare AI Agents" vs "Healthcare AI Agents as Infrastructure"
- "CLAW Stack Standardization" vs "CLAW Stack Standardization & Orchestration Moat"

These mismatches would cause text-based joins to fail silently.

### 4. Orphaned Actions

72 of 115 actions (62.6%) have no thesis_connection. This is a large intelligence gap -- these actions exist outside the thesis framework entirely. Without reviewing each, it is impossible to know how many SHOULD have thesis connections that are missing.

---

## Section 8: Recommendations for M6 IRGI Improvements

### P0 -- Critical (Intelligence accuracy directly affected)

1. **Populate key_questions_json for all theses.** 5 of 8 have empty open question arrays. This is the single highest-leverage fix because it cascades into better suggest_actions output and forces explicit articulation of what evidence would change conviction.

2. **Fix detect_thesis_bias to count evidence items, not newlines.** Current approach splits on `\n` which inflates verbose evidence blocks. Count distinct evidence items using the `++`/`+`/`?`/`??` prefix markers that already exist in the evidence text as a structured delimiter.

3. **Add a thesis_connection relevance threshold.** Actions with IRGI scores below 0.6 (currently 2 actions) or tagged to 5+ theses (currently 11 actions) should be flagged for manual review rather than silently included. Consider a hard cap of 3 thesis connections per action.

4. **Update core_thesis text for SaaS Death (Thesis 4).** The thesis statement is now more extreme than its own evidence supports. The Gokul 8-moats nuance (weak-moat SaaS dies, strong-moat survives) should be reflected in the core_thesis definition.

### P1 -- High (Intelligence quality improvement)

5. **Upgrade Healthcare AI conviction from "New" to "Medium".** The evidence base (Confido 10x growth, 80% automation, PE adoption, content agent enrichments) clearly exceeds "New" threshold.

6. **Strengthen evidence-against across all theses.** Every thesis except SaaS Death (4) has weak contra-evidence. Add a pipeline step or prompt instruction that requires the content agent to actively seek and attribute contra-evidence from the same sources it processes.

7. **Fix suggest_actions digest gap matching.** Replace the loose `similarity() > 0.1` with a minimum threshold of 0.3, and add an exclusion for digest-thesis connections where the strength is "Weak" or absent. The current logic is generating false follow-ups (coding podcasts for USTOL).

8. **Resolve Thesis 3 / Thesis 6 overlap.** Either merge CLAW Stack into Agentic AI Infrastructure as a sub-thread, or add distinct evidence that validates the CLAW-specific claims (ARM chips, Claude-specific reasoning layer) independently.

### P2 -- Moderate (System design improvement)

9. **Add quality-weighted bias detection.** Supplement the volume ratio with a character-length-weighted ratio: `SUM(LENGTH(each_against_item)) / SUM(LENGTH(each_for_item))`. This would reduce false HIGH flags for theses like Agentic AI Infra where contra-evidence is substantive but fewer in number.

10. **Improve vector similarity for abstract theses.** For theses where the top-5 nearest companies have cosine distance > 0.30 (Agentic AI Infra: 0.295, CLAW Stack: 0.318, Non-Consumption: 0.247), supplement embedding-based matching with keyword/tag-based matching from company descriptions. The embedding approach fails for conceptual theses that do not map onto company-name semantics.

11. **Audit orphaned actions.** Run a one-time review of the 72 thesis-unconnected actions to determine: (a) how many should have thesis tags, (b) whether the content agent is failing to tag thesis connections during action generation, (c) whether pre-content-agent actions were never backfilled.

12. **Normalize thesis name references.** Content digest thesis connections use abbreviated names ("Healthcare AI Agents", "CLAW Stack Standardization") that do not match canonical thread_name values. Add a lookup/alias layer or enforce canonical names at write time.

---

## Appendix: Raw Scoring Summary

| Thesis | Conviction Cal. | Evidence FOR | Evidence AGAINST | Key Questions | Thesis Def. | Bias | Vector Sim. | Action Conn. | Suggest Actions | **Avg** |
|--------|-----------------|-------------|------------------|---------------|-------------|------|-------------|-------------|-----------------|---------|
| 1. Cybersecurity | 7 | 8 | 3 | 7 | 7 | HIGH | 9 | 7 | 6 | **6.8** |
| 2. Healthcare AI | 5 | 8 | 6 | 2 | 8 | OK | 9 | 6 | 5 | **6.1** |
| 3. Agentic AI | 8 | 9 | 7 | 5 | 9 | HIGH | 5 | 7 | 7 | **7.1** |
| 4. SaaS Death | 7 | 9 | 8 | 2 | 8 | OK | 4 | 6 | 5 | **6.1** |
| 5. USTOL | 8 | 4 | 5 | 2 | 5 | OK | 8 | 4 | 2 | **4.8** |
| 6. CLAW Stack | 6 | 6 | 5 | 1 | 5 | OK | 3 | 5 | 6 | **4.7** |
| 7. Agent Codebase | 7 | 7 | 3 | 1 | 7 | OK | 7 | 5 | 5 | **5.3** |
| 11. Non-Consumption | 6 | 6 | 0 | 8 | 7 | CRIT | 2 | 4 | 8 | **5.1** |
| **System Average** | **6.8** | **7.1** | **4.6** | **3.5** | **7.0** | -- | **5.9** | **5.5** | **5.5** | **5.7** |

**Weakest dimension system-wide: Key Questions (3.5/10)** -- this is the single biggest drag on intelligence quality.

**Strongest dimension system-wide: Evidence FOR (7.1/10)** -- the content pipeline is effective at accumulating supporting evidence.

---

*Audit performed by Intelligence Quality Reviewer. Data sourced from Supabase project llfkxnsfczludgigknbs, all 8 thesis_threads rows, 43 thesis-connected actions_queue rows, 10 published content_digests, and 2 Postgres functions (detect_thesis_bias, suggest_actions_for_thesis).*
