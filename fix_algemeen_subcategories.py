"""
Script to fix articles that have "Algemeen" as a sub_category.
Removes "Algemeen" from sub_categories and updates the articles in Supabase.
"""
import sys
import os
from datetime import datetime

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Import required modules
try:
    from supabase_client import SupabaseClient
except ImportError as e:
    print(f"Error importing modules: {e}")
    sys.exit(1)


def fix_algemeen_subcategories():
    """Fix articles that have 'Algemeen' as a sub_category."""
    print("=" * 80)
    print("CORRIGEER ARTIKELEN MET 'ALGEMEEN' ALS SUB_CATEGORIE")
    print("=" * 80)
    print(f"Start tijd: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Initialize Supabase client
    try:
        supabase = SupabaseClient()
    except Exception as e:
        print(f"ERROR: Fout bij initialiseren Supabase client: {e}")
        return
    
    # Get all articles
    print("Ophalen alle artikelen...")
    all_articles = []
    offset = 0
    batch_size = 100
    
    while True:
        response = supabase.client.table('articles').select('id, main_category, sub_categories, title').limit(batch_size).offset(offset).execute()
        articles = response.data if response.data else []
        
        if not articles or len(articles) == 0:
            break
        
        all_articles.extend(articles)
        offset += batch_size
        
        if len(articles) < batch_size:
            break
    
    print(f"Totaal artikelen gevonden: {len(all_articles)}")
    print()
    
    # Find articles with "Algemeen" in sub_categories
    articles_to_fix = []
    
    for article in all_articles:
        sub_categories = article.get('sub_categories', [])
        main_category = article.get('main_category')
        
        if isinstance(sub_categories, list) and 'Algemeen' in sub_categories:
            articles_to_fix.append(article)
        elif main_category == 'Algemeen' and sub_categories and len(sub_categories) > 0:
            # Also fix articles where main_category is "Algemeen" but has sub_categories
            articles_to_fix.append(article)
    
    print(f"Artikelen gevonden met 'Algemeen' als sub_categorie: {len(articles_to_fix)}")
    print()
    
    if len(articles_to_fix) == 0:
        print("Geen artikelen gevonden die gecorrigeerd moeten worden.")
        return
    
    # Fix articles
    fixed_count = 0
    error_count = 0
    
    for article in articles_to_fix:
        article_id = article.get('id')
        title = article.get('title', '')[:60]
        main_category = article.get('main_category')
        sub_categories = article.get('sub_categories', [])
        
        if not isinstance(sub_categories, list):
            sub_categories = []
        
        # Remove "Algemeen" from sub_categories
        if 'Algemeen' in sub_categories:
            sub_categories = [c for c in sub_categories if c != 'Algemeen']
        
        # If main_category is "Algemeen", ensure sub_categories is empty
        if main_category == 'Algemeen':
            sub_categories = []
        
        # Rebuild categories list
        categories = []
        if main_category:
            categories.append(main_category)
        categories.extend([c for c in sub_categories if c != main_category])
        categories = list(dict.fromkeys(categories))  # Remove duplicates
        
        # Update article
        try:
            import pytz
            
            update_data = {
                'sub_categories': sub_categories,
                'categories': categories,
                'updated_at': datetime.now(pytz.UTC).isoformat()
            }
            
            supabase.client.table('articles').update(update_data).eq('id', article_id).execute()
            fixed_count += 1
            print(f"  [{fixed_count}/{len(articles_to_fix)}] OK: {title}...")
        except Exception as e:
            error_count += 1
            print(f"  ERROR: {title}... - {e}")
    
    print()
    print("=" * 80)
    print("CORRECTIE VOLTOOID")
    print("=" * 80)
    print(f"Eind tijd: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print(f"Statistieken:")
    print(f"   Gevonden artikelen: {len(articles_to_fix)}")
    print(f"   Gecorrigeerd: {fixed_count}")
    print(f"   Fouten: {error_count}")
    print()


if __name__ == "__main__":
    try:
        fix_algemeen_subcategories()
    except KeyboardInterrupt:
        print("\n\nWARNING: Script gestopt door gebruiker (Ctrl+C)")
    except Exception as e:
        print(f"\n\nERROR: Onverwachte fout: {e}")
        import traceback
        traceback.print_exc()
