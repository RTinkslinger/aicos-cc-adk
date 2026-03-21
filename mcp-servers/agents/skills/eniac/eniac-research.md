# Skill: ENIAC Research Operations

Instructions for ENIAC's autonomous research workflow — queue management, context loading,
and findings persistence.

---

## Research Queue

The research queue is ENIAC's work backlog. It surfaces the highest-priority research needs
across the entire system — thesis gaps, company blind spots, stale intelligence, and
user-requested deep dives.

### Checking the Queue

```bash
psql $DATABASE_URL -c "SELECT * FROM eniac_research_queue(15)"
```

Returns a prioritized table:

| Column | Type | Meaning |
|--------|------|---------|
| `priority_rank` | integer | 1 = most urgent |
| `research_type` | text | `thesis_gap`, `company_enrichment`, `signal_followup`, `stale_intelligence`, `user_request` |
| `entity_type` | text | `thesis`, `company`, `person`, `portfolio` |
| `entity_id` | integer | ID in the relevant table |
| `entity_name` | text | Human-readable name |
| `urgency` | text | `critical`, `high`, `medium`, `low` |
| `reason` | text | Why this needs research now |
| `context` | jsonb | Additional context (related theses, recent signals, etc.) |

### Queue Priority Logic

The queue auto-ranks by:
1. **User-requested research** (always top)
2. **Active thesis with evidence gaps** (conviction is evolving but key questions unanswered)
3. **Portfolio companies with stale intelligence** (no interaction in 30+ days)
4. **Emerging signals needing validation** (spike detected but context missing)
5. **Companies in deal pipeline** (active deal flow needing diligence)
6. **General enrichment** (fill empty fields on high-priority entities)

---

## Research Brief

Before starting research, ALWAYS load a research brief. This gives you the full context
on what's already known, what's missing, and what questions to answer.

### For a Thesis

```bash
psql $DATABASE_URL -t -A -c "SELECT eniac_research_brief(p_thesis_id := 42)"
```

Returns JSONB with:
- `entity_type`: "thesis"
- `entity_name`: thesis thread name
- `current_state`: conviction, status, core_thesis, key_questions
- `evidence_summary`: counts of for/against evidence, latest evidence date
- `gaps`: what's missing (unanswered key questions, stale evidence areas)
- `connected_entities`: linked companies, people, portfolio entries
- `recent_signals`: last 14 days of relevant signals
- `research_directions`: suggested areas to investigate

### For a Company

```bash
psql $DATABASE_URL -t -A -c "SELECT eniac_research_brief(p_company_id := 123)"
```

Returns JSONB with:
- `entity_type`: "company"
- `entity_name`: company name
- `current_state`: sector, stage, deal status, website, key fields
- `intelligence_completeness`: 0.0-1.0 score of how much we know
- `gaps`: empty fields, missing context, stale data
- `thesis_connections`: which thesis threads reference this company
- `recent_interactions`: recent meetings/emails involving this company's people
- `research_directions`: suggested areas to investigate

### Brief Usage Pattern

```
1. Check queue: eniac_research_queue()
2. Pick top item
3. Load brief: eniac_research_brief(entity_id)
4. Read the gaps and research_directions
5. Research via web tools (web_search, web_browse, web_scrape)
6. Save findings: eniac_save_research_findings()
```

---

## Saving Research Findings

After completing research, persist findings to the database. This creates a permanent
record that other agents and functions can reference.

### Function Signature

```bash
psql $DATABASE_URL -t -A -c "
  SELECT eniac_save_research_findings(
    p_entity_type := 'company',
    p_entity_id := 123,
    p_finding_type := 'competitive_landscape',
    p_content := 'Detailed findings text here...',
    p_source := 'eniac_agent',
    p_confidence := 0.85
  )"
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `p_entity_type` | text | YES | `company`, `thesis`, `person`, `portfolio` |
| `p_entity_id` | integer | YES | ID in the entity's table |
| `p_finding_type` | text | YES | Category of finding (see table below) |
| `p_content` | text | YES | The actual research content — structured, detailed |
| `p_source` | text | no | Default `'eniac_agent'`. Could be `'web_search'`, `'linkedin'`, etc. |
| `p_confidence` | float | no | Default `0.7`. Your confidence in accuracy (0.0-1.0) |

### Finding Types

| Finding Type | Use When |
|--------------|----------|
| `competitive_landscape` | Market positioning, competitors, differentiation |
| `funding_history` | Rounds, investors, valuations |
| `team_analysis` | Key hires, departures, founder background |
| `product_update` | New launches, pivots, feature changes |
| `market_signal` | Industry trends affecting this entity |
| `thesis_evidence` | Evidence for or against a thesis (tag as for/against in content) |
| `risk_factor` | Identified risks or concerns |
| `opportunity` | Identified opportunities or positive signals |
| `general_enrichment` | Filling in basic entity information |

### Return Value

Returns JSONB:
```json
{
  "status": "saved",
  "entity_type": "company",
  "entity_id": 123,
  "finding_type": "competitive_landscape",
  "content_added": 542,
  "embedding_invalidated": true,
  "note": "Embedding needs re-computation"
}
```

### Where Data Goes

The function does NOT write to a separate findings table. It appends directly:

| Entity Type | Where It Writes | What Happens |
|-------------|-----------------|-------------|
| `company` | `companies.page_content` | Appends research block, invalidates embedding |
| `thesis` | `thesis_threads.evidence_for` or `evidence_against` | Appends evidence block (use `finding_type = 'contra_evidence'` for against) |
| `network` | `entity_connections` (connection_type = 'research_finding') | Creates a self-referencing connection with metadata |

**Thesis evidence routing:** `finding_type = 'contra_evidence'` writes to `evidence_against`.
ALL OTHER finding types write to `evidence_for`. Choose carefully.

---

## Research Quality Standards

1. **Always cite sources.** Include URLs, dates, and source names in `p_content`.
2. **Separate fact from inference.** Mark opinions/analysis distinctly from verified facts.
3. **Set confidence honestly.** 0.9+ = verified from multiple sources. 0.7 = single
   reliable source. 0.5 = inferred or partially verified. Below 0.5 = speculative.
4. **Don't duplicate.** Check the research brief for existing findings before saving.
5. **Connect to thesis.** When researching a company, always check if findings are
   relevant to any active thesis thread. Save separate thesis_evidence findings.
6. **Date your findings.** Include the date of discovery in the content. Intelligence
   decays — future agents need to know when this was current.
