"""Strategy cache — learn what works per site, auto-promote winners.

Uses SQLite WAL for persistence + UCB (Upper Confidence Bound) bandit
to select between candidate strategies for each origin.

WAL mode for concurrent reads/writes, init schema once at startup,
record_outcome auto-wired from lib functions (not relying on agent prompt).

threading.Lock() wraps all write operations (record_outcome, upsert, seed) to
prevent concurrent write contention on M2/multi-threaded callers.
"""

import json
import logging
import math
import sqlite3
import threading
from pathlib import Path

logger = logging.getLogger("web-agent")

DB_PATH = "/opt/web-agent/strategy.db"
_db: sqlite3.Connection | None = None
_write_lock = threading.Lock()  # Serialize all writes — M2 audit finding


def _get_db() -> sqlite3.Connection:
    """Get or create module-level connection (reused, not per-call).

    check_same_thread=False is safe here because WAL mode serializes writes
    and we use a single connection. Required for FastMCP which may call from
    different threads via run_in_executor.
    """
    global _db
    if _db is None:
        Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
        _db = sqlite3.connect(DB_PATH, timeout=10, check_same_thread=False)
        _db.row_factory = sqlite3.Row
        _db.execute("PRAGMA journal_mode=WAL")  # Safe concurrent reads/writes
        _init_schema(_db)
    return _db


def _init_schema(db: sqlite3.Connection) -> None:
    """Create tables once at startup (not per-call)."""
    db.execute("""
        CREATE TABLE IF NOT EXISTS strategies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            origin TEXT NOT NULL,
            strategy_name TEXT NOT NULL,
            config TEXT NOT NULL DEFAULT '{}',
            successes INTEGER DEFAULT 0,
            failures INTEGER DEFAULT 0,
            total_attempts INTEGER DEFAULT 0,
            avg_latency_ms REAL DEFAULT 0,
            last_used TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            UNIQUE(origin, strategy_name)
        )
    """)
    db.commit()


def get_strategy(origin: str) -> dict | None:
    """Get the best strategy for an origin using UCB bandit selection."""
    db = _get_db()
    rows = db.execute(
        "SELECT * FROM strategies WHERE origin = ?", (origin,)
    ).fetchall()

    if not rows:
        return None

    total_pulls = sum(r["total_attempts"] for r in rows)
    if total_pulls == 0:
        row = rows[0]
        return {
            "strategy_name": row["strategy_name"],
            "config": json.loads(row["config"]),
            "source": "default",
        }

    # UCB1 selection
    best_score = -1.0
    best_row = rows[0]
    for row in rows:
        if row["total_attempts"] == 0:
            return {
                "strategy_name": row["strategy_name"],
                "config": json.loads(row["config"]),
                "source": "unexplored",
            }

        success_rate = row["successes"] / row["total_attempts"]
        exploration = math.sqrt(2 * math.log(total_pulls) / row["total_attempts"])
        ucb_score = success_rate + exploration

        if ucb_score > best_score:
            best_score = ucb_score
            best_row = row

    return {
        "strategy_name": best_row["strategy_name"],
        "config": json.loads(best_row["config"]),
        "success_rate": best_row["successes"] / max(best_row["total_attempts"], 1),
        "attempts": best_row["total_attempts"],
        "source": "ucb",
    }


def record_outcome(
    origin: str, strategy_name: str, success: bool, latency_ms: float = 0
) -> None:
    """Record the outcome of a strategy attempt.

    Uses upsert — works even if the strategy hasn't been seeded yet.
    Protected by threading.Lock() to prevent concurrent write contention.
    """
    db = _get_db()
    with _write_lock:
        db.execute(
            """
            INSERT INTO strategies (origin, strategy_name, config, successes, failures, total_attempts, avg_latency_ms, last_used)
            VALUES (?, ?, '{}', ?, ?, 1, ?, datetime('now'))
            ON CONFLICT(origin, strategy_name) DO UPDATE SET
                successes = successes + excluded.successes,
                failures = failures + excluded.failures,
                total_attempts = total_attempts + 1,
                avg_latency_ms = (avg_latency_ms * total_attempts + excluded.avg_latency_ms) / (total_attempts + 1),
                last_used = datetime('now')
        """,
            (
                origin,
                strategy_name,
                1 if success else 0,
                0 if success else 1,
                latency_ms,
            ),
        )
        db.commit()


def seed_strategies(origin: str, fingerprint_result: dict) -> None:
    """Seed default strategies for a new origin based on its fingerprint.

    Protected by threading.Lock() to prevent concurrent write contention.
    """
    db = _get_db()

    strategies = []
    if fingerprint_result.get("is_spa"):
        strategies = [
            ("jina_reader", {"method": "jina"}),
            ("browser_mutation_observer", {"method": "browse", "readiness": "auto"}),
            ("browser_time_wait", {"method": "browse", "readiness": "time:5000"}),
        ]
    else:
        strategies = [
            ("jina_reader", {"method": "jina"}),
            ("browser_fast", {"method": "browse", "readiness": "none"}),
        ]

    if fingerprint_result.get("auth_required"):
        strategies.append(
            (
                "browser_with_cookies",
                {"method": "browse", "readiness": "auto", "cookies": True},
            )
        )

    with _write_lock:
        for name, config in strategies:
            db.execute(
                """
                INSERT OR IGNORE INTO strategies (origin, strategy_name, config)
                VALUES (?, ?, ?)
            """,
                (origin, name, json.dumps(config)),
            )
        db.commit()


def get_all_strategies() -> list[dict]:
    """Get all strategies across all origins (for diagnostics)."""
    db = _get_db()
    rows = db.execute(
        "SELECT * FROM strategies ORDER BY origin, successes DESC"
    ).fetchall()
    return [dict(r) for r in rows]
