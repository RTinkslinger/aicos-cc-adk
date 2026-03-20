// =============================================================================
// IRGI Phase A: Auto Embeddings Edge Function
// =============================================================================
// Supabase Edge Function that processes embedding jobs from pgmq queue.
// Called by pg_cron via pg_net every 10 seconds.
//
// Embedding model: Voyage AI voyage-3.5 (1024 dimensions, 32K context)
// API docs: https://docs.voyageai.com/reference/embeddings-api
//
// Deploy: supabase functions deploy embed --project-ref llfkxnsfczludgigknbs
// Secret: supabase secrets set VOYAGE_API_KEY=<key> --project-ref llfkxnsfczludgigknbs
//
// Architecture:
//   INSERT/UPDATE -> trigger -> pgmq -> pg_cron (10s) -> pg_net HTTP POST
//   -> this Edge Function -> Voyage AI API -> write embedding back to row
//   -> delete job from pgmq queue
// =============================================================================

import "jsr:@supabase/functions-js/edge-runtime.d.ts";

import { z } from "npm:zod";

// Direct Postgres connection to read content and write embeddings
import postgres from "https://deno.land/x/postgresjs@v3.4.5/mod.js";

// Initialize Postgres client using built-in Supabase env var
const sql = postgres(Deno.env.get("SUPABASE_DB_URL")!);

// Voyage AI configuration
const VOYAGE_API_KEY = Deno.env.get("VOYAGE_API_KEY");
const VOYAGE_API_URL = "https://api.voyageai.com/v1/embeddings";
const VOYAGE_MODEL = "voyage-3.5";
// voyage-3.5 outputs 1024-dimensional vectors by default

// ---- Schemas ----

const jobSchema = z.object({
  jobId: z.number(),
  id: z.number(),
  schema: z.string(),
  table: z.string(),
  contentFunction: z.string(),
  embeddingColumn: z.string(),
});

const failedJobSchema = jobSchema.extend({
  error: z.string(),
});

type Job = z.infer<typeof jobSchema>;
type FailedJob = z.infer<typeof failedJobSchema>;

type Row = {
  id: number;
  content: unknown;
};

const QUEUE_NAME = "embedding_jobs";

// ---- Voyage AI ----

/**
 * Generates an embedding for the given text using Voyage AI voyage-3.5.
 *
 * Voyage AI API reference:
 * POST https://api.voyageai.com/v1/embeddings
 * Body: { input: string | string[], model: string }
 * Response: { data: [{ embedding: number[] }] }
 *
 * Rate limits: 300 RPM, 1M tokens/min on the default tier.
 * voyage-3.5 context: 32K tokens (~120K chars).
 */
async function generateEmbedding(text: string): Promise<number[]> {
  if (!VOYAGE_API_KEY) {
    throw new Error(
      "VOYAGE_API_KEY not set. Run: supabase secrets set VOYAGE_API_KEY=<key>"
    );
  }

  // Truncate text if excessively long (Voyage AI has 32K token limit,
  // ~120K chars is a safe approximation)
  const truncatedText = text.length > 120_000 ? text.slice(0, 120_000) : text;

  const response = await fetch(VOYAGE_API_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${VOYAGE_API_KEY}`,
    },
    body: JSON.stringify({
      input: truncatedText,
      model: VOYAGE_MODEL,
    }),
  });

  if (!response.ok) {
    const errorBody = await response.text();

    // Detect rate limiting for caller-side backoff
    if (response.status === 429) {
      throw new Error(`RATE_LIMITED: ${errorBody}`);
    }

    throw new Error(
      `Voyage AI API error (${response.status}): ${errorBody}`
    );
  }

  const result = await response.json();
  const data = result.data?.[0];

  if (!data?.embedding) {
    throw new Error("Voyage AI returned no embedding data");
  }

  return data.embedding;
}

// ---- Job Processing ----

/**
 * Processes a single embedding job:
 * 1. Reads the row content using the specified content function
 * 2. Generates embedding via Voyage AI
 * 3. Writes the embedding back to the row
 * 4. Deletes the job from pgmq queue
 */
async function processJob(job: Job): Promise<void> {
  const { jobId, id, schema, table, contentFunction, embeddingColumn } = job;

  // Validate identifiers to prevent SQL injection (only allow alphanumeric + underscores)
  const safeIdRegex = /^[a-zA-Z_][a-zA-Z0-9_]*$/;
  for (const [name, val] of Object.entries({ schema, table, contentFunction, embeddingColumn })) {
    if (!safeIdRegex.test(val)) {
      throw new Error(`Invalid identifier for ${name}: ${val}`);
    }
  }

  // Fetch content for the schema/table/row using the content function
  const [row]: [Row] = await sql`
    SELECT
      id,
      ${sql(contentFunction)}(t) AS content
    FROM
      ${sql(schema)}.${sql(table)} t
    WHERE
      id = ${id}
  `;

  if (!row) {
    throw new Error(`Row not found: ${schema}.${table}/${id}`);
  }

  if (typeof row.content !== "string") {
    throw new Error(
      `Invalid content - expected string: ${schema}.${table}/${id}`
    );
  }

  // Skip empty content (nothing meaningful to embed)
  if (row.content.trim().length === 0) {
    console.log(`Skipping empty content: ${schema}.${table}/${id}`);
    // Still delete the job so it doesn't retry endlessly
    await sql`SELECT pgmq.delete(${QUEUE_NAME}, ${jobId}::bigint)`;
    return;
  }

  // Generate embedding via Voyage AI
  const embedding = await generateEmbedding(row.content);

  // Write embedding back to the row
  await sql`
    UPDATE
      ${sql(schema)}.${sql(table)}
    SET
      ${sql(embeddingColumn)} = ${JSON.stringify(embedding)}
    WHERE
      id = ${id}
  `;

  // Delete the completed job from the queue
  await sql`SELECT pgmq.delete(${QUEUE_NAME}, ${jobId}::bigint)`;
}

// ---- Worker Lifecycle ----

/**
 * Returns a promise that rejects if the Deno worker is terminating
 * (e.g., wall clock limit reached). This allows us to gracefully handle
 * pending jobs by marking them as failed with a termination reason.
 */
function catchUnload(): Promise<never> {
  return new Promise((_resolve, reject) => {
    addEventListener(
      "beforeunload",
      (ev: Event & { detail?: { reason?: string } }) => {
        reject(new Error(ev.detail?.reason ?? "Worker terminated"));
      }
    );
  });
}

// ---- HTTP Handler ----

Deno.serve(async (req) => {
  // Health check endpoint
  if (req.method === "GET") {
    return new Response(
      JSON.stringify({
        status: "ok",
        function: "embed",
        model: VOYAGE_MODEL,
        hasApiKey: !!VOYAGE_API_KEY,
      }),
      {
        status: 200,
        headers: { "content-type": "application/json" },
      }
    );
  }

  if (req.method !== "POST") {
    return new Response("Expected POST request", { status: 405 });
  }

  if (req.headers.get("content-type") !== "application/json") {
    return new Response("Expected JSON body", { status: 400 });
  }

  // Validate request body: array of jobs
  let rawBody: unknown;
  try {
    rawBody = await req.json();
  } catch {
    return new Response("Invalid JSON body", { status: 400 });
  }

  const parseResult = z.array(jobSchema).safeParse(rawBody);

  if (parseResult.error) {
    return new Response(
      `Invalid request body: ${parseResult.error.message}`,
      { status: 400 }
    );
  }

  const pendingJobs = parseResult.data;

  if (pendingJobs.length === 0) {
    return new Response(
      JSON.stringify({ completedJobs: [], failedJobs: [] }),
      {
        status: 200,
        headers: { "content-type": "application/json" },
      }
    );
  }

  const completedJobs: Job[] = [];
  const failedJobs: FailedJob[] = [];

  async function processAllJobs(): Promise<void> {
    let currentJob: Job | undefined;

    while ((currentJob = pendingJobs.shift()) !== undefined) {
      try {
        await processJob(currentJob);
        completedJobs.push(currentJob);
      } catch (error) {
        failedJobs.push({
          ...currentJob,
          error:
            error instanceof Error ? error.message : JSON.stringify(error),
        });

        // If rate limited, stop processing remaining jobs to avoid hammering the API
        if (error instanceof Error && error.message.startsWith("RATE_LIMITED")) {
          console.warn("Rate limited by Voyage AI, stopping batch early");
          // Push remaining jobs as failed with rate limit reason
          failedJobs.push(
            ...pendingJobs.map((job) => ({
              ...job,
              error: "Skipped due to rate limiting",
            }))
          );
          pendingJobs.length = 0; // Clear remaining
          break;
        }
      }
    }
  }

  try {
    // Process jobs, but abort gracefully if the worker is terminating
    await Promise.race([processAllJobs(), catchUnload()]);
  } catch (error) {
    // Worker terminating -- mark all remaining pending jobs as failed
    failedJobs.push(
      ...pendingJobs.map((job) => ({
        ...job,
        error:
          error instanceof Error ? error.message : JSON.stringify(error),
      }))
    );
  }

  // Log for observability (visible in Supabase Edge Function logs)
  console.log("Embedding job batch complete:", {
    completed: completedJobs.length,
    failed: failedJobs.length,
    failedDetails: failedJobs.map((j) => ({
      table: j.table,
      id: j.id,
      error: j.error,
    })),
  });

  return new Response(
    JSON.stringify({
      completedJobs,
      failedJobs,
    }),
    {
      status: 200,
      headers: {
        "content-type": "application/json",
        "x-completed-jobs": completedJobs.length.toString(),
        "x-failed-jobs": failedJobs.length.toString(),
      },
    }
  );
});
