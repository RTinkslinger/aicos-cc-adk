# Content Analysis Skill

Instructions for analyzing content for Aakash Kumar (MD at Z47/$550M fund + MD at DeVC/$60M fund). This skill defines the IDS methodology, priority buckets, and analysis framework.

---

## Context: Who This Is For

Aakash Kumar is a network-first investor managing two funds. He processes 7-8 meetings/day plus continuous content consumption. The AI CoS optimizes his action space by extracting investing-relevant intelligence from content.

**Core question for every piece of content:** "Does this help answer 'What's Next?' for Aakash?"

---

## IDS Methodology (Increasing Degrees of Sophistication)

IDS is Aakash's core operating methodology. Use this notation system in all analysis output.

### Notation

| Symbol | Meaning | Example |
|--------|---------|---------|
| `+` | Positive signal | `+ Strong founder-market fit` |
| `++` | Table-thumping positive (strong conviction) | `++ Multiple independent sources confirm TAM thesis` |
| `?` | Concern or open question | `? Unit economics unclear at scale` |
| `??` | Significant concern | `?? Regulatory risk could cap TAM` |
| `+?` | Positive but needs validation | `+? AI moat claimed but unverified` |
| `-` | Neutral or negative signal | `- Crowded market, no clear differentiation` |

### When to use each

- `++` : Reserve for convergent evidence from 2+ independent sources, or data points that directly support an active thesis at high conviction.
- `+` : Single positive signal, reasonable but not yet corroborated.
- `+?` : Promising but requires follow-up. Always pair with a specific validation action.
- `?` : Genuine uncertainty. Pair with a key question.
- `??` : Red flag. Should trigger a specific investigation or portfolio check.
- `-` : Weak or negative. Include only when it contradicts an existing positive signal.

---

## Priority Buckets (Ranked)

Every content analysis must identify which bucket(s) the content serves.

| Priority | Bucket | Weight | Description |
|----------|--------|--------|-------------|
| 1 | **New Cap Tables** | Highest | Content that helps identify amazing companies to invest in. Sector trends, emerging companies, founder signals. |
| 2 | **Deepen Existing Cap Tables** | High | Content relevant to portfolio companies. Competitive intel, market data, follow-on decision inputs. |
| 3 | **New Founders/Companies** | High | Content that surfaces backable founders via DeVC Collective pipeline. |
| 4 | **Thesis Evolution** | Lower (but never zero) | Content that evolves thesis lines. New frameworks, contrarian views, cross-domain connections. |

**Bucket assignment rules:**
- A single piece of content can serve multiple buckets. List all that apply.
- Bucket 1 gets highest scoring weight. A piece of content that opens new cap table opportunities scores higher than one that reinforces existing knowledge.
- Bucket 4 is the "intellectual fuel" bucket. Even when Buckets 1-3 are saturated, Bucket 4 content keeps the thesis engine running.

---

## Net Newness Categories

Classify every analyzed piece of content on this spectrum:

| Category | Definition | Scoring Impact |
|----------|-----------|---------------|
| **Mostly New** (>70% new) | Majority of insights are new to Aakash's knowledge base | Highest action potential |
| **Additive** | Builds on existing knowledge with meaningful new data points | Good action potential |
| **Reinforcing** | Confirms existing thesis/understanding without new data | Low action potential (strengthens conviction) |
| **Contra** | Challenges or contradicts existing thesis/understanding | High action potential (thesis stress-test) |
| **Mixed** | Contains both reinforcing and new/contra elements | Moderate action potential |

**Contra content is high-value.** It should always generate actions even if the overall score is moderate, because it stress-tests existing beliefs.

---

## Content Analysis Sequence

For every piece of content, follow this sequence:

### 1. Relevance Assessment
- Is this work-relevant? (Use work/personal keyword lists from youtube-extraction skill)
- Which priority buckets does it serve?
- What is the net newness?

### 2. Essence Extraction
Extract and structure:
- **Core arguments** -- The main claims or theses presented
- **Data points** -- Specific numbers, metrics, benchmarks
- **Frameworks** -- Mental models, decision frameworks, analytical tools
- **Key quotes** -- Verbatim quotes that capture essential insights
- **Predictions** -- Forward-looking claims with timeframes

### 3. Thesis Connection Mapping
For each active thesis thread in the Thesis Tracker:
- Does this content provide evidence for or against?
- Does it answer any open key questions?
- Does it raise new key questions?
- What is the evidence direction (for/against/mixed) and strength (Strong/Moderate/Weak)?

Query active thesis threads:
```bash
psql $DATABASE_URL -c "SELECT id, thread_name, conviction, status FROM thesis_threads WHERE status IN ('Active', 'Exploring') ORDER BY status, thread_name;"
```

### 4. Portfolio Connection Check
For each company mentioned or implied:
- Is it in the portfolio? Check Companies DB.
- What are the implications (competitive threat, partnership, market validation)?
- Any follow-on or exit considerations?

### 5. Action Proposal
Generate scored actions using the scoring skill. Each action must have:
- Clear description (what to do)
- Action type (Research, Meeting/Outreach, Thesis Update, Content Follow-up, Portfolio Check-in)
- Priority assignment (P0-P3)
- Reasoning (why this action matters)
- Thesis/portfolio connections

### 6. Watch Sections (for video content)
Identify specific timestamps worth watching:
- Sections with `++` or `??` signals
- Sections with novel frameworks or contrarian takes
- Sections with specific data points or company mentions

---

## Relevance Scoring (High / Medium / Low)

| Level | Criteria |
|-------|----------|
| **High** | Directly actionable for Buckets 1-2. Contains `++` signals. Names specific companies/people in Aakash's universe. Addresses open key questions. |
| **Medium** | Relevant to Buckets 3-4. Contains `+` signals. Tangential to active thesis threads. General industry insights. |
| **Low** | Marginally relevant. Reinforcing only. No clear action potential. Entertainment-adjacent. |

---

## Thesis Connections vs Bucket Assignment

These are distinct concepts:

- **Bucket assignment** answers: "Which of Aakash's 4 priority objectives does this content serve?" -- it's about the TYPE of value.
- **Thesis connections** answer: "Which specific thesis threads does this content provide evidence for?" -- it's about the SPECIFIC hypotheses.

A piece of content can serve Bucket 4 (Thesis Evolution) while connecting to multiple specific thesis threads (e.g., "Agentic AI Infrastructure" and "CLAW Stack Standardization").

---

## DigestData JSON Schema

The output of content analysis is a DigestData JSON object. Required fields:

```json
{
  "slug": "short-url-slug",
  "title": "Content Title",
  "channel": "Source Channel/Author",
  "duration": "HH:MM:SS or word count",
  "content_type": "Podcast | Interview | Talk | Tutorial | Panel | Article",
  "upload_date": "YYYY-MM-DD",
  "url": "https://source-url",
  "generated_at": "ISO-8601 timestamp",
  "relevance_score": "High | Medium | Low",
  "net_newness": "Mostly New | Additive | Reinforcing | Contra | Mixed",
  "connected_buckets": ["New Cap Tables", "Thesis Evolution"],
  "essence_notes": {
    "core_arguments": ["argument 1", "argument 2"],
    "data_points": ["data point 1"],
    "frameworks": ["framework 1"],
    "key_quotes": ["quote 1"],
    "predictions": ["prediction 1"]
  },
  "watch_sections": [
    {"timestamp": "12:30", "topic": "Topic description", "signal": "+?"}
  ],
  "contra_signals": ["contra 1"],
  "rabbit_holes": ["follow-up research topic 1"],
  "portfolio_connections": [
    {"company": "Company Name", "relevance": "description", "signal": "+"}
  ],
  "thesis_connections": [
    {"thread": "Thread Name", "evidence": "description", "direction": "for", "strength": "Moderate"}
  ],
  "new_thesis_suggestions": [
    {"name": "Suggested Thread Name", "core_thesis": "description", "trigger": "what in the content triggered this"}
  ],
  "proposed_actions": [
    {
      "action": "Action description",
      "type": "Research",
      "priority": "P1",
      "reasoning": "Why this matters",
      "thesis_connection": "Thread Name"
    }
  ]
}
```

---

## Quality Bars

### Minimum viable analysis
- Relevance score assigned
- At least 1 essence note category populated
- Net newness classified
- At least 1 bucket assigned
- Thesis connections checked (even if none found)

### Good analysis
All of the above, plus:
- 3+ essence note categories populated
- Specific thesis connections with evidence direction
- Portfolio connections checked
- At least 1 proposed action (if relevance >= Medium)
- Contra signals identified (even if none)

### Excellent analysis
All of the above, plus:
- Watch sections with timestamps (for video)
- Rabbit holes identified for follow-up
- New thesis suggestions where warranted
- Actions scored with full factor breakdown
