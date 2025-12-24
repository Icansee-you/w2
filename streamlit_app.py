"""
Streamlit app for NOS News Aggregator with horizontal menu.
Pages: Nieuws, Waarom?, Gebruiker
"""
import os
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import pytz

# Add project root to Python path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Load environment variables from .env file if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, skip .env loading

import streamlit as st
import re
from html import unescape
from supabase_client import get_supabase_client
from articles_repository import fetch_and_upsert_articles, generate_missing_eli5_summaries
from nlp_utils import generate_eli5_summary_nl_with_llm
from background_scheduler import start_background_scheduler, is_scheduler_running

# Page configuration
st.set_page_config(
    page_title="NOS Nieuws Aggregator",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Hide default Streamlit menu and footer
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Horizontal menu */
    .horizontal-menu {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 2rem;
        padding: 1rem 0;
        border-bottom: 2px solid #e0e0e0;
        margin-bottom: 2rem;
        background-color: #ffffff;
    }
    
    .menu-items-container {
        display: flex;
        justify-content: center;
        gap: 2rem;
        flex: 1;
    }
    
    .user-indicator {
        font-size: 0.75rem;
        color: #888;
        padding: 0.5rem 1rem;
        white-space: nowrap;
        margin-left: auto;
        text-align: right;
    }
    
    .menu-item {
        font-size: 1.2rem;
        font-weight: 500;
        color: #666;
        text-decoration: none;
        padding: 0.5rem 1rem;
        border-radius: 4px;
        transition: all 0.2s;
        cursor: pointer;
    }
    
    .menu-item:hover {
        background-color: #f0f0f0;
        color: #1f77b4;
    }
    
    .menu-item.active {
        color: #1f77b4;
        border-bottom: 3px solid #1f77b4;
    }
    
    /* Article cards */
    .article-card {
        padding: 1rem;
        margin-bottom: 1.5rem;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        background-color: #ffffff;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: transform 0.2s, box-shadow 0.2s;
    }
    
    .article-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }
    
    .article-image {
        width: 100%;
        max-height: 200px;
        object-fit: cover;
        border-radius: 4px;
        margin-bottom: 0.75rem;
    }
    
    .article-title {
        font-size: 1.1rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 0.5rem;
        line-height: 1.4;
    }
    
    .article-meta {
        font-size: 0.85rem;
        color: #666;
        margin-bottom: 0.5rem;
    }
    
    .article-summary {
        font-size: 0.9rem;
        color: #333;
        line-height: 1.5;
        margin: 0.5rem 0;
    }
    
    /* Larger button for article summary - show full text */
    div[data-testid="stButton"] > button[kind="secondary"] {
        min-height: 80px;
        height: auto;
        white-space: normal;
        word-wrap: break-word;
        overflow-wrap: break-word;
        padding: 1rem 1.25rem;
        text-align: left;
        line-height: 1.6;
        font-size: 0.95rem;
        display: flex;
        align-items: flex-start;
        justify-content: flex-start;
    }
    
    /* Specific styling for summary buttons */
    button[key^="summary_"] {
        min-height: 80px !important;
        height: auto !important;
        white-space: normal !important;
        word-wrap: break-word !important;
        overflow-wrap: break-word !important;
        text-overflow: unset !important;
    }
    
    .categories-container {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin: 0.5rem 0;
    }
    
    .article-category {
        display: inline-block;
        background-color: #e3f2fd;
        color: #1976d2;
        padding: 0.4rem 0.8rem;
        border-radius: 12px;
        font-size: 0.9rem;
        white-space: nowrap;
        margin: 0;
        word-break: keep-all;
        overflow-wrap: normal;
    }
    
    .eli5-box {
        background-color: #f0f7ff;
        border-left: 4px solid #1f77b4;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 4px;
    }
    
    .eli5-title {
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    
    .eli5-llm-badge {
        font-size: 0.75rem;
        color: #666;
        font-style: italic;
        margin-top: 0.5rem;
    }
    
    /* Compact article detail page */
    .article-detail-container {
        max-width: 900px;
        margin: 0 auto;
    }
    
    .article-detail-image {
        max-width: 50% !important;
        margin: 0 auto;
        display: block;
    }
    
    /* Responsive header image with abstract sunrise */
    .header-image-container {
        width: 100%;
        height: 200px;
        background: linear-gradient(135deg, #ff6b6b 0%, #ffa500 25%, #ffd700 50%, #ff8c00 75%, #ff6347 100%);
        background-size: cover;
        background-position: center;
        margin: 0;
        padding: 0;
        position: relative;
        overflow: hidden;
    }
    
    .header-image-container::before {
        content: '';
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        height: 60%;
        background: linear-gradient(to top, rgba(255, 140, 0, 0.8) 0%, rgba(255, 215, 0, 0.6) 30%, rgba(255, 165, 0, 0.4) 60%, transparent 100%);
    }
    
    .header-image-container::after {
        content: '';
        position: absolute;
        top: 20%;
        left: 50%;
        transform: translateX(-50%);
        width: 120px;
        height: 120px;
        background: radial-gradient(circle, rgba(255, 255, 255, 0.9) 0%, rgba(255, 255, 200, 0.7) 40%, transparent 70%);
        border-radius: 50%;
        box-shadow: 0 0 60px rgba(255, 255, 200, 0.8);
    }
    
    @media (max-width: 768px) {
        .horizontal-menu {
            flex-direction: column;
            gap: 0.5rem;
        }
        .menu-item {
            text-align: center;
        }
        .header-image-container {
            height: 150px;
        }
        .header-image-container::after {
            width: 80px;
            height: 80px;
        }
    }
    
    @media (min-width: 1200px) {
        .header-image-container {
            height: 250px;
        }
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'user' not in st.session_state:
    st.session_state.user = None
if 'supabase' not in st.session_state:
    st.session_state.supabase = None
if 'preferences' not in st.session_state:
    st.session_state.preferences = None
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'Nieuws'
if 'last_fetch_time' not in st.session_state:
    st.session_state.last_fetch_time = None
if 'is_fetching' not in st.session_state:
    st.session_state.is_fetching = False
if 'supabase_session_token' not in st.session_state:
    st.session_state.supabase_session_token = None
if 'supabase_refresh_token' not in st.session_state:
    st.session_state.supabase_refresh_token = None


def set_cookie(name: str, value: str, days: int = 30):
    """Set a cookie using JavaScript."""
    if not value:
        # Delete cookie
        js_code = f"""
        <script>
        document.cookie = "{name}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
        </script>
        """
    else:
        # Set cookie with expiration
        js_code = f"""
        <script>
        const expires = new Date();
        expires.setTime(expires.getTime() + ({days} * 24 * 60 * 60 * 1000));
        document.cookie = "{name}={value}; expires=" + expires.toUTCString() + "; path=/; SameSite=Lax";
        </script>
        """
    st.markdown(js_code, unsafe_allow_html=True)


def get_cookie(name: str) -> Optional[str]:
    """Get a cookie value using JavaScript and return via query params."""
    cookie_key = f"_cookie_{name}"
    
    # Check if we already have it in session state
    if cookie_key in st.session_state:
        return st.session_state[cookie_key]
    
    # Use JavaScript to read cookie and pass to Python via query params
    # This will work on the next rerun
    js_code = f"""
    <script>
    (function() {{
        function getCookie(name) {{
            const value = `; ${{document.cookie}}`;
            const parts = value.split(`; ${{name}}=`);
            if (parts.length === 2) {{
                const val = parts.pop().split(';').shift();
                // Store in URL query params so Python can read it
                const url = new URL(window.location);
                if (val) {{
                    url.searchParams.set("_cookie_{name}", val);
                    window.history.replaceState({{}}, '', url);
                }}
                return val;
            }}
            return null;
        }}
        getCookie("{name}");
    }})();
    </script>
    """
    st.markdown(js_code, unsafe_allow_html=True)
    
    # Try to read from query params (set by JavaScript)
    cookie_value = st.query_params.get(f"_cookie_{name}")
    if cookie_value:
        st.session_state[cookie_key] = cookie_value
        # Clean up query param after reading
        params = dict(st.query_params)
        if f"_cookie_{name}" in params:
            del params[f"_cookie_{name}"]
            st.query_params.clear()
            for k, v in params.items():
                st.query_params[k] = v
        return cookie_value
    
    return None


def init_supabase():
    """Initialize Supabase client or local storage."""
    try:
        if st.session_state.supabase is None:
            st.session_state.supabase = get_supabase_client()
            
            # Supabase is initialized (or local storage fallback)
        
        return st.session_state.supabase
    except Exception as e:
        st.error(f"Error initializing storage: {str(e)}")
        return None


def get_user_attr(user, attr: str, default=None):
    """Safely get user attribute from dict or Pydantic object."""
    if user is None:
        return default
    
    # If it's a dictionary
    if isinstance(user, dict):
        return user.get(attr, default)
    
    # If it's a Pydantic object or has attributes
    if hasattr(user, attr):
        return getattr(user, attr, default)
    
    # Try to access as dict if it has __getitem__
    try:
        return user[attr]
    except (TypeError, KeyError):
        pass
    
    return default


def render_horizontal_menu():
    """Render horizontal navigation menu."""
    # Get user email for display
    user_email = "geen"
    if st.session_state.user:
        user_email = get_user_attr(st.session_state.user, 'email', 'geen')
    
    menu_html = f"""
    <div class="horizontal-menu">
        <div class="menu-items-container">
        <a class="menu-item" href="?page=Nieuws" onclick="window.location.href='?page=Nieuws'; return false;" target="_self">Nieuws</a>
        <a class="menu-item" href="?page=Waarom" onclick="window.location.href='?page=Waarom'; return false;" target="_self">Waarom?</a>
            <a class="menu-item" href="?page=Frustrate" onclick="window.location.href='?page=Frustrate'; return false;" target="_self">Dit wil je niet</a>
        <a class="menu-item" href="?page=Gebruiker" onclick="window.location.href='?page=Gebruiker'; return false;" target="_self">Gebruiker</a>
        </div>
        <div class="user-indicator">Ingelogde gebruiker: {user_email}</div>
    </div>
    """
    st.markdown(menu_html, unsafe_allow_html=True)
    
    # Update current page from query params
    page = st.query_params.get("page", "Nieuws")
    if page in ["Nieuws", "Waarom", "Frustrate", "Gebruiker"]:
        st.session_state.current_page = page


def strip_html_tags(text: str) -> str:
    """Remove HTML tags from text (for summary extraction)."""
    if not text:
        return ""
    text = re.sub(r'<[^>]+>', '', text)
    text = unescape(text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def clean_html_for_display(text: str) -> str:
    """Clean HTML but preserve formatting tags like <p>, <br>, <strong>, <em>."""
    if not text:
        return ""
    
    # Unescape HTML entities
    text = unescape(text)
    
    # Remove dangerous/script tags but keep formatting tags
    # Keep: p, br, strong, em, b, i, u, h1-h6, ul, ol, li, blockquote, a
    # Remove: script, style, iframe, object, embed, form, input, button
    dangerous_tags = ['script', 'style', 'iframe', 'object', 'embed', 'form', 'input', 'button', 'onclick', 'onerror']
    
    for tag in dangerous_tags:
        # Remove opening and closing tags
        text = re.sub(rf'<{tag}[^>]*>.*?</{tag}>', '', text, flags=re.IGNORECASE | re.DOTALL)
        # Remove self-closing tags
        text = re.sub(rf'<{tag}[^>]*/?>', '', text, flags=re.IGNORECASE)
    
    # Remove onclick and other event handlers from remaining tags
    text = re.sub(r'\s+on\w+="[^"]*"', '', text, flags=re.IGNORECASE)
    text = re.sub(r"\s+on\w+='[^']*'", '', text, flags=re.IGNORECASE)
    
    # Clean up multiple spaces but preserve line breaks from <br> and <p>
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
    
    return text.strip()


def format_datetime(dt_str: Optional[str]) -> str:
    """Format datetime string for display."""
    if not dt_str:
        return ""
    try:
        from dateutil import parser
        dt = parser.parse(dt_str)
        amsterdam_tz = pytz.timezone('Europe/Amsterdam')
        if dt.tzinfo is None:
            dt = pytz.utc.localize(dt)
        dt = dt.astimezone(amsterdam_tz)
        return dt.strftime('%d %B %Y, %H:%M')
    except Exception:
        return dt_str


def get_summary_sentences(text: str, num_sentences: int = 3) -> str:
    """Extract first N complete sentences from text."""
    if not text:
        return ""
    text = strip_html_tags(text)
    
    # Better sentence splitting - handle multiple sentence endings
    # Split on sentence endings followed by space and capital letter or end of string
    sentences = re.split(r'([.!?]+)\s+(?=[A-Z]|$)', text)
    
    # Reconstruct sentences with their punctuation
    complete_sentences = []
    i = 0
    while i < len(sentences):
        if i + 1 < len(sentences) and re.match(r'[.!?]+', sentences[i + 1]):
            # This is a sentence with punctuation
            sentence = (sentences[i] + sentences[i + 1]).strip()
            if sentence:
                complete_sentences.append(sentence)
            i += 2
        else:
            # Last part or no punctuation found
            if sentences[i].strip():
                complete_sentences.append(sentences[i].strip())
            i += 1
    
    # If regex splitting didn't work well, try simpler approach
    if len(complete_sentences) < num_sentences:
        # Fallback: split on sentence endings
        sentences = re.split(r'([.!?]+)\s+', text)
        complete_sentences = []
        for i in range(0, len(sentences) - 1, 2):
            if i + 1 < len(sentences):
                sentence = (sentences[i] + sentences[i + 1]).strip()
                if sentence:
                    complete_sentences.append(sentence)
        if len(sentences) % 2 == 1 and sentences[-1].strip():
            complete_sentences.append(sentences[-1].strip())
    
    # Take first N sentences and join them
    if len(complete_sentences) >= num_sentences:
        summary = ' '.join(complete_sentences[:num_sentences])
        # Ensure it ends with punctuation
        if summary and not summary[-1] in '.!?':
            summary += '.'
        return summary
    elif complete_sentences:
        # Return all available sentences
        summary = ' '.join(complete_sentences)
        if summary and not summary[-1] in '.!?':
            summary += '.'
        return summary
    else:
        # Fallback: return first part of text (up to reasonable length)
        text_clean = text.strip()
        if len(text_clean) > 300:
            # Try to find a sentence ending within first 300 chars
            match = re.search(r'[.!?]+\s+', text_clean[:300])
            if match:
                return text_clean[:match.end()].strip()
            return text_clean[:300].strip() + '...'
        return text_clean


def article_matches_category_filter(article: Dict[str, Any], selected_categories: List[str]) -> bool:
    """
    Check if article matches category filter.
    
    Logic: Article is INCLUDED ONLY if ALL its categories are in selected_categories.
    If article has ANY category NOT in selected_categories, it is FILTERED OUT.
    
    Special case: If no categories are selected, show all articles (no filter).
    
    Args:
        article: Article dictionary
        selected_categories: List of selected category names
    
    Returns:
        True if article should be INCLUDED (all categories are selected), False if FILTERED OUT
    """
    if not selected_categories or len(selected_categories) == 0:
        # No categories selected = show all articles (no filter)
        return True
    
    # Collect all categories from the article
    # Only use valid categories from the CATEGORIES list
    from categorization_engine import CATEGORIES
    valid_categories = [cat.lower().strip() for cat in CATEGORIES]
    
    article_categories = []
    
    # Add single category field if present AND it's a valid category
    article_category = article.get('category', '')
    if article_category and article_category.lower().strip() in valid_categories:
        article_categories.append(article_category)
    
    # Add categories from array if present (only valid ones)
    article_categories_array = article.get('categories', []) or []
    if article_categories_array:
        for cat in article_categories_array:
            if cat and cat.lower().strip() in valid_categories:
                article_categories.append(cat)
    
    # Remove duplicates and empty values
    article_categories = [cat for cat in article_categories if cat]
    article_categories = list(set(article_categories))  # Remove duplicates
    
    # If article has no categories, include it (no filter applies)
    if not article_categories:
        return True
    
    # Check if ALL article categories are in selected_categories
    # If ANY category is NOT in selected_categories, filter it out
    # Case-insensitive comparison to handle variations
    selected_lower = [cat.lower().strip() for cat in selected_categories if cat]
    for cat in article_categories:
        if cat and cat.lower().strip() not in selected_lower:
            return False  # This category is not selected, so filter out
    
    # All categories are in selected_categories
    return True


def ensure_eli5_summary(article: Dict[str, Any], supabase, generate_if_missing: bool = False) -> Dict[str, Any]:
    """
    Ensure article has ELI5 summary.
    
    Args:
        article: Article dict
        supabase: Supabase client
        generate_if_missing: If True, generate summary synchronously (can freeze page). 
                            If False, only return existing summary (default).
    """
    if not article.get('eli5_summary_nl'):
        if generate_if_missing:
            # Generate ELI5 summary (can take 30+ seconds - use with caution)
            with st.spinner("Eenvoudige uitleg genereren..."):
        text = f"{article.get('title', '')} {article.get('description', '')}"
        if article.get('full_content'):
            text += f" {article.get('full_content', '')[:1000]}"
        
        result = generate_eli5_summary_nl_with_llm(text, article.get('title', ''))
        if result and result.get('summary'):
            article['eli5_summary_nl'] = result['summary']
            article['eli5_llm'] = result.get('llm', 'Onbekend')
            # Save to database
            supabase.update_article_eli5(article['id'], result['summary'], result.get('llm'))
        else:
                    article['eli5_summary_nl'] = None
                    article['eli5_llm'] = None
        else:
            # Don't generate, just return existing or None
            article['eli5_summary_nl'] = None
            article['eli5_llm'] = None
    else:
        # Get LLM info if available
        article['eli5_llm'] = article.get('eli5_llm', 'Onbekend')
    
    return article


def render_article_card(article: Dict[str, Any], supabase):
    """Render a single article card (overview - only image and summary)."""
    article_id = article['id']
    
    # Create a container for the clickable card
    with st.container():
        # Image
    if article.get('image_url'):
            try:
                st.image(article['image_url'], use_container_width=True)
            except:
                pass
    
        # Title (clickable - this is the main way to open article)
    title = article.get('title', 'Geen titel')
        title_display = title[:70] + "..." if len(title) > 70 else title
        if st.button(title_display, key=f"article_{article_id}", use_container_width=True):
        st.query_params["article"] = article_id
        st.rerun()
    
        # Summary from article content (first sentences) - clickable
        full_content = article.get('full_content', '')
        if full_content:
            # Get first 3-4 complete sentences from the article content
            summary = get_summary_sentences(full_content, num_sentences=3)
            if summary:
                # Make the summary clickable - show full text without truncation
                # Use a button with proper styling to show complete sentences
                if st.button(summary, key=f"summary_{article_id}", use_container_width=True):
                    st.query_params["article"] = article_id
                    st.rerun()


def render_article_detail(article_id: str):
    """Render full article detail page."""
    supabase = st.session_state.supabase
    article = supabase.get_article_by_id(article_id)
    
    if not article:
        st.error("Artikel niet gevonden")
        if st.button("← Terug"):
            del st.query_params["article"]
            st.rerun()
        return
    
    # Don't generate ELI5 automatically (prevents freezing)
    # Only use existing summary if available
    article = ensure_eli5_summary(article, supabase, generate_if_missing=False)
    
    st.markdown('<div class="article-detail-container">', unsafe_allow_html=True)
    
    if st.button("← Terug naar overzicht"):
        del st.query_params["article"]
        st.rerun()
    
    st.title(article.get('title', 'Geen titel'))
    
    meta = []
    if article.get('published_at'):
        meta.append(format_datetime(article['published_at']))
    if meta:
        st.caption(" | ".join(meta))
    
    st.markdown("---")
    
    # Layout: Image on left, Categorization info on right
    col_img, col_cat = st.columns([1, 1])
    
        with col_img:
        # Image on the left
        if article.get('image_url'):
            try:
                st.image(article['image_url'], use_container_width=True)
            except:
                pass
    
    with col_cat:
        # Categorization information on the right
    categories = article.get('categories', [])
    
    # Handle categories if they're stored as a string (JSON) or list
    if isinstance(categories, str):
        try:
            import json
            categories = json.loads(categories)
        except:
            # If it's a string but not JSON, try to parse it manually
            if categories.strip().startswith('['):
                # Remove brackets and split by comma
                categories = [c.strip().strip('"\'') for c in categories.strip('[]').split(',') if c.strip()]
            else:
                categories = []
    
    # Ensure categories is a list
    if not isinstance(categories, list):
        categories = []
    
    if categories and len(categories) > 0:
        st.subheader("Categorieën")
        # Display categories in a horizontal flex container
        # Use proper HTML escaping for category names
        from html import escape
        categories_html = '<div class="categories-container">'
        for cat in categories:
            if cat:  # Only add non-empty categories
                escaped_cat = escape(str(cat))
                categories_html += f'<span class="article-category">{escaped_cat}</span>'
        categories_html += '</div>'
        st.markdown(categories_html, unsafe_allow_html=True)
        
        # Show which LLM was used for categorization
        categorization_llm = article.get('categorization_llm', 'Keywords')
        if categorization_llm and categorization_llm != 'Keywords':
            llm_display = {
                'Hugging Face': 'Hugging Face',
                'Groq': 'Groq',
                'OpenAI': 'OpenAI',
                'ChatLLM': 'ChatLLM (Aitomatic)'
            }.get(categorization_llm, categorization_llm)
            st.caption(f"📊 Categorisatie door: {llm_display}")
        else:
            st.caption("📊 Categorisatie door: Keywords (geen LLM)")
        else:
            st.subheader("Categorieën")
            st.info("Geen categorieën beschikbaar")
        
        st.markdown("---")
    
    # Description
    if article.get('description'):
        st.subheader("Samenvatting")
        clean_description = clean_html_for_display(article['description'])
        st.markdown(clean_description, unsafe_allow_html=True)
        st.markdown("---")
    
    # ELI5 Summary (show existing or allow generation on demand)
    # Check if we need to generate
    if not article.get('eli5_summary_nl'):
        # Show button to generate ELI5 summary (prevents freezing)
        if st.button("✨ Genereer eenvoudige uitleg (ELI5)", key=f"generate_eli5_{article.get('id', article_id)}"):
            article = ensure_eli5_summary(article, supabase, generate_if_missing=True)
            st.rerun()
    
    if article.get('eli5_summary_nl'):
        llm_name = article.get('eli5_llm', 'Onbekend')
        llm_display = {
            'ChatLLM': 'ChatLLM (Aitomatic)',
            'Groq': 'Groq',
            'HuggingFace': 'Hugging Face',
            'OpenAI': 'OpenAI',
            'Simple': 'Eenvoudige extractie'
        }.get(llm_name, llm_name)
        
        st.markdown(f"""
        <div class="eli5-box">
            <div class="eli5-title">📚 Leg uit alsof ik 5 ben:</div>
            {article['eli5_summary_nl']}
            <div class="eli5-llm-badge">Gegenereerd met: {llm_display}</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("---")
    else:
        # Show message if ELI5 generation failed
        st.info("⚠️ Eenvoudige uitleg kon niet worden gegenereerd. Probeer het later opnieuw.")
        st.markdown("---")
    
    # Full content
    if article.get('full_content'):
        st.subheader("Volledige inhoud")
        clean_content = clean_html_for_display(article['full_content'])
        st.markdown(clean_content, unsafe_allow_html=True)
    
    # Source link
    st.markdown("---")
    if article.get('url'):
        st.markdown(f"**Bron:** {article.get('source', 'NOS')} — [Bekijk origineel artikel]({article['url']})")
    
    st.markdown('</div>', unsafe_allow_html=True)


def check_and_fetch_new_articles():
    """Check if 15 minutes have passed since last fetch and fetch new articles if needed."""
    import time
    from datetime import datetime, timedelta
    
    # Check if we're already fetching to avoid duplicate fetches
    if st.session_state.is_fetching:
        return
    
    # Check if 15 minutes have passed since last fetch
    should_fetch = False
    if st.session_state.last_fetch_time is None:
        # First time, fetch immediately
        should_fetch = True
    else:
        # Check if 15 minutes (900 seconds) have passed
        time_since_last_fetch = time.time() - st.session_state.last_fetch_time
        if time_since_last_fetch >= 900:  # 15 minutes
            should_fetch = True
    
    if should_fetch:
        st.session_state.is_fetching = True
        
        # Fetch articles in background (non-blocking)
        feed_urls = [
            'https://feeds.nos.nl/nosnieuwsalgemeen',
            'https://feeds.nos.nl/nosnieuwsbinnenland',
            'https://feeds.nos.nl/nosnieuwsbuitenland',
        ]
        
        total_inserted = 0
        total_updated = 0
        
        # Use a placeholder to show status
        status_placeholder = st.empty()
        status_placeholder.info("🔄 Controleren op nieuwe artikelen...")
        
        try:
            for feed_url in feed_urls:
            try:
                # Use LLM categorization for better accuracy
                result = fetch_and_upsert_articles(feed_url, max_items=30, use_llm_categorization=True)
                if result.get('success'):
                    total_inserted += result.get('inserted', 0)
                    total_updated += result.get('updated', 0)
            except Exception as e:
                    # Silently log errors but continue
                    pass
        
            # Update last fetch time
            st.session_state.last_fetch_time = time.time()
        
            # Show brief status message
        if total_inserted > 0 or total_updated > 0:
                status_placeholder.success(f"✅ {total_inserted} nieuwe artikelen gevonden")
                time.sleep(2)  # Show message briefly
                status_placeholder.empty()
        else:
                status_placeholder.empty()
                
        except Exception as e:
            status_placeholder.empty()
        finally:
            st.session_state.is_fetching = False


def render_nieuws_page():
    """Render main news overview page."""
    # Ensure supabase is initialized
    if st.session_state.supabase is None:
        st.session_state.supabase = init_supabase()
    
    supabase = st.session_state.supabase
    
    if not supabase:
        st.error("❌ Opslag niet geïnitialiseerd. Herlaad de pagina.")
        return
    
    st.title("📰 Nieuws")
    
    # Check if viewing article detail
    if "article" in st.query_params:
        render_article_detail(st.query_params["article"])
        return
    
    # Automatic article fetching disabled - articles are managed externally
    # check_and_fetch_new_articles()  # Disabled: articles stored in Supabase, no local fetching needed
    
    # Get user preferences
    blacklist = []
    selected_categories = None
    if st.session_state.user:
        # Load preferences if not already loaded
        if st.session_state.preferences is None:
            user_id = get_user_attr(st.session_state.user, 'id')
            if user_id:
                st.session_state.preferences = supabase.get_user_preferences(user_id)
        
        if st.session_state.preferences:
            blacklist = st.session_state.preferences.get('blacklist_keywords', [])
            selected_categories = st.session_state.preferences.get('selected_categories', [])
        
        # Ensure selected_categories is always a list, not None
        if selected_categories is None:
            selected_categories = []
    
    # Debug: Show blacklist if in debug mode
    if st.session_state.get('debug_mode', False):
        if blacklist:
            st.info(f"🔍 Debug: Blacklist actief: {', '.join(blacklist)}")
        else:
            st.info("🔍 Debug: Geen blacklist actief")
    
    # Get articles
    try:
        if not supabase:
            st.error("❌ Opslag niet geïnitialiseerd. Herlaad de pagina.")
            articles = []
        else:
            # Only apply category filter if user is logged in AND has selected categories
            # If no user is logged in, show all articles (categories_filter = None)
            if st.session_state.user and selected_categories and len(selected_categories) > 0:
                categories_filter = selected_categories
            else:
                categories_filter = None
        
        # Ensure blacklist is properly formatted
        blacklist_to_use = None
        if blacklist and isinstance(blacklist, list) and len(blacklist) > 0:
            # Filter out empty strings and normalize
            blacklist_to_use = [kw.strip() for kw in blacklist if kw and kw.strip()]
            if len(blacklist_to_use) == 0:
                blacklist_to_use = None
        
        articles = supabase.get_articles(
            limit=50,
                category=None,
            categories=categories_filter,
                search_query=None,
            blacklist_keywords=blacklist_to_use
        )
            
            # Debug output if no articles found
            if len(articles) == 0:
                # Try fetching without category filters to see if that works
                test_articles = supabase.get_articles(limit=5, category=None, categories=None, search_query=None, blacklist_keywords=blacklist_to_use)
                if len(test_articles) > 0:
                    if selected_categories and len(selected_categories) > 0:
                        st.warning(f"⚠️ Geen artikelen gevonden met de geselecteerde categorieën. Zonder categorie filter: {len(test_articles)} artikelen beschikbaar.")
                        st.info("💡 Tip: Selecteer meer categorieën op de 'Gebruiker' pagina, of controleer of artikelen de juiste categorieën hebben.")
                    else:
                        st.info("ℹ️ Geen artikelen gevonden. Controleer of er artikelen in de database staan.")
                else:
                    st.warning("⚠️ Geen artikelen in database. Wacht even tot artikelen worden opgehaald...")
            
            # Debug: Show article count if in debug mode
            if st.session_state.get('debug_mode', False):
                st.info(f"🔍 Debug: {len(articles)} artikelen opgehaald")
    except Exception as e:
        st.error(f"Fout bij ophalen artikelen: {str(e)}")
        import traceback
        st.exception(e)
        articles = []
    
    # Display articles
    if not articles:
        st.info("ℹ️ Geen artikelen gevonden. Klik op '🔄 Artikelen Vernieuwen' om artikelen op te halen.")
    else:
        st.subheader(f"Artikelen ({len(articles)})")
        
        articles_list = list(articles)
        num_rows = (len(articles_list) + 3) // 4
        
        for row in range(num_rows):
            cols = st.columns(4)
            for col_idx in range(4):
                article_idx = row * 4 + col_idx
                if article_idx < len(articles_list):
                    with cols[col_idx]:
                        render_article_card(articles_list[article_idx], supabase)
        
        if len(articles) >= 50:
            st.info("ℹ️ Toon maximaal 50 artikelen. Gebruik filters om te verfijnen.")


def render_waarom_page():
    """Render 'Waarom?' page."""
    st.title("Waarom?")
    st.markdown("---")
    st.markdown("## Omdat het kan. Omdat het beter is.")
    st.markdown("---")
    st.markdown("""
    Deze nieuwsaggregator is gemaakt om nieuws toegankelijker te maken voor iedereen.
    
    **Omdat het kan:**
    - Moderne technologie maakt gepersonaliseerd nieuws mogelijk
    - AI helpt artikelen te categoriseren en uit te leggen
    - Iedereen verdient toegang tot begrijpelijk nieuws
    
    **Omdat het beter is:**
    - Eenvoudige uitleg voor complexe onderwerpen
    - Persoonlijke voorkeuren worden gerespecteerd
    - Geen informatie-overload, alleen wat jij wilt zien
    """)


def render_frustrate_page():
    """Render 'Dit wil je niet' page showing filtered articles."""
    supabase = st.session_state.supabase
    
    # Check if viewing article detail
    if "article" in st.query_params:
        render_article_detail(st.query_params["article"])
        return
    
    st.title("Dit wil je niet")
    st.markdown("---")
    st.markdown("**Deze pagina toont alle artikelen die door de blacklist filter EN categorie filter zijn uitgefilterd.**")
    st.markdown("Gebruik dit om te testen of de categorisatie en keyword filters correct werken.")
    st.markdown("---")
    
    # Check if user is logged in
    if not st.session_state.user:
        st.warning("⚠️ Je moet ingelogd zijn om deze pagina te gebruiken.")
        st.info("Ga naar de 'Gebruiker' pagina om in te loggen.")
        return
    
    # Load preferences if not already loaded
    if st.session_state.preferences is None:
        user_id = get_user_attr(st.session_state.user, 'id')
        if user_id:
            st.session_state.preferences = supabase.get_user_preferences(user_id)
    
    # Get user preferences to know what was filtered
    blacklist = []
    selected_categories = []
    if st.session_state.preferences:
        blacklist = st.session_state.preferences.get('blacklist_keywords', [])
        selected_categories = st.session_state.preferences.get('selected_categories', [])
    
    # Ensure selected_categories is a list
    if selected_categories is None or not isinstance(selected_categories, list):
        selected_categories = []
    
    # Debug info
    if st.session_state.get('debug_mode', False):
        user_id = get_user_attr(st.session_state.user, 'id', 'N/A')
        st.write(f"Debug - User ID: {user_id}")
        st.write(f"Debug - Preferences loaded: {st.session_state.preferences is not None}")
        if st.session_state.preferences:
            st.write(f"Debug - Preferences keys: {list(st.session_state.preferences.keys())}")
            st.write(f"Debug - Blacklist from prefs: {st.session_state.preferences.get('blacklist_keywords', 'NOT FOUND')}")
            st.write(f"Debug - Selected categories: {selected_categories}")
    
    # Show active filters
    has_filters = False
    if blacklist and len(blacklist) > 0:
        st.info(f"**Actieve blacklist ({len(blacklist)} trefwoorden):** {', '.join(blacklist)}")
        has_filters = True
    
    if selected_categories and len(selected_categories) > 0:
        st.info(f"**Geselecteerde categorieën ({len(selected_categories)}):** {', '.join(selected_categories)}")
        has_filters = True
    elif not selected_categories or len(selected_categories) == 0:
        st.warning("⚠️ Geen categorieën geselecteerd. Alle artikelen worden uitgefilterd.")
        has_filters = True
    
    if not has_filters:
        st.warning("⚠️ Geen filters ingesteld. Ga naar de 'Gebruiker' pagina om filters in te stellen.")
        st.markdown("---")
        return
    
    st.markdown("---")
    
    # Get ALL articles without any filters
    try:
        all_articles = supabase.get_articles(
            limit=200,  # Get more articles
            blacklist_keywords=None,  # No blacklist filter - get everything
            categories=None  # No category filter - get everything
        )
        
        # Now manually filter to find articles that WOULD be filtered
        filtered_articles = []
            for article in all_articles:
            is_filtered = False
            filter_reason = []
            
            # Check category filter
            # New logic: Article is filtered out if ANY category is NOT in selected_categories
            if selected_categories and len(selected_categories) > 0:
                if not article_matches_category_filter(article, selected_categories):
                    is_filtered = True
                    filter_reason.append("Categorie filter")
            
            # Check blacklist filter
            if blacklist:
                title = (article.get('title') or '').lower()
                description = (article.get('description') or '').lower()
                full_content = (article.get('full_content') or '').lower()
                
                all_text = f"{title} {description} {full_content}"
                
                # Check if article contains any blacklisted keyword
                for keyword in blacklist:
                    keyword_lower = keyword.lower().strip()
                    if keyword_lower and keyword_lower in all_text:
                        is_filtered = True
                        filter_reason.append(f"Blacklist: {keyword}")
                        break  # Only add reason once per article
            
            if is_filtered:
                article['_filter_reason'] = ', '.join(filter_reason)
                        filtered_articles.append(article)
        
        if filtered_articles:
            st.subheader(f"📋 {len(filtered_articles)} uitgefilterde artikelen")
            st.caption("Deze artikelen worden normaal gesproken verborgen door je blacklist en/of categorie filters.")
            st.markdown("---")
            
            # Display filtered articles
            articles_list = filtered_articles
            num_cols = 4
            
            for row_start in range(0, len(articles_list), num_cols):
                cols = st.columns(num_cols)
                for col_idx, col in enumerate(cols):
                    article_idx = row_start + col_idx
                    if article_idx < len(articles_list):
                        with col:
                            render_article_card(articles_list[article_idx], supabase)
        else:
            st.success("✅ Geen artikelen gevonden die door de blacklist worden uitgefilterd.")
            st.info("Dit betekent dat er momenteel geen artikelen zijn die je blacklist trefwoorden bevatten.")
    
    except Exception as e:
        st.error(f"Fout bij ophalen artikelen: {str(e)}")
        import traceback
        st.code(traceback.format_exc())


def render_gebruiker_page():
    """Render user page with login/logout and preferences."""
    supabase = st.session_state.supabase
    
    st.title("👤 Gebruiker")
    st.markdown("---")
    
    if not st.session_state.user:
        # Login/Signup
        st.subheader("Inloggen of Registreren")
        
        tab1, tab2 = st.tabs(["Inloggen", "Registreren"])
        
        with tab1:
            # Use form to enable Enter key submission
            with st.form("login_form", clear_on_submit=False):
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Wachtwoord", type="password", key="login_password")
                login_submitted = st.form_submit_button("Inloggen", use_container_width=True)
            
            if login_submitted:
                # Prevent login with test@local.com (mock user for local testing only)
                if email.lower() == 'test@local.com':
                    st.error("Dit is een test account voor lokale ontwikkeling. Gebruik een echt account.")
                    return
                
                result = supabase.sign_in(email, password)
                if result.get('success'):
                    user = result.get('user')
                    # Convert user to dict if it's a Pydantic object
                    if user and not isinstance(user, dict):
                        user_dict = {
                            'id': get_user_attr(user, 'id'),
                            'email': get_user_attr(user, 'email'),
                            'created_at': get_user_attr(user, 'created_at')
                        }
                    else:
                        user_dict = user
                    
                    # Double-check: never allow test@local.com
                    user_email = get_user_attr(user_dict, 'email', '')
                    if user_email and user_email.lower() == 'test@local.com':
                        st.error("Dit account kan niet worden gebruikt.")
                        try:
                            supabase.sign_out()
                        except:
                            pass
                        return
                    
                    # Store user in session state - this persists across reruns in the same browser session
                    st.session_state.user = user_dict
                    st.session_state.preferences = None
                    
                    # Store session token in cookie for persistence across page reloads
                    if result.get('access_token'):
                        # Store in cookie (30 days expiration)
                        set_cookie("supabase_access_token", result.get('access_token'), days=30)
                        st.session_state.supabase_session_token = result.get('access_token')
                    if result.get('refresh_token'):
                        set_cookie("supabase_refresh_token", result.get('refresh_token'), days=30)
                        st.session_state.supabase_refresh_token = result.get('refresh_token')
                    
                    # Also store user email in cookie for quick display
                    if user_email:
                        set_cookie("user_email", user_email, days=30)
                    
                    # Also verify the session is stored in Supabase client
                    # The Supabase client should have the session from sign_in response
                    st.success("Ingelogd!")
                    st.rerun()
                else:
                    st.error(f"Inloggen mislukt: {result.get('error', 'Onbekende fout')}")
        
        with tab2:
            # Use form to enable Enter key submission
            with st.form("signup_form", clear_on_submit=False):
            new_email = st.text_input("Email", key="signup_email")
            new_password = st.text_input("Wachtwoord", type="password", key="signup_password")
            confirm_password = st.text_input("Bevestig wachtwoord", type="password", key="signup_confirm")
                signup_submitted = st.form_submit_button("Registreren", use_container_width=True)
            
            if signup_submitted:
                if new_password != confirm_password:
                    st.error("Wachtwoorden komen niet overeen")
                elif len(new_password) < 6:
                    st.error("Wachtwoord moet minimaal 6 tekens zijn")
                else:
                    result = supabase.sign_up(new_email, new_password)
                    if result.get('success'):
                        st.success("Account aangemaakt! Je kunt nu inloggen.")
                    else:
                        st.error(f"Registratie mislukt: {result.get('error', 'Onbekende fout')}")
    else:
        # User is logged in
        user_email = get_user_attr(st.session_state.user, 'email', 'Gebruiker')
        st.success(f"👤 Ingelogd als: {user_email}")
        
        if st.button("🚪 Uitloggen", use_container_width=True):
            # Sign out from Supabase
            try:
            supabase.sign_out()
            except Exception as e:
                # Continue even if sign_out fails
                pass
            
            # Clear session state and tokens
            st.session_state.user = None
            st.session_state.preferences = None
            st.session_state.supabase_session_token = None
            st.session_state.supabase_refresh_token = None
            
            # Clear cookies
            set_cookie("supabase_access_token", "")
            set_cookie("supabase_refresh_token", "")
            set_cookie("user_email", "")
            
            # Force rerun to update UI
            st.rerun()
        
        st.markdown("---")
        
        # Get preferences
        if st.session_state.preferences is None:
            user_id = get_user_attr(st.session_state.user, 'id')
            if user_id:
                st.session_state.preferences = supabase.get_user_preferences(user_id)
        
        prefs = st.session_state.preferences
        blacklist = prefs.get('blacklist_keywords', []) if prefs else []
        selected_categories = prefs.get('selected_categories', []) if prefs else []
        
        # Ensure selected_categories is always a list, not None
        if selected_categories is None or not isinstance(selected_categories, list):
            selected_categories = []
        
        # Category selection
        st.subheader("📂 Categorieën")
        st.caption("Selecteer welke categorieën je wilt zien")
        
        from categorization_engine import get_all_categories
        all_categories = get_all_categories()
        category_selections = {}
        
        # Ensure selected_categories is a list before using 'in' operator
        if not isinstance(selected_categories, list):
            selected_categories = []
        
        for category in all_categories:
            category_selections[category] = st.checkbox(
                category,
                value=category in selected_categories,
                key=f"cat_pref_{category}"
            )
        
        new_selected = [cat for cat, selected in category_selections.items() if selected]
        
        # Save button for categories
        if st.button("💾 Opslaan", key="save_categories", use_container_width=True):
            user_id = get_user_attr(st.session_state.user, 'id')
            if user_id and supabase.update_user_preferences(user_id, selected_categories=new_selected):
                st.session_state.preferences = None
                st.success("✅ Categorieën opgeslagen! Statistieken worden bijgewerkt...")
                st.rerun()
            else:
                st.error("❌ Fout bij opslaan van categorieën")
        
        st.markdown("---")
        
        # Blacklist management
        st.subheader("🚫 Blacklist Trefwoorden")
        st.caption("Artikelen met deze woorden worden verborgen")
        
        if blacklist:
            for keyword in blacklist:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.text(keyword)
                with col2:
                    if st.button("❌", key=f"remove_{keyword}", use_container_width=True):
                        blacklist.remove(keyword)
                        user_id = get_user_attr(st.session_state.user, 'id')
                        if user_id:
                            supabase.update_user_preferences(user_id, blacklist_keywords=blacklist)
                        st.session_state.preferences = None
                        st.rerun()
        else:
            st.info("Geen trefwoorden in blacklist")
        
        st.markdown("---")
        new_keyword = st.text_input("Nieuw trefwoord toevoegen", key="new_keyword")
        if st.button("➕ Toevoegen", use_container_width=True):
            if new_keyword and new_keyword.strip():
                keyword = new_keyword.strip()
                if keyword not in blacklist:
                    blacklist.append(keyword)
                    user_id = get_user_attr(st.session_state.user, 'id')
                    if user_id and supabase.update_user_preferences(user_id, blacklist_keywords=blacklist):
                        st.session_state.preferences = None
                        st.success(f"'{keyword}' toegevoegd")
                        st.rerun()
                else:
                    st.warning("Dit trefwoord staat al in de blacklist")
        
        st.markdown("---")
        
        # Recategorize articles without LLM categorization
        st.subheader("🔄 Her-categoriseren met LLM")
        st.caption("Her-categoriseer artikelen die nog geen LLM-categorisatie hebben")
        
        from categorization_engine import is_llm_available
        
        if is_llm_available():
            if st.button("🔄 Her-categoriseer artikelen zonder LLM", use_container_width=True, key="recategorize_without_llm"):
                from articles_repository import recategorize_articles_without_llm
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                article_text = st.empty()
                
                # Progress callback function
                def update_progress(processed, total, current_title):
                    if total > 0:
                        progress = (processed / total) * 0.9  # 0% to 90%
                        progress_bar.progress(progress)
                        status_text.text(f"Her-categoriseren: {processed}/{total} artikelen...")
                        article_text.text(f"Huidige artikel: {current_title}...")
                
                status_text.text("Artikelen ophalen...")
                progress_bar.progress(0.05)
                
                try:
                    result = recategorize_articles_without_llm(limit=50, progress_callback=update_progress)
                except Exception as e:
                    st.error(f"Fout tijdens her-categoriseren: {str(e)}")
                    result = {'success': False, 'error': str(e)}
                
                progress_bar.progress(1.0)
                article_text.empty()
                
                if result.get('success'):
                    processed = result.get('processed', 0)
                    updated = result.get('updated', 0)
                    errors = result.get('errors', 0)
                    skipped = result.get('skipped', 0)
                    total = result.get('total', 0)
                    
                    status_text.text("Klaar!")
                    
                    if updated > 0:
                        st.success(f"✅ {updated} artikelen her-categoriseerd met LLM!")
                        if errors > 0:
                            st.warning(f"⚠️ {errors} artikelen konden niet worden her-categoriseerd")
                        if skipped > 0:
                            st.info(f"ℹ️ {skipped} artikelen hadden al LLM-categorisatie en zijn overgeslagen")
                    elif result.get('message'):
                        st.info(f"ℹ️ {result.get('message')}")
                    else:
                        st.info("Geen artikelen gevonden om te her-categoriseren")
                else:
                    st.error(f"Fout: {result.get('error', 'Onbekende fout')}")
                
                import time
                time.sleep(2)
                st.rerun()
        else:
            st.warning("⚠️ Geen LLM beschikbaar. Configureer een LLM API key (Groq, Hugging Face, OpenAI, of ChatLLM) om artikelen te her-categoriseren.")
            st.info("💡 Tip: Groq API is gratis en snel. Voeg GROQ_API_KEY toe aan je .env bestand.")
        
        st.markdown("---")
        
        # Statistics: Articles included/excluded per day
        st.subheader("📊 Statistieken")
        st.caption("Aantal artikelen per dag op basis van je voorkeuren")
        
        try:
            # Get all articles from the last 7 days
            from datetime import datetime, timedelta
            import pytz
            
            amsterdam_tz = pytz.timezone('Europe/Amsterdam')
            now = datetime.now(amsterdam_tz)
            seven_days_ago = now - timedelta(days=7)
            
            # Get all articles (we'll filter in Python to calculate stats)
            all_articles = supabase.get_articles(limit=500, category=None, categories=None, search_query=None, blacklist_keywords=None)
            
            # Filter articles by date (last 7 days)
            recent_articles = []
            for article in all_articles:
                if article.get('published_at'):
                    try:
                        from dateutil import parser
                        pub_date = parser.parse(article['published_at'])
                        if pub_date.tzinfo is None:
                            pub_date = pytz.utc.localize(pub_date)
                        pub_date = pub_date.astimezone(amsterdam_tz)
                        
                        if pub_date >= seven_days_ago:
                            recent_articles.append(article)
                    except:
                        pass
            
            # Group articles by date
            articles_by_date = {}
            for article in recent_articles:
                try:
                    from dateutil import parser
                    pub_date = parser.parse(article['published_at'])
                    if pub_date.tzinfo is None:
                        pub_date = pytz.utc.localize(pub_date)
                    pub_date = pub_date.astimezone(amsterdam_tz)
                    date_key = pub_date.strftime('%Y-%m-%d')
                    
                    if date_key not in articles_by_date:
                        articles_by_date[date_key] = []
                    articles_by_date[date_key].append(article)
                except:
                    pass
            
            # Calculate included/excluded for each day
            stats_data = []
            for date_key in sorted(articles_by_date.keys(), reverse=True):
                day_articles = articles_by_date[date_key]
                
                included = 0
                excluded = 0
                
                for article in day_articles:
                    # Check if article matches user preferences
                    is_included = True
                    
                    # Check category filter
                    # New logic: Article is filtered out if ANY category is NOT in selected_categories
                    if selected_categories:
                        if not article_matches_category_filter(article, selected_categories):
                            is_included = False
                    
                    # Check blacklist
                    if is_included and blacklist:
                        title = (article.get('title') or '').lower()
                        description = (article.get('description') or '').lower()
                        full_content = (article.get('full_content') or '').lower()
                        all_text = f"{title} {description} {full_content}"
                        
                        for keyword in blacklist:
                            if keyword.lower().strip() in all_text:
                                is_included = False
                                break
                    
                    if is_included:
                        included += 1
                    else:
                        excluded += 1
                
                # Format date for display
                try:
                    from dateutil import parser
                    date_obj = parser.parse(date_key)
                    date_display = date_obj.strftime('%d %B %Y')
                except:
                    date_display = date_key
                
                stats_data.append({
                    'date': date_display,
                    'included': included,
                    'excluded': excluded,
                    'total': included + excluded
                })
            
            # Display statistics
            if stats_data:
                # Summary metrics
                col1, col2, col3 = st.columns(3)
                total_included = sum(s['included'] for s in stats_data)
                total_excluded = sum(s['excluded'] for s in stats_data)
                total_articles = sum(s['total'] for s in stats_data)
                
                with col1:
                    st.metric("Totaal Inclusief", total_included)
                with col2:
                    st.metric("Totaal Uitgesloten", total_excluded)
                with col3:
                    st.metric("Totaal Artikelen", total_articles)
                
                st.markdown("---")
                
                # Daily breakdown
                st.caption("Per dag:")
                for stat in stats_data:
                    if stat['total'] > 0:
                        percentage_included = (stat['included'] / stat['total']) * 100 if stat['total'] > 0 else 0
                        st.write(f"**{stat['date']}**")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"✅ Inclusief: {stat['included']} ({percentage_included:.1f}%)")
                        with col2:
                            st.write(f"❌ Uitgesloten: {stat['excluded']} ({100 - percentage_included:.1f}%)")
                        st.progress(percentage_included / 100)
            else:
                st.info("Geen artikelen gevonden in de afgelopen 7 dagen.")
                
        except Exception as e:
            st.error(f"Fout bij berekenen statistieken: {str(e)}")
            import traceback
            if st.session_state.get('debug_mode', False):
                st.code(traceback.format_exc())


def main():
    """Main Streamlit app."""
    # Start background scheduler for automatic RSS fetching
    if not is_scheduler_running():
        start_background_scheduler()
    
    # Read cookies on first load and store in session state
    # This needs to happen before checking user state
    if '_cookies_read' not in st.session_state:
        cookie_token = get_cookie("supabase_access_token")
        cookie_email = get_cookie("user_email")
        if cookie_token:
            st.session_state.supabase_session_token = cookie_token
        if cookie_email:
            st.session_state['_cookie_user_email'] = cookie_email
        st.session_state['_cookies_read'] = True
    
    # Render header image with abstract sunrise
    st.markdown('<div class="header-image-container"></div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Initialize storage
    supabase = init_supabase()
    if not supabase:
        st.error("Opslag niet geconfigureerd. Zie de documentatie voor setup instructies.")
        return
    
    # Check for persisted Supabase session and restore user state if exists
    # This maintains login state across page navigations and Streamlit reruns
    # IMPORTANT: Never auto-login with test@local.com (local storage mock user)
    # 
    # Strategy: Use cookies to persist session across page reloads
    # 1. Check cookie for stored access token and user email
    # 2. If cookie exists, verify session with Supabase and restore user
    # 3. Fallback to Supabase client's persisted session (localStorage)
    
    if st.session_state.user is None:
        try:
            # Only check for persisted session if we're using Supabase (not LocalStorage)
            from local_storage import LocalStorage
            if not isinstance(supabase, LocalStorage):
                # Method 1: Check cookie for stored session token
                # Use session state first (set in main() before this check)
                cookie_token = st.session_state.get('supabase_session_token') or get_cookie("supabase_access_token")
                cookie_email = st.session_state.get('_cookie_user_email') or get_cookie("user_email")
                
                if cookie_token and cookie_email and cookie_email.lower() != 'test@local.com':
                    # We have a cookie with token and email - try to verify session
                    try:
                        current_user = supabase.get_current_user()
                        if current_user:
                            user_email = get_user_attr(current_user, 'email', '')
                            # Verify the email matches the cookie
                            if user_email and user_email.lower() == cookie_email.lower() and user_email.lower() != 'test@local.com':
                                # Convert to dict format for consistency
                                if not isinstance(current_user, dict):
                                    st.session_state.user = {
                                        'id': get_user_attr(current_user, 'id'),
                                        'email': get_user_attr(current_user, 'email'),
                                        'created_at': get_user_attr(current_user, 'created_at')
                                    }
                                else:
                                    st.session_state.user = current_user
                                st.session_state.preferences = None  # Will be loaded when needed
                                # Update session state tokens from cookie
                                st.session_state.supabase_session_token = cookie_token
                    except Exception:
                        # Session might be expired, clear cookie
                        set_cookie("supabase_access_token", "")
                        set_cookie("supabase_refresh_token", "")
                        set_cookie("user_email", "")
                
                # Method 2: Fallback to Supabase client's persisted session (localStorage)
                if st.session_state.user is None:
                    try:
                        current_user = supabase.get_current_user()
                        if current_user:
                            user_email = get_user_attr(current_user, 'email', '')
                            # NEVER restore test@local.com - it's a mock user for local testing only
                            if user_email and user_email.lower() != 'test@local.com':
                                # Convert to dict format for consistency
                                if not isinstance(current_user, dict):
                                    st.session_state.user = {
                                        'id': get_user_attr(current_user, 'id'),
                                        'email': get_user_attr(current_user, 'email'),
                                        'created_at': get_user_attr(current_user, 'created_at')
                                    }
                                else:
                                    st.session_state.user = current_user
                                st.session_state.preferences = None  # Will be loaded when needed
                                
                                # Also update cookie to keep it in sync
                                set_cookie("user_email", user_email, days=30)
                        else:
                            # No valid session - clear cookies
                            set_cookie("supabase_access_token", "")
                            set_cookie("supabase_refresh_token", "")
                            set_cookie("user_email", "")
                    except Exception:
                        # No session available - clear cookies
                        set_cookie("supabase_access_token", "")
                        set_cookie("supabase_refresh_token", "")
                        set_cookie("user_email", "")
        except ImportError:
            # LocalStorage not available - this is fine, we're using Supabase
            pass
        except Exception as e:
            # Any other error - don't log, user will need to log in manually
            pass
    
    # Render horizontal menu
    render_horizontal_menu()
    
    # Render current page
    page = st.session_state.current_page
    
    if page == "Nieuws":
        render_nieuws_page()
    elif page == "Waarom":
        render_waarom_page()
    elif page == "Frustrate":
        render_frustrate_page()
    elif page == "Gebruiker":
        render_gebruiker_page()


if __name__ == "__main__":
    main()
