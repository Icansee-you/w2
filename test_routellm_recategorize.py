"""
Script om de nieuwste 10 artikelen opnieuw te categoriseren met RouteLLM.
"""
import sys
import os
from pathlib import Path
from datetime import datetime
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

def recategorize_latest_articles_with_routellm(limit: int = 10):
    """Recategoriseer de nieuwste artikelen met RouteLLM."""
    print("=" * 60)
    print("ROUTELLM RECATEGORISATIE - NIEUWSTE ARTIKELEN")
    print("=" * 60)
    
    # Check if RouteLLM API key is available
    routellm_api_key = os.getenv('ROUTELLM_API_KEY')
    if not routellm_api_key:
        print("[ERROR] ROUTELLM_API_KEY niet gevonden!")
        return
    
    print(f"[INFO] RouteLLM API key gevonden: {routellm_api_key[:10]}...")
    print(f"[INFO] Haal {limit} nieuwste artikelen op...\n")
    
    supabase = get_supabase_client()
    
    try:
        # Get latest articles
        articles = supabase.get_articles(limit=limit)
        
        if not articles:
            print("[WARN] Geen artikelen gevonden.")
            return
        
        print(f"[INFO] {len(articles)} artikelen gevonden. Start recategorisatie met RouteLLM...\n")
        
        updated_count = 0
        error_count = 0
        
        for i, article in enumerate(articles, 1):
            try:
                article_id = article.get('id')
                title = article.get('title', '')
                description = article.get('description', '')
                content = article.get('full_content', '')
                rss_feed_url = article.get('rss_feed_url')
                
                if not article_id or not title:
                    print(f"  [{i}] [SKIP] Artikel zonder ID of titel")
                    continue
                
                print(f"  [{i}] Categoriseren: {title[:60]}...")
                
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
                            
                            print(f"       [OK] Categorie: {main_category or categories[0] if categories else 'Geen'}")
                            if sub_categories:
                                print(f"              Sub: {', '.join(sub_categories)}")
                            if argumentation:
                                print(f"              Arg: {argumentation[:80]}...")
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
        
        print("\n" + "=" * 60)
        print("RESULTAAT")
        print("=" * 60)
        print(f"  [OK] {updated_count} artikelen succesvol gerecategoriseerd")
        if error_count > 0:
            print(f"  [WARN] {error_count} artikelen hadden fouten")
        print("=" * 60)
        
    except Exception as e:
        print(f"[ERROR] Fout bij recategorisatie: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    recategorize_latest_articles_with_routellm(limit=10)
