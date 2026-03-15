"""Cookie management — status check, domain listing."""

import time
from pathlib import Path

COOKIE_DIR = "/opt/ai-cos/cookies"


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
