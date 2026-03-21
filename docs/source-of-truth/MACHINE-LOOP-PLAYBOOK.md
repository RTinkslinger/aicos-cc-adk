# Machine Loop Playbook — Operational Supplement

**Primary reference: `GOLDEN-SESSION-PATTERN.md` (v2). This file is supplementary.**

This playbook contains operational details that supplement the golden pattern. For the core pattern, machine list, loop structure, feedback system, and session checklist — read the golden pattern file.

---

## Quick Reference: "Resume Machineries"

```
1. Read CHECKPOINT.md
2. Read GOLDEN-SESSION-PATTERN.md (entire file)
3. Create docs/feedback-timeline-YYYY-MM-DD.md
4. Create task dashboard (TaskCreate per machine)
5. Launch ALL permanent machines as perpetual loops IN PARALLEL
6. Each prompt: feedback check SQL + cross-machine context + "DO NOT ASK — EXECUTE"
7. As machines complete: check feedback → report inline → relaunch
8. Never stop until user says pause/sync/stop
```

## Machine Prompt Template

See Section 7 of GOLDEN-SESSION-PATTERN.md.

## Feedback Infrastructure

See Section 4 of GOLDEN-SESSION-PATTERN.md.

SQL functions deployed to Supabase `llfkxnsfczludgigknbs`:
- `get_machine_feedback(machine_name)` — returns unprocessed feedback
- `mark_feedback_processed(feedback_id, machine_name)` — marks as handled
- `user_feedback_store` table with `processed_by text[]` column

## Key Supabase IDs

- Project: `llfkxnsfczludgigknbs` (Mumbai)
- Feedback table: `user_feedback_store`
- Agent feedback: `agent_feedback_store`
- Key questions: `portfolio_key_questions` (386 rows with embeddings)

## Cindy Email Setup

- Cindy's inbox: `cindy.aacash@agentmail.to`
- AgentMail API key: on droplet at `/opt/agents/.env`
- Gmail MCP: OUT OF SCOPE (user's work email is Outlook)
- Cindy reads HER inbox only. User forwards/CCs to her.

## Droplet Services

- State MCP: `:8000` (mcp.3niac.com)
- Web Tools MCP: `:8001` (web.3niac.com)
- Orchestrator: manages Content Agent + other agents
- All services via systemd, managed by lifecycle.py
