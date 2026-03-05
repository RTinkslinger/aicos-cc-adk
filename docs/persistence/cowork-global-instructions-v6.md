# Cowork Global Instructions — v6.2.0 (March 4, 2026)
# This is the EXACT text to paste into: Claude Desktop → Settings → Cowork → Global Instructions
# These instructions apply to ALL Cowork sessions, before any skill loads.

# --- PASTE BELOW THIS LINE ---

## Session Hygiene (always enforce)
- When I say "checkpoint", "save state", or "save progress": immediately write a pickup file to `docs/session-checkpoints/` in my project folder. Capture what's done, what's in progress, what's pending, key files modified. Fast — under 60 seconds.
- When I say "close session", "end session", "wrap up", or "session done": execute the mandatory 8-step close checklist: (1a) write iteration log to `docs/iteration-logs/`, (1b) Build Roadmap insights if any, (1c) Session Behavioral Audit via Bash subagent, (2) update CONTEXT.md, (3) update CLAUDE.md last session ref, (4) sync thesis threads to Notion, (5) update `docs/v6-artifacts-index.md` with version bumps, (6) package updated skills as .skill ZIPs, (7) update Build Roadmap metadata in Notion, (8) confirm all steps complete.
- Steps 2, 3, 5 MUST use Bash subagents — never edit these large files from main session (prevents context compaction).
- Never skip session-end updates. The system enforces its own maintenance.

## Project Context
- My AI CoS project folder is at `/Users/Aakash/Claude Projects/Aakash AI CoS`. When mounted, read `CONTEXT.md` first — it's the single source of truth.
- For any Notion operations, load the `notion-mastery` skill before making calls.
- For anything related to my investing work, meetings, network, pipeline, thesis, IDS, portfolio, actions, or scoring: load the `ai-cos` skill.

## Subagent Handling (critical)
- Bash subagents get ONLY the prompt text — no CLAUDE.md, no skills, no MCP tools, no conversation history.
- ALWAYS check `scripts/subagent-prompts/` template library before spawning a subagent.
- Every subagent prompt MUST include: SUBAGENT CONSTRAINTS block, file allowlist, sandbox rules, HAND-OFF protocol for MCP tasks.
- MCP operations (Notion, osascript, present_files) stay in main session — subagents hand off via output.

## Operating Principles
- I live on mobile and WhatsApp. Never design for desktop dashboards.
- Every interaction is a learning session for the AI CoS build. At the end of any task, note if findings connect to my thesis threads, pipeline companies, or suggest new actions.
- My primary methodology is IDS (Increasing Degrees of Sophistication).
- Ask clarifying questions before starting multi-step work.

# --- END PASTE ---
