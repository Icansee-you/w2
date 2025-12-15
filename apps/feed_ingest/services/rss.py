"""
RSS feed parsing and ingestion service.
"""
import feedparser
from datetime import datetime, timezone as tz
from django.conf import settings
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from apps.news.models import Article, Category
from apps.news.categorizer import assign_category
from apps.feed_ingest.models import IngestionRun


def parse_feed_entry(entry):
    """
    Parse a feed entry into article data.
    
    Args:
        entry: Feed entry from feedparser
    
    Returns:
        dict with article fields
    """
    # Extract title
    title = entry.get('title', '').strip()
    
    # Extract summary/description
    summary = entry.get('summary', '').strip()
    if not summary:
        summary = entry.get('description', '').strip()
    
    # Extract content
    content = ''
    if 'content' in entry:
        if isinstance(entry.content, list) and entry.content:
            content = entry.content[0].get('value', '').strip()
    elif 'description' in entry and not summary:
        content = entry.description.strip()
    
    # Extract link
    link = entry.get('link', '').strip()
    
    # Extract guid
    guid = None
    if 'id' in entry:
        guid = entry.id.strip()
    elif 'guid' in entry:
        if hasattr(entry.guid, 'value'):
            guid = entry.guid.value.strip()
        else:
            guid = str(entry.guid).strip()
    
    # Extract published date
    published_at = None
    if 'published_parsed' in entry and entry.published_parsed:
        published_at = datetime(*entry.published_parsed[:6], tzinfo=tz.utc)
    elif 'published' in entry:
        try:
            published_at = parse_datetime(entry.published)
            if published_at and not timezone.is_aware(published_at):
                published_at = timezone.make_aware(published_at)
        except (ValueError, TypeError):
            pass
    
    if not published_at:
        published_at = timezone.now()
    
    # Extract image URL
    image_url = None
    if 'media_thumbnail' in entry and entry.media_thumbnail:
        if isinstance(entry.media_thumbnail, list) and entry.media_thumbnail:
            image_url = entry.media_thumbnail[0].get('url', '')
        elif isinstance(entry.media_thumbnail, dict):
            image_url = entry.media_thumbnail.get('url', '')
    
    if not image_url and 'enclosures' in entry:
        for enclosure in entry.enclosures:
            if enclosure.get('type', '').startswith('image/'):
                image_url = enclosure.get('href', '')
                break
    
    if not image_url and 'media_content' in entry:
        if isinstance(entry.media_content, list):
            for media in entry.media_content:
                if media.get('type', '').startswith('image/'):
                    image_url = media.get('url', '')
                    break
    
    return {
        'title': title,
        'summary': summary,
        'content': content,
        'link': link,
        'guid': guid,
        'published_at': published_at,
        'image_url': image_url,
    }


def upsert_article(article_data, source_name='NOS', source_feed_url=None):
    """
    Upsert an article (insert or update).
    
    Args:
        article_data: dict with article fields
        source_name: Source name (default: NOS)
        source_feed_url: Feed URL
    
    Returns:
        tuple: (article, is_new)
    """
    if not source_feed_url:
        source_feed_url = getattr(settings, 'NOS_RSS_FEED_URL', '')
    
    guid = article_data.get('guid')
    link = article_data.get('link')
    published_at = article_data.get('published_at')
    
    # Try to find existing article
    article = None
    if guid:
        try:
            article = Article.objects.get(guid=guid)
        except Article.DoesNotExist:
            pass
    
    if not article and link and published_at:
        try:
            article = Article.objects.get(link=link, published_at=published_at)
        except Article.DoesNotExist:
            pass
    
    is_new = article is None
    
    if not article:
        # Create new article
        # Assign category
        category = assign_category(
            title=article_data.get('title', ''),
            summary=article_data.get('summary', ''),
            content=article_data.get('content', '')
        )
        
        article = Article.objects.create(
            title=article_data.get('title', ''),
            summary=article_data.get('summary'),
            content=article_data.get('content'),
            link=link,
            guid=guid,
            source_name=source_name,
            source_feed_url=source_feed_url,
            category=category,
            published_at=published_at,
            image_url=article_data.get('image_url'),
        )
    else:
        # Update existing article if fields changed
        updated = False
        
        if article.title != article_data.get('title', ''):
            article.title = article_data.get('title', '')
            updated = True
        
        if article.summary != article_data.get('summary', ''):
            article.summary = article_data.get('summary')
            updated = True
        
        if article.content != article_data.get('content', ''):
            article.content = article_data.get('content')
            updated = True
        
        if article.image_url != article_data.get('image_url', ''):
            article.image_url = article_data.get('image_url')
            updated = True
        
        # Re-categorize if title/summary/content changed
        if updated:
            new_category = assign_category(
                title=article.title,
                summary=article.summary or '',
                content=article.content or ''
            )
            if new_category:
                article.category = new_category
            article.save()
    
    return article, is_new


def fetch_and_ingest_all_feeds(max_items=None):
    """
    Fetch all configured NOS RSS feeds and ingest articles.
    
    Args:
        max_items: Maximum number of items per feed (default: None for all)
    
    Returns:
        list of IngestionRun instances
    """
    feed_urls = getattr(settings, 'NOS_RSS_FEEDS', [])
    if not feed_urls:
        # Fallback to single feed URL
        single_feed = getattr(settings, 'NOS_RSS_FEED_URL', '')
        if single_feed:
            feed_urls = [single_feed]
        else:
            raise ValueError("No feed URLs configured")
    
    runs = []
    for feed_url in feed_urls:
        try:
            run = fetch_and_ingest_feed(feed_url=feed_url, max_items=max_items)
            runs.append(run)
        except Exception as e:
            # Create a failed run for this feed
            run = IngestionRun.objects.create(
                status=IngestionRun.FAILED,
                started_at=timezone.now(),
                finished_at=timezone.now(),
                error_message=f"Failed to process feed {feed_url}: {str(e)}"
            )
            runs.append(run)
    
    return runs


def fetch_and_ingest_feed(feed_url=None, max_items=None):
    """
    Fetch RSS feed and ingest articles.
    
    Args:
        feed_url: Feed URL (defaults to NOS_RSS_FEED_URL)
        max_items: Maximum number of items to fetch (default: 100 for first run, None for all)
    
    Returns:
        IngestionRun instance
    """
    if not feed_url:
        feed_url = getattr(settings, 'NOS_RSS_FEED_URL', '')
    
    if not feed_url:
        raise ValueError("No feed URL provided")
    
    # Create ingestion run
    run = IngestionRun.objects.create(
        status=IngestionRun.SUCCESS,
        started_at=timezone.now()
    )
    
    try:
        # Fetch and parse feed
        feed = feedparser.parse(feed_url)
        
        if feed.bozo and feed.bozo_exception:
            raise Exception(f"Feed parsing error: {feed.bozo_exception}")
        
        entries = feed.entries
        
        if max_items:
            entries = entries[:max_items]
        
        run.fetched_count = len(entries)
        
        inserted_count = 0
        updated_count = 0
        skipped_count = 0
        
        for entry in entries:
            try:
                article_data = parse_feed_entry(entry)
                
                # Skip if missing required fields
                if not article_data.get('title') or not article_data.get('link'):
                    skipped_count += 1
                    continue
                
                article, is_new = upsert_article(
                    article_data,
                    source_name='NOS',
                    source_feed_url=feed_url
                )
                
                if is_new:
                    inserted_count += 1
                else:
                    updated_count += 1
                    
            except Exception as e:
                # Log error but continue with other entries
                import traceback
                print(f"Error processing entry: {e}")
                print(traceback.format_exc())
                skipped_count += 1
                continue
        
        run.inserted_count = inserted_count
        run.updated_count = updated_count
        run.skipped_count = skipped_count
        
        # Determine status
        if run.fetched_count == 0:
            run.status = IngestionRun.FAILED
            run.error_message = "No entries found in feed"
        elif inserted_count == 0 and updated_count == 0:
            run.status = IngestionRun.PARTIAL
            run.error_message = "No articles inserted or updated"
        elif skipped_count > run.fetched_count * 0.5:
            run.status = IngestionRun.PARTIAL
            run.error_message = f"High skip rate: {skipped_count}/{run.fetched_count}"
        
        run.finished_at = timezone.now()
        run.save()
        
    except Exception as e:
        run.status = IngestionRun.FAILED
        run.error_message = str(e)
        run.finished_at = timezone.now()
        run.save()
    
    return run

