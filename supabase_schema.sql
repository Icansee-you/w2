-- Supabase database schema for news aggregator
-- Run this SQL in your Supabase SQL editor to create the necessary tables

-- Articles table
CREATE TABLE IF NOT EXISTS articles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    stable_id TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    url TEXT NOT NULL,
    source TEXT DEFAULT 'NOS',
    published_at TIMESTAMPTZ,
    full_content TEXT,
    image_url TEXT,
    category TEXT,  -- Legacy single category (kept for compatibility)
    categories TEXT[],  -- New: multiple categories array
    categorization_llm TEXT,  -- Which LLM was used for categorization
    eli5_summary_nl TEXT,
    eli5_llm TEXT,  -- Which LLM was used to generate ELI5
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index on stable_id for fast lookups
CREATE INDEX IF NOT EXISTS idx_articles_stable_id ON articles(stable_id);

-- Create index on published_at for sorting
CREATE INDEX IF NOT EXISTS idx_articles_published_at ON articles(published_at DESC);

-- Create index on category for filtering
CREATE INDEX IF NOT EXISTS idx_articles_category ON articles(category);

-- Create index on categories array for filtering
CREATE INDEX IF NOT EXISTS idx_articles_categories ON articles USING gin(categories);

-- Create full-text search index
CREATE INDEX IF NOT EXISTS idx_articles_search ON articles USING gin(to_tsvector('dutch', coalesce(title, '') || ' ' || coalesce(description, '')));

-- User preferences table
CREATE TABLE IF NOT EXISTS user_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE,
    blacklist_keywords TEXT[] DEFAULT ARRAY['Trump', 'Rusland', 'Soedan', 'aanslag'],
    selected_categories TEXT[],  -- Categories user wants to see
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index on user_id
CREATE INDEX IF NOT EXISTS idx_user_preferences_user_id ON user_preferences(user_id);

-- Enable Row Level Security (RLS)
ALTER TABLE articles ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_preferences ENABLE ROW LEVEL SECURITY;

-- Policies for articles (public read, service role write)
CREATE POLICY "Articles are viewable by everyone" ON articles
    FOR SELECT USING (true);

CREATE POLICY "Articles are insertable by service role" ON articles
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Articles are updatable by service role" ON articles
    FOR UPDATE USING (true);

-- Policies for user_preferences (users can only access their own)
CREATE POLICY "Users can view their own preferences" ON user_preferences
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own preferences" ON user_preferences
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own preferences" ON user_preferences
    FOR UPDATE USING (auth.uid() = user_id);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to auto-update updated_at
CREATE TRIGGER update_articles_updated_at BEFORE UPDATE ON articles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_preferences_updated_at BEFORE UPDATE ON user_preferences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

