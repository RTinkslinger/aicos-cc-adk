"""Stealth — persona management, anti-detection configuration.

Key principle: coherence > randomization.
A stable persona (consistent IP + timezone + locale + UA) beats
rotating everything randomly. Inconsistency is the detection signal.
"""

PERSONAS = {
    "linux_us": {
        "user_agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36"
        ),
        "viewport": {"width": 1920, "height": 1080},
        "locale": "en-US",
        "timezone_id": "America/New_York",
    },
    "mac_us": {
        "user_agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36"
        ),
        "viewport": {"width": 1440, "height": 900},
        "locale": "en-US",
        "timezone_id": "America/Los_Angeles",
    },
    "win_us": {
        "user_agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36"
        ),
        "viewport": {"width": 1920, "height": 1080},
        "locale": "en-US",
        "timezone_id": "America/Chicago",
    },
}

# Default persona for our droplet (Linux, US datacenter)
DEFAULT_PERSONA = "linux_us"


def get_persona(name: str = DEFAULT_PERSONA) -> dict:
    """Get a coherent persona profile."""
    return PERSONAS.get(name, PERSONAS[DEFAULT_PERSONA])
