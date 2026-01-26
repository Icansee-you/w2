"""
Script om de categorisatie van het meest recente artikel te repareren met RouteLLM.
"""
import sys
import os
from pathlib import Path

# Add project root to Python path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Set RouteLLM API key
os.environ['ROUTELLM_API_KEY'] = 's2_760166137897436c8b1dc5248b05db5a'

from supabase_client import get_supabase_client
from categorization_engine import categorize_article

def fix_latest_article():
    """Repareer de categorisatie van het meest recente artikel."""
    print("=" * 80)
    print("REPARATIE MEEST RECENTE ARTIKEL CATEGORISATIE")
    print("=" * 80)
    
    supabase = get_supabase_client()
    
    try:
        # Haal het meest recente artikel op
        print("\n[INFO] Haal meest recente artikel op...")
        articles = supabase.get_articles(limit=1)
        
        if not articles:
            print("[WARN] Geen artikelen gevonden")
            return
        
        article = articles[0]
        article_id = article.get('id')
        title = article.get('title', '')
        description = article.get('description', '')
        content = article.get('full_content', '')
        rss_feed_url = article.get('rss_feed_url', '')
        current_llm = article.get('categorization_llm', 'Unknown')
        current_category = article.get('main_category') or article.get('category', 'Unknown')
        
        print(f"\n[INFO] Meest recente artikel:")
        print(f"  ID: {article_id}")
        print(f"  Titel: {title[:80]}...")
        print(f"  Huidige categorie: {current_category}")
        print(f"  Huidige LLM: {current_llm}")
        print(f"  RSS Feed: {rss_feed_url}")
        
        # Categoriseer opnieuw met RouteLLM
        print(f"\n[INFO] Categoriseer opnieuw met RouteLLM...")
        try:
            categorization_result = categorize_article(
                title, 
                description, 
                content or '', 
                rss_feed_url=rss_feed_url
            )
            
            if isinstance(categorization_result, dict):
                main_category = categorization_result.get('main_category')
                sub_categories = categorization_result.get('sub_categories', [])
                categories = categorization_result.get('categories', [])
                argumentation = categorization_result.get('categorization_argumentation', '')
                llm = categorization_result.get('llm', 'Unknown')
                
                print(f"\n[RESULTAAT]")
                print(f"  Main Category: {main_category}")
                print(f"  Sub Categories: {sub_categories}")
                print(f"  Categories: {categories}")
                print(f"  LLM: {llm}")
                print(f"  Argumentatie: {argumentation[:100]}...")
                
                if llm in ['Keywords', 'Keywords-Fallback', 'Keywords-Error']:
                    print(f"\n[ERROR] LLM categorisatie faalde - gebruikt nog steeds keywords!")
                    return
                
                # Update artikel in database
                print(f"\n[INFO] Update artikel in database...")
                try:
                    # Combine main_category and sub_categories into categories list
                    all_categories = [main_category] if main_category else []
                    if sub_categories:
                        all_categories.extend([c for c in sub_categories if c != main_category])
                    all_categories = list(dict.fromkeys(all_categories))  # Remove duplicates
                    
                    # Only include fields that exist in the database
                    update_data = {
                        'categories': all_categories,
                        'categorization_llm': llm,
                        'category': main_category or 'Algemeen'  # Legacy field
                    }
                    
                    # Try to add main_category and sub_categories if they exist in the schema
                    # (These might not exist in all database versions)
                    try:
                        # Test if main_category exists by checking the article
                        if 'main_category' in article:
                            update_data['main_category'] = main_category
                        if 'sub_categories' in article:
                            update_data['sub_categories'] = sub_categories
                        if 'categorization_argumentation' in article:
                            update_data['categorization_argumentation'] = argumentation
                    except:
                        pass  # Skip if fields don't exist
                    
                    # Update via Supabase
                    supabase.client.table('articles').update(update_data).eq('id', article_id).execute()
                    
                    print(f"\n[OK] Artikel succesvol bijgewerkt!")
                    print(f"  Nieuwe categorie: {main_category}")
                    print(f"  Nieuwe LLM: {llm}")
                    
                except Exception as update_error:
                    print(f"\n[ERROR] Fout bij updaten artikel: {update_error}")
                    import traceback
                    traceback.print_exc()
            else:
                print(f"\n[ERROR] Onverwacht resultaat van categorisatie: {categorization_result}")
                
        except Exception as cat_error:
            print(f"\n[ERROR] Fout bij categorisatie: {cat_error}")
            import traceback
            traceback.print_exc()
            
    except Exception as e:
        print(f"\n[ERROR] Fout bij ophalen artikel: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    fix_latest_article()
