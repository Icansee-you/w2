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
from supabase_client import get_supabase_client
from articles_repository import fetch_and_upsert_articles, generate_missing_eli5_summaries
from nlp_utils import generate_eli5_summary_nl_with_llm

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
        justify-content: center;
        gap: 2rem;
        padding: 1rem 0;
        border-bottom: 2px solid #e0e0e0;
        margin-bottom: 2rem;
        background-color: #ffffff;
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
    
    .article-category {
        display: inline-block;
        background-color: #e3f2fd;
        color: #1976d2;
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.8rem;
        margin: 0.25rem 0.25rem 0.25rem 0;
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
    
    @media (max-width: 768px) {
        .horizontal-menu {
            flex-direction: column;
            gap: 0.5rem;
        }
        .menu-item {
            text-align: center;
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
    """Initialize Supabase client or local storage."""
    try:
        if st.session_state.supabase is None:
            st.session_state.supabase = get_supabase_client()
            
            # Check if using local storage
            try:
                from local_storage import LocalStorage
                if isinstance(st.session_state.supabase, LocalStorage):
                    st.info("🧪 **Testmodus**: Gebruikt lokale opslag (geen Supabase vereist)")
            except ImportError:
                pass
        
        return st.session_state.supabase
    except Exception as e:
        st.error(f"Error initializing storage: {str(e)}")
        return None


def render_horizontal_menu():
    """Render horizontal navigation menu."""
    menu_html = """
    <div class="horizontal-menu">
        <a class="menu-item" href="?page=Nieuws" onclick="window.location.href='?page=Nieuws'; return false;">Nieuws</a>
        <a class="menu-item" href="?page=Waarom" onclick="window.location.href='?page=Waarom'; return false;">Waarom?</a>
        <a class="menu-item" href="?page=Gebruiker" onclick="window.location.href='?page=Gebruiker'; return false;">Gebruiker</a>
    </div>
    """
    st.markdown(menu_html, unsafe_allow_html=True)
    
    # Update current page from query params
    page = st.query_params.get("page", "Nieuws")
    if page in ["Nieuws", "Waarom", "Gebruiker"]:
        st.session_state.current_page = page


def strip_html_tags(text: str) -> str:
    """Remove HTML tags from text."""
    if not text:
        return ""
    text = re.sub(r'<[^>]+>', '', text)
    text = unescape(text)
    text = re.sub(r'\s+', ' ', text)
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


def ensure_eli5_summary(article: Dict[str, Any], supabase) -> Dict[str, Any]:
    """Ensure article has ELI5 summary, generate if missing."""
    if not article.get('eli5_summary_nl'):
        # Generate ELI5 summary
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
        # Get LLM info if available
        article['eli5_llm'] = article.get('eli5_llm', 'Onbekend')
    
    return article


def render_article_card(article: Dict[str, Any], supabase):
    """Render a single article card with auto-generated ELI5."""
    # Ensure ELI5 summary exists
    article = ensure_eli5_summary(article, supabase)
    
    # Image
    if article.get('image_url'):
        try:
            st.image(article['image_url'], use_container_width=True)
        except:
            pass
    
    # Title (clickable)
    title = article.get('title', 'Geen titel')
    if st.button(title[:70] + "..." if len(title) > 70 else title, key=f"article_{article['id']}", use_container_width=True):
        st.query_params["article"] = article['id']
        st.rerun()
    
    # Category badges
    categories = article.get('categories', [])
    if categories:
        for cat in categories[:3]:  # Show max 3 categories
            st.markdown(f'<span class="article-category">{cat}</span>', unsafe_allow_html=True)
    
    # Date
    if article.get('published_at'):
        date_str = format_datetime(article['published_at'])
        st.caption(date_str)
    
    # Summary (2 sentences)
    description = article.get('description', '')
    if description:
        summary = get_summary_sentences(description, num_sentences=2)
        st.markdown(f'<div class="article-summary">{summary}</div>', unsafe_allow_html=True)
    
    # ELI5 Summary (automatically shown)
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
    
    # Ensure ELI5 summary
    article = ensure_eli5_summary(article, supabase)
    
    st.markdown('<div class="article-detail-container">', unsafe_allow_html=True)
    
    if st.button("← Terug naar overzicht"):
        del st.query_params["article"]
        st.rerun()
    
    st.title(article.get('title', 'Geen titel'))
    
    meta = []
    if article.get('published_at'):
        meta.append(format_datetime(article['published_at']))
    if article.get('categories'):
        meta.append(f"**{', '.join(article['categories'][:3])}**")
    if meta:
        st.caption(" | ".join(meta))
    
    st.markdown("---")
    
    # Image
    if article.get('image_url'):
        col_left, col_img, col_right = st.columns([1, 2, 1])
        with col_img:
            st.image(article['image_url'], use_container_width=True)
    
    # Description
    if article.get('description'):
        st.subheader("Samenvatting")
        clean_description = strip_html_tags(article['description'])
        st.markdown(clean_description)
        st.markdown("---")
    
    # ELI5 Summary (automatically shown)
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
    
    # Full content
    if article.get('full_content'):
        st.subheader("Volledige inhoud")
        clean_content = strip_html_tags(article['full_content'])
        st.markdown(clean_content)
    
    # Source link
    st.markdown("---")
    if article.get('url'):
        st.markdown(f"**Bron:** {article.get('source', 'NOS')} — [Bekijk origineel artikel]({article['url']})")
    
    st.markdown('</div>', unsafe_allow_html=True)


def render_nieuws_page():
    """Render main news overview page."""
    supabase = st.session_state.supabase
    
    st.title("📰 Nieuws")
    
    # Check if viewing article detail
    if "article" in st.query_params:
        render_article_detail(st.query_params["article"])
        return
    
    # Filters
    col1, col2 = st.columns([2, 1])
    with col1:
        search_query = st.text_input("🔍 Zoeken", placeholder="Zoek in artikelen...", key="search")
    with col2:
        category_filter = st.selectbox(
            "Categorie",
            ["Alle", "Politiek", "Nationaal", "Internationaal", "Sport", "Trump", "Rusland", "Overig"],
            key="category_filter"
        )
    
    st.markdown("---")
    
    # Refresh button
    if st.button("🔄 Artikelen Vernieuwen", use_container_width=True):
        with st.spinner("Artikelen ophalen..."):
            feed_urls = [
                'https://feeds.nos.nl/nosnieuwsalgemeen',
                'https://feeds.nos.nl/nosnieuwsbinnenland',
                'https://feeds.nos.nl/nosnieuwsbuitenland',
            ]
            total_inserted = 0
            total_updated = 0
            for feed_url in feed_urls:
                result = fetch_and_upsert_articles(feed_url, max_items=30)
                if result.get('success'):
                    total_inserted += result.get('inserted', 0)
                    total_updated += result.get('updated', 0)
            
            if total_inserted > 0 or total_updated > 0:
                st.success(f"✅ {total_inserted} nieuwe artikelen, {total_updated} bijgewerkt")
            else:
                st.info("Geen nieuwe artikelen gevonden")
            st.rerun()
    
    # Get user preferences
    blacklist = []
    selected_categories = None
    if st.session_state.user and st.session_state.preferences:
        blacklist = st.session_state.preferences.get('blacklist_keywords', [])
        selected_categories = st.session_state.preferences.get('selected_categories')
    
    # Get articles
    category = None if category_filter == "Alle" else category_filter
    try:
        categories_filter = selected_categories if (st.session_state.user and selected_categories) else None
        
        articles = supabase.get_articles(
            limit=50,
            category=category,
            categories=categories_filter,
            search_query=search_query if search_query else None,
            blacklist_keywords=blacklist if blacklist else None
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
                        st.success("Account aangemaakt! Je kunt nu inloggen.")
                    else:
                        st.error(f"Registratie mislukt: {result.get('error', 'Onbekende fout')}")
    else:
        # User is logged in
        st.success(f"👤 Ingelogd als: {st.session_state.user.get('email', 'Gebruiker')}")
        
        if st.button("🚪 Uitloggen", use_container_width=True):
            supabase.sign_out()
            st.session_state.user = None
            st.session_state.preferences = None
            st.rerun()
        
        st.markdown("---")
        
        # Get preferences
        if st.session_state.preferences is None:
            st.session_state.preferences = supabase.get_user_preferences(st.session_state.user['id'])
        
        prefs = st.session_state.preferences
        blacklist = prefs.get('blacklist_keywords', [])
        selected_categories = prefs.get('selected_categories', [])
        
        # Category selection
        st.subheader("📂 Categorieën")
        st.caption("Selecteer welke categorieën je wilt zien")
        
        from categorization_engine import get_all_categories
        all_categories = get_all_categories()
        category_selections = {}
        
        for category in all_categories:
            category_selections[category] = st.checkbox(
                category,
                value=category in selected_categories,
                key=f"cat_pref_{category}"
            )
        
        new_selected = [cat for cat, selected in category_selections.items() if selected]
        if new_selected != selected_categories:
            if supabase.update_user_preferences(st.session_state.user['id'], selected_categories=new_selected):
                st.session_state.preferences = None
                st.rerun()
        
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
                        supabase.update_user_preferences(st.session_state.user['id'], blacklist_keywords=blacklist)
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
                    if supabase.update_user_preferences(st.session_state.user['id'], blacklist_keywords=blacklist):
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
    
    # Check authentication
    if st.session_state.user is None:
        user = supabase.get_current_user()
        if user:
            st.session_state.user = user
    
    # Render horizontal menu
    render_horizontal_menu()
    
    # Render current page
    page = st.session_state.current_page
    
    if page == "Nieuws":
        render_nieuws_page()
    elif page == "Waarom":
        render_waarom_page()
    elif page == "Gebruiker":
        render_gebruiker_page()


if __name__ == "__main__":
    main()
