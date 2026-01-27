-- SQL function to delete articles older than 72 hours
-- This function bypasses Row Level Security (RLS) policies
-- Run this in the Supabase SQL Editor

CREATE OR REPLACE FUNCTION delete_old_articles()
RETURNS INTEGER
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    deleted_count INTEGER := 0;
    temp_count INTEGER;
BEGIN
    -- Delete articles older than 72 hours based on published_at
    DELETE FROM articles
    WHERE published_at < NOW() - INTERVAL '72 hours';
    
    GET DIAGNOSTICS temp_count = ROW_COUNT;
    deleted_count := deleted_count + temp_count;
    
    -- Also delete articles without published_at that are older than 72 hours based on created_at
    DELETE FROM articles
    WHERE published_at IS NULL
      AND created_at < NOW() - INTERVAL '72 hours';
    
    GET DIAGNOSTICS temp_count = ROW_COUNT;
    deleted_count := deleted_count + temp_count;
    
    RETURN deleted_count;
END;
$$;

-- Grant execute permission to authenticated users (or anon if needed)
-- Adjust based on your RLS policies
GRANT EXECUTE ON FUNCTION delete_old_articles() TO authenticated;
GRANT EXECUTE ON FUNCTION delete_old_articles() TO anon;
