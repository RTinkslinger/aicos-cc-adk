"""In-memory store for async web tasks (CAI submit/poll/retrieve pattern)."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class WebTask:
    """A single async web task with lifecycle tracking."""

    task_id: str
    task: str
    url: str
    status: str = "started"  # started, running, complete, error
    result: dict | None = None
    error: str | None = None
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    cost_usd: float | None = None


_tasks: dict[str, WebTask] = {}


def create_task(task: str, url: str = "") -> WebTask:
    """Create a new task entry and store it. Returns the WebTask."""
    t = WebTask(task_id=f"wt_{uuid.uuid4().hex[:12]}", task=task, url=url)
    _tasks[t.task_id] = t
    return t


def get_task(task_id: str) -> WebTask | None:
    """Look up a task by ID. Returns None if not found."""
    return _tasks.get(task_id)


def complete_task(task_id: str, result: dict, cost_usd: float = 0) -> None:
    """Mark a task as complete with its result."""
    t = _tasks.get(task_id)
    if t:
        t.status = "complete"
        t.result = result
        t.cost_usd = cost_usd
        t.completed_at = datetime.utcnow()


def fail_task(task_id: str, error: str) -> None:
    """Mark a task as failed with an error message."""
    t = _tasks.get(task_id)
    if t:
        t.status = "error"
        t.error = error
        t.completed_at = datetime.utcnow()
