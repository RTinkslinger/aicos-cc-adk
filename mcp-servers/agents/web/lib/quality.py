"""Content quality validation — reject garbage before returning results."""

import logging

logger = logging.getLogger("web-agent")


def validate_content(content: str, url: str = "", expected_type: str = "") -> dict:
    """Score content quality. Returns score (0-100), issues, and verdict.

    Checks: length, structure, login walls, cookie banners, error pages.
    """
    issues: list[str] = []
    score = 100

    if not content or not content.strip():
        return {"score": 0, "verdict": "empty", "issues": ["No content extracted"]}

    text = content.strip()
    text_lower = text.lower()
    word_count = len(text.split())

    # Length check
    if word_count < 10:
        score -= 60
        issues.append(f"Very short: {word_count} words")
    elif word_count < 50:
        score -= 30
        issues.append(f"Short: {word_count} words")

    # Login wall detection
    login_signals = [
        "sign in",
        "log in",
        "create account",
        "forgot password",
        "enter your email",
        "enter your password",
    ]
    login_count = sum(1 for s in login_signals if s in text_lower)
    if login_count >= 2 and word_count < 200:
        score -= 50
        issues.append(f"Likely login wall ({login_count} login signals)")

    # Cookie/consent overlay detection
    consent_signals = [
        "accept cookies",
        "cookie policy",
        "we use cookies",
        "privacy preferences",
        "consent",
    ]
    consent_count = sum(1 for s in consent_signals if s in text_lower)
    if consent_count >= 2 and word_count < 100:
        score -= 40
        issues.append("Likely cookie consent overlay")

    # Error page detection
    error_signals = [
        "404",
        "page not found",
        "error occurred",
        "access denied",
        "403 forbidden",
    ]
    if any(s in text_lower for s in error_signals) and word_count < 100:
        score -= 30
        issues.append("Possible error page")

    # Structural quality (has headings, paragraphs, etc.)
    if "\n" not in text and word_count > 100:
        score -= 10
        issues.append("No line breaks — may be poorly structured")

    score = max(0, min(100, score))
    verdict = "good" if score >= 70 else "acceptable" if score >= 40 else "poor"

    return {
        "score": score,
        "verdict": verdict,
        "word_count": word_count,
        "issues": issues,
    }
