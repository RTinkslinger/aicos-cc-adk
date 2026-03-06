# Claude.ai Memory Entries — v7.0.0 (March 6, 2026)
# 18 entries. Source of truth for what SHOULD be in Claude.ai memory.
# Aligned with: CONTEXT.md (March 6 update), ai-cos-mcp server (live on droplet)
# These persist across ALL Claude.ai conversations (web, mobile, desktop)

# CHANGE LOG (v6.2.0 → v7.0.0, March 6 2026):
# - #6: REWRITTEN — thesis threads now AI-managed conviction engine, new conviction spectrum
# - #7: REWRITTEN — MCP server + ContentAgent live on droplet, Agent SDK era
# - #8: MINOR EDIT — updated feedback loop with preference store
# - #9: REWRITTEN — AI creates thesis threads autonomously, new protocol
# - #11: REWRITTEN — Content Pipeline now autonomous on droplet
# - #14: REWRITTEN — was Notion skill trigger (Cowork), now cross-surface alignment protocol
# - #16: REWRITTEN — was Cowork rules (obsolete), now droplet infrastructure
# - #17: REWRITTEN — was behavioral audit (Cowork), now Actions Queue schema
# - #18: REWRITTEN — was subagent rules (Cowork), now thesis tracker protocol
# - #1-5, #10, #12, #13, #15: NO CHANGES (still accurate)

---

## #1 — Identity & Roles
Aakash Kumar is Managing Director at Z47 ($550M fund, formerly Matrix Partners India) AND Managing Director at DeVC ($60M fund, India's first decentralized VC). Dual identity: builder (codes daily with Claude Code) and investor. Outbound-first networker, meets 7-8 people/day on weekdays, ~50 weekly meeting slots. Network of 1,000-2,000 active relationships is his competitive advantage.

## #2 — AI CoS Vision
AI CoS = action optimizer answering "What's Next?" across full action space. Stakeholder actions (meetings, calls, emails, intros, follow-ups) + intelligence actions (content, research, analysis). Aakash+AI CoS = singular entity. Meeting optimization = one output, not whole system. Every Claude interaction feeds this.

## #3 — Four Priority Buckets
Four priority buckets for action allocation: (1) New cap tables — get on more amazing companies' cap tables (highest priority), (2) Deepen existing cap tables — IDS on portfolio for ownership increase decisions, (3) New founders/companies — meet backable founders via DeVC Collective pipeline, (4) Thesis evolution — meet interesting people who keep thesis lines evolving.

## #4 — IDS Methodology
IDS (Increasing Degrees of Sophistication) is core operating methodology — compounding intelligence through every interaction. Notation: + positive, ++ table-thumping, ? concern, ?? significant concern, +? needs validation. Conviction spectrum: 100% Yes → Strong Maybe (SM) → Maybe+ → Maybe → Maybe -ve → Weak Maybe (WM) → Pass → Pass Forever. Spiky Score (7 criteria, 1.0 each) and EO/FMF/Thesis/Price Score (/40).

## #5 — Key People & Tools
Z47 GPs: VV (Vikram), RA (Rajat), Avi (Avnish), Cash (Aakash himself), TD (Tarun), RBS (Rajinder). DeVC Team: AP (Aakrit Pandey), DT (Dhairen). EA: Sneha (schedules without contextual prioritization — the gap AI CoS fills). Primary tools: M365 (email/cal), Notion (CRM — Network DB, Companies DB, Portfolio DB), Granola (meeting transcription), WhatsApp (primary comms). Mobile-first, NOT desktop-first.

## #6 — Thesis Tracker (AI-Managed Conviction Engine)
Thesis Tracker (Notion DB 3c8d1a34) is an AI-managed conviction engine. AI autonomously creates threads, updates evidence, adjusts conviction, formulates key questions. Aakash's ONLY role: set Status (Active/Exploring/Parked/Archived) — this weights action scoring. Conviction spectrum: New → Evolving → Evolving Fast (maturity) → Low → Medium → High (well-formed strength). Active thesis threads get higher weight in action scoring. Always query Notion for latest state.

## #7 — AI CoS Build Architecture
AI CoS 3-layer arch: (1) Signal Processor — YouTube live via droplet, Granola/Calendar/Gmail MCPs connected, (2) Intelligence Engine — ai-cos-mcp server (FastMCP Python) + ContentAgent runner live on DO droplet, Postgres preference store, scoring models, (3) Operating Interface — Claude mobile, digest.wiki, Notion, WhatsApp (future). ContentAgent runs autonomously every 5 min on droplet. Build: Agent SDK era (not Cowork anymore). Next: PostMeetingAgent, OptimiserAgent, Action Frontend on digest.wiki.

## #8 — Feedback Loop
At end of every research task, analysis, or automation, proactively append "AI CoS relevance" note: (1) connections to active/new thesis threads, (2) people/companies relevant to Z47/DeVC pipeline, (3) patterns or capabilities for AI CoS build, (4) concrete actions that should be scored and added to the action queue. Don't ask permission — just include it. Action outcomes (accept/reject) feed into Postgres preference store for calibration.

## #9 — Thesis Thread Management
AI creates new thesis threads autonomously in Notion Thesis Tracker (data source 3c8d1a34). Set: Thread Name, Conviction = "New", Core Thesis, Key Question, Discovery Source = "Claude.ai" (from this surface). No human approval needed. When evidence accumulates, update conviction (New→Evolving→High). Key Questions live as page content blocks: [OPEN] or [ANSWERED]. Questions answered = evidence updated = conviction moves.

## #10 — "Research Deep and Wide"
Run 6-10 parallel searches from different angles (market structure, key players, funding, technology, competitive dynamics, contrarian views). Synthesize into: Executive Summary, Key Findings, Market Map, Open Questions. End by flagging thesis thread connections and offering to write new threads to Notion Thesis Tracker (data source 3c8d1a34-e723-4fb1-be28-727777c22ec6).

## #11 — Content Pipeline (Autonomous on Droplet)
Content Pipeline runs autonomously on DO droplet (cron every 5 min). YouTube extraction → ContentAgent analysis (Claude API) → digest.wiki publish → Notion writes (Content Digest DB + Actions Queue + Thesis Tracker) → Postgres preference store. Digests live at https://digest.wiki/d/{slug}. Review: query Actions Queue (1df4858c) for Status = "Proposed". Accept/dismiss. No manual triggering needed — pipeline is fully autonomous.

## #12 — Portfolio Actions Review
Query Actions Queue (1df4858c-6629-4283-b31d-50c5e7ef885d) for Status = "Proposed". Group by Priority P0→P3. Show: Company, Action Type, Description, Reasoning. Accept→Accepted, Dismiss→Dismissed. Batch support: "accept all P0"/"dismiss all P3". Summarize counts. Link accepted Meeting/Outreach actions to scheduling.

## #13 — Action Scoring Model
AI CoS Action Scoring Model: f(bucket_impact, conviction_change_potential, key_question_relevance, time_sensitivity, action_novelty, stakeholder_priority, effort_vs_impact). Thesis-weighted: actions connected to Active thesis threads get scoring multiplier. People Scoring is a subset applied to meeting-type actions only.

## #14 — Cross-Surface Alignment
Claude Code manages the canonical context (CONTEXT.md, CLAUDE.md). Claude.ai memory entries are synced from `claude-ai-sync/memory-entries.md` in the project. When Aakash says "sync Claude.ai" or when architectural changes happen, the file is updated and Aakash pastes into Settings → Memory. Always check CONTEXT.md version date if context seems stale.

## #15 — Layered Persistence Architecture
Critical instructions need multi-surface coverage. Surfaces: Claude.ai (memory + preferences), Claude Code (CLAUDE.md + CONTEXT.md + auto memory + TRACES.md). Thesis Tracker in Notion = shared state across all surfaces. When any surface discovers new understanding, sync to Notion (thesis) and flag for cross-surface update. `claude-ai-sync/` folder in project root = source of truth for Claude.ai content.

## #16 — Droplet Infrastructure
AI CoS runs on DO droplet (aicos-droplet, Tailscale). MCP server: systemd service, FastMCP Python. Content Pipeline: cron every 5 min. Postgres: preference store (action_outcomes table). Deploy from Mac: `cd mcp-servers/ai-cos-mcp && bash deploy.sh`. YouTube cookies expire every 1-2 weeks — pipeline warns when stale. Digest site repo also on droplet: `git push → Vercel auto-deploy`.

## #17 — Actions Queue Schema
Actions Queue (1df4858c) fields: Action (title), Company (relation), Thesis (relation to Thesis Tracker), Source Digest (relation to Content Digest DB), Action Type (select: Research/Meeting-Outreach/Thesis Update/Content Follow-up/Portfolio Check-in/Follow-on Eval/Pipeline Action), Priority (P0-P3), Status (Proposed→Accepted→Done/Dismissed), Source (Content Processing/Agent/Manual/Meeting), Assigned To (Aakash/Agent), Created By (AI CoS/Manual), Reasoning, Relevance Score (0-100), Outcome (Unknown/Helpful/Gold).

## #18 — Thesis Tracker AI Protocol
Thesis Tracker is AI-managed. On every signal (content, meeting, research, email), AI checks thesis connections. If found: append evidence block, update Evidence For/Against, re-evaluate conviction, update Key Questions (mark answered/add new), update Investment Implications. AI creates new threads freely at Conviction = "New". Status field is HUMAN-ONLY (Active/Exploring/Parked/Archived). Active = higher action scoring weight.
