"""
Background scheduler for automatically fetching RSS feeds every 15 minutes.
Runs independently of user interactions.
"""
import os
import time
import threading
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from articles_repository import fetch_and_upsert_articles

# File to store last fetch time (persists across app restarts)
LAST_FETCH_FILE = Path(__file__).parent / ".last_fetch_time"


def get_last_fetch_time() -> float:
    """Get the last fetch time from file."""
    try:
        if LAST_FETCH_FILE.exists():
            with open(LAST_FETCH_FILE, 'r') as f:
                data = json.load(f)
                return data.get('last_fetch_time', 0)
    except Exception:
        pass
    return 0


def set_last_fetch_time(timestamp: float):
    """Save the last fetch time to file."""
    try:
        with open(LAST_FETCH_FILE, 'w') as f:
            json.dump({'last_fetch_time': timestamp}, f)
    except Exception:
        pass


def fetch_articles_background():
    """Fetch articles from RSS feeds in the background."""
    try:
        feed_urls = [
            'https://feeds.nos.nl/nosnieuwsalgemeen',
            'https://feeds.nos.nl/nosnieuwsbinnenland',
            'https://feeds.nos.nl/nosnieuwsbuitenland',
        ]
        
        total_inserted = 0
        total_updated = 0
        
        for feed_url in feed_urls:
            try:
                # Use LLM categorization for better accuracy
                result = fetch_and_upsert_articles(feed_url, max_items=30, use_llm_categorization=True)
                if result.get('success'):
                    total_inserted += result.get('inserted', 0)
                    total_updated += result.get('updated', 0)
            except Exception as e:
                # Silently log errors but continue
                print(f"Background fetch error for {feed_url}: {e}")
                pass
        
        # Update last fetch time
        set_last_fetch_time(time.time())
        
        if total_inserted > 0 or total_updated > 0:
            print(f"[Background] Fetched {total_inserted} new articles, {total_updated} updated")
        
    except Exception as e:
        print(f"[Background] Error fetching articles: {e}")


def background_scheduler_worker():
    """Background worker that runs every 15 minutes."""
    # Wait a bit on startup before first fetch
    time.sleep(30)
    
    while True:
        try:
            current_time = time.time()
            last_fetch = get_last_fetch_time()
            
            # Check if 15 minutes (900 seconds) have passed
            time_since_last_fetch = current_time - last_fetch
            
            if last_fetch == 0 or time_since_last_fetch >= 900:  # 15 minutes
                print(f"[Background] Starting RSS feed check...")
                fetch_articles_background()
            else:
                # Calculate time until next fetch
                time_until_next = 900 - time_since_last_fetch
                print(f"[Background] Next fetch in {int(time_until_next / 60)} minutes")
            
            # Sleep for 5 minutes, then check again
            time.sleep(300)  # 5 minutes
            
        except Exception as e:
            print(f"[Background] Scheduler error: {e}")
            time.sleep(60)  # Wait 1 minute before retrying


# Global thread variable
_scheduler_thread = None
_scheduler_running = False


def start_background_scheduler():
    """Start the background scheduler thread."""
    global _scheduler_thread, _scheduler_running
    
    if _scheduler_running:
        return  # Already running
    
    try:
        _scheduler_thread = threading.Thread(
            target=background_scheduler_worker,
            daemon=True,  # Dies when main thread dies
            name="RSSBackgroundScheduler"
        )
        _scheduler_thread.start()
        _scheduler_running = True
        print("[Background] RSS feed scheduler started (checks every 15 minutes)")
    except Exception as e:
        print(f"[Background] Failed to start scheduler: {e}")


def is_scheduler_running() -> bool:
    """Check if the background scheduler is running."""
    global _scheduler_thread, _scheduler_running
    if _scheduler_thread and _scheduler_thread.is_alive():
        return True
    _scheduler_running = False
    return False

