# Methodology & Technology Decisions
*Last Updated: 2026-03-07*

Build principles, technology evaluation framework, and open decision spikes for the AI CoS system.

---

## Build Principles

15 principles governing all build decisions, discovered through reconciliation of vision with implementation reality.

### Build Philosophy

1. **Vision is north star, not blueprint.** The 6-store topology, Context Assembly API, full ER pipeline — these are directional targets refined through building, not designed in advance.
2. **Functional build vs vision architecture.** Build with whatever works NOW (LLM-as-matcher, Notion queries, simple Postgres). Graduate to proper architecture when triggers fire.
3. **Infrastructure follows friction.** Don't build infra speculatively. Build when a workflow hits a concrete limitation. Each infra piece starts as MVP and graduates through IDS levels.
4. **Migration cost as decision framework.** For each technology: assess cost of migrating from pragmatic-first to end-vision. Low migration cost = start pragmatic. High migration cost = lean toward end-vision tech upfront.

### Plan Structure

5. **Dependency graphs, not phases.** Define what requires what. Leave sequencing to judgment at build time.
6. **Define patterns, not rosters.** Don't enumerate all future runners or signal sources. Define the runner pattern, the signal source pattern, and let instances emerge from need.
7. **Deepen + Broaden dual-track.** Track 1: take the content pipeline closer to uber vision (pulls infra). Track 2: add new signal sources in parallel (stress-tests infra). Both tracks feed each other.

### Architecture

8. **Preference Store = RL infrastructure.** Not just "remember what Aakash liked." It's the reinforcement learning substrate. Every accept/reject feeds scoring models, runner behavior, action prioritization. The compounding mechanism.
9. **Action Frontend is infrastructure, not a feature.** It completes the human-in-the-loop feedback cycle. Without it, the RL loop is broken.
10. **Three ingestion tiers: Active, Passive, Ambient.** Each requires more infrastructure and more trust. IDS applied to signal capture.
11. **Trust spectrum as governance framework.** Read, Suggest, Act, Auto-act — earned at category level. Runners earn trust through operation, not design.

### Data

12. **CRM is a swappable interface.** Notion now, Attio later. Build to an abstraction, not to a specific backend.
13. **Schema divergence is by design.** Postgres (agent layer) will be a superset of CRM (human layer). Agents need fields humans don't.

### Operations

14. **Documentation is infrastructure.** Great docs enable Claude Code productivity and potential future developer onboarding. If it's not documented, it doesn't compound.
15. **Budget unconstrained; operational simplicity is the constraint.** Prefer Postgres extensions and managed services over self-hosted engines.

---

## Technology Evaluation Framework

For each store in the vision topology, assessed against Principle #4 (migration cost).

| Vision Store | Pragmatic Start (+) | Migration Cost to Vision | Recommendation |
|-------------|-------------------|------------------------|----------------|
| **OLTP / CRM** | Notion (current) | LOW to Attio | Stay on Notion. Build CRM abstraction layer. Migrate when human-layer UX justifies effort. |
| **Document Store** | Local files + Notion + digest.wiki JSONs | LOW to S3 | Stay pragmatic. Add S3 when cross-document retrieval is needed. |
| **Vector Search** | pgvector (Postgres extension) | LOW to Qdrant/Pinecone | Start with pgvector. Zero new infra. Graduate when scale exceeds limits. |
| **Graph Store** | Postgres JSONB + recursive CTEs | MEDIUM-HIGH to Neo4j | EVALUATE EARLY. Spike before committing to deep Postgres graph modeling. |
| **Timeline Store** | Postgres (timestamp columns) | LOW to TimescaleDB | Start with plain Postgres. Add extension when time-series patterns emerge. |
| **ER Index** | Postgres + LLM-as-matcher | MEDIUM to Elasticsearch | Start with Postgres. Current scale (~200 companies, ~400 contacts) doesn't warrant Elasticsearch. |

**Summary:** 4 of 6 stores safe to start pragmatic with Postgres. Graph Store needs early evaluation. CRM layer needs abstraction interface.

### Adapted 6-Store Topology (Vision State)

1. **OLTP / CRM** — Attio (human layer) + Postgres (agent layer)
2. **Searchable Corpus** — S3 (blobs) + Vector DB (embeddings) — one capability, not two separate stores
3. **Graph Store** — Neo4j or Postgres (pending evaluation spike)
4. **Timeline Store** — TimescaleDB extension on Postgres
5. **ER Index** — Postgres or Elasticsearch (scale-dependent)

All start as Postgres. Graduate individually when triggers fire.

---

## Open Evaluations

Technology decisions that need a spike/prototype before committing.

### Graph Store Evaluation

**Question:** Do the relationship queries we actually need justify Neo4j, or can Postgres recursive CTEs handle them?

**Spike:** Define 5 concrete queries from the Relationship Intelligence capability (CAPABILITY-MAP.md cap. 6). Implement in both Postgres and Neo4j. Compare complexity, performance, maintainability.

**Test queries:**
1. "Who connects me to Person X?" (shortest path)
2. "Who are the most connected people in my thesis-relevant network?" (centrality)
3. "Which communities exist in my network?" (community detection)
4. "Who should I know but don't, based on my thesis threads?" (gap analysis)
5. "Show me all relationships between Company X's team and my existing network" (subgraph)

If queries 1-2 are the main use case: Postgres is fine.
If queries 3-5 are frequent: Neo4j is worth the operational cost.

### Embedding Model Selection

**Question:** Which embedding model for pgvector / vector search?

**Considerations:** Cost per embed, dimension count (affects storage), quality for investor/startup domain content, API availability.

**Candidates:** OpenAI text-embedding-3-small, Claude embeddings (if available), open-source models via local inference.

**Spike:** Embed 100 existing digests. Test retrieval quality for known-relevant queries.
