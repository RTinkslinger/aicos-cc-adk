# Skill: ENIAC Company & Portfolio Intelligence

Instructions for ENIAC's company research, portfolio monitoring, deal intelligence,
and connection discovery.

---

## Company Intelligence Profile

Full intelligence report on a single company. Use this before any company-focused
research to understand what's known and what's missing.

```bash
psql $DATABASE_URL -c "SELECT * FROM company_intelligence_profile(123)"
```

### Return Columns (metric / value / detail rows)

Covers:
- **Basic info**: name, sector, stage, website, headquarters
- **Deal status**: current deal state, pipeline position
- **People**: key contacts in our network, their roles, last interaction dates
- **Thesis connections**: which thesis threads reference this company, conviction levels
- **Portfolio link**: if this is a portfolio company, fund, ownership, health
- **Recent interactions**: last 5 interactions involving this company's people
- **Content coverage**: recent content digests mentioning this company
- **Actions**: open/completed actions related to this company
- **Intelligence gaps**: fields that are empty or stale
- **Completeness score**: 0.0-1.0 measure of how much we know

### Usage Pattern

```
1. company_intelligence_profile(id) — understand current state
2. Identify gaps from the output
3. Research via web tools to fill gaps
4. eniac_save_research_findings() — persist what you learned
```

---

## Portfolio Deep Context

Comprehensive context for a portfolio company. Goes deeper than company_intelligence_profile
by including financial data, follow-on analysis, and strategic positioning.

```bash
psql $DATABASE_URL -t -A -c "SELECT portfolio_deep_context(42)"
```

Returns JSONB with:
- `portfolio`: full portfolio record (fund, ownership, entry cheque, valuation, health, stage)
- `company`: linked company record
- `thesis_connections`: thesis threads with conviction and evidence status
- `key_people`: network contacts linked to this company, with interaction history
- `recent_interactions`: last 30 days of interactions
- `obligations`: open obligations (I-owe and they-owe) related to this company
- `actions`: pending and recent completed actions
- `deal_history`: deal pipeline entries and status changes
- `risk_factors`: identified risks (from portfolio_risk_assessment)
- `strategic_notes`: Megamind's depth grades and strategic assessments

Use for:
- Pre-BRC preparation (board review committee)
- Follow-on investment analysis
- Quarterly portfolio reviews

---

## Deal Intelligence Brief

Full context for an active or potential deal. Everything needed for investment decision support.

```bash
psql $DATABASE_URL -t -A -c "SELECT deal_intelligence_brief(123)"
```

Returns JSONB with:
- `company`: company details, sector, stage
- `deal_state`: current pipeline position, last status change
- `thesis_fit`: which theses align, conviction levels, evidence strength
- `competitive_landscape`: similar companies in our database
- `key_relationships`: who in our network is connected
- `due_diligence_gaps`: what we don't know yet
- `interaction_history`: chronological interaction timeline
- `market_context`: recent content/signals about the market/sector
- `risk_assessment`: flagged concerns
- `action_items`: open actions related to this deal

### ENIAC's Deal Research Protocol

1. Load `deal_intelligence_brief(company_id)` for full context
2. Identify `due_diligence_gaps` — these are your research targets
3. Research each gap via web tools
4. Save findings with `p_finding_type = 'competitive_landscape'`, `'funding_history'`,
   `'team_analysis'`, `'market_signal'`, or `'risk_factor'` as appropriate
5. Cross-reference findings against thesis threads — save relevant thesis evidence

---

## Deal Pipeline Intelligence

Broader view — all deal flow intelligence for a company, including similar companies
and timeline context.

```bash
psql $DATABASE_URL -c "SELECT * FROM deal_pipeline_intelligence(123)"
```

Returns per-company: company_name, sector, deal_status, website, key_people (jsonb),
thesis_connections (jsonb), related_actions (jsonb), company_interactions (jsonb),
similar_companies (jsonb), portfolio_info (jsonb), timeline (jsonb),
intel_completeness (0.0-1.0).

---

## Connection Discovery

Find hidden connections between entities. This is ENIAC's relationship mapping engine.

```bash
psql $DATABASE_URL -t -A -c "
  SELECT discover_connections('company', 123, 20)"
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `p_entity_type` | text | `company`, `person`, `thesis`, `portfolio` |
| `p_entity_id` | integer | ID of the entity to discover connections from |
| `p_limit` | integer | Max connections to return (default 20) |

### Returns JSONB

```json
{
  "entity": {"type": "company", "id": 123, "name": "Composio"},
  "connections": [
    {
      "connected_entity_type": "person",
      "connected_entity_id": 45,
      "connected_entity_name": "John Doe",
      "connection_type": "key_contact",
      "strength": 0.85,
      "evidence": ["3 meetings in last 30 days", "email thread active"]
    },
    {
      "connected_entity_type": "thesis",
      "connected_entity_id": 7,
      "connected_entity_name": "Agentic AI Infrastructure",
      "connection_type": "thesis_alignment",
      "strength": 0.92,
      "evidence": ["core_thesis mentions", "2 evidence blocks"]
    }
  ]
}
```

### Connection Discovery Workflow

1. Run `discover_connections()` for entities that appear isolated
2. Look for unexpected connections (company linked to thesis via people, not direct mention)
3. When you find meaningful connections, validate via research
4. Report to Megamind for strategic assessment if connections change the picture

---

## Portfolio Intelligence Map

System-wide portfolio overview with attention flags.

```bash
psql $DATABASE_URL -c "SELECT * FROM portfolio_intelligence_map(200)"
```

Returns per portfolio company: fund, health, stage, financials, intelligence_score,
thesis connections, interaction recency, obligation count, pending actions, key people,
freshness grade, and — most importantly — `attention_needed` (boolean) with
`attention_reason` (text).

Use this to:
- Identify portfolio companies needing immediate research
- Find stale portfolio entries (freshness_grade = `D` or `F`)
- Spot attention flags before they become problems

---

## Portfolio Risk Assessment

Risk analysis across all portfolio companies.

```bash
psql $DATABASE_URL -c "SELECT * FROM portfolio_risk_assessment()"
```

Returns per company: health, ops_priority, cadence, thesis alignment count, open actions,
overdue obligations, days since last interaction, entity connections, risk_score,
risk_tier (`low`, `medium`, `high`, `critical`), and risk_factors (jsonb with specific
issues).

### ENIAC's Portfolio Risk Response

| Risk Tier | ENIAC Action |
|-----------|-------------|
| `critical` | Immediate research — validate risk factors, check for stale data |
| `high` | Add to research queue as urgent |
| `medium` | Schedule for next research cycle |
| `low` | Monitor only |

---

## Detection Functions

### Detect Emerging Signals

Find entities with unusual activity spikes.

```bash
psql $DATABASE_URL -c "SELECT * FROM detect_emerging_signals(14)"
```

Returns entities where recent activity significantly exceeds baseline, with:
`entity_type`, `entity_name`, `signal_type`, `spike_ratio`, `related_deal_signals`,
`connected_theses`, `urgency`.

### Detect Interaction Patterns

Analyze interaction patterns across the network.

```bash
psql $DATABASE_URL -t -A -c "SELECT detect_interaction_patterns()"
```

Returns JSONB with pattern analysis: frequency changes, new relationships,
fading relationships, and cross-entity interaction clusters.

### Detect Opportunities

Identify potential opportunities from cross-referencing signals.

```bash
psql $DATABASE_URL -t -A -c "SELECT detect_opportunities()"
```

Returns JSONB with identified opportunities: warm introductions, thesis-company
matches, cross-pollination between portfolio companies, network leverage points.

---

## Intelligence Reports

### Network Intelligence Report

Full intelligence on a person or all key people.

```bash
# Single person
psql $DATABASE_URL -c "SELECT * FROM network_intelligence_report(45)"

# All people (system-wide)
psql $DATABASE_URL -c "SELECT * FROM network_intelligence_report()"
```

### Interaction Intelligence Report

Deep analysis of interaction patterns with a person.

```bash
psql $DATABASE_URL -c "SELECT * FROM interaction_intelligence_report(45)"
```

### Scoring Intelligence Report

System-wide scoring model health and calibration.

```bash
psql $DATABASE_URL -t -A -c "SELECT scoring_intelligence_report()"
```

### IRGI System Report

Full system health across all IRGI capabilities.

```bash
psql $DATABASE_URL -t -A -c "SELECT irgi_system_report()"
```

### IRGI Benchmark

Performance test across all IRGI functions — latency, row counts, errors.

```bash
psql $DATABASE_URL -c "SELECT * FROM irgi_benchmark()"
```

Run after deploying new functions or when performance seems degraded.
