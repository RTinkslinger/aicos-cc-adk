"""Shared types across all agents. Import from here, not from individual agents."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class DigestData:
    """Schema for content analysis output. Content Agent produces, Sync Agent consumes."""

    title: str
    slug: str
    url: str
    channel: str
    content_type: str = ""
    duration: str = ""
    relevance_score: str = "Medium"
    net_newness: dict[str, Any] = field(default_factory=dict)
    connected_buckets: list[str] = field(default_factory=list)
    essence_notes: dict[str, Any] = field(default_factory=dict)
    thesis_connections: list[dict[str, Any]] = field(default_factory=list)
    portfolio_connections: list[dict[str, Any]] = field(default_factory=list)
    proposed_actions: list[dict[str, Any]] = field(default_factory=list)
    contra_signals: list[dict[str, Any]] = field(default_factory=list)
    rabbit_holes: list[dict[str, Any]] = field(default_factory=list)
    watch_sections: list[dict[str, Any]] = field(default_factory=list)
    new_thesis_suggestions: list[dict[str, Any]] = field(default_factory=list)
    generated_at: str = ""
    upload_date: str | None = None
    request_id: str = ""  # Idempotency key (C2)


@dataclass
class ActionProposal:
    """Single proposed action from content analysis."""

    action: str
    priority: str = "P2"
    action_type: str = "content"
    assigned_to: str = "Aakash"
    reasoning: str = ""
    thesis_connections: list[str] = field(default_factory=list)
    company: str | None = None
    score: float = 0.0
    classification: str = "context_only"
    request_id: str = ""  # Idempotency key (C2)


@dataclass
class ThesisEvidence:
    """Evidence to append to a thesis thread."""

    thesis_name: str
    evidence: str
    direction: str = "for"  # "for", "against", "mixed"
    source: str = "Content Pipeline"
    conviction: str | None = None
    new_key_questions: list[str] | None = None
    answered_questions: list[str] | None = None
    investment_implications: str | None = None
    key_companies: str | None = None
    request_id: str = ""  # Idempotency key (C2)
