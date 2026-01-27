"""
Script om LLM-Failed artikelen te herstellen vanuit de categories (text) kolom.
"""
import sys
import os
from typing import List, Dict, Any
import json

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


def parse_categories_text(categories_text: str) -> List[str]:
    """Parse categories text (can be JSON string or comma-separated) into list."""
    if not categories_text:
        return []
    
    # Try JSON first
    try:
        parsed = json.loads(categories_text)
        if isinstance(parsed, list):
            return parsed
    except:
        pass
    
    # Try comma-separated
    if ',' in categories_text:
        categories = [c.strip().strip('"\'[]') for c in categories_text.split(',')]
        return [c for c in categories if c]
    
    # Single category
    return [categories_text.strip()] if categories_text.strip() else []


def restore_llm_failed_articles():
    """Herstel LLM-Failed artikelen vanuit de categories kolom."""
    print("=" * 80)
    print("HERSTEL LLM-FAILED ARTIKELEN")
    print("=" * 80)
    print()
    
    # Initialize Supabase client
    try:
        supabase = SupabaseClient()
    except Exception as e:
        print(f"ERROR: Fout bij initialiseren Supabase client: {e}")
        return
    
    # Get all articles with LLM-Failed
    print("Stap 1: Ophalen artikelen met LLM-Failed...")
    try:
        # Get all articles with categorization_llm = 'LLM-Failed'
        all_articles = []
        offset = 0
        batch_size = 100
        
        while True:
            response = supabase.client.table('articles').select(
                'id, stable_id, title, categories, main_category, sub_categories, categorization_llm'
            ).eq('categorization_llm', 'LLM-Failed').limit(batch_size).offset(offset).execute()
            
            articles = response.data if response.data else []
            if not articles or len(articles) == 0:
                break
            
            all_articles.extend(articles)
            offset += batch_size
            
            if len(articles) < batch_size:
                break
        
        print(f"  Gevonden: {len(all_articles)} artikelen met LLM-Failed")
        print()
        
        if len(all_articles) == 0:
            print("Geen artikelen gevonden met LLM-Failed.")
            return
        
        # Process each article
        restored_count = 0
        skipped_count = 0
        error_count = 0
        
        print("Stap 2: Herstellen artikelen...")
        print()
        
        for article in all_articles:
            article_id = article.get('id')
            stable_id = article.get('stable_id', '')
            title = article.get('title', '')[:60]
            categories_text = article.get('categories')
            
            # Parse categories from text
            categories = []
            if isinstance(categories_text, str):
                categories = parse_categories_text(categories_text)
            elif isinstance(categories_text, list):
                categories = categories_text
            
            # If no categories found, set to Algemeen
            if not categories or len(categories) == 0:
                categories = ['Algemeen']
            
            # Determine main_category and sub_categories
            main_category = categories[0] if categories else 'Algemeen'
            sub_categories = categories[1:] if len(categories) > 1 else []
            
            # Ensure main_category is valid
            from categorization_engine import get_all_categories
            valid_categories = get_all_categories()
            if main_category not in valid_categories:
                main_category = 'Algemeen'
                sub_categories = []
            
            # Remove 'Algemeen' from sub_categories if main_category is 'Algemeen'
            if main_category == 'Algemeen':
                sub_categories = []
            else:
                sub_categories = [c for c in sub_categories if c != 'Algemeen' and c != main_category and c in valid_categories]
            
            # Update article
            try:
                update_data = {
                    'main_category': main_category,
                    'sub_categories': sub_categories,
                    'categorization_llm': 'Restored-From-Categories',
                    'categorization_argumentation': f'Hersteld vanuit categories kolom: {", ".join(categories)}'
                }
                
                # Update in Supabase
                response = supabase.client.table('articles').update(update_data).eq('id', article_id).execute()
                
                if response.data:
                    restored_count += 1
                    print(f"  OK {title}... -> {main_category}" + (f" + {len(sub_categories)} sub" if sub_categories else ""))
                else:
                    skipped_count += 1
                    print(f"  X {title}... -> Update mislukt")
                    
            except Exception as e:
                error_count += 1
                print(f"  X {title}... -> Fout: {e}")
        
        print()
        print("=" * 80)
        print("RESULTATEN")
        print("=" * 80)
        print(f"Hersteld: {restored_count}")
        print(f"Overgeslagen: {skipped_count}")
        print(f"Fouten: {error_count}")
        print(f"Totaal: {len(all_articles)}")
        print()
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    try:
        restore_llm_failed_articles()
    except KeyboardInterrupt:
        print("\n\nWARNING: Script gestopt door gebruiker (Ctrl+C)")
    except Exception as e:
        print(f"\n\nERROR: Onverwachte fout: {e}")
        import traceback
        traceback.print_exc()
