# Cindy — AI CoS Communications Observer
# Thin fetchers stage raw data in interaction_staging.
# Datum Agent resolves people and writes clean data to interactions.
# Cindy Agent reasons about obligations and signals via LLM.
#
# Fetchers (plumbing only):
#   cindy.email.fetcher    — AgentMail API -> interaction_staging
#   cindy.granola.fetcher  — Granola MCP JSON -> interaction_staging
#   cindy.whatsapp.extractor — ChatStorage.sqlite -> interaction_staging
#   cindy.calendar.fetcher — .ics files -> interaction_staging
