# Action Scoring Skill

Instructions for scoring proposed actions using the 5-factor weighted model. The agent calculates scores directly -- no external scoring service needed.

---

## The Formula

```
Action Score = (0.25 * bucket_impact) + (0.25 * conviction_change) + (0.20 * time_sensitivity) + (0.15 * action_novelty) + (0.15 * effort_vs_impact)
```

All factors are on a 0-10 scale. Result is 0-10.

### Default Weights

| Factor | Weight | Why |
|--------|--------|-----|
| `bucket_impact` | 0.25 | Which priority bucket(s) this action serves -- highest weight because bucket alignment is the primary value driver. |
| `conviction_change` | 0.25 | Could this change conviction on an active investment? Equal weight because conviction-moving information is the most actionable. |
| `time_sensitivity` | 0.20 | How urgent is this action? Time-sensitive items decay in value. |
| `action_novelty` | 0.15 | Is this genuinely new information/opportunity or repetitive? |
| `effort_vs_impact` | 0.15 | High impact for low effort = high score. |

Weights must sum to 1.0 (tolerance: 0.95-1.05).

---

## Factor Scoring Guide

### bucket_impact (0-10)

Score based on which priority bucket(s) the action serves:

| Score | Bucket | Rationale |
|-------|--------|-----------|
| 10 | New Cap Tables (Bucket 1) | Highest priority -- getting on amazing companies' cap tables |
| 8 | Deepen Existing Cap Tables (Bucket 2) | High priority -- ownership-increase decisions on portfolio |
| 8 | New Founders/Companies (Bucket 3) | High priority -- DeVC Collective pipeline |
| 6 | Thesis Evolution (Bucket 4) | Important but lower weight when conflicting with 1-3 |
| 9 | Serves Bucket 1 + another bucket | Multi-bucket actions are more leveraged |
| 7 | Serves Buckets 2 + 4 | Common combination (portfolio + thesis) |
| 3-5 | Tangential to any bucket | Related but not directly serving bucket objectives |
| 0-2 | No clear bucket alignment | Pure information, no strategic alignment |

### conviction_change (0-10)

Could this action move conviction on an active investment thesis or portfolio company?

| Score | Meaning |
|-------|---------|
| 10 | Would definitively confirm or kill an investment thesis |
| 8-9 | Strong evidence that could move conviction 1-2 levels (e.g., Medium -> High) |
| 6-7 | Moderate evidence, would add meaningful data point to conviction assessment |
| 4-5 | Incremental evidence, adds to existing picture |
| 2-3 | Tangential to conviction but provides useful context |
| 0-1 | No conviction relevance |

### time_sensitivity (0-10)

How urgent is this action? Does it decay in value over time?

| Score | Window | Examples |
|-------|--------|----------|
| 10 | Today | Breaking competitive intel, time-limited meeting opportunity |
| 8 | This week | Pre-meeting research, deal deadline approaching |
| 5 | This month | Follow-up on recent content, thesis research |
| 3 | This quarter | Long-term research, relationship building |
| 0 | Evergreen | Reference material, methodology updates |

### action_novelty (0-10)

Is this genuinely new or repetitive?

| Score | Meaning |
|-------|---------|
| 10 | Completely new insight, never seen before. First signal in a new area. |
| 8 | New angle on known topic. Connects dots not previously connected. |
| 6 | Meaningful update to existing knowledge. New data point. |
| 4 | Incremental update. Confirms existing understanding with minor additions. |
| 2 | Largely redundant with existing knowledge. Minor variation. |
| 0 | Exact duplicate of previous action or information already processed. |

### effort_vs_impact (0-10)

What is the expected impact relative to the effort required?

| Score | Profile |
|-------|---------|
| 10 | High impact, minimal effort. E.g., "Forward this article to portfolio CEO" (1 minute, could change a decision). |
| 8 | High impact, moderate effort. E.g., "30-minute research deep-dive that addresses a key thesis question." |
| 6 | Moderate impact, moderate effort. E.g., "Schedule and prep for a meeting with a potential connector." |
| 4 | Moderate impact, high effort. E.g., "Write a detailed thesis memo." |
| 2 | Low impact, high effort. E.g., "Compile market data that is nice-to-have but not decision-critical." |
| 0 | No clear impact, any effort. |

---

## Classification Thresholds

After computing the score, classify the action:

| Score Range | Classification | What It Means |
|-------------|---------------|---------------|
| **>= 7.0** | `surface` | Immediate action candidate. Present to Aakash. |
| **4.0 - 6.99** | `low_confidence` | Worth tracking. Tag for context enrichment. May become actionable with more evidence. |
| **< 4.0** | `context_only` | Informational only. Store for reference but do not surface as an action. |

---

## Priority Level Mapping

Map the score to a priority level for the Actions Queue:

| Score | Priority | Meaning |
|-------|----------|---------|
| >= 8.0 | **P0 - Act Now** | Do this today. Time-critical, high-impact. |
| >= 7.0 | **P1 - This Week** | Important, schedule this week. |
| >= 4.0 | **P2 - This Month** | Worth doing when capacity exists. |
| < 4.0 | **P3 - Backlog** | Future reference. May never be acted on. |

---

## Worked Example

**Content:** Podcast where a16z partner discusses how Composio's MCP integration is gaining enterprise traction. Mentions 3 portfolio companies considering adoption.

**Factor scores:**
- `bucket_impact = 8` -- Serves Bucket 2 (Deepen Existing: portfolio companies) + Bucket 4 (Thesis Evolution: Agentic AI)
- `conviction_change = 7` -- Could strengthen conviction on Agentic AI Infrastructure thesis (currently Evolving Fast)
- `time_sensitivity = 5` -- Not urgent but timely (Composio is active in pipeline)
- `action_novelty = 8` -- First enterprise traction data point for MCP adoption
- `effort_vs_impact = 7` -- Quick check with portfolio companies, high signal value

**Calculation:**
```
Score = (0.25 * 8) + (0.25 * 7) + (0.20 * 5) + (0.15 * 8) + (0.15 * 7)
      = 2.0 + 1.75 + 1.0 + 1.2 + 1.05
      = 7.0
```

**Classification:** `surface` (>= 7.0)
**Priority:** P1 - This Week
**Action:** "Check with portfolio companies (Unifize, CodeAnt, Highperformr) on MCP adoption plans. Share Composio enterprise traction data point."

---

## Thesis-Weighted Scoring Modifier

Actions connected to thesis threads that Aakash has marked as **Active** (Status field in Thesis Tracker) receive a scoring boost:

- `key_question_relevance` (subcomponent of conviction_change): +1 if the action addresses an open key question on an Active thesis.
- `conviction_change_potential` (subcomponent of conviction_change): +1 if the action could meaningfully move conviction on an Active thesis.

These modifiers are applied BEFORE the weighted sum. Maximum final score is still 10.

**To check thesis status:**
```bash
psql $DATABASE_URL -c "SELECT thread_name, status, conviction FROM thesis_threads WHERE status = 'Active';"
```

---

## Preference Store Calibration

Past action outcomes are stored in the `action_outcomes` Postgres table. Before scoring a batch of actions, query recent outcomes to calibrate:

```bash
psql $DATABASE_URL -c "SELECT action_type, outcome, bucket_impact, conviction_change, time_sensitivity, action_novelty, effort_vs_impact FROM action_outcomes WHERE outcome IN ('Helpful', 'Gold') ORDER BY created_at DESC LIMIT 20;"
```

**What to look for:**
- Gold-rated actions: What factor profiles characterize the most valuable actions?
- Patterns: Are certain action types consistently rated higher?
- Drift: Have scoring patterns changed over time?

Use these patterns to refine your factor scoring within the guide ranges. The model improves as more outcomes are recorded.
