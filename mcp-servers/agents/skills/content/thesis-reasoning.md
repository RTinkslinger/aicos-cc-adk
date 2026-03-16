# Thesis Reasoning Skill

Instructions for reasoning about thesis threads -- the AI-managed conviction engine that tracks investment hypotheses.

---

## Conviction Spectrum

Thesis threads move through two dimensions: **maturity** (how well-formed) and **strength** (how confident).

### Maturity Stages

| Stage | Meaning | Typical Evidence |
|-------|---------|-----------------|
| **New** | Just identified from a single signal. Minimal evidence. | 1 content piece, 1 meeting mention, 1 observation. |
| **Evolving** | Active evidence accumulation. Direction not yet clear. | 3-5 data points, mixed signals, key questions being formulated. |
| **Evolving Fast** | Rapid signal flow. Thesis crystallizing quickly. Velocity signal = pay attention. | Multiple signals arriving within days. Independent source convergence. |

### Strength Levels (well-formed thesis only)

| Level | Meaning | Evidence Profile |
|-------|---------|-----------------|
| **Low** | Well-formed thesis but evidence is weak. May be parked. | Key questions mostly unanswered. More `?` than `+` signals. |
| **Medium** | Well-formed, moderate evidence strength. Worth continued tracking. | Mix of answered questions and open ones. Balance of `+` and `?` signals. |
| **High** | Well-formed, strong convergent evidence. Investable. | Most key questions answered positively. Strong `++` signals. Multiple independent confirmations. |

### Lifecycle Transitions

```
New -> Evolving        (when 2+ evidence blocks accumulated)
Evolving -> Evolving Fast  (when 3+ signals arrive within 7 days)
Evolving/Evolving Fast -> Low/Medium/High  (when thesis is well-articulated and evidence direction is clear)
Any -> Low             (when evidence weakens)
Low -> Medium          (when new positive evidence arrives)
Medium -> High         (when strong convergent evidence from 2+ independent sources)

Auto-park trigger: No new evidence for 30+ days AND maturity is still New/Evolving
```

---

## CONVICTION GUARDRAIL (MANDATORY)

**Never set the conviction field autonomously.** This is a hard rule.

When evidence suggests conviction should change:
1. Provide the evidence (with IDS notation).
2. State your assessment of direction and strength.
3. Recommend a conviction level change.
4. Let Aakash (or the human reviewing) make the final call.

**Why:** Conviction drives action scoring weights, which drives what Aakash spends his time on. This is a human judgment call, not an AI decision.

**What you CAN do autonomously:**
- Create new thesis threads (always starts at Conviction = "New")
- Append evidence blocks (for/against)
- Update key questions (mark answered, add new)
- Update Investment Implications
- Update Key Companies and Key People

---

## Key Questions Lifecycle

Key questions are the mechanism by which conviction moves. They live as page content blocks in Notion.

### Format

**Open question:**
```
[OPEN] What is the enterprise adoption rate for MCP integrations? -- Added 2026-03-10 via ContentAgent
```

**Answered question:**
```
[ANSWERED 2026-03-15 via ContentAgent] What is the enterprise adoption rate for MCP integrations? -> 23% of Fortune 500 evaluating, 8% deployed. Evidence: ++ (a16z enterprise survey data)
```

### Lifecycle Rules

1. **Creating questions:** When content raises an important uncertainty, create an `[OPEN]` question. Tag with source agent and date.

2. **Answering questions:** When evidence addresses an open question:
   - Mark as `[ANSWERED YYYY-MM-DD via SourceAgent]`
   - Include the answer summary
   - Rate evidence strength with IDS notation

3. **Answer becomes evidence:** When a question is answered:
   - Positive answer (`+` or `++`) -> Add to "Evidence For" property
   - Negative answer (`?` or `??`) -> Add to "Evidence Against" property
   - Mixed (`+?`) -> Add to both with context

4. **New questions from answers:** Answering one question often raises new ones. Create new `[OPEN]` entries for these.

5. **Key Questions property:** Update the summary count: "3 open, 2 answered" (or whatever the current count is).

---

## Evidence Assessment Framework

When processing new evidence (from content, meetings, research):

### Evidence Direction

| Direction | When to Use |
|-----------|------------|
| **For** | Evidence supports the thesis. Positive data points, confirming signals. |
| **Against** | Evidence challenges the thesis. Negative data, contradictions, risks. |
| **Mixed** | Evidence contains both supporting and challenging elements. |

### Evidence Strength

| Strength | Criteria |
|----------|---------|
| **Strong** | Primary source data, direct observation, multiple independent confirmations. Expert with domain authority. Quantitative data with clear methodology. |
| **Moderate** | Secondary source analysis, single expert opinion, reasonable inference from data. Qualitative but credible signal. |
| **Weak** | Anecdotal, speculative, single data point without context, potentially biased source. |

### Evidence Notation for Properties

Append to "Evidence For" or "Evidence Against" properties using this format:

```
[NEW 2026-03-15] ++ Enterprise MCP adoption at 23% of Fortune 500 (a16z survey). 3 portfolio companies considering. Source: ContentAgent/podcast-slug
```

Key rules:
- **Always append, never overwrite.** Evidence is cumulative.
- **Always include timestamp and source.**
- **Use IDS notation** (`+`, `++`, `?`, `??`, `+?`, `-`).
- **Include specific data points** -- not just "positive signal" but what the signal actually says.

---

## Creating New Thesis Threads

### Criteria for new thread creation

Create a new thesis thread when you identify:
1. A **pattern** worth tracking -- not a one-off observation, but a recurring theme across 2+ signals.
2. An **investment implication** -- the pattern, if true, has consequences for how Aakash should allocate capital or time.
3. A **testable hypothesis** -- there are specific key questions that would confirm or refute the thesis.

### What a new thread needs

```bash
psql $DATABASE_URL -c "INSERT INTO thesis_threads (thread_name, conviction, status, core_thesis, key_questions, evidence_for, evidence_against, connected_buckets, discovery_source, date_discovered, notion_synced) VALUES (
  'Thread Name',
  'New',
  'Exploring',
  'The core thesis statement -- what is the durable value insight?',
  '1 open, 0 answered',
  '[2026-03-15] + Initial signal description. Source: ContentAgent/content-slug',
  '',
  '{\"Thesis Evolution\"}',
  'ContentAgent',
  '2026-03-15',
  FALSE
);"
```

**Always start at Conviction = "New" and Status = "Exploring".** No exceptions.

### Don't create threads for:
- One-off interesting facts with no investment implication
- Company-specific observations (those go in Companies DB)
- Person-specific notes (those go in Network DB)
- Short-term market events (those go in Actions Queue as research tasks)

---

## Active Thesis Threads Reference

Query current active threads before every analysis:

```bash
psql $DATABASE_URL -c "SELECT thread_name, conviction, status, core_thesis FROM thesis_threads WHERE status IN ('Active', 'Exploring') ORDER BY CASE status WHEN 'Active' THEN 1 WHEN 'Exploring' THEN 2 END, thread_name;"
```

Known active threads (as of March 2026 -- always query for current state):
1. **Agentic AI Infrastructure** -- Harness layer as durable value. MCP ecosystem. CLAW stack.
2. **Cybersecurity / Pen Testing** -- Service to platform transition.
3. **USTOL / Aviation / Deep Tech Mobility** -- Ultra-short takeoff and landing.
4. **SaaS Death / Agentic Replacement** -- AI agents replacing traditional SaaS.
5. **CLAW Stack Standardization & Orchestration Moat** -- CLAW stack as LAMP/MEAN successor.
6. **Healthcare AI Agents** -- AI enabling personalized care pathways.

---

## Thesis Update Protocol

When content analysis identifies thesis connections:

1. **Query active threads** (psql, see above).
2. **For each connection found:**
   - Determine evidence direction (for/against/mixed) and strength (Strong/Moderate/Weak).
   - Append to evidence properties.
   - Check if any key questions are addressed. If yes, mark answered.
   - Add new key questions raised by the content.
   - Update Investment Implications if evidence is significant.
3. **If conviction change seems warranted:**
   - State your assessment clearly.
   - Include the evidence trail.
   - Recommend a new conviction level.
   - **Do NOT set it.** Write to notifications for Aakash to review.
4. **Update Postgres:**
   ```bash
   psql $DATABASE_URL -c "UPDATE thesis_threads SET evidence_for = evidence_for || E'\n[NEW 2026-03-15] + Evidence text', key_questions = '3 open, 2 answered', investment_implications = 'Updated implication text', notion_synced = FALSE WHERE thread_name = 'Thread Name';"
   ```
