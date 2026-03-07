# Claude.ai Memory Entries — v7.2.0 (March 7, 2026)
# 19 entries. Source of truth for what SHOULD be in Claude.ai memory.
# Aligned with: CONTEXT.md, ai-cos-mcp server (17 tools, public at mcp.3niac.com)
# These persist across ALL Claude.ai conversations (web, mobile, desktop)

# CHANGE LOG (v7.1.0 → v7.2.0, March 7 2026):
# - #7: UPDATED — 9→17 MCP tools, SyncAgent now live (10-min cron)
# - #16: UPDATED — Postgres 7 tables (not just action_outcomes)
# - #1-6, #8-15, #17-19: NO CHANGES

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
AI CoS 3-layer arch: (1) Signal Processor — YouTube live via droplet, Granola/Calendar/Gmail MCPs connected, (2) Intelligence Engine — ai-cos-mcp server (FastMCP Python, 17 tools) on DO droplet, publicly accessible at mcp.3niac.com via Cloudflare Tunnel, Postgres (7 tables), scoring models, (3) Operating Interface — Claude mobile, digest.wiki, Notion, WhatsApp (future). ContentAgent (5-min cron) + SyncAgent (10-min cron, Notion↔Postgres bidirectional sync) run autonomously. All surfaces (Claude.ai, Claude Code, Content Pipeline) write through ai-cos-mcp tools — droplet is single write authority for thesis data. Next: PostMeetingAgent, OptimiserAgent, Action Frontend.

## #8 — Feedback Loop
At end of every research task, analysis, or automation, proactively append "AI CoS relevance" note: (1) connections to active/new thesis threads, (2) people/companies relevant to Z47/DeVC pipeline, (3) patterns or capabilities for AI CoS build, (4) concrete actions that should be scored and added to the action queue. Don't ask permission — just include it. Action outcomes (accept/reject) feed into Postgres preference store for calibration.

## #9 — Thesis Write Protocol (via MCP)
All thesis writes go through AI CoS MCP tools — never use Notion MCP directly for Thesis Tracker. Workflow: (1) call `cos_get_thesis_threads` to see current state, (2) if evidence maps to existing thread: `cos_update_thesis`, (3) if genuinely new territory: `cos_create_thesis_thread`. Set source="Claude" from this surface. Provide evidence, direction, key questions, and implications — but never set the conviction parameter. Conviction changes require the full evidence picture; ask Aakash "Should conviction move from X to Y?" instead. When in doubt between create and update, ask Aakash.

## #10 — "Research Deep and Wide"
Run 6-10 parallel searches from different angles (market structure, key players, funding, technology, competitive dynamics, contrarian views). Synthesize into: Executive Summary, Key Findings, Market Map, Open Questions. End by flagging thesis thread connections and offering to create new threads via `cos_create_thesis_thread`.

## #11 — Content Pipeline (Autonomous on Droplet)
Content Pipeline runs autonomously on DO droplet (cron every 5 min). YouTube extraction → ContentAgent analysis (Claude API) → digest.wiki publish → Notion writes (Content Digest DB + Actions Queue + Thesis Tracker) → Postgres preference store. Digests live at https://digest.wiki/d/{slug}. Review: query Actions Queue (1df4858c) for Status = "Proposed". Accept/dismiss. No manual triggering needed — pipeline is fully autonomous.

## #12 — Portfolio Actions Review
Use `cos_get_actions` to read the Actions Queue (supports status filter: Proposed, Accepted, In Progress, Done, Dismissed). Group by Priority P0→P3. Show: Company, Action Type, Description, Reasoning. To accept or dismiss actions, update status via Notion (Actions Queue 1df4858c). Batch support: "accept all P0"/"dismiss all P3". Summarize counts. Link accepted Meeting/Outreach actions to scheduling.

## #13 — Action Scoring Model
AI CoS Action Scoring Model: f(bucket_impact, conviction_change_potential, key_question_relevance, time_sensitivity, action_novelty, stakeholder_priority, effort_vs_impact). Thesis-weighted: actions connected to Active thesis threads get scoring multiplier. People Scoring is a subset applied to meeting-type actions only.

## #14 — Cross-Surface Alignment
Claude Code manages the canonical context (CONTEXT.md, CLAUDE.md). Claude.ai memory entries are synced from `claude-ai-sync/memory-entries.md` in the project. When Aakash says "sync Claude.ai" or when architectural changes happen, the file is updated and Aakash pastes into Settings → Memory. Always check CONTEXT.md version date if context seems stale.

## #15 — Layered Persistence Architecture
Critical instructions need multi-surface coverage. Surfaces: Claude.ai (memory + preferences), Claude Code (CLAUDE.md + CONTEXT.md + auto memory + TRACES.md). Thesis Tracker in Notion = shared state across all surfaces. When any surface discovers new understanding, sync to Notion (thesis) and flag for cross-surface update. `claude-ai-sync/` folder in project root = source of truth for Claude.ai content.

## #16 — Droplet Infrastructure
AI CoS runs on DO droplet (aicos-droplet, Tailscale). MCP server: systemd service, FastMCP Python, publicly accessible at mcp.3niac.com via Cloudflare Tunnel (zero-trust, auto-TLS, no inbound ports). Content Pipeline: cron every 5 min. SyncAgent: cron every 10 min. Postgres: 7 tables (thesis_threads, actions_queue, action_outcomes, companies, network, sync_queue, change_events). YouTube cookies expire every 1-2 weeks — pipeline warns when stale. Digest site: git push → Vercel auto-deploy at digest.wiki.

## #17 — Actions Queue Schema
Actions Queue (1df4858c) fields: Action (title), Company (relation), Thesis (relation to Thesis Tracker), Source Digest (relation to Content Digest DB), Action Type (select: Research/Meeting-Outreach/Thesis Update/Content Follow-up/Portfolio Check-in/Follow-on Eval/Pipeline Action), Priority (P0-P3), Status (Proposed→Accepted→Done/Dismissed), Source (Content Processing/Agent/Manual/Meeting), Assigned To (Aakash/Agent), Created By (AI CoS/Manual), Reasoning, Relevance Score (0-100), Outcome (Unknown/Helpful/Gold).

## #18 — Thesis Tracker AI Protocol
When any signal (content, meeting, research) connects to a thesis, use AI CoS MCP tools — not Notion MCP. Steps: (1) `cos_get_thesis_threads` to check current state, (2) `cos_update_thesis` with evidence, direction (for/against/mixed), key questions, investment implications, key companies, (3) or `cos_create_thesis_thread` if genuinely new. Never set conviction yourself — provide evidence and ask Aakash if conviction should change. Status field (Active/Exploring/Parked/Archived) is human-only. Connected Buckets options: New Cap Tables, Deepen Existing, New Founders, Thesis Evolution.

## #19 — AI CoS MCP Tool Routing
Use AI CoS MCP (mcp.3niac.com) instead of Notion MCP for these databases: Thesis Tracker (all reads + writes via cos_* tools), Content Digest (reads via `cos_get_recent_digests`), Actions Queue (reads via `cos_get_actions`). Notion MCP is still used for: Actions Queue status changes (accept/dismiss), Companies DB, Network DB, Portfolio DB, and any database without a cos_* tool. When a cos_* tool exists for an operation, always prefer it over Notion MCP.
