"""
Streamlit app for NOS News Aggregator
This app uses Django ORM to access the database without running the full Django server.
"""
import os
import sys
from pathlib import Path

# Add project root to Python path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Configure Django settings before importing models
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Initialize Django
import django
django.setup()

from django.core.management import call_command

# Now we can import Django models
from apps.news.models import Article, Category
from apps.accounts.models import UserProfile
from django.contrib.auth.models import User
from django.db.models import Q
from django.core.paginator import Paginator
import streamlit as st
from datetime import datetime
import pytz

# Page configuration
st.set_page_config(
    page_title="NOS Nieuws Aggregator",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .article-card {
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 4px solid #1f77b4;
        background-color: #f8f9fa;
        border-radius: 5px;
    }
    .article-title {
        font-size: 1.2rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .article-meta {
        font-size: 0.85rem;
        color: #666;
        margin-bottom: 0.5rem;
    }
    .article-summary {
        margin-top: 0.5rem;
        color: #333;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'selected_categories' not in st.session_state:
    st.session_state.selected_categories = []


def ensure_database_initialized():
    """Ensure database is initialized with migrations and categories."""
    # Use session state to track if we've already initialized
    if 'db_initialized' in st.session_state and st.session_state.db_initialized:
        return
    
    from django.db import connection
    from django.core.management import call_command
    
    # Check if database file exists and has tables
    try:
        with connection.cursor() as cursor:
            # Try to query a table to see if database is initialized
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='news_category'")
            table_exists = cursor.fetchone() is not None
            
            if not table_exists:
                # Run migrations
                try:
                    call_command("migrate", interactive=False, verbosity=0)
                except Exception:
                    # If migrations fail, try to continue anyway
                    pass
                
                # Initialize categories
                try:
                    call_command("init_categories", verbosity=0)
                except Exception:
                    # If command fails, create categories manually
                    category_data = [
                        ('POLITICS', 'Politiek'),
                        ('NATIONAL', 'Nationaal'),
                        ('INTERNATIONAL', 'Internationaal'),
                        ('SPORT', 'Sport'),
                        ('OTHER', 'Overig'),
                    ]
                    for key, name in category_data:
                        Category.objects.get_or_create(key=key, defaults={'name': name})
                
                st.session_state.db_initialized = True
            else:
                st.session_state.db_initialized = True
    except Exception:
        # If database doesn't exist or can't be accessed, migrations will create it
        try:
            call_command("migrate", interactive=False, verbosity=0)
            call_command("init_categories", verbosity=0)
            st.session_state.db_initialized = True
        except Exception:
            pass


@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_categories():
    """Get all categories."""
    try:
        return list(Category.objects.all().order_by('key'))
    except Exception:
        # If database query fails, try to initialize and return empty list
        ensure_database_initialized()
        try:
            return list(Category.objects.all().order_by('key'))
        except Exception:
            return []


def ensure_initial_articles_ingested():
    """
    Ensure there are some NOS articles in the database on first deploy.
    If there are no articles yet, run a one-time ingestion with a limited number
    of items to quickly seed the feed.
    """
    from django.core.management import call_command

    try:
        if Article.objects.count() == 0:
            with st.spinner("Eerste NOS artikelen ophalen..."):
                # Ingest a limited number of items for the initial seed
                try:
                    call_command("ingest_nos", max_items=100)
                except Exception:
                    # If ingestion fails, we just continue; the app will show a message
                    pass
    except Exception:
        # If the database is not reachable, initialization will handle it
        pass


@st.cache_data(ttl=1800)  # Refresh ingestion at most once every 30 minutes
def refresh_articles_periodically():
    """
    Periodically refresh NOS RSS feed.
    This is safe to call on every page load; caching ensures it's only executed
    once per 30-minute window per server instance.
    """
    from django.core.management import call_command

    try:
        call_command("ingest_nos")
    except Exception:
        # Swallow errors so the UI remains usable even if ingestion fails
        pass


@st.cache_data(ttl=60)  # Cache for 1 minute
def get_articles_count():
    """Get total article count."""
    return Article.objects.count()


def get_articles(categories=None, search_query=None, limit=50):
    """Get articles filtered by categories and search query."""
    articles = Article.objects.all()
    
    # Filter by categories
    if categories:
        articles = articles.filter(category__in=categories)
    
    # Search functionality
    if search_query:
        articles = articles.filter(
            Q(title__icontains=search_query) |
            Q(summary__icontains=search_query) |
            Q(content__icontains=search_query)
        )
    
    # Order by published_at desc
    articles = articles.order_by('-published_at')
    
    return articles[:limit]


def format_datetime(dt):
    """Format datetime for display."""
    if dt:
        amsterdam_tz = pytz.timezone('Europe/Amsterdam')
        if dt.tzinfo is None:
            dt = pytz.utc.localize(dt)
        dt = dt.astimezone(amsterdam_tz)
        return dt.strftime('%d %B %Y, %H:%M')
    return ""


def main():
    """Main Streamlit app."""
    # Ensure database is initialized before any queries
    ensure_database_initialized()
    # Ensure we have initial data and keep refreshing the feed
    ensure_initial_articles_ingested()
    refresh_articles_periodically()
    
    st.title("📰 NOS Nieuws Aggregator")
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.header("Filters")
        
        # Get categories
        categories = get_categories()
        
        if not categories:
            st.warning("⚠️ Geen categorieën gevonden. Voer eerst `python manage.py init_categories` uit.")
            return
        
        # Category selection
        st.subheader("Categorieën")
        selected_category_keys = []
        
        for category in categories:
            checked = st.checkbox(
                category.name,
                value=category.key in st.session_state.selected_categories,
                key=f"cat_{category.key}"
            )
            if checked:
                selected_category_keys.append(category.key)
        
        st.session_state.selected_categories = selected_category_keys
        
        # Search
        st.subheader("Zoeken")
        search_query = st.text_input(
            "Zoek in artikelen",
            placeholder="Typ om te zoeken...",
            key="search_input"
        )
        
        # Stats
        st.markdown("---")
        st.subheader("Statistieken")
        total_articles = get_articles_count()
        st.metric("Totaal artikelen", total_articles)
        
        if selected_category_keys:
            selected_categories_objs = Category.objects.filter(key__in=selected_category_keys)
            filtered_count = Article.objects.filter(category__in=selected_categories_objs).count()
            st.metric("Gefilterde artikelen", filtered_count)
    
    # Main content
    # Get selected category objects
    selected_categories_objs = []
    if st.session_state.selected_categories:
        selected_categories_objs = Category.objects.filter(key__in=st.session_state.selected_categories)
    
    # Get articles
    articles = get_articles(
        categories=selected_categories_objs if selected_categories_objs else None,
        search_query=search_query if search_query else None,
        limit=50
    )
    
    # Display articles
    if not articles:
        if st.session_state.selected_categories and not search_query:
            st.info("ℹ️ Geen artikelen gevonden voor de geselecteerde categorieën. Selecteer andere categorieën of verwijder filters.")
        elif search_query:
            st.info(f"ℹ️ Geen artikelen gevonden voor de zoekopdracht: '{search_query}'")
        else:
            st.info("ℹ️ Geen artikelen gevonden. Voer eerst `python manage.py ingest_nos` uit om artikelen te importeren.")
    else:
        st.subheader(f"Artikelen ({len(articles)})")
        
        # Display articles
        for article in articles:
            with st.container():
                # Article card
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    # Title with link
                    st.markdown(f"### [{article.title}]({article.link})")
                    
                    # Meta information
                    meta_info = []
                    if article.category:
                        meta_info.append(f"**{article.category.name}**")
                    if article.published_at:
                        meta_info.append(format_datetime(article.published_at))
                    if article.source_name:
                        meta_info.append(article.source_name)
                    
                    st.markdown(" | ".join(meta_info))
                    
                    # Summary
                    if article.summary:
                        st.markdown(article.summary)
                    
                    # Image
                    if article.image_url:
                        st.image(article.image_url, use_container_width=True)
                    
                    # Content preview
                    if article.content and article.content != article.summary:
                        content_preview = article.content[:500] + "..." if len(article.content) > 500 else article.content
                        with st.expander("Lees meer"):
                            st.markdown(content_preview)
                
                with col2:
                    # Article ID for reference
                    st.caption(f"ID: {str(article.id)[:8]}...")
                
                st.markdown("---")
        
        # Load more button (if needed)
        if len(articles) >= 50:
            st.info("ℹ️ Toon maximaal 50 artikelen. Gebruik filters om te verfijnen.")


if __name__ == "__main__":
    main()


