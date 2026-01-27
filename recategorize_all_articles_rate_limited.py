"""
Script to recategorize all articles in Supabase with rate limiting.
Processes 2 articles per minute (1 every 30 seconds).
Stops after 5 consecutive minutes with only LLM errors.
"""
import time
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Load environment variables from .env file (for local development)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv not installed, will use environment variables directly
    pass

# Import required modules
try:
    from supabase_client import SupabaseClient
    from categorization_engine import categorize_article
except ImportError as e:
    print(f"Error importing modules: {e}")
    sys.exit(1)


def get_all_articles(supabase) -> List[Dict[str, Any]]:
    """Get all articles from Supabase without limit (bypasses 72-hour restriction)."""
    try:
        all_articles = []
        offset = 0
        batch_size = 100  # Fetch in batches of 100
        
        while True:
            # Query directly from Supabase client to bypass 72-hour restriction
            response = supabase.client.table('articles').select('*').order('published_at', desc=True).limit(batch_size).offset(offset).execute()
            
            articles = response.data if response.data else []
            
            if not articles or len(articles) == 0:
                break
            
            all_articles.extend(articles)
            offset += batch_size
            
            # If we got fewer than batch_size, we've reached the end
            if len(articles) < batch_size:
                break
        
        return all_articles
    except Exception as e:
        print(f"Error getting articles: {e}")
        import traceback
        traceback.print_exc()
        return []


def update_article_categories(supabase, article_id: str, categorization_result: Dict[str, Any]) -> bool:
    """Update article with new categorization (main_category, sub_categories, categories)."""
    try:
        from datetime import datetime
        import pytz
        
        main_category = categorization_result.get('main_category')
        sub_categories = categorization_result.get('sub_categories', [])
        categories = categorization_result.get('categories', [])
        categorization_llm = categorization_result.get('llm', 'Unknown')
        categorization_argumentation = categorization_result.get('categorization_argumentation', '')
        
        # Build update data
        update_data = {
            'main_category': main_category,
            'sub_categories': sub_categories,
            'categories': categories,
            'categorization_llm': categorization_llm,
            'updated_at': datetime.now(pytz.UTC).isoformat()
        }
        
        # Add categorization_argumentation if available
        if categorization_argumentation:
            update_data['categorization_argumentation'] = categorization_argumentation
        
        # Update article
        supabase.client.table('articles').update(update_data).eq('id', article_id).execute()
        return True
    except Exception as e:
        print(f"Error updating article categories: {e}")
        return False


def recategorize_all_articles():
    """Recategorize all articles with rate limiting (2 per minute)."""
    print("=" * 80)
    print("HERCATEGORISATIE VAN ALLE ARTIKELEN")
    print("=" * 80)
    print(f"Start tijd: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Initialize Supabase client (direct, without Streamlit)
    try:
        supabase = SupabaseClient()
    except Exception as e:
        print(f"ERROR: Fout bij initialiseren Supabase client: {e}")
        return
    
    # Get all articles
    print("Artikelen ophalen uit Supabase...")
    all_articles = get_all_articles(supabase)
    total_articles = len(all_articles)
    
    if total_articles == 0:
        print("ERROR: Geen artikelen gevonden in Supabase.")
        return
    
    print(f"OK: {total_articles} artikelen gevonden.")
    print()
    print("Start hercategorisatie...")
    print(f"   Rate limit: 2 artikelen per minuut (1 elke 30 seconden)")
    print()
    
    # Statistics
    success_count = 0
    error_count = 0
    skipped_count = 0
    
    # Track consecutive error minutes
    consecutive_error_minutes = 0
    last_error_minute = None
    errors_in_current_minute = 0
    successes_in_current_minute = 0
    
    # Process each article
    for idx, article in enumerate(all_articles, 1):
        article_id = article.get('id')
        title = article.get('title', 'Geen titel')[:60]
        stable_id = article.get('stable_id', 'Onbekend')[:12]
        
        if not article_id:
            print(f"[{idx}/{total_articles}] WARNING: SKIP: Artikel zonder ID")
            skipped_count += 1
            continue
        
        # Rate limiting: wait 30 seconds between articles (2 per minute)
        if idx > 1:  # Don't wait before first article
            print(f"   Wachten 30 seconden...")
            time.sleep(30)
        
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        current_minute = datetime.now().replace(second=0, microsecond=0)
        
        # Reset counters if we're in a new minute
        if last_error_minute is not None and current_minute != last_error_minute:
            # Check if previous minute had only errors
            if errors_in_current_minute > 0 and successes_in_current_minute == 0:
                consecutive_error_minutes += 1
            else:
                consecutive_error_minutes = 0
            errors_in_current_minute = 0
            successes_in_current_minute = 0
        
        print(f"[{idx}/{total_articles}] {current_time}")
        print(f"   Artikel: {title}...")
        print(f"   ID: {stable_id}...")
        
        # Get article data for categorization
        article_title = article.get('title', '')
        article_description = article.get('description', '') or article.get('summary', '')
        article_content = article.get('full_content', '') or article_description
        rss_feed_url = article.get('rss_feed_url')
        
        # Categorize article
        try:
            categorization_result = categorize_article(
                title=article_title,
                description=article_description,
                content=article_content[:3000],  # Limit content length
                rss_feed_url=rss_feed_url
            )
            
            # Check if categorization was successful
            main_category = categorization_result.get('main_category')
            llm_used = categorization_result.get('llm', 'Unknown')
            
            if main_category and llm_used and llm_used != 'LLM-Failed':
                # Update article in Supabase
                if update_article_categories(supabase, article_id, categorization_result):
                    print(f"   SUCCESS: {main_category} (LLM: {llm_used})")
                    success_count += 1
                    successes_in_current_minute += 1
                else:
                    print(f"   ERROR: Categorisatie gelukt maar update mislukt")
                    error_count += 1
                    errors_in_current_minute += 1
            else:
                print(f"   ERROR: LLM categorisatie mislukt (LLM: {llm_used})")
                error_count += 1
                errors_in_current_minute += 1
                    
        except Exception as e:
            print(f"   ERROR: Exception tijdens categorisatie: {e}")
            error_count += 1
            errors_in_current_minute += 1
        
        print()
        
        # Update last_error_minute
        last_error_minute = current_minute
        
        # Check if we should stop (5 consecutive minutes with only errors)
        if consecutive_error_minutes >= 5:
            print("=" * 80)
            print("WARNING: STOPPING: 5 opeenvolgende minuten met alleen foutmeldingen van LLM")
            print("=" * 80)
            break
    
    # Final statistics
    print("=" * 80)
    print("HERCATEGORISATIE VOLTOOID")
    print("=" * 80)
    print(f"Eind tijd: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print(f"Statistieken:")
    print(f"   Totaal artikelen: {total_articles}")
    print(f"   Succesvol: {success_count}")
    print(f"   Fouten: {error_count}")
    print(f"   Overgeslagen: {skipped_count}")
    print(f"   Verwerkt: {success_count + error_count + skipped_count}")
    print()


if __name__ == "__main__":
    try:
        recategorize_all_articles()
    except KeyboardInterrupt:
        print("\n\nWARNING: Script gestopt door gebruiker (Ctrl+C)")
    except Exception as e:
        print(f"\n\nERROR: Onverwachte fout: {e}")
        import traceback
        traceback.print_exc()
