# Single-Server Multi-Agent Playbook

**Source run:** `trun_...b008340c571cb475`
**Date:** 2026-03-15

## Key Concepts

- **Postgres SKIP LOCKED queues** — Use `SELECT ... FOR UPDATE SKIP LOCKED` as a lightweight job queue. No external broker needed; each agent worker atomically claims rows without contention.
- **Blackboard pattern** — Shared state store (Postgres table or in-memory dict) where agents read/write intermediate results. Decouples agents from each other while enabling collaboration on shared data.
- **systemd timers vs cron** — systemd timers offer dependency ordering, journal integration, `OnBootSec`/`OnUnitActiveSec` flexibility, and cgroup isolation. Prefer over cron for agent scheduling.
- **Circuit breakers with DEGRADED state** — Three states: CLOSED (normal), OPEN (failing, stop calls), DEGRADED (partial service, reduced rate). Prevents cascade failures when downstream services flap.
- **Saga pattern + idempotency keys** — Multi-step workflows use compensating transactions on failure (Saga). Idempotency keys ensure retries don't duplicate side effects (Notion writes, emails).
- **Advisory locks** — Postgres `pg_advisory_lock()` for cross-process mutual exclusion without table-level locking. Use for singleton agent tasks (e.g., only one sync agent runs at a time).
- **Unix domain sockets (2us latency)** — For inter-agent communication on the same host, UDS eliminates TCP overhead. 2 microsecond round-trip vs ~100us for localhost TCP.
- **journald 500MB cap** — Set `SystemMaxUse=500M` in `/etc/systemd/journald.conf` to prevent agent logs from filling disk. Use structured logging (`logger --journald`) for queryability.
- **LangGraph vs CrewAI vs Claude Agent SDK** — LangGraph: graph-based state machines, max flexibility, high complexity. CrewAI: role-based delegation, quick prototyping, less control. Claude Agent SDK: native Anthropic integration, first-party tool support, production-grade but Anthropic-only.

## Top 5 References

1. Postgres advisory locks — `postgresql.org/docs/current/explicit-locking.html`
2. Circuit breaker pattern (Martin Fowler) — `martinfowler.com/bliki/CircuitBreaker.html`
3. Saga pattern — `microservices.io/patterns/data/saga.html`
4. systemd timer documentation — `freedesktop.org/software/systemd/man/systemd.timer.html`
5. LangGraph documentation — `langchain-ai.github.io/langgraph/`
