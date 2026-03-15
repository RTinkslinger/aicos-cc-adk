"""Notion field formatting utilities for Content Agent.

Extracted from runners/content_agent.py. Converts DigestData dicts into
Notion rich_text field strings.
"""
from __future__ import annotations

from typing import Any


def format_summary(digest: dict[str, Any]) -> str:
    """Build Summary from essence_notes core arguments."""
    en = digest.get("essence_notes", {})
    args = en.get("core_arguments", [])
    if not args:
        return ""
    return "\n".join(f"• {a}" for a in args)


def format_key_insights(digest: dict[str, Any]) -> str:
    """Build Key Insights from essence_notes frameworks + data points."""
    en = digest.get("essence_notes", {})
    parts: list[str] = []
    for fw in en.get("frameworks", []):
        parts.append(f"[Framework] {fw}")
    for dp in en.get("data_points", []):
        parts.append(f"[Data] {dp}")
    for pred in en.get("predictions", []):
        parts.append(f"[Prediction] {pred}")
    return "\n".join(parts) if parts else ""


def format_thesis_connections_text(digest: dict[str, Any]) -> str:
    """Format thesis connections for Notion rich_text."""
    tcs = digest.get("thesis_connections", [])
    if not tcs:
        return ""
    lines: list[str] = []
    for tc in tcs:
        direction = tc.get("evidence_direction", "")
        strength = tc.get("strength", "")
        lines.append(f"• {tc.get('thread', '')} [{strength}, {direction}]: {tc.get('connection', '')}")
    return "\n".join(lines)


def format_portfolio_relevance(digest: dict[str, Any]) -> str:
    """Format portfolio connections for Notion rich_text."""
    pcs = digest.get("portfolio_connections", [])
    if not pcs:
        return ""
    lines: list[str] = []
    for pc in pcs:
        lines.append(f"• {pc.get('company', '')}: {pc.get('relevance', '')}")
        if pc.get("key_question"):
            lines.append(f"  Key Q: {pc['key_question']}")
    return "\n".join(lines)


def format_essence_notes(digest: dict[str, Any]) -> str:
    """Format essence notes for Notion rich_text."""
    en = digest.get("essence_notes", {})
    if not en:
        return ""
    parts: list[str] = []
    for arg in en.get("core_arguments", []):
        parts.append(f"• {arg}")
    for quote in en.get("key_quotes", []):
        speaker = quote.get("speaker", "")
        ts = quote.get("timestamp", "")
        parts.append(f'"{quote.get("text", "")}" —{speaker} [{ts}]')
    return "\n".join(parts) if parts else ""


def format_watch_sections(digest: dict[str, Any]) -> str:
    """Format watch sections for Notion rich_text."""
    ws = digest.get("watch_sections", [])
    if not ws:
        return ""
    lines: list[str] = []
    for s in ws:
        lines.append(f"• [{s.get('timestamp_range', '')}] {s.get('title', '')}")
        lines.append(f"  Why: {s.get('why_watch', '')}")
    return "\n".join(lines)


def format_contra_signals(digest: dict[str, Any]) -> str:
    """Format contra signals for Notion rich_text."""
    cs = digest.get("contra_signals", [])
    if not cs:
        return ""
    lines: list[str] = []
    for c in cs:
        strength = c.get("strength", "")
        lines.append(f"• [{strength}] {c.get('what', '')}")
        if c.get("implication"):
            lines.append(f"  → {c['implication']}")
    return "\n".join(lines)


def format_rabbit_holes(digest: dict[str, Any]) -> str:
    """Format rabbit holes for Notion rich_text."""
    rhs = digest.get("rabbit_holes", [])
    if not rhs:
        return ""
    lines: list[str] = []
    for r in rhs:
        lines.append(f"• {r.get('title', '')}: {r.get('what', '')}")
        if r.get("entry_point"):
            lines.append(f"  Start: {r['entry_point']}")
    return "\n".join(lines)


def format_proposed_actions_summary(digest: dict[str, Any]) -> str:
    """Format proposed actions summary for Notion rich_text."""
    actions = digest.get("proposed_actions", [])
    if not actions:
        return ""
    lines: list[str] = []
    for a in actions:
        score_str = f" (score: {a['score']})" if a.get("score") else ""
        lines.append(f"• [{a.get('priority', 'P2')}]{score_str} {a.get('action', '')}")
    return "\n".join(lines)
