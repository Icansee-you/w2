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

import streamlit as st
import re
from html import unescape

# Load environment variables from .env file (for local development)
# Also supports Streamlit Secrets (for production deployment)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv not installed, will use environment variables directly
    pass

from secrets_helper import get_secret

from supabase_client import get_supabase_client
from articles_repository import fetch_and_upsert_articles, generate_missing_eli5_summaries
from nlp_utils import generate_eli5_summary_nl_with_llm
from rss_background_checker import start_background_checker, get_last_check_info, is_running

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
    
    /* Remove top white space - conservative approach */
    .main .block-container {
        padding-top: 0 !important;
        padding-bottom: 1rem !important;
        margin-top: 0 !important;
    }
    
    /* Extra: Remove top spacing on article detail pages */
    [data-article-page="true"] {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }
    
    .article-detail-content {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }
    
    .stApp > header {
        padding-top: 0 !important;
        padding-bottom: 0 !important;
        margin-top: 0 !important;
        margin-bottom: 0 !important;
        height: 0 !important;
        display: none !important;
    }
    
    /* Remove top margin from first element */
    .main .block-container > div:first-child {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }
    
    /* Reduce spacing in Streamlit app container */
    .stApp {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
    
    /* Target the main content area */
    section[data-testid="stAppViewContainer"] {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
    
    /* Reduce spacing in block containers */
    [data-testid="stVerticalBlock"] {
        gap: 0.5rem !important;
    }
    
    /* First vertical block should have no top margin */
    [data-testid="stVerticalBlock"]:first-child {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }
    
    /* Remove top spacing from the first markdown element (horizontal menu) */
    .main .block-container > div:first-child > div:first-child {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }
    
    /* Target Streamlit's default spacing */
    .element-container:first-child {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }
    
    /* Remove any top spacing from the horizontal menu container */
    .horizontal-menu {
        margin-top: 0 !important;
        padding-top: 0.5rem !important;
    }
    
    /* Additional aggressive spacing removal */
    div[data-testid="stVerticalBlock"]:first-child {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }
    
    /* Remove top spacing from all first-level children */
    .main > div:first-child {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }
    
    /* Horizontal menu - two times smaller */
    .horizontal-menu {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 1rem;
        padding: 0.5rem 1rem;
        border-bottom: 2px solid #e0e0e0;
        margin-bottom: 1rem;
        background-color: #ffffff;
        position: relative;
    }
    
    .menu-items-container {
        display: flex;
        justify-content: center;
        gap: 1rem;
        flex: 1;
    }
    
    .menu-item {
        font-size: 1.2rem;
        font-weight: 500;
        color: #666;
        text-decoration: none;
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
        transition: all 0.2s;
        cursor: pointer;
    }
    
    .user-info {
        font-size: 0.9rem;
        color: #666;
        white-space: nowrap;
        margin-left: auto;
        display: flex;
        flex-direction: column;
        align-items: flex-end;
    }
    
    .last-update {
        font-size: 0.8rem;
        color: #999;
        margin-top: 0.25rem;
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
        padding: 0.3rem 0.6rem;
        border-radius: 12px;
        font-size: 0.85rem;
        white-space: nowrap;
        margin: 0 0.25rem 0 0;
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
        width: 100%;
        margin: 0 auto;
    }
    
    /* Default block-container width for non-article pages */
    .main .block-container {
        max-width: 800px !important;
    }
    
    /* Article detail images - 70% width */
    .article-detail-content img {
        max-width: 70% !important;
        width: 70% !important;
    }
    
    /* Allow categories to be inline */
    .article-detail-content .article-category {
        max-width: none !important;
        display: inline-block !important;
    }
    
    
    /* Smaller image */
    .article-detail-image {
        max-width: 30% !important;
        margin: 0 auto;
        display: block;
        max-height: 200px !important;
        object-fit: cover !important;
    }
    
    /* Reduced vertical spacing */
    .article-detail-container h1 {
        margin-bottom: 0.5rem !important;
        margin-top: 0.5rem !important;
    }
    
    .article-detail-container h2 {
        margin-bottom: 0.5rem !important;
        margin-top: 0.75rem !important;
    }
    
    .article-detail-container h3 {
        margin-bottom: 0.25rem !important;
        margin-top: 0.5rem !important;
    }
    
    /* Reduced line spacing in article text */
    .article-detail-content p {
        line-height: 1.4 !important;
        margin-bottom: 0.5rem !important;
    }
    
    /* Reduced spacing for separators */
    .article-detail-container hr {
        margin: 0.5rem 0 !important;
    }
    
    /* Smaller image in article detail */
    .article-detail-container img {
        max-width: 30% !important;
        margin: 0.25rem 0 !important;
        max-height: 200px !important;
        object-fit: cover !important;
    }
    
    /* Additional compact spacing */
    .article-detail-container .stButton {
        margin-bottom: 0.25rem !important;
    }
    
    .article-detail-container .stInfo {
        margin-bottom: 0.5rem !important;
        padding: 0.5rem !important;
    }
    
    .article-detail-container .stCaption {
        margin-top: 0.25rem !important;
        margin-bottom: 0.25rem !important;
    }
    
    /* Compact ELI5 box */
    .eli5-box {
        padding: 0.75rem !important;
        margin: 0.5rem 0 !important;
    }
    
    @media (max-width: 768px) {
        .horizontal-menu {
            flex-direction: column;
            gap: 0.5rem;
        }
        .menu-items-container {
            flex-direction: column;
            width: 100%;
        }
        .menu-item {
            text-align: center;
        }
        .user-info {
            text-align: center;
            margin-left: 0;
            width: 100%;
        }
        
        /* Full width on mobile */
        .article-detail-content {
            width: 100%;
            max-width: 100%;
            padding: 0 1rem;
        }
        
        /* Stack image and metadata vertically on mobile */
        .article-detail-content [data-testid="column"] {
            width: 100% !important;
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


def init_supabase():
    """Initialize Supabase client. Always uses Supabase."""
    try:
        if st.session_state.supabase is None:
            st.session_state.supabase = get_supabase_client()
        
        return st.session_state.supabase
    except ValueError as e:
        # Missing credentials
        st.error(f"❌ **Supabase configuratie ontbreekt**: {str(e)}")
        st.info("💡 **Voor lokale ontwikkeling**: Maak een `.env` bestand met `SUPABASE_URL` en `SUPABASE_ANON_KEY`")
        st.info("💡 **Voor productie**: Voeg secrets toe in Streamlit Cloud (Settings → Secrets)")
        return None
    except Exception as e:
        # Other errors (connection issues, etc.)
        st.error(f"❌ **Supabase connectie mislukt**: {str(e)}")
        st.info("💡 Controleer of je Supabase credentials correct zijn en of je internetverbinding werkt.")
        return None


def _find_category_match_by_keywords(cat_name: str) -> Optional[str]:
    """Find matching new category based on partial keywords."""
    cat_lower = cat_name.lower()
    
    # Buitenland keywords
    if any(kw in cat_lower for kw in ['buitenland', 'internationaal', 'conflict', 'europa', 'oorlog']):
        return 'Buitenland'
    
    # Sport keywords
    if any(kw in cat_lower for kw in ['sport', 'voetbal', 'wielrennen', 'olympisch']):
        return 'Sport'
    
    # Bekende personen keywords
    if any(kw in cat_lower for kw in ['bekende', 'nederlander', 'celebrity', 'artiest', 'acteur']):
        return 'Bekende personen'
    
    # Koningshuis keywords
    if any(kw in cat_lower for kw in ['koningshuis', 'koning', 'koningin', 'prins', 'oranje']):
        return 'Koningshuis'
    
    # Politiek keywords
    if any(kw in cat_lower for kw in ['politiek', 'kabinet', 'minister', 'regering', 'gemeente']):
        return 'Politiek'
    
    return None


def _map_old_categories_to_new(old_categories: List[str], valid_categories: List[str]) -> List[str]:
    """Map old category names to new category names."""
    if not old_categories:
        return []
    
    # Mapping from old categories to new categories (case-insensitive matching)
    # This maps all old category variations to the 5 new categories
    category_mapping = {
        # Buitenland mappings
        'buitenland - europa': 'Buitenland',
        'buitenland - overig': 'Buitenland',
        'internationale conflicten': 'Buitenland',
        'buitenland': 'Buitenland',
        'internationaal': 'Buitenland',
        
        # Sport mappings
        'sport - voetbal': 'Sport',
        'sport - wielrennen': 'Sport',
        'overige sport': 'Sport',
        'sport': 'Sport',
        
        # Bekende personen mappings
        'bekende nederlanders': 'Bekende personen',
        'bekende personen': 'Bekende personen',
        
        # Koningshuis mappings (already correct)
        'koningshuis': 'Koningshuis',
        
        # Politiek mappings
        'nationale politiek': 'Politiek',
        'lokale politiek': 'Politiek',
        'politiek': 'Politiek',
        
        # Other old categories that should be filtered out (not in new 5 categories)
        'binnenland': None,  # Remove - not in new categories
        'misdaad': None,  # Remove - not in new categories
        'huizenmarkt': None,  # Remove - not in new categories
        'economie': None,  # Remove - not in new categories
        'technologie': None,  # Remove - not in new categories
    }
    
    mapped = []
    for old_cat in old_categories:
        if not old_cat:
            continue
        
        # Normalize the category name (strip and lowercase for matching)
        normalized_cat = old_cat.strip()
        normalized_key = normalized_cat.lower()
        
        # First check if it's already a valid category (exact match)
        if normalized_cat in valid_categories:
            if normalized_cat not in mapped:
                mapped.append(normalized_cat)
            continue
        
        # Try to map it (case-insensitive)
        mapped_cat = category_mapping.get(normalized_key)
        
        # If mapping explicitly says None, skip this category (it should be removed)
        if mapped_cat is None:
            continue
        
        # If no direct mapping found, try keyword-based matching
        if not mapped_cat:
            mapped_cat = _find_category_match_by_keywords(normalized_cat)
        
        # If we found a mapping, use it
        if mapped_cat and mapped_cat in valid_categories:
            if mapped_cat not in mapped:
                mapped.append(mapped_cat)
    
    return mapped


def get_user_id(user_obj) -> Optional[str]:
    """Helper function to extract user ID from user object (handles different formats)."""
    if not user_obj:
        return None
    
    # Try different ways to get ID
    if isinstance(user_obj, dict):
        return user_obj.get('id')
    
    if hasattr(user_obj, 'id'):
        user_id = user_obj.id
        if user_id:
            return user_id
    
    # Try nested user object (Supabase sometimes wraps it)
    if hasattr(user_obj, 'user') and hasattr(user_obj.user, 'id'):
        user_id = user_obj.user.id
        if user_id:
            return user_id
    
    return None


def get_user_email(user_obj) -> str:
    """Helper function to extract email from user object (handles different formats)."""
    if not user_obj:
        return None
    
    # Try different ways to get email
    if isinstance(user_obj, dict):
        return user_obj.get('email')
    
    if hasattr(user_obj, 'email'):
        email = user_obj.email
        if email:
            return email
    
    # Try nested user object (Supabase sometimes wraps it)
    if hasattr(user_obj, 'user') and hasattr(user_obj.user, 'email'):
        email = user_obj.user.email
        if email:
            return email
    
    return None


def render_horizontal_menu():
    """Render horizontal navigation menu."""
    # Get user email if logged in
    user_email = None
    if st.session_state.user:
        user_email = get_user_email(st.session_state.user)
        # If we can't get email but user is logged in, use default (auto-login)
        if not user_email:
            user_email = 'test@hotmail.com'
    
    # Get current datetime for "Laatste update"
    from datetime import datetime
    amsterdam_tz = pytz.timezone('Europe/Amsterdam')
    current_time = datetime.now(amsterdam_tz)
    last_update_str = current_time.strftime('%d-%m-%Y %H:%M:%S')
    
    # Build user info (right aligned)
    user_info_html = ""
    if user_email:
        user_info_html = f'<div class="user-info"><div>De volgende gebruiker is ingelogd: {user_email}</div><div class="last-update">Laatste update: {last_update_str}</div></div>'
    
    # Build complete menu HTML
    menu_html = f'<div class="horizontal-menu"><div class="menu-items-container"><a class="menu-item" href="?page=Nieuws" onclick="window.location.href=\'?page=Nieuws\'; return false;" target="_self">Nieuws</a><a class="menu-item" href="?page=Waarom" onclick="window.location.href=\'?page=Waarom\'; return false;" target="_self">Waarom?</a><a class="menu-item" href="?page=Frustrate" onclick="window.location.href=\'?page=Frustrate\'; return false;" target="_self">Dit wil je niet</a><a class="menu-item" href="?page=Statistics" onclick="window.location.href=\'?page=Statistics\'; return false;" target="_self">Statistics</a><a class="menu-item" href="?page=Gebruiker" onclick="window.location.href=\'?page=Gebruiker\'; return false;" target="_self">Gebruiker</a></div>{user_info_html}</div>'
    
    st.markdown(menu_html, unsafe_allow_html=True)
    
    # Update current page from query params
    page = st.query_params.get("page", "Nieuws")
    if page in ["Nieuws", "Waarom", "Frustrate", "Statistics", "Gebruiker"]:
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


def get_summary_sentences(text: str, num_sentences: int = 2) -> str:
    """Extract first N sentences from text."""
    if not text:
        return ""
    text = strip_html_tags(text)
    sentences = re.split(r'[.!?]+\s+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    if len(sentences) >= num_sentences:
        summary = '. '.join(sentences[:num_sentences])
        if summary and not summary[-1] in '.!?':
            summary += '.'
        return summary
    return text[:200] + "..." if len(text) > 200 else text


def ensure_eli5_summary(article: Dict[str, Any], supabase, show_spinner: bool = False) -> Dict[str, Any]:
    """Ensure article has ELI5 summary, generate if missing."""
    if not article.get('eli5_summary_nl'):
        # Generate ELI5 summary with timeout and loading indicator
        text = f"{article.get('title', '')} {article.get('description', '')}"
        if article.get('full_content'):
            text += f" {article.get('full_content', '')[:1000]}"
        
        # Use spinner if requested (for UI feedback)
        if show_spinner:
            with st.spinner("🔄 Eenvoudige uitleg genereren..."):
                result = generate_eli5_summary_nl_with_llm(text, article.get('title', ''))
        else:
            # Try with timeout to prevent freezing
            import signal
            result = None
            try:
                # For Windows, we can't use signal.alarm, so we'll just try with a simple timeout wrapper
                result = generate_eli5_summary_nl_with_llm(text, article.get('title', ''))
            except Exception as e:
                print(f"Error generating ELI5: {e}")
                result = None
        
        if result and result.get('summary'):
            article['eli5_summary_nl'] = result['summary']
            article['eli5_llm'] = result.get('llm', 'Onbekend')
            # Save to database
            try:
                supabase.update_article_eli5(article['id'], result['summary'], result.get('llm'))
            except Exception as e:
                print(f"Error saving ELI5 to database: {e}")
        else:
            article['eli5_summary_nl'] = None
            article['eli5_llm'] = None
    else:
        # Get LLM info if available
        article['eli5_llm'] = article.get('eli5_llm', 'Onbekend')
    
    return article


def render_article_card(article: Dict[str, Any], supabase):
    """Render a single article card (overview - only image and summary)."""
    article_id = article['id']
    
    # Image (clickable) - stays in same window
    if article.get('image_url'):
        try:
            # Use HTML with onclick that updates query params (stays in same window)
            # window.location.search stays in the same window
            image_html = f"""
            <div class="clickable-image-container" 
                 onclick="window.location.search = '?article={article_id}'; return false;" 
                 style="cursor: pointer; margin-bottom: 0.5rem;">
                <img src="{article['image_url']}" 
                     style="width: 100%; height: auto; border-radius: 4px; display: block;" 
                     alt="Click to view article" />
            </div>
            """
            st.markdown(image_html, unsafe_allow_html=True)
        except:
            # Fallback: just show image
            try:
                st.image(article['image_url'], use_container_width=True)
            except:
                pass
    
    # Title (clickable)
    title = article.get('title', 'Geen titel')
    if st.button(title[:70] + "..." if len(title) > 70 else title, key=f"article_{article_id}", use_container_width=True):
        st.query_params["article"] = article_id
        st.rerun()
    
    # Summary (2 sentences) - only this on overview
    description = article.get('description', '')
    if description:
        summary = get_summary_sentences(description, num_sentences=2)
        st.markdown(f'<div class="article-summary">{summary}</div>', unsafe_allow_html=True)


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
    
    # Render page immediately - don't wait for ELI5 generation
    # ELI5 will be generated in background or shown if it already exists
    # Add a unique identifier to the page so we can target all containers on this page
    # Also add a class to body via JavaScript for CSS targeting
    st.markdown("""
    <script>
    // Add class to body when on article page (for CSS targeting)
    (function() {
        if (document.body) {
            document.body.classList.add('article-page-active');
        } else {
            document.addEventListener('DOMContentLoaded', function() {
                document.body.classList.add('article-page-active');
            });
        }
    })();
    </script>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="article-detail-container" data-article-page="true">', unsafe_allow_html=True)
    
    # Create 3-column layout: left white space (20%), middle content (60%), right white space (20%)
    col_left, col_center, col_right = st.columns([2, 6, 2])
    
    with col_center:
        # Wrap content in responsive container - 60% of screen width
        st.markdown('<div id="article-detail-content-main" class="article-detail-content">', unsafe_allow_html=True)
        
        # Title without extra spacing
        article_title = article.get('title', 'Geen titel')
        st.markdown(f"### {article_title}")
        
        # Date directly under title, same style as "Laatste update"
        if article.get('published_at'):
            date_str = format_datetime(article['published_at'])
            st.markdown(f'<div class="article-date" style="font-size: 0.8rem; color: #999; margin-top: 0.25rem; margin-bottom: 1rem;">{date_str}</div>', unsafe_allow_html=True)
        
        # Categories (on detail page)
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
        
        # Map old categories to new categories
        from categorization_engine import get_all_categories
        valid_categories = get_all_categories()
        mapped_categories = _map_old_categories_to_new(categories, valid_categories)
        categories = mapped_categories
        
        # Create two-column layout: Image (70%) and Metadata (30%)
        if article.get('image_url'):
            col_image, col_meta = st.columns([7, 3])  # 70% / 30% split
            
            with col_image:
                # Image on left - 70% of text width
                article_id = article['id']
                image_html = f"""
                <div class="clickable-image-container" 
                     onclick="window.location.search = '?article={article_id}'; return false;" 
                     style="cursor: pointer;">
                    <img src="{article['image_url']}" 
                         style="width: 100%; height: auto; border-radius: 4px; display: block; margin: 0.25rem 0; max-height: 300px; object-fit: cover;" 
                         alt="Click to view article" />
                </div>
                """
                st.markdown(image_html, unsafe_allow_html=True)
            
            with col_meta:
                # Categories on right
                if categories and len(categories) > 0:
                    from html import escape
                    # Build all categories in one HTML string
                    category_html = '<div style="margin: 0.25rem 0;">'
                    for cat in categories:
                        if cat:  # Only add non-empty categories
                            escaped_cat = escape(str(cat))
                            category_html += f'<span class="article-category" style="margin-right: 0.5rem; display: inline-block;">{escaped_cat}</span>'
                    category_html += '</div>'
                    st.markdown(category_html, unsafe_allow_html=True)
                    
                    # Show which LLM was used for categorization
                    categorization_llm = article.get('categorization_llm', 'Keywords')
                    st.markdown("---")
                    st.markdown("**📊 Categorisatie:**")
                    if categorization_llm and categorization_llm != 'Keywords':
                        llm_display = {
                            'Hugging Face': 'Hugging Face',
                            'Groq': 'Groq',
                            'OpenAI': 'OpenAI',
                            'ChatLLM': 'ChatLLM (Aitomatic)'
                        }.get(categorization_llm, categorization_llm)
                        st.caption(f"{llm_display}")
                    else:
                        st.caption("Keywords")
                else:
                    st.markdown("### 🏷️ Categorieën")
                    st.caption("Geen categorieën")
        
        else:
            # No image - show categories only
            if categories and len(categories) > 0:
                st.markdown("---")
                from html import escape
                # Build all categories in one HTML string
                category_html = '<div style="margin: 0.25rem 0;">'
                for cat in categories:
                    if cat:
                        escaped_cat = escape(str(cat))
                        category_html += f'<span class="article-category" style="margin-right: 0.5rem; display: inline-block;">{escaped_cat}</span>'
                category_html += '</div>'
                st.markdown(category_html, unsafe_allow_html=True)
                
                categorization_llm = article.get('categorization_llm', 'Keywords')
                st.markdown("---")
                st.markdown("**📊 Categorisatie:**")
                if categorization_llm and categorization_llm != 'Keywords':
                    llm_display = {
                        'Hugging Face': 'Hugging Face',
                        'Groq': 'Groq',
                        'OpenAI': 'OpenAI',
                        'ChatLLM': 'ChatLLM (Aitomatic)'
                    }.get(categorization_llm, categorization_llm)
                    st.caption(f"{llm_display}")
                else:
                    st.caption("Keywords")
        
        st.markdown("---")
        
        # Description
        if article.get('description'):
            clean_description = clean_html_for_display(article['description'])
            st.markdown(clean_description, unsafe_allow_html=True)
            st.markdown("---")
        
        # ELI5 Summary - show if exists, otherwise show placeholder (page loads immediately)
        if article.get('eli5_summary_nl'):
            # ELI5 already exists - show it immediately
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
            # ELI5 doesn't exist - show placeholder with manual generation button
            # Page loads immediately without waiting for ELI5 generation
            st.info("📚 Eenvoudige uitleg is nog niet beschikbaar voor dit artikel.")
            
            # Check if we have API keys
            has_llm_keys = any([
                get_secret('GROQ_API_KEY'),
                get_secret('HUGGINGFACE_API_KEY'),
                get_secret('OPENAI_API_KEY'),
                get_secret('CHATLLM_API_KEY')
            ])
            
            if has_llm_keys:
                # Show button to manually generate ELI5 (optional, non-blocking)
                if st.button("🔄 Genereer Eenvoudige Uitleg Nu", use_container_width=True):
                    # Generate ELI5 when button is clicked
                    with st.spinner("🔄 Eenvoudige uitleg genereren..."):
                        text = f"{article.get('title', '')} {article.get('description', '')}"
                        if article.get('full_content'):
                            text += f" {article.get('full_content', '')[:1000]}"
                        
                        result = generate_eli5_summary_nl_with_llm(text, article.get('title', ''))
                        
                        if result and result.get('summary'):
                            # Save to database
                            try:
                                supabase.update_article_eli5(article['id'], result['summary'], result.get('llm'))
                            except Exception as e:
                                print(f"Error saving ELI5: {e}")
                            
                            # Rerun to show the ELI5
                            st.rerun()
                        else:
                            st.error("⚠️ Eenvoudige uitleg kon niet worden gegenereerd. Probeer het later opnieuw.")
                else:
                    st.caption("💡 Tip: De automatische RSS checker genereert ELI5 samenvattingen in de achtergrond. Of klik op de knop hierboven om het nu te genereren.")
            else:
                st.caption("ℹ️ Geen LLM API keys geconfigureerd. ELI5 samenvattingen worden niet gegenereerd.")
            
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
        
        st.markdown('</div>', unsafe_allow_html=True)  # Close article-detail-content
    
    # Left and right columns are empty (white space)
    with col_left:
        st.empty()  # Empty column for white space
    
    with col_right:
        st.empty()  # Empty column for white space
    
    st.markdown('</div>', unsafe_allow_html=True)  # Close article-detail-container


def render_nieuws_page():
    """Render main news overview page."""
    supabase = st.session_state.supabase
    
    # Check if viewing article detail first - don't show "Nieuws" title
    if "article" in st.query_params:
        render_article_detail(st.query_params["article"])
        return
    
    st.title("📰 Nieuws")
    
    # Show RSS checker status
    if is_running():
        check_info = get_last_check_info()
        if check_info:
            last_check = check_info.get('last_check_time')
            result = check_info.get('last_check_result', {})
            if last_check:
                try:
                    from dateutil import parser
                    last_check_dt = parser.parse(last_check)
                    now = datetime.now(pytz.UTC)
                    if last_check_dt.tzinfo is None:
                        last_check_dt = pytz.UTC.localize(last_check_dt)
                    time_ago = now - last_check_dt
                    minutes_ago = int(time_ago.total_seconds() / 60)
                    
                    if result.get('inserted', 0) > 0 or result.get('updated', 0) > 0:
                        st.success(f"🔄 Automatische updates: {result.get('inserted', 0)} nieuwe, {result.get('updated', 0)} bijgewerkt ({minutes_ago} min geleden)")
                    elif minutes_ago < 20:
                        st.info(f"🔄 Automatische updates actief (laatste check: {minutes_ago} min geleden)")
                except Exception as e:
                    # Silently fail if status can't be displayed
                    pass
    
    # Filters
    col1, col2 = st.columns([2, 1])
    with col1:
        search_query = st.text_input("🔍 Zoeken", placeholder="Zoek in artikelen...", key="search")
    with col2:
        from categorization_engine import get_all_categories
        all_categories = get_all_categories()
        category_options = ["Alle"] + all_categories
        category_filter = st.selectbox(
            "Categorie",
            category_options,
            key="category_filter"
        )
    
    st.markdown("---")
    
    # Action buttons
    col1, col2 = st.columns(2)
    with col1:
        refresh_clicked = st.button("🔄 Artikelen Vernieuwen", use_container_width=True)
    with col2:
        recategorize_clicked = st.button("🏷️ Alle Artikelen Her-categoriseren", use_container_width=True)
    
    # Handle refresh button
    if refresh_clicked:
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        feed_urls = [
            'https://feeds.nos.nl/nosnieuwsalgemeen',
            'https://feeds.nos.nl/nosnieuwsbinnenland',
            'https://feeds.nos.nl/nosnieuwsbuitenland',
        ]
        
        total_inserted = 0
        total_updated = 0
        total_skipped = 0
        
        for idx, feed_url in enumerate(feed_urls):
            status_text.text(f"Feed {idx + 1}/{len(feed_urls)} ophalen...")
            progress_bar.progress((idx) / len(feed_urls))
            
            try:
                # Use LLM categorization for better accuracy
                result = fetch_and_upsert_articles(feed_url, max_items=30, use_llm_categorization=True)
                if result.get('success'):
                    total_inserted += result.get('inserted', 0)
                    total_updated += result.get('updated', 0)
                    total_skipped += result.get('skipped', 0)
                else:
                    st.warning(f"Fout bij feed {feed_url}: {result.get('error', 'Onbekende fout')}")
            except Exception as e:
                st.error(f"Fout bij verwerken van feed: {str(e)[:200]}")
                total_skipped += 1
        
        progress_bar.progress(1.0)
        status_text.text("Klaar!")
        
        if total_inserted > 0 or total_updated > 0:
            st.success(f"✅ {total_inserted} nieuwe artikelen, {total_updated} bijgewerkt")
            if total_skipped > 0:
                st.info(f"ℹ️ {total_skipped} artikelen overgeslagen")
        else:
            st.info("Geen nieuwe artikelen gevonden")
        
        # Small delay to show progress
        import time
        time.sleep(0.5)
        st.rerun()
    
    # Handle recategorize button
    if recategorize_clicked:
        from articles_repository import recategorize_all_articles
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        status_text.text("Artikelen ophalen...")
        progress_bar.progress(0.1)
        
        # Recategorize using LLM
        status_text.text("Artikelen her-categoriseren met LLM...")
        progress_bar.progress(0.3)
        
        result = recategorize_all_articles(limit=None, use_llm=True)
        
        progress_bar.progress(1.0)
        
        if result.get('success'):
            processed = result.get('processed', 0)
            updated = result.get('updated', 0)
            errors = result.get('errors', 0)
            
            status_text.text("Klaar!")
            
            if updated > 0:
                st.success(f"✅ {updated} artikelen her-categoriseerd!")
                if errors > 0:
                    st.warning(f"⚠️ {errors} fouten opgetreden")
            else:
                st.info("Geen artikelen gevonden om te her-categoriseren")
        else:
            st.error(f"Fout: {result.get('error', 'Onbekende fout')}")
        
        import time
        time.sleep(2)
        st.rerun()
    
    # Get user preferences
    blacklist = []
    selected_categories = None
    if st.session_state.user:
        # Load preferences if not already loaded
        if st.session_state.preferences is None:
            user_id = get_user_id(st.session_state.user)
            if user_id:
                st.session_state.preferences = supabase.get_user_preferences(user_id)
        
        if st.session_state.preferences:
            blacklist = st.session_state.preferences.get('blacklist_keywords', [])
            selected_categories = st.session_state.preferences.get('selected_categories')
    
    # Debug: Show blacklist if in debug mode
    if st.session_state.get('debug_mode', False):
        if blacklist:
            st.info(f"🔍 Debug: Blacklist actief: {', '.join(blacklist)}")
        else:
            st.info("🔍 Debug: Geen blacklist actief")
    
    # Get articles
    category = None if category_filter == "Alle" else category_filter
    try:
        categories_filter = selected_categories if (st.session_state.user and selected_categories) else None
        
        # Ensure blacklist is properly formatted
        blacklist_to_use = None
        if blacklist and isinstance(blacklist, list) and len(blacklist) > 0:
            # Filter out empty strings and normalize
            blacklist_to_use = [kw.strip() for kw in blacklist if kw and kw.strip()]
            if len(blacklist_to_use) == 0:
                blacklist_to_use = None
        
        articles = supabase.get_articles(
            limit=50,
            category=category,
            categories=categories_filter,
            search_query=search_query if search_query else None,
            blacklist_keywords=blacklist_to_use
        )
    except Exception as e:
        st.error(f"Fout bij ophalen artikelen: {str(e)}")
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
    
    # Check if viewing article detail (same as Nieuws page)
    if "article" in st.query_params:
        render_article_detail(st.query_params["article"])
        return
    
    st.title("😤 Dit wil je niet")
    st.markdown("---")
    st.markdown("**Deze pagina toont alle artikelen die door de blacklist filter of door gedeselecteerde categorieën zijn uitgefilterd.**")
    st.markdown("Gebruik dit om te testen of de categorisatie en keyword filters correct werken.")
    st.markdown("---")
    
    # Check if user is logged in
    if not st.session_state.user:
        st.warning("⚠️ Je moet ingelogd zijn om deze pagina te gebruiken.")
        st.info("Ga naar de 'Gebruiker' pagina om in te loggen.")
        return
    
    # Load preferences if not already loaded
    if st.session_state.preferences is None:
        user_id = get_user_id(st.session_state.user)
        if user_id:
            st.session_state.preferences = supabase.get_user_preferences(user_id)
    
    # Get user preferences to know what was filtered
    blacklist = []
    selected_categories = None
    if st.session_state.preferences:
        blacklist = st.session_state.preferences.get('blacklist_keywords', [])
        selected_categories = st.session_state.preferences.get('selected_categories', [])
    
    # Get all available categories
    from categorization_engine import get_all_categories
    all_categories = get_all_categories()
    
    # Determine deselected categories (categories that are NOT in selected_categories)
    deselected_categories = []
    if selected_categories:
        deselected_categories = [cat for cat in all_categories if cat not in selected_categories]
    
    # Debug info
    if st.session_state.get('debug_mode', False):
        user_id = get_user_id(st.session_state.user) or 'N/A'
        st.write(f"Debug - User ID: {user_id}")
        st.write(f"Debug - Preferences loaded: {st.session_state.preferences is not None}")
        if st.session_state.preferences:
            st.write(f"Debug - Preferences keys: {list(st.session_state.preferences.keys())}")
            st.write(f"Debug - Blacklist from prefs: {st.session_state.preferences.get('blacklist_keywords', 'NOT FOUND')}")
            st.write(f"Debug - Selected categories: {selected_categories}")
            st.write(f"Debug - Deselected categories: {deselected_categories}")
    
    # Show info about active filters
    has_filters = False
    if blacklist and len(blacklist) > 0:
        st.info(f"**Actieve blacklist ({len(blacklist)} trefwoorden):** {', '.join(blacklist)}")
        has_filters = True
    
    if deselected_categories and len(deselected_categories) > 0:
        st.info(f"**Gedeselecteerde categorieën ({len(deselected_categories)}):** {', '.join(deselected_categories)}")
        has_filters = True
    
    if not has_filters:
        st.warning("⚠️ Geen filters actief. Ga naar de 'Gebruiker' pagina om categorieën te deselecteren of trefwoorden toe te voegen aan je blacklist.")
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
            article_categories = article.get('categories', [])
            if not isinstance(article_categories, list):
                article_categories = []
            
            # Check if article is filtered by blacklist
            filtered_by_blacklist = False
            if blacklist:
                title = (article.get('title') or '').lower()
                description = (article.get('description') or '').lower()
                full_content = (article.get('full_content') or '').lower()
                all_text = f"{title} {description} {full_content}"
                
                for keyword in blacklist:
                    keyword_lower = keyword.lower().strip()
                    if keyword_lower and keyword_lower in all_text:
                        filtered_by_blacklist = True
                        break
            
            # Check if article is filtered by deselected categories
            filtered_by_category = False
            if deselected_categories:
                # Check if article has any category that is deselected
                for article_cat in article_categories:
                    if article_cat in deselected_categories:
                        filtered_by_category = True
                        break
            
            # Add article if it's filtered by either blacklist or category
            if filtered_by_blacklist or filtered_by_category:
                filtered_articles.append(article)
        
        if filtered_articles:
            st.subheader(f"📋 {len(filtered_articles)} uitgefilterde artikelen")
            st.caption("Deze artikelen worden normaal gesproken verborgen door je filters.")
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
            st.success("✅ Geen artikelen gevonden die door je filters worden uitgefilterd.")
            st.info("Dit betekent dat er momenteel geen artikelen zijn die door je blacklist of gedeselecteerde categorieën worden uitgefilterd.")
    
    except Exception as e:
        st.error(f"Fout bij ophalen artikelen: {str(e)}")
        import traceback
        st.code(traceback.format_exc())


def recategorize_all_articles(supabase) -> int:
    """Recategorize all articles in the database using LLM."""
    try:
        from categorization_engine import categorize_article
        
        # Get all articles
        articles = supabase.get_articles(limit=1000)  # Get up to 1000 articles
        
        if not articles:
            return 0
        
        recategorized_count = 0
        
        for article in articles:
            try:
                title = article.get('title', '')
                description = article.get('description', '')
                content = article.get('full_content', '')
                article_id = article.get('id')
                
                if not title or not article_id:
                    continue
                
                # Categorize using LLM
                result = categorize_article(title, description, content)
                categories = result.get('categories', [])
                llm = result.get('llm', 'Keywords')
                
                # Update article in database
                if supabase.update_article_categories(article_id, categories, llm):
                    recategorized_count += 1
                
                # Small delay to avoid rate limiting
                import time
                time.sleep(0.1)
                
            except Exception as e:
                print(f"Error recategorizing article {article.get('id', 'unknown')}: {e}")
                continue
        
        return recategorized_count
    except Exception as e:
        print(f"Error in recategorize_all_articles: {e}")
        return -1


def render_statistics_page():
    """Render statistics page with article counts, ELI5 summaries, categories, and user count."""
    supabase = st.session_state.supabase
    
    st.title("📊 Statistics")
    st.markdown("---")
    
    # Always using Supabase now
    from supabase_client import SupabaseClient
    import pandas as pd
    
    is_supabase = isinstance(supabase, SupabaseClient)
    
    if is_supabase:
        # Get statistics from Supabase
        try:
            stats = supabase.get_statistics()
            
            # Display article counts
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("📰 Totaal Artikelen", stats.get('total_articles', 0))
            
            with col2:
                st.metric("📚 Artikelen met ELI5", stats.get('articles_with_eli5', 0))
            
            with col3:
                st.metric("⏳ Artikelen zonder ELI5", stats.get('articles_without_eli5', 0))
            
            st.markdown("---")
            
            # ELI5 summary percentage
            total = stats.get('total_articles', 0)
            with_eli5 = stats.get('articles_with_eli5', 0)
            if total > 0:
                eli5_percentage = (with_eli5 / total) * 100
                st.subheader("ELI5 Samenvattingen")
                st.progress(eli5_percentage / 100)
                st.caption(f"{eli5_percentage:.1f}% van de artikelen heeft een ELI5 samenvatting")
            
            st.markdown("---")
            
            # Recategorize all articles button
            st.subheader("🔄 Hercategorisatie")
            st.info("Herbereken alle categorieën voor artikelen met behulp van LLM API. Dit kan even duren.")
            
            if st.button("🔄 Hercategoriseer Alle Artikelen", use_container_width=True):
                with st.spinner("Artikelen worden hercategoriseerd... Dit kan even duren."):
                    recategorized_count = recategorize_all_articles(supabase)
                    if recategorized_count >= 0:
                        st.success(f"✅ {recategorized_count} artikelen zijn hercategoriseerd!")
                        st.rerun()
                    else:
                        st.error("❌ Er is een fout opgetreden bij het hercategoriseren.")
            
            st.markdown("---")
            
            # Category distribution graph
            category_counts = stats.get('category_counts', {})
            if category_counts:
                st.subheader("📈 Categorisatie Labels Distributie")
                
                # Sort categories by count
                sorted_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
                
                # Create data for chart
                categories = [cat for cat, count in sorted_categories]
                counts = [count for cat, count in sorted_categories]
                
                # Use Streamlit's built-in chart
                df = pd.DataFrame({
                    'Categorie': categories,
                    'Aantal': counts
                })
                
                st.bar_chart(df.set_index('Categorie'))
                
                # Also show as table
                with st.expander("📋 Gedetailleerde Categorie Tabel"):
                    st.dataframe(df, use_container_width=True)
            else:
                st.info("Geen categorisatie data beschikbaar")
            
            st.markdown("---")
            
            # User count
            st.subheader("👥 Gebruikers")
            try:
                # Try to get user count
                user_count = supabase.get_user_count()
                if user_count >= 0:
                    st.metric("Geregistreerde Gebruikers", user_count)
                    if user_count == 0:
                        st.caption("ℹ️ Geen gebruikers gevonden. Dit kan betekenen dat gebruikers nog geen voorkeuren hebben ingesteld.")
                else:
                    st.info("⚠️ Gebruikersaantal kon niet worden opgehaald.")
                    st.caption("Tip: Zorg ervoor dat de user_preferences tabel bestaat en dat gebruikers zijn ingelogd (dit creëert automatisch voorkeuren).")
            except Exception as e:
                st.warning(f"⚠️ Fout bij ophalen gebruikersaantal: {str(e)}")
                st.caption("Controleer de Supabase connectie en database structuur.")
            
        except Exception as e:
            st.error(f"Fout bij ophalen statistieken: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
    else:
        # Supabase not initialized
        st.error("❌ **Fout**: Supabase is niet geïnitialiseerd. Statistieken zijn niet beschikbaar.")
        st.info("💡 Controleer of SUPABASE_URL en SUPABASE_ANON_KEY correct zijn ingesteld.")
        
        # Try to get basic stats anyway (in case supabase is None but we want to show something)
        try:
            articles = supabase.get_articles(limit=1000) if supabase else []
            total_articles = len(articles)
            
            articles_with_eli5 = sum(1 for a in articles if a.get('eli5_summary_nl'))
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("📰 Totaal Artikelen", total_articles)
            with col2:
                st.metric("📚 Artikelen met ELI5", articles_with_eli5)
            
            # Category counts
            category_counts = {}
            for article in articles:
                categories = article.get('categories', [])
                if isinstance(categories, list):
                    for cat in categories:
                        if cat:
                            category_counts[cat] = category_counts.get(cat, 0) + 1
            
            if category_counts:
                st.markdown("---")
                st.subheader("📈 Categorisatie Labels Distributie")
                sorted_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
                
                df = pd.DataFrame({
                    'Categorie': [cat for cat, count in sorted_categories],
                    'Aantal': [count for cat, count in sorted_categories]
                })
                
                st.bar_chart(df.set_index('Categorie'))
        except Exception as e:
            st.error(f"Fout bij ophalen lokale statistieken: {str(e)}")


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
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Wachtwoord", type="password", key="login_password")
            
            if st.button("Inloggen", use_container_width=True):
                result = supabase.sign_in(email, password)
                if result.get('success'):
                    st.session_state.user = result.get('user')
                    st.session_state.preferences = None
                    # Clear explicit logout flag when user successfully logs in manually
                    if 'user_explicitly_logged_out' in st.session_state:
                        del st.session_state.user_explicitly_logged_out
                    st.success("Ingelogd!")
                    st.rerun()
                else:
                    st.error(f"Inloggen mislukt: {result.get('error', 'Onbekende fout')}")
        
        with tab2:
            new_email = st.text_input("Email", key="signup_email")
            new_password = st.text_input("Wachtwoord", type="password", key="signup_password")
            confirm_password = st.text_input("Bevestig wachtwoord", type="password", key="signup_confirm")
            
            if st.button("Registreren", use_container_width=True):
                if new_password != confirm_password:
                    st.error("Wachtwoorden komen niet overeen")
                elif len(new_password) < 6:
                    st.error("Wachtwoord moet minimaal 6 tekens zijn")
                else:
                    result = supabase.sign_up(new_email, new_password)
                    if result.get('success'):
                        # Clear explicit logout flag when user successfully registers
                        if 'user_explicitly_logged_out' in st.session_state:
                            del st.session_state.user_explicitly_logged_out
                        st.success("Account aangemaakt! Je kunt nu inloggen.")
                    else:
                        st.error(f"Registratie mislukt: {result.get('error', 'Onbekende fout')}")
    else:
        # User is logged in
        user_email = get_user_email(st.session_state.user)
        # If we can't get email but user is logged in, use default (auto-login)
        if not user_email:
            user_email = 'test@hotmail.com'
        
        st.success(f"👤 Ingelogd als: {user_email}")
        
        if st.button("🚪 Uitloggen", use_container_width=True):
            supabase.sign_out()
            st.session_state.user = None
            st.session_state.preferences = None
            # Set flag to prevent auto-login after explicit logout
            st.session_state.user_explicitly_logged_out = True
            # Reset auto-login flag
            if 'auto_login_attempted' in st.session_state:
                del st.session_state.auto_login_attempted
            st.rerun()
        
        st.markdown("---")
        
        # Get preferences
        if st.session_state.preferences is None:
            user_id = get_user_id(st.session_state.user)
            if user_id:
                st.session_state.preferences = supabase.get_user_preferences(user_id)
        
        prefs = st.session_state.preferences or {}
        blacklist = prefs.get('blacklist_keywords', []) if prefs else []
        selected_categories = prefs.get('selected_categories') if prefs else None
        
        # Ensure selected_categories is always a list (not None)
        # If empty or None, default to all categories selected
        from categorization_engine import get_all_categories
        all_categories = get_all_categories()
        
        # If selected_categories is None, empty, or not a list, default to all categories
        if selected_categories is None or not isinstance(selected_categories, list) or len(selected_categories) == 0:
            # Default to all categories selected for display
            selected_categories = all_categories.copy()
        
        # Category selection
        st.subheader("📂 Categorieën")
        st.caption("Selecteer welke categorieën je wilt zien")
        
        category_selections = {}
        
        for category in all_categories:
            # Check if category should be selected (default to True if in selected_categories)
            is_selected = category in selected_categories
            category_selections[category] = st.checkbox(
                category,
                value=is_selected,
                key=f"cat_pref_{category}"
            )
        
        # Store current selections in session state for saving
        new_selected = [cat for cat, selected in category_selections.items() if selected]
        
        # Save button for categories
        if st.button("💾 Opslaan Categorieën", use_container_width=True, type="primary"):
            user_id = get_user_id(st.session_state.user)
            if user_id:
                if supabase.update_user_preferences(user_id, selected_categories=new_selected):
                    st.session_state.preferences = None
                    st.success("✅ Categorieën opgeslagen!")
                    st.rerun()
                else:
                    st.error("❌ Fout bij opslaan van categorieën")
            else:
                st.error("❌ Geen gebruiker ID gevonden")
        
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
                        user_id = get_user_id(st.session_state.user)
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
                    user_id = get_user_id(st.session_state.user)
                    if user_id and supabase.update_user_preferences(user_id, blacklist_keywords=blacklist):
                        st.session_state.preferences = None
                        st.success(f"'{keyword}' toegevoegd")
                        st.rerun()
                else:
                    st.warning("Dit trefwoord staat al in de blacklist")


def main():
    """Main Streamlit app."""
    # Initialize storage
    supabase = init_supabase()
    if not supabase:
        st.error("Opslag niet geconfigureerd. Zie de documentatie voor setup instructies.")
        return
    
    # Start background RSS checker (only once)
    if 'rss_checker_started' not in st.session_state:
        try:
            start_background_checker()
            st.session_state.rss_checker_started = True
        except Exception as e:
            # Silently fail if checker can't start (e.g., in some deployment environments)
            print(f"Could not start RSS background checker: {e}")
            st.session_state.rss_checker_started = False
    
    # Check authentication
    if st.session_state.user is None:
        # First try to get existing session
        user = supabase.get_current_user()
        if user:
            st.session_state.user = user
            # Clear explicit logout flag if user successfully logged in manually
            if 'user_explicitly_logged_out' in st.session_state:
                del st.session_state.user_explicitly_logged_out
        else:
            # Auto-login with test@hotmail.com if no user is logged in
            # BUT: Don't auto-login if user explicitly logged out
            if not st.session_state.get('user_explicitly_logged_out', False):
                # Only attempt once per session to avoid infinite loops
                if 'auto_login_attempted' not in st.session_state:
                    st.session_state.auto_login_attempted = True
                    test_email = "test@hotmail.com"
                    test_password = get_secret('TEST_USER_PASSWORD', 'test123')  # Default password, can be overridden via env var
                    
                    result = supabase.sign_in(test_email, test_password)
                    if result.get('success'):
                        user_obj = result.get('user')
                        st.session_state.user = user_obj
                        # Ensure email is accessible - store it explicitly if needed
                        # The user object from Supabase should have email, but we'll handle it in get_user_email()
                        # Load preferences immediately
                        user_id = get_user_id(user_obj)
                        if user_id:
                            prefs = supabase.get_user_preferences(user_id)
                            st.session_state.preferences = prefs
                            # Ensure test@hotmail.com has all categories selected
                            from categorization_engine import get_all_categories
                            all_categories = get_all_categories()
                            if prefs.get('selected_categories') != all_categories:
                                # Update to have all categories selected
                                supabase.update_user_preferences(user_id, selected_categories=all_categories)
                                # Reload preferences
                                st.session_state.preferences = supabase.get_user_preferences(user_id)
                        # Rerun to show the logged-in state
                        st.rerun()
                    # If login fails, silently continue - user can manually login
    
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
    elif page == "Statistics":
        render_statistics_page()
    elif page == "Gebruiker":
        render_gebruiker_page()


if __name__ == "__main__":
    main()
