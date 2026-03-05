# AI CoS — docs/ Directory Index

> Reorganised: Session 040 (2026-03-05)

## Active Folders

| Folder | What lives here | When to use |
|--------|----------------|-------------|
| `schema/` | Notion Database schema guides & field-level metadata | Building queries, onboarding new agents to a DB |
| `vision/` | System vision docs (v1→v3) | Understanding the "why" and architecture of AI CoS |
| `plans/` | Feature plans, roadmaps, implementation specs | Planning new capabilities |
| `persistence/` | Artifact versions, memory entries, layered coverage map | Cross-surface sync, version audits, persistence debugging |
| `research/` | Deep-dive research outputs (architecture, integrations, diagnostics) | Reference during builds |
| `iteration-logs/` | Per-session logs (sessions 001–039+) | Understanding what happened in any past session |
| `session-checkpoints/` | Mid-session pickups & checkpoint snapshots | Resuming interrupted work |
| `audit-reports/` | Behavioral audits & QA reports (incl. qa-session-038 deep audit) | Compliance checks, rule drift detection |
| `adr/` | Architecture Decision Records | Understanding past design tradeoffs |
| `stack-docs/` | External stack research (LinkedIn/X APIs, M365, connectors) | Evaluating tooling & integration options |

## Key Files (quick access)

- **Network DB reference** → `schema/network-db-schema-guide.md`
- **Current artifacts index** → `persistence/v6-artifacts-index.md`
- **Layered persistence map** → `persistence/layered-persistence-coverage.md`
- **Latest vision** → `vision/system-vision-v3.md`
- **Content Pipeline v5 spec** → `plans/content-pipeline-v5-plan.md`

## Deprecated Folders (cannot delete from mounted FS)

These folders have been consolidated into the structure above. Contents were copied, originals remain as empty shells:

- `plan-versions/` → merged into `plans/`
- `stack docs/` → merged into `stack-docs/` (removed space in name)
- `stack-discoveries/` → merged into `stack-docs/`
- `qa-audit-session-038/` → merged into `audit-reports/qa-session-038/`
