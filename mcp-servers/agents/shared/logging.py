"""Structured JSON logging for all agents. Trace ID propagation across agent boundaries."""
from __future__ import annotations

import logging
import uuid
from contextvars import ContextVar

from pythonjsonlogger import json as jsonlogger

# Trace ID for cross-agent request correlation (C4)
_trace_id: ContextVar[str] = ContextVar("trace_id", default="")


def get_trace_id() -> str:
    """Get current trace ID from context."""
    return _trace_id.get() or ""


def set_trace_id(trace_id: str | None = None) -> str:
    """Set trace ID in context. Generates one if not provided."""
    tid = trace_id or uuid.uuid4().hex[:16]
    _trace_id.set(tid)
    return tid


class AgentJsonFormatter(jsonlogger.JsonFormatter):
    """JSON formatter that injects trace_id and agent name into every log entry."""

    def add_fields(
        self,
        log_record: dict,
        record: logging.LogRecord,
        message_dict: dict,
    ) -> None:
        super().add_fields(log_record, record, message_dict)
        log_record["trace_id"] = get_trace_id()
        log_record["agent"] = getattr(record, "agent", record.name)


def setup_logger(agent_name: str, log_file: str | None = None) -> logging.Logger:
    """Create a structured JSON logger for an agent.

    Args:
        agent_name: Name of the agent (e.g., "sync-agent", "web-agent")
        log_file: Optional path to log file. If None, logs only to stderr.
    """
    logger = logging.getLogger(agent_name)
    if logger.handlers:
        return logger  # Already configured

    logger.setLevel(logging.INFO)

    formatter = AgentJsonFormatter(
        fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
        rename_fields={"asctime": "timestamp", "levelname": "level", "name": "agent"},
    )

    # Console handler (stderr)
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File handler
    if log_file:
        fh = logging.FileHandler(log_file)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger
