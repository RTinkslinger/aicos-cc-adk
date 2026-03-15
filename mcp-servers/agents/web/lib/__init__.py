"""Web agent library — public API surface."""

from .browser import browse, create_context, get_browser, shutdown_browser
from .extraction import DedupTracker, check_cookie_health, classify_relevance, extract_and_save, get_transcript, process_videos
from .fingerprint import fingerprint
from .monitor import get_watched_urls, register_watch
from .quality import validate_content
from .scrape import scrape
from .search import search
from .sessions import (
    check_storage_state_valid,
    cookie_status,
    get_cookie_path,
    is_cookie_fresh,
    list_storage_states,
    load_storage_state,
    save_storage_state,
)
from .stealth import get_persona
from .strategy import get_all_strategies, get_strategy, record_outcome, seed_strategies

__all__ = [
    # browser
    "browse",
    "create_context",
    "get_browser",
    "shutdown_browser",
    # scrape
    "scrape",
    # search
    "search",
    # fingerprint
    "fingerprint",
    # quality
    "validate_content",
    # strategy
    "get_strategy",
    "record_outcome",
    "seed_strategies",
    "get_all_strategies",
    # stealth
    "get_persona",
    # sessions
    "cookie_status",
    "is_cookie_fresh",
    "get_cookie_path",
    "save_storage_state",
    "load_storage_state",
    "check_storage_state_valid",
    "list_storage_states",
    # extraction
    "DedupTracker",
    "extract_and_save",
    "get_transcript",
    "classify_relevance",
    "check_cookie_health",
    "process_videos",
    # monitor
    "register_watch",
    "get_watched_urls",
]
