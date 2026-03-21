# Skill: ENIAC Thesis Analysis

Instructions for ENIAC's thesis intelligence — health monitoring, bias detection,
momentum tracking, and interaction cross-referencing.

---

## Thesis Health Dashboard

The system-wide thesis health monitor. Run this periodically (at least once per session)
to identify theses needing attention.

```bash
psql $DATABASE_URL -c "SELECT * FROM thesis_health_dashboard()"
```

### Return Columns

| Column | Type | Meaning |
|--------|------|---------|
| `thesis_id` | integer | ID |
| `thread_name` | text | Thesis name |
| `conviction` | text | Current conviction level |
| `status` | text | Active, Exploring, Parked, Archived |
| `age_days` | integer | Days since thesis creation |
| `momentum_score` | numeric | 0.0-1.0, higher = more momentum |
| `momentum_label` | text | `accelerating`, `steady`, `decelerating`, `stalled` |
| `evidence_freshness_score` | numeric | 0.0-1.0, how recent is latest evidence |
| `freshness_label` | text | `fresh`, `aging`, `stale`, `dormant` |
| `latest_evidence_date` | date | When last evidence was added |
| `total_actions` | integer | All-time actions related to this thesis |
| `recent_actions_7d` | integer | Actions in last 7 days |
| `entity_connections` | bigint | Number of entity_connections rows |
| `network_reach` | bigint | People connected to this thesis |
| `company_coverage` | bigint | Companies connected |
| `open_questions` | integer | Unanswered key questions count |
| `bias_severity` | text | `none`, `possible`, `confirmed` |
| `evidence_ratio` | numeric | for_count / against_count ratio |
| `health_grade` | text | Overall grade: `A`, `B`, `C`, `D`, `F` |

### Health Grade Interpretation

| Grade | Meaning | ENIAC Action |
|-------|---------|-------------|
| A | Healthy — active momentum, fresh evidence, balanced | Monitor only |
| B | Good — minor gaps (slightly stale or few connections) | Light research to fill gaps |
| C | Attention needed — stale evidence or bias detected | Prioritize in research queue |
| D | Unhealthy — dormant, biased, or disconnected | Urgent research or recommend parking |
| F | Critical — no recent evidence, no connections, high bias | Flag to Megamind for strategic review |

---

## Thesis Research Package

Deep context dump for a single thesis. Use before doing focused thesis research.

```bash
psql $DATABASE_URL -t -A -c "SELECT thesis_research_package(42)"
```

Returns JSONB with:
- `thesis`: full thesis record (name, conviction, core_thesis, key_questions, evidence)
- `evidence_blocks`: all for/against evidence with dates and sources
- `connected_companies`: companies linked to this thesis
- `connected_people`: people linked to this thesis
- `related_actions`: actions referencing this thesis
- `related_content`: content digests mentioning this thesis
- `interaction_crossrefs`: interactions relevant to this thesis
- `bias_analysis`: output of detect_thesis_bias for this thesis
- `momentum`: momentum metrics and trajectory
- `research_gaps`: identified gaps in evidence coverage
- `suggested_research`: specific research questions to investigate

---

## Thesis Bias Detection

Detect confirmation bias, source bias, and evidence imbalance in thesis reasoning.

```bash
# All theses
psql $DATABASE_URL -c "SELECT * FROM detect_thesis_bias()"

# Single thesis
psql $DATABASE_URL -c "SELECT * FROM detect_thesis_bias(42)"
```

### Return Columns

| Column | Type | Meaning |
|--------|------|---------|
| `thesis_id` | integer | ID |
| `thread_name` | text | Name |
| `conviction` | text | Current conviction |
| `evidence_for_count` | integer | Number of supporting evidence blocks |
| `evidence_against_count` | integer | Number of contradicting evidence blocks |
| `ratio` | numeric | for / against (high ratio with few against = bias risk) |
| `confirmation_bias` | boolean | TRUE if conviction is High but ratio > 5:1 |
| `possible_bias` | boolean | TRUE if ratio > 3:1 with Evolving+ conviction |
| `source_bias` | boolean | TRUE if > 80% of evidence comes from same source type |
| `flags` | jsonb | Detailed bias flags with explanations |

### ENIAC's Bias Response Protocol

When bias is detected:
1. **confirmation_bias = TRUE**: Research counter-evidence immediately. Search for
   bear cases, competitor advantages, market risks. Save as `thesis_evidence` with
   against orientation.
2. **possible_bias = TRUE**: Note in research queue. Less urgent but track.
3. **source_bias = TRUE**: Diversify research sources. If all evidence is from
   content digests, search for interaction-based evidence. If all from one sector
   publication, broaden.
4. **NEVER change conviction.** Report findings. Let Aakash decide.

---

## Interaction-Thesis Cross-Reference

Find interactions (meetings, emails, chats) that are relevant to thesis threads but
haven't been explicitly linked. This is ENIAC's signal discovery engine.

```bash
psql $DATABASE_URL -c "
  SELECT * FROM irgi_interaction_thesis_crossref(
    90,    -- days_back
    0.55   -- min_relevance
  )"
```

### Return Columns

| Column | Type | Meaning |
|--------|------|---------|
| `interaction_id` | integer | Interaction record ID |
| `interaction_date` | date | When it happened |
| `interaction_source` | text | `email`, `whatsapp`, `granola`, `calendar` |
| `interaction_summary` | text | Interaction summary text |
| `thesis_id` | integer | Matched thesis thread |
| `thesis_name` | text | Thesis name |
| `thesis_conviction` | text | Current conviction |
| `relevance_score` | float | 0.0-1.0 match strength |
| `evidence_type` | text | `supporting`, `contradicting`, `neutral`, `tangential` |
| `key_question_match` | text | Which key question this interaction might answer |
| `action_suggestion` | text | What to do with this insight |

### Cross-Reference Workflow

1. Run `irgi_interaction_thesis_crossref()` regularly (every session)
2. For high-relevance matches (> 0.7): create thesis evidence blocks immediately
3. For medium matches (0.55-0.7): add to research queue for validation
4. For matches with `key_question_match`: prioritize — these may answer open questions

---

## Thesis Landscape

System-wide thesis overview with intelligence completeness scores.

```bash
psql $DATABASE_URL -c "SELECT * FROM thesis_landscape()"
```

Returns per-thesis: conviction, status, evidence counts, momentum score/direction,
connected entity counts, key companies/people, bias severity, days since last signal,
and intelligence completeness (0.0-1.0).

Use this for:
- Identifying which theses have low intelligence_completeness
- Spotting momentum shifts (direction = `decelerating` on high-conviction thesis = alert)
- Finding disconnected theses (low entity counts)

---

## Thesis Momentum Report

Detailed momentum analysis for a single thesis.

```bash
psql $DATABASE_URL -c "SELECT * FROM thesis_momentum_report(42)"
```

Returns metric/value/detail rows covering:
- Signal velocity (signals per week, trend)
- Evidence accumulation rate
- Network expansion (new people connecting)
- Company coverage growth
- Action generation rate
- Interaction frequency

Use when the health dashboard flags a thesis as `decelerating` or `stalled` to
understand specifically what stopped moving.

---

## Scoring Multipliers (Read-Only Context)

ENIAC's raw scores feed into Megamind's strategic scoring via multipliers. You don't
set these directly, but understanding them helps you prioritize research:

| Multiplier | Function | What It Measures |
|------------|----------|-----------------|
| `thesis_momentum_multiplier(action)` | Boosts actions tied to fast-moving theses | Higher momentum = higher action score |
| `thesis_breadth_multiplier(action)` | Boosts actions connected to multiple theses | Cross-thesis actions are more valuable |
| `portfolio_health_multiplier(action)` | Boosts actions for portfolio companies needing attention | Unhealthy portfolio = higher urgency |
| `interaction_recency_boost(action)` | Boosts actions for recently-interacted entities | Recent interaction = higher relevance |

When you research a thesis and find new evidence, it can change the momentum
multiplier — which cascades into action scores across the system.
