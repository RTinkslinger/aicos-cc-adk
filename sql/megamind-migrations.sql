-- Megamind Strategic Reasoning Agent — Database Migrations
-- Created: 2026-03-20
-- Tables: depth_grades, cascade_events, strategic_assessments, strategic_config
--
-- These tables support Megamind's three work types:
--   1. Depth Grading — calibrating how deep to investigate agent-delegated actions
--   2. Cascade Re-ranking — re-evaluating actions after new information arrives
--   3. Strategic Assessment — periodic portfolio-level analysis
--
-- All tables are Megamind-owned (read/write). Other agents have read-only access.

-- =============================================================================
-- Table 1: depth_grades
-- Tracks every depth grading decision Megamind makes.
-- =============================================================================

CREATE TABLE depth_grades (
    id SERIAL PRIMARY KEY,

    -- What action this grades
    action_id INTEGER NOT NULL,
        -- FK to actions_queue.id
    action_text TEXT NOT NULL,
        -- Cached action description for quick reference

    -- The grading decision
    auto_depth INTEGER NOT NULL,
        -- 0=Skip, 1=Scan, 2=Investigate, 3=Ultra
    approved_depth INTEGER,
        -- NULL until approved. Set by WebFront or auto-approval.
    strategic_score REAL NOT NULL,
        -- Megamind's strategic ROI score (0.0-1.0)
    reasoning TEXT NOT NULL,
        -- Why this depth was assigned

    -- Context snapshot (for calibration)
    eniac_raw_score REAL,
        -- ENIAC's raw action score at grading time
    thesis_connections TEXT[],
        -- Connected thesis thread names
    diminishing_returns_n INTEGER DEFAULT 0,
        -- How many similar actions completed in window
    marginal_value REAL,
        -- After diminishing returns: strategic_score x 0.7^n

    -- Execution tracking
    execution_status TEXT NOT NULL DEFAULT 'pending',
        -- pending | approved | executing | completed | skipped
    execution_agent TEXT,
        -- 'content' | 'datum' | NULL
    execution_prompt TEXT,
        -- The depth-calibrated prompt sent to executing agent
    execution_cost_usd REAL,
        -- Actual cost after completion (for budget tracking)

    -- Approval
    approved_by TEXT,
        -- 'auto' | 'webfront' | 'cai'
    approved_at TIMESTAMPTZ,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- For WebFront Depth Queue (pending grades needing approval)
CREATE INDEX idx_depth_grades_pending ON depth_grades(execution_status) WHERE execution_status = 'pending';

-- For budget tracking (daily spend)
CREATE INDEX idx_depth_grades_daily ON depth_grades(created_at) WHERE execution_status = 'completed';

-- For diminishing returns lookups (recent grades by thesis)
CREATE INDEX idx_depth_grades_thesis ON depth_grades USING gin(thesis_connections);

-- For Orchestrator: find approved grades needing execution routing
CREATE INDEX idx_depth_grades_approved ON depth_grades(execution_status) WHERE execution_status = 'approved';

-- For cascade trigger check: completed grades not yet cascaded
CREATE INDEX idx_depth_grades_completed ON depth_grades(execution_status, id) WHERE execution_status = 'completed';


-- =============================================================================
-- Table 2: cascade_events
-- Tracks every cascade re-ranking Megamind processes.
-- =============================================================================

CREATE TABLE cascade_events (
    id SERIAL PRIMARY KEY,

    -- What triggered this cascade
    trigger_type TEXT NOT NULL,
        -- 'depth_completed' | 'conviction_change' | 'new_thesis' | 'contra_signal' | 'portfolio_event'
    trigger_source_id INTEGER,
        -- FK to the triggering record (depth_grades.id, thesis_threads.id, etc.)
    trigger_description TEXT NOT NULL,
        -- Human-readable summary of the trigger

    -- Blast radius
    affected_thesis_threads TEXT[],
    affected_companies TEXT[],
    affected_actions_count INTEGER NOT NULL,
        -- How many open actions were in the blast radius

    -- Results
    actions_rescored INTEGER NOT NULL DEFAULT 0,
        -- How many actions had meaningful score changes (delta > 0.1)
    actions_resolved INTEGER NOT NULL DEFAULT 0,
        -- How many actions were closed as redundant/superseded
    actions_generated INTEGER NOT NULL DEFAULT 0,
        -- How many new actions were created
    net_action_delta INTEGER NOT NULL,
        -- actions_generated - actions_resolved (should be <= 0)

    -- Convergence
    convergence_pass BOOLEAN NOT NULL,
        -- TRUE if net_action_delta <= 0
    convergence_exception_reason TEXT,
        -- If convergence_pass = FALSE, why was the exception allowed?

    -- The full cascade report (for WebFront display)
    cascade_report JSONB NOT NULL,
        -- {
        --   rescored: [{action_id, old_score, new_score, delta, reasoning}],
        --   resolved: [{action_id, reason}],
        --   generated: [{action_text, score, reasoning, thesis_connection}],
        --   summary: "human-readable summary"
        -- }

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- For cascade feed on WebFront (recent cascades)
CREATE INDEX idx_cascade_events_recent ON cascade_events(created_at DESC);

-- For convergence monitoring
CREATE INDEX idx_cascade_events_convergence ON cascade_events(convergence_pass) WHERE convergence_pass = FALSE;

-- For cascade chain limit check (prevent infinite loops)
CREATE INDEX idx_cascade_events_trigger ON cascade_events(trigger_type, trigger_source_id);


-- =============================================================================
-- Table 3: strategic_assessments
-- Periodic strategic snapshots Megamind produces.
-- =============================================================================

CREATE TABLE strategic_assessments (
    id SERIAL PRIMARY KEY,

    -- Assessment type
    assessment_type TEXT NOT NULL,
        -- 'daily' | 'post_cascade' | 'on_demand'

    -- Portfolio-level metrics
    total_open_actions INTEGER NOT NULL,
    total_open_human_actions INTEGER NOT NULL,
    total_open_agent_actions INTEGER NOT NULL,
    actions_resolved_since_last INTEGER NOT NULL,
    actions_generated_since_last INTEGER NOT NULL,

    -- Per-bucket analysis
    bucket_distribution JSONB NOT NULL,
        -- {
        --   "New Cap Tables": {open: 5, resolved_7d: 3, coverage: "adequate"},
        --   "Deepen Existing": {open: 8, resolved_7d: 2, coverage: "heavy"},
        --   ...
        -- }

    -- Per-thesis analysis
    thesis_momentum JSONB NOT NULL,
        -- {
        --   "Agentic AI Infrastructure": {
        --     conviction: "Evolving Fast",
        --     open_actions: 4,
        --     evidence_velocity: "high",
        --     assessment: "Well-covered, diminishing returns applying"
        --   },
        --   ...
        -- }

    -- Flags
    stale_actions INTEGER NOT NULL DEFAULT 0,
        -- Actions open > 14 days
    concentration_warnings TEXT[],
        -- Thesis threads with > 5 human actions open
    underserved_buckets TEXT[],
        -- Buckets with no actions resolved in 7 days

    -- Recommendations
    recommendations JSONB NOT NULL,
        -- [{type: "resolve", action_id: 42, reason: "stale"},
        --  {type: "depth_grade", action_id: 55, recommended_depth: 2, reason: "thesis momentum"},
        --  {type: "focus_shift", from: "Thesis A", to: "Thesis B", reason: "diminishing returns"}]

    -- Convergence health
    convergence_trend TEXT NOT NULL,
        -- 'converging' | 'stable' | 'diverging'
    convergence_ratio REAL NOT NULL,
        -- actions_resolved / actions_generated over last 7 days (should be >= 1.0)

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- For WebFront strategic overview (latest assessment)
CREATE INDEX idx_strategic_latest ON strategic_assessments(created_at DESC);


-- =============================================================================
-- Table 4: strategic_config
-- System-level configuration for Megamind's behavior.
-- =============================================================================

CREATE TABLE strategic_config (
    key TEXT PRIMARY KEY,
    value JSONB NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Seed default configuration
INSERT INTO strategic_config (key, value) VALUES
    ('trust_level', '"manual"'),
    ('trust_stats', '{"total_graded": 0, "auto_accepted": 0, "overridden": 0}'),
    ('daily_depth_budget_usd', '10.0'),
    ('diminishing_returns_decay', '0.7'),
    ('diminishing_returns_window_days', '14'),
    ('action_cap_human_per_thesis', '5'),
    ('action_cap_agent_per_thesis', '3'),
    ('staleness_warning_days', '14'),
    ('staleness_resolution_days', '30'),
    ('cascade_chain_limit', '1'),
    ('convergence_critical_threshold', '0.8'),
    ('convergence_critical_consecutive_days', '3');
