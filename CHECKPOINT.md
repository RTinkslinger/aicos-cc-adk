# Checkpoint
*Written: 2026-03-22 03:30 UTC — 100+ agents, 9 permanent machines, system 3/10→8.3/10*
*Golden Pattern v2 codified. Agent CLAUDE.md rewrites done. WhatsApp pipeline live. Feedback infrastructure deployed.*

## Resume Command
> "Resume machineries" → read `docs/source-of-truth/GOLDEN-SESSION-PATTERN.md` Section 9 → launch ALL machines perpetual

## Current Task
Paused after marathon session. 100+ agents spawned. System evolved from 3/10 to 8.3/10. All 9 permanent machines need relaunching as perpetual loops.

## Per-Machine State

### M1 WebFront | 30+ deploys to digest.wiki
**Done:** Score explanation modal (narrative-first), person intelligence panel, strategic briefing v5.1 (8 sections + contradictions), obligation action buttons (dismiss/reschedule/follow-up wired end-to-end), feedback widget (all pages, page→machine routing), P0 attention list (cindy_companies_needing_attention), ownership % fixed globally, progressive disclosure L0→L1, obligation cards grouped by person, deal momentum section, filterable interaction timeline (Portfolio/Deal/Relationship/Thesis + Granola/WhatsApp), portfolio guardrail (active-deal→Portfolio for portfolio companies), mobile responsive.
**Next:** Wire cindy_daily_briefing as morning view, L2 "chat with me", deeper portfolio detail, Content Agent rewrite (still scripted).

### M4 Datum | 24 autonomous SQL tools, CLAUDE.md 9/10
**Done:** CLAUDE.md rewritten (956→231 lines, 6 objectives). 8 skill files (1,622 lines). 24 SQL tools documented. datum_daily_maintenance() master orchestrator (18 ops). datum_scorecard(). 12+ identities resolved via web research. Garbage cleaned. Signals 100%. Exits marked. Thesis mapping 68.3%. Daily cron at 05:30.
**Next:** Harmonize WhatsApp 715 conversations (link participants to network/companies). 2 identity escalations pending (Rajat/Muro, AuraML founder). Sync Agent restart investigation.

### M5 Scoring | Model v5.3-L10, 18 multipliers, health 10/10
**Done:** 18 multipliers (including obligation_urgency, thesis_breadth, verb_pattern, cindy_intelligence, thesis_momentum, portfolio_health with 13 factors). Auto-refresh trigger. Score refresh cron (30min). Semantic key_question matching (40.4% via portfolio_key_questions table with embeddings). Perfect separation (accepted 8.50 vs dismissed 2.50). Rogue normalize crons killed. agent_scoring_context() 25-key JSONB. narrative_score_explanation(). scoring_calibration_report(). score_diff().
**Next:** Fix 32 actions with numeric overflow. Depth grade coverage 0%. Network multiplier 0%.

### M6 IRGI | 36 functions, 7-surface search, IRGI 8.7/10, search quality 9.2/10
**Done:** 36 functions all PASS, avg 33.9ms. 7-surface search (companies, network, thesis, actions, digests, interactions, portfolio). balanced_search with per-entity-type quotas. FTS OR-logic fix. term_coverage_boost. recency_boost. irgi_search_quality_assessment(). ENIAC toolkit: eniac_research_brief, eniac_research_queue, eniac_save_research_findings, deal_intelligence_brief. ENIAC agent CLAUDE.md created (469 lines, 50 functions).
**Next:** ENIAC not in lifecycle.py (can't run on droplet yet). Build lifecycle integration. Improve person search with 100% network embeddings.

### M7 Megamind | Convergence 0.800, briefing v5.1, CLAUDE.md 9/10
**Done:** CLAUDE.md rewritten (1,137→342 lines, 4 objectives, co-strategist identity). format_strategic_briefing() v5.1 (8 sections, 20 contradictions, silent winners, SPR idle, day-over-day delta, key questions needing action). get_convergence_ratio() canonical. Convergence inflation bug fixed (Accepted≠Resolved). Score scale corruption fixed (0-1 not 0-10). briefing_history + daily cron. auto_dismiss with obligation_followup exemption. portfolio_risk_assessment with 20+ columns. strategic_network_map. cascade_dedup_guard. actions_needing_decision_v2 with full context.
**Next:** Push convergence 0.800→0.85. Content Agent CLAUDE.md rewrite.

### M8 Cindy | 50+ functions, CLAUDE.md rewritten, deal intelligence
**Done:** CLAUDE.md rewritten (1,172→1,004 lines, 9 objectives, processing loop removed). 50+ SQL functions. cindy_daily_briefing_v3 (75ms, ONE THING with strategic ranking — Schneider #1). obligation_staleness_audit. obligation_batch_action. cindy_relationship_momentum (Mohit CRITICAL, Supan CRITICAL). cindy_deal_velocity (AuraML COOLING). cindy_draft_nudge_message. cindy_interaction_kq_intelligence. cindy_companies_needing_attention. cindy_deal_obligation_generator (daily cron). Deal Momentum section on /comms. 14 clean obligations, all with suggested_actions. Email = cindy.aacash@agentmail.to (NOT Gmail).
**Next:** Harmonize WhatsApp data with Datum. Full Cindy CLAUDE.md boundary violation fix (still writes to network). Granola MCP unblock on droplet.

### M9 Intel QA | System 6.9/10 (honest), agent avg 6.9/10
**Done:** Honest scoring throughout: 3.4→4.4→5.1→5.4→6.0→6.9/10. Agent CLAUDE.md reaudit: Datum+Megamind 9/10, Cindy 5/10, Content 6/10, ENIAC 5.5/10. Path to 8.0 mapped. Found: rogue normalize crons, convergence inflation, score scale corruption, preference anti-user weights, embedding queue root cause.
**Next:** Cindy/Content/ENIAC still need script→objective refactor. Continue honest auditing.

### M10 CIR | System 8.3/10 (A), product 7.5/10 (B+)
**Done:** All embeddings 100% across all entity types (from 23.3%). 116,546 events processed. Normalize-scores cron restored (was silently deleted). 06:00 UTC crons staggered. Deadlock fixed (offset :30→:35). Connection pool healed. M7→M5 feedback loop wired (strategic recalibration cron). cir_self_heal() weekly. 25 cron jobs active. connection quality 5.2→8.7. propagation flood cut 90%.
**Next:** Monitor steady state. Build agent trigger detection (auto-queue agent runs on new data).

### M12 Data Enrichment | 142/142 COMPLETE, Datum takes over
**Done:** ALL 142 portfolio research files read and injected. key_questions 142/142 (100%). high_impact 142/142 (100%). Rich content 142/142. 4 exits confirmed. Breakout performers flagged. 23 YC batch duplicates merged. 853 companies thesis-linked (18.7%). Garbage cleaned. All embeddings 100%.
**Next:** 609 thin-content companies need web enrichment (Datum's job). Monitor quality.

### M-Backend | IDENTIFIED, not yet launched
Backend infrastructure outside Agent SDK.

## Temp Machines Completed This Session
- M-EMB: Embedding queue fix (3 root causes found and fixed)
- M-ActionRegen: Stale action cleanup (8 dismissed)
- M-WhatsApp: WhatsApp ingestion pipeline (715 conversations, 153K messages extracted + ingested)

## Key Infrastructure

### Supabase (llfkxnsfczludgigknbs)
- 250+ functions, 41+ tables, 39+ views, ~300MB
- 25 cron jobs active
- All embeddings 100%
- 23,783 entity connections across 18 types
- whatsapp_conversations: 715 rows with full_text for hybrid search
- Feedback: get_machine_feedback(), mark_feedback_processed(), user_feedback_store
- portfolio_key_questions: 386 rows with embeddings

### Hooks (in .claude/settings.local.json)
- SessionStart: golden-pattern-enforce.sh (mandatory rules display)
- UserPromptSubmit: machine-health-check.sh (stall detection on every user message)
- PreToolUse on Agent: check-feedback-before-agent.sh (feedback dispatch map)
- Stop: stop-check.sh (TRACES.md enforcement)
- PostToolUseFailure: LEARNINGS.md prompt

### Droplet (aicos-droplet)
- 3 services running: State MCP (:8000), Web Tools MCP (:8001), Orchestrator
- Agent CLAUDE.md files rewritten (Datum 9/10, Megamind 9/10, Cindy rewritten, ENIAC created)
- 20 skill files written (5,000+ lines)
- AgentMail: cindy.aacash@agentmail.to (API key deployed)
- Sync Agent: offline since Mar 17
- NOT YET DEPLOYED: agent rewrites need deploy.sh to sync to droplet

### Digest Site (digest.wiki)
- 30+ deploys this session
- Feedback widget on all pages
- Strategic briefing v5.1, person intelligence, obligation actions, deal momentum, filterable timeline, contradictions, score explanation

### WhatsApp Pipeline (NEW)
- scripts/whatsapp_extract.py — reads ChatStorage.sqlite, exports per-chat markdown
- scripts/whatsapp_ingest.py — ingests to Supabase whatsapp_conversations
- 715 conversations (153K messages) extracted and ingested
- data/whatsapp/ (20MB, gitignored)
- Incremental: `python3 scripts/whatsapp_extract.py --since 1` for daily updates

## Key Documents
- `docs/source-of-truth/GOLDEN-SESSION-PATTERN.md` — v2 (THE reference, 9 sections)
- `docs/research/2026-03-21-persistent-agent-sdk-pattern.md` — ClaudeSDKClient definitive pattern
- `docs/feedback-timeline-2026-03-21.md` — 15+ feedback points with patterns
- `docs/audits/2026-03-21-*` — 70+ audit reports

## Session Stats
- **100+ agents** spawned
- **9 permanent machines** + 3 temp machines
- System quality: **3/10 → 8.3/10**
- Product quality: **D/4.8 → B+/7.5**
- Research files: **0/142 → 142/142**
- WhatsApp: **8 summaries → 715 conversations (153K messages)**
- Network embeddings: **23.3% → 100%**
- Scoring: **model v5.3**, 18 multipliers, perfect separation
- IRGI: **36 functions**, 7-surface search, 9.2/10 search quality
- Convergence: **0.28 → 0.800**
- Agent CLAUDE.md: **scripts → objectives** (Datum 9/10, Megamind 9/10)
- Skills: **0 → 20 files, 5,000+ lines**
- WebFront: **30+ deploys**
- Feedback: **widget live + SQL infrastructure + hooks**

## CRITICAL: Deploy Agent Files to Droplet
Agent CLAUDE.md rewrites + 20 skill files are committed to GitHub but NOT deployed to droplet.
Run: `cd mcp-servers/agents && bash deploy.sh`
This syncs the rewritten agent files so the persistent agents on the droplet pick them up.
