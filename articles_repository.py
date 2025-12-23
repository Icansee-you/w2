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


def parse_feed_entry(entry: Dict[str, Any], use_llm_categorization: bool = False) -> Dict[str, Any]:
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
    
    # Determine category (simplified - you can enhance this)
    category = None
    title_lower = (entry.get('title', '') or '').lower()
    description_lower = (entry.get('description', '') or entry.get('summary', '') or '').lower()
    full_text = f"{title_lower} {description_lower}"
    
    if 'trump' in full_text:
        category = 'Trump'
    elif 'rusland' in full_text:
        category = 'Rusland'
    elif any(kw in full_text for kw in ['politiek', 'kabinet', 'minister', 'regering']):
        category = 'Politiek'
    elif any(kw in full_text for kw in ['voetbal', 'sport', 'ajax', 'psv']):
        category = 'Sport'
    elif any(kw in full_text for kw in ['nederland', 'nederlands']):
        category = 'Nationaal'
    else:
        category = 'Overig'
    
    stable_id = generate_stable_id(entry.get('link', ''), published_at)
    
    # Get title, description, and content for categorization
    title = entry.get('title', '')[:500]
    description = entry.get('description') or entry.get('summary', '')[:2000]
    content = entry.get('content', [{}])[0].get('value', '')[:10000] if entry.get('content') else None
    
    # Categorize article - use fast keyword matching by default, LLM only if requested
    if use_llm_categorization:
        try:
            # Use LLM categorization (slower, but more accurate)
            categorization_result = categorize_article(title, description, content or '')
            if isinstance(categorization_result, dict):
                categories = categorization_result.get('categories', [])[:3]  # Limit to 3
                categorization_llm = categorization_result.get('llm', 'Keywords')
            else:
                # Backward compatibility
                categories = (categorization_result if isinstance(categorization_result, list) else [])[:3]  # Limit to 3
                categorization_llm = 'Keywords'
        except Exception as e:
            print(f"LLM categorization failed, using keywords: {e}")
            from categorization_engine import _categorize_with_keywords
            categories = _categorize_with_keywords(title, description, content or '')[:3]  # Limit to 3
            categorization_llm = 'Keywords'
    else:
        # Use fast keyword matching (non-blocking)
        try:
            from categorization_engine import _categorize_with_keywords
            categories = _categorize_with_keywords(title, description, content or '')[:3]  # Limit to 3
            categorization_llm = 'Keywords'
        except Exception:
            # Fallback to simple category
            categories = ([category] if category else [])[:3]  # Limit to 3
            categorization_llm = 'Keywords'
    
    return {
        'stable_id': stable_id,
        'title': title,
        'description': description,
        'url': entry.get('link', '')[:1000],
        'source': 'NOS',
        'published_at': published_at.isoformat() if published_at else None,
        'full_content': content,
        'image_url': image_url[:1000] if image_url else None,
        'category': category,  # Legacy single category
        'categories': categories,  # New: multiple categories
        'categorization_llm': categorization_llm,  # Which LLM was used for categorization
        'eli5_summary_nl': None,  # Will be generated later
        'created_at': datetime.utcnow().isoformat(),
        'updated_at': datetime.utcnow().isoformat()
    }


def fetch_and_upsert_articles(feed_url: str, max_items: Optional[int] = None, use_llm_categorization: bool = False) -> Dict[str, Any]:
    """
    Fetch articles from RSS feed and upsert them to storage (Supabase or local).
    
    Args:
        feed_url: URL of the RSS feed
        max_items: Maximum number of items to process
        use_llm_categorization: If True, use LLM for categorization (slower). 
                                If False, use fast keyword matching (default).
    
    Returns:
        Dict with counts of fetched, inserted, updated, skipped
    """
    storage = get_supabase_client()  # Returns Supabase or LocalStorage
    
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
                article_data = parse_feed_entry(entry, use_llm_categorization=use_llm_categorization)
                
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
                        storage.upsert_article(article_data)
                        updated_count += 1
                    else:
                        storage.upsert_article(article_data)
                        inserted_count += 1
                elif isinstance(storage, SupabaseClient):
                    # Supabase: check if exists by stable_id
                    try:
                        # Check if article exists by stable_id
                        response = storage.client.table('articles').select('id, eli5_summary_nl').eq('stable_id', article_data['stable_id']).execute()
                        
                        if response.data and len(response.data) > 0:
                            # Update existing article (but preserve ELI5 if it exists)
                            if response.data[0].get('eli5_summary_nl'):
                                article_data['eli5_summary_nl'] = response.data[0]['eli5_summary_nl']
                            
                            storage.upsert_article(article_data)
                            updated_count += 1
                        else:
                            # Insert new article
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


def recategorize_all_articles(limit: int = None, use_llm: bool = True, progress_callback=None) -> Dict[str, Any]:
    """
    Recategorize all existing articles using LLM or keywords.
    
    Args:
        limit: Maximum number of articles to recategorize (None for all, default: 50)
        use_llm: Whether to use LLM categorization (True) or keywords (False)
        progress_callback: Optional callback function(processed, total, current_title) for progress updates
    
    Returns:
        Dict with counts of processed, updated, errors
    """
    storage = get_supabase_client()
    
    try:
        # Default limit to 50 to prevent hanging on large datasets
        if limit is None:
            limit = 50
        
        # Get all articles
        all_articles = storage.get_articles(limit=limit)
        total_articles = len(all_articles) if all_articles else 0
        
        if not all_articles:
            return {
                'success': True,
                'processed': 0,
                'updated': 0,
                'errors': 0,
                'total': 0
            }
        
        processed = 0
        updated = 0
        errors = 0
        
        for idx, article in enumerate(all_articles, 1):
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
                
                # Update progress
                if progress_callback:
                    progress_callback(processed, total_articles, title[:50])
                
                # Recategorize
                if use_llm:
                    try:
                        # Try categorization (has built-in timeout handling)
                        result = categorize_article(title, description, content)
                        
                        if result:
                            if isinstance(result, dict):
                                new_categories = result.get('categories', [])[:3]  # Limit to 3
                                categorization_llm = result.get('llm', 'Keywords')
                            else:
                                new_categories = (result if isinstance(result, list) else [])[:3]  # Limit to 3
                                categorization_llm = 'Keywords'
                        else:
                            # Fall back to keywords if LLM failed
                            from categorization_engine import _categorize_with_keywords
                            new_categories = _categorize_with_keywords(title, description, content)[:3]  # Limit to 3
                            categorization_llm = 'Keywords'
                    except TimeoutError:
                        print(f"  ⚠️ LLM categorization timeout for article {article.get('id', 'unknown')}")
                        # Fall back to keywords
                        from categorization_engine import _categorize_with_keywords
                        new_categories = _categorize_with_keywords(title, description, content)[:3]  # Limit to 3
                        categorization_llm = 'Keywords'
                    except Exception as llm_error:
                        print(f"  ⚠️ LLM categorization failed for article {article.get('id', 'unknown')}: {llm_error}")
                        # Fall back to keywords
                        from categorization_engine import _categorize_with_keywords
                        new_categories = _categorize_with_keywords(title, description, content)[:3]  # Limit to 3
                        categorization_llm = 'Keywords'
                else:
                    from categorization_engine import _categorize_with_keywords
                    new_categories = _categorize_with_keywords(title, description, content)[:3]  # Limit to 3
                    categorization_llm = 'Keywords'
                
                # Ensure we have at least one category
                if not new_categories:
                    new_categories = ['binnenland']  # Default category
                
                # Limit to maximum 3 categories
                new_categories = new_categories[:3]
                
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
            'errors': errors,
            'total': total_articles
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'processed': 0,
            'updated': 0,
            'errors': 0
        }


def recategorize_articles_without_llm(limit: int = 50, progress_callback=None) -> Dict[str, Any]:
    """
    Recategorize articles that don't have LLM-based categorization.
    Only processes articles where categorization_llm is 'Keywords' or None.
    Only runs if an LLM is available.
    
    Args:
        limit: Maximum number of articles to recategorize (default: 50)
        progress_callback: Optional callback function(processed, total, current_title) for progress updates
    
    Returns:
        Dict with counts of processed, updated, errors, skipped
    """
    from categorization_engine import is_llm_available, categorize_article
    
    # Check if LLM is available
    if not is_llm_available():
        return {
            'success': False,
            'error': 'Geen LLM beschikbaar. Configureer een LLM API key (Groq, Hugging Face, OpenAI, of ChatLLM).',
            'processed': 0,
            'updated': 0,
            'errors': 0,
            'skipped': 0,
            'total': 0
        }
    
    storage = get_supabase_client()
    
    try:
        # Get all articles
        all_articles = storage.get_articles(limit=500)  # Get more to filter
        
        if not all_articles:
            return {
                'success': True,
                'processed': 0,
                'updated': 0,
                'errors': 0,
                'skipped': 0,
                'total': 0
            }
        
        # Filter articles that need LLM categorization
        articles_to_recategorize = []
        for article in all_articles:
            categorization_llm = article.get('categorization_llm', 'Keywords')
            # Only recategorize if it was categorized with keywords or has no LLM
            if categorization_llm in [None, 'Keywords', '']:
                articles_to_recategorize.append(article)
        
        total_to_process = min(len(articles_to_recategorize), limit)
        
        if total_to_process == 0:
            return {
                'success': True,
                'processed': 0,
                'updated': 0,
                'errors': 0,
                'skipped': len(all_articles) - len(articles_to_recategorize),
                'total': len(all_articles),
                'message': 'Alle artikelen hebben al LLM-categorisatie.'
            }
        
        processed = 0
        updated = 0
        errors = 0
        
        for idx, article in enumerate(articles_to_recategorize[:limit], 1):
            try:
                title = article.get('title') or ''
                description = article.get('description') or ''
                content = article.get('full_content') or ''
                
                # Ensure we have at least a title
                if not title:
                    errors += 1
                    processed += 1
                    continue
                
                # Update progress
                if progress_callback:
                    progress_callback(processed, total_to_process, title[:50])
                
                # Recategorize with LLM
                try:
                    result = categorize_article(title, description, content)
                    
                    if result:
                        if isinstance(result, dict):
                            new_categories = result.get('categories', [])[:3]  # Limit to 3
                            categorization_llm = result.get('llm', 'Keywords')
                        else:
                            new_categories = (result if isinstance(result, list) else [])[:3]  # Limit to 3
                            categorization_llm = 'Keywords'
                    else:
                        # If LLM failed, skip this article (don't update)
                        errors += 1
                        processed += 1
                        continue
                    
                    # Only update if LLM was actually used (not Keywords)
                    if categorization_llm and categorization_llm != 'Keywords':
                        # Ensure we have at least one category
                        if not new_categories:
                            new_categories = ['binnenland']  # Default category
                        
                        # Limit to maximum 3 categories
                        new_categories = new_categories[:3]
                        
                        # Update article
                        article['categories'] = new_categories
                        article['categorization_llm'] = categorization_llm
                        
                        if storage.upsert_article(article):
                            updated += 1
                        else:
                            errors += 1
                    else:
                        # LLM wasn't actually used, skip
                        errors += 1
                        
                except Exception as llm_error:
                    # Skip articles where LLM fails
                    errors += 1
                
                processed += 1
                
            except Exception as e:
                errors += 1
                processed += 1
                continue
        
        return {
            'success': True,
            'processed': processed,
            'updated': updated,
            'errors': errors,
            'skipped': len(all_articles) - len(articles_to_recategorize),
            'total': len(all_articles)
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'processed': 0,
            'updated': 0,
            'errors': 0,
            'skipped': 0
        }

