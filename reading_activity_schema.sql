-- SQL Schema voor reading_activity tabel in Supabase
-- Voer dit uit in de SQL Editor van je Supabase dashboard

-- Verwijder de tabel als deze al bestaat (alleen nodig bij eerste setup of als je de fout hebt gekregen)
DROP TABLE IF EXISTS reading_activity CASCADE;

-- Maak de reading_activity tabel
CREATE TABLE IF NOT EXISTS reading_activity (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    article_id UUID NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    opened_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    last_viewed_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    read_duration_seconds INTEGER DEFAULT 0,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    
    -- Unieke constraint: één record per gebruiker per artikel
    UNIQUE(user_id, article_id)
);

-- Index voor snelle queries op user_id
CREATE INDEX IF NOT EXISTS idx_reading_activity_user_id ON reading_activity(user_id);

-- Index voor snelle queries op article_id
CREATE INDEX IF NOT EXISTS idx_reading_activity_article_id ON reading_activity(article_id);

-- Index voor snelle queries op opened_at (voor recent gelezen artikelen)
CREATE INDEX IF NOT EXISTS idx_reading_activity_opened_at ON reading_activity(opened_at DESC);

-- Index voor snelle queries op last_viewed_at
CREATE INDEX IF NOT EXISTS idx_reading_activity_last_viewed_at ON reading_activity(last_viewed_at DESC);

-- Row Level Security (RLS) policies
ALTER TABLE reading_activity ENABLE ROW LEVEL SECURITY;

-- Policy: Gebruikers kunnen alleen hun eigen reading activity zien
CREATE POLICY "Users can view their own reading activity"
    ON reading_activity
    FOR SELECT
    USING (auth.uid() = user_id);

-- Policy: Gebruikers kunnen alleen hun eigen reading activity toevoegen/updaten
CREATE POLICY "Users can insert their own reading activity"
    ON reading_activity
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own reading activity"
    ON reading_activity
    FOR UPDATE
    USING (auth.uid() = user_id);

-- Trigger om updated_at automatisch bij te werken
CREATE OR REPLACE FUNCTION update_reading_activity_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_reading_activity_updated_at
    BEFORE UPDATE ON reading_activity
    FOR EACH ROW
    EXECUTE FUNCTION update_reading_activity_updated_at();

-- Optionele view voor statistieken
CREATE OR REPLACE VIEW reading_activity_stats AS
SELECT 
    user_id,
    COUNT(*) as total_articles_opened,
    COUNT(*) FILTER (WHERE is_read = TRUE) as total_articles_read,
    MAX(opened_at) as last_article_opened_at,
    AVG(read_duration_seconds) as avg_read_duration_seconds
FROM reading_activity
GROUP BY user_id;
