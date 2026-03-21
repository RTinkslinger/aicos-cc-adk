"""
Cindy Email Pipeline — Thin Fetcher Only.

Fetches emails from AgentMail and stages raw data in interaction_staging.
NO signal extraction, NO obligation detection, NO people resolution.

Datum Agent resolves people and writes to interactions.
Cindy Agent reasons about obligations and signals via LLM.

Usage:
    python3 -m cindy.email.fetcher --dry-run --use-sample
    python3 -m cindy.email.fetcher --since 2h
"""

from cindy.email.fetcher import (
    AgentMailClient,
    EmailMessage,
    StagingWriter,
    fetch_and_stage,
    main,
    parse_agentmail_message,
)

__all__ = [
    "AgentMailClient",
    "EmailMessage",
    "StagingWriter",
    "fetch_and_stage",
    "main",
    "parse_agentmail_message",
]
