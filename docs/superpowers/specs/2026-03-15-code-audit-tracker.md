# Code Audit Tracker — Three-Agent Architecture

**Date:** 2026-03-15
**Status:** In progress — 2/25 resolved, 23 remaining

## Resolution Log

| # | Issue | Status | Action Taken | Downstream Check |
|---|-------|--------|-------------|-----------------|
| **C1** | query() with hooks | **NOT A BUG** | Tested on droplet: hooks DO fire with query() in SDK 0.1.48. SDK audit relied on outdated README. Table in 02-query-and-client.md confirms hooks supported in 0.1.x+. | None needed |
| **C5** | Broken imports (from runners., from lib.) | **FIXED** | Fixed 10 imports across 3 files: sync/tools.py (4), sync/lib/notion_client.py (5), sync/lib/change_detection.py (1). Rewrote cos_sync_actions, cos_full_sync, cos_process_changes. Deployed + restarted. | Verify sync cycle runs without import errors (check journalctl -u sync-agent after 10 min) |

## Remaining Items

### CRITICAL
| # | Issue | File(s) | Priority |
|---|-------|---------|----------|
| C2 | Health check protocol (GET→POST+JSON-RPC) | deploy.sh, health_check.sh | Next |
| C3 | Cron install duplicates on re-run | systemd/install.sh | Next |
| C4 | Global _tools_called race condition | content/hooks.py | Next |
| C6 | Unclosed psycopg2 connections | sync/tools.py, sync/lib/*.py | Next |

### HIGH
| # | Issue | File(s) |
|---|-------|---------|
| H1 | Fingerprint tool name mismatch | web/tools.py, web/agent.py |
| H2 | WatchdogSec=120 but no sd_notify | All .service files |
| H3 | pkill -f chrome kills all Chrome | web-agent.service |
| H4 | No Postgres readiness check | sync/server.py |
| H5 | EnvironmentFile=- makes .env optional | All .service files |
| H6 | Partial failure in write_actions batch | sync/tools.py |
| H7 | Model name should be env-configurable | All agent.py files |

### MEDIUM
| # | Issue | File(s) |
|---|-------|---------|
| M1 | Double logging (file + systemd) | shared/logging.py, .service files |
| M2 | Deploy waits only 3s for sync-agent | deploy.sh |
| M3 | Thread-unsafe rate limit dict | web/hooks.py |
| M4 | Non-atomic dedup file write | sync/lib/dedup.py |
| M5 | Race condition on idempotency INSERT | sync/tools.py |
| M6 | scoring.py validate() never called | content/lib/scoring.py |

### LOW
| # | Issue | File(s) |
|---|-------|---------|
| L1 | Hook signatures use bare object | All hooks.py |
| L2 | Hardcoded SDK server version | web/tools.py, content/tools.py |

## Downstream Checks Pending
1. Verify sync cycle completes without errors: `ssh root@aicos-droplet "journalctl -u sync-agent --since '10 min ago' | grep -E 'error|sync_cycle'"` — check after 10 min
2. (More checks will be added as fixes are applied)
