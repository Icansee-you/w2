"""
Celery tasks for feed ingestion.
"""
from celery import shared_task
from apps.feed_ingest.services.rss import fetch_and_ingest_all_feeds


@shared_task
def fetch_nos_feed():
    """
    Celery task to fetch and ingest all NOS RSS feeds.
    """
    return fetch_and_ingest_all_feeds()

