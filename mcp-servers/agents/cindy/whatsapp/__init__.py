# Cindy WhatsApp Extraction (runs on Mac, not droplet)
# Reads ChatStorage.sqlite from iCloud backup, extracts conversations,
# resolves participants, and writes structured summaries to Postgres.
# Raw message text is NEVER stored — privacy-critical constraint.
