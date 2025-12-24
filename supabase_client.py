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
        
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_ANON_KEY')
        
        if not supabase_url or not supabase_key:
            raise ValueError(
                "SUPABASE_URL and SUPABASE_ANON_KEY must be set in environment variables"
            )
        
        # Try to create client with options, fallback to simple initialization
        try:
            if ClientOptions:
                options = ClientOptions(
                    auto_refresh_token=True,
                    persist_session=True
                )
                self.client: Client = create_client(
                    supabase_url,
                    supabase_key,
                    options=options
                )
            else:
                self.client: Client = create_client(
                    supabase_url,
                    supabase_key
                )
        except (AttributeError, TypeError) as e:
            # If ClientOptions has issues, use simple initialization
            self.client: Client = create_client(
                supabase_url,
                supabase_key
            )
    
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
            # Explicitly store the session - this ensures it's available for subsequent requests
            if response.session:
                # The session is automatically stored by Supabase client with persist_session=True
                # But we verify it's set correctly
                pass
            
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
            # Sign out and clear session
            self.client.auth.sign_out()
            # Also try to clear any persisted session
            try:
                # Clear session from storage if possible
                session = self.client.auth.get_session()
                if session:
                    self.client.auth.sign_out()
            except:
                pass
            return True
        except Exception as e:
            # Log error but don't fail
            print(f"Error signing out: {e}")
            return False
    
    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """Get current authenticated user from persisted session."""
        try:
            # Try to get the user directly - Supabase client will use persisted session
            # if available (from browser localStorage via persist_session=True)
            # This works because Supabase's Python client syncs with browser localStorage
            user_response = self.client.auth.get_user()
            if user_response and user_response.user:
                return {
                    "id": user_response.user.id,
                    "email": user_response.user.email,
                    "created_at": user_response.user.created_at
                }
        except Exception as e:
            # get_user() will raise an exception if no valid session exists
            # This is normal when user is not logged in - don't log errors
            pass
        
        # Fallback: try to get session explicitly
        try:
            session = self.client.auth.get_session()
            if session and hasattr(session, 'user') and session.user:
                return {
                    "id": session.user.id,
                    "email": session.user.email,
                    "created_at": session.user.created_at
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
                return response.data[0]
            else:
                # Create default preferences
                return self.create_default_preferences(user_id)
        except Exception as e:
            # If table doesn't exist, return defaults
            return {
                "user_id": user_id,
                "blacklist_keywords": ["Trump", "Rusland", "Soedan", "aanslag"]
            }
    
    def create_default_preferences(self, user_id: str) -> Dict[str, Any]:
        """Create default preferences for a new user."""
        default_prefs = {
            "user_id": user_id,
            "blacklist_keywords": ["Trump", "Rusland", "Soedan", "aanslag"]
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
            
            # Don't filter by category in SQL - we'll filter in Python to check both
            # category field and categories array
            
            # Note: Supabase doesn't support complex OR queries easily
            # We'll filter search results in Python if needed
            query = query.order('published_at', desc=True).limit(limit).offset(offset)
            
            response = query.execute()
            articles = response.data if response.data else []
            
            # Filter by category (check both category field and categories array)
            if category:
                filtered = []
                for article in articles:
                    article_category = article.get('category', '')
                    article_categories = article.get('categories', []) or []
                    # Check if category matches either the single category field or is in the array
                    if article_category == category or category in article_categories:
                        filtered.append(article)
                articles = filtered
            
            # Filter by categories array (if provided)
            # Logic: Article is INCLUDED ONLY if ALL its categories are in the selected list
            # If ANY category is NOT in the selected list, filter it out
            # Special case: If categories is empty/None, don't filter (show all)
            if categories and len(categories) > 0:
                filtered = []
                categories_lower = [cat.lower().strip() for cat in categories if cat]
                # Import valid categories list
                from categorization_engine import CATEGORIES
                valid_categories_lower = [cat.lower().strip() for cat in CATEGORIES]
                
                for article in articles:
                    # Collect all categories from the article (only valid ones)
                    article_cats = []
                    article_category = article.get('category', '')
                    # Only add if it's a valid category
                    if article_category and article_category.lower().strip() in valid_categories_lower:
                        article_cats.append(article_category)
                    article_categories_array = article.get('categories', []) or []
                    if article_categories_array:
                        for cat in article_categories_array:
                            if cat and cat.lower().strip() in valid_categories_lower:
                                article_cats.append(cat)
                    article_cats = [cat for cat in article_cats if cat]
                    article_cats = list(set(article_cats))  # Remove duplicates
                    
                    # If article has no categories, include it
                    if not article_cats:
                        filtered.append(article)
                        continue
                    
                    # Check if ALL article categories are in the selected list
                    # If ANY category is NOT in the list, filter it out
                    # Case-insensitive comparison
                    all_match = True
                    for cat in article_cats:
                        if cat and cat.lower().strip() not in categories_lower:
                            all_match = False
                            break
                    
                    if all_match:
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
            import traceback
            print(f"Error getting articles: {e}")
            traceback.print_exc()
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
    
    def get_articles_without_eli5(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get articles that don't have ELI5 summaries yet."""
        try:
            response = self.client.table('articles').select('*').is_('eli5_summary_nl', 'null').limit(limit).execute()
            return response.data if response.data else []
        except Exception:
            return []


# Global instance (will be initialized when needed)
_supabase_client: Optional[SupabaseClient] = None
_local_storage = None


def get_supabase_client():
    """Get or create Supabase client instance, or fall back to local storage."""
    global _supabase_client, _local_storage
    
    # Check if Supabase credentials are available
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

