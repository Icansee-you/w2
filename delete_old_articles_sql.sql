-- SQL script to delete articles older than 72 hours from Supabase
-- Run this in the Supabase SQL Editor
-- This bypasses Row Level Security (RLS) policies

-- Delete articles older than 72 hours based on published_at
DELETE FROM articles
WHERE published_at < NOW() - INTERVAL '72 hours';

-- Also delete articles without published_at that are older than 72 hours based on created_at
DELETE FROM articles
WHERE published_at IS NULL
  AND created_at < NOW() - INTERVAL '72 hours';

-- Verify deletion (optional - run this to see how many articles remain)
-- SELECT COUNT(*) as remaining_old_articles
-- FROM articles
-- WHERE published_at < NOW() - INTERVAL '72 hours';
