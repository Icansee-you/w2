"""
Script om alle categorisaties te resetten en artikelen van vandaag opnieuw te categoriseren.
"""
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import pytz

# Add project root to Python path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from supabase_client import get_supabase_client
from categorization_engine import categorize_article
from secrets_helper import get_secret


def reset_all_categories_to_algemeen():
    """Reset alle artikelen naar main_category 'Algemeen'."""
    print("[RESET] Resetten van alle categorisaties naar 'Algemeen'...")
    
    supabase = get_supabase_client()
    
    try:
        # Get all articles
        all_articles = supabase.get_articles(limit=10000)
        
        if not all_articles:
            print("[INFO] Geen artikelen gevonden.")
            return 0
        
        updated_count = 0
        
        for article in all_articles:
            try:
                article_id = article.get('id')
                if not article_id:
                    continue
                
                # Update to "Algemeen"
                # Only update categories field (main_category and sub_categories may not exist in DB)
                update_data = {
                    'categories': ['Algemeen'],
                    'categorization_llm': 'Reset',
                    'updated_at': datetime.now(pytz.UTC).isoformat()
                }
                
                # Use upsert to update
                try:
                    supabase.client.table('articles').update(update_data).eq('id', article_id).execute()
                    updated_count += 1
                    
                    if updated_count % 100 == 0:
                        print(f"  [INFO] {updated_count} artikelen geüpdatet...")
                except Exception as update_error:
                    # Silently continue if update fails (e.g., column doesn't exist)
                    # Only log if it's not a column error
                    error_msg = str(update_error)
                    if 'column' not in error_msg.lower() and 'schema' not in error_msg.lower():
                        print(f"  [WARN] Fout bij updaten artikel {article.get('id', 'unknown')}: {error_msg}")
                    continue
                    
            except Exception as e:
                # Only log non-column errors
                error_msg = str(e)
                if 'column' not in error_msg.lower() and 'schema' not in error_msg.lower():
                    print(f"  [WARN] Fout bij artikel {article.get('id', 'unknown')}: {error_msg}")
                continue
        
        print(f"[OK] {updated_count} artikelen gereset naar 'Algemeen'")
        return updated_count
        
    except Exception as e:
        print(f"[ERROR] Fout bij resetten: {e}")
        return 0


def recategorize_today_articles_with_groq():
    """Recategoriseer artikelen van vandaag met Groq LLM."""
    print("\n[RECAT] Recategoriseren van artikelen van vandaag met Groq LLM...")
    
    # Check if Groq API key is available
    groq_api_key = get_secret('GROQ_API_KEY')
    if not groq_api_key:
        print("[WARN] Groq API key niet gevonden. Skipping recategorisatie.")
        return 0
    
    supabase = get_supabase_client()
    
    try:
        # Get today's date in Amsterdam timezone
        amsterdam_tz = pytz.timezone('Europe/Amsterdam')
        today_start = datetime.now(amsterdam_tz).replace(hour=0, minute=0, second=0, microsecond=0)
        today_start_utc = today_start.astimezone(pytz.UTC)
        today_start_str = today_start_utc.isoformat()
        
        print(f"[INFO] Zoeken naar artikelen vanaf: {today_start.strftime('%Y-%m-%d %H:%M:%S')} (Amsterdam tijd)")
        
        # Get articles from today
        # Note: We'll get all recent articles and filter by date in Python
        all_recent_articles = supabase.get_articles(limit=1000)
        
        today_articles = []
        for article in all_recent_articles:
            published_at = article.get('published_at')
            if published_at:
                try:
                    from dateutil import parser
                    pub_date = parser.parse(published_at)
                    if pub_date.tzinfo is None:
                        pub_date = pytz.UTC.localize(pub_date)
                    
                    # Check if article is from today
                    if pub_date >= today_start_utc:
                        today_articles.append(article)
                except Exception:
                    continue
        
        if not today_articles:
            print("[INFO] Geen artikelen van vandaag gevonden.")
            return 0
        
        print(f"[INFO] {len(today_articles)} artikelen van vandaag gevonden. Start categorisatie...")
        
        updated_count = 0
        error_count = 0
        
        for article in today_articles:
            try:
                article_id = article.get('id')
                title = article.get('title', '')
                description = article.get('description', '')
                content = article.get('full_content', '')
                rss_feed_url = article.get('rss_feed_url')
                
                if not article_id or not title:
                    continue
                
                print(f"  [CAT] Categoriseren: {title[:60]}...")
                
                # Categorize with Groq
                try:
                    result = categorize_article(
                        title=title,
                        description=description or '',
                        content=content or '',
                        rss_feed_url=rss_feed_url
                    )
                    
                    if result and isinstance(result, dict):
                        main_category = result.get('main_category')
                        sub_categories = result.get('sub_categories', [])
                        categories = result.get('categories', [])
                        argumentation = result.get('categorization_argumentation', '')
                        llm = result.get('llm', 'Groq')
                        
                        # Only update if we got a valid result
                        if main_category or categories:
                            # Use categories list (main_category/sub_categories may not exist in DB)
                            final_categories = categories or [main_category or 'Algemeen']
                            
                            update_data = {
                                'categories': final_categories,
                                'categorization_llm': llm,
                                'updated_at': datetime.now(pytz.UTC).isoformat()
                            }
                            
                            supabase.client.table('articles').update(update_data).eq('id', article_id).execute()
                            updated_count += 1
                            print(f"    [OK] Categorie: {main_category or final_categories}")
                        else:
                            print(f"    [WARN] Geen categorieen gekregen van LLM")
                            error_count += 1
                    else:
                        print(f"    [WARN] Ongeldig resultaat van categorisatie")
                        error_count += 1
                        
                except Exception as llm_error:
                    print(f"    [ERROR] LLM categorisatie mislukt: {llm_error}")
                    error_count += 1
                    continue
                    
            except Exception as e:
                print(f"  [WARN] Fout bij artikel {article.get('id', 'unknown')}: {e}")
                error_count += 1
                continue
        
        print(f"\n[OK] {updated_count} artikelen succesvol gerecategoriseerd")
        if error_count > 0:
            print(f"[WARN] {error_count} artikelen hadden fouten")
        
        return updated_count
        
    except Exception as e:
        print(f"[ERROR] Fout bij recategorisatie: {e}")
        import traceback
        traceback.print_exc()
        return 0


def main():
    """Main function."""
    print("=" * 60)
    print("CATEGORISATIE RESET EN RECATEGORISATIE")
    print("=" * 60)
    
    # Step 1: Reset all categories
    reset_count = reset_all_categories_to_algemeen()
    
    if reset_count == 0:
        print("\n[WARN] Geen artikelen gereset. Stoppen.")
        return
    
    # Step 2: Recategorize today's articles
    recat_count = recategorize_today_articles_with_groq()
    
    print("\n" + "=" * 60)
    print("KLAAR")
    print(f"  - {reset_count} artikelen gereset naar 'Algemeen'")
    print(f"  - {recat_count} artikelen van vandaag gerecategoriseerd")
    print("=" * 60)


if __name__ == "__main__":
    main()
