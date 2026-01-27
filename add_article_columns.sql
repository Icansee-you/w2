-- SQL script to add missing columns to the articles table in Supabase
-- Run this in the Supabase SQL Editor

-- Add main_category column (TEXT, nullable)
-- This stores the primary category for the article (e.g., "Algemeen", "Buitenland", "Politiek")
ALTER TABLE articles 
ADD COLUMN IF NOT EXISTS main_category TEXT;

-- Add sub_categories column (TEXT[], nullable)
-- This stores an array of additional category labels
-- Example: ["Politiek", "Buitenland"] when main_category is "Buitenland"
ALTER TABLE articles 
ADD COLUMN IF NOT EXISTS sub_categories TEXT[];

-- Add categorization_argumentation column (TEXT, nullable)
-- This stores the reasoning/explanation for why the article was categorized this way
ALTER TABLE articles 
ADD COLUMN IF NOT EXISTS categorization_argumentation TEXT;

-- Add rss_feed_url column (TEXT, nullable)
-- This stores the RSS feed URL where the article came from
-- Example: "https://feeds.nos.nl/nosnieuwsbuitenland"
ALTER TABLE articles 
ADD COLUMN IF NOT EXISTS rss_feed_url TEXT;

-- Optional: Add comments to document the columns
COMMENT ON COLUMN articles.main_category IS 'Primary category for the article (e.g., Algemeen, Buitenland, Politiek)';
COMMENT ON COLUMN articles.sub_categories IS 'Array of additional category labels';
COMMENT ON COLUMN articles.categorization_argumentation IS 'Reasoning/explanation for the categorization';
COMMENT ON COLUMN articles.rss_feed_url IS 'RSS feed URL where the article was fetched from';

-- Optional: Create index on main_category for faster filtering
CREATE INDEX IF NOT EXISTS idx_articles_main_category ON articles(main_category);

-- Optional: Create GIN index on sub_categories for array queries
CREATE INDEX IF NOT EXISTS idx_articles_sub_categories ON articles USING GIN(sub_categories);
