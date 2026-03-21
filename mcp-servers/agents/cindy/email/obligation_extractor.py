#!/usr/bin/env python3
"""
Obligation Extractor for Cindy.

Pattern-based detection of commitments and requests from email text.
Follows the obligation detection spec in skills/cindy/obligation-detection.md.

Two obligation types:
  - I_OWE_THEM: Aakash committed to do something for someone
  - THEY_OWE_ME: Someone committed to do something for Aakash

Categories: send_document, reply, schedule, follow_up, introduce,
            review, deliver, connect, provide_info, other

Confidence threshold: >= 0.7 to create an obligation.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Aakash's known email addresses (used for direction inference)
# ---------------------------------------------------------------------------

AAKASH_EMAILS = {
    "ak@z47.com",
    "aakash@z47.com",
    "aakash@devc.fund",
    "hi@aacash.me",
}


# ---------------------------------------------------------------------------
# Commitment patterns (regex + metadata)
# ---------------------------------------------------------------------------

# I_OWE_THEM: Aakash (first-person) committed to do something
_I_OWE_PATTERNS: list[dict[str, Any]] = [
    {
        "pattern": r"(?:i'?ll|i will|let me|i'?m going to)\s+send\b",
        "category": "send_document",
        "confidence": 0.90,
    },
    {
        "pattern": r"(?:i'?ll|i will|let me)\s+(?:get back|circle back|revert|respond|reply)\b",
        "category": "reply",
        "confidence": 0.85,
    },
    {
        "pattern": r"(?:i'?ll|i will|let me)\s+(?:schedule|set up|arrange|book)\b",
        "category": "schedule",
        "confidence": 0.85,
    },
    {
        "pattern": r"(?:i'?ll|i will|let me)\s+(?:follow up|follow-up|check (?:on|with))\b",
        "category": "follow_up",
        "confidence": 0.80,
    },
    {
        "pattern": r"(?:i'?ll|i will|let me)\s+(?:introduce|connect)\s+you\b",
        "category": "introduce",
        "confidence": 0.90,
    },
    {
        "pattern": r"(?:i'?ll|i will|let me)\s+(?:review|look at|go through|take a look)\b",
        "category": "review",
        "confidence": 0.80,
    },
    {
        "pattern": r"(?:i'?ll|i will|let me)\s+(?:share|forward|pass along|send over)\b",
        "category": "send_document",
        "confidence": 0.85,
    },
    {
        "pattern": r"(?:i'?ll|i will)\s+(?:do|handle|take care of|work on)\b",
        "category": "other",
        "confidence": 0.75,
    },
    {
        "pattern": r"(?:will do|on it|i'?m on it|consider it done)\b",
        "category": "other",
        "confidence": 0.75,
    },
    {
        "pattern": r"(?:i'?ll|let me)\s+(?:ping|loop in|bring in|pull in)\b",
        "category": "connect",
        "confidence": 0.80,
    },
    {
        "pattern": r"(?:i'?ll|let me)\s+(?:find out|check|confirm|verify)\b",
        "category": "provide_info",
        "confidence": 0.75,
    },
]

# THEY_OWE_ME: Someone else committed to do something for Aakash
_THEY_OWE_PATTERNS: list[dict[str, Any]] = [
    {
        "pattern": r"(?:i'?ll|i will|let me)\s+send\s+(?:you|it|the|that)\b",
        "category": "send_document",
        "confidence": 0.85,
    },
    {
        "pattern": r"(?:i'?ll|i will|let me)\s+(?:get back|circle back|revert)\s+(?:to you)?\b",
        "category": "reply",
        "confidence": 0.80,
    },
    {
        "pattern": r"(?:i'?ll|i will)\s+(?:share|forward|send over)\b",
        "category": "send_document",
        "confidence": 0.80,
    },
    {
        "pattern": r"(?:i'?ll|i will)\s+(?:schedule|set up|arrange)\b",
        "category": "schedule",
        "confidence": 0.80,
    },
    {
        "pattern": r"(?:i'?ll|i will)\s+(?:follow up|check|confirm|look into)\b",
        "category": "follow_up",
        "confidence": 0.75,
    },
    {
        "pattern": r"(?:i'?ll|i will)\s+(?:introduce|connect)\b",
        "category": "introduce",
        "confidence": 0.80,
    },
    {
        "pattern": r"we(?:'?ll| will)\s+(?:send|share|provide|deliver|get back)\b",
        "category": "deliver",
        "confidence": 0.75,
    },
]

# REQUEST patterns: Aakash asks someone to do something -> THEY_OWE_ME
_REQUEST_PATTERNS: list[dict[str, Any]] = [
    {
        "pattern": r"(?:could you|can you|would you)\s+(?:send|share|forward)\b",
        "category": "send_document",
        "confidence": 0.85,
    },
    {
        "pattern": r"(?:could you|can you|would you)\s+(?:please\s+)?(?:send|share|forward)\b",
        "category": "send_document",
        "confidence": 0.85,
    },
    {
        "pattern": r"(?:please|pls)\s+(?:send|share|forward|provide)\b",
        "category": "send_document",
        "confidence": 0.80,
    },
    {
        "pattern": r"(?:could you|can you|would you)\s+(?:please\s+)?(?:review|look at|check)\b",
        "category": "review",
        "confidence": 0.75,
    },
    {
        "pattern": r"(?:could you|can you|would you)\s+(?:please\s+)?(?:schedule|set up|arrange)\b",
        "category": "schedule",
        "confidence": 0.75,
    },
    {
        "pattern": r"(?:could you|can you|would you)\s+(?:please\s+)?(?:follow up|check on)\b",
        "category": "follow_up",
        "confidence": 0.75,
    },
    {
        "pattern": r"(?:could you|can you|would you)\s+(?:please\s+)?(?:introduce|connect)\b",
        "category": "introduce",
        "confidence": 0.80,
    },
    {
        "pattern": r"(?:could you|can you|would you mind)\b",
        "category": "other",
        "confidence": 0.70,
    },
]


# ---------------------------------------------------------------------------
# Date extraction from natural language
# ---------------------------------------------------------------------------

# Relative date references
_DATE_PATTERNS: list[tuple[str, int]] = [
    (r"\b(?:today|eod|end of day)\b", 0),
    (r"\btomorrow\b", 1),
    (r"\bday after tomorrow\b", 2),
    (r"\b(?:eow|end of week)\b", 5),   # approximate: next Friday
    (r"\bnext week\b", 7),
    (r"\b(?:this|next) monday\b", -1),  # computed dynamically
    (r"\b(?:this|next) tuesday\b", -1),
    (r"\b(?:this|next) wednesday\b", -1),
    (r"\b(?:this|next) thursday\b", -1),
    (r"\b(?:this|next) friday\b", -1),
    (r"\b(?:next month|end of month|eom)\b", 30),
    (r"\b(?:in a few days|in a couple days)\b", 3),
    (r"\b(?:in a week|within a week)\b", 7),
    (r"\b(?:in two weeks|in 2 weeks)\b", 14),
]

_DAY_NAME_TO_WEEKDAY = {
    "monday": 0, "tuesday": 1, "wednesday": 2,
    "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6,
}


def extract_due_date(text: str) -> tuple[Optional[str], Optional[str]]:
    """Extract a due date from natural language text.

    Returns (iso_date_string_or_none, source_phrase_or_none).
    """
    text_lower = text.lower()
    now = datetime.now(timezone.utc)

    # Check for explicit dates: "March 25", "3/25", "2026-03-25"
    # ISO format
    iso_match = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", text)
    if iso_match:
        return iso_match.group(1), iso_match.group(0)

    # "Month Day" format
    month_day = re.search(
        r"\b(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
        r"jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)"
        r"\s+(\d{1,2})(?:st|nd|rd|th)?\b",
        text_lower,
    )
    if month_day:
        month_str = month_day.group(1)[:3]
        day = int(month_day.group(2))
        month_map = {
            "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
            "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
        }
        month = month_map.get(month_str, 1)
        year = now.year
        try:
            due = datetime(year, month, day, tzinfo=timezone.utc)
            if due < now:
                due = due.replace(year=year + 1)
            return due.strftime("%Y-%m-%d"), month_day.group(0)
        except ValueError:
            pass

    # "by Friday", "by next week", etc.
    by_match = re.search(r"\bby\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b", text_lower)
    if by_match:
        target_day_name = by_match.group(1)
        target_weekday = _DAY_NAME_TO_WEEKDAY[target_day_name]
        current_weekday = now.weekday()
        days_ahead = (target_weekday - current_weekday) % 7
        if days_ahead == 0:
            days_ahead = 7  # "by Friday" means next Friday if today is Friday
        due = now + timedelta(days=days_ahead)
        return due.strftime("%Y-%m-%d"), by_match.group(0)

    # Relative date patterns
    for pattern, days_offset in _DATE_PATTERNS:
        m = re.search(pattern, text_lower)
        if m:
            if days_offset == -1:
                # Dynamic weekday computation
                for day_name, weekday_num in _DAY_NAME_TO_WEEKDAY.items():
                    if day_name in m.group(0):
                        current_weekday = now.weekday()
                        days_ahead = (weekday_num - current_weekday) % 7
                        if days_ahead == 0:
                            days_ahead = 7
                        # "next" adds another week
                        if "next" in m.group(0):
                            days_ahead += 7
                        due = now + timedelta(days=days_ahead)
                        return due.strftime("%Y-%m-%d"), m.group(0)
                        break
            else:
                due = now + timedelta(days=days_offset)
                return due.strftime("%Y-%m-%d"), m.group(0)

    return None, None


# ---------------------------------------------------------------------------
# Core extraction function
# ---------------------------------------------------------------------------

# Skip list: generic phrases that look like commitments but are not actionable
_SKIP_PHRASES = {
    "let's catch up sometime",
    "let's catch up soon",
    "we should do something together",
    "let's stay in touch",
    "let's keep in touch",
    "i'll keep you posted",  # too vague
}


def _extract_context_around(text: str, match: re.Match[str], chars: int = 120) -> str:
    """Extract surrounding context around a regex match."""
    start = max(0, match.start() - 40)
    end = min(len(text), match.end() + chars)
    snippet = text[start:end].strip()
    # Clean up to sentence boundaries if possible
    if start > 0:
        snippet = "..." + snippet
    if end < len(text):
        snippet = snippet + "..."
    return snippet


def extract_obligations(
    text: str,
    sender_email: str,
    sender_name: str = "",
    subject: str = "",
    surface: str = "email",
) -> list[dict[str, Any]]:
    """Extract obligation signals from email text.

    Determines direction (I_OWE_THEM vs THEY_OWE_ME) based on whether
    the sender is Aakash (I_OWE patterns) or someone else (THEY_OWE patterns).

    Returns list of obligation dicts ready for DB insertion:
        {
            "obligation_type": "I_OWE_THEM" | "THEY_OWE_ME",
            "category": str,
            "description": str,
            "source_quote": str,
            "confidence": float,
            "detection_method": "explicit",
            "due_date": str | None,
            "due_date_source": str | None,
            "person_email": str,
            "person_name": str,
            "surface": str,
        }
    """
    if not text or len(text.strip()) < 10:
        return []

    # Normalize whitespace
    text_clean = re.sub(r"\s+", " ", text)
    text_lower = text_clean.lower()

    # Skip vague pleasantries
    for skip in _SKIP_PHRASES:
        if skip in text_lower:
            text_lower = text_lower.replace(skip, "")

    # Determine email direction
    sender_is_aakash = sender_email.lower() in AAKASH_EMAILS
    obligations: list[dict[str, Any]] = []
    seen_quotes: set[str] = set()  # dedup within same email

    # --- I_OWE_THEM: First-person commitments ---
    if sender_is_aakash:
        # When Aakash is the sender, first-person = I_OWE_THEM
        for pat_info in _I_OWE_PATTERNS:
            for match in re.finditer(pat_info["pattern"], text_clean, re.IGNORECASE):
                quote = _extract_context_around(text_clean, match)
                quote_key = quote[:60].lower()
                if quote_key in seen_quotes:
                    continue
                seen_quotes.add(quote_key)

                if pat_info["confidence"] < 0.7:
                    continue

                due_date, due_source = extract_due_date(quote)

                obligations.append({
                    "obligation_type": "I_OWE_THEM",
                    "category": pat_info["category"],
                    "description": _build_description(
                        "I_OWE_THEM", pat_info["category"], quote, subject
                    ),
                    "source_quote": quote,
                    "confidence": pat_info["confidence"],
                    "detection_method": "explicit",
                    "due_date": due_date,
                    "due_date_source": due_source,
                    "person_email": "",  # recipients are the owed parties
                    "person_name": "",
                    "surface": surface,
                })
    else:
        # When someone else is the sender, their first-person = THEY_OWE_ME
        for pat_info in _THEY_OWE_PATTERNS:
            for match in re.finditer(pat_info["pattern"], text_clean, re.IGNORECASE):
                quote = _extract_context_around(text_clean, match)
                quote_key = quote[:60].lower()
                if quote_key in seen_quotes:
                    continue
                seen_quotes.add(quote_key)

                if pat_info["confidence"] < 0.7:
                    continue

                due_date, due_source = extract_due_date(quote)

                obligations.append({
                    "obligation_type": "THEY_OWE_ME",
                    "category": pat_info["category"],
                    "description": _build_description(
                        "THEY_OWE_ME", pat_info["category"], quote, subject,
                        person_name=sender_name,
                    ),
                    "source_quote": quote,
                    "confidence": pat_info["confidence"],
                    "detection_method": "explicit",
                    "due_date": due_date,
                    "due_date_source": due_source,
                    "person_email": sender_email,
                    "person_name": sender_name,
                    "surface": surface,
                })

    # --- REQUEST patterns (only when Aakash is the sender) ---
    # These are things Aakash asked for -> THEY_OWE_ME
    if sender_is_aakash:
        for pat_info in _REQUEST_PATTERNS:
            for match in re.finditer(pat_info["pattern"], text_clean, re.IGNORECASE):
                quote = _extract_context_around(text_clean, match)
                quote_key = quote[:60].lower()
                if quote_key in seen_quotes:
                    continue
                seen_quotes.add(quote_key)

                if pat_info["confidence"] < 0.7:
                    continue

                due_date, due_source = extract_due_date(quote)

                obligations.append({
                    "obligation_type": "THEY_OWE_ME",
                    "category": pat_info["category"],
                    "description": _build_description(
                        "THEY_OWE_ME", pat_info["category"], quote, subject
                    ),
                    "source_quote": quote,
                    "confidence": pat_info["confidence"],
                    "detection_method": "explicit",
                    "due_date": due_date,
                    "due_date_source": due_source,
                    "person_email": "",  # recipients owe this
                    "person_name": "",
                    "surface": surface,
                })

    return obligations


def _build_description(
    obligation_type: str,
    category: str,
    source_quote: str,
    subject: str,
    person_name: str = "",
) -> str:
    """Build a concise, action-oriented description from the detected pattern."""
    # Extract the actionable phrase from the source quote
    quote_clean = source_quote.strip("... ")
    # Truncate to a reasonable length
    if len(quote_clean) > 100:
        quote_clean = quote_clean[:100].rsplit(" ", 1)[0] + "..."

    if obligation_type == "I_OWE_THEM":
        prefix = "Aakash to"
    else:
        prefix = f"{person_name or 'They'} to"

    category_verbs = {
        "send_document": "send",
        "reply": "reply/respond",
        "schedule": "schedule",
        "follow_up": "follow up",
        "introduce": "make introduction",
        "review": "review",
        "deliver": "deliver",
        "connect": "connect",
        "provide_info": "provide info",
        "other": "complete",
    }
    verb = category_verbs.get(category, category)

    return f"{prefix} {verb} — re: {subject}" if subject else f"{prefix} {verb}"
