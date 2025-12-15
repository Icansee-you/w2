"""
Management command to manually trigger NOS feed ingestion.
"""
from django.core.management.base import BaseCommand
from apps.feed_ingest.services.rss import fetch_and_ingest_all_feeds
from django.conf import settings


class Command(BaseCommand):
    help = 'Manually trigger NOS RSS feed ingestion for all feeds'

    def add_arguments(self, parser):
        parser.add_argument(
            '--max-items',
            type=int,
            default=None,
            help='Maximum number of items per feed to fetch (default: all)'
        )
        parser.add_argument(
            '--feed-url',
            type=str,
            default=None,
            help='Process only a specific feed URL (optional)'
        )

    def handle(self, *args, **options):
        max_items = options.get('max_items')
        feed_url = options.get('feed_url')
        
        if feed_url:
            # Process single feed
            from apps.feed_ingest.services.rss import fetch_and_ingest_feed
            self.stdout.write(f'Starting NOS feed ingestion for: {feed_url}')
            run = fetch_and_ingest_feed(feed_url=feed_url, max_items=max_items)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Ingestion completed: {run.get_status_display()}\n'
                    f'Fetched: {run.fetched_count}\n'
                    f'Inserted: {run.inserted_count}\n'
                    f'Updated: {run.updated_count}\n'
                    f'Skipped: {run.skipped_count}'
                )
            )
            
            if run.error_message:
                self.stdout.write(
                    self.style.WARNING(f'Error: {run.error_message}')
                )
        else:
            # Process all feeds
            self.stdout.write('Starting NOS feed ingestion for all feeds...')
            feed_urls = getattr(settings, 'NOS_RSS_FEEDS', [])
            self.stdout.write(f'Processing {len(feed_urls)} feeds...')
            
            runs = fetch_and_ingest_all_feeds(max_items=max_items)
            
            total_fetched = sum(r.fetched_count for r in runs)
            total_inserted = sum(r.inserted_count for r in runs)
            total_updated = sum(r.updated_count for r in runs)
            total_skipped = sum(r.skipped_count for r in runs)
            failed_runs = [r for r in runs if r.status == 'FAILED']
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'\nAll feeds processed:\n'
                    f'Total fetched: {total_fetched}\n'
                    f'Total inserted: {total_inserted}\n'
                    f'Total updated: {total_updated}\n'
                    f'Total skipped: {total_skipped}\n'
                    f'Failed feeds: {len(failed_runs)}/{len(runs)}'
                )
            )
            
            if failed_runs:
                self.stdout.write(self.style.WARNING('\nFailed feeds:'))
                for run in failed_runs:
                    self.stdout.write(
                        self.style.WARNING(f'  - {run.error_message}')
                    )

