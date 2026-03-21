"""
CLI entry point for: python3 -m cindy.email

Delegates to fetcher.main() — stages raw email data only.
"""

from cindy.email.fetcher import main

main()
