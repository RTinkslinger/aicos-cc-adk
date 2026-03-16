# Notion Patterns Skill

Instructions for interacting with the Notion API. Covers property formatting, tool selection, database IDs, rate limits, and common gotchas.

---

## Tool Selection

The Sync Agent uses python3 scripts with the Notion API (via the `notion-client` library or direct REST calls). This skill documents the patterns those scripts must follow.

For reference, the Notion MCP Enhanced Connector tools are:

| Tool | Use For |
|------|---------|
| `notion-fetch` | Read any page, database, or data source by URL/ID |
| `notion-search` | Semantic search across workspace |
| `notion-create-pages` | Create pages in a database (batch up to 100) |
| `notion-update-page` | Update properties or content |
| `notion-query-database-view` | Query using a database view's pre-configured filters |

### Decision Tree

```
READ a page?          -> notion-fetch (page ID or URL)
SEARCH workspace?     -> notion-search (semantic)
CREATE pages?         -> notion-create-pages (with parent data_source_id)
UPDATE properties?    -> notion-update-page (command: "update_properties")
UPDATE page content?  -> notion-update-page (command: "replace_content" or "insert_content_after")
BULK-READ database?   -> notion-query-database-view (with view://UUID)
```

### Bulk-Read Pattern (CRITICAL)

The ONLY reliable method for reading all rows from a database:

1. `notion-fetch` on the database ID -> find `<view url="view://UUID">` in response
2. `notion-query-database-view` with `view_url: "view://UUID"`

**Broken methods (NEVER use):**
- `API-query-data-source` -- Returns "Invalid request URL" for ALL data source endpoints
- `notion-fetch` on `collection://UUID` -- Returns schema only, NOT data rows
- `notion-query-database-view` with `https://` URLs -- Fails with "Invalid database view URL"

---

## Database IDs

| Database | Data Source ID | Collection URL |
|----------|---------------|----------------|
| **Thesis Tracker** | `3c8d1a34-e723-4fb1-be28-727777c22ec6` | `collection://3c8d1a34-e723-4fb1-be28-727777c22ec6` |
| **Content Digest** | `df2d73d6-e020-46e8-9a8a-7b9da48b6ee2` | `collection://df2d73d6-e020-46e8-9a8a-7b9da48b6ee2` |
| **Actions Queue** | `1df4858c-6629-4283-b31d-50c5e7ef885d` | `collection://1df4858c-6629-4283-b31d-50c5e7ef885d` |
| **Portfolio DB** | `4dba9b7f-e623-41a5-9cb7-2af5976280ee` | `collection://4dba9b7f-e623-41a5-9cb7-2af5976280ee` |
| **Network DB** | `6462102f-112b-40e9-8984-7cb1e8fe5e8b` | `collection://6462102f-112b-40e9-8984-7cb1e8fe5e8b` |
| **Companies DB** | `1edda9cc-df8b-41e1-9c08-22971495aa43` | `collection://1edda9cc-df8b-41e1-9c08-22971495aa43` |
| **Build Roadmap** | `6e1ffb7e-01f1-4295-a7ea-67d5c9216d8f` | `collection://6e1ffb7e-01f1-4295-a7ea-67d5c9216d8f` |
| **Tasks Tracker** | `1b829bcc-b6fc-80fc-9da8-000b4927455b` | -- |

**Known view URLs:**
- Build Roadmap: `view://4eb66bc1-322b-4522-bb14-253018066fef`

---

## Property Formatting

When creating or updating pages via the Notion API, properties must use specific formats.

### Title Properties
```json
{"Thread Name": "My Thesis Thread"}
```

### Text Properties
```json
{"Core Thesis": "The investment hypothesis text"}
```

### URL Properties
```json
{"Video URL": "https://youtube.com/watch?v=abc123"}
```

### Number Properties
Native integers or floats. NOT strings.
```json
{"Relevance Score": 8}
```
Wrong: `{"Relevance Score": "8"}`

### Select Properties
Exact option name (case-sensitive):
```json
{"Status": "Active"}
{"Conviction": "Evolving Fast"}
{"Priority": "P1 - This Week"}
```

### Multi-Select Properties
JSON arrays encoded as strings:
```json
{"Connected Buckets": "[\"New Cap Tables\", \"Thesis Evolution\"]"}
```

### Checkbox Properties
Special string values, NOT booleans:
```json
{"Is Active": "__YES__"}
{"Is Active": "__NO__"}
```
Wrong: `{"Is Active": true}`

### Date Properties (EXPANDED FORMAT -- mandatory)
Dates MUST be split into three expanded fields. You cannot use `"Due Date": "2026-03-15"`.

```json
{
  "date:Due Date:start": "2026-03-15",
  "date:Due Date:end": null,
  "date:Due Date:is_datetime": 0
}
```

- `start`: Required. ISO-8601 date or datetime.
- `end`: NULL for single dates. Present for date ranges.
- `is_datetime`: 0 for date-only, 1 for datetime.

### Relation Properties
JSON arrays of page URLs (not IDs):
```json
{"Company": "[\"https://www.notion.so/page-id-here\"]"}
```

To set a relation, you need the target page URL first. Query the related database to find it.

---

## Rate Limits

| Limit | Value | Strategy |
|-------|-------|----------|
| Rate limit | 3 requests/sec (2,700 per 15 min) | Space requests by at least 350ms |
| Pagination | Max 100 items per page | Use `nextPageToken` or `start_cursor` |
| Block append | Max 100 blocks per `children` array | Split into multiple appends |
| Rich text | Max 2,000 chars per text object | Break long text across multiple objects |
| Nesting depth | 2 levels max | Flatten deeper structures |
| Payload size | 500 KB | Split large batch operations |
| Page creation | Up to 100 pages per call | Batch efficiently |

### Rate Limit Handling

```python
import time

def notion_request_with_backoff(func, *args, max_retries=3):
    for attempt in range(max_retries):
        try:
            result = func(*args)
            time.sleep(0.35)  # Space requests
            return result
        except Exception as e:
            if "rate_limited" in str(e).lower() or "429" in str(e):
                wait = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                time.sleep(wait)
            else:
                raise
    raise Exception(f"Failed after {max_retries} retries")
```

---

## Common Gotchas

1. **Enhanced connector has broader access.** Pages returning 404 on Raw API may work on Enhanced Connector. Always try enhanced first.

2. **Date expansion is mandatory.** `"Due Date": "2026-03-15"` will silently fail. Must use `"date:Due Date:start"`.

3. **Multi-select values are stringified JSON arrays.** Not native arrays.

4. **Checkbox is `"__YES__"` / `"__NO__"`.** Not `true`/`false`.

5. **Relations need page URLs, not IDs.** Format: `"[\"https://www.notion.so/page-id\"]"`

6. **Select options are case-sensitive.** "Active" works, "active" fails silently.

7. **notion-update-page has multiple commands:** `update_properties`, `replace_content`, `replace_content_range`, `insert_content_after`. Choose the right one.

8. **Content selection uses ellipsis format.** For `replace_content_range`: `"selection_with_ellipsis": "# Section Ti...end of text"` (first ~10 chars + `...` + last ~10 chars).

9. **Cannot trash pages via API.** `API-patch-page` with `in_trash: true` returns 404. Workaround: prefix title with `[DELETED]`, set status to "Dismissed".

10. **[NEW] markers for evidence fields.** Prepend evidence updates with `[NEW YYYY-MM-DD]`. Use `\n` for line breaks (or `<br>` for better Notion rendering).

11. **Numbers are native, not strings.** `"Relevance Score": 8`, not `"Relevance Score": "8"`.

12. **Relations require fetching target pages first.** To set a Company relation, query Portfolio DB to find the page URL.

13. **Fetch schema before writing.** Always `notion-fetch` on `collection://` URL to get current schema. This prevents silent failures from misspelled property names.

---

## Sync Agent Notion Write Patterns

### Creating a new Thesis Thread in Notion

```python
# Using notion-create-pages
parent = {"data_source_id": "3c8d1a34-e723-4fb1-be28-727777c22ec6"}
properties = {
    "Thread Name": thread_name,
    "Status": "Exploring",  # Default -- Aakash sets this
    "Conviction": conviction,
    "Core Thesis": core_thesis,
    "Key Questions": f"{open_count} open, {answered_count} answered",
    "Evidence For": evidence_for,
    "Evidence Against": evidence_against,
    "Connected Buckets": json.dumps(buckets),  # e.g., '["New Cap Tables", "Thesis Evolution"]'
    "Discovery Source": discovery_source,
    "date:Date Discovered:start": date_discovered,
    "date:Date Discovered:is_datetime": 0,
}
```

### Creating an Action in Notion

```python
parent = {"data_source_id": "1df4858c-6629-4283-b31d-50c5e7ef885d"}
properties = {
    "Action": action_text,
    "Action Type": action_type,
    "Priority": priority,  # "P0 - Act Now", "P1 - This Week", etc.
    "Status": "Proposed",
    "Source": source,
    "Assigned To": assigned_to,
    "Created By": "AI CoS",
    "Reasoning": reasoning,
    "Relevance Score": relevance_score,  # integer
    "Thesis Connection": thesis_connection_text,
}
# Add relations if available:
if company_page_url:
    properties["Company"] = json.dumps([company_page_url])
if thesis_page_url:
    properties["Thesis"] = json.dumps([thesis_page_url])
if digest_page_url:
    properties["Source Digest"] = json.dumps([digest_page_url])
```

### Updating a Thesis Thread in Notion

```python
# notion-update-page with command: "update_properties"
page_id = notion_page_id
properties = {
    "Evidence For": updated_evidence_for,  # Full text, not just the new addition
    "Key Questions": f"{new_open} open, {new_answered} answered",
    "Investment Implications": updated_implications,
}
```

### Adding Content Blocks to a Thesis Page

For key questions and evidence blocks that live in the page body (not properties):

```python
# Use API-patch-block-children to append blocks
block_id = notion_page_id
children = [
    {
        "object": "block",
        "type": "paragraph",
        "paragraph": {
            "rich_text": [{"text": {"content": "[OPEN] New key question text -- Added 2026-03-15 via ContentAgent"}}]
        }
    }
]
```
