"""
Supabase client for authentication and database operations.
"""
import os
from typing import Optional, Dict, List, Any
from datetime import datetime
try:
    from supabase import create_client, Client
    from supabase.lib.client_options import ClientOptions
except ImportError:
    # Fallback if supabase not installed
    Client = None
    ClientOptions = None


def _log_with_timestamp(message: str):
    """Helper function to print log messages with timestamp."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}")


class SupabaseClient:
    """Wrapper for Supabase client with auth and database operations."""
    
    def __init__(self):
        """Initialize Supabase client."""
        if Client is None:
            raise ImportError("supabase package not installed. Install with: pip install supabase")
        
        # Get secrets from Streamlit secrets or environment variables
        try:
            from secrets_helper import get_secret
            supabase_url = get_secret('SUPABASE_URL')
            supabase_key = get_secret('SUPABASE_ANON_KEY')
        except:
            # Fallback to environment variables if secrets_helper not available
            supabase_url = os.getenv('SUPABASE_URL')
            supabase_key = os.getenv('SUPABASE_ANON_KEY')
        
        if not supabase_url or not supabase_key:
            raise ValueError(
                "SUPABASE_URL and SUPABASE_ANON_KEY must be set in environment variables"
            )
        
        # Create client with minimal options to avoid compatibility issues
        try:
            if ClientOptions:
                # Try with options first
                try:
                    options = ClientOptions(
                        auto_refresh_token=True,
                        persist_session=True
                    )
                    self.client: Client = create_client(
                        supabase_url,
                        supabase_key,
                        options=options
                    )
                except (AttributeError, TypeError):
                    # Fallback: create without options if ClientOptions has issues
                    self.client: Client = create_client(
                        supabase_url,
                        supabase_key
                    )
            else:
                # No ClientOptions available, create without options
                self.client: Client = create_client(
                    supabase_url,
                    supabase_key
                )
        except Exception as e:
            raise ValueError(f"Failed to create Supabase client: {e}")
    
    # Authentication methods
    def sign_up(self, email: str, password: str) -> Dict[str, Any]:
        """Sign up a new user."""
        try:
            response = self.client.auth.sign_up({
                "email": email,
                "password": password
            })
            return {
                "success": True,
                "user": response.user,
                "session": response.session
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def sign_in(self, email: str, password: str) -> Dict[str, Any]:
        """Sign in an existing user."""
        try:
            response = self.client.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            return {
                "success": True,
                "user": response.user,
                "session": response.session
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def sign_out(self) -> bool:
        """Sign out current user."""
        try:
            self.client.auth.sign_out()
            return True
        except Exception:
            return False
    
    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """Get current authenticated user."""
        try:
            user = self.client.auth.get_user()
            if user:
                return {
                    "id": user.user.id,
                    "email": user.user.email,
                    "created_at": user.user.created_at
                }
        except Exception:
            pass
        return None
    
    def get_session(self):
        """Get current session."""
        try:
            return self.client.auth.get_session()
        except Exception:
            return None
    
    # User preferences methods
    def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get user preferences including blacklist."""
        try:
            response = self.client.table('user_preferences').select('*').eq('user_id', user_id).execute()
            if response.data:
                prefs = response.data[0]
                # Only set default categories if selected_categories is completely missing (new user)
                # Do NOT overwrite if user has explicitly set categories (even if empty list)
                if 'selected_categories' not in prefs or prefs.get('selected_categories') is None:
                    # Only set default if field is completely missing or None (not if it's an empty list)
                    # Empty list means user explicitly deselected all categories - respect that choice
                    from categorization_engine import get_all_categories
                    prefs['selected_categories'] = get_all_categories()
                    # Update in database only if it was missing (new user)
                    self.update_user_preferences(user_id, selected_categories=prefs['selected_categories'])
                return prefs
            else:
                # Create default preferences
                return self.create_default_preferences(user_id)
        except Exception as e:
            # If table doesn't exist, return defaults
            from categorization_engine import get_all_categories
            return {
                "user_id": user_id,
                "blacklist_keywords": [],  # No keywords blocked by default for new users
                "selected_categories": get_all_categories()  # All categories selected by default
            }
    
    def create_default_preferences(self, user_id: str) -> Dict[str, Any]:
        """Create default preferences for a new user."""
        from categorization_engine import get_all_categories
        all_categories = get_all_categories()
        
        default_prefs = {
            "user_id": user_id,
            "blacklist_keywords": [],  # No keywords blocked by default for new users
            "selected_categories": all_categories  # All categories selected by default
        }
        try:
            response = self.client.table('user_preferences').insert(default_prefs).execute()
            return response.data[0] if response.data else default_prefs
        except Exception:
            return default_prefs
    
    def update_user_preferences(self, user_id: str, blacklist_keywords: List[str] = None, selected_categories: List[str] = None) -> bool:
        """Update user preferences. Only updates fields that are provided (not None)."""
        try:
            from datetime import datetime
            
            # First, get existing preferences to preserve fields that aren't being updated
            existing_prefs = self.get_user_preferences(user_id)
            
            # Build update dict with only fields that are being updated
            prefs = {
                "user_id": user_id,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # Only update fields that are explicitly provided (not None)
            if blacklist_keywords is not None:
                prefs["blacklist_keywords"] = blacklist_keywords
            else:
                # Preserve existing blacklist if not being updated
                if existing_prefs.get('blacklist_keywords') is not None:
                    prefs["blacklist_keywords"] = existing_prefs['blacklist_keywords']
            
            if selected_categories is not None:
                prefs["selected_categories"] = selected_categories
            else:
                # Preserve existing categories if not being updated
                if existing_prefs.get('selected_categories') is not None:
                    prefs["selected_categories"] = existing_prefs['selected_categories']
            
            # Try to update first
            update_response = self.client.table('user_preferences').update(prefs).eq('user_id', user_id).execute()
            if not update_response.data:
                # If no existing record, insert
                self.client.table('user_preferences').insert(prefs).execute()
            return True
        except Exception as e:
            _log_with_timestamp(f"Error updating preferences: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    # Article methods
    def upsert_article(self, article_data: Dict[str, Any]) -> bool:
        """Insert or update an article in Supabase."""
        try:
            from datetime import datetime
            
            # Create a copy to avoid modifying the original
            data_to_upsert = article_data.copy()
            
            # Ensure categories is a list (Supabase expects array)
            if 'categories' in data_to_upsert and data_to_upsert['categories']:
                if not isinstance(data_to_upsert['categories'], list):
                    data_to_upsert['categories'] = list(data_to_upsert['categories'])
            else:
                data_to_upsert['categories'] = []
            
            # Remove fields that might not exist in the database schema
            # These fields are optional and may not be present in all database setups
            optional_fields = ['categorization_argumentation', 'sub_categories', 'main_category', 'rss_feed_url']
            for field in optional_fields:
                if field in data_to_upsert:
                    # Try to check if field exists, but if it doesn't, remove it
                    # We'll remove it preemptively to avoid schema errors
                    # Note: If the column exists, we can add it back later
                    # For now, we'll only include it if we're sure it exists
                    pass  # We'll filter it out below
            
            # Filter out fields that might not exist in schema
            # Keep only fields that are definitely in the schema
            # Note: rss_feed_url is now in optional_fields, not safe_fields
            safe_fields = [
                'stable_id', 'title', 'description', 'url', 'source', 'published_at',
                'full_content', 'image_url', 'category', 'categories', 'categorization_llm',
                'eli5_summary_nl', 'eli5_llm', 'created_at', 'updated_at'
            ]
            
            # Build safe data dict with only known fields
            safe_data = {}
            for field in safe_fields:
                if field in data_to_upsert:
                    safe_data[field] = data_to_upsert[field]
            
            # Try to include optional fields if they exist in data_to_upsert
            # These fields may not exist in the database schema, so we'll try with them first
            # and remove them if we get a schema error
            optional_fields_data = {}
            for field in optional_fields:
                if field in data_to_upsert:
                    optional_fields_data[field] = data_to_upsert[field]
            
            # First try: include optional fields if they exist
            if optional_fields_data:
                safe_data_with_optional = {**safe_data, **optional_fields_data}
                try:
                    self.client.table('articles').upsert(
                        safe_data_with_optional,
                        on_conflict='stable_id'
                    ).execute()
                    return True
                except Exception as schema_error:
                    # If it's a schema error about optional fields, try without them
                    error_msg = str(schema_error)
                    # Check if error mentions any optional field (case-insensitive)
                    error_lower = error_msg.lower()
                    optional_field_found = any(field.lower() in error_lower for field in optional_fields)
                    
                    if optional_field_found or 'PGRST204' in error_msg or 'schema cache' in error_lower:
                        # Remove optional fields and try again with only safe fields
                        _log_with_timestamp(f"[WARN] Optional fields not in schema, retrying without them: {error_msg}")
                        try:
                            self.client.table('articles').upsert(
                                safe_data,
                                on_conflict='stable_id'
                            ).execute()
                            _log_with_timestamp("[WARN] Upserted article without optional fields (categorization_argumentation, sub_categories, main_category, rss_feed_url)")
                            return True
                        except Exception as retry_error:
                            _log_with_timestamp(f"Error upserting article (retry): {retry_error}")
                            return False
                    else:
                        # Different error, log and return False
                        _log_with_timestamp(f"Error upserting article: {schema_error}")
                        return False
            else:
                # No optional fields to include, just use safe_data
                try:
                    self.client.table('articles').upsert(
                        safe_data,
                        on_conflict='stable_id'
                    ).execute()
                    return True
                except Exception as e:
                    _log_with_timestamp(f"Error upserting article: {e}")
                    return False
        except Exception as e:
            _log_with_timestamp(f"Error upserting article (outer exception): {e}")
            return False
    
    def get_articles(
        self,
        limit: int = 50,
        offset: int = 0,
        category: Optional[str] = None,
        categories: Optional[List[str]] = None,
        search_query: Optional[str] = None,
        blacklist_keywords: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get articles from Supabase with optional filters.
        Only returns articles published in the last 72 hours.
        """
        try:
            from datetime import datetime, timedelta
            import pytz
            
            # Calculate 72 hours ago
            cutoff_date = datetime.now(pytz.UTC) - timedelta(hours=72)
            cutoff_date_str = cutoff_date.isoformat()
            
            query = self.client.table('articles').select('*')
            
            # Only get articles from the last 72 hours
            query = query.gte('published_at', cutoff_date_str)
            
            if category:
                query = query.eq('category', category)
            
            # Filter by categories array (if any category in the list matches)
            if categories:
                # Supabase supports array overlap with 'cs' (contains) operator
                # We'll filter in Python for better compatibility
                pass  # Will filter after fetching
            
            # Note: Supabase doesn't support complex OR queries easily
            # We'll filter search results in Python if needed
            query = query.order('published_at', desc=True).limit(limit).offset(offset)
            
            response = query.execute()
            articles = response.data if response.data else []
            
            # Filter by categories array (if provided)
            # IMPORTANT: Only filter by main_category, ignore sub_categories
            if categories:
                filtered = []
                for article in articles:
                    # Get main_category from article (preferred) or fallback to first category
                    main_category = article.get('main_category')
                    if not main_category:
                        # Fallback: use first category from categories array if main_category not available
                        article_categories = article.get('categories', []) or []
                        main_category = article_categories[0] if article_categories else None
                    
                    # Only show article if main_category is in selected_categories
                    if main_category and main_category in categories:
                        filtered.append(article)
                articles = filtered
            
            # Apply search filter in Python (if query provided)
            if search_query:
                search_lower = search_query.lower()
                filtered = []
                for article in articles:
                    title = (article.get('title') or '').lower()
                    description = (article.get('description') or '').lower()
                    content = (article.get('full_content') or '').lower()
                    if search_lower in title or search_lower in description or search_lower in content:
                        filtered.append(article)
                articles = filtered
            
            # Apply blacklist filter if provided
            if blacklist_keywords:
                filtered_articles = []
                for article in articles:
                    # Check title, description, and full_content
                    title = (article.get('title') or '').lower()
                    description = (article.get('description') or '').lower()
                    full_content = (article.get('full_content') or '').lower()
                    
                    # Combine all text for checking
                    all_text = f"{title} {description} {full_content}"
                    
                    should_include = True
                    
                    # Check each keyword (case-insensitive)
                    for keyword in blacklist_keywords:
                        keyword_lower = keyword.lower().strip()
                        if keyword_lower and keyword_lower in all_text:
                            should_include = False
                            break
                    
                    if should_include:
                        filtered_articles.append(article)
                
                return filtered_articles
            
            return articles
        except Exception as e:
            _log_with_timestamp(f"Error getting articles: {e}")
            return []
    
    def get_article_by_id(self, article_id: str) -> Optional[Dict[str, Any]]:
        """Get a single article by ID."""
        try:
            response = self.client.table('articles').select('*').eq('id', article_id).execute()
            if response.data:
                article = response.data[0]
                # Ensure categories is a list (Supabase returns TEXT[] as list, but handle edge cases)
                if article.get('categories') and isinstance(article.get('categories'), str):
                    try:
                        import json
                        article['categories'] = json.loads(article['categories'])
                    except:
                        article['categories'] = []
                elif not article.get('categories'):
                    article['categories'] = []
                return article
            return None
        except Exception:
            return None
    
    def update_article_eli5(self, article_id: str, eli5_summary: str, llm: str = None) -> bool:
        """Update article with ELI5 summary and LLM used."""
        try:
            from datetime import datetime
            import pytz
            
            update_data = {
                'eli5_summary_nl': eli5_summary,
                'updated_at': datetime.now(pytz.UTC).isoformat()
            }
            # Always set eli5_llm, even if None (use 'Onbekend' as fallback)
            update_data['eli5_llm'] = llm if llm else 'Onbekend'
            
            self.client.table('articles').update(update_data).eq('id', article_id).execute()
            return True
        except Exception as e:
            _log_with_timestamp(f"Error updating ELI5: {e}")
            return False
    
    def update_article_categories(self, article_id: str, categories: List[str], categorization_llm: str) -> bool:
        """Update article with new categories and LLM used."""
        try:
            from datetime import datetime
            import pytz
            
            update_data = {
                'categories': categories,
                'categorization_llm': categorization_llm,
                'updated_at': datetime.now(pytz.UTC).isoformat()
            }
            
            self.client.table('articles').update(update_data).eq('id', article_id).execute()
            return True
        except Exception as e:
            _log_with_timestamp(f"Error updating categories: {e}")
            return False
    
    def get_articles_without_eli5(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get articles that don't have ELI5 summaries yet. Only returns articles from the last 72 hours."""
        try:
            from datetime import datetime, timedelta
            import pytz
            
            # Calculate 72 hours ago
            cutoff_date = datetime.now(pytz.UTC) - timedelta(hours=72)
            cutoff_date_str = cutoff_date.isoformat()
            
            query = self.client.table('articles').select('*')
            # Only get articles from the last 72 hours
            query = query.gte('published_at', cutoff_date_str)
            # Only get articles without ELI5
            query = query.is_('eli5_summary_nl', 'null')
            query = query.limit(limit)
            
            response = query.execute()
            return response.data if response.data else []
        except Exception:
            return []
    
    def get_user_count(self) -> int:
        """Get total count of registered users from Supabase Auth."""
        try:
            # Method 1: Try to call database function if it exists
            try:
                response = self.client.rpc('get_user_count').execute()
                if response.data is not None:
                    # RPC functions return data in different formats
                    if isinstance(response.data, (int, float)):
                        return int(response.data)
                    elif isinstance(response.data, list) and len(response.data) > 0:
                        # Function returns a list with one integer
                        value = response.data[0]
                        if isinstance(value, dict):
                            # Sometimes wrapped in dict
                            for key in ['get_user_count', 'count', 'result', 'value']:
                                if key in value:
                                    return int(value[key])
                        else:
                            return int(value)
                    elif isinstance(response.data, dict):
                        # Try common keys
                        for key in ['count', 'result', 'value', 'user_count', 'get_user_count']:
                            if key in response.data:
                                return int(response.data[key])
                    # If it's a single value, try to convert
                    try:
                        return int(response.data)
                    except:
                        pass
            except Exception as e:
                print(f"RPC function not available (this is OK if function not created yet): {e}")
            
            # Method 2: Count distinct users from user_preferences table
            # This works because get_user_preferences creates default preferences for new users
            try:
                # Use count='exact' to get the count without fetching all data
                response = self.client.table('user_preferences').select('user_id', count='exact').execute()
                
                # Check if count attribute exists
                if hasattr(response, 'count') and response.count is not None:
                    return int(response.count)
                
                # Fallback: fetch all and count unique user_ids
                # Note: This might be slow with many users, but works reliably
                all_prefs = self.client.table('user_preferences').select('user_id').execute()
                if all_prefs.data:
                    unique_users = set()
                    for pref in all_prefs.data:
                        user_id = pref.get('user_id')
                        if user_id:
                            unique_users.add(str(user_id))  # Convert to string for consistency
                    return len(unique_users)
                
                return 0
            except Exception as e:
                print(f"Error counting users from user_preferences: {e}")
                # Try alternative: count all rows
                try:
                    response = self.client.table('user_preferences').select('id', count='exact').execute()
                    if hasattr(response, 'count') and response.count is not None:
                        return int(response.count)
                except Exception:
                    pass
            
            # If all methods fail, return -1 to indicate unavailable
            return -1
        except Exception as e:
            print(f"Error in get_user_count: {e}")
            return -1
    
    def delete_old_articles(self, days_old: int = None, hours_old: int = None) -> Dict[str, Any]:
        """
        Delete articles older than specified number of days or hours.
        
        Args:
            days_old: Number of days old (deprecated, use hours_old instead)
            hours_old: Number of hours old (default: 72 hours = 3 days)
        
        Returns:
            Dict with count of deleted articles and any errors
        """
        try:
            from datetime import datetime, timedelta
            import pytz
            
            # Default to 72 hours if not specified
            if hours_old is None:
                if days_old is not None:
                    hours_old = days_old * 24
                else:
                    hours_old = 72  # Default: 72 hours
            
            # Calculate cutoff date (articles older than this will be deleted)
            cutoff_date = datetime.now(pytz.UTC) - timedelta(hours=hours_old)
            cutoff_date_str = cutoff_date.isoformat()
            
            print(f"[Delete Old Articles] Deleting articles older than {hours_old} hours (before {cutoff_date_str})")
            
            # First, get count of articles to be deleted (for logging)
            try:
                count_response = self.client.table('articles').select('id', count='exact').lt('published_at', cutoff_date_str).execute()
                count = count_response.count if hasattr(count_response, 'count') and count_response.count is not None else 0
            except Exception as e:
                print(f"[Delete Old Articles] Error counting articles: {e}")
                count = 0
            
            if count == 0:
                print(f"[Delete Old Articles] No articles older than {hours_old} hours found")
                return {
                    'success': True,
                    'deleted_count': 0,
                    'error': None
                }
            
            # Delete articles older than cutoff date
            # Use published_at if available, otherwise use created_at
            try:
                # Try deleting by published_at first
                response = self.client.table('articles').delete().lt('published_at', cutoff_date_str).execute()
                deleted_count = len(response.data) if response.data else 0
                
                # Also delete articles without published_at that are old based on created_at
                response2 = self.client.table('articles').delete().is_('published_at', 'null').lt('created_at', cutoff_date_str).execute()
                deleted_count += len(response2.data) if response2.data else 0
                
                print(f"[Delete Old Articles] Successfully deleted {deleted_count} articles")
                
                return {
                    'success': True,
                    'deleted_count': deleted_count,
                    'error': None
                }
            except Exception as e:
                error_msg = f"Error deleting articles: {str(e)}"
                print(f"[Delete Old Articles] {error_msg}")
                return {
                    'success': False,
                    'deleted_count': 0,
                    'error': error_msg
                }
        except Exception as e:
            error_msg = f"Exception in delete_old_articles: {str(e)}"
            print(f"[Delete Old Articles] {error_msg}")
            return {
                'success': False,
                'deleted_count': 0,
                'error': error_msg
            }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about articles and ELI5 summaries. Only includes articles from the last 72 hours."""
        try:
            from datetime import datetime, timedelta
            import pytz
            
            # Calculate 72 hours ago
            cutoff_date = datetime.now(pytz.UTC) - timedelta(hours=72)
            cutoff_date_str = cutoff_date.isoformat()
            
            # Get total article count (last 72 hours only)
            articles_response = self.client.table('articles').select('id', count='exact').gte('published_at', cutoff_date_str).execute()
            total_articles = articles_response.count if hasattr(articles_response, 'count') else len(articles_response.data) if articles_response.data else 0
            
            # Get articles with ELI5 (last 72 hours only)
            eli5_response = self.client.table('articles').select('id', count='exact').gte('published_at', cutoff_date_str).not_.is_('eli5_summary_nl', 'null').execute()
            articles_with_eli5 = eli5_response.count if hasattr(eli5_response, 'count') else len(eli5_response.data) if eli5_response.data else 0
            
            # Get all articles with categories (last 72 hours only)
            all_articles_response = self.client.table('articles').select('categories, categorization_llm').gte('published_at', cutoff_date_str).execute()
            articles = all_articles_response.data if all_articles_response.data else []
            
            # Count categories
            category_counts = {}
            for article in articles:
                categories = article.get('categories', [])
                if isinstance(categories, str):
                    try:
                        import json
                        categories = json.loads(categories)
                    except:
                        categories = []
                if isinstance(categories, list):
                    for cat in categories:
                        if cat:
                            category_counts[cat] = category_counts.get(cat, 0) + 1
            
            return {
                'total_articles': total_articles,
                'articles_with_eli5': articles_with_eli5,
                'articles_without_eli5': total_articles - articles_with_eli5,
                'category_counts': category_counts
            }
        except Exception as e:
            print(f"Error getting statistics: {e}")
            return {
                'total_articles': 0,
                'articles_with_eli5': 0,
                'articles_without_eli5': 0,
                'category_counts': {}
            }

    # Reading activity methods
    def track_article_opened(self, user_id: str, article_id: str) -> bool:
        """
        Track when a user opens an article.
        Creates a new record or updates last_viewed_at if record already exists.
        
        Args:
            user_id: The user's ID
            article_id: The article's ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            from datetime import datetime
            import pytz
            
            now = datetime.now(pytz.UTC).isoformat()
            
            # Check if record already exists
            existing = self.client.table('reading_activity').select('id, opened_at').eq('user_id', user_id).eq('article_id', article_id).execute()
            
            if existing.data and len(existing.data) > 0:
                # Update existing record
                self.client.table('reading_activity').update({
                    'last_viewed_at': now,
                    'updated_at': now
                }).eq('user_id', user_id).eq('article_id', article_id).execute()
            else:
                # Insert new record
                self.client.table('reading_activity').insert({
                    'user_id': user_id,
                    'article_id': article_id,
                    'opened_at': now,
                    'last_viewed_at': now
                }).execute()
            
            return True
        except Exception as e:
            print(f"Error tracking article opened: {e}")
            return False
    
    def mark_article_as_read(self, user_id: str, article_id: str, read_duration_seconds: int = None) -> bool:
        """
        Mark an article as read by a user.
        
        Args:
            user_id: The user's ID
            article_id: The article's ID
            read_duration_seconds: Optional duration in seconds the user spent reading
            
        Returns:
            True if successful, False otherwise
        """
        try:
            from datetime import datetime
            import pytz
            
            now = datetime.now(pytz.UTC).isoformat()
            
            update_data = {
                'is_read': True,
                'last_viewed_at': now,
                'updated_at': now
            }
            
            if read_duration_seconds is not None:
                update_data['read_duration_seconds'] = read_duration_seconds
            
            # First ensure the record exists (track as opened if not)
            self.track_article_opened(user_id, article_id)
            
            # Then update to mark as read
            self.client.table('reading_activity').update(update_data).eq('user_id', user_id).eq('article_id', article_id).execute()
            
            return True
        except Exception as e:
            print(f"Error marking article as read: {e}")
            return False
    
    def get_user_reading_activity(self, user_id: str, limit: int = 50, only_read: bool = False) -> List[Dict[str, Any]]:
        """
        Get reading activity for a user.
        
        Args:
            user_id: The user's ID
            limit: Maximum number of records to return
            only_read: If True, only return articles marked as read
            
        Returns:
            List of reading activity records
        """
        try:
            query = self.client.table('reading_activity').select('*').eq('user_id', user_id)
            
            if only_read:
                query = query.eq('is_read', True)
            
            query = query.order('last_viewed_at', desc=True).limit(limit)
            
            response = query.execute()
            return response.data if response.data else []
        except Exception as e:
            print(f"Error getting reading activity: {e}")
            return []
    
    def get_user_read_articles(self, user_id: str, limit: int = 50) -> List[str]:
        """
        Get list of article IDs that a user has read.
        
        Args:
            user_id: The user's ID
            limit: Maximum number of article IDs to return
            
        Returns:
            List of article IDs
        """
        try:
            activity = self.get_user_reading_activity(user_id, limit=limit, only_read=True)
            return [record['article_id'] for record in activity]
        except Exception as e:
            print(f"Error getting read articles: {e}")
            return []
    
    def get_user_opened_articles(self, user_id: str, limit: int = 50) -> List[str]:
        """
        Get list of article IDs that a user has opened (read or not).
        
        Args:
            user_id: The user's ID
            limit: Maximum number of article IDs to return
            
        Returns:
            List of article IDs
        """
        try:
            activity = self.get_user_reading_activity(user_id, limit=limit, only_read=False)
            return [record['article_id'] for record in activity]
        except Exception as e:
            print(f"Error getting opened articles: {e}")
            return []
    
    def is_article_read_by_user(self, user_id: str, article_id: str) -> bool:
        """
        Check if a specific article has been read by a user.
        
        Args:
            user_id: The user's ID
            article_id: The article's ID
            
        Returns:
            True if article is read, False otherwise
        """
        try:
            response = self.client.table('reading_activity').select('is_read').eq('user_id', user_id).eq('article_id', article_id).execute()
            if response.data and len(response.data) > 0:
                return response.data[0].get('is_read', False)
            return False
        except Exception as e:
            print(f"Error checking if article is read: {e}")
            return False
    
    def get_reading_statistics(self, user_id: str) -> Dict[str, Any]:
        """
        Get reading statistics for a user.
        
        Args:
            user_id: The user's ID
            
        Returns:
            Dictionary with reading statistics
        """
        try:
            # Get all reading activity for user
            all_activity = self.get_user_reading_activity(user_id, limit=1000)
            
            total_opened = len(all_activity)
            total_read = sum(1 for record in all_activity if record.get('is_read', False))
            
            # Calculate average read duration
            read_records = [r for r in all_activity if r.get('is_read', False) and r.get('read_duration_seconds')]
            avg_duration = sum(r['read_duration_seconds'] for r in read_records) / len(read_records) if read_records else 0
            
            return {
                'total_articles_opened': total_opened,
                'total_articles_read': total_read,
                'avg_read_duration_seconds': avg_duration,
                'read_percentage': (total_read / total_opened * 100) if total_opened > 0 else 0
            }
        except Exception as e:
            print(f"Error getting reading statistics: {e}")
            return {
                'total_articles_opened': 0,
                'total_articles_read': 0,
                'avg_read_duration_seconds': 0,
                'read_percentage': 0
            }
    
    def get_all_users_with_reading_stats(self) -> List[Dict[str, Any]]:
        """
        Get all registered users with their reading statistics.
        This is an admin function that requires proper permissions.
        Uses database function if available, otherwise falls back to manual query.
        
        Returns:
            List of dictionaries with user info and reading statistics
        """
        try:
            # First try to use the database function (most efficient and includes emails)
            try:
                response = self.client.rpc('get_all_users_with_reading_stats').execute()
                if response.data:
                    # Convert database function results to our format
                    users_with_stats = []
                    for record in response.data:
                        users_with_stats.append({
                            'user_id': record.get('user_id'),
                            'email': record.get('email', 'Onbekend'),
                            'total_articles_opened': record.get('total_articles_opened', 0),
                            'total_articles_read': record.get('total_articles_read', 0),
                            'avg_read_duration_seconds': float(record.get('avg_read_duration_seconds', 0)) if record.get('avg_read_duration_seconds') else 0,
                            'read_percentage': float(record.get('read_percentage', 0)) if record.get('read_percentage') else 0
                        })
                    return users_with_stats
            except Exception as e:
                print(f"Database function not available, using fallback method: {e}")
                # Fall through to manual method
            
            # Fallback: Manual method
            # Note: Without the database function, we can only get users who have preferences or activity
            # This is a limitation - to get ALL users, you need to run the SQL function
            
            # Get users from user_preferences (users who have logged in at least once)
            user_ids_from_prefs = []
            try:
                prefs_response = self.client.table('user_preferences').select('user_id').execute()
                if prefs_response.data:
                    user_ids_from_prefs = [pref['user_id'] for pref in prefs_response.data if pref.get('user_id')]
            except Exception as e:
                print(f"Could not get users from preferences: {e}")
            
            # Get users from reading_activity
            user_ids_from_activity = []
            try:
                activity_response = self.client.table('reading_activity').select('user_id').execute()
                if activity_response.data:
                    user_ids_from_activity = [record['user_id'] for record in activity_response.data if record.get('user_id')]
            except Exception as e:
                print(f"Could not get users from reading_activity: {e}")
            
            # Combine and get unique user IDs
            all_user_ids = list(set(user_ids_from_prefs + user_ids_from_activity))
            
            if not all_user_ids:
                print("No users found in preferences or reading_activity. Database function required to get all users.")
                return []
            
            # Try to get emails via RPC function
            user_emails_map = {}
            try:
                # Try to get emails using the get_user_emails function
                emails_response = self.client.rpc('get_user_emails', {'user_ids': all_user_ids}).execute()
                if emails_response.data:
                    for record in emails_response.data:
                        user_emails_map[record.get('user_id')] = record.get('email', 'Onbekend')
            except Exception as e:
                print(f"Could not get emails via RPC function: {e}")
                # Continue without emails
            
            # For each user, get their email and reading statistics
            users_with_stats = []
            
            for user_id in all_user_ids:
                try:
                    # Get reading statistics
                    stats = self.get_reading_statistics(user_id)
                    
                    # Get email from map or use fallback
                    user_email = user_emails_map.get(user_id, f"User {user_id[:8]}...")
                    
                    users_with_stats.append({
                        'user_id': user_id,
                        'email': user_email,
                        'total_articles_opened': stats.get('total_articles_opened', 0),
                        'total_articles_read': stats.get('total_articles_read', 0),
                        'avg_read_duration_seconds': stats.get('avg_read_duration_seconds', 0),
                        'read_percentage': stats.get('read_percentage', 0)
                    })
                except Exception as e:
                    print(f"Error getting stats for user {user_id}: {e}")
                    continue
            
            # Sort by total_articles_read (descending)
            users_with_stats.sort(key=lambda x: x['total_articles_read'], reverse=True)
            
            return users_with_stats
        except Exception as e:
            print(f"Error getting all users with reading stats: {e}")
            return []
    
    def get_all_users_with_reading_stats_via_activity(self) -> List[Dict[str, Any]]:
        """
        Alternative method: Get all users from reading_activity table.
        This is more efficient if reading_activity table exists.
        Uses database function if available, otherwise falls back to manual query.
        
        Returns:
            List of dictionaries with user info and reading statistics
        """
        try:
            # First try to use the database function (most efficient and includes emails)
            try:
                response = self.client.rpc('get_all_users_with_reading_stats').execute()
                if response.data:
                    # Convert database function results to our format
                    users_with_stats = []
                    for record in response.data:
                        users_with_stats.append({
                            'user_id': record.get('user_id'),
                            'email': record.get('email', 'Onbekend'),
                            'total_articles_opened': record.get('total_articles_opened', 0),
                            'total_articles_read': record.get('total_articles_read', 0),
                            'avg_read_duration_seconds': float(record.get('avg_read_duration_seconds', 0)) if record.get('avg_read_duration_seconds') else 0,
                            'read_percentage': float(record.get('read_percentage', 0)) if record.get('read_percentage') else 0
                        })
                    return users_with_stats
            except Exception as e:
                print(f"Database function not available, using fallback method: {e}")
                # Fall through to manual method
            
            # Fallback: Manual method with email lookup
            # Get all unique user_ids from reading_activity
            response = self.client.table('reading_activity').select('user_id').execute()
            
            if not response.data:
                # If no reading activity, try to get users from user_preferences
                return self.get_all_users_with_reading_stats()
            
            # Get unique user IDs
            user_ids = list(set([record['user_id'] for record in response.data if record.get('user_id')]))
            
            # Also get users from user_preferences who might not have reading activity yet
            try:
                prefs_response = self.client.table('user_preferences').select('user_id').execute()
                if prefs_response.data:
                    pref_user_ids = [pref['user_id'] for pref in prefs_response.data if pref.get('user_id')]
                    # Add users from preferences who aren't in reading_activity yet
                    for pref_user_id in pref_user_ids:
                        if pref_user_id not in user_ids:
                            user_ids.append(pref_user_id)
            except:
                pass
            
            # Try to get emails via RPC function
            user_emails_map = {}
            try:
                # Try to get emails using the get_user_emails function
                emails_response = self.client.rpc('get_user_emails', {'user_ids': user_ids}).execute()
                if emails_response.data:
                    for record in emails_response.data:
                        user_emails_map[record.get('user_id')] = record.get('email', 'Onbekend')
            except Exception as e:
                print(f"Could not get emails via RPC function: {e}")
                # Continue without emails
            
            # For each user, get their reading statistics
            users_with_stats = []
            
            for user_id in user_ids:
                try:
                    # Get reading statistics
                    stats = self.get_reading_statistics(user_id)
                    
                    # Get email from map or use fallback
                    user_email = user_emails_map.get(user_id, f"user_{user_id[:8]}")
                    
                    users_with_stats.append({
                        'user_id': user_id,
                        'email': user_email,
                        'total_articles_opened': stats.get('total_articles_opened', 0),
                        'total_articles_read': stats.get('total_articles_read', 0),
                        'avg_read_duration_seconds': stats.get('avg_read_duration_seconds', 0),
                        'read_percentage': stats.get('read_percentage', 0)
                    })
                except Exception as e:
                    print(f"Error getting stats for user {user_id}: {e}")
                    continue
            
            # Sort by total_articles_read (descending)
            users_with_stats.sort(key=lambda x: x['total_articles_read'], reverse=True)
            
            return users_with_stats
        except Exception as e:
            print(f"Error getting all users with reading stats via activity: {e}")
            # Fallback to the other method
            return self.get_all_users_with_reading_stats()


# Global instance (for non-Streamlit contexts only)
_supabase_client: Optional[SupabaseClient] = None
_local_storage = None


def create_supabase_client() -> SupabaseClient:
    """Create a new Supabase client instance. Use this for session isolation."""
    # Check if Supabase credentials are available
    # Try Streamlit secrets first, then environment variables
    try:
        from secrets_helper import get_secret
        supabase_url = get_secret('SUPABASE_URL')
        supabase_key = get_secret('SUPABASE_ANON_KEY')
    except Exception as e:
        print(f"DEBUG: Error loading secrets: {e}")
        # Fallback to environment variables if secrets_helper not available
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_ANON_KEY')
    
    if not supabase_url or not supabase_key:
        raise ValueError(
            "SUPABASE_URL and SUPABASE_ANON_KEY must be set. "
            "For local development, add them to your .env file. "
            "For production, add them to Streamlit Secrets."
        )
    
    try:
        client = SupabaseClient()
        print("DEBUG: Supabase client created successfully")
        return client
    except Exception as e:
        raise RuntimeError(
            f"Failed to create Supabase client: {e}. "
            "Please check your SUPABASE_URL and SUPABASE_ANON_KEY."
        ) from e
    

def get_supabase_client():
    """
    Get Supabase client instance with session isolation.
    
    In Streamlit context: Creates a per-session client (stored in st.session_state)
    Outside Streamlit: Uses global singleton (for backwards compatibility)
    """
    # Try to use Streamlit session state for session isolation
    try:
        import streamlit as st
        if hasattr(st, 'session_state'):
            # Use session-specific client for proper isolation
            if 'supabase_client_instance' not in st.session_state:
                st.session_state.supabase_client_instance = create_supabase_client()
            return st.session_state.supabase_client_instance
    except (ImportError, RuntimeError, AttributeError):
        # Not in Streamlit context, use global singleton
        pass
    
    # Fallback to global singleton (for non-Streamlit contexts)
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = create_supabase_client()
    return _supabase_client


def get_local_storage():
    """Get local storage instance for testing without Supabase."""
    global _local_storage
    if _local_storage is None:
        from local_storage import LocalStorage
        _local_storage = LocalStorage()
    return _local_storage

