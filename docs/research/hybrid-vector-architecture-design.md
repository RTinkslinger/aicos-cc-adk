# Hybrid Notion + Vector Store Architecture Design
**AI Chief of Staff Knowledge Layer**
**Status:** Research Design (Pre-Implementation)
**Last Updated:** 2026-03-04

---

## 1. Problem Statement

Notion is excellent for **structured, queryable data** (people, companies, theses, actions) but fundamentally limited for **semantic search**:

- "Find all meetings where someone discussed competitive threats in cybersecurity" requires embedding-based retrieval
- "Which portfolio companies align with our deeptech thesis?" needs cross-reference semantic matching
- "When did we last identify this founder archetype?" requires memory-aware dense search across unstructured signals

**Current state:** Action Optimizer uses Notion filters (boolean, keyword) → misses semantic relevance, context, and temporal patterns.

**Goal:** Hybrid system where Notion remains the source-of-truth for structured data, and a vector store enables **semantic retrieval + re-ranking** without abandoning relational integrity.

---

## 2. Vector Store Evaluation

| **Candidate** | **Local-First** | **Hybrid Search** | **Embed Cost** | **Latency** | **Scalability** | **Agent SDK Fit** |
|---|---|---|---|---|---|---|
| **Chroma** | ✅ Excellent | ⚠️ Basic (BM25) | None (embed locally) | ~50ms | Good (100K vectors) | ⭐⭐⭐ Embedded in Python |
| **Pinecone** | ❌ Managed | ✅ Full hybrid | $0.04/M vectors | ~100-200ms | Excellent | ⭐⭐ SaaS, API latency |
| **Weaviate** | ✅ Docker/local | ✅ Full hybrid | Custom | ~100ms | Excellent (1M+ vectors) | ⭐⭐ Containerized, more complex |
| **QMD** | ✅ Excellent | ✅ Hybrid built-in | None (Markdown-native) | ~10-20ms | Good (10K-100K docs) | ⭐⭐⭐⭐ Already in use for transcripts |
| **pgvector** | ✅ If Postgres exists | ⚠️ Keyword-only | None (PostgreSQL) | ~20-50ms | Excellent | ⭐⭐ Requires DB infrastructure |

### Recommendation: **Staged Multi-Store Approach**

- **Phase 1 (P0):** QMD local for meeting transcripts (already identified as fit)
- **Phase 2-3:** Chroma for research docs + content digests (low cost, embedded)
- **Phase 4+:** Weaviate for scale (if crossing 500K vectors) or Pinecone if multi-surface deployment needed

**Rationale:** Cowork sandbox (no outbound) → local-first essential. Start with QMD (already in play), add Chroma (simple embed), defer Weaviate/Pinecone to scale milestone. Reversible decisions until Phase 4.

---

## 3. Data Model: What Gets Vectorized

### 3.1 Vector-Eligible Data Sources

| **Source** | **Content Type** | **Chunk Strategy** | **Metadata** | **Refresh Cadence** |
|---|---|---|---|---|
| **Granola Transcripts** | Meeting audio → text | Semantic chunks (sentences/paragraphs, not fixed size) | company_id, thesis_id, attendees, date, duration, source_type="meeting" | On capture (~weekly) |
| **Research Docs** | Markdown deep-dives | Page-level + section chunks | doc_id, thesis_id, author, date_created, content_type="research" | On create/edit |
| **Notion Company Notes** | IDS trails, conviction changes, cap table notes | Page-level (don't over-chunk structured data) | company_id, portfolio_status, thesis_tags, source_type="notion" | On edit → queue |
| **Content Digest Analysis** | YouTube/content insights + AI analysis | Per-digest entry | digest_id, thesis_id, company_refs[], score, date, source_type="digest" | On digest publish |
| **Email/WhatsApp Signals** | Future: snippets from key stakeholders | Conversation-level chunks | sender_id, recipient_id, topic, date, source_type="message" | On receipt (future) |

### 3.2 What NOT to Vectorize

- **Notion database rows as-is** (e.g., Network DB full records) → Too structured; Notion filters suffice
- **Binary blobs** (PDFs, images without OCR) → Defer until OCR/document parsing in scope
- **Highly sensitive cap tables** → Encrypt at rest; restrict embedding to approved fields only

---

## 4. Hybrid Retrieval Architecture

```
User Query: "Companies working on supply chain + AI"
     ↓
[Query Router]
     ├─→ Structured Path: "Find companies with portfolio_status='Active'
     │                     AND thesis_tags contains 'supply_chain'"
     │   (Notion API + filters) → {companies: [C1, C2, ...]}
     │
     └─→ Semantic Path: Embed query → search vectors
         (Chroma/QMD + similarity) → {docs: [D1, D2, ...], scores: [0.87, 0.72, ...]}

[Merge + Re-rank]
     ├─ Extract context_objects from semantic results (company_id, thesis_id)
     ├─ Cross-reference with structured results
     ├─ Re-rank by: semantic_score × action_score × recency × bucket_impact
     └─ Return merged, scored results
```

### 4.1 Query Routing Rules

1. **Structured-only queries** (e.g., "Show my active portfolio" → Notion filters)
2. **Semantic-only queries** (e.g., "How did we describe Series A dynamics?" → vector search)
3. **Hybrid queries** (e.g., "Which portfolio companies match cybersecurity convictions?"):
   - Route to both paths in parallel
   - Merge results via Reciprocal Rank Fusion (RRF)
   - Re-rank with AI CoS context (action score, bucket priority, IDS state)

### 4.2 Reciprocal Rank Fusion (RRF) Formula

```
score(doc) = Σ [1 / (k + rank_source(doc))]
             across all sources

k = 60 (typical value; can tune)
rank_source = position in that source's ranking (1, 2, 3...)
```

Example:
- Doc A: rank 2 in Notion (1/62), rank 5 in vectors (1/65) → RRF score = 0.031
- Doc B: rank 8 in Notion (1/68), rank 1 in vectors (1/61) → RRF score = 0.033 ← winner

### 4.3 Re-ranking with AI CoS Scoring

After RRF merge:

```
final_score = (rrf_score × 0.4)
            + (action_score × 0.3)     # Bucket impact, time sensitivity
            + (recency_boost × 0.2)    # Temporal relevance (exponential decay)
            + (ids_state_match × 0.1)  # Does doc match current conviction level?
```

—Allows semantic relevance to be balanced against strategic priorities.

---

## 5. Write-Through Consistency

When Notion data changes, vectors must stay in sync without over-triggering.

### 5.1 Change Detection

```
[Notion Update]
     ↓
[Change Log Queue] (JSON log: page_id, timestamp, fields_changed)
     ↓
[Batch Process every 2 hours OR on explicit sync]
     ├─ Query Notion for affected pages
     ├─ Chunk modified content
     ├─ Delete old vectors for page_id
     ├─ Embed + upsert new vectors with updated metadata
     └─ Log sync status → Actions Queue (proposal: "Sync vectorstore with {page_id}")
```

### 5.2 Which Notion Fields Trigger Sync?

```yaml
Network DB:
  trigger: ["Notes", "IDS_State", "Archetype"]
  skip: ["Email", "Phone", "LinkedIn_URL"]  # Structured; no semantic value

Companies DB:
  trigger: ["Notes", "Conviction_Change", "IDS_Trail", "Cap_Table_Notes"]
  skip: ["Revenue", "Headcount", "Industry"]  # Notion filters work fine

Portfolio DB:
  trigger: ["Investment_Thesis", "Conviction_Rationale"]
  skip: ["Ownership_%", "Follow_On_Stage"]  # Structured
```

**Skip lists** prevent vector bloat and unnecessary embedding costs.

---

## 6. Implementation Phases (IDS Approach)

### Phase 1: Meeting Transcripts (P0, Weeks 1-2)
- **Scope:** Vectorize Granola transcripts via QMD local
- **Data:** ~50-100 recent transcripts (4-6 meetings/week × 12 weeks)
- **Output:** QMD index searchable by semantic queries + metadata filters (company, thesis, date)
- **Validation:** "Find all mentions of Series A pricing pressure" returns transcripts in ranked order
- **Blockers:** None (QMD already in use)

### Phase 2: Research Docs + Content Digests (Weeks 2-4)
- **Scope:** Chroma local for markdown research docs + Content Digest DB entries
- **Data:** ~200 research docs + ~100 digests
- **Output:** Chroma instance with multi-field metadata (doc_id, thesis_id, company_refs, content_type)
- **Validation:** Hybrid query: "Supply chain + AI" returns docs + digests ranked by relevance
- **Tech debt:** Define chunking strategy (page-level vs semantic boundaries)

### Phase 3: Notion Content Selective Sync (Weeks 4-6)
- **Scope:** Companies DB + Network DB notes → Chroma (selective fields only)
- **Data:** ~200 company pages + ~400 people pages (notes only, not structured fields)
- **Output:** Unified Chroma instance with 4 content types (transcripts, research, digests, Notion notes)
- **Validation:** Query that spans all 4 sources with RRF merge + re-ranking
- **Caution:** Set strict sync triggers to avoid vectorizing every Notion update

### Phase 4: Full Hybrid Retrieval + Re-ranking (Weeks 6-8)
- **Scope:** Notion API + Vector store + Action Scoring Model
- **Output:** "What's Next?" optimizer uses hybrid retrieval as primary knowledge layer
- **Validation:** Compare recommendations (old: Notion filters only vs new: hybrid) for action coverage
- **Milestone:** Close loop: hybrid query → proposed actions → Actions Queue

### Phase 5+: Multi-Surface + Scale (TBD)
- Add email/WhatsApp signals (post-MVP)
- Evaluate Weaviate if crossing 500K vectors
- Consider Pinecone for multi-region Agent SDK deployment

---

## 7. Data Integrity & Schema

### 7.1 Vector Metadata Schema

Every vector must carry:
```json
{
  "vector_id": "v-uuid",                    // Unique identifier
  "source_type": "meeting|research|digest|notion",
  "source_id": "page_id|transcript_id|...",
  "company_ids": ["company-1", "company-2"],  // Multi-relation
  "thesis_ids": ["thesis-1"],
  "content_type": "notes|transcript|analysis",
  "created_at": "2026-03-04T10:30:00Z",
  "updated_at": "2026-03-04T10:30:00Z",
  "is_archived": false,
  "embedding_model": "text-embedding-3-small",  // Reproducibility
  "chunk_index": 0,                         // For multi-chunk pages
  "chunk_text": "..."                       // For UI display
}
```

### 7.2 Validation Rules

- **No orphaned vectors:** If source_id is deleted in Notion, vector must be deleted
- **Metadata consistency:** company_ids in vector metadata must match actual Notion relations
- **Embedding reproducibility:** Store model name so re-embeddings use same model
- **Staleness detection:** If updated_at < (now - 7 days) AND source was edited, flag for re-sync

---

## 8. Agent SDK Considerations

The long-term vision is a custom Agent SDK. This architecture must be **portable**:

### 8.1 Reversible Decisions

✅ **Local vector store choice (Chroma)** → Can swap to Weaviate/Pinecone later; storage format doesn't lock in
✅ **Metadata schema** → JSON structure is portable across stores
✅ **Chunking strategy** → Defined in code, not in vector store; can re-chunk and re-embed if needed
✅ **Embedding model** → Stored in metadata; can migrate to different model with full re-embedding

❌ **Lock-in decisions to avoid:**
- Using Pinecone proprietary filtering (JSON filter syntax varies by platform)
- Hardcoding store-specific query syntax (use abstraction layer)
- Storing secrets/credentials in vector store (use external key management)

### 8.2 Abstraction Layer

Create `VectorStoreAdapter`:
```python
class VectorStoreAdapter:
    def search(self, query, filters, top_k) → List[Result]
    def upsert(self, vectors, metadata) → None
    def delete(self, vector_ids) → None
    def sync_from_notion(self, change_log) → None
```

—Allows swapping Chroma ↔ Weaviate ↔ Pinecone with one-line config change.

---

## 9. Deployment & Operations

### 9.1 Local-First (Cowork Sandbox)

```
Cowork Environment:
  ├─ QMD: /Users/.../qmd-index/ (local, no network)
  ├─ Chroma: ~/.chroma/ (local, ephemeral or synced to Git)
  ├─ Scripts:
  │   ├─ sync_notion_to_chroma.py (triggered on change or cron)
  │   ├─ embed_transcripts.py (triggered by Granola on_new_transcript)
  │   └─ rerank_results.py (called by optimizer)
  └─ Logs: docs/vector-sync-logs/
```

### 9.2 Sync Triggers

- **QMD:** On Granola new transcript → osascript MCP calls `embed_transcripts.py`
- **Chroma:** On content digest publish → `embed_digest.py`; on Notion change log → batch `sync_notion_to_chroma.py` every 2 hours
- **Validation:** Each script logs to `vector-sync-logs/` with timestamps, vector counts, errors

### 9.3 Monitoring Checklist

- [ ] Vector count drift (e.g., "50 Notion vectors deleted but source pages still exist")
- [ ] Embedding model mismatch (metadata says model X, but new embeddings use model Y)
- [ ] Stale vectors (updated_at too old; source was modified but not re-synced)
- [ ] Orphaned metadata (company_ids reference deleted companies)

---

## 10. Retrieval in Action: Example Flows

### 10.1 "Who Am I Underweighting in Cybersecurity?"

```
Structured: Get portfolio_status="Active" AND thesis_tags contains "cybersecurity"
            → {C1, C2, C3} (from Notion)

Semantic: Embed query → search for "security threats", "competitive dynamics",
          "market expansion" in transcripts + research
          → {T1 (score 0.89), T2 (score 0.78), ...}

Cross-reference: T1 mentions {C1, C4}; T2 mentions {C2, C5}
Merge: {C1, C2, C3, C4, C5}
Re-rank: C4 and C5 appear in semantic results but NOT in portfolio
         → Flag as "potential underweight, high conviction match"
         → Propose action: "Schedule deep-dive with C4 founders"

Output → Actions Queue
```

### 10.2 "What Did We Learn from That Founder Meeting?"

```
Query: Embed meeting context from calendar → search Granola index
Results: {T1, T2, T3} (top 3 most relevant transcript chunks)
Metadata: T1.company_id = C42, T1.thesis_ids = ["supply_chain", "AI"]
Context: Cross-reference with C42 in Notion → conviction level, investment stage
Display (mobile):
  "You met with C42 (Series B, $8M). Key insights:
   - <T1 excerpt> (supply_chain thesis)
   - <T2 excerpt> (competitive positioning)
   Proposed: Update C42 conviction score → Actions Queue"
```

---

## 11. Open Questions & Future Work

1. **Embedding freshness:** Re-embed all transcripts monthly? Or only on explicit request?
2. **Privacy at scale:** Email signals will add PII → need encrypted-at-rest vector storage. Defer to Phase 5.
3. **Multi-language:** If DeVC team includes non-English founders, need multilingual embeddings (e.g., text-embedding-3 supports 100+ languages).
4. **Feedback loops:** When user dismisses a proposal, does that re-weight result ranking? (Consider for Phase 4+)
5. **Agent SDK portability:** Will custom Agent SDK run vector store on-device? Or call Pinecone API? Impacts latency + cost trade-off.

---

## 12. Success Metrics

- ✅ QMD enables semantic transcript search (P0 Phase 1)
- ✅ Hybrid query precision (semantic + structured) > Notion-only by 30%+ (Phase 2)
- ✅ Action proposals improve from "What should I review?" → "Why should you prioritize C4?"
- ✅ Vector sync latency < 5 min from Notion change to queryable (Phase 3)
- ✅ Architecture remains portable: can swap vector store with <2 hours refactor (all phases)

---

**End of Document**

---

**Related:** This design feeds Phase 4+ of Build Roadmap ("Optimize My Meetings" + "Who Am I Underweighting?"). Ties to Thesis Tracker sync patterns (Phase 5: research tasks generate thesis evidence, which updates vectors).
