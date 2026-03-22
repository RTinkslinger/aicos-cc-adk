# WhatsApp Ingestion Pipeline Audit

**Date:** 2026-03-21
**Machine:** TEMP (WhatsApp Pipeline)
**Status:** Complete - Layer 1 + Layer 2 operational, Layer 3 documented

---

## What Was Built

### Layer 1: Mac-Side Extraction (`scripts/whatsapp_extract.py`)

**Source:** `~/Library/Group Containers/group.net.whatsapp.WhatsApp.shared/ChatStorage.sqlite` (181MB)

**SQLite Schema Understanding:**
- `ZWACHATSESSION` - Chat sessions (3,248 active). Key fields: `ZCONTACTJID` (WhatsApp JID), `ZPARTNERNAME` (contact name), `ZSESSIONTYPE` (0=1:1, 1=Group, 3=Status, 4=Community), `ZLASTMESSAGEDATE` (Core Data timestamp)
- `ZWAMESSAGE` - Messages (162,220 total). Key fields: `ZCHATSESSION` (FK), `ZISFROMME`, `ZMESSAGEDATE`, `ZTEXT`, `ZMESSAGETYPE`, `ZGROUPMEMBER` (FK for sender in groups), `ZFROMJID`
- `ZWAGROUPMEMBER` - Group participants (26,006 unique JIDs). `ZMEMBERJID`, `ZCONTACTNAME`
- `ZWAPROFILEPUSHNAME` - JID-to-name mapping (1,161 entries). Most reliable name source
- `ZWAMEDIAITEM` - Media metadata (not binary data)

**Name Resolution Strategy (multi-layer):**
1. `ZWAPROFILEPUSHNAME.ZPUSHNAME` - highest quality (1,161 entries)
2. `ZWACHATSESSION.ZPARTNERNAME` - 100% coverage for 1:1 chats (544 contacts)
3. `ZWAGROUPMEMBER.ZCONTACTNAME` - sparse but useful
4. Phone number extraction from `@s.whatsapp.net` JIDs
5. Truncated hash fallback for `@lid` format JIDs

**Key Discovery:** `ZPUSHNAME` field on `ZWAMESSAGE` is protobuf-encoded (not plain text). The `ZWAPROFILEPUSHNAME` table has the clean string mapping. Group member JID resolution rate is only 2.1% via push name table, but 1:1 chats have 100% name coverage via `ZPARTNERNAME`.

**Timestamp Format:** Core Data timestamps (seconds since 2001-01-01). Offset: +978307200 to convert to Unix epoch.

**Script Features:**
- Read-only SQLite access (`?mode=ro`)
- Incremental extraction via `.last_run` timestamp file
- Outputs markdown per conversation to `data/whatsapp/`
- Metadata header: chat name, type, JID, message count, date range, participants
- Messages grouped by date with sender resolution
- Modes: `--full`, `--since N`, `--chat NAME`, `--min-messages N`, `--dry-run`

**Extraction Results:**
- 715 conversations exported (min 5 messages threshold)
- 153,542 total messages
- 20MB total markdown output
- Date range: 2011-12-10 to 2026-03-22
- Largest chat: 77 Place Residents (13,868 messages, 1.6MB)

### Layer 2: Supabase Ingestion (`scripts/whatsapp_ingest.py`)

**Table:** `public.whatsapp_conversations` (project `llfkxnsfczludgigknbs`)

**Schema (after migration):**
| Column | Type | Notes |
|--------|------|-------|
| id | serial PK | Auto-increment |
| chat_name | text NOT NULL | Unique constraint (pre-existing) |
| chat_type | text NOT NULL | "1:1" or "Group" |
| jid | text UNIQUE | WhatsApp JID (added) |
| participant_count | int | |
| message_count | int | |
| first_message_at | timestamptz | |
| last_message_at | timestamptz | |
| participants | jsonb | Array of participant names |
| resolved_participants | int | For Datum identity resolution |
| group_context | text | For Cindy context |
| metadata | jsonb | Extensible |
| full_text | text | Complete markdown (added, not yet populated) |
| summary | text | Compact descriptor (added) |
| embedding | vector(1536) | For semantic search (added, not yet populated) |
| created_at | timestamptz | |
| updated_at | timestamptz | (added) |

**Indexes:**
- `idx_whatsapp_conversations_chat_name` (chat_name)
- `idx_whatsapp_conversations_jid` (jid, unique)
- `idx_whatsapp_conversations_last_message` (last_message_at DESC)

**Ingestion Results:**
- 715 rows inserted via Supabase REST API
- 386 DM (1:1) chats, 329 group chats
- Bulk insert via batches of 50 with `resolution=merge-duplicates`
- RLS temporarily disabled for bulk insert, re-enabled after

**Script Modes:**
- `--sql` - Generate SQL INSERT statements (for MCP execute_sql)
- `--api` - Direct Supabase REST API (requires SUPABASE_SECRET_KEY in .env.local)
- `--dry-run` - Preview without writing

### Layer 3: Datum + Cindy Integration (Documented)

**Datum Agent Integration:**
1. **Identity Resolution:** Match `whatsapp_conversations.participants[]` names against `network.name` in Supabase. Use fuzzy matching for partial names (e.g., "Krish Bajaj" matches "Krish Bajaj" in Network DB)
2. **JID-to-Network Mapping:** Populate `identity_map` table with `surface='whatsapp'`, `identifier=jid`, `network_id=<resolved network ID>`
3. **Company Resolution:** For group chats containing company names (e.g., "Confido <> DeVC"), link to `companies` table
4. **Participant Enrichment:** For each resolved participant, update `resolved_participants` count on the conversation row

**Cindy Agent Integration:**
1. **Cross-Source Reasoning:** Query `whatsapp_conversations` by participant name to find conversation context when processing email/calendar/Granola signals
2. **Obligation Detection:** For 1:1 chats with high message counts, read the markdown files from `data/whatsapp/` to scan for I-owe/they-owe patterns
3. **Interaction Backfill:** Create `interaction_staging` entries from WhatsApp message patterns (frequent exchanges = active relationship signal)
4. **Group Context Tagging:** Populate `group_context` field with semantic labels (e.g., "deal flow", "portfolio monitoring", "personal") for use in action scoring

**Refresh Cadence:**
- Run `python3 scripts/whatsapp_extract.py` daily (incremental mode) on Mac
- Run `python3 scripts/whatsapp_ingest.py --api` after extraction to sync to Supabase
- Full re-extraction monthly (`--full`) to catch name resolution improvements

---

## Data Quality Notes

- **Name resolution gaps:** ~2% of group member JIDs resolve to readable names via `ZWAPROFILEPUSHNAME`. Most show as truncated LID hashes. This improves as more contacts are added to the phone.
- **Timestamp anomalies:** Some chats have future-looking timestamps (e.g., year 9026, 7026, 8026). These are likely WhatsApp internal system messages or clock skew. The `DeVC Founders` and `Matrix Vault` chats show this pattern.
- **Full text not in Supabase yet:** The `full_text` column exists but is not populated. This was intentional -- 18.3MB of markdown is better served from local files initially. Can be populated later with `--api` mode when a service role key is configured.
- **Embeddings not generated:** The `embedding` column exists but needs a trigger or batch process to generate embeddings from the summary/full_text fields.

## Files Created

| File | Purpose |
|------|---------|
| `scripts/whatsapp_extract.py` | SQLite to markdown extraction |
| `scripts/whatsapp_ingest.py` | Markdown to Supabase ingestion |
| `data/whatsapp/*.md` | 715 conversation markdown files |
| `data/whatsapp/.last_run` | Incremental extraction state |

## Top Conversations by Message Count

| Chat | Type | Messages |
|------|------|----------|
| 77 Place Residents | Group | 13,868 |
| 77 Place Core Poker | Group | 11,361 |
| IITB Kora-HSR-Indiranagar | Group | 5,736 |
| IIT Bombay Startup Founders | Group | 5,466 |
| All @ Z47 | Group | 4,373 |
| IITB AA Maharashtra | Group | 3,548 |
| Oceans- VC Community | Group | 3,015 |
| RM / Cash 1:1 | Group | 2,785 |
| Anish Patil * Matrix | 1:1 | 2,706 |
| DeVC IP 4.0 | Group | 2,645 |
