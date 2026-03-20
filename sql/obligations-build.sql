-- ============================================================
-- Obligations Intelligence — Phase 0: Schema Build
-- Created: 2026-03-20
-- Spec: docs/superpowers/specs/2026-03-20-obligations-intelligence-design.md
-- ============================================================

-- 1. Create obligations table
CREATE TABLE IF NOT EXISTS obligations (
    id SERIAL PRIMARY KEY,

    -- Who
    person_id INTEGER NOT NULL,
        -- FK to network.id — the other party in the obligation
    person_name TEXT NOT NULL,
        -- Denormalized for quick display (avoid JOIN on every WebFront render)
    person_role TEXT,
        -- Denormalized: current_role from network table

    -- What
    obligation_type TEXT NOT NULL CHECK (obligation_type IN ('I_OWE_THEM', 'THEY_OWE_ME')),
        -- I_OWE_THEM: Aakash committed to do something for this person
        -- THEY_OWE_ME: This person committed to do something for Aakash
    description TEXT NOT NULL,
        -- Human-readable: "Send term sheet feedback to Rahul"
    category TEXT NOT NULL DEFAULT 'follow_up',
        -- 'send_document' | 'reply' | 'schedule' | 'follow_up' | 'introduce' |
        -- 'review' | 'deliver' | 'connect' | 'provide_info' | 'other'

    -- Source (provenance)
    source TEXT NOT NULL,
        -- 'email' | 'whatsapp' | 'granola' | 'calendar' | 'manual'
    source_interaction_id INTEGER,
        -- FK to interactions.id — which interaction this was detected from
    source_quote TEXT,
        -- The exact text that triggered detection: "I'll send you the deck by Friday"
    detection_method TEXT NOT NULL DEFAULT 'explicit',
        -- 'explicit' — clear verbal/written commitment
        -- 'implied' — inferred from unanswered message, meeting etiquette, etc.
        -- 'manual' — Aakash created it manually

    -- Timing
    detected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        -- When Cindy detected this obligation
    due_date TIMESTAMPTZ,
        -- Explicit deadline if stated ("by Friday"), or inferred ("next week" = +7 days)
        -- NULL if no deadline mentioned — staleness tracking applies instead
    due_date_source TEXT,
        -- 'explicit' | 'inferred' | 'etiquette' | NULL

    -- Status lifecycle
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN (
        'pending', 'fulfilled', 'overdue', 'cancelled', 'snoozed', 'escalated'
    )),
        -- pending: active, not yet fulfilled
        -- fulfilled: completed (manually marked or auto-detected)
        -- overdue: past due_date or staleness threshold exceeded
        -- cancelled: no longer relevant
        -- snoozed: temporarily hidden (snooze_until timestamp)
        -- escalated: Megamind flagged as strategically critical
    status_changed_at TIMESTAMPTZ DEFAULT NOW(),
    fulfilled_at TIMESTAMPTZ,
    fulfilled_method TEXT,
        -- 'manual' | 'auto_detected' | 'action_completed'
    fulfilled_evidence TEXT,
        -- What resolved it: "Email sent on March 22 — interaction #456"
    snooze_until TIMESTAMPTZ,
        -- If snoozed: when to resurface

    -- Priority (Cindy's comms priority)
    cindy_priority REAL NOT NULL DEFAULT 0.5,
        -- 0.0-1.0 — Cindy's assessment based on relationship, staleness, type, source
    cindy_priority_factors JSONB,
        -- { relationship_tier, staleness_weight, obligation_type_weight, etc. }

    -- Priority (Megamind's strategic overlay)
    megamind_priority REAL,
        -- 0.0-1.0 — NULL until Megamind processes
    megamind_priority_factors JSONB,
    megamind_override BOOLEAN DEFAULT FALSE,
        -- TRUE if Megamind overrode to P0 for time-sensitive strategic opportunity

    -- Blended priority (final ranking) — GENERATED COLUMN
    -- 60% Cindy (relationship dynamics) + 40% Megamind (strategic context)
    -- Megamind can override to 1.0 for P0 strategic urgency
    blended_priority REAL GENERATED ALWAYS AS (
        CASE
            WHEN megamind_override THEN 1.0
            WHEN megamind_priority IS NOT NULL
                THEN (cindy_priority * 0.6) + (megamind_priority * 0.4)
            ELSE cindy_priority
        END
    ) STORED,

    -- Context
    context JSONB,
        -- { thesis_connection, company, company_id, deal_stage, related_obligations, etc. }

    -- Linked action (if an action was created to fulfill this obligation)
    linked_action_id INTEGER,
        -- FK to actions_queue.id

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Staleness view (NOW() is not immutable, so cannot be a stored generated column)
-- Use this view for any query that needs staleness_days
CREATE OR REPLACE VIEW obligations_with_staleness AS
SELECT *,
    CASE
        WHEN status IN ('pending', 'overdue', 'escalated')
            THEN EXTRACT(DAY FROM (NOW() - detected_at))::INTEGER
        ELSE 0
    END AS staleness_days
FROM obligations;

-- 3. Indexes

-- Primary query: active obligations sorted by blended priority
CREATE INDEX IF NOT EXISTS idx_obligations_active ON obligations(blended_priority DESC)
    WHERE status IN ('pending', 'overdue', 'escalated');

-- Obligations by person (for "what do I owe X?" / "what does X owe me?")
CREATE INDEX IF NOT EXISTS idx_obligations_person ON obligations(person_id, status);

-- Obligations by type (split view: I_OWE vs THEY_OWE)
CREATE INDEX IF NOT EXISTS idx_obligations_type ON obligations(obligation_type, status, blended_priority DESC)
    WHERE status IN ('pending', 'overdue', 'escalated');

-- Overdue obligations by due_date (for staleness processor)
CREATE INDEX IF NOT EXISTS idx_obligations_overdue ON obligations(due_date)
    WHERE status = 'pending' AND due_date IS NOT NULL;

-- Snoozed obligations ready to resurface
CREATE INDEX IF NOT EXISTS idx_obligations_snoozed ON obligations(snooze_until)
    WHERE status = 'snoozed' AND snooze_until IS NOT NULL;

-- Obligations by source interaction (dedup and provenance)
CREATE INDEX IF NOT EXISTS idx_obligations_source ON obligations(source_interaction_id)
    WHERE source_interaction_id IS NOT NULL;

-- Obligations with Megamind override (P0 strategic urgency)
CREATE INDEX IF NOT EXISTS idx_obligations_megamind_override ON obligations(updated_at DESC)
    WHERE megamind_override = TRUE AND status IN ('pending', 'escalated');

-- Full-text search on description
CREATE INDEX IF NOT EXISTS idx_obligations_description_fts ON obligations
    USING gin(to_tsvector('english', description));
