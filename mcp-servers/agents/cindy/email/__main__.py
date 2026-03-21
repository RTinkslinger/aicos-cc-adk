"""
CLI entry point for: python3 -m cindy.email

Delegates to email_processor.main() which handles argument parsing.
"""

from cindy.email.email_processor import main

main()
