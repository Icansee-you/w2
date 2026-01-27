"""
Background RSS feed checker that runs every 15 minutes.
Automatically fetches new articles, categorizes them, and generates ELI5 summaries.
"""
import threading
import time
from datetime import datetime, timedelta
from typing import List, Optional
import os

# Ensure RouteLLM API key is available for categorization
# This is set here to ensure it's available even when Streamlit is not initialized
ROUTELLM_API_KEY = os.getenv('ROUTELLM_API_KEY', 's2_760166137897436c8b1dc5248b05db5a')
if ROUTELLM_API_KEY:
    os.environ['ROUTELLM_API_KEY'] = ROUTELLM_API_KEY

# RSS feed URLs to check
RSS_FEED_URLS = [
    'https://feeds.nos.nl/nosnieuwsalgemeen',
    'https://feeds.nos.nl/nosnieuwsbinnenland',
    'https://feeds.nos.nl/nosnieuwsbuitenland',
]

# Check interval in seconds (15 minutes = 900 seconds)
CHECK_INTERVAL = 15 * 60  # 15 minutes

# Cleanup is now done during RSS feed checks (every 15 minutes)
# Articles older than 72 hours are automatically removed

# Global state
_checker_thread: Optional[threading.Thread] = None
_checker_running = False
_last_check_time: Optional[datetime] = None
_last_check_result: Optional[dict] = None
_last_cleanup_time: Optional[datetime] = None


def check_rss_feeds() -> dict:
    """
    Check all RSS feeds for new articles and process them.
    Also cleans up articles older than 72 hours.
    
    Returns:
        Dict with summary of the check (inserted, updated, skipped, errors)
    """
    from articles_repository import fetch_and_upsert_articles
    from articles_repository import generate_missing_eli5_summaries
    
    global _last_check_time, _last_check_result
    
    # First, cleanup old articles (older than 72 hours)
    cleanup_old_articles()
    
    total_inserted = 0
    total_updated = 0
    total_skipped = 0
    errors = []
    
    # Check each feed
    for feed_url in RSS_FEED_URLS:
        try:
            # Reset counters before each feed
            from categorization_engine import reset_routellm_categorization_counter
            from nlp_utils import reset_routellm_eli5_counter
            reset_routellm_categorization_counter()
            reset_routellm_eli5_counter()
            
            # Use LLM categorization for better accuracy
            result = fetch_and_upsert_articles(
                feed_url, 
                max_items=50,  # Check up to 50 items per feed
                use_llm_categorization=True
            )
            
            if result.get('success'):
                inserted = result.get('inserted', 0)
                updated = result.get('updated', 0)
                total_inserted += inserted
                total_updated += updated
                total_skipped += result.get('skipped', 0)
                
                # Get categorization stats
                cat_groq = result.get('cat_groq', 0)
                cat_routellm = result.get('cat_routellm', 0)
                cat_failed = result.get('cat_failed', 0)
                
                # Get RouteLLM API call counts
                from categorization_engine import get_routellm_categorization_count
                from nlp_utils import get_routellm_eli5_count
                routellm_cat_calls = get_routellm_categorization_count()
                routellm_eli5_calls = get_routellm_eli5_count()
                
                # Generate ELI5 for new articles
                eli5_groq = 0
                eli5_routellm = 0
                eli5_failed = 0
                if inserted > 0:
                    eli5_result = generate_missing_eli5_summaries(limit=min(inserted, 10))
                    eli5_groq = eli5_result.get('groq', 0)
                    eli5_routellm = eli5_result.get('routellm', 0)
                    eli5_failed = eli5_result.get('failed', 0)
                
                # Calculate total API calls
                total_groq_calls = cat_groq + eli5_groq
                total_routellm_calls = routellm_cat_calls + routellm_eli5_calls
                
                # Log summary per feed (compact format)
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                print(f"[{timestamp}] RSS feed {feed_url}: {inserted} nieuw, {updated} bestaand. "
                      f"Cat: {cat_groq} Groq, {cat_routellm} RouteLLM, {cat_failed} gefaald. "
                      f"ELI5: {eli5_groq} Groq, {eli5_routellm} RouteLLM, {eli5_failed} gefaald. "
                      f"API calls: {total_groq_calls} Groq, {total_routellm_calls} RouteLLM")
            else:
                error_msg = result.get('error', 'Unknown error')
                errors.append(f"{feed_url}: {error_msg}")
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                print(f"[{timestamp}] RSS feed {feed_url}: Fout - {error_msg}")
                
        except Exception as e:
            error_msg = f"Exception checking {feed_url}: {str(e)}"
            errors.append(error_msg)
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f"[{timestamp}] RSS feed {feed_url}: Fout - {error_msg}")
    
    _last_check_time = datetime.now()
    _last_check_result = {
        'timestamp': _last_check_time.isoformat(),
        'inserted': total_inserted,
        'updated': total_updated,
        'skipped': total_skipped,
        'errors': errors,
        'success': len(errors) == 0
    }
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] RSS check voltooid: {total_inserted} nieuwe artikelen, {total_updated} bijgewerkt, {len(errors)} fouten")
    
    return _last_check_result


def cleanup_old_articles():
    """
    Delete articles older than 72 hours (3 days).
    This function is called during RSS feed checks.
    """
    global _last_cleanup_time
    
    try:
        # Suppress Streamlit warnings in background thread
        import warnings
        warnings.filterwarnings('ignore', category=UserWarning, message='.*ScriptRunContext.*')
        
        from supabase_client import get_supabase_client
        
        print(f"[RSS Checker] Starting cleanup of articles older than 72 hours at {datetime.now()}")
        supabase = get_supabase_client()
        
        if supabase:
            # Delete articles older than 72 hours (3 days)
            result = supabase.delete_old_articles(hours_old=72)
            _last_cleanup_time = datetime.now()
            
            if result.get('success'):
                deleted_count = result.get('deleted_count', 0)
                print(f"[RSS Checker] Cleanup complete: deleted {deleted_count} articles older than 72 hours")
            else:
                error = result.get('error', 'Unknown error')
                print(f"[RSS Checker] Cleanup error: {error}")
        else:
            print("[RSS Checker] Cannot perform cleanup: Supabase client not available")
    except Exception as e:
        print(f"[RSS Checker] Exception during cleanup: {e}")


def _background_checker_loop():
    """Background thread that checks RSS feeds periodically and cleans up old articles."""
    global _checker_running, _last_cleanup_time
    
    # Suppress Streamlit warnings in background thread (this is normal - background threads don't have Streamlit context)
    import warnings
    warnings.filterwarnings('ignore', category=UserWarning, message='.*ScriptRunContext.*')
    
    print("[RSS Checker] Background checker started")
    
    # Wait a bit before first check (to let app initialize)
    time.sleep(30)
    
    # Perform initial cleanup check
    cleanup_old_articles()
    
    while _checker_running:
        try:
            # Check RSS feeds (every 15 minutes)
            # This also performs cleanup of articles older than 72 hours
            check_rss_feeds()
                
        except Exception as e:
            print(f"[RSS Checker] Error in background checker loop: {e}")
        
        # Wait for next check interval
        if _checker_running:
            time.sleep(CHECK_INTERVAL)
    
    print("[RSS Checker] Background checker stopped")


def start_background_checker():
    """Start the background RSS checker thread."""
    global _checker_thread, _checker_running
    
    if _checker_running:
        print("[RSS Checker] Background checker already running")
        return
    
    _checker_running = True
    _checker_thread = threading.Thread(
        target=_background_checker_loop,
        daemon=True,  # Thread will stop when main program exits
        name="RSSBackgroundChecker"
    )
    _checker_thread.start()
    print(f"[RSS Checker] Background checker started (checking every {CHECK_INTERVAL // 60} minutes)")


def stop_background_checker():
    """Stop the background RSS checker thread."""
    global _checker_running, _checker_thread
    
    if not _checker_running:
        return
    
    _checker_running = False
    if _checker_thread:
        _checker_thread.join(timeout=5)
    print("[RSS Checker] Background checker stopped")


def get_last_check_info() -> Optional[dict]:
    """Get information about the last RSS check."""
    global _last_check_time, _last_check_result
    
    if _last_check_time is None:
        return None
    
    return {
        'last_check_time': _last_check_time.isoformat(),
        'last_check_result': _last_check_result,
        'next_check_in': _get_next_check_time().isoformat() if _checker_running else None,
        'is_running': _checker_running
    }


def _get_next_check_time() -> datetime:
    """Calculate when the next check will happen."""
    global _last_check_time
    
    if _last_check_time is None:
        return datetime.now() + timedelta(seconds=CHECK_INTERVAL)
    
    return _last_check_time + timedelta(seconds=CHECK_INTERVAL)


def is_running() -> bool:
    """Check if the background checker is running."""
    return _checker_running
