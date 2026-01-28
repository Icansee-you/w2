-- =============================================================================
-- LLM usage logging: tabel + view per uur
-- Voer dit script uit in Supabase SQL Editor.
-- =============================================================================

-- Tabel: één rij per succesvolle API-call
CREATE TABLE IF NOT EXISTS llm_usage_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    llm TEXT NOT NULL,
    call_type TEXT NOT NULL,
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    total_tokens INTEGER,
    compute_points_used NUMERIC,
    article_id UUID REFERENCES articles(id) ON DELETE SET NULL
);

COMMENT ON TABLE llm_usage_log IS 'Log van tokengebruik per succesvolle LLM API-call (categorisatie of ELI5).';
COMMENT ON COLUMN llm_usage_log.llm IS 'LLM provider: Groq, RouteLLM, etc.';
COMMENT ON COLUMN llm_usage_log.call_type IS 'Type call: categorization of eli5';
COMMENT ON COLUMN llm_usage_log.compute_points_used IS 'RouteLLM credits indien beschikbaar.';

-- Index voor snelle aggregatie per uur
CREATE INDEX IF NOT EXISTS idx_llm_usage_log_created_at ON llm_usage_log (created_at);
CREATE INDEX IF NOT EXISTS idx_llm_usage_log_llm_call_type ON llm_usage_log (llm, call_type);

-- View: gebruik per uur, per LLM, per call_type
CREATE OR REPLACE VIEW llm_usage_per_hour AS
SELECT
    date_trunc('hour', created_at) AS hour_utc,
    llm,
    call_type,
    COUNT(*) AS successful_calls,
    COALESCE(SUM(prompt_tokens), 0)::BIGINT AS total_prompt_tokens,
    COALESCE(SUM(completion_tokens), 0)::BIGINT AS total_completion_tokens,
    COALESCE(SUM(total_tokens), 0)::BIGINT AS total_tokens,
    COALESCE(SUM(compute_points_used), 0)::NUMERIC AS total_compute_points_used
FROM llm_usage_log
GROUP BY date_trunc('hour', created_at), llm, call_type
ORDER BY hour_utc DESC, llm, call_type;

COMMENT ON VIEW llm_usage_per_hour IS 'Rapport per uur: aantal succesvolle API-calls en totaal tokens per LLM en call_type.';

-- RLS (optioneel): alleen lezen voor authenticated users
ALTER TABLE llm_usage_log ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "llm_usage_log_select" ON llm_usage_log;
CREATE POLICY "llm_usage_log_select" ON llm_usage_log FOR SELECT TO authenticated USING (true);

DROP POLICY IF EXISTS "llm_usage_log_insert_service" ON llm_usage_log;
CREATE POLICY "llm_usage_log_insert_service" ON llm_usage_log FOR INSERT TO authenticated WITH CHECK (true);

-- Voor anon (bijv. server-side met anon key) ook insert toestaan als je die gebruikt
DROP POLICY IF EXISTS "llm_usage_log_insert_anon" ON llm_usage_log;
CREATE POLICY "llm_usage_log_insert_anon" ON llm_usage_log FOR INSERT TO anon WITH CHECK (true);
