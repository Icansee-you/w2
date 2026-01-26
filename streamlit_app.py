"""
Streamlit app for NOS News Aggregator with horizontal menu.
Pages: Nieuws, Achtergrond, Gebruiker
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

# Import RSS background checker functions (with error handling for deployment)
try:
    from rss_background_checker import start_background_checker, get_last_check_info, is_running
except ImportError as e:
    # Fallback if rss_background_checker cannot be imported (e.g., missing dependencies)
    print(f"Warning: Could not import rss_background_checker: {e}")
    def start_background_checker():
        pass
    def get_last_check_info():
        return None
    def is_running():
        return False

# Page configuration
st.set_page_config(
    page_title="NOS Nieuws Aggregator",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS om de header en extra whitespace te verwijderen - Agressieve aanpak
st.markdown("""
    <style>
    /* Verberg de standaard Streamlit-header volledig */
    header[data-testid="stHeader"] {
        height: 0px !important;
        min-height: 0px !important;
        visibility: hidden !important;
        display: none !important;
    }
    
    /* Verberg alle header elementen */
    .stApp > header,
    header[data-testid="stHeader"],
    div[data-testid="stHeader"] {
        height: 0px !important;
        min-height: 0px !important;
        max-height: 0px !important;
        padding: 0 !important;
        margin: 0 !important;
        visibility: hidden !important;
        display: none !important;
        overflow: hidden !important;
    }
    
    /* Verklein de padding van de hoofdcontainer - meerdere selectors */
    .main .block-container,
    .block-container,
    div[data-testid="stAppViewContainer"] > .main .block-container {
        padding-top: 0rem !important;
        padding-bottom: 1rem !important;
        margin-top: 0rem !important;
        max-width: 100% !important;
    }
    
    /* Target de app view container zelf */
    section[data-testid="stAppViewContainer"],
    div[data-testid="stAppViewContainer"] {
        padding-top: 0rem !important;
        margin-top: 0rem !important;
    }
    
    /* Target de stApp container */
    .stApp {
        padding-top: 0rem !important;
        margin-top: 0rem !important;
    }
    
    /* Hide default Streamlit menu and footer */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Remove spacing from first element in main container */
    .main .block-container > div:first-child,
    .main > div:first-child,
    .main .block-container > *:first-child {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }
    
    /* Reduce spacing in block containers */
    [data-testid="stVerticalBlock"] {
        gap: 0.5rem !important;
    }
    
    /* First vertical block should have no top margin */
    [data-testid="stVerticalBlock"]:first-child,
    [data-testid="stVerticalBlock"]:nth-child(1) {
        margin-top: 0 !important;
        padding-top: 0 !important;
        margin-bottom: 0 !important;
    }
    
    /* Target element containers */
    .element-container:first-child,
    .element-container:nth-child(1) {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }
    
    /* Remove any top spacing from the horizontal menu container */
    .horizontal-menu {
        margin-top: 0 !important;
        padding-top: 0.5rem !important;
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
    
    /* Target markdown containers */
    .stMarkdown:first-child,
    .stMarkdown:nth-child(1) {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }
    
    /* Remove spacing from Streamlit's internal spacing elements */
    .stApp > div:first-child,
    .stApp > section:first-child {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }
    
    /* Target all possible spacing sources */
    div[class*="block-container"]:first-child {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
    
    /* Remove any top margin/padding from the very first element */
    body > div:first-child,
    #root > div:first-child {
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

# JavaScript om dynamisch whitespace te verwijderen (backup voor CSS)
st.markdown("""
    <script>
    (function() {
        function removeTopWhitespace() {
            // Verberg header
            const headers = document.querySelectorAll('header[data-testid="stHeader"], .stApp > header, div[data-testid="stHeader"]');
            headers.forEach(header => {
                header.style.height = '0px';
                header.style.minHeight = '0px';
                header.style.maxHeight = '0px';
                header.style.padding = '0';
                header.style.margin = '0';
                header.style.visibility = 'hidden';
                header.style.display = 'none';
            });
            
            // Verwijder padding/margin van block-container
            const containers = document.querySelectorAll('.main .block-container, .block-container');
            containers.forEach(container => {
                container.style.paddingTop = '0rem';
                container.style.marginTop = '0rem';
            });
            
            // Verwijder spacing van eerste elementen
            const firstElements = document.querySelectorAll('.main .block-container > div:first-child, [data-testid="stVerticalBlock"]:first-child');
            firstElements.forEach(el => {
                el.style.marginTop = '0';
                el.style.paddingTop = '0';
            });
            
            // Verwijder spacing van app view container
            const appView = document.querySelector('section[data-testid="stAppViewContainer"]');
            if (appView) {
                appView.style.paddingTop = '0rem';
                appView.style.marginTop = '0rem';
            }
        }
        
        // Run immediately
        removeTopWhitespace();
        
        // Run after DOM is ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', removeTopWhitespace);
        }
        
        // Run after a short delay (for dynamic content)
        setTimeout(removeTopWhitespace, 100);
        setTimeout(removeTopWhitespace, 500);
        
        // Monitor for changes (MutationObserver)
        const observer = new MutationObserver(removeTopWhitespace);
        observer.observe(document.body, {
            childList: true,
            subtree: true,
            attributes: true,
            attributeFilter: ['style', 'class']
        });
        
        // Also run periodically as backup
        setInterval(removeTopWhitespace, 1000);
    })();
    </script>
    """,
    unsafe_allow_html=True)

# Initialize session state
if 'user' not in st.session_state:
    st.session_state.user = None
if 'supabase' not in st.session_state:
    st.session_state.supabase = None
if 'preferences' not in st.session_state:
    st.session_state.preferences = None
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'Nieuws'
if 'manual_login_performed' not in st.session_state:
    st.session_state.manual_login_performed = False  # Track if user manually logged in


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
    
    # Koningshuis keywords (highest priority)
    if any(kw in cat_lower for kw in ['koningshuis', 'koning', 'koningin', 'prins', 'oranje']):
        return 'Koningshuis'
    
    # Misdaad keywords
    if any(kw in cat_lower for kw in ['misdaad', 'crimineel', 'diefstal', 'moord', 'aanslag', 'drugs']):
        return 'Misdaad'
    
    # Sport keywords
    if any(kw in cat_lower for kw in ['sport', 'voetbal', 'wielrennen', 'olympisch']):
        return 'Sport'
    
    # Politiek keywords
    if any(kw in cat_lower for kw in ['politiek', 'kabinet', 'minister', 'regering', 'gemeente']):
        return 'Politiek'
    
    # Buitenland keywords
    if any(kw in cat_lower for kw in ['buitenland', 'internationaal', 'conflict', 'europa', 'oorlog']):
        return 'Buitenland'
    
    # Cultuur keywords
    if any(kw in cat_lower for kw in ['cultuur', 'kunst', 'museum', 'theater', 'muziek']):
        return 'Cultuur'
    
    # Opmerkelijk keywords
    if any(kw in cat_lower for kw in ['opmerkelijk', 'bijzonder', 'vreemd', 'grappig']):
        return 'Opmerkelijk'
    
    # Algemeen (default)
    if any(kw in cat_lower for kw in ['algemeen', 'overig', 'nieuws']):
        return 'Algemeen'
    
    return None


def _map_old_categories_to_new(old_categories: List[str], valid_categories: List[str]) -> List[str]:
    """Map old category names to new category names."""
    if not old_categories:
        return []
    
    # Mapping from old categories to new categories (case-insensitive matching)
    # This maps all old category variations to the new 8 categories
    category_mapping = {
        # Koningshuis mappings
        'koningshuis': 'Koningshuis',
        
        # Misdaad mappings
        'misdaad': 'Misdaad',
        'crimineel': 'Misdaad',
        'criminaliteit': 'Misdaad',
        
        # Sport mappings
        'sport - voetbal': 'Sport',
        'sport - wielrennen': 'Sport',
        'overige sport': 'Sport',
        'sport': 'Sport',
        
        # Politiek mappings
        'nationale politiek': 'Politiek',
        'lokale politiek': 'Politiek',
        'politiek': 'Politiek',
        
        # Buitenland mappings
        'buitenland - europa': 'Buitenland',
        'buitenland - overig': 'Buitenland',
        'internationale conflicten': 'Buitenland',
        'buitenland': 'Buitenland',
        'internationaal': 'Buitenland',
        
        # Cultuur mappings
        'cultuur': 'Cultuur',
        'kunst': 'Cultuur',
        'entertainment': 'Cultuur',
        'bekende nederlanders': 'Cultuur',  # Map bekende personen to Cultuur
        'bekende personen': 'Cultuur',  # Map bekende personen to Cultuur
        
        # Opmerkelijk mappings
        'opmerkelijk': 'Opmerkelijk',
        'bijzonder': 'Opmerkelijk',
        
        # Algemeen mappings
        'algemeen': 'Algemeen',
        'overig': 'Algemeen',
        'binnenland': 'Algemeen',  # Map binnenland to Algemeen
        'nieuws': 'Algemeen',
        
        # Other old categories that should be filtered out or mapped
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
    menu_html = f'<div class="horizontal-menu"><div class="menu-items-container"><a class="menu-item" href="?page=Nieuws" onclick="window.location.href=\'?page=Nieuws\'; return false;" target="_self">Nieuws</a><a class="menu-item" href="?page=Waarom" onclick="window.location.href=\'?page=Waarom\'; return false;" target="_self">Achtergrond</a><a class="menu-item" href="?page=Frustrate" onclick="window.location.href=\'?page=Frustrate\'; return false;" target="_self">Dit wil je niet</a><a class="menu-item" href="?page=Statistics" onclick="window.location.href=\'?page=Statistics\'; return false;" target="_self">Statistieken</a><a class="menu-item" href="?page=Gebruiker" onclick="window.location.href=\'?page=Gebruiker\'; return false;" target="_self">Gebruiker</a></div>{user_info_html}</div>'
    
    st.markdown(menu_html, unsafe_allow_html=True)
    
    # Update current page from query params
    page = st.query_params.get("page", "Nieuws")
    # Check for admin page (can be accessed via ?page=Admin)
    # Note: Streamlit doesn't support custom routes like /admin, but you can use ?page=Admin
    if page == "Admin":
        st.session_state.current_page = "Admin"
    elif page in ["Nieuws", "Waarom", "Frustrate", "Statistics", "Gebruiker"]:
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
            with st.spinner("🔄 Kort & Simpel genereren..."):
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
    
    # Track article opened (if user is logged in)
    if st.session_state.user:
        user_id = get_user_id(st.session_state.user)
        if user_id:
            try:
                supabase.track_article_opened(user_id, article_id)
            except Exception as e:
                # Silently fail if tracking doesn't work (e.g., table doesn't exist yet)
                print(f"Could not track article opened: {e}")
    
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
                <div class="eli5-title">📚 Kort & Simpel:</div>
                {article['eli5_summary_nl']}
                <div class="eli5-llm-badge">Gegenereerd met: {llm_display}</div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("---")
        else:
            # ELI5 doesn't exist - show placeholder with manual generation button
            # Page loads immediately without waiting for ELI5 generation
            st.info("📚 Kort & Simpel is nog niet beschikbaar voor dit artikel.")
            
            # Check if we have API keys
            has_llm_keys = any([
                get_secret('GROQ_API_KEY'),
                get_secret('HUGGINGFACE_API_KEY'),
                get_secret('OPENAI_API_KEY'),
                get_secret('CHATLLM_API_KEY')
            ])
            
            if has_llm_keys:
                # Show button to manually generate ELI5 (optional, non-blocking)
                if st.button("🔄 Genereer Kort & Simpel Nu", use_container_width=True):
                    # Generate ELI5 when button is clicked
                    with st.spinner("🔄 Kort & Simpel genereren..."):
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
                            st.error("⚠️ Kort & Simpel kon niet worden gegenereerd. Probeer het later opnieuw.")
                else:
                    st.caption("💡 Tip: De automatische RSS checker genereert Kort & Simpel samenvattingen in de achtergrond. Of klik op de knop hierboven om het nu te genereren.")
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
        search_query = st.text_input("🔍 Zoeken", placeholder="Zoek in artikelen...", key="search")
    
    st.markdown("---")
    
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
    
    # Get articles (no category filter - always show all categories)
    category = None
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
        st.info("ℹ️ Geen artikelen gevonden. Artikelen worden automatisch elke 15 minuten opgehaald.")
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
    """Render 'Achtergrond' page."""
    st.title("Achtergrond")
    st.markdown("tbd")


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
    
    st.title("📊 Statistieken")
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


def render_admin_page():
    """Render admin page with all users and their reading statistics."""
    supabase = st.session_state.supabase
    
    st.title("🔐 Admin Dashboard")
    st.caption("💡 Tip: Toegankelijk via [jouw-url]?page=Admin")
    st.markdown("---")
    
    # Check if user is logged in
    if not st.session_state.user:
        st.warning("⚠️ Je moet ingelogd zijn om de admin pagina te bekijken.")
        return
    
    st.subheader("📊 Gebruikers en Leesstatistieken")
    
    # Refresh button
    if st.button("🔄 Vernieuw Data", use_container_width=True):
        st.rerun()
    
    try:
        # Try to get all users (including those without activity)
        users_data = supabase.get_all_users_with_reading_stats_via_activity()
        
        if not users_data:
            st.warning("⚠️ Geen gebruikers gevonden. Controleer of de database functie correct is uitgevoerd.")
            st.info("💡 Tip: Voer het SQL script `admin_get_user_emails.sql` uit in Supabase om alle gebruikers te zien.")
            return
        
        # Create DataFrame for better display
        import pandas as pd
        
        # Prepare data for table
        table_data = []
        for user in users_data:
            table_data.append({
                'Gebruiker ID': user['user_id'][:8] + '...' if len(user['user_id']) > 8 else user['user_id'],
                'Email': user['email'],
                'Artikelen Geopend': user['total_articles_opened'],
                'Artikelen Gelezen': user['total_articles_read'],
                'Gem. Leesduur (sec)': round(user['avg_read_duration_seconds'], 1) if user['avg_read_duration_seconds'] > 0 else 0,
                'Leespercentage': f"{user['read_percentage']:.1f}%" if user['read_percentage'] > 0 else "0%"
            })
        
        df = pd.DataFrame(table_data)
        
        # Display summary metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Totaal Gebruikers", len(users_data))
        with col2:
            total_read = sum(u['total_articles_read'] for u in users_data)
            st.metric("Totaal Gelezen", total_read)
        with col3:
            total_opened = sum(u['total_articles_opened'] for u in users_data)
            st.metric("Totaal Geopend", total_opened)
        with col4:
            avg_read_per_user = total_read / len(users_data) if users_data else 0
            st.metric("Gem. Gelezen/User", f"{avg_read_per_user:.1f}")
        
        st.markdown("---")
        
        # Display table
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Gebruiker ID": st.column_config.TextColumn("Gebruiker ID", width="small"),
                "Email": st.column_config.TextColumn("Email", width="medium"),
                "Artikelen Geopend": st.column_config.NumberColumn("Geopend", width="small"),
                "Artikelen Gelezen": st.column_config.NumberColumn("Gelezen", width="small"),
                "Gem. Leesduur (sec)": st.column_config.NumberColumn("Leesduur", width="small"),
                "Leespercentage": st.column_config.TextColumn("Lees%", width="small")
            }
        )
        
        # Download button
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download als CSV",
            data=csv,
            file_name=f"users_reading_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )
        
    except Exception as e:
        st.error(f"❌ Fout bij ophalen gebruikersdata: {str(e)}")
        import traceback
        with st.expander("🔍 Technische Details"):
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
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Wachtwoord", type="password", key="login_password")
            
            if st.button("Inloggen", use_container_width=True):
                result = supabase.sign_in(email, password)
                if result.get('success'):
                    user_obj = result.get('user')
                    # Store user as dict for better persistence across page navigations
                    if hasattr(user_obj, 'id'):
                        user_dict = {
                            'id': user_obj.id,
                            'email': getattr(user_obj, 'email', email),
                            'created_at': getattr(user_obj, 'created_at', None)
                        }
                    elif isinstance(user_obj, dict):
                        user_dict = user_obj
                    else:
                        # Fallback: try to extract from user object
                        user_dict = {
                            'id': getattr(user_obj, 'id', None) or (user_obj.user.id if hasattr(user_obj, 'user') else None),
                            'email': email,  # Use the email from input
                            'created_at': None
                        }
                    
                    st.session_state.user = user_dict
                    st.session_state.preferences = None  # Will be reloaded on next render
                    # Mark that user manually logged in
                    st.session_state.manual_login_performed = True
                    # Store the user email in session state for verification
                    st.session_state.manual_login_email = email
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
                        # Mark that user manually registered
                        st.session_state.manual_login_performed = True
                        st.success("Account aangemaakt! Je kunt nu inloggen.")
                    else:
                        st.error(f"Registratie mislukt: {result.get('error', 'Onbekende fout')}")
    else:
        # User is logged in
        user_email = get_user_email(st.session_state.user)
        
        if user_email:
            st.success(f"👤 Ingelogd als: {user_email}")
        else:
            st.success("👤 Ingelogd")
        
        if st.button("🚪 Uitloggen", use_container_width=True):
            supabase.sign_out()
            st.session_state.user = None
            st.session_state.preferences = None
            # Reset manual login flags
            st.session_state.manual_login_performed = False
            if 'manual_login_email' in st.session_state:
                del st.session_state.manual_login_email
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
    # IMPORTANT: If user is already in session_state, keep it (don't overwrite with Supabase session)
    # This ensures manual logins are preserved across page navigations
    
    # Always ensure preferences are loaded if user exists
    if st.session_state.user and st.session_state.preferences is None:
        user_id = get_user_id(st.session_state.user)
        if user_id:
            try:
                st.session_state.preferences = supabase.get_user_preferences(user_id)
            except Exception as e:
                print(f"Error loading preferences: {e}")
    
    if st.session_state.user is None:
        # Try to restore user from Supabase session (if user previously logged in)
        # No auto-login - users must manually sign up and login
        try:
            user = supabase.get_current_user()
            if user:
                # Store user in session state to preserve across page navigations
                st.session_state.user = user
                # Load preferences if not already loaded
                if st.session_state.preferences is None:
                    user_id = get_user_id(user)
                    if user_id:
                        st.session_state.preferences = supabase.get_user_preferences(user_id)
        except Exception as e:
            # If get_current_user fails, user is not logged in - that's OK
            # User can browse the site without login, but won't have personalization
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
    elif page == "Statistics":
        render_statistics_page()
    elif page == "Gebruiker":
        render_gebruiker_page()
    elif page == "Admin":
        render_admin_page()


if __name__ == "__main__":
    main()
