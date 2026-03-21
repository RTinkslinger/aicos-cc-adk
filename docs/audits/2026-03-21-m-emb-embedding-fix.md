# M-EMB: Embedding Queue Recovery Audit

**Date:** 2026-03-21
**Machine:** M-EMB (Temporary)
**Status:** FIXED - Queue draining autonomously

---

## Problem Statement

18,576 embedding messages stuck in pgmq `embedding_jobs` queue. All had `read_ct=0`. Reports of "connection failed" errors. Embedding coverage severely degraded (companies 10.4%, network 2.5%). Vector search impaired.

## Root Cause Analysis

### Primary Cause: Throughput Drop from M10 Cron Fix

The embedding processor cron (`process-embeddings`, jobid=1) was changed by M10 from `*/1 * * * *` (every 59 seconds) to `*/5 * * * *` (every 5 minutes). This was the correct fix for CIR reliability but had a side effect:

- **Before M10 fix:** 100 items/minute = 6,000/hour
- **After M10 fix:** 100 items/5min = 1,200/hour (5x reduction)

### Secondary Cause: M12 Data Enrichment Bulk Queue

M12's `page_content` enrichment updated thousands of companies and network rows. Each update fired the `queue_embeddings` trigger, which:
1. Cleared the existing embedding (set to NULL)
2. Queued a new embedding job

This created ~70,000+ queue entries in a short window. At the reduced 1,200/hour rate, the backlog became significant.

### Why read_ct=0 Was Misleading

The initial report said all messages had `read_ct=0`, suggesting nothing was being processed. Investigation revealed:
- The system WAS processing ~100 items per 5-min cycle (all succeeding)
- `pgmq.read()` sets a visibility timeout (VT=300s), during which `read_ct` increments
- After the Edge Function processes and deletes the message, it disappears
- The 18,576 messages with `read_ct=0` were simply ones that hadn't been reached yet

### The "Connection Failed" Errors

Investigation of `net._http_response` revealed 7,846 failed jobs across the day. These were NOT from a broken Edge Function but from **connection pool exhaustion** during high-concurrency periods. The Edge Function connects back to Postgres to write embeddings and delete queue messages. When too many parallel calls happen, the 60-connection limit is exhausted.

## Architecture (How Embeddings Work)

```
Trigger (queue_embeddings) -> pgmq.send('embedding_jobs', {...})
     |
Cron (*/5 * * * *) -> SELECT util.process_embeddings()
     |
process_embeddings():
  1. pgmq.read() - dequeue batch (sets VT=300s)
  2. Group into batches of batch_size
  3. For each batch: net.http_post -> Edge Function 'embed'
     |
Edge Function 'embed':
  1. For each job: call contentFunction to get text
  2. Generate embedding via AI model
  3. UPDATE table SET embedding = vector
  4. pgmq.delete() - remove from queue
```

Key: `net.http_post` is fire-and-forget. The Edge Function handles the full lifecycle including queue deletion.

## Fix Applied

### Changed `util.process_embeddings()` Default Parameters

| Parameter | Before | After | Impact |
|-----------|--------|-------|--------|
| `batch_size` | 10 | **25** | Items per Edge Function call |
| `max_requests` | 10 | **15** | Parallel Edge Function calls |
| **Per cycle** | 100 | **375** | 3.75x throughput increase |
| **Per hour** | 1,200 | **4,500** | With 5-min cron interval |

Why not higher:
- `max_requests=50` exhausted the 60-connection pool (confirmed by testing)
- `max_requests=20` still caused occasional exhaustion when stacking with other cron jobs
- `max_requests=15` with 25 baseline connections leaves ~20 spare = safe margin
- `batch_size=25` proven with 0 failures in Edge Function responses

### Verification

Post-fix cron cycle at 08:50 UTC:
- 15 Edge Function responses, each: `completed=25, failed=0`
- 375 items processed in one cycle
- No connection exhaustion
- Queue draining steadily

## Current State (08:52 UTC)

### Queue Status
| Table | Queue Items | Total Rows | Notes |
|-------|------------|------------|-------|
| Companies | 12,340 | 4,575 | Multiple queue entries per row (enrichment re-queued) |
| Network | 3,853 | 3,528 | Same - M12 enrichment re-queued |
| Interactions | 68 | - | Small batch |
| Actions Queue | 15 | 144 | Nearly done |
| **Total** | **16,276** | | |

### Embedding Coverage (Improving)
| Table | Start of Session | Current | Target |
|-------|-----------------|---------|--------|
| Companies | 10.7% (488/4575) | **50.8% (2324/4575)** | ~100% |
| Network | 5.3% (187/3528) | 10.4% (367/3528)* | ~100% |
| Actions Queue | - | **94.4% (136/144)** | ~100% |

*Network coverage temporarily dropped because M12 enrichment cleared old embeddings and re-queued. Will recover as network queue items are processed (they're behind companies in the queue).

### Drain Rate & ETA
- **Current rate:** 375 items per 5 minutes = 4,500/hour
- **Remaining:** 16,276 items
- **ETA to empty:** ~3.6 hours (~12:25 UTC / ~18:00 IST)

### Total Processed Today
- **51,445 embeddings completed** (since 02:35 UTC)
- **7,846 failed** (connection exhaustion, all retried automatically)
- **Zero Edge Function errors** - all failures were from connection pool pressure

## Recommendations

1. **Monitor queue depth** - Check `SELECT count(*) FROM pgmq.q_embedding_jobs` periodically. Should reach 0 by ~12:25 UTC.
2. **Connection pool awareness** - With 60 max connections and 25 baseline usage, the safe ceiling for parallel Edge Function calls is ~15. This should be documented for any future changes.
3. **Consider connection pooler** - If embedding throughput needs to increase beyond 4,500/hr, enable Supabase's PgBouncer connection pooler or increase the project's connection limit.
4. **Net._http_response cleanup** - The `net._http_response` table has 6,000+ rows. Consider periodic cleanup: `DELETE FROM net._http_response WHERE created < now() - interval '24 hours'`.
5. **Cron interval vs batch size** - The M10 fix (5-min interval) was correct for CIR stability. The right knob for embedding throughput is batch size, not cron frequency.
