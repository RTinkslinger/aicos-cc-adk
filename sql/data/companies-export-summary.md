# Companies DB - Notion Export Summary

**Export Date:** 2026-03-20 02:18
**Total Rows:** 545
**Named Companies:** 538
**Empty Name Rows:** 7
**Total Fields:** 44
**Data File:** `companies-notion-export.json` (860,950 bytes)

## Extraction Method
- Queried 10 database views from the Companies DB (`1edda9cc-df8b-41e1-9c08-22971495aa43`)
- Each view returns max 100 rows (Notion MCP limitation)
- Different views have different sort orders, yielding different row subsets
- Rows merged by `url` (Notion page URL) as dedup key
- Field values merged across views: non-empty values preferred
- **Note:** `has_more=true` on several views means the DB likely contains more than 545 rows. The Notion MCP `query-database-view` tool does not support pagination.

## Column Coverage

| Field | Populated | Total | % |
|-------|-----------|-------|---|
| `action_due` | 197 | 545 | 36% (MED) |
| `alums` | 78 | 545 | 14% (LOW) |
| `angels` | 108 | 545 | 20% (LOW) |
| `batch` | 74 | 545 | 14% (LOW) |
| `corp_dev` | 2 | 545 | 0% (LOW) |
| `current_people` | 376 | 545 | 69% (MED) |
| `deal_status` | 545 | 545 | 100% (HIGH) |
| `deal_status_at_discovery` | 545 | 545 | 100% (HIGH) |
| `deck_link` | 40 | 545 | 7% (LOW) |
| `devc_ip_poc` | 234 | 545 | 43% (MED) |
| `domain_eval` | 0 | 545 | 0% (LOW) |
| `finance_db` | 34 | 545 | 6% (LOW) |
| `founding_timeline` | 124 | 545 | 23% (LOW) |
| `hil_review` | 0 | 545 | 0% (LOW) |
| `investors_vcs_micros` | 178 | 545 | 33% (MED) |
| `jtbd` | 169 | 545 | 31% (MED) |
| `known_portfolio` | 58 | 545 | 11% (LOW) |
| `last_edited_time` | 545 | 545 | 100% (HIGH) |
| `last_round_m` | 95 | 545 | 17% (LOW) |
| `last_round_timing` | 107 | 545 | 20% (LOW) |
| `meeting_notes` | 1 | 545 | 0% (LOW) |
| `met_by` | 24 | 545 | 4% (LOW) |
| `money_committed` | 21 | 545 | 4% (LOW) |
| `mpi_connect` | 2 | 545 | 0% (LOW) |
| `name` | 538 | 545 | 99% (HIGH) |
| `network_db` | 28 | 545 | 5% (LOW) |
| `notion_page_id` | 545 | 545 | 100% (HIGH) |
| `notion_url` | 545 | 545 | 100% (HIGH) |
| `pending_tasks` | 84 | 545 | 15% (LOW) |
| `piped_from` | 291 | 545 | 53% (MED) |
| `pipeline_status` | 545 | 545 | 100% (HIGH) |
| `portfolio_interaction_notes` | 107 | 545 | 20% (LOW) |
| `priority` | 248 | 545 | 46% (MED) |
| `sector` | 412 | 545 | 76% (HIGH) |
| `sector_tags` | 292 | 545 | 54% (MED) |
| `sells_to` | 123 | 545 | 23% (LOW) |
| `shared_with` | 50 | 545 | 9% (LOW) |
| `smart_money` | 0 | 545 | 0% (LOW) |
| `surface_to_collective` | 4 | 545 | 1% (LOW) |
| `type` | 100 | 545 | 18% (LOW) |
| `vault_link` | 56 | 545 | 10% (LOW) |
| `venture_funding` | 98 | 545 | 18% (LOW) |
| `website` | 44 | 545 | 8% (LOW) |
| `yc_partner` | 42 | 545 | 8% (LOW) |

## Pipeline Status Distribution

| Status | Count |
|--------|-------|
| NA | 213 |
| Portfolio | 107 |
| Pass Forever | 59 |
| Mining | 36 |
| Acquired/Shut Down/Defunct | 32 |
| Evaluating | 17 |
| Passed Last Track For Next | 12 |
| Lost | 10 |
| Tracking_30 | 10 |
| Missed without screen | 8 |
| Active Screening | 7 |
| Screen | 7 |
| Anti Folio | 6 |
| Process Miss | 5 |
| Won & Closing | 5 |
| Passive Screening | 4 |
| Parked | 3 |
| Tracking_90 | 2 |
| Tracking_7 | 2 |

## Priority Distribution

| Priority | Count |
|----------|-------|
| (empty) | 297 |
| P0🔥 | 137 |
| P1 | 69 |
| P2 | 42 |

## Sector Distribution (Top 15)

| Sector | Count |
|--------|-------|
| (empty) | 133 |
| Venture Capital Firm | 101 |
| Consumer 🧑 | 96 |
| SaaS 💻 | 96 |
| Financial Services 🏦 | 63 |
| Frontier 🚀 | 36 |
| B2B 🏢 | 20 |

## Sample Rows (3 Most Populated)

### Sample 1: OnFinance AI
```json
{
  "notion_page_id": "d53c8a3c-d70d-479e-b7f4-d31a37b9dc1d",
  "notion_url": "https://www.notion.so/d53c8a3cd70d479eb7f4d31a37b9dc1d",
  "name": "OnFinance AI",
  "deal_status": "NA",
  "deal_status_at_discovery": "NA",
  "pipeline_status": "Pass Forever",
  "priority": "P0🔥",
  "sector": "Financial Services 🏦",
  "venture_funding": "Seed",
  "founding_timeline": "",
  "last_round_timing": "H2 2023",
  "batch": "",
  "type": "SMB",
  "piped_from": "[\"https://www.notion.so/d8c847d550144163b3df9b180f7dd5e3\"]",
  "sector_tags": [
    "AI",
    "Compliance"
  ],
  "sells_to": [
    "Enterprise",
    "Mid Market"
  ],
  "last_round_m": 1.1,
  "money_committed": 200000.0,
  "website": "",
  "vault_link": "https://matrixindia.sharepoint.com/sites/TheVault/Shared%20Documents/Forms/AllItems.aspx?FolderCTID=0x01200086EDF952FD49E241A70AF470BB78292F&id=%2Fsites%2FTheVault%2FShared%20Documents%2FDeVC%2FSourcing%2C%20Eval%20%26%20Strategy%2FSourcing%2FLeads%2F1%2E%20Financial%20Services%2FOnFinance&viewid=888bb05a%2D6d3d%2D44e9%2D8bfa%2D78171a357754",
  "deck_link": "",
  "action_due": "2025-05-05",
  "surface_to_collective": "",
  "domain_eval": null,
  "hil_review": null,
  "smart_money": null,
  "angels": [
    "52aaa09b-ae8c-4f00-b2c7-1253d9462e87",
    "26c29bcc-b6fc-80d5-b8da-da68d162ef4e"
  ],
  "alums": [],
  "current_people": [
    "7a9864c9-2acd-416d-b92d-430928726007",
    "12829bcc-b6fc-80ec-87fe-c035751cab6e"
  ],
  "investors_vcs_micros": [
    "17429bcc-b6fc-8083-a8e5-c7e8ef7e7b05"
  ],
  "pending_tasks": [
    "1ca29bcc-b6fc-803d-9c70-c5dc7f5e62c7",
    "1e329bcc-b6fc-804e-910d-f9823030c5ae",
    "1e429bcc-b6fc-8086-8771-d4e9d6edfcfa",
    "1e429bcc-b6fc-8064-8072-c1e2a80dfacc",
    "1ea29bcc-b6fc-80b4-bb47-d4a9b1a513c5"
  ],
  "portfolio_interaction_notes": [],
  "finance_db": [
    "28729bcc-b6fc-81ee-8b59-e947a125f705"
  ],
  "network_db": [],
  "meeting_notes": [],
  "known_portfolio": [],
  "corp_dev": [],
  "mpi_connect": [],
  "devc_ip_poc": [
    "user://3a14f1fb-d1e4-47ea-805d-edeca3193186",
    "user://5bdd202e-47f0-4c71-800e-9538efabefff"
  ],
  "met_by": [
    "https://www.notion.so/59f7e10b1edd491f9c6ba7b7aea62a58"
  ],
  "shared_with": [
    "https://www.notion.so/720d53fc0db64339acaf41738e0e398c",
    "https://www.notion.so/14729bccb6fc8052aacfff612db7b2c5"
  ],
  "jtbd": "[\"1PE Done\",\"2PE Done\",\"MPE Done\",\"BRCs Done\",\"DE Done\"]",
  "yc_partner": "",
  "last_edited_time": "2026-02-19T13:26:31.138Z"
}
```

### Sample 2: Mello
```json
{
  "notion_page_id": "23829bcc-b6fc-81f0-ad62-ecd94d5b6540",
  "notion_url": "https://www.notion.so/23829bccb6fc81f0ad62ecd94d5b6540",
  "name": "Mello",
  "deal_status": "NA",
  "deal_status_at_discovery": "NA",
  "pipeline_status": "Portfolio",
  "priority": "P0🔥",
  "sector": "Consumer 🧑",
  "venture_funding": "Raising",
  "founding_timeline": "H1 2023",
  "last_round_timing": "H2 2025",
  "batch": "",
  "type": "SMB",
  "piped_from": "[\"https://www.notion.so/9e07d2f9876340c182344e5d3bf06561\"]",
  "sector_tags": [
    "AI",
    "Companionship 🤗"
  ],
  "sells_to": [
    "Consumers"
  ],
  "last_round_m": 2.5,
  "money_committed": 100000.0,
  "website": "",
  "vault_link": "",
  "deck_link": "https://mpidevc.sharepoint.com/:b:/s/PitchDecksAutomated/EcyhRK88ZM5Og2oMew7BeUwBzBPIJJ-GEk7PwWlOj_QfgA",
  "action_due": "2025-07-30",
  "surface_to_collective": "",
  "domain_eval": null,
  "hil_review": null,
  "smart_money": null,
  "angels": [],
  "alums": [],
  "current_people": [
    "23829bcc-b6fc-8047-9257-e4f0bde0966c",
    "23829bcc-b6fc-8066-af9b-e20a0b8e1d43"
  ],
  "investors_vcs_micros": [
    "dbee2c0d-cb4f-4c72-a87d-aa6dcbb1abc2"
  ],
  "pending_tasks": [],
  "portfolio_interaction_notes": [
    "2b929bcc-b6fc-81d1-962f-f89e713d12d1"
  ],
  "finance_db": [
    "26929bcc-b6fc-8196-8bb2-d4bb5c900fab"
  ],
  "network_db": [],
  "meeting_notes": [],
  "known_portfolio": [],
  "corp_dev": [],
  "mpi_connect": [],
  "devc_ip_poc": [
    "user://3a14f1fb-d1e4-47ea-805d-edeca3193186",
    "user://5bdd202e-47f0-4c71-800e-9538efabefff"
  ],
  "met_by": [],
  "shared_with": [
    "https://www.notion.so/03e8eef06eda409f9a3a2cb4afcce408",
    "https://www.notion.so/60a061e23f9f4862a6fa94f92a0a1c74"
  ],
  "jtbd": "[\"2PE Pending\",\"MPE Pending\",\"BRCs Pending\",\"1PE Done\"]",
  "yc_partner": "",
  "last_edited_time": "2025-11-29T10:33:53.052Z"
}
```

### Sample 3: AeroDome Technologies Private Limited
```json
{
  "notion_page_id": "1e929bcc-b6fc-81e6-88fd-cd56a3b2366f",
  "notion_url": "https://www.notion.so/1e929bccb6fc81e688fdcd56a3b2366f",
  "name": "AeroDome Technologies Private Limited",
  "deal_status": "NA",
  "deal_status_at_discovery": "NA",
  "pipeline_status": "Portfolio",
  "priority": "P0🔥",
  "sector": "Frontier 🚀",
  "venture_funding": "Raising",
  "founding_timeline": "H1 2023",
  "last_round_timing": "H1 2025",
  "batch": "",
  "type": "",
  "piped_from": "[\"https://www.notion.so/9e07d2f9876340c182344e5d3bf06561\"]",
  "sector_tags": [
    "Aerospace"
  ],
  "sells_to": [],
  "last_round_m": null,
  "money_committed": 50000.0,
  "website": "",
  "vault_link": "",
  "deck_link": "https://mpidevc.sharepoint.com/:b:/s/PitchDecksAutomated/ERJiU5nYAtdPnlIOuEBn1rsB5860Mr27wL3DVxGmgVnetQ",
  "action_due": "2025-05-12",
  "surface_to_collective": "",
  "domain_eval": null,
  "hil_review": null,
  "smart_money": null,
  "angels": [
    "5d79d566-bd22-4d24-952b-7304895ca242",
    "02be8c39-cf7a-42ea-9e37-6f1db5a25f5b"
  ],
  "alums": [
    "1ec29bcc-b6fc-810a-8870-e1bf3c9a1a33",
    "32629bcc-b6fc-81fa-8c7e-e478426708b7"
  ],
  "current_people": [
    "1e929bcc-b6fc-81c4-bcc2-dc24bbbddc8d",
    "1ec29bcc-b6fc-80f5-b0d9-e9c0d7af3f6b",
    "1ec29bcc-b6fc-804a-bc8f-e7310513e0c0"
  ],
  "investors_vcs_micros": [
    "9300849f-f862-4c83-a193-b08ba3d34fdb"
  ],
  "pending_tasks": [
    "1ea29bcc-b6fc-800d-ba67-f4f01747e368"
  ],
  "portfolio_interaction_notes": [
    "1f729bcc-b6fc-80d5-b059-fba772be8357"
  ],
  "finance_db": [
    "26929bcc-b6fc-81e0-8425-dfddc9ed822d"
  ],
  "network_db": [],
  "meeting_notes": [],
  "known_portfolio": [],
  "corp_dev": [],
  "mpi_connect": [],
  "devc_ip_poc": [
    "user://88cda0ab-5ec0-4093-8956-704b568f2e21"
  ],
  "met_by": [],
  "shared_with": [],
  "jtbd": "[\"MPE Pending\",\"BRCs Pending\",\"1PE Done\",\"2PE Done\"]",
  "yc_partner": "",
  "last_edited_time": "2025-12-03T10:00:03.399Z"
}
```

## Data Quality Issues

1. **7 rows with empty names** - Notion pages with no title set
2. **Formula fields skipped** - `AIF/USA`, `Ownership %`, `Money In` are formulas; their values appear as `formulaResult://` references, not computed values
3. **Rollup fields skipped** - `AIF/USA (Rollup)`, `Ownership % (Rollup)`, `Money In (Rollup)` appear as `<omitted />`
4. **Pagination gap** - Several views had `has_more=true` at 100 rows. Total DB size is likely larger than 545.
5. **`domain_eval`, `hil_review`, `smart_money`** checkbox fields are 0% populated (always false/empty)
6. **`meeting_notes`, `corp_dev`, `mpi_connect`** relation fields are nearly empty (<1%)
7. **Some `date:*:is_datetime` fields** exist as integer 0/1 markers alongside actual date values
8. **Emoji in field values** - Priority uses emoji markers (P0🔥), Sector uses emoji (Consumer 🧑), etc.
