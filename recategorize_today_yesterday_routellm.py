"""
Script om alle artikelen van vandaag en gisteren opnieuw te categoriseren met RouteLLM.
"""
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import pytz

# Add project root to Python path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Set RouteLLM API key (tijdelijk voor test)
os.environ['ROUTELLM_API_KEY'] = 's2_760166137897436c8b1dc5248b05db5a'

from supabase_client import get_supabase_client
from categorization_engine import categorize_article

def recategorize_today_yesterday_with_routellm():
    """Recategoriseer alle artikelen van vandaag en gisteren met RouteLLM."""
    print("=" * 60)
    print("ROUTELLM RECATEGORISATIE - VANDAAG EN GISTEREN")
    print("=" * 60)
    
    # Check if RouteLLM API key is available
    routellm_api_key = os.getenv('ROUTELLM_API_KEY')
    if not routellm_api_key:
        print("[ERROR] ROUTELLM_API_KEY niet gevonden!")
        return
    
    print(f"[INFO] RouteLLM API key gevonden: {routellm_api_key[:10]}...")
    
    # Get timezone (Amsterdam)
    amsterdam_tz = pytz.timezone('Europe/Amsterdam')
    now = datetime.now(amsterdam_tz)
    
    # Calculate start of yesterday (00:00:00)
    yesterday_start = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    # Calculate end of today (23:59:59)
    today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    print(f"[INFO] Periode: {yesterday_start.strftime('%Y-%m-%d %H:%M')} - {today_end.strftime('%Y-%m-%d %H:%M')} (Amsterdam tijd)")
    print(f"[INFO] Haal artikelen op...\n")
    
    supabase = get_supabase_client()
    
    try:
        # Get all articles from yesterday and today
        # Convert to UTC for database query
        yesterday_start_utc = yesterday_start.astimezone(pytz.UTC)
        today_end_utc = today_end.astimezone(pytz.UTC)
        
        # Query articles from yesterday and today
        response = supabase.client.table('articles').select('*').gte('published_at', yesterday_start_utc.isoformat()).lte('published_at', today_end_utc.isoformat()).order('published_at', desc=True).execute()
        
        articles = response.data if hasattr(response, 'data') else []
        
        if not articles:
            print("[WARN] Geen artikelen gevonden voor vandaag en gisteren.")
            return
        
        print(f"[INFO] {len(articles)} artikelen gevonden. Start recategorisatie met RouteLLM...\n")
        
        updated_count = 0
        error_count = 0
        skipped_count = 0
        
        for i, article in enumerate(articles, 1):
            try:
                article_id = article.get('id')
                title = article.get('title', '')
                description = article.get('description', '')
                content = article.get('full_content', '')
                rss_feed_url = article.get('rss_feed_url')
                published_at = article.get('published_at', '')
                
                if not article_id or not title:
                    print(f"  [{i}] [SKIP] Artikel zonder ID of titel")
                    skipped_count += 1
                    continue
                
                # Format published date for display
                try:
                    pub_date = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                    pub_date_ams = pub_date.astimezone(amsterdam_tz)
                    date_str = pub_date_ams.strftime('%Y-%m-%d %H:%M')
                except:
                    date_str = published_at[:10] if published_at else 'Onbekend'
                
                print(f"  [{i}/{len(articles)}] [{date_str}] {title[:60]}...")
                
                # Categorize with RouteLLM
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
                        llm = result.get('llm', 'RouteLLM')
                        
                        # Check if RouteLLM was actually used
                        if llm != 'RouteLLM':
                            print(f"       [WARN] Gebruikt {llm} in plaats van RouteLLM")
                        
                        # Only update if we got a valid result
                        if main_category or categories:
                            update_data = {
                                'categories': categories or [main_category or 'Algemeen'],
                                'categorization_llm': llm,
                                'updated_at': datetime.now(pytz.UTC).isoformat()
                            }
                            
                            supabase.client.table('articles').update(update_data).eq('id', article_id).execute()
                            updated_count += 1
                            
                            category_display = main_category or (categories[0] if categories else 'Geen')
                            print(f"       [OK] {category_display}", end='')
                            if sub_categories:
                                print(f" (sub: {', '.join(sub_categories)})", end='')
                            print()
                        else:
                            print(f"       [WARN] Geen categorieen gekregen van LLM")
                            error_count += 1
                    else:
                        print(f"       [WARN] Ongeldig resultaat van categorisatie")
                        error_count += 1
                        
                except Exception as llm_error:
                    print(f"       [ERROR] LLM categorisatie mislukt: {llm_error}")
                    error_count += 1
                    continue
                    
            except Exception as e:
                print(f"  [{i}] [ERROR] Fout bij artikel {article.get('id', 'unknown')}: {e}")
                error_count += 1
                continue
            
            # Progress update every 10 articles
            if i % 10 == 0:
                print(f"\n[PROGRESS] {i}/{len(articles)} artikelen verwerkt ({updated_count} succesvol, {error_count} fouten)\n")
        
        print("\n" + "=" * 60)
        print("RESULTAAT")
        print("=" * 60)
        print(f"  [OK] {updated_count} artikelen succesvol gerecategoriseerd")
        if error_count > 0:
            print(f"  [WARN] {error_count} artikelen hadden fouten")
        if skipped_count > 0:
            print(f"  [SKIP] {skipped_count} artikelen overgeslagen")
        print(f"  [TOTAAL] {len(articles)} artikelen verwerkt")
        print("=" * 60)
        
    except Exception as e:
        print(f"[ERROR] Fout bij recategorisatie: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    recategorize_today_yesterday_with_routellm()
