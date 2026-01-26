"""
Local storage for testing without Supabase.
Uses SQLite database for articles and JSON file for user preferences.
"""
import os
import sqlite3
import json
from typing import Optional, Dict, List, Any
from pathlib import Path
from datetime import datetime
import hashlib


class LocalStorage:
    """Local storage implementation for testing without Supabase."""
    
    def __init__(self, db_path: str = "local_test.db"):
        """Initialize local storage."""
        self.db_path = db_path
        self.preferences_file = Path("local_preferences.json")
        self._init_database()
        self._init_preferences()
    
    def _init_database(self):
        """Initialize SQLite database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create articles table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS articles (
                id TEXT PRIMARY KEY,
                stable_id TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                url TEXT NOT NULL,
                source TEXT DEFAULT 'NOS',
                published_at TEXT,
                full_content TEXT,
                image_url TEXT,
                category TEXT,
                categories TEXT,
                categorization_llm TEXT,
                eli5_summary_nl TEXT,
                eli5_llm TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Migrate: Add categories column if it doesn't exist (for existing databases)
        try:
            cursor.execute("PRAGMA table_info(articles)")
            columns = [row[1] for row in cursor.fetchall()]
            if 'categories' not in columns:
                cursor.execute("ALTER TABLE articles ADD COLUMN categories TEXT")
            if 'categorization_llm' not in columns:
                cursor.execute("ALTER TABLE articles ADD COLUMN categorization_llm TEXT")
        except Exception:
            pass  # Column might already exist or table doesn't exist yet
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_stable_id ON articles(stable_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_published_at ON articles(published_at DESC)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_category ON articles(category)")
        
        conn.commit()
        conn.close()
    
    def _init_preferences(self):
        """Initialize preferences file."""
        if not self.preferences_file.exists():
            with open(self.preferences_file, 'w') as f:
                json.dump({}, f)
    
    # Mock authentication (for local testing)
    def sign_up(self, email: str, password: str) -> Dict[str, Any]:
        """Mock sign up - just creates a local user."""
        return {
            "success": True,
            "user": {"id": hashlib.md5(email.encode()).hexdigest(), "email": email}
        }
    
    def sign_in(self, email: str, password: str) -> Dict[str, Any]:
        """Mock sign in - accepts any email/password."""
        return {
            "success": True,
            "user": {"id": hashlib.md5(email.encode()).hexdigest(), "email": email}
        }
    
    def sign_out(self) -> bool:
        """Mock sign out."""
        return True
    
    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """Get current user from session (mock)."""
        # For local testing, return a default user
        return {"id": "local_user", "email": "test@local.com"}
    
    def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get user preferences from JSON file."""
        try:
            with open(self.preferences_file, 'r') as f:
                all_prefs = json.load(f)
                if user_id in all_prefs:
                    prefs = all_prefs[user_id]
                    # Ensure selected_categories exists
                    if 'selected_categories' not in prefs:
                        from categorization_engine import get_all_categories
                        prefs['selected_categories'] = get_all_categories()
                    return prefs
        except Exception:
            pass
        
        # Return defaults
        from categorization_engine import get_all_categories
        return {
            "user_id": user_id,
            "blacklist_keywords": [],  # No keywords blocked by default for new users
            "selected_categories": get_all_categories()  # All categories selected by default
        }
    
    def update_user_preferences(self, user_id: str, blacklist_keywords: List[str] = None, selected_categories: List[str] = None) -> bool:
        """Update user preferences in JSON file."""
        try:
            with open(self.preferences_file, 'r') as f:
                all_prefs = json.load(f)
        except Exception:
            all_prefs = {}
        
        # Get existing preferences or create new
        if user_id in all_prefs:
            prefs = all_prefs[user_id]
        else:
            prefs = {}
        
        if blacklist_keywords is not None:
            prefs["blacklist_keywords"] = blacklist_keywords
        
        if selected_categories is not None:
            prefs["selected_categories"] = selected_categories
        
        prefs["user_id"] = user_id
        prefs["updated_at"] = datetime.utcnow().isoformat()
        
        all_prefs[user_id] = prefs
        
        with open(self.preferences_file, 'w') as f:
            json.dump(all_prefs, f, indent=2)
        
        return True
    
    def upsert_article(self, article_data: Dict[str, Any]) -> bool:
        """Insert or update article in SQLite."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if exists
            cursor.execute("SELECT id FROM articles WHERE stable_id = ?", (article_data['stable_id'],))
            existing = cursor.fetchone()
            
            if existing:
                # Update
                # Convert categories list to JSON string for SQLite
                categories_json = json.dumps(article_data.get('categories', [])) if article_data.get('categories') else None
                cursor.execute("""
                    UPDATE articles SET
                        title = ?, description = ?, url = ?, source = ?,
                        published_at = ?, full_content = ?, image_url = ?,
                        category = ?, categories = ?, categorization_llm = ?,
                        eli5_summary_nl = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE stable_id = ?
                """, (
                    article_data.get('title'),
                    article_data.get('description'),
                    article_data.get('url'),
                    article_data.get('source', 'NOS'),
                    article_data.get('published_at'),
                    article_data.get('full_content'),
                    article_data.get('image_url'),
                    article_data.get('category'),
                    categories_json,
                    article_data.get('categorization_llm', 'Keywords'),
                    article_data.get('eli5_summary_nl'),
                    article_data['stable_id']
                ))
            else:
                # Insert
                article_id = hashlib.md5(article_data['stable_id'].encode()).hexdigest()
                categories_json = json.dumps(article_data.get('categories', [])) if article_data.get('categories') else None
                cursor.execute("""
                    INSERT INTO articles (
                        id, stable_id, title, description, url, source,
                        published_at, full_content, image_url, category,
                        categories, categorization_llm, eli5_summary_nl, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """, (
                    article_id,
                    article_data['stable_id'],
                    article_data.get('title'),
                    article_data.get('description'),
                    article_data.get('url'),
                    article_data.get('source', 'NOS'),
                    article_data.get('published_at'),
                    article_data.get('full_content'),
                    article_data.get('image_url'),
                    article_data.get('category'),
                    categories_json,
                    article_data.get('categorization_llm', 'Keywords'),
                    article_data.get('eli5_summary_nl')
                ))
            
            conn.commit()
            conn.close()
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
        """Get articles from SQLite."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = "SELECT * FROM articles WHERE 1=1"
            params = []
            
            if category:
                query += " AND category = ?"
                params.append(category)
            
            query += " ORDER BY published_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            articles = []
            for row in rows:
                article = dict(row)
                # Parse categories from JSON string
                if article.get('categories'):
                    try:
                        article['categories'] = json.loads(article['categories'])
                    except:
                        article['categories'] = []
                else:
                    article['categories'] = []
                articles.append(article)
            
            # Filter by categories array (if provided)
            if categories:
                filtered = []
                for article in articles:
                    article_categories = article.get('categories', []) or []
                    # Check if any of the requested categories match
                    if any(cat in article_categories for cat in categories):
                        filtered.append(article)
                articles = filtered
            
            # Apply search filter
            if search_query:
                search_lower = search_query.lower()
                articles = [
                    a for a in articles
                    if search_lower in (a.get('title', '') or '').lower() or
                       search_lower in (a.get('description', '') or '').lower() or
                       search_lower in (a.get('full_content', '') or '').lower()
                ]
            
            # Apply blacklist filter
            if blacklist_keywords:
                filtered = []
                for article in articles:
                    # Check title, description, and full_content
                    title = (article.get('title', '') or '').lower()
                    description = (article.get('description', '') or '').lower()
                    full_content = (article.get('full_content', '') or '').lower()
                    
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
                        filtered.append(article)
                
                articles = filtered
            
            conn.close()
            return articles
        except Exception as e:
            print(f"Error getting articles: {e}")
            return []
    
    def get_article_by_id(self, article_id: str) -> Optional[Dict[str, Any]]:
        """Get a single article by ID."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM articles WHERE id = ? OR stable_id = ?", (article_id, article_id))
            row = cursor.fetchone()
            
            if row:
                article = dict(row)
                # Parse categories from JSON string
                if article.get('categories'):
                    try:
                        article['categories'] = json.loads(article['categories'])
                    except:
                        article['categories'] = []
                else:
                    article['categories'] = []
                return article
            return None
        except Exception as e:
            print(f"Error getting article by ID: {e}")
            return None
        """Get article by ID."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM articles WHERE id = ?", (article_id,))
            row = cursor.fetchone()
            
            conn.close()
            return dict(row) if row else None
        except Exception:
            return None
    
    def update_article_eli5(self, article_id: str, eli5_summary: str, llm: str = None) -> bool:
        """Update article ELI5 summary and LLM used."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if eli5_llm column exists, add if not
            cursor.execute("PRAGMA table_info(articles)")
            columns = [row[1] for row in cursor.fetchall()]
            if 'eli5_llm' not in columns:
                cursor.execute("ALTER TABLE articles ADD COLUMN eli5_llm TEXT")
            
            cursor.execute(
                "UPDATE articles SET eli5_summary_nl = ?, eli5_llm = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (eli5_summary, llm, article_id)
            )
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error updating ELI5: {e}")
            return False
    
    def get_articles_without_eli5(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get articles without ELI5 summaries."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT * FROM articles WHERE eli5_summary_nl IS NULL OR eli5_summary_nl = '' LIMIT ?",
                (limit,)
            )
            rows = cursor.fetchall()
            
            conn.close()
            return [dict(row) for row in rows]
        except Exception:
            return []

