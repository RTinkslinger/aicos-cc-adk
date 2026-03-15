"""Session management — cookie management + storageState persistence.

Merges cookie status/freshness checking (from web-agent cookies.py) with
storageState management for full browser session persistence.

Cookie functions: status check, domain listing, freshness validation.
StorageState functions: save/load/validate Playwright storageState JSON blobs
  (cookies + localStorage + sessionStorage) keyed by domain.
"""

import json
import logging
import time
from pathlib import Path

logger = logging.getLogger("web-agent")

COOKIE_DIR = "/opt/ai-cos/cookies"
STORAGE_STATE_DIR = "/opt/ai-cos/storage-states"


# ---------------------------------------------------------------------------
# Cookie management (from web-agent/lib/cookies.py)
# ---------------------------------------------------------------------------


def cookie_status(cookie_dir: str = COOKIE_DIR) -> dict:
    """Check which domain cookies are available and their freshness."""
    cookie_path = Path(cookie_dir)
    if not cookie_path.exists():
        return {
            "cookies": [],
            "cookie_dir": cookie_dir,
            "error": "Cookie directory not found",
        }

    cookies = []
    for f in sorted(cookie_path.glob("*.txt")):
        age_days = (time.time() - f.stat().st_mtime) / 86400
        line_count = sum(
            1
            for line in f.read_text().splitlines()
            if line.strip() and not line.startswith("#")
        )
        entry: dict = {
            "domain": f.stem,
            "cookie_count": line_count,
            "age_days": round(age_days, 1),
            "file": str(f),
        }
        if age_days > 7:
            entry["warning"] = "STALE — re-run cookie-sync.sh"
        cookies.append(entry)

    return {"cookies": cookies, "cookie_dir": cookie_dir}


def is_cookie_fresh(domain: str, cookie_dir: str = COOKIE_DIR, max_age_days: float = 7.0) -> bool:
    """Return True if the cookie file for domain exists and is within max_age_days."""
    cookie_file = Path(cookie_dir) / f"{domain}.txt"
    if not cookie_file.exists():
        return False
    age_days = (time.time() - cookie_file.stat().st_mtime) / 86400
    return age_days <= max_age_days


def get_cookie_path(domain: str, cookie_dir: str = COOKIE_DIR) -> str | None:
    """Return the path to the cookie file for domain, or None if it doesn't exist."""
    cookie_file = Path(cookie_dir) / f"{domain}.txt"
    return str(cookie_file) if cookie_file.exists() else None


# ---------------------------------------------------------------------------
# StorageState management (new — Playwright session persistence)
# ---------------------------------------------------------------------------


def save_storage_state(domain: str, state_json: dict, storage_dir: str = STORAGE_STATE_DIR) -> None:
    """Persist a Playwright storageState dict to disk, keyed by domain.

    storageState contains cookies, localStorage, and sessionStorage — giving
    full session persistence across Playwright context restarts.

    Args:
        domain: Domain key (e.g. "linkedin.com", "twitter.com")
        state_json: Dict returned by Playwright's context.storage_state()
        storage_dir: Directory to store state files (default: STORAGE_STATE_DIR)
    """
    state_path = Path(storage_dir)
    state_path.mkdir(parents=True, exist_ok=True)
    state_file = state_path / f"{domain}.json"
    try:
        with open(state_file, "w", encoding="utf-8") as f:
            json.dump(state_json, f, indent=2, ensure_ascii=False)
        logger.info("Saved storageState for %s to %s", domain, state_file)
    except OSError as e:
        logger.warning("Failed to save storageState for %s: %s", domain, e)


def load_storage_state(domain: str, storage_dir: str = STORAGE_STATE_DIR) -> dict | None:
    """Load a persisted Playwright storageState dict for domain.

    Returns None if no state file exists for the domain.

    Args:
        domain: Domain key (e.g. "linkedin.com")
        storage_dir: Directory containing state files

    Returns:
        storageState dict suitable for Playwright's browser.new_context(storage_state=...)
        or None if not found.
    """
    state_file = Path(storage_dir) / f"{domain}.json"
    if not state_file.exists():
        return None
    try:
        with open(state_file, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Failed to load storageState for %s: %s", domain, e)
        return None


def check_storage_state_valid(
    domain: str,
    storage_dir: str = STORAGE_STATE_DIR,
    max_age_days: float = 7.0,
) -> bool:
    """Return True if a storageState file exists for domain and is within max_age_days.

    Does NOT validate that the session is actually authenticated — that requires
    a live browser check. This is a quick file-freshness gate only.

    Args:
        domain: Domain key (e.g. "linkedin.com")
        storage_dir: Directory containing state files
        max_age_days: Maximum acceptable age in days (default: 7)

    Returns:
        True if the state file exists and is fresh, False otherwise.
    """
    state_file = Path(storage_dir) / f"{domain}.json"
    if not state_file.exists():
        return False
    age_days = (time.time() - state_file.stat().st_mtime) / 86400
    return age_days <= max_age_days


def list_storage_states(storage_dir: str = STORAGE_STATE_DIR) -> list[dict]:
    """List all persisted storageState files with freshness info."""
    state_path = Path(storage_dir)
    if not state_path.exists():
        return []
    states = []
    for f in sorted(state_path.glob("*.json")):
        age_days = (time.time() - f.stat().st_mtime) / 86400
        entry: dict = {
            "domain": f.stem,
            "age_days": round(age_days, 1),
            "file": str(f),
            "fresh": age_days <= 7.0,
        }
        if age_days > 7:
            entry["warning"] = "STALE — session may be expired"
        states.append(entry)
    return states
