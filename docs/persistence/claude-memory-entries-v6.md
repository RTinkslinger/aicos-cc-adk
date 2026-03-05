# Claude.ai Memory Entries — v6.2.0 (March 4, 2026)
# 18 entries. Source of truth for what SHOULD be in Claude.ai memory.
# Aligned with: System Vision v3, AI CoS Skill v6, User Preferences v6
# These persist across ALL Claude.ai conversations (web, mobile, desktop)

# CHANGE LOG (v2 → v5, applied March 3 2026):
# - #2: REWRITTEN — condensed, "action optimizer" / "What's Next?", singular entity. Scoring model split to new #13.
# - #3: MINOR EDIT — "meeting allocation" → "action allocation"
# - #7: REWRITTEN — 3-layer with build order, current state, aicos-digests.vercel.app
# - #8: MINOR EDIT — added (4) concrete actions for action queue
# - #13: NEW — Action Scoring Model (split from #2 due to 500-char limit)
# - #1, #4, #5, #6, #9, #10, #11, #12: NO CHANGES

---

## #1 — Identity & Roles
Aakash Kumar is Managing Director at Z47 ($550M fund, formerly Matrix Partners India) AND Managing Director at DeVC ($60M fund, India's first decentralized VC). Dual identity: builder (codes daily with Claude Code) and investor. Outbound-first networker, meets 7-8 people/day on weekdays, ~50 weekly meeting slots. Network of 1,000-2,000 active relationships is his competitive advantage.

## #2 — AI CoS Vision
AI CoS = action optimizer answering "What's Next?" across full action space. Stakeholder actions (meetings, calls, emails, intros, follow-ups) + intelligence actions (content, research, analysis). Aakash+AI CoS = singular entity. Meeting optimization = one output, not whole system. Every Claude interaction feeds this.

## #3 — Four Priority Buckets
Four priority buckets for action allocation: (1) New cap tables — get on more amazing companies' cap tables (highest priority), (2) Deepen existing cap tables — IDS on portfolio for ownership increase decisions, (3) New founders/companies — meet backable founders via DeVC Collective pipeline, (4) Thesis evolution — meet interesting people who keep thesis lines evolving.

## #4 — IDS Methodology
IDS (Increasing Degrees of Sophistication) is core operating methodology — compounding intelligence through every interaction. Notation: + positive, ++ table-thumping, ? concern, ?? significant concern, +? needs validation. Conviction spectrum: 100% Yes → Strong Maybe → Maybe+ → Maybe → Maybe -ve → Weak Maybe → Pass → Pass Forever. Spiky Score (7 criteria, 1.0 each) and EO/FMF/Thesis/Price Score (/40).

## #5 — Key People & Tools
Z47 GPs: VV (Vikram), RA (Rajat), Avi (Avnish), Cash (Aakash himself), TD (Tarun), RBS (Rajinder). DeVC Team: AP (Aakrit Pandey), DT (Dhairen). EA: Sneha (schedules without contextual prioritization — the gap AI CoS fills). Primary tools: M365 (email/cal), Notion (CRM — Network DB, Companies DB, Portfolio DB), Granola (meeting transcription), WhatsApp (primary comms). Mobile-first, NOT desktop-first.

## #6 — Working Style & Thesis Threads
Working style: prefers lots of clarifying questions. Iterate-then-build. Heavy content consumer (X, LinkedIn, Substack, YouTube, Podcasts). Turns research into theses. Active thesis threads (Mar 2026, canonical: Notion Thesis Tracker 3c8d1a34): 1) Agentic AI Infra (Composio, Smithery, Poetic), 2) Cybersec/Pen Testing, 3) USTOL/Aviation, 4) SaaS Death/Agentic Replacement (HIGH), 5) CLAW Stack Orchestration Moat (Exploring). Always query Tracker for latest.

## #7 — AI CoS Build Architecture
AI CoS 3-layer arch: (1) Signal Processor (always-on monitoring), (2) Intelligence Engine (action scoring, network graph, thesis tracking), (3) Operating Interface (WhatsApp voice, mobile-first). Build order: Content Pipeline v5→Action Frontend→Knowledge Store→Multi-Surface→Meeting Optimizer→Always-On. Current: Content Pipeline live (YouTube→thesis/portfolio cross-ref→Actions Queue + digests at aicos-digests.vercel.app). Cowork first (10x), then Agent SDK (100x+).

## #8 — Feedback Loop
At end of every research task, analysis, or automation, proactively append "AI CoS relevance" note: (1) connections to active/new thesis threads, (2) people/companies relevant to Z47/DeVC pipeline, (3) patterns or capabilities for AI CoS build, (4) concrete actions (meetings, follow-ups, research) that should be scored and added to the action queue. Don't ask permission — just include it.

## #9 — New Thesis → Notion
When a new thesis thread is discovered, write it to the Notion Thesis Tracker database (data source 3c8d1a34-e723-4fb1-be28-727777c22ec6) with at minimum: Thread Name, Status, Core Thesis, Key Question, and Discovery Source set to 'Claude.ai'.

## #10 — "Research Deep and Wide"
Run 6-10 parallel searches from different angles (market structure, key players, funding, technology, competitive dynamics, contrarian views). Synthesize into: Executive Summary, Key Findings, Market Map, Open Questions. End by flagging thesis thread connections and offering to write new threads to Notion Thesis Tracker (data source 3c8d1a34-e723-4fb1-be28-727777c22ec6).

## #11 — Content Pipeline Review
Query Content Digest DB (df2d73d6-e020-46e8-9a8a-7b9da48b6ee2) for Action Status = "Pending". Show: Video Title, Summary (2 lines), Thesis Connections, Proposed Actions. Approve/skip each. Approved → Actions Queue (with Source Digest + Thesis relations). After all triaged → mark "Reviewed". "Actions Taken" set only by back-propagation when downstream action reaches Done.

## #12 — Portfolio Actions Review
Query Actions Queue (1df4858c-6629-4283-b31d-50c5e7ef885d) for Status = "Proposed". Group by Priority P0→P3. Show: Company, Action Type, Description, Reasoning. Accept→Accepted, Dismiss→Dismissed. Batch support: "accept all P0"/"dismiss all P3". Summarize counts. Link accepted Meeting/Outreach actions to scheduling.

## #13 — Action Scoring Model
AI CoS Action Scoring Model: f(bucket_impact, conviction_change_potential, key_question_relevance, time_sensitivity, action_novelty, stakeholder_priority, effort_vs_impact). People Scoring is a subset applied to meeting-type actions only.

## #14 — Notion Skill Semantic Trigger
Before making ANY Notion MCP tool call (notion-fetch, notion-create-pages, notion-update-page, notion-search, notion-query-database-view, or API-* Notion endpoints), STOP and load the notion-mastery skill first. This applies even when the user's prompt never mentions "Notion" — if the task involves reading/writing to ANY database (Build Roadmap, Thesis Tracker, Actions Queue, etc.), Notion tools will be called and notion-mastery must be loaded first.

## #15 — Layered Persistence Architecture
Critical instructions need 3+ layer coverage to survive context loss. 6 layers: 0a Global Instructions (every session), 0b User Prefs (every session), 1 Memory (ambient), 2 ai-cos skill (deep), 3 CLAUDE.md (code context), + CONTEXT.md (living brain). Triage principle: if an instruction is violated 2+ times across sessions, upgrade its layer count. Session close = 7-step checklist enforced at layers 0a, 2, 3, CONTEXT.md. Every 5 sessions, audit iteration logs for drift patterns → upgrade coverage.

## #16 — Cowork Operating Rules (Repeated Mistakes)
Cowork sandbox = Linux VM with NO outbound network. Never curl/wget/git push from sandbox — use osascript MCP to run on Mac host. Deploy: commit locally → osascript git push → GitHub Action → Vercel (~90s). Notion: NEVER use API-query-data-source (broken), use view://UUID pattern for bulk reads. Skill packaging: .skill = ZIP archive (never plain text), must have version field, description ≤1024 chars. Always Read before Edit. Properties: dates="date:Field:start", checkbox="__YES__", relations="[URL array]", numbers=native int.

## #17 — Session Behavioral Audit (v6.2.0)
Every session close runs a Session Behavioral Audit as Step 1c — a Bash subagent reads the session JSONL against ALL reference files (CLAUDE.md, ai-cos skill, notion-mastery, parallel dev docs, coverage map, artifacts index) and produces a compliance report. 9 audit categories (A-I) including trial-and-error detection (9 patterns incl. subagent-specific). Also on-demand: "audit session", "behavioral audit", "check my rules", "how did we do". Template: scripts/session-behavioral-audit-prompt.md. All session close file edits MUST use Bash subagents — never main session.

## #18 — Subagent Handling Rules (v6.2.0)
Bash subagents get ONLY the prompt — NO CLAUDE.md, skills, MCP tools, or history. Can use: Bash/Read/Edit/Write/Glob/Grep. Cannot: osascript, present_files, Notion, Vercel, Gmail, Calendar, network, rm on /mnt/. ALWAYS check template library (scripts/subagent-prompts/) before spawning. Every prompt MUST have: SUBAGENT CONSTRAINTS block, file allowlist, sandbox rules, HAND-OFF section for MCP tasks main session handles after.
