# Checkpoint
*Written: 2026-03-20 09:00*

## Current State
WebFront v3 live at digest.wiki. 3 iterations shipped (v1→v2→v3). Companies/Network schema audit done, migration SQL drafted. Two workstreams ready for next session.

## Workstream 1: WebFront — CONTINUE ITERATING

### What's Live (digest.wiki)
- `/` — Home with stats grid, recent actions, active thesis
- `/actions` — 115 actions, filters (status/priority/type/assigned_to), batch select, inline reasoning
- `/actions/[id]` — Detail with AI reasoning, scoring bars, adversarial perspective, triage controls
- `/thesis` — 8 threads with mini conviction gauges, evidence dots
- `/thesis/[id]` — Detail with stepped conviction gauge, adversarial framework, key questions timeline, evidence trail (FOR/AGAINST with IDS notation), connected content
- `/d/[slug]` — SSG digests (22) with related actions section
- Navigation bar across all pages

### Bugs to Fix (from QA + UX audit)
1. **Nav touch targets** — 38px, needs 44px min. Fix: `min-h-[44px]` on nav links in `Nav.tsx`
2. **Content→Action linkage gap** — DigestActions query returns empty despite actions existing. The `fetchDigestActions` uses ilike on `source_content` but the data linkage between digests and actions may not match. Investigate `source_content` field values.
3. **Triage controls buried** on action detail page — need sticky footer so Accept/Dismiss visible without scrolling
4. **No undo** on triage actions — add undo toast
5. **3 touch target failures** — nav links, "Show more" toggle, back links
6. **Thesis names not clickable** in digest or action list views — should link to `/thesis/[id]`
7. **Evidence sections too long** without collapsing — add `<details>` for sections with 5+ entries

### Reports
- QA: `aicos-digests/docs/iterations/003-qa-report.md` (12/13 pass)
- UX: `aicos-digests/docs/iterations/003-ux-audit.md` (7.2/10)
- Plans: `aicos-digests/docs/iterations/001-webfront-v1.md`, `003-webfront-v3.md`

### Still TODO from Phase 1 Plan
- [ ] IRGI Phase A: vector columns, Auto Embeddings pipeline, FTS indexes, hybrid search function
- [ ] Realtime subscriptions (new actions appear live)
- [ ] Mobile-responsive polish (v3 improved but UX audit flagged issues)

## Workstream 2: Companies + Network DB Schema Migration

### What's Done
- Schema audit: `docs/audits/2026-03-20-companies-network-schema-audit.md`
- Companies: 49 Notion fields vs 32 Postgres columns → 24 gaps (6 HIGH)
- Network: 44 Notion fields vs 34 Postgres columns → 18 gaps (5 HIGH)
- Draft ALTER TABLE SQL in the audit doc

### What's Needed Next Session
1. **Notion MCP now configured** — query LIVE Notion schemas for Companies DB (`1edda9cc-df8b-41e1-9c08-22971495aa43`) and Network DB (`6462102f-112b-40e9-8984-7cb1e8fe5e8b`) to verify completeness
2. **Cross-reference** live Notion fields vs audit doc — fill any gaps
3. **Execute migration SQL** via Supabase MCP after verification
4. **Populate data** — sync Notion rows into Postgres (need to figure out the sync mechanism)

### Rule (from user, MANDATORY)
Final Postgres schema = MAX(current Postgres + full Notion). No field from either side gets dropped. Deduplicate exact matches, keep both where they serve different purposes.

## Supabase (LIVE)
- Project: **AI COS Mumbai** (`llfkxnsfczludgigknbs`), ap-south-1
- Pooler: `aws-1-ap-south-1.pooler.supabase.com:5432` (session mode)
- PG17, pgvector 0.8.0, 11 tables
- Keys: stored in Vercel env vars only (`vercel env pull` to get locally)

## New Artifacts This Session
- `docs/product/eniac-apm-brief.md` — ENIAC APM reference for team-of-agents builds
- `docs/source-of-truth/TLDR.md` — Concise project picture (agent system, build pattern, 3 pillars)
- `mcp-servers/agents/skills/reasoning/adversarial-analysis.md` — 7 investment lenses, 4 polarity pairs, 3-round protocol
- `docs/research/2026-03-20-council-adversarial-reasoning-source.md` — Source article
- `docs/audits/2026-03-20-companies-network-schema-audit.md` — Full schema gap analysis

## Infrastructure
- Vercel CLI v50.33.1 installed, authenticated as hi-1231, linked to aicos-digests
- Droplet: 2 agents (Orchestrator + ENIAC) + 2 MCPs (State :8000, Web Tools :8001) — untouched this session
- Orchestrator still detecting "pipeline overdue" every heartbeat (known, burns $0.25-0.51/cycle)

## Team-of-Agents Pattern (established this session)
When user says "use a team of agents" for building:
- Load APM brief from `docs/product/` for domain context
- Product Agent writes iteration plan to `aicos-digests/docs/iterations/`
- Backend Agent: queries, Server Actions, data utilities (src/lib/)
- Frontend Agent: pages, components, UI (src/app/, src/components/)
- QA Agent: functional verification
- UX Expert Agent: consumer experience audit
- Zero file overlap between Backend and Frontend agents
- Use feature branches (feat/webfront-vN), merge to main, push to deploy
- Use frontend-design + design-system-enforcer skills for Frontend Agent prompts

## TRACES.md
Iteration 27 logged. This is iteration 3 of current milestone window — **compaction due at iteration 28**.
