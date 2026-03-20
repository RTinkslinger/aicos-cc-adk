# Parallel Dashboard & Past Research Findings
*Audit date: 2026-03-20*

## Summary

**No batch enrichment of 140+ portfolio companies was found.** The Parallel platform has been used for individual deep research runs (not batch enrichment), and only 20 portfolio companies have research files. The "140-150 companies" figure refers to DeVC's portfolio size per fund cycle (from Session 001 planning notes), not to a completed Parallel research batch.

## Key Findings

### 1. No "List Past Runs" Capability Exists

The Parallel API does **not** have a list/history endpoint. You can only:
- Retrieve a specific run by `run_id` (`GET /v1/tasks/runs/{run_id}`)
- Fetch runs within a specific task group by `taskgroup_id` (`GET /v1beta/tasks/groups/{taskgroup_id}/runs`)

The `parallel-cli` has no `list` or `history` subcommand. The only way to find past runs is:
1. The **Parallel platform dashboard** (requires browser login at `platform.parallel.ai`)
2. Saved run IDs in local files

### 2. Dashboard Requires Interactive Browser Login

The Parallel platform at `https://platform.parallel.ai` requires OAuth authentication (Email, Google, or SSO). The stored CLI credential (`~/.config/parallel-web-tools/credentials.json`) is an OAuth access token, not an API key usable for dashboard access. Automated browser login was not possible in this session (click permission denied).

**To access the dashboard manually:**
1. Open `https://platform.parallel.ai` in a browser
2. Sign in with Google (or email link)
3. Navigate to research history / past runs

### 3. Known Run IDs Found in Local Files

All discovered run IDs are for **individual deep research** (topic research, not portfolio company enrichment):

| Run ID | Status | Processor | Created | Topic |
|--------|--------|-----------|---------|-------|
| `trun_4719934bf6364778a0cb03bf66411d9d` | completed | ultra | 2026-03-11 | CC-CAI sync research |
| `trun_4719934bf6364778aa2e5ec7a1d3c6fc` | completed | ultra | 2026-03-16 | OpenClaw architecture |
| `trun_4e978fe567d34864a2ff30ae46574b8b` | completed | ultra-fast | 2026-03-19 | Supabase agent capabilities |
| `trun_4e978fe567d34864ab905a9cd710914a` | completed | ultra-fast | 2026-03-19 | Supabase new keys + agent mastery |
| `trun_...a26d6a581881fe0d` (partial) | completed | - | ~2026-03-15 | SPA/PWA content extraction |
| `trun_...a2f508c1d97ad560` (partial) | completed | - | ~2026-03-15 | Agent adaptation/learning |
| `trun_...92e5e3af722acd83` (partial) | completed | - | ~2026-03-15 | Anti-detection stealth |
| `trun_...8e72da218f93bc21` (partial) | completed | - | ~2026-03-15 | Agent MCP integration |
| `trun_...ae34733a5c50e8b2` (partial) | completed | - | ~2026-03-15 | Agent SDK fundamentals |
| `trun_...b008340c571cb475` (partial) | completed | - | ~2026-03-15 | Multi-agent orchestration |
| `trun_4719934bf6364778aa54f47886bd8a0f` (ref only) | - | - | ~2026-03-15 | Production patterns |

**Zero task group IDs (`tgrp_*`) were found anywhere** in the codebase, conversation logs, or subagent logs. No batch enrichment has been run.

### 4. Existing Portfolio Research (20 Companies, Not 140+)

The `portfolio-research/` directory contains **20 deep research files**, all batch-created on **2026-03-09**. These appear to have been generated via Parallel deep research (individual runs), not via the Task Group batch enrichment API.

**Companies with research files:**
1. Atica (Hospitality tech)
2. Ballisto / Orbit AgriTech (AgriTech / EV farm mechanization)
3. Boba Bhai (F&B chain)
4. CodeAnt AI (Developer tools)
5. Confido Health (Healthcare)
6. Cybrilla (Fintech infrastructure)
7. Dodo Payments (Payments)
8. GameRamp (Gaming)
9. Highperformr AI (Social media AI)
10. InspeCity (Construction tech)
11. Isler (Climate tech)
12. Legend of Toys (D2C toys)
13. Orange Slice (Unverified - disambiguation needed)
14. PowerUp Money (Fintech)
15. Smallest.ai (Voice AI)
16. Stance Health (Healthcare)
17. StepSecurity (DevSecOps)
18. Terafac (Manufacturing)
19. Terractive (Climate/Agriculture)
20. Unifize (Manufacturing SaaS)

**Gap:** The Companies DB has ~2,000 records, and DeVC targets 140-150 companies per fund cycle. Only 20 have Parallel deep research.

### 5. Platform Result URLs

Past runs can be viewed at these URLs (after logging in to `platform.parallel.ai`):

- `https://platform.parallel.ai/play/deep-research/trun_4e978fe567d34864ab905a9cd710914a`
- `https://platform.parallel.ai/play/deep-research/trun_4e978fe567d34864a2ff30ae46574b8b`
- `https://platform.parallel.ai/play/deep-research/trun_4719934bf6364778aa2e5ec7a1d3c6fc`
- `https://platform.parallel.ai/play/deep-research/trun_4719934bf6364778a0cb03bf66411d9d`

## Recommendations

### To Access Past Dashboard Results
1. **Log in manually** at `https://platform.parallel.ai` via browser
2. Look for a "History" or "Runs" tab in the sidebar/navigation
3. The dashboard should show all past runs associated with the account

### To Research the Remaining 120+ Companies
Use the Parallel Task Group API (`createTaskGroup`) for batch enrichment:

```
# Example: Batch enrich companies from Notion Companies DB
1. Query Companies DB via Notion MCP to get full company list
2. Use createTaskGroup with inputs = company names/websites
3. Output fields: CEO, sector, funding stage, latest round, revenue, key metrics
4. Processor: base or core (cost-effective for structured enrichment)
```

Estimated cost for 140 companies at `base` processor: ~$7-14 (at $0.05-0.10/task).

### To Track Run IDs Going Forward
Save all `trun_*` and `tgrp_*` IDs to a local registry file (e.g., `docs/research/parallel-run-registry.json`) so past results remain accessible without needing the dashboard.

## Technical Details

### Authentication
- **CLI auth:** OAuth via `parallel-cli auth` (working, stored at `~/.config/parallel-web-tools/credentials.json`)
- **API key:** `Ojxgt2idrDN7uVxY3U6EPUlKX3phFfwjx6KFSEW8` (stored in credentials, works for API calls)
- **Dashboard:** Requires separate browser-based OAuth login at `platform.parallel.ai`

### API Endpoints Verified
| Endpoint | Method | Works? | Notes |
|----------|--------|--------|-------|
| `/v1/tasks/runs/{run_id}` | GET | Yes | Retrieves individual run status |
| `/v1/tasks/runs/{run_id}/result` | GET | Yes | Retrieves run results |
| `/v1/tasks/runs` | GET | No | "No Product supports method: GET for path" |
| `/v1beta/tasks/groups/{tgrp_id}/runs` | GET | Untested | No task group IDs found |

### File Locations
- Portfolio research: `/Users/Aakash/Claude Projects/Aakash AI CoS CC ADK/portfolio-research/` (20 files)
- Parallel CLI config: `/Users/Aakash/.parallel-cli/config.json`
- Parallel credentials: `/Users/Aakash/.config/parallel-web-tools/credentials.json`
- Research JSON outputs: `/Users/Aakash/Claude Projects/Aakash AI CoS CC ADK/docs/research/*.json` (2 files)
- Prior catalog: `/Users/Aakash/Claude Projects/Aakash AI CoS CC ADK/docs/audits/2026-03-20-research-files-catalog-local.md`
