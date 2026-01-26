-- SQL Functie om user emails op te halen voor admin pagina
-- Voer dit uit in de SQL Editor van je Supabase dashboard

-- Functie die user emails ophaalt voor een lijst van user IDs
CREATE OR REPLACE FUNCTION get_user_emails(user_ids UUID[])
RETURNS TABLE(user_id UUID, email TEXT) 
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        au.id::UUID as user_id,
        au.email::TEXT as email
    FROM auth.users au
    WHERE au.id = ANY(user_ids);
END;
$$;

-- Functie die alle users met reading stats en emails ophaalt
-- Haalt ALLE geregistreerde gebruikers op uit auth.users, niet alleen diegenen met activiteit
CREATE OR REPLACE FUNCTION get_all_users_with_reading_stats()
RETURNS TABLE(
    user_id UUID,
    email TEXT,
    total_articles_opened BIGINT,
    total_articles_read BIGINT,
    avg_read_duration_seconds NUMERIC,
    read_percentage NUMERIC
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    RETURN QUERY
    WITH user_stats AS (
        SELECT 
            ra.user_id,
            COUNT(*) FILTER (WHERE ra.opened_at IS NOT NULL) as opened,
            COUNT(*) FILTER (WHERE ra.is_read = TRUE) as read,
            AVG(ra.read_duration_seconds) FILTER (WHERE ra.is_read = TRUE AND ra.read_duration_seconds > 0) as avg_duration
        FROM reading_activity ra
        GROUP BY ra.user_id
    )
    SELECT 
        au.id::UUID as user_id,
        COALESCE(au.email, 'Onbekend')::TEXT as email,
        COALESCE(us.opened, 0)::BIGINT as total_articles_opened,
        COALESCE(us.read, 0)::BIGINT as total_articles_read,
        COALESCE(us.avg_duration, 0)::NUMERIC as avg_read_duration_seconds,
        CASE 
            WHEN us.opened > 0 THEN (us.read::NUMERIC / us.opened::NUMERIC * 100)
            ELSE 0
        END::NUMERIC as read_percentage
    FROM auth.users au
    LEFT JOIN user_stats us ON us.user_id = au.id
    WHERE au.deleted_at IS NULL  -- Alleen actieve gebruikers (niet verwijderd)
    ORDER BY COALESCE(us.read, 0) DESC, au.created_at DESC;
END;
$$;

-- Grant execute permissions (aanpasbaar naar je security requirements)
GRANT EXECUTE ON FUNCTION get_user_emails(UUID[]) TO authenticated;
GRANT EXECUTE ON FUNCTION get_all_users_with_reading_stats() TO authenticated;
