# Megamind Build Review + Lifecycle Integration Report
*Date: 2026-03-20 | Milestone 7 Loop 3+4*

---

## Part 1: Build Review

### Database Verification (Supabase)

| Check | Status | Details |
|-------|--------|---------|
| Tables exist | PASS | All 4 tables present: `depth_grades`, `cascade_events`, `strategic_assessments`, `strategic_config` |
| Config seeded | PASS | All 12 config keys present with correct default values |
| Indexes exist | PASS | 12 indexes total (5 on depth_grades, 3 on cascade_events, 1 on strategic_assessments, 3 PKs) |
| Trust level | PASS | Initialized to `"manual"` with zeroed trust_stats |

### CLAUDE.md Coverage (970 lines)

| Section | Present | Quality |
|---------|---------|---------|
| 1. Identity | Yes | Clear role boundaries — not scorer, not data processor, not content analyst |
| 2. Capabilities | Yes | Tool list correct: Bash, Read, Write, Edit, Grep, Glob, Skill. No web tools. |
| 3. Database Access | Yes | Read/write tables, read-only tables, never-touch tables all specified with correct column names |
| 4. Priority Buckets | Yes | 4 buckets with weight hierarchy |
| 5. Strategic ROI | Yes | 5-component formula with weights summing to 1.0 |
| 6. Three Work Types | Yes | Depth grading, cascade processing, strategic assessment — all with step-by-step SQL |
| 7. Diminishing Returns | Yes | Decay table, contra exemption, detection heuristics |
| 8. Convergence Rules | Yes | 6 hard constraints with config references |
| 9. Trust Ramp | Yes | 3 levels with promotion criteria and SQL patterns |
| 10. Interaction Protocol | Yes | Prompt formats for all 3 work types, ACK format |
| 11. Convergence Failure | Yes | Critical flag, depth cap, recovery plan, recovery criteria |
| 12. ACK Protocol | Yes | Mandatory structured ACK format with PASS/WARN/FAIL |
| 13. State Tracking | Yes | State files, compaction, restart protocol |
| 14. Anti-Patterns | Yes | 18 anti-patterns covering all major failure modes |
| 15. Error Handling | Yes | DB errors, logic errors, capacity protection |
| 16. Quality Bars | Yes | Quality criteria for all 3 work types |

### Skills Verification

| Skill | File | DB Column References Correct | Key Concern |
|-------|------|------------------------------|-------------|
| strategic-reasoning.md | 244 lines | Yes — `actions_queue.relevance_score`, `thesis_threads.conviction`, `depth_grades`, `portfolio`, `companies` all match schema | Component weights match CLAUDE.md (0.30/0.20/0.20/0.15/0.15) |
| depth-grading.md | 271 lines | Yes — `depth_grades.auto_depth`, `approved_depth`, `execution_status`, `execution_agent`, `execution_cost_usd` all correct | Trust level behavior table is clear |
| cascade-protocol.md | 314 lines | Yes — `cascade_events.trigger_type`, `trigger_source_id`, `convergence_pass`, `cascade_report` all correct | Convergence enforcement step is explicit |

### Anti-Pattern Comprehensiveness

The 18 anti-patterns cover:
- Convergence violations (1, 8)
- Boundary violations with other agents (3, 4, 5)
- User override respect (2)
- ROI justification requirement (6)
- Cascade chain limits (7)
- Contra signal handling (9)
- Conviction guardrail (10)
- Technical constraints (11 — psql only, 16 — score bounds, 17 — dedup check)
- Protocol compliance (12, 13, 14, 15)
- Trust level enforcement (15)
- Evidence boundary (18)

**Assessment:** Comprehensive. No obvious gaps.

### Convergence Guarantee Enforceability

| Guarantee | Mechanism | Enforceable? |
|-----------|-----------|-------------|
| Net action count trends down | Cascade Step 5 drops lowest-ROI new actions | Yes — algorithm is deterministic |
| Per-thesis cap | SQL check before grading (Step 6) | Yes — hard cap with overflow to 'Queued' |
| Diminishing returns decay | 0.7^n formula applied in strategic score | Yes — mathematical, not judgment-based |
| Daily depth budget | SQL SUM check before grading (Step 4) | Yes — hard cap at $10 |
| Staleness resolution | SQL date check in assessment | Yes — automatic downgrade at 14d |
| No infinite cascades | Chain limit = 1, checked via SQL count | Yes — hard stop |

**One concern:** The convergence exception clause ("If ALL new actions have higher ROI than all resolved actions, log exception") creates a soft escape hatch. However, the monitoring check ("If > 20% of cascades have exceptions, the system is miscalibrated") provides a second-order enforcement. Acceptable for now — worth monitoring in production.

---

## Part 2: Lifecycle Integration

### Changes Made

| File | Change |
|------|--------|
| `orchestrator/lifecycle.py` | Added Megamind as 4th managed ClaudeSDKClient (constants, ClientState, bridge tool, options builder, lifecycle functions, main loop integration) |
| `orchestrator/CLAUDE.md` | Added `send_to_megamind_agent` to capabilities table, Section 5c (Megamind usage), 3 new anti-patterns (#11-13) |
| `orchestrator/HEARTBEAT.md` | Added `strategy_*` routing to Megamind in routing table, Steps 3b-3e (depth grading check, approved depth execution, cascade trigger, strategic assessment) |
| `deploy.sh` | Updated comment header, added `live-megamind.sh` to deploy output |
| `deploy/tools/live-megamind.sh` | New file — live log viewer for megamind agent |

### lifecycle.py Integration Points (8 total)

1. **Constants:** `MEGAMIND_WORKSPACE` + `MEGAMIND_LIVE_LOG` added at module level
2. **ClientState:** `megamind_client`, `megamind_needs_restart`, `megamind_busy` added
3. **_state_dir:** `megamind` case added -> `MEGAMIND_WORKSPACE / "state"`
4. **Bridge server:** `_read_megamind_response()` + `send_to_megamind_agent` @tool added, tool list updated to 3 tools
5. **build_megamind_options():** Sonnet 4.6, 25 turns, $3.0 budget, 10K thinking, NO web tools, NO MCP servers
6. **Lifecycle functions:** `start_megamind_client()`, `stop_megamind_client()`, `restart_megamind_client()`
7. **run_agent() loop:** Startup after datum, restart check in heartbeat loop, cleanup in finally + main()
8. **Orchestrator allowed_tools:** `mcp__bridge__send_to_megamind_agent` added

### Megamind Options vs Other Agents

| Parameter | Orchestrator | Content | Datum | Megamind |
|-----------|-------------|---------|-------|----------|
| Model | Sonnet 4.6 | Sonnet 4.6 | Sonnet 4.6 | Sonnet 4.6 |
| Thinking | None | 10K | 5K | 10K |
| Effort | low | high | high | high |
| Max turns | 15 | 50 | 30 | 25 |
| Budget | $0.50 | $5.00 | $2.00 | $3.00 |
| Web tools | No | Yes | Yes | No |
| MCP servers | bridge | web | web | None |
| Agent tool | No | Yes | No | No |
| Skill tool | No | Yes | Yes | Yes |

### AST Verification

```
python3 -c "import ast; ast.parse(open('orchestrator/lifecycle.py').read()); print('AST OK')"
-> AST OK
```

### HEARTBEAT.md New Steps

| Step | Trigger | Action |
|------|---------|--------|
| 3b: Depth Grading | Ungraded agent actions in actions_queue | Send list to Megamind for grading |
| 3c: Approved Depth Execution | Approved depth_grades | Route execution_prompt to content/datum agent |
| 3d: Cascade Trigger | Completed depth_grades not yet cascaded | Send cascade trigger to Megamind |
| 3e: Strategic Assessment | 24h since last assessment | Send daily assessment request to Megamind |

### Activation Pattern

Megamind is **on-demand only** (like Datum), not heartbeat-driven (like Content pipeline). The Orchestrator wakes Megamind when strategic work exists. Megamind sleeps between prompts.

---

## Commit

```
feat: Megamind lifecycle integration — fourth managed ClaudeSDKClient
```

Files committed:
- `mcp-servers/agents/orchestrator/lifecycle.py` (core integration)
- `mcp-servers/agents/orchestrator/CLAUDE.md` (capabilities + Section 5c + anti-patterns)
- `mcp-servers/agents/orchestrator/HEARTBEAT.md` (routing + Steps 3b-3e)
- `mcp-servers/agents/megamind/CLAUDE.md` (unchanged, included for completeness)
- `mcp-servers/agents/skills/megamind/*` (unchanged, included for completeness)
- `mcp-servers/agents/deploy.sh` (megamind live log reference)
- `mcp-servers/agents/deploy/tools/live-megamind.sh` (new)
