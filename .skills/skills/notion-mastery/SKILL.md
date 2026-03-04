---
name: notion-mastery
version: 1.2.0
description: >
  Master reference for all Notion operations — reading, writing, querying, updating pages and databases.
  Works across ALL Claude surfaces: Cowork, Claude.ai (web/mobile/desktop), and Claude Code. Use this
  skill whenever ANY task will call Notion MCP tools — even if the user never says "Notion." If the
  task involves structured data stored in Notion (databases, pages, properties), this skill must load
  BEFORE the first tool call. The trigger is tool usage pattern, not user keywords: about to call
  notion-fetch, notion-create-pages, notion-update-page, notion-search, notion-query-database-view,
  or any API-* Notion endpoint? Load this first. Also trigger when building pipelines or workflows
  that read from or write to Notion databases, even if Notion is just one step in a larger chain.
---

# Notion Mastery Skill

This skill works across **all Claude surfaces** (Cowork, Claude.ai, Claude Code). Tool names vary
by surface but the patterns, property formatting, gotchas, and recipes are universal.

---

## Step 0: Detect Your Surface & Available Tools

Before doing anything, identify which Notion tools you have. Tool names include a UUID prefix that
varies per session/surface, but the suffixes are stable. Look for tools matching these patterns:

### Enhanced Connector (PREFERRED — look for tools containing `notion-`)

The tool names follow the pattern: `mcp__<UUID>__notion-<action>` where the UUID varies per session.
Scan your available tools for names containing `notion-fetch`, `notion-search`, `notion-create-pages`, etc.

Returns data in **Notion-flavored Markdown** with `<data-source>` tags, SQLite table definitions,
and `collection://` URLs. Has broader page access than the raw API.

| Tool suffix | Use For |
|-------------|---------|
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

### Raw API (USE for block-level ops — look for tools containing `API-`)

Tool names follow the pattern: `mcp__<UUID>__API-<action>` or `mcp__notion__API-<action>`.

Returns raw JSON in Notion's internal format. More granular but noisier.

| Tool suffix | Use For |
|-------------|---------|
| `API-post-search` | Text search (returns raw property objects, cursor pagination) |
| `API-get-block-children` | Read child blocks of a page/block |
| `API-patch-block-children` | Append new blocks to a page |
| `API-retrieve-a-block` | Get a single block |
| `API-update-a-block` | Update block text/checked state, archive/restore |
| `API-delete-a-block` | Delete a block |
| `API-retrieve-a-page` | Get page properties (raw JSON) |
| `API-patch-page` | Update page properties, archive, set icon/cover |
| `API-post-page` | Create a single page (raw property format) |
| `API-retrieve-a-page-property` | Get a single property value (paginated for rollups/relations) |
| `API-retrieve-a-comment` / `API-create-a-comment` | Comments |
| `API-query-data-source` | Query database with filters/sorts (raw format) |
| `API-retrieve-a-data-source` / `API-update-a-data-source` / `API-create-a-data-source` | DB schema CRUD |
| `API-list-data-source-templates` | Get database templates |
| `API-retrieve-a-database` | Get database metadata |
| `API-move-page` | Move a page to new parent |
| `API-get-users` / `API-get-user` / `API-get-self` | User info |

### Surface-Specific Notes

**Cowork:** Both tool sets typically available. Enhanced connector UUIDs change per session — always
scan your tool list. Prefer enhanced connector for everything except block-level operations.

**Claude.ai (web/mobile/desktop):** May have Notion tools via MCP connectors configured in Claude.ai
settings. Same patterns apply — scan available tools for `notion-` prefixed suffixes. If no Notion
tools are available, you cannot write to Notion directly — inform Aakash and suggest actions he can
take manually or defer to Cowork.

**Claude Code:** Notion tools available via MCP server configuration in `.mcp.json` or settings.
Same enhanced connector patterns. Can also use `curl` against the Notion API as fallback if MCP
tools are misconfigured (requires API key in environment).

---

## Decision Tree: Which Tool Set?

```
Need to READ a page's content or database schema?
  → Enhanced: notion-fetch (cleaner, broader access)

Need to SEARCH the workspace?
  → Enhanced: notion-search (semantic, includes connected sources)

Need to CREATE pages in a database?
  → Enhanced: notion-create-pages (batch up to 100, SQLite-style properties)

Need to UPDATE page properties?
  → Enhanced: notion-update-page with command: "update_properties"

Need to UPDATE page content (body text)?
  → Enhanced: notion-update-page with command: "replace_content" / "replace_content_range" / "insert_content_after"

Need to work with INDIVIDUAL BLOCKS (append, read children, delete)?
  → Raw API: API-get-block-children, API-patch-block-children, API-delete-a-block

Need to QUERY/BULK-READ a database?
  → `notion-fetch` on DB ID → find `<view url="view://UUID">` in response → `notion-query-database-view` with that `view://UUID`
  → Returns ALL rows with full properties in ONE call. Filter in-context after fetching.
  → ⚠️ NEVER use: `API-query-data-source` (all `/data_sources/*` endpoints broken), `notion-fetch` on `collection://` (schema only), `notion-query-database-view` with `https://` URLs (fails)
  → Known view URLs: Build Roadmap = `view://4eb66bc1-322b-4522-bb14-253018066fef`

Need to modify DATABASE SCHEMA?
  → Enhanced: notion-update-data-source (SQL DDL syntax)
```

**Key finding from testing:** The Enhanced Connector has broader page access than the Raw API.
Pages that return 404 on `API-retrieve-a-page` may be fully accessible via `notion-fetch`.
Always prefer the Enhanced Connector for reading pages.

---

## Property Formatting (Enhanced Connector)

When using `notion-create-pages` or `notion-update-page`, properties follow the **SQLite column format**
from the data source schema. Get the schema first with `notion-fetch` on `collection://<data_source_id>`.

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

### Date Properties (EXPANDED FORMAT — this is critical)

Dates are split into three expanded fields:

```json
{
  "date:Due Date:start": "2026-03-15",
  "date:Due Date:end": null,
  "date:Due Date:is_datetime": 0
}
```

Rules:
- `start` is required (ISO-8601 date or datetime string)
- `end` must be NULL for single dates, present for date ranges
- `is_datetime`: 0 for date-only, 1 for datetime (NULL defaults to 0)

### Relation Properties

Relations are JSON arrays of page URLs:

```json
{
  "Company": "[\"https://www.notion.so/page-id-here\"]"
}
```

You need the target page URL. Fetch the related data source first to find page URLs.

### Select/Multi-Select

Use the exact option name string. For multi-select, use a JSON array:

```json
{
  "Status": "Active",
  "Connected Buckets": "[\"New Cap Tables\", \"Thesis Evolution\"]"
}
```

---

## Aakash's Key Database IDs

Quick reference for the AI CoS databases (get full schemas with `notion-fetch` on the collection URL):

| Database | Data Source ID | Collection URL |
|----------|---------------|----------------|
| **Thesis Tracker** | `3c8d1a34-e723-4fb1-be28-727777c22ec6` | `collection://3c8d1a34-e723-4fb1-be28-727777c22ec6` |
| **Content Digest** | `df2d73d6-e020-46e8-9a8a-7b9da48b6ee2` | `collection://df2d73d6-e020-46e8-9a8a-7b9da48b6ee2` |
| **Portfolio Actions Tracker** | `1df4858c-6629-4283-b31d-50c5e7ef885d` | `collection://1df4858c-6629-4283-b31d-50c5e7ef885d` |
| **Portfolio DB** | `4dba9b7f-e623-41a5-9cb7-2af5976280ee` | `collection://4dba9b7f-e623-41a5-9cb7-2af5976280ee` |
| **Network DB** | `6462102f-112b-40e9-8984-7cb1e8fe5e8b` | `collection://6462102f-112b-40e9-8984-7cb1e8fe5e8b` |
| **Companies DB** | `1edda9cc-df8b-41e1-9c08-22971495aa43` | `collection://1edda9cc-df8b-41e1-9c08-22971495aa43` |
| **Build Roadmap** | `6e1ffb7e-01f1-4295-a7ea-67d5c9216d8f` | `collection://6e1ffb7e-01f1-4295-a7ea-67d5c9216d8f` |
| **Tasks Tracker** | `1b829bcc-b6fc-80fc-9da8-000b4927455b` | — |

---

## Common Recipes

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
     "Created By": "Cowork",
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
     "Evidence For": "existing text + \\n[NEW 2026-03-02] New evidence here",
     "Key Companies": "existing + \\n[NEW] Company Name (context)"
   }
```

### Recipe 4: Bulk-Read Any Database (PROVEN — session 032)

**This is the ONLY working method for reading all rows from a database.**

```
# Step 1: Get the view URL (skip if you already know it — see Known View URLs below)
notion-fetch with id: "<database-id>"
# Response includes: <view url="view://UUID"> tags

# Step 2: Fetch all rows with full properties (ONE call)
notion-query-database-view with view_url: "view://UUID-from-step-1"
# Returns all rows with all property values. Filter in-context.
```

**⚠️ BROKEN methods (never use for bulk reads):**
- `API-query-data-source` — ALL `/data_sources/*` endpoints return "Invalid request URL"
- `notion-fetch` on `collection://UUID` — returns schema/structure only, NOT data rows
- `notion-query-database-view` with `https://www.notion.so/...?v=...` — "Invalid database view URL"
- `notion-search` — returns titles only, no property values, max 10 per call

**Known View URLs (skip step 1):**
- Build Roadmap: `view://4eb66bc1-322b-4522-bb14-253018066fef`

### Recipe 5: Build Roadmap Operations

```
# READ all items (ONE call):
notion-query-database-view with view_url: "view://4eb66bc1-322b-4522-bb14-253018066fef"
# Then filter in-context for specific queries.

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
# Note: Epic and Priority are set during triage (Insight → Backlog), not at capture time.

# UPDATE — Move item through pipeline:
notion-update-page with command: "update_properties", page_id: "<page-id>"
properties: { "Status": "🔨 In Progress" }

# Dependencies is a one-way self-relation. To set:
# "Dependencies": "[\"https://www.notion.so/<page-id>\"]"
# GOTCHA: Dual self-relation via API fails with 500 — create one-way, toggle to two-way in Notion UI.
```

### Recipe 6: Search and Cross-Reference

```
1. Search workspace: notion-search → "topic keywords"
2. For each relevant result, fetch full content: notion-fetch → result.id
3. Cross-reference with thesis tracker entries
4. Create actions or update thesis threads based on findings
```

---

## API Limits & Guardrails

| Limit | Value | What to Do |
|-------|-------|------------|
| Rate limit | 3 requests/second (2,700 per 15 min) | Space requests; batch where possible |
| Pagination | Max 100 items per page | Use cursor-based pagination (`start_cursor` / `nextPageToken`) |
| Block append | Max 100 blocks per `children` array | Split large content into multiple appends |
| Rich text | Max 2,000 chars per text object | Break long text across multiple rich_text objects |
| Rich text array | Max 100 elements | Chunk if needed |
| Nesting depth | 2 levels max | Flatten deeper structures |
| Payload size | 500 KB | Split large batch operations |
| Page creation | Up to 100 pages per create-pages call | Batch efficiently |

### Pagination Pattern

Enhanced connector returns `nextPageToken` in responses. Raw API returns `next_cursor` + `has_more`.

```
// Enhanced connector
result = notion-query-database-view(view_url)
if result.nextPageToken:
    next_page = notion-query-database-view(view_url, pageToken=result.nextPageToken)

// Raw API
result = API-query-data-source(data_source_id, page_size=100)
if result.has_more:
    next_page = API-query-data-source(data_source_id, start_cursor=result.next_cursor)
```

---

## Gotchas & Patterns Discovered

1. **Enhanced connector has broader access.** Pages returning 404 on raw API may work fine on
   enhanced connector. Always try enhanced first.

2. **ALL Raw API `/data_sources/*` endpoints are broken** (session 032). `API-query-data-source`,
   `API-retrieve-a-data-source` — all return "Invalid request URL" regardless of UUID format
   (with/without dashes, data_source_id vs database_id). Use `notion-query-database-view` with
   `view://UUID` format instead. For schema, use `notion-fetch` on `collection://` URL (hyphens).

3. **Date property expansion is mandatory.** You cannot set `"Due Date": "2026-03-15"`. You must
   use the expanded format: `"date:Due Date:start"`, `"date:Due Date:end"`, `"date:Due Date:is_datetime"`.

4. **Multi-select values are JSON arrays as strings.** Not native arrays — wrap in a JSON string:
   `"[\"Option A\", \"Option B\"]"`

5. **Checkbox values are special strings.** Use `"__YES__"` and `"__NO__"`, not `true`/`false`.

6. **Relations need page URLs, not IDs.** Format: `"[\"https://www.notion.so/page-id\"]"`

7. **notion-update-page has multiple commands:**
   - `update_properties` — change property values only
   - `replace_content` — replace entire page body
   - `replace_content_range` — replace a specific section (use `selection_with_ellipsis`)
   - `insert_content_after` — add content after a specific point

8. **Content selection uses ellipsis format.** When targeting specific content for replacement:
   `"selection_with_ellipsis": "# Section Ti...end of text"` — first ~10 chars + `...` + last ~10 chars.

9. **notion-create-pages parent types:**
   - `{ "data_source_id": "uuid" }` — add to a specific data source (most common for databases)
   - `{ "page_id": "uuid" }` — add as child of a page
   - `{ "database_id": "uuid" }` — only if database has a single data source
   - Omit parent entirely — creates as private workspace-level page

10. **Raw API search returns different results.** `API-post-search` does text matching against titles
    and returns raw Notion property objects. Enhanced `notion-search` does semantic search and returns
    cleaner results with highlights.

11. **Large data source schemas.** Portfolio DB and Network DB have many properties. When fetching
    schemas, the response can exceed context limits. Use `Grep` on the saved output file to find
    specific property definitions rather than reading the entire response.

12. **Appending [NEW] markers to evidence fields.** When updating thesis threads, prepend evidence
    additions with `[NEW YYYY-MM-DD]` and use `<br>` for line breaks in rich text properties.
    The enhanced connector accepts plain `\n` in properties but `<br>` renders better in Notion.

13. **Cannot trash pages via raw API if created through enhanced connector.** The raw API's
    `API-patch-page` with `in_trash: true` returns 404 for pages only accessible via the enhanced
    connector. To "delete" test/junk pages, update their status to "Dismissed" and prefix the
    title with `[DELETED]`, then manually trash in the Notion UI.

14. **Number properties are plain numbers.** Use `"Relevance Score": 8`, not `"Relevance Score": "8"`.
    The enhanced connector accepts native JS numbers.

15. **Relation property requires fetching target pages first.** To set a Company relation on
    Portfolio Actions, you need the Notion page URL of the company from the Portfolio DB.
    Search or query the Portfolio DB data source first, then use the page URL in the relation.

---

## Workflow: Always Fetch Schema First

Before writing to ANY database, always:

1. `notion-fetch` the `collection://` URL to get the current schema
2. Read the SQLite table definition to know exact property names and types
3. Verify select/multi-select option names match exactly (case-sensitive)
4. Then proceed with create/update

This prevents silent failures from misspelled property names or invalid option values.
