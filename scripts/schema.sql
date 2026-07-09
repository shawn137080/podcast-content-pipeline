-- Podcast Pipeline — PostgreSQL Schema
-- Run once against your database:
--   psql -h localhost -U podcast -d podcast_pipeline -f schema.sql

-- ── Pipeline Runs Table ────────────────────────────────────────
CREATE TABLE IF NOT EXISTS pipeline_runs (
    id SERIAL PRIMARY KEY,
    episode_title TEXT NOT NULL,
    audio_url TEXT,
    audio_duration_minutes INTEGER,
    transcript_length INTEGER,
    transcript_text TEXT,
    speakers JSONB,
    stt_provider TEXT NOT NULL DEFAULT 'speechmatics',
    stt_job_id TEXT,
    llm_provider TEXT NOT NULL DEFAULT 'minimax',
    generated_content TEXT,
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- ── Indexes ───────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_pipeline_runs_status ON pipeline_runs(status);
CREATE INDEX IF NOT EXISTS idx_pipeline_runs_created_at ON pipeline_runs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_pipeline_runs_episode_title ON pipeline_runs(episode_title);

-- ── Timestamps trigger ────────────────────────────────────────
CREATE OR REPLACE FUNCTION update_completed_at()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'completed' AND OLD.status != 'completed' THEN
        NEW.completed_at = NOW();
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_completed_at ON pipeline_runs;
CREATE TRIGGER trigger_update_completed_at
    BEFORE UPDATE ON pipeline_runs
    FOR EACH ROW
    EXECUTE FUNCTION update_completed_at();

-- ── Sample data (for testing) ─────────────────────────────────
-- INSERT INTO pipeline_runs (episode_title, status) VALUES
--     ('Test Episode 1', 'pending'),
--     ('Test Episode 2', 'pending');
