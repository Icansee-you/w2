"""
Repository for article operations with Supabase.
Handles fetching from RSS, upserting to Supabase, and querying.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
import hashlib
import sys

# Workaround for Python 3.13: cgi module was removed
# Patch cgi module before feedparser tries to import it
try:
    import cgi
except ImportError:
    # Python 3.13+ - cgi module was removed
    try:
        import legacy_cgi as cgi
        sys.modules['cgi'] = cgi
    except ImportError:
        # If legacy-cgi is not available, create a minimal cgi module stub
        from types import ModuleType
        cgi = ModuleType('cgi')
        sys.modules['cgi'] = cgi
        # Add minimal functions that feedparser might need
        def parse_header(value):
            return value.split(';', 1)[0].strip(), {}
        cgi.parse_header = parse_header

import feedparser
from supabase_client import get_supabase_client
from nlp_utils import generate_eli5_summary_nl
from categorization_engine import categorize_article


def generate_stable_id(link: str, published_at: Optional[datetime] = None) -> str:
    """Generate a stable unique identifier for an article."""
    # Use link + published_at as stable identifier
    if published_at:
        stable_string = f"{link}|{published_at.isoformat()}"
    else:
        stable_string = link
    
    # Create hash for stable ID
    return hashlib.md5(stable_string.encode()).hexdigest()


def parse_feed_entry(entry: Dict[str, Any], use_llm_categorization: bool = True, rss_feed_url: str = None) -> Dict[str, Any]:
    """Parse a feedparser entry into article data structure."""
    # Extract published date
    published_at = None
    if hasattr(entry, 'published_parsed') and entry.published_parsed:
        try:
            from datetime import datetime
            import time
            published_at = datetime(*entry.published_parsed[:6])
        except Exception:
            pass
    
    if not published_at and hasattr(entry, 'published'):
        try:
            from dateutil import parser
            published_at = parser.parse(entry.published)
        except Exception:
            pass
    
    # Extract image URL
    image_url = None
    if hasattr(entry, 'media_content') and entry.media_content:
        image_url = entry.media_content[0].get('url')
    elif hasattr(entry, 'links'):
        for link in entry.links:
            if link.get('type', '').startswith('image'):
                image_url = link.get('href')
                break
    
    stable_id = generate_stable_id(entry.get('link', ''), published_at)
    
    # Get title, description, and content for categorization
    title = entry.get('title', '')[:500]
    description = entry.get('description') or entry.get('summary', '')[:2000]
    content = entry.get('content', [{}])[0].get('value', '')[:10000] if entry.get('content') else None
    
    # Categorize article - ALWAYS use LLM categorization (RouteLLM preferred)
    # NOTE: This categorization will only be used for NEW articles.
    # Existing articles will preserve their existing LLM categorization (see fetch_and_upsert_articles)
    if use_llm_categorization:
        try:
            # Ensure RouteLLM API key is available
            import os
            if not os.getenv('ROUTELLM_API_KEY'):
                # Set default RouteLLM API key if not available
                os.environ['ROUTELLM_API_KEY'] = 's2_760166137897436c8b1dc5248b05db5a'
            
            # Use LLM categorization (RouteLLM preferred, falls back to other LLMs if needed)
            # Only do this for NEW articles - existing articles will preserve their categorization
            categorization_result = categorize_article(title, description, content or '', rss_feed_url=rss_feed_url)
            if isinstance(categorization_result, dict):
                categories = categorization_result.get('categories', [])
                main_category = categorization_result.get('main_category')
                sub_categories = categorization_result.get('sub_categories', [])
                categorization_argumentation = categorization_result.get('categorization_argumentation', '')
                categorization_llm = categorization_result.get('llm', 'Unknown')
                
                # Log which LLM was used
                print(f"[INFO] Article categorized with {categorization_llm}: {main_category}")
                
                # If LLM returned 'Keywords' or 'LLM-Failed', log a warning
                if categorization_llm in ['Keywords', 'Keywords-Fallback', 'Keywords-Error']:
                    print(f"[ERROR] LLM categorization returned {categorization_llm} - this should NEVER happen! RouteLLM should be used.")
                elif categorization_llm == 'LLM-Failed':
                    print(f"[WARN] All LLM categorization failed - using default 'Algemeen'")
            else:
                # Backward compatibility
                categories = categorization_result if isinstance(categorization_result, list) else []
                main_category = categories[0] if categories else None
                sub_categories = categories[1:] if len(categories) > 1 else []
                categorization_argumentation = ''
                categorization_llm = 'Unknown'
            
            # Ensure we have at least one category
            if not categories or len(categories) == 0:
                print(f"[WARN] No categories from LLM, using default 'Algemeen'")
                categories = ['Algemeen']
                main_category = 'Algemeen'
                sub_categories = []
                categorization_argumentation = 'LLM categorisatie faalde - standaard categorie gebruikt'
                categorization_llm = 'LLM-Failed'
        except Exception as e:
            print(f"[ERROR] LLM categorization failed completely: {e}")
            # Use default category, no keyword fallback
            categories = ['Algemeen']
            main_category = 'Algemeen'
            sub_categories = []
            categorization_argumentation = f'LLM categorisatie faalde - fout: {str(e)}'
            categorization_llm = 'LLM-Failed'
    
    # ALWAYS use LLM categorization - no keyword fallback
    # If use_llm_categorization is False, we still try LLM (but log a warning)
    if not use_llm_categorization:
        print(f"[WARN] use_llm_categorization=False but LLM categorization is required. Using LLM anyway.")
        try:
            categorization_result = categorize_article(title, description, content or '', rss_feed_url=rss_feed_url)
            if isinstance(categorization_result, dict):
                categories = categorization_result.get('categories', ['Algemeen'])
                main_category = categorization_result.get('main_category', 'Algemeen')
                sub_categories = categorization_result.get('sub_categories', [])
                categorization_argumentation = categorization_result.get('categorization_argumentation', '')
                categorization_llm = categorization_result.get('llm', 'LLM-Failed')
            else:
                categories = ['Algemeen']
                main_category = 'Algemeen'
                sub_categories = []
                categorization_argumentation = ''
                categorization_llm = 'LLM-Failed'
        except Exception as e:
            print(f"[ERROR] LLM categorization failed: {e}")
            categories = ['Algemeen']
            main_category = 'Algemeen'
            sub_categories = []
            categorization_argumentation = f'LLM categorisatie faalde: {str(e)}'
            categorization_llm = 'LLM-Failed'
    
    return {
        'stable_id': stable_id,
        'title': title,
        'description': description,
        'url': entry.get('link', '')[:1000],
        'source': 'NOS',
        'published_at': published_at.isoformat() if published_at else None,
        'full_content': content,
        'image_url': image_url[:1000] if image_url else None,
        'category': main_category or 'Algemeen',  # Legacy single category (use main_category)
        'categories': categories,  # New: multiple categories
        'main_category': main_category,  # Main category
        'sub_categories': sub_categories,  # Sub categories
        'categorization_argumentation': categorization_argumentation,  # Argumentation
        'categorization_llm': categorization_llm,  # Which LLM was used for categorization
        'rss_feed_url': rss_feed_url,  # RSS feed URL where article came from
        'eli5_summary_nl': None,  # Will be generated later
        'created_at': datetime.utcnow().isoformat(),
        'updated_at': datetime.utcnow().isoformat()
    }


def fetch_and_upsert_articles(feed_url: str, max_items: Optional[int] = None, use_llm_categorization: bool = True) -> Dict[str, Any]:
    """
    Fetch articles from RSS feed and upsert them to storage (Supabase or local).
    Also removes articles older than 72 hours.
    
    Args:
        feed_url: URL of the RSS feed
        max_items: Maximum number of items to process
        use_llm_categorization: If True, use LLM for categorization (default: True).
                                If False, use fast keyword matching (not recommended).
    
    Returns:
        Dict with counts of fetched, inserted, updated, skipped
    """
    storage = get_supabase_client()  # Returns Supabase or LocalStorage
    
    # Cleanup old articles (older than 72 hours) before processing new ones
    from supabase_client import SupabaseClient
    if isinstance(storage, SupabaseClient):
        try:
            cleanup_result = storage.delete_old_articles(hours_old=72)
            if cleanup_result.get('success'):
                deleted_count = cleanup_result.get('deleted_count', 0)
                if deleted_count > 0:
                    print(f"[RSS Feed] Cleaned up {deleted_count} articles older than 72 hours")
        except Exception as cleanup_error:
            print(f"[RSS Feed] Error during cleanup: {cleanup_error}")
    
    try:
        # Parse RSS feed
        feed = feedparser.parse(feed_url)
        
        if feed.bozo and feed.bozo_exception:
            return {
                'success': False,
                'error': f"Feed parsing error: {feed.bozo_exception}",
                'fetched': 0,
                'inserted': 0,
                'updated': 0,
                'skipped': 0
            }
        
        entries = feed.entries
        if max_items:
            entries = entries[:max_items]
        
        fetched_count = len(entries)
        inserted_count = 0
        updated_count = 0
        skipped_count = 0
        
        for entry in entries:
            try:
                article_data = parse_feed_entry(entry, use_llm_categorization=use_llm_categorization, rss_feed_url=feed_url)
                
                # Check if article already exists (works for both Supabase and LocalStorage)
                from local_storage import LocalStorage
                from supabase_client import SupabaseClient
                
                if isinstance(storage, LocalStorage):
                    # Local storage: check if exists
                    existing = storage.get_article_by_id(article_data['stable_id'])
                    if existing:
                        # Preserve ELI5 if exists
                        if existing.get('eli5_summary_nl'):
                            article_data['eli5_summary_nl'] = existing['eli5_summary_nl']
                            article_data['eli5_llm'] = existing.get('eli5_llm')
                        
                        # Preserve LLM categorization if it exists (don't re-categorize with LLM)
                        # Only preserve if it's a valid LLM (not Keywords, LLM-Failed, etc.)
                        existing_llm = existing.get('categorization_llm', '')
                        if existing_llm and existing_llm not in ['Keywords', 'Keywords-Fallback', 'Keywords-Error', 'LLM-Failed', 'Unknown']:
                            # Article already has LLM categorization, keep it
                            article_data['categories'] = existing.get('categories', [])
                            article_data['categorization_llm'] = existing.get('categorization_llm')
                            print(f"[RSS Checker] Preserving existing LLM categorization ({existing_llm}) for article {article_data.get('stable_id')[:8]}...")
                        
                        storage.upsert_article(article_data)
                        updated_count += 1
                    else:
                        # Insert new article (will be categorized with LLM if use_llm_categorization=True)
                        storage.upsert_article(article_data)
                        inserted_count += 1
                elif isinstance(storage, SupabaseClient):
                    # Supabase: check if exists by stable_id
                    try:
                        # Check if article exists by stable_id - also get categories and categorization_llm
                        response = storage.client.table('articles').select(
                            'id, eli5_summary_nl, categories, categorization_llm, eli5_llm'
                        ).eq('stable_id', article_data['stable_id']).execute()
                        
                        if response.data and len(response.data) > 0:
                            existing = response.data[0]
                            # Preserve ELI5 if it exists
                            if existing.get('eli5_summary_nl'):
                                article_data['eli5_summary_nl'] = existing['eli5_summary_nl']
                                article_data['eli5_llm'] = existing.get('eli5_llm')
                            
                            # Preserve LLM categorization if it exists (don't re-categorize with LLM)
                            # Only preserve if it's a valid LLM (not Keywords, LLM-Failed, etc.)
                            existing_llm = existing.get('categorization_llm', '')
                            if existing_llm and existing_llm not in ['Keywords', 'Keywords-Fallback', 'Keywords-Error', 'LLM-Failed', 'Unknown']:
                                # Article already has LLM categorization, keep it
                                article_data['categories'] = existing.get('categories', [])
                                article_data['categorization_llm'] = existing.get('categorization_llm')
                                print(f"[RSS Checker] Preserving existing LLM categorization ({existing_llm}) for article {article_data.get('stable_id')[:8]}...")
                            
                            storage.upsert_article(article_data)
                            updated_count += 1
                        else:
                            # Insert new article (will be categorized with LLM if use_llm_categorization=True)
                            storage.upsert_article(article_data)
                            inserted_count += 1
                    except Exception as e:
                        print(f"Error checking/upserting article in Supabase: {e}")
                        storage.upsert_article(article_data)
                        inserted_count += 1
                else:
                    # Unknown storage type, try to upsert anyway
                    storage.upsert_article(article_data)
                    inserted_count += 1
                    
            except Exception as e:
                print(f"Error processing entry: {e}")
                skipped_count += 1
                continue
        
        return {
            'success': True,
            'fetched': fetched_count,
            'inserted': inserted_count,
            'updated': updated_count,
            'skipped': skipped_count
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'fetched': 0,
            'inserted': 0,
            'updated': 0,
            'skipped': 0
        }


def generate_missing_eli5_summaries(limit: int = 5) -> int:
    """
    Generate ELI5 summaries for articles that don't have them yet.
    
    Returns:
        Number of summaries generated
    """
    storage = get_supabase_client()  # Returns Supabase or LocalStorage
    generated_count = 0
    
    try:
        articles = storage.get_articles_without_eli5(limit=limit)
        
        for article in articles:
            try:
                # Combine title and description for summary generation
                text = f"{article.get('title', '')} {article.get('description', '')}"
                if article.get('full_content'):
                    text += f" {article.get('full_content', '')[:1000]}"
                
                eli5_summary = generate_eli5_summary_nl(
                    text,
                    article.get('title', '')
                )
                
                if eli5_summary:
                    storage.update_article_eli5(article['id'], eli5_summary)
                    generated_count += 1
            except Exception as e:
                print(f"Error generating ELI5 for article {article.get('id')}: {e}")
                continue
    except Exception as e:
        print(f"Error getting articles for ELI5: {e}")
    
    return generated_count


def recategorize_all_articles(limit: int = None, use_llm: bool = True) -> Dict[str, Any]:
    """
    Recategorize all existing articles using LLM or keywords.
    
    Args:
        limit: Maximum number of articles to recategorize (None for all)
        use_llm: Whether to use LLM categorization (True) or keywords (False)
    
    Returns:
        Dict with counts of processed, updated, errors
    """
    storage = get_supabase_client()
    
    try:
        # Get all articles
        all_articles = storage.get_articles(limit=1000 if not limit else limit)
        
        if not all_articles:
            return {
                'success': True,
                'processed': 0,
                'updated': 0,
                'errors': 0
            }
        
        processed = 0
        updated = 0
        errors = 0
        
        for article in all_articles:
            try:
                title = article.get('title') or ''
                description = article.get('description') or ''
                content = article.get('full_content') or ''
                
                # Ensure we have at least a title
                if not title:
                    print(f"  ⚠️ Skipping article {article.get('id', 'unknown')}: no title")
                    errors += 1
                    processed += 1
                    continue
                
                # Recategorize - ALWAYS use LLM (no keyword fallback)
                try:
                    result = categorize_article(title, description, content)
                    if isinstance(result, dict):
                        new_categories = result.get('categories', ['Algemeen'])
                        categorization_llm = result.get('llm', 'LLM-Failed')
                    else:
                        new_categories = result if isinstance(result, list) else ['Algemeen']
                        categorization_llm = 'LLM-Failed'
                except Exception as llm_error:
                    print(f"  ⚠️ LLM categorization failed for article {article.get('id', 'unknown')}: {llm_error}")
                    # Use default category, no keyword fallback
                    new_categories = ['Algemeen']
                    categorization_llm = 'LLM-Failed'
                
                # Ensure we have at least one category
                if not new_categories:
                    new_categories = ['Algemeen']  # Default category
                    categorization_llm = 'LLM-Failed'
                
                # Update article
                article['categories'] = new_categories
                article['categorization_llm'] = categorization_llm
                
                if storage.upsert_article(article):
                    updated += 1
                else:
                    errors += 1
                
                processed += 1
                
            except Exception as e:
                print(f"Error recategorizing article {article.get('id', 'unknown')}: {e}")
                errors += 1
                processed += 1
                continue
        
        return {
            'success': True,
            'processed': processed,
            'updated': updated,
            'errors': errors
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'processed': 0,
            'updated': 0,
            'errors': 0
        }

