"""
Repository for article operations with Supabase.
Handles fetching from RSS, upserting to Supabase, and querying.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
import hashlib
import sys


def _log_with_timestamp(message: str):
    """Helper function to print log messages with timestamp."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}")

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
                
                # LLM categorization completed (no individual logging)
            else:
                # Backward compatibility
                categories = categorization_result if isinstance(categorization_result, list) else []
                main_category = categories[0] if categories else None
                sub_categories = categories[1:] if len(categories) > 1 else []
                categorization_argumentation = ''
                categorization_llm = 'Unknown'
            
            # Ensure we have at least one category
            if not categories or len(categories) == 0:
                categories = ['Algemeen']
                main_category = 'Algemeen'
                sub_categories = []
                categorization_argumentation = 'LLM categorisatie faalde - standaard categorie gebruikt'
                categorization_llm = 'LLM-Failed'
        except Exception as e:
            # Use default category, no keyword fallback
            categories = ['Algemeen']
            main_category = 'Algemeen'
            sub_categories = []
            categorization_argumentation = f'LLM categorisatie faalde - fout: {str(e)}'
            categorization_llm = 'LLM-Failed'
    
    # ALWAYS use LLM categorization - no keyword fallback
    # If use_llm_categorization is False, we still try LLM
    if not use_llm_categorization:
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
                    _log_with_timestamp(f"[RSS Feed] Cleaned up {deleted_count} articles older than 72 hours")
        except Exception as cleanup_error:
            _log_with_timestamp(f"[RSS Feed] Error during cleanup: {cleanup_error}")
    
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
        
        # Counters for categorization and ELI5 by LLM
        cat_groq = 0
        cat_routellm = 0
        cat_failed = 0
        eli5_groq = 0
        eli5_routellm = 0
        eli5_failed = 0
        
        for entry in entries:
            try:
                # Extract published_at first (needed for stable_id, but no LLM call yet)
                published_at = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    try:
                        from datetime import datetime
                        published_at = datetime(*entry.published_parsed[:6])
                    except Exception:
                        pass
                
                if not published_at and hasattr(entry, 'published'):
                    try:
                        from dateutil import parser
                        published_at = parser.parse(entry.published)
                    except Exception:
                        pass
                
                # Generate stable_id to check if article already exists
                stable_id = generate_stable_id(entry.get('link', ''), published_at)
                
                # Check if article already exists BEFORE parsing/categorizing (to avoid unnecessary RouteLLM API calls)
                from local_storage import LocalStorage
                from supabase_client import SupabaseClient
                
                existing = None
                article_is_new = False
                
                if isinstance(storage, LocalStorage):
                    # Local storage: check if exists
                    existing = storage.get_article_by_id(stable_id)
                    article_is_new = existing is None
                elif isinstance(storage, SupabaseClient):
                    # Supabase: check if exists by stable_id
                    try:
                        response = storage.client.table('articles').select(
                            'id, eli5_summary_nl, categories, categorization_llm, eli5_llm'
                        ).eq('stable_id', stable_id).execute()
                        
                        if response.data and len(response.data) > 0:
                            existing = response.data[0]
                            article_is_new = False
                        else:
                            article_is_new = True
                    except Exception as e:
                        article_is_new = True  # Assume new if check fails
                else:
                    article_is_new = True  # Unknown storage type, assume new
                
                # Only parse and categorize if article is NEW
                # This prevents unnecessary RouteLLM API calls for existing articles
                if article_is_new:
                    # Parse entry and categorize (only for new articles - this calls RouteLLM)
                    # NOTE: parse_feed_entry ALWAYS returns article_data, even if categorization fails
                    # It will use default 'Algemeen' category if LLM fails
                    try:
                        article_data = parse_feed_entry(entry, use_llm_categorization=use_llm_categorization, rss_feed_url=feed_url)
                        
                        # Ensure article_data is valid before upserting
                        if not article_data or 'stable_id' not in article_data:
                            skipped_count += 1
                            cat_failed += 1
                            continue
                        
                        # Count categorization LLM
                        cat_llm = article_data.get('categorization_llm', 'Unknown')
                        if cat_llm == 'Groq':
                            cat_groq += 1
                        elif cat_llm == 'RouteLLM':
                            cat_routellm += 1
                        else:
                            cat_failed += 1
                        
                        # Try to upsert the article - this should ALWAYS succeed, even if categorization failed
                        if isinstance(storage, LocalStorage):
                            if storage.upsert_article(article_data):
                                inserted_count += 1
                            else:
                                skipped_count += 1
                        elif isinstance(storage, SupabaseClient):
                            if storage.upsert_article(article_data):
                                inserted_count += 1
                            else:
                                skipped_count += 1
                        else:
                            if storage.upsert_article(article_data):
                                inserted_count += 1
                            else:
                                skipped_count += 1
                    except Exception as parse_error:
                        # Even if parsing fails, try to create a minimal article entry
                        try:
                            minimal_article = {
                                'stable_id': stable_id,
                                'title': entry.get('title', '')[:500] or 'Geen titel',
                                'description': entry.get('description') or entry.get('summary', '')[:2000] or '',
                                'url': entry.get('link', '')[:1000] or '',
                                'source': 'NOS',
                                'published_at': None,
                                'full_content': None,
                                'image_url': None,
                                'category': 'Algemeen',
                                'categories': ['Algemeen'],
                                'main_category': 'Algemeen',
                                'sub_categories': [],
                                'categorization_llm': 'Parse-Error',
                                'rss_feed_url': feed_url,
                                'eli5_summary_nl': None,
                                'created_at': datetime.utcnow().isoformat(),
                                'updated_at': datetime.utcnow().isoformat()
                            }
                            if storage.upsert_article(minimal_article):
                                inserted_count += 1
                                cat_failed += 1
                            else:
                                skipped_count += 1
                        except Exception as minimal_error:
                            skipped_count += 1
                            cat_failed += 1
                else:
                    # Article already exists - skip parsing/categorization to save RouteLLM API calls
                    updated_count += 1
                    
            except Exception as e:
                skipped_count += 1
                continue
        
        return {
            'success': True,
            'fetched': fetched_count,
            'inserted': inserted_count,
            'updated': updated_count,
            'skipped': skipped_count,
            'cat_groq': cat_groq,
            'cat_routellm': cat_routellm,
            'cat_failed': cat_failed
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


def generate_missing_eli5_summaries(limit: int = 5) -> Dict[str, Any]:
    """
    Generate ELI5 summaries for articles that don't have them yet.
    
    Returns:
        Dict with counts: generated, groq, routellm, failed
    """
    storage = get_supabase_client()  # Returns Supabase or LocalStorage
    generated_count = 0
    eli5_groq = 0
    eli5_routellm = 0
    eli5_failed = 0
    
    try:
        articles = storage.get_articles_without_eli5(limit=limit)
        
        for article in articles:
            try:
                # Combine title and description for summary generation
                text = f"{article.get('title', '')} {article.get('description', '')}"
                if article.get('full_content'):
                    text += f" {article.get('full_content', '')[:1000]}"
                
                result = generate_eli5_summary_nl_with_llm(
                    text,
                    article.get('title', '')
                )
                
                if result and result.get('summary'):
                    eli5_llm = result.get('llm', 'Unknown')
                    storage.update_article_eli5(article['id'], result['summary'], eli5_llm)
                    generated_count += 1
                    
                    # Count ELI5 LLM
                    if eli5_llm == 'Groq':
                        eli5_groq += 1
                    elif eli5_llm == 'RouteLLM':
                        eli5_routellm += 1
                    else:
                        eli5_failed += 1
                else:
                    eli5_failed += 1
            except Exception as e:
                eli5_failed += 1
                continue
    except Exception as e:
        pass
    
    return {
        'generated': generated_count,
        'groq': eli5_groq,
        'routellm': eli5_routellm,
        'failed': eli5_failed
    }


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
                    _log_with_timestamp(f"  ⚠️ Skipping article {article.get('id', 'unknown')}: no title")
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
                    _log_with_timestamp(f"  ⚠️ LLM categorization failed for article {article.get('id', 'unknown')}: {llm_error}")
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
                _log_with_timestamp(f"Error recategorizing article {article.get('id', 'unknown')}: {e}")
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

