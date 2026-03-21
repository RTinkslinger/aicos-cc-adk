-- Migration: Add embedding queue triggers to interactions table
-- Applied: 2026-03-20 by M8 Cindy Infrastructure
--
-- This adds two triggers that were missing from the interactions table:
-- 1. clear_interactions_embedding_on_update - clears embedding vector on content change
--    (so Supabase auto-embeddings will re-embed the row)
-- 2. interactions_embedding_queue - sends new/updated rows to pgmq 'embedding_jobs' queue
--    (so the embedding worker picks them up)
--
-- The content function embedding_input_interactions() was also created to generate
-- the text that gets embedded (summary + source + participants + action_items).

-- Content function for embedding text generation
CREATE OR REPLACE FUNCTION embedding_input_interactions(rec interactions)
RETURNS text
LANGUAGE plpgsql
IMMUTABLE
AS $$
BEGIN
  RETURN
    coalesce(rec.summary, '') || E'\n\n' ||
    'Source: ' || coalesce(rec.source, '') || E'\n' ||
    'Participants: ' || coalesce(array_to_string(rec.participants, ', '), '') || E'\n' ||
    'Action items: ' || coalesce(array_to_string(rec.action_items, '; '), '');
END;
$$;

-- Clear embedding on content update (same pattern as content_digests, thesis_threads, etc.)
CREATE TRIGGER clear_interactions_embedding_on_update
BEFORE UPDATE OF summary, participants, action_items, source ON public.interactions
FOR EACH ROW
EXECUTE FUNCTION util.clear_column('embedding');

-- Queue embedding job on insert or content update
CREATE TRIGGER interactions_embedding_queue
AFTER INSERT OR UPDATE OF summary, participants, action_items ON public.interactions
FOR EACH ROW
EXECUTE FUNCTION util.queue_embeddings('embedding_input_interactions', 'embedding');
