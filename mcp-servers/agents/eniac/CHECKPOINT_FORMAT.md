# ENIAC Checkpoint Format

When sending checkpoint state to the Orchestrator, use this format:

```json
{
  "agent": "eniac",
  "status": "idle|researching|health_check|error",
  "session_metrics": {
    "queue_items_processed": 0,
    "findings_saved": 0,
    "health_checks_run": false,
    "bias_checks_run": false,
    "alerts_sent": 0
  },
  "current_research": {
    "entity_type": null,
    "entity_id": null,
    "entity_name": null,
    "started_at": null
  },
  "last_health_check": {
    "theses_needing_attention": [],
    "portfolio_risks": [],
    "emerging_signals": [],
    "bias_alerts": []
  },
  "errors": []
}
```

## Field Definitions

- `status`: Current agent state. `idle` = waiting for work. `researching` = actively
  working a queue item. `health_check` = running periodic health checks. `error` =
  something went wrong.
- `session_metrics`: Cumulative counts for this session. Reset on agent restart.
- `current_research`: What ENIAC is actively working on. Null fields when idle.
- `last_health_check`: Summary of most recent health check findings. Orchestrator uses
  this to decide whether to trigger follow-up work.
- `errors`: Array of error strings from this session. Orchestrator monitors for patterns.
