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
        padding: 0.75rem;
        margin-bottom: 1rem;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        background-color: #ffffff;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: transform 0.2s, box-shadow 0.2s;
        height: 100%;
        display: flex;
        flex-direction: column;
    }
    .article-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }
    .article-image {
        width: 100%;
        height: 150px;
        object-fit: cover;
        border-radius: 4px;
        margin-bottom: 0.5rem;
    }
    .article-title {
        font-size: 0.95rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 0.5rem;
        line-height: 1.3;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }
    .article-meta {
        font-size: 0.75rem;
        color: #666;
        margin-bottom: 0.5rem;
    }
    .article-summary {
        font-size: 0.85rem;
        color: #333;
        line-height: 1.4;
        flex-grow: 1;
        display: -webkit-box;
        -webkit-line-clamp: 3;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }
    .article-category {
        display: inline-block;
        background-color: #e3f2fd;
        color: #1976d2;
        padding: 0.2rem 0.5rem;
        border-radius: 12px;
        font-size: 0.7rem;
        margin-top: 0.5rem;
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
                        ('TRUMP', 'Trump'),
                        ('RUSSIA', 'Rusland'),
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
    # Check if we've already tried to ingest in this session
    if 'ingestion_attempted' in st.session_state and st.session_state.ingestion_attempted:
        return
    
    try:
        article_count = Article.objects.count()
        if article_count == 0:
            # Mark that we're attempting ingestion
            st.session_state.ingestion_attempted = True
            
            # Try to ingest articles using the RSS service directly
            try:
                from apps.feed_ingest.services.rss import fetch_and_ingest_all_feeds
                from django.conf import settings
                
                # Get feed URLs
                feed_urls = getattr(settings, 'NOS_RSS_FEEDS', [])
                if not feed_urls:
                    single_feed = getattr(settings, 'NOS_RSS_FEED_URL', '')
                    if single_feed:
                        feed_urls = [single_feed]
                
                if feed_urls:
                    # Try to fetch from all feeds, but limit items per feed for faster initial load
                    runs = fetch_and_ingest_all_feeds(max_items=30)
                    
                    # Check results
                    total_inserted = sum(r.inserted_count for r in runs)
                    total_updated = sum(r.updated_count for r in runs)
                    failed_runs = [r for r in runs if r.status == 'FAILED']
                    
                    # Store results in session state for display
                    st.session_state.last_ingestion_result = {
                        'inserted': total_inserted,
                        'updated': total_updated,
                        'failed': len(failed_runs),
                        'total_feeds': len(runs)
                    }
                    
                    # If all failed, try with just the first feed
                    if total_inserted == 0 and total_updated == 0 and failed_runs and len(failed_runs) == len(runs):
                        from apps.feed_ingest.services.rss import fetch_and_ingest_feed
                        try:
                            run = fetch_and_ingest_feed(feed_url=feed_urls[0], max_items=50)
                            if run.inserted_count > 0 or run.updated_count > 0:
                                st.session_state.last_ingestion_result = {
                                    'inserted': run.inserted_count,
                                    'updated': run.updated_count,
                                    'failed': 0,
                                    'total_feeds': 1
                                }
                        except Exception:
                            pass
            except Exception as e:
                # Store error for debugging
                st.session_state.ingestion_error = str(e)
    except Exception:
        # If database query fails, that's handled elsewhere
        pass


@st.cache_data(ttl=1800)  # Refresh ingestion at most once every 30 minutes
def refresh_articles_periodically():
    """
    Periodically refresh NOS RSS feed.
    This is safe to call on every page load; caching ensures it's only executed
    once per 30-minute window per server instance.
    """
    from apps.feed_ingest.services.rss import fetch_and_ingest_all_feeds

    try:
        # Use the RSS service directly for better control
        runs = fetch_and_ingest_all_feeds()
        # Check if any runs failed
        failed_runs = [r for r in runs if r.status == 'FAILED']
        if failed_runs:
            # Log but don't break the app
            pass
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


def get_summary_sentences(text, num_sentences=2):
    """Extract first N sentences from text."""
    if not text:
        return ""
    
    # Split by sentence endings
    import re
    sentences = re.split(r'[.!?]+\s+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    # Take first N sentences
    selected = sentences[:num_sentences]
    summary = '. '.join(selected)
    
    # Add period if it doesn't end with punctuation
    if summary and not summary[-1] in '.!?':
        summary += '.'
    
    return summary


def display_article_detail(article_id):
    """Display full article detail page."""
    try:
        article = Article.objects.get(id=article_id)
        
        st.title(article.title)
        
        # Meta information
        col1, col2 = st.columns([3, 1])
        with col1:
            meta_info = []
            if article.published_at:
                meta_info.append(format_datetime(article.published_at))
            if article.category:
                meta_info.append(f"**{article.category.name}**")
            if meta_info:
                st.markdown(" | ".join(meta_info))
        
        with col2:
            if st.button("← Terug naar overzicht"):
                del st.query_params["article"]
                st.rerun()
        
        st.markdown("---")
        
        # Image
        if article.image_url:
            st.image(article.image_url, use_container_width=True)
        
        # Summary
        if article.summary:
            st.subheader("Samenvatting")
            st.markdown(article.summary)
            st.markdown("---")
        
        # Full content
        if article.content:
            st.subheader("Volledige inhoud")
            st.markdown(article.content)
        
        # Link to original
        st.markdown("---")
        st.markdown(f"**Bron:** {article.source_name} — [Bekijk origineel artikel]({article.link})")
        
    except Article.DoesNotExist:
        st.error("Artikel niet gevonden.")
        if st.button("← Terug naar overzicht"):
            st.query_params.clear()
            st.rerun()




def manual_refresh_articles():
    """Manually trigger article refresh."""
    from apps.feed_ingest.services.rss import fetch_and_ingest_all_feeds
    
    try:
        with st.spinner("Artikelen ophalen van NOS..."):
            runs = fetch_and_ingest_all_feeds(max_items=50)
            total_inserted = sum(r.inserted_count for r in runs)
            total_updated = sum(r.updated_count for r in runs)
            failed_runs = [r for r in runs if r.status == 'FAILED']
            
            if total_inserted > 0 or total_updated > 0:
                st.success(f"✅ {total_inserted} nieuwe artikelen toegevoegd, {total_updated} bijgewerkt")
                # Clear cache to show new articles immediately
                get_categories.cache_data.clear()
                get_articles_count.cache_data.clear()
            elif failed_runs:
                st.error(f"❌ Fout bij ophalen artikelen. Probeer het later opnieuw.")
            else:
                st.info("ℹ️ Geen nieuwe artikelen gevonden.")
    except Exception as e:
        st.error(f"❌ Fout: {str(e)}")


def main():
    """Main Streamlit app."""
    # Ensure database is initialized before any queries
    ensure_database_initialized()
    # Ensure we have initial data and keep refreshing the feed
    ensure_initial_articles_ingested()
    refresh_articles_periodically()
    
    st.title("📰 NOS Nieuws Aggregator")
    
    # Show ingestion status if available
    if 'last_ingestion_result' in st.session_state:
        result = st.session_state.last_ingestion_result
        if result['inserted'] > 0 or result['updated'] > 0:
            st.success(f"✅ {result['inserted']} artikelen toegevoegd, {result['updated']} bijgewerkt")
        elif result['failed'] > 0:
            st.warning(f"⚠️ {result['failed']} van {result['total_feeds']} feeds gefaald")
    
    if 'ingestion_error' in st.session_state:
        st.error(f"❌ Fout bij ophalen artikelen: {st.session_state.ingestion_error}")
    
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.header("Filters")
        
        # Manual refresh button
        if st.button("🔄 Artikelen Vernieuwen", use_container_width=True):
            manual_refresh_articles()
            st.rerun()
        
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
    
    # Check if we're viewing an article detail
    if "article" in st.query_params:
        article_id = st.query_params["article"]
        try:
            display_article_detail(article_id)
            return
        except Exception as e:
            st.error(f"Fout bij laden artikel: {str(e)}")
            if st.button("← Terug naar overzicht"):
                del st.query_params["article"]
                st.rerun()
            return
    
    # Display articles in grid
    if not articles:
        if st.session_state.selected_categories and not search_query:
            st.info("ℹ️ Geen artikelen gevonden voor de geselecteerde categorieën. Selecteer andere categorieën of verwijder filters.")
        elif search_query:
            st.info(f"ℹ️ Geen artikelen gevonden voor de zoekopdracht: '{search_query}'")
        else:
            st.info("ℹ️ Geen artikelen gevonden. Klik op '🔄 Artikelen Vernieuwen' om artikelen op te halen.")
    else:
        st.subheader(f"Artikelen ({len(articles)})")
        
        # Display articles in grid (4 per row)
        articles_list = list(articles)
        num_rows = (len(articles_list) + 3) // 4  # Round up division
        
        for row in range(num_rows):
            cols = st.columns(4)
            for col_idx in range(4):
                article_idx = row * 4 + col_idx
                if article_idx < len(articles_list):
                    with cols[col_idx]:
                        article = articles_list[article_idx]
                        
                        # Image
                        if article.image_url:
                            try:
                                st.image(article.image_url, use_container_width=True)
                            except:
                                pass
                        
                        # Title (clickable via button)
                        title_text = article.title[:70] + "..." if len(article.title) > 70 else article.title
                        if st.button(title_text, key=f"title_{article.id}", use_container_width=True):
                            st.query_params["article"] = str(article.id)
                            st.rerun()
                        
                        # Category badge
                        if article.category:
                            st.markdown(f'<span class="article-category">{article.category.name}</span>', unsafe_allow_html=True)
                        
                        # Date
                        if article.published_at:
                            date_str = format_datetime(article.published_at)
                            st.caption(date_str)
                        
                        # Summary (2 sentences)
                        summary_text = article.summary or article.content or ""
                        summary = get_summary_sentences(summary_text, num_sentences=2)
                        if summary:
                            st.markdown(f'<div class="article-summary">{summary}</div>', unsafe_allow_html=True)
        
        # Load more info
        if len(articles) >= 50:
            st.info("ℹ️ Toon maximaal 50 artikelen. Gebruik filters om te verfijnen.")


if __name__ == "__main__":
    main()


