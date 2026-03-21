"""
Cindy Email Processing Pipeline.

AgentMail integration for cindy.aacash@agentmail.to.
Polls inbox, parses messages, extracts signals and obligations,
resolves people, and writes to Supabase.

Usage:
    python3 -m cindy.email --dry-run --use-sample-data
    python3 -m cindy.email --since 2h
    python3 -m cindy.email --help
"""

from cindy.email.email_processor import (
    AgentMailClient,
    DatabaseWriter,
    EmailMessage,
    extract_action_items,
    extract_deal_signals,
    extract_thesis_signals,
    main,
    parse_agentmail_message,
    process_email,
    run,
)
from cindy.email.obligation_extractor import (
    extract_due_date,
    extract_obligations,
)

__all__ = [
    "AgentMailClient",
    "DatabaseWriter",
    "EmailMessage",
    "extract_action_items",
    "extract_deal_signals",
    "extract_due_date",
    "extract_obligations",
    "extract_thesis_signals",
    "main",
    "parse_agentmail_message",
    "process_email",
    "run",
]
