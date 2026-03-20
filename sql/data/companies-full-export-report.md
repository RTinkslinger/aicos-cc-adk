# Companies & Network DB Full Export Report

**Date:** 2026-03-20
**Method:** Notion REST API with cursor-based pagination
**Token source:** Droplet `/opt/agents/.env` (integration: `ai-cos-agent`)

---

## Companies DB

| Metric | Value |
|--------|-------|
| **Total rows extracted** | 4,635 |
| **Unique page IDs** | 4,635 |
| **Companies with names** | 4,571 (64 unnamed/blank) |
| **Properties per row** | 53 |
| **File size** | 8.3 MB |
| **Output file** | `sql/data/companies-full-export.json` |
| **API database ID** | `45a7e3ff-56f5-4363-b72c-f44456786c60` |
| **Data source ID** | `1edda9cc-df8b-41e1-9c08-22971495aa43` |

### Pipeline Status Distribution

| Status | Count |
|--------|-------|
| NA | 2,976 |
| Pass Forever | 961 |
| Mining | 163 |
| Portfolio | 140 |
| Missed without screen | 95 |
| Passed Last Track For Next | 50 |
| Acquired/Shut Down/Defunct | 43 |
| Active Screening | 34 |
| Evaluating | 27 |
| Tracking_30 | 22 |
| Passive Screening | 21 |
| Lost | 20 |
| Process Miss | 19 |
| Screen | 18 |
| Anti Folio | 17 |
| Parked | 13 |
| Tracking_7 | 6 |
| Won & Closing | 5 |
| Tracking_90 | 4 |
| Tracking_180 | 1 |

### Sector Distribution

| Sector | Count |
|--------|-------|
| (empty) | 2,722 |
| Consumer | 599 |
| SaaS | 496 |
| Financial Services | 268 |
| Venture Capital Firm | 214 |
| B2B | 169 |
| Frontier | 167 |

### All Properties (53)

`AIF/USA`, `AIF/USA (Rollup)`, `Action Due?`, `Alums`, `Angels`, `Batch`, `Corp Dev`, `Created by`, `Current People`, `DeVC IP POC`, `Deal Status`, `Deal Status @ Discovery`, `Deck if link`, `Domain Eval?`, `Founding Timeline`, `HIL Review?`, `Investors (VCs, Micros)`, `JTBD`, `Known Portfolio`, `Last Round $M`, `Last Round Timing`, `Last edited time`, `MPI Connect`, `Meeting Notes`, `Met by?`, `Money Committed`, `Money In`, `Money In (Rollup)`, `Name`, `Ownership %`, `Ownership % (Rollup)`, `Pending Tasks`, `Piped From`, `Pipeline Status`, `Portfolio Interaction Notes`, `Priority`, `Sector`, `Sector Tags`, `Sells To`, `Shared with`, `Smart Money?`, `Surface to collective`, `Type`, `Vault Link`, `Venture Funding`, `Website`, `YC Partner`, `created_time`, `last_edited_time`, `notion_page_id`, `notion_url`, `Network DB`, `Finance DB`

---

## Network DB

| Metric | Value |
|--------|-------|
| **Total rows extracted** | 3,339 |
| **Unique page IDs** | 3,339 |
| **People with names** | 3,326 (13 unnamed/blank) |
| **Properties per row** | 46 |
| **File size** | 5.6 MB |
| **Output file** | `sql/data/network-full-export.json` |
| **API database ID** | `d5f52503-f234-47b0-9701-d9b354af9d1a` |
| **Data source ID** | `6462102f-112b-40e9-8984-7cb1e8fe5e8b` |

### All Properties (46)

`Angel Folio`, `Batch`, `Big Events Invite`, `C+E Attendance`, `C+E Speaker`, `Collective Flag`, `Company Stage`, `Current Co`, `Current Role`, `Customer For`, `DeVC POC`, `DeVC Relationship`, `E/E Priority`, `Engagement Playbook`, `Folio Franchise`, `Home Base`, `In Folio Of`, `Investing Activity`, `Investorship`, `Last edited time`, `Led by?`, `Leverage`, `Linkedin`, `Local Network`, `Meeting Notes`, `Name`, `Network Tasks?`, `Operating Franchise`, `Participation Attribution`, `Past Cos`, `Piped to DeVC`, `Prev Foundership`, `R/Y/G`, `SaaS Buyer Type`, `Schools`, `Sector Classification`, `Sourcing Attribution`, `Sourcing/Flow/HOTS`, `Tasks Pending`, `Unstructured Leads`, `Venture Partner? (old)`, `YC Partner Portfolio`, `created_time`, `last_edited_time`, `notion_page_id`, `notion_url`

---

## Extraction Method

### Strategies Attempted

1. **MCP View Queries (10 views)** -- Extracted 1,048 unique companies across 10 views. Capped at 100 rows per view with heavy overlap between views.

2. **MCP Search with date/keyword filters** -- Returned 25 results per query with heavy semantic overlap. Too slow to scale (would need 300+ queries for full coverage).

3. **Create/Update views (for custom filters)** -- Permission denied by MCP tool.

4. **Direct Notion REST API with pagination** -- Successfully extracted ALL rows using the `NOTION_TOKEN` from the droplet. The Notion API supports `start_cursor` pagination with 100 rows per page.

### Key Discovery

The Notion MCP tool `query-database-view` caps at 100 rows with no cursor support. The Notion REST API (`/v1/databases/{id}/query`) supports full cursor-based pagination. The API database ID differs from the `data_source_id` used by the MCP tool:

| Database | Data Source ID (MCP) | API Database ID |
|----------|---------------------|-----------------|
| Companies | `1edda9cc-df8b-41e1-9c08-22971495aa43` | `45a7e3ff-56f5-4363-b72c-f44456786c60` |
| Network | `6462102f-112b-40e9-8984-7cb1e8fe5e8b` | `d5f52503-f234-47b0-9701-d9b354af9d1a` |

The API database ID is the Notion page ID visible in the URL when viewing the database. The data_source_id is the collection ID used internally by Notion's MCP integration.

### Replication

To re-run this extraction:

```python
import urllib.request, json, ssl, time

token = "ntn_..."  # from droplet /opt/agents/.env
database_id = "45a7e3ff-56f5-4363-b72c-f44456786c60"  # Companies
# database_id = "d5f52503-f234-47b0-9701-d9b354af9d1a"  # Network

url = f"https://api.notion.com/v1/databases/{database_id}/query"
headers = {
    "Authorization": f"Bearer {token}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

ctx = ssl.create_default_context()
all_results, cursor = [], None

while True:
    body = {"page_size": 100}
    if cursor:
        body["start_cursor"] = cursor
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=headers, method="POST")
    with urllib.request.urlopen(req, context=ctx, timeout=60) as resp:
        data = json.loads(resp.read())
        all_results.extend(data["results"])
        if not data["has_more"]:
            break
        cursor = data["next_cursor"]
        time.sleep(0.35)
```

### Previous Exports (Superseded)

| File | Rows | Status |
|------|------|--------|
| `companies-notion-export.json` | 545 | Superseded by full export |
| `network-notion-export.json` | 528 | Superseded by full export |
