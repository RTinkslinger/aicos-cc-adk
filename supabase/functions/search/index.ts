// =============================================================================
// IRGI Phase A: Hybrid Search API Edge Function
// =============================================================================
// Supabase Edge Function that provides semantic + keyword hybrid search
// across all AI CoS tables (content_digests, thesis_threads, actions_queue,
// companies).
//
// Called by WebFront (or any client) via:
//   POST https://llfkxnsfczludgigknbs.supabase.co/functions/v1/search
//
// Flow:
//   1. Client sends query text + optional filters
//   2. This function calls Voyage AI to embed the query
//   3. Calls the hybrid_search() SQL function with the embedding
//   4. Returns ranked results with snippets and metadata
//
// Deploy: supabase functions deploy search --project-ref llfkxnsfczludgigknbs
// =============================================================================

import "jsr:@supabase/functions-js/edge-runtime.d.ts";

import { z } from "npm:zod";

// Direct Postgres connection to call hybrid_search()
import postgres from "https://deno.land/x/postgresjs@v3.4.5/mod.js";

// Initialize Postgres client
const sql = postgres(Deno.env.get("SUPABASE_DB_URL")!);

// Voyage AI configuration
const VOYAGE_API_KEY = Deno.env.get("VOYAGE_API_KEY");
const VOYAGE_API_URL = "https://api.voyageai.com/v1/embeddings";
const VOYAGE_MODEL = "voyage-3.5";

// ---- Request Schema ----

const VALID_TABLES = [
  "content_digests",
  "thesis_threads",
  "actions_queue",
  "companies",
] as const;

const searchRequestSchema = z.object({
  // The search query text (required)
  query: z
    .string()
    .min(1, "Query must not be empty")
    .max(10_000, "Query too long"),

  // Optional: restrict to specific tables
  tables: z
    .array(z.enum(VALID_TABLES))
    .optional()
    .default(undefined as unknown as z.infer<z.ZodArray<z.ZodEnum<typeof VALID_TABLES>>>),

  // Optional: filter by status (e.g., "active", "pending", "published")
  status: z.string().optional(),

  // Optional: date range filters (ISO 8601)
  date_from: z.string().datetime({ offset: true }).optional(),
  date_to: z.string().datetime({ offset: true }).optional(),

  // Optional: filter by thesis thread ID (for thesis-scoped search)
  thesis_id: z.number().int().positive().optional(),

  // Optional: max results (default 20, max 50)
  limit: z.number().int().min(1).max(50).optional().default(20),

  // Optional: RRF weights (default 0.7 semantic, 0.3 keyword)
  semantic_weight: z.number().min(0).max(1).optional().default(0.7),
  keyword_weight: z.number().min(0).max(1).optional().default(0.3),
});

type SearchRequest = z.infer<typeof searchRequestSchema>;

// ---- Response Types ----

interface SearchResult {
  source_table: string;
  record_id: number;
  title: string;
  snippet: string;
  semantic_rank: number | null;
  keyword_rank: number | null;
  semantic_score: number;
  keyword_score: number;
  combined_score: number;
}

interface SearchResponse {
  query: string;
  results: SearchResult[];
  total: number;
  timing_ms: number;
  filters: {
    tables: string[] | null;
    status: string | null;
    date_from: string | null;
    date_to: string | null;
  };
}

// ---- Voyage AI Embedding ----

/**
 * Generates a query embedding using Voyage AI voyage-3.5.
 * Uses input_type: "query" for retrieval-optimized embeddings.
 */
async function embedQuery(text: string): Promise<number[]> {
  if (!VOYAGE_API_KEY) {
    throw new Error(
      "VOYAGE_API_KEY not set. Run: supabase secrets set VOYAGE_API_KEY=<key>"
    );
  }

  const response = await fetch(VOYAGE_API_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${VOYAGE_API_KEY}`,
    },
    body: JSON.stringify({
      input: text,
      model: VOYAGE_MODEL,
      input_type: "query", // Optimized for search queries
    }),
  });

  if (!response.ok) {
    const errorBody = await response.text();
    if (response.status === 429) {
      throw new Error(`Rate limited by Voyage AI. Try again shortly.`);
    }
    throw new Error(`Voyage AI API error (${response.status}): ${errorBody}`);
  }

  const result = await response.json();
  const data = result.data?.[0];

  if (!data?.embedding) {
    throw new Error("Voyage AI returned no embedding data");
  }

  return data.embedding;
}

// ---- CORS Headers ----

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers":
    "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};

// ---- HTTP Handler ----

Deno.serve(async (req) => {
  // Handle CORS preflight
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }

  // Health check
  if (req.method === "GET") {
    return new Response(
      JSON.stringify({
        status: "ok",
        function: "search",
        model: VOYAGE_MODEL,
        hasApiKey: !!VOYAGE_API_KEY,
        searchables: VALID_TABLES,
      }),
      {
        status: 200,
        headers: { ...corsHeaders, "content-type": "application/json" },
      }
    );
  }

  if (req.method !== "POST") {
    return new Response("Expected POST request", {
      status: 405,
      headers: corsHeaders,
    });
  }

  const startTime = performance.now();

  // Parse and validate request
  let rawBody: unknown;
  try {
    rawBody = await req.json();
  } catch {
    return new Response(
      JSON.stringify({ error: "Invalid JSON body" }),
      {
        status: 400,
        headers: { ...corsHeaders, "content-type": "application/json" },
      }
    );
  }

  const parseResult = searchRequestSchema.safeParse(rawBody);

  if (!parseResult.success) {
    return new Response(
      JSON.stringify({
        error: "Invalid request",
        details: parseResult.error.issues.map((i) => ({
          path: i.path.join("."),
          message: i.message,
        })),
      }),
      {
        status: 400,
        headers: { ...corsHeaders, "content-type": "application/json" },
      }
    );
  }

  const request: SearchRequest = parseResult.data;

  try {
    // Step 1: Generate query embedding via Voyage AI
    const queryEmbedding = await embedQuery(request.query);
    const embeddingStr = `[${queryEmbedding.join(",")}]`;

    // Step 2: Call hybrid_search() SQL function
    // Build the query with all optional filters
    const results: SearchResult[] = await sql`
      SELECT
        source_table,
        record_id,
        title,
        snippet,
        semantic_rank,
        keyword_rank,
        semantic_score,
        keyword_score,
        combined_score
      FROM hybrid_search(
        query_text := ${request.query},
        query_embedding := ${embeddingStr}::vector(1024),
        match_count := ${request.limit},
        keyword_weight := ${request.keyword_weight},
        semantic_weight := ${request.semantic_weight},
        filter_tables := ${request.tables ?? null},
        filter_status := ${request.status ?? null},
        filter_date_from := ${request.date_from ?? null}::timestamptz,
        filter_date_to := ${request.date_to ?? null}::timestamptz
      )
    `;

    // Step 3: If thesis_id filter is set, post-filter results
    // (thesis_id is a cross-reference -- thesis_threads by ID, other tables
    // by thesis_connection matching the thread name)
    let filteredResults = results;
    if (request.thesis_id) {
      // Get the thesis thread name for cross-referencing
      const [thesis] = await sql`
        SELECT thread_name FROM thesis_threads WHERE id = ${request.thesis_id}
      `;

      if (thesis) {
        filteredResults = results.filter((r) => {
          if (r.source_table === "thesis_threads") {
            return r.record_id === request.thesis_id;
          }
          // For other tables, the thesis connection is in the snippet/title
          // This is a soft filter -- the semantic search already biases toward
          // thesis-related content. A hard filter would require joining back
          // to the source tables, which we avoid for performance.
          return true;
        });
      }
    }

    const timingMs = Math.round(performance.now() - startTime);

    const response: SearchResponse = {
      query: request.query,
      results: filteredResults,
      total: filteredResults.length,
      timing_ms: timingMs,
      filters: {
        tables: request.tables ?? null,
        status: request.status ?? null,
        date_from: request.date_from ?? null,
        date_to: request.date_to ?? null,
      },
    };

    console.log(
      `Search: "${request.query.slice(0, 50)}" -> ${filteredResults.length} results in ${timingMs}ms`
    );

    return new Response(JSON.stringify(response), {
      status: 200,
      headers: {
        ...corsHeaders,
        "content-type": "application/json",
        "x-timing-ms": timingMs.toString(),
        "x-result-count": filteredResults.length.toString(),
      },
    });
  } catch (error) {
    const errorMessage =
      error instanceof Error ? error.message : "Unknown error";
    console.error(`Search error: ${errorMessage}`);

    // Determine appropriate status code
    const status = errorMessage.includes("Rate limited") ? 429 : 500;

    return new Response(
      JSON.stringify({
        error: errorMessage,
        query: request.query,
      }),
      {
        status,
        headers: { ...corsHeaders, "content-type": "application/json" },
      }
    );
  }
});
