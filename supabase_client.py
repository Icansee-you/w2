"""
Supabase client for authentication and database operations.
"""
import os
from typing import Optional, Dict, List, Any
try:
    from supabase import create_client, Client
    from supabase.lib.client_options import ClientOptions
except ImportError:
    # Fallback if supabase not installed
    Client = None
    ClientOptions = None


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
                # If selected_categories is missing, None, or empty list, set to all categories
                selected_cats = prefs.get('selected_categories')
                if 'selected_categories' not in prefs or selected_cats is None or (isinstance(selected_cats, list) and len(selected_cats) == 0):
                    from categorization_engine import get_all_categories
                    prefs['selected_categories'] = get_all_categories()
                    # Update in database
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
                "blacklist_keywords": ["Trump", "Rusland", "Soedan", "aanslag"],
                "selected_categories": get_all_categories()
            }
    
    def create_default_preferences(self, user_id: str) -> Dict[str, Any]:
        """Create default preferences for a new user."""
        from categorization_engine import get_all_categories
        all_categories = get_all_categories()
        
        default_prefs = {
            "user_id": user_id,
            "blacklist_keywords": ["Trump", "Rusland", "Soedan", "aanslag"],
            "selected_categories": all_categories  # All categories selected by default
        }
        try:
            response = self.client.table('user_preferences').insert(default_prefs).execute()
            return response.data[0] if response.data else default_prefs
        except Exception:
            return default_prefs
    
    def update_user_preferences(self, user_id: str, blacklist_keywords: List[str] = None, selected_categories: List[str] = None) -> bool:
        """Update user preferences."""
        try:
            from datetime import datetime
            prefs = {
                "user_id": user_id,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            if blacklist_keywords is not None:
                prefs["blacklist_keywords"] = blacklist_keywords
            
            if selected_categories is not None:
                prefs["selected_categories"] = selected_categories
            
            # Try to update first
            update_response = self.client.table('user_preferences').update(prefs).eq('user_id', user_id).execute()
            if not update_response.data:
                # If no existing record, insert
                self.client.table('user_preferences').insert(prefs).execute()
            return True
        except Exception as e:
            print(f"Error updating preferences: {e}")
            return False
    
    # Article methods
    def upsert_article(self, article_data: Dict[str, Any]) -> bool:
        """Insert or update an article in Supabase."""
        try:
            # Ensure categories is a list (Supabase expects array)
            if 'categories' in article_data and article_data['categories']:
                if not isinstance(article_data['categories'], list):
                    article_data['categories'] = list(article_data['categories'])
            else:
                article_data['categories'] = []
            
            self.client.table('articles').upsert(
                article_data,
                on_conflict='stable_id'
            ).execute()
            return True
        except Exception as e:
            print(f"Error upserting article: {e}")
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
        """Get articles from Supabase with optional filters."""
        try:
            query = self.client.table('articles').select('*')
            
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
            if categories:
                filtered = []
                for article in articles:
                    article_categories = article.get('categories', []) or []
                    # Check if any of the requested categories match
                    if any(cat in article_categories for cat in categories):
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
            print(f"Error getting articles: {e}")
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
            update_data = {
                'eli5_summary_nl': eli5_summary,
                'updated_at': 'now()'
            }
            if llm:
                update_data['eli5_llm'] = llm
            
            self.client.table('articles').update(update_data).eq('id', article_id).execute()
            return True
        except Exception as e:
            print(f"Error updating ELI5: {e}")
            return False
    
    def update_article_categories(self, article_id: str, categories: List[str], categorization_llm: str) -> bool:
        """Update article with new categories and LLM used."""
        try:
            update_data = {
                'categories': categories,
                'categorization_llm': categorization_llm,
                'updated_at': 'now()'
            }
            
            self.client.table('articles').update(update_data).eq('id', article_id).execute()
            return True
        except Exception as e:
            print(f"Error updating categories: {e}")
            return False
    
    def get_articles_without_eli5(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get articles that don't have ELI5 summaries yet."""
        try:
            response = self.client.table('articles').select('*').is_('eli5_summary_nl', 'null').limit(limit).execute()
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
    
    def delete_old_articles(self, days_old: int = 7) -> Dict[str, Any]:
        """
        Delete articles older than specified number of days.
        
        Args:
            days_old: Number of days old (default: 7 for 1 week)
        
        Returns:
            Dict with count of deleted articles and any errors
        """
        try:
            from datetime import datetime, timedelta
            import pytz
            
            # Calculate cutoff date (articles older than this will be deleted)
            cutoff_date = datetime.now(pytz.UTC) - timedelta(days=days_old)
            cutoff_date_str = cutoff_date.isoformat()
            
            print(f"[Delete Old Articles] Deleting articles older than {days_old} days (before {cutoff_date_str})")
            
            # First, get count of articles to be deleted (for logging)
            try:
                count_response = self.client.table('articles').select('id', count='exact').lt('published_at', cutoff_date_str).execute()
                count = count_response.count if hasattr(count_response, 'count') and count_response.count is not None else 0
            except Exception as e:
                print(f"[Delete Old Articles] Error counting articles: {e}")
                count = 0
            
            if count == 0:
                print(f"[Delete Old Articles] No articles older than {days_old} days found")
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
        """Get statistics about articles and ELI5 summaries."""
        try:
            # Get total article count
            articles_response = self.client.table('articles').select('id', count='exact').execute()
            total_articles = articles_response.count if hasattr(articles_response, 'count') else len(articles_response.data) if articles_response.data else 0
            
            # Get articles with ELI5
            eli5_response = self.client.table('articles').select('id', count='exact').not_.is_('eli5_summary_nl', 'null').execute()
            articles_with_eli5 = eli5_response.count if hasattr(eli5_response, 'count') else len(eli5_response.data) if eli5_response.data else 0
            
            # Get all articles with categories
            all_articles_response = self.client.table('articles').select('categories, categorization_llm').execute()
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


# Global instance (will be initialized when needed)
_supabase_client: Optional[SupabaseClient] = None
_local_storage = None


def get_supabase_client():
    """Get or create Supabase client instance, or fall back to local storage."""
    global _supabase_client, _local_storage
    
    # Check if Supabase credentials are available
    # Try Streamlit secrets first, then environment variables
    try:
        from secrets_helper import get_secret
        supabase_url = get_secret('SUPABASE_URL')
        supabase_key = get_secret('SUPABASE_ANON_KEY')
    except:
        # Fallback to environment variables if secrets_helper not available
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_ANON_KEY')
    
    if supabase_url and supabase_key:
        # Use Supabase
        if _supabase_client is None:
            try:
                _supabase_client = SupabaseClient()
            except Exception as e:
                print(f"Warning: Could not initialize Supabase: {e}")
                print("Falling back to local storage for testing...")
                return get_local_storage()
        return _supabase_client
    else:
        # Use local storage for testing
        return get_local_storage()


def get_local_storage():
    """Get local storage instance for testing without Supabase."""
    global _local_storage
    if _local_storage is None:
        from local_storage import LocalStorage
        _local_storage = LocalStorage()
    return _local_storage

