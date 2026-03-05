# Notion Operations Guide

Canonical reference for all Notion operations in Claude Code. Read this before any Notion tool call.

---

## Tools

Notion MCP provides two tool sets. **Prefer the Enhanced Connector** for everything except block-level operations.

### Enhanced Connector (preferred)

Tool names contain `notion-` suffixes. Returns Notion-flavored Markdown with `<data-source>` tags and `collection://` URLs. Has broader page access than the Raw API.

| Tool | Use for |
|------|---------|
| `notion-fetch` | Read any page, database, or data source by URL/ID. Returns full content + schema. |
| `notion-search` | Semantic search across workspace + connected sources (Slack, Drive, etc.) |
| `notion-create-pages` | Create one or more pages in a database or standalone. Batch up to 100. |
| `notion-update-page` | Update properties, replace/insert content. Multiple command modes. |
| `notion-create-database` | Create databases with SQL DDL syntax. |
| `notion-update-data-source` | Add/drop/rename columns, change types. SQL DDL statements. |
| `notion-query-database-view` | Query using a database view's pre-configured filters/sorts. |
| `notion-query-meeting-notes` | Query meeting notes with structured filters. |
| `notion-get-comments` | Read discussions and comments on a page. |
| `notion-create-comment` | Add comments to pages or specific content. |
| `notion-get-users` | List/search workspace users. |
| `notion-get-teams` | List teamspaces. |
| `notion-duplicate-page` | Clone a page (async). |
| `notion-move-pages` | Move pages between parents. |

### Raw API (block-level only)

Tool names contain `API-` prefixes. Use only when you need block-level operations: `API-get-block-children`, `API-patch-block-children`, `API-delete-a-block`, `API-update-a-block`. The Enhanced Connector handles everything else better.

---

## Decision Tree

```
READ a page or database schema?
  → notion-fetch (cleaner, broader access than Raw API)

SEARCH the workspace?
  → notion-search (semantic, includes connected sources)

CREATE pages in a database?
  → notion-create-pages (batch up to 100, SQLite-style properties)

UPDATE page properties?
  → notion-update-page with command: "update_properties"

UPDATE page content (body text)?
  → notion-update-page with command: "replace_content" / "replace_content_range" / "insert_content_after"

BULK-READ a database?
  → notion-fetch on DB ID → find <view url="view://UUID"> → notion-query-database-view with view://UUID
  → Returns ALL rows in ONE call. Filter in-context.
  → Known view URLs: Build Roadmap = view://4eb66bc1-322b-4522-bb14-253018066fef
  → ⚠️ NEVER: API-query-data-source (broken), notion-fetch on collection:// (schema only),
    notion-query-database-view with https:// URLs (fails)

MODIFY database schema?
  → notion-update-data-source (SQL DDL syntax)

BLOCK-LEVEL ops (append, read children, delete blocks)?
  → Raw API: API-get-block-children, API-patch-block-children, API-delete-a-block
```

---

## Property Formatting

When using `notion-create-pages` or `notion-update-page`, properties follow the SQLite column format. Always fetch schema first with `notion-fetch` on `collection://<data_source_id>`.

### Standard Types

```json
{
  "Title Property": "The title text",
  "Text Property": "Plain text value",
  "URL Property": "https://example.com",
  "Number Property": 42,
  "Checkbox Property": "__YES__",
  "Select Property": "Option Name",
  "Multi-Select": "[\"Option A\", \"Option B\"]",
  "Email": "user@example.com"
}
```

### Dates (EXPANDED FORMAT — mandatory)

Dates must be split into three expanded fields. You cannot set `"Due Date": "2026-03-15"`.

```json
{
  "date:Due Date:start": "2026-03-15",
  "date:Due Date:end": null,
  "date:Due Date:is_datetime": 0
}
```

- `start`: required (ISO-8601 date or datetime)
- `end`: NULL for single dates, present for ranges
- `is_datetime`: 0 for date-only, 1 for datetime

### Relations

JSON arrays of page URLs (not IDs). Fetch the related data source first to find page URLs.

```json
{
  "Company": "[\"https://www.notion.so/page-id-here\"]"
}
```

### Select / Multi-Select

Exact option name string. Multi-select uses JSON array as string:

```json
{
  "Status": "Active",
  "Connected Buckets": "[\"New Cap Tables\", \"Thesis Evolution\"]"
}
```

---

## Database IDs

| Database | Data Source ID | Collection URL |
|----------|---------------|----------------|
| **Thesis Tracker** | `3c8d1a34-e723-4fb1-be28-727777c22ec6` | `collection://3c8d1a34-e723-4fb1-be28-727777c22ec6` |
| **Content Digest** | `df2d73d6-e020-46e8-9a8a-7b9da48b6ee2` | `collection://df2d73d6-e020-46e8-9a8a-7b9da48b6ee2` |
| **Portfolio Actions** | `1df4858c-6629-4283-b31d-50c5e7ef885d` | `collection://1df4858c-6629-4283-b31d-50c5e7ef885d` |
| **Portfolio DB** | `4dba9b7f-e623-41a5-9cb7-2af5976280ee` | `collection://4dba9b7f-e623-41a5-9cb7-2af5976280ee` |
| **Network DB** | `6462102f-112b-40e9-8984-7cb1e8fe5e8b` | `collection://6462102f-112b-40e9-8984-7cb1e8fe5e8b` |
| **Companies DB** | `1edda9cc-df8b-41e1-9c08-22971495aa43` | `collection://1edda9cc-df8b-41e1-9c08-22971495aa43` |
| **Build Roadmap** | `6e1ffb7e-01f1-4295-a7ea-67d5c9216d8f` | `collection://6e1ffb7e-01f1-4295-a7ea-67d5c9216d8f` |
| **Tasks Tracker** | `1b829bcc-b6fc-80fc-9da8-000b4927455b` | — |

---

## Recipes

### Recipe 1: Create a Content Digest Entry

```
1. Fetch schema: notion-fetch → collection://df2d73d6-e020-46e8-9a8a-7b9da48b6ee2
2. Create page:
   notion-create-pages with parent: { data_source_id: "df2d73d6-e020-46e8-9a8a-7b9da48b6ee2" }
   properties: {
     "Video Title": "Title Here",
     "Video URL": "https://youtube.com/...",
     "Summary": "AI-generated summary",
     "Key Insights": "Insight 1\nInsight 2",
     "Content Type": "Podcast",
     "Relevance Score": "High",
     "Net Newness": "Mostly New",
     "Action Status": "Pending",
     "Connected Buckets": "[\"New Cap Tables\", \"Thesis Evolution\"]",
     "date:Processing Date:start": "2026-03-02",
     "date:Processing Date:is_datetime": 0
   }
```

### Recipe 2: Create a Portfolio Action

```
1. Fetch schema: notion-fetch → collection://1df4858c-6629-4283-b31d-50c5e7ef885d
2. Find the portfolio company page URL (search or fetch Portfolio DB)
3. Create page:
   notion-create-pages with parent: { data_source_id: "1df4858c-6629-4283-b31d-50c5e7ef885d" }
   properties: {
     "Action": "Schedule technical deep-dive on MCP integration",
     "Action Type": "Meeting/Outreach",
     "Priority": "P1 - This Week",
     "Status": "Proposed",
     "Assigned To": "Aakash",
     "Source": "Content Pipeline",
     "Created By": "Claude Code",
     "Company": "[\"https://www.notion.so/company-page-id\"]",
     "Reasoning": "New evidence from podcast about MCP adoption...",
     "Relevance Score": 8
   }
```

### Recipe 3: Update a Thesis Thread

```
1. Search for the thesis: notion-search → "Agentic AI Infrastructure"
2. Read current state: notion-fetch → page ID from search
3. Update with new evidence:
   notion-update-page with command: "update_properties"
   page_id: "the-page-id"
   properties: {
     "Evidence For": "existing text + \n[NEW 2026-03-02] New evidence here",
     "Key Companies": "existing + \n[NEW] Company Name (context)"
   }
```

### Recipe 4: Bulk-Read Any Database

**The ONLY working method for reading all rows.**

```
# Step 1: Get the view URL (skip if you know it — see Known View URLs)
notion-fetch with id: "<database-id>"
# Response includes: <view url="view://UUID"> tags

# Step 2: Fetch all rows with full properties (ONE call)
notion-query-database-view with view_url: "view://UUID-from-step-1"
# Returns all rows with all property values. Filter in-context.
```

**Broken methods (never use):**
- `API-query-data-source` — ALL `/data_sources/*` endpoints return "Invalid request URL"
- `notion-fetch` on `collection://UUID` — schema only, NOT data rows
- `notion-query-database-view` with `https://` URLs — "Invalid database view URL"
- `notion-search` — titles only, no property values, max 10 per call

**Known view URLs:** Build Roadmap = `view://4eb66bc1-322b-4522-bb14-253018066fef`

### Recipe 5: Build Roadmap Operations

```
# READ all items (ONE call):
notion-query-database-view with view_url: "view://4eb66bc1-322b-4522-bb14-253018066fef"

# WRITE — Add a build insight:
notion-create-pages with parent: { data_source_id: "6e1ffb7e-01f1-4295-a7ea-67d5c9216d8f" }
properties: {
  "Item": "Description of the build insight",
  "Status": "💡 Insight",
  "Build Layer": "<appropriate layer>",
  "Source": "Session Insight",
  "Discovery Session": "Session NNN",
  "Technical Notes": "Context and rationale"
}

# UPDATE — Move item through pipeline:
notion-update-page with command: "update_properties", page_id: "<page-id>"
properties: { "Status": "🔨 In Progress" }

# Dependencies: one-way self-relation only.
# "Dependencies": "[\"https://www.notion.so/<page-id>\"]"
# GOTCHA: Dual self-relation via API fails with 500 — create one-way, toggle to two-way in Notion UI.
```

### Recipe 6: Search and Cross-Reference

```
1. Search workspace: notion-search → "topic keywords"
2. For each result, fetch full content: notion-fetch → result.id
3. Cross-reference with thesis tracker entries
4. Create actions or update thesis threads based on findings
```

---

## API Limits

| Limit | Value | What to do |
|-------|-------|------------|
| Rate limit | 3 req/sec (2,700 per 15 min) | Space requests; batch where possible |
| Pagination | Max 100 items per page | Use `nextPageToken` (enhanced) or `start_cursor` (raw API) |
| Block append | Max 100 blocks per `children` array | Split large content into multiple appends |
| Rich text | Max 2,000 chars per text object | Break long text across multiple rich_text objects |
| Nesting depth | 2 levels max | Flatten deeper structures |
| Payload size | 500 KB | Split large batch operations |
| Page creation | Up to 100 pages per call | Batch efficiently |

---

## Gotchas

1. **Enhanced connector has broader access.** Pages returning 404 on Raw API may work on Enhanced Connector. Always try enhanced first.

2. **ALL Raw API `/data_sources/*` endpoints are broken.** `API-query-data-source`, `API-retrieve-a-data-source` — all return "Invalid request URL" regardless of UUID format. Use `notion-query-database-view` with `view://UUID` instead.

3. **Date property expansion is mandatory.** Cannot use `"Due Date": "2026-03-15"` — must use `"date:Due Date:start"`, `"date:Due Date:end"`, `"date:Due Date:is_datetime"`.

4. **Multi-select values are JSON arrays as strings.** Not native arrays: `"[\"Option A\", \"Option B\"]"`

5. **Checkbox values are special strings.** `"__YES__"` and `"__NO__"`, not `true`/`false`.

6. **Relations need page URLs, not IDs.** Format: `"[\"https://www.notion.so/page-id\"]"`

7. **notion-update-page has multiple commands:** `update_properties`, `replace_content`, `replace_content_range` (use `selection_with_ellipsis`), `insert_content_after`.

8. **Content selection uses ellipsis format.** `"selection_with_ellipsis": "# Section Ti...end of text"` — first ~10 chars + `...` + last ~10 chars.

9. **notion-create-pages parent types:** `{ "data_source_id": "uuid" }` (most common), `{ "page_id": "uuid" }`, `{ "database_id": "uuid" }`, or omit for workspace-level.

10. **Raw API search differs from Enhanced.** `API-post-search` does text matching; `notion-search` does semantic search with highlights.

11. **Large schemas exceed context.** Portfolio DB and Network DB have many properties. Use `Grep` on saved output to find specific properties.

12. **[NEW] markers for evidence fields.** Prepend with `[NEW YYYY-MM-DD]`. Use `\n` in properties (`<br>` renders better in Notion UI).

13. **Cannot trash enhanced-connector pages via Raw API.** `API-patch-page` with `in_trash: true` returns 404. Workaround: prefix title with `[DELETED]`, set status to "Dismissed", manually trash in Notion UI.

14. **Number properties are plain numbers.** `"Relevance Score": 8`, not `"Relevance Score": "8"`.

15. **Relations require fetching target pages first.** To set a Company relation, you need the page URL from Portfolio DB. Query that DB first.

---

## Before Writing: Always Fetch Schema First

1. `notion-fetch` the `collection://` URL to get current schema
2. Read the SQLite table definition for exact property names and types
3. Verify select/multi-select option names match exactly (case-sensitive)
4. Then proceed with create/update

This prevents silent failures from misspelled property names or invalid option values.

---

## Database Schemas

Detailed schema docs live in `schemas/`:
- **Network DB** — `schemas/network-db.md` (44 columns, 13 archetypes, query translation guide)

For databases without schema docs, query live Notion: `notion-fetch` on the collection URL from the Database IDs table above. Schema docs will be added here as databases are documented.
