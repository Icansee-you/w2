"""
Script to recategorize all existing articles using LLM.
This will update categories and categorization_llm for all articles.
"""
import os
import sys
from typing import List, Dict, Any

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from supabase_client import get_supabase_client
from categorization_engine import categorize_article


def recategorize_all_articles(limit: int = None, use_llm: bool = True):
    """
    Recategorize all articles in the database.
    
    Args:
        limit: Maximum number of articles to recategorize (None for all)
        use_llm: Whether to use LLM categorization (True) or keywords (False)
    """
    print("=" * 60)
    print("RECATEGORIZING ALL ARTICLES")
    print("=" * 60)
    
    # Get storage client
    storage = get_supabase_client()
    if not storage:
        print("ERROR: Could not initialize storage client")
        return
    
    print(f"\nFetching articles...")
    
    # Get all articles (without limit first to see how many there are)
    try:
        all_articles = storage.get_articles(limit=1000)  # Get up to 1000 articles
        total_count = len(all_articles)
        
        if limit:
            all_articles = all_articles[:limit]
            print(f"Processing {len(all_articles)} of {total_count} articles (limited)")
        else:
            print(f"Processing {len(all_articles)} articles")
        
        if not all_articles:
            print("No articles found to recategorize")
            return
        
        print(f"\nUsing {'LLM' if use_llm else 'keyword-based'} categorization")
        print("-" * 60)
        
        success_count = 0
        error_count = 0
        
        for idx, article in enumerate(all_articles, 1):
            article_id = article.get('id')
            title = article.get('title', '')
            
            print(f"\n[{idx}/{len(all_articles)}] Processing: {title[:60]}...")
            
            try:
                # Get article content
                description = article.get('description', '')
                content = article.get('full_content', '')
                
                # Recategorize
                if use_llm:
                    result = categorize_article(title, description, content)
                    if isinstance(result, dict):
                        new_categories = result.get('categories', [])
                        categorization_llm = result.get('llm', 'Keywords')
                    else:
                        # Backward compatibility
                        new_categories = result if isinstance(result, list) else []
                        categorization_llm = 'Keywords'
                else:
                    from categorization_engine import _categorize_with_keywords
                    new_categories = _categorize_with_keywords(title, description, content)
                    categorization_llm = 'Keywords'
                
                # Update article
                update_data = {
                    'categories': new_categories,
                    'categorization_llm': categorization_llm
                }
                
                # Use upsert to update
                article_data = article.copy()
                article_data.update(update_data)
                
                if storage.upsert_article(article_data):
                    print(f"  ✓ Updated: {len(new_categories)} categories, LLM: {categorization_llm}")
                    success_count += 1
                else:
                    print(f"  ✗ Failed to update article")
                    error_count += 1
                    
            except Exception as e:
                print(f"  ✗ Error: {str(e)}")
                error_count += 1
                continue
        
        print("\n" + "=" * 60)
        print("RECATEGORIZATION COMPLETE")
        print("=" * 60)
        print(f"Success: {success_count}")
        print(f"Errors: {error_count}")
        print(f"Total: {len(all_articles)}")
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Recategorize all articles")
    parser.add_argument("--limit", type=int, default=None, help="Maximum number of articles to process")
    parser.add_argument("--keywords", action="store_true", help="Use keyword-based categorization instead of LLM")
    
    args = parser.parse_args()
    
    recategorize_all_articles(limit=args.limit, use_llm=not args.keywords)

